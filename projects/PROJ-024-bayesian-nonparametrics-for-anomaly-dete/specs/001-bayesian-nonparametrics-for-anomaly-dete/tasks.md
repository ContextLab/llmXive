# Tasks: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Input**: Design documents from `/specs/001-bayesian-nonparametrics-for-anomaly-dete/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
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

## Phase 0: Ground Truth Simulation (FR-020)

**Purpose**: Validate the ADVI estimator's fidelity BEFORE any main inference implementation.

**⚠️ CRITICAL**: This phase MUST complete and pass validation before Phase 3 (User Story 1) begins.

- [ ] T018 [P] [US1] Create `code/src/simulation/ground_truth.py` implementing simulation study to verify $\dot{\alpha}$ SNR under null hypothesis (FR-020). **Note**: This task MUST precede T020.

**Checkpoint**: Simulation study complete; ADVI estimator validated or fallback strategy triggered.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `code/src/` directory structure: `models/`, `baselines/`, `data/`, `evaluation/`, `services/`, `simulation/`
- [ ] T005 [P] Create `data/raw/` and `data/processed/results/` directories; ensure NO `data/results/` or nested `data/raw/raw/` exist
- [ ] T006 [P] Create `state/projects/` directory for artifact hashes
- [ ] T007 [P] Initialize `code/config.yaml` with ONLY hyperparameters, seeds, and base paths (must remain <2KB)
- [ ] T008 [P] Create `code/.gitignore` excluding `__pycache__/`, `*.pyc`, `*.log` (except `logs/elbo/`)
- [ ] T009 [P] Create `specs/contracts/` directory and define all schema YAML files (`dataset.schema.yaml`, `anomaly_score.schema.yaml`, etc.)
- [ ] T010 [P] Implement `code/src/services/state_update.py` to compute and record SHA256 hashes for synthetic generator and windowing logic
- [ ] T011 [P] Create `code/src/utils/checksums.py` for recording and verifying data artifacts in state file
- [ ] T012 [P] Create `data/data-dictionary.md` documenting UCI dataset sources, licenses, and access dates (Electricity, Traffic, Synthetic Control Chart only)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core DPGMM Training and Dynamic Signature Extraction (Priority: P1) 🎯 MVP

**Goal**: Implement stick-breaking DP-GMM with ADVI, extract $\dot{\alpha}$ and weight variance, validate against ground truth simulation

**Independent Test**: Load synthetic dataset with injected anomalies, run sliding window inference, verify output includes time-series of posterior mean $\alpha$, its first derivative, and component weight variance for every window step.

**⚠️ EXECUTION ORDER**: T021 (Windowing) MUST precede T019 and T020. T018 (Phase 0) MUST precede T020.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Contract test for `AnomalyDetectorService` SCHEMA in `code/tests/contract/test_anomaly_detector_schema.py` (Depends on T009, NOT T022)
- [ ] T014 [P] [US1] Contract test for `DPGMM` model schema in `code/tests/contract/test_dpgmm_schema.py`
- [ ] T015 [P] [US1] Integration test for sliding window inference and derivative extraction in `code/tests/integration/test_streaming_update.py`
- [ ] T016 [P] [US1] Unit test for ADVI convergence check and exclusion logic in `code/tests/unit/test_advi_convergence.py`
- [ ] T017 [P] [US1] Unit test for bootstrap resampling logic when anomaly count <10 in `code/tests/unit/test_bootstrap_fallback.py`

### Implementation for User Story 1

