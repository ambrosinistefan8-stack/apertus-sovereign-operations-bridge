# Track 2B - Apertus Sovereign Operations Bridge

The judge package for the existing clean-room prototype. The implementation was
started during Hack Apertus in October 2026. This directory follows the current
Track 2B layout; the existing root deployment is retained for compatibility.

- Technical report: [technical_report.md](technical_report.md)
- Report PDF: [SPINNENNETZ-DNA_Report.pdf](SPINNENNETZ-DNA_Report.pdf)
- Runtime code: `src/`; synthetic data: `data/`; supporting notes: `docs/`
- Published live evidence: [CSCS 70B, 3 October](../evidence/live-cscs-20261003.json)
- Official requirements: https://github.com/HackApertus/project-template/tree/main/track_2b

## Run for judges

Requirements: Docker and Make. Supply an authorized Apertus endpoint and model
through the official environment names; credentials must remain in the environment.

```sh
export LLM_NAME=swiss-ai/Apertus-v1.5-70B
export LLM_BASE_URL=https://api.inference.cscs.ch/v1
# Set LLM_API_KEY through your authorized secret environment.
make run
```

Open http://127.0.0.1:8080 and run the five scenarios. `make run` defaults to live
mode and fails on missing model/endpoint configuration; it never silently falls
back to mock inference. `make demo` explicitly runs the offline deterministic
control demonstration, which is not a live Apertus result. Root `make run` forwards
here. Choose a free port with `make run PORT=8081`.

Target deployment: on-premise application plus an operator-managed Apertus
OpenAI-compatible inference endpoint. Model hosting is an external prerequisite;
model weights, GPU serving and hardware sizing are not bundled. The public Render
demo using CSCS inference is not proof that the whole stack resides in Switzerland.

The code in `src/app` and `src/static` is a byte-for-byte packaging snapshot of the
public root implementation, checked by tests. `scripts/sync_judge_package.py`
refreshes this snapshot after root changes. No private bridge code is included.

The separate official submission portal is https://hackapertus.ch/online-hack/submissions.
Devpost's submitted badge does not establish receipt by that portal. The technical
package update does not create a second submission or accept new terms.
