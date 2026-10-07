# Tasks: Statistical Power Analysis of Openly Available fMRI Datasets

**Input**: Design documents from `/specs/001-statistical-power-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Research & Data Source Definition

**Purpose**: Establish the verified data sources and simulation parameters before implementation begins.

- [X] T000 [P] Create and populate `specs/001-statistical-power-analysis/research.md`. **Define the list of verified OpenNeuro dataset IDs (Motor, Working Memory, Emotional Face, Auditory Oddball, Visual Motion) with their checksums. Explicitly document the streaming chunk size strategy (e.g., 'process by subject') and the fixed random seed (seed=42) for all subsampling operations. This file serves as the single source of truth for T008 and T052.** **Output: `specs/001-statistical-power-analysis/research.md` with complete dataset metadata.**

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Initialize project directory structure. **Create directories: `code/`, `code/download/`, `code/preprocess/`, `code/simulation/`, `code/analysis/`, `code/models/`, `code/utils/`, `tests/`, `tests/contract/`, `tests/integration/`, `tests/unit/`, `data/`, `data/raw/`, `data/derived/`, `data/aggregated/`, `results/`, `results/paper/`.**
- [X] T001b [P] Create `__init__.py` in all Python package directories created in T001a. **Depends on T001a.**

- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt`. **Dependencies: bidslib>=2.0.0, nibabel>=3.0.0, nilearn>=0.9.0, scikit-learn>=1.0.0, statsmodels>=0.13.0, pandas>=1.3.0, numpy>=1.20.0, mne>=1.0.0, datasets>=2.0.0, pytest>=7.0.0.** **Depends on T001a.**
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`. **Depends on T001a.**

---

## Phase 2a: Infrastructure (Foundational Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY implementation or testing

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/seed_manager.py` to enforce fixed random seeds for reproducibility (PRINCIPLE I).
- [X] T005 [P] Implement `code/utils/memory_monitor.py` to track RAM usage and trigger downsampling if >6GB (FR-006).
- [X] T006 [P] Create `code/models/simulation_config.py` defining `SimulationConfig` entity (sample_size_target, smoothing_kernel, num_iterations, random_seed). **Depends on T005.**
- [X] T007 [P] Create `code/models/replication_result.py` defining `ReplicationResult` entity (effect_size_est, p_value, replication_success, smoothing_kernel_used). **Depends on T006.**
- [X] T038 [P] Implement `code/utils/timer.py` to provide `start_run`, `end_run`, and `log_split` methods for wall‑clock time monitoring (SC-005). **Output: `results/paper/timing_report.md` and `results/paper/timing_breakdown.csv`.** **Depends on T004.**
- [X] T083 [P] [All] Implement `code/utils/execution_order_validator.py` as a **standalone utility module**. **This validator must be called by `code/main.py` (T018) as a pre-flight check before any analysis begins. It must raise a `TaskOrderError` if a dependency is missing, preventing the pipeline from proceeding with stale or missing data.** **Depends on T004, T005.**

**Checkpoint**: Infrastructure ready - implementation can now begin

---

## Phase 2b: Core Implementation (Data, Preprocess, Model, & Validation Integrity)

**Purpose**: Implementation of core data flow, model logic, and strict validation integrity

- [X] T058 [Optional] [P] Implement `code/utils/streaming_chunker.py` to handle datasets where the full BIDS structure cannot be loaded into RAM. This utility yields subjects in chunks, allowing the `openneuro_fetcher` to process large datasets without exceeding available RAM constraints, while maintaining the integrity of the random seed for reproducibility. **Optional: Only used if `datasets.load_dataset(..., streaming=True)` is insufficient.** **Does NOT depend on T008; depends on T001/T005.**

