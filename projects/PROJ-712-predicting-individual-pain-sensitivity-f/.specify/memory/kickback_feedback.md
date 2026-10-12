# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- `T004` (rejected 1x): the task writes platform-owned path(s) inside the project: `state/log.txt` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- `T008` (rejected 1x): The repository contains `code/preprocessing.py` with a plausible implementation, but the required verification artifacts are absent or inadequate: the unit test `tests/unit/test_preprocessing.py` never actually runs `extract_microstate_features` on data nor checks for a 30‑column DataFrame, and the integration test `tests/integration/test_full_preprocess.py` is missing, as is the expected output file `data/processed/feature_matrix.csv`. Consequently the task’s verification criteria are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

