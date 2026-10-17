# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m code.main --thin (rc=1); python code/main.py  --max-samples 2000  --mc-dropout-passes 50  --ensemble-size 3  --coverage-sweep-start 0.80  --coverage-sweep-stop 0.99  --coverage-sweep-step 0.01  --seed 42 (rc=1); 4 declared deliverable(s) absent: data/results/cost_metrics.csv; data/results/metrics_raw.csv; data/results/pipeline_log.csv

## Failing / missing run-book commands

- python -m code.main --thin -> rc=1
 line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/main.py", line 31, in <module>
    from download import download_all
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/download.py", line 14, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-737-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-737-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-737-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/main.py  --max-samples 2000  --mc-dropout-passes 50  --ensemble-size 3  --coverage-sweep-start 0.80  --coverage-sweep-stop 0.99  --coverage-sweep-step 0.01  --seed 42 -> rc=1
ost recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/main.py", line 31, in <module>
    from download import download_all
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-737-assessing-uncertainty-quantification-tec/code/download.py", line 14, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-737-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-737-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-737-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4


## Declared deliverables still missing

- data/results/cost_metrics.csv
- data/results/metrics_raw.csv
- data/results/pipeline_log.csv
- data/results/uq_methods.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results/cost_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/cost_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/metrics_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_metrics_raw.py` — NOT invoked by the run-book
    - `code/metrics/generate_metrics_raw.py` — NOT invoked by the run-book
    - `code/tests/test_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/metrics_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/pipeline_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/pipeline.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/pipeline_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/uq_methods.csv` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline.py` — NOT invoked by the run-book
    - `code/tests/test_full_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/uq_methods.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
