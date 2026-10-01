# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The claim only provides a feature specification and no visible evidence that the required directories (`src/`, `data/raw/`, `data/derived/`, `data/annotations/`, `results/`, `tests/`, `specs/`) actually exist in the repository. Without directory listings or files confirming their creation, the task is not satisfied. The implementer must create the specified folders and provide proof (e.g., a directory tree listing).
- `T004` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.ruff.toml`, or similar) were presented, nor any evidence (scripts, documentation, CI integration) showing that ruff and black have been configured for the project. Consequently the required artifact is missing.
- `T006` (rejected 1x): The required file `src/extraction/schema.py` does not exist, so the data classes PullRequest, BugDetection, and AlignmentResult are not defined. The implementer must create this file and implement the specified data classes.
- `T007` (rejected 1x): The required file `src/detection/schema.py` does not exist, so no data class (LLMCodeDetectionResult) is defined. The implementer must add the missing file with the appropriate data class implementation.
- `T008` (rejected 1x): The required file `src/inference/schema.py` does not exist, so the data classes `InferenceRequest` and `InferenceResponse` are not defined. The implementer must add this file with the appropriate data class definitions.
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/timeout_wrapper.py
- `T010` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/logger.py
- `T011` (rejected 1x): The claim mentions creating `contracts/` YAML schemas, but no YAML files (e.g., `contracts/pr_data.yaml`, `contracts/bug_detection.yaml`, `contracts/alignment_result.yaml`) are present or referenced in the provided evidence. Without the actual schema files, we cannot verify that the required artifacts exist or contain the correct structure. The implementer must add the YAML schema files in the `contracts/` directory.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

