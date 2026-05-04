---
description: "Task list template for feature implementation"
---

# Tasks: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Input**: Design documents from `/specs/PROJ-024-bayesian-nonparametrics-anomaly-detection/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Branch**: `PROJ-024-bayesian-nonparametrics-anomaly-detection`
**Tests**: Tests are REQUIRED per spec.md Independent Test scenarios for all user stories.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **All phases**: Use relative paths from project root (e.g., `code/`, `code/src/`, `code/tests/`, `data/raw/`, `state/projects/`)
- **Single project**: `code/src/`, `code/tests/` at repository root under project folder
- **State files**: `state/projects/<project-id>.yaml`

## Phase 0: Research & Design Documentation (Blocking)

**Purpose**: Create required design artifacts that plan.md designates as Phase 0 outputs

- [X] T000 [P] Create `research.md` with literature review and DPGMM theoretical foundations in `specs/PROJ-024-bayesian-nonparametrics-anomaly-detection/research.md` per plan.md Phase 0
- [X] T001 [P] Create `data-model.md` with entity definitions and schema specifications in `specs/PROJ-024-bayesian-nonparametrics-anomaly-detection/data-model.md` per plan.md Phase 0
- [X] T002 [P] Create `quickstart.md` with usage examples and installation instructions in `specs/PROJ-024-bayesian-nonparametrics-anomaly-detection/quickstart.md` per plan.md Phase 0

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T003 Create project structure per implementation plan at `code/`
- [X] T004 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [X] T005 [P] Configure linting (ruff/black) and formatting tools in `code/`
- [X] T006 [P] Create `README.md` with usage instructions for all baselines and DPGMM
- [X] T007 [P] Create `LICENSE` file (MIT License) at repository root
- [X] T008 [P] Create `.gitignore` with `__pycache__/`, `*.pyc`, `*.log` entries

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T009 [P] Create `config.yaml` with hyperparameters, random seeds, and dataset paths per **FR-009** in `code/config.yaml`
- [X] T010 [P] Implement data directory structure (`data/raw/`, `data/processed/`) in `data/` - ENSURE NO NESTED `raw/raw/` STRUCTURES
- [X] T011 [P] Create `download_datasets.py` with wget/curl fetchers for UCI datasets per **FR-009** AND implement SHA256 checksum validation for all downloaded files per Constitution Principle III in `code/src/data/download_datasets.py`
- [X] T012 [P] Implement `streaming.py` utilities for sequential observation processing in `code/src/utils/streaming.py`
- [X] T013 Create base `TimeSeries` dataclass/entity in `code/src/models/time_series.py`
- [X] T014 [P] Setup pytest framework with contract tests directory structure in `code/tests/contract/`
- [X] T015 [P] Create `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection.yaml` for artifact hashes AND implement checksum recording logic for all state artifacts per Constitution Principle III in `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection.yaml`
- [X] T139 [P] Add data-model.md section documenting which time series are extracted from each UCI dataset (full path: `specs/PROJ-024-bayesian-nonparametrics-anomaly-detection/data-model.md`) per SC-001 univariate constraint
- [X] T140 [P] Document why each UCI dataset satisfies the univariate constraint while remaining representative (full path: `specs/PROJ-024-bayesian-nonparametrics-anomaly-detection/data-model.md`)
- [X] T141 [P] Verify Electricity dataset univariate series selection (37 series total, select representative subset) (full path: `specs/PROJ-024-bayesian-nonparametrics-anomaly-detection/data-model.md`)

## Phase 2.5: Physical Cleanup (Blocking Prerequisites for Phase 6)

**Purpose**: Physical filesystem cleanup that must complete before Phase 6 tasks that depend on them

