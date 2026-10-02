# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…y try/except fallback to synthetic data. It checks for local fil…”
- code/data_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…tch this and fallback to synthetic data.         # The task requ…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/data_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…y try/except fallback to synthetic data. It checks for local fil…”; code/data_fetcher.py: synthetic/fake INPUT data not authorized by the spec — “…tch this and fallback to synthetic data.         # The task requ…”; 1 command(s) failed: python code/main.py (rc=1); 7 declared deliverable(s) absent: data/processed/cleaned_data.csv; data/processed/correlation_results.csv; data/processed/lasso_diagnostics.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-077-investigating-the-correlation-between-gu/code/main.py", line 8, in <module>
    from data_ingestion import run_ingestion_pipeline
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-077-investigating-the-correlation-between-gu/code/data_ingestion.py", line 3, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python -c "import pandas as pd; df = pd.read_csv('data/processed/cleaned_data.csv'); print(df.shape); print(df.isnull().sum())" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'pandas'

## Declared deliverables still missing

- data/processed/cleaned_data.csv
- data/processed/correlation_results.csv
- data/processed/lasso_diagnostics.json
- data/processed/lasso_results.csv
- data/processed/regression_diagnostics.json
- data/processed/regression_results.csv
- data/processed/vif_results.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/diversity.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
    - `code/save_cleaned_data.py` — NOT invoked by the run-book
    - `code/residual_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/save_correlation_results.py` — NOT invoked by the run-book
    - `code/validate_sc001.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/lasso_diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `code/residual_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/lasso_diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/lasso_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/save_lasso_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/lasso_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_diagnostics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression_diagnostics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/validate_sc002.py` — NOT invoked by the run-book
    - `code/save_regression_results.py` — NOT invoked by the run-book
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/vif_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/vif_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