- [ ] T019 [P] [US1] Create `code/src/data/synthetic_generator.py` generating datasets with pre-anomaly dynamics, abrupt shifts, and independent ground-truth timestamps (FR-021, FR-022). **Note**: Used for simulation and as fallback if real data search fails.
- [ ] T020 [US1] Create `code/src/models/dpgmm.py` implementing stick-breaking DP-GMM using PyMC 4 and ADVI variational inference. **Constraint**: MUST use the stick-breaking construction (Sethuraman, 1994) to ensure nonparametric behavior, NOT a fixed-k approximation.
- [ ] T021 [US1] Implement `code/src/data/windowing.py` for sliding window extraction (length=30, stride=1) with normalization. **Order**: Must be completed before T019 and T020.
- [ ] T022 [US1] Implement `code/src/services/anomaly_detector.py` with a modular set of methods including `__init__`, `load_model`, `process_stream`, `update_model`, `compute_score`, `get_uncertainty`, and `save_checkpoint`.
- [ ] T023 [US1] Implement logic to track posterior mean $\alpha$ and $\pi$ at each window step and compute first derivative $\dot{\alpha}$
- [ ] T024 [US1] Implement exclusion logic for non-convergent ADVI runs (ELBO delta >0.01 for 10 iterations within 500 iterations) per FR-009
- [ ] T025 [US1] Implement bootstrap resampling procedure for p-values and confidence intervals when anomaly count <10 (FR-011, FR-012)
- [ ] T026 [US1] Implement MCMC (NUTS) robustness check on a subset of windows to validate $\dot{\alpha}$ is not an ADVI artifact (FR-018)
- [ ] T027 [US1] Create `code/src/evaluation/metrics.py` implementing Kolmogorov-Smirnov test for distributional differences (FR-010, FR-014, FR-015)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Comparison and Time-to-Detection Analysis (Priority: P2)

**Goal**: Compute reconstruction errors from fixed GMMs and ARIMA, calculate time-to-detection, perform statistical comparisons

**Independent Test**: Run baseline models and DP-GMM on same data, compute time-to-detection, verify DP-GMM detects anomaly significantly earlier (statistically significant difference) than baselines.

### Tests for User Story 2 (MANDATORY) ⚠️

- [ ] T028 [P] [US2] Contract test for `EvaluationMetrics` schema in `code/tests/contract/test_metrics_schema.py`
- [ ] T029 [P] [US2] Integration test for baseline comparison and time-to-detection calculation in `code/tests/integration/test_baseline_comparison.py`
- [ ] T030 [P] [US2] Unit test for Wilcoxon signed-rank test and paired t-test sensitivity check in `code/tests/unit/test_statistical_tests.py`

### Implementation for User Story 2

- [ ] T031 [P] [US2] Create `code/src/baselines/gmm_fixed.py` implementing fixed-component GMMs (k=3, 5, 10) for reconstruction error
- [ ] T032 [P] [US2] Create `code/src/baselines/arima.py` implementing ARIMA model for reconstruction error
- [ ] T033 [US2] Implement `code/src/evaluation/metrics.py` functions for time-to-detection calculation against independent ground-truth timestamps (FR-013)
- [ ] T034 [US2] Implement Wilcoxon signed-rank test on time-to-detection values; add paired t-test as secondary check only if normality assumptions met (FR-006)
- [ ] T035 [US2] Implement KS test comparing baseline reconstruction error distribution against DP-GMM signature distribution on normalized scores (FR-015)
- [ ] T036 [US2] Implement KS test comparing "rate of change" metrics between anomaly and negative control (gradual drift) windows (FR-014)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Justification and Sensitivity Analysis (Priority: P3)

**Goal**: Implement threshold sensitivity analysis, validate robustness, ensure nested validation to prevent data-dredging

**Independent Test**: Run detection logic with three distinct threshold values on held-out test set, verify output includes table showing variation in FP/FN rates.

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T037 [P] [US3] Contract test for `ThresholdCalibratorService` methods in `code/tests/contract/test_threshold_calibrator_schema.py`
- [ ] T038 [P] [US3] Integration test for threshold sensitivity sweep and nested validation in `code/tests/integration/test_threshold_calibration.py`
- [ ] T039 [P] [US3] Unit test for Bonferroni correction application in statistical tests (FR-007b)

### Implementation for User Story 3

