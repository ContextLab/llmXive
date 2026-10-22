# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 command(s) failed: python -m src.llmxive.data --download (rc=1); python -m src.llmxive.cli.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61  --max_epochs 5  --output outputs/fixed_baselines.json (rc=1); python -m src.llmxive.cli.run_experiments  --mode adaptive  --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61  --max_epochs 5  --output outputs/adaptive_run.json (rc=1)

## Failing / missing run-book commands

- python -m src.llmxive.data --download -> rc=1
m code.data import (
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 38, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 58, in <module>
    import pandas as pd
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/__init__.py", line 26, in <module>
    from pandas.compat import (
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/compat/__init__.py", line 27, in <module>
    from pandas.compat.pyarrow import (
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/compat/pyarrow.py", line 10, in <module>
    _palv = Version(Version(pa.__version__).base_version)
                            ^^^^^^^^^^^^^^
AttributeError: module 'pyarrow' has no attribute '__version__'

- python -m src.llmxive.cli.run_experiments  --mode fixed  --rhos 0.1 0.3 0.5 0.7 0.9  --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61  --max_epochs 5  --output outputs/fixed_baselines.json -> rc=1
 import download_all
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 38, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 58, in <module>
    import pandas as pd
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/__init__.py", line 26, in <module>
    from pandas.compat import (
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/compat/__init__.py", line 27, in <module>
    from pandas.compat.pyarrow import (
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/compat/pyarrow.py", line 10, in <module>
    _palv = Version(Version(pa.__version__).base_version)
                            ^^^^^^^^^^^^^^
AttributeError: module 'pyarrow' has no attribute '__version__'

- python -m src.llmxive.cli.run_experiments  --mode adaptive  --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61  --max_epochs 5  --output outputs/adaptive_run.json -> rc=1
 import download_all
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 38, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 58, in <module>
    import pandas as pd
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/__init__.py", line 26, in <module>
    from pandas.compat import (
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/compat/__init__.py", line 27, in <module>
    from pandas.compat.pyarrow import (
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/compat/pyarrow.py", line 10, in <module>
    _palv = Version(Version(pa.__version__).base_version)
                            ^^^^^^^^^^^^^^
AttributeError: module 'pyarrow' has no attribute '__version__'

- python -m src.llmxive.cli.run_experiments  --mode control_shuffle  --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61  --max_epochs 5  --output outputs/control_shuffle.json -> rc=1
 import download_all
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 38, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 58, in <module>
    import pandas as pd
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/__init__.py", line 26, in <module>
    from pandas.compat import (
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/compat/__init__.py", line 27, in <module>
    from pandas.compat.pyarrow import (
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/compat/pyarrow.py", line 10, in <module>
    _palv = Version(Version(pa.__version__).base_version)
                            ^^^^^^^^^^^^^^
AttributeError: module 'pyarrow' has no attribute '__version__'

- python -m src.llmxive.cli.run_experiments  --mode fixed_median  --median_rho 0.55  --seeds 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61  --max_epochs 5  --output outputs/fixed_median.json -> rc=1
 import download_all
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-847-llmxive-follow-up-extending-learning-fro/code/data.py", line 38, in <module>
    from datasets import load_dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-847-llmxive-follow-up-extending-learning-fro/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 58, in <module>
    import pandas as pd
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/__init__.py", line 26, in <module>
    from pandas.compat import (
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/compat/__init__.py", line 27, in <module>
    from pandas.compat.pyarrow import (
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/compat/pyarrow.py", line 10, in <module>
    _palv = Version(Version(pa.__version__).base_version)
                            ^^^^^^^^^^^^^^
AttributeError: module 'pyarrow' has no attribute '__version__'

