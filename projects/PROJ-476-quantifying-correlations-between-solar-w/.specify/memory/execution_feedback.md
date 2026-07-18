# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/neff.py: synthetic/fake INPUT data not authorized by the spec — “…:     # Simple test with synthetic data to verify logic     test…”
- code/data/fetch.py: synthetic/fake INPUT data not authorized by the spec — “…alling back to synthetic/mock data.          Args:…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/neff.py: synthetic/fake INPUT data not authorized by the spec — “…:     # Simple test with synthetic data to verify logic     test…”; code/data/fetch.py: synthetic/fake INPUT data not authorized by the spec — “…alling back to synthetic/mock data.          Args:…”; 4 command(s) failed: python code/main.py fetch --start 1998-01-01 --end 2020-12-31 (rc=1); python code/main.py compute-thresholds (rc=1); python code/main.py analyze --data data/processed/synced.csv --lags 0,1,2,3,6 (rc=1); 3 declared deliverable(s) absent: data/processed/synced.csv; data/raw/ace_raw.csv; data/raw/noaa_raw.csv

## Failing / missing run-book commands

- python code/main.py fetch --start 1998-01-01 --end 2020-12-31 -> rc=1
    2026-07-18 11:26:12,822 - solar_wind - INFO - Pipeline started at 2026-07-18T11:26:12.822635
2026-07-18 11:26:12,822 - solar_wind - INFO - Configuration: Train=1998-2017, Test=2018-2020
2026-07-18 11:26:12,822 - solar_wind - INFO - --- Phase 1: Data Acquisition & Synchronization ---
2026-07-18 11:26:12,822 - solar_wind - INFO - Fetching ACE and NOAA data...
2026-07-18 11:26:12,822 - solar_wind - INFO - Fetching ACE data from ftp://spdf.gsfc.nasa.gov/pub/data/ace/ for range 1998 to 2020
2026-07-18 11:26:12,822 - solar_wind - ERROR - Failed to fetch data: strptime() argument 1 must be str, not int
- python code/main.py compute-thresholds -> rc=1
    2026-07-18 11:26:14,289 - solar_wind - INFO - Pipeline started at 2026-07-18T11:26:14.289467
2026-07-18 11:26:14,289 - solar_wind - INFO - Configuration: Train=1998-2017, Test=2018-2020
2026-07-18 11:26:14,289 - solar_wind - INFO - --- Phase 1: Data Acquisition & Synchronization ---
2026-07-18 11:26:14,289 - solar_wind - INFO - Fetching ACE and NOAA data...
2026-07-18 11:26:14,289 - solar_wind - INFO - Fetching ACE data from ftp://spdf.gsfc.nasa.gov/pub/data/ace/ for range 1998 to 2020
2026-07-18 11:26:14,289 - solar_wind - ERROR - Failed to fetch data: strptime() argument 1 must be str, not int
- python code/main.py analyze --data data/processed/synced.csv --lags 0,1,2,3,6 -> rc=1
    2026-07-18 11:26:15,755 - solar_wind - INFO - Pipeline started at 2026-07-18T11:26:15.755415
2026-07-18 11:26:15,755 - solar_wind - INFO - Configuration: Train=1998-2017, Test=2018-2020
2026-07-18 11:26:15,755 - solar_wind - INFO - --- Phase 1: Data Acquisition & Synchronization ---
2026-07-18 11:26:15,755 - solar_wind - INFO - Fetching ACE and NOAA data...
2026-07-18 11:26:15,755 - solar_wind - INFO - Fetching ACE data from ftp://spdf.gsfc.nasa.gov/pub/data/ace/ for range 1998 to 2020
2026-07-18 11:26:15,755 - solar_wind - ERROR - Failed to fetch data: strptime() argument 1 must be str, not int
- python code/main.py validate --data data/processed/synced.csv --test-start 2018-01-01 --test-end 2020-12-31 -> rc=1
    2026-07-18 11:26:17,213 - solar_wind - INFO - Pipeline started at 2026-07-18T11:26:17.213046
2026-07-18 11:26:17,213 - solar_wind - INFO - Configuration: Train=1998-2017, Test=2018-2020
2026-07-18 11:26:17,213 - solar_wind - INFO - --- Phase 1: Data Acquisition & Synchronization ---
2026-07-18 11:26:17,213 - solar_wind - INFO - Fetching ACE and NOAA data...
2026-07-18 11:26:17,213 - solar_wind - INFO - Fetching ACE data from ftp://spdf.gsfc.nasa.gov/pub/data/ace/ for range 1998 to 2020
2026-07-18 11:26:17,213 - solar_wind - ERROR - Failed to fetch data: strptime() argument 1 must be str, not int

## Declared deliverables still missing

- data/processed/synced.csv
- data/raw/ace_raw.csv
- data/raw/noaa_raw.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/synced.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/viz/report.py` — NOT invoked by the run-book
    - `code/viz/plots.py` — NOT invoked by the run-book
    - `code/viz/report_generation.py` — NOT invoked by the run-book
    - `code/data/align.py` — NOT invoked by the run-book
    - `code/analysis/thresholds.py` — NOT invoked by the run-book
    - `code/analysis/correlation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/synced.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ace_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data/validate.py` — NOT invoked by the run-book
    - `code/data/align.py` — NOT invoked by the run-book
    - `code/data/fetch.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/ace_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/noaa_raw.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/data/validate.py` — NOT invoked by the run-book
    - `code/data/align.py` — NOT invoked by the run-book
    - `code/data/fetch.py` — NOT invoked by the run-book
    - `code/tests/test_pipeline.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/noaa_raw.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
