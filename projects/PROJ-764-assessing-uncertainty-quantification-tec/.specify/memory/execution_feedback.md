# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python code/data/download.py (rc=1); python code/data/generate_validation_report.py (rc=1); python code/data/preprocess.py (rc=1); 4 declared deliverable(s) absent: data/processed/features_train_20pca.csv; data/processed/raw_test.csv; data/processed/raw_train.csv

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
tasets
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-764-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-764-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-764-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/data/download.py", line 11, in <module>
    raise ImportError(
ImportError: The 'datasets' package is required. Please install it via 'pip install datasets'.

- python code/data/generate_validation_report.py -> rc=1

2026-10-11 10:19:18,173 - ValidationReportGenerator - INFO - Starting validation report generation.
2026-10-11 10:19:18,173 - ValidationReportGenerator - INFO - Loading exclusion log from /home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/data/processed/exclusion_log.json
2026-10-11 10:19:18,173 - ValidationReportGenerator - ERROR - File not found: Exclusion log not found at /home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/data/processed/exclusion_log.json. Ensure T006b2 has been executed successfully.

- python code/data/preprocess.py -> rc=1
2026-10-11 10:19:18,378 - __main__ - INFO - Starting PCA Transform & Exclusion (T006d)...
2026-10-11 10:19:18,378 - __main__ - ERROR - Task T006d failed: PCA transformer not found: data/processed/pca_transformer.pkl. Please run T006c (PCA Fit) first.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/data/preprocess.py", line 186, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/data/preprocess.py", line 179, in main
    perform_pca_and_exclusion()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/data/preprocess.py", line 136, in perform_pca_and_exclusion
    pca = load_pca_transformer()
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/data/preprocess.py", line 59, in load_pca_transformer
    raise FileNotFoundError(
FileNotFoundError: PCA transformer not found: data/processed/pca_transformer.pkl. Please run T006c (PCA Fit) first.

- python code/main.py -> rc=1

2026-10-11 10:19:18 - pipeline - INFO - Starting main pipeline with timeout=5.0 hours
2026-10-11 10:19:18 - pipeline - INFO - --- PIPELINE START ---
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/main.py", line 258, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/main.py", line 248, in main
    success = run_pipeline()
              ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/main.py", line 165, in run_pipeline
    signal.alarm(TIMEOUT_SECONDS)
TypeError: 'float' object cannot be interpreted as an integer

- python -m pytest tests/ -v -> rc=2
q.uncertainty_decomposition' (/home/runner/work/llmXive/llmXive/projects/PROJ-764-assessing-uncertainty-quantification-tec/code/uq/uncertainty_decomposition.py)
=============================== warnings summary ===============================
../../.llmxive-venvs/PROJ-764-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/torch/jit/_script.py:1491
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-764-assessing-uncertainty-quantification-tec/lib/python3.11/site-packages/torch/jit/_script.py:1491: FutureWarning: `torch.jit.script` is deprecated. Please switch to `torch.compile` or `torch.export`.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/integration/test_screening.py
ERROR tests/unit/test_download.py
ERROR tests/unit/test_linting_config.py
ERROR tests/unit/test_preprocess.py
ERROR tests/unit/test_sparse_gp.py
ERROR tests/unit/test_uncertainty_decomposition.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
========================= 1 warning, 6 errors in 1.67s =========================



## Declared deliverables still missing

- data/processed/features_train_20pca.csv
- data/processed/raw_test.csv
- data/processed/raw_train.csv
- data/processed/raw_val.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features_train_20pca.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/models/baseline_nn.py` — NOT invoked by the run-book
    - `code/models/mc_dropout.py` — NOT invoked by the run-book
    - `code/models/sparse_gp.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features_train_20pca.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_test.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
    - `code/run_ece_seeds.py` — NOT invoked by the run-book
    - `code/uq/compute_calibration_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/raw_test.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_train.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/raw_train.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/raw_val.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/raw_val.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