- [X] T008 [P] [US1] Implement `code/download/openneuro_fetcher.py` to download raw BIDS data for **the set of verified datasets**. **Read dataset IDs dynamically from `specs/001-statistical-power-analysis/research.md` (T000). Validate checksums against a manifest before fetching. Use `datasets.load_dataset(..., streaming=True)` for datasets > 1 GB. On any fetch failure, `raise ValueError("Real data fetch failed. Aborting.")` – no synthetic fallback. **Fetch must be streamed/chunked to avoid loading full dataset into memory before T012 extraction.** **Depends on T000, T005.**

- [X] T062 [P] [US1] Implement `code/utils/data_integrity_hash.py` to generate a SHA-256 hash of the *validated subset* of the raw BIDS dataset used in each run (post-T009). This hash must be included in the final `final_analysis_report.md` to guarantee that the results are tied to a specific version of the raw data. **Depends on T009 (run after validation to hash validated data).**

- [X] T009 [P] [US1] Implement `code/download/data_validator.py` to verify BIDS structure and checksum raw NIfTI files; skip corrupted subjects and log warnings. **If valid subjects < 5, raise error code 1 and log "Insufficient Data".** **Depends on T008 (fetch first).**

- [X] T012 [P] [US1] Implement `code/preprocess/roi_extractor.py` to extract ROI time‑series from **FULL** raw BIDS data (CPU‑tractable substitute for fMRIPrep). **Order of operations: 1. Extract ROI from full (or streamed) dataset. 2. Validate SNR preservation. 3. Output the FULL set of ROI time-series (do NOT subsample here; subsampling occurs dynamically in T017).** Explicitly validate that this approach satisfies FR-002's 'equivalent' clause by referencing the justification in `docs/preprocessing_justification.md` (T077b). **Depends on T008.**

- [X] T013 [P] [US1] Implement `code/preprocess/temporal_smoothing.py` to apply **temporal** smoothing kernels to 1‑D ROI time‑series. Mapping: 4 s (TR = 2 s) ↔ 4 mm spatial. Use standard Gaussian kernel sigma = FWHM / conversion_factor. Boundary handling: reflect. Configurable `mode` parameter (`temporal` default). **Input: FULL dataset from T012. Output: FULL smoothed dataset.** **Depends on T012.**

- [X] T014 [P] [US1] Implement `code/simulation/noise_estimator.py` to estimate noise characteristics from **REAL** preprocessed data (T013 output). **Calculate mean, variance, and autocorrelation of the real ROI time-series to derive realistic noise parameters (sigma, AR(1) coefficient).** **Output: `data/derived/noise_parameters.json`.** **This step is critical for the 'Known-Truth' simulation: noise is derived from reality to parameterize the synthetic data.** **Depends on T013.**

