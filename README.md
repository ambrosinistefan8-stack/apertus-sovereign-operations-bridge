# Apertus Sovereign Operations Bridge

Open-source clean-room Hack Apertus Track 2B prototype for source-aware, human-controlled AI workflows.

**Public demo:** https://apertus-sovereign-operations-bridge.onrender.com

The project demonstrates a simple but important boundary:

> AI may propose work. Deterministic controls decide whether that work is safe to continue, requires human review, or must be blocked.

## Flow

`Request -> Apertus -> structured facts -> control checks -> human gate -> readback -> VERIFIED / HUMAN_REVIEW / BLOCKED`

This repository is standalone. It does not import private SPINNENNETZ-DNA code, documents, APIs, prompts, credentials, customer data, legal records, family data or private email.

## Current status

| Capability | Status |
| --- | --- |
| Clean-room implementation | READY |
| Five deterministic control scenarios | 5/5 PASS |
| Browser demo | LIVE |
| Public repository | LIVE |
| OpenAI-compatible Apertus client | READY |
| Live Apertus request/readback | VERIFIED with CSCS Apertus v1.5 70B (2026-10-03) |
| Paid compute | NOT ENABLED |

Authorized CSCS inference is configured for the hosted demo in **live mode**. The dated synthetic request/response evidence is in `evidence/live-cscs-20261003.json`. This is a prototype demonstration, not a guarantee of model accuracy or permission to execute external actions.

## What the control layer checks

- conflicting facts across sources;
- missing required information;
- embedded untrusted instructions;
- protected external actions that require human approval (including caller-observed requests that the model omits);
- separation between model proposal and authorization.

Final states:

- **VERIFIED** — no deterministic blocker detected;
- **HUMAN_REVIEW** — missing/conflicting information or protected action;
- **BLOCKED** — untrusted embedded instruction detected.

## Run locally

```bash
python -m unittest discover -s tests -v
python -m app.server
```

Open http://127.0.0.1:8080

CLI scenarios:

```bash
python -m scripts.run_demo normal
python -m scripts.run_demo conflict
python -m scripts.run_demo missing
python -m scripts.run_demo untrusted
python -m scripts.run_demo human_gate
```

Expected mock/control statuses:

- normal -> VERIFIED
- missing -> HUMAN_REVIEW
- conflict -> HUMAN_REVIEW
- untrusted -> BLOCKED
- human_gate -> HUMAN_REVIEW

## Live Apertus binding

The live client uses an OpenAI-compatible `/chat/completions` interface.

The organizer-confirmed CSCS base URL is `https://api.inference.cscs.ch/v1`. Credentials stay in the runtime secret store; they are never included in source or evidence.

```bash
export APERTUS_MODE=live
export APERTUS_BASE_URL="https://api.inference.cscs.ch/v1"
export APERTUS_API_KEY="<AUTHORIZED_SECRET>"
export APERTUS_MODEL="swiss-ai/Apertus-v1.5-8B"

python -m scripts.live_probe --scenario normal
```

For the exact final sequence and evidence requirements, see [LIVE_RUNBOOK.md](LIVE_RUNBOOK.md) and [LIVE_EVIDENCE_TEMPLATE.md](LIVE_EVIDENCE_TEMPLATE.md).

### PowerShell (5.1 or 7)

After installing Python 3.11+, set `APERTUS_API_KEY` in an authorized environment
or secret store, then run:

```powershell
powershell.exe -NoProfile -File .\scripts\ApertusAdapter.ps1 -Scenario normal -PythonExecutable python -TimeoutSeconds 120
```

The adapter defaults to `https://api.publicai.co/v1`, discovers `/models`, validates
`APERTUS_MODEL` exactly (or selects an offered Apertus 1.5 model, preferring 8B),
and calls the existing Python live probe. It returns a JSON status and a local
`evidence/runtime-<UTC_TIMESTAMP>.json` receipt. Codex is not a runtime dependency.
No live provider verification is claimed without authorized inference access.
See the runbook for configuration, exit codes and bridge invocation.

## Security

- Never commit API keys or tokens.
- `.env` is ignored.
- Runtime evidence files are ignored until manually reviewed.
- Live evidence records that authentication exists, never the credential value.
- Demo fixtures contain synthetic data only.

## Hack Apertus

Track: **Apertus Adoption — Own Project (2B)**

The project is designed around the Track 2B criteria: purposeful AI use, technical rigour, value/cost/scalability, sovereign deployability and implementation feasibility.

See [SUBMISSION.md](SUBMISSION.md), [CLEANROOM.md](CLEANROOM.md) and [SECURITY.md](SECURITY.md).
