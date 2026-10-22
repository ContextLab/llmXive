# Execution failures — fix these before the analysis can run

## ⛔ HOLLOW RESULTS — the analysis RAN but MEASURED NOTHING

Every command exited 0 and the files were written — but the numbers in them are missing. A result that is `null`, `NaN`, an empty `[]`, a header-only CSV, or a column left blank in every row is NOT a measurement. Writing an empty result file is not 'done' — it is the same failure as fabrication, just quieter. You MUST:

1. Find WHY the value is missing. A `null`/`NaN` correlation almost always means the inputs were empty, misaligned, or the wrong column was read — fix the computation, do NOT paper over it with a default.
2. Verify you loaded the REAL dataset the spec names. If the study is about behavioural confidence ratings, a stand-in dataset (a bundled sklearn toy set, a random frame) is NOT the data — it will produce exactly these null/NaN results.
3. Make sure the key measure is actually POPULATED before you compute on it: if the column the study depends on is blank in every row, the extraction step is broken and that is the real bug.
4. NEVER self-certify. A `{"status": "PASS"}` written by your own code proves nothing; the numbers must be there.

- every produced artifact is gitignored (data/processed/features.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: every produced artifact is gitignored (data/processed/features.csv) — the run left NO durable evidence: nothing is committed for a reviewer to inspect or a paper to cite. Write the results a reader needs (e.g. data/results/*, figures/*) outside the ignored data/raw + data/processed dataset caches.; 6 command(s) failed: python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv (rc=1); python -m src.validate data/processed/features.csv (rc=1); python -m src.split data/processed/features.csv data/processed/train.csv data/processed/test.csv (rc=1)

## Failing / missing run-book commands

- python -m src.featurize data/raw/materials_defects.csv data/processed/features.csv -> rc=1

2026-10-22 16:11:25,474 ERROR src.data.featurize: [Errno 2] No such file or directory: 'data/raw/materials_defects.csv'

- python -m src.validate data/processed/features.csv -> rc=1

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/src/validate.py", line 23, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/src/validate.py", line 20, in main
    _impl_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/src/data/validate.py", line 49, in main
    raise FileNotFoundError(f"Features file not found at {features_path}")
FileNotFoundError: Features file not found at /home/runner/work/llmXive/llmXive/projects/PROJ-542-predicting-defect-formation-energies-in-/data/processed/features.csv

- python -m src.split data/processed/features.csv data/processed/train.csv data/processed/test.csv -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.split

- python -m src.train data/processed/train.csv data/processed/cv_metrics.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.train

- python -m src.evaluate data/processed/train.csv data/processed/test.csv data/processed/performance.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/bin/python: No module named src.evaluate

- python -m pytest -q -> rc=1
ated - use 'reset_cache'
    parser.resetCache()

projects/PROJ-542-predicting-defect-formation-energies-in-/code/tests/test_requirements.py::test_requirements_install_and_imports
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-542-predicting-defect-formation-energies-in-/lib/python3.11/site-packages/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED code/tests/test_pipeline_entry.py::test_pipeline_entry - RuntimeError:...
FAILED src/tests/test_descriptor_gaps.py::test_check_descriptor_gaps_with_missing
FAILED src/tests/test_quickstart.py::test_quickstart_pipeline - subprocess.Ca...
FAILED src/tests/test_train.py::test_training_produces_outputs - NameError: n...
FAILED tests/test_generate_checksums.py::test_checksum_files_created - Assert...
FAILED tests/test_split.py::test_split_dataset_basic - assert 2 <= 1
FAILED tests/test_split.py::test_cli_execution - AssertionError: assert False
7 failed, 7 passed, 15 warnings in 7.28s


