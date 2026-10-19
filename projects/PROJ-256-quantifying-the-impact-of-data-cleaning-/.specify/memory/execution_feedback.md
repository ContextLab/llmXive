# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/sensitivity.py: self-declared fabricated metric — “…lder         inc_rate = 0.1 # Placeholder                  results["fpr"].append({"k": k, "fpr"…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/sensitivity.py: self-declared fabricated metric — “…lder         inc_rate = 0.1 # Placeholder                  results["fpr"].append({"k": k, "fpr"…”; 3 command(s) failed: python -m src.data_loader download_all (rc=1); python -m src.main run_all (rc=1); python -m pytest -m contract (rc=2); 4 declared deliverable(s) absent: data/processed/baseline_metrics.json; data/processed/cleaned_metrics.json; data/processed/comparison_report.json

## Failing / missing run-book commands

- python -m src.data_loader download_all -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-256-quantifying-the-impact-of-data-cleaning-/bin/python: Error while finding module specification for 'src.data_loader' (ModuleNotFoundError: No module named 'src')

- python -m src.main run_all -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-256-quantifying-the-impact-of-data-cleaning-/bin/python: Error while finding module specification for 'src.main' (ModuleNotFoundError: No module named 'src')

- python -m pytest -m contract -> rc=2
ests/test_outlier_threshold_sweep.py
ERROR tests/test_t013_baseline_output.py
ERROR tests/test_t013_record_baseline_metrics.py
ERROR tests/test_t023_cleaned_metrics.py
ERROR tests/test_t023_reanalyze_cleaned_variants.py
ERROR tests/test_t030_dataset_size_sensitivity.py
ERROR tests/test_t032_null_fpr.py
ERROR tests/test_t032_permutation_null_fpr.py
ERROR tests/test_t033_outlier_threshold_sweep.py
ERROR tests/test_t040_comparison_report.py
ERROR tests/test_t040_create_comparison_report.py
ERROR tests/test_t041_final_report.py
ERROR tests/unit/test_acquisition.py
ERROR tests/unit/test_comparison_report.py
ERROR tests/unit/test_data_loader.py
ERROR tests/unit/test_reporting_t027.py
ERROR tests/unit/test_t023_reanalyze.py
ERROR tests/unit/test_t030_dataset_size_sensitivity.py
ERROR tests/unit/test_t030_size_binning.py
ERROR tests/unit/test_t032_permutation_null.py
ERROR tests/unit/test_t033_threshold_sweep.py
ERROR tests/unit/test_t037_ci_width_reporting.py
ERROR tests/unit/test_t039_exclusion.py
ERROR tests/unit/test_t040.py
!!!!!!!!!!!!!!!!!!! Interrupted: 34 errors during collection !!!!!!!!!!!!!!!!!!!
================ 106 deselected, 1 warning, 34 errors in 2.00s =================



## Declared deliverables still missing

- data/processed/baseline_metrics.json
- data/processed/cleaned_metrics.json
- data/processed/comparison_report.json
- data/processed/null_fpr_metrics.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/baseline_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — NOT invoked by the run-book
    - `code/reporting.py` — NOT invoked by the run-book
    - `code/scripts/generate_migration_plan.py` — NOT invoked by the run-book
    - `code/scripts/quickstart_fix.py` — NOT invoked by the run-book
    - `code/sensitivity.py` — NOT invoked by the run-book
    - `code/validate_dataset_bins.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `scripts/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/cleaned_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/reporting.py` — NOT invoked by the run-book
    - `code/sensitivity.py` — NOT invoked by the run-book
    - `code/validation.py` — NOT invoked by the run-book
    - `scripts/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/cleaned_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/comparison_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/reporting.py` — NOT invoked by the run-book
    - `code/scripts/generate_migration_plan.py` — NOT invoked by the run-book
    - `code/scripts/quickstart_fix.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/comparison_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/null_fpr_metrics.json` is declared but was NOT written. Scripts referencing it:
    - `code/reporting.py` — NOT invoked by the run-book
    - `code/sensitivity.py` — NOT invoked by the run-book
    - `scripts/run_quickstart_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/null_fpr_metrics.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
## Platform-owned paths written inside the project

A script in this project created `.github/`, `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
