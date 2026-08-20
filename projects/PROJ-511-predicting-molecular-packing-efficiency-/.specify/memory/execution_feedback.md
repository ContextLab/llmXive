# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/run_pipeline.py; python code/run_pipeline.py; 4 declared deliverable(s) absent: data/dataset.csv; data/dataset_filtered.csv; data/dataset_intermediate.csv

## Failing / missing run-book commands

- python code/run_pipeline.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/run_pipeline.py': [Errno 2] No such file or directory
- python code/run_pipeline.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-511-predicting-molecular-packing-efficiency-/code/run_pipeline.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/dataset.csv
- data/dataset_filtered.csv
- data/dataset_intermediate.csv
- data/dataset_with_metrics.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/cif_loader.py` — NOT invoked by the run-book
    - `code/data_loader_utils.py` — NOT invoked by the run-book
    - `code/compute_RAW_metrics.py` — NOT invoked by the run-book
    - `code/filter_dataset.py` — NOT invoked by the run-book
    - `code/logging_utils.py` — NOT invoked by the run-book
    - `code/parse_cif.py` — NOT invoked by the run-book
    - `code/validate_dataset.py` — NOT invoked by the run-book
    - `code/add_3d_descriptors.py` — NOT invoked by the run-book
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
