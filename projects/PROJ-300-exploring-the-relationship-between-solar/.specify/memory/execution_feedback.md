# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/run_sensitivity_demo.py: synthetic/fake INPUT data not authorized by the spec — “…vity analysis on real or synthetic data and output results. This…”
- code/run_sensitivity_demo.py: synthetic/fake INPUT data not authorized by the spec — “…oints=5000):     """     Generate synthetic data that mimics the str…”
- code/run_sensitivity_demo.py: synthetic/fake INPUT data not authorized by the spec — “…# For this task, we generate synthetic data to ensure the scrip…”
- code/run_sensitivity_demo.py: synthetic/fake INPUT data not authorized by the spec — “…e.     print("Generating synthetic data for demonstration...")…”
- code/run_sensitivity_demo.py: synthetic/fake INPUT data not authorized by the spec — “…Clean and resample (even synthetic data needs alignment)     pri…”
- code/run_us3_sample.py: synthetic/fake INPUT data not authorized by the spec — “…# Fallback to a small synthetic dataset if real fetch fails (for…”
- code/run_us3_sample.py: synthetic/fake INPUT data not authorized by the spec — “…print("⚠️ Using synthetic fallback data due to fetch error.")…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 fabricated/simulated-result signal(s) — results are not real measurements: code/run_sensitivity_demo.py: synthetic/fake INPUT data not authorized by the spec — “…vity analysis on real or synthetic data and output results. This…”; code/run_sensitivity_demo.py: synthetic/fake INPUT data not authorized by the spec — “…oints=5000):     """     Generate synthetic data that mimics the str…”; code/run_sensitivity_demo.py: synthetic/fake INPUT data not authorized by the spec — “…# For this task, we generate synthetic data to ensure the scrip…”; 1 command(s) failed: python code/main.py --start 2023-01-01 --end 2023-01-03 (rc=1); 1 declared deliverable(s) absent: data/processed/quality_log.json

## Failing / missing run-book commands

- python code/main.py --start 2023-01-01 --end 2023-01-03 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py", line 15, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'

## Declared deliverables still missing

- data/processed/quality_log.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/quality_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_e2e_validation.py` — NOT invoked by the run-book
    - `code/run_us3_sample.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/quality_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
