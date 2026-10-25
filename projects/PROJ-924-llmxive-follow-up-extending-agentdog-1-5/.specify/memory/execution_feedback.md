# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/main.py --prepare-annotation`
  - script usage: `main.py [-h] [--validate-only] [--skip-taxonomy] [--skip-dataset-fetch]`
  - argparse error: `main.py: error: unrecognized arguments: --prepare-annotation`
- run-book command: `python code/validation.py --validate`
  - script usage: `validation.py [-h] [--drift DRIFT] [--ground_truth GROUND_TRUTH]`
  - argparse error: `validation.py: error: unrecognized arguments: --validate`
- run-book command: `python code/main.py --all`
  - script usage: `main.py [-h] [--validate-only] [--skip-taxonomy] [--skip-dataset-fetch]`
  - argparse error: `main.py: error: unrecognized arguments: --all`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/embeddings.py --generate-centroids; python code/embeddings.py --score; python code/baseline_llm.py --baseline; 5 command(s) failed: python -m pytest tests/unit/ -v | tee data/processed/test_results.log (rc=4); python code/data_loader.py --download (rc=1); python code/main.py --prepare-annotation (rc=2)

## Failing / missing run-book commands

- python -m pytest tests/unit/ -v | tee data/processed/test_results.log -> rc=4
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-8.2.0, pluggy-1.7.0 -- /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5
configfile: pyproject.toml
plugins: anyio-4.15.1
collecting ... collected 0 items

============================ no tests ran in 0.00s =============================

ERROR: file or directory not found: |


- python code/data_loader.py --download -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/data_loader.py", line 24, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/embeddings.py --generate-centroids -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/embeddings.py': [Errno 2] No such file or directory

- python code/embeddings.py --score -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/embeddings.py': [Errno 2] No such file or directory

- python code/main.py --prepare-annotation -> rc=2

usage: main.py [-h] [--validate-only] [--skip-taxonomy] [--skip-dataset-fetch]
main.py: error: unrecognized arguments: --prepare-annotation

- python code/validation.py --validate -> rc=2

usage: validation.py [-h] [--drift DRIFT] [--ground_truth GROUND_TRUTH]
                     [--annotations ANNOTATIONS] [--output OUTPUT]
validation.py: error: unrecognized arguments: --validate

- python code/baseline_llm.py --baseline -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/baseline_llm.py': [Errno 2] No such file or directory

- python code/report.py --generate -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/report.py': [Errno 2] No such file or directory

- python code/main.py --all -> rc=2

usage: main.py [-h] [--validate-only] [--skip-taxonomy] [--skip-dataset-fetch]
main.py: error: unrecognized arguments: --all

