# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generate_master_dataset.py: synthetic/fake INPUT data not authorized by the spec — “…ure anomaly.     It also generates synthetic control windows for the…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_master_dataset.py: synthetic/fake INPUT data not authorized by the spec — “…ure anomaly.     It also generates synthetic control windows for the…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/report.py; 3 command(s) failed: python code/download.py (rc=1); python code/preprocess.py (rc=1); python code/analysis.py (rc=1); 1 declared deliverable(s) absent: data/processed/master_dataset.csv

## Failing / missing run-book commands

- python code/download.py -> rc=1
    2026-07-21 00:07:16 - __main__ - INFO - Starting download pipeline (T012: Checksumming & Immutability)

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/download.py", line 252, in <module>
    exit(main())
         ^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/download.py", line 218, in main
    if not verify_deviations():
           ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/download.py", line 34, in verify_deviations
    if not dev_path.exists():
           ^^^^^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'exists'
- python code/preprocess.py -> rc=1
    in load_raw_earthquake_data
    raise FileNotFoundError(f"Raw earthquake data not found at {raw_path}")
FileNotFoundError: Raw earthquake data not found at data/raw/usgs_test_subset.json

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py", line 323, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py", line 308, in main
    eq_df, press_df, report = preprocess_data()
                              ^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py", line 280, in preprocess_data
    eq_df = load_raw_earthquake_data(raw_earthquake_path)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/preprocess.py", line 29, in load_raw_earthquake_data
    raise FileNotFoundError(f"Raw earthquake data not found at {raw_path}")
FileNotFoundError: Raw earthquake data not found at data/raw/usgs_test_subset.json
- python code/analysis.py -> rc=1
    2026-07-21 00:07:17 - __main__ - INFO - Starting analysis pipeline.

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 320, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 313, in main
    results = run_analysis()
              ^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 267, in run_analysis
    df = load_master_dataset()
         ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/analysis.py", line 19, in load_master_dataset
    raise FileNotFoundError(f"Master dataset not found at {path}")
FileNotFoundError: Master dataset not found at data/processed/master_dataset.csv
- python code/report.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-252-exploring-the-correlation-between-atmosp/code/report.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/master_dataset.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `obspy` to the project's `requirements.txt` and `pip install obspy`.
- **Verified**: this loads **1725** real records with fields: earthquake_id, origin_time, magnitude, depth_km, latitude, longitude.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import json
from obspy.clients.fdsn import Client
client = Client("USGS")
# Example query: all magnitude >=5 events in 2022
cat = client.get_events(starttime="2022-01-01", endtime="2022-12-31", minmagnitude=5)
records = len(cat)
print(f"RECORDS={records}")
# Map native attributes to required field names
fields = ["earthquake_id","origin_time","magnitude","depth_km","latitude","longitude"]
print("FIELDS=" + ",".join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/master_dataset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_master_dataset.py` — NOT invoked by the run-book
    - `code/generate_robustness_report.py` — NOT invoked by the run-book
    - `code/analysis.py` — IS a run-book command
    - `code/generate_statistical_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/master_dataset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/master_dataset.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/generate_master_dataset.py`, `code/analysis.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/master_dataset.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/generate_master_dataset.py`, `code/analysis.py`.

### `data/raw/usgs_test_subset.json`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/preprocess.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/raw/usgs_test_subset.json`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/preprocess.py`.
