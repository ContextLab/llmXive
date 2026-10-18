# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/ingest.py  --url "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet"  --out-dir data/raw  --dataset-id ds000208`
  - script usage: `ingest.py [-h] --dataset-url DATASET_URL [--output-dir OUTPUT_DIR]`
  - argparse error: `ingest.py: error: the following arguments are required: --dataset-url`
- run-book command: `python code/report.py  --analysis results/analysis_output.json  --outlier-sensitivity results/outlier_sensitivity.json  --design data/interim/design_branch.json  --output paper/report.md`
  - script usage: `report.py [-h] --input INPUT --output OUTPUT`
  - argparse error: `report.py: error: the following arguments are required: --input`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/ingest.py  --url "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet"  --out-dir data/raw  --dataset-id ds000208 (rc=2); python code/preprocess.py  --input data/raw/ds000208.parquet  --output data/processed/analysis_ready_ds000208.csv (rc=1); python code/analyze.py  --data data/processed/analysis_ready_ds000208.csv  --output results/analysis_output.json (rc=1); 1 declared deliverable(s) absent: data/processed/metadata.json

## Failing / missing run-book commands

- python code/ingest.py  --url "https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet"  --out-dir data/raw  --dataset-id ds000208 -> rc=2

usage: ingest.py [-h] --dataset-url DATASET_URL [--output-dir OUTPUT_DIR]
                 [--dataset-id DATASET_ID]
ingest.py: error: the following arguments are required: --dataset-url

- python code/preprocess.py  --input data/raw/ds000208.parquet  --output data/processed/analysis_ready_ds000208.csv -> rc=1
l-rejection/code/preprocess.py", line 337, in run_preprocessing
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
FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/ds000208.parquet'

- python code/analyze.py  --data data/processed/analysis_ready_ds000208.csv  --output results/analysis_output.json -> rc=1
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

- python code/analyze.py  --data data/processed/analysis_ready_ds000208.csv  --outlier-sensitivity results/outlier_sensitivity.json -> rc=1
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

- python code/report.py  --analysis results/analysis_output.json  --outlier-sensitivity results/outlier_sensitivity.json  --design data/interim/design_branch.json  --output paper/report.md -> rc=2

usage: report.py [-h] --input INPUT --output OUTPUT
                 [--results-output RESULTS_OUTPUT]
report.py: error: the following arguments are required: --input

- python -m pytest tests/ -> rc=2
est' (/home/runner/work/llmXive/llmXive/projects/PROJ-258-the-effect-of-simulated-social-rejection/code/ingest.py)
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
ERROR tests/test_ingest_manifest.py
ERROR tests/test_performance.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.90s ===============================



## Declared deliverables still missing

- data/processed/metadata.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/analyze.py` — IS a run-book command
    - `code/ingest.py` — IS a run-book command
    - `code/report.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
