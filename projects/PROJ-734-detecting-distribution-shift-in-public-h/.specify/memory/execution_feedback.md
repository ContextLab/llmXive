# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/benchmark_mmd.py: synthetic/fake INPUT data not authorized by the spec — “…")         # Extend with synthetic data just for benchmarking if…”
- code/bocpd.py: synthetic/fake INPUT data not authorized by the spec — “…")         # Fallback to synthetic data for testing if real data…”
- code/bocpd.py: synthetic/fake INPUT data not authorized by the spec — “…logger.warning("Using synthetic data for BOCPD baseline as re…”
- code/download_data.py: synthetic/fake INPUT data not authorized by the spec — “…fallback to synthetic or mock data.  Constitution Principle…”
- code/synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic data generator for unit tests…”
- code/synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…tests only.  This module generates synthetic public health surveillan…”
- code/synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generate a synthetic ILI (Influenza-like Illn…”
- code/synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…ED ) -> str:     """     Generate synthetic data and save it to a CS…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 11 fabricated/simulated-result signal(s) — results are not real measurements: code/benchmark_mmd.py: synthetic/fake INPUT data not authorized by the spec — “…")         # Extend with synthetic data just for benchmarking if…”; code/bocpd.py: synthetic/fake INPUT data not authorized by the spec — “…")         # Fallback to synthetic data for testing if real data…”; code/bocpd.py: synthetic/fake INPUT data not authorized by the spec — “…logger.warning("Using synthetic data for BOCPD baseline as re…”; 2 command(s) failed: python code/download_data.py (rc=1); python code/main.py (rc=1); 2 declared deliverable(s) absent: data/raw/fluview_ili.csv; data/raw/ground_truth_events.csv

## Failing / missing run-book commands

- python code/download_data.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-734-detecting-distribution-shift-in-public-h/code/download_data.py", line 309, in main
    fetch_cdc_data(url, output_path, data_type)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-734-detecting-distribution-shift-in-public-h/code/download_data.py", line 99, in fetch_cdc_data
    logger.info(f"Attempting to fetch {data_type} from: {url}")
    ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'info'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-734-detecting-distribution-shift-in-public-h/code/download_data.py", line 342, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-734-detecting-distribution-shift-in-public-h/code/download_data.py", line 329, in main
    logger.error(f"Unexpected error processing {data_type}: {e}")
    ^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'error'
- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-734-detecting-distribution-shift-in-public-h/code/main.py", line 3, in <module>
    import yaml
ModuleNotFoundError: No module named 'yaml'

## Declared deliverables still missing

- data/raw/fluview_ili.csv
- data/raw/ground_truth_events.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Download / stream** this exact data URL directly (do NOT `pip install` it — it is a data file, not a package): `https://raw.githubusercontent.com/alireza-jafari/ILI-Influenza-Dataset/main/ILINet.csv`
- **Verified**: streaming a sample yielded **3994** real records with fields: REGION TYPE, REGION, YEAR, WEEK, % WEIGHTED ILI, %UNWEIGHTED ILI, AGE 0-4, AGE 25-49, AGE 25-64, AGE 5-24, AGE 50-64, AGE 65, ILITOTAL, NUM. OF PROVIDERS, TOTAL PATIENTS.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pandas as pd
url = 'https://raw.githubusercontent.com/alireza-jafari/ILI-Influenza-Dataset/main/ILINet.csv'
df = pd.read_csv(url)
# Expected columns: 'epiweek' (int), 'ili' (float), 'outbreak' (0/1)
if 'epiweek' in df.columns:
    df['week'] = df['epiweek'].apply(lambda x: f"{x//100}-W{x%100:02d}")
if 'ili' in df.columns:
    df['ili_percent'] = df['ili']
if 'outbreak' in df.columns:
    df['outbreak_flag'] = df['outbreak'].astype(bool)
RECORDS = len(df)
print(f"RECORDS={RECORDS}")
fields = [c for c in ['week','ili_percent','outbreak_flag'] if c in df.columns]
print('FIELDS=' + ','.join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw/fluview_ili.csv` is declared but was NOT written. Scripts referencing it:
    - `code/sensitivity.py` — NOT invoked by the run-book
    - `code/benchmark_mmd.py` — NOT invoked by the run-book
    - `code/download_data.py` — IS a run-book command
    - `code/exceptions.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/fluview_ili.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/ground_truth_events.csv` is declared but was NOT written. Scripts referencing it:
    - `code/report_generator.py` — NOT invoked by the run-book
    - `code/sensitivity.py` — NOT invoked by the run-book
    - `code/evaluate.py` — NOT invoked by the run-book
    - `code/download_data.py` — IS a run-book command
    - `code/exceptions.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/ground_truth_events.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
