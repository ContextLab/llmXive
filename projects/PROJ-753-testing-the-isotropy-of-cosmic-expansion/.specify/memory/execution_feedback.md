# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis.py: self-declared fabricated metric — “…nd: {residuals_path}")      # Placeholder results – real values will be comput…”
- code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…p="Run the pipeline on a synthetic dataset (placeholder)",     )…”
- code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…of dipole to inject into synthetic data",     )     args = parse…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis.py: self-declared fabricated metric — “…nd: {residuals_path}")      # Placeholder results – real values will be comput…”; code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…p="Run the pipeline on a synthetic dataset (placeholder)",     )…”; code/analysis.py: synthetic/fake INPUT data not authorized by the spec — “…of dipole to inject into synthetic data",     )     args = parse…”; 5 command(s) failed: python code/download_pantheon.py   # writes data/raw/pantheon_plus.dat and records SHA‑256 (rc=1); python code/download_pantheon.py --verify-only (rc=1); python code/power_analysis.py (rc=1); 2 declared deliverable(s) absent: data/processed/residuals.csv; data/raw/metadata.json

## Failing / missing run-book commands

- python code/download_pantheon.py   # writes data/raw/pantheon_plus.dat and records SHA‑256 -> rc=1

2026-10-25 19:07:52,415 INFO __main__: Downloading Pantheon+ dataset from https://zenodo.org/record/7968445/files/Pantheon%2B_Data.fits?download=1
2026-10-25 19:07:52,978 WARNING __main__: Primary download URL failed (404 Client Error: NOT FOUND for url: https://zenodo.org/records/7968445/files/Pantheon+_Data.fits). Attempting fallback URL.
2026-10-25 19:07:52,978 INFO __main__: Downloading Pantheon+ dataset from https://zenodo.org/records/7968445/files/Pantheon%2B_Data.fits?download=1
2026-10-25 19:07:53,400 ERROR __main__: Pantheon+ download failed: 404 Client Error: NOT FOUND for url: https://zenodo.org/records/7968445/files/Pantheon%2B_Data.fits?download=1

- python code/download_pantheon.py --verify-only -> rc=1

2026-10-25 19:07:53,698 ERROR __main__: Pantheon+ download failed: File not found for verification: /home/runner/work/llmXive/llmXive/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/data/raw/pantheon_plus.fits

- python code/power_analysis.py -> rc=1

2026-10-25 19:07:54,180 INFO __main__: Downloading Pantheon+ dataset from https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/main/Pantheon%2B_SH0ES.dat
2026-10-25 19:07:54,293 ERROR __main__: Power analysis failed: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/main/Pantheon%2B_SH0ES.dat

- python code/analysis.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/code/analysis.py", line 58, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/code/analysis.py", line 39, in main
    raise FileNotFoundError(f"Residuals file not found: {residuals_path}")
FileNotFoundError: Residuals file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/data/processed/residuals.csv

- python code/analysis.py --synthetic --inject-dipole 0.04 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/code/analysis.py", line 58, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/code/analysis.py", line 39, in main
    raise FileNotFoundError(f"Residuals file not found: {residuals_path}")
FileNotFoundError: Residuals file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/data/processed/residuals.csv


## Declared deliverables still missing

- data/processed/residuals.csv
- data/raw/metadata.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **1701** real records with fields: sn_name, survey_id, redshift_hd, redshift_hd_err, redshift_cmb, redshift_cmb_err, redshift_helio, redshift_helio_err, apparent_mag_b, apparent_mag_b_err, stretch_x1, stretch_x1_err, color_c, color_c_err, host_log_mass, host_log_mass_err, fit_probability, distance_modulus, distance_modulus_err.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets

ds = datasets.load_dataset("juliensimon/pantheon-plus-sne-ia", split="train")
records = len(ds)
print(f"RECORDS={records}")
print("FIELDS=" + ",".join(ds.column_names))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/residuals.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — IS a run-book command
    - `code/ingest.py` — NOT invoked by the run-book
    - `code/power_analysis.py` — IS a run-book command
    - `code/spherical_harmonics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/residuals.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/download_pantheon.py` — IS a run-book command
    - `code/power_analysis.py` — IS a run-book command
    - `code/utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
