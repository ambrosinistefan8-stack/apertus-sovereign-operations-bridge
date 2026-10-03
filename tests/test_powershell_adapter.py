"""Loopback adapter tests: no provider credentials, paid requests or Codex runtime.

Each test generates an in-memory authentication sentinel; no credential fixture is
stored. APERTUS_TEST_POWERSHELL selects PowerShell 5.1 or 7 explicitly.
"""
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
SHELL = os.environ.get("APERTUS_TEST_POWERSHELL") or shutil.which("pwsh") or shutil.which("powershell")
MODEL = "test-provider/Apertus-1.5-8B"


@unittest.skipUnless(SHELL, "PowerShell is required for adapter process tests")
class PowerShellAdapterTests(unittest.TestCase):
    def setUp(self):
        (ROOT / "evidence").mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix="runtime-adapter test-", dir=ROOT / "evidence")
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT / "app", self.root / "app", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "scripts", self.root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        self.key = secrets.token_urlsafe(32)
        self.get_statuses = [200]
        self.post_status = 200
        self.models = ["test-provider/Apertus-1.5-70B", MODEL]
        self.requests = []
        self.echo_secret = False
        self.response_model = MODEL
        self.invalid_discovery = False
        self.retry_after = "0"
        self.requested_actions = ["draft_response"]
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, status, value):
                body = json.dumps(value).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                if status == 429:
                    self.send_header("Retry-After", owner.retry_after)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                owner.requests.append(("GET", self.path, dict(self.headers), None, time.monotonic()))
                status = owner.get_statuses[0]
                if len(owner.get_statuses) > 1:
                    owner.get_statuses.pop(0)
                payload = {"data": [{"id": m} for m in owner.models]}
                if owner.invalid_discovery:
                    payload = {"unexpected": True}
                if status != 200:
                    payload = {"error": owner.key}  # Hostile body must never reach evidence/logs.
                self.reply(status, payload)

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                owner.requests.append(("POST", self.path, dict(self.headers), body, time.monotonic()))
                content = "APERTUS_E2E_PASS plus extra text"
                if sum(r[0] == "POST" for r in owner.requests) > 1:
                    content = json.dumps({
                        "facts": [{"key": "product", "value": "Demo", "source_id": "product"},
                                  {"key": "price_chf", "value": "490", "source_id": "product"},
                                  {"key": "delivery_days", "value": "3", "source_id": "policy"}],
                        "missing_required": [], "untrusted_instructions": [],
                        "proposed_response": owner.key if owner.echo_secret else "Synthetic draft.",
                        "requested_actions": owner.requested_actions,
                    })
                self.reply(owner.post_status, {"model": owner.response_model,
                    "choices": [{"message": {"content": content}}],
                    "usage": {"prompt_tokens": 12, "completion_tokens": 20, "total_tokens": 32},
                    "error": owner.key if owner.post_status != 200 else None})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.tmp.cleanup()

    def run_adapter(self, extra=(), settings=None, missing_key=False, timeout=10, no_codex=False):
        env = {k: v for k, v in os.environ.items() if not k.startswith("APERTUS_")}
        env.update(APERTUS_API_KEY=self.key,
                   APERTUS_BASE_URL=f"http://127.0.0.1:{self.server.server_port}/v1///")
        if missing_key:
            env.pop("APERTUS_API_KEY")
        env.update(settings or {})
        if no_codex:
            env = {k: v for k, v in env.items() if k.lower() != "path" and not k.startswith("CODEX")}
            env["PATH"] = os.path.dirname(sys.executable) + os.pathsep + os.path.join(os.environ.get("SystemRoot", "/usr"), "System32")
            self.assertIsNone(shutil.which("codex", path=env["PATH"]))
        cmd = [SHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File",
               str(self.root / "scripts" / "ApertusAdapter.ps1"),
               "-PythonExecutable", sys.executable, "-TimeoutSeconds", str(timeout), *extra]
        result = subprocess.run(cmd, env=env, capture_output=True, encoding="utf-8", timeout=35)
        self.assertNotIn(self.key, result.stdout)
        self.assertNotIn(self.key, result.stderr)
        summary = json.loads(result.stdout.lstrip("\ufeff"))
        path = Path(summary["evidence_file"])
        self.assertEqual(path.parent, self.root / "evidence")
        self.assertTrue(path.name.startswith("runtime-"))
        raw = path.read_text(encoding="utf-8")
        self.assertNotIn(self.key, raw)
        evidence = json.loads(raw)
        self.assertEqual(result.returncode, evidence["exit_code"])
        self.assertEqual(summary["codex_runtime_dependency"], "NONE")
        return result, summary, evidence

    def test_missing_key_creates_failure_receipt_without_network(self):
        result, summary, _ = self.run_adapter(missing_key=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(summary["error_class"], "MISSING_API_KEY")
        self.assertEqual(self.requests, [])

    def test_invalid_model_fails_exact_validation(self):
        result, summary, _ = self.run_adapter(settings={"APERTUS_MODEL": MODEL.lower()})
        self.assertEqual(result.returncode, 4)
        self.assertEqual(summary["error_class"], "ENDPOINT_OR_MODEL_NOT_FOUND")
        self.assertEqual(len(self.requests), 1)

    def test_discovery_prefers_8b_and_calls_existing_probe(self):
        result, summary, evidence = self.run_adapter(extra=("-Prompt", 'Synthetic "quoted" task with unicode ä'))
        self.assertEqual(result.returncode, 0, summary)
        self.assertEqual(summary["model_used"], MODEL)
        self.assertEqual(summary["control_status"], "VERIFIED")
        self.assertEqual(summary["live_apertus_e2e"], "NOT_VERIFIED_TEST_ENDPOINT")
        self.assertEqual([r[0] for r in self.requests], ["GET", "POST", "POST"])
        self.assertEqual(self.requests[-1][1], "/v1/chat/completions")
        self.assertIn('Synthetic "quoted" task', self.requests[-1][3]["messages"][-1]["content"].replace('\\"', '"'))
        self.assertEqual(evidence["total_tokens"], 32)
        self.assertEqual(evidence["runtime"]["mode"], "live")
        for request in self.requests:
            self.assertEqual(request[2]["Authorization"], "Bearer " + self.key)
            self.assertEqual(request[2]["User-Agent"], "SPINNENNETZ-DNA/1.0")

    def test_model_id_alias_and_user_agent(self):
        result, summary, _ = self.run_adapter(extra=("-DiscoveryOnly",), settings={"APERTUS_MODEL_ID": MODEL, "APERTUS_USER_AGENT": "AdapterTest/1.0"})
        self.assertEqual(result.returncode, 0, summary)
        self.assertEqual(summary["model_used"], MODEL)
        self.assertEqual(self.requests[0][2]["User-Agent"], "AdapterTest/1.0")
        self.assertEqual(len(self.requests), 1)
        self.assertNotEqual(summary["live_apertus_e2e"], "VERIFIED")

    def test_canonical_model_overrides_alias(self):
        result, _, _ = self.run_adapter(extra=("-DiscoveryOnly",), settings={"APERTUS_MODEL": MODEL, "APERTUS_MODEL_ID": "invalid"})
        self.assertEqual(result.returncode, 0)

    def test_discovery_empty_schema_fails(self):
        self.invalid_discovery = True
        result, _, _ = self.run_adapter()
        self.assertEqual(result.returncode, 4)

    def test_authentication_no_retry_or_secret_echo(self):
        self.get_statuses = [401]
        result, summary, evidence = self.run_adapter()
        self.assertEqual(result.returncode, 3)
        self.assertEqual(summary["error_class"], "AUTHENTICATION_ERROR")
        self.assertEqual(evidence["http_status"], 401)
        self.assertEqual(len(self.requests), 1)

    def test_endpoint_not_found_no_retry(self):
        self.get_statuses = [404]
        result, _, _ = self.run_adapter()
        self.assertEqual(result.returncode, 4)
        self.assertEqual(len(self.requests), 1)

    def test_rate_limit_retry_after_then_success(self):
        self.get_statuses = [429, 200]
        self.retry_after = "2"
        result, _, _ = self.run_adapter(extra=("-DiscoveryOnly",))
        self.assertEqual(result.returncode, 0)
        self.assertGreaterEqual(self.requests[1][4] - self.requests[0][4], 1.9)

    def test_rate_limit_respects_budget_without_early_retry(self):
        self.get_statuses = [429]
        self.retry_after = "120"
        result, summary, _ = self.run_adapter()
        self.assertEqual(result.returncode, 5)
        self.assertEqual(summary["error_class"], "RATE_LIMITED")
        self.assertEqual(len(self.requests), 1)

    def test_provider_failure_has_three_attempt_limit(self):
        self.get_statuses = [503]
        result, summary, _ = self.run_adapter()
        self.assertEqual(result.returncode, 6)
        self.assertEqual(summary["error_class"], "PROVIDER_TRANSIENT_ERROR")
        self.assertEqual(len(self.requests), 3)

    def test_child_exit_code_preserved_and_streams_suppressed(self):
        (self.root / "scripts" / "live_probe.py").write_text(
            "import os,sys\nprint(os.environ['APERTUS_API_KEY'])\n"
            "print(os.environ['APERTUS_API_KEY'],file=sys.stderr)\nraise SystemExit(23)\n", encoding="utf-8")
        result, summary, _ = self.run_adapter()
        self.assertEqual(result.returncode, 23)
        self.assertEqual(summary["error_class"], "EXECUTION_ERROR")

    def test_child_timeout(self):
        (self.root / "scripts" / "live_probe.py").write_text("import time\ntime.sleep(10)\n", encoding="utf-8")
        result, summary, _ = self.run_adapter(timeout=1)
        self.assertEqual(result.returncode, 7)
        self.assertEqual(summary["error_class"], "TIMEOUT")

    def test_failed_child_invalid_evidence_preserves_exit(self):
        (self.root / "scripts" / "live_probe.py").write_text(
            "import sys\nfrom pathlib import Path\np=Path(sys.argv[sys.argv.index('--output')+1])\n"
            "p.parent.mkdir(exist_ok=True)\np.write_text('not json')\nraise SystemExit(23)\n", encoding="utf-8")
        result, summary, _ = self.run_adapter()
        self.assertEqual(result.returncode, 23)
        self.assertEqual(summary["error_class"], "EXECUTION_ERROR")

    def test_power_shell_runtime_without_codex_on_path(self):
        result, summary, evidence = self.run_adapter(no_codex=True)
        self.assertEqual(result.returncode, 0, summary)
        self.assertEqual(summary["control_status"], "VERIFIED")
        self.assertTrue(evidence["runtime"]["success"])

    def test_provider_echo_is_redacted_before_persistence(self):
        self.echo_secret = True
        result, summary, evidence = self.run_adapter()
        self.assertEqual(result.returncode, 0, summary)
        self.assertEqual(evidence["runtime"]["results"][0]["model_output"]["proposed_response"], "[REDACTED]")

    def test_child_http_error_mapping_and_exit(self):
        self.post_status = 403
        result, summary, evidence = self.run_adapter()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(summary["error_class"], "AUTHENTICATION_ERROR")
        self.assertEqual(evidence["http_status"], 403)

    def test_response_model_must_match_discovery(self):
        self.response_model = "unrelated-model"
        result, summary, _ = self.run_adapter()
        self.assertEqual(result.returncode, 8)
        self.assertNotEqual(summary["live_apertus_e2e"], "VERIFIED")

    def test_human_gate_is_preserved(self):
        self.requested_actions = ["send_email"]
        result, summary, _ = self.run_adapter(extra=("-Scenario", "human_gate"))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(summary["control_status"], "HUMAN_REVIEW")
        self.assertNotEqual(summary["live_apertus_e2e"], "VERIFIED")

    def test_url_credentials_are_rejected_without_echo(self):
        result, summary, _ = self.run_adapter(settings={"APERTUS_BASE_URL": "https://example.invalid/v1?key=" + self.key})
        self.assertEqual(result.returncode, 2)
        self.assertEqual(summary["error_class"], "CONFIGURATION_ERROR")
        self.assertEqual(self.requests, [])


if __name__ == "__main__":
    unittest.main()
