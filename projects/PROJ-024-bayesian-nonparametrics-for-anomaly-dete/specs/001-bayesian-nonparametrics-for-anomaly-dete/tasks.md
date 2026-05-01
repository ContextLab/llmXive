# Tasks: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Input**: Design documents from `/specs/001-bayesian-nonparametrics-anomaly-detection/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/
**Branch**: `001-bayesian-nonparametrics-anomaly-detection`
**Tests**: Tests are REQUIRED per spec.md Independent Test scenarios for all user stories.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/src/`, `code/tests/` at repository root under `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 0: Research & Design Documentation (Blocking)

**Purpose**: Create required design artifacts that plan.md designates as Phase 0/1 outputs

**⚠️ CRITICAL**: These artifacts must be created before Phase 1 Setup begins

- [X] T000 [P] Create `research.md` with literature review and DPGMM theoretical foundations in `specs/001-bayesian-nonparametrics-anomaly-detection/research.md` per plan.md Phase 0
- [ ] T001 [P] Create `data-model.md` with entity definitions and schema specifications in `specs/001-bayesian-nonparametrics-anomaly-detection/data-model.md` per plan.md Phase 1
- [ ] T002 [P] Create `quickstart.md` with usage examples and installation instructions in `specs/001-bayesian-nonparametrics-anomaly-detection/quickstart.md` per plan.md Phase 1
- [ ] T003 [P] Run initial Constitution Principles I-VII compliance check before Phase 0 and document in `specs/001-bayesian-nonparametrics-anomaly-detection/constitution_check.md` per plan.md Constitution Check requirement

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T004 Create project structure per implementation plan at `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/`
- [ ] T005 Initialize Python 3.11 project with pinned dependencies in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/requirements.txt`
- [ ] T006 [P] Configure linting (ruff/black) and formatting tools in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/`
- [ ] T016 [P] Create schema YAML files in `specs/contracts/`: `dataset.schema.yaml`, `anomaly_score.schema.yaml`, `evaluation_metrics.schema.yaml`, `anomaly_detector.schema.yaml`, `threshold_calibrator.schema.yaml` per plan.md Schema Creation Tasks
- [ ] T017 [P] Create `code/src/__init__.py` files for all subpackages to ensure proper Python package structure per plan.md Project Structure
- [ ] T016a [P] Create `code/tests/README.md` documenting test coverage requirements and verification process per Constitution Principle I
- [ ] T017a [P] Implement PII scanning using `bandit` for code PII patterns in `code/` directory per Constitution Principle III
- [ ] T017b [P] Implement credential scanning using `trufflehog` for data files in `data/` directory per Constitution Principle III
- [ ] T018 [P] Run Constitution Principles I-VII re-check after Phase 1 design completion and document in `specs/001-bayesian-nonparametrics-anomaly-detection/constitution_check.md` per plan.md Constitution Check requirement

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create `config.yaml` with hyperparameters, random seeds, and dataset paths per FR-009 in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/config.yaml` (MUST remain under 2KB)
- [ ] T008 [P] Implement data directory structure (`data/raw/`, `data/processed/`, `data/processed/results/`) in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/data/`
- [ ] T009 [P] Create `download_datasets.py` with wget/curl fetchers for UCI datasets (Electricity, Traffic, Synthetic Control Chart) per FR-007 AND implement SHA256 checksum validation for all downloaded files per Constitution Principle III in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/data/download_datasets.py`
- [ ] T010 [P] Implement `streaming.py` utilities for sequential observation processing in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/utils/streaming.py`
- [ ] T011 Create base `TimeSeries` dataclass/entity in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/time_series.py`
- [ ] T012 [P] Setup pytest framework with contract tests directory structure in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/contract/`
- [ ] T013 Create `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml` for artifact hashes AND implement checksum recording logic for all state artifacts per Constitution Principle III
- [ ] T014 [P] Create `code/scripts/generate_data_checksums.py` to generate explicit checksums for all data files in `data/raw/` and record in state file per Constitution Principle III
- [ ] T015 [P] Create `code/mypy.ini` configuration and update CI pipeline to run mypy with strict mode; ensure zero type errors per T072

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

