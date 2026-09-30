# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/model.py --input data/processed/GSE12345_processed.csv --output data/processed/; python code/report.py --input data/processed/ --output results/; 3 command(s) failed: python code/ingest.py --accession GSE12345 --output data/raw/ (rc=1); python code/preprocess.py --input data/raw/GSE12345_raw.csv --output data/processed/ (rc=1); python code/validation.py --input data/processed/GSE12345_processed.csv --model data/processed/GSE12345_model.pkl --output data/processed/ (rc=1); 6 declared deliverable(s) absent: data/interim/batch_corrected_data.csv; data/interim/harmonized.csv; data/processed/feature_importance.csv

## Failing / missing run-book commands

- python code/ingest.py --accession GSE12345 --output data/raw/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-407-predicting-plant-herbivore-resistance-fr/code/ingest.py", line 1, in <module>
    import requests
ModuleNotFoundError: No module named 'requests'
- python code/preprocess.py --input data/raw/GSE12345_raw.csv --output data/processed/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-407-predicting-plant-herbivore-resistance-fr/code/preprocess.py", line 9, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/model.py --input data/processed/GSE12345_processed.csv --output data/processed/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-407-predicting-plant-herbivore-resistance-fr/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-407-predicting-plant-herbivore-resistance-fr/code/model.py': [Errno 2] No such file or directory
- python code/validation.py --input data/processed/GSE12345_processed.csv --model data/processed/GSE12345_model.pkl --output data/processed/ -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-407-predicting-plant-herbivore-resistance-fr/code/validation.py", line 4, in <module>
    import numpy as np
ModuleNotFoundError: No module named 'numpy'
- python code/report.py --input data/processed/ --output results/ -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-407-predicting-plant-herbivore-resistance-fr/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-407-predicting-plant-herbivore-resistance-fr/code/report.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/interim/batch_corrected_data.csv
- data/interim/harmonized.csv
- data/processed/feature_importance.csv
- data/processed/model_metrics.json
- data/processed/pca_reduced.csv
- data/raw/raw_dataset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/batch_corrected_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validation.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/batch_corrected_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/interim/harmonized.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingest.py` — IS a run-book command
    - `code/preprocess.py` — IS a run-book command
    - `code/validation.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/harmonized.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/feature_importance.csv` is declared but was NOT written. Scripts referencing it:
    - `code/feature_importance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_importance.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/validation.py` — IS a run-book command
    - `code/feature_importance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pca_reduced.csv` is declared but was NOT written. Scripts referencing it:
    - `code/preprocess.py` — IS a run-book command
    - `code/validation.py` — IS a run-book command
    - `code/feature_importance.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/pca_reduced.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/raw_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/ingest.py` — IS a run-book command
    - `code/save_raw_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/raw_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
