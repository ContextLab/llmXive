# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/stats.py: synthetic/fake INPUT data not authorized by the spec — “…ion, we will construct a dummy contingency table if not available,…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 fabricated/simulated-result signal(s) — results are not real measurements: code/stats.py: synthetic/fake INPUT data not authorized by the spec — “…ion, we will construct a dummy contingency table if not available,…”; 1 command(s) failed: python code/main.py (rc=1); 18 declared deliverable(s) absent: data/processed/ablation_labels_train.json; data/processed/ablation_labels_validation.json; data/processed/ablation_train_set.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    2026-07-22 18:33:17,812 - llmXive.main - INFO - Starting FULL pipeline execution.
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-990-llmxive-follow-up-extending-agenticsts-a/code/main.py", line 230, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-990-llmxive-follow-up-extending-agenticsts-a/code/main.py", line 227, in main
    run_full_pipeline(config)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-990-llmxive-follow-up-extending-agenticsts-a/code/main.py", line 158, in run_full_pipeline
    validate_data_source()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-990-llmxive-follow-up-extending-agenticsts-a/code/parser.py", line 84, in validate_data_source
    raise FileNotFoundError(
FileNotFoundError: No trajectory files found in data/raw. Expected files with extensions: ['.json', '.jsonl', '.log']

## Declared deliverables still missing

- data/processed/ablation_labels_train.json
- data/processed/ablation_labels_validation.json
- data/processed/ablation_train_set.csv
- data/processed/analysis_config.json
- data/processed/baseline_comparison.csv
- data/processed/benchmark_log.json
- data/processed/divergence_report.json
- data/processed/metrics_with_moves.csv
- data/processed/proxy_validation_report.json
- data/processed/simulation_logs_dynamic.json
- data/processed/simulation_logs_random.json
- data/processed/simulation_logs_static.json
- data/processed/static_log_proxy.json
- data/processed/statistical_results.json
- data/processed/test_set.csv
- data/processed/token_reduction_verification.json
- data/processed/train_set.csv
- data/processed/validation_set.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/ablation_labels_train.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
    - `code/benchmark.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/main_optimized.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ablation_labels_train.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ablation_labels_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ablation_labels_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ablation_train_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
    - `code/benchmark.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ablation_train_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/analysis_config.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/generate_analysis_config.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_config.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/baseline_comparison.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/generate_statistical_report.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/generate_baseline_comparison.py` — NOT invoked by the run-book
    - `code/schema_validator.py` — NOT invoked by the run-book
    - `code/token_reduction_verifier.py` — NOT invoked by the run-book
    - `code/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_comparison.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/benchmark_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/optimization_report.py` — NOT invoked by the run-book
    - `code/benchmark.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/benchmark_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/divergence_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/schema_validator.py` — NOT invoked by the run-book
    - `code/stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/divergence_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics_with_moves.csv` is declared but was NOT written. Scripts referencing it:
    - `code/parser.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
    - `code/benchmark.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/main_optimized.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics_with_moves.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/proxy_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/classifier.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/schema_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/proxy_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/simulation_logs_dynamic.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
    - `code/benchmark.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/simulation_logs_dynamic.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/simulation_logs_random.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/simulation_logs_random.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/simulation_logs_static.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
    - `code/benchmark.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/simulation_logs_static.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/static_log_proxy.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/static_log_proxy.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/generate_statistical_report.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
    - `code/benchmark.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/generate_baseline_comparison.py` — NOT invoked by the run-book
    - `code/schema_validator.py` — NOT invoked by the run-book
    - `code/main_optimized.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/statistical_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
    - `code/benchmark.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/token_reduction_verification.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/schema_validator.py` — NOT invoked by the run-book
    - `code/token_reduction_verifier.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/token_reduction_verification.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/splitter.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
    - `code/benchmark.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/schema_validator.py` — NOT invoked by the run-book
    - `code/main_optimized.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/train_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
