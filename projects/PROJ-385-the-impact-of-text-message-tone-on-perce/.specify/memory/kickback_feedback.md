# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The script `code/02_simulate_ratings.py` is incomplete (the `save_ratings` function is cut off and there is no entry‑point that actually writes `data/raw/ratings.csv`). Consequently the required output file `data/raw/ratings.csv` does not exist. The task’s core deliverable – a generated ratings CSV – is missing.
- `T016` (rejected 1x): The provided `code/03_clean_data.py` only defines a detection function that flags participants based on zero variance but never validates that participants have rated the full set of stimuli, nor does it write any exclusion flags to `data/processed/cleaning_log.csv` (the file is missing). Consequently the required output artifact is absent and the implementation does not fulfill the task specifications.
- `T019` (rejected 1x): The required integration test file `tests/integration/test_lmm_pipeline.py` does not exist, so the claimed implementation provides no evidence of a functional test for the full LMM pipeline. The task cannot be considered completed until this file is created with appropriate test code.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

