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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create directory `code/`. **Create `__init__.py` in the directory to form a valid Python package.**
- [X] T001b [P] Create directory `code/download/`. **Create `__init__.py`.**
- [X] T001c [P] Create directory `code/preprocess/`. **Create `__init__.py`.**
- [X] T001d [P] Create directory `code/simulation/`. **Create `__init__.py`.**
- [X] T001e [P] Create directory `code/analysis/`. **Create `__init__.py`.**
- [X] T001f [P] Create directory `code/models/`. **Create `__init__.py`.**
- [X] T001g [P] Create directory `code/utils/`. **Create `__init__.py`.**
- [X] T001h [P] Create directory `tests/`. **Create `__init__.py`.**
- [X] T001i [P] Create directory `tests/contract/`. **Create `__init__.py`.**
- [X] T001j [P] Create directory `tests/integration/`. **Create `__init__.py`.**
- [X] T001k [P] Create directory `tests/unit/`. **Create `__init__.py`.**
- [X] T001l [P] Create directory `data/`.
- [X] T001m [P] Create directory `data/raw/`.
- [X] T001n [P] Create directory `data/derived/`.
- [X] T001o [P] Create directory `data/aggregated/`.
- [X] T001p [P] Create directory `results/`.
- [X] T001q [P] Create directory `results/paper/`.

- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (bidslib, nibabel, nilearn, scikit-learn, statsmodels, pandas, numpy, mne, datasets). **Depends on T001a.**
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`. **Depends on T001a.**

---

## Phase 2a: Infrastructure (Foundational Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY implementation or testing

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/seed_manager.py` to enforce fixed random seeds for reproducibility (PRINCIPLE I).
- [X] T005 [P] Implement `code/utils/memory_monitor.py` to track RAM usage and trigger downsampling if >6GB (FR-006).
- [X] T006 [P] Create `code/models/simulation_config.py` defining `SimulationConfig` entity (sample_size_target, smoothing_kernel, num_iterations, random_seed). **Depends on T005.**
- [X] T007 Create `code/models/replication_result.py` defining `ReplicationResult` entity (effect_size_est, p_value, replication_success, smoothing_kernel_used). **Depends on T006.**
- [X] T038b [P] Implement `code/utils/timer.py` to provide `start_run`, `end_run`, and `log_split` methods for wall‑clock time monitoring (SC-005). **Output: `results/paper/timing_report.md` and `results/paper/timing_breakdown.csv`.** **Depends on T004.**

**Checkpoint**: Infrastructure ready - implementation can now begin

---

## Phase 2b: Core Implementation (Data, Preprocess, Model)

**Purpose**: Implementation of core data flow and model logic

