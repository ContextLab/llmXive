# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required `code/`, `data/`, `results/`, or `tests/` directories (or any files within them) was provided; without a directory listing or actual artifacts, we cannot confirm the project structure was created. The implementer must supply the filesystem layout showing these folders (and ideally some placeholder content) to satisfy the task.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) are present in the provided evidence, nor any documentation showing that ruff/flake8 and black have been set up for the project. Consequently the task of configuring these tools is not satisfied.
- `T007` (rejected 1x): No files or code were presented showing a `code/models/` directory containing definitions for `Participant`, `MicrobiomeProfile`, or `CognitiveScore`. Without these model files, the required data entities have not been demonstrated as created. The implementer must add the model definitions in the specified path.
- `T009` (rejected 1x): No configuration files, scripts, or documentation for managing the UK Biobank token were presented; the implementer provided no tangible artifact showing environment configuration management for credentials. Consequently, the requirement is not satisfied.
- `T019` (rejected 1x): The required evidence file `results/power/power_report.md` does not exist, so the task’s deliverable (a generated report) is missing. Consequently the implementation does not satisfy the stated requirement.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

