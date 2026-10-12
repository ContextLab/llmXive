# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/download.py --config code/config.yaml`
  - script usage: `download.py [-h] [--force] [--verify-only]`
  - argparse error: `download.py: error: unrecognized arguments: --config code/config.yaml`
- run-book command: `python code/analyze.py --mode pilot --config code/config.yaml`
  - script usage: `analyze.py [-h] [--task TASK] [--metrics-file METRICS_FILE]`
  - argparse error: `analyze.py: error: unrecognized arguments: --mode pilot --config code/config.yaml`
- run-book command: `python code/correct.py --input data/processed/baseline_naive/ --output data/processed/flow_corrected/ --model raft-small --precision fp16`
  - script usage: `correct.py [-h] [--input-dir INPUT_DIR] [--output-dir OUTPUT_DIR]`
  - argparse error: `correct.py: error: unrecognized arguments: --model raft-small --precision fp16`
- run-book command: `python code/analyze.py --metrics data/results/metrics.csv --output data/results/statistics.json`
  - script usage: `analyze.py [-h] [--task TASK] [--metrics-file METRICS_FILE]`
  - argparse error: `analyze.py: error: unrecognized arguments: --output data/results/statistics.json`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/evaluate.py --inputs data/processed/baseline_full/ data/processed/baseline_naive/ data/processed/flow_corrected/ --output data/results/metrics.csv; 7 command(s) failed: python code/download.py --config code/config.yaml (rc=2); python code/analyze.py --mode pilot --config code/config.yaml (rc=2); python code/generate.py --mode baseline-full --output data/processed/baseline_full/ --config code/config.yaml (rc=1)

## Failing / missing run-book commands

- python code/download.py --config code/config.yaml -> rc=2

usage: download.py [-h] [--force] [--verify-only]
download.py: error: unrecognized arguments: --config code/config.yaml

- python code/analyze.py --mode pilot --config code/config.yaml -> rc=2

usage: analyze.py [-h] [--task TASK] [--metrics-file METRICS_FILE]
                  [--pilot-file PILOT_FILE]
analyze.py: error: unrecognized arguments: --mode pilot --config code/config.yaml

- python code/generate.py --mode baseline-full --output data/processed/baseline_full/ --config code/config.yaml -> rc=1

2026-10-12 15:20:55,954 - utils.flow_benchmark - WARNING - RAFT-Small not available. Install with: pip install raft-s
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr/code/generate.py", line 27, in <module>
    logging.FileHandler("results/generation.log"),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr/results/generation.log'

- python code/generate.py --mode baseline-naive --output data/processed/baseline_naive/ --config code/config.yaml -> rc=1

2026-10-12 15:20:57,551 - utils.flow_benchmark - WARNING - RAFT-Small not available. Install with: pip install raft-s
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr/code/generate.py", line 27, in <module>
    logging.FileHandler("results/generation.log"),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr/results/generation.log'

- python code/correct.py --input data/processed/baseline_naive/ --output data/processed/flow_corrected/ --model raft-small --precision fp16 -> rc=2

2026-10-12 15:20:59,154 - utils.flow_benchmark - WARNING - RAFT-Small not available. Install with: pip install raft-s
2026-10-12 15:20:59,155 - config - INFO - No config.json found. Using defaults.
usage: correct.py [-h] [--input-dir INPUT_DIR] [--output-dir OUTPUT_DIR]
correct.py: error: unrecognized arguments: --model raft-small --precision fp16

- python code/evaluate.py --inputs data/processed/baseline_full/ data/processed/baseline_naive/ data/processed/flow_corrected/ --output data/results/metrics.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-874-llmxive-follow-up-extending-enhancing-tr/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr/code/evaluate.py': [Errno 2] No such file or directory

- python code/analyze.py --metrics data/results/metrics.csv --output data/results/statistics.json -> rc=2

usage: analyze.py [-h] [--task TASK] [--metrics-file METRICS_FILE]
                  [--pilot-file PILOT_FILE]
analyze.py: error: unrecognized arguments: --output data/results/statistics.json

- python -m pytest tests/contract/ -> rc=2

tests/contract/test_metrics_schema.py:26: in <module>
    from code.config import get_results_dir, get_contract_dir
E   ImportError: cannot import name 'get_contract_dir' from 'code.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr/code/config.py)

During handling of the above exception, another exception occurred:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/contract/test_metrics_schema.py:31: in <module>
    from code.config import get_results_dir, get_contract_dir
E   ImportError: cannot import name 'get_contract_dir' from 'code.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr/code/config.py)
=========================== short test summary info ============================
ERROR tests/contract/test_download.py
ERROR tests/contract/test_flow_schema.py
ERROR tests/contract/test_metrics_schema.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 3 errors in 1.60s ===============================


## Platform-owned paths written inside the project

A script in this project created `.github/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
