# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…_DATA=True): Loads local mock data.     - Final Mode (USE_M…”
- code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…"Prototype Mode: Loading mock data from local files.")…”
- code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…# We will attempt to generate a minimal synthetic structure for the pipeli…”
- code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…logger.warning("Mock data files missing. Generatin…”
- code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…sing. Generating minimal synthetic data for prototype validation…”
- code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…"""Generates minimal mock data for prototype validation…”
- code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…"""     # Create a small mock MSD dataset     mock_msd = pd.DataFr…”
- code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…# Create a small mock AMT dataset     mock_amt = pd.DataFr…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 9 fabricated/simulated-result signal(s) — results are not real measurements: code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…_DATA=True): Loads local mock data.     - Final Mode (USE_M…”; code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…"Prototype Mode: Loading mock data from local files.")…”; code/data_ingestion.py: synthetic/fake INPUT data not authorized by the spec — “…# We will attempt to generate a minimal synthetic structure for the pipeli…”; 4 run-book script(s) missing (plan/impl path mismatch): python code/02_preprocess.py; python code/04_exposure.py; python code/06_sensitivity.py; 4 command(s) failed: python code/01_download_data.py (rc=1); python code/03_aggregate.py (rc=1); python code/05_model.py (rc=1); 5 declared deliverable(s) absent: data/final/bootstrap_results.csv; data/final/regression_summary.csv; data/final/sensitivity_analysis.csv

## Failing / missing run-book commands

- python code/01_download_data.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/01_download_data.py", line 16, in <module>
    from data_ingestion import download_datasets
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/data_ingestion.py", line 16, in <module>
    from datasets import load_dataset
ModuleNotFoundError: No module named 'datasets'
- python code/02_preprocess.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/02_preprocess.py': [Errno 2] No such file or directory
- python code/03_aggregate.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/03_aggregate.py", line 33, in <module>
    from utils import setup_logging, get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/utils.py", line 12, in <module>
    from .config import get_project_root
ImportError: attempted relative import with no known parent package
- python code/04_exposure.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/04_exposure.py': [Errno 2] No such file or directory
- python code/05_model.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/05_model.py", line 17, in <module>
    def fit_mixed_model(df: pd.DataFrame) -> smf.MixedLMResults:
                                             ^^^^^^^^^^^^^^^^^^
AttributeError: module 'statsmodels.formula.api' has no attribute 'MixedLMResults'
- python code/06_sensitivity.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/06_sensitivity.py': [Errno 2] No such file or directory
- python code/07_selection_correction.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/07_selection_correction.py': [Errno 2] No such file or directory
- python code/08_visualize.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/08_visualize.py", line 27, in <module>
    from utils import setup_logging, get_logger
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-200-the-impact-of-incidental-music-on-autobi/code/utils.py", line 12, in <module>
    from .config import get_project_root
ImportError: attempted relative import with no known parent package

## Declared deliverables still missing

- data/final/bootstrap_results.csv
- data/final/regression_summary.csv
- data/final/sensitivity_analysis.csv
- data/processed/ingested_cohort.parquet
- data/processed/user_track_pairs.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/final/bootstrap_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/verify_artifacts.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
    - `code/05_model.py` — IS a run-book command
  Make ONE of these WRITE `data/final/bootstrap_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/final/regression_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/verify_artifacts.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/generate_regression_summary.py` — NOT invoked by the run-book
    - `code/generate_diagnostic_plots.py` — NOT invoked by the run-book
    - `code/security.py` — NOT invoked by the run-book
    - `code/08_visualize.py` — IS a run-book command
    - `code/generate_permutation_results.py` — NOT invoked by the run-book
    - `code/05_model.py` — IS a run-book command
  Make ONE of these WRITE `data/final/regression_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/final/sensitivity_analysis.csv` is declared but was NOT written. Scripts referencing it:
    - `code/verify_artifacts.py` — NOT invoked by the run-book
    - `code/generate_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/security.py` — NOT invoked by the run-book
    - `code/08_visualize.py` — IS a run-book command
    - `code/generate_final_results.py` — NOT invoked by the run-book
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/final/sensitivity_analysis.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ingested_cohort.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/verify_artifacts.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/generate_ingested_cohort.py` — NOT invoked by the run-book
    - `code/aggregation.py` — NOT invoked by the run-book
    - `code/generate_user_track_pairs.py` — NOT invoked by the run-book
    - `code/03_aggregate.py` — IS a run-book command
    - `code/modeling.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ingested_cohort.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/user_track_pairs.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/verify_artifacts.py` — NOT invoked by the run-book
    - `code/generate_sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/generate_regression_summary.py` — NOT invoked by the run-book
    - `code/generate_diagnostic_plots.py` — NOT invoked by the run-book
    - `code/security.py` — NOT invoked by the run-book
    - `code/08_visualize.py` — IS a run-book command
    - `code/aggregation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/user_track_pairs.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
