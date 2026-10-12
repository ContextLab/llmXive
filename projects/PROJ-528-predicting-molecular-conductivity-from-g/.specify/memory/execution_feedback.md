# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/main.py (rc=1); python -m pytest tests/unit/ (rc=2); python -m pytest tests/integration/ (rc=4); 4 declared deliverable(s) absent: data/processed/analysis_summary.json; data/processed/feature_importance.csv; data/processed/model_results.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
a_loader_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/data_loader.py", line 111, in main
    from code.download_dataset import main as download_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/download_dataset.py", line 9, in <module>
    import datasets
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-528-predicting-molecular-conductivity-from-g/lib/python3.11/site-packages/datasets/__init__.py", line 22, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-528-predicting-molecular-conductivity-from-g/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-528-predicting-molecular-conductivity-from-g/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m pytest tests/unit/ -> rc=2
/site-packages/matplotlib/_fontconfig_pattern.py:92
../../.llmxive-venvs/PROJ-528-predicting-molecular-conductivity-from-g/lib/python3.11/site-packages/matplotlib/_fontconfig_pattern.py:92
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-528-predicting-molecular-conductivity-from-g/lib/python3.11/site-packages/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../.llmxive-venvs/PROJ-528-predicting-molecular-conductivity-from-g/lib/python3.11/site-packages/matplotlib/_mathtext.py:45
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-528-predicting-molecular-conductivity-from-g/lib/python3.11/site-packages/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_plot.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
======================== 13 warnings, 1 error in 1.39s =========================


- python -m pytest tests/integration/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.0.0, pluggy-1.6.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g
plugins: anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/integration/



## Declared deliverables still missing

- data/processed/analysis_summary.json
- data/processed/feature_importance.csv
- data/processed/model_results.json
- data/processed/sensitivity_analysis.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis_summary.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/run_analysis_summary.py` — NOT invoked by the run-book
    - `code/run_validation_task.py` — NOT invoked by the run-book
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/feature_importance.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis_summary.py` — NOT invoked by the run-book
    - `code/feature_importance.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_importance.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/model_training.py` — NOT invoked by the run-book
    - `code/run_analysis.py` — NOT invoked by the run-book
    - `code/run_finalize_results.py` — NOT invoked by the run-book
    - `code/run_huckel_vif_loop.py` — NOT invoked by the run-book
    - `code/run_training.py` — NOT invoked by the run-book
    - `code/run_validation_task.py` — NOT invoked by the run-book
    - `code/save_model_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/run_finalize_results.py` — NOT invoked by the run-book
    - `code/run_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/save_model_results.py` — NOT invoked by the run-book
    - `code/save_sensitivity_results.py` — NOT invoked by the run-book
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
