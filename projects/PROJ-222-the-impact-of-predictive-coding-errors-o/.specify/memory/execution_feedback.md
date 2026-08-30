# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/visualize.py; 3 command(s) failed: python code/download.py (rc=1); python code/preprocess.py (rc=1); python code/analysis.py (rc=1); 2 declared deliverable(s) absent: data/processed/exclusion_log.json; data/processed/standardized.csv

## Failing / missing run-book commands

- python code/download.py -> rc=1
    Processing dataset: 42277 from openml
Processing dataset: 42278 from openml
Gate 0 status written to gate0_status.json: blocked - Failed to fetch 42277 from openml; Failed to fetch 42278 from openml

No permission to create OpenML directory at /home/runner/.config! This can result in OpenML-Python not working properly.
/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/download.py:85: FutureWarning: Starting from Version 0.15 `download_data`, `download_qualities`, and `download_features_meta_data` will all be ``False`` instead of ``True`` by default to enable lazy loading. To disable this message until version 0.15 explicitly set `download_data`, `download_qualities`, and `download_features_meta_data` to a bool while calling `get_dataset`.
  dataset = openml.datasets.get_dataset(dataset_id)
Error fetching OpenML dataset 42277: https://www.openml.org/api/v1/xml/data/42277 returned code 111: Unknown dataset - None
Error fetching OpenML dataset 42278: https://www.openml.org/api/v1/xml/data/42278 returned code 111: Unknown dataset - None
- python code/preprocess.py -> rc=1
    2026-08-30 03:20:14,759 - INFO - Processing dataset: dataset_1
2026-08-30 03:20:14,760 - ERROR - Failed to process dataset_1: Dataset dataset_1 not found in /home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/data/raw
2026-08-30 03:20:14,760 - INFO - Processing dataset: dataset_2
2026-08-30 03:20:14,760 - ERROR - Failed to process dataset_2: Dataset dataset_2 not found in /home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/data/raw
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/preprocess.py", line 244, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/preprocess.py", line 241, in main
    run_preprocessing_pipeline(dataset_ids, output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/preprocess.py", line 212, in run_preprocessing_pipeline
    raise ValueError("No datasets were successfully processed.")
ValueError: No datasets were successfully processed.
- python code/analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/analysis.py", line 12, in <module>
    from pingouin import calculate_cohens_d, compute_esci
ImportError: cannot import name 'calculate_cohens_d' from 'pingouin' (/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/.venv/lib/python3.11/site-packages/pingouin/__init__.py)
/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/.venv/lib/python3.11/site-packages/outdated/utils.py:14: OutdatedPackageWarning: The package pingouin is out of date. Your version is 0.5.3, the latest is 0.6.1.
Set the environment variable OUTDATED_IGNORE=1 to disable these warnings.
  return warn(
- python code/visualize.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/visualize.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/exclusion_log.json
- data/processed/standardized.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/exclusion_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/update_readme_exclusions.py` — NOT invoked by the run-book
    - `code/filter_datasets.py` — NOT invoked by the run-book
    - `code/run_preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/standardized.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
    - `code/analysis.py` — IS a run-book command
    - `code/save_markov_artifacts.py` — NOT invoked by the run-book
    - `code/run_t017.py` — NOT invoked by the run-book
    - `code/generate_standardized_output.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/standardized.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
