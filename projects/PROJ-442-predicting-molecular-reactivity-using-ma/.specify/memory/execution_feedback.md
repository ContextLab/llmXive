# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python src/modeling/evaluate.py --input data/results/cv_results.csv --output reports/final_report.md; 3 command(s) failed: python src/data/ingestion.py --output data/processed/filtered_reactions.parquet (rc=1); python src/data/preprocessing.py --input data/processed/filtered_reactions.parquet --output data/processed/features.parquet (rc=1); python src/modeling/train.py --config src/modeling/config.yaml (rc=1); 5 declared deliverable(s) absent: data/models/xgboost_model.json; data/processed/analysis_report.json; data/processed/feature_matrix.parquet

## Failing / missing run-book commands

- python src/data/ingestion.py --output data/processed/filtered_reactions.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/src/data/ingestion.py", line 22, in <module>
    from tqdm import tqdm
ModuleNotFoundError: No module named 'tqdm'
- python src/data/preprocessing.py --input data/processed/filtered_reactions.parquet --output data/processed/features.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/src/data/preprocessing.py", line 314, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/src/data/preprocessing.py", line 307, in main
    setup_logger(__name__)
    ^^^^^^^^^^^^
NameError: name 'setup_logger' is not defined. Did you mean: 'get_logger'?
- python src/modeling/train.py --config src/modeling/config.yaml -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/src/modeling/train.py", line 13, in <module>
    from sklearn.metrics import spearmanr
ImportError: cannot import name 'spearmanr' from 'sklearn.metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/code/.venv/lib/python3.11/site-packages/sklearn/metrics/__init__.py)
- python src/modeling/evaluate.py --input data/results/cv_results.csv --output reports/final_report.md -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-442-predicting-molecular-reactivity-using-ma/src/modeling/evaluate.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/models/xgboost_model.json
- data/processed/analysis_report.json
- data/processed/feature_matrix.parquet
- data/processed/filtered_reactions.csv
- data/processed/training_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/models/xgboost_model.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_train_save.py` — NOT invoked by the run-book
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/modeling/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/models/xgboost_model.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/analysis_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/src/main.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/feature_matrix.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_train_save.py` — NOT invoked by the run-book
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/modeling/train.py` — NOT invoked by the run-book
    - `code/src/data/preprocessing.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_matrix.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/filtered_reactions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_t017_save.py` — NOT invoked by the run-book
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/data/ingestion.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/filtered_reactions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/training_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/tests/unit/test_train_save.py` — NOT invoked by the run-book
    - `code/src/main.py` — NOT invoked by the run-book
    - `code/src/modeling/train.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/training_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
