# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 5 declared deliverable(s) absent: data/analysis/centrality_metrics.csv; data/analysis/diagnostics.json; data/analysis/qc_log.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
    p": "2026-08-14T18:39:02.625382", "level": "INFO", "logger": "us1", "message": "Starting User Story 1 Pipeline", "module": "main_us1", "function": "run_us1_pipeline", "line": 31}
{"timestamp": "2026-08-14T18:39:02.625444", "level": "INFO", "logger": "us1", "message": "Step 1: Downloading ADNI data...", "module": "main_us1", "function": "run_us1_pipeline", "line": 36}
{"timestamp": "2026-08-14T18:39:02.625512", "level": "INFO", "logger": "downloader", "message": "Starting ADNI Downloader", "module": "adni_downloader", "function": "run_downloader", "line": 83}
{"timestamp": "2026-08-14T18:39:02.625584", "level": "ERROR", "logger": "downloader", "message": "ADNI Credentials missing or invalid: Missing required ADNI credentials: ADNI_USER, ADNI_PASS, ADNI_SUBJECT_LIST", "module": "adni_downloader", "function": "run_downloader", "line": 89}
{"timestamp": "2026-08-14T18:39:02.625657", "level": "ERROR", "logger": "us1", "message": "Download failed.", "module": "main_us1", "function": "run_us1_pipeline", "line": 39}
{"timestamp": "2026-08-14T18:39:02.625720", "level": "ERROR", "logger": "main", "message": "US1 failed. Aborting pipeline.", "module": "main", "function": "main", "line": 60}

## Declared deliverables still missing

- data/analysis/centrality_metrics.csv
- data/analysis/diagnostics.json
- data/analysis/qc_log.json
- data/analysis/regression_results.csv
- data/raw/participant_list.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/centrality_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main_us1.py` — NOT invoked by the run-book
    - `code/data_models.py` — NOT invoked by the run-book
    - `code/analysis/data_merger.py` — NOT invoked by the run-book
    - `code/centrality/metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/centrality_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `code/main_us2.py` — NOT invoked by the run-book
    - `code/analysis/diagnostics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/qc_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/main_us1.py` — NOT invoked by the run-book
    - `code/preprocess/fMRI_pipeline.py` — NOT invoked by the run-book
    - `code/analysis/qc_validator.py` — NOT invoked by the run-book
    - `code/centrality/metrics.py` — NOT invoked by the run-book
    - `code/centrality/connectivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/qc_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/regression_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main_us2.py` — NOT invoked by the run-book
    - `code/viz/plotting.py` — NOT invoked by the run-book
    - `code/analysis/regression.py` — NOT invoked by the run-book
    - `code/analysis/diagnostics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/regression_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/participant_list.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main_us1.py` — NOT invoked by the run-book
    - `code/preprocess/fMRI_pipeline.py` — NOT invoked by the run-book
    - `code/download/adni_downloader.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/participant_list.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