- [X] T008 [US1] Implement `code/download/openneuro_fetcher.py` to download raw BIDS data for **the set of verified datasets**. **Read dataset IDs dynamically from `specs/001-statistical-power-analysis/research.md` under `root.datasets`. Validate checksums against a manifest before fetching. Use `datasets.load_dataset(..., streaming=True)` for datasets >1 GB. On any fetch failure, `raise ValueError("Real data fetch failed. Aborting.")` – no synthetic fallback. Clamp the fetch to available memory by sampling subjects if necessary. **Depends on T005.**
- [X] T009 [P] Implement `code/download/data_validator.py` to verify BIDS structure and checksum raw NIfTI files; skip corrupted subjects and log warnings. **If valid subjects < 5, raise error code 1 and log “Insufficient Data”.** **Depends on T008.**
- [X] T012 [US1] Implement `code/preprocess/roi_extractor.py` to extract ROI time‑series from raw BIDS data (CPU‑tractable substitute for fMRIPrep). **Only ROI extraction; no spatial normalization or other heavy preprocessing steps, preserving the plan’s “lightweight” claim.** Randomly subsample subjects to achieve the requested sample size *before* extraction. **Depends on T008.**
- [X] T013 [US1] Implement `code/preprocess/temporal_smoothing.py` to apply **temporal** smoothing kernels to 1‑D ROI time‑series. Mapping: 4 s (TR = 2 s) ↔ 4 mm spatial, 8 s ↔ 8 mm spatial. Gaussian kernel with sigma = FWHM / (sqrt(2 ln 2)). Boundary handling: reflect. Configurable `mode` parameter (`temporal` default). Random subsampling performed *before* smoothing. **Depends on T012.**
- [X] T053 [P] Implement `code/preprocess/spatial_smoothing.py` to apply **spatial** smoothing kernels (4 mm, 8 mm) to 3‑D/4‑D NIfTI data. This satisfies FR‑002’s requirement for two distinct smoothing kernel sizes. The implementation is CPU‑tractable (uses Nilearn’s `smooth_img`). **Depends on T012.**
- [X] T014 [P] Implement `code/simulation/noise_estimator.py` to estimate noise characteristics from **real** preprocessed data for GLM modeling. **No synthetic generation references.** **Depends on T013.**
- [X] T016 [P] Implement `code/analysis/glm_fitter.py` to fit a GLM on **real** preprocessed data (post‑smoothing) and estimate effect size (Cohen’s d). **Randomly subsample subjects to simulate the requested sample size *before* fitting.** Capture convergence status (max iterations, tolerance) and log to `data/aggregated/convergence_log.json` using the schema `[{\"iteration_id\": int, \"converged\": bool, \"max_iterations\": int, \"tolerance\": float}]`. **Depends on T013.**
- [X] T017 [US1] Implement `code/analysis/split_half_validator.py` to perform **bootstrap loop**: for each sample‑size configuration, run **≥ 50** random split‑half iterations, fit GLM on the training half, compute Cohen’s d, test significance on the held‑out half, and record replication success (direction match, p < 0.05, magnitude within ±20%). Aggregate the successes to produce an empirical replication probability per sample size. **Depends on T016.**
- [X] T019 [US1] Extend `split_half_validator.py` to discard GLM iterations that fail to converge and flag the run “Unreliable” if > 20 % of iterations fail. **Depends on T017.**

**Checkpoint**: Core implementation ready - testing and orchestration can begin

---

## Phase 2c: Testing (Validation of Implementation)

**Purpose**: Validate core implementation before orchestration

- [X] T010 [US1] Contract test for `SimulationConfig` schema in `tests/contract/test_simulation_config_schema.py`. **Write this test FIRST (TDD); it will fail until T006 is implemented.** Validate `sample_size_target > 0` and `random_seed` is int. **Depends on T006.**
- [X] T011 [US1] Integration test for end‑to‑end pipeline in `tests/integration/test_end_to_end_pipeline.py`. **Write this test FIRST (TDD); it will fail until T012‑T017 are implemented.** Run with inputs: ds000030, N=10, kernel=4 mm (spatial) *or* 4 s (temporal), paradigm=Motor. Assert output file `data/aggregated/power_curves.json` exists and contains `sample_sizes_tested` and `empirical_rates` (list of floats). **Depends on T012‑T017.**

**Checkpoint**: Core implementation validated

---

## Phase 3a: Power Curve Generator (US2 Core Logic)

**Purpose**: Implement the power curve generation logic

- [X] T022 [US2] Implement `code/analysis/power_curve_generator.py` to orchestrate **bootstrap iterations** per sample size (FR‑004) and support **multiple smoothing kernels** (both temporal and spatial). For each (sample size, kernel) pair, call `split_half_validator` to obtain replication successes, then compute the mean success rate → power curve point. **Also iterate over alpha thresholds `[0.01, 0.05, 0.1]` (Assumption‑Alpha) and store separate curves per alpha.** **Depends on T012‑T017, T008.**
- [X] T023 [P] Add logic in `power_curve_generator.py` to clamp requested sample size to the available data if N > original (Edge Case 2). **Depends on T022.**
- [X] T024 [US2] Implement logistic regression model in `power_curve_generator.py` using `statsmodels` with replication success as outcome and fixed effects: sample size, preprocessing variant, estimated_noise_level (from T014), and alpha. **Depends on T022, T014.**
- [X] T025 [P] Add VIF calculation in `power_curve_generator.py` to check multicollinearity (SC‑004). Log “High Collinearity” if VIF ≥ 5 and flag model result as “Invalid” in output metadata; do not halt pipeline. **Depends on T024.**
- [X] T026 [P] Implement aggregation logic to output `data/aggregated/power_curves.json` with fields `sample_sizes_tested`, `empirical_rates`, and `alpha_values`. **Depends on T022.**
- [X] T026b [P] Implement `code/utils/bootstrap_aggregator.py` to consume lists of replication results per configuration and compute empirical rates. **Called by T022.** **Depends on T022.**

