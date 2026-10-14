# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/query_generator.py --levels 1 2 3 4 --count [sufficient sample size] --seed 42`
  - script usage: `query_generator.py [-h] --levels LEVELS [LEVELS ...] [--count COUNT]`
  - argparse error: `query_generator.py: error: unrecognized arguments: sample size]`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/data_loader.py --prepare; python code/ground_truth_engine.py --input data/processed/generation_log.json --output data/processed/generation_log.json; python code/benchmark_runner.py --throttle cgroups --timeout 60; 3 command(s) failed: python code/query_generator.py --levels 1 2 3 4 --count [sufficient sample size] --seed 42 (rc=2); python code/analysis/stats.py --input data/processed/execution_logs.csv (rc=1); python -m code.main (rc=1); 1 declared deliverable(s) absent: data/processed/execution_logs.csv

## Failing / missing run-book commands

- python code/data_loader.py --prepare -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-883-llmxive-follow-up-extending-omniretrieva/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/code/data_loader.py': [Errno 2] No such file or directory

- python code/query_generator.py --levels 1 2 3 4 --count [sufficient sample size] --seed 42 -> rc=2

usage: query_generator.py [-h] --levels LEVELS [LEVELS ...] [--count COUNT]
                          [--seed SEED] [--output OUTPUT]
query_generator.py: error: unrecognized arguments: sample size]

- python code/ground_truth_engine.py --input data/processed/generation_log.json --output data/processed/generation_log.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-883-llmxive-follow-up-extending-omniretrieva/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/code/ground_truth_engine.py': [Errno 2] No such file or directory

- python code/benchmark_runner.py --throttle cgroups --timeout 60 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-883-llmxive-follow-up-extending-omniretrieva/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/code/benchmark_runner.py': [Errno 2] No such file or directory

- python code/analysis/stats.py --input data/processed/execution_logs.csv -> rc=1
ode/analysis/stats.py", line 10, in load_execution_logs
    return pd.read_csv(filepath)
           ^^^^^^^^^^^^^^^^^^^^^
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
FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/execution_logs.csv'

- python code/visualize.py --input data/processed/execution_logs.csv --output data/results/interaction_plot.png -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-883-llmxive-follow-up-extending-omniretrieva/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/code/visualize.py': [Errno 2] No such file or directory

- python -m code.main -> rc=1

2026-10-14 05:30:28,402 INFO __main__: Verifying required datasets (real fetch)...
2026-10-14 05:30:28,403 INFO utils.data_fetcher: Dataset file /home/runner/work/llmXive/llmXive/projects/PROJ-883-llmxive-follow-up-extending-omniretrieva/data/raw/microsoft_ms_marco_v1.1_train.jsonl missing – fetching.
2026-10-14 05:30:28,647 ERROR utils.data_fetcher: Failed to import datasets library: pyarrow requires NumPy 2.0 or newer, found 1.26.4
2026-10-14 05:30:28,647 WARNING __main__: Skipping real dataset verification due to import error or fetch failure: Unable to import datasets library and synthetic fallback is disabled.
2026-10-14 05:30:28,647 INFO __main__: Proceeding with synthetic execution – the benchmark uses only synthetic queries and lightweight executors.
2026-10-14 05:30:28,652 ERROR __main__: CPU throttling could not be applied: Failed to create cgroup directory /sys/fs/cgroup/llmxive_throttle_5402: [Errno 13] Permission denied: '/sys/fs/cgroup/llmxive_throttle_5402'


## Declared deliverables still missing

- data/processed/execution_logs.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/execution_logs.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/stats.py` — IS a run-book command
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/execution_logs.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
