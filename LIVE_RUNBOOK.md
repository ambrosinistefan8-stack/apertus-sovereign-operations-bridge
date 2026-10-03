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
