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
runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/.venv/lib/python3.11/site-packages/datasets/load.py", line 1134, in dataset_module_factory
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
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/logging_config.py", line 73, in handle_data_insufficient
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
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/logging_config.py", line 86, in handle_power_warning
    raise error
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/03_train.py", line 292, in main
    df = load_cleaned_data()
         ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/code/03_train.py", line 34, in load_cleaned_data
    raise DataInsufficientError(f"Cleaned dataset not found at {data_path}. Run 02_preprocess.py first.")
exceptions.DataInsufficientError: Cleaned dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/data/raw/processed/dataset_cleaned.csv. Run 02_preprocess.py first.

- python code/04_evaluate.py -> rc=1
2026-10-10 03:15:27,065 - INFO - Starting evaluation phase (T019/T020)
2026-10-10 03:15:27,066 - ERROR - Data loading failed: Data file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-278-predicting-the-diffusion-of-carbon-in-bc/data/processed/dataset_cleaned.csv


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

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/dataset_cleaned.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_preprocess.py` — IS a run-book command
    - `code/03_train.py` — IS a run-book command
    - `code/04_evaluate.py` — IS a run-book command
    - `code/05_validate.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/dataset_cleaned.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
