# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): declared artifact(s) missing/empty/invalid: requirements.txt
- `T002` (rejected 1x): declared artifact(s) missing/empty/invalid: requirements.txt
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `pyproject.toml` with Black settings, or CI scripts invoking ruff/black) are present in the provided evidence, so the required artifact to claim the task completed is missing.
- `T004` (rejected 1x): No `state/` directory or any checksum/versioning files were presented; the implementer provided only the feature specification for logic distillation, which does not address the required setup of a `state/` directory for artifact checksums and versioning. The required artifact is missing.
- `T005` (rejected 1x): No `utils/emulator.py` file or any code defining the required functions (`launch_emulator`, `send_action`, `check_crash`, `get_screenshot`) and error codes (`EMU_CRASH`, `EMU_TIMEOUT`, `EMU_NOT_FOUND`) is present in the provided artifacts. The task therefore remains unimplemented.
- `T006` (rejected 1x): No `utils/metrics.py` file or any code defining base classes for “Success Rate” and “Step Efficiency” was provided. The required artifact is missing, so the task is not satisfied.
- `T008` (rejected 1x): No configuration file, script, or documentation was provided to set up environment variables for dataset paths and random seeds, which is the core requirement of task T008. The artifacts shown relate only to dataset extraction, model training, and evaluation, not to environment variable management.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

