# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `data/`, `tests/`, `specs/`) is present in the provided artifacts; the implementer did not supply any file or folder listings showing that the project structure has been created. The task therefore remains unfinished.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., a `pyproject.toml` or `.ruff.toml` enabling ruff, and a `pyproject.toml` or `black` config) were presented, nor any evidence of these tools being set up in the `code/` directory. The required artifacts are missing, so the task is not satisfied.
- `T004` (rejected 1x): No evidence of a `specs/001-text-tone-emotional-support/data-model.md` file was provided, nor any content showing the required entities (Stimulus, Participant, Rating, AnalysisResult) or validation against the specification. The necessary artifact is missing, so the task is not satisfied.
- `T005` (rejected 1x): No evidence of the required directories (`data/raw/`, `data/processed/`, `data/consent/`) being present or populated is provided; the only artifacts shown are project specifications, not the filesystem structure. The implementer must create the three data sub‑directories (and optionally add placeholder files) to satisfy the task.
- `T006` (rejected 1x): The required schema files (`stimulus.schema.yaml`, `rating.schema.yaml`, `analysis_result.schema.yaml`) are missing from the `specs/001-text-tone-emotional-support/contracts/` directory; no schemas are present to validate the JSON/YAML data. The task therefore is not satisfied.
- `T009b` (rejected 1x): The repository contains `code/00_power_analysis.py`, but the shown content only defines utility functions for loading results and estimating duration; there is no code that creates a power‑vs‑sample‑size plot or saves it. Moreover, the required output file `data/processed/power_curve.png` is absent. The task’s core deliverable—a power curve visualization saved to the specified path—is missing.
- `T015` (rejected 1x): The repository contains `code/04_collect_real_data.py`, but the required output file `data/raw/real_ratings.csv` is absent, so the pipeline’s primary artifact does not exist. Without this CSV the task’s core requirement (real human ratings) is unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