## Phase 3: User Story 1 - Core DPGMM Implementation with Streaming Updates (Priority: P1) 🎯 MVP

**Goal**: Implement incremental DPGMM that processes time series observations one at a time with stick-breaking construction and ADVI variational inference

**Independent Test**: Can be fully tested by processing a synthetic time series with known anomaly points and verifying that the model produces anomaly scores without requiring batch retraining

### Tests for User Story 1 (REQUIRED per spec.md)

- [ ] T019 [P] [US1] Contract test for DPGMM model output schema in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/contract/test_dp_gmm_schema.py`
- [ ] T020 [P] [US1] Integration test for streaming observation update in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/integration/test_streaming_update.py`
- [ ] T021 [P] [US1] Memory usage test verifying <7GB RAM limit in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/unit/test_memory_profile.py`

### Implementation for User Story 1

- [ ] T022 [P] [US1] Create `DPGMMModel` class with stick-breaking construction in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/dpgmm.py` per FR-001
- [ ] T023 [US1] Implement ADVI variational inference with posterior update mechanism in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/dpgmm.py` per FR-002
- [ ] T024 [US1] Implement incremental posterior mixture weight update for each new observation in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/dpgmm.py` per FR-002
- [ ] T025 [P] [US1] Create `AnomalyScore` dataclass for negative log posterior probability in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/anomaly_score.py` per FR-003
- [ ] T026 [US1] Implement anomaly scoring function computing negative log posterior per observation in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/dpgmm.py` per FR-003
- [ ] T027 [US1] Add probabilistic uncertainty estimates to anomaly scoring output in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/dpgmm.py` per US1 acceptance scenario 3
- [ ] T028 [US1] Implement memory profiling during 1000 observation processing in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/utils/memory_profiler.py` per FR-005
- [ ] T029 [US1] Add edge case handling for low-variance time series causing numerical instability in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/dpgmm.py` per Edge Cases
- [ ] T030 [US1] Add edge case handling for missing values in time series that break streaming update in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/dpgmm.py` per Edge Cases
- [ ] T031 [US1] Add concentration parameter tuning logic for too many/too few mixture components in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/dpgmm.py` per Edge Cases
- [ ] T032 [P] [US1] Create synthetic anomaly dataset generator with known ground truth for validation in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/data/synthetic_generator.py` per spec.md Assumptions
- [ ] T033 [US1] Implement explicit time-ordered train/test split to prevent temporal data leakage per implementation correctness review
- [ ] T034 [P] Create `code/src/utils/time_split.py` for explicit time-ordered train/test split to prevent temporal leakage per T033
- [ ] T035 [P] Document temporal split methodology in `data-model.md` with train/test timestamps for all three datasets per T033

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

## Phase 4: User Story 2 - Baseline Comparison and Performance Evaluation (Priority: P2)

**Goal**: Compare DPGMM detector against ARIMA, moving average, and LSTM Autoencoder baselines on public benchmarks with F1-score validation

**Independent Test**: Can be fully tested by running all three models on a single UCI dataset and generating precision-recall curves with F1-score measurements

### Tests for User Story 2 (REQUIRED per spec.md)

- [ ] T036 [P] [US2] Contract test for evaluation metrics output schema in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/contract/test_metrics_schema.py`
- [ ] T037 [P] [US2] Integration test for end-to-end baseline comparison pipeline in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/integration/test_baseline_comparison.py`

### Implementation for User Story 2

