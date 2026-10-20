# Tasks: Statistical Power Analysis of Openly Available fMRI Datasets

**Input**: Design documents from `/specs/001-statistical-power-analysis/` (spec.md, plan.md, research.md, data-model.md, contracts/)
**Revision**: Re-plan after verifier rejection of T016, T017, T044a, T049 and task-format repair (duplicate/ambiguous identities). Verified completed work is preserved below as checked; only the rejected requirements are reopened, under fresh unique task IDs to eliminate the prior duplicate-identity failure.

## Verified completed work (preserve; do not redo)

The following prior requirements were independently verified complete and remain satisfied by existing artifacts under `code/`, `tests/`, `docs/`, and `specs/`:

- [ ] V01 Project scaffolding, `requirements.txt`, seed manager (`code/utils/seed_manager.py`), memory monitor, `SimulationConfig`/`ReplicationResult` models, timer, execution-order validator (prior T001a–T007, T038, T083).
- [ ] V02 Real-data ingestion with fail-loudly policy: `code/download/openneuro_fetcher.py` (stream-first, `verify_real_source()`, no synthetic fallback), `data_validator.py`, `corruption_handler.py`, `streaming_chunker.py`, `data_integrity_hash.py`, `sampling_strategy.py`, `resource_guard.py` (prior T008, T009, T058, T062, T067, T071, T078, T079, T081).
- [ ] V03 Preprocessing: `code/preprocess/roi_extractor.py` and `temporal_smoothing.py` (CPU-tractable ROI + temporal smoothing; kernels 4 s / 8 s), with `pipeline_config_hash.py` and `docs/preprocessing_justification.md` (prior T012, T013, T076, T077a/b, T068a/b).
- [ ] V04 Noise estimation and known-truth signal injection: `code/simulation/noise_estimator.py` (`data/derived/noise_parameters.json`), synthetic-data generation with real-noise parameters and ground-truth Cohen's d ∈ {0.0, 0.2, 0.5, 0.8, 1.0} (prior T014, T015).
- [ ] V05 Data-leakage guard `code/utils/data_leakage_guard.py` and its unit test (prior T066, T070).
- [ ] V06 Power-curve orchestration: `power_curve_generator.py` with clamping/insufficient-data guardrails, `bootstrap_aggregator.py`, logistic regression with VIF check and BH-FDR, alpha sweep, `multi_paradigm_runner.py`, `paradigm_loader.py` (prior T022–T026b, T029, T041, T052, T061, T072).
- [ ] V07 Sensitivity analysis: `temporal_sensitivity_orchestrator.py`, `effect_size_extractor.py` with seed logging, `sensitivity_metrics.json`, `sensitivity_report.md`, configurable threshold (prior T031–T034, T060, T074).
- [ ] V08 Orchestration and docs: `code/main.py` entry point, CLI docs, README data-integrity sections, `audit_data_sources.sh`, `verify_fail_loudly_policy.sh`, contract tests, integration tests (prior T018, T035–T036b, T042, T048, T054, T063–T065, T075, T082, T085, T087, T089).
- [ ] V09 Final reporting: `result_finalizer.py` → `final_analysis_report.md` with provenance section, `validate_success_criteria.py`, `convergence_report_generator.py`, `final_report_hash_linker.py`, `cpu_tractability_validator.py` (prior T049-adjacent T073, T055, T056, T076b).

## Reopened work (verifier-rejected requirements)

- [ ] T101 [P1] [US1] Rewrite `code/analysis/glm_fitter.py` as a complete, importable module (no truncation, no syntax errors) exposing a reusable `fit_glm(data: pd.DataFrame, sample_size: int, seed: int) -> dict` function.
    - Input: DataFrame with columns `[subject_id, roi_id, time_series]`; subsample to `sample_size` with the fixed seed BEFORE fitting.
    - Fit `time_series ~ 1` (or the task-contrast design), compute Cohen's d and a p-value, and return `{"effect_size": float, "p_value": float, "converged": bool, "max_iterations": int}`.
    - On each fit, append a record matching `[{"iteration_id": int, "sample_size": int, "converged": bool, "max_iterations": int, "error_message": str | null}]` to `data/aggregated/convergence_log.json` (create the file; it must exist and be valid JSON after any run).
    - Include focused unit tests in `tests/unit/test_glm_fitter.py` covering: normal convergence, convergence failure (returns `converged: false` and logs it), and N=1 input.
    - Verification: `pytest tests/unit/test_glm_fitter.py` passes; `python -c "from code.analysis.glm_fitter import fit_glm"` succeeds; a smoke call writes a valid `convergence_log.json` entry.
- [ ] T102 [P1] [US1] Rewrite `code/analysis/split_half_validator.py` as a complete module implementing the bootstrap split-half loop (FR-003, FR-004), consuming `fit_glm` from T101.
    - For each sample-size configuration: ≥ 50 iterations; per iteration randomly subsample subjects, split 50/50 train/test (via `data_leakage_guard.py`), fit GLM on the training half, evaluate on the test half; replication success = 1 iff test-set p < α AND direction matches AND test Cohen's d is within ±20% of the training estimate; discard non-converged iterations and count them; flag the run "Unreliable" if > 20% of iterations fail.
    - Output `data/aggregated/split_half_results.json` with schema `[{"sample_size": int, "kernel": str, "replication_rate": float, "iterations": int}]` — the file MUST be created even when iterations = 0 (empty list plus metadata). Each record must also satisfy `specs/001-statistical-power-analysis-of-openly-ava/contracts/replication_result.schema.yaml` fields where applicable.
    - Include focused unit tests in `tests/unit/test_split_half_validator.py` covering the magnitude/direction/α logic and the empty-result case.
    - Verification: `pytest tests/unit/test_split_half_validator.py` passes; running the validator on the T101 smoke input produces a valid non-empty `split_half_results.json`.
