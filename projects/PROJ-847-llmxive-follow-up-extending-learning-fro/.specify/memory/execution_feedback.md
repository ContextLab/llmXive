# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python -m src.llmxive.data --download (rc=1); python -m src.llmxive.cli.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/fixed_baselines.json (rc=1); python -m src.llmxive.cli.run_experiments  --mode adaptive  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/adaptive_run.json (rc=1)

## Failing / missing run-book commands

- python -m src.llmxive.data --download -> rc=1
runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/src/llmxive/data.py", line 3, in <module>
    from code.data import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 15, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m src.llmxive.cli.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/fixed_baselines.json -> rc=1
ts import main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/run_experiments.py", line 29, in <module>
    from code.data import download_all
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 15, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m src.llmxive.cli.run_experiments  --mode adaptive  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/adaptive_run.json -> rc=1
ts import main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/run_experiments.py", line 29, in <module>
    from code.data import download_all
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 15, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python -m src.llmxive.cli.run_experiments  --mode control_shuffle  --seeds 42 43 44 45 46 47 48 49 50 51  --output outputs/control_shuffle.json -> rc=1
ts import main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/run_experiments.py", line 29, in <module>
    from code.data import download_all
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 15, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

