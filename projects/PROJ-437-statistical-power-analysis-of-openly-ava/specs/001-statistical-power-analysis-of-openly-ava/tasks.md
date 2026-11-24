# Tasks: Statistical Power Analysis of Openly Available fMRI Datasets

**Input**: Design documents from `/specs/001-statistical-power-analysis/` (spec.md, plan.md, research.md, data-model.md, contracts/)  
**Revision**: Re‑plan after verifier rejection of T016, T017, T044a, T049 and task‑format repair (duplicate/ambiguous identities). Verified completed work is preserved below as checked; only the rejected requirements are reopened, under fresh unique task IDs to eliminate the prior duplicate‑identity failure.

## Verified completed work (preserved)

- [ ] V01 Project scaffolding, `requirements.txt`, seed manager (`code/utils/seed_manager.py`), memory monitor, `SimulationConfig`/`ReplicationResult` models, timer, execution-order validator (prior T001a–T007, T038, T083).
- [ ] V02 Real-data ingestion with fail‑loudly policy: `code/download/openneuro_fetcher.py` (stream‑first, `verify_real_source()`, no synthetic fallback), `data_validator.py`, `corruption_handler.py`, `streaming_chunker.py`, `data_integrity_hash.py`, `sampling_strategy.py`, `resource_guard.py` (prior T008, T009, T058, T062, T067, T071, T078, T079, T081). <!-- FAILED-IN-EXECUTION: code/download/openneuro_fetcher.py exit=1 -->
- [ ] V03 Preprocessing: `code/preprocess/roi_extractor.py` and `temporal_smoothing.py` (CPU‑tractable ROI + temporal smoothing; kernels 4 mm / 8 mm spatial), with `pipeline_config_hash.py` and `docs/preprocessing_justification.md` (prior T012, T013, T076, T077a/b, T068a/b).
- [ ] V04 Noise estimation and known‑truth signal injection: `code/simulation/noise_estimator.py` (`data/derived/noise_parameters.json`), synthetic‑data generation with real‑noise parameters and ground‑truth Cohen's d ∈ {0.0, 0.2, 0.5, 0.8, 1.0} (prior T014, T015).
- [ ] V05 Data‑leakage guard `code/utils/data_leakage_guard.py` and its unit test (prior T066, T070).
- [ ] V06 Power‑curve orchestration: `power_curve_generator.py` with clamping/insufficient‑data guardrails, `bootstrap_aggregator.py`, logistic regression with VIF check and BH‑FDR, alpha sweep, `multi_paradigm_runner.py`, `paradigm_loader.py` (prior T022–T026b, T029, T041, T052, T061, T072).
- [ ] V07 Sensitivity analysis: `temporal_sensitivity_orchestrator.py`, `effect_size_extractor.py` with seed logging, `sensitivity_metrics.json`, `sensitivity_report.md`, configurable threshold (prior T031–T034, T060, T074).
- [ ] V08 Orchestration and docs: `code/main.py` entry point, CLI docs, README data‑integrity sections, `audit_data_sources.sh`, `verify_fail_loudly_policy.sh`, contract tests, integration tests (prior T018, T035–T036b, T042, T048, T054, T063–T065, T075, T082, T085, T087, T089).
- [ ] V09 Final reporting: `result_finalizer.py` → `final_analysis_report.md` with provenance section, `validate_success_criteria.py`, `convergence_report_generator.py`, `final_report_hash_linker.py`, `cpu_tractability_validator.py` (prior T049‑adjacent T073, T055, T056, T076b).

## Reopened work (verifier‑rejected requirements)

- [ ] T101 [P1] [US1] Rewrite `code/analysis/glm_fitter.py` as a complete, importable module (no truncation, no syntax errors) exposing a reusable `fit_glm(data: pd.DataFrame, sample_size: int, seed: int) -> dict` function.  
  - **Enhancement**: Each iteration now logs a `tolerance` value (final optimization tolerance) in `data/aggregated/convergence_log.json` entries: `{"iteration_id": int, "sample_size": int, "converged": bool, "max_iterations": int, "tolerance": float, "error_message": str | null}`.  
  - Includes unit tests covering normal convergence, failure, and N=1 input. Verification passes with `pytest tests/unit/test_glm_fitter.py` and a smoke import succeeds, producing a valid convergence‑log entry.

- [ ] T102 [P1] [US1] Rewrite `code/analysis/split_half_validator.py` as a complete module implementing the bootstrap split‑half loop (FR‑003, FR‑004), consuming `fit_glm` from T101.  
  - For each sample‑size configuration: ≥ 50 iterations; per iteration randomly subsample subjects, split 50/50 train/test via `data_leakage_guard.py`, fit GLM on training half, evaluate on test half; replication success = 1 iff test‑set p < α **AND** direction matches **AND** test Cohen's d within ±20 % of training estimate.  
  - Discard non‑converged iterations, flag “Unreliable” if > 20 % fail.  
  - **Outputs**:  
    1. `data/derived/replication_results/individual_results.json` – list of per‑iteration records complying with `replication_result.schema.yaml` (all required fields populated).  
    2. `data/aggregated/split_half_results.json` – aggregated schema `[{"sample_size": int, "kernel": float, "replication_rate": float, "iterations": int}]`.  
  - Includes unit tests for magnitude/direction/α logic and empty‑result case.

