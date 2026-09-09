# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/curation.py: synthetic/fake INPUT data not authorized by the spec — “…ning in validation mode (mock data). Skipping strict real-d…”
- code/models/training.py: synthetic/fake INPUT data not authorized by the spec — “…g Error: Cannot train on synthetic data. Real data source requir…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/data/curation.py: synthetic/fake INPUT data not authorized by the spec — “…ning in validation mode (mock data). Skipping strict real-d…”; code/models/training.py: synthetic/fake INPUT data not authorized by the spec — “…g Error: Cannot train on synthetic data. Real data source requir…”; 2 command(s) failed: python code/data/acquisition.py (rc=1); python code/main.py (rc=1); 3 declared deliverable(s) absent: data/curated/filtered.csv; data/raw/fetched_diffusion.csv; data/raw/source_metadata.json

## Failing / missing run-book commands

- python code/data/acquisition.py -> rc=1
    2026-09-09 06:25:03,374 - __main__ - INFO - Starting data acquisition with streaming...
2026-09-09 06:25:03,453 - __main__ - ERROR - Network error: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/materialsvirtuallab/materials-database/main/diffusion_data.csv
Data Fetch Failed: Network error - 404 Client Error: Not Found for url: https://raw.githubusercontent.com/materialsvirtuallab/materials-database/main/diffusion_data.csv
- python code/main.py -> rc=1
    06:25:06,553 - utils.resource_monitor - INFO - RAM usage at stage 'Pipeline_Start': 0.60 GB
2026-09-09 06:25:06,553 - __main__ - INFO - Phase: Data Acquisition
2026-09-09 06:25:06,553 - utils.resource_monitor - INFO - RAM usage at stage 'Acquisition_Start': 0.60 GB
2026-09-09 06:25:06,553 - data.acquisition - INFO - Starting data acquisition with streaming...
2026-09-09 06:25:06,579 - data.acquisition - ERROR - Network error: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/materialsvirtuallab/materials-database/main/diffusion_data.csv
2026-09-09 06:25:06,579 - __main__ - INFO - Pipeline Execution Time: 0.03 seconds
2026-09-09 06:25:06,579 - utils.resource_monitor - INFO - RAM usage at stage 'Pipeline_End': 0.60 GB
2026-09-09 06:25:06,579 - utils.resource_monitor - INFO - Resource usage report saved to /home/runner/work/llmXive/llmXive/projects/PROJ-415-predicting-the-impact-of-alloying-on-the/reports/resource_usage.json
2026-09-09 06:25:06,579 - __main__ - INFO - Resource usage report saved.
Data Fetch Failed: Network error - 404 Client Error: Not Found for url: https://raw.githubusercontent.com/materialsvirtuallab/materials-database/main/diffusion_data.csv

## Declared deliverables still missing

- data/curated/filtered.csv
- data/raw/fetched_diffusion.csv
- data/raw/source_metadata.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/curated/filtered.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/ingestion.py` — NOT invoked by the run-book
    - `code/data/curation.py` — NOT invoked by the run-book
    - `code/models/training.py` — NOT invoked by the run-book
    - `code/models/benchmark_gridsearch.py` — NOT invoked by the run-book
    - `code/models/inference.py` — NOT invoked by the run-book
    - `code/validation/stats.py` — NOT invoked by the run-book
    - `code/validation/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/curated/filtered.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/fetched_diffusion.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/acquisition.py` — IS a run-book command
    - `code/data/curation.py` — NOT invoked by the run-book
    - `code/validation/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/fetched_diffusion.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/source_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/acquisition.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/source_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
