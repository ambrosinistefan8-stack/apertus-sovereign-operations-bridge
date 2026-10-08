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

## What we learned

The hardest problem is not getting an LLM to write a plausible answer. The harder problem is defining what must happen between a model answer and a real-world action. Separating semantic generation from authorization makes failures visible and testable.

## Engineering update - 8 October 2026

The wider SPINNENNETZ-DNA development environment now provides additional, bounded execution evidence:

- **Phone-to-PC communication:** a phone ChatGPT request reached the HP worker and its result was read back; communication was checked again after the phone session restarted.
- **Physical output:** one PC-initiated and one phone-initiated single-page print completed. The owner confirmed receiving both pages. Rechecking the second job did not submit another print.
- **Native Office workflows:** five phone-initiated jobs passed: create a Word document, append text into a new Word copy, create an Excel workbook, change cells in a new Excel copy, and create a PowerPoint presentation. Each output was saved, reopened in its native application, and checked. The two source documents remained unchanged.
- **Bounded execution:** these five Office jobs used existing direct worker actions without invoking a coding agent. Receipts, content readback and file hashes were checked; the actions do not provide unrestricted desktop control.

These are maintainer-verified results from a separate private integration environment. They support the engineering pattern of explicit user intent, bounded execution and target-state verification. They are **not** evidence that Apertus or the public demo controls Microsoft Office or a printer. The public clean-room prototype and its five published live Apertus scenarios remain independently reproducible and separate from this integration work.

General mission recovery, automatic cross-system handoff, closed-lid operation and remote wake remain unverified. The public prototype does not execute protected external actions. Cost/scaling benchmarks, the 8B/70B comparison and a fully self-hosted Swiss deployment remain future work.

## What's next for Apertus Sovereign Operations Bridge

Next steps are to benchmark Apertus 8B and 70B for different workload/cost profiles, add more synthetic SME workflows, strengthen source-level evaluation, and test a fully self-hosted Swiss deployment path.

The goal is not unrestricted autonomy. The goal is a reusable pattern for **controlled autonomy with evidence and human responsibility**.

## Additional explainer: SPINNENNETZ-DNA

[So funktioniert SPINNENNETZ-DNA – Architektur und geprüfter Ablauf](https://scrimba.com/explain/guide0fr35d7gp?fullscreen=1)

German narrated, animated explanation (2 minutes 26 seconds) of the broader SPINNENNETZ-DNA architecture, the documented phone-to-HP test workflow, user approval and result verification. This is an explanatory animation, not a live screen recording or an additional execution test. It distinguishes demonstrated workflows from open capabilities. The short promotional video remains the main video above.
