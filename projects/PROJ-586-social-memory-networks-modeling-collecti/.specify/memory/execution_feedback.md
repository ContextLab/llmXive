# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/loaders.py: synthetic/fake INPUT data not authorized by the spec — “…Currently only synthetic datasets are supported as per spe…”
- code/data/loaders.py: synthetic/fake INPUT data not authorized by the spec — “…"description": "Synthetic game data for social memory experi…”
- code/data/loaders.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate all synthetic datasets needed for the…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic dataset generation for social me…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…xperiments.  This module generates realistic synthetic game data for testing an…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…dation. Per spec FR-004, synthetic data is used as real datasets…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic game data for social mem…”
- code/data/synthetic.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate all synthetic datasets and save to dis…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 12 fabricated/simulated-result signal(s) — results are not real measurements: code/data/loaders.py: synthetic/fake INPUT data not authorized by the spec — “…Currently only synthetic datasets are supported as per spe…”; code/data/loaders.py: synthetic/fake INPUT data not authorized by the spec — “…"description": "Synthetic game data for social memory experi…”; code/data/loaders.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate all synthetic datasets needed for the…”; 2 command(s) failed: python code/run_experiment.py --context full --agents 3,5,7 --games 800 --plot scaling (rc=2); python code/run_experiment.py --context limited --agents 5 --games 1000 --thresholds 128,256,512 (rc=2)

## Failing / missing run-book commands

- python code/run_experiment.py --context full --agents 3,5,7 --games 800 --plot scaling -> rc=2
    usage: run_experiment.py [-h] [--context {full,limited}] [--agents AGENTS]
                         [--games GAMES] [--seed SEED]
                         [--output-dir OUTPUT_DIR] [--log-file LOG_FILE]
run_experiment.py: error: unrecognized arguments: --plot scaling
- python code/run_experiment.py --context limited --agents 5 --games 1000 --thresholds 128,256,512 -> rc=2
    usage: run_experiment.py [-h] [--context {full,limited}] [--agents AGENTS]
                         [--games GAMES] [--seed SEED]
                         [--output-dir OUTPUT_DIR] [--log-file LOG_FILE]
run_experiment.py: error: unrecognized arguments: --thresholds 128,256,512
- python -c "from data.loaders import verify_datasets; verify_datasets()" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
ImportError: cannot import name 'verify_datasets' from 'data.loaders' (/home/runner/work/llmXive/llmXive/projects/PROJ-586-social-memory-networks-modeling-collecti/code/data/loaders.py)
