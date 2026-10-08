# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/rm_executor.py  --input data/raw/synthetic_puzzles.jsonl  --output data/processed/execution_log.csv  --max-turns 50  --batch-size 5  --device cpu (rc=1); python code/analyzer.py  --puzzles data/raw/synthetic_puzzles.jsonl  --results data/processed/execution_log.csv  --output results/statistical_report.json  --thresholds 40 50 60 (rc=1); 2 declared deliverable(s) absent: data/processed/execution_log.csv; data/processed/extended_budget_log.csv

## Failing / missing run-book commands

- python code/rm_executor.py  --input data/raw/synthetic_puzzles.jsonl  --output data/processed/execution_log.csv  --max-turns 50  --batch-size 5  --device cpu -> rc=1
    2026-10-08 21:29:37,848 - __main__ - ERROR - Input file not found: data/raw/logical_puzzles.jsonl. Please run data generation first.
- python code/analyzer.py  --puzzles data/raw/synthetic_puzzles.jsonl  --results data/processed/execution_log.csv  --output results/statistical_report.json  --thresholds 40 50 60 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/code/analyzer.py", line 9, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python -c "import json; data = [json.loads(l) for l in open('data/raw/synthetic_puzzles.jsonl')]; print(f'Count: {len(data)}'); print(f'Depth Range: {min(d[\"nesting_depth\"] for d in data)}-{max(d[\"nesting_depth\"] for d in data)}')" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/synthetic_puzzles.jsonl'

## Declared deliverables still missing

- data/processed/execution_log.csv
- data/processed/extended_budget_log.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/execution_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_checksums.py` — NOT invoked by the run-book
    - `code/write_execution_results.py` — NOT invoked by the run-book
    - `code/execution_metrics.py` — NOT invoked by the run-book
    - `code/extended_budget_runner.py` — NOT invoked by the run-book
    - `code/analyzer.py` — IS a run-book command
    - `code/batch_processor.py` — NOT invoked by the run-book
    - `code/rm_executor.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/execution_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/extended_budget_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_checksums.py` — NOT invoked by the run-book
    - `code/extended_budget_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/extended_budget_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/raw/logical_puzzles.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/write_execution_results.py`, `code/execution_metrics.py`, `code/extended_budget_runner.py`, `code/batch_processor.py`, `code/rm_executor.py`, `code/perturb_ground_truth.py`, `code/write_puzzles.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/logical_puzzles.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/write_execution_results.py`, `code/checksum_runner.py`, `code/execution_metrics.py`, `code/checksum_generator.py`, `code/extended_budget_runner.py`, `code/batch_processor.py`, `code/rm_executor.py`, `code/perturb_ground_truth.py`, `code/write_puzzles.py`.
