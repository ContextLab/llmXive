# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/pipelines/infer_missing_intents.py --input-csv data/derived/normalized_traces.csv --out-csv data/derived/inferred_intents.csv --seed 42`
  - script usage: `infer_missing_intents.py [-h] --input-csv INPUT_CSV --out-csv OUT_CSV`
  - argparse error: `infer_missing_intents.py: error: unrecognized arguments: --seed 42`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 run-book script(s) missing (plan/impl path mismatch): python src/pipelines/build_intent_graph.py  --traces-csv data/derived/normalized_traces.csv  --inferred-csv data/derived/inferred_intents.csv  --out-dir data/derived/intent_graphs  --latency-out data/derived/graph_construction_latency.csv  --max-tokens 2048; python src/pipelines/build_intent_graph_gt.py  --traces-csv data/derived/normalized_traces.csv  --out-dir data/derived/intent_graphs_gt  --latency-out data/derived/graph_construction_latency.csv  --max-tokens 2048; python src/pipelines/run_lightweight_agent.py  --graph-dir data/derived/intent_graphs  --seed $SEED  --out data/derived/inference_logs/lightweight_seed${SEED}.csv; 3 command(s) failed: python src/pipelines/download_pi_bench.py (rc=1); python src/pipelines/parse_traces.py  --raw-dir data/raw  --out-csv data/derived/normalized_traces.csv (rc=1); python code/pipelines/infer_missing_intents.py --input-csv data/derived/normalized_traces.csv --out-csv data/derived/inferred_intents.csv --seed 42 (rc=2)

## Failing / missing run-book commands

- python src/pipelines/download_pi_bench.py -> rc=1
load_pi_bench.py", line 30, in _run_underlying
    runpy.run_path(str(impl_path), run_name="__main__")
  File "<frozen runpy>", line 291, in run_path
  File "<frozen runpy>", line 98, in _run_module_code
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/download_pi_bench.py", line 171, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/download_pi_bench.py", line 138, in main
    checksums = _download_pi_bench(
                ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/download_pi_bench.py", line 69, in _download_pi_bench
    dataset = load_dataset("pi_bench", streaming=True)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/datasets.py", line 40, in load_dataset
    raise ImportError(
ImportError: The stubbed `datasets` library only supports the 'json' format. Requested dataset: pi_bench

- python src/pipelines/parse_traces.py  --raw-dir data/raw  --out-csv data/derived/normalized_traces.csv -> rc=1
e_traces.py", line 30, in _run_underlying
    runpy.run_path(str(impl_path), run_name="__main__")
  File "<frozen runpy>", line 291, in run_path
  File "<frozen runpy>", line 98, in _run_module_code
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/parse_traces.py", line 184, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/parse_traces.py", line 140, in main
    json_files = _download_and_save_raw(raw_dir)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/code/pipelines/parse_traces.py", line 32, in _download_and_save_raw
    ds = load_dataset("pi_bench", streaming=True)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-942-llmxive-follow-up-extending-bench-evalua/datasets.py", line 40, in load_dataset
    raise ImportError(
ImportError: The stubbed `datasets` library only supports the 'json' format. Requested dataset: pi_bench

- python code/pipelines/infer_missing_intents.py --input-csv data/derived/normalized_traces.csv --out-csv data/derived/inferred_intents.csv --seed 42 -> rc=2

usage: infer_missing_intents.py [-h] --input-csv INPUT_CSV --out-csv OUT_CSV
infer_missing_intents.py: error: unrecognized arguments: --seed 42

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

