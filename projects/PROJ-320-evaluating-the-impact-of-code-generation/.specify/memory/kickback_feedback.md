# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001b` (rejected 1x): No `__init__.py` files are present in any `code/` subdirectory in the provided evidence; the required package‑initialisation files are missing, so the task’s requirement is not satisfied.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections, `.ruff.toml`, or similar) are present, nor any documentation or scripts showing that `ruff` and `black` have been set up for the project. Consequently the required artifact for task T003 is missing.
- `T033` (rejected 1x): The repository contains `code/analysis/save_complexity_scores.py`, but the required input file `data/processed/prs_labeled.csv` does not exist, and the expected output `data/processed/complexity_scores.csv` is missing. Consequently the script cannot produce the required CSV with `pr_id` and `complexity_score` columns, so the task is not fulfilled.
- `T022` (rejected 1x): The repository contains a partially‑written `code/data/extract_metrics.py` that stops mid‑function and never implements the metric calculations or the join logic. Moreover, the required input files `data/processed/prs_labeled.csv` and `data/processed/complexity_scores.csv` are absent, so the script cannot be executed or verified. The task’s core outputs are therefore not produced.
- `T023` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/prs_metrics.csv
- `T027` (rejected 1x): The `code/analysis/generate_results_report.py` file exists but is truncated and its logic reads an existing `data/processed/results.json` rather than creating it. Moreover, the required `data/processed/results.json` file is missing entirely. The task’s core requirement—to generate a results JSON with all statistical outputs—is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

