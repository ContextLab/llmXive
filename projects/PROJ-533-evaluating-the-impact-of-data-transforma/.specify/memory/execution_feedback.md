# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python -m code.main --stage all (rc=1); python -m code.main --stage all --resume --run-id your_run_id (rc=1); 2 declared deliverable(s) absent: data/checksums.csv; data/datasets.csv

## Failing / missing run-book commands

- python -m code.main --stage all -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-533-evaluating-the-impact-of-data-transforma/code/main.py", line 5, in <module>
    from code.utils.checkpointing import load_state
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-533-evaluating-the-impact-of-data-transforma/code/utils/__init__.py", line 13, in <module>
    from .statistical_tests import t_test, anova_one_way, shapiro_test, friedman_test
ImportError: cannot import name 'anova_one_way' from 'code.utils.statistical_tests' (/home/runner/work/llmXive/llmXive/projects/PROJ-533-evaluating-the-impact-of-data-transforma/code/utils/statistical_tests.py)

- python -m code.main --stage all --resume --run-id your_run_id -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-533-evaluating-the-impact-of-data-transforma/code/main.py", line 5, in <module>
    from code.utils.checkpointing import load_state
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-533-evaluating-the-impact-of-data-transforma/code/utils/__init__.py", line 13, in <module>
    from .statistical_tests import t_test, anova_one_way, shapiro_test, friedman_test
ImportError: cannot import name 'anova_one_way' from 'code.utils.statistical_tests' (/home/runner/work/llmXive/llmXive/projects/PROJ-533-evaluating-the-impact-of-data-transforma/code/utils/statistical_tests.py)


## Declared deliverables still missing

- data/checksums.csv
- data/datasets.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checksums.csv` is declared but was NOT written. Scripts referencing it:
    - `code/checksum_datasets.py` — NOT invoked by the run-book
    - `code/download_datasets.py` — NOT invoked by the run-book
    - `code/extract_metadata.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/update_artifact_hashes.py` — NOT invoked by the run-book
    - `code/utils/schema_definitions.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/checksums.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/datasets.csv` is declared but was NOT written. Scripts referencing it:
    - `code/apply_transformations.py` — NOT invoked by the run-book
    - `code/checksum_datasets.py` — NOT invoked by the run-book
    - `code/download_datasets.py` — NOT invoked by the run-book
    - `code/extract_metadata.py` — NOT invoked by the run-book
    - `code/filter_datasets.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/utils/schema_definitions.py` — NOT invoked by the run-book
    - `code/utils/streaming_utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/datasets.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
