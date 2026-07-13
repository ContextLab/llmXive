# Tasks: Reconstructing Solar Irradiance from Historical Sunspot Records

**Input**: Design documents from `/specs/001-reconstructing-solar-irradiance/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create project directory structure: `code/`, `tests/`, `data/raw/`, `data/processed/`, `code/models/`, `code/analysis/`
- [ ] T001b [P] Create `__init__.py` files in all `code/` subdirectories and `tests/`
- [ ] T001c [P] Create `.gitkeep` files in `data/raw/` and `data/processed/` to ensure directories are tracked
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pin `pandas`, `scikit-learn`, `numpy`, `scipy`, `requests`, `pyyaml`)
- [ ] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` with paths, random seeds, and constants (FR-002 gap logic, FR-009 thresholds)
- [ ] T005 [P] Create `contracts/dataset_schema.schema.yaml` defining `SunspotRecord` and `TSIRecord` entities
- [~] T006 [P] Create `contracts/output_schema.schema.yaml` defining reconstruction and validation report schemas
- [~] T007 Implement `code/data/__init__.py` and base logging infrastructure
- [~] T008 Configure environment variable management for data paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Cycle-Specific TSI Reconstruction Model (Priority: P1) 🎯 MVP

**Goal**: Ingest GSN and TSI data, train non-linear models with Cycle ID features, and validate via Leave-One-Cycle-Out.

**Independent Test**: The model can be fully tested by running the training pipeline on the satellite-era data using a leave-one-cycle-out validation scheme and verifying it produces a valid reconstruction file with calculated RMSE and R² metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. Running tests can be parallel, but writing them is sequential.

- [~] T010 [P] [US1] Unit test for data ingestion in `tests/test_ingestion.py` (verify SILSO/SORCE URL reachability)
- [~] T011 [P] [US1] Unit test for gap filling logic in `tests/test_preprocessing.py` (verify ≥1yr gaps use GSN=0 proxy, not TSI units)
- [~] T012 [P] [US1] Integration test for LOCO CV in `tests/test_model_training.py` (verify cycle holdout logic)

### Implementation for User Story 1

- [~] T013 [US1] Implement `code/data/ingestion.py` to fetch GSN (SILSO) and TSI (SORCE/TIM) from verified URLs to `data/raw/`
- [~] T014 [US1] Implement `code/data/preprocessing.py`:
 - Part 1: Linear interpolation for gaps < 1 year in GSN data.
 - Part 2: Apply **GSN=0 proxy** (not TSI units) for gaps ≥ 1 year, per FR-002.
 - Detect cycle boundaries using SILSO method.
 - Output: `data/processed/preprocessed_data.parquet` (final, atomic write).
- [~] T015 [US1] Implement `code/models/train.py`:
 - Utilize **Cycle ID** (from official SILSO historical cycle list, mapped as categorical integer) as a feature, per FR-003 and Constitution Principle VI.
 - Train Random Forest (max_depth=10, n_estimators=100) and Gaussian Process (RBF kernel).
 - Execute **Leave-One-Cycle-Out (LOCO)** Cross-Validation: Train on all cycles except one, validate on the held-out cycle.
 - Calculate RMSE and R² for each held-out cycle.
 - Save best model artifact to `code/models/artifacts/best_model.joblib`.
 - Generate `data/processed/cv_report.json` containing per-cycle RMSE, R², and model selection rationale.
- [~] T016 [US1] Implement `code/models/predict.py` (basic inference for held-out block validation)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3.5: Fallback Model & Sensitivity Analysis (Critical for FR-003, FR-004, FR-009)

**Purpose**: Train the Cycle-Agnostic fallback model, derive cycle-specific offsets for sensitivity analysis, and validate robustness. This phase is a **blocking prerequisite** for Phase 4 (US2).

- [~] T019 [US1/Phase3.5] Implement `code/models/train_fallback.py`:
 - Train a **single Cycle-Agnostic fallback model** (GSN-only, no Cycle ID features) on the full satellite-era dataset (2003–present).
 - **Derive per-cycle baseline offsets**: Calculate the mean residual of each satellite-era cycle against this single global fallback model.
 - Save the fallback model to `code/models/artifacts/fallback_model.joblib`.
 - Save the per-cycle baseline offsets to `data/processed/cycle_specific_coefficients.json`.
- [~] T029 [US1/Phase3.5] Implement `code/analysis/sensitivity.py` to:
 - Load `data/processed/cycle_specific_coefficients.json` (per-cycle baseline offsets from T019).
 - Sweep **inconsistency tolerance threshold** over absolute differences {0.01, 0.05, 0.1}, per FR-009.
 - Measure **reconstruction stability** defined as the standard deviation of RMSE across the sweep, comparing against the Cycle-Agnostic baseline.
 - Output: `data/processed/sensitivity_report.json`.
- [~] T031 [US1] Verify computational resource usage (RAM < 7 GB, Runtime < 6h) in `tests/test_performance.py` (FR-008, SC-004).

**Checkpoint**: US1 complete including fallback and sensitivity validation. Phase 4 can now begin.

---

## Phase 4: User Story 2 - Pre-Satellite TSI Reconstruction Generation (Priority: P2)

**Goal**: Apply the calibrated model (and Cycle-Agnostic fallback) to the pre-satellite GSN record (1610–2002) to generate TSI reconstruction with uncertainty bands.

