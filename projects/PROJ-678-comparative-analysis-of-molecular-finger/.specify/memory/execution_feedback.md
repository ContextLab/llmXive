# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/download.py (rc=1); python code/fingerprints.py (rc=1); python code/split.py (rc=1); 1 declared deliverable(s) absent: data/processed/organophosphates_filtered.csv

## Failing / missing run-book commands

- python code/download.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/download.py", line 150, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/download.py", line 138, in main
    setup_logging()
    ^^^^^^^^^^^^^
NameError: name 'setup_logging' is not defined
- python code/fingerprints.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/fingerprints.py", line 240, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/fingerprints.py", line 185, in main
    setup_logging()
    ^^^^^^^^^^^^^
NameError: name 'setup_logging' is not defined
- python code/split.py -> rc=1
    2026-07-23 00:51:47,506 - __main__ - INFO - Starting Greedy Maximal Dissimilarity Split
2026-07-23 00:51:47,506 - __main__ - ERROR - Input file not found: data/processed/organophosphates_filtered.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/split.py", line 292, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/split.py", line 253, in main
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: data/processed/organophosphates_filtered.csv
- python code/train.py -> rc=1
    Data file missing: Split file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/data/processed/splits/split_fold_0.pkl
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/train.py", line 327, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/train.py", line 310, in main
    splits = load_split_indices(split_dir)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/train.py", line 43, in load_split_indices
    raise FileNotFoundError(f"Split file not found: {split_file}")
FileNotFoundError: Split file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/data/processed/splits/split_fold_0.pkl
- python code/evaluate.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/evaluate.py", line 16, in <module>
    from report_generator import load_metrics_from_disk, load_statistical_results, load_sc003_results, generate_markdown_table, generate_final_report
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/report_generator.py", line 26, in <module>
    from evaluate import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/evaluate.py", line 16, in <module>
    from report_generator import load_metrics_from_disk, load_statistical_results, load_sc003_results, generate_markdown_table, generate_final_report
ImportError: cannot import name 'load_metrics_from_disk' from partially initialized module 'report_generator' (most likely due to a circular import) (/home/runner/work/llmXive/llmXive/projects/PROJ-678-comparative-analysis-of-molecular-finger/code/report_generator.py)

## Declared deliverables still missing

- data/processed/organophosphates_filtered.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/organophosphates_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/split.py` — IS a run-book command
    - `code/fingerprints.py` — IS a run-book command
    - `code/filter.py` — IS a run-book command
    - `code/train.py` — IS a run-book command
    - `code/evaluate.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/organophosphates_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/organophosphates_filtered.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/split.py`, `code/fingerprints.py`, `code/filter.py`, `code/train.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/organophosphates_filtered.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/split.py`, `code/fingerprints.py`, `code/filter.py`, `code/train.py`, `code/evaluate.py`.
