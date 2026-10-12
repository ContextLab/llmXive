# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/utils/verify_checksums.py; python code/_prune_model.py --retention-pct 50; 2 command(s) failed: python code/01_sensitivity_analysis.py --sample-size '[variable]' --masking-unit head (rc=1); python code/04_statistical_validation.py (rc=1); 4 declared deliverable(s) absent: data/processed/original_faithfulness_scores.csv; data/processed/pruned_faithfulness_scores.csv; data/processed/sensitivity_results.csv

## Failing / missing run-book commands

- python code/utils/verify_checksums.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/utils/verify_checksums.py': [Errno 2] No such file or directory

- python code/01_sensitivity_analysis.py --sample-size '[variable]' --masking-unit head -> rc=1
set
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/01_sensitivity_analysis.py", line 22, in <module>
    from utils.dataset_loader import load_and_cache_dataset, verify_checksum
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/utils/dataset_loader.py", line 23, in <module>
    raise ImportError(
ImportError: The 'datasets' library is required. Install it via: pip install datasets

- python code/_prune_model.py --retention-pct 50 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/_prune_model.py': [Errno 2] No such file or directory

- python code/04_statistical_validation.py -> rc=1
2026-10-12 03:47:51,439 - INFO - Loading original faithfulness scores...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/04_statistical_validation.py", line 300, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/04_statistical_validation.py", line 270, in main
    original_scores = load_faithfulness_scores(original_scores_path)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/04_statistical_validation.py", line 39, in load_faithfulness_scores
    raise FileNotFoundError(f"Faithfulness scores file not found: {file_path}")
FileNotFoundError: Faithfulness scores file not found: data/processed/original_faithfulness_scores.csv


## Declared deliverables still missing

- data/processed/original_faithfulness_scores.csv
- data/processed/pruned_faithfulness_scores.csv
- data/processed/sensitivity_results.csv
- data/processed/statistical_validation_report.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/original_faithfulness_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_statistical_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/original_faithfulness_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pruned_faithfulness_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_statistical_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/pruned_faithfulness_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_sensitivity_analysis.py` — IS a run-book command
    - `code/02_prune_model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_statistical_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/statistical_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
