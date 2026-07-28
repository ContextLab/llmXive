# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required repository skeleton directories (`src/`, `tests/`, `data/`, `results/`, `docs/`, `contracts/`) is present; the provided material only contains a feature specification and no filesystem artifacts. The task therefore remains unfinished.
- `T003` (rejected 1x): No `renv.lock` file, R initialization script, or any evidence of the listed Bioconductor packages being installed is present. The required artifact (the environment lockfile and installation steps) is missing, so the task is not satisfied.
- `T003c` (rejected 1x): No `renv.lock` file, nor any unit‑test code or test results were provided; without these artifacts we cannot verify that a test checks the lockfile’s existence and that it records package versions. The required test and lockfile are missing.
- `T003d` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/integration/test_renv_status.py
- `T005d` (rejected 1x): declared artifact(s) missing/empty/invalid: scripts/validate_ci_workflow.py, tests/unit/test_ci_workflow_structure.py
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/logger.py
- `T006c` (rejected 1x): The repository contains a non‑empty `tests/unit/test_logger_fields.py` that checks the four required fields, but the referenced schema file `contracts/pipeline_log.schema.yaml` is missing and the test does not perform any validation against such a schema. Therefore the task’s requirement to ensure conformity to the schema is not satisfied.
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: species.yaml, parameters.yaml
- `T009c` (rejected 1x): The repository contains the unit‑test `tests/unit/test_config_files.py`, but the two configuration files it is supposed to check (`src/config/species.yaml` and `src/config/parameters.yaml`) are absent, so the test would fail and the requirement is not met. The missing YAML files must be added (or the test adjusted) for the task to be complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

