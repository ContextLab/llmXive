# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv (rc=1); python -m src.validate data/processed/features.csv (rc=1); python -m src.split data/processed/features.csv data/processed/train.csv data/processed/test.csv (rc=1)

## Failing / missing run-book commands

- python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv -> rc=1
2:41:30,693 WARNING src.data.download: Fallback download failed for https://raw.githubusercontent.com/materialsproject/mp-data/main/defects/defect_entries.csv.gz: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/materialsproject/mp-data/main/defects/defect_entries.csv.gz
2026-10-22 12:41:30,693 INFO src.data.download: Attempting public fallback download from https://raw.githubusercontent.com/materialsproject/mp-data/master/defects/defect_entries.csv.gz
2026-10-22 12:41:30,720 WARNING src.data.download: Fallback download failed for https://raw.githubusercontent.com/materialsproject/mp-data/master/defects/defect_entries.csv.gz: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/materialsproject/mp-data/master/defects/defect_entries.csv.gz
2026-10-22 12:41:30,720 ERROR src.data.download: All fallback download attempts failed. Last error: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/materialsproject/mp-data/master/defects/defect_entries.csv.gz
2026-10-22 12:41:30,720 ERROR src.data.featurize: Automatic download failed: Materials Project API key not provided. Ensure the raw CSV exists at data/raw/materials_defects.csv.

- python -m src.validate data/processed/features.csv -> rc=1
        ^^^^^^^^^^^^^^^^^^^^^^^^^^
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
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/data/processed/features.csv'

- python -m src.split data/processed/features.csv data/processed/train.csv data/processed/test.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.split

- python -m src.train data/processed/train.csv data/processed/cv_metrics.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.train

- python -m src.evaluate data/processed/train.csv data/processed/test.csv data/processed/performance.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.evaluate

- python -m pytest -q -> rc=1
nd_imports
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/lib/python3.11/site-packages/matplotlib/_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

projects/PROJ-542-predicting-defect-formation-energies-in-/code/tests/test_requirements.py::test_requirements_install_and_imports
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/lib/python3.11/site-packages/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED code/tests/test_pipeline_entry.py::test_pipeline_entry - RuntimeError:...
FAILED src/tests/test_descriptor_gaps.py::test_check_descriptor_gaps_with_missing
FAILED src/tests/test_quickstart.py::test_quickstart_pipeline - subprocess.Ca...
FAILED tests/test_generate_checksums.py::test_checksum_files_created - Assert...
4 failed, 3 passed, 14 warnings in 11.02s


