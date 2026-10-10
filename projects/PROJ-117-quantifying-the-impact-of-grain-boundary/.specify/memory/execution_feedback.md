# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/download.py (rc=1); python code/preprocess.py (rc=1); python code/train.py (rc=1); 2 declared deliverable(s) absent: data/processed/cleaned_dataset.parquet; data/processed/parsed_geometry.parquet

## Failing / missing run-book commands

- python code/download.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/download.py", line 25, in <module>
    logger = setup_logging()
             ^^^^^^^^^^^^^^^
TypeError: setup_logging() missing 1 required positional argument: 'name'

- python code/preprocess.py -> rc=1
2026-10-10 02:28:24 - preprocess - INFO - Starting preprocessing pipeline
2026-10-10 02:28:24 - preprocess - ERROR - Unexpected error during preprocessing: Input file not found: data/processed/parsed_geometry.parquet

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/preprocess.py", line 286, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/preprocess.py", line 255, in main
    df = load_parsed_data()
         ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/preprocess.py", line 28, in load_parsed_data
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: data/processed/parsed_geometry.parquet

- python code/train.py -> rc=1
2026-10-10 02:28:26 - train - ERROR - Cleaned dataset not found at data/processed/cleaned_dataset.parquet. Run preprocess.py first.


- python code/validate.py -> rc=1
2026-10-10 02:28:27 - validate - ERROR - Validation failed: Model file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/models/best_model.json. Run T012b first.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/validate.py", line 275, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/validate.py", line 241, in main
    X_test, y_test, model = load_model_and_data()
                            ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/validate.py", line 39, in load_model_and_data
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Run T012b first.")
FileNotFoundError: Model file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/models/best_model.json. Run T012b first.

- python code/interpret.py -> rc=1
2026-10-10 02:28:30 - interpret - INFO - Starting interpretability analysis...
2026-10-10 02:28:30 - interpret - INFO - Loaded threshold justification: Fundamentals and Catalytic Applications of CeO₂-Based Materials, 2016
2026-10-10 02:28:30 - interpret - INFO - Loading model from models/best_model.json
2026-10-10 02:28:30 - interpret - ERROR - Failed to load model or data: Model file not found: models/best_model.json


- python -m pytest tests/ -v -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/.venv/bin/python: No module named pytest


## Declared deliverables still missing

- data/processed/cleaned_dataset.parquet
- data/processed/parsed_geometry.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/diagnostics.py` — IS a run-book command
    - `code/interpret.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/train.py` — IS a run-book command
    - `code/train_final.py` — NOT invoked by the run-book
    - `code/train_tuning.py` — NOT invoked by the run-book
    - `code/validate.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/parsed_geometry.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/parsed_geometry.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