- [X] T211 [P] Create `code/scripts/verify_config_compliance.py` with `os.path.getsize()` check that exits with code 1 if config.yaml >2048 bytes per FR-009
- [X] T210 [P] [DEPENDS: T211] Physically migrate ALL derived statistics from `code/config.yaml` to `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection.yaml` - VERIFY via `os.path.getsize()` that config.yaml is now <2048 bytes using `verify_config_compliance.py`
- [X] T213 [P] Physically remove all files from `data/raw/raw/` subdirectory and move to flat `data/raw/` - VERIFY via `ls -la data/raw/` that no nested `raw/` exists
- [X] T216 [P] Physically delete ALL PEMS-SF files from `data/raw/` (including `pems_sf.csv`, `pems_sf_synthetic.csv`, any `pems_*` files) - VERIFY via `ls data/raw/ | grep pems` returns empty
- [X] T155 [P] [DEPENDS: T216] Verify no PEMS‑SF files exist in `data/raw/` per **dataset requirements** (3 UCI datasets only: Electricity, Traffic, Synthetic Control Chart) - mark [X] only after T216 physical deletion

## Phase 3: User Story 1 - Core DPGMM Implementation with Streaming Updates (Priority: P1) 🎯 MVP

**Goal**: Implement DPGMM model with ADVI variational inference supporting streaming updates

**Independent Test**: Verify model converges on synthetic data and updates posterior incrementally

### Tests for User Story 1

- [X] T016 [P] [US1] Contract tests for DPGMM‑related schemas in `code/tests/contract/` - NOTE: Test files created but DO NOT EXECUTE until Phase 9
  - `test_dp_gmm_schema.py` (DPGMM schema)
  - `test_dataset_schema.py` (Dataset schema)
  - `test_anomaly_score_schema.py` (AnomalyScore schema)
  - `test_anomaly_detector_schema.py` (AnomalyDetector schema)
- [X] T017 [P] [US1] Unit test for streaming update logic in `code/tests/unit/test_streaming_update.py`
- [X] T018 [US1] Integration test for model training on synthetic data in `code/tests/integration/test_dpgmm_training.py`

### Implementation for User Story 1

- [X] T019 [P] [US1] Implement DPGMM core class in `code/src/models/dpgmm.py`
- [X] T020 [US1] Implement ADVI variational inference engine in `code/src/models/advi_engine.py`
- [X] T021 [US1] Implement streaming posterior update method in `code/src/models/dpgmm.py`
- [X] T022 [US1] Implement anomaly scoring function in `code/src/models/dpgmm.py`
- [X] T023 [US1] Add ELBO convergence logging to `logs/elbo/` per Constitution Principle VI - **CONSOLIDATED WITH T177**
- [X] T024 [US1] Integrate config loading for hyperparameters in `code/src/models/dpgmm.py`

**Checkpoint**: DPGMM model trains and updates incrementally on synthetic data

## Phase 4: User Story 2 - Baseline Implementation & Comparative Evaluation (Priority: P2)

**Goal**: Implement ARIMA, Moving Average, and LSTM‑AE baselines for comparison

**Independent Test**: Verify baselines produce scores on test data within expected ranges

### Tests for User Story 2

- [X] T025 [P] [US2] Contract test for metrics schema in `code/tests/contract/test_metrics_schema.py` - NOTE: Test file created but DO NOT EXECUTE until Phase 9
- [X] T026 [P] [US2] Unit test for baseline scoring logic in `code/tests/unit/test_baseline_scoring.py`
- [X] T027 [US2] Integration test for baseline comparison pipeline in `code/tests/integration/test_baseline_comparison.py`

### Implementation for User Story 2

- [X] T028 [P] [US2] Implement ARIMA baseline in `code/src/baselines/arima.py`
- [X] T029 [P] [US2] Implement Moving Average baseline in `code/src/baselines/moving_average.py`
- [X] T030 [US2] Implement LSTM‑AE baseline in `code/src/baselines/lstm_ae.py`
- [X] T031 [US2] Implement evaluation metrics (F1, Precision, Recall) in `code/src/evaluation/metrics.py`
- [X] T032 [US2] Implement paired t‑test for SC‑001 statistical significance in `code/src/evaluation/stats.py`
- [X] T033 [US2] Generate confusion matrices and ROC/PR curves in `data/processed/results/`

**Checkpoint**: All baselines implemented and evaluation metrics calculated

