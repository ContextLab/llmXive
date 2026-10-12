# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generate_synthetic_test_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Test Data Generator for Unit Tests…”
- code/generate_synthetic_test_data.py: synthetic/fake INPUT data not authorized by the spec — “…Tests Only.  This script generates synthetic pupil dilation and cogni…”
- code/generate_synthetic_test_data.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates a synthetic dataset mimicking the st…”
- code/generate_synthetic_test_data.py: synthetic/fake INPUT data not authorized by the spec — “…er(         description="Generate synthetic test data. MUST be run w…”
- code/generate_synthetic_test_data.py: synthetic/fake INPUT data not authorized by the spec — “…help="Directory to write synthetic data files."     )     parser…”
- code/generate_synthetic_test_data.py: synthetic/fake INPUT data not authorized by the spec — “…print(f"Generating synthetic data for {args.num_subjects}…”
- code/generate_synthetic_test_data.py: synthetic/fake INPUT data not authorized by the spec — “…False)     print(f"Saved synthetic data to: {output_file}")…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python -m pytest code/tests/ -v --test-mode`
  - argparse error: `__main__.py: error: unrecognized arguments: --test-mode`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 7 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_synthetic_test_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Test Data Generator for Unit Tests…”; code/generate_synthetic_test_data.py: synthetic/fake INPUT data not authorized by the spec — “…Tests Only.  This script generates synthetic pupil dilation and cogni…”; code/generate_synthetic_test_data.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates a synthetic dataset mimicking the st…”; 3 command(s) failed: python code/verify_data_availability.py (rc=1); python code/main.py --config code/config.yaml (rc=1); python -m pytest code/tests/ -v --test-mode (rc=4); 1 declared deliverable(s) absent: data/processed/features.csv

## Failing / missing run-book commands

- python code/verify_data_availability.py -> rc=1
2026-10-12 10:23:44,333 - INFO - Starting data availability verification with plan: /home/runner/work/llmXive/llmXive/projects/PROJ-174-investigating-the-relationship-between-p/plan.md
2026-10-12 10:23:44,333 - ERROR - Verification failed with unexpected error: plan.md not found at /home/runner/work/llmXive/llmXive/projects/PROJ-174-investigating-the-relationship-between-p/plan.md


- python code/main.py --config code/config.yaml -> rc=1

WARNING:root:pyedflib not available. EDF files will not be supported.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-174-investigating-the-relationship-between-p/code/main.py", line 18, in <module>
    from preprocessing.load_data import run_loading_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-174-investigating-the-relationship-between-p/code/preprocessing/__init__.py", line 5, in <module>
    from .load_data import load_raw_data, standardize_columns, process_dataset, main, LoadResult
ImportError: cannot import name 'load_raw_data' from 'preprocessing.load_data' (/home/runner/work/llmXive/llmXive/projects/PROJ-174-investigating-the-relationship-between-p/code/preprocessing/load_data.py)

- python -m pytest code/tests/ -v --test-mode -> rc=4

ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
__main__.py: error: unrecognized arguments: --test-mode
  inifile: /home/runner/work/llmXive/llmXive/projects/PROJ-174-investigating-the-relationship-between-p/code/pyproject.toml
  rootdir: /home/runner/work/llmXive/llmXive/projects/PROJ-174-investigating-the-relationship-between-p/code



## Declared deliverables still missing

- data/processed/features.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/features.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlations.py` — NOT invoked by the run-book
    - `code/analysis/lme_fit.py` — NOT invoked by the run-book
    - `code/analysis/lme_model.py` — NOT invoked by the run-book
    - `code/analysis/lrt_test.py` — NOT invoked by the run-book
    - `code/analysis/metrics.py` — NOT invoked by the run-book
    - `code/analysis/trial_validation.py` — NOT invoked by the run-book
    - `code/analysis/vif_check.py` — NOT invoked by the run-book
    - `code/classification/classifier.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/features.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
