# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories `projects/PROJ-560-embodied-curriculum-learning-physical-si/code/src/` and `.../code/tests/` was provided; the claim lacks any artifact confirming their creation. The task remains incomplete until those folders exist (and are non‑empty).
- `T001b` (rejected 1x): No evidence of the four required directories (`data/raw/`, `data/processed/`, `data/synthetic/`, `data/derivation_logs/` under the project path) is provided; the implementer did not supply any filesystem listing or screenshots confirming their creation. The task remains unfinished until those directories are shown to exist and be non‑empty.
- `T001c` (rejected 1x): No evidence was provided that the required directory `projects/PROJ-560-embodied-curriculum-learning-physical-si/state/projects/PROJ-560-embodied-curriculum-learning-physical-si/` actually exists or contains any files; the submission contains only specification text and no tangible artifact confirming the directory creation.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: pyproject.toml, ruff.toml
- `T017` (rejected 1x): No code, configuration, or log files were provided showing that logging for data loading, skipped records, or synthetic generation parameters was added. The required artifact (e.g., updated scripts with logging statements and resulting log outputs) is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

