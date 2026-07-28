# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…-> pd.DataFrame:     """Generates synthetic data with specified para…”
- code/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…"""Main function to generate and save synthetic data."""      n_samples…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…-> pd.DataFrame:     """Generates synthetic data with specified para…”; code/synthetic_generator.py: synthetic/fake INPUT data not authorized by the spec — “…"""Main function to generate and save synthetic data."""      n_samples…”; 5 run-book script(s) missing (plan/impl path mismatch): python code/data/loader.py --source "gss"  --url "<GSS_URL>"  --output data/raw/gss_2018.parquet; python code/data/loader.py --source "acs"  --url "<ACS_URL>"  --output data/raw/acs_income.parquet; python code/imputation/run_all.py  --input data/processed/synthetic_mar.parquet  --methods "cc,single,mice"  --mice-chains 4  --mice-iterations 1000  --burn-in 500  --output data/processed/imputation_results.json; 1 command(s) failed: python code/synthetic_generator.py --n-rows 50000 --mechanism MAR --output data/processed/synthetic_mar.parquet (rc=1); 4 declared deliverable(s) absent: data/processed/baseline_results.json; data/processed/synthetic_mar_v1.csv; data/processed/synthetic_mar_v1_meta.json

## Failing / missing run-book commands

- python -c "import pandas; import sklearn; import statsmodels; import miceforest; print('Environment OK')" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'pandas'
- python code/data/loader.py --source "gss"  --url "<GSS_URL>"  --output data/raw/gss_2018.parquet -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/data/loader.py': [Errno 2] No such file or directory
- python code/data/loader.py --source "acs"  --url "<ACS_URL>"  --output data/raw/acs_income.parquet -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/data/loader.py': [Errno 2] No such file or directory
- python code/synthetic_generator.py --n-rows 50000 --mechanism MAR --output data/processed/synthetic_mar.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/synthetic_generator.py", line 7, in <module>
    import pandas as pd
ModuleNotFoundError: No module named 'pandas'
- python code/imputation/run_all.py  --input data/processed/synthetic_mar.parquet  --methods "cc,single,mice"  --mice-chains 4  --mice-iterations 1000  --burn-in 500  --output data/processed/imputation_results.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/imputation/run_all.py': [Errno 2] No such file or directory
- python code/metrics/bias.py  --results data/processed/imputation_results.json  --true-variance 150.5  --sweep-param "m"  --sweep-values "5,10,20"  --output data/reports/bias_analysis.json -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/metrics/bias.py': [Errno 2] No such file or directory
- python code/main.py --generate-report --output reports/final_report.md -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-325-evaluating-the-impact-of-data-imputation/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/baseline_results.json
- data/processed/synthetic_mar_v1.csv
- data/processed/synthetic_mar_v1_meta.json
- data/raw/gss_2018_subset.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/baseline_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/synthetic_mar_v1.csv` is declared but was NOT written. Scripts referencing it:
    - `code/synthetic_generator.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/synthetic_mar_v1.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/synthetic_mar_v1_meta.json` is declared but was NOT written. Scripts referencing it:
    - `code/synthetic_generator.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/synthetic_mar_v1_meta.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/gss_2018_subset.csv` is declared but was NOT written. Scripts referencing it:
    - `code/variance_estimator.py` — NOT invoked by the run-book
    - `code/imputation_pipeline.py` — NOT invoked by the run-book
    - `code/data_ingestion.py` — NOT invoked by the run-book
    - `code/baseline_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/gss_2018_subset.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
