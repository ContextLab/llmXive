# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/pipeline.py --config code/config.py; 1 command(s) failed: python code/downloader.py --dataset NJU-LINK/TELBench --output data/raw/tebench_raw.json (rc=1); 3 declared deliverable(s) absent: data/processed/metrics.csv; data/processed/test_metrics.csv; data/processed/threshold_config.json

## Failing / missing run-book commands

- python -c "import pandas, networkx, datasets; print('All imports successful')" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'pandas'
- python code/downloader.py --dataset NJU-LINK/TELBench --output data/raw/tebench_raw.json -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee/code/downloader.py", line 10, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee/code/downloader.py", line 12, in <module>
    raise ImportError(
ImportError: The 'datasets' library is required for streaming TELBench. Please install it via: pip install datasets
- python code/pipeline.py --config code/config.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee/code/pipeline.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/metrics.csv
- data/processed/test_metrics.csv
- data/processed/threshold_config.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/metrics.py` — NOT invoked by the run-book
    - `code/evaluator.py` — NOT invoked by the run-book
    - `code/run_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threshold_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/evaluator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threshold_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
