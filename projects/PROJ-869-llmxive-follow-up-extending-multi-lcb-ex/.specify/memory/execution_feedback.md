# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/feasibility_gate.py: self-declared fabricated metric — “…"throughput": 5.0, # Mock value         "final_config": {},…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/feasibility_gate.py: self-declared fabricated metric — “…"throughput": 5.0, # Mock value         "final_config": {},…”; 7 command(s) failed: python -m src.data_loader --cache-dir data/raw --verify-checksum (rc=1); python -m src.data_loader --filter-stochasticity --output data/processed/filtered_tasks.json (rc=1); python -m src.anchor_extractor --input data/processed/filtered_tasks.json --output data/processed/anchors.json (rc=1); 1 declared deliverable(s) absent: data/feasibility_log.json

## Failing / missing run-book commands

- python -m src.data_loader --cache-dir data/raw --verify-checksum -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/bin/python: No module named src.data_loader

- python -m src.data_loader --filter-stochasticity --output data/processed/filtered_tasks.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/bin/python: No module named src.data_loader

- python -m src.anchor_extractor --input data/processed/filtered_tasks.json --output data/processed/anchors.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/bin/python: No module named src.anchor_extractor

- python -m src.inference_engine --condition blind --input data/processed/filtered_tasks.json --output results/blind_results.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/bin/python: No module named src.inference_engine

- python -m src.inference_engine --condition guided --input data/processed/filtered_tasks.json --anchors data/processed/anchors.json --output results/guided_results.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/bin/python: No module named src.inference_engine

- python -m src.sandbox_runner --input results/blind_results.json results/guided_results.json --timeout 10 --output results/execution_logs.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/bin/python: No module named src.sandbox_runner

- python -m src.stats_analyzer --input results/execution_logs.json --output results/statistical_report.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/bin/python: No module named src.stats_analyzer


## Declared deliverables still missing

- data/feasibility_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/feasibility_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/src/feasibility_gate.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/feasibility_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