- [ ] T038 [P] [US2] Implement ARIMA baseline model in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/baselines/arima.py` per US2 acceptance scenario 1
- [ ] T039 [P] [US2] Implement moving average with z-score baseline in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/baselines/moving_average.py` per US2 acceptance scenario 1
- [ ] T090 [P] [US2] Implement LSTM Autoencoder baseline for anomaly detection in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/baselines/lstm_ae.py` per spec.md User Story 2 update (creativity review addition)
- [ ] T040 [US2] Create `EvaluationMetrics` class containing F1-scores, precision, recall, AUC in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/metrics.py` per FR-006
- [ ] T041 [US2] Implement F1-score, precision, recall, AUC computation functions in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/metrics.py` per FR-006
- [ ] T042 [US2] Create confusion matrix generator for model evaluation in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/metrics.py` per FR-006
- [ ] T043 [US2] Implement ROC curve generator saving PNG files in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/plots.py` per FR-006
- [ ] T044 [US2] Implement PR curve generator saving PNG files in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/plots.py` per FR-006
- [ ] T045 [US2] Implement paired t-test with Bonferroni correction across datasets in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/evaluation/statistical_tests.py` per US2 acceptance scenario 2
- [ ] T046 [US2] Dataset fetchers consolidated in T009 - UCI Electricity, Traffic, and Synthetic Control Chart datasets downloaded via single download_datasets.py per spec.md Assumptions
- [ ] T047 [US2] Dataset fetchers consolidated in T009 - UCI Electricity, Traffic, and Synthetic Control Chart datasets downloaded via single download_datasets.py per spec.md Assumptions
- [ ] T048 [US2] Dataset fetchers consolidated in T009 - UCI Electricity, Traffic, and Synthetic Control Chart datasets downloaded via single download_datasets.py per SC-001 requirement for 3 UCI datasets
- [ ] T049 [US2] Implement runtime monitoring to verify <30 minutes per dataset in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/utils/runtime_monitor.py` per SC-003 AND implement timeout handling for edge case (30-minute limit) - log warning, save partial results, trigger retry per Edge Cases
- [ ] T050 [US2] Create hyperparameter counting utility to verify <30% tunable parameters vs baselines in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/utils/hyperparameter_counter.py` per SC-004

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

## Phase 5: User Story 3 - Anomaly Score Threshold Calibration (Priority: P3)

**Goal**: Calibrate posterior probability threshold for anomaly flagging without labeled data for real-world streaming deployment

**Independent Test**: Can be fully tested by running the model on unlabeled data and verifying that the adaptive threshold produces reasonable anomaly rates based on statistical properties of the scores

### Tests for User Story 3 (REQUIRED per spec.md)

- [ ] T051 [P] [US3] Contract test for ThresholdCalibratorService interface in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/contract/test_threshold_calibrator_schema.py` per spec.md Service Interfaces section
- [ ] T052 [P] [US3] Integration test for unlabeled data threshold calibration in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/integration/test_threshold_calibration.py`

### Implementation for User Story 3

- [ ] T053 [P] [US3] Implement adaptive threshold computation using 95th percentile of score distribution in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/utils/threshold.py` per spec.md Assumptions
- [ ] T054 [US3] Create threshold calibration function for unlabeled data in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/utils/threshold.py` per FR-004
- [ ] T055 [US3] Document decision boundary in config.yaml for replication per FR-009 and US3 acceptance scenario 2
- [ ] T056 [US3] Implement anomaly rate validation against expected bounds in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/utils/threshold.py` per US3 acceptance scenario 1
- [ ] T057 [US3] Add support for threshold calibration across multiple datasets without labeled data in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/utils/threshold.py` per US3 acceptance scenario 3

**Checkpoint**: All user stories should now be independently functional

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T058 [P] Documentation updates in `specs/001-bayesian-nonparametrics-anomaly-detection/` directory (NOT docs/) per plan.md Project Structure
- [ ] T059 Code cleanup and refactoring across all implementation files
- [ ] T060 Performance optimization for streaming DPGMM inference
- [ ] T061 [P] Additional unit tests for edge cases in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/unit/`
- [ ] T062 [US1] Implement cluster anomaly handling for clustered anomalies rather than isolated points in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/dpgmm.py` per Edge Cases
- [ ] T063 [P] Add GitHub Actions workflow for automated testing within 30-minute runtime constraint per SC-003
- [ ] T064 [P] Implement exponential backoff retry logic for GitHub Actions timeout handling in `.github/workflows/ci.yml` per Edge Cases specification
- [ ] T065 Create README with usage instructions for all four baselines and DPGMM
- [ ] T066 Verify Constitution Principles I-VII are all satisfied and documented
- [ ] T067 Validate quickstart.md (created in Phase 0) and verify all artifacts hash correctly
- [ ] T068 Implement ELBO convergence logging for ADVI variational inference per Constitution Principle VI in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/src/models/dpgmm.py` with explicit stopping criteria (ELBO improvement <0.001 for 50 consecutive iterations or 500 max iterations) AND create `logs/elbo/` directory and verify ADVI training writes convergence logs
- [ ] T069 [P] Consolidated .gitignore task: Add comprehensive `.gitignore` entries for `__pycache__/`, `*.pyc`, `*.log` (except `logs/elbo/`), `data/raw/`, `*.egg-info/` per Constitution Principle I reproducibility requirements
- [ ] T070 [P] Consolidated requirements.txt task: Ensure `requirements.txt` is fully pinned with exact versions (e.g., `pymc==5.9.0`) AND verify pinned versions in CI per Constitution Principle I reproducibility requirements
- [ ] T071 [P] Consolidated LICENSE task: Add LICENSE file to project root with MIT License (MIT) per spec.md Assumptions AND verify LICENSE file exists at project root with MIT License content
- [ ] T072 [P] Add `code/src/services/anomaly_detector.py` service wrapper per plan.md Project Structure specification. **Interface: load_model(), process_stream(), update_model(), compute_score(), get_uncertainty(), save_checkpoint(), __init__**
- [ ] T073 [P] Add `code/src/services/threshold_calibrator.py` service wrapper per plan.md Project Structure specification. **Interface: calibrate(), validate_threshold(), get_decision_boundary(), update_decision_boundary(), compute_expected_bounds(), __init__**
- [ ] T074 [P] Run coverage report with pytest-cov and verify ≥80% line coverage for all public APIs per spec.md test coverage requirement. T016 documents coverage requirements, T074 executes verification.
- [ ] T075 [P] Execute full evaluation pipeline on all 3 UCI datasets and populate `data/processed/results/` with metrics, curves, and validation reports per research_reviewer__2026-05-01 concern #3
- [ ] T076 [P] Verify F1-scores, ROC/PR curves, memory profiles, and runtime measurements exist in results directory per SC-001 through SC-005
- [ ] T077 [P] Create `data/processed/results/summary.md` documenting all success criteria measurements (F1-scores, memory usage, runtime, hyperparameter counts) per research_reviewer__2026-05-01 concern #3
- [ ] T078 [P] Verify paired t-tests with Bonferroni correction completed across all datasets per US2 acceptance scenario 2
- [ ] T079 [P] Document data licenses for UCI datasets in data-dictionary.md per data quality review
- [ ] T080 [P] Verify `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml` exists with complete checksum entries for all data files per Constitution Principle III
- [ ] T081 [P] Create `code/scripts/generate_state_checksums.py` to automate state file updates when artifacts change per Constitution Principle III
- [ ] T082 [P] Verify `config.yaml` is under 2KB using `os.path.getsize()` and document final size in `code/tests/test_report.md` per FR-009
- [ ] T083 [P] Run `code/scripts/verify_config_compliance.py` to confirm config.yaml contains only hyperparameters, seeds, and base paths (no derived statistics) per T082
- [ ] T084 [P] Document config.yaml contents breakdown in `code/tests/test_report.md` showing hyperparameters vs. state file contents
- [ ] T085 [P] Verify CI pipeline runs contract tests, unit tests, and integration tests with coverage reporting per T069
- [ ] T086 [P] Create `code/scripts/verify_parallel_safety.py` to confirm no file conflicts between parallel tasks per spec.md Assumptions
- [ ] T087 [P] Create `code/scripts/verify_dependency_order.py` to check execution order against task graph per spec.md Assumptions
- [ ] T088 [P] Create contract test for AnomalyDetectorService interface in `projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete/code/tests/contract/test_anomaly_detector_schema.py` per spec.md Service Interfaces section

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research & Design)**: No dependencies - can start immediately
- **Setup (Phase 1)**: Depends on Phase 0 completion
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete - BLOCKS final acceptance

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (REQUIRED) MUST be written and FAIL before implementation
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
- Phase 6 revision tasks can be executed in parallel where file conflicts do not exist

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for DPGMM model output schema in code/tests/contract/test_dp_gmm_schema.py"
Task: "Integration test for streaming observation update in code/tests/integration/test_streaming_update.py"
Task: "Memory usage test verifying <7GB RAM limit in code/tests/unit/test_memory_profile.py"

