# Tasks: Quantifying the Effect of Alloying Elements on the Glass-Forming Ability of Metallic Glasses

**Input**: Design documents from `/specs/001-quantifying-the-effect-of-alloying-eleme/`
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

- [ ] T001 Create project structure per implementation plan by executing: `mkdir -p code/data code/models code/utils code/config data/raw data/processed state output tests/contract tests/integration tests/unit docs/paper docs/reports` (projects/PROJ-124-quantifying-the-effect-of-alloying-eleme/)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pymatgen, scikit-learn, pandas, numpy, shap, statsmodels, scipy)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004a [P] Create `data/raw/` and `data/processed/` directory structure (filesystem operation)
- [ ] T004b [P] Implement `code/data/checksums.py` with functions `generate_checksum(file_path)` and `verify_checksum(file_path, expected_hash)` to generate `.sha256` files and verify data integrity (Constitution Principle III)
- [ ] T005 [P] Implement `code/utils/state_manager.py` with function `update_artifact_hash(path)` that computes SHA-256 and appends to `state/artifact_hashes.yaml` (Constitution Principle V)
- [ ] T006 [P] Create base logging infrastructure and error handling for pipeline failures
- [ ] T007 Create `code/utils/` module for shared utilities (novelty check, SHAP utils)
- [ ] T008a Configure environment configuration management for dataset URLs and random seeds
- [ ] T008b Define and save the '30 most abundant metallic elements' list to `data/config/elements.yaml` and `code/config/elements.py` (Al, Ca, Fe, Mg, Ti, Na, K, Zn, Si, Zr, Cu, Ni, Cr, Mn, V, Sn, Pb, Ag, Au, Pd, Pt, Mo, W, Nb, Ta, Hf, Y, La, Ce, Sc) for use by T030
- [ ] T008c [P] Download or generate `data/known_alloys.csv` for novelty checks (FR-013); if external source is unavailable, create a placeholder file with a clear warning to be populated later, but the task must ensure the file path exists before T036 runs.
- [ ] T009 Setup `contracts/` directory for schema definitions (CSV and JSON)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Ingest raw composition data, parse elemental fractions, and compute physics-based descriptors and interaction features using Pymatgen.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying that the output CSV contains the original composition columns plus the computed descriptor columns with no null values for known elements, and that the row count matches the sum of source datasets.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test in `tests/contract/test_data_schema.py::test_schema_matches_contracts` validating against the *expected* schema defined in `contracts/data_schema.yaml` (derived from FR-001), ensuring the test can run before data download (US-1)
- [ ] T011 [P] [US1] Integration test in `tests/integration/test_data_pipeline.py` for end-to-end data ingestion and feature engineering

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download.py` to fetch Dataset (Recent Experimental GFA)

The research question remains: How do specific architectural choices impact the efficiency of Generative Flow Algorithms? The method involves comparative analysis of algorithmic performance across varying computational constraints. References: Smith et al. (2020), arXiv:2103.01234. from HuggingFace with retry logic and SHA-256 verification; success condition: produces `data/raw/gfa_dataset.csv` and `data/raw/gfa_dataset.csv.sha256` (FR-001)
- [ ] T013 [US1] Implement `code/data/ingest.py` to parse CSV, normalize elemental fractions to sum to 1.0 ± 0.01, and log warnings for unknown elements (US-1, FR-001)
- [ ] T014 [US1] Implement `code/data/features.py` to compute atomic radius, electronegativity, VEC_raw, and weighted mean VEC_avg using Pymatgen; output: `data/processed/features.csv` with columns [composition, log10_Rc, atomic_radius_mean, electronegativity_mean, VEC_avg, size_mismatch, etc.] (FR-002)
- [ ] T015 [US1] Implement pairwise size mismatch descriptor calculation in `code/data/features.py` for unique element pairs (FR-002b)
- [ ] T016 [US1] Add validation logic to exclude rows with unknown elements and log specific warnings (US-1, Edge Cases)
- [ ] T017 [US1] Save processed feature-engineered dataset to `data/processed/features.csv` with `source_row_id` traceability (Constitution Principle IV)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting models, perform LOCO cross-validation, handle heteroscedasticity, and generate SHAP values.

**Independent Test**: Can be fully tested by running the training script and verifying that two distinct model artifacts are saved, cross-validation scores are printed, the selected model has an MAE lower than a baseline mean-predictor, and a SHAP feature importance report is generated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for model artifact schema in `tests/contract/test_model_artifacts.py`
- [ ] T019 [P] [US2] Integration test for LOCO CV and model selection in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/models/train.py` to train RandomForestRegressor and GradientBoostingRegressor with hyperparameter grids ≤30; output: `best_model.pkl` and `best_model_weighted.pkl` (if applicable) and print LOCO-MAE scores (FR-003)
- [ ] T021 [US2] Implement LOCO cross-validation logic in `code/models/train.py` based on primary metallic element families; output: `data/processed/X_train.pkl` (features only, no labels) and `data/processed/y_train.pkl` (labels) for downstream DoA (FR-004)
- [ ] T022 [US2] Implement model selection logic to save `best_model.pkl` based on lowest LOCO-MAE (US-2, FR-003)
- [ ] T023 [US2] Implement `code/models/validate.py` to perform Breusch-Pagan test for heteroscedasticity; output: `state/heteroscedasticity_test.json` containing `p_value` and `heteroscedasticity_flag` (boolean) (FR-010)
- [ ] T024 [US2] Implement weighted loss retraining in `code/models/validate.py` (binning residuals, local variance estimation) if `heteroscedasticity_flag` is true; save `best_model_weighted.pkl` (FR-010)
- [ ] T025 [US2] Implement `code/utils/shap_utils.py` to generate global SHAP values for the best model (FR-011)
- [ ] T026 [US2] Save `shap_feature_importance.json` with global SHAP values (FR-012)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Novel Composition Screening and Ranking (Priority: P3)

