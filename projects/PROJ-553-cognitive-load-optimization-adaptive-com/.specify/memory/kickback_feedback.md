# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories (`data/raw/`, `data/processed/`, `data/explanation_tiers/`, `data/simulation_results/`, `code/`, `tests/`, `docs/`) being created is provided; the implementer did not supply a directory listing or any files confirming the structure exists.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) are present in the provided evidence, so the required setup for ruff/flake8 and black is missing. The task’s deliverable is not demonstrated.
- `T005` (rejected 1x): The repository lacks the required `data/processed/golden_set.csv` file, and the provided `code/load_data.py` does not contain any logic to verify the presence of that CSV, check for an `expert_load_score` (or self‑report) column, or raise a specific error when it is missing. The task’s validation step is therefore not implemented.
- `T006b` (rejected 1x): The repository contains a partially‑implemented `code/create_golden_set.py`, but the script is truncated (the `apply_expert_rubric` function is incomplete) and lacks any code that writes the generated data to `data/processed/golden_set.csv`. Consequently the required output file does not exist. The task’s requirement to actually create and save a synthetic expert‑labeled Golden Set is not fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

