# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingestion.py: self-declared fabricated metric — “…'mean_atomic_radius'] = 10  # Dummy value     df['electronegativity_std…”
- code/ingestion.py: self-declared fabricated metric — “…ectronegativity_std'] = 2.5 # dummy value     return df  def validate_n…”
- code/verify_citation_log.py: synthetic/fake INPUT data not authorized by the spec — “…# Create a minimal dummy dataset for validation     # Thi…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/ingestion.py: self-declared fabricated metric — “…'mean_atomic_radius'] = 10  # Dummy value     df['electronegativity_std…”; code/ingestion.py: self-declared fabricated metric — “…ectronegativity_std'] = 2.5 # dummy value     return df  def validate_n…”; code/verify_citation_log.py: synthetic/fake INPUT data not authorized by the spec — “…# Create a minimal dummy dataset for validation     # Thi…”; 1 command(s) failed: python code/run_pipeline_timing.py (rc=1); 6 declared deliverable(s) absent: data/reports/data_availability_report.json; data/results/baseline_metrics.json; data/results/feature_ranking_table.csv

## Failing / missing run-book commands

- python code/run_pipeline_timing.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-314-predicting-the-impact-of-composition-on-/code/run_pipeline_timing.py", line 12, in <module>
    from ingestion import main as run_ingestion
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-314-predicting-the-impact-of-composition-on-/code/ingestion.py", line 1, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'

## Declared deliverables still missing

- data/reports/data_availability_report.json
- data/results/baseline_metrics.json
- data/results/feature_ranking_table.csv
- data/results/leakage_report.json
- data/results/shap_summary.png
- data/results/stability_metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/reports/data_availability_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/ingestion.py` — NOT invoked by the run-book
    - `code/scripts/run_gap_test.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/reports/data_availability_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/baseline_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/diagnostics.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/baseline_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/feature_ranking_table.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_shap_plots.py` — NOT invoked by the run-book
    - `code/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/feature_ranking_table.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/leakage_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_metrics_report.py` — NOT invoked by the run-book
    - `code/diagnostics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/leakage_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/shap_summary.png` is declared but was NOT written. Scripts referencing it:
    - `code/generate_shap_plots.py` — NOT invoked by the run-book
    - `code/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/shap_summary.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/stability_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_shap_plots.py` — NOT invoked by the run-book
    - `code/report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/stability_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
