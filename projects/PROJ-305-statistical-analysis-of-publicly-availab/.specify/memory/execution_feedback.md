# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/data/validate.py`
  - script usage: `validate.py [-h] --input INPUT [--schema SCHEMA]`
  - argparse error: `validate.py: error: the following arguments are required: --input`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python src/data/download.py (rc=1); python src/data/validate.py (rc=2); python src/data/clean.py (rc=1)

## Failing / missing run-book commands

- python src/data/download.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/src/data/download.py", line 15, in <module>
    from datasets import load_dataset, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-305-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-305-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-305-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python src/data/validate.py -> rc=2

usage: validate.py [-h] --input INPUT [--schema SCHEMA]
validate.py: error: the following arguments are required: --input

- python src/data/clean.py -> rc=1

2026-10-25 12:09:45,694 - clean - INFO - Starting data cleaning process
2026-10-25 12:09:45,695 - clean - ERROR - No VAERS data files found in /home/runner/work/llmXive/llmXive/projects/PROJ-305-statistical-analysis-of-publicly-availab/data/raw

- python src/main.py -> rc=1
2026-10-25 12:09:46,737 - matplotlib.font_manager - INFO - Failed to extract font properties from /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf: In FT2Font: Can not load face (unknown file format; error code 0x2)
2026-10-25 12:09:46,938 - matplotlib.font_manager - INFO - generated new fontManager
2026-10-25 12:09:47,213 - pipeline - INFO - No action specified. Use --full or --phase N


- python -m pytest -q tests/contract/ -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract/


