# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/report.py; 4 command(s) failed: python code/download.py (rc=1); python code/preprocess.py (rc=1); python code/analysis.py (rc=1)

## Failing / missing run-book commands

- python code/download.py -> rc=1
2026-10-12 04:31:03 - __main__ - INFO - Starting download pipeline (T002).
2026-10-12 04:31:03 - __main__ - WARNING - DEV-001 (Global Data Block) deviation record not found.
2026-10-12 04:31:03 - __main__ - CRITICAL - NOAA download failed: name 'pd' is not defined


- python code/preprocess.py -> rc=1
taset written to data/processed/master_dataset.parquet
2026-10-12 04:31:03,674 - __main__ - INFO - Checksum written to data/processed/master_dataset.parquet.sha256
2026-10-12 04:31:03,674 - __main__ - ERROR - Preprocessing failed: Schema file not found at contracts/earthquake.yaml
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py", line 363, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py", line 357, in main
    create_master_dataset(deduped, config)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py", line 268, in create_master_dataset
    earthquake_schema = load_schema("earthquake")
                        ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py", line 62, in load_schema
    raise FileNotFoundError(f"Schema file not found at {schema_path}")
FileNotFoundError: Schema file not found at contracts/earthquake.yaml


- python code/analysis.py -> rc=1
2026-10-12 04:31:04 - __main__ - INFO - Starting analysis pipeline.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 320, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 313, in main
    results = run_analysis()
              ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 267, in run_analysis
    df = load_master_dataset()
         ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 19, in load_master_dataset
    raise FileNotFoundError(f"Master dataset not found at {path}")
FileNotFoundError: Master dataset not found at /home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/data/processed/master_dataset.csv

- python code/report.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-252-exploring-the-correlation-between-atmosp/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/report.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/unit/test_t017_master_dataset.py:11: in <module>
    from preprocess import load_config, validate_master_dataset, load_schema, get_expected_count
E   ImportError: cannot import name 'validate_master_dataset' from 'preprocess' (/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py)
=========================== short test summary info ============================
ERROR tests/integration/test_permutation.py
ERROR tests/unit/test_config.py
ERROR tests/unit/test_generate_master_dataset.py
ERROR tests/unit/test_null_hypothesis.py
ERROR tests/unit/test_ocean_mask.py
ERROR tests/unit/test_preprocess.py
ERROR tests/unit/test_preprocess_anomalies.py
ERROR tests/unit/test_statistics.py
ERROR tests/unit/test_t017_master_dataset.py
!!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 9 errors in 0.67s ===============================


