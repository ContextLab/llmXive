# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…HuggingFace datasets or synthetic data generation. """ import o…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/ingest.py: synthetic/fake INPUT data not authorized by the spec — “…HuggingFace datasets or synthetic data generation. """ import o…”; 2 command(s) failed: python code/main.py (rc=1); python code/validate.py data/processed/aligned_events.csv contracts/aligned_event.schema.yaml (rc=1); 2 declared deliverable(s) absent: data/processed/aligned_events.csv; data/processed/analysis_subset.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    for NOAA_SWPC_FTP (FTP Port 21 reachable)
2026-08-26 08:18:22,576 - Pipeline - INFO - Verifying heartbeat for NOAA_SWPC_DST: https://www.swpc.noaa.gov/products/dst-index
2026-08-26 08:18:23,620 - Pipeline - WARNING - HEAD failed for NOAA_SWPC_DST with 404, trying GET...
2026-08-26 08:18:24,142 - Pipeline - INFO - Verifying heartbeat for NOAA_SWPC_KP: https://www.swpc.noaa.gov/products/kp-index
2026-08-26 08:18:24,687 - Pipeline - WARNING - HEAD failed for NOAA_SWPC_KP with 404, trying GET...
2026-08-26 08:18:25,204 - Pipeline - INFO - Verifying heartbeat for CDAWeb_LASCO: https://cdaweb.gsfc.nasa.gov/index.html/
2026-08-26 08:18:25,482 - Pipeline - INFO - Heartbeat OK for CDAWeb_LASCO (Status 200)
2026-08-26 08:18:25,483 - Pipeline - ERROR - Data source heartbeat verification failed for:
NOAA_SWPC_DST: HTTP Heartbeat failed for NOAA_SWPC_DST: Status 404
NOAA_SWPC_KP: HTTP Heartbeat failed for NOAA_SWPC_KP: Status 404
2026-08-26 08:18:25,483 - Pipeline - ERROR - Pipeline failed due to data source issues: Data source heartbeat verification failed for:
NOAA_SWPC_DST: HTTP Heartbeat failed for NOAA_SWPC_DST: Status 404
NOAA_SWPC_KP: HTTP Heartbeat failed for NOAA_SWPC_KP: Status 404
- python code/validate.py data/processed/aligned_events.csv contracts/aligned_event.schema.yaml -> rc=1
    2026-08-26 08:18:25,609 - INFO - Validating data/processed/aligned_events.csv against contracts/aligned_event.schema.yaml
2026-08-26 08:18:25,609 - ERROR - CSV file not found: data/processed/aligned_events.csv
Error: data/processed/aligned_events.csv not found. Run align.py first.

## Declared deliverables still missing

- data/processed/aligned_events.csv
- data/processed/analysis_subset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/aligned_events.csv` is declared but was NOT written. Scripts referencing it:
    - `code/log_data_quality.py` — NOT invoked by the run-book
    - `code/align.py` — NOT invoked by the run-book
    - `code/validate.py` — IS a run-book command
    - `code/write_aligned_output.py` — NOT invoked by the run-book
    - `code/filter_analysis_subset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/aligned_events.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/analysis_subset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/filter_analysis_subset.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_subset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/aligned_events.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/log_data_quality.py`, `code/align.py`, `code/write_aligned_output.py`, `code/filter_analysis_subset.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/aligned_events.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/log_data_quality.py`, `code/align.py`, `code/validate.py`, `code/write_aligned_output.py`, `code/filter_analysis_subset.py`.