## Phase 5: User Story 3 - Anomaly Score Threshold Calibration (Priority: P3)

**Goal**: Implement unsupervised threshold calibration service

**Independent Test**: Verify threshold adapts to score distribution without labeled data

### Tests for User Story 3

- [X] T034 [P] [US3] Contract tests for ThresholdCalibrator generic schema in `code/tests/contract/` - NOTE: Test file created but DO NOT EXECUTE until Phase 9
  - `test_threshold_schema.py` (generic threshold_calibrator.schema.yaml)
- [X] T035 [P] [US3] Unit test for calibration logic in `code/tests/unit/test_threshold_calibration.py`
- [X] T036 [US3] Integration test for threshold update in streaming mode in `code/tests/integration/test_threshold_calibration.py`

### Implementation for User Story 3

- [X] T037 [P] [US3] Implement ThresholdCalibratorService in `code/src/services/threshold_calibrator.py` - **SINGLE IMPLEMENTATION TASK** - VERIFY ALL 6 METHODS: __init__, calibrate, validate_threshold, get_decision_boundary, update_decision_boundary, compute_expected_bounds per spec.md Service Interfaces section
- [X] T038 [US3] Implement percentile‑based calibration method in `code/src/services/threshold_calibrator.py`
- [X] T039 [US3] Implement adaptive boundary update logic in `code/src/services/threshold_calibrator.py`
- [X] T040 [P] [US3] [DEPENDS: T034, T035, T036, T037] Document decision boundary in **state file** per **FR‑009** and US3 acceptance scenario 2 (path: `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection.yaml`) - DO NOT MARK [X] UNTIL T034‑T036 PASS

**Checkpoint**: Threshold calibration works without labeled data

## Phase 6: Service Interfaces & Early Compliance (Priority: P4)

**Purpose**: Implement service interfaces required by User Stories 1 and 3, and move compliance checks earlier

### 6.1 Service Interface Implementation

- [X] T159 [P] [DEPENDS: T019, T020] Implement `AnomalyDetectorService` in `code/src/services/anomaly_detector.py` with all 7 required methods per spec.md Service Interfaces section - VERIFY EXACTLY 7 METHODS: __init__, load_model, process_stream, update_model, compute_score, get_uncertainty, save_checkpoint - **REMOVED DEPENDENCY ON T037**
- [X] T161 [P] Add type hints to all public APIs in services per PEP 484 compliance (now reflected in spec.md Service Interfaces)

### 6.2 Configuration & Directory Hygiene

- [X] T151 [P] [DEPENDS: T210] Ensure `code/config.yaml` stays <2KB by moving derived statistics to state file per **FR‑009** (Preventive - do not create >2KB files) - mark [X] only after T210 verification passes
- [X] T152 [P] Consolidate source code to `code/src/` subdirectories (models/, services/, baselines/, data/, evaluation/, utils/) per plan.md
- [X] T153 [P] [DEPENDS: T214] Verify `data/results/` directory does NOT exist and document verification in `code/tests/directory_compliance_report.md` - **CONSOLIDATED WITH T214**
- [X] T154 [P] Fix Phase 2 T010 data directory structure - remove any nested `data/raw/raw/` directories and ensure flat `data/raw/` structure

### 6.3 Data Provenance & Integrity

- [X] T156 [P] [DEPENDS: T216] Verify 3 UCI datasets exist: Electricity, Traffic, Synthetic Control Chart in `data/raw/`
- [X] T170 [P] [DEPENDS: T156] Verify Electricity dataset exists in `data/raw/` with correct filename (electricity.csv) and ≥1000 observations per SC-003
- [X] T171 [P] [DEPENDS: T156] Verify Traffic dataset exists in `data/raw/` with correct filename (traffic.csv) and ≥1000 observations per SC-003
- [X] T172 [P] [DEPENDS: T156] Verify Synthetic Control Chart dataset exists in `data/raw/` with correct filename (synthetic_control_chart.csv) and ≥1000 observations per SC-003
- [X] T157 [P] Implement SHA256 checksum recording logic in `code/src/utils/checksums.py` for all data artifacts - INTEGRATE WITH T011
- [X] T158 [P] Update `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection.yaml` with checksums for all raw data files - USE CONSISTENT PATH WITH T015

