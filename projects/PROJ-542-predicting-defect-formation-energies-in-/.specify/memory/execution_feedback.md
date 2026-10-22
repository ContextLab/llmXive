# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv (rc=1); python -m src.validate data/processed/features.csv (rc=1); python -m src.split data/processed/features.csv data/processed/train.csv data/processed/test.csv (rc=1)

## Failing / missing run-book commands

- python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv -> rc=1

2026-10-22 04:33:48,438 INFO src.data.featurize: Input file data/raw/materials_defects.csv not found – attempting to download raw dataset.
2026-10-22 04:33:48,438 WARNING src.data.download: MP_API_KEY not provided; attempting public fallback download.
2026-10-22 04:33:48,477 INFO src.data.download: Attempting fallback download from https://raw.githubusercontent.com/materialsproject/mp-data/master/defects/defect_entries.csv
Materials Project API key not provided

- python -m src.validate data/processed/features.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.validate

- python -m src.split data/processed/features.csv data/processed/train.csv data/processed/test.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.split

- python -m src.train data/processed/train.csv data/processed/cv_metrics.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.train

- python -m src.evaluate data/processed/train.csv data/processed/test.csv data/processed/performance.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.evaluate

- python -m pytest -q -> rc=1
formation-energies-in-/code/tests/test_requirements.py::test_requirements_install_and_imports
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/lib/python3.11/site-packages/matplotlib/_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

projects/PROJ-542-predicting-defect-formation-energies-in-/code/tests/test_requirements.py::test_requirements_install_and_imports
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/lib/python3.11/site-packages/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED code/tests/test_pipeline_entry.py::test_pipeline_entry - NameError: na...
FAILED src/tests/test_quickstart.py::test_quickstart_pipeline - subprocess.Ca...
FAILED tests/test_generate_checksums.py::test_checksum_files_created - Assert...
3 failed, 3 passed, 14 warnings in 6.24s


