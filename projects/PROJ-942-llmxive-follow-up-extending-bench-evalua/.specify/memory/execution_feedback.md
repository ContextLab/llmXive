# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/pipelines/parse_traces.py --raw-dir data/raw --out-csv data/derived/normalized_traces.csv`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 run-book script(s) missing (plan/impl path mismatch): python src/pipelines/build_intent_graph_llm.py  --input-csv data/derived/normalized_traces.csv  --out-dir data/derived/intent_graphs  --max-tokens $(cat data/derived/model_max_tokens.txt)  --seed 42  --latency-out data/derived/graph_construction_latency.csv; python src/pipelines/run_lightweight_agent.py  --graph-dir data/derived/intent_graphs  --seed $SEED  --out data/derived/inference_logs/lightweight_seed${SEED}.csv; python src/pipelines/run_raw_baseline.py  --raw-dir data/raw  --max-tokens $(cat data/derived/model_max_tokens.txt)  --seed $SEED  --out data/derived/inference_logs/raw_seed${SEED}.csv; 2 command(s) failed: python code/pipelines/download_pi_bench.py (rc=1); python code/pipelines/parse_traces.py --raw-dir data/raw --out-csv data/derived/normalized_traces.csv (rc=1)

## Failing / missing run-book commands

- python code/pipelines/download_pi_bench.py -> rc=1
ive-follow-up-extending-bench-evalua/lib/python3.11/site-packages/datasets/__init__.py", line 22, in <module>
    from .arrow_dataset import Dataset
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/lib/python3.11/site-packages/datasets/arrow_dataset.py", line 59, in <module>
    import pyarrow as pa
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/lib/python3.11/site-packages/pyarrow/__init__.py", line 59, in <module>
    from pyarrow.lib import (BuildInfo, CppBuildInfo, RuntimeInfo, set_timezone_db_path,
  File "pyarrow/lib.pyx", line 42, in init pyarrow.lib
ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/download_pi_bench.py", line 14, in <module>
    raise ImportError(
ImportError: The 'datasets' library is required and must be installable with a compatible pyarrow version. Ensure requirements.txt includes 'datasets' and 'pyarrow'.

- python code/pipelines/parse_traces.py --raw-dir data/raw --out-csv data/derived/normalized_traces.csv -> rc=1

2026-10-22 05:12:18,972 ERROR __main__: Failed to download pi_bench dataset: The `datasets` library is required to download the pi_bench dataset. Ensure it is installed (add `datasets` to requirements.txt).
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/parse_traces.py", line 184, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/parse_traces.py", line 140, in main
    json_files = _download_and_save_raw(raw_dir)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/parse_traces.py", line 26, in _download_and_save_raw
    raise ImportError(
ImportError: The `datasets` library is required to download the pi_bench dataset. Ensure it is installed (add `datasets` to requirements.txt).

- python src/pipelines/build_intent_graph_llm.py  --input-csv data/derived/normalized_traces.csv  --out-dir data/derived/intent_graphs  --max-tokens $(cat data/derived/model_max_tokens.txt)  --seed 42  --latency-out data/derived/graph_construction_latency.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/build_intent_graph_llm.py': [Errno 2] No such file or directory

- python src/pipelines/run_lightweight_agent.py  --graph-dir data/derived/intent_graphs  --seed $SEED  --out data/derived/inference_logs/lightweight_seed${SEED}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/run_lightweight_agent.py': [Errno 2] No such file or directory

- python src/pipelines/run_raw_baseline.py  --raw-dir data/raw  --max-tokens $(cat data/derived/model_max_tokens.txt)  --seed $SEED  --out data/derived/inference_logs/raw_seed${SEED}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/run_raw_baseline.py': [Errno 2] No such file or directory

- python src/pipelines/run_null_baseline.py  --raw-dir data/raw  --seed $SEED  --out data/derived/inference_logs/null_seed${SEED}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/run_null_baseline.py': [Errno 2] No such file or directory

- python src/pipelines/evaluate.py  --logs-dir data/derived/inference_logs  --graph-dir data/derived/intent_graphs  --graph-latency data/derived/graph_construction_latency.csv  --out-dir data/derived/eval_results -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/evaluate.py': [Errno 2] No such file or directory

