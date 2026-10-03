from __future__ import annotations

import argparse
import json
import os
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


def run_scenario(client: OpenAICompatibleApertusClient, scenario: str) -> dict:
    result = run_workflow(
        client,
        TASK,
        scenario_documents(scenario),
        REQUIRED_FIELDS,
    )
    return {
        "scenario": scenario,
        "status": result["status"],
        "model_output": result["model_output"],
        "control": result["control"],
        "evidence": result["evidence"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a real Apertus request and capture sanitized end-to-end evidence."
    )
    parser.add_argument("--scenario", choices=SCENARIOS, default="normal")
    parser.add_argument("--all", action="store_true", help="Run all five synthetic control scenarios.")
    parser.add_argument(
        "--output",
        help="Optional evidence JSON path. Defaults to evidence/runtime-<timestamp>.json.",
    )
    args = parser.parse_args()

    base_url = _safe_endpoint(os.environ.get("APERTUS_BASE_URL", ""))
    api_key = os.environ.get("APERTUS_API_KEY", "")
    model = os.environ.get("APERTUS_MODEL", "swiss-ai/Apertus-v1.5-8B")

    if not base_url:
        raise SystemExit("APERTUS_BASE_URL is required.")
    if not api_key:
        raise SystemExit("APERTUS_API_KEY is required for the authorized hosted live run.")

    client = OpenAICompatibleApertusClient(
        base_url=base_url,
        api_key=api_key,
        model=model,
    )

    scenarios = SCENARIOS if args.all else (args.scenario,)
    observed_at = datetime.now(timezone.utc)
    results = [run_scenario(client, scenario) for scenario in scenarios]

    payload = {
        "evidence_version": 1,
        "observed_at_utc": observed_at.isoformat(),
        "mode": "live",
        "base_url": base_url,
        "model": model,
        "authentication_configured": True,
        "credential_value_recorded": False,
        "synthetic_data_only": True,
        "results": results,
    }

    if args.output:
        path = Path(args.output)
    else:
        stamp = observed_at.strftime("%Y%m%dT%H%M%SZ")
        path = Path("evidence") / f"runtime-{stamp}.json"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"\nEVIDENCE_FILE={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
