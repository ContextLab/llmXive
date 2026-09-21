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

- [ ] T001a [P] Create directory `code/`, `code/download/`, `code/preprocess/`, `code/simulation/`, `code/analysis/`, `code/models/`, `code/utils/`. **Create `__init__.py` in each to form valid Python packages.**
- [ ] T001b [P] Create directory `tests/`, `tests/contract/`, `tests/integration/`, `tests/unit/`. **Create `__init__.py` in each.**
- [ ] T001c [P] Create directory `data/`, `data/raw/`, `data/derived/`, `data/aggregated/`.
- [ ] T001d [P] Create directory `results/`, `results/paper/`.

- [ ] T002 [P] Initialize Python 3.11 project with `requirements.txt` (bidslib, nibabel, nilearn, scikit-learn, statsmodels, pandas, numpy, mne, datasets). **Depends on T001a.**
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`. **Depends on T001a.**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 [P] Implement `code/utils/seed_manager.py` to enforce fixed random seeds for reproducibility (PRINCIPLE I).
- [ ] T005 [P] Implement `code/utils/memory_monitor.py` to track RAM usage and trigger downsampling if >6GB (FR-006).
- [ ] T006 [P] Create `code/models/simulation_config.py` defining `SimulationConfig` entity (sample_size_target, smoothing_kernel, num_iterations, random_seed). **Depends on T005.**
- [ ] T007 [P] Create `code/models/replication_result.py` defining `ReplicationResult` entity (effect_size_est, p_value, replication_success, smoothing_kernel_used). **Depends on T006.**
- [ ] T008 [P] [US1] Implement `code/download/openneuro_fetcher.py` to download raw BIDS data for **5 verified datasets** (ds000030, ds000248, ds000250, ds000251, ds000252). **Must use `datasets.load_dataset(..., streaming=True)` for datasets >1GB (chunk_size=1GB, iterator strategy).** **Must explicitly `raise ValueError("Real data fetch failed. Aborting.")` on failure; NO synthetic fallback.** **Must validate against the hardcoded whitelist of 5 IDs before fetching.** **Depends on T005.**
- [ ] T009 [P] Implement `code/download/data_validator.py` to verify BIDS structure and checksum raw NIfTI files; skip corrupted subjects and log warnings. **CRITICAL**: If valid subjects < 5, raise error with code 1 and log "Insufficient Data" (Edge Case 1). **Depends on T008.**
- [ ] T010 [P] [US1] Contract test for `SimulationConfig` schema in `tests/contract/test_simulation_config_schema.py`. **Write this test FIRST (TDD); it will fail until T006 is implemented.** **Validate against `code/models/simulation_config.py`; verify `sample_size_target > 0` and `random_seed` is int.**
- [ ] T011 [P] [US1] Integration test for end-to-end pipeline in `tests/integration/test_end_to_end_pipeline.py`. **Write this test FIRST (TDD); it will fail until T012-T017 are implemented.** **Run with inputs: ds000030, N=10, kernel=4mm. Assert output file `data/aggregated/power_curves.json` exists and contains `sample_sizes_tested` and `empirical_rates` (list of floats).**
- [ ] T012 [P] [US1] Implement `code/preprocess/roi_extractor.py` to extract ROI time-series from raw BIDS data (CPU-tractable substitute for fMRIPrep). **Must support real data input.**
- [ ] T013 [P] [US1] Implement `code/preprocess/temporal_smoothing.py` to apply **temporal** smoothing kernels to 1D ROI time-series. **Required by FR-002 (adapted); distinct from spatial smoothing.** **Mapping: 4mm spatial [deferred] -> 4s temporal (TR=2s), 8mm spatial [deferred] -> 8s temporal (TR=2s).**
- [ ] T013b [P] [US1] Implement `code/preprocess/traceability_logger.py` to log the specific **Custom ROI Pipeline** version, parameters (ROI mask, temporal kernel size), and GLM configuration to `results/paper/pipeline_config.json`. **Must explicitly state fMRIPrep is NOT used.** **Depends on T012/T013.**
- [ ] T014 [P] [US1] Implement `code/simulation/noise_estimator.py` to estimate noise characteristics from **real** preprocessed data for GLM modeling. **Remove all references to 'synthetic generation'.**
- [ ] T016 [P] [US1] Implement `code/analysis/glm_fitter.py` to fit GLM on **real** preprocessed data (post-temporal smoothing) and estimate effect size (Cohen's d).
- [ ] T017 [P] [US1] Implement `code/analysis/split_half_validator.py` to partition **real** data into train/test sets, test significance on held-out set, and determine replication success. **Replication success = direction match AND magnitude within ±20% (0.8x-1.2x) of training estimate.** (FR-003)
- [ ] T018 [P] [US1] Implement `code/main.py` entry point to orchestrate download, preprocess, and validate for a single run configuration. **Depends on T004-T009, T012-T017, T022.**
- [ ] T019 [P] [US1] Add error handling in `code/analysis/split_half_validator.py` to discard failed GLM iterations and flag "Unreliable" if failure rate >20% (Edge Case 3).
- [ ] T038b [P] [Shared] Implement `code/utils/timer.py` to provide `start_run`, `end_run`, and `log_split` methods for wall-clock time monitoring (SC-005). **Output: `results/paper/timing_report.md` and `results/paper/timing_breakdown.csv`.** **Depends on T004.**
- [ ] T050 [P] [US2] Update `code/utils/timer.py` (T038b) to log intermediate timing for each paradigm and sample size, not just the total run time. **Output: `results/paper/timing_breakdown.csv`.** **Depends on T038b.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducibility Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Execute end-to-end pipeline (download → preprocess → model → validate) on a single dataset with fixed sample size.

**Independent Test**: Run pipeline on `ds000030` (N=10) and verify binary replication result (0/1) without crashing or GPU usage.

### Implementation for User Story 1

- [ ] T022 [P] [US2] Implement `code/analysis/power_curve_generator.py` to orchestrate multiple bootstrap iterations per sample size (FR-004) and support multiple smoothing kernels. **Depends on T012-T017, T008.**
- [ ] T023 [P] [US2] Implement logic in `code/analysis/power_curve_generator.py` to clamp requested sample size to available data if N > original (Edge Case 2).
- [ ] T024 [P] [US2] Implement logistic regression model in `code/analysis/power_curve_generator.py` using `statsmodels` (CPU-optimized) with replication success as outcome (FR-005).
- [ ] T025 [P] [US2] Add VIF (Variance Inflation Factor) calculation in `code/analysis/power_curve_generator.py` to check for multicollinearity (SC-004). **Log 'High Collinearity' if VIF >= 5; do NOT fail pipeline.**
- [ ] T026 [P] [US2] Implement aggregation logic to output `data/aggregated/power_curves.json` with `sample_sizes_tested` and `empirical_rates`.
- [ ] T027 [P] [US2] Apply **Benjamini-Hochberg FDR** multiple-comparison correction to final model results across the **5 MVP paradigms** (Spec Assumption: Power Correction). **Output: `data/aggregated/corrected_power_curves.json`.**
- [ ] T029 [P] [US2] Implement `code/analysis/multi_paradigm_runner.py` to orchestrate the power curve generation loop across the 5 distinct cognitive paradigms (Motor, Working Memory, Emotional Face, Auditory Oddball, Visual Motion). **Must call T038b/T050 timer logging methods during the loop.** **Depends on T022.**
- [ ] T028 [P] [US2] Implement alpha-sweep sensitivity analysis (alpha values: [0.01, 0.05, 0.1]) and generate `results/paper/alpha_sensitivity_report.md`. **Must iterate across the 5 distinct cognitive paradigms (Motor, Working Memory, Emotional Face, Auditory Oddball, Visual Motion) as defined in `plan.md`.** **Depends on T029.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Preprocessing Sensitivity Analysis (Priority: P3)

**Goal**: Compare effect sizes and replication rates across different smoothing kernels.

**Independent Test**: Run analysis with 4mm and 8mm kernels and verify output reports two different effect sizes and a difference metric.

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement parameter injection in `code/analysis/power_curve_generator.py` (via T022) to run separate loops for different **temporal** smoothing kernels (4mm, 8mm). **Kernel support is native to T022.** **Mapping: 4mm spatial [deferred] -> 4s temporal (TR=2s), 8mm spatial [deferred] -> 8s temporal (TR=2s).**
- [ ] T032 [P] [US3] Implement comparison logic in `code/analysis/power_curve_generator.py` to calculate absolute difference in Cohen's d and replication rates (SC-003).
- [ ] T033 [P] [US3] Add "High Sensitivity" flag in `code/analysis/power_curve_generator.py` if replication rate difference >10 percentage points (US-3 Scenario 2).
- [ ] T034 [P] [US3] Implement summary report generation in `results/paper/sensitivity_report.md` comparing 4mm vs 8mm results.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Update `README.md` with CLI usage examples and installation instructions.
- [ ] T036 [P] Add docstrings to `code/main.py` and `code/analysis/power_curve_generator.py` with parameter descriptions.
- [ ] T037 [P] Document API endpoints in `docs/api.md` with request/response examples.
- [ ] T038 [P] [US2] Implement wall-clock time monitoring in `code/utils/timer.py` (T038b) to log start/end times and verify execution < 6 hours (SC-005). **Output: `results/paper/timing_report.md`.** **Depends on T038b.**
- [ ] T039 [P] Remove unused imports from all `code/` modules.
- [ ] T040 [P] Enforce Black formatting on all `code/` and `tests/` files.
- [ ] T041a [P] Extract bootstrap loop logic in `code/analysis/power_curve_generator.py` into `code/utils/bootstrap_runner.py`. **Function name: `run_bootstrap_iterations`.**
- [ ] T041b [P] Extract aggregation logic in `code/analysis/power_curve_generator.py` into `code/utils/aggregation_utils.py`. **Function name: `aggregate_power_results`.**
- [ ] T042 [P] Add unit tests for `code/analysis/glm_fitter.py` (functions: fit, predict) and `code/analysis/split_half_validator.py` (functions: validate). **Cover edge cases: convergence failure, N=1.**
- [ ] T043 [P] Implement regex filter for email/SSN patterns in logging middleware to prevent PII leakage (PRINCIPLE III). **Verify by running `scripts/pii_scan.sh`.**
- [ ] T044 [P] Run `quickstart.md` validation on GitHub Actions free-tier. **Command: `python code/main.py --config test_config.yaml`. Success: exit code 0, output file exists.**

---

## Phase 6: Data Streaming & Robustness (Critical Review Response)

**Goal**: Ensure the data loader strictly adheres to "Fail Loudly" and "Stream Real Data" rules, preventing synthetic fallbacks and handling large datasets correctly.

**Independent Test**: Verify that `code/download/openneuro_fetcher.py` raises an exception on missing data and uses `streaming=True` for large datasets.

### Implementation for Robustness

- [ ] T048 [P] [US2] Add a task to `code/analysis/multi_paradigm_runner.py` that logs the exact sample size used per paradigm if clamping occurred (Edge Case 2), ensuring transparency in the final report.

**Checkpoint**: Data ingestion is strictly real, streamed, and fails loudly on error.

---

## Phase 7: Execution Monitoring & Reporting (Critical Review Response)

**Goal**: Ensure all execution constraints (time, memory, convergence) are actively monitored and reported in the final artifacts.

**Independent Test**: Verify that `results/paper/timing_report.md` and `results/paper/convergence_report.md` are generated and contain valid data.

### Implementation for Monitoring

- [ ] T049 [P] [US2] Implement `code/utils/convergence_monitor.py` to track GLM convergence status across all bootstrap iterations. **Convergence Failure Criteria: max iterations > 100 OR tolerance < 1e-4.** **Output: `results/paper/convergence_report.md` listing any failed iterations and their causes (format: JSON list of {iteration_id, reason}).**
- [ ] T051 [P] [US2] Add a final validation step in `code/main.py` that checks if all required output files (power curves, sensitivity reports, timing logs) exist before exiting. **Exit with code 1 if any are missing.**

**Checkpoint**: Full observability into pipeline execution and model health.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Robustness (Phase 6)**: Must be completed before final data ingestion runs.
- **Monitoring (Phase 7)**: Must be completed before final execution run.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 components (GLM, Split-Half) and T029 (Multi-Paradigm)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 components

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase 6 (Robustness) and Phase 7 (Monitoring) can be implemented in parallel with Phase 3-5.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Monitoring (Phase 7) → Ensure full observability
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D: Robustness (Phase 6) & Monitoring (Phase 7)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Rule**: Never use synthetic data as a fallback. If real data fetch fails, the pipeline must crash with a clear error.
- **Critical Rule**: Always stream large datasets; never load them entirely into memory.
- **Critical Rule**: Adhere strictly to the 5-dataset MVP scope defined in plan.md.