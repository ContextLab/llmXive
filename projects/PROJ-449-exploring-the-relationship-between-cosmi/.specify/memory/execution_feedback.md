# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/main.py --stage retrieve (rc=1); python code/main.py --stage ratios (rc=1); python code/main.py --stage correlation (rc=1); 4 declared deliverable(s) absent: data/processed/correlation_results.json; data/processed/correlation_summary.csv; data/processed/modulation_amplitudes.csv

## Failing / missing run-book commands

- python code/main.py --stage retrieve -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/main.py", line 21, in <module>
    from code.utils.logging import setup_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/utils/__init__.py", line 2, in <module>
    from code.utils.config import CONFIG
ImportError: cannot import name 'CONFIG' from 'code.utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/utils/config.py)
- python code/main.py --stage ratios -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/main.py", line 21, in <module>
    from code.utils.logging import setup_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/utils/__init__.py", line 2, in <module>
    from code.utils.config import CONFIG
ImportError: cannot import name 'CONFIG' from 'code.utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/utils/config.py)
- python code/main.py --stage correlation -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/main.py", line 21, in <module>
    from code.utils.logging import setup_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/utils/__init__.py", line 2, in <module>
    from code.utils.config import CONFIG
ImportError: cannot import name 'CONFIG' from 'code.utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/utils/config.py)
- python code/main.py --stage bootstrap -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/main.py", line 21, in <module>
    from code.utils.logging import setup_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/utils/__init__.py", line 2, in <module>
    from code.utils.config import CONFIG
ImportError: cannot import name 'CONFIG' from 'code.utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/utils/config.py)
- python code/main.py --stage model -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/main.py", line 21, in <module>
    from code.utils.logging import setup_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/utils/__init__.py", line 2, in <module>
    from code.utils.config import CONFIG
ImportError: cannot import name 'CONFIG' from 'code.utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/utils/config.py)
- python code/main.py --stage all -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/main.py", line 21, in <module>
    from code.utils.logging import setup_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/utils/__init__.py", line 2, in <module>
    from code.utils.config import CONFIG
ImportError: cannot import name 'CONFIG' from 'code.utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-449-exploring-the-relationship-between-cosmi/code/utils/config.py)

## Declared deliverables still missing

- data/processed/correlation_results.json
- data/processed/correlation_summary.csv
- data/processed/modulation_amplitudes.csv
- data/processed/unified_timeseries.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/correlation_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/visualization.py` — NOT invoked by the run-book
    - `code/analysis/validate_pvalues.py` — NOT invoked by the run-book
    - `code/analysis/bootstrap.py` — NOT invoked by the run-book
    - `code/analysis/save_correlation_results.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/visualization.py` — NOT invoked by the run-book
    - `code/analysis/save_correlation_results.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/modulation_amplitudes.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/model_validation.py` — NOT invoked by the run-book
    - `code/analysis/model_fitting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/modulation_amplitudes.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/unified_timeseries.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/align_data.py` — NOT invoked by the run-book
    - `code/data/validate_coverage.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/analysis/model_fitting.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/unified_timeseries.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