### 6.4 ELBO & Results Verification

- [X] T177 [P] Create `logs/elbo/` directory structure for ELBO convergence logs per Constitution Principle VI - **CONSOLIDATED WITH T023**
- [X] T164 [P] [DEPENDS: T177] Verify ELBO convergence logs exist in `logs/elbo/` with stopping criteria per Constitution Principle VI

## Phase 7: Test Infrastructure & Final Compliance (BLOCKS `analyzed` stage)

**Purpose**: Complete test infrastructure and final compliance checks

**⚠️ STAGE GATE**: Phase 7 MUST complete before project advances to `analyzed` stage

### 7.1 Contract Test Infrastructure

- [X] T162 [P] Create remaining 2 contract test files for service interfaces (anomaly_detector_service, threshold_calibrator_service) per Schema‑Test Mapping in `code/tests/contract/` - TOTAL 8 FILES - NOTE: Test files created but DO NOT EXECUTE until Phase 9

### 7.2 Test Coverage & Final Acceptance

- [X] T163 [P] Generate `code/tests/test_report.md` with pass/fail status per task AND EXPLICITLY VERIFY ≥80% LINE COVERAGE THRESHOLD IS MET per spec.md Test Coverage Requirements - MUST COMPLETE BEFORE FINAL ACCEPTANCE

### 7.3 Documentation & Legal Compliance

- [X] T166 [P] Create `data/data-dictionary.md` with exact URLs, licenses, and access dates for all 3 UCI datasets
- [X] T173 [P] [DEPENDS: T156] Verify all 3 UCI datasets have ≥1000 observations each per SC‑002 observation requirement and document in `data/sample_size_report.md`

## Phase 8: Schema Files Creation & Verification (BLOCKS `analyzed` stage)

**Purpose**: Create all 8 schema YAML files per spec.md Schema Definitions and validate them

**⚠️ STAGE GATE**: Phase 8 MUST complete before project advances to `analyzed` stage

### 8.1 Schema File Creation

- [X] T184 [P] Create all 8 schema files in `specs/contracts/` per spec.md Schema Definitions section:
  - `dataset.schema.yaml`
  - `anomaly_score.schema.yaml`
  - `evaluation_metrics.schema.yaml`
  - `threshold_calibrator.schema.yaml`
  - `anomaly_detector.schema.yaml`
  - `dpgmm.schema.yaml`
  - `anomaly_detector_service.schema.yaml`
  - `threshold_calibrator_service.schema.yaml`
- [X] T185 [P] Validate all 8 schema files with YAML linter and store validation logs in `code/tests/schema_validation_report.md` - **ADDED TO PLAN.MD MAPPING TABLE**

### 8.2 Service Interface Schema Validation

- [X] T186 [P] [DEPENDS: T184, T159, T037] Verify 8 schema YAML files match service interface method counts and structures per spec.md Service Interfaces - ANOMALY_DETECTOR_SERVICE must have method_count=7, THRESHOLD_CALIBRATOR_SERVICE must have method_count=6 - Document in `code/tests/service_interface_schema_validation.md` - **EVIDENCE: See `code/tests/service_interface_schema_validation.md` with method count verification**

## Phase 9: Critical Resolution Tasks (FINAL BLOCKING PHASE)

**Purpose**: Address the persistent violations that have blocked T145 Final Acceptance across multiple review cycles

**⚠️ CRITICAL**: These tasks MUST be completed before T145 can pass. Evidence of actual filesystem changes is required.

### 9.1 Final Physical Fixes

