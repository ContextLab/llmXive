# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/run_pipeline.py (rc=1); python code/run_pipeline.py (rc=1); 6 declared deliverable(s) absent: data/dataset.csv; data/dataset_filtered.csv; data/dataset_intermediate.csv

## Failing / missing run-book commands

- python code/run_pipeline.py -> rc=1
    ing type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/parse_cif.py", line 429, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/parse_cif.py", line 401, in main
    log_processing_statistics(success_count, failure_count, len(cif_files))
TypeError: log_processing_statistics() missing 2 required positional arguments: 'start_time' and 'end_time'
2026-08-26 14:35:32 - ERROR - Step code/parse_cif.py raised CalledProcessError: Command '['/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/.venv/bin/python', 'code/parse_cif.py']' returned non-zero exit status 1.
2026-08-26 14:35:32 - ERROR - Pipeline failed at step: code/parse_cif.py
2026-08-26 14:35:32 - ERROR - Pipeline execution failed. Failed steps: ['code/parse_cif.py']
- python code/run_pipeline.py -> rc=1
    ing type, and better interoperability with other libraries)
but was not found to be installed on your system.
If this would cause problems for you,
please provide us feedback at https://github.com/pandas-dev/pandas/issues/54466
        
  import pandas as pd
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/parse_cif.py", line 429, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/parse_cif.py", line 401, in main
    log_processing_statistics(success_count, failure_count, len(cif_files))
TypeError: log_processing_statistics() missing 2 required positional arguments: 'start_time' and 'end_time'
2026-08-26 14:35:33 - ERROR - Step code/parse_cif.py raised CalledProcessError: Command '['/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/.venv/bin/python', 'code/parse_cif.py']' returned non-zero exit status 1.
2026-08-26 14:35:33 - ERROR - Pipeline failed at step: code/parse_cif.py
2026-08-26 14:35:33 - ERROR - Pipeline execution failed. Failed steps: ['code/parse_cif.py']

## Declared deliverables still missing

- data/dataset.csv
- data/dataset_filtered.csv
- data/dataset_intermediate.csv
- data/dataset_with_metrics.csv
- data/features_matrix.npy
- data/targets.npy

## ⚠ SHARED-MODULE CONTRACT — fix the DEFINITION, tolerant of ALL callers

One or more failures are API-CONTRACT errors on a symbol YOUR OWN code defines and that MANY scripts call in DIFFERENT ways. Rewriting the definition to match one caller breaks the others — that is why this keeps failing. Fix the DEFINITION **once** so it is compatible with EVERY call site listed below: accept ``*args, **kwargs``, branch on what was actually passed, and NEVER raise on an unexpected call shape. For an auxiliary utility (e.g. logging), doing nothing on an unrecognized shape is fine. Do NOT edit the call sites — edit only the defining module.

**CRITICAL — ADD, do not REPLACE.** Edit the defining module *in place*: ADD the missing methods/parameters and PRESERVE every function, method, and attribute that already exists. Do NOT rewrite the file from scratch and do NOT delete a definition to make room for another. Each round that deletes a previously-working symbol just moves the failure to that symbol next round — an infinite loop. The fix is cumulative: the module must satisfy ALL callers from ALL rounds simultaneously.

**This list is CUMULATIVE across every fix round** — it includes contracts you may have ALREADY satisfied in an earlier round. Keep satisfying them while you fix the rest. Do NOT remove a method or parameter merely because it is absent from this round's traceback; if it is listed here, some script still depends on it.

### `log_processing_statistics` — defined in `code/error_handling.py`; called 1 way(s):

- code/parse_cif.py: log_processing_statistics(success_count, failure_count, len(cif_files))

Make `log_processing_statistics` in `code/error_handling.py` accept ALL of the above.

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
