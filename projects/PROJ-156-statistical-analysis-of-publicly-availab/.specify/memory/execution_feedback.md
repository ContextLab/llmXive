# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/scripts/generate_report.py; 4 command(s) failed: python code/scripts/fetch_data.py (rc=1); python code/scripts/preprocess.py (rc=1); python code/scripts/fit_distributions.py (rc=1); 4 declared deliverable(s) absent: data/processed/distribution_fits.csv; data/processed/game_metadata.csv; data/processed/model_results.csv

## Failing / missing run-book commands

- python code/scripts/fetch_data.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/scripts/fetch_data.py", line 16, in <module>
    logging.FileHandler('code/logs/fetch_data.log'),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/logs/fetch_data.log'
- python code/scripts/preprocess.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/scripts/preprocess.py", line 17, in <module>
    logging.FileHandler('code/logs/preprocess.log')
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/logs/preprocess.log'
- python code/scripts/fit_distributions.py -> rc=1
    2026-10-05 10:13:32,877 - INFO - Starting distribution fitting with checkpointing.
2026-10-05 10:13:32,891 - INFO - Loading processed data for 15 games...
2026-10-05 10:13:32,891 - ERROR - Processed data not found: data/processed/run_records.csv. Run preprocessing first.
- python code/scripts/fit_mixed_effects.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/scripts/fit_mixed_effects.py", line 20, in <module>
    from scripts.preprocess import load_config, load_schema, validate_record
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/scripts/preprocess.py", line 17, in <module>
    logging.FileHandler('code/logs/preprocess.log')
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/logs/preprocess.log'
- python code/scripts/generate_report.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/scripts/generate_report.py': [Errno 2] No such file or directory
- python -c "import pandas as pd; df = pd.read_csv('data/processed/run_records.csv'); print(f'Completeness: {df.notna().mean().mean():.2%}')" -> rc=1
    ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 300, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1643, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1907, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-156-statistical-analysis-of-publicly-availab/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 930, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/run_records.csv'

## Declared deliverables still missing

- data/processed/distribution_fits.csv
- data/processed/game_metadata.csv
- data/processed/model_results.csv
- data/processed/run_records.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/distribution_fits.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/fit_distributions.py` — IS a run-book command
    - `code/scripts/validate_distribution_fits.py` — NOT invoked by the run-book
    - `code/scripts/utils/bonferroni.py` — NOT invoked by the run-book
    - `code/tests/test_models.py` — NOT invoked by the run-book
    - `code/tests/test_distribution_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/distribution_fits.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/game_metadata.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/load_game_metadata.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/game_metadata.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/fit_mixed_effects.py` — IS a run-book command
    - `code/tests/test_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/run_records.csv` is declared but was NOT written. Scripts referencing it:
    - `code/scripts/preprocess.py` — IS a run-book command
    - `code/scripts/fit_distributions.py` — IS a run-book command
    - `code/scripts/fit_mixed_effects.py` — IS a run-book command
    - `code/tests/test_distribution_fitting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/run_records.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/run_records.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/scripts/preprocess.py`, `code/scripts/fit_distributions.py`, `code/scripts/fit_mixed_effects.py`, `code/tests/test_distribution_fitting.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/run_records.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/scripts/preprocess.py`, `code/scripts/fit_distributions.py`, `code/scripts/fit_mixed_effects.py`, `code/tests/test_distribution_fitting.py`.