- [X] T212 [P] [DEPENDS: T210] Run `verify_config_compliance.py` and capture output in `code/tests/config_compliance_report.md` showing <2KB verification
- [X] T214 [P] [DEPENDS: T213] Verify `data/results/` directory does NOT exist and document verification in `code/tests/directory_compliance_report.md` - **CONSOLIDATED WITH T153 - T214 REMOVED FROM PHASE 2.5**
- [X] T215 [P] [DEPENDS: T214] Update all references in code to use `data/processed/results/` instead of legacy `data/results/` paths
- [X] T217 [P] [DEPENDS: T216] Update `data/data-dictionary.md` to explicitly list ONLY 3 UCI datasets (Electricity, Traffic, Synthetic Control Chart) with no PEMS references
- [X] T218 [P] [DEPENDS: T217] Update `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection.yaml` to remove all PEMS-SF checksums and retain only 3 UCI dataset checksums
- [X] T178 [P] [DEPENDS: T152] Verify all Python source files are located in `code/src/` subdirectories (models/, services/, baselines/, data/, evaluation/, utils/) - NO Python files at `code/` root level
- [X] T219 [P] [DEPENDS: T178] Verify `download_datasets.py` exists at correct location `code/src/data/download_datasets.py` per T011 creation - DO NOT MOVE AS FILE WAS ALREADY CREATED CORRECTLY
- [X] T220 [P] [DEPENDS: T219] Update all import statements in Python files to reflect `code/src/` paths
- [X] T221 [P] [DEPENDS: T220] Update `README.md` and `quickstart.md` to reflect corrected `code/src/` paths in all usage examples

### 9.2 Test Infrastructure Verification

- [X] T225 [P] [DEPENDS: T162, T184] List all 8 contract test files in `code/tests/contract/` and verify each file is non-empty with valid pytest structure
- [X] T226 [P] [DEPENDS: T225, T184, T016, T025, T034, T162] Run `pytest code/tests/contract/ -v` and capture output in `code/tests/contract_test_report.md` showing all 8 tests pass - **EXPLICIT DEPENDENCY ON T184 SCHEMA CREATION - ORDERING: T184 (Phase 8) → T225 → T226**
- [X] T228 [P] [DEPENDS: T018, T027, T036] Run all integration tests (`pytest code/tests/integration/ -v`) and capture output in `code/tests/integration_test_report.md`
- [X] T229 [P] [DEPENDS: T228] Verify all integration tests pass with no FAILED-IN-EXECUTION comments
- [X] T230 [P] [DEPENDS: T017, T026, T035] Run all unit tests (`pytest code/tests/unit/ -v`) and capture output in `code/tests/unit_test_report.md`
- [X] T231 [P] [DEPENDS: T230] Verify all unit tests pass with no FAILED-IN-EXECUTION comments

### 9.3 State File & Checksum Verification

- [X] T232 [P] [DEPENDS: T015, T158] Verify `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection.yaml` contains SHA256 checksums for all 3 UCI raw data files - **T174 REMOVED - NO DEPENDENCY**
- [X] T233 [P] [DEPENDS: T232] Verify state file contains derived statistics moved from config.yaml (dataset stats, decision boundaries, computed metrics)
- [X] T235 [P] Create `code/scripts/verify_checksums.py` to automate SHA256 verification for electricity.csv, traffic.csv, synthetic_control_chart.csv per Constitution Principle III
- [X] T234 [P] [DEPENDS: T235] Run checksum verification script for all raw data files and capture output in `code/tests/checksum_verification_report.md`
- [X] T236 [P] [DEPENDS: T234] Run automated checksum verification and document any mismatches in `code/tests/checksum_verification_report.md`

### 9.4 T145 Final Acceptance Resolution

- [X] T222 [P] [DEPENDS: T210, T213, T216, T219, T184, T226] Verify T145 has no FAILED‑IN‑EXECUTION comments before marking [X] - EXECUTE BEFORE T145 - **EXPLICIT DEPENDENCY ON PHASE 8 COMPLETION - EVIDENCE: grep -r "FAILED-IN-EXECUTION" output in `code/tests/failed_execution_report.md`**
- [X] T223 [P] [DEPENDS: T222] Re-run `code/scripts/final_acceptance_verification.py` and capture output showing exit=0 in `code/tests/final_acceptance_report.md` - **ADDED TO PLAN.MD SECTION 9.2 AS EXTERNAL VERIFICATION REQUIREMENT FOR T145**

