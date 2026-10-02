# Technical report draft

## Problem
Generative AI can draft answers quickly, but business users still need to know whether source information is complete, contradictory, manipulated, or subject to human approval.

## Solution
Apertus performs semantic document analysis. A deterministic control layer independently checks source conflicts, missing required information, untrusted embedded instructions, and protected actions.

Final status:
- VERIFIED
- HUMAN_REVIEW
- BLOCKED

## Why Apertus
Open Swiss model foundation with a path toward sovereign deployment. The control layer is provider-independent and the live client uses an OpenAI-compatible interface.

## Evaluation
1. Normal -> VERIFIED
2. Missing fact -> HUMAN_REVIEW
3. Conflicting sources -> HUMAN_REVIEW
4. Embedded malicious instruction -> BLOCKED
5. Protected external action -> HUMAN_REVIEW

## Live Apertus step
The client is implemented. Final evidence must add a real Apertus request/response after official inference access is bound.
