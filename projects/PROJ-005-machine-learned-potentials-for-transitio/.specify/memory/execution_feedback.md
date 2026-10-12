# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): bash ./scripts/run_full_pipeline.sh; 7 command(s) failed: python src/data/ingest.py --fetch (rc=1); python src/data/ingest.py --verify (rc=1); python code/src/data/graph_construction.py (rc=1)

## Failing / missing run-book commands

- python src/data/ingest.py --fetch -> rc=1
Error: 'datasets' package is required. Install it with: pip install datasets


- python src/data/ingest.py --verify -> rc=1
Error: 'datasets' package is required. Install it with: pip install datasets


- python code/src/data/graph_construction.py -> rc=1
Warning: Config file code/specs/config.yaml not found. Using defaults.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-005-machine-learned-potentials-for-transitio/code/src/data/graph_construction.py", line 14, in <module>
    from src.utils.config import get_project_root
ImportError: cannot import name 'get_project_root' from 'src.utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-005-machine-learned-potentials-for-transitio/code/src/utils/config.py)

- python code/src/models/ensemble.py --epochs 30 --seed 42 -> rc=1
Warning: Config file code/specs/config.yaml not found. Using defaults.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-005-machine-learned-potentials-for-transitio/code/src/models/ensemble.py", line 14, in <module>
    from src.utils.config import load_config, get_project_root
ImportError: cannot import name 'get_project_root' from 'src.utils.config' (/home/runner/work/llmXive/llmXive/projects/PROJ-005-machine-learned-potentials-for-transitio/code/src/utils/config.py)

- python code/src/models/predict.py --test-split -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-005-machine-learned-potentials-for-transitio/code/src/models/predict.py", line 35, in <module>
    logging.FileHandler(ROOT / "logs" / "predict.log", mode="a", encoding="utf-8"),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1181, in __init__
    StreamHandler.__init__(self, self._open())
                                 ^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/logging/__init__.py", line 1213, in _open
    return open_func(self.baseFilename, self.mode,
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/llmXive/llmXive/projects/PROJ-005-machine-learned-potentials-for-transitio/logs/predict.log'

- python code/src/analysis/feature_importance.py -> rc=1
{"timestamp": "2026-10-12T16:19:42.092108Z", "level": "ERROR", "logger": "__main__", "message": "No model checkpoints found in data/processed/models/", "module": "feature_importance", "function": "main", "line": 451}

WARNING:root:Captum not installed. Integrated Gradients will be unavailable.

- python code/src/analysis/statistics.py -> rc=1
^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-005-machine-learned-potentials-for-transitio/code/src/analysis/statistics.py", line 48, in load_residuals_with_ligand_labels
    df = pd.read_parquet(residuals_path)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-005-machine-learned-potentials-for-transitio/lib/python3.11/site-packages/pandas/io/parquet.py", line 654, in read_parquet
    impl = get_engine(engine)
           ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-005-machine-learned-potentials-for-transitio/lib/python3.11/site-packages/pandas/io/parquet.py", line 66, in get_engine
    raise ImportError(
ImportError: Unable to find a usable engine; tried using: 'pyarrow', 'fastparquet'.
A suitable version of pyarrow or fastparquet is required for parquet support.
Trying to import the above resulted in these errors:
 - Missing optional dependency 'pyarrow'. pyarrow is required for parquet support. Use pip or conda to install pyarrow.
 - Missing optional dependency 'fastparquet'. fastparquet is required for parquet support. Use pip or conda to install fastparquet.

- bash ./scripts/run_full_pipeline.sh -> rc=-1

shell script must be an existing project-local .sh file
