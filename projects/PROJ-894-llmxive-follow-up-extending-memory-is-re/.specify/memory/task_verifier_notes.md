# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T040** — The repository contains the `code/data_loader.py` script, but the required audit artifact `data/audit/audit_report.json` is missing, and there is no evidence that the script was run under a mocked `ConnectionError`, that it exited with a non‑zero code, or that synthetic files were checked. The task’s core verification and report generation steps have not been provided.
- **T041** — The required artifact `data/audit/streaming_log.json` is absent, and there is no evidence that `code/runner.py` was run with `streaming=True` or that memory usage was monitored. Without the log file, the task’s validation requirement is not satisfied.
