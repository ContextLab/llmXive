# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/ingestion.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/ingestion.py (rc=1); python code/features.py (rc=1); python code/train.py (rc=1); 4 declared deliverable(s) absent: data/models/sc002_status.json; data/models/statistical_comparison.json; data/processed/processed_alloys.csv

## Failing / missing run-book commands

- python code/ingestion.py -> rc=1
    venv/lib/python3.11/site-packages/datasets/load.py", line 1166, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'matsci/glass-forming-ability' doesn't exist on the Hub or cannot be accessed.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py", line 216, in <module>
    run_ingestion()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py", line 188, in run_ingestion
    df = load_glass_data()
         ^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py", line 96, in load_glass_data
    raise ValueError(f"Data fetch failed: {DATASET_NAME} unavailable. Error: {str(e)}")
ValueError: Data fetch failed: matsci/glass-forming-ability unavailable. Error: Dataset 'matsci/glass-forming-ability' doesn't exist on the Hub or cannot be accessed.
- python code/features.py -> rc=1
    2026-09-09 13:26:21,494 - __main__ - INFO - Starting feature engineering pipeline

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py", line 286, in <module>
    run_features()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py", line 265, in run_features
    raise FileNotFoundError(f"Input file not found: {input_path}. Run ingestion.py first.")
FileNotFoundError: Input file not found: data/processed/processed_alloys_raw.csv. Run ingestion.py first.
- python code/train.py -> rc=1
    2026-09-09 13:26:23,486 - __main__ - INFO - Starting training pipeline

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py", line 175, in <module>
    run_training()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py", line 142, in run_training
    X, y = load_data()
           ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py", line 34, in load_data
    raise FileNotFoundError(f"Processed data not found at {DATA_PATH}. Run ingestion.py first.")
FileNotFoundError: Processed data not found at data/processed/processed_alloys.csv. Run ingestion.py first.
- python code/analyze.py -> rc=1
    2026-09-09 13:26:24,944 - __main__ - ERROR - Baseline model not found at data/models/random_forest_model.pkl.

## Declared deliverables still missing

- data/models/sc002_status.json
- data/models/statistical_comparison.json
- data/processed/processed_alloys.csv
- data/processed/processed_alloys_raw.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/models/sc002_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/t024c_gate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/sc002_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/models/statistical_comparison.json` is declared but was NOT written. Scripts referencing it:
    - `code/t024c_gate.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/validate_schemas.py` — NOT invoked by the run-book
    - `code/statistical_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/statistical_comparison.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/processed_alloys.csv` is declared but was NOT written. Scripts referencing it:
    - `code/train.py` — IS a run-book command
    - `code/analyze.py` — IS a run-book command
    - `code/validate_data_availability.py` — NOT invoked by the run-book
    - `code/ingestion.py` — IS a run-book command
    - `code/features.py` — IS a run-book command
    - `code/validate_data.py` — NOT invoked by the run-book
    - `code/t031_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/processed_alloys.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/processed_alloys_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — IS a run-book command
    - `code/features.py` — IS a run-book command
    - `code/validate_schemas.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/processed_alloys_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/processed_alloys.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/train.py`, `code/analyze.py`, `code/ingestion.py`, `code/features.py`, `code/t031_sensitivity_analysis.py`, `code/generate_report.py`, `code/statistical_test.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/processed_alloys.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/train.py`, `code/analyze.py`, `code/validate_data_availability.py`, `code/features.py`, `code/validate_data.py`, `code/t031_sensitivity_analysis.py`, `code/generate_report.py`, `code/validate_schemas.py`, `code/statistical_test.py`.

### `data/processed/processed_alloys_raw.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/ingestion.py`, `code/features.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/processed_alloys_raw.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/features.py`, `code/validate_schemas.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model.pkl`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/train.py`, `code/analyze.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model.pkl`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/train.py`, `code/analyze.py`, `code/t029b_fallback.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/train.py`, `code/analyze.py`, `code/ingestion.py`, `code/features.py`, `code/t031_sensitivity_analysis.py`, `code/generate_report.py`, `code/statistical_test.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/train.py`, `code/analyze.py`, `code/validate_data_availability.py`, `code/features.py`, `code/validate_data.py`, `code/t031_sensitivity_analysis.py`, `code/generate_report.py`, `code/validate_schemas.py`, `code/statistical_test.py`.
