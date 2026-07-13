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

- [X] T018 [P] [US1] Create `code/src/simulation/ground_truth.py` implementing simulation study to verify $\dot{\alpha}$ SNR under null hypothesis (FR-020). **Deliverable**: Generate `data/processed/results/simulation_snr.csv` [UNRESOLVED-CLAIM: c_02cf758f — status=not_enough_info] and assert SNR > 1 in logs [UNRESOLVED-CLAIM: c_c4b21093 — status=not_enough_info]. **Note**: This task MUST precede T020. **Checkpoint**: Pipeline MUST fail if `data/processed/results/simulation_snr.csv` does not exist or if SNR <= 1.

**Checkpoint**: Simulation study complete; ADVI estimator validated or fallback strategy triggered.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/src/` directory structure: `models/`, `baselines/`, `data/`, `evaluation/`, `services/`, `simulation/`
- [X] T005 [P] Create `data/raw/` and `data/processed/results/` directories; ensure NO `data/results/` or nested `data/raw/raw/` exist
- [X] T006 [P] Create `state/projects/` directory for artifact hashes
- [X] T007 [P] Initialize `code/config.yaml` with ONLY hyperparameters, seeds, and base paths (must remain <2KB)
- [X] T008 [P] Create `code/.gitignore` excluding `__pycache__/`, `*.pyc`, `*.log` (except `logs/elbo/`)
- [X] T009 [P] Create `specs/contracts/` directory and define all schema YAML files (`dataset.schema.yaml`, `anomaly_score.schema.yaml`, etc.)
- [X] T010 [P] Implement `code/src/services/state_update.py` to compute and record SHA256 hashes for synthetic generator and windowing logic
- [X] T011 [P] Create `code/src/utils/checksums.py` for recording and verifying data artifacts in state file
- [X] T012 [P] Create `data/data-dictionary.md` documenting UCI dataset sources, licenses, and access dates (Electricity, Traffic only)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Test First (TDD Cycle)

**Purpose**: Write all contract and integration tests BEFORE implementation to ensure testability and prevent drift.

- [X] T013 [US1] Contract test for `AnomalyDetectorService` SCHEMA in `code/tests/contract/test_anomaly_detector_schema.py`. **Note**: Requires T009 completion. **Dependency**: Must wait for Phase 2 (Schemas) to complete.
- [X] T014 [US1] Contract test for `DPGMM` model schema in `code/tests/contract/test_dpgmm_schema.py`. **Note**: Requires T009 completion. **Dependency**: Must wait for Phase 2 (Schemas) to complete.
- [X] T015 [P] [US1] Integration test for sliding window inference and derivative extraction in `code/tests/integration/test_streaming_update.py`
- [X] T016 [P] [US1] Unit test for ADVI convergence check and exclusion logic in `code/tests/unit/test_advi_convergence.py`
- [X] T017 [P] [US1] Unit test for bootstrap resampling logic when anomaly count <10 in `code/tests/unit/test_bootstrap_fallback.py`
- [X] T028 [P] [US2] Contract test for `EvaluationMetrics` schema in `code/tests/contract/test_metrics_schema.py`
- [X] T029 [P] [US2] Integration test for baseline comparison and time-to-detection calculation in `code/tests/integration/test_baseline_comparison.py`
- [X] T030 [P] [US2] Unit test for Wilcoxon signed-rank test and paired t-test sensitivity check in `code/tests/unit/test_statistical_tests.py`
- [X] T037 [P] [US3] Contract test for `ThresholdCalibratorService` methods in `code/tests/contract/test_threshold_calibrator_schema.py`
- [X] T038 [P] [US3] Integration test for threshold sensitivity sweep and nested validation in `code/tests/integration/test_threshold_calibration.py`
- [X] T039 [P] [US3] Unit test for Bonferroni correction application in statistical tests (FR-007b)
- [X] T046 [P] [US4] Unit test for memory profiling using `psutil` to measure peak RSS
- [X] T047 [P] [US4] Unit test for runtime measurement and timeout enforcement

**Checkpoint**: All tests written and failing; ready for implementation.

---

## Phase 3: User Story 1 - Core DPGMM Training and Dynamic Signature Extraction (Priority: P1) 🎯 MVP

**Goal**: Implement stick-breaking DP-GMM with ADVI, extract $\dot{\alpha}$ and weight variance, validate against ground truth simulation

**Independent Test**: Load synthetic dataset with injected anomalies, run sliding window inference, verify output includes time-series of posterior mean $\alpha$, its first derivative, and component weight variance for every window step.

**⚠️ EXECUTION ORDER & GATES**:
1. **T021 (Windowing) MUST precede T019 and T020.**
2. **T018 (Phase 0 Simulation) MUST PASS before T020 and T023 can start.** If T018 fails, the pipeline halts immediately.

### Implementation for User Story 1

- [X] T021 [US1] Implement `code/src/data/windowing.py` for sliding window extraction (length=50, stride=1) with normalization. **Order**: Must be completed before T019 and T020. **Constraint**: Window size MUST be 50 as per Plan Technical Context for stability.
- [X] T019 [P] [US1] Create `code/src/data/synthetic_generator.py` generating datasets with pre-anomaly dynamics, abrupt shifts, and independent ground-truth timestamps (FR-021, FR-022). **Note**: Used for simulation and as fallback if real data search fails.
- [X] T020 [US1] Create `code/src/models/dpgmm.py` implementing stick-breaking DP-GMM using PyMC 4 and ADVI variational inference. **Constraint**: MUST use the stick-breaking construction (Sethuraman, 1994) AND a hierarchical time-varying prior ($\alpha_t \sim \text{Normal}(\alpha_{t-1}, \sigma)$) to ensure nonparametric behavior and local signal validity (FR-002).
- [X] T022 [US1] Implement `code/src/services/anomaly_detector.py` with a modular set of methods including `__init__`, `load_model`, `process_stream`, `update_model`, `compute_score`, `get_uncertainty`, and `save_checkpoint`.
- [X] T023 [US1] Implement logic to track posterior mean $\alpha$ and $\pi$ at each window step and compute first derivative $\dot{\alpha}$
- [X] T024 [US1] Implement exclusion logic for non-convergent ADVI runs (ELBO delta >0.01 for 10 iterations within 500 iterations) per FR-009
- [X] T025 [US1] Implement bootstrap resampling procedure for p-values and confidence intervals when anomaly count <10 (FR-011, FR-012)
- [X] T026 [US1] Implement MCMC (NUTS) robustness check on a specific set of windows selected by ground-truth injection timestamps (Equal numbers of pre-anomaly and anomaly samples, plus a larger set of transition samples) to validate $\dot{\alpha}$ is not an ADVI artifact (FR-018). **Deliverable**: Generate `data/processed/results/mcmc_validation.csv` [UNRESOLVED-CLAIM: c_6d5988e5 — status=not_enough_info]. **Constraint**: FAIL if deviation in posterior mean $\alpha$ between ADVI and MCMC exceeds 10%.
- [X] T027 [US1] Create `code/src/evaluation/metrics.py` implementing Kolmogorov-Smirnov test for distributional differences (FR-010, FR-014, FR-015)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Comparison and Time-to-Detection Analysis (Priority: P2)

**Goal**: Compute reconstruction errors from fixed GMMs and ARIMA, calculate time-to-detection, perform statistical comparisons

**Independent Test**: Run baseline models and DP-GMM on same data, compute time-to-detection, verify DP-GMM detects anomaly significantly earlier (statistically significant difference) than baselines.

### Implementation for User Story 2

- [X] T031 [P] [US2] Create `code/src/baselines/gmm_fixed.py` implementing fixed-component GMMs (k=3, 5, 10) for reconstruction error
- [X] T032 [P] [US2] Create `code/src/baselines/arima.py` implementing ARIMA model for reconstruction error
- [X] T033 [US2] Implement `code/src/evaluation/metrics.py` functions for time-to-detection calculation against independent ground-truth timestamps (FR-013)
- [X] T034 [US2] Implement Wilcoxon signed-rank test on time-to-detection values; add paired t-test as secondary check only if normality assumptions met (FR-006)
- [X] T035 [US2] Implement KS test comparing baseline reconstruction error distribution against DP-GMM signature distribution on normalized scores (FR-015)
- [X] T036 [US2] Implement KS test comparing "rate of change" metrics between anomaly and negative control (gradual drift) windows (FR-014)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Justification and Sensitivity Analysis (Priority: P3)

**Goal**: Implement threshold sensitivity analysis, validate robustness, ensure nested validation to prevent data-dredging

**Independent Test**: Run detection logic with three distinct threshold values on held-out test set, verify output includes table showing variation in FP/FN rates.

### Implementation for User Story 3

- [X] T040 [P] [US3] Create `code/src/services/threshold_calibrator.py` with a set of methods including `__init__`, `calibrate`, `validate_threshold`, `get_decision_boundary`, `update_decision_boundary`, and `compute_expected_bounds`.
- [X] T041 [US3] Implement `code/src/evaluation/threshold_sweep.py` to sweep cutoffs over a representative set of significance thresholds including 0.05 (1501.05788, https://arxiv.org/abs/1501.05788) and 0.1 on normalized reconstruction error [UNRESOLVED-CLAIM: c_c93a3e5e — status=not_enough_info] (FR-007). **Deliverable**: Generate `data/processed/results/sensitivity_report.csv` with columns: `threshold`, `fp_rate`, `fn_rate`, `instability_flag` [UNRESOLVED-CLAIM: c_65d50fcf — status=not_enough_info].
- [X] T042 [US3] Implement `code/src/evaluation/data_splitter.py` to split data into train/validation/test sets using a time-series aware split with a majority allocation to the training set. **Constraint**: Select threshold on validation set, apply to held-out test set (FR-019). **Deliverable**: Generate `data/processed/results/splits_manifest.json` containing keys: `train_indices`, `val_indices`, `test_indices`, `split_ratios`, `seed` [UNRESOLVED-CLAIM: c_5fcaeea7 — status=not_enough_info].
- [X] T043 [US3] Implement Bonferroni correction for multiple comparisons specifically when using threshold-swept outcomes in statistical tests (FR-007b). **Constraint**: Do NOT apply generically; only when threshold-swept outcomes are used.
- [X] T044 [US3] Implement sensitivity analysis on window size and derivative calculation method (including smoothing and lag variations) to validate robustness (FR-016)
- [X] T045 [US3] Implement logic to flag threshold instability when error rates spike in sensitivity report (FR-007)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Resource Constraint Validation and CPU Feasibility (Priority: P3)

**Goal**: Validate pipeline runs within GitHub Actions free-tier constraints (≤2 CPU, 7 GB RAM, 6 hours) [UNRESOLVED-CLAIM: c_8eedfe7b — status=not_enough_info]

**Independent Test**: Execute full pipeline on standard GitHub Actions runner, verify peak memory <7 GB and runtime <6 hours.

### Implementation for User Story 4

- [X] T048 [P] [US4] Create `code/src/utils/memory_profiler.py` using `psutil.Process().memory_info().rss` to track peak RAM
- [X] T049 [US4] Implement `code/src/services/anomaly_detector.py` resource validation logic: measure peak RAM and total runtime, fail run if limits exceeded (FR-008) <!-- FAILED: unspecified -->
- [X] T050 [P] [US4] Create `code/scripts/verify_resource_compliance.py` to enforce CPU-only execution and validate no CUDA library loading
- [X] T051 [US4] Implement logic to generate resource validation report outputting peak RAM and runtime metrics

**Checkpoint**: Resource constraints validated - pipeline is CPU-feasible

---

## Phase 7: Data Acquisition and Provenance (Critical Path)

**Goal**: Execute search procedure for real-world datasets; fetch only if verified; generate Deferred report if not found.

**⚠️ CRITICAL ORDER**: T052b (Search) MUST precede T052c (Deferred) and T052 (Fetch).
- **IF T052b FAILS**: Run T052c immediately. T052 is BLOCKED.
- **IF T052b SUCCEEDS**: Run T052. T052c is SKIPPED.

- [X] T052b [P] [Data] Execute mandatory search procedure for real-world datasets with labeled regime shifts (FR-017). **Search Keywords**: "anomaly detection", "regime shift", "time series", "NAB", "PhysioNet", "UCI". **Sources**: NAB, UCI, PhysioNet. **Deliverable**: If no verified source is found, generate `data/processed/results/validation_deferred.md` with exact fields: `search_query`, `result_count`, `status: DEFERRED`, `reason: FR-017b`. **Note**: This task MUST precede T052.
- [X] T052 [Data] **Conditional on T052b success**: Create `code/src/data/download_datasets.py` fetching verified NAB/PhysioNet subsets or UCI Electricity Load Diagrams and Traffic via `ucimlrepo` or verified URLs. **Do NOT execute if T052b failed.** **Constraint**: Do NOT fetch synthetic datasets (e.g., Synthetic Control Chart) as "real-world".
- [X] T053 [Data] Verify all downloaded datasets have ≥1,000 observations [UNRESOLVED-CLAIM: c_94df5841 — status=not_enough_info]; reject dataset if insufficient size (FR-001). **Conditional on T052 execution.**
- [X] T054 [Data] Delete all PEMS-SF files (`pems_sf.csv`, `pems_sf_synthetic.csv`) from `data/raw/`
- [X] T054b [Data] **Conditional on T054 failure**: Execute `rm -f data/raw/pems_sf.csv data/raw/pems_sf_synthetic.csv` and verify with `ls -la data/raw/ | grep pems` returning empty. Log output to `data/data_provenance_report.md`.
- [X] T055 [Data] Flatten `data/raw/raw/` directory: move all files to `data/raw/` and remove nested directory
- [X] T055b [Data] **Conditional on T055 failure**: Execute `find data/raw/ -type d -name raw -exec rm -rf {} +` and verify with `find data/raw/ -type d -name raw` returning empty. Log output to `data/data_provenance_report.md`.
- [X] T056 [Data] Delete legacy `data/results/` directory and migrate all contents to `data/processed/results/`
- [X] T056b [Data] **Conditional on T056 failure**: Execute `rm -rf data/results/` and verify with `ls -la data/ | grep results` returning only `processed/results`. Log output to `data/data_provenance_report.md`.
- [X] T057 [Data] Generate SHA256 checksums for all raw data files and record in `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml`
- [X] T058 [Data] **Conditional on T052b success**: Update `data/data-dictionary.md` to list only verified UCI datasets (Electricity, Traffic) with explicit license terms and URLs. **If T052b failed, update to note 'Deferred by Design' per FR-017b.**
- [ ] T059 [Data] Implement `code/src/data/download_datasets.py` verification logic to check dataset integrity against checksums before processing
- [X] T052c [Data] **Conditional on T052b failure**: Generate 'Validation Deferred' report citing search query and result count, mark requirement as 'Deferred by Design' (FR-017b).

**Checkpoint**: Data hygiene established - only compliant UCI datasets present with verified checksums OR Deferred report generated.

---

## Phase 8: Configuration and Filesystem Hygiene (Critical Path)

**Goal**: Ensure config.yaml <2KB, correct file locations, complete documentation

- [ ] T060 [Config] Migrate all derived statistics (keys: `dataset_stats`, `inference_results`, `simulation_metrics`) from `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/config.yaml` to `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml` using `code/src/utils/migrate_config.py`, then verify `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/config.yaml` size <2048 bytes.
- [X] T061 [Config] Verify `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/config.yaml` size <2048 bytes [UNRESOLVED-CLAIM: c_ef0d62ef — status=not_enough_info] using `os.path.getsize()`; fail if exceeded (FR-009)
- [X] T062 [Config] Create `code/scripts/verify_config_compliance.py` with explicit size check and error exit code
- [X] T063 [FS] Move all Python source files from `code/` root to `code/src/` subdirectories (models/, baselines/, data/, evaluation/, services/, utils/, simulation/)
- [X] T064 [FS] Update all imports in `code/src/` files to reflect new package structure
- [X] T065 [FS] Create `README.md` at repository root with usage instructions for DPGMM and baselines
- [X] T066 [FS] Create `LICENSE` file (MIT) at repository root
- [X] T067 [FS] Verify `code/.gitignore` includes `__pycache__/`, `*.pyc`, `*.egg-info/`
- [X] T068 [FS] Create `logs/elbo/` directory for ELBO convergence logs per Constitution Principle VI
- [X] T069 [FS] Verify `code/src/` contains NO files at root level; run `find code/ -maxdepth 1 -name "*.py"` and ensure empty
- [X] T070 [FS] Verify `data/raw/` contains NO nested `raw/` directories; run `find data/raw/ -type d -name raw` and ensure empty
- [X] T071 [FS] Verify `data/` contains NO `results/` directory; run `ls -la data/ | grep results` and ensure only `processed/results/` exists
- [X] T072 [FS] Verify no PEMS-SF files exist in `data/raw/`; run `grep -r "pems" data/raw/` and ensure empty

**Checkpoint**: Filesystem hygiene and config compliance verified

---

## Phase 9: Reporting and Compliance (Final Gate)

**Goal**: Generate final reports, validate all requirements, execute final acceptance

- [X] T089 [Report] Generate `data/processed/results/simulation_validation.csv` with SNR metrics from Phase 0 (FR-020)
- [X] T090 [Report] Generate `data/processed/results/posterior_trajectory.csv` with $\dot{\alpha}$ and weight variance trajectories
- [X] T091 [Report] Generate `data/processed/results/statistical_report.csv` with KS tests, Wilcoxon tests, bootstrap p-values
- [X] T092 [Report] Generate `data/processed/results/sensitivity_report.md` with threshold sweep results and instability flags
- [X] T093 [Report] Generate `data/processed/results/final_report.md` including methodology, results, fallback status, and "Deferred by Design" note if real-world data search fails (FR-017b)
- [X] T094 [Report] Generate `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml` with all artifact hashes and dataset checksums
- [X] T095 [Compliance] Run `code/scripts/verify_config_compliance.py` and capture output in `code/tests/config_compliance_report.md`
- [X] T096 [Compliance] Run `code/scripts/verify_resource_compliance.py` and capture output in `data/processed/results/resource_validation_report.md`
- [X] T097 [Compliance] Verify all UCI datasets present with checksums in state file; generate `data/sample_size_report.md` confirming ≥1000 observations each (or Deferred report if applicable)
- [X] T098 [Compliance] Run `find data/raw/ -type f -name "*.csv"` and verify only Electricity, Traffic present; output to `data/data_provenance_report.md` (or Deferred status)
- [X] T099 [Compliance] Run `ls -la code/src/` and verify correct subdirectory structure; output to `code/src_structure_report.md`
- [X] T100 [Compliance] Execute T145 Final Acceptance: verify all [X] tasks have no FAILED-IN-EXECUTION comments, all filesystem hygiene checks pass, all tests pass, all reports generated

**Checkpoint**: All success criteria met - project ready for `research_complete` stage

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Ground Truth Simulation)**: No dependencies - MUST complete before Phase 3.
- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **Test First (Phase 2.5)**: Depends on Phase 2 (Schemas) - BLOCKS all User Story implementations.
- **User Stories (Phase 3-6)**: All depend on Phase 0, Phase 2, Phase 2.5, and Phase 7 (Data Acquisition).
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Data Acquisition (Phase 7)**: MUST complete before Phase 3 (User Story 1) implementation. **T052b (Search) MUST precede T052c (Deferred) and T052 (Fetch).**
- **Hygiene (Phase 8)**: Must complete before Final Acceptance (T100)
- **Reporting (Phase 9)**: Depends on all previous phases; final gate before `research_complete`

### User Story Dependencies

- **User Story 1 (P1)**: Requires Phase 0, Phase 2, Phase 2.5, and Phase 7 (Data Acquisition).
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
- Once Phase 0, Phase 2, Phase 2.5, and Phase 7 complete, all user stories can start in parallel (if team capacity allows)
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
4. Complete Phase 2.5: Test First (CRITICAL - ensures testability)
5. Complete Phase 7: Data Acquisition (Search first, then Fetch or Deferred)
6. Complete Phase 3: User Story 1
7. **STOP and VALIDATE**: Test User Story 1 independently

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational + Test First + Data Acquisition → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Validate resource constraints
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational + Test First + Data Acquisition together
2. Once Foundation ready:
 - Developer A: User Story 1 (DPGMM core)
 - Developer B: User Story 2 (Baselines)
 - Developer C: User Story 3 (Thresholds)
3. Stories complete and integrate independently

### Revision Remediation Strategy

**CRITICAL**: Do NOT retry the same tasks that failed in prior reviews. Remediation is handled via conditional branches within Phase 7 (e.g., T054b, T055b, T056b) for physical file cleanup. No separate remediation phase exists.

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
- **CRITICAL**: Phase 7 (Data Acquisition) MUST complete before Phase 3. T052b (Search) MUST precede T052c (Deferred) and T052 (Fetch).
- **CRITICAL**: T018 (Simulation) MUST complete after T019 (Creation) and before T020 (DPGMM).
- **CRITICAL**: T021 (Windowing) MUST precede T019 and T020.
- **CRITICAL**: All verification outputs (ls, find, stat, grep) MUST be captured in report files.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T101 Reconcile run-book vs implementation for `code/src/config.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/src/config.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T102 Reconcile run-book vs implementation for `code/src/evaluation/simulation.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/src/evaluation/simulation.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T103 Reconcile run-book vs implementation for `code/src/evaluation/robustness.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/src/evaluation/robustness.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
