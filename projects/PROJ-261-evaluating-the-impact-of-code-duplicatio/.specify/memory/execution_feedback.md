# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/data_loader.py # Stage 1: Download data`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/quickstart_validation.py validate_directory_structure (rc=1); python code/main.py (rc=1); python code/data_loader.py # Stage 1: Download data (rc=1); 1 declared deliverable(s) absent: data/raw/github-code-sample.csv

## Failing / missing run-book commands

- python code/quickstart_validation.py validate_directory_structure -> rc=1
    9,149 - __main__ - INFO -   Documentation Validation: FAIL
2026-06-29 06:07:19,149 - __main__ - INFO -   Output Validation: WARN
2026-06-29 06:07:19,149 - __main__ - INFO -   Overall: FAIL
2026-06-29 06:07:19,149 - __main__ - INFO - ------------------------------------------------------------
2026-06-29 06:07:19,149 - __main__ - ERROR - Quickstart validation FAILED. Please review the errors above.
- python code/main.py -> rc=1
    _pipeline(raw_data_path, output_dir, logger)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/main.py", line 133, in run_pipeline
    setup_memory_monitoring(get_memory_limit_mb(), logger)
TypeError: setup_memory_monitoring() takes from 0 to 1 positional arguments but 2 were given
- python code/data_loader.py # Stage 1: Download data -> rc=1
    oad_and_save_sample(
                 ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/data_loader.py", line 252, in download_and_save_sample
    raise RuntimeError(f"Download failed: {str(e)}")
RuntimeError: Download failed: Dataset streaming failed: Dataset scripts are no longer supported, but found github-code.py
- python code/bug_detection.py # Stage 4: Bug detection -> rc=1
    icatio/code/bug_detection.py", line 474, in main
    record_artifact_checksums(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/checksum_manifest.py", line 165, in record_artifact_checksums
    raise TypeError(f"manifest_path must be a Path object, got {type(manifest_path)}")
TypeError: manifest_path must be a Path object, got <class 'str'>
- python code/visualization.py # Stage 6: Visualizations -> rc=1
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/code/.venv/lib/python3.11/site-packages/numpy/linalg/_linalg.py", line 156, in _raise_linalgerror_lstsq
    raise LinAlgError("SVD did not converge in Linear Least Squares")
numpy.linalg.LinAlgError: SVD did not converge in Linear Least Squares
- python code/quickstart_validation.py -> rc=1
    0,018 - __main__ - INFO -   Documentation Validation: FAIL
2026-06-29 06:20:20,018 - __main__ - INFO -   Output Validation: PASS
2026-06-29 06:20:20,018 - __main__ - INFO -   Overall: FAIL
2026-06-29 06:20:20,018 - __main__ - INFO - ------------------------------------------------------------
2026-06-29 06:20:20,018 - __main__ - ERROR - Quickstart validation FAILED. Please review the errors above.

## Declared deliverables still missing

- data/raw/github-code-sample.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/github-code-sample.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data_loader.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/github-code-sample.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
