# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/simulation/runner.py: self-declared fabricated metric — “…tency_ms": len(prompt) * 2  # Simulated latency         }  def load_annotated…”
- code/simulation/runner.py: metric `score` assigned from an RNG draw (line 28)

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/data/ingest.py --annotate --sample-size 500`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/simulation/runner.py: self-declared fabricated metric — “…tency_ms": len(prompt) * 2  # Simulated latency         }  def load_annotated…”; code/simulation/runner.py: metric `score` assigned from an RNG draw (line 28); 4 command(s) failed: python code/data/ingest.py --annotate --sample-size 500 (rc=1); python code/main.py --config code/config.yaml (rc=1); python code/analysis/viz.py --input data/simulation/results.csv --output plots/pareto_frontier.png (rc=1)

## Failing / missing run-book commands

- python code/data/ingest.py --annotate --sample-size 500 -> rc=1
    Attempting to load dataset: macaron-data/a2ui-bench (streaming=True)...

`trust_remote_code` is not supported anymore.
Please check that the Hugging Face dataset 'macaron-data/a2ui-bench' isn't based on a loading script and remove `trust_remote_code`.
If the dataset is based on a loading script, please ask the dataset author to remove it and convert it to a standard format like Parquet.
FATAL ERROR: CRITICAL: Failed to load real dataset from macaron-data/a2ui-bench. Error: Dataset 'macaron-data/a2ui-bench' doesn't exist on the Hub or cannot be accessed.. Per Data Hygiene Principle, this script does NOT support synthetic fallback. Please check your internet connection, dataset ID, or HuggingFace access.
- python code/main.py --config code/config.yaml -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-914-llmxive-follow-up-extending-macaron-a2ui/code/main.py", line 31, in <module>
    from models.router import load_router, run_inference
ModuleNotFoundError: No module named 'models.router'
- python code/analysis/viz.py --input data/simulation/results.csv --output plots/pareto_frontier.png -> rc=1
    2026-08-22 18:56:24,729 - ERROR - File not found: Input file not found: data/simulation/results.csv
- python code/analysis/stats.py --input data/simulation/results.csv --output data/analysis/stats_report.json -> rc=1
    ERROR:__main__:Analysis failed: Simulation results file not found: data/simulation/results.csv
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-914-llmxive-follow-up-extending-macaron-a2ui/code/analysis/stats.py", line 463, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-914-llmxive-follow-up-extending-macaron-a2ui/code/analysis/stats.py", line 425, in main
    df = load_simulation_data(args.input)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-914-llmxive-follow-up-extending-macaron-a2ui/code/analysis/stats.py", line 39, in load_simulation_data
    raise FileNotFoundError(f"Simulation results file not found: {input_path}")
FileNotFoundError: Simulation results file not found: data/simulation/results.csv

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/simulation/results.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/main.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/simulation/results.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/main.py`.