## Phase 9.5: Filesystem Verification Enforcement (NEW - Addresses Persistent Review Concerns)

**Purpose**: Force actual filesystem verification for tasks that were marked complete without evidence

**⚠️ CRITICAL**: These tasks require explicit filesystem command output in report files. All Phase 9.5 tasks are VERIFICATION TASKS that validate Phase 2.5 cleanup actions.

- [X] T240 [P] [DEPENDS: T216] Run `ls -la data/raw/` and save output to `code/tests/pems_deletion_verification.md` - MUST show NO pems_* files present - mark [X] only if grep pems returns empty - **EVIDENCE: See `code/tests/pems_deletion_verification.md`**
- [X] T241 [P] [DEPENDS: T213] Run `find data/raw/ -type d -name raw` and save output to `code/tests/nested_raw_verification.md` - MUST show NO nested raw directories - mark [X] only if find returns empty - **EVIDENCE: See `code/tests/nested_raw_verification.md`**
- [X] T242 [P] [DEPENDS: T214] Run `ls -la data/ | grep results` and save output to `code/tests/legacy_results_verification.md` - MUST show NO data/results/ directory - mark [X] only if grep returns empty - **EVIDENCE: See `code/tests/legacy_results_verification.md`**
- [X] T243 [P] [DEPENDS: T210] Run `stat -c%s code/config.yaml` and save output to `code/tests/config_size_verification.md` - MUST show value <2048 - mark [X] only if size is under 2KB - **EVIDENCE: See `code/tests/config_size_verification.md`**
- [X] T244 [P] [DEPENDS: T178] Run `find code/ -maxdepth 1 -name "*.py" -type f` and save output to `code/tests/source_location_verification.md` - MUST show NO .py files at code/ root level - mark [X] only if find returns empty - **EVIDENCE: See `code/tests/source_location_verification.md`**
- [X] T245 [P] [DEPENDS: T232] Run `cat state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection.yaml | grep -E "pems|PEMS"` and save output to `code/tests/state_file_pems_check.md` - MUST show NO PEMS checksums - mark [X] only if grep returns empty - **EVIDENCE: See `code/tests/state_file_pems_check.md`**
- [X] T246 [P] [DEPENDS: T240, T241, T242, T243, T244, T245] Create `code/tests/filesystem_compliance_summary.md` with aggregate verification status - mark [X] only if ALL 6 verification reports show PASS

## Phase 9.6: Test Infrastructure Completeness Verification (NEW - Addresses Test File Concerns)

**Purpose**: Verify all contract test files actually exist and are executable

- [X] T247 [P] [DEPENDS: T184, T162] Run `ls -la code/tests/contract/` and save output to `code/tests/contract_test_file_listing.md` - MUST show all 8 test files present and non-empty
- [X] T248 [P] [DEPENDS: T247] Run `pytest code/tests/contract/ --collect-only` and save output to `code/tests/contract_test_collection.md` - MUST show all 8 tests collected without errors
- [X] T249 [P] [DEPENDS: T248] Run `pytest code/tests/contract/ -v --cov=code/src --cov-report=term-missing` and save output to `code/tests/contract_test_coverage_report.md` - MUST show ≥80% line coverage
- [X] T250 [P] [DEPENDS: T249] Create `code/tests/test_infrastructure_completeness.md` documenting all test files, execution results, and coverage metrics - mark [X] only if all 8 tests pass with ≥80% coverage

## Phase 10: Final Acceptance (BLOCKS `analyzed` stage)

**Purpose**: T145 Final Acceptance executes after ALL Phase 8 AND Phase 9 tasks complete with EXTERNAL VERIFICATION

**⚠️ STAGE GATE**: T145 MUST pass before project advances to `analyzed` stage