- [X] T015 [P] [US1] Implement `code/simulation/synthetic_data_gen.py` to generate synthetic fMRI time-series with embedded ground-truth effect sizes. **Input: `noise_parameters.json` from T014. Use real noise parameters to generate synthetic data, then inject known effect sizes (Cohen's d = 0.0, 0.2, 0.5, 0.8, 1.0) at specific time points.** **Output: `data/derived/synthetic_timeseries.npy`.** **This task implements the 'Known-Truth' simulation by combining real noise with known signals.** **Depends on T014.**

- [X] T016 [P] [US1] Implement `code/analysis/glm_fitter.py` as a **reusable function/module** (not a one-shot script). **Input: A subset of data (real or synthetic). Fit a GLM and estimate effect size (Cohen's d). Output: `{"effect_size": float, "p_value": float, "converged": bool}`.** **Randomly subsample subjects to simulate the requested sample size *before* fitting (passed as input). Capture convergence status and log to `data/aggregated/convergence_log.json`.** **Depends on T013/T015.**

- [X] T066 [P] [US1] Implement `code/utils/data_leakage_guard.py` to enforce strict memory isolation during the split-half bootstrap loop. This utility must explicitly delete training set references and force garbage collection (`gc.collect()`) before loading the test set, and verify that no shared object IDs exist between the two sets to prevent accidental data leakage. **This is a critical prerequisite for T017.** **Depends on T004/T005.**

- [X] T017 [P] [US1] Implement `code/analysis/split_half_validator.py` to perform **bootstrap loop**: for each sample‑size configuration, run **≥ 50** random split‑half iterations. **Algorithm: 1. Load FULL dataset (T013/T015). 2. **INSIDE LOOP**: Randomly subsample subjects into train/test sets (dynamic resampling per iteration). 3. Call `glm_fitter` (T016) to fit GLM on training half. 4. Check convergence: if failed, discard iteration and increment counter. 5. If converged, check magnitude: is test Cohen's d within ±20% of training estimate? 6. Check direction: is sign of test Cohen's d same as training? 7. If both match, record replication success (1), else 0. 8. If >20% iterations fail, flag run "Unreliable".** Aggregate the successes to produce an empirical replication probability per sample size. **Explicitly implements the ±20% magnitude constraint, direction check, and p < 0.05 threshold.** **Output: `data/aggregated/split_half_results.json` with schema `[{"sample_size": int, "kernel": str, "replication_rate": float, "iterations": int}]`. **MUST create this file even if iterations=0 (empty list with metadata).** **Depends on T016, T066.**

- [X] T023 [P] [US2] Implement logic in `code/analysis/power_curve_generator.py` to clamp requested sample size to the available data if N > original (Edge Case 2). **If clamping occurs, log a "Data Limitation" warning with the original and clamped sizes.** **Depends on T017.**

- [X] T077a [P] [All] Update `specs/001-statistical-power-analysis/plan.md` to explicitly document the architectural deviation from fMRIPrep to ROI extraction + temporal smoothing as a CPU-tractable substitute. **Must cite: Smith et al., 2013; Eklund et al., 2016.** **Must explicitly argue that for known-truth simulations, ROI extraction preserves the signal-to-noise ratio characteristics required for power analysis while avoiding the computational intractability of full-brain fMRIPrep. Document the `pipeline_config_hash` generated by T076.** **This task updates the plan, not the spec, to resolve the architectural deviation.** **Depends on T012, T013.**

- [X] T077b [P] [All] Create `docs/preprocessing_justification.md` to document the static scientific rationale for the CPU-tractable alternative. **Must cite: Smith et al., 2013; Eklund et al., 2016.** **Must explicitly argue that for known-truth simulations, ROI extraction preserves the signal-to-noise ratio characteristics required for power analysis while avoiding the computational intractability of full-brain fMRIPrep. Document the `pipeline_config_hash` generated by T076.** **This task documents the deviation in docs; it does not modify spec.md or plan.md.** **Depends on T012, T013, T077a.**

**Checkpoint**: Core implementation ready - testing and orchestration can begin

---

## Phase 2c: Testing (Validation of Implementation)

**Purpose**: Validate core implementation before orchestration

- [X] T010 [US1] Contract test for `SimulationConfig` schema in `tests/contract/test_simulation_config_schema.py`. **Write this test FIRST (TDD); it will fail until T006 is implemented.** Validate `sample_size_target > 0` and `random_seed` is int. **Depends on T006.**
- [X] T011 [US1] Integration test for end‑to‑end pipeline in `tests/integration/test_end_to_end_pipeline.py`. **Write this test FIRST (TDD); it will fail until T012‑T017 are implemented.** Run with inputs: ds000030, N=10, kernel=4 s (temporal), paradigm=Motor. Assert output file `data/aggregated/power_curves.json` exists and contains `sample_sizes_tested` and `empirical_rates` (list of floats). **Depends on T012‑T017.**

**Checkpoint**: Core implementation validated

---

## Phase 3a: Power Curve Generator (US2 Core Logic)

**Purpose**: Implement the power curve generation logic

- [X] T022 [P] [US2] Implement `code/analysis/power_curve_generator.py` to orchestrate **bootstrap iterations** per sample size (FR‑004) and support **multiple smoothing kernels** (temporal variants 4s/8s). For each (sample size, kernel) pair, call `split_half_validator` to obtain replication successes, then compute the mean success rate → power curve point. **Also iterate over alpha thresholds representing standard significance levels (Assumption‑Alpha) and store separate curves per alpha.** **Depends on T012‑T017, T008, T052.**
- [X] T024 [P] [US2] Implement logistic regression model in `power_curve_generator.py` using `statsmodels` with replication success as outcome and fixed effects: sample size, preprocessing variant, estimated_noise_level (from T014). **Explicitly exclude 'alpha' as a fixed effect; instead, implement alpha-sweep logic to verify robustness across low, medium, and high thresholds by running separate models for each alpha.** **Apply Benjamini-Hochberg FDR correction by default to final results; Bonferroni is optional via CLI.** **Output: `data/aggregated/logistic_regression_model.json` with schema `{"coefficients": {}, "vif": {}, "alpha_sweep_results": [{"alpha": float, "coefficients": {}, "p_values": {}, "corrected_p_values": {}, "correction_method": str}]}`.** **Depends on T022, T014.**
- [X] T025 [P] Add VIF calculation in `power_curve_generator.py` to check multicollinearity (SC‑004). Log "High Collinearity" if VIF ≥ 5 and flag model result as "Invalid" in output metadata; do not halt pipeline. **Depends on T024.**
- [X] T026 [P] Implement aggregation logic to output `data/aggregated/power_curves.json` with fields `sample_sizes_tested`, `empirical_rates`, and `alpha_values`. **Depends on T022.**
- [X] T026b [P] Implement `code/utils/bootstrap_aggregator.py` to consume lists of replication results per configuration and compute empirical rates. **Called by T022.** **Depends on T022.**
- [X] T041 [P] [US2] Refactor `power_curve_generator.py` to extract aggregation logic into a dedicated module (`utils/bootstrap_aggregator.py`) and expose a clean API for multi‑kernel, multi‑alpha runs. This consolidates the previously missing T041a/T041b responsibilities. **Depends on T022.**

**Checkpoint**: Power curve logic ready

---

## Phase 3b: Multi‑Paradigm & Alpha Sweep (US2 Orchestration)

**Purpose**: Orchestrate the power curve generation across paradigms and alpha values

- [X] T052 [P] [US2] Implement `code/download/paradigm_loader.py` to read the list of cognitive paradigms and their associated dataset IDs from `specs/001-statistical-power-analysis/research.md` (T000). **Explicitly limit loading to a set of verified paradigms.** Returns list of dicts `{ "paradigm": str, "dataset_id": str }`. **Depends on T008, T000.**
- [X] T029 [P] [US2] Implement `code/analysis/multi_paradigm_runner.py` to loop over verified paradigms, invoke `power_curve_generator` for each, and log timing via `timer.py`. Handles alpha‑sweep internally (via T022). **Depends on T022, T052, T038.**

**Checkpoint**: US2 complete

---

## Phase 4: User Story 3 - Preprocessing Sensitivity Analysis (Priority: P3)

**Goal**: Compare effect sizes and replication rates across different smoothing kernels.

- [X] T031 [P] [US3] Extend `power_curve_generator.py` (via its parameter interface) to run separate loops for the two **temporal** smoothing kernels (4 s, 8 s). This provides per‑kernel power curves. **Depends on T013, T022.**
- [X] T031b [P] [US3] Implement `code/analysis/temporal_sensitivity_orchestrator.py` to invoke `power_curve_generator` for each kernel variant, collect both replication rates and Cohen's d values, and pass them to the comparison task. **Depends on T031.**
- [X] T031c [P] [US3] Implement `code/analysis/effect_size_extractor.py` to extract Cohen's d from each GLM fit for a given kernel. Outputs a list of effect sizes per kernel. **Depends on T016.**
- [X] T032 [P] [US3] Implement comparison logic in `temporal_sensitivity_orchestrator.py` to calculate **absolute difference in Cohen's d** and **difference in replication rates** between kernel pairs. Write results to `data/aggregated/sensitivity_metrics.json` with schema `[{"paradigm": str, "kernel_a": str, "kernel_b": str, "diff_cohen_d": float, "diff_replication_rate": float}]`. **Depends on T031b, T031c.**
- [X] T033 [P] Add "High Sensitivity" flag in `temporal_sensitivity_orchestrator.py` if **both** replication‑rate difference > 10 pp **or** Cohen's d difference > 0.2 (US‑3 Scenario 2). **Depends on T032.**
- [X] T034 [P] Implement summary report generation in `results/paper/sensitivity_report.md` comparing kernel conditions. Include a Markdown table with columns: Paradigm, Cohen's d (4 s), Cohen's d (8 s), Diff (Cohen's d), Replication Rate (4 s), Replication Rate (8 s), Diff (Rate), Sensitivity Flag. **Depends on T033.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T018 [P] [US1] Implement `code/main.py` entry point to orchestrate download, preprocess, and validate for a single run configuration. **Orchestrates T004-T009, T012-T017, T022, T029. Calls T083 (pre-flight) and T055/T056 as final steps.** **Depends on T016, T017, T022, T004-T009, T012-T013, T083.**
- [X] T035 [P] Update `README.md` with CLI usage examples and installation instructions. **Reference T054 for exact CLI commands and arguments.** **Depends on T054.**
- [X] T036a [P] Add docstrings to `code/main.py` with parameter descriptions. **Use Google style. Document all parameters and return types.** **Verify via `pydocstyle` (0 errors).** **Depends on T018.**
- [X] T036b [P] Add docstrings to `code/analysis/power_curve_generator.py` with parameter descriptions. **Use Google style. Document all parameters and return types.** **Verify via `pydocstyle` (0 errors).** **Depends on T022.**
- [X] T054 [P] Document CLI interface in `docs/cli.md` with command examples, arguments, and exit codes. **Replaces previous API‑endpoint doc.**
- [X] T039 [P] Remove unused imports from all `code/` modules.
- [X] T040 [P] Enforce Black formatting on all `code/` and `tests/` files. **Use the Black code formatter with a line length of 88.**
- [X] T042 [P] Add unit tests for `code/analysis/glm_fitter.py` (functions: `fit`, `predict`) and `code/analysis/split_half_validator.py` (functions: `validate`). Cover edge cases: convergence failure, N=1.
- [X] T044a [P] [US1] Run `quickstart.md` validation on GitHub Actions free‑tier. **Command:** `python code/main.py --config test_config.yaml`. **Assert:** `data/derived/roi_timeseries.csv` exists and has > 100 rows. Exit code 0. **Depends on T012.**
- [X] T044b [P] Run `quickstart.md` validation on GitHub Actions free‑tier. **Assert:** `data/aggregated/power_curves.json` exists and contains valid data. Exit code 0. **Depends on T022.**
- [X] T048 [P] [US2] Add logging in `multi_paradigm_runner.py` to record the exact sample size used per paradigm when clamping occurs (Edge Case 2), ensuring transparency in the final report. **Depends on T023.**

**Checkpoint**: Data ingestion is strictly real, streamed, and fails loudly on error.

---

## Phase 7: Execution Monitoring & Reporting (Critical Review Response)

**Goal**: Ensure all execution constraints (time, memory, convergence) are actively monitored and reported in the final artifacts.

- [X] T049 [P] [US2] Implement `code/utils/convergence_monitor.py` to parse `convergence_log.json` from T016 (schema: `iteration_id`, `converged`, `max_iterations`, `tolerance`), flag iterations where `max_iterations > 100` or `tolerance < 1e-4`, and output `results/paper/convergence_report.md` (JSON list of `{iteration_id, reason}`). **Depends on T016.**
- [X] T050 [P] [US2] Update `code/utils/timer.py` (T038) to log intermediate timing for each paradigm, sample size, and kernel, not just total run time. **Output:** `results/paper/timing_breakdown.csv`.
- [X] T051 [P] [US2] Add final validation step in `code/main.py` that checks for existence of all required output files (`power_curves.json`, `sensitivity_report.md`, timing logs, convergence report) before exiting. Exit code 1 if any are missing. **Depends on T073, T049.**

**Checkpoint**: Full observability into pipeline execution and model health.

---

## Phase 8: Final Verification & Reporting (Critical Review Response)

**Goal**: Ensure all analysis results are correctly aggregated, validated against success criteria, and formatted for the final paper.

- [X] T055 [P] [US2] Implement `code/analysis/result_finalizer.py` to aggregate `power_curves.json`, `sensitivity_metrics.json`, `convergence_report.md`, and `timing_breakdown.csv` into a single `results/paper/final_analysis_report.md`. Include a summary table of all paradigms with their power curves (N vs Replication Rate), sensitivity flags, and convergence status. Explicitly note any paradigm that failed SC‑002 or SC‑003.
- [X] T056 [P] [US2] Implement `scripts/validate_success_criteria.py` that reads `final_analysis_report.md` and verifies that all Success Criteria (SC‑001 to SC‑005) are met. Output `results/paper/success_criteria_status.json` with boolean flags per SC. Exit code indicating failure if any SC is unmet. **Depends on T055.**

**Checkpoint**: Final verification complete; all success criteria validated and reported.

---

## Phase 9: Execution Optimization & Resource Management (Revision Response)

**Goal**: Address specific concerns regarding memory safety, task ordering, and the strict separation of training/test data to prevent data leakage during the bootstrap process.

- [X] T060 [P] [US3] Enhance `code/analysis/effect_size_extractor.py` to log the **exact random seed** used for the subject subsampling in each iteration. This ensures that the "High Sensitivity" flag in T033 can be traced back to a specific random partition, aiding in reproducibility and debugging of edge cases. **Depends on T031c.**
- [X] T061 [P] [US2] Update `code/analysis/power_curve_generator.py` to include a **minimum sample size guardrail**. If the available dataset after clamping (Edge Case) has an insufficient number of subjects, the generator must skip that sample size configuration. and log a "Skipped: Insufficient Data" entry in `data/aggregated/power_curves.json` rather than attempting a statistically invalid fit. **This logic is integrated into T023.** **Depends on T023.**

**Checkpoint**: Execution is optimized for memory, data integrity, and strict ordering.

---

## Phase 10: Documentation & Reproducibility Audit (Revision Response)

**Goal**: Ensure all documentation explicitly references the real data sources, streaming strategies, and the "Fail Loudly" policy to prevent future fabrication risks.

- [X] T063 [P] Update `docs/cli.md` and `README.md` to include a specific section on "Data Source Integrity" that documents the exact OpenNeuro IDs used, the streaming method, and the strict "no synthetic fallback" policy. **Include the following text template: "This project uses real data from OpenNeuro (IDs: [list]). Data is streamed in chunks of varying sizes. If fetch fails, the process aborts with no synthetic fallback."** **Verify that `research.md` (T000) contains a table of OpenNeuro IDs and checksums.** **Depends on T008, T048.**
- [X] T064 [P] Add a `scripts/audit_data_sources.sh` script that verifies the existence and checksum of all raw data files in `data/raw/` against the manifest in `research.md` (T000), ensuring no stale or missing data exists before running the analysis. **Exit code 1 if mismatch. Output: `results/paper/audit_report.md`.** **This is a hard gate for T055. Depends on T009, T062.**
- [X] T065 [P] **Verify** `specs/001-statistical-power-analysis/research.md` (T000) explicitly lists the streaming chunk size (variable rows) and the exact random seed strategy (seed=42) used for subject subsampling, ensuring full reproducibility of the "real data sample" approach. **Do NOT modify research.md; verify T000 output.** **Depends on T000.**

**Checkpoint**: Documentation fully reflects real data usage and reproducibility guarantees.

---

## Phase 11: Review Response - Data Integrity & Reproducibility Hardening

**Goal**: Address specific reviewer concerns regarding the strict separation of training/test data, the "Fail Loudly" data policy, and the explicit justification of the CPU-tractable preprocessing alternative.

- [X] T067 [P] [US1] Refactor `code/download/openneuro_fetcher.py` to include a mandatory `verify_real_source()` step that checks for the existence of a local data manifest (from `research.md`, T000) before attempting any fetch. If a verified source is present but the local fetch fails, the system must raise a critical error citing the specific missing verified source, rather than attempting to fetch from a guessed URL. **Depends on T008.**
- [X] T069 [P] [US2] Add a "Data Provenance" section to `results/paper/final_analysis_report.md` that lists the exact OpenNeuro dataset IDs, the specific subject counts used per paradigm, and the SHA-256 hash of the raw data used, ensuring full traceability of the "real data" claim. **Depends on T055, T062.**
- [X] T070 [P] [US2] Implement a `scripts/check_data_leakage.py` unit test that simulates a split-half run and asserts that no memory addresses overlap between the training and test data buffers during the GLM fitting process, validating the effectiveness of T066. **Depends on T066.**

**Checkpoint**: Full observability into pipeline execution and model health.

---

## Phase 12: Final Integration & Edge Case Validation (Revision Response)

**Goal**: Ensure robust handling of edge cases (corrupted data, insufficient subjects, convergence failures) and validate the complete pipeline against all success criteria with real data.

- [X] T071 [P] [US1] Implement `code/download/corruption_handler.py` to explicitly detect and log corrupted NIfTI files during the validation phase (T009), skip affected subjects, and raise a critical error if the remaining valid subject count falls below the minimum threshold (N=5) required for statistical power. **Depends on T009.**
- [X] T072 [P] [US2] Update `code/analysis/power_curve_generator.py` to explicitly handle the "Data Limitation" edge case where the requested sample size exceeds the available dataset size, ensuring the system clamps the size, logs a warning, and proceeds without attempting to synthesize missing data. **Depends on T023, T071.**
- [X] T073 [P] [US2] Implement `code/utils/convergence_report_generator.py` to aggregate convergence logs from `glm_fitter` (T016) and produce a detailed `results/paper/convergence_analysis.md` that identifies systematic convergence failures across specific paradigms or sample sizes. **Depends on T049, T016.**
- [X] T074 [P] [US3] Extend `temporal_sensitivity_orchestrator.py` (T031b) to include a "Sensitivity Threshold" configuration parameter that allows users to adjust the "High Sensitivity" flag criteria (currently 10pp rate difference or 0.2 Cohen's d difference) via CLI, ensuring flexibility for different research contexts. **Depends on T031b, T032.**
- [X] T075 [P] [All] Add a final integration test `tests/integration/test_full_pipeline_validation.py` that runs the entire pipeline on a small, verified dataset (ds000030) with all edge cases enabled (corruption simulation, small N, convergence limits) and asserts that the system fails gracefully or clamps appropriately without synthesizing data. **Depends on T071, T072, T073, T074.**

---

## Phase 13: Specification Alignment & Hash Generation (Revision Response)

**Goal**: Address specification deviations and ensure traceability of pipeline configurations.

- [X] T076 [P] [All] Implement `code/utils/pipeline_config_hash.py` to generate a SHA-256 hash of the *actual* pipeline parameters (ROI masks, sigma values, smoothing kernel) used in every run. This hash is generated by the code during execution and logged to the final report. **This task generates the hash; T068b appends it.** **Depends on T012, T013.**
- [X] T068a [P] [All] Create `docs/preprocessing_justification.md` to document the static scientific rationale for the CPU-tractable alternative. **This task writes the static justification BEFORE execution.** **Depends on T012, T013.**
- [X] T068b [P] [All] Append the runtime `pipeline_config_hash` (from T076) to `docs/preprocessing_justification.md` after execution. **This task updates the document with the runtime hash.** **Depends on T076.**

---

## Phase 14: Execution Gate & Resource Constraint Hardening (Revision Response)

**Goal**: Address the "Compute Feasibility" rule by explicitly ensuring the pipeline fails loudly on resource exhaustion and never attempts to simulate a GPU workload on CPU, while enforcing strict data streaming for large datasets.

- [X] T078 [P] [All] Implement `code/utils/resource_guard.py` to enforce a hard memory ceiling during data loading and model fitting. **If memory usage exceeds this threshold, the utility must immediately raise a `ResourceExhaustionError` with a specific error code (e.g., 13) and a message directing the user to reduce sample size or enable streaming. Do NOT attempt to swap to disk or degrade precision silently.** **Depends on T005.**
- [X] T079 [P] [US1] Update `code/download/openneuro_fetcher.py` to implement a "Stream-First" policy for datasets > 500 MB. **The fetcher must default to `datasets.load_dataset(..., streaming=True)` for any dataset exceeding this threshold. If streaming fails, it must raise an error rather than attempting a full download that might crash the runner.** **Depends on T078.**
- [X] T084 [P] [All] Implement `code/utils/device_selector.py` to implement adaptive device selection. **This utility must check for available GPU resources; if present and supported, it may use GPU for acceleration, but MUST default to CPU if GPU is unavailable or if the code is designed for CPU-only execution. It must NOT raise a hard error if a GPU is detected, but rather log a warning and proceed with CPU execution if the GPU path is not explicitly enabled.** **Depends on T078.**
- [X] T081 [P] [US2] Implement `code/utils/sampling_strategy.py` to define and enforce a "Real Sample" policy. **This utility must ensure that any subsampling of subjects is performed via `itertools.islice` or a fixed-seed random sample from the *real* streamed data, and must explicitly log the sample size and the specific random seed used. It must NOT generate synthetic data or use a bundled toy dataset as a fallback.** **Depends on T079.**
- [X] T082 [P] [All] Add a "Data Integrity" contract test in `tests/contract/test_data_integrity.py` that verifies the `data_integrity_hash` (T062) matches the actual raw data checksums in `data/raw/` before any analysis begins. **If the hashes do not match, the test must fail and abort the pipeline, ensuring no analysis is performed on corrupted or modified data.** **Depends on T062.**
- [X] T089 [P] [All] Implement `code/utils/cpu_tractability_validator.py` to validate that the ROI extraction + temporal smoothing pipeline completes within the operational time constraint (SC-005) on a simulated run. **This task replaces the impossible T088 (fMRIPrep benchmark) with a validation of the actual CPU-tractable approach.** **Depends on T012, T013, T038.**

---

## Phase 15: Final Validation & Execution Gate Compliance (Revision Response)

**Goal**: Address the final set of concerns regarding the strict ordering of tasks, the explicit handling of the "CPU-first" constraint, and the verification of the "Fail Loudly" policy before the project is considered ready for execution.

- [X] T085 [P] [All] Implement `scripts/verify_fail_loudly_policy.sh` to simulate a fetch failure scenario (e.g., by temporarily renaming a verified dataset file) and assert that the pipeline raises a `ValueError` with the message "Real data fetch failed. Aborting." and exits with a non-zero code. **This script must be run as part of the CI/CD pipeline to ensure the "Fail Loudly" policy is consistently enforced.** **Depends on T008, T079.**
- [X] T086 [P] [US2] Update `code/analysis/power_curve_generator.py` to include a final "Data Integrity" check that verifies the `data_integrity_hash` (T062) matches the hash of the data actually used in the analysis (post-sampling). **If the hashes do not match, the generator must raise a `DataIntegrityError` and abort, ensuring that no analysis is performed on modified or corrupted data.** **Depends on T062, T081.**
- [X] T087 [P] [All] Add a final "Execution Gate" test in `tests/integration/test_execution_gate.py` that runs the entire pipeline with all constraints enabled (memory limits, CPU-only, stream-first, fail-loudly) and asserts that the pipeline completes successfully or fails gracefully with the appropriate error codes. **This test must be the final gate before the project is considered ready for execution.** **Depends on T078, T079, T084, T081, T082, T083, T085, T086, T089.**