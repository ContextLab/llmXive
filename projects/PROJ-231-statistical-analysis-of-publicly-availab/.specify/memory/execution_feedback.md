# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/ingestion.py --mode download --dataset sungduk/wip_cmip6 --shard test-00000-of-00012 (rc=1); python code/main.py (rc=1); python -m pytest tests/unit/ (rc=2)

## Failing / missing run-book commands

- python code/ingestion.py --mode download --dataset sungduk/wip_cmip6 --shard test-00000-of-00012 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-231-statistical-analysis-of-publicly-availab/code/ingestion.py", line 8, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-231-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/datasets/__init__.py", line 22, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-231-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-231-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python code/main.py -> rc=1
 "/home/runner/work/llmXive/llmXive/projects/PROJ-231-statistical-analysis-of-publicly-availab/code/main.py", line 20, in <module>
    from ingestion import download_cmip6_data, apply_imputation_to_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-231-statistical-analysis-of-publicly-availab/code/ingestion.py", line 8, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-231-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/datasets/__init__.py", line 22, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-231-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 60, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-231-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m pytest tests/unit/ -> rc=2
al-analysis-of-publicly-availab/lib/python3.11/site-packages/matplotlib/_fontconfig_pattern.py:92: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

../../.llmxive-venvs/PROJ-231-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/matplotlib/_mathtext.py:45
  /home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-231-statistical-analysis-of-publicly-availab/lib/python3.11/site-packages/matplotlib/_mathtext.py:45: PyparsingDeprecationWarning: 'enablePackrat' deprecated - use 'enable_packrat'
    ParserElement.enablePackrat()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/unit/test_basis.py
ERROR tests/unit/test_fpca.py
ERROR tests/unit/test_imputation_fallback.py
ERROR tests/unit/test_ingestion.py
ERROR tests/unit/test_robustness.py
ERROR tests/unit/test_robustness_t030.py
ERROR tests/unit/test_run_basis.py
ERROR tests/unit/test_visualize.py
!!!!!!!!!!!!!!!!!!! Interrupted: 8 errors during collection !!!!!!!!!!!!!!!!!!!!
======================== 13 warnings, 8 errors in 1.14s ========================


- python -m pytest tests/contract/ -> rc=5
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-7.4.4, pluggy-1.7.0
rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-231-statistical-analysis-of-publicly-availab
plugins: platformdirs-4.13.0, cov-4.1.0, anyio-4.15.1
collected 0 items

============================ no tests ran in 0.01s =============================


