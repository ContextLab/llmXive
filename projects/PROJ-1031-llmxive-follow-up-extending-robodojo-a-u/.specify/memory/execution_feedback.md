# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/src/executor.py: self-declared fabricated metric — “…ction time                  # Mock result for demonstration if no real…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/utils/io.py --verify-checksums`
  - script usage: `io.py [-h] [--test]`
  - argparse error: `io.py: error: unrecognized arguments: --verify-checksums`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/src/executor.py: self-declared fabricated metric — “…ction time                  # Mock result for demonstration if no real…”; 9 command(s) failed: python code/src/main.py --stage download (rc=1); python code/src/main.py --stage embed --tasks 18 (rc=1); python code/src/main.py --stage plan --tasks 18 (rc=1); 2 declared deliverable(s) absent: data/interim/baseline_results.parquet; data/interim/execution_logs.parquet

## Failing / missing run-book commands

- python code/src/main.py --stage download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/main.py", line 27, in <module>
    from src.oracle_executor import OracleExecutor, run_oracle_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/oracle_executor.py", line 24, in <module>
    from src.config import DATA_INTERIM_PATH
ImportError: cannot import name 'DATA_INTERIM_PATH' from 'src.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/config.py)

- python code/src/main.py --stage embed --tasks 18 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/main.py", line 27, in <module>
    from src.oracle_executor import OracleExecutor, run_oracle_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/oracle_executor.py", line 24, in <module>
    from src.config import DATA_INTERIM_PATH
ImportError: cannot import name 'DATA_INTERIM_PATH' from 'src.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/config.py)

- python code/src/main.py --stage plan --tasks 18 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/main.py", line 27, in <module>
    from src.oracle_executor import OracleExecutor, run_oracle_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/oracle_executor.py", line 24, in <module>
    from src.config import DATA_INTERIM_PATH
ImportError: cannot import name 'DATA_INTERIM_PATH' from 'src.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/config.py)

- python code/src/main.py --stage execute --mode oracle -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/main.py", line 27, in <module>
    from src.oracle_executor import OracleExecutor, run_oracle_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/oracle_executor.py", line 24, in <module>
    from src.config import DATA_INTERIM_PATH
ImportError: cannot import name 'DATA_INTERIM_PATH' from 'src.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/config.py)

- python code/src/main.py --stage execute --mode real -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/main.py", line 27, in <module>
    from src.oracle_executor import OracleExecutor, run_oracle_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/oracle_executor.py", line 24, in <module>
    from src.config import DATA_INTERIM_PATH
ImportError: cannot import name 'DATA_INTERIM_PATH' from 'src.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/config.py)

- python code/src/main.py --stage baseline_gpu --subset 5 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/main.py", line 27, in <module>
    from src.oracle_executor import OracleExecutor, run_oracle_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/oracle_executor.py", line 24, in <module>
    from src.config import DATA_INTERIM_PATH
ImportError: cannot import name 'DATA_INTERIM_PATH' from 'src.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/config.py)

- python code/src/main.py --stage analyze -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/main.py", line 27, in <module>
    from src.oracle_executor import OracleExecutor, run_oracle_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/oracle_executor.py", line 24, in <module>
    from src.config import DATA_INTERIM_PATH
ImportError: cannot import name 'DATA_INTERIM_PATH' from 'src.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/config.py)

- python code/utils/io.py --verify-checksums -> rc=2

usage: io.py [-h] [--test]
io.py: error: unrecognized arguments: --verify-checksums

- python -c "import pandas as pd; print(pd.read_parquet('data/interim/execution_logs.parquet').head())" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 667, in read_parquet
    return impl.read(
           ^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 267, in read
    path_or_handle, handles, filesystem = _get_path_or_handle(
                                          ^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/parquet.py", line 140, in _get_path_or_handle
    handles = get_handle(
              ^^^^^^^^^^^
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/io/common.py", line 882, in get_handle
    handle = open(handle, ioargs.mode)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'data/interim/execution_logs.parquet'

- python -m pytest code/tests/ -v -> rc=2
cutor.py ______________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/tests/unit/test_oracle_executor.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
code/tests/unit/test_oracle_executor.py:15: in <module>
    from src.oracle_executor import OracleExecutor, OracleExecutionOutcome, run_oracle_pipeline
code/src/oracle_executor.py:24: in <module>
    from src.config import DATA_INTERIM_PATH
E   ImportError: cannot import name 'DATA_INTERIM_PATH' from 'src.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-1031-llmxive-follow-up-extending-robodojo-a-u/code/src/config.py)
=========================== short test summary info ============================
ERROR code/tests/unit/test_config.py
ERROR code/tests/unit/test_oracle_executor.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 3.17s ===============================



## Declared deliverables still missing

- data/interim/baseline_results.parquet
- data/interim/execution_logs.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/baseline_results.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/stats_analysis.py` — NOT invoked by the run-book
    - `code/tests/integration/test_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/baseline_results.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/execution_logs.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/src/executor.py` — NOT invoked by the run-book
    - `code/src/stats_analysis.py` — NOT invoked by the run-book
    - `code/tests/integration/test_executor_logging.py` — NOT invoked by the run-book
    - `code/tests/integration/test_failure_logging.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/execution_logs.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
