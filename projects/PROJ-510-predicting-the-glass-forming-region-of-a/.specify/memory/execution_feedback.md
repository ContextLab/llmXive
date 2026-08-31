# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/ingestion.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/ingestion.py (rc=1); python code/features.py (rc=1); python code/train.py (rc=1); 2 declared deliverable(s) absent: data/processed/feature_importance.json; data/processed/processed_alloys.csv

## Failing / missing run-book commands

- python code/ingestion.py -> rc=1
    venv/lib/python3.11/site-packages/datasets/load.py", line 1166, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'matsci/glass-forming-ability' doesn't exist on the Hub or cannot be accessed.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py", line 180, in <module>
    run_ingestion()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py", line 146, in run_ingestion
    df = load_glass_data()
         ^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py", line 68, in load_glass_data
    raise ValueError(f"Data fetch failed: {DATASET_NAME} unavailable. Error: {str(e)}")
ValueError: Data fetch failed: matsci/glass-forming-ability unavailable. Error: Dataset 'matsci/glass-forming-ability' doesn't exist on the Hub or cannot be accessed.
- python code/features.py -> rc=1
    Usage: python features.py <input_csv> <output_csv>
- python code/train.py -> rc=1
    10-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv
2026-08-31 05:16:36,434 - __main__ - ERROR - Pipeline failed: Processed data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv. Run ingestion.py first.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py", line 252, in <module>
    run_training()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py", line 190, in run_training
    X_train, X_test, y_train, y_test = load_data()
                                       ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py", line 53, in load_data
    raise FileNotFoundError(f"Processed data not found at {DATA_PATH}. Run ingestion.py first.")
FileNotFoundError: Processed data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv. Run ingestion.py first.
- python code/analyze.py -> rc=1
    2026-08-31 05:16:37,817 - INFO - Starting Analysis Pipeline

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py", line 236, in <module>
    run_analysis()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py", line 181, in run_analysis
    model, df = load_model_and_data(model_path, data_path)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py", line 43, in load_model_and_data
    raise FileNotFoundError(f"Model file not found: {model_path}")
FileNotFoundError: Model file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model.pkl

## Declared deliverables still missing

- data/processed/feature_importance.json
- data/processed/processed_alloys.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/feature_importance.json` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/train.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/feature_importance.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/processed_alloys.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validate_schemas.py` — NOT invoked by the run-book
    - `code/ingestion.py` — IS a run-book command
    - `code/analyze.py` — IS a run-book command
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/train.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/processed_alloys.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model.pkl`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/analyze.py`, `code/train.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model.pkl`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/analyze.py`, `code/train.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/ingestion.py`, `code/analyze.py`, `code/generate_report.py`, `code/train.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/validate_schemas.py`, `code/ingestion.py`, `code/analyze.py`, `code/generate_report.py`, `code/train.py`.