- [ ] T040 [P] [US3] Create `code/src/services/threshold_calibrator.py` with a set of methods including `__init__`, `calibrate`, `validate_threshold`, `get_decision_boundary`, `update_decision_boundary`, and `compute_expected_bounds`.
- [ ] T041 [US3] Implement `code/src/evaluation/threshold_sweep.py` to sweep cutoffs over a range of low to moderate values on normalized reconstruction error (FR-007)
- [ ] T042 [US3] Implement logic to split data into train/validation/test sets; select threshold on validation set, apply to held-out test set (FR-019)
- [ ] T043 [US3] Implement Bonferroni correction for multiple comparisons specifically when using threshold-swept outcomes in statistical tests (FR-007b). **Constraint**: Do NOT apply generically; only when threshold-swept outcomes are used.
- [ ] T044 [US3] Implement sensitivity analysis on window size and derivative calculation method (including smoothing and lag variations) to validate robustness (FR-016)
- [ ] T045 [US3] Implement logic to flag threshold instability when error rates spike in sensitivity report (FR-007)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Resource Constraint Validation and CPU Feasibility (Priority: P3)

**Goal**: Validate pipeline runs within GitHub Actions free-tier constraints (≤2 CPU, 7 GB RAM, 6 hours)

**Independent Test**: Execute full pipeline on standard GitHub Actions runner, verify peak memory <7 GB and runtime <6 hours.

### Tests for User Story 4 (MANDATORY) ⚠️

- [ ] T046 [P] [US4] Unit test for memory profiling using `psutil` to measure peak RSS
- [ ] T047 [P] [US4] Unit test for runtime measurement and timeout enforcement

### Implementation for User Story 4

- [ ] T048 [P] [US4] Create `code/src/utils/memory_profiler.py` using `psutil.Process().memory_info().rss` to track peak RAM
- [ ] T049 [US4] Implement `code/src/services/anomaly_detector.py` resource validation logic: measure peak RAM and total runtime, fail run if limits exceeded (FR-008)
- [ ] T050 [US4] Create `code/scripts/verify_resource_compliance.py` to enforce CPU-only execution and validate no CUDA library loading
- [ ] T051 [US4] Implement logic to generate resource validation report outputting peak RAM and runtime metrics

**Checkpoint**: Resource constraints validated - pipeline is CPU-feasible

---

## Phase 7: Data Acquisition and Provenance (Critical Path)

**Goal**: Execute search procedure for real-world datasets; fetch only if verified; generate Deferred report if not found.

**⚠️ CRITICAL ORDER**: T052b (Search) MUST precede T052 (Fetch). T052 is conditional on T052b success.

- [ ] T052b [P] [Data] Execute mandatory search procedure for real-world datasets with verified regime shifts (FR-017). Search UCI, PhysioNet, etc. If no verified source is found, flag for T052c.
- [ ] T052 [Data] **Conditional on T052b success**: Create `code/src/data/download_datasets.py` fetching UCI Electricity Load Diagrams, Traffic, and Synthetic Control Chart via `ucimlrepo` or verified URLs. **Do NOT execute if T052b failed.**
- [ ] T053 [Data] Verify all downloaded datasets have ≥1,000 observations; reject dataset if insufficient size (FR-001). **Conditional on T052 execution.**
- [ ] T054 [Data] Delete all PEMS-SF files (`pems_sf.csv`, `pems_sf_synthetic.csv`) from `data/raw/`
- [ ] T055 [Data] Flatten `data/raw/raw/` directory: move all files to `data/raw/` and remove nested directory
- [ ] T056 [Data] Delete legacy `data/results/` directory and migrate all contents to `data/processed/results/`
- [ ] T057 [Data] Generate SHA256 checksums for all raw data files and record in `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`
- [ ] T058 [Data] **Conditional on T052b success**: Update `data/data-dictionary.md` to list only 3 UCI datasets with explicit license terms and URLs. **If T052b failed, update to note 'Deferred by Design' per FR-017b.**
- [ ] T059 [Data] Implement `code/src/data/download_datasets.py` verification logic to check dataset integrity against checksums before processing
- [ ] T052c [Data] **Conditional on T052b failure**: Generate 'Validation Deferred' report citing search query and result count, mark requirement as 'Deferred by Design' (FR-017b).

**Checkpoint**: Data hygiene established - only compliant UCI datasets present with verified checksums OR Deferred report generated.

---

## Phase 8: Configuration and Filesystem Hygiene (Critical Path)

**Goal**: Ensure config.yaml <2KB, correct file locations, complete documentation

