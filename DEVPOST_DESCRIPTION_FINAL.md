## Inspiration

Most AI assistants stop after producing a fluent answer. Real business workflows need something more: source awareness, explicit approval boundaries, and evidence of what was actually allowed, blocked, or sent for human review.

We wanted to demonstrate a practical pattern for using an open Swiss language model in real work without letting the model authorize its own external actions.

## What it does

**Apertus Sovereign Operations Bridge** turns a business request and a small set of synthetic documents into controlled, auditable work.

The flow is:

`Request → Apertus → structured facts → deterministic control checks → human gate → readback → VERIFIED / HUMAN_REVIEW / BLOCKED`

Apertus performs semantic analysis and prepares structured output. A separate deterministic layer then checks for:

- missing required information;
- conflicting facts between sources;
- untrusted instructions embedded in source documents;
- protected external actions such as sending email, payments, purchases, contracts, permission changes, or destructive operations.

The model can propose an action, but it cannot authorize it.

## Why Apertus

Apertus gives the project an open Swiss model foundation and a credible path toward sovereign deployment. The application logic and safety boundary remain inspectable instead of relying on a closed provider or a hidden prompt to enforce business policy.

For Track 2B, the project demonstrates Apertus as a useful component inside a controlled workflow rather than as another standalone chatbot.

## How we built it

The hackathon output is a standalone clean-room open-source prototype, separated from private SPINNENNETZ-DNA code and data.

The implementation includes:

- Python 3.11 service;
- OpenAI-compatible client for authorized CSCS hosted inference;
- `swiss-ai/Apertus-v1.5-70B`;
- structured model-output schema with source IDs;
- deterministic post-model control layer;
- browser demo and CLI;
- Dockerfile;
- automated unit tests;
- SHA-256 evidence for workflow inputs;
- sanitized live-request evidence that never records the API key.

Public repository:
https://github.com/ambrosinistefan8-stack/apertus-sovereign-operations-bridge

Live demo:
https://apertus-sovereign-operations-bridge.onrender.com

Live evidence:
https://github.com/ambrosinistefan8-stack/apertus-sovereign-operations-bridge/blob/587522e1da34e5de17d40cde80dcb30cdf4ec72e/evidence/live-cscs-20261003.json

## Challenges we ran into

The main challenge was separating language-model intelligence from authorization. A model can generate a convincing answer even when information is incomplete or conflicting, so the control boundary had to remain outside the model.

A second challenge was live hosted inference. We prepared the integration and evidence path before authorized access was available, then bound the official CSCS endpoint without exposing the credential. We also had to keep mock/control testing clearly separated from real live-model evidence.

## Accomplishments that we're proud of

**LIVE APERTUS VERIFIED — 3 October 2026.**

The complete HP → public demo → CSCS → deterministic control-readback path was exercised with authorized hosted inference using `swiss-ai/Apertus-v1.5-70B`.

Five out of five expected scenarios returned HTTP 200 and the intended control state:

1. complete sources → **VERIFIED**
2. missing fact → **HUMAN_REVIEW**
3. conflicting sources → **HUMAN_REVIEW**
4. embedded untrusted instruction → **BLOCKED**
5. protected external action → **HUMAN_REVIEW**

No protected external action was executed.

The project now has a public repository, live hosted demo, reproducible tests, and published live evidence without credentials or private data.

## What we learned

The hardest part is not getting an LLM to write a plausible answer. The harder engineering problem is defining what must happen between a model answer and a real-world action.

Separating semantic generation from deterministic authorization makes uncertainty, policy boundaries, and failures visible and testable.

## How the architecture evolved during the hackathon

Since the first submission, the engineering work has validated the same control pattern at a broader agentic-operations level:

`intent → governed mission → Apertus semantic work → deterministic authorization → bounded execution → target-state readback → evidence`

The hackathon repository deliberately remains a standalone clean-room implementation. It does not import private SPINNENNETZ-DNA code, data, credentials or internal APIs. The broader system work is relevant as engineering validation: authorization stays outside the model, external effects remain gated, successful writes require independent readback, evidence is attached to runs, and recovery avoids blindly replaying unknown effects.

This positions Apertus Sovereign Operations Bridge as a compact open reference implementation for **sovereign controlled-agent workflows**, not merely a conversational demo.

## What's next for Apertus Sovereign Operations Bridge

Next steps are to benchmark Apertus 8B and 70B for different workload/cost profiles, add more synthetic SME workflows, strengthen source-level evaluation, and test a fully self-hosted Swiss deployment path.

The goal is not unrestricted autonomy. The goal is a reusable pattern for **controlled autonomy with evidence and human responsibility**.
