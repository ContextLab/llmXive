# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014a` (rejected 1x): The implementer only noted that the filtering logic was removed and moved to another task, but no download or preprocessing scripts, CSV outputs, logs, or README documentation are present. Consequently, the mandatory artifacts for User Story 1 (data acquisition, preprocessing, surprisal calculation, and ≥100 valid rows) are missing.
- `T014b` (rejected 1x): No data download or preprocessing scripts, no generated CSV files, and no exclusion‑logging implementation are present. The required artifacts for User Story 1 (scripts, processed CSV with required columns, README logging) are missing, so the task’s core requirement is not satisfied.
- `T041` (rejected 1x): The provided `code/preprocess.py` is truncated and does not show any logic that builds the Markov transition matrix online or writes `markov_counts.json` and `markov_state.json`. Moreover, both required output files are absent from `data/processed/`. The task’s core output artifacts are missing, so the implementation is incomplete.
- `T017b` (rejected 1x): The claim provides no evidence that a `markov_state.json` file exists, that it contains `"order": 1`, nor that a confirmation entry was written to `analysis/verification_log.json`. These required artifacts are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

