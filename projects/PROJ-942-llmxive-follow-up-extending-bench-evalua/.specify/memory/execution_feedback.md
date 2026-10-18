# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python src/pipelines/parse_traces.py  --raw-dir data/raw  --out-csv data/derived/normalized_traces.csv; python src/pipelines/build_intent_graph.py  --input-csv data/derived/normalized_traces.csv  --out-dir data/derived/intent_graphs  --seed 42; python src/pipelines/run_lightweight_agent.py  --graph-dir data/derived/intent_graphs  --seed $SEED  --out data/derived/inference_logs/lightweight_seed${SEED}.csv

## Failing / missing run-book commands

- python -c "from datasets import load_dataset; load_dataset('pi_bench', data_dir='data/raw')" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/lib/python3.11/site-packages/datasets/__init__.py", line 17, in <module>
    from .arrow_dataset import Column, Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

- python src/pipelines/parse_traces.py  --raw-dir data/raw  --out-csv data/derived/normalized_traces.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/parse_traces.py': [Errno 2] No such file or directory

- python src/pipelines/build_intent_graph.py  --input-csv data/derived/normalized_traces.csv  --out-dir data/derived/intent_graphs  --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/build_intent_graph.py': [Errno 2] No such file or directory

- python src/pipelines/run_lightweight_agent.py  --graph-dir data/derived/intent_graphs  --seed $SEED  --out data/derived/inference_logs/lightweight_seed${SEED}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/run_lightweight_agent.py': [Errno 2] No such file or directory

- python src/pipelines/run_raw_baseline.py  --raw-dir data/raw  --seed $SEED  --out data/derived/inference_logs/raw_seed${SEED}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/run_raw_baseline.py': [Errno 2] No such file or directory

- python src/pipelines/run_null_baseline.py  --raw-dir data/raw  --seed $SEED  --out data/derived/inference_logs/null_seed${SEED}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/run_null_baseline.py': [Errno 2] No such file or directory

- python src/pipelines/evaluate.py  --logs-dir data/derived/inference_logs  --graph-dir data/derived/intent_graphs  --out-dir data/derived/eval_results -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/evaluate.py': [Errno 2] No such file or directory

