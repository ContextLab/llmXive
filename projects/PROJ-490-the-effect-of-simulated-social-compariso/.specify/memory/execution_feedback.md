# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/interpretation.py: synthetic/fake INPUT data not authorized by the spec — “…'synthetic' for simulated data.      Returns:         s…”
- code/analysis/interpretation.py: synthetic/fake INPUT data not authorized by the spec — “…ysis "             "used synthetic data generated with known gro…”
- code/analysis/report_generator.py: synthetic/fake INPUT data not authorized by the spec — “…e parameter recovery (if synthetic data)     if sensitivity_resu…”
- code/analysis/sensitivity.py: synthetic/fake INPUT data not authorized by the spec — “…ound truth parameters if synthetic data was used."""     config…”
- code/analysis/sensitivity.py: synthetic/fake INPUT data not authorized by the spec — “…un parameter recovery if synthetic data is available."""     con…”
- code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…d.DataFrame:     """     Generates synthetic data with ground truth p…”
- code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…logger.info(f"Generating synthetic dataset with N={n_samples} and s…”
- code/data/download.py: synthetic/fake INPUT data not authorized by the spec — “…})          logger.info("Synthetic dataset generated successfully."…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 16 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/interpretation.py: synthetic/fake INPUT data not authorized by the spec — “…'synthetic' for simulated data.      Returns:         s…”; code/analysis/interpretation.py: synthetic/fake INPUT data not authorized by the spec — “…ysis "             "used synthetic data generated with known gro…”; code/analysis/report_generator.py: synthetic/fake INPUT data not authorized by the spec — “…e parameter recovery (if synthetic data)     if sensitivity_resu…”; 4 run-book script(s) missing (plan/impl path mismatch): python code/main.py --action download; python code/main.py --action preprocess; python code/main.py --action analyze; 5 declared deliverable(s) absent: data/processed/final_report.json; data/processed/imputed_data.csv; data/processed/pre_imputation_validation.json

## Failing / missing run-book commands

- python code/main.py --action download -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-490-the-effect-of-simulated-social-compariso/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-490-the-effect-of-simulated-social-compariso/code/main.py': [Errno 2] No such file or directory
- python code/main.py --action preprocess -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-490-the-effect-of-simulated-social-compariso/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-490-the-effect-of-simulated-social-compariso/code/main.py': [Errno 2] No such file or directory
- python code/main.py --action analyze -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-490-the-effect-of-simulated-social-compariso/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-490-the-effect-of-simulated-social-compariso/code/main.py': [Errno 2] No such file or directory
- python code/main.py --action validate -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-490-the-effect-of-simulated-social-compariso/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-490-the-effect-of-simulated-social-compariso/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/final_report.json
- data/processed/imputed_data.csv
- data/processed/pre_imputation_validation.json
- data/processed/regression_coefficients.csv
- data/raw/synthetic_seed.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/final_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/imputed_data.csv` is declared but was NOT written. Scripts referencing it:
    - `code/data/validate_imputed.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/regression.py` — NOT invoked by the run-book
    - `code/analysis/bootstrap.py` — NOT invoked by the run-book
    - `code/analysis/collinearity_handler.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/imputed_data.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pre_imputation_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/validate_raw.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/pre_imputation_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/regression_coefficients.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/report_generator.py` — NOT invoked by the run-book
    - `code/analysis/sensitivity.py` — NOT invoked by the run-book
    - `code/analysis/export_results.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/regression_coefficients.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/synthetic_seed.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/seed_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/synthetic_seed.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
