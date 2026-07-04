# Tasks: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

**Input**: Design documents from `/specs/001-predict-tg-metallic-glasses/`
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

- [ ] T001 Create project structure per implementation plan (projects/PROJ-342-predicting-the-influence-of-alloying-on-/)
- [ ] T002 Initialize Python 3.10 project with pinned dependencies (pandas, scikit-learn, numpy, mendeleev==0.31.0, pyyaml, jsonschema)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `data/raw/` and `data/processed/` directories with `.gitkeep` and checksum tracking logic
- [ ] T005 [P] Implement `code/contracts/` schema loaders for `dataset.schema.yaml` and `artifact.schema.yaml`
- [ ] T006 Create `code/__init__.py` and configure logging infrastructure for pipeline steps
- [ ] T007 Setup environment configuration management (`.env` for DOIs, `config.yaml` for seeds/limits)
- [ ] T008 Implement resource monitoring wrapper (CPU time/RAM) to enforce FR-005 (6h/7GB limits)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Validation (Priority: P1) 🎯 MVP

**Goal**: Load and validate metallic glass datasets from Zenodo, ensuring data integrity before analysis.

**Independent Test**: Can be fully tested by executing the data loading script and verifying the output dataframe contains > 0 rows, no null Tg or composition fields remain, and a log reports the retention rate.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation.**
> **[P] Tag Note**: T010 and T011 are parallel-safe *with respect to each other* (they test different aspects). They logically depend on the existence of the code being tested, but can be written concurrently with implementation tasks if the team is split. Tests MUST be written and failing before implementation begins.

- [ ] T010 [P] [US1] Contract test for dataset schema validation in `tests/unit/test_ingest_schema.py`
- [ ] T011 [P] [US1] Integration test for Zenodo DOI reachability and data retention in `tests/integration/test_data_ingestion.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/ingest.py` to fetch Zenodo DOI 10.5281/zenodo.10043838 (fallback: 10.5281/zenodo.11023456)
- [ ] T013 [US1] Implement data cleaning logic in `code/ingest.py`: drop records missing Tg or full composition (FR-001)
- [ ] T014 [US1] Implement retention rate logging and save cleaned data to `data/processed/cleaned_mg.csv`
- [ ] T015 [US1] Add error handling for invalid DOIs: if primary DOI fails, attempt fallback to secondary DOI; if both fail, halt with DATA_UNAVAILABLE (FR-001)
- [ ] T016 [US1] Write data retention rate and record counts to `data/ingestion_stats.json` to satisfy SC-003 and Single Source of Truth (SC-003)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training, Feature Engineering, and Sensitivity Analysis (Priority: P2)

**Goal**: Compute atomic descriptors, train a Gradient Boosting model with LOFO CV, and prepare artifacts for analysis.
**Note**: Sensitivity Analysis (FR-006) and VIF Calculation (FR-007) are moved to Phase 5 (US3) to align with `code/analyze.py` per Plan and Spec.