- [ ] T060 [P] [Config] Migrate all derived statistics from `code/config.yaml` to `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`
- [ ] T060b [Config] **Explicit Migration**: Migrate the derived statistics (keys: `dataset_stats`, `inference_results`, `simulation_metrics`) from `code/config.yaml` to `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml` using `code/src/utils/migrate_config.py`. Verify removal from config.yaml.
- [ ] T061 [Config] Verify `code/config.yaml` size <2048 bytes using `os.path.getsize()`; fail if exceeded (FR-009)
- [ ] T062 [Config] Create `code/scripts/verify_config_compliance.py` with explicit size check and error exit code
- [ ] T063 [FS] Move all Python source files from `code/` root to `code/src/` subdirectories (models/, baselines/, data/, evaluation/, services/, utils/, simulation/)
- [ ] T064 [FS] Update all imports in `code/src/` files to reflect new package structure
- [ ] T065 [FS] Create `README.md` at repository root with usage instructions for DPGMM and baselines
- [ ] T066 [FS] Create `LICENSE` file (MIT) at repository root
- [ ] T067 [FS] Verify `code/.gitignore` includes `__pycache__/`, `*.pyc`, `*.egg-info/`
- [ ] T068 [FS] Create `logs/elbo/` directory for ELBO convergence logs per Constitution Principle VI
- [ ] T069 [FS] Verify `code/src/` contains NO files at root level; run `find code/ -maxdepth 1 -name "*.py"` and ensure empty
- [ ] T070 [FS] Verify `data/raw/` contains NO nested `raw/` directories; run `find data/raw/ -type d -name raw` and ensure empty
- [ ] T071 [FS] Verify `data/` contains NO `results/` directory; run `ls -la data/ | grep results` and ensure only `processed/results/` exists
- [ ] T072 [FS] Verify no PEMS-SF files exist in `data/raw/`; run `grep -r "pems" data/raw/` and ensure empty

**Checkpoint**: Filesystem hygiene and config compliance verified

---

## Phase 9: Testing Infrastructure and Coverage (Critical Path)

**Goal**: Implement and verify contract, integration, and unit tests with ≥80% coverage

- [ ] T073 [P] [Test] Create `code/tests/unit/test_advi_convergence.py`
- [ ] T074 [P] [Test] Create `code/tests/unit/test_bootstrap_fallback.py`
- [ ] T075 [P] [Test] Create `code/tests/unit/test_statistical_tests.py`
- [ ] T076 [P] [Test] Create `code/tests/unit/test_memory_profile.py`
- [ ] T077 [P] [Test] Create `code/tests/contract/test_anomaly_detector_schema.py`
- [ ] T078 [P] [Test] Create `code/tests/contract/test_dpgmm_schema.py`
- [ ] T079 [P] [Test] Create `code/tests/contract/test_metrics_schema.py`
- [ ] T080 [P] [Test] Create `code/tests/contract/test_threshold_calibrator_schema.py`
- [ ] T081 [P] [Test] Create `code/tests/contract/test_threshold_schema.py`
- [ ] T082 [P] [Test] Create `code/tests/integration/test_streaming_update.py`
- [ ] T083 [P] [Test] Create `code/tests/integration/test_baseline_comparison.py`
- [ ] T084 [P] [Test] Create `code/tests/integration/test_threshold_calibration.py`
- [ ] T085 [Test] Run `pytest --cov=code/src --cov-report=term-missing` and verify ≥80% line coverage
- [ ] T086 [Test] Create `code/tests/test_report.md` documenting pass/fail status per test file and coverage metrics
- [ ] T087 [Test] Fix any failing tests to achieve [deferred] pass rate
- [ ] T088 [Test] Re-run coverage analysis and confirm ≥80% threshold met

**Checkpoint**: Test infrastructure complete and verified

---

## Phase 10: Reporting and Compliance (Final Gate)

**Goal**: Generate final reports, validate all requirements, execute final acceptance

