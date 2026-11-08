# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/feasibility_gate.py: self-declared fabricated metric — “…"throughput": 5.0, # Mock value         "final_config": {},…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/src/data_loader.py --filter-stochasticity --output data/processed/filtered_tasks.json`
  - script usage: `data_loader.py [-h] [--cache-dir CACHE_DIR] [--verify-checksum]`
  - argparse error: `data_loader.py: error: unrecognized arguments: --filter-stochasticity --output data/processed/filtered_tasks.json`

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/src/data_loader.py --cache-dir data/raw --verify-checksum`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/feasibility_gate.py: self-declared fabricated metric — “…"throughput": 5.0, # Mock value         "final_config": {},…”; 5 run-book script(s) missing (plan/impl path mismatch): python code/src/anchor_extractor.py --input data/processed/filtered_tasks.json --output data/processed/anchors.json; python code/src/inference_engine.py --condition blind --input data/processed/filtered_tasks.json --output results/blind_results.json; python code/src/inference_engine.py --condition guided --input data/processed/filtered_tasks.json --anchors data/processed/anchors.json --output results/guided_results.json; 2 command(s) failed: python code/src/data_loader.py --cache-dir data/raw --verify-checksum (rc=1); python code/src/data_loader.py --filter-stochasticity --output data/processed/filtered_tasks.json (rc=2); 1 declared deliverable(s) absent: data/feasibility_log.json

## Failing / missing run-book commands

- python code/src/data_loader.py --cache-dir data/raw --verify-checksum -> rc=1
follow-up-extending-multi-lcb-ex/lib/python3.11/site-packages/datasets/load.py", line 2556, in load_dataset
    builder_instance = load_dataset_builder(
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/lib/python3.11/site-packages/datasets/load.py", line 2228, in load_dataset_builder
    dataset_module = dataset_module_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/lib/python3.11/site-packages/datasets/load.py", line 1873, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/lib/python3.11/site-packages/datasets/load.py", line 1819, in dataset_module_factory
    raise DatasetNotFoundError(
datasets.exceptions.DatasetNotFoundError: Dataset 'multilcb' doesn't exist on the Hub or cannot be accessed. If the dataset is private or gated, make sure to log in with `huggingface-cli login` or visit the dataset page at https://huggingface.co/datasets/multilcb to ask for access.

- python code/src/data_loader.py --filter-stochasticity --output data/processed/filtered_tasks.json -> rc=2

usage: data_loader.py [-h] [--cache-dir CACHE_DIR] [--verify-checksum]
data_loader.py: error: unrecognized arguments: --filter-stochasticity --output data/processed/filtered_tasks.json

- python code/src/anchor_extractor.py --input data/processed/filtered_tasks.json --output data/processed/anchors.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/code/src/anchor_extractor.py': [Errno 2] No such file or directory

- python code/src/inference_engine.py --condition blind --input data/processed/filtered_tasks.json --output results/blind_results.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/code/src/inference_engine.py': [Errno 2] No such file or directory

- python code/src/inference_engine.py --condition guided --input data/processed/filtered_tasks.json --anchors data/processed/anchors.json --output results/guided_results.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/code/src/inference_engine.py': [Errno 2] No such file or directory

- python code/src/sandbox_runner.py --input results/blind_results.json results/guided_results.json --timeout 10 --output results/execution_logs.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/code/src/sandbox_runner.py': [Errno 2] No such file or directory

- python code/src/stats_analyzer.py --input results/execution_logs.json --output results/statistical_report.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/code/src/stats_analyzer.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/feasibility_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/feasibility_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/src/feasibility_gate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/feasibility_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
