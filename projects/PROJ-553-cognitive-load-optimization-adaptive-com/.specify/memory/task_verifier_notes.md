# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`data/raw/`, `data/processed/`, `data/explanation_tiers/`, `data/simulation_results/`, `code/`, `tests/`, `docs/`) being created is provided; the implementer did not supply a directory listing or any files confirming the structure exists.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) are present in the provided evidence, so the required setup for ruff/flake8 and black is missing. The task’s deliverable is not demonstrated.
- **T005** — The repository does not contain `data/processed/golden_set.csv`, and the shown portion of `code/load_data.py` contains no logic that checks for this file, verifies an `expert_load_score` column (or self‑reports), or exits with a specific error when it is absent. Both the required artifact and the necessary code are missing.
- **T006b** — The provided `create_golden_set.py` is truncated (the `apply_expert_rubric` function is incomplete) and no `data/processed/golden_set.csv` file exists, so the script does not actually generate and save the required synthetic Golden Set. The task’s core output is missing.
