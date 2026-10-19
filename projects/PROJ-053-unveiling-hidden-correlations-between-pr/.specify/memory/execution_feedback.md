# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/main.py --step download (rc=1); python code/main.py --step preprocess (rc=1); python code/main.py --step train (rc=1); 1 declared deliverable(s) absent: data/literature_baseline_importance.json

## Failing / missing run-book commands

- python code/main.py --step download -> rc=1

2026-10-19 00:12:32,477 INFO data_loader: Searching Zenodo for dataset: NIST AM Bench
2026-10-19 00:12:33,155 INFO data_loader: Found 5 candidate record(s).
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 93, in <module>
    run_download_step()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 33, in run_download_step
    download_data_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data_loader.py", line 238, in main
    download_url = _choose_download_url(records)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data_loader.py", line 90, in _choose_download_url
    raise FileNotFoundError(
FileNotFoundError: No file with extensions ('.csv', '.zip', '.xlsx', '.xls') found in the searched Zenodo records.

- python code/main.py --step preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 95, in <module>
    run_preprocess_step()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 37, in run_preprocess_step
    validate_and_preprocess()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/data/preprocess.py", line 227, in validate_and_preprocess
    raise FileNotFoundError(f"No CSV files found in raw data directory: {raw_dir}")
FileNotFoundError: No CSV files found in raw data directory: /home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/data/raw

- python code/main.py --step train -> rc=1

2026-10-19 00:12:35,560 - models.gpr_trainer - INFO - Starting GPR training step...
2026-10-19 00:12:35,560 INFO models.gpr_trainer: Starting GPR training step...
2026-10-19 00:12:35,560 - models.gpr_trainer - ERROR - Processed train or test CSV not found.
2026-10-19 00:12:35,560 ERROR models.gpr_trainer: Processed train or test CSV not found.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 97, in <module>
    run_train_step()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 41, in run_train_step
    train_gpr_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/models/gpr_trainer.py", line 110, in main
    raise FileNotFoundError("Processed data files missing.")
FileNotFoundError: Processed data files missing.

- python code/main.py --step analyze -> rc=1

2026-10-19 00:12:36,796 - importance - INFO - Starting permutation importance analysis...
2026-10-19 00:12:36,796 INFO importance: Starting permutation importance analysis...
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 99, in <module>
    run_analyze_step()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/main.py", line 46, in run_analyze_step
    importance_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/analysis/importance.py", line 157, in main
    test_df = load_test_data()
              ^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/code/analysis/importance.py", line 41, in load_test_data
    raise FileNotFoundError(f"Test CSV not found at {test_path}")
FileNotFoundError: Test CSV not found at /home/runner/work/llmXive/llmXive/projects/PROJ-053-unveiling-hidden-correlations-between-pr/data/processed/test.csv


## Declared deliverables still missing

- data/literature_baseline_importance.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/literature_baseline_importance.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/importance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/literature_baseline_importance.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
