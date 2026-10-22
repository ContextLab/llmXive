# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv (rc=1); python -m src.validate data/processed/features.csv (rc=1); python -m src.split data/processed/features.csv data/processed/train.csv data/processed/test.csv (rc=1)

## Failing / missing run-book commands

- python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv -> rc=1

2026-10-22 04:31:33,434 INFO src.data.featurize: Input file data/raw/materials_defects.csv not found – attempting to download raw dataset.
2026-10-22 04:31:33,434 WARNING src.data.download: MP_API_KEY not provided; attempting public fallback download.
2026-10-22 04:31:33,473 INFO src.data.download: Attempting fallback download from https://raw.githubusercontent.com/materialsproject/mp-data/master/defects/defect_entries.csv
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
 failed: {result.stderr}"
E       AssertionError: Checksum script failed: 2026-10-22 04:31:36,767 ERROR __main__: Input file(s) not found for checksum generation: /home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/data/raw/materials_defects.csv, /home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/data/processed/features.csv
E         
E       assert 1 == 0
E        +  where 1 = CompletedProcess(args=['/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies.../runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/data/processed/features.csv\n').returncode

tests/test_generate_checksums.py:30: AssertionError
=========================== short test summary info ============================
FAILED code/tests/test_pipeline_entry.py::test_pipeline_entry - NameError: na...
FAILED code/tests/test_requirements.py::test_requirements_install_and_imports
FAILED src/tests/test_quickstart.py::test_quickstart_pipeline - subprocess.Ca...
FAILED tests/test_generate_checksums.py::test_checksum_files_created - Assert...
4 failed, 2 passed in 2.84s


