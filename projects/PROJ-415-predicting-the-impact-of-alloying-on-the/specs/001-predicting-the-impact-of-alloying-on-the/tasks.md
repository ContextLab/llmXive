# Tasks: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

**Input**: Design documents from `/specs/001-predict-alloy-diffusion/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `models/`, `reports/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scikit-learn, scipy, requests, pymatgen, pytest)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` with global constants, random seeds, and path definitions
- [X] T005 Implement `code/utils/constants.py` with versioned periodic table data (Metallic Radii, Electronegativity)
- [ ] T006 Implement `code/utils/logging.py` for standardized logging and error tracking
- [~] T007 Setup `data/` directory structure (`raw/`, `curated/`, `artifacts/`) and checksum logic
- [~] T008 [P] Implement `code/data/acquisition.py` to fetch real data from NIST/Materials Project sources using Materials Project API v2 (endpoint: `, params: `elements`, `crystal_system=fcc`, auth via `MP_API_KEY` env var); MUST save output to `data/raw/fetched_diffusion.csv` and MUST log a warning "Data Insufficiency: N < 50" and proceed if N < 50 (resolving conflict with spec Edge Cases) instead of halting; this task replaces the hard halt to satisfy spec Edge Cases and FR-001/FR-002 flow
- [ ] T009 [P] Implement `tests/contract/test_schema.py` to validate data structure against `contracts/diffusion_record.schema.yaml` for the `DiffusionRecord` entity
- [ ] T010 Implement `tests/unit/test_constants.py` to verify periodic table data integrity

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Curation (Priority: P1) 🎯 MVP

**Goal**: Load raw diffusion datasets, filter for FCC self-diffusion, and handle missing values.

**Independent Test**: Run ingestion script against a mock CSV with mixed structures (FCC, BCC, HCP) and verify output contains ONLY FCC self-diffusion entries with standardized units.

### Tests for User Story 1

- [ ] T011 [P] [US1] Contract test for data schema validation in `tests/contract/test_data.py`
- [ ] T012 [P] [US1] Integration test for ingestion pipeline in `tests/integration/test_pipeline.py` (mock data)

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `code/data/ingestion.py` to load CSVs, filter `crystal_structure == "FCC"` and `diffusion_mode == "self"`, and convert units to eV/atom
- [ ] T014 [US1] Implement `code/data/curation.py` to exclude rows with missing solute concentration or missing atomic radii; log exclusions to `data/logs/exclusions.log` (CSV format with `row_id`, `reason_code`) AND explicitly record the **count of excluded rows as the first line** of the log file (e.g., `# EXCLUSION_COUNT: 5`) to satisfy US-1 acceptance scenario 2; log concentration exclusions with reason code 'MISSING_CONCENTRATION' and atomic data errors to `errors/missing_atomic_data.csv`
- [ ] T015 [US1] Implement edge case handling in `code/data/ingestion.py` for single-host-metal datasets: fallback to random split and log the specific warning: 'Stratification by host metal was not possible due to single-class data.'
- [ ] T016 [US1] Implement error logging for missing atomic radii in `code/data/curation.py` (output to `errors/missing_atomic_data.csv`)
- [ ] T017 [US1] Add validation script `tests/unit/test_ingestion.py` to verify filtering logic on mixed-structure mock data

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Engineering and Model Training (Priority: P2)

**Goal**: Compute atomic descriptors, train RF/GB models with GridSearch, and train Linear Regression for statistical inference.

**Independent Test**: Verify `size_mismatch` calculation matches manual math; confirm RF/GB/Linear train on CPU without CUDA errors and output metrics.

### Tests for User Story 2

