# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/analysis/visualize_features.py`
- `python code/attribution.py`
- `python code/data/preprocess_3d.py`
- `python code/download_data.py`
- `python code/stats.py`
- `python code/train.py --seeds 0 1 2 3 4`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/download_data.py; python code/train.py --seeds 0 1 2 3 4; python code/attribution.py; 2 command(s) failed: python code/data/preprocess_3d.py (rc=1); python code/analysis/visualize_features.py (rc=1); 1 declared deliverable(s) absent: data/reports/excluded_molecules.csv

## Failing / missing run-book commands

- python code/download_data.py -> rc=2 [script missing]
    Error in sitecustomize; set PYTHONVERBOSE for traceback:
ImportError: Real NumPy package not found in site‑packages.
/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/download_data.py': [Errno 2] No such file or directory
- python code/data/preprocess_3d.py -> rc=1
    Error in sitecustomize; set PYTHONVERBOSE for traceback:
ImportError: Real NumPy package not found in site‑packages.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/preprocess_3d.py", line 3, in <module>
    import numpy as np
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/numpy/__init__.py", line 17, in <module>
    from ..numpy_real import *  # noqa: F403,F401
    ^^^^^^^^^^^^^^^^^^^^^^^^^^
ImportError: attempted relative import beyond top-level package
- python code/train.py --seeds 0 1 2 3 4 -> rc=2 [script missing]
    Error in sitecustomize; set PYTHONVERBOSE for traceback:
ImportError: Real NumPy package not found in site‑packages.
/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/train.py': [Errno 2] No such file or directory
- python code/attribution.py -> rc=2 [script missing]
    Error in sitecustomize; set PYTHONVERBOSE for traceback:
ImportError: Real NumPy package not found in site‑packages.
/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/attribution.py': [Errno 2] No such file or directory
- python code/analysis/visualize_features.py -> rc=1
    Error in sitecustomize; set PYTHONVERBOSE for traceback:
ImportError: Real NumPy package not found in site‑packages.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/visualize_features.py", line 37, in <module>
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3D projection)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'mpl_toolkits'
- python code/stats.py -> rc=2 [script missing]
    Error in sitecustomize; set PYTHONVERBOSE for traceback:
ImportError: Real NumPy package not found in site‑packages.
/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/stats.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/reports/excluded_molecules.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/reports/excluded_molecules.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/generate_processed_data.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/reports/excluded_molecules.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `results/significance.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/generate_summary.py`, `code/analysis/generate_significance.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `results/significance.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/generate_summary.py`, `code/quickstart_validation.py`, `code/analysis/generate_significance.py`.
