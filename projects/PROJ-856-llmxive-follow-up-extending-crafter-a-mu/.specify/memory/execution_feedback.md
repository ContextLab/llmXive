# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…---------------------- # Synthetic data generation (used when ``…”
- src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…tr) -> None:     """     Generate a deterministic synthetic dataset without external…”
- src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…ult=False,         help="Generate deterministic synthetic data without downloading…”
- src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…nly`` takes precedence – generate synthetic data.     if args.verify…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m src.analysis.retention_check  --log-dir data/logs/  --min-valid 28  --required-participants 32`
  - script usage: `retention_check.py [-h] --log-dir LOG_DIR [--min-valid MIN_VALID]`
  - argparse error: `retention_check.py: error: unrecognized arguments: --required-participants 32`
- run-book command: `python -m src.validation.run_validation  --log-dir data/logs/  --output-dir data/validation/`
  - script usage: `run_validation.py [-h] --log-dir LOG_DIR --ground-truth-dir`
  - argparse error: `run_validation.py: error: the following arguments are required: --ground-truth-dir`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…---------------------- # Synthetic data generation (used when ``…”; src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…tr) -> None:     """     Generate a deterministic synthetic dataset without external…”; src/curators/curate_failed_figures.py: synthetic/fake INPUT data not authorized by the spec — “…ult=False,         help="Generate deterministic synthetic data without downloading…”; 5 command(s) failed: python -m src.curators.curate_failed_figures  --download  --output-dir data/ (rc=1); python -m src.analysis.retention_check  --log-dir data/logs/  --min-valid 28  --required-participants 32 (rc=2); python -m src.validation.run_validation  --log-dir data/logs/  --output-dir data/validation/ (rc=2)

## Failing / missing run-book commands

- python -m src.curators.curate_failed_figures  --download  --output-dir data/ -> rc=1

verified source unavailable\n
- python -m src.analysis.retention_check  --log-dir data/logs/  --min-valid 28  --required-participants 32 -> rc=2

usage: retention_check.py [-h] --log-dir LOG_DIR [--min-valid MIN_VALID]
retention_check.py: error: unrecognized arguments: --required-participants 32

- python -m src.validation.run_validation  --log-dir data/logs/  --output-dir data/validation/ -> rc=2
.1%
64.4%
64.7%
64.9%
65.2%
65.5%
65.8%
66.1%
66.3%
66.6%
66.9%
67.2%
67.5%
67.7%
68.0%
68.3%
68.6%
68.9%
69.1%
69.4%
69.7%
70.0%
70.3%
70.5%
70.8%
71.1%
71.4%
71.7%
71.9%
72.2%
72.5%
72.8%
73.1%
73.3%
73.6%
73.9%
74.2%
74.4%
74.7%
75.0%
75.3%
75.6%
75.8%
76.1%
76.4%
76.7%
77.0%
77.2%
77.5%
77.8%
78.1%
78.4%
78.6%
78.9%
79.2%
79.5%
79.8%
80.0%
80.3%
80.6%
80.9%
81.2%
81.4%
81.7%
82.0%
82.3%
82.6%
82.8%
83.1%
83.4%
83.7%
84.0%
84.2%
84.5%
84.8%
85.1%
85.4%
85.6%
85.9%
86.2%
86.5%
86.8%
87.0%
87.3%
87.6%
87.9%
88.2%
88.4%
88.7%
89.0%
89.3%
89.6%
89.8%
90.1%
90.4%
90.7%
91.0%
91.2%
91.5%
91.8%
92.1%
92.4%
92.6%
92.9%
93.2%
93.5%
93.8%
94.0%
94.3%
94.6%
94.9%
95.2%
95.4%
95.7%
96.0%
96.3%
96.6%
96.8%
97.1%
97.4%
97.7%
98.0%
98.2%
98.5%
98.8%
99.1%
99.4%
99.6%
99.9%
100.0%
usage: run_validation.py [-h] --log-dir LOG_DIR --ground-truth-dir
                         GROUND_TRUTH_DIR [--prediction-dir PREDICTION_DIR]
                         [--ground-truth-image-dir GROUND_TRUTH_IMAGE_DIR]
                         [--prediction-image-dir PREDICTION_IMAGE_DIR]
                         --output-dir OUTPUT_DIR
run_validation.py: error: the following arguments are required: --ground-truth-dir

- python -m src.analysis.wilcoxon_analysis  --log-dir data/logs/  --validation-dir data/validation/  --output-dir outputs/ -> rc=1

2026-10-25 14:11:35,839 ERROR __main__: Interaction log missing required columns: {'figure_id', 'interface', 'participant_id'}

- python -m src.analysis.generate_report  --analysis-dir outputs/  --output-file outputs/report.md -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-856-llmxive-follow-up-extending-crafter-a-mu/bin/python: No module named src.analysis.generate_report

