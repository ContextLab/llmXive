# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/data/generate_processed_data.py (rc=1); python code/training/train_gnn.py (rc=1); python code/training/train_rf.py (rc=1); 1 declared deliverable(s) absent: data/processed/molecules_10k.parquet

## Failing / missing run-book commands

- python code/data/generate_processed_data.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/generate_processed_data.py", line 41, in <module>
    import numpy as np
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/numpy/__init__.py", line 19, in <module>
    _real_numpy_module = importlib.import_module('numpy_real')
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/numpy_real.py", line 27, in <module>
    __version__ = _real_numpy.__version__
                  ^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: partially initialized module 'numpy' has no attribute '__version__' (most likely due to a circular import)
- python code/training/train_gnn.py -> rc=1
    llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/numpy_real.py", line 20, in <module>
    _real_numpy = _importlib.import_module("numpy")
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 940, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/numpy/__init__.py", line 23, in <module>
    raise ImportError("Failed to locate the real NumPy implementation via numpy_real.")
ImportError: Failed to locate the real NumPy implementation via numpy_real.
- python code/training/train_rf.py -> rc=1
    /PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_rf.py", line 24, in <module>
    import pandas as pd
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/pandas/__init__.py", line 11, in <module>
    __import__(_dependency)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/numpy/__init__.py", line 19, in <module>
    _real_numpy_module = importlib.import_module('numpy_real')
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/numpy_real.py", line 27, in <module>
    __version__ = _real_numpy.__version__
                  ^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: partially initialized module 'numpy' has no attribute '__version__' (most likely due to a circular import)
- python code/analysis/generate_performance_plots.py -> rc=1
    ng-molecular-dipole-moments-with/code/analysis/generate_performance_plots.py", line 29, in <module>
    import pandas as pd
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/.venv/lib/python3.11/site-packages/pandas/__init__.py", line 11, in <module>
    __import__(_dependency)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/numpy/__init__.py", line 19, in <module>
    _real_numpy_module = importlib.import_module('numpy_real')
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/numpy_real.py", line 27, in <module>
    __version__ = _real_numpy.__version__
                  ^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: partially initialized module 'numpy' has no attribute '__version__' (most likely due to a circular import)
- python code/analysis/generate_significance.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/generate_significance.py", line 17, in <module>
    import numpy as np
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/numpy/__init__.py", line 19, in <module>
    _real_numpy_module = importlib.import_module('numpy_real')
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.15/x64/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/numpy_real.py", line 27, in <module>
    __version__ = _real_numpy.__version__
                  ^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: partially initialized module 'numpy' has no attribute '__version__' (most likely due to a circular import)
- python code/generate_summary.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/generate_summary.py", line 162, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/generate_summary.py", line 153, in main
    generate_summary(
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/generate_summary.py", line 66, in generate_summary
    significance = load_csv_as_dicts(significance_path)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-262-predicting-molecular-dipole-moments-with/code/generate_summary.py", line 25, in load_csv_as_dicts
    raise FileNotFoundError(f"CSV file not found: {csv_path}")
FileNotFoundError: CSV file not found: results/significance.csv

## Declared deliverables still missing

- data/processed/molecules_10k.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/molecules_10k.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/quickstart_validation.py` — NOT invoked by the run-book
    - `code/data/generate_processed_data.py` — IS a run-book command
    - `code/training/train_rf.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/molecules_10k.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `results/significance.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/generate_summary.py`, `code/analysis/generate_significance.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `results/significance.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/generate_summary.py`, `code/quickstart_validation.py`, `code/analysis/generate_significance.py`.
