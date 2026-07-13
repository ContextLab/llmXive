# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…nput to output (assuming synthetic input is already 'corrected' f…”
- code/tools/verify_batching.py: synthetic/fake INPUT data not authorized by the spec — “…original implementation generated synthetic NIfTI‑like data, which v…”
- code/tools/verify_batching.py: synthetic/fake INPUT data not authorized by the spec — “…d without     generating synthetic NIfTI data.  The function simply ca…”
- code/viz/network.py: synthetic/fake INPUT data not authorized by the spec — “…d if available,     # or generate a synthetic one for demonstration.…”
- code/viz/network.py: synthetic/fake INPUT data not authorized by the spec — “…g synthetic.")         # Generate a synthetic connectivity matrix (400…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 5 fabricated/simulated-result signal(s) — results are not real measurements: code/data/preprocess.py: synthetic/fake INPUT data not authorized by the spec — “…nput to output (assuming synthetic input is already 'corrected' f…”; code/tools/verify_batching.py: synthetic/fake INPUT data not authorized by the spec — “…original implementation generated synthetic NIfTI‑like data, which v…”; code/tools/verify_batching.py: synthetic/fake INPUT data not authorized by the spec — “…d without     generating synthetic NIfTI data.  The function simply ca…”; 4 command(s) failed: python code/main.py --step download_preprocess --subjects 50 (rc=2); python code/main.py --step extract_metrics (rc=2); python code/main.py --step analyze (rc=2); 3 declared deliverable(s) absent: data/analysis/factor_scores.csv; data/analysis/full_metrics.csv; data/analysis/pca_loadings.csv

## Failing / missing run-book commands

- python code/main.py --step download_preprocess --subjects 50 -> rc=2
    usage: main.py [-h]
               {download_preprocess,extract_metrics,analyze,viz_report} ...
main.py: error: unrecognized arguments: --step
- python code/main.py --step extract_metrics -> rc=2
    usage: main.py [-h]
               {download_preprocess,extract_metrics,analyze,viz_report} ...
main.py: error: unrecognized arguments: --step
- python code/main.py --step analyze -> rc=2
    usage: main.py [-h]
               {download_preprocess,extract_metrics,analyze,viz_report} ...
main.py: error: unrecognized arguments: --step
- python code/main.py --step viz_report -> rc=2
    usage: main.py [-h]
               {download_preprocess,extract_metrics,analyze,viz_report} ...
main.py: error: unrecognized arguments: --step

## Declared deliverables still missing

- data/analysis/factor_scores.csv
- data/analysis/full_metrics.csv
- data/analysis/pca_loadings.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real, installable source was discovered AND verified by actually loading data from it:

- **Install**: add `nilearn` to the project's `requirements.txt` and `pip install nilearn`.
- **Verified**: this loads **30** real records with fields: Unnamed: 0, Subject, Rest.Scan, MeanFD, NumFD_greater_than_0.20, rootMeanSquareFD, FDquartile.top1.4thFD., PercentFD_greater_than_0.20, MeanDVARS, MeanFD_Jenkinson, site, sibling_id, data_set, age, sex, handedness, full_2_iq, full_4_iq, viq, piq, iq_measure, tdc, adhd, adhd_inattentive, adhd_combined, adhd_subthreshold, diagnosis_using_cdis, notes, sess_1_anat_2, oppositional, cog_inatt, hyperac, anxious_shy, perfectionism, social_problems, psychosomatic, conn_adhd, restless_impulsive, emot_lability, conn_gi_tot, dsm_iv_inatt, dsm_iv_h_i, dsm_iv_tot, study, sess_1_rest_1, sess_1_rest_1_eyes, sess_1_rest_2, sess_1_rest_2_eyes, sess_1_rest_3, sess_1_rest_3_eyes, sess_1_rest_4, sess_1_rest_4_eyes, sess_1_rest_5, sess_1_rest_5_eyes, sess_1_rest_6, sess_1_rest_6_eyes, sess_1_anat_1, sess_1_which_anat, sess_2_rest_1, sess_2_rest_1_eyes, sess_2_rest_2, sess_2_rest_2_eyes, sess_2_anat_1, defacing_ok, defacing_notes.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import os
from nilearn import datasets

bunch = datasets.fetch_adhd(
    data_dir=os.path.join(os.getenv("HOME"), "nilearn_data"),
    verbose=0,
)

records = len(bunch.phenotypic)
print(f"RECORDS={records}")

fields = list(bunch.phenotypic.columns)
print("FIELDS=" + ",".join(fields))
```

Write the loader to use this package/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/analysis/factor_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlations.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/factor_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/full_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/viz/network.py` — NOT invoked by the run-book
    - `code/viz/scatter.py` — NOT invoked by the run-book
    - `code/analysis/correlations.py` — NOT invoked by the run-book
    - `code/analysis/correlations_main_runner.py` — NOT invoked by the run-book
    - `code/tools/verify_batching.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/full_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/analysis/pca_loadings.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlations.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/analysis/pca_loadings.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
