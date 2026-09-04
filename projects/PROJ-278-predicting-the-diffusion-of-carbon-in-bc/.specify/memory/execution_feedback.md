# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/01_download.py`
- `python code/05_validate.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/01_download.py (rc=1); python code/02_preprocess.py (rc=1); python code/03_train.py (rc=1); 1 declared deliverable(s) absent: data/processed/dataset_cleaned.csv

## Failing / missing run-book commands

- python code/01_download.py -> rc=1
    runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1166, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'MeliDC/MeLiDC' doesn't exist on the Hub or cannot be accessed.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/01_download.py", line 128, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/01_download.py", line 106, in main
    download_file(DATASET_ID, output_file)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/01_download.py", line 78, in download_file
    raise DataInsufficientError(f"Failed to download dataset: {e}")
exceptions.DataInsufficientError: Failed to download dataset: Dataset 'MeliDC/MeLiDC' doesn't exist on the Hub or cannot be accessed.
- python code/02_preprocess.py -> rc=1
    .
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/02_preprocess.py", line 407, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/02_preprocess.py", line 401, in main
    handle_data_insufficient(e)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/logging_config.py", line 52, in handle_data_insufficient
    raise error
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/02_preprocess.py", line 330, in main
    df = load_raw_data()
         ^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/02_preprocess.py", line 37, in load_raw_data
    raise DataInsufficientError(f"Raw dataset not found at {raw_path}. Run 01_download.py first.")
exceptions.DataInsufficientError: Raw dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/data/raw/raw/dataset.parquet. Run 01_download.py first.
- python code/03_train.py -> rc=1
    File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/03_train.py", line 315, in <module>
    sys.exit(main())
             ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/03_train.py", line 308, in main
    handle_power_warning(e)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/logging_config.py", line 58, in handle_power_warning
    raise error
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/03_train.py", line 292, in main
    df = load_cleaned_data()
         ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/03_train.py", line 34, in load_cleaned_data
    raise DataInsufficientError(f"Cleaned dataset not found at {data_path}. Run 02_preprocess.py first.")
exceptions.DataInsufficientError: Cleaned dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/data/raw/processed/dataset_cleaned.csv. Run 02_preprocess.py first.
- python code/04_evaluate.py -> rc=1
    2026-09-04 00:53:53,950 - INFO - Starting evaluation phase (T019/T020)
2026-09-04 00:53:53,950 - ERROR - Data loading failed: Data file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/data/processed/dataset_cleaned.csv
- python code/05_validate.py -> rc=1
    rbon-in-bc/code/01_download.py", line 128, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/01_download.py", line 106, in main
    download_file(DATASET_ID, output_file)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/01_download.py", line 78, in download_file
    raise DataInsufficientError(f"Failed to download dataset: {e}")
exceptions.DataInsufficientError: Failed to download dataset: Dataset 'MeliDC/MeLiDC' doesn't exist on the Hub or cannot be accessed.

ERROR:root:Validation failed with error
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/05_validate.py", line 133, in run_quickstart_validation
    run_script("01_download.py")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/05_validate.py", line 115, in run_script
    raise RuntimeError(f"Script {script_name} failed")
RuntimeError: Script 01_download.py failed
ERROR:root:FAILURE: Validation failed.
ERROR:root:  - Script 01_download.py failed

## Declared deliverables still missing

- data/processed/dataset_cleaned.csv

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `get_path` — defined in `code/config.py`; called 22 way(s):

- code/config.py: 1. get_path(config, "processed", "dataset_cleaned.csv") -> config.data_path / "processed" / "dataset_cleaned.csv"
- code/config.py: 2. get_path(config, "outputs", create=True) -> config.output_path / "outputs" (created if needed)
- code/config.py: 3. get_path("config.yaml") -> returns Path to config.yaml
- code/config.py: 4. get_path("data/processed") -> returns Path relative to project root
- code/config.py: 5. get_path("data/outputs") -> returns Path relative to project root
- code/config.py: 6. get_path() -> returns project root
- code/config.py: # Case: get_path("config.yaml") or get_path("data/processed")
- code/config.py: # Case: get_path(config, "processed", "dataset_cleaned.csv")
- code/03_train.py: data_path = get_path(config, "processed", "dataset_cleaned.csv")
- code/03_train.py: split_config_path = get_path(config, "processed", "split_config.json")
- code/03_train.py: output_dir = get_path(config, "outputs", create=True)
- code/05_validate.py: cleaned_data_path = get_path(config, "data_path", "processed") / "dataset_cleaned.csv"
- code/05_validate.py: model_results_path = get_path(config, "output_path", "outputs") / "model_results.json"
- code/05_validate.py: feature_importance_path = get_path(config, "output_path", "outputs") / "feature_importance.json"
- code/05_validate.py: variance_partition_path = get_path(config, "output_path", "outputs") / "variance_partition.csv"
- code/setup_logging.py: log_file=str(config.get_path("logs") / "pipeline.log"),
- code/setup_logging.py: log_dir = config.get_path("logs")
- code/02_preprocess.py: raw_path = get_path(config, "data_path", "raw") / "dataset.parquet"
- code/02_preprocess.py: out_dir = get_path(config, "data_path", "processed")
- code/04_evaluate.py: config_path = get_path("config.yaml")
- code/04_evaluate.py: data_dir = get_path("data/processed")
- code/04_evaluate.py: output_dir = get_path("data/outputs")

Make `get_path` in `code/config.py` accept ALL of the above.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/dataset_cleaned.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/03_train.py` — IS a run-book command
    - `code/05_validate.py` — IS a run-book command
    - `code/02_preprocess.py` — IS a run-book command
    - `code/04_evaluate.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/dataset_cleaned.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `dataset_cleaned.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/03_train.py`, `code/02_preprocess.py`, `code/04_evaluate.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `dataset_cleaned.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/config.py`, `code/03_train.py`, `code/05_validate.py`, `code/02_preprocess.py`, `code/04_evaluate.py`.

### `home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/data/processed/dataset_cleaned.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/03_train.py`, `code/02_preprocess.py`, `code/04_evaluate.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/data/processed/dataset_cleaned.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/config.py`, `code/03_train.py`, `code/05_validate.py`, `code/02_preprocess.py`, `code/04_evaluate.py`.
