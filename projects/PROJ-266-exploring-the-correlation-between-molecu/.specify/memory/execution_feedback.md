# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/run_pipeline.py; python code/utils/check_pass_rate.py data/processed/cleaned_dataset.csv; python code/utils/check_success_rate.py data/processed/flexibility_descriptors.csv; 1 command(s) failed: python -m pytest tests/ (rc=2); 4 declared deliverable(s) absent: data/processed/descriptors_raw.csv; data/processed/enriched_data.csv; data/processed/filtered_data.csv

## Failing / missing run-book commands

- python code/run_pipeline.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-266-exploring-the-correlation-between-molecu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-266-exploring-the-correlation-between-molecu/code/run_pipeline.py': [Errno 2] No such file or directory

- python code/utils/check_pass_rate.py data/processed/cleaned_dataset.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-266-exploring-the-correlation-between-molecu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-266-exploring-the-correlation-between-molecu/code/utils/check_pass_rate.py': [Errno 2] No such file or directory

- python code/utils/check_success_rate.py data/processed/flexibility_descriptors.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-266-exploring-the-correlation-between-molecu/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-266-exploring-the-correlation-between-molecu/code/utils/check_success_rate.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
xive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/contract/test_dataset_schema.py - FileNotFoundError: Schema not f...
ERROR tests/test_analysis_multivariate.py
ERROR tests/test_analysis_t019a.py
ERROR tests/test_conformer_gen.py
ERROR tests/test_descriptors.py
ERROR tests/test_logging.py
ERROR tests/test_project_structure.py
ERROR tests/test_retrieval.py
ERROR tests/test_scaling_metric_setup.py
ERROR tests/test_scaling_power_analysis.py
ERROR tests/test_setup.py
!!!!!!!!!!!!!!!!!!! Interrupted: 11 errors during collection !!!!!!!!!!!!!!!!!!!
======================= 16 warnings, 11 errors in 1.64s ========================



## Declared deliverables still missing

- data/processed/descriptors_raw.csv
- data/processed/enriched_data.csv
- data/processed/filtered_data.csv
- data/raw/chembl_caco2_raw.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/descriptors_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/descriptors.py` — NOT invoked by the run-book
    - `code/data/validate_scaling_models.py` — NOT invoked by the run-book
    - `code/utils/generate_transparency_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/enriched_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/analysis.py` — NOT invoked by the run-book
    - `code/data/benchmark_pipeline.py` — NOT invoked by the run-book
    - `code/data/scaling_metric_setup.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/enriched_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/conformer_gen.py` — NOT invoked by the run-book
    - `code/data/descriptors.py` — NOT invoked by the run-book
    - `code/data/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/chembl_caco2_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocessing.py` — NOT invoked by the run-book
    - `code/data/retrieval.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/chembl_caco2_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
