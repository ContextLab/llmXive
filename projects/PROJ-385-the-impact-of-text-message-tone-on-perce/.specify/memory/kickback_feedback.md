# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required project directories (`code/`, `data/`, `tests/`, `specs/`) is provided; the response contains only the specification text and no file or folder listings to confirm the structure exists. The implementer must create and show these directories (with at least placeholder files) to satisfy the task.
- `T003` (rejected 1x): No configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or Black settings) or scripts were provided to show that ruff linting and black formatting have been set up in the `code/` directory. The required artifacts are missing, so the task is not satisfied.
- `T004` (rejected 1x): No `data-model.md` file was found in `specs/001-text-tone-emotional-support/`, and no content defining the entities Stimulus, Participant, Rating, and AnalysisResult with their relationships was provided. The required documentation artifact is missing.
- `T005` (rejected 1x): No evidence was provided that the required directories (`data/raw/`, `data/processed/`, `data/consent/`) actually exist; the artifacts listed only describe feature specifications and user stories, with no mention of creating or populating those folders. The implementer must create the three directories in the project repository.
- `T006` (rejected 1x): The required schema files (`stimulus.schema.yaml`, `rating.schema.yaml`, `analysis_result.schema.yaml`) are absent from the `specs/001-text-tone-emotional-support/contracts/` directory; only a placeholder note indicates a missing `schema.yaml`. Consequently, no defined or validated JSON/YAML schemas are present.
- `T008` (rejected 1x): No logging configuration files, code modules, or documentation were provided to demonstrate that a logging infrastructure (capturing pipeline steps and data exclusion reasons) has been created. The required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

