# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/main.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py (rc=1); python -m pytest tests/ (rc=2); 7 declared deliverable(s) absent: data/ecotourism/metadata.json; data/processed/climate_covariates.parquet; data/processed/ecotourism_data.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
2026-10-18 13:34:17 - root - INFO - Running specification validation (T001)…
2026-10-18 13:34:17 - root - INFO - Specification validation succeeded.
2026-10-18 13:34:17 - root - INFO - Fetching site coordinates (T003)…
2026-10-18 13:34:17 - fetch_site_coordinates - INFO - Downloading WDPA release from https://dopa.jrc.ec.europa.eu/download.php?file=WDPA_WDOECM_csv.zip
2026-10-18 13:34:17 - root - ERROR - Site‑metadata acquisition failed: Failed to fetch site coordinates: Failed to download WDPA archive: HTTP 404

Warning: Could not create log file data/logs/pipeline.log: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-555-investigating-the-potential-benefits-of-/data/logs/pipeline.log'

- python -m pytest tests/ -> rc=2
odule>
    from code.detection import fit_asymptotic_model, calculate_r_squared
E   ImportError: cannot import name 'fit_asymptotic_model' from 'code.detection' (/home/runner/work/llmXive/llmXive/projects/PROJ-555-investigating-the-potential-benefits-of-/code/detection.py)
=============================== warnings summary ===============================
tests/test_fetch_site_coordinates.py:9
  /home/runner/work/llmXive/llmXive/projects/PROJ-555-investigating-the-potential-benefits-of-/tests/test_fetch_site_coordinates.py:9: PytestUnknownMarkWarning: Unknown pytest.mark.integration - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    @pytest.mark.integration

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_pipeline.py
ERROR tests/unit/test_data_acquisition_climate.py
ERROR tests/unit/test_detection.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 3 errors in 1.09s =========================



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
    - `code/main.py` — IS a run-book command
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
