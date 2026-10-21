# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python src/utils/compute_median_graph_token_budget.py --out data/derived/token_budget.txt; python src/pipelines/build_intent_graph.py  --input-csv data/derived/normalized_traces.csv  --out-dir data/derived/intent_graphs  --token-budget $(cat data/derived/token_budget.txt)  --seed 42  --log-latency data/derived/graph_construction_latency.csv; python src/pipelines/run_lightweight_agent.py  --graph-dir data/derived/intent_graphs  --seed $SEED  --out data/derived/inference_logs/lightweight_seed${SEED}.csv; 1 command(s) failed: python code/pipelines/parse_traces.py --raw-dir data/raw --out-csv data/derived/normalized_traces.csv (rc=1)

## Failing / missing run-book commands

- python -c "from datasets import load_dataset; load_dataset('pi_bench', data_dir='data/raw')" -> rc=1

Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/datasets.py", line 42, in load_dataset
    raise NotImplementedError(
NotImplementedError: This stub only implements JSON loading; received name='pi_bench'

- python code/pipelines/parse_traces.py --raw-dir data/raw --out-csv data/derived/normalized_traces.csv -> rc=1

2026-10-21 16:10:03,407 ERROR __main__: No JSON files found in data/raw
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/parse_traces.py", line 103, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/parse_traces.py", line 72, in main
    raise FileNotFoundError(f"No JSON files found in {raw_dir}")
FileNotFoundError: No JSON files found in data/raw

- python src/utils/compute_median_graph_token_budget.py --out data/derived/token_budget.txt -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/utils/compute_median_graph_token_budget.py': [Errno 2] No such file or directory

- python src/pipelines/build_intent_graph.py  --input-csv data/derived/normalized_traces.csv  --out-dir data/derived/intent_graphs  --token-budget $(cat data/derived/token_budget.txt)  --seed 42  --log-latency data/derived/graph_construction_latency.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/build_intent_graph.py': [Errno 2] No such file or directory

- python src/pipelines/run_lightweight_agent.py  --graph-dir data/derived/intent_graphs  --seed $SEED  --out data/derived/inference_logs/lightweight_seed${SEED}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/run_lightweight_agent.py': [Errno 2] No such file or directory

- python src/pipelines/run_raw_baseline.py  --raw-dir data/raw  --token-budget $(cat data/derived/token_budget.txt)  --seed $SEED  --out data/derived/inference_logs/raw_seed${SEED}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/run_raw_baseline.py': [Errno 2] No such file or directory

- python src/pipelines/run_null_baseline.py  --raw-dir data/raw  --seed $SEED  --out data/derived/inference_logs/null_seed${SEED}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/run_null_baseline.py': [Errno 2] No such file or directory

- python src/pipelines/evaluate.py  --logs-dir data/derived/inference_logs  --graph-dir data/derived/intent_graphs  --graph-latency data/derived/graph_construction_latency.csv  --out-dir data/derived/eval_results -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/evaluate.py': [Errno 2] No such file or directory