**Goal**: Generate unique ternary combinations, predict GFA, check novelty, apply Domain of Applicability penalties, and rank candidates.

**Independent Test**: Can be fully tested by running the screening script and verifying that the output CSV contains up to 10 rows, sorted by predicted $log_{10}(R_c)$, with confidence intervals and novelty status fields.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for candidates CSV schema in `tests/contract/test_candidates_schema.py`
- [ ] T029 [P] [US3] Integration test for screening and ranking pipeline in `tests/integration/test_screening.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/models/predict.py` to generate all unique ternary combinations from the most abundant metallic elements defined in `data/config/elements.yaml` (FR-005)
- [ ] T031 [US3] Implement prediction logic using the best model (or weighted if applicable) for all ternary combinations (FR-005)
- [ ] T032 [US3] Implement `code/models/predict.py::calculate_doa()` to calculate the Domain of Applicability (DoA) using the **convex hull of the training feature space** loaded from `data/processed/X_train.pkl`; save `state/convex_hull_model.pkl`. If the convex hull cannot be computed, the task MUST raise a fatal error (as per FR-009 strictness) rather than falling back to PCA (FR-009)
- [ ] T033 [US3] Apply +1.0 penalty to $log_{10}(R_c)$ for candidates outside DoA before ranking (FR-009)
- [ ] T034 [US3] Implement filtering logic to retain candidates in the bottom 10th percentile of the dataset distribution or < 4.0 (FR-006)
- [ ] T035 [US3] Generate **exactly 10 bootstrapped Random Forest models** on the training data to create an ensemble; predict on candidates; calculate confidence intervals (lower and upper percentiles) from the variance of these 10 predictions; output confidence intervals for each candidate (FR-003, FR-007)
- [ ] T036 [US3] Implement novelty check in `code/utils/novelty.py` against `data/known_alloys.csv`; output `novelty_status` MUST be strictly `"novel"` or `"known"` per FR-013 (no fallback allowed); if the list is missing, the task must fail or flag the check as impossible (FR-013)
- [ ] T037 [US3] Rank candidates by ascending `final_score` (predicted + penalty) and select a representative subset of top-ranked items (FR-006)
- [ ] T038 [US3] Generate `output/candidates.csv` with top 10 candidates, predictions, CIs, and risk scores (FR-006, FR-007)
- [ ] T039 [US3] Generate `output/verification_requests.json` containing a list of 10 objects with fields: `composition`, `predicted_log10_Rc`, `confidence_interval`, `novelty_status` (must be strictly "novel" or "known"), `status` ("pending_verification"); run schema validator to ensure `novelty_status` is strictly "novel" or "known" before saving (FR-008, FR-013)
- [ ] T040 [US3] Handle edge case of zero candidates below threshold by outputting empty CSV with header (Edge Cases)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041a [P] Draft `docs/paper/01-introduction.md` (background, problem statement)
- [ ] T041b [P] Draft `docs/paper/02-methods.md` (data pipeline, model training, screening)
- [ ] T042 Code cleanup and refactoring across `code/` modules
- [ ] T043 Performance optimization for combinatorial generation and model training within CPU constraints; success metric: `code/models/predict.py` runtime < 3 hours (to ensure total pipeline ≤ 6 hours) and memory < 7GB on GitHub Actions
- [ ] T044 [P] Additional unit tests for feature engineering logic in `tests/unit/test_features.py`
- [ ] T045 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T046 Verify all artifacts in `state/artifact_hashes.yaml` are correctly updated

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model from US2 and data from US1

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
Task: "Contract test for dataset schema validation in tests/contract/test_data_schema.py::test_schema_matches_contracts"
Task: "Integration test for data ingestion and feature engineering in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py"
Task: "Implement code/data/ingest.py"
Task: "Implement code/data/features.py"
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