- [ ] T103 [P1] [US1] Execute the documented quickstart end-to-end run on real data to produce the missing intermediate artifact.
    - Command (documented in `specs/001-statistical-power-analysis/quickstart.md`): `python code/main.py --config test_config.yaml` with ds000030, N=10, temporal kernel 4 s, paradigm Motor.
    - Assert: `data/derived/processed_roi/roi_timeseries.csv` exists and has > 100 rows; `data/aggregated/split_half_results.json` (from T102) exists and contains a binary replication status; exit code 0. Record the actual exit code and row count in `results/paper/quickstart_run_log.md`.
    - Verification: re-running the command from clean derived outputs reproduces the CSV and JSON; the run log states the real measured row count and exit code (no invented values).
- [ ] T104 [P2] [US2] Rewrite `code/utils/convergence_monitor.py` as a complete module that reads `data/aggregated/convergence_log.json` (produced by T101), flags iterations with `max_iterations > 100` or `tolerance < 1e-4`, and writes the flagged iterations to `results/paper/convergence_report.md`.
    - The report must contain a Markdown table of flagged iterations (`iteration_id`, reason) and a summary count; the file MUST exist after the run (currently absent).
    - Include a contract test in `tests/unit/test_convergence_monitor.py` that feeds a fixture log with one flagged and one clean iteration and asserts the report content.
    - Verification: `pytest tests/unit/test_convergence_monitor.py` passes; after the T103 run, `results/paper/convergence_report.md` exists and reflects the actual convergence log entries.
- [ ] T105 [P2] [US2] Run the complete specified analysis domain and produce the final validated result set (FR-004, FR-005, SC-002, SC-003).
    - Execute `code/analysis/multi_paradigm_runner.py` over the five verified paradigms (ds000030, ds000206, ds000117, ds000247, ds001141), primary grid (10, 20, 40, 60), fine grid (10, 15, 20, 30, 40, 50, 60) on two paradigms, both temporal kernels (4 s, 8 s), effect-size grid {0.0, 0.2, 0.5, 0.8, 1.0}, ≥ 50 bootstrap iterations per configuration, α sweep {0.01, 0.05, 0.10}, magnitude-tolerance sweep {±10%, ±20%, ±30%}.
    - Outputs: `data/aggregated/power_curves/` per-paradigm CSVs conforming to `power_curve.schema.yaml`, `data/aggregated/predictor_correlation.csv` (VIF check), `data/aggregated/logistic_models/`, `data/aggregated/sensitivity_metrics.json`, `results/paper/timing_breakdown.csv` (SC-005: total wall-clock < 6 h on the 2-core CPU runner).
    - Verification: `scripts/validate_success_criteria.py` exits 0 with `results/paper/success_criteria_status.json` showing SC-001–SC-005 satisfied from the ACTUAL computed rates (no expected or placeholder values).
- [ ] T106 [P3] Generate the specified figures and result tables directly from the validated outputs (SC-002, SC-003).
    - Produce power-curve figures (replication rate vs. sample size, one panel per paradigm, per α and per kernel) and the sensitivity comparison table (Cohen's d 4 s vs 8 s, replication-rate difference, High-Sensitivity flag) as scripts reading only `data/aggregated/` rows — no manual transcription.
    - Outputs: `figures/power_curves_{paradigm}.png`, updated `results/paper/sensitivity_report.md` and `results/paper/final_analysis_report.md` with figures referenced by relative path.
    - Verification: each figure file exists and regenerates deterministically from the aggregated CSVs; the final report's numbers match the CSV cells.
- [ ] T107 [P3] Write the concise methods/results account and paper-stage handoff.
    - Add a methods/results section to `results/paper/final_analysis_report.md` linked to actual output cells and figure files; describe negative findings (e.g., non-monotonic curves, near-zero effect sizes yielding rates < 0.05), convergence failures, clamping events, and the associational-framing limitation of the signal-injection model honestly.
    - Document the paper-stage handoff: required figures/tables, the data-provenance block (OpenNeuro IDs, subject counts, SHA-256 hashes, pipeline_config_hash), and the reproducible command sequence (`python code/main.py --config ...`, `scripts/validate_success_criteria.py`).
    - Verification: every claim in the report cites an existing artifact path; re-running the documented workflow from declared inputs reproduces the result files and all tests pass (`pytest tests/`).

## Dependencies and requirement coverage

- **FR-001** (real OpenNeuro download): V02 (verified); consumed by T103/T105.
- **FR-002** (CPU-tractable preprocessing, two kernels): V03 (verified).
- **FR-003** (split-half validation, direction + magnitude): T101 → T102 → T103.
- **FR-004** (≥ 50 bootstrap iterations): T102, executed at scale in T105.
- **FR-005** (logistic regression, CPU): V06 (verified), re-executed in T105.
- **FR-006** (memory-limited downsampling): V02/V05 (verified).
- **SC-001–SC-005**: validated end-to-end by T105 (`validate_success_criteria.py`); SC-005 wall-clock recorded in `timing_breakdown.csv`.
- **Ordering**: T101 before T102 (validator consumes `fit_glm`); T102 before T103 (end-to-end run needs the validator); T103 before T104 (convergence log must exist before the monitor reads it); T105 after T101–T104; T106 after T105; T107 last.

## Revision behavior

Checked items V01–V09 preserve previously verified artifacts unchanged. Only the four verifier-rejected requirements were reopened (as T101–T104 with fresh unique IDs resolving the prior duplicate-identity failure: old T016, T017, T044a, T049), plus the downstream execution, figure, and reporting steps (T105–T107) that depend on them. No scientific requirement was dropped or weakened.
