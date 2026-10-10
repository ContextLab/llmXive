# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/01_download_preprocess.py: self-declared fabricated metric — “…',         'k_score': 3.5,  # Mock value         'd_prime': 2.1,  # Mo…”
- code/01_download_preprocess.py: self-declared fabricated metric — “…ue         'd_prime': 2.1,  # Mock value         'accuracy': 0.85,…”
- code/01_download_preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…nted in this mock. Using mock data structure.")         ret…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/01_download_preprocess.py: self-declared fabricated metric — “…',         'k_score': 3.5,  # Mock value         'd_prime': 2.1,  # Mo…”; code/01_download_preprocess.py: self-declared fabricated metric — “…ue         'd_prime': 2.1,  # Mock value         'accuracy': 0.85,…”; code/01_download_preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…nted in this mock. Using mock data structure.")         ret…”; 3 command(s) failed: python code/01_download_preprocess.py --dataset ds000248 --output data/processed (rc=1); python code/02_extract_metrics.py --input data/processed/epochs.h5 --output data/metrics (rc=1); python code/03_correlation_analysis.py --power data/metrics/alpha_power.csv --plv data/metrics/plv.csv --output data/results (rc=1); 2 declared deliverable(s) absent: data/metrics/plv.csv; data/results/threshold_results.json

## Failing / missing run-book commands

- python code/01_download_preprocess.py --dataset ds000248 --output data/processed -> rc=1

2026-10-10T02:30:15 [INFO] root: Logging initialized
2026-10-10T02:30:15 [INFO] __main__: Loaded configuration from code/config.yaml
2026-10-10T02:30:15 [INFO] __main__: Step 1: Downloading ds000248
2026-10-10T02:30:15 [INFO] __main__: Step 2: Validating dataset structure
2026-10-10T02:30:15 [ERROR] __main__: Dataset directory does not exist: data/raw
2026-10-10T02:30:15 [ERROR] __main__: Dataset validation failed. Exiting.

- python code/02_extract_metrics.py --input data/processed/epochs.h5 --output data/metrics -> rc=1
ject S0048
2026-10-10T02:30:15 [INFO] __main__: Processing subject: S0049
2026-10-10T02:30:15 [WARNING] __main__: Skipping subject S0049: No epoch files found for subject S0049
2026-10-10T02:30:15 [INFO] __main__: Processing subject: S0050
2026-10-10T02:30:15 [WARNING] __main__: Skipping subject S0050: No epoch files found for subject S0050
2026-10-10T02:30:15 [INFO] __main__: Processing subject: S0051
2026-10-10T02:30:15 [WARNING] __main__: Skipping subject S0051: No epoch files found for subject S0051
2026-10-10T02:30:15 [INFO] __main__: Processing subject: S0052
2026-10-10T02:30:15 [WARNING] __main__: Skipping subject S0052: No epoch files found for subject S0052
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-335-investigating-the-relationship-between-a/code/02_extract_metrics.py", line 270, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-335-investigating-the-relationship-between-a/code/02_extract_metrics.py", line 264, in main
    alpha_collection.to_csv(base_dir / 'data' / 'metrics' / 'alpha_power.csv')
    ^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'AlphaPowerCollection' object has no attribute 'to_csv'

- python code/03_correlation_analysis.py --power data/metrics/alpha_power.csv --plv data/metrics/plv.csv --output data/results -> rc=1

2026-10-10T02:30:16 [INFO] root: Logging initialized
2026-10-10T02:30:16 [INFO] __main__: Starting correlation analysis with split-half reliability
2026-10-10T02:30:16 [ERROR] __main__: Required metric file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-335-investigating-the-relationship-between-a/data/metrics/alpha_power.csv


## Declared deliverables still missing

- data/metrics/plv.csv
- data/results/threshold_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/metrics/plv.csv` is declared but was NOT written. Scripts referencing it:
    - `code/02_extract_metrics.py` — IS a run-book command
    - `code/02_store_plv.py` — NOT invoked by the run-book
    - `code/03_correlation_analysis.py` — IS a run-book command
    - `code/05_generate_report.py` — NOT invoked by the run-book
    - `code/models/__init__.py` — NOT invoked by the run-book
    - `code/models/plv_metric.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/metrics/plv.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/threshold_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_threshold_analysis.py` — NOT invoked by the run-book
    - `code/05_generate_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/threshold_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
