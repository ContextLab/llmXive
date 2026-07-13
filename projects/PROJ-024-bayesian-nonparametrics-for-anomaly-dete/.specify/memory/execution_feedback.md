# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/evaluation/metrics.py: metric `y_scores` assigned from an RNG draw (line 363)
- code/evaluation/plots.py: metric `y_scores` assigned from an RNG draw (line 348)
- code/scripts/execute_evaluation_pipeline.py: self-declared fabricated metric — “…# No ground truth - use placeholder values             f1 = 0.0…”
- code/scripts/execute_evaluation_pipeline.py: self-declared fabricated metric — “…())                  # Return placeholder result         return EvaluationResu…”
- code/scripts/verify_confusion_matrix.py: metric `y_scores` assigned from an RNG draw (line 50)
- code/src/evaluation/metrics.py: metric `y_scores` assigned from an RNG draw (line 363)
- code/src/evaluation/plots.py: metric `y_scores` assigned from an RNG draw (line 348)
- code/src/services/threshold_calibrator.py: metric `normal_scores` assigned from an RNG draw (line 418)

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python code/src/config.py --check`
- `python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05`
- `python code/src/evaluation/robustness.py --subset-size 50`
- `python code/src/evaluation/simulation.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 79 fabricated/simulated-result signal(s) — results are not real measurements: code/evaluation/metrics.py: metric `y_scores` assigned from an RNG draw (line 363); code/evaluation/plots.py: metric `y_scores` assigned from an RNG draw (line 348); code/scripts/execute_evaluation_pipeline.py: self-declared fabricated metric — “…# No ground truth - use placeholder values             f1 = 0.0…”; 3 run-book script(s) missing (plan/impl path mismatch): python code/src/config.py --check; python code/src/evaluation/simulation.py; python code/src/evaluation/robustness.py --subset-size 50; 3 command(s) failed: python code/src/data/download_datasets.py (rc=1); python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05 (rc=2); python code/src/services/anomaly_detector.py (rc=1)

## Failing / missing run-book commands

- python code/src/config.py --check -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/config.py': [Errno 2] No such file or directory
- python code/src/data/download_datasets.py -> rc=1
    e/projects/data/raw/traffic.csv
2026-07-13 16:13:54,139 - ERROR - Download failed: HTTP Error 404: Not Found
2026-07-13 16:13:54,139 - INFO - Traffic: ✗
2026-07-13 16:13:54,139 - INFO - Downloading from https://archive.ics.uci.edu/static/public/363/synthetic_control_data.zip to /home/runner/work/llmXive/llmXive/projects/data/raw/synthetic_control_chart.csv
2026-07-13 16:13:54,567 - ERROR - Download failed: HTTP Error 404: Not Found
2026-07-13 16:13:54,567 - INFO - Synthetic Control Chart: ✗
2026-07-13 16:13:54,568 - INFO - Saved checksum cache to /home/runner/work/llmXive/llmXive/projects/state/checksums.json
2026-07-13 16:13:54,568 - INFO - ============================================================
2026-07-13 16:13:54,568 - INFO - Download Summary:
2026-07-13 16:13:54,568 - INFO - ============================================================
2026-07-13 16:13:54,568 - INFO -   electricity: FAILED - HTTP Error 404: Not Found
2026-07-13 16:13:54,568 - INFO -   traffic: FAILED - HTTP Error 404: Not Found
2026-07-13 16:13:54,568 - INFO -   synthetic_control_chart: FAILED - HTTP Error 404: Not Found
2026-07-13 16:13:54,568 - ERROR - ✗ Some downloads failed. Check error messages above.
- python code/src/data/synthetic_generator.py --seed 42 --anomaly-rate 0.05 -> rc=2
    usage: synthetic_generator.py [-h] [--n_samples N_SAMPLES]
                              [--anomaly_rate ANOMALY_RATE]
                              [--signal_type {sine,random_walk,ar1,mixed}]
                              [--seed SEED] [--output OUTPUT]
synthetic_generator.py: error: unrecognized arguments: --anomaly-rate 0.05
- python code/src/services/anomaly_detector.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/services/anomaly_detector.py", line 10, in <module>
    from src.models.dp_gmm import DPGMMModel, DPGMMConfig
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/__init__.py", line 5, in <module>
    from .dp_gmm import DPGMMConfig, DPGMMModel, ELBOHistory, ClusterAnomalyResult, main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/dp_gmm.py", line 125, in <module>
    import _winapi
ModuleNotFoundError: No module named '_winapi'
- python code/src/evaluation/simulation.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/simulation.py': [Errno 2] No such file or directory
- python code/src/evaluation/robustness.py --subset-size 50 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/robustness.py': [Errno 2] No such file or directory
