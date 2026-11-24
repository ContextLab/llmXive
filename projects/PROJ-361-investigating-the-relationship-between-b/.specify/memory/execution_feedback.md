# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m pytest tests/ -v --cov=code`
  - argparse error: `__main__.py: error: unrecognized arguments: --cov=code`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 run-book script(s) missing (plan/impl path mismatch): python code/io/data_loader.py --download; python code/io/data_loader.py --verify; python code/preprocessing/pipeline.py --run-fmriprep; 3 command(s) failed: python -m pytest tests/unit/test_seeds.py -v (rc=4); python -m pytest tests/ -v --cov=code (rc=4); python -m pytest tests/contract/test_schemas.py -v (rc=4)

## Failing / missing run-book commands

- python -m pytest tests/unit/test_seeds.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-361-investigating-the-relationship-between-b/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-361-investigating-the-relationship-between-b
configfile: pyproject.toml
plugins: platformdirs-4.13.5
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/unit/test_seeds.py


- python code/io/data_loader.py --download -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-361-investigating-the-relationship-between-b/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-361-investigating-the-relationship-between-b/code/io/data_loader.py': [Errno 2] No such file or directory

- python code/io/data_loader.py --verify -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-361-investigating-the-relationship-between-b/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-361-investigating-the-relationship-between-b/code/io/data_loader.py': [Errno 2] No such file or directory

- python code/preprocessing/pipeline.py --run-fmriprep -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-361-investigating-the-relationship-between-b/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-361-investigating-the-relationship-between-b/code/preprocessing/pipeline.py': [Errno 2] No such file or directory

- python code/preprocessing/motion_qc.py --threshold 0.5 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-361-investigating-the-relationship-between-b/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-361-investigating-the-relationship-between-b/code/preprocessing/motion_qc.py': [Errno 2] No such file or directory

- python code/topology/metrics.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-361-investigating-the-relationship-between-b/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-361-investigating-the-relationship-between-b/code/topology/metrics.py': [Errno 2] No such file or directory

- python code/io/schema_registry.py --merge -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-361-investigating-the-relationship-between-b/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-361-investigating-the-relationship-between-b/code/io/schema_registry.py': [Errno 2] No such file or directory

- python code/statistics/correlation.py --fdr -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-361-investigating-the-relationship-between-b/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-361-investigating-the-relationship-between-b/code/statistics/correlation.py': [Errno 2] No such file or directory

- python -m pytest tests/ -v --cov=code -> rc=4

ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --cov=code
  inifile: /home/runner/work/llmXive/llmXive/projects/PROJ-361-investigating-the-relationship-between-b/pyproject.toml
  rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-361-investigating-the-relationship-between-b


- python -m pytest tests/contract/test_schemas.py -v -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-361-investigating-the-relationship-between-b/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-361-investigating-the-relationship-between-b
configfile: pyproject.toml
plugins: platformdirs-4.13.5
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: tests/contract/test_schemas.py


