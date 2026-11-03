# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/scripts/run_regression_summary.py: self-declared fabricated metric — “…p in participants:         # Mock value for demonstration         sta…”
- code/scripts/profile_all_stages.py: synthetic/fake INPUT data not authorized by the spec — “…..")          # Generate mock data for profiling (real data…”
- code/scripts/profile_permutation.py: synthetic/fake INPUT data not authorized by the spec — “…"Generate representative mock data for profiling."""     rn…”
- code/scripts/run_regression_summary.py: synthetic/fake INPUT data not authorized by the spec — “…bject_id}/     """     # Mock data for demonstration purpos…”
- code/scripts/save_analysis_results.py: synthetic/fake INPUT data not authorized by the spec — “…np.ndarray]:     """     Generate synthetic data for testing purpose…”
- code/scripts/save_analysis_results.py: synthetic/fake INPUT data not authorized by the spec — “…Loads real data (or generates synthetic for testing if real data…”
- code/scripts/save_analysis_results.py: synthetic/fake INPUT data not authorized by the spec — “…# For now, we'll use synthetic data to demonstrate the pipel…”
- code/scripts/save_analysis_results.py: synthetic/fake INPUT data not authorized by the spec — “…al data not found. Using synthetic data for demonstration.")…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 fabricated/simulated-result signal(s) — results are not real measurements: code/scripts/run_regression_summary.py: self-declared fabricated metric — “…p in participants:         # Mock value for demonstration         sta…”; code/scripts/profile_all_stages.py: synthetic/fake INPUT data not authorized by the spec — “…..")          # Generate mock data for profiling (real data…”; code/scripts/profile_permutation.py: synthetic/fake INPUT data not authorized by the spec — “…"Generate representative mock data for profiling."""     rn…”; 3 command(s) failed: python code/main.py --validate-only (rc=1); python code/main.py --window-length 30 --permutations 10000 (rc=1); python code/main.py --sweep-windows (rc=1); 5 declared deliverable(s) absent: data/checksums.json; data/interim/included_subjects.csv; data/interim/permutation_results.csv

## Failing / missing run-book commands

- python code/main.py --validate-only -> rc=1
Starting Brain Dynamics and Creativity Pipeline...
CRITICAL ERROR: Behavioral JSON file not found in raw data.

2026-11-03 13:07:37,509 INFO root: Pipeline execution started.
2026-11-03 13:07:37,509 ERROR root: CRITICAL ERROR: Behavioral JSON file not found in raw data.

- python code/main.py --window-length 30 --permutations 10000 -> rc=1
Starting Brain Dynamics and Creativity Pipeline...
CRITICAL ERROR: Behavioral JSON file not found in raw data.

2026-11-03 13:07:37,781 INFO root: Pipeline execution started.
2026-11-03 13:07:37,781 ERROR root: CRITICAL ERROR: Behavioral JSON file not found in raw data.

- python code/main.py --sweep-windows -> rc=1
Starting Brain Dynamics and Creativity Pipeline...
CRITICAL ERROR: Behavioral JSON file not found in raw data.

2026-11-03 13:07:38,051 INFO root: Pipeline execution started.
2026-11-03 13:07:38,051 ERROR root: CRITICAL ERROR: Behavioral JSON file not found in raw data.


## Declared deliverables still missing

- data/checksums.json
- data/interim/included_subjects.csv
- data/interim/permutation_results.csv
- data/interim/sensitivity_summary.csv
- data/raw/manifest.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Download / stream** this exact data URL directly (do NOT `pip install` it — it is a data file, not a package): `https://raw.githubusercontent.com/OpenNeuroDatasets/ds000224/master/participants.tsv`
- **Verified**: streaming a sample yielded **10** real records with fields: participant_id, gender, age, education_degree, education_years.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pandas as pd, urllib.request, io
url = 'https://raw.githubusercontent.com/OpenNeuroDatasets/ds000224/master/participants.tsv'
with urllib.request.urlopen(url) as resp:
    data = resp.read().decode('utf-8')
df = pd.read_csv(io.StringIO(data), sep='\t')
print(f'RECORDS={len(df)}')
mapping = {
    'participant_id': 'participant_id',
    'age': 'age',
    'sex': 'sex',
    'education': 'education_level',
    'education_level': 'education_level',
    'creative_achievement_score': 'creative_achievement_score'
}
fields = [mapping[col] for col in df.columns if col in mapping]
print('FIELDS=' + ','.join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/checksums.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/loader.py` — NOT invoked by the run-book
    - `code/data/run_fetch.py` — NOT invoked by the run-book
    - `code/tests/unit/test_loader_fetch.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/checksums.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/included_subjects.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/loader.py` — NOT invoked by the run-book
    - `code/tests/unit/test_filter_subjects.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/included_subjects.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/permutation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/saving.py` — NOT invoked by the run-book
    - `code/scripts/profile_all_stages.py` — NOT invoked by the run-book
    - `code/scripts/save_analysis_results.py` — NOT invoked by the run-book
    - `code/scripts/save_permutation_and_sensitivity.py` — NOT invoked by the run-book
    - `code/scripts/save_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/permutation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/interim/sensitivity_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/saving.py` — NOT invoked by the run-book
    - `code/scripts/profile_all_stages.py` — NOT invoked by the run-book
    - `code/scripts/save_analysis_results.py` — NOT invoked by the run-book
    - `code/scripts/save_permutation_and_sensitivity.py` — NOT invoked by the run-book
    - `code/scripts/save_results.py` — NOT invoked by the run-book
    - `code/scripts/verify_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/sensitivity_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/loader.py` — NOT invoked by the run-book
    - `code/data/run_fetch.py` — NOT invoked by the run-book
    - `code/scripts/save_analysis_results.py` — NOT invoked by the run-book
    - `code/scripts/update_readme.py` — NOT invoked by the run-book
    - `code/tests/unit/test_filter_subjects.py` — NOT invoked by the run-book
    - `code/tests/unit/test_loader_fetch.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
