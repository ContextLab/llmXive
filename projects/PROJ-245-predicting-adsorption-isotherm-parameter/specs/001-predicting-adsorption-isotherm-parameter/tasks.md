# Tasks: Predicting Adsorption Isotherm Parameters from Molecular Features

**Input**: Design documents from `/specs/001-predicting-adsorption-isotherm-params/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project structure per `plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per `plan.md` (code/, data/, tests/, contracts/)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (rdkit, scikit-learn, pandas, numpy, shap, pyyaml, pytest)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Define `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml`
- [X] T005 [P] [US1] Create `code/data/synthetic_gen.py` to generate raw synthetic data (N=5000) with noise and random correlations
- [X] T006 [P] [US1] Create `code/data/validate_schema.py` to validate generated data against `contracts/dataset.schema.yaml`
- [X] T007 [P] [US1] Implement `code/data/download.py` to attempt NIST/MOF-1000 fetch and write `verification_log.json` on failure
- [ ] T008 Create base data classes/entities for Adsorbate, Adsorbent, and IsothermParameter
- [X] T009 Configure environment variable management and logging infrastructure in `code/__init__.py`
- [ ] T010 Setup pytest configuration and test directory structure (`tests/unit`, `tests/integration`, `tests/contract`)
- [X] T011 [P] Create `code/main.py` orchestrator to support both synthetic and external data flows (US1, US2, US3)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Curate and Prepare the Adsorption Dataset (Priority: P1) 🎯 MVP

**Goal**: Generate a clean, normalized CSV linking molecular descriptors to isotherm parameters, handling both synthetic and real data sources.

**Independent Test**: Run `code/data/preprocess.py` on the synthetic dataset and verify the output CSV contains exactly `polarizability`, `langmuir_capacity`, `henry_constant`, `surface_area` (m²/g) with no missing values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Contract test for schema compliance in `tests/contract/test_dataset_schema.py`
- [X] T013 [P] [US1] Unit test for RDKit descriptor calculation in `tests/unit/test_descriptors.py`

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement `code/data/descriptors.py` to calculate molecular weight, polar surface area, polarizability, H-bond counts, van der Waals volume (per FR-001), AND kinetic diameter (required for SC-002 consensus check) using RDKit. Note: Kinetic diameter is an additional requirement for SC-002, not FR-001.
- [X] T015 [US1] Implement `code/data/preprocess.py` to filter Type I isotherms, remove entries with missing targets, normalize units (m²/g), and handle missing pore volume (impute/exclude with logging) (FR-002); depends on T014
- [ ] T016 [US1] Implement outlier detection in `code/data/preprocess.py` to flag adsorbates with identical descriptors but conflicting targets; depends on T014, T015; output must be `data/processed/outliers.csv` with columns [material_id, descriptor_hash, target_variance] (Edge Cases)
- [X] T017 [US1] Update `code/main.py` orchestrator to run the full data curation pipeline (Download -> Synthetic Gen -> Preprocess -> Outlier Check); depends on T015, T016

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and Evaluate Predictive Models (Priority: P2)

**Goal**: Train baseline models (Linear, RF, GB) with strict material-level splitting and evaluate performance.

**Independent Test**: Run training on synthetic data; verify that the test set contains no materials present in the training set and that metrics (R², RMSE) are logged.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py` <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
 in "<unicode string>", line 3, column 3:
 - **File Created**: `tests/contrac...
 ^
