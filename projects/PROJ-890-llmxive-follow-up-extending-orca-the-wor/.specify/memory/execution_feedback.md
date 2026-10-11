# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/scripts/download_data.py; python code/main_pipeline.py; 5 declared deliverable(s) absent: data/.checksums.json; data/processed/latents.csv; data/processed/original_labels.csv

## Failing / missing run-book commands

- python code/scripts/download_data.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-890-llmxive-follow-up-extending-orca-the-wor/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-890-llmxive-follow-up-extending-orca-the-wor/code/scripts/download_data.py': [Errno 2] No such file or directory

- python code/main_pipeline.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-890-llmxive-follow-up-extending-orca-the-wor/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-890-llmxive-follow-up-extending-orca-the-wor/code/main_pipeline.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/.checksums.json
- data/processed/latents.csv
- data/processed/original_labels.csv
- data/raw/scenarios.csv
- data/validation/physics_ground_truth_subset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/.checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/utils/checksums.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/.checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/latents.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/extract_latents.py` — NOT invoked by the run-book
    - `code/data/physics_verify.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/latents.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/original_labels.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/extract_original_labels.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/original_labels.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/scenarios.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/download_orca.py` — NOT invoked by the run-book
    - `code/data/extract_latents.py` — NOT invoked by the run-book
    - `code/data/physics_verify.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/scenarios.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/validation/physics_ground_truth_subset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/physics_verify.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/validation/physics_ground_truth_subset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
