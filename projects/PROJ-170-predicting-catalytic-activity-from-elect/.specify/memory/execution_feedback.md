# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/download_data.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python code/train_baseline.py; python code/stat_test.py; python code/evaluate_reduced.py; 7 command(s) failed: python code/download_data.py (rc=1); python code/extract_descriptors.py (rc=1); python code/preprocess.py (rc=1); 1 declared deliverable(s) absent: data/processed/aligned_dataset.csv

## Failing / missing run-book commands

- python code/download_data.py -> rc=1
oject/oc20' doesn't exist on the Hub. If the repo is private or gated, make sure to log in with `huggingface-cli login`.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/download_data.py", line 328, in main
    parquet_path = download_oc20_stratified_sample()
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/download_data.py", line 217, in download_oc20_stratified_sample
    raise RuntimeError(f"Failed to fetch OC20 dataset: {e}") from e
RuntimeError: Failed to fetch OC20 dataset: Couldn't find a dataset script at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/open-catalyst-project/oc20/oc20.py or any data file in the same directory. Couldn't find 'open-catalyst-project/oc20' on the Hugging Face Hub either: FileNotFoundError: Dataset 'open-catalyst-project/oc20' doesn't exist on the Hub. If the repo is private or gated, make sure to log in with `huggingface-cli login`.

- python code/extract_descriptors.py -> rc=1
^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/extract_descriptors.py", line 31, in load_oc20_sample
    raise FileNotFoundError(f"OC20 sample not found at {path}")
FileNotFoundError: OC20 sample not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/data/raw/oc20_sample.parquet

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/extract_descriptors.py", line 189, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/extract_descriptors.py", line 161, in main
    oc20_df = load_oc20_sample()
              ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/extract_descriptors.py", line 31, in load_oc20_sample
    raise FileNotFoundError(f"OC20 sample not found at {path}")
FileNotFoundError: OC20 sample not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/data/raw/oc20_sample.parquet

- python code/preprocess.py -> rc=1
/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/preprocess.py", line 45, in load_extracted_descriptors
    raise FileNotFoundError(f"Unified dataset not found at {path}")
FileNotFoundError: Unified dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/data/processed/unified_dataset.parquet

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/preprocess.py", line 482, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/preprocess.py", line 418, in main
    df = load_extracted_descriptors()
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/preprocess.py", line 45, in load_extracted_descriptors
    raise FileNotFoundError(f"Unified dataset not found at {path}")
FileNotFoundError: Unified dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/data/processed/unified_dataset.parquet

- python code/train.py          # XGBoost -> rc=1

Runtime projection file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/outputs/runtime_projection.json. Proceeding with default max_n_estimators=200.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/train.py", line 220, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/train.py", line 194, in main
    df = load_aligned_dataset()
         ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/train.py", line 28, in load_aligned_dataset
    raise FileNotFoundError(f"Aligned dataset not found at {file_path}")
FileNotFoundError: Aligned dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/data/processed/aligned_dataset.csv

- python code/train_baseline.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-170-predicting-catalytic-activity-from-elect/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/train_baseline.py': [Errno 2] No such file or directory

- python code/stat_test.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-170-predicting-catalytic-activity-from-elect/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/stat_test.py': [Errno 2] No such file or directory

- python code/interpret.py -> rc=1
026-10-23 08:54:51,726 INFO __main__: ================================================================================
2026-10-23 08:54:51,726 INFO __main__: T106: SHAP Analysis and SC-003 Verification
2026-10-23 08:54:51,726 INFO __main__: ================================================================================
2026-10-23 08:54:51,727 ERROR __main__: Error in T106: Best XGBoost model not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/models/best_xgboost.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/interpret.py", line 287, in main
    model_full = load_best_xgboost_model()
                 ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/interpret.py", line 35, in load_best_xgboost_model
    raise FileNotFoundError(f"Best XGBoost model not found at {model_path}")
FileNotFoundError: Best XGBoost model not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/models/best_xgboost.json

- python code/evaluate_reduced.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-170-predicting-catalytic-activity-from-elect/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/evaluate_reduced.py': [Errno 2] No such file or directory

- python code/report.py -> rc=1
3 08:54:52,127 - __main__ - ERROR - Report generation failed: Metrics file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/results/metrics.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/report.py", line 247, in main
    output_file = run_report_generation()
                  ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/report.py", line 215, in run_report_generation
    raise e
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/report.py", line 203, in run_report_generation
    metrics = load_metrics()
              ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/report.py", line 33, in load_metrics
    raise FileNotFoundError(f"Metrics file not found at {path}")
FileNotFoundError: Metrics file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/results/metrics.json

- python -m pytest -v -> rc=2
ity-from-elect/code/preprocess.py)
____________________ ERROR collecting tests/test_report.py _____________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/tests/test_report.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/test_report.py:17: in <module>
    from report import (
E   ImportError: cannot import name 'NORSKOV_REFERENCE_DESCRIPTORS' from 'report' (/home/runner/work/llmXive/llmXive/projects/PROJ-170-predicting-catalytic-activity-from-elect/code/report.py)
=========================== short test summary info ============================
ERROR tests/test_config.py
ERROR tests/test_download.py
ERROR tests/test_generate_aligned_dataset.py
ERROR tests/test_hashing.py
ERROR tests/test_preprocess.py
ERROR tests/test_report.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 6 errors in 1.50s ===============================



## Declared deliverables still missing

- data/processed/aligned_dataset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/aligned_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/evaluate.py` — NOT invoked by the run-book
    - `code/generate_aligned_dataset.py` — NOT invoked by the run-book
    - `code/interpret.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/run_pipeline.py` — NOT invoked by the run-book
    - `code/train.py` — IS a run-book command
    - `code/utils/runtime_estimator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
