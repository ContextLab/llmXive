# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017b` (rejected 1x): The provided `semantic_similarity.py` is truncated (the `calculate_similarity` function ends abruptly and no code is shown that writes a Parquet file), and the required output `data/processed/semantic_scores.parquet` does not exist. Both the implementation and the expected artifact are missing, so the task is not satisfied.
- `T020` (rejected 1x): The `check_significance` function is correctly implemented, but the required output file `data/processed/significance_flag.json` does not exist, so the task’s output artifact is missing.
- `T030` (rejected 1x): The repository contains a partially shown `code/analysis/sensitivity.py`, but the file is truncated and does not demonstrate the required logic for computing the 80 % significance consistency across exactly five subsets, nor does it write `data/processed/sensitivity_summary.json`. The expected JSON output file is absent, so the task’s deliverable is not satisfied.
- `T034` (rejected 1x): No code, script, notebook, or other artifact implementing the matching logic for the Prompt‑Based cohort is present; the only evidence is the task description itself. The required implementation (e.g., a function/module that performs propensity‑score matching using the US2 covariates) is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