**Independent Test**: The feature is tested by running the application of the trained model to the pre-satellite GSN subset and verifying the output contains a complete time series with corresponding lower and upper uncertainty bounds.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T018 [P] [US2] Unit test for Cycle-Agnostic fallback logic in `tests/test_preprocessing.py`
- [~] T040 [P] [US2] Unit test for bootstrap resampling in `tests/test_stats.py` (verify 1000 iterations)

### Implementation for User Story 2

- [~] T020 [US2] Implement `code/models/predict.py` (extended):
 - Load pre-satellite GSN (historical–pre-satellite era).
 - Apply trained RF/GP model (from T015) for cycles present in training.
 - Apply **Cycle-Agnostic fallback model** (from T019) for unseen cycles.
 - Generate prediction intervals for uncertainty bands.
 - Output: `data/processed/reconstruction_1610_2002.parquet`.
- [~] T021 [US2] Implement `code/analysis/stats.py`:
 - Bootstrap resampling with **at least 1000 iterations** for variance comparison across Maunder, Dalton, and Modern minima (FR-005, Constitution Principle VII).
- [~] T022 [US2] Generate `data/processed/reconstruction_1610_2002.parquet` with TSI values and uncertainty bounds (if not already done in T020).
- [ ] T023 [US2] Generate `data/processed/variance_analysis.json` with bootstrap results.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Baseline Comparison and Methodological Validation (Priority: P3)

**Goal**: Compare new reconstruction against 2007 baseline and CMIP6, calculate error reduction, and ensure associational framing.

**Independent Test**: The feature is tested by executing the comparison module which ingests the new reconstruction, the 2007 baseline, and CMIP6 data, outputting a final report with the specific error reduction metric.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for error reduction calculation in `tests/test_comparison.py`
- [ ] T025 [P] [US3] Unit test for FDR correction logic in `tests/test_stats.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/analysis/comparison.py`:
 - Load a baseline year and CMIP v3.2 data.
 - Calculate RMSE over the overlapping satellite era (2016–present), per SC-001.
 - Compute percentage error reduction (SC-001).
- [ ] T027 [US3] Implement `code/analysis/stats.py` (extended):
 - Apply multiple-comparison correction (Bonferroni or FDR) for hypothesis tests (FR-007).
 - Ensure all findings are framed as associational in output text (FR-006).
- [ ] T028 [US3] Generate `data/processed/final_report.md` containing error reduction metrics, variance comparisons, and methodological constraints.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032a [P] Update `README.md` installation section with environment setup instructions.
- [ ] T032b [P] Update `README.md` usage section with pipeline execution commands.
- [ ] T032c [P] Create `docs/data_dictionary.md` documenting input/output schemas.
- [ ] T033 Code cleanup and refactoring
- [ ] T034 [P] Run `quickstart.md` validation to ensure full pipeline reproducibility
- [ ] T035 Verify `research.md` citations match dataset URLs in `code/data/ingestion.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (Phase 3)**: Can start after Foundational.
 - **Phase 3.5 (Fallback Model & Sensitivity)**: Depends on T015 (US1 model artifact) and T014 (preprocessed data). **Blocks Phase 4**.
 - **User Story 2 (Phase 4)**: **Depends on T015 (US1 model) AND T019 (Fallback model)**. Cannot start until Phase 3.5 is complete.
 - **User Story 3 (Phase 5)**: Depends on T020 (US2 reconstruction output).
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: **Strictly Sequential**: Depends on Phase 3.5 completion (T015 + T019).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 reconstruction output
- **Sensitivity (Phase 3.5)**: Depends on US1 completion (specifically T019 output).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion/preprocessing before model training
- Model training before prediction
- Prediction before comparison/reporting
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start.
- **US2 and US3 cannot start in parallel with US1 or Phase 3.5**; they must wait for US1 and Phase 3.5 artifacts.
- All tests for a user story marked [P] can run in parallel (after writing).
- Sensitivity analysis (Phase 3.5) runs sequentially after US1 training, before US2.

---

## Parallel Example: User Story 1

```bash
# Step 1: Write tests (Sequential - must fail first)
Task: "Write Unit test for data ingestion in tests/test_ingestion.py"
Task: "Write Unit test for gap filling logic in tests/test_preprocessing.py"

# Step 2: Run tests and Implement (Parallel execution of independent files)
Task: "Run Unit test for data ingestion"
Task: "Run Unit test for gap filling logic"
Task: "Implement code/data/ingestion.py"
Task: "Implement code/data/preprocessing.py"
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
3. Add Phase 3.5 (Fallback + Sensitivity) → Generate coefficients and stability report
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Model Training)
 - Developer B: Phase 3.5 (Fallback Model + Sensitivity) - *Depends on A's output*
 - Developer C: User Story 2 (Reconstruction) - *Depends on A & B*
3. Stories complete and integrate sequentially.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: Ensure all models (RF, GP) use default precision and no GPU libraries (FR-008).
- **Data Integrity**: Use only real datasets from SILSO/SORCE; no synthetic data generation for inputs.
- **Spec Override**: Task T015 explicitly uses Cycle ID features as per FR-003, overriding the Plan's Cycle Phase strategy (Plan updated to align).
- **Unit Correction**: Tasks T014, T011 now correctly specify GSN=0 proxy for gaps, not TSI units.
- **Bootstrap Rigor**: Task T021 explicitly mandates 1000 iterations.
- **Sensitivity Definition**: Task T029 explicitly defines sweep values and stability metric.