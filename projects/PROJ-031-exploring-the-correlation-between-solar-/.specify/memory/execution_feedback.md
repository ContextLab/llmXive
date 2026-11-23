# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/main.py (rc=1); python code/validate.py data/processed/aligned_events.csv contracts/aligned_event.schema.yaml (rc=1); 1 declared deliverable(s) absent: data/processed/aligned_events.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-031-exploring-the-correlation-between-solar-/code/main.py", line 20, in <module>
    from validate import main as validate_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-031-exploring-the-correlation-between-solar-/code/validate.py", line 18, in <module>
    from jsonschema import validate, ValidationError, Draft7Validator
ModuleNotFoundError: No module named 'jsonschema'
- python code/validate.py data/processed/aligned_events.csv contracts/aligned_event.schema.yaml -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-031-exploring-the-correlation-between-solar-/code/validate.py", line 18, in <module>
    from jsonschema import validate, ValidationError, Draft7Validator
ModuleNotFoundError: No module named 'jsonschema'

## Declared deliverables still missing

- data/processed/aligned_events.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/aligned_events.csv` is declared but was NOT written. Scripts referencing it:
    - `code/filter_analysis_subset.py` — NOT invoked by the run-book
    - `code/align.py` — NOT invoked by the run-book
    - `code/verify_analysis_subset.py` — NOT invoked by the run-book
    - `code/log_data_quality.py` — NOT invoked by the run-book
    - `code/write_aligned_output.py` — NOT invoked by the run-book
    - `code/validate.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/aligned_events.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/aligned_events.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/filter_analysis_subset.py`, `code/align.py`, `code/log_data_quality.py`, `code/write_aligned_output.py`, `code/validate.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/aligned_events.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/filter_analysis_subset.py`, `code/align.py`, `code/verify_analysis_subset.py`, `code/log_data_quality.py`, `code/write_aligned_output.py`, `code/validate.py`.
