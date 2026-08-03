# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T061** — The provided `src/environment/runner.py` does not contain any code that checks for the existence of `data/processed/empirical_results.json` or enforces ordering of producer vs. consumer tasks, and the required `empirical_results.json` file is absent. Consequently, the explicit data‑flow dependency check and the runtime assertion demanded by the task are not present.
