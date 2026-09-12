# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories (`data/raw`, `data/distorted`, `data/outputs`, `data/metadata`) being present or populated is provided; the prompt contains no file‑system listing or screenshots confirming their creation. The implementer’s claim cannot be verified without concrete artifacts.
- `T001b` (rejected 1x): No evidence was provided showing that the three required directories (`src/generators`, `src/inference`, `src/analysis`) actually exist in the repository; without a directory listing or similar proof, we cannot confirm the task was fulfilled. The implementer must create the directories and supply a view (e.g., `tree` output) confirming their presence.
- `T001c` (rejected 1x): The implementer supplied only a feature specification and no file system evidence; there is no indication that `tests/unit` or `tests/integration` directories were created, nor any listing or content showing those folders. The required test directory structure is missing.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` entries for Black, a `.ruff.toml` or `ruff.toml`, or related setup scripts) were provided, nor any evidence that ruff and black have been integrated into the project. The required artifacts are missing, so the task is not satisfied.
- `T005` (rejected 1x): No evidence of a `models/` directory is provided; the artifact list is empty, so we cannot confirm that the required cache directory was actually created. The implementer must add the `models/` folder (non‑empty or at least present) to satisfy the task.
- `T007a` (rejected 1x): The required file `specs/001-extreme-aspect-ratio-robustness/contracts/dataset.schema.yaml` does not exist on disk, so the schema definition for the synthetic video metadata is missing. The task is therefore not satisfied.
- `T007b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T012b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/generators/fetch_original.py
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: src/generators/distort_video.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

