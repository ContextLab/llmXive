# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/analysis/validation_audit.py; 7 command(s) failed: python code/data/download.py (rc=1); python code/data/preprocess.py (rc=1); python code/data/fingerprint.py (rc=1); 9 declared deliverable(s) absent: data/derived/conformational_limitations.csv; data/derived/data_quality_report.csv; data/derived/deviation_contexts.csv

## Failing / missing run-book commands

- python code/data/download.py -> rc=1
:13:38,110 - __main__ - WARNING - Failed to fetch WaterSolubility for CID 1964: 'Compound' object has no attribute 'water_solubility'
2026-10-19 18:13:38,110 - __main__ - WARNING - Failed to fetch BoilingPoint for CID 1964: 'Compound' object has no attribute 'boiling_point'
2026-10-19 18:13:38,110 - __main__ - WARNING - Failed to fetch RecordType for CID 1964: 'Compound' object has no attribute 'record_type'
2026-10-19 18:13:38,110 - __main__ - ERROR - Failed to fetch data for CID 1964: 'Compound' object has no attribute 'record_type'
2026-10-19 18:13:38,402 - __main__ - WARNING - Failed to fetch WaterSolubility for CID 1973: 'Compound' object has no attribute 'water_solubility'
2026-10-19 18:13:38,402 - __main__ - WARNING - Failed to fetch BoilingPoint for CID 1973: 'Compound' object has no attribute 'boiling_point'
2026-10-19 18:13:38,402 - __main__ - WARNING - Failed to fetch RecordType for CID 1973: 'Compound' object has no attribute 'record_type'
2026-10-19 18:13:38,402 - __main__ - ERROR - Failed to fetch data for CID 1973: 'Compound' object has no attribute 'record_type'
2026-10-19 18:13:38,403 - __main__ - ERROR - No data fetched. Check CID list and PubChemPy connectivity.

- python code/data/preprocess.py -> rc=1

2026-10-19 18:13:38,874 - __main__ - ERROR - Raw data file not found: data/raw/pubchem_raw.csv. Run T008 first.

- python code/data/fingerprint.py -> rc=1

2026-10-19 18:13:39,820 - __main__ - INFO - Ensured output directories: [PosixPath('data/processed'), PosixPath('data/derived')]
2026-10-19 18:13:39,821 - __main__ - ERROR - Open Babel (obabel) not found in PATH. Please install it.
2026-10-19 18:13:39,821 - __main__ - ERROR - Open Babel not available. Cannot proceed.

- python code/models/baseline.py -> rc=1
ope/code/models/baseline.py", line 87, in process_dataset
    df = pd.read_csv(input_path)
         ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1026, in read_csv
    return _read(filepath_or_buffer, kwds)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 620, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1620, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parsers/readers.py", line 1880, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/common.py", line 873, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/derived/diverse_subset.csv'

- python code/models/rf.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/models/rf.py", line 33, in <module>
    from code.utils.config import get_runtime_config, get_joblib_parallel_backend
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/utils/config.py", line 20, in <module>
    from data.preprocess import load_preprocessed_data
ModuleNotFoundError: No module named 'data.preprocess'

- python code/analysis/stats.py -> rc=1
2026-10-19 18:13:42,203 - stats - INFO - Generating Experimental Validation Protocol (T058)...
ERROR: Metadata file not found at data/raw/dataset_metadata.json. Run T031 first.


- python code/analysis/validation_audit.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-324-predicting-molecular-properties-from-ope/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-324-predicting-molecular-properties-from-ope/code/analysis/validation_audit.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
e-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../../../../.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45
  /home/runner/.cache/llmxive/base-env/py311-6f1866971868/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/contract/test_fingerprint_generation.py
ERROR tests/unit/test_baseline.py
ERROR tests/unit/test_fingerprint_generation.py
ERROR tests/unit/test_lint_config.py
ERROR tests/unit/test_lint_format.py
ERROR tests/unit/test_linting_config.py
!!!!!!!!!!!!!!!!!!! Interrupted: 6 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 14 warnings, 6 errors in 1.48s ========================



## Declared deliverables still missing

- data/derived/conformational_limitations.csv
- data/derived/data_quality_report.csv
- data/derived/deviation_contexts.csv
- data/derived/rf_test_predictions.csv
- data/derived/test_set.csv
- data/derived/train_set.csv
- data/processed/test_fingerprints.csv
- data/raw/dataset_metadata.json
- data/raw/pubchem_raw.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/derived/conformational_limitations.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/explainability.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/conformational_limitations.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/data_quality_report.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/data_quality_report.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/deviation_contexts.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/explainability.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/deviation_contexts.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/rf_test_predictions.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/explainability.py` — IS a run-book command
    - `code/analysis/stats.py` — IS a run-book command
    - `code/models/rf.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/rf_test_predictions.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/test_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/explainability.py` — IS a run-book command
    - `code/analysis/stats.py` — IS a run-book command
    - `code/data/fingerprint.py` — IS a run-book command
    - `code/data/preprocess.py` — IS a run-book command
    - `code/models/rf.py` — IS a run-book command
  Make ONE of these WRITE `data/derived/test_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/derived/train_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/fingerprint.py` — IS a run-book command
    - `code/data/fingerprints.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — IS a run-book command
    - `code/models/baseline.py` — IS a run-book command
    - `code/models/random_forest.py` — NOT invoked by the run-book
    - `code/models/rf.py` — IS a run-book command
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/derived/train_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test_fingerprints.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/explainability.py` — IS a run-book command
    - `code/models/rf.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/test_fingerprints.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/dataset_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — IS a run-book command
    - `code/data/download.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/dataset_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/pubchem_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — IS a run-book command
    - `code/data/download.py` — IS a run-book command
    - `code/data/preprocess.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/pubchem_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
