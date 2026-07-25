# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/report.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/download.py (rc=1); python code/preprocess.py (rc=1); python code/features.py (rc=1); 1 declared deliverable(s) absent: data/processed/lzc_metrics.csv

## Failing / missing run-book commands

- python code/download.py -> rc=1
    
- python code/preprocess.py -> rc=1
    2026-07-25 10:14:41,440 - preprocess - INFO - Starting preprocessing pipeline
2026-07-25 10:14:41,442 - preprocess - WARNING - No EEG files found in data/raw
2026-07-25 10:14:41,442 - preprocess - ERROR - Pipeline failed: save_exclusion_log_csv() takes 1 positional argument but 2 were given
- python code/features.py -> rc=1
    2026-07-25 10:14:43,046 - features - INFO - Starting Permutation Entropy calculation pipeline
2026-07-25 10:14:43,046 - features - ERROR - Processed data directory not found: data/processed
- python code/analysis.py -> rc=1
    2026-07-25 10:14:44,183 - __main__ - INFO - Starting analysis pipeline.
2026-07-25 10:14:44,183 - __main__ - ERROR - Features file not found: data/processed/lzc_metrics.csv

INFO:__main__:Starting analysis pipeline.
ERROR:__main__:Features file not found: data/processed/lzc_metrics.csv
- python code/report.py -> rc=1
    

## Declared deliverables still missing

- data/processed/lzc_metrics.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/lzc_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/lzc_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/lzc_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/lzc_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/analysis.py`.
