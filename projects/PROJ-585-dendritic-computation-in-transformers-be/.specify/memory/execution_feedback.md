# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 command(s) failed: python code/utils/download_data.py (rc=1); python code/experiments/train.py --config config.yaml (rc=1); python code/experiments/probe.py --input-dir data/experiments/ (rc=1)

## Failing / missing run-book commands

- python code/utils/download_data.py -> rc=1

2026-10-15 03:30:19,992 - INFO - Downloading https://huggingface.co/datasets/glue/resolve/main/SST-2/train.tsv → /home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be/data/raw/sst2/train.tsv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be/code/utils/download_data.py", line 93, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be/code/utils/download_data.py", line 78, in main
    download_file(url, dest_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be/code/utils/download_data.py", line 45, in download_file
    response.raise_for_status()
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://huggingface.co/datasets/nyu-mll/glue/resolve/main/SST-2/train.tsv

- python code/experiments/train.py --config config.yaml -> rc=1
zer, get_linear_schedule_with_warmup
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-585-dendritic-computation-in-transformers-be/lib/python3.11/site-packages/transformers/__init__.py", line 30, in <module>
    from . import dependency_versions_check
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-585-dendritic-computation-in-transformers-be/lib/python3.11/site-packages/transformers/dependency_versions_check.py", line 16, in <module>
    from .utils.versions import require_version, require_version_core
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-585-dendritic-computation-in-transformers-be/lib/python3.11/site-packages/transformers/utils/__init__.py", line 77, in <module>
    from .hub import (
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-585-dendritic-computation-in-transformers-be/lib/python3.11/site-packages/transformers/utils/hub.py", line 29, in <module>
    from huggingface_hub import (
ImportError: cannot import name 'ResolvedRevision' from 'huggingface_hub' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-585-dendritic-computation-in-transformers-be/lib/python3.11/site-packages/huggingface_hub/__init__.py)

- python code/experiments/probe.py --input-dir data/experiments/ -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be/code/experiments/probe.py", line 22, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-585-dendritic-computation-in-transformers-be/lib/python3.11/site-packages/datasets/__init__.py", line 22, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-585-dendritic-computation-in-transformers-be/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-585-dendritic-computation-in-transformers-be/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.24.3

- python code/experiments/analyze.py -> rc=1
tation-in-transformers-be/code/experiments/analyze.py", line 18, in <module>
    from experiments.probe import set_seed, load_checkpoint, extract_layer_features, train_linear_probe, load_sst2_data
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be/code/experiments/probe.py", line 22, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-585-dendritic-computation-in-transformers-be/lib/python3.11/site-packages/datasets/__init__.py", line 22, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-585-dendritic-computation-in-transformers-be/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-585-dendritic-computation-in-transformers-be/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.24.3

- python code/tests/test_architecture_match.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be/code/tests/test_architecture_match.py", line 26, in <module>
    from models.transformer_base import TransformerBaseline
ModuleNotFoundError: No module named 'models.transformer_base'

- python -m pytest code/tests/ -> rc=2
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be
plugins: anyio-4.15.1
collected 0 items / 1 error

==================================== ERRORS ====================================
____________ ERROR collecting code/tests/test_architecture_match.py ____________
ImportError while importing test module '/home/runner/work/llmXive/llmXive/projects/PROJ-585-dendritic-computation-in-transformers-be/code/tests/test_architecture_match.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
code/tests/test_architecture_match.py:26: in <module>
    from models.transformer_base import TransformerBaseline
E   ModuleNotFoundError: No module named 'models.transformer_base'
=========================== short test summary info ============================
ERROR code/tests/test_architecture_match.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.07s ===============================


