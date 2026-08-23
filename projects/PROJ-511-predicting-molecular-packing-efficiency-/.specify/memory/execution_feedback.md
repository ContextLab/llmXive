# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/run_pipeline.py (rc=1); python code/run_pipeline.py (rc=1); 6 declared deliverable(s) absent: data/dataset.csv; data/dataset_filtered.csv; data/dataset_intermediate.csv

## Failing / missing run-book commands

- python code/run_pipeline.py -> rc=1
    INFO - Running step: /home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/.venv/bin/python code/download_cif.py
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/download_cif.py", line 302, in <module>
    success = main()
              ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/download_cif.py", line 232, in main
    raw_cif_dir = os.path.join(output_dir, "data", "raw_cif")
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen posixpath>", line 76, in join
TypeError: expected str, bytes or os.PathLike object, not NoneType
2026-08-23 13:40:38 - ERROR - Step code/download_cif.py raised CalledProcessError: Command '['/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/.venv/bin/python', 'code/download_cif.py']' returned non-zero exit status 1.
2026-08-23 13:40:38 - ERROR - Pipeline failed at step: code/download_cif.py
2026-08-23 13:40:38 - ERROR - Pipeline execution failed. Failed steps: ['code/download_cif.py']
- python code/run_pipeline.py -> rc=1
    INFO - Running step: /home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/.venv/bin/python code/download_cif.py
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/download_cif.py", line 302, in <module>
    success = main()
              ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/download_cif.py", line 232, in main
    raw_cif_dir = os.path.join(output_dir, "data", "raw_cif")
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen posixpath>", line 76, in join
TypeError: expected str, bytes or os.PathLike object, not NoneType
2026-08-23 13:40:39 - ERROR - Step code/download_cif.py raised CalledProcessError: Command '['/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/.venv/bin/python', 'code/download_cif.py']' returned non-zero exit status 1.
2026-08-23 13:40:39 - ERROR - Pipeline failed at step: code/download_cif.py
2026-08-23 13:40:39 - ERROR - Pipeline execution failed. Failed steps: ['code/download_cif.py']

## Declared deliverables still missing

- data/dataset.csv
- data/dataset_filtered.csv
- data/dataset_intermediate.csv
- data/dataset_with_metrics.csv
- data/features_matrix.npy
- data/targets.npy

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/cif_loader.py` — NOT invoked by the run-book
    - `code/feature_assembly.py` — NOT invoked by the run-book
    - `code/data_loader_utils.py` — NOT invoked by the run-book
    - `code/compute_RAW_metrics.py` — NOT invoked by the run-book
    - `code/filter_dataset.py` — NOT invoked by the run-book
    - `code/logging_utils.py` — NOT invoked by the run-book
    - `code/parse_cif.py` — NOT invoked by the run-book
    - `code/run_pipeline.py` — IS a run-book command
  Make ONE of these WRITE `data/dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/dataset_filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/filter_dataset.py` — NOT invoked by the run-book
    - `code/add_3d_descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/dataset_filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/dataset_intermediate.csv` is declared but was NOT written. Scripts referencing it:
    - `code/compute_RAW_metrics.py` — NOT invoked by the run-book
    - `code/parse_cif.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/dataset_intermediate.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/dataset_with_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/compute_RAW_metrics.py` — NOT invoked by the run-book
    - `code/filter_dataset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/dataset_with_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/features_matrix.npy` is declared but was NOT written. Scripts referencing it:
    - `code/feature_assembly.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/features_matrix.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/targets.npy` is declared but was NOT written. Scripts referencing it:
    - `code/feature_assembly.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/targets.npy` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
