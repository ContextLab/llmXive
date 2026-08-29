# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/filtered_hypothetical_library.csv, data/processed/hypothetical_library.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/filtered_hypothetical_library.csv, data/processed/hypothetical_library.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 1 run-book script(s) missing (plan/impl path mismatch): python main.py; 3 command(s) failed: python code/data/download.py (rc=1); python code/models/train.py (rc=1); python code/models/predict.py (rc=1); 1 declared deliverable(s) absent: data/processed/features.csv

## Failing / missing run-book commands

- python main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/main.py': [Errno 2] No such file or directory
- python code/data/download.py -> rc=1
    29 13:26:56 - pipeline - INFO - [EVENT] Starting T013: Data Ingestion
2026-08-29 13:26:56 - __main__ - WARNING - Materials Project API key not found. Skipping MP fetch.
2026-08-29 13:26:56 - __main__ - INFO - MP fetched: 0 entries.
2026-08-29 13:26:56 - __main__ - INFO - MP entries (0) < 5000. Fetching OQMD...
2026-08-29 13:26:57 - __main__ - ERROR - Failed to fetch from OQMD: Expecting value: line 1 column 1 (char 0)
2026-08-29 13:26:57 - __main__ - INFO - OQMD fetched: 0 entries. Total: 0
2026-08-29 13:26:57 - __main__ - INFO - After filtering: 0 entries.
2026-08-29 13:26:57 - __main__ - ERROR - Fatal Error: Total valid entries (0) is below the required minimum of 5000 after exhausting all sources.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/data/download.py", line 269, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/data/download.py", line 255, in main
    raise RuntimeError(error_msg)
RuntimeError: Fatal Error: Total valid entries (0) is below the required minimum of 5000 after exhausting all sources.
- python code/models/train.py -> rc=1
    2026-08-29 13:26:59 - pipeline - INFO - [EVENT] Training Pipeline Started
2026-08-29 13:26:59 - __main__ - INFO - Loading data from data/processed/features.csv

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/models/train.py", line 190, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/models/train.py", line 155, in main
    df = load_data(args.input)
         ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/models/train.py", line 27, in load_data
    raise FileNotFoundError(f"Input file not found: {input_path}")
FileNotFoundError: Input file not found: data/processed/features.csv
- python code/models/predict.py -> rc=1
    6-08-29 13:26:59 - __main__ - INFO - Generated 100 combinations.
2026-08-29 13:26:59 - __main__ - INFO - Saved generated library to data/processed/hypothetical_library.csv
2026-08-29 13:26:59 - __main__ - INFO - Calculating geometric feasibility (tolerance factor)...
2026-08-29 13:26:59 - __main__ - INFO - Filtered library: 90 feasible out of 100 candidates (excluded 10 based on 0.8 <= t <= 1.1).
2026-08-29 13:26:59 - __main__ - INFO - Saved filtered library to data/processed/filtered_hypothetical_library.csv

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/models/predict.py", line 337, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/models/predict.py", line 325, in main
    model = load_model(model_path)
            ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-186-predicting-the-stability-of-perovskite-s/code/models/predict.py", line 204, in load_model
    raise FileNotFoundError(f"Model file not found: {model_path}")
FileNotFoundError: Model file not found: results/model.pkl

## Declared deliverables still missing

- data/processed/features.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validate.py` — NOT invoked by the run-book
    - `code/viz/plot.py` — NOT invoked by the run-book
    - `code/models/screening_full.py` — NOT invoked by the run-book
    - `code/models/predict.py` — IS a run-book command
    - `code/models/model_utils.py` — NOT invoked by the run-book
    - `code/models/train.py` — IS a run-book command
    - `code/data/verify_nulls.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/features.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/viz/plot.py`, `code/models/train.py`, `code/data/preprocess.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/features.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/quickstart_validate.py`, `code/viz/plot.py`, `code/models/train.py`, `code/data/verify_nulls.py`, `code/data/preprocess.py`, `code/utils/config.py`.

### `results/model.pkl`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/viz/plot.py`, `code/models/screening_full.py`, `code/models/predict.py`, `code/models/train.py`, `code/utils/model_metadata.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `results/model.pkl`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/quickstart_validate.py`, `code/viz/plot.py`, `code/models/screening_full.py`, `code/models/predict.py`, `code/models/train.py`, `code/utils/config.py`, `code/utils/model_metadata.py`.
