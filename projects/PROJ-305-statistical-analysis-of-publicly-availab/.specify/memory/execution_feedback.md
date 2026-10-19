# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/data/validate.py`
  - script usage: `validate.py [-h] --input INPUT [--schema SCHEMA]`
  - argparse error: `validate.py: error: the following arguments are required: --input`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python src/data/download.py (rc=1); python src/data/validate.py (rc=2); python code/src/data/clean.py (rc=1)

## Failing / missing run-book commands

- python src/data/download.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/src/data/download.py", line 22, in <module>
    from huggingface_hub import hf_hub_download, RepositoryNotFoundError, RevisionNotFoundError, HfHubHTTPError
ImportError: cannot import name 'RepositoryNotFoundError' from 'huggingface_hub' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-305-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/huggingface_hub/__init__.py)

- python src/data/validate.py -> rc=2

usage: validate.py [-h] --input INPUT [--schema SCHEMA]
validate.py: error: the following arguments are required: --input

- python code/src/data/clean.py -> rc=1

2026-10-19 04:15:04,972 - clean - INFO - Starting data cleaning process
2026-10-19 04:15:04,972 - clean - ERROR - No VAERS CSV files found in /home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/code/data/raw

- python src/main.py -> rc=1
2026-10-19 04:15:05,719 - pipeline - INFO - No action specified. Use --full or --phase N


- python -m pytest -q tests/contract/ -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract/


