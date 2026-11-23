# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/data/target_calc.py (rc=1); python code/models/trainer.py (rc=1); 3 declared deliverable(s) absent: data/processed/bins.csv; data/processed/electrolyte_features.csv; data/processed/model_run.json

## Failing / missing run-book commands

- python code/data/target_calc.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-085-predicting-battery-electrolyte-decomposi/code/data/target_calc.py", line 18, in <module>
    from utils.constants import get_reactions_schema_template
ImportError: cannot import name 'get_reactions_schema_template' from 'utils.constants' (/home/runner/work/llmXive/llmXive/projects/PROJ-085-predicting-battery-electrolyte-decomposi/code/utils/constants.py)

- python code/models/trainer.py -> rc=1
Running Trainer Pipeline...

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-085-predicting-battery-electrolyte-decomposi/code/models/trainer.py", line 193, in <module>
    run_trainer_pipeline("low")
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-085-predicting-battery-electrolyte-decomposi/code/models/trainer.py", line 149, in run_trainer_pipeline
    df = load_processed_features()
         ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-085-predicting-battery-electrolyte-decomposi/code/models/trainer.py", line 35, in load_processed_features
    raise FileNotFoundError(f"Processed features file not found at {path}")
FileNotFoundError: Processed features file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-085-predicting-battery-electrolyte-decomposi/data/processed/electrolyte_features.csv


## Declared deliverables still missing

- data/processed/bins.csv
- data/processed/electrolyte_features.csv
- data/processed/model_run.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/bins.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/binning.py` — NOT invoked by the run-book
    - `code/data/run_binning.py` — NOT invoked by the run-book
    - `code/models/feature_shift_analyzer.py` — NOT invoked by the run-book
    - `code/models/model_saver.py` — NOT invoked by the run-book
    - `code/models/run_trainer_wrapper.py` — NOT invoked by the run-book
    - `code/models/sensitivity_report_generator.py` — NOT invoked by the run-book
    - `code/models/trainer.py` — IS a run-book command
    - `code/utils/constants.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/bins.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/electrolyte_features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/binning.py` — NOT invoked by the run-book
    - `code/data/run_binning.py` — NOT invoked by the run-book
    - `code/data/run_descriptor_pipeline.py` — NOT invoked by the run-book
    - `code/data/split_data.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/models/trainer.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/electrolyte_features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_run.json` is declared but was NOT written. Scripts referencing it:
    - `code/models/__init__.py` — NOT invoked by the run-book
    - `code/models/evaluator.py` — IS a run-book command
    - `code/models/feature_shift_analyzer.py` — NOT invoked by the run-book
    - `code/models/model_saver.py` — NOT invoked by the run-book
    - `code/models/run_trainer_wrapper.py` — NOT invoked by the run-book
    - `code/models/sensitivity_report_generator.py` — NOT invoked by the run-book
    - `code/models/trainer.py` — IS a run-book command
    - `code/visualization/plot_importance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_run.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
