# Technical report — live verified submission state

Project: **Apertus Sovereign Operations Bridge**  
Hackathon track: **Apertus Adoption — Own Project (2B)**  
Public demo: https://apertus-sovereign-operations-bridge.onrender.com

## Problem

Generative AI can draft answers quickly, but business users still need to know whether source information is complete, contradictory, manipulated, or subject to human approval. A fluent model response is not the same thing as an authorized business action.

## Solution

Apertus is used as the semantic document-analysis component. Its structured output is passed to an independent deterministic control layer that checks:

1. source conflicts;
2. missing required information;
3. untrusted embedded instructions;
4. protected external actions requiring explicit human approval.

The model never authorizes its own external action.

Final control states:

- **VERIFIED**
- **HUMAN_REVIEW**
- **BLOCKED**

## Architecture

`Request -> Apertus -> structured facts -> deterministic controls -> human gate -> readback -> outcome`

The model-facing layer is replaceable. The control layer is deliberately provider-independent.

## Why Apertus

Apertus provides an open Swiss model foundation and supports a path toward sovereign deployment. The project keeps the application and control logic open and auditable instead of hiding policy decisions inside a closed model prompt.

## Current evidence

- clean-room standalone repository: PASS;
- synthetic-only demo data: PASS;
- browser demo: LIVE;
- OpenAI-compatible Apertus client: IMPLEMENTED;
- deterministic control tests: **5/5 PASS**;
- public secret boundary: no credentials committed;
- live Apertus request/readback: **VERIFIED** with authorized CSCS hosted inference using `swiss-ai/Apertus-v1.5-70B`.

The hosted demo is now bound to authorized CSCS inference in live mode. Public evidence is stored in `evidence/live-cscs-20261003.json`; no credential value is recorded.

## Evaluation scenarios

1. Normal complete sources -> VERIFIED
2. Missing required fact -> HUMAN_REVIEW
3. Conflicting sources -> HUMAN_REVIEW
4. Embedded untrusted instruction -> BLOCKED
5. Protected external action -> HUMAN_REVIEW

The same five control outcomes were also exercised through the live HP → public demo → CSCS → control-readback path on 3 October 2026, with HTTP 200 responses and the expected VERIFIED / HUMAN_REVIEW / BLOCKED states.

## Track 2B criteria mapping

### Purposeful use of AI
Apertus performs semantic extraction and response preparation where language understanding is useful. Authorization and policy enforcement remain outside the model.

### Technical rigour
Structured model schema, deterministic post-model checks, source IDs, explicit outcome states, automated tests and SHA-256 input evidence.

### Value, cost and scalability
The pattern targets repetitive office/document workflows and can use the 8B model for lower-cost deployment. The control layer does not require a second model call.

### Sovereign deployability
Open-source application code, open model path, synthetic test data and no dependency on private SPINNENNETZ-DNA infrastructure. The design can be deployed on authorized Swiss-hosted or self-hosted Apertus infrastructure.

### Implementation feasibility
Standalone Python service, browser UI, CLI, Dockerfile, public hosted demo and a prepared live client.

## Live Apertus completion evidence

The live gate is complete:

`authorized CSCS endpoint -> real Apertus request -> structured parse -> deterministic control readback -> evidence -> hosted live demo`

The repository contains:

- `LIVE_RUNBOOK.md` — exact execution sequence;
- `scripts/live_probe.py` — sanitized real-request evidence runner;
- `LIVE_EVIDENCE_TEMPLATE.md` — promotion checklist.

`LIVE_APERTUS_VERIFIED` is now supported by the published live evidence and independent HP-side readback. The claim is limited to this synthetic hackathon workflow and does not imply unrestricted production autonomy.

## Limitations

- The public demo uses authorized hosted Apertus inference; model outputs remain non-deterministic.
- The live verification covers the defined synthetic hackathon scenarios, not arbitrary real customer workloads.
- Real LLM outputs are non-deterministic; the deterministic control layer is designed to detect unsafe/ambiguous outcomes rather than force a desired model result.
- This prototype prepares controlled work; it does not autonomously send email, make payments, sign contracts, change permissions or perform destructive actions.
