# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/download_data.py`
- `python projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/model_fit.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/download_data.py; python projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/model_fit.py; 1 command(s) failed: python code/preprocess.py (rc=1); 2 declared deliverable(s) absent: data/derived/cleaned_data.csv; data/raw/data.csv

## Failing / missing run-book commands

- python projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/download_data.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/download_data.py': [Errno 2] No such file or directory
- python code/preprocess.py -> rc=1
    2026-09-01 18:14:45,994 - __main__ - INFO - [START] preprocess_pipeline: Starting preprocessing pipeline.
2026-09-01 18:14:45,994 - __main__ - INFO - [START] load_raw_data: Checking path: /home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/data/raw/data.csv
2026-09-01 18:14:45,994 - __main__ - ERROR - Data fetch error: Raw data file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/data/raw/data.csv. Please run code/download.py first to fetch data.
- python projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/model_fit.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/projects/PROJ-150-detecting-statistical-power-drift-in-rep/code/model_fit.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/derived/cleaned_data.csv
- data/raw/data.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/cleaned_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/visualize.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/robustness.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/cleaned_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/update_state.py` — NOT invoked by the run-book
    - `code/run_subset_pipeline.py` — NOT invoked by the run-book
    - `code/validate_source.py` — NOT invoked by the run-book
    - `code/compute_trends.py` — NOT invoked by the run-book
    - `code/visualize.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/data/raw/data.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/run_subset_pipeline.py`, `code/visualize.py`, `code/preprocess.py`, `code/robustness.py`, `code/download.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-150-detecting-statistical-power-drift-in-rep/data/raw/data.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/run_subset_pipeline.py`, `code/validate_source.py`, `code/visualize.py`, `code/preprocess.py`, `code/robustness.py`, `code/download.py`.
