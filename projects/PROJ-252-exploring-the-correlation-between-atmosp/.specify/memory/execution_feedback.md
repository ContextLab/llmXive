# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/report.py; 4 command(s) failed: python -m pytest tests/   # should exit with a success status (rc=4); python code/preprocess.py   # deterministic implementation follows the plan specification (rc=1); python code/analysis.py (rc=1); 1 declared deliverable(s) absent: data/raw/usgs_2013_2023.csv

## Failing / missing run-book commands

- python -m pytest tests/   # should exit with a success status -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.2, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-252-exploring-the-correlation-between-atmosp/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: #


- python code/preprocess.py   # deterministic implementation follows the plan specification -> rc=1
taset written to data/processed/master_dataset.parquet
2026-10-18 08:27:57,241 - __main__ - INFO - Checksum written to data/processed/master_dataset.parquet.sha256
2026-10-18 08:27:57,242 - __main__ - ERROR - Preprocessing failed: Schema file not found at contracts/earthquake.yaml
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py", line 398, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py", line 392, in main
    create_master_dataset(deduped, config)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py", line 304, in create_master_dataset
    earthquake_schema = load_schema("earthquake")
                        ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py", line 67, in load_schema
    raise FileNotFoundError(f"Schema file not found at {schema_path}")
FileNotFoundError: Schema file not found at contracts/earthquake.yaml


- python code/analysis.py -> rc=1
File "pandas/_libs/hashtable_class_helper.pxi", line 7089, in pandas._libs.hashtable.PyObjectHashTable.get_item
KeyError: 'is_event'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 317, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 310, in main
    results = run_analysis()
              ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 267, in run_analysis
    event_data = df[df['is_event'] == 1]['pressure_anomaly'].values
                    ~~^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/frame.py", line 4102, in __getitem__
    indexer = self.columns.get_loc(key)
              ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/core/indexes/base.py", line 3812, in get_loc
    raise KeyError(key) from err
KeyError: 'is_event'

- python code/report.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-252-exploring-the-correlation-between-atmosp/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/report.py': [Errno 2] No such file or directory

- python -m pytest tests/contract/ -> rc=1
data_schema.py:63: in load_schema
    raise FileNotFoundError(f"Schema file not found: {schema_file}")
E   FileNotFoundError: Schema file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/contracts/earthquake.yaml
=========================== short test summary info ============================
FAILED tests/contract/test_data_schema.py::TestDataSchemaValidation::test_load_earthquake_schema
FAILED tests/contract/test_data_schema.py::TestDataSchemaValidation::test_load_pressure_anomaly_schema
FAILED tests/contract/test_data_schema.py::TestDataSchemaValidation::test_earthquake_schema_validates_valid_data
FAILED tests/contract/test_data_schema.py::TestDataSchemaValidation::test_earthquake_schema_rejects_missing_fields
FAILED tests/contract/test_data_schema.py::TestDataSchemaValidation::test_pressure_anomaly_schema_validates_valid_data
FAILED tests/contract/test_data_schema.py::TestDataSchemaValidation::test_pressure_anomaly_schema_rejects_missing_fields
FAILED tests/contract/test_data_schema.py::TestDataSchemaValidation::test_required_fields_match_spec
============================== 7 failed in 0.09s ===============================



## Declared deliverables still missing

- data/raw/usgs_2013_2023.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/usgs_2013_2023.csv` is declared but was NOT written. Scripts referencing it:
    - `code/download.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/usgs_2013_2023.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
