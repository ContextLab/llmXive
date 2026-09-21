# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of a `data/raw` directory being present was provided; the response contains only task description and specifications, with no actual filesystem artifact or confirmation that the directory exists. The required artifact is missing.
- `T001b` (rejected 1x): No evidence of a `data/processed` directory (or any files within it) is provided; the claim lacks the required artifact confirming the directory’s creation. The implementer must add the actual `data/processed` folder to the repository (or show its presence) for the task to be considered complete.
- `T001c` (rejected 1x): No evidence was provided showing that a `data/assets` directory exists (or contains any files). Without a visible directory or confirmation of its creation, the requirement cannot be verified as satisfied. The implementer must add the `data/assets` folder (and optionally populate it) and provide proof of its presence.
- `T002` (rejected 1x): No evidence of the required `code`, `artifacts`, or `tests` directories (or any files within them) is provided; the claim lacks concrete artifacts confirming their existence.
- `T004` (rejected 1x): The submission contains no linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with `ruff`/`black` settings, or GitHub Action workflow steps) and provides no evidence that flake8, ruff, or black have been set up in the repository. Without these artifacts, the task of configuring linting and formatting tools is not satisfied.
- `T009` (rejected 1x): No evidence of a logging setup was presented: there is no code, configuration, or generated files in `artifacts/logs/` or `artifacts/metrics.json` to show that structured logs are being written. The required artifacts are missing, so the task is not satisfied.
- `T010b` (rejected 1x): Both required files (`data/raw/reference_substructures_raw.csv` and `data/raw/checksums.json`) are missing, so no checksum verification could be performed. The task’s core artifact is absent, making the claim unsubstantiated.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

