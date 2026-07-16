# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/download.py (rc=1); python code/preprocess.py (rc=1); python code/diagnostics.py (rc=1); 2 declared deliverable(s) absent: data/processed/cleaned_dataset.parquet; data/processed/parsed_geometry.parquet

## Failing / missing run-book commands

- python code/download.py -> rc=1
    7-16 07:39:27 - utils - ERROR - MP_API_KEY not found in environment variables.
2026-07-16 07:39:27 - utils - WARNING - OPENKIM_API_KEY not found. Skipping OpenKIM fetch.
2026-07-16 07:39:27 - utils - INFO - Total records retrieved: 0

Data Insufficiency: Retrieved 0, Valid 0, Required 500
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/download.py", line 239, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/download.py", line 234, in main
    raise_data_insufficiency(retrieved=total_count, required=500)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/utils.py", line 118, in raise_data_insufficiency
    exit_on_insufficiency(retrieved, required, missing_features)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/error_handling.py", line 49, in exit_on_insufficiency
    raise DataInsufficiencyError(error_msg)
error_handling.DataInsufficiencyError: Data Insufficiency: Retrieved 0, Valid 0, Required 500
- python code/preprocess.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/preprocess.py", line 15, in <module>
    from data_streamer import stream_data_source
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/data_streamer.py", line 25, in <module>
    logger = setup_logging("data_streamer")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/utils.py", line 26, in setup_logging
    logger.setLevel(level)
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1464, in setLevel
    self.level = _checkLevel(level)
                 ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 207, in _checkLevel
    raise ValueError("Unknown level: %r" % level)
ValueError: Unknown level: 'data_streamer'
- python code/diagnostics.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/diagnostics.py", line 17, in <module>
    from sklearn.metrics import mutual_info_regression
ImportError: cannot import name 'mutual_info_regression' from 'sklearn.metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/.venv/lib/python3.11/site-packages/sklearn/metrics/__init__.py)
- python code/train.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/train.py", line 18, in <module>
    from preprocess import load_parsed_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/preprocess.py", line 15, in <module>
    from data_streamer import stream_data_source
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/data_streamer.py", line 25, in <module>
    logger = setup_logging("data_streamer")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/utils.py", line 26, in setup_logging
    logger.setLevel(level)
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1464, in setLevel
    self.level = _checkLevel(level)
                 ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 207, in _checkLevel
    raise ValueError("Unknown level: %r" % level)
ValueError: Unknown level: 'data_streamer'
- python code/validate.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/validate.py", line 36, in <module>
    logger = setup_logging("validate")
             ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/utils.py", line 26, in setup_logging
    logger.setLevel(level)
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1464, in setLevel
    self.level = _checkLevel(level)
                 ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 207, in _checkLevel
    raise ValueError("Unknown level: %r" % level)
ValueError: Unknown level: 'validate'
- python code/interpret.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/interpret.py", line 17, in <module>
    logger = setup_logging("interpret")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-117-quantifying-the-impact-of-grain-boundary/code/utils.py", line 26, in setup_logging
    logger.setLevel(level)
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 1464, in setLevel
    self.level = _checkLevel(level)
                 ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/logging/__init__.py", line 207, in _checkLevel
    raise ValueError("Unknown level: %r" % level)
ValueError: Unknown level: 'interpret'

## Declared deliverables still missing

- data/processed/cleaned_dataset.parquet
- data/processed/parsed_geometry.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/interpret.py` — IS a run-book command
    - `code/diagnostics.py` — IS a run-book command
    - `code/train.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/train_final.py` — NOT invoked by the run-book
    - `code/train_tuning.py` — NOT invoked by the run-book
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/validate.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/cleaned_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/parsed_geometry.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/parsed_geometry.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `models/best_model.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/interpret.py`, `code/train.py`, `code/train_final.py`, `code/validate.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `models/best_model.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/interpret.py`, `code/train.py`, `code/train_final.py`, `code/validate_quickstart.py`, `code/validate.py`.