**Checkpoint**: Power curve logic ready

---

## Phase 3b: Multi‑Paradigm & Alpha Sweep (US2 Orchestration)

**Purpose**: Orchestrate the power curve generation across paradigms and alpha values

- [X] T052 [US2] Implement `code/download/paradigm_loader.py` to read the list of cognitive paradigms and their associated dataset IDs from `specs/001-statistical-power-analysis/research.md`. Returns list of dicts `{ "paradigm": str, "dataset_id": str }`. Supports up to 15 paradigms (FR‑001). **Depends on T008.**
- [X] T029 [US2] Implement `code/analysis/multi_paradigm_runner.py` to loop over verified paradigms, invoke `power_curve_generator` for each, and log timing via `timer.py`. Handles alpha‑sweep internally (via T022). **Depends on T022, T052.**

**Checkpoint**: US2 complete

---

## Phase 4: User Story 3 - Preprocessing Sensitivity Analysis (Priority: P3)

**Goal**: Compare effect sizes and replication rates across different smoothing kernels.

- [X] T031 [US3] Extend `power_curve_generator.py` (via its parameter interface) to run separate loops for the two **temporal** smoothing kernels (4 s, 8 s) *and* the two **spatial** kernels (4 mm, 8 mm). This provides per‑kernel power curves. **Depends on T013 and T053.**
- [X] T031b [US3] Implement `code/analysis/temporal_sensitivity_orchestrator.py` to invoke `power_curve_generator` for each kernel variant, collect both replication rates and Cohen’s d values, and pass them to the comparison task. **Depends on T031.**
- [X] T031c [US3] Implement `code/analysis/effect_size_extractor.py` to extract Cohen’s d from each GLM fit for a given kernel. Outputs a list of effect sizes per kernel. **Depends on T016.**
- [X] T032 [US3] Implement comparison logic in `temporal_sensitivity_orchestrator.py` to calculate **absolute difference in Cohen’s d** and **difference in replication rates** between kernel pairs. Write results to `data/aggregated/sensitivity_metrics.json` with schema `[{"paradigm": str, "kernel_a": str, "kernel_b": str, "diff_cohen_d": float, "diff_replication_rate": float}]`. **Depends on T031b, T031c.**
- [X] T033 [P] Add “High Sensitivity” flag in `temporal_sensitivity_orchestrator.py` if **both** replication‑rate difference > 10 pp **or** Cohen’s d difference > 0.2 (US‑3 Scenario 2). **Depends on T032.**
- [X] T034 [P] Implement summary report generation in `results/paper/sensitivity_report.md` comparing kernel conditions. Include a Markdown table with columns: Paradigm, Cohen’s d (4 mm), Cohen’s d (8 mm), Diff (Cohen’s d), Replication Rate (4 mm), Replication Rate (8 mm), Diff (Rate), Sensitivity Flag. **Depends on T033.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T018 [US1] Implement `code/main.py` entry point to orchestrate download, preprocess, and validate for a single run configuration. **Depends on T004‑T009, T012‑T017, T022, T029.**
- [X] T035 [P] Update `README.md` with CLI usage examples and installation instructions.
- [X] T036 [P] Add docstrings to `code/main.py` and `code/analysis/power_curve_generator.py` with parameter descriptions.
- [X] T054 [P] Document CLI interface in `docs/cli.md` with command examples, arguments, and exit codes. **Replaces previous API‑endpoint doc.**
- [X] T038 [US2] Implement wall‑clock time monitoring in `code/utils/timer.py` (T038b) to log start/end times and verify execution < 6 h (SC‑005). **Output: `results/paper/timing_report.md`.** **Depends on T038b.**
- [X] T039 [P] Remove unused imports from all `code/` modules.
- [X] T040 [P] Enforce Black formatting on all `code/` and `tests/` files.
- [X] T042 [P] Add unit tests for `code/analysis/glm_fitter.py` (functions: `fit`, `predict`) and `code/analysis/split_half_validator.py` (functions: `validate`). Cover edge cases: convergence failure, N=1.
- [X] T043 [P] Implement regex filter for email/SSN patterns in logging middleware to prevent PII leakage (PRINCIPLE III). Verify via `scripts/pii_scan.sh`.
- [X] T044 [P] Run `quickstart.md` validation on GitHub Actions free‑tier. **Command:** `python code/main.py --config test_config.yaml`. Success: exit code 0, output file exists.
- [X] T041 [P] Refactor `power_curve_generator.py` to extract aggregation logic into a dedicated module (`utils/bootstrap_aggregator.py`) and expose a clean API for multi‑kernel, multi‑alpha runs. This consolidates the previously missing T041a/T041b responsibilities. **Depends on T022.**

