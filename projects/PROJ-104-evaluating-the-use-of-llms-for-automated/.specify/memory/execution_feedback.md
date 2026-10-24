# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m src.run_pipeline --sample 5 (rc=1); python -m src.analysis.power_analysis (rc=1); python -m src.run_pipeline --full (rc=1); 1 declared deliverable(s) absent: data/raw/commit_pairs.csv

## Failing / missing run-book commands

- python -m src.run_pipeline --sample 5 -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-104-evaluating-the-use-of-llms-for-automated/bin/python: Error while finding module specification for 'src.run_pipeline' (ModuleNotFoundError: No module named 'src')

- python -m src.analysis.power_analysis -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-104-evaluating-the-use-of-llms-for-automated/bin/python: Error while finding module specification for 'src.analysis.power_analysis' (ModuleNotFoundError: No module named 'src')

- python -m src.run_pipeline --full -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-104-evaluating-the-use-of-llms-for-automated/bin/python: Error while finding module specification for 'src.run_pipeline' (ModuleNotFoundError: No module named 'src')

- python -m pytest tests/contract/ -> rc=1
_________________

    def test_commitpair_csv_schema():
        schema = load_schema()
        csv_path = paths.data("raw", "commit_pairs.csv")
>       assert csv_path.exists(), f"{csv_path} does not exist"
E       AssertionError: /home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/raw/commit_pairs.csv does not exist
E       assert False
E        +  where False = <bound method Path.exists of PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/raw/commit_pairs.csv')>()
E        +    where <bound method Path.exists of PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/raw/commit_pairs.csv')> = PosixPath('/home/runner/work/llmXive/llmXive/projects/PROJ-104-evaluating-the-use-of-llms-for-automated/data/raw/commit_pairs.csv').exists

tests/contract/test_commitpair_schema.py:30: AssertionError
=========================== short test summary info ============================
FAILED tests/contract/test_commitpair_schema.py::test_commitpair_csv_schema
============================== 1 failed in 0.14s ===============================


- python -m pytest tests/unit/ -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive
configfile: pyproject.toml
plugins: anyio-4.15.1
collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/unit/



## Declared deliverables still missing

- data/raw/commit_pairs.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/commit_pairs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data_extraction.py` — NOT invoked by the run-book
    - `code/gold_annotation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/commit_pairs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
