# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`data/raw/`, `data/processed/`, `data/explanation_tiers/`, `data/simulation_results/`, `code/`, `tests/`, `docs/`) being created is provided; the implementer did not supply a directory listing or any files confirming the structure exists.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) are present in the provided evidence, so the required setup for ruff/flake8 and black is missing. The task’s deliverable is not demonstrated.
- **T005** — The repository lacks the required `data/processed/golden_set.csv` file, and the provided `code/load_data.py` does not contain any logic to verify the presence of that CSV, check for an `expert_load_score` (or self‑report) column, or raise a specific error when it is missing. The task’s validation step is therefore not implemented.
- **T006a** — declared artifact(s) missing/empty/invalid: data/processed/golden_set.csv
- **T006b** — The repository contains a partially‑implemented `code/create_golden_set.py`, but the script is truncated (the `apply_expert_rubric` function is incomplete) and lacks any code that writes the generated data to `data/processed/golden_set.csv`. Consequently the required output file does not exist. The task’s requirement to actually create and save a synthetic expert‑labeled Golden Set is not fulfilled.
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/golden_set.csv