- [ ] T103 [P1] [US1] Execute the documented quick‑start end‑to‑end run on real data to produce the missing intermediate artifacts.  
  - Command (as in `specs/001-statistical-power-analysis/quickstart.md`):  
    ```bash
    python code/main.py --config test_config.yaml
    ```  
    with `ds000030`, `N=10`, spatial smoothing kernel `4mm`, paradigm `Motor`.  
  - **Verification steps**:  
    1. Prior to execution, clean derived outputs: `rm -rf data/derived/ data/aggregated/`.  
    2. After run, assert `data/derived/processed_roi/roi_timeseries.csv` exists and contains **> 100 rows**.  
    3. Assert `data/aggregated/split_half_results.json` exists and contains a `replication_rate` field (float 0‑1).  
    4. Record actual exit code and row count in `results/paper/quickstart_run_log.md`.  
  - Re‑running from a clean state must reproduce identical CSV and JSON.

- [ ] T104 [P2] [US2] Rewrite `code/utils/convergence_monitor.py` as a complete module that reads `data/aggregated/convergence_log.json` (produced by T101) and flags iterations where `max_iterations > 100` **or** `tolerance < 1e-4`.  
  - Writes `results/paper/convergence_report.md` containing a Markdown table of flagged iterations (`iteration_id`, `reason`) and a summary count.  
  - Includes a contract test feeding a fixture log with one flagged and one clean entry, asserting correct report content.

- [ ] T090 [P2] Implement `code/analysis/collinearity_checker.py` to compute predictor correlation matrix and VIF for the logistic regression predictors (sample size, smoothing kernel, SNR level).  
  - Writes `data/aggregated/predictor_correlation.csv` with columns `predictor`, `VIF`.  
  - Unit test `tests/unit/test_collinearity_checker.py` verifies VIF < 5 for a synthetic low‑collinearity dataset and raises warning when VIF ≥ 5.

- [ ] T105 [P2] Orchestrator task that runs the full analysis pipeline after the lower‑level components are in place. It depends on T105a‑d (see below) and simply sequences them.

- [ ] T105a [P2] Run the **primary grid** (sample sizes 10, 20, 40, 60) across all five verified paradigms, both spatial kernels (4 mm, 8 mm), all effect‑size levels, α = 0.05, magnitude tolerance ±20 %, with ≥ 50 bootstrap iterations per configuration.  
  - Produces intermediate per‑paradigm result files under `data/derived/replication_results/`.

- [ ] T105b [P2] Run the **fine grid** (10, 15, 20, 30, 40, 50, 60) for the two selected paradigms, same other dimensions as T105a.  
  - Stores results alongside primary‑grid outputs.

- [ ] T105c [P2] Aggregate all replication results (from T105a and T105b) into power‑curve CSVs (`data/aggregated/power_curves/…`) conforming to `power_curve.schema.yaml`, fit the logistic regression model (including VIF check via T090), and write model pickles to `data/aggregated/logistic_models/`.  

- [ ] T105d [P2] Execute `scripts/validate_success_criteria.py` to verify SC‑001 – SC‑005 are satisfied. It writes `results/paper/success_criteria_status.json` and a human‑readable summary `results/paper/success_criteria_report.md`.  

- [ ] T106 [P3] Generate the required figures and tables directly from validated outputs.  
  - Power‑curve figures (`figures/power_curves_{paradigm}.png`) for each paradigm, each kernel, and each α.  
  - Sensitivity comparison table (`results/paper/sensitivity_report.md`) showing Cohen's d for 4 mm vs 8 mm, replication‑rate differences, and a “High‑Sensitivity” flag when the difference exceeds a predefined threshold.  
  - All artifacts are produced by deterministic scripts reading only `data/aggregated/` rows.

- [ ] T107 [P3] Write the concise methods/results section and paper‑stage handoff in `results/paper/final_analysis_report.md`.  
  - Links all figures/tables via relative paths, cites exact artifact locations (e.g., dataset IDs, SHA‑256 hashes, `pipeline_config_hash`).  
  - Describes negative findings, convergence failures, clamping events, and frames results as associational due to the signal‑injection model.  
  - Provides the reproducible command sequence (`python code/main.py --config …`, `scripts/validate_success_criteria.py`).  
  - Verification: every claim references an existing artifact; re‑running the documented workflow reproduces all files and all tests pass (`pytest tests/`).
