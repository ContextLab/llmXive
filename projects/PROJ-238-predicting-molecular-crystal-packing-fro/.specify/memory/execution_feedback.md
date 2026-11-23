# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 command(s) failed: python code/02_train_models.py (rc=1); python code/03_evaluate_and_report.py (rc=1); 7 declared deliverable(s) absent: data/descriptors/raw_descriptors.csv; data/interactions/interaction_classification.csv; data/interactions/raw_interactions.csv

## Failing / missing run-book commands

- python code/02_train_models.py -> rc=1
238-predicting-molecular-crystal-packing-fro/code/.venv/lib/python3.11/site-packages/sklearn/base.py", line 19, in <module>
    from .utils import _IS_32BIT
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-238-predicting-molecular-crystal-packing-fro/code/.venv/lib/python3.11/site-packages/sklearn/utils/__init__.py", line 22, in <module>
    from ._param_validation import Interval, validate_params
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-238-predicting-molecular-crystal-packing-fro/code/.venv/lib/python3.11/site-packages/sklearn/utils/_param_validation.py", line 15, in <module>
    from .validation import _is_arraylike_not_scalar
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-238-predicting-molecular-crystal-packing-fro/code/.venv/lib/python3.11/site-packages/sklearn/utils/validation.py", line 24, in <module>
    from numpy.core.numeric import ComplexWarning  # type: ignore
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ImportError: cannot import name 'ComplexWarning' from 'numpy.core.numeric' (/home/runner/work/llmXive/llmXive/projects/PROJ-238-predicting-molecular-crystal-packing-fro/code/.venv/lib/python3.11/site-packages/numpy/core/numeric.py)

- python code/03_evaluate_and_report.py -> rc=1
238-predicting-molecular-crystal-packing-fro/code/.venv/lib/python3.11/site-packages/sklearn/base.py", line 19, in <module>
    from .utils import _IS_32BIT
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-238-predicting-molecular-crystal-packing-fro/code/.venv/lib/python3.11/site-packages/sklearn/utils/__init__.py", line 22, in <module>
    from ._param_validation import Interval, validate_params
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-238-predicting-molecular-crystal-packing-fro/code/.venv/lib/python3.11/site-packages/sklearn/utils/_param_validation.py", line 15, in <module>
    from .validation import _is_arraylike_not_scalar
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-238-predicting-molecular-crystal-packing-fro/code/.venv/lib/python3.11/site-packages/sklearn/utils/validation.py", line 24, in <module>
    from numpy.core.numeric import ComplexWarning  # type: ignore
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ImportError: cannot import name 'ComplexWarning' from 'numpy.core.numeric' (/home/runner/work/llmXive/llmXive/projects/PROJ-238-predicting-molecular-crystal-packing-fro/code/.venv/lib/python3.11/site-packages/numpy/core/numeric.py)


## Declared deliverables still missing

- data/descriptors/raw_descriptors.csv
- data/interactions/interaction_classification.csv
- data/interactions/raw_interactions.csv
- data/processed/split_report.json
- data/processed/test.csv
- data/processed/train.csv
- data/processed/val.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/descriptors/raw_descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_add_hydrogens.py` — NOT invoked by the run-book
    - `code/01_ingest_and_descriptors.py` — IS a run-book command
    - `code/02_filter_packing_coefficient.py` — NOT invoked by the run-book
    - `code/02_impute_and_filter.py` — NOT invoked by the run-book
    - `code/03_generate_hashes.py` — NOT invoked by the run-book
    - `code/04_generate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/descriptors/raw_descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interactions/interaction_classification.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_generate_hashes.py` — NOT invoked by the run-book
    - `code/04_generate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interactions/interaction_classification.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interactions/raw_interactions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_generate_hashes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interactions/raw_interactions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/split_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/03_generate_hashes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/split_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_setup_data_directories.py` — NOT invoked by the run-book
    - `code/01_ingest_and_descriptors.py` — IS a run-book command
    - `code/02_save_metrics.py` — NOT invoked by the run-book
    - `code/02_statistical_evaluation.py` — NOT invoked by the run-book
    - `code/02_train_models.py` — IS a run-book command
    - `code/03_control_analysis.py` — NOT invoked by the run-book
    - `code/03_evaluate_and_report.py` — IS a run-book command
    - `code/03_generate_hashes.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_setup_data_directories.py` — NOT invoked by the run-book
    - `code/01_ingest_and_descriptors.py` — IS a run-book command
    - `code/02_filter_packing_coefficient.py` — NOT invoked by the run-book
    - `code/02_impute_and_filter.py` — NOT invoked by the run-book
    - `code/02_statistical_evaluation.py` — NOT invoked by the run-book
    - `code/02_train_models.py` — IS a run-book command
    - `code/03_control_analysis.py` — NOT invoked by the run-book
    - `code/03_evaluate_and_report.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/train.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/val.csv` is declared but was NOT written. Scripts referencing it:
    - `code/00_setup_data_directories.py` — NOT invoked by the run-book
    - `code/01_ingest_and_descriptors.py` — IS a run-book command
    - `code/02_filter_packing_coefficient.py` — NOT invoked by the run-book
    - `code/02_impute_and_filter.py` — NOT invoked by the run-book
    - `code/02_save_metrics.py` — NOT invoked by the run-book
    - `code/02_statistical_evaluation.py` — NOT invoked by the run-book
    - `code/02_train_models.py` — IS a run-book command
    - `code/03_control_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/val.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
