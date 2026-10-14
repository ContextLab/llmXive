# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): Requested task execution failed; rerun successfully: data/raw/ppmi_clinical.parquet exit=-1; code/src/pipeline/run_preprocess_default.py exit=1
- `T005` (rejected 1x): Requested task execution failed; rerun successfully: tests/test_mixed_effects_execution.py exit=5
- `T006` (rejected 1x): The permutation implementation (`code/src/pipeline/permutation.py`) and its test (`code/tests/test_permutation.py`) are present and meet most functional specs, but the required output artifact `data/results/permutation_pvalues.csv` is missing from the repository. The task mandates that this CSV be generated (and persisted) by the pipeline; its absence means the deliverable is incomplete. Generating and committing the results file (or a placeholder with correct schema) will satisfy the requirement.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

