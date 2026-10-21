# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/msd.py: self-declared fabricated metric — “…t_ns = t * 0.01 # arbitrary scaling for mock                 msd_…”
- code/analysis/msd.py: synthetic/fake INPUT data not authorized by the spec — “…# Parse the mock file to generate synthetic but deterministic MSD da…”
- code/reporting/plots.py: synthetic/fake INPUT data not authorized by the spec — “…tting function."""     # Mock data     results = […”
- code/simulation/runner.py: synthetic/fake INPUT data not authorized by the spec — “…# Write some dummy coordinate data to make it look real…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/msd.py: self-declared fabricated metric — “…t_ns = t * 0.01 # arbitrary scaling for mock                 msd_…”; code/analysis/msd.py: synthetic/fake INPUT data not authorized by the spec — “…# Parse the mock file to generate synthetic but deterministic MSD da…”; code/reporting/plots.py: synthetic/fake INPUT data not authorized by the spec — “…tting function."""     # Mock data     results = […”; 1 run-book script(s) missing (plan/impl path mismatch): python code/pipeline.py            # simulations + analysis + reporting; 1 command(s) failed: python code/simulations/run_simulation.py --solvents water ethanol acetone --durations 1 5 10 --seeds 3 (rc=1)

## Failing / missing run-book commands

- python code/pipeline.py            # simulations + analysis + reporting -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-424-investigating-the-predictive-power-of-mo/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-424-investigating-the-predictive-power-of-mo/code/pipeline.py': [Errno 2] No such file or directory

- python code/simulations/run_simulation.py --solvents water ethanol acetone --durations 1 5 10 --seeds 3 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-424-investigating-the-predictive-power-of-mo/code/simulations/run_simulation.py", line 26, in <module>
    from openmm import Simulation
ImportError: cannot import name 'Simulation' from 'openmm' (/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-424-investigating-the-predictive-power-of-mo/lib/python3.11/site-packages/openmm/__init__.py)

