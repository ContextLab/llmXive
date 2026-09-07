# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/generate_mock_trajectories.py: self-declared fabricated metric — “…# Layer utility (mock value)             layer_utility =…”
- code/generate_mock_trajectories.py: synthetic/fake INPUT data not authorized by the spec — “…DE is not set to 'true'. Mock data generation is restricted…”
- code/generate_mock_trajectories.py: synthetic/fake INPUT data not authorized by the spec — “…active. Proceeding with mock data generation.")     return…”
- code/generate_mock_trajectories.py: synthetic/fake INPUT data not authorized by the spec — “…ectory to ensure     the mock data matches the expected fie…”
- code/generate_mock_trajectories.py: synthetic/fake INPUT data not authorized by the spec — “…all set of deterministic mock data     # We create 5 trajec…”
- code/generate_mock_trajectories.py: synthetic/fake INPUT data not authorized by the spec — “…{len(mock_trajectories)} mock trajectory records.")     logger.info(f"Out…”
- code/run_random_baseline.py: synthetic/fake INPUT data not authorized by the spec — “…unction if it can handle mock data.…”
- code/t003c_mock_data_guard.py: synthetic/fake INPUT data not authorized by the spec — “…"""     Execute the mock data guard logic.          Lo…”

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 21 fabricated/simulated-result signal(s) — results are not real measurements: code/generate_mock_trajectories.py: self-declared fabricated metric — “…# Layer utility (mock value)             layer_utility =…”; code/generate_mock_trajectories.py: synthetic/fake INPUT data not authorized by the spec — “…DE is not set to 'true'. Mock data generation is restricted…”; code/generate_mock_trajectories.py: synthetic/fake INPUT data not authorized by the spec — “…active. Proceeding with mock data generation.")     return…”; 1 command(s) failed: python code/main.py (rc=1); 25 declared deliverable(s) absent: data/processed/ablation_labels_holdout.json; data/processed/ablation_labels_train.json; data/processed/agg_stats.json

## Failing / missing run-book commands

- python code/main.py -> rc=1
    2026-09-07 00:14:32,962 - INFO - Starting FULL pipeline execution.
2026-09-07 00:14:32,962 - INFO - Running stage: code/t005c_fetch_manifest.py
2026-09-07 00:14:33,012 - INFO - Fetching manifest from: https://huggingface.co/datasets/agenticsts/trajectories/raw/main/manifest.json
2026-09-07 00:14:33,012 - INFO - Target path: data/raw/manifest.json
2026-09-07 00:14:33,090 - ERROR - HTTP Error 401 while fetching manifest: Unauthorized
2026-09-07 00:14:33,090 - CRITICAL - T005c failed: Manifest fetch failed (HTTP 401); pipeline cannot proceed.
2026-09-07 00:14:33,098 - ERROR - Stage code/t005c_fetch_manifest.py raised CalledProcessError: Command '['/home/runner/work/llmXive/llmXive/projects/PROJ-990-llmxive-follow-up-extending-agenticsts-a/code/.venv/bin/python', 'code/t005c_fetch_manifest.py']' returned non-zero exit status 1.
2026-09-07 00:14:33,098 - ERROR - Pipeline failed at stage: code/t005c_fetch_manifest.py

## Declared deliverables still missing

- data/processed/ablation_labels_holdout.json
- data/processed/ablation_labels_train.json
- data/processed/agg_stats.json
- data/processed/baseline_comparison.csv
- data/processed/config_state.json
- data/processed/divergence_report.json
- data/processed/entropy_metrics.csv
- data/processed/ground_truth_utility_holdout.csv
- data/processed/ground_truth_utility_train.csv
- data/processed/metrics_with_moves.csv
- data/processed/paired_status.json
- data/processed/pipeline_validation_report.json
- data/processed/power_analysis.json
- data/processed/proxy_validation_report.json
- data/processed/simulation_logs_dynamic.json
- data/processed/simulation_logs_random.json
- data/processed/simulation_logs_static.json
- data/processed/success_criteria_report.json
- data/processed/test_set.csv
- data/processed/token_budget_detailed.csv
- data/processed/token_consistency_report.json
- data/processed/token_savings_per_trajectory.csv
- data/processed/train_set.csv
- data/processed/validation_set.csv
- data/raw/manifest.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/ablation_labels_holdout.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ablation_labels_holdout.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ablation_labels_train.json` is declared but was NOT written. Scripts referencing it:
    - `code/classifier.py` — NOT invoked by the run-book
    - `code/t008d_ablation_failure_handler.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/check_sample_size.py` — NOT invoked by the run-book
    - `code/main_optimized.py` — NOT invoked by the run-book
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/ablation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ablation_labels_train.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/agg_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/generate_statistical_report.py` — NOT invoked by the run-book
    - `code/aggregate_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/agg_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/baseline_comparison.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/schema_validator.py` — NOT invoked by the run-book
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/token_consistency_checker.py` — NOT invoked by the run-book
    - `code/generate_baseline_comparison.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/generate_statistical_report.py` — NOT invoked by the run-book
    - `code/token_reduction_verifier.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/baseline_comparison.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/config_state.json` is declared but was NOT written. Scripts referencing it:
    - `code/splitter.py` — NOT invoked by the run-book
    - `code/t005a_no_data_warning.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/config_state.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/divergence_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/stats.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/divergence_checker.py` — NOT invoked by the run-book
    - `code/schema_validator.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/divergence_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/entropy_metrics.csv` is declared but was NOT written. Scripts referencing it:
    - `code/t006b_entropy_runner.py` — NOT invoked by the run-book
    - `code/entropy.py` — NOT invoked by the run-book
    - `code/pipeline_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/entropy_metrics.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ground_truth_utility_holdout.csv` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ground_truth_utility_holdout.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ground_truth_utility_train.csv` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ground_truth_utility_train.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metrics_with_moves.csv` is declared but was NOT written. Scripts referencing it:
    - `code/classifier.py` — NOT invoked by the run-book
    - `code/run_random_baseline.py` — NOT invoked by the run-book
    - `code/run_dynamic_simulation.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/splitter.py` — NOT invoked by the run-book
    - `code/main_optimized.py` — NOT invoked by the run-book
    - `code/entropy.py` — NOT invoked by the run-book
    - `code/proxy_extractor.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metrics_with_moves.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/paired_status.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/generate_statistical_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/paired_status.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pipeline_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/pipeline_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/power_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/generate_statistical_report.py` — NOT invoked by the run-book
    - `code/aggregate_stats.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/power_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/proxy_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/classifier.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/schema_validator.py` — NOT invoked by the run-book
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/proxy_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/proxy_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/simulation_logs_dynamic.json` is declared but was NOT written. Scripts referencing it:
    - `code/stats.py` — NOT invoked by the run-book
    - `code/run_dynamic_simulation.py` — NOT invoked by the run-book
    - `code/token_budget_logger.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/generate_baseline_comparison.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/simulation_logs_dynamic.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/simulation_logs_random.json` is declared but was NOT written. Scripts referencing it:
    - `code/run_random_baseline.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/generate_baseline_comparison.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
    - `code/engine_runner.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/simulation_logs_random.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/simulation_logs_static.json` is declared but was NOT written. Scripts referencing it:
    - `code/stats.py` — NOT invoked by the run-book
    - `code/baseline_static_runner.py` — NOT invoked by the run-book
    - `code/token_budget_logger.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/quickstart_runner.py` — NOT invoked by the run-book
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/generate_baseline_comparison.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/simulation_logs_static.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/success_criteria_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/generate_statistical_report.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/success_criteria_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/baseline_static_runner.py` — NOT invoked by the run-book
    - `code/run_random_baseline.py` — NOT invoked by the run-book
    - `code/run_dynamic_simulation.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/splitter.py` — NOT invoked by the run-book
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/simulator.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/token_budget_detailed.csv` is declared but was NOT written. Scripts referencing it:
    - `code/token_budget_logger.py` — NOT invoked by the run-book
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/simulator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/token_budget_detailed.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/token_consistency_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/token_consistency_checker.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/token_consistency_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/token_savings_per_trajectory.csv` is declared but was NOT written. Scripts referencing it:
    - `code/pipeline_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/token_savings_per_trajectory.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/splitter.py` — NOT invoked by the run-book
    - `code/main_optimized.py` — NOT invoked by the run-book
    - `code/schema_validator.py` — NOT invoked by the run-book
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/train_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/validation_set.csv` is declared but was NOT written. Scripts referencing it:
    - `code/classifier.py` — NOT invoked by the run-book
    - `code/run_quickstart_validation.py` — NOT invoked by the run-book
    - `code/splitter.py` — NOT invoked by the run-book
    - `code/proxy_extractor.py` — NOT invoked by the run-book
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/quickstart_validator.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/validation_set.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/manifest.json` is declared but was NOT written. Scripts referencing it:
    - `code/t005b_ingest_trajectories.py` — NOT invoked by the run-book
    - `code/t005c_fetch_manifest.py` — NOT invoked by the run-book
    - `code/pipeline_validator.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
  Make ONE of these WRITE `data/raw/manifest.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