- [ ] T018 [P] [US2] Unit test for `size_mismatch` calculation in `tests/unit/test_descriptors.py`
- [ ] T019 [P] [US2] Unit test for model training (CPU-only check) in `tests/unit/test_models.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/data/descriptors.py` to compute `size_mismatch = (solute_r - host_r) / host_r` using Metallic Radii from `constants.py`
- [ ] T021 [US2] Implement `code/models/training.py` to train Random Forest with `GridSearchCV` (5-fold cross-validation, `cv=5` explicitly overriding default, max_depth a moderate to deep range, n_estimators a range sufficient to ensure model stability and performance.) maximizing R²; explicitly consume `data/curated/filtered.csv` as the output of T013/T014 (satisfying FR-003)
- [ ] T022 [US2] Implement `code/models/training.py` to train Gradient Boosting with same GridSearch parameters (`cv=5` explicitly set, max_depth will be optimized to a suitable value, n_estimators 50-200); explicitly consume `data/curated/filtered.csv` as the output of T013/T014 (satisfying FR-003)
- [ ] T023 [US2] Implement `code/models/training.py` to train Linear Regression and extract `size_mismatch` coefficient with p-value
- [ ] T024 [US2] Implement logic to save models to `models/final_rf.pkl`, `models/final_gb.pkl`, and coefficients to `models/linear_coef.json`
- [ ] T025 [US2] Implement `code/models/inference.py` to compute R², RMSE, MAE on held-out test set for RF and GB
- [ ] T026 [US2] Handle edge case in `code/models/training.py` where R² < 0.1 (flag as "Low Predictive Power" in report, do not crash)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Threshold Sensitivity (Priority: P3)

**Goal**: Validate statistical significance of the `size_mismatch` coefficient and perform threshold sensitivity analysis.

**Independent Test**: Generate report confirming p < 0.05 for the coefficient and a stability plot for thresholds 0.45–0.55 eV.

### Tests for User Story 3

- [ ] T027 [P] [US3] Unit test for bootstrap confidence interval calculation in `tests/unit/test_stats.py`
- [ ] T028 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/validation/stats.py` to compute 95% bootstrap confidence interval for `size_mismatch` coefficient
- [ ] T030 [US3] Implement `code/validation/stats.py` to verify p-value < 0.05 for the `size_mismatch` coefficient
- [ ] T031 [US3] Implement `code/validation/sensitivity.py` to define baseline shift: `predicted_E_solute - measured_E_pure_host` (using model prediction for solute and **measured** value for pure host metal at 0 at.% from `data/curated/filtered.csv` to satisfy FR-006 Experimental Ground Truth; if 0 at.% row is missing, interpolate from nearest concentrations or fallback to model prediction with a warning); this explicitly resolves the Single Source of Truth conflict (F001) and FR-006 requirement
- [ ] T032 [US3] Implement `code/validation/sensitivity.py` to sweep classification threshold across a narrow range centered around the optimal value (fine-grained steps)
- [ ] T033 [US3] Implement logic in `code/validation/sensitivity.py` to calculate classification stability as **`SD(classification_rate) / RMSE`** (explicit formula to satisfy SC-003); explicitly consume `reports/validation_report.json` to extract the `rmse` field produced by T025 (satisfying ordering constraint)
- [ ] T034 [US3] Generate `reports/validation_report.json` containing R², RMSE, p-values, CI, and stability metrics
- [ ] T035 [US3] Implement `code/main.py` orchestration to run full pipeline: Ingestion → Features → Training → Validation

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `quickstart.md` and `research.md`; **Implement Power Analysis** using post-hoc F-test for regression coefficient (alpha=0.05, target_power=0.80) as required by FR-005 and US-3; explicitly satisfy FR-005 requirement
- [ ] T037 Code cleanup and refactoring of `code/models/training.py` for readability
- [ ] T038 Performance optimization: Ensure GridSearch runs within 15 mins on 2-core CPU
- [ ] T039 [P] Additional unit tests for edge cases (missing atomic data, single host metal) in `tests/unit/`
- [ ] T040 Run `quickstart.md` validation and verify all artifacts are checksummed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on models from US2

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_data.py"
Task: "Integration test for ingestion pipeline in tests/integration/test_pipeline.py"

# Launch all implementation for User Story 1 together:
Task: "Implement code/data/ingestion.py to load CSVs..."
Task: "Implement code/data/curation.py to exclude rows..."
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
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Critical**: All data tasks MUST use real, reachable URLs (NIST/Materials Project). No synthetic data generation for hypothesis validation.
- **Critical**: All models MUST run on CPU-only hardware (no CUDA, no 8-bit/4-bit quantization).