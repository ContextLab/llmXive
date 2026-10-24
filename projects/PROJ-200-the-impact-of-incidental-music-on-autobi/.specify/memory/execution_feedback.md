# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…nimal demonstration that generates synthetic data,   fits a simple mo…”
- code/main.py: synthetic/fake INPUT data not authorized by the spec — “…g demo mode – generating synthetic data and model.")     # Ensur…”
- code/simulate_amt.py: synthetic/fake INPUT data not authorized by the spec — “…def main():     """     Generate a small synthetic AMT dataset required for…”
- code/simulate_amt.py: synthetic/fake INPUT data not authorized by the spec — “…ex=False)     log.info(f"Simulated AMT data written to {out_path}")…”
- code/simulate_demo.py: synthetic/fake INPUT data not authorized by the spec — “…demo pipeline for T003.  Generates a small synthetic validation dataset (10 u…”
- code/simulate_demo.py: synthetic/fake INPUT data not authorized by the spec — “…nthetic pipeline:      * Generate the raw synthetic cohort.     * Persist ``…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 fabricated/simulated-result signal(s) — results are not real measurements: code/main.py: synthetic/fake INPUT data not authorized by the spec — “…nimal demonstration that generates synthetic data,   fits a simple mo…”; code/main.py: synthetic/fake INPUT data not authorized by the spec — “…g demo mode – generating synthetic data and model.")     # Ensur…”; code/simulate_amt.py: synthetic/fake INPUT data not authorized by the spec — “…def main():     """     Generate a small synthetic AMT dataset required for…”; 1 command(s) failed: python code/main.py --full-run (rc=1); 5 declared deliverable(s) absent: data/final/permutation_results.csv; data/final/regression_summary.csv; data/final/sensitivity_analysis.csv

## Failing / missing run-book commands

- python code/main.py --full-run -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/main.py", line 31, in <module>
    from simulate_demo import main as run_thin_demo
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/simulate_demo.py", line 21, in <module>
    import pandas as pd
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/__init__.py", line 26, in <module>
    from pandas.compat import (
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/compat/__init__.py", line 27, in <module>
    from pandas.compat.pyarrow import (
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/pandas/compat/pyarrow.py", line 10, in <module>
    _palv = Version(Version(pa.__version__).base_version)
                            ^^^^^^^^^^^^^^
AttributeError: module 'pyarrow' has no attribute '__version__'


## Declared deliverables still missing

- data/final/permutation_results.csv
- data/final/regression_summary.csv
- data/final/sensitivity_analysis.csv
- data/processed/ingested_cohort.parquet
- data/processed/user_track_pairs.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/final/permutation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/generate_final_results.py` — NOT invoked by the run-book
    - `code/generate_permutation_results.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/security.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/permutation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/final/regression_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/05_model.py` — NOT invoked by the run-book
    - `code/08_visualize.py` — NOT invoked by the run-book
    - `code/generate_diagnostic_plots.py` — NOT invoked by the run-book
    - `code/generate_permutation_results.py` — NOT invoked by the run-book
    - `code/generate_regression_summary.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/modeling.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/regression_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/final/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/08_visualize.py` — NOT invoked by the run-book
    - `code/generate_final_results.py` — NOT invoked by the run-book
    - `code/generate_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/security.py` — NOT invoked by the run-book
    - `code/verify_artifacts.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ingested_cohort.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/02_preprocess.py` — NOT invoked by the run-book
    - `code/03_aggregate.py` — NOT invoked by the run-book
    - `code/aggregation.py` — NOT invoked by the run-book
    - `code/data/aggregate.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/generate_ingested_cohort.py` — NOT invoked by the run-book
    - `code/generate_user_track_pairs.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/ingested_cohort.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/user_track_pairs.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/03_aggregate.py` — NOT invoked by the run-book
    - `code/05_model.py` — NOT invoked by the run-book
    - `code/08_visualize.py` — NOT invoked by the run-book
    - `code/aggregation.py` — NOT invoked by the run-book
    - `code/generate_diagnostic_plots.py` — NOT invoked by the run-book
    - `code/generate_regression_summary.py` — NOT invoked by the run-book
    - `code/generate_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/generate_user_track_pairs.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/user_track_pairs.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
