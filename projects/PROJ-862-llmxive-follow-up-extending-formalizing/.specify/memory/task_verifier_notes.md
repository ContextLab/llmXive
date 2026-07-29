# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T026** — The repository lacks a `requirements.txt` file, so the required explicit pinning of the `sentence-transformers` version is not present. Without this file the task’s reproducibility requirement is unmet, regardless of the partial implementation of `check_input_drift` and the existence of `validity_log.csv`. The next implementer must add a `requirements.txt` that pins the `sentence-transformers` library (e.g., `sentence-transformers==2.2.2`).
