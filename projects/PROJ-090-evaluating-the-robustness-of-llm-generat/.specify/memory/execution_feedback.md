# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 6 declared deliverable(s) absent: data/logs/halt_report.json; data/processed/calibration_report.json; data/processed/inference_logs.json

## Failing / missing run-book commands

- python -c "import datasets; d = datasets.load_dataset('openai/openai_humaneval', split='test'); print(f'Loaded {len(d)} tasks')" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-090-evaluating-the-robustness-of-llm-generat/code/.venv/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-090-evaluating-the-robustness-of-llm-generat/code/.venv/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-090-evaluating-the-robustness-of-llm-generat/code/.venv/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/main.py -> rc=1

2026-10-09 23:26:24,411 - llmXive.budget - INFO - Starting Budget Cap Enforcer (T029b)...
2026-10-09 23:26:24 - llmXive.budget - INFO - Starting Budget Cap Enforcer (T029b)...
2026-10-09 23:26:24,411 - llmXive.budget - INFO - Loading feasibility config from data/config/feasibility.json
2026-10-09 23:26:24 - llmXive.budget - INFO - Loading feasibility config from data/config/feasibility.json
2026-10-09 23:26:24,411 - llmXive.budget - INFO - Budget cap determined: 4 samples
2026-10-09 23:26:24 - llmXive.budget - INFO - Budget cap determined: 4 samples
2026-10-09 23:26:24,411 - llmXive.budget - INFO - Loading original HumanEval tasks...
2026-10-09 23:26:24 - llmXive.budget - INFO - Loading original HumanEval tasks...
2026-10-09 23:26:24,411 - llmXive.budget - ERROR - Data file missing: Original HumanEval data not found at data/raw/humaneval.json. Ensure T010 (download) has been executed.
2026-10-09 23:26:24 - llmXive.budget - ERROR - Data file missing: Original HumanEval data not found at data/raw/humaneval.json. Ensure T010 (download) has been executed.


## Declared deliverables still missing

- data/logs/halt_report.json
- data/processed/calibration_report.json
- data/processed/inference_logs.json
- data/processed/perturbation_candidates.json
- data/processed/perturbation_candidates_raw.json
- data/processed/perturbation_candidates_validated.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/logs/halt_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/filter_perturbations.py` — NOT invoked by the run-book
    - `code/data/semantic_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/logs/halt_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/calibration_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/model/confidence_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/calibration_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/inference_logs.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/statistics.py` — NOT invoked by the run-book
    - `code/model/confidence_metrics.py` — NOT invoked by the run-book
    - `code/model/inference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/inference_logs.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/perturbation_candidates.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/statistics.py` — NOT invoked by the run-book
    - `code/data/filter_perturbations.py` — NOT invoked by the run-book
    - `code/data/generate_perturbations.py` — NOT invoked by the run-book
    - `code/data/log_perturbation_candidates.py` — NOT invoked by the run-book
    - `code/data/logging_integration.py` — NOT invoked by the run-book
    - `code/data/semantic_validator.py` — NOT invoked by the run-book
    - `code/model/inference.py` — NOT invoked by the run-book
    - `code/utils/logging.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/perturbation_candidates.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/perturbation_candidates_raw.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/generate_perturbations.py` — NOT invoked by the run-book
    - `code/data/semantic_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/perturbation_candidates_raw.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/perturbation_candidates_validated.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/filter_perturbations.py` — NOT invoked by the run-book
    - `code/data/semantic_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/perturbation_candidates_validated.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
