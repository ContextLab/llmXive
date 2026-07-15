# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/validation_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/validation_report.json) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 4 command(s) failed: python code/download.py (rc=1); python code/preprocess.py (rc=1); python code/features.py (rc=1); 2 declared deliverable(s) absent: data/processed/lzc_metrics.csv; data/processed/pe_metrics.csv

## Failing / missing run-book commands

- python code/download.py -> rc=1
    2026-07-15 08:33:30,626 - download - INFO - Starting data retrieval and validation pipeline.
2026-07-15 08:33:30,628 - download - INFO - Attempting to fetch Sleep-EDF dataset...
2026-07-15 08:33:30,628 - download - ERROR - Failed to fetch Sleep-EDF: No module named 'datasets'
2026-07-15 08:33:30,628 - download - INFO - Attempting to fetch SHHS dataset as fallback...
2026-07-15 08:33:30,628 - download - ERROR - Failed to fetch SHHS: No module named 'datasets'
2026-07-15 08:33:30,629 - download - INFO - Validation report written to /home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/data/processed/validation_report.json
2026-07-15 08:33:30,629 - download - ERROR - Validation failed for all sources.
2026-07-15 08:33:30,629 - download - ERROR - Halting with exit code 1.
- python code/preprocess.py -> rc=1
    2026-07-15 08:33:30,844 - preprocess - INFO - Starting preprocessing pipeline

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/preprocess.py", line 310, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/preprocess.py", line 281, in main
    processed_data, summary = process_eeg_stream(stream, config, logger)
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/preprocess.py", line 214, in process_eeg_stream
    for filename, raw in stream:
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-470-predicting-cognitive-fatigue-from-restin/code/preprocess.py", line 25, in stream_eeg_files
    raise FileNotFoundError(f"Data directory not found: {data_dir}")
FileNotFoundError: Data directory not found: data/raw
- python code/features.py -> rc=1
    2026-07-15 08:33:31,149 - features - INFO - Starting feature extraction pipeline
2026-07-15 08:33:31,149 - features - INFO - Input: data/processed/preprocessed_eeg.npy
2026-07-15 08:33:31,149 - features - INFO - Output LZC: data/processed/lzc_metrics.csv
2026-07-15 08:33:31,149 - features - INFO - Output PE: data/processed/pe_metrics.csv
2026-07-15 08:33:31,149 - features - INFO - Loading preprocessed EEG data from data/processed/preprocessed_eeg.npy
2026-07-15 08:33:31,149 - features - ERROR - Data file not found: Preprocessed data not found at data/processed/preprocessed_eeg.npy
- python code/analysis.py -> rc=1
    2026-07-15 08:33:32,182 - __main__ - INFO - Starting analysis pipeline.
2026-07-15 08:33:32,184 - __main__ - ERROR - Complexity metrics file not found: data/processed/complexity_metrics.csv

## Declared deliverables still missing

- data/processed/lzc_metrics.csv
- data/processed/pe_metrics.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/lzc_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/collinearity.py` — NOT invoked by the run-book
    - `code/features.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/lzc_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pe_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/collinearity.py` — NOT invoked by the run-book
    - `code/features.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/pe_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/complexity_metrics.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/complexity_metrics.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/analysis.py`.

### `data/processed/preprocessed_eeg.npy`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/profile_memory.py`, `code/features.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/preprocessed_eeg.npy`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/profile_memory.py`, `code/features.py`.
