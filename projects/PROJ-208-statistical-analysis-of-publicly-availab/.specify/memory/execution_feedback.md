# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/analysis/results.py: synthetic/fake INPUT data not authorized by the spec — “…summary.json"          # Dummy data for demonstration if run…”
- code/data/validators_hf.py: synthetic/fake INPUT data not authorized by the spec — “…vents silent fallback to synthetic data, satisfying the executio…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 fabricated/simulated-result signal(s) — results are not real measurements: code/analysis/results.py: synthetic/fake INPUT data not authorized by the spec — “…summary.json"          # Dummy data for demonstration if run…”; code/data/validators_hf.py: synthetic/fake INPUT data not authorized by the spec — “…vents silent fallback to synthetic data, satisfying the executio…”; 1 run-book script(s) missing (plan/impl path mismatch): python code/main.py; 8 declared deliverable(s) absent: data/processed/cleaned_issues.csv; data/processed/distribution_metrics.json; data/processed/outlier_report.json

## Failing / missing run-book commands

- python code/main.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-208-statistical-analysis-of-publicly-availab/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-208-statistical-analysis-of-publicly-availab/code/main.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/cleaned_issues.csv
- data/processed/distribution_metrics.json
- data/processed/outlier_report.json
- data/processed/repo_metadata.json
- data/processed/sensitivity_report.json
- data/processed/sensitivity_sweep.json
- data/raw/github_issues_raw_api.parquet
- data/raw/github_issues_raw_hf.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/cleaned_issues.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/cross_validation.py` — NOT invoked by the run-book
    - `code/analysis/distribution_fitting.py` — NOT invoked by the run-book
    - `code/analysis/hypothesis_testing.py` — NOT invoked by the run-book
    - `code/analysis/mixed_effects_model.py` — NOT invoked by the run-book
    - `code/analysis/outlier_detection.py` — NOT invoked by the run-book
    - `code/analysis/save_distribution_outputs.py` — NOT invoked by the run-book
    - `code/collect/save_cleaned_data.py` — NOT invoked by the run-book
    - `code/diagnostics/collinearity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_issues.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/distribution_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/distribution_fitting.py` — NOT invoked by the run-book
    - `code/analysis/save_distribution_outputs.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/distribution_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/outlier_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/outlier_detection.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/outlier_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/repo_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/collect/enrich_metadata.py` — NOT invoked by the run-book
    - `code/collect/preprocess.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/repo_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_sweep.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_report_generator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_sweep.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/github_issues_raw_api.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/collect/enrich_metadata.py` — NOT invoked by the run-book
    - `code/collect/fetch_issues.py` — NOT invoked by the run-book
    - `code/collect/preprocess.py` — NOT invoked by the run-book
    - `code/data/loader_api.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/github_issues_raw_api.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/github_issues_raw_hf.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/collect/enrich_metadata.py` — NOT invoked by the run-book
    - `code/collect/preprocess.py` — NOT invoked by the run-book
    - `code/data/loader_hf.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/github_issues_raw_hf.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
