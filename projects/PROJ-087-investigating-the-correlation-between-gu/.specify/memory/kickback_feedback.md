# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or `__init__.py` files were presented as evidence; the required folders (`src`, `data/raw`, `data/processed`, `tests/unit`, `tests/integration`, `docs`) and empty `__init__.py` files are not shown, so the task’s deliverable is missing.
- `T004` (rejected 1x): No evidence was provided showing that the `data/raw/`, `data/processed/`, and `data/processed/plots/` directories actually exist, nor that each contains a `.gitkeep` file. Without visible directory listings or file contents, the requirement cannot be confirmed as satisfied.
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/hashing.py
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/cleaned_microbiome_sleep.csv
- `T017` (rejected 1x): The required artifact `data/processed/ingestion_report.json` does not exist, so the exclusion counts and proportion are not logged as specified. The task therefore remains unfinished.
- `T037` (rejected 1x): The required file `src/models/schemas.py` does not exist, so no Pydantic models (`MicrobiomeSample`, `SleepMetric`, `CorrelationResult`) are defined as required. The artifact is missing, making the task unfinished.
- `T020b` (rejected 1x): The required input file `data/processed/cleaned_microbiome_sleep.csv` is absent, and the `src/diversity.py` implementation is truncated (the `calculate_alpha_diversity` function is incomplete), so the alpha‑diversity computation using the rarefied table is not fully provided.
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/correlation_results.csv
- `T029` (rejected 1x): The required `src/report.py` file does not exist, so no report or summary table of correlations is present. The task’s core deliverable is missing.
- `T030` (rejected 1x): No evidence of any plot files (e.g., PNG, PDF, SVG) existing in the required `data/processed/plots/` directory is provided; the implementer did not supply the saved plot artifacts, so the task requirement is not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

