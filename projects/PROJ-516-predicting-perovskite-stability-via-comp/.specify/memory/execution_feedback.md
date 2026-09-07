# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python validation.py; python main.py; 3 command(s) failed: python code/data_ingestion.py (rc=1); python code/model_training.py (rc=1); python code/utils/state_manager.py (rc=1); 7 declared deliverable(s) absent: data/processed/descriptors_filtered.csv; data/processed/model_runs.json; data/processed/vif_report.csv

## Failing / missing run-book commands

- python code/data_ingestion.py -> rc=1
    INFO:__main__:Starting T012a: NREL Data Ingestion
CRITICAL:__main__:Task T012a failed: Required API key 'NREL_API_KEY' is missing. Please ensure it is set in the .env file or environment variables.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/code/data_ingestion.py", line 159, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/code/data_ingestion.py", line 121, in main
    raw_df = load_raw_data()
             ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/code/data_ingestion.py", line 34, in load_raw_data
    api_key = get_api_key("NREL_API_KEY")
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/code/utils/config_manager.py", line 96, in get_api_key
    raise ConfigError(
utils.config_manager.ConfigError: Required API key 'NREL_API_KEY' is missing. Please ensure it is set in the .env file or environment variables.
- python code/model_training.py -> rc=1
    INFO:__main__:Loading data...
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/code/model_training.py", line 288, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/code/model_training.py", line 241, in main
    df, X, y, y_strat = load_data()
                        ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/code/model_training.py", line 54, in load_data
    raise FileNotFoundError(f"Data file {DATA_PATH} not found. Run T017 first.")
FileNotFoundError: Data file data/processed/descriptors.csv not found. Run T017 first.
- python validation.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/validation.py': [Errno 2] No such file or directory
- python code/utils/state_manager.py -> rc=1
    Usage: python -m code.utils.state_manager <update|verify> <file_path>
- python main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-516-predicting-perovskite-stability-via-comp/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/descriptors_filtered.csv
- data/processed/model_runs.json
- data/processed/vif_report.csv
- data/raw/metadata.json
- data/raw/mp_perovskites.csv
- data/raw/nrel_perovskites.csv
- data/raw/perovskites_merged.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/descriptors_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/filter_descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_runs.json` is declared but was NOT written. Scripts referencing it:
    - `code/model_training.py` — IS a run-book command
    - `code/save_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_runs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/vif_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/vif_diagnostic.py` — NOT invoked by the run-book
    - `code/utils/vif_calculator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/vif_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/fetch_mp_perovskites.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — IS a run-book command
    - `code/filter_descriptors.py` — NOT invoked by the run-book
    - `code/data_ingestion_metadata.py` — NOT invoked by the run-book
    - `code/save_models.py` — NOT invoked by the run-book
    - `code/uncertainty_flagger.py` — NOT invoked by the run-book
    - `code/write_metadata.py` — NOT invoked by the run-book
    - `code/extract_metadata.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/mp_perovskites.csv` is declared but was NOT written. Scripts referencing it:
    - `code/fetch_mp_perovskites.py` — NOT invoked by the run-book
    - `code/merge_datasets.py` — NOT invoked by the run-book
    - `code/verify_dual_source.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/mp_perovskites.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/nrel_perovskites.csv` is declared but was NOT written. Scripts referencing it:
    - `code/merge_datasets.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — IS a run-book command
    - `code/fetch_nrel_perovskites.py` — NOT invoked by the run-book
    - `code/data_ingestion_metadata.py` — NOT invoked by the run-book
    - `code/verify_dual_source.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/nrel_perovskites.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/perovskites_merged.csv` is declared but was NOT written. Scripts referencing it:
    - `code/merge_datasets.py` — NOT invoked by the run-book
    - `code/feature_engineering.py` — NOT invoked by the run-book
    - `code/finalize_descriptors.py` — NOT invoked by the run-book
    - `code/write_metadata.py` — NOT invoked by the run-book
    - `code/extract_metadata.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/perovskites_merged.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/descriptors.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/filter_descriptors.py`, `code/feature_engineering.py`, `code/vif_diagnostic.py`, `code/save_models.py`, `code/finalize_descriptors.py`, `code/grid_search.py`, `code/propagate_uncertainty.py`, `code/utils/vif_calculator.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/descriptors.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/model_training.py`, `code/filter_descriptors.py`, `code/feature_engineering.py`, `code/vif_diagnostic.py`, `code/save_models.py`, `code/finalize_descriptors.py`, `code/verify_descriptors.py`, `code/grid_search.py`, `code/propagate_uncertainty.py`, `code/utils/vif_calculator.py`.