**Independent Test**: Can be fully tested by running the training pipeline and confirming the model artifacts contain performance metrics (R², MAE), feature importances, and a diagnostic log containing the weighted mean radius.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for descriptor calculation logic (radius mismatch, VEC, electronegativity) in `tests/unit/test_descriptors.py`
- [ ] T019 [P] [US2] Integration test for LOFO split correctness (no family leakage) in `tests/integration/test_train_cv.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/descriptors.py` to compute radius mismatch, electronegativity difference, VEC using `mendeleev==0.31.0` (FR-002)
- [ ] T021 [P] [US2] Implement `code/descriptors.py` to calculate 'weighted mean radius' for diagnostic logging only (FR-002, exclude from model)
- [ ] T022 [US2] Implement `code/train.py` with GradientBoostingRegressor and Leave-One-Family-Out (LOFO) cross-validation (FR-003)
- [ ] T023 [US2] Implement grid search in `code/train.py` for hyperparameter optimization (≤10 combos) (FR-003)
- [ ] T024 [US2] Save model artifacts (`artifacts/models/`) and metrics (`artifacts/metrics/`) including R², MAE, and feature importances (SC-001)
- [ ] T025 [US2] Add resource monitoring checks to ensure runtime < 6h and RAM < 7GB (FR-005, SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Result Interpretation, Reporting, and Statistical Validation (Priority: P3)

**Goal**: Generate reports with statistical validation, FDR correction, and associational framing. Perform Sensitivity Analysis and VIF checks here as per Plan/Spec.

**Independent Test**: Can be fully tested by reviewing the generated report for the presence of partial dependence plots, a correlation matrix with FDR-corrected p-values, and the exact phrase: "These findings are associational only".

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T040 [P] [US3] Contract test for report content validation (no causal language) in `tests/contract/test_report_content.py`
- [ ] T041 [P] [US3] Integration test for statistical validation (FDR, VIF) in `tests/integration/test_statistical_validation.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/analyze.py` for Pearson/Spearman correlation calculation between predictors (FR-009). **Input**: `data/processed/descriptors.csv`
- [ ] T034 [US3] Implement `code/analyze.py` for Benjamini-Hochberg FDR correction on correlations (α ≤ 0.05) (FR-008). **Input**: Results from T033. **Note**: Overrides Plan's contradictory "Bonferroni" mention in Complexity Tracking; Spec FR-008 mandates FDR.
- [ ] T035 [US3] Implement `code/analyze.py` for VIF calculation. If VIF > 5, iteratively drop the highest VIF predictor until all remaining predictors have VIF < 5 (FR-007, Plan Complexity Tracking). **Input**: `data/processed/descriptors.csv`. **Note**: Plan requires iterative remediation for stability, overriding Spec FR-007's initial "flag only" draft.
- [ ] T036 [US3] Implement sensitivity analysis in `code/analyze.py`: sweep `max_depth` ∈ {3, 5, 7} on the best model from T022, report R² variance (FR-006). **Input**: `artifacts/models/best_model.pkl`
- [ ] T037 [US3] Implement `code/analyze.py` for bootstrapping (a sufficient number of resamples) to calculate 95% CI for feature importance (SC-002). **Input**: `artifacts/models/best_model.pkl`
- [ ] T038 [US3] Save stability metrics (95% CI for feature importance) to `artifacts/metrics/stability_metrics.json` (SC-002)
- [ ] T039 [US3] Implement `code/report.py` to generate visualizations (partial dependence plots, correlation matrices) AND include numerical stability metrics (SC-002)
- [ ] T040 [US3] Implement `code/report.py` to enforce associational language (FR-004) and insert "These findings are associational only"
- [ ] T041 [US3] Generate final report artifact including sensitivity analysis results and VIF diagnostics
- [ ] T042 [US3] Validate report against `artifact.schema.yaml` (Single Source of Truth)
- [ ] T048 [P] [US3] Contract test for dataset schema validation in `tests/unit/test_ingest_schema.py` (Renumbered from T024 to avoid ID collision)
- [ ] T049 [P] [US3] Integration test for Zenodo DOI reachability and data retention in `tests/integration/test_data_ingestion.py` (Renumbered from T025 to avoid ID collision)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Documentation updates in `docs/` (README, quickstart.md)
- [ ] T044 Code cleanup and refactoring (remove unused imports, ensure type hints)
- [ ] T045 Performance optimization (ensure vectorized operations in descriptors to stay within 7GB RAM)
- [ ] T046 [P] Run quickstart.md validation to ensure end-to-end reproducibility
- [ ] T047 Verify all tasks execute on CPU-only CI (a minimal core configuration with constrained RAM) without GPU dependencies

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires model artifacts from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Descriptors before services/training
- Training before analysis/reporting
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema validation in tests/unit/test_ingest_schema.py"
Task: "Integration test for Zenodo DOI reachability and data retention in tests/integration/test_data_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingest.py to fetch Zenodo DOI..."
Task: "Implement data cleaning logic in code/ingest.py..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (ensure data is valid)
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
   - Developer A: User Story 1 (Data)
   - Developer B: User Story 2 (Modeling)
   - Developer C: User Story 3 (Reporting & Analysis)
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
- **Critical**: Ensure no tasks require GPU (CUDA) or 8-bit/4-bit quantization libraries. All models must run on CPU.
- **Note on Plan Discrepancy**: The Plan currently suggests Bonferroni correction, but the Spec (FR-008) mandates Benjamini-Hochberg (FDR). This tasks.md follows the Spec (FDR). The Plan requires correction.
- **Note on VIF Remediation**: Task T035 implements iterative VIF remediation (dropping features) as required by the Plan's Complexity Tracking, overriding the Spec's initial "flag only" draft to ensure alignment with the final Plan requirement.