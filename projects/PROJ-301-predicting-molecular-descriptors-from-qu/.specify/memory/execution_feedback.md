# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/analyze_results.py`
- `python code/extract_features.py`
- `python code/train_models.py`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/01_data_download.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/extract_features.py; python code/train_models.py; python code/analyze_results.py; 1 command(s) failed: python code/01_data_download.py (rc=1); 7 declared deliverable(s) absent: data/checksums.json; data/processed/features_2d.npy; data/processed/features_3d.npy

## Failing / missing run-book commands

- python code/01_data_download.py -> rc=1
    ^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-301-predicting-molecular-descriptors-from-qu/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1696, in load_dataset
    builder_instance = load_dataset_builder(
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-301-predicting-molecular-descriptors-from-qu/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1323, in load_dataset_builder
    dataset_module = dataset_module_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-301-predicting-molecular-descriptors-from-qu/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1209, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-301-predicting-molecular-descriptors-from-qu/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1166, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'lisn/QM9' doesn't exist on the Hub or cannot be accessed.
- python code/extract_features.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-301-predicting-molecular-descriptors-from-qu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-301-predicting-molecular-descriptors-from-qu/code/extract_features.py': [Errno 2] No such file or directory
- python code/train_models.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-301-predicting-molecular-descriptors-from-qu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-301-predicting-molecular-descriptors-from-qu/code/train_models.py': [Errno 2] No such file or directory
- python code/analyze_results.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-301-predicting-molecular-descriptors-from-qu/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-301-predicting-molecular-descriptors-from-qu/code/analyze_results.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/checksums.json
- data/processed/features_2d.npy
- data/processed/features_3d.npy
- data/processed/labels_test.csv
- data/processed/labels_train.csv
- data/processed/molecules_cleaned.parquet
- data/raw/qm9_full.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_data_download.py` — IS a run-book command
  Make ONE of these WRITE `data/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features_2d.npy` is declared but was NOT written. Scripts referencing it:
    - `code/02_feature_extraction.py` — NOT invoked by the run-book
    - `code/04_model_training.py` — NOT invoked by the run-book
    - `code/03_model_training.py` — NOT invoked by the run-book
    - `code/04_analysis.py` — NOT invoked by the run-book
    - `code/05_quickstart_validator.py` — NOT invoked by the run-book
    - `code/utils/models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features_2d.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/features_3d.npy` is declared but was NOT written. Scripts referencing it:
    - `code/02_feature_extraction.py` — NOT invoked by the run-book
    - `code/04_model_training.py` — NOT invoked by the run-book
    - `code/03_model_training.py` — NOT invoked by the run-book
    - `code/04_analysis.py` — NOT invoked by the run-book
    - `code/05_quickstart_validator.py` — NOT invoked by the run-book
    - `code/utils/models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features_3d.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/labels_test.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_feature_extraction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/labels_test.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/labels_train.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_feature_extraction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/labels_train.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/molecules_cleaned.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/02_feature_extraction.py` — NOT invoked by the run-book
    - `code/04_model_training.py` — NOT invoked by the run-book
    - `code/02_clean.py` — NOT invoked by the run-book
    - `code/05_optimize_data_loading.py` — NOT invoked by the run-book
    - `code/05_quickstart_validator.py` — NOT invoked by the run-book
    - `code/extract.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/molecules_cleaned.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/qm9_full.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/02_clean.py` — NOT invoked by the run-book
    - `code/01_data_download.py` — IS a run-book command
    - `code/05_quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/qm9_full.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
