# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/download.py (rc=1); python code/preprocess.py (rc=1); python code/analysis.py (rc=1); 1 declared deliverable(s) absent: data/processed/standardized.csv

## Failing / missing run-book commands

- python code/download.py -> rc=1
    port Dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/.venv/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 67, in <module>
    from .arrow_writer import ArrowWriter, OptimizedTypedSequence
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/.venv/lib/python3.11/site-packages/datasets/arrow_writer.py", line 27, in <module>
    from .features import Features, Image, Value
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/.venv/lib/python3.11/site-packages/datasets/features/__init__.py", line 18, in <module>
    from .features import Array2D, Array3D, Array4D, Array5D, ClassLabel, Features, Sequence, Value
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/.venv/lib/python3.11/site-packages/datasets/features/features.py", line 634, in <module>
    class _ArrayXDExtensionType(pa.PyExtensionType):
                                ^^^^^^^^^^^^^^^^^^
AttributeError: module 'pyarrow' has no attribute 'PyExtensionType'. Did you mean: 'ExtensionType'?
- python code/preprocess.py -> rc=1
    runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/data/processed/exclusion_log.json
2026-08-31 10:23:33,490 - ERROR - Preprocessing pipeline failed: No datasets were successfully processed.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/preprocess.py", line 338, in main
    run_preprocessing_pipeline(dataset_ids, output_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/preprocess.py", line 266, in run_preprocessing_pipeline
    raise ValueError("No datasets were successfully processed.")
ValueError: No datasets were successfully processed.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/preprocess.py", line 344, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/preprocess.py", line 341, in main
    sys.exit(1)
    ^^^
NameError: name 'sys' is not defined
- python code/analysis.py -> rc=1
    2026-08-31 10:23:35,079 - INFO - Loading data from /home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/data/processed/standardized.csv
2026-08-31 10:23:35,079 - ERROR - Analysis failed: Preprocessed data not found at /home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/data/processed/standardized.csv
/home/runner/work/llmXive/llmXive/projects/PROJ-222-the-impact-of-predictive-coding-errors-o/code/.venv/lib/python3.11/site-packages/outdated/utils.py:14: OutdatedPackageWarning: The package pingouin is out of date. Your version is 0.5.3, the latest is 0.6.1.
Set the environment variable OUTDATED_IGNORE=1 to disable these warnings.
  return warn(

## Declared deliverables still missing

- data/processed/standardized.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/standardized.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
    - `code/analysis.py` — IS a run-book command
    - `code/save_markov_artifacts.py` — NOT invoked by the run-book
    - `code/run_t017.py` — NOT invoked by the run-book
    - `code/generate_standardized_output.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/standardized.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
