# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python main_pipeline.py; python label_mapper.py --input data/processed/spectral_features.csv --lookup data/omniopt_lookup.json --output data/processed/labeled_dataset.json; python correlation_analyzer.py --input data/processed/labeled_dataset.json --output data/processed/results.json; 2 command(s) failed: python code/spectral_extractor.py --output data/processed/spectral_features.csv (rc=1); python -m pytest tests/ (rc=2)

## Failing / missing run-book commands

- python -c "from datasets import load_dataset; ds = load_dataset('Multimodal-Fatima/TinyImagenet_train', split='train', streaming=True); print(next(iter(ds)))" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python main_pipeline.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/main_pipeline.py': [Errno 2] No such file or directory

- python code/spectral_extractor.py --output data/processed/spectral_features.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/spectral_extractor.py", line 25, in <module>
    from torchvision import transforms
ModuleNotFoundError: No module named 'torchvision'

- python label_mapper.py --input data/processed/spectral_features.csv --lookup data/omniopt_lookup.json --output data/processed/labeled_dataset.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/label_mapper.py': [Errno 2] No such file or directory

- python correlation_analyzer.py --input data/processed/labeled_dataset.json --output data/processed/results.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/correlation_analyzer.py': [Errno 2] No such file or directory

- python -m pytest tests/ -> rc=2
ojects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/tests/integration/test_t013c_save_features.py _
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/tests/integration/test_t013c_save_features.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/integration/test_t013c_save_features.py:19: in <module>
    from extract_and_save_spectral_features import save_features_to_csv, main
code/extract_and_save_spectral_features.py:28: in <module>
    from spectral_extractor import (
code/spectral_extractor.py:25: in <module>
    from torchvision import transforms
E   ModuleNotFoundError: No module named 'torchvision'
=========================== short test summary info ============================
ERROR tests/integration/test_t013c_save_features.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 1.27s ===============================


## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
