# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 run-book script(s) missing (plan/impl path mismatch): python main.py --stage download; python main.py --stage preprocess; python main.py --stage entropy; 1 command(s) failed: python -m pytest tests/ (rc=1); 8 declared deliverable(s) absent: data/processed/behavioral_scores.csv; data/processed/effect_sizes.json; data/processed/entropy_metrics.csv

## Failing / missing run-book commands

- python -c "import mne; import neurokit2; import statsmodels; print('All imports OK')" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'neurokit2'

- python main.py --stage download -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-454-investigating-the-relationship-between-n/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-454-investigating-the-relationship-between-n/main.py': [Errno 2] No such file or directory

- python main.py --stage preprocess -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-454-investigating-the-relationship-between-n/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-454-investigating-the-relationship-between-n/main.py': [Errno 2] No such file or directory

- python main.py --stage entropy -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-454-investigating-the-relationship-between-n/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-454-investigating-the-relationship-between-n/main.py': [Errno 2] No such file or directory

- python main.py --stage analyze -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-454-investigating-the-relationship-between-n/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-454-investigating-the-relationship-between-n/main.py': [Errno 2] No such file or directory

- python main.py --stage sensitivity -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-454-investigating-the-relationship-between-n/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-454-investigating-the-relationship-between-n/main.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-454-investigating-the-relationship-between-n/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/processed/behavioral_scores.csv
- data/processed/effect_sizes.json
- data/processed/entropy_metrics.csv
- data/processed/exclusion_log.csv
- data/processed/sensitivity_exclusion_results.csv
- data/processed/sensitivity_report.json
- data/processed/sensitivity_threshold_results.csv
- data/processed/snr_metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/behavioral_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/012b_extract_behavioral_scores.py` — NOT invoked by the run-book
    - `code/012c_extract_behavioral_scores.py` — NOT invoked by the run-book
    - `code/02_extract_behavior.py` — NOT invoked by the run-book
    - `code/02_extract_behavioral.py` — NOT invoked by the run-book
    - `code/04_regression_analysis.py` — NOT invoked by the run-book
    - `code/05_generate_report.py` — NOT invoked by the run-book
    - `code/generate_data_flow_diagram.py` — NOT invoked by the run-book
    - `code/generate_methodology_notes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/behavioral_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/effect_sizes.json` is declared but was NOT written. Scripts referencing it:
    - `code/05_generate_report.py` — NOT invoked by the run-book
    - `code/utils/stats_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/effect_sizes.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/entropy_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_regression_analysis.py` — NOT invoked by the run-book
    - `code/compute_entropy.py` — NOT invoked by the run-book
    - `code/generate_data_flow_diagram.py` — NOT invoked by the run-book
    - `code/utils/entropy_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/entropy_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_validate_data.py` — NOT invoked by the run-book
    - `code/02_preprocess_eeg.py` — NOT invoked by the run-book
    - `code/generate_data_flow_diagram.py` — NOT invoked by the run-book
    - `code/utils/logging_config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_exclusion_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_sensitivity_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_exclusion_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/05_generate_report.py` — NOT invoked by the run-book
    - `code/generate_data_flow_diagram.py` — NOT invoked by the run-book
    - `code/generate_sensitivity_report.py` — NOT invoked by the run-book
    - `code/validate_json_schema.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_threshold_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_regression_analysis.py` — NOT invoked by the run-book
    - `code/generate_sensitivity_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_threshold_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/snr_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/02_preprocess_eeg.py` — NOT invoked by the run-book
    - `code/generate_data_flow_diagram.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/snr_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
