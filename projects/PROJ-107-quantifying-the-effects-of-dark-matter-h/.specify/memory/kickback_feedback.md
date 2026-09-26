# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required project directories (`code/`, `data/`, `outputs/`) is present; the provided material only contains a feature specification and no filesystem artifacts. The implementer must create the three top‑level folders (and populate them as appropriate) to satisfy the task.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, `.flake8`, or related CI setup) are present in the provided evidence. Consequently, the task of configuring ruff/flake8 and Black has not been demonstrated. The implementer must add the appropriate configuration files and, optionally, show they are active (e.g., a sample run output).
- `T006` (rejected 1x): No code, configuration files, or documentation for a base logging infrastructure were provided; the only artifacts shown relate to data ingestion and analysis, not to pipeline tracking logs. Consequently, the required logging component is missing.
- `T017` (rejected 1x): The repository contains a `pipeline_runner.py` file, but it is truncated and does not show the required logic for merging chunk results, validating the axial ratios (0 < b/a ≤ 1 and 0 < c/a ≤ 1), logging excluded haloes, or writing the final `data/processed/halo_shapes.csv`. Moreover, the expected output CSV file is absent from the `data/processed` directory. The task therefore remains unfinished.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

