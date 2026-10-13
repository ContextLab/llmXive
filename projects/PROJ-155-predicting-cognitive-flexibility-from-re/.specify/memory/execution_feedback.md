# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/data/preprocess.py: self-declared fabricated metric — “…'Total_Scan_Time'])         # Placeholder values:         writer.writerow([su…”
- code/utils/noise_filter.py: synthetic/fake INPUT data not authorized by the spec — “…help="Run unit tests on synthetic data")     args = parser.pars…”
- code/utils/noise_filter.py: synthetic/fake INPUT data not authorized by the spec — “…if args.test:         # Generate synthetic test data         np.ran…”
- code/utils/noise_filter.py: synthetic/fake INPUT data not authorized by the spec — “…execute verification on synthetic data.")…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 fabricated/simulated-result signal(s) — results are not real measurements: code/data/preprocess.py: self-declared fabricated metric — “…'Total_Scan_Time'])         # Placeholder values:         writer.writerow([su…”; code/utils/noise_filter.py: synthetic/fake INPUT data not authorized by the spec — “…help="Run unit tests on synthetic data")     args = parser.pars…”; code/utils/noise_filter.py: synthetic/fake INPUT data not authorized by the spec — “…if args.test:         # Generate synthetic test data         np.ran…”; 3 command(s) failed: python code/main.py --stage download_preprocess (rc=1); python code/main.py --stage features (rc=1); python code/main.py --stage analysis (rc=1); 4 declared deliverable(s) absent: data/processed/exclusion_log.csv; data/processed/final_results.csv; data/processed/metrics.csv

## Failing / missing run-book commands

- python code/main.py --stage download_preprocess -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-155-predicting-cognitive-flexibility-from-re/code/main.py", line 15, in <module>
    from code.data.download import download_adhd_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-155-predicting-cognitive-flexibility-from-re/code/data/__init__.py", line 8, in <module>
    from code.data.paths import (
ImportError: cannot import name 'get_project_root' from 'code.data.paths' (/home/runner/work/llmXive/llmXive/projects/PROJ-155-predicting-cognitive-flexibility-from-re/code/data/paths.py)

- python code/main.py --stage features -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-155-predicting-cognitive-flexibility-from-re/code/main.py", line 15, in <module>
    from code.data.download import download_adhd_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-155-predicting-cognitive-flexibility-from-re/code/data/__init__.py", line 8, in <module>
    from code.data.paths import (
ImportError: cannot import name 'get_project_root' from 'code.data.paths' (/home/runner/work/llmXive/llmXive/projects/PROJ-155-predicting-cognitive-flexibility-from-re/code/data/paths.py)

- python code/main.py --stage analysis -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-155-predicting-cognitive-flexibility-from-re/code/main.py", line 15, in <module>
    from code.data.download import download_adhd_dataset
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-155-predicting-cognitive-flexibility-from-re/code/data/__init__.py", line 8, in <module>
    from code.data.paths import (
ImportError: cannot import name 'get_project_root' from 'code.data.paths' (/home/runner/work/llmXive/llmXive/projects/PROJ-155-predicting-cognitive-flexibility-from-re/code/data/paths.py)


## Declared deliverables still missing

- data/processed/exclusion_log.csv
- data/processed/final_results.csv
- data/processed/metrics.csv
- data/results/regression_summary.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/exclusion_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/success_rate_calculator.py` — NOT invoked by the run-book
    - `code/data/behavioral_validator.py` — NOT invoked by the run-book
    - `code/data/merge.py` — NOT invoked by the run-book
    - `code/utils/exclusion_stats.py` — NOT invoked by the run-book
    - `code/utils/exclusion_validator.py` — NOT invoked by the run-book
    - `code/utils/success_rate.py` — NOT invoked by the run-book
    - `code/utils/validate_exclusions.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/final_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/final_results_generator.py` — NOT invoked by the run-book
    - `code/analysis/permutation.py` — NOT invoked by the run-book
    - `code/analysis/success_rate_calculator.py` — NOT invoked by the run-book
    - `code/data/validation.py` — NOT invoked by the run-book
    - `code/utils/validation_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/final_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/fdr_correction.py` — NOT invoked by the run-book
    - `code/analysis/final_results_generator.py` — NOT invoked by the run-book
    - `code/analysis/permutation.py` — NOT invoked by the run-book
    - `code/analysis/regression.py` — NOT invoked by the run-book
    - `code/analysis/regression_summary_generator.py` — NOT invoked by the run-book
    - `code/analysis/success_rate_calculator.py` — NOT invoked by the run-book
    - `code/features/aggregation.py` — NOT invoked by the run-book
    - `code/features/batch_processor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/regression_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/final_results_generator.py` — NOT invoked by the run-book
    - `code/analysis/regression.py` — NOT invoked by the run-book
    - `code/analysis/regression_summary_generator.py` — NOT invoked by the run-book
    - `code/analysis/success_rate_calculator.py` — NOT invoked by the run-book
    - `code/utils/exclusion_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/regression_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
