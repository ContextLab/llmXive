# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/download_data.py (rc=1); python code/preprocess.py (rc=1); python code/train_models.py (rc=1); 4 declared deliverable(s) absent: data/processed/X_derived.csv; data/processed/X_raw.csv; data/processed/cleaned_316L.csv

## Failing / missing run-book commands

- python code/download_data.py -> rc=1
    2026-09-26 02:50:58,426 - root - INFO - Using dataset URL from research.md: https://zenodo.org/records/10068024
2026-09-26 02:50:58,959 - root - WARNING - Could not definitively verify 316L material type from metadata, proceeding with filename check.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/download_data.py", line 280, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/download_data.py", line 263, in main
    verify_material_type(metadata, target_file_name)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/download_data.py", line 200, in verify_material_type
    raise ValueError(f"Material verification failed: Dataset does not appear to be for 316L stainless steel. File: {file_name}")
ValueError: Material verification failed: Dataset does not appear to be for 316L stainless steel. File: scGSEA_script.R
- python code/preprocess.py -> rc=1
    2026-09-26 02:50:59,674 - utils - INFO - Starting preprocessing of data/raw/316L_LPBF_dataset.csv
2026-09-26 02:50:59,674 - utils - ERROR - File not found: Input file not found: data/raw/316L_LPBF_dataset.csv
- python code/train_models.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/train_models.py", line 23, in <module>
    logger = setup_logging("train_models")
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-363-predicting-the-impact-of-additive-manufa/code/utils.py", line 31, in setup_logging
    logging.basicConfig(
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 2062, in basicConfig
    root.setLevel(level)
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 1464, in setLevel
    self.level = _checkLevel(level)
                 ^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.16/x64/lib/python3.11/logging/__init__.py", line 207, in _checkLevel
    raise ValueError("Unknown level: %r" % level)
ValueError: Unknown level: 'train_models'
- python code/analyze_explainability.py -> rc=1
    2026-09-26 02:51:04,742 - utils - INFO - Starting Explainability Analysis (US3)
2026-09-26 02:51:04,742 - utils - ERROR - State file not found: state/selected_model.yaml. Ensure T028 has run.

## Declared deliverables still missing

- data/processed/X_derived.csv
- data/processed/X_raw.csv
- data/processed/cleaned_316L.csv
- data/processed/degenerate_flag.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/X_derived.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
    - `code/analyze_explainability.py` — IS a run-book command
    - `code/train_models.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/X_derived.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/X_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
    - `code/analyze_explainability.py` — IS a run-book command
    - `code/train_models.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/X_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_316L.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
    - `code/validate_quickstart.py` — NOT invoked by the run-book
    - `code/analyze_explainability.py` — IS a run-book command
    - `code/train_models.py` — IS a run-book command
    - `code/save_significance_report.py` — NOT invoked by the run-book
    - `code/save_processed_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_316L.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/degenerate_flag.json` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
    - `code/orchestration_check.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/degenerate_flag.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/cleaned_316L.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/preprocess.py`, `code/analyze_explainability.py`, `code/train_models.py`, `code/save_significance_report.py`, `code/save_processed_data.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/cleaned_316L.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/preprocess.py`, `code/validate_quickstart.py`, `code/analyze_explainability.py`, `code/train_models.py`, `code/save_significance_report.py`, `code/save_processed_data.py`.

### `data/raw/316L_LPBF_dataset.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/preprocess.py`, `code/save_processed_data.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/316L_LPBF_dataset.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/preprocess.py`, `code/download_data.py`, `code/save_processed_data.py`.

### `models/artifacts/best_raw_model.pkl`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/analyze_explainability.py`, `code/train_models.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `models/artifacts/best_raw_model.pkl`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/analyze_explainability.py`, `code/train_models.py`.