---

## Phase 6: Data Streaming & Robustness (Critical Review Response)

**Goal**: Ensure the data loader strictly adheres to “Fail Loudly” and “Stream Real Data” rules, preventing synthetic fallbacks and handling large datasets correctly.

- [X] T048 [P] [US2] Add logging in `multi_paradigm_runner.py` to record the exact sample size used per paradigm when clamping occurs (Edge Case 2), ensuring transparency in the final report.

**Checkpoint**: Data ingestion is strictly real, streamed, and fails loudly on error.

---

## Phase 7: Execution Monitoring & Reporting (Critical Review Response)

**Goal**: Ensure all execution constraints (time, memory, convergence) are actively monitored and reported in the final artifacts.

- [X] T049 [P] [US2] Implement `code/utils/convergence_monitor.py` to parse `convergence_log.json` from T016, flag iterations where `max_iterations > 100` or `tolerance < 1e-4`, and output `results/paper/convergence_report.md` (JSON list of `{iteration_id, reason}`).
- [X] T050 [P] [US2] Update `code/utils/timer.py` (T038b) to log intermediate timing for each paradigm, sample size, and kernel, not just total run time. **Output:** `results/paper/timing_breakdown.csv`.
- [X] T051 [P] [US2] Add final validation step in `code/main.py` that checks for existence of all required output files (`power_curves.json`, `sensitivity_report.md`, timing logs, convergence report) before exiting. Exit code 1 if any are missing.

**Checkpoint**: Full observability into pipeline execution and model health.

---

## Phase 8: Final Verification & Reporting (Critical Review Response)

**Goal**: Ensure all analysis results are correctly aggregated, validated against success criteria, and formatted for the final paper.

- [X] T055 [US2] Implement `code/analysis/result_finalizer.py` to aggregate `power_curves.json`, `sensitivity_metrics.json`, `convergence_report.md`, and `timing_breakdown.csv` into a single `results/paper/final_analysis_report.md`. Include a summary table of all paradigms with their power curves (N vs Replication Rate), sensitivity flags, and convergence status. Explicitly note any paradigm that failed SC‑002 or SC‑003.
- [X] T056 [US2] Implement `scripts/validate_success_criteria.py` that reads `final_analysis_report.md` and verifies that all Success Criteria (SC‑001 to SC‑005) are met. Output `results/paper/success_criteria_status.json` with boolean flags per SC. Exit code 1 if any SC is unmet.

**Checkpoint**: Final verification complete; all success criteria validated and reported.
