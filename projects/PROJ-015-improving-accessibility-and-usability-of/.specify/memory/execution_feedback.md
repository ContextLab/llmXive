# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/simulator/app.py: self-declared fabricated metric — “…engagement_time = 5.0 # Placeholder                          metrics = {                 "session…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/simulator/app.py: self-declared fabricated metric — “…engagement_time = 5.0 # Placeholder                          metrics = {                 "session…”; run-book completed but produced no data/figure artifacts; 1 declared deliverable(s) absent: data/processed/metrics_summary.csv

## Failing / missing run-book commands

- python -c "import scipy, matplotlib, pandas, streamlit; print('All dependencies OK')" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'scipy'

## Declared deliverables still missing

- data/processed/metrics_summary.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/metrics_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/perf_optimizer.py` — NOT invoked by the run-book
    - `code/analysis/generate_metrics_summary.py` — NOT invoked by the run-book
    - `code/analysis/visualizer.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
