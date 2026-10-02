# Apertus Sovereign Operations Bridge

Open-source clean-room Hack Apertus prototype for source-aware, human-controlled AI workflows.

Flow:

`Request -> Apertus -> structured facts -> control checks -> human gate -> readback -> VERIFIED / HUMAN_REVIEW / BLOCKED`

This folder is standalone and must not import private SPINNENNETZ-DNA code, documents, APIs, prompts, credentials, or customer data.

## Status
- Clean-room code: implemented
- Five control scenarios: implemented/tested
- Browser demo: implemented
- OpenAI-compatible Apertus client: implemented
- Live Apertus inference: pending official hackathon/model access
- Paid compute: not enabled

## Run
```bash
python -m unittest discover -s tests -v
python -m app.server
```

Open http://127.0.0.1:8080

CLI:
```bash
python -m scripts.run_demo normal
python -m scripts.run_demo conflict
python -m scripts.run_demo missing
python -m scripts.run_demo untrusted
python -m scripts.run_demo human_gate
```

Live endpoint:
```bash
export APERTUS_MODE=live
export APERTUS_BASE_URL="https://YOUR-ENDPOINT/v1"
export APERTUS_API_KEY="..."
export APERTUS_MODEL="swiss-ai/Apertus-v1.5-8B"
python -m app.server
```

Expected statuses:
- normal -> VERIFIED
- missing -> HUMAN_REVIEW
- conflict -> HUMAN_REVIEW
- untrusted -> BLOCKED
- human_gate -> HUMAN_REVIEW

See CLEANROOM.md and SUBMISSION.md.

