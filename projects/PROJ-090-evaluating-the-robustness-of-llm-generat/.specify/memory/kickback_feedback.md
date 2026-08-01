# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016` (rejected 1x): The required data files (`data/processed/perturbation_candidates_raw.json`, `data/processed/perturbation_candidates_validated.json`, and `data/logs/halt_report.json`) are absent, and the provided `semantic_validator.py` is truncated before showing the full validation, scoring, threshold check, and file‑writing logic. Consequently the implementation does not demonstrably meet the task’s specifications.
- `T018` (rejected 1x): The `filter_perturbations.py` script exists but the required output file `data/processed/perturbation_candidates.json` (and the halt report `data/logs/halt_report.json`) are not present, indicating the filtering step never produced the primary dataset or the error‑handling file. Consequently the task’s core requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

