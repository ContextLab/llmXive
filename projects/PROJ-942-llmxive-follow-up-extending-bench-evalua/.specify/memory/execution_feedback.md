# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 run-book script(s) missing (plan/impl path mismatch): python src/pipelines/build_intent_graph.py  --traces-csv data/derived/normalized_traces.csv  --inferred-csv data/derived/inferred_intents.csv  --out-dir data/derived/intent_graphs  --latency-out data/derived/graph_construction_latency.csv  --max-tokens 2048; python src/pipelines/build_intent_graph_gt.py  --traces-csv data/derived/normalized_traces.csv  --out-dir data/derived/intent_graphs_gt  --latency-out data/derived/graph_construction_latency.csv  --max-tokens 2048; python src/pipelines/run_lightweight_agent.py  --graph-dir data/derived/intent_graphs  --seed $SEED  --out data/derived/inference_logs/lightweight_seed${SEED}.csv; 3 command(s) failed: python src/pipelines/download_pi_bench.py (rc=1); python src/pipelines/parse_traces.py  --raw-dir data/raw  --out-csv data/derived/normalized_traces.csv (rc=1); python code/pipelines/infer_missing_intents.py --input-csv data/derived/normalized_traces.csv --out-csv data/derived/inferred_intents.csv --seed 42 (rc=1)

## Failing / missing run-book commands

- python src/pipelines/download_pi_bench.py -> rc=1
e_hub/utils/_validators.py", line 89, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/lib/python3.11/site-packages/huggingface_hub/hf_api.py", line 3259, in dataset_info
    hf_raise_for_status(r)
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/lib/python3.11/site-packages/huggingface_hub/utils/_http.py", line 953, in hf_raise_for_status
    raise _format(RepositoryNotFoundError, message, response, repo_type=repo_type, repo_id=repo_id) from e
huggingface_hub.errors.RepositoryNotFoundError: 401 Client Error. (Request ID: Root=1-6ada7028-52c24cbe05c75f562e3754cc;5e632aed-a460-483f-8385-045a978443c3)

Repository Not Found for url: https://huggingface.co/api/datasets/pi_bench/revision/main.
Please make sure you specified the correct `repo_id` and `repo_type`.
If you are trying to access a private or gated repo, make sure you are authenticated and your token has the required permissions.
For more details, see https://huggingface.co/docs/huggingface_hub/authentication
Invalid username or password.

- python src/pipelines/parse_traces.py  --raw-dir data/raw  --out-csv data/derived/normalized_traces.csv -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/parse_traces.py", line 35, in <module>
    _run_underlying()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/parse_traces.py", line 30, in _run_underlying
    runpy.run_path(str(impl_path), run_name="__main__")
  File "<frozen runpy>", line 291, in run_path
  File "<frozen runpy>", line 98, in _run_module_code
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/parse_traces.py", line 114, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/parse_traces.py", line 96, in main
    raise FileNotFoundError(f"No JSON files found in {raw_dir}")
FileNotFoundError: No JSON files found in data/raw

- python code/pipelines/infer_missing_intents.py --input-csv data/derived/normalized_traces.csv --out-csv data/derived/inferred_intents.csv --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/infer_missing_intents.py", line 32, in <module>
    import torch
ModuleNotFoundError: No module named 'torch'

- python src/pipelines/build_intent_graph.py  --traces-csv data/derived/normalized_traces.csv  --inferred-csv data/derived/inferred_intents.csv  --out-dir data/derived/intent_graphs  --latency-out data/derived/graph_construction_latency.csv  --max-tokens 2048 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/build_intent_graph.py': [Errno 2] No such file or directory

- python src/pipelines/build_intent_graph_gt.py  --traces-csv data/derived/normalized_traces.csv  --out-dir data/derived/intent_graphs_gt  --latency-out data/derived/graph_construction_latency.csv  --max-tokens 2048 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/build_intent_graph_gt.py': [Errno 2] No such file or directory

- python src/pipelines/run_lightweight_agent.py  --graph-dir data/derived/intent_graphs  --seed $SEED  --out data/derived/inference_logs/lightweight_seed${SEED}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/run_lightweight_agent.py': [Errno 2] No such file or directory

- python src/pipelines/run_lightweight_agent_gt.py  --graph-dir data/derived/intent_graphs_gt  --seed $SEED  --out data/derived/inference_logs/lightweight_gt_seed${SEED}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/run_lightweight_agent_gt.py': [Errno 2] No such file or directory

- python src/pipelines/run_raw_baseline.py  --raw-dir data/raw  --max-tokens 2048  --seed $SEED  --out data/derived/inference_logs/raw_seed${SEED}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/run_raw_baseline.py': [Errno 2] No such file or directory

- python src/pipelines/run_null_baseline.py  --raw-dir data/raw  --seed $SEED  --out data/derived/inference_logs/null_seed${SEED}.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/run_null_baseline.py': [Errno 2] No such file or directory

- python src/pipelines/evaluate.py  --logs-dir data/derived/inference_logs  --graph-dir data/derived/intent_graphs  --graph-gt-dir data/derived/intent_graphs_gt  --graph-latency data/derived/graph_construction_latency.csv  --out-dir data/derived/eval_results -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-942-llmxive-follow-up-extending-bench-evalua/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/src/pipelines/evaluate.py': [Errno 2] No such file or directory

