# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was provided that the required directories (`code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`) actually exist on disk; the response contains only the task description and no file‑system listing or screenshots showing those folders. The implementer must create the directories (and optionally include a brief directory tree) to satisfy the task.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.ruff.toml`, or a `pre-commit` config) were provided or referenced, so there is no evidence that ruff and black have been set up in the `code/` directory. The required artifacts are missing.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T019` (rejected 1x): The provided `download.py` contains only placeholder logic, raises a `FileNotFoundError` instead of performing a real download, and leaves the expected MD5 checksum empty. Moreover, the required output file `data/raw/uspto_raw.parquet` is missing. The implementation does not fulfill the download, checksum verification, or Constitution Principle II gate check as specified.
- `T014` (rejected 1x): The `sanitize.py` file is present but only partially shown and does not demonstrate loading the parquet file or completing the sanitization pipeline (the code is truncated after “# 3. Parse Yield”). Moreover, the required input file `data/raw/uspto_raw.parquet` is missing, so the script cannot be executed as specified. The task’s core requirement—loading the USPTO parquet, sanitizing reactions, and standardizing them—is therefore not satisfied.
- `T017` (rejected 1x): The `code/preprocessing/ingest.py` script exists and implements the ingestion pipeline, but the required output artifact `data/processed/cleaned_reactions.parquet` is missing from the repository, so the task’s core deliverable (saving the cleaned dataset) is not present.
- `T018` (rejected 1x): The `ingest.py` script only logs high‑level pipeline steps and does not record exclusion reasons or compute/write data‑quality metrics, and the required `data/results/data_quality_report.json` file is absent. Both the logging enhancements and the JSON report generation are missing.
- `T010` (rejected 1x): The required input file `data/processed/cleaned_reactions.parquet` does not exist, and the expected output `data/processed/scaffold_groups.parquet` was never created. Moreover, the provided `scaffold.py` is truncated and lacks the logic to load the input parquet, generate scaffolds, and save the resulting dataframe, so the task’s core requirement is unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

