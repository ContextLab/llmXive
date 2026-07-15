# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/reporting.py: synthetic/fake INPUT data not authorized by the spec — “…lines.append("- **Synthetic Data**: **No** synthetic data…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/reporting.py: synthetic/fake INPUT data not authorized by the spec — “…lines.append("- **Synthetic Data**: **No** synthetic data…”; 1 command(s) failed: python code/main.py (rc=1); 1 declared deliverable(s) absent: data/curated_builds.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    2026-07-15 15:10:44,709 - root - CRITICAL - Missing dependency: statsmodels. Please install via requirements.txt.

## Declared deliverables still missing

- data/curated_builds.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/curated_builds.csv` is declared but was NOT written. Scripts referencing it:
    - `code/models/lme_model.py` — NOT invoked by the run-book
    - `code/models/save_lme_artifact.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/reporting.py` — NOT invoked by the run-book
    - `code/tests/conftest.py` — NOT invoked by the run-book
    - `code/data/cleaning.py` — NOT invoked by the run-book
    - `code/data/preprocessing.py` — NOT invoked by the run-book
    - `code/data/version_artifact.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/curated_builds.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
