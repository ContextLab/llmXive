# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of a `projects/PROJ-551-asymptotic-behavior-of-random-matrix-eig/` directory or any files within it is provided; the claim lacks any tangible artifact showing the required project structure has been created.
- `T003` (rejected 1x): No configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or `black` settings) or any other evidence of ruff/black being set up in the `code/` directory were presented. Without visible artifacts, the claim cannot be verified as fulfilled.
- `T015` (rejected 1x): The implementer only supplied the feature specification and test scenarios but did not provide any code changes, data files, or scripts that actually write eigenvalues and perturbation parameters (with metadata) to `data/processed/`. No artifact exists on disk to verify that the recording logic was implemented. The required output files are missing.
- `T019` (rejected 1x): No `data/raw/` directory or any generated matrix files with checksums are present in the provided evidence; the claim lacks any tangible artifacts demonstrating raw matrix instances or their verification. The task therefore remains unfulfilled.
- `T040` (rejected 1x): No files or directories were presented under `data/raw/sweep/`, and no checksums or intermediate state records were supplied. Consequently, the required raw matrix instances and their verification data are missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

