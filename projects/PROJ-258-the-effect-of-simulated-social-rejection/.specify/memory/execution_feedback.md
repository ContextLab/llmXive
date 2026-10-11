# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/ingest.py --dataset-url "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet" --output-dir data/raw (rc=1); python code/analyze.py --input data/processed/analysis_ready.csv --output results/analysis_output.json (rc=1); python code/report.py --input results/analysis_output.json --output paper/report.md (rc=1); 4 declared deliverable(s) absent: data/interim/condition_report.json; data/processed/analysis_raw.json; data/processed/final_results.json

## Failing / missing run-book commands

- python code/ingest.py --dataset-url "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet" --output-dir data/raw -> rc=1
.zip
2026-10-11 18:09:53,580 - INFO - Extracting /home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/data/raw/ds000208.zip
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/ingest.py", line 383, in <module>
    run_ingestion()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/ingest.py", line 354, in run_ingestion
    file_list = download_and_extract_zip(dataset_id, raw_dir)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/ingest.py", line 125, in download_and_extract_zip
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/zipfile.py", line 1355, in __init__
    self._RealGetContents()
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/zipfile.py", line 1422, in _RealGetContents
    raise BadZipFile("File is not a zip file")
zipfile.BadZipFile: File is not a zip file

- python code/analyze.py --input data/processed/analysis_ready.csv --output results/analysis_output.json -> rc=1
^^^^^^^^^^^^^^^^^^^^^^^^^
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
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/data/processed/features_ds000208.csv'

- python code/report.py --input results/analysis_output.json --output paper/report.md -> rc=1

2026-10-11 18:09:55,592 - ERROR - Reporting pipeline failed: Analysis results file not found: results/analysis_output.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/report.py", line 343, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/report.py", line 337, in main
    run_reporting_pipeline(args.input, args.output, final_results_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/report.py", line 291, in run_reporting_pipeline
    raise FileNotFoundError(f"Analysis results file not found: {analysis_results_path}")
FileNotFoundError: Analysis results file not found: results/analysis_output.json

- python -m pytest tests/ -> rc=2
ml
plugins: anyio-4.15.1
collecting ... collected 58 items / 1 error

==================================== ERRORS ====================================
__________________ ERROR collecting tests/test_performance.py __________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/tests/test_performance.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/test_performance.py:19: in <module>
    from performance_monitor import (
E   ImportError: cannot import name 'MAX_RUNTIME_SECONDS' from 'performance_monitor' (/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/performance_monitor.py)
=========================== short test summary info ============================
ERROR tests/test_performance.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 1.15s ===============================



## Declared deliverables still missing

- data/interim/condition_report.json
- data/processed/analysis_raw.json
- data/processed/final_results.json
- data/processed/metadata.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/condition_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingest.py` — IS a run-book command
  Make ONE of these WRITE `data/interim/condition_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/analysis_raw.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/analyze.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/analysis_raw.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/report.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/final_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/analyze.py` — IS a run-book command
    - `code/ingest.py` — IS a run-book command
    - `code/report.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
