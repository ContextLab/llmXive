# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 run-book script(s) missing (plan/impl path mismatch): python code/01_download_data.py; python code/02_preprocess.py; python code/03_aggregate.py; 6 declared deliverable(s) absent: data/final/permutation_results.csv; data/final/regression_summary.csv; data/final/sensitivity_analysis.csv

## Failing / missing run-book commands

- python code/01_download_data.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/01_download_data.py': [Errno 2] No such file or directory
- python code/02_preprocess.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/02_preprocess.py': [Errno 2] No such file or directory
- python code/03_aggregate.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/03_aggregate.py': [Errno 2] No such file or directory
- python code/04_exposure.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/04_exposure.py': [Errno 2] No such file or directory
- python code/05_model.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/05_model.py': [Errno 2] No such file or directory
- python code/06_sensitivity.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/06_sensitivity.py': [Errno 2] No such file or directory
- python code/07_selection_correction.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/07_selection_correction.py': [Errno 2] No such file or directory
- python code/08_visualize.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/08_visualize.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/final/permutation_results.csv
- data/final/regression_summary.csv
- data/final/sensitivity_analysis.csv
- data/processed/ingested_cohort.parquet
- data/processed/user_track_pairs.parquet
- data/processed/user_track_pairs_threshold_X.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/final/permutation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/security.py` — NOT invoked by the run-book
    - `code/generate_permutation_results.py` — NOT invoked by the run-book
    - `code/generate_final_results.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/permutation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/final/regression_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/generate_regression_summary.py` — NOT invoked by the run-book
    - `code/generate_diagnostic_plots.py` — NOT invoked by the run-book
    - `code/security.py` — NOT invoked by the run-book
    - `code/generate_permutation_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/regression_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/final/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/security.py` — NOT invoked by the run-book
    - `code/generate_final_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ingested_cohort.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/generate_ingested_cohort.py` — NOT invoked by the run-book
    - `code/aggregation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ingested_cohort.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/user_track_pairs.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/generate_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/generate_regression_summary.py` — NOT invoked by the run-book
    - `code/generate_diagnostic_plots.py` — NOT invoked by the run-book
    - `code/security.py` — NOT invoked by the run-book
    - `code/aggregation.py` — NOT invoked by the run-book
    - `code/generate_user_track_pairs.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/user_track_pairs.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/user_track_pairs_threshold_X.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/generate_sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/user_track_pairs_threshold_X.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
