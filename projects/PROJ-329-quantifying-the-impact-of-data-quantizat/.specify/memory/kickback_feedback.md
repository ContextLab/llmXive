# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005` (rejected 1x): No code, scripts, or documentation implementing checksumming for the `data/raw/` and `data/processed/` directories was provided. The required data‑hygiene utilities are missing, so the task is not satisfied.
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils.py
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): No code, configuration files, tests, or documentation were provided that show error handling for missing or corrupted noise files has been added. The claim lacks any tangible artifact demonstrating the required graceful‑failure behavior, so the task is not satisfied.
- `T009` (rejected 1x): No configuration files, scripts, or documentation were provided that set random seeds, define CI resource limits (2 CPU, 7 GB RAM), or contain the calculated batch‑size constraints for a pilot of N = 1200. The required artifacts are missing, so the task is not satisfied.
- `T010` (rejected 1x): No calculation, table, or written documentation showing that the batch size N = 1200 fits within the 6‑hour CI time limit and 7 GB RAM constraint is present. The implementer supplied only the task description without any quantitative analysis or evidence, so the required artifact is missing.
- `T011` (rejected 1x): The required artifact `tests/unit/test_quantization.py` is missing entirely, so no unit test code exists to verify the 1‑bit and 16‑bit edge cases. Without this file, the task’s deliverable is not present.
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data_generation.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

