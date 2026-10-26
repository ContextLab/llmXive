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

2026-10-26 19:13:46,628 INFO __main__: Downloading Pantheon+ FITS from https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/main/Pantheon%2B_Data.fits
2026-10-26 19:13:46,679 ERROR __main__: Pantheon+ download failed: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/main/Pantheon%2B_Data.fits

- python code/download_pantheon.py --verify-only -> rc=1

2026-10-26 19:13:47,064 ERROR __main__: Pantheon+ download failed: File not found for verification: /home/runner/work/llmXive/llmXive/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/data/raw/pantheon_plus.fits

- python code/power_analysis.py -> rc=1

/home/runner/work/llmXive/llmXive/projects/PROJ-753-testing-the-isotropy-of-cosmic-expansion/code/power_analysis.py:23: UserWarning: A NumPy version >=1.22.4 and <2.3.0 is required for this version of SciPy (detected version 2.4.6)
  from scipy.spatial.transform import Rotation
2026-10-26 19:13:47,491 INFO __main__: Downloading Pantheon+ dataset from https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/main/Pantheon%2B_SH0ES.dat
2026-10-26 19:13:47,613 ERROR __main__: Power analysis failed: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/main/Pantheon%2B_SH0ES.dat

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
