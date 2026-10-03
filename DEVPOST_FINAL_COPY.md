# Devpost final copy — ready for final enrichment

Project: **Apertus Sovereign Operations Bridge**  
Track: **Apertus Adoption — Own Project (2B)**

## One-line pitch

A sovereign AI workflow that uses Apertus for document understanding, then independently checks whether the result can safely proceed, needs human review, or must be blocked.

## Inspiration

Businesses increasingly use generative AI for emails, documents and decisions, but fluent output is not the same as trustworthy execution. Real workflows contain missing information, conflicting sources, embedded instructions and actions that should never be authorized by the model itself.

We wanted to show a practical pattern for using an open Swiss model while keeping control, evidence and human responsibility outside the model.

## What it does

The prototype follows this chain:

`Request → Apertus → structured facts → deterministic control checks → human gate → readback → VERIFIED / HUMAN_REVIEW / BLOCKED`

Apertus handles semantic analysis and response preparation. A separate deterministic layer checks for:

- conflicting facts;
- missing required information;
- untrusted instructions embedded in source documents;
- protected external actions such as sending email, payments, purchases, contracts, permission changes or destructive operations.

The model can propose an action but cannot authorize it.

## How we built it

- standalone Python 3.11 service;
- OpenAI-compatible Apertus client;
- structured model-output schema with source IDs;
- deterministic post-model control layer;
- browser demo and CLI;
- Dockerfile;
- automated unit tests;
- SHA-256 evidence for workflow inputs;
- clean-room boundary that excludes private SPINNENNETZ-DNA code and data;
- live-request evidence runner that never records the API key.

## Evaluation

Five deterministic scenarios are implemented and passing:

1. complete sources → VERIFIED
2. missing fact → HUMAN_REVIEW
3. conflicting sources → HUMAN_REVIEW
4. embedded untrusted instruction → BLOCKED
5. protected external action → HUMAN_REVIEW

These tests validate the control layer independently of the language model.

## Why Apertus

Apertus gives the project an open Swiss model foundation and a credible path to sovereign deployment. The application logic and safety boundary remain inspectable instead of relying on a closed provider or a hidden prompt to enforce business policy.

## Track 2B fit

**Purposeful AI use:** language understanding is used where it adds value; authorization is kept deterministic.

**Technical rigour:** structured schema, source attribution, explicit states, automated tests, input hashes and independent controls.

**Value, cost & scalability:** the pattern targets repetitive document/office workflows and can use Apertus 8B for a lower-resource path.

**Sovereign deployability:** open-source code, open model path, synthetic public demo data and no dependency on private internal infrastructure.

**Implementation feasibility:** public repository, hosted browser demo, CLI, Dockerfile and prepared live inference integration.

## Current public evidence

Repository: https://github.com/ambrosinistefan8-stack/apertus-sovereign-operations-bridge

Demo: https://apertus-sovereign-operations-bridge.onrender.com

Control tests: PASS

Live Apertus status: **VERIFIED**

Authorized hosted inference is live against the CSCS OpenAI-compatible endpoint with `swiss-ai/Apertus-v1.5-70B`. On 3 October 2026, the project completed the full HP → public demo → CSCS → deterministic control readback path. Five out of five expected control outcomes passed with HTTP 200 responses:

1. complete sources → VERIFIED
2. missing fact → HUMAN_REVIEW
3. conflicting sources → HUMAN_REVIEW
4. embedded untrusted instruction → BLOCKED
5. protected external action → HUMAN_REVIEW

No protected external action was executed. The model proposes; the control layer decides whether the result may proceed, requires human review, or must be blocked.

Public live evidence:
https://github.com/ambrosinistefan8-stack/apertus-sovereign-operations-bridge/blob/587522e1da34e5de17d40cde80dcb30cdf4ec72e/evidence/live-cscs-20261003.json

## Final live-evidence paragraph

> LIVE APERTUS VERIFIED: On 3 October 2026, the project completed real hosted inference through the authorized CSCS endpoint using `swiss-ai/Apertus-v1.5-70B`. The response was parsed into the structured schema, passed through the independent deterministic control layer, and was verified across five control scenarios. The live evidence is published in the repository without storing credentials or private data.

## What we learned

The hardest problem is not getting an LLM to write a plausible answer. The harder problem is defining what must happen between a model answer and a real-world action. Separating semantic generation from authorization makes failures visible and testable.

## What's next

1. update the existing editable Devpost submission with the verified live evidence;
2. confirm repository, public demo and evidence links in the submission;
3. add or refresh project media if required by the current submission form;
4. perform the final jury-facing review before the 16 October 2026, 12:00 CEST deadline.
