# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python main.py; 2 command(s) failed: python -m src.ingestion.fetch_nist (rc=1); python -m src.ingestion.fetch_journal_data (rc=1); 6 declared deliverable(s) absent: data/processed/alloys_features.csv; data/processed/alloys_raw.csv; data/processed/completeness_report.json

## Failing / missing run-book commands

- python -m src.ingestion.fetch_nist -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-393-predicting-the-influence-of-composition-/code/.venv/bin/python: No module named src.ingestion.fetch_nist
- python -m src.ingestion.fetch_journal_data -> rc=1
    /home/runner/work/llmXive/llmXive/projects/PROJ-393-predicting-the-influence-of-composition-/code/.venv/bin/python: No module named src.ingestion.fetch_journal_data
- python main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-393-predicting-the-influence-of-composition-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-393-predicting-the-influence-of-composition-/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/alloys_features.csv
- data/processed/alloys_raw.csv
- data/processed/completeness_report.json
- data/processed/model_metrics.json
- data/raw/elemental_properties.csv
- data/raw/manual_curated.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/alloys_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/models/linear_regressor.py` — NOT invoked by the run-book
    - `code/src/models/random_forest_regressor.py` — NOT invoked by the run-book
    - `code/src/models/training_pipeline.py` — NOT invoked by the run-book
    - `code/src/models/feature_importance.py` — NOT invoked by the run-book
    - `code/src/features/feature_engineering_pipeline.py` — NOT invoked by the run-book
    - `code/src/features/descriptor_calculator.py` — NOT invoked by the run-book
    - `code/tests/integration/test_feature_importance.py` — NOT invoked by the run-book
    - `code/tests/unit/test_random_forest_regressor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/alloys_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/alloys_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/ingestion/ingest_pipeline.py` — NOT invoked by the run-book
    - `code/src/features/feature_engineering_pipeline.py` — NOT invoked by the run-book
    - `code/src/features/descriptor_calculator.py` — NOT invoked by the run-book
    - `code/src/preprocessing/preprocess_pipeline.py` — NOT invoked by the run-book
    - `code/src/preprocessing/unit_normalizer.py` — NOT invoked by the run-book
    - `code/src/preprocessing/scarcity_checker.py` — NOT invoked by the run-book
    - `code/src/preprocessing/validator.py` — NOT invoked by the run-book
    - `code/src/preprocessing/completeness_reporter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/alloys_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/completeness_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/preprocessing/completeness_reporter.py` — NOT invoked by the run-book
    - `code/scripts/generate_completeness_report.py` — NOT invoked by the run-book
    - `code/tests/unit/test_completeness_reporter.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/completeness_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/models/linear_regressor.py` — NOT invoked by the run-book
    - `code/src/models/random_forest_regressor.py` — NOT invoked by the run-book
    - `code/src/models/training_pipeline.py` — NOT invoked by the run-book
    - `code/scripts/generate_model_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/elemental_properties.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/utils/periodic_table_loader.py` — NOT invoked by the run-book
    - `code/src/utils/logging_config.py` — NOT invoked by the run-book
    - `code/src/features/descriptor_calculator.py` — NOT invoked by the run-book
    - `code/src/preprocessing/validator.py` — NOT invoked by the run-book
    - `code/scripts/generate_elemental_properties.py` — NOT invoked by the run-book
    - `code/tests/unit/test_descriptor_calculator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/elemental_properties.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/manual_curated.csv` is declared but was NOT written. Scripts referencing it:
    - `code/src/ingestion/ingest_pipeline.py` — NOT invoked by the run-book
    - `code/src/ingestion/manual_curator.py` — NOT invoked by the run-book
    - `code/tests/integration/test_manual_curator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/manual_curated.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