- [ ] T089 [Report] Generate `data/processed/results/simulation_validation.csv` with SNR metrics from Phase 0 (FR-020)
- [ ] T090 [Report] Generate `data/processed/results/posterior_trajectory.csv` with $\dot{\alpha}$ and weight variance trajectories
- [ ] T091 [Report] Generate `data/processed/results/statistical_report.csv` with KS tests, Wilcoxon tests, bootstrap p-values
- [ ] T092 [Report] Generate `data/processed/results/sensitivity_report.md` with threshold sweep results and instability flags
- [ ] T093 [Report] Generate `data/processed/results/final_report.md` including methodology, results, fallback status, and "Deferred by Design" note if real-world data search fails (FR-017b)
- [ ] T094 [Report] Generate `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml` with all artifact hashes and dataset checksums
- [ ] T095 [Compliance] Run `code/scripts/verify_config_compliance.py` and capture output in `code/tests/config_compliance_report.md`
- [ ] T096 [Compliance] Run `code/scripts/verify_resource_compliance.py` and capture output in `data/processed/results/resource_validation_report.md`
- [ ] T097 [Compliance] Verify all UCI datasets present with checksums in state file; generate `data/sample_size_report.md` confirming ≥1000 observations each (or Deferred report if applicable)
- [ ] T098 [Compliance] Run `find data/raw/ -type f -name "*.csv"` and verify only Electricity, Traffic, Synthetic Control Chart present; output to `data/data_provenance_report.md` (or Deferred status)
- [ ] T099 [Compliance] Run `ls -la code/src/` and verify correct subdirectory structure; output to `code/src_structure_report.md`
- [ ] T100 [Compliance] Execute T145 Final Acceptance: verify all [X] tasks have no FAILED-IN-EXECUTION comments, all filesystem hygiene checks pass, all tests pass, all reports generated

**Checkpoint**: All success criteria met - project ready for `research_complete` stage

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Ground Truth Simulation)**: No dependencies - MUST complete before Phase 3.
- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3-6)**: All depend on Phase 0 and Phase 2 completion.
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Data Acquisition (Phase 7)**: MUST complete before Phase 3 (User Story 1) implementation. **T052b (Search) MUST precede T052 (Fetch).**
- **Hygiene (Phase 8)**: Must complete before Final Acceptance (T100)
- **Testing (Phase 9)**: Tests written in Phases 3-6 must be executed and verified in Phase 9
- **Reporting (Phase 10)**: Depends on all previous phases; final gate before `research_complete`

### User Story Dependencies

- **User Story 1 (P1)**: Requires Phase 0, Phase 2, and Phase 7 (Data Acquisition).
- **User Story 2 (P2)**: Requires Phase 3 (US1) completion for baseline comparison.
- **User Story 3 (P3)**: Requires Phase 4 (US2) completion for threshold calibration.
- **User Story 4 (P3)**: Can run in parallel with US2/US3 but requires full pipeline execution.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Phase 0, Phase 2, and Phase 7 complete, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for AnomalyDetectorService schema in code/tests/contract/test_anomaly_detector_schema.py"
Task: "Integration test for sliding window inference in code/tests/integration/test_streaming_update.py"

# Launch all models for User Story 1 together:
Task: "Create DP-GMM model in code/src/models/dpgmm.py (stick-breaking)"
Task: "Create synthetic generator in code/src/data/synthetic_generator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Ground Truth Simulation (CRITICAL - validates metric)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 7: Data Acquisition (Search first, then Fetch or Deferred)
5. Complete Phase 3: User Story 1
6. **STOP and VALIDATE**: Test User Story 1 independently

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational + Data Acquisition → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Validate resource constraints
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational + Data Acquisition together
2. Once Foundation ready:
   - Developer A: User Story 1 (DPGMM core)
   - Developer B: User Story 2 (Baselines)
   - Developer C: User Story 3 (Thresholds)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: All PEMS-SF files must be removed; only UCI datasets allowed (or Deferred report)
- **CRITICAL**: All source files must be under `code/src/`
- **CRITICAL**: `config.yaml` must be <2KB (migrate ~8KB stats to state file)
- **CRITICAL**: No legacy `data/results/` or nested `data/raw/raw/` directories
- **CRITICAL**: Phase 7 (Data Acquisition) MUST complete before Phase 3. T052b (Search) MUST precede T052 (Fetch).
- **CRITICAL**: T018 (Simulation) MUST complete before T020 (DPGMM).
- **CRITICAL**: T021 (Windowing) MUST precede T019 and T020.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence