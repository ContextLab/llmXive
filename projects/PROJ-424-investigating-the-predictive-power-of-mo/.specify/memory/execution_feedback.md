# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/reporting/plots.py: synthetic/fake INPUT data not authorized by the spec — “…tting function."""     # Mock data     results = […”
- code/simulation/runner.py: synthetic/fake INPUT data not authorized by the spec — “…# Write some dummy coordinate data to make it look real…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/reporting/plots.py: synthetic/fake INPUT data not authorized by the spec — “…tting function."""     # Mock data     results = […”; code/simulation/runner.py: synthetic/fake INPUT data not authorized by the spec — “…# Write some dummy coordinate data to make it look real…”; 2 command(s) failed: python code/main.py --full-batch (rc=1); python code/pipeline.py --solvent water --duration 1 --seed 0 (rc=1)

## Failing / missing run-book commands

- python code/main.py --full-batch -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-424-investigating-the-predictive-power-of-mo/code/main.py", line 17, in <module>
    from config import (
ImportError: cannot import name 'SIMULATION_CONFIG' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-424-investigating-the-predictive-power-of-mo/code/config.py)

- python code/pipeline.py --solvent water --duration 1 --seed 0 -> rc=1
NFO __main__: Pipeline start: water, 1.0ns, seed 0
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-424-investigating-the-predictive-power-of-mo/code/pipeline.py", line 127, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-424-investigating-the-predictive-power-of-mo/code/pipeline.py", line 124, in main
    run_pipeline(solvent=args.solvent, duration_ns=args.duration, seed=args.seed)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-424-investigating-the-predictive-power-of-mo/code/pipeline.py", line 78, in run_pipeline
    refs = load_refs()
           ^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-424-investigating-the-predictive-power-of-mo/code/data/loader.py", line 89, in load_refs
    _verify_checksum(json_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-424-investigating-the-predictive-power-of-mo/code/data/loader.py", line 54, in _verify_checksum
    raise ValueError(
ValueError: Checksum mismatch for nist_refs.json: computed a81b3f2b1c6059459e121dfa834574745ef83bfa95b338c5007b7ebf6dbc4e7d, expected 6c9f020e8c6683c7b2e406c1c5caa5f7a0c0d8591b3c0e5c9f7a2d1e4c3b7a5f