- [X] T145 [P] Final acceptance verification task - confirm all [X] marked tasks have no FAILED‑IN‑EXECUTION comments per spec.md Status Tracking Mechanism **and** verify that all six final acceptance conditions (SC‑001 through SC‑006) are satisfied **and** verify external completion evidence: T222 (Phase 9 verification), T226 (contract test execution), T186 (schema-service interface validation), T223 (final acceptance script) all show [X] - EXECUTE AFTER ALL PHASE 8 AND PHASE 9 TASKS COMPLETE - **EXTERNAL VERIFICATION REQUIRED** - **SELF-MARKING MECHANISM: T145 marks itself [X] ONLY after final_acceptance_verification.py exits with code 0 and all external verification tasks show [X] - NO CIRCULAR DEPENDENCY: T222, T223, T226, T186 all complete BEFORE T145 marks itself**

---

**Phase 11 DELETED**: All original Phase 11 tasks (T237-T265) were REDISTRIBUTED into Phase 2.5 and Phase 9 to eliminate logical contradictions and redundant task definitions. **New tasks T240-T250 in Phase 9.5/9.6 are ADDITIONAL filesystem verification tasks, NOT from original Phase 11**. Traceability documented in plan.md Section 9.2.

**T224 DELETED**: Task T224 (mark T145 as [X]) has been removed to eliminate circular dependency where T224 depended on T145 while T145 was the final acceptance gate. T145 now directly marks itself [X] after completing its own verification with external verification tasks (T222, T226, T186, T223) completing first. **Traceability documented in plan.md Section 9.2**.

**T214 DUPLICATE REMOVED**: T214 was duplicated in Phase 2.5 and Phase 9.1. T214 in Phase 2.5 has been REMOVED; only T214 in Phase 9.1 remains. T153 was consolidated into T214.

**Consolidation Notes**:
- T160 removed - T037 is the single implementation task for ThresholdCalibratorService (Phase 5)
- T159 dependency on T037 removed - AnomalyDetectorService is independent per spec.md
- T023 and T177 consolidated - T177 creates directory, T023 logs to it
- T174 removed - T232-T236 are the verification tasks (no T174 dependency)
- T153 and T214 consolidated - T214 is the verification task, T153 removed
- T165 consolidated into T163 - T163 now includes coverage verification
- T214 removed from Phase 2.5 (duplicate in Phase 9.1)
- **T150 REMOVED**: T150 has been consolidated into T225-T226 per plan.md Section 9.2 Consolidation Decisions. T150 no longer exists as a separate task in Phase 9.2.

**State File Naming Correction**: All references updated from `PROJ-024-bayesian-nonparametrics-for-anomaly-detect.yaml` to `PROJ-024-bayesian-nonparametrics-for-anomaly-detection.yaml` per project naming conventions.

**Phase 9.5 and 9.6 Added**: New verification phases added to address persistent filesystem hygiene violations identified in multiple research reviews. These tasks require explicit filesystem command evidence rather than task completion markers alone. **These are ADDITIONAL verification tasks, NOT from original Phase 11 **(T237-T265)

**FAILED-IN-EXECUTION VERIFICATION PROCESS**: T145 scans ALL prior tasks (T000-T250) for `FAILED-IN-EXECUTION` comments using `grep -r "FAILED-IN-EXECUTION"` across code/, specs/, data/, state/ directories. If any FAILED-IN-EXECUTION comments are found, T145 cannot mark itself [X] and must document the findings in `code/tests/failed_execution_report.md`.

**T186 EVIDENCE REQUIREMENT**: T186 must have documented evidence in `code/tests/service_interface_schema_validation.md` showing method count verification (AnomalyDetectorService=7, ThresholdCalibratorService=6).

**T222 EVIDENCE REQUIREMENT**: T222 must have documented evidence from grep verification showing no FAILED-IN-EXECUTION comments exist.

**Phase 7 vs Phase 9 Coverage Clarification**: T163 (Phase 7) generates initial test coverage report. T249 (Phase 9.6) generates final coverage verification as part of contract test infrastructure completeness. T163 is a preliminary check; T249 is the final verification gate before T145. This eliminates redundancy by clarifying T163 as preliminary and T249 as final.