expected alphabetic or numeric character, but found '*'
 in "<unicode string>", line 3, column 4:
 - **File Created**: `tests/contract...
 ^) -->
- [X] T019 [P] [US2] Integration test for material-level data splitting in `tests/integration/test_data_split.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/models/train.py` to perform material-level split: Group rows by material_id, then split groups, ensuring no material_id exists in both train and test sets (FR-003); depends on T015
- [X] T021 [US2] Implement `code/models/train.py` to train Linear Regression, Random Forest, and Gradient Boosting models (FR-004)
- [X] T022 [US2] Implement 5-fold cross-validation and hyperparameter tuning in `code/models/train.py`
- [X] T023 [US2] Implement `code/models/evaluate.py` to calculate R², RMSE, MAE on the independent test set (SC-001)
- [ ] T024 [US2] Implement null model comparison (predicting mean) and verify a significant RMSE improvement
- [ ] T025 [US2] Implement permutation-based p-value calculation for feature importances
- [X] T026 [US2] Implement Benjamini-Hochberg FDR correction for p-values in `code/models/evaluate.py` (FR-006, SC-005)
- [X] T027 [US2] Update `code/main.py` orchestrator to support running the pipeline on the external literature dataset (Phase 3); depends on T020, T021

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpret Model Drivers via SHAP Analysis (Priority: P3)

**Goal**: Generate SHAP plots and validate feature importance against physicochemical consensus.

**Independent Test**: Run SHAP analysis on the best model; verify the top 3 features include at least 2 from the consensus list (polarizability, kinetic diameter, etc.) if using the external validation dataset.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Contract test for SHAP output format in `tests/contract/test_shap_output.py`
- [ ] T029 [P] [US3] Integration test for feature ranking validation in `tests/integration/test_feature_ranking.py`

### Implementation for User Story 3

- [~] T035a [US3] Curate and save the external validation dataset (Kr on CNTs) to `data/external/kr_cnt.csv`. Source: Manually extract data points from the literature source "Krypton adsorption on carbon nanotubes" () or equivalent verified source. Ensure the CSV matches `contracts/dataset.schema.yaml`. This task creates the missing producer for T035.
- [~] T035 [US3] Implement `code/data/load_external.py` to load the manually curated `data/external/kr_cnt.csv` and validate it against `contracts/dataset.schema.yaml` (Phase 3 External Data); depends on T035a
- [X] T030 [P] [US3] Implement `code/interpret/shap_analysis.py` to generate SHAP summary plots for top-ranked features (FR-005)
- [X] T031 [US3] Implement `code/interpret/shap_analysis.py` to generate partial dependence plots (PDP) for top descriptors
- [X] T032 [US3] Implement validation logic in `code/interpret/shap_analysis.py` to compare top-ranked features against the literature consensus list (polarizability, kinetic diameter, Lennard-Jones energy parameter, quadrupole moment, molecular volume). This logic MUST be implemented to generate `data/validation/sc002_match_report.json` when the external dataset is loaded. The orchestrator (T036) will determine when to execute this check, but the code path and artifact generation are mandatory for the external phase. (SC-002)
- [X] T033 [US3] Implement re-training logic in `code/interpret/shap_analysis.py` on the top 3 descriptors only and verify R² >= 0.60. This logic MUST be implemented to generate `data/validation/sc003_r2_report.json` when the external dataset is loaded. The orchestrator (T036) will determine when to execute this check, but the code path and artifact generation are mandatory for the external phase to satisfy SC-003.
- [~] T034 [US3] Implement diagnostic report generation for cases where R² < 0.5 (suggesting non-linear effects)
- [X] T036 [US3] Update `code/main.py` orchestrator to integrate the external dataset loading and validation flow (Phase 3); depends on T035, T032, T033; must trigger T032 and T033 only when external data is present.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T037 [P] Documentation updates in `README.md` and `docs/`
- [X] T038 Code cleanup and refactoring of `code/main.py` orchestrator
- [~] T039 Performance optimization: Ensure pipeline runtime < 6h on GitHub Actions free-tier (SC-004) <!-- ATOMIZE: requested -->
- [~] T040 [P] Additional unit tests for edge cases (empty datasets, single material) in `tests/unit/`
- [X] T041 Security hardening: Sanitize inputs in `code/data/download.py`
- [~] T042 Run `quickstart.md` validation if available

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

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
Task: "Contract test for schema compliance in tests/contract/test_dataset_schema.py"
Task: "Unit test for RDKit descriptor calculation in tests/unit/test_descriptors.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/descriptors.py to calculate molecular descriptors"
Task: "Implement code/data/preprocess.py to filter Type I isotherms"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Synthetic Data)
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
 - Developer A: User Story 1 (Data Curation)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Interpretation)
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
- **Critical**: All data processing must run on CPU-only runners; no GPU/CUDA dependencies.
- **Critical**: Synthetic data is for pipeline validation only; Phase 3 (External Validation) is required for scientific claims.
- **Critical**: T032 and T033 implement the logic unconditionally; the orchestrator (T036) controls execution based on the dataset.
- **Critical**: T035a ensures the external dataset is reproducible by citing a specific source.