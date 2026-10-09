# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/ingest.py --dataset-url "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet" --output-dir data/raw`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/ingest.py --dataset-url "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet" --output-dir data/raw (rc=1); python code/analyze.py --input data/processed/analysis_ready.csv --output results/analysis_output.json (rc=1); python code/report.py --input results/analysis_output.json --output paper/report.md (rc=1); 4 declared deliverable(s) absent: data/interim/condition_report.json; data/processed/analysis_raw.json; data/processed/final_results.json

## Failing / missing run-book commands

- python code/ingest.py --dataset-url "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet" --output-dir data/raw -> rc=1

2026-10-09 12:32:34,648 - INFO - Downloading dataset ds000208 via HuggingFace `datasets` library...
2026-10-09 12:32:34,768 - INFO - HTTP Request: HEAD https://huggingface.co/datasets/openneuro/ds000208/resolve/main/README.md "HTTP/1.1 401 Unauthorized"
2026-10-09 12:32:34,769 - ERROR - Failed to load dataset openneuro/ds000208: Dataset 'openneuro/ds000208' doesn't exist on the Hub or cannot be accessed.

- python code/analyze.py --input data/processed/analysis_ready.csv --output results/analysis_output.json -> rc=1
lated-social-rejection/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 300, in _read
    parser = TextFileReader(filepath_or_buffer, **kwds)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1643, in __init__
    self._engine = self._make_engine(f, self.engine)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/.venv/lib/python3.11/site-packages/pandas/io/parsers/readers.py", line 1907, in _make_engine
    self.handles = get_handle(
                   ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/.venv/lib/python3.11/site-packages/pandas/io/common.py", line 930, in get_handle
    handle = open(
             ^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/data/processed/features_ds000208.csv'

- python code/report.py --input results/analysis_output.json --output paper/report.md -> rc=1

2026-10-09 12:32:36,778 - ERROR - Reporting pipeline failed: Analysis results file not found: results/analysis_output.json
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/report.py", line 343, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/report.py", line 337, in main
    run_reporting_pipeline(args.input, args.output, final_results_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/report.py", line 291, in run_reporting_pipeline
    raise FileNotFoundError(f"Analysis results file not found: {analysis_results_path}")
FileNotFoundError: Analysis results file not found: results/analysis_output.json

- python -m pytest tests/ -> rc=2
rror

==================================== ERRORS ====================================
__________________ ERROR collecting tests/test_performance.py __________________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/tests/test_performance.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_performance.py:19: in <module>
    from performance_monitor import (
E   ImportError: cannot import name 'MAX_RUNTIME_SECONDS' from 'performance_monitor' (/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/performance_monitor.py)
=========================== short test summary info ============================
ERROR tests/test_performance.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 1.07s ===============================



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
