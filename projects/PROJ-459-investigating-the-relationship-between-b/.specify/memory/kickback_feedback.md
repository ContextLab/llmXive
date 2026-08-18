# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): No code, configuration files, or documentation defining `check_memory_limit()` or `set_runtime_cap()` were provided, nor any evidence of environment configuration management for memory limits and runtime caps. The required artifacts are missing, so the task is not satisfied.
- `T017` (rejected 1x): No code, script, or documentation defining the required `exclude_subjects_by_missing_data()` function was provided; the claim lacks any tangible artifact (e.g., a Python module, notebook, or test output) demonstrating the validation logic for >10 % missing behavioral data or >10 % corrupted fMRI volumes. The implementer must supply the actual implementation (and optionally usage examples or tests) to satisfy the task.
- `T018` (rejected 1x): No code defining `exclude_subjects_by_motion()` or any logic to flag subjects with framewise displacement > 0.5 mm is present in the provided artifacts; the required function and motion‑exclusion implementation are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

