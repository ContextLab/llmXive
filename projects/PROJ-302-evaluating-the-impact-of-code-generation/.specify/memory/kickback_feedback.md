# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required core directories (`code/`, `data/`, `tests/`, `docs/`) being present was provided; the implementer supplied no artifact list or screenshots showing these folders. The task remains undone until those directories exist in the project repository.
- `T001b` (rejected 1x): No evidence of the required `data/raw/` and `data/processed/` directories (or any files within them) is provided; without tangible artifacts the claim that the subdirectories were created cannot be verified. The implementer must add the actual directories (and optionally placeholder files) to the repository.
- `T001d` (rejected 1x): No directory structure was presented in the evidence; there is no listing or contents showing that the required subfolders (`code/data_acquisition/`, `code/feature_extraction/`, `code/analysis/`, `code/utils/`) actually exist. The implementer’s claim cannot be verified without these artifacts.
- `T003` (rejected 1x): No configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`) or scripts setting up ruff linting and black formatting are present in the provided evidence, so the required artifact for task T003 is missing.
- `T014b` (rejected 1x): The repository contains `code/data_acquisition/synthetic_generator.py`, but the required output file `data/processed/generated_snippets.parquet` is missing, and the shown script is truncated before any logic that writes the Parquet file or fully creates the amendment markdown. Without the generated dataset, the mandatory generation requirement is not satisfied.
- `T017b` (rejected 1x): The `semantic_similarity.py` file exists but is incomplete (truncated) and there is no `data/processed/diagnostic_scores.parquet` output file. The required artifact (the diagnostic scores Parquet file) is missing, so the task is not fully satisfied.
- `T022b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/deviation_report.md

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

