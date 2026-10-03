# Live Apertus runbook

This runbook is the final technical handoff from the verified mock/control prototype to a real Apertus inference run.

## Current gate

The application, deterministic control layer, browser demo and five local control scenarios are implemented. A real Apertus run remains blocked only by authorized hosted inference access.

Public Swiss AI repositories document an OpenAI-compatible CSCS endpoint at:

`https://api.swissai.svc.cscs.ch/v1`

Use that endpoint only when the Hack Apertus organizers or the authorized access instructions confirm that the provided credential is valid for it. Do not guess, scrape or bypass access controls.

## Security rules

- Never commit an API key, token, password or one-time code.
- Keep credentials only in the deployment/runtime secret store or local environment.
- `.env` and generated runtime evidence are git-ignored.
- Evidence records whether authentication was configured, but never records the credential value.
- Use synthetic demo documents only. Do not upload private SPINNENNETZ-DNA, customer, legal, family or email data.

## 1. Local preflight

```bash
python -m unittest discover -s tests -v
```

Expected: all deterministic tests pass.

## 2. Bind authorized live access

```bash
export APERTUS_MODE=live
export APERTUS_BASE_URL="https://api.swissai.svc.cscs.ch/v1"
export APERTUS_API_KEY="<SET_IN_SECRET_STORE_OR_SHELL>"
export APERTUS_MODEL="swiss-ai/Apertus-v1.5-8B"
```

If the organizers provide a different endpoint or model identifier, their instructions take precedence.

## 3. Run the first real request

```bash
python -m scripts.live_probe --scenario normal
```

The probe performs a real model request, then sends the structured result through the independent deterministic control layer.

## 4. Run the full synthetic control set

```bash
python -m scripts.live_probe --all
```

The five scenarios are:

- normal
- missing
- conflict
- untrusted
- human_gate

A real model is non-deterministic, so these runs are evidence of end-to-end behavior, not a promise that every model response will reproduce the mock status exactly. Any discrepancy must be recorded, not hidden.

## 5. Evidence

By default the live probe writes a timestamped JSON file under `evidence/runtime-*.json`. These files are intentionally ignored by git until reviewed.

Evidence contains:

- UTC timestamp
- endpoint base URL
- model identifier
- whether authentication was configured
- scenario
- model output
- deterministic control result
- input SHA-256
- elapsed time

It does not contain the API key.

## 6. Promotion rule

Do not change the project status to `LIVE_APERTUS_VERIFIED` until all of the following are true:

1. authorized inference access was used;
2. a real Apertus request returned successfully;
3. the response parsed into the expected structured schema;
4. the deterministic control layer completed;
5. the result and evidence were independently read back;
6. no secret or private data was exposed.

After that, update README, SUBMISSION, the hosted demo configuration and the Devpost entry with the verified evidence.

## PowerShell adapter

`scripts/ApertusAdapter.ps1` is a standalone PowerShell 5.1/7 entrypoint. It uses
the existing `scripts.live_probe` and `OpenAICompatibleApertusClient`; it does not
implement a second inference client or control layer. Python 3.11+ must remain
installed. Codex is needed only for engineering, never for this execution path.

Configuration is read from Process environment, then User environment for each
unset value. The adapter does not persist environment changes or read `.env`.

| Variable | Behavior |
| --- | --- |
| `APERTUS_API_KEY` | Required; authorized secret, never printed or stored in evidence |
| `APERTUS_BASE_URL` | Defaults to `https://api.publicai.co/v1`; trailing slashes removed; HTTPS required except loopback tests; URL credentials/query/fragment rejected |
| `APERTUS_MODEL` | Canonical model; exact, case-sensitive match against discovery |
| `APERTUS_MODEL_ID` | Compatibility fallback only when canonical model is unset; removed from child environment |
| `APERTUS_USER_AGENT` | Defaults to `SPINNENNETZ-DNA/1.0`; used for discovery and inference |

Use only a base URL authorized for the supplied key. Set an absolute Python path
if `python` resolves to the Windows Store launcher rather than an installed runtime.

```powershell
# Credentials must already exist in the authorized environment/secret store.
.\scripts\ApertusAdapter.ps1 -DiscoveryOnly -PythonExecutable python
.\scripts\ApertusAdapter.ps1 -Scenario normal -Prompt 'Prepare the correct customer response.' -TimeoutSeconds 120 -PythonExecutable python
```

Discovery reads `GET /models` before inference. With no configured model it selects
an offered Apertus 1.5 ID, preferring 8B; it never invents an ID. Unsupported or
empty discovery fails closed. Discovery-only success is not a live inference proof.
Without `-DiscoveryOnly`, the same client first sends a connectivity prompt, then
runs the selected synthetic scenario through the existing control layer. Response
model IDs must match discovery; connectivity accepts additional response text.
`--prompt`, `--timeout` and `--connectivity` are also available on the Python probe.

The adapter outputs one JSON completion object with the absolute `evidence_file`
path. Existing Python evidence, transport metadata and control readback are retained
under `runtime` in that receipt. Child stdout/stderr are drained but not forwarded;
failure messages are fixed text and credentials echoed by a provider are redacted
before persistence. Do not put real keys in commands, fixtures, logs or documents.

| Exit | Meaning |
| --- | --- |
| 0 | Completed successfully; inspect `control_status` and `live_apertus_e2e` separately |
| 2 | Missing credential or invalid configuration |
| 3 | Discovery authentication error (401/403) |
| 4 | Discovery endpoint/model missing or invalid |
| 5 | Discovery rate limit (429) |
| 6 | Discovery transient provider failure (5xx) |
| 7 | Discovery or child timeout |
| 8 | Adapter execution/readback failure |
| Other child failure | Nonzero child exit code preserved verbatim, including 1; inspect `error_class` |

Discovery retries only 429/5xx, at most three attempts. `Retry-After` is respected;
if it exceeds the remaining retry budget, the adapter stops without an early retry.
401/403/404 are not retried. Inference is not automatically retried. Timeout applies
to each HTTP request and separately bounds the complete Python child process.

A bridge can run the same command with `-NoProfile -NonInteractive -File`, capture
the exit code and parse stdout JSON, then read the local evidence file. Where local
policy permits, `-ExecutionPolicy Bypass` is a process-only invocation option;
the adapter never changes persistent execution policy. Existing bridge permissions
and human gates still apply. No bridge configuration or cloud/Drive dependency is
installed by this public project. Internal synchronization can ingest the reviewed
receipt separately.

Tests use a loopback HTTP fixture and runtime-generated authentication sentinels:

```powershell
# Optional: choose the other installed shell to exercise both PowerShell versions.
$env:APERTUS_TEST_POWERSHELL = (Get-Command powershell.exe).Source
python -m unittest discover -s tests -p test_powershell_adapter.py -v
```

Loopback tests always report `NOT_VERIFIED_TEST_ENDPOINT`; missing authorized
access remains `LIVE_APERTUS_E2E=PENDING_AUTHORIZED_ACCESS`. A real normal workflow
can report `VERIFIED` only after successful discovered-model HTTP responses,
nonempty responses and a `VERIFIED` control result. Human review and blocked
results are preserved and never authorize protected effects.