# Launch all models for User Story 1 together:
Task: "Create DPGMMModel class with stick-breaking construction in code/src/models/dpgmm.py"
Task: "Create AnomalyScore dataclass in code/src/models/anomaly_score.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research & Design Documentation
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently
4. Developer D (or team rotation): Phase 6 review-driven revisions
5. Final verification and acceptance

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are REQUIRED per spec.md Independent Test scenarios (not OPTIONAL)
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Dataset URLs must be real and reachable (UCI Machine Learning Repository: Electricity, Traffic, Synthetic Control Chart)
- Task ordering MUST respect data flow: download datasets (T009) BEFORE model training (T022-T031), model training BEFORE evaluation (T040-T045)
- Note: `contracts/` under `specs/` contains schema definitions; `code/tests/contract/` contains pytest validation tests against those schemas
- PEMS-SF is from PEMS project NOT UCI Machine Learning Repository - use UCI Synthetic Control Chart or ECG Five Groups instead
- **Phase 6 tasks are CRITICAL and must be completed before final acceptance per research-stage review requirements**
- All execution failure tasks must be resolved and marked [X] before project can transition to analyzed stage
- Structure deviation (code/src/ vs projects/.../code/) must be corrected per Constitution Principle V
- config.yaml must be under 2KB per T082 requirement
- All datasets must have proper provenance documentation per T079
- Modern baseline (LSTM-AE) must be added per creativity review T090
- Type hints and mypy CI must be implemented per T015
- All test infrastructure must be verified per T012, T074
- Repository hygiene (.gitignore, pinned requirements) must be addressed per T069, T070
- **All [X] tasks with FAILED-IN-EXECUTION comments indicate resolved execution failures**
- File paths corrected: download_datasets.py (not downloaders.py), plots.py (not visualizations.py), threshold_calibrator.py (consistent location)
- **Schema-test mapping: `specs/contracts/dataset.schema.yaml` → `code/tests/contract/test_dataset_schema.py`, `specs/contracts/anomaly_score.schema.yaml` → `code/tests/contract/test_dp_gmm_schema.py`, `specs/contracts/evaluation_metrics.schema.yaml` → `code/tests/contract/test_metrics_schema.py`**
- **Test coverage definition: Adequate coverage means ≥80% line coverage for all public APIs, with contract tests for all schema validations and integration tests for all user stories**
- **Parallel execution verification: Each [P] task must have corresponding `verify_parallel_safety.py` script that confirms no file conflicts**
- **Dependency ordering verification: Each task dependency must be validated by `verify_dependency_order.py` script that checks execution order against task graph**
- **Schema files must exist in specs/contracts/ before contract tests can run per plan.md Schema Creation Tasks**
- **ELBO logging directory logs/elbo/ must exist with convergence logs per Constitution Principle VI**
- **State file state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml must contain all artifact checksums per Constitution Principle III**
- **Missing scripts added: `verify_parallel_safety.py`, `verify_dependency_order.py`, `generate_data_checksums.py`**
- **Dataset downloads consolidated to Phase 2 with single download_datasets.py**
- **Config.yaml size check added at runtime in T082**
- **Time-split documentation moved before implementation**