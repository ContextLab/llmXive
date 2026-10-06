# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence was provided showing that the directories `data/raw`, `data/processed`, `data/results`, `code`, `tests/unit`, `tests/integration`, `specs/contracts`, and `state` exist under `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/`. Without confirming the presence of this project structure, the task requirement is not satisfied.
- **T002** — The required file `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/requirements.txt` does not exist, and the existing `requirements.txt` files contain only package lists, not the full specification excerpt the task expects. The task’s core requirement is therefore unmet.
- **T003a** — declared artifact(s) missing/empty/invalid: ruff.toml
- **T007c** — The `pilot_validation.py` script is incomplete (the shown code truncates before finishing the precision calculation and never computes a correlation or writes `pilot_correlation.json`). The provided `regularity_scores.csv` contains only 5 rows, not the required 20‑sample size, and the expected output file `data/processed/pilot_correlation.json` is missing. These gaps mean the task’s requirements are not satisfied.
