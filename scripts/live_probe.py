from __future__ import annotations

import argparse
import json
import os
import socket
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from app.apertus_client import OpenAICompatibleApertusClient
from app.fixtures import scenario_documents
from app.service import run_workflow

SCENARIOS = ("normal", "missing", "conflict", "untrusted", "human_gate")
REQUIRED_FIELDS = ["product", "price_chf", "delivery_days"]
TASK = "Prepare the correct customer response."


def _safe_endpoint(value: str) -> str:
    return value.rstrip("/")


def run_scenario(client: OpenAICompatibleApertusClient, scenario: str, task: str = TASK) -> dict:
    result = run_workflow(
        client,
        task,
        scenario_documents(scenario),
        REQUIRED_FIELDS,
    )
    return {
        "scenario": scenario,
        "status": result["status"],
        "model_output": result["model_output"],
        "control": result["control"],
        "evidence": result["evidence"],
        "transport": client.last_metadata,
    }


def sanitize(value, secret):
    """Sanitize before persistence, including a provider accidentally echoing a key."""
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]") if secret else value
    if isinstance(value, dict):
        return {sanitize(k, secret): sanitize(v, secret) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v, secret) for v in value]
    return value


def error_class(exc):
    if isinstance(exc, urllib.error.HTTPError):
        return ({401: "AUTHENTICATION_ERROR", 403: "AUTHENTICATION_ERROR",
                 404: "ENDPOINT_OR_MODEL_NOT_FOUND", 429: "RATE_LIMITED"}.get(exc.code)
                or ("PROVIDER_TRANSIENT_ERROR" if 500 <= exc.code < 600 else "EXECUTION_ERROR"))
    if isinstance(exc, (TimeoutError, socket.timeout)) or (
        isinstance(exc, urllib.error.URLError) and isinstance(exc.reason, (TimeoutError, socket.timeout))
    ):
        return "TIMEOUT"
    return "EXECUTION_ERROR"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a real Apertus request and capture sanitized end-to-end evidence."
    )
    parser.add_argument("--scenario", choices=SCENARIOS, default="normal")
    parser.add_argument("--all", action="store_true", help="Run all five synthetic control scenarios.")
    parser.add_argument("--prompt", default=os.environ.get("APERTUS_PROBE_PROMPT", TASK))
    parser.add_argument("--timeout", type=float, default=90)
    parser.add_argument("--connectivity", action="store_true", help="Run a connectivity request before the control workflow.")
    parser.add_argument(
        "--output",
        help="Optional evidence JSON path. Defaults to evidence/runtime-<timestamp>.json.",
    )
    args = parser.parse_args()

    base_url = _safe_endpoint(os.environ.get("APERTUS_BASE_URL", ""))
    api_key = os.environ.get("APERTUS_API_KEY", "")
    model = os.environ.get("APERTUS_MODEL", "swiss-ai/Apertus-v1.5-8B")

    scenarios = SCENARIOS if args.all else (args.scenario,)
    observed_at = datetime.now(timezone.utc)
    payload = {
        "evidence_version": 1,
        "observed_at_utc": observed_at.isoformat(),
        "mode": "live",
        "base_url": base_url,
        "model": model,
        "authentication_configured": bool(api_key),
        "credential_value_recorded": False,
        "synthetic_data_only": True,
        "results": [],
        "success": False,
    }
    exit_code = 0
    try:
        # Credentials must never be embedded in the URL, including its query string.
        from urllib.parse import urlsplit
        parsed = urlsplit(base_url)
        if not api_key or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Invalid live configuration")
        if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}):
            raise ValueError("HTTPS required")
        if not 0 < args.timeout <= 300:
            raise ValueError("Invalid timeout")
        client = OpenAICompatibleApertusClient(base_url=base_url, api_key=api_key, model=model, timeout=args.timeout)
        if args.connectivity:
            client.complete("You are a connectivity test assistant.", "Antworte exakt mit: APERTUS_E2E_PASS")
            payload["connectivity"] = dict(client.last_metadata)
            if not client.last_metadata["response_present"]:
                raise ValueError("Empty connectivity response")
        for scenario in scenarios:
            payload["results"].append(run_scenario(client, scenario, args.prompt))
        payload["success"] = True
    except Exception as exc:
        exit_code = 1
        payload.update(error_class=error_class(exc), error_message="Live request or structured readback failed.",
                       http_status=exc.code if isinstance(exc, urllib.error.HTTPError) else None)

    if args.output:
        path = Path(args.output)
    else:
        stamp = observed_at.strftime("%Y%m%dT%H%M%S%fZ")
        path = Path("evidence") / f"runtime-{stamp}.json"

    payload = sanitize(payload, api_key)
    # Do not persist malformed endpoint credentials even on configuration failure.
    if not payload["success"]:
        payload["base_url"] = "[OMITTED_ON_FAILURE]"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\nEVIDENCE_FILE={path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
