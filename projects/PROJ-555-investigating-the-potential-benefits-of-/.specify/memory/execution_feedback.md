# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 1 command(s) failed: python -m pytest tests/ (rc=2); 7 declared deliverable(s) absent: data/ecotourism/metadata.json; data/processed/climate_covariates.parquet; data/processed/ecotourism_data.csv

## Failing / missing run-book commands

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-555-investigating-the-potential-benefits-of-/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-555-investigating-the-potential-benefits-of-/code/main.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
not import name 'verify_fr002_nonlinear_fallback' from 'code.spec_validation' (/home/runner/work/llmXive/llmXive/projects/PROJ-555-investigating-the-potential-benefits-of-/code/spec_validation.py)
=============================== warnings summary ===============================
tests/test_fetch_site_coordinates.py:9
  /home/runner/work/llmXive/llmXive/projects/PROJ-555-investigating-the-potential-benefits-of-/tests/test_fetch_site_coordinates.py:9: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_pipeline.py
ERROR tests/test_spec_validation.py
ERROR tests/unit/test_data_acquisition_climate.py
ERROR tests/unit/test_detection.py
ERROR tests/unit/test_spec_validation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 5 errors during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 5 errors in 1.30s =========================



## Declared deliverables still missing

- data/ecotourism/metadata.json
- data/processed/climate_covariates.parquet
- data/processed/ecotourism_data.csv
- data/processed/ndvi_timeseries.parquet
- data/processed/recovery_trajectories.parquet
- data/processed/site_metadata.csv
- data/raw/query_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/ecotourism/metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/data_acquisition.py` — NOT invoked by the run-book
    - `code/data_acquisition_climate.py` — NOT invoked by the run-book
    - `code/fetch_site_coordinates.py` — NOT invoked by the run-book
    - `code/generate_recovery_trajectories.py` — NOT invoked by the run-book
    - `code/generate_site_coordinates.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/ecotourism/metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/climate_covariates.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/data_acquisition_climate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/climate_covariates.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ecotourism_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ecotourism_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ndvi_timeseries.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/detection.py` — NOT invoked by the run-book
    - `code/generate_recovery_trajectories.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ndvi_timeseries.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/recovery_trajectories.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/detection.py` — NOT invoked by the run-book
    - `code/generate_recovery_trajectories.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/recovery_trajectories.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/site_metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/fetch_site_coordinates.py` — NOT invoked by the run-book
    - `code/generate_recovery_trajectories.py` — NOT invoked by the run-book
    - `code/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/site_metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/query_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/data_acquisition.py` — NOT invoked by the run-book
    - `code/data_acquisition_climate.py` — NOT invoked by the run-book
    - `code/fetch_site_coordinates.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/query_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
