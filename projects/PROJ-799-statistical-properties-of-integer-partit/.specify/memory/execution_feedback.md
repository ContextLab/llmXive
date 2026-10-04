# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/generate_partitions.py --n_max 50000`
  - script usage: `generate_partitions.py [-h] [--n-max N_MAX]`
  - argparse error: `generate_partitions.py: error: unrecognized arguments: --n_max 50000`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/regression_analysis.py; python code/validation.py; 2 command(s) failed: python code/generate_partitions.py --n_max 50000 (rc=2); python code/feature_engineering.py (rc=1); 3 declared deliverable(s) absent: data/processed/features.csv; data/raw/partitions_raw.csv; data/reference_values.csv

## Failing / missing run-book commands

- python code/generate_partitions.py --n_max 50000 -> rc=2
    usage: generate_partitions.py [-h] [--n-max N_MAX]
generate_partitions.py: error: unrecognized arguments: --n_max 50000
- python code/feature_engineering.py -> rc=1
    Loading partition data from data/raw/partitions_raw.csv...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-799-statistical-properties-of-integer-partit/code/feature_engineering.py", line 311, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-799-statistical-properties-of-integer-partit/code/feature_engineering.py", line 290, in main
    n_values, p_P_n, Q_as_n = load_partition_data(input_path)
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-799-statistical-properties-of-integer-partit/code/feature_engineering.py", line 24, in load_partition_data
    with open(filepath, 'r', newline='') as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/partitions_raw.csv'
- python code/regression_analysis.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-799-statistical-properties-of-integer-partit/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-799-statistical-properties-of-integer-partit/code/regression_analysis.py': [Errno 2] No such file or directory
- python code/validation.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-799-statistical-properties-of-integer-partit/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-799-statistical-properties-of-integer-partit/code/validation.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/features.csv
- data/raw/partitions_raw.csv
- data/reference_values.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/regression_model.py` — NOT invoked by the run-book
    - `code/feature_engineering.py` — IS a run-book command
    - `code/visualize_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/partitions_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/feature_engineering.py` — IS a run-book command
    - `code/generate_partitions.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/partitions_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/reference_values.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_partitions.py` — IS a run-book command
    - `code/generate_reference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/reference_values.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/raw/partitions_raw.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/feature_engineering.py`, `code/generate_partitions.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/partitions_raw.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/feature_engineering.py`, `code/generate_partitions.py`.
