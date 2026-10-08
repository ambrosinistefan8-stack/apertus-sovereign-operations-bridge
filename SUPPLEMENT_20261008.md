## Engineering update - 8 October 2026

The wider SPINNENNETZ-DNA development environment now provides additional, bounded execution evidence:

- **Phone-to-PC communication:** a phone ChatGPT request reached the HP worker and its result was read back; communication was checked again after the phone session restarted.
- **Physical output:** one PC-initiated and one phone-initiated single-page print completed. The owner confirmed receiving both pages. Rechecking the second job did not submit another print.
- **Native Office workflows:** five phone-initiated jobs passed: create a Word document, append text into a new Word copy, create an Excel workbook, change cells in a new Excel copy, and create a PowerPoint presentation. Each output was saved, reopened in its native application, and checked. The two source documents remained unchanged.
- **Bounded execution:** these five Office jobs used existing direct worker actions without invoking a coding agent. Receipts, content readback and file hashes were checked; the actions do not provide unrestricted desktop control.

These are maintainer-verified results from a separate private integration environment. They support the engineering pattern of explicit user intent, bounded execution and target-state verification. They are **not** evidence that Apertus or the public demo controls Microsoft Office or a printer. The public clean-room prototype and its five published live Apertus scenarios remain independently reproducible and separate from this integration work.

General mission recovery, automatic cross-system handoff, closed-lid operation and remote wake remain unverified. The public prototype does not execute protected external actions. Cost/scaling benchmarks, the 8B/70B comparison and a fully self-hosted Swiss deployment remain future work.
