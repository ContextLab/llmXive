# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/02_preprocessing_grace.py: self-declared fabricated metric — “…nts DEGREE_1_COEFFS = {     # Placeholder values for the specific degree-1 co…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/02_preprocessing_grace.py: self-declared fabricated metric — “…nts DEGREE_1_COEFFS = {     # Placeholder values for the specific degree-1 co…”; 3 run-book script(s) missing (plan/impl path mismatch): python code/04_visualization.py; python code/05_sensitivity_report.py; python code/verify_completeness.py --threshold 0.90; 3 command(s) failed: python code/01_data_ingestion.py (rc=1); python code/02_preprocessing.py (rc=1); python code/03_correlation_analysis.py (rc=1); 2 declared deliverable(s) absent: data/processed/correlation_results.csv; data/processed/merged_monthly.csv

## Failing / missing run-book commands

- python code/01_data_ingestion.py -> rc=1
    2026-08-24 08:56:21,985 - INFO - === Data Ingestion Pipeline Start ===
2026-08-24 08:56:21,985 - INFO - Starting GRACE-FO data ingestion...
2026-08-24 08:56:21,986 - INFO - Fetching GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc from https://gracefo.jpl.nasa.gov/msl/files/RL06/mascons/CSR/GR60/GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc
2026-08-24 08:56:22,417 - ERROR - Failed to fetch GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc: 404 Client Error: Not Found for url: https://gracefo.jpl.nasa.gov/msl/files/RL06/mascons/CSR/GR60/GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc
2026-08-24 08:56:22,417 - CRITICAL - GRACE-FO ingestion failed: Real data fetch failed for GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc: 404 Client Error: Not Found for url: https://gracefo.jpl.nasa.gov/msl/files/RL06/mascons/CSR/GR60/GR60_JPLRL06_MASCON_CSM_v2.0_202301.nc
- python code/02_preprocessing.py -> rc=1
    2026-08-24 08:56:23,246 - INFO - Starting preprocessing and merge pipeline
2026-08-24 08:56:23,246 - ERROR - Failed to load raw data: No GRACE-FO CSV files found in /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/data/raw/grace-fo
- python code/03_correlation_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/code/03_correlation_analysis.py", line 24, in <module>
    from statsmodels.sandbox.regression.gmm import NeweyWest
ImportError: cannot import name 'NeweyWest' from 'statsmodels.sandbox.regression.gmm' (/home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/code/.venv/lib/python3.11/site-packages/statsmodels/sandbox/regression/gmm.py)
- python code/04_visualization.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/code/04_visualization.py': [Errno 2] No such file or directory
- python code/05_sensitivity_report.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/code/05_sensitivity_report.py': [Errno 2] No such file or directory
- python code/verify_completeness.py --threshold 0.90 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-267-exploring-the-relationship-between-atmos/code/verify_completeness.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/correlation_results.csv
- data/processed/merged_monthly.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_correlation_analysis.py` — IS a run-book command
    - `code/05_control_validation.py` — NOT invoked by the run-book
    - `code/06_control_validation.py` — NOT invoked by the run-book
    - `code/05_bootstrap_correction.py` — NOT invoked by the run-book
    - `code/03_correlation.py` — NOT invoked by the run-book
    - `code/04_bootstrap_correction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/merged_monthly.csv` is declared but was NOT written. Scripts referencing it:
    - `code/03_merge_output.py` — NOT invoked by the run-book
    - `code/07_visualization_timeseries.py` — NOT invoked by the run-book
    - `code/03_correlation_analysis.py` — IS a run-book command
    - `code/05_control_validation.py` — NOT invoked by the run-book
    - `code/06_control_validation.py` — NOT invoked by the run-book
    - `code/02_preprocessing.py` — IS a run-book command
    - `code/02_preprocessing_merge.py` — NOT invoked by the run-book
    - `code/05_bootstrap_correction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/merged_monthly.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
