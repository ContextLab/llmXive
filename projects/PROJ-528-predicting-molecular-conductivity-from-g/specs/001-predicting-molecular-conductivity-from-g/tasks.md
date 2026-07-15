# Tasks: Predicting Molecular Conductivity from Graph-Based Features

**Input**: Design documents from `/specs/001-predicting-molecular-conductivity-from-g/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure by executing: `mkdir -p code tests data/raw data/processed contracts docs`
- [X] T002 Initialize Python 3.11 project by creating `requirements.txt` containing: `rdkit`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`
- [X] T003 [P] Configure linting and formatting tools by creating `pyproject.toml` with `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (select=['E', 'F', 'W'], ignore=['E501']) sections

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration module (`code/config.py`) defining constants: `DATA_PATH`, `SEED`, `OUTLIER_SIGMA`, `VIF_THRESHOLD`, `TARGET_VAR`
- [X] T005 [P] Implement data validation utilities in `code/validators.py` with functions `validate_smiles(smiles_str)` and `check_target_range(values, min_log_range=3.0)`
- [X] T006 [P] Setup logging infrastructure in `code/logging_config.py` that configures a rotating file handler to `logs/pipeline.log` with JSON formatting
- [X] T007 Create `code/models.py` with Pydantic classes `Molecule` (fields: smiles, descriptors, target) and `Descriptor` (fields: name, value)
- [X] T008 [P] Implement scaffold splitting utility in `code/scaffold_split.py` ensuring structural diversity and enforcing a standard training/testing split to prevent data leakage (FR-002)
- [ ] T009 Create `contracts/model_results_schema.yaml` defining fields: `r2`, `mae`, `cv_scores`, `sensitivity_data`, `vif_scores`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Load molecular structures and compute graph-based descriptors (Priority: P1) 🎯 MVP

**Goal**: Parse SMILES, compute standard topological descriptors, and implement quantum-inspired proxies as per reviewer feedback.

**Independent Test**: Can be fully tested by running the descriptor computation pipeline on a sample of SMILES strings and verifying that the output table contains all required descriptor columns with valid numeric values for each molecule.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write unit test code (expected to fail) before implementation

- [ ] T010 [P] [US1] Write unit test code (expected to fail) for aromaticity index calculation on benzene (SMILES: "c1ccccc1")
- [ ] T011 [P] [US1] Write unit test code (expected to fail) for conjugation path length on butadiene vs. butane
- [ ] T012 [P] [US1] Write unit test code (expected to fail) for descriptor computation on mixed hybridization molecules

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `load_smiles(path: str) -> pd.DataFrame` in `code/data_loader.py` returning DataFrame with columns [smiles, valid, error_msg]
- [X] T014 [US1] Implement standard graph descriptors (degree dist, path length, ring count) in `code/descriptors.py` (FR-001)
- [ ] T014.5 [US1] Implement standard descriptor decomposition in `code/descriptors.py` to compute 4 scalar metrics for degree (mean, std, max, min) and 4 scalar metrics for path length (mean, std, max, min) to ensure distinct columns
- [X] T015 [US1] Implement Hückel aromaticity index calculation in `code/descriptors.py` (FR-008)
- [X] T016 [US1] Implement aromatic ring count calculation in `code/descriptors.py` (FR-008)
- [X] T020 [US1] Implement bond-order annotation logic in `code/descriptors.py` to estimate bond orders (sp2 vs sp3) and assign effective bond lengths (aromatic vs. aliphatic) based on RDKit bond types and hybridization (Reviewer: linus-pauling-simulated)
- [X] T021 [US1] Implement electronegativity difference calculation in `code/descriptors.py` using Pauling scale values from RDKit atom properties, multiplied by bond length to create a "bond polarity" descriptor (Reviewer: linus-pauling-simulated)
- [X] T022 [US1] Implement fragment-based resonance energy estimation using Hückel Molecular Orbital (HMO) theory approximations for conjugated systems in `code/descriptors.py`, avoiding full DFT (Reviewer: linus-pauling-simulated)
- [ ] T015.5 [US1] Implement physics-based descriptor aggregation in `code/descriptors.py` to compute 'bond_polarity' and 'resonance_energy' as final scalar columns
- [~] T017 [US1] Implement fallback logic for missing quantum descriptors (log warning, use topological proxies) (FR-014)
- [~] T018 [US1] Implement error handling for invalid SMILES and missing conductivity (FR-012)
- [ ] T019 [US1] Write descriptor computation results to `data/processed/descriptors.csv` with EXACT columns: [smiles, status, degree_mean, degree_std, degree_max, degree_min, path_length_mean, path_length_std, path_length_max, path_length_min, aromaticity_index, conjugation_length, ring_count, bond_polarity, resonance_energy] and no NaN values

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train regression models and evaluate predictive performance (Priority: P2)

**Goal**: Split data, train RF/GB models, handle outliers via sensitivity analysis, and validate target variable dynamic range.

**Independent Test**: Can be fully tested by running the training pipeline on a fixed dataset and verifying that both models produce R² scores, MAE values, and cross-validation metrics in a structured results file.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T023 [P] [US2] Integration test for scaffold split ensuring no structural leakage
- [~] T024 [P] [US2] Unit test for log-transformation of target variable
- [~] T025 [P] [US2] Unit test for outlier exclusion threshold logic

### Implementation for User Story 2

- [X] T026 [US2] Implement target variable validation in `code/data_loader.py`: Check for 'conductivity'. If present and log-range >= 3.0, proceed. If missing, check for 'HOMO_LUMO_gap'. If missing, HALT with error "No valid target variable found". If HOMO_LUMO exists, log warning "Conductivity missing; using HOMO-LUMO gap fallback" and trigger T026.5
- [ ] T026.5 [US2] [Conditional] If T026 triggered fallback, set `TARGET_VAR` to 'HOMO_LUMO_gap' in `code/config.py` and log the state change
- [X] T027 [US2] Implement scaffold-based train/test split (80/20 ratio) in `code/scaffold_split.py` AFTER T019 completes (FR-002)
- [~] T028 [US2] Implement log-transformation of the selected target variable (conductivity or HOMO-LUMO)
- [~] T029 [US2] Train Random Forest and Gradient Boosting regressors on log-transformed target (FR-003)
- [~] T030 [US2] Implement 5-fold cross-validation and metric recording (FR-004)
- [~] T031 [US2] Implement threshold filter function and retrain logic for outlier sensitivity, ensuring it reuses the exact split indices from T027 and seed from T004
- [ ] T032 [US2] Implement sensitivity analysis loop calling T031, sweeping thresholds {σ, 3.0σ, 3.5σ}, performing Kruskal-Wallis test on R² variances, and saving results to `data/processed/sensitivity_analysis.json` (FR-007)
- [ ] T032.5 [US2] Generate human-readable summary report of sensitivity analysis variance and Kruskal-Wallis results, logging to `data/processed/sensitivity_report.txt`
- [ ] T033 [US2] Save model results and sensitivity analysis data to `data/processed/model_results.json` with keys: {rf_r2, gb_r2, sensitivity_analysis: [{threshold, r2, kruskal_stat, kruskal_pval},...]}

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate feature importance analysis and correlation plots (Priority: P3)

**Goal**: Analyze feature importance, apply VIF filtering, correct for multiple comparisons, and generate visualizations.

**Independent Test**: Can be fully tested by running the analysis script on a trained model and verifying that feature importance rankings are exported and correlation plots are generated as image files.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T034 [P] [US3] Unit test for VIF calculation and thresholding
- [~] T035 [P] [US3] Unit test for Benjamini-Hochberg correction implementation
- [~] T036 [P] [US3] Unit test for correlation plot generation with confidence intervals

### Implementation for User Story 3

- [~] T037 [P] [US3] Implement VIF calculation for all predictor pairs (FR-013)
- [~] T038 [US3] Implement feature exclusion logic for features with VIF > 10 (FR-013)
- [~] T039 [US3] Implement iterative retraining loop: WHILE any VIF > 10, exclude the highest VIF feature and retrain model using the EXACT split indices from T027 and random seed from T004 (FR-013)
- [~] T040 [US3] Compute feature importance rankings (permutation or tree-based) on the final VIF-filtered model (FR-005)
- [~] T041 [US3] Calculate feature-conductivity (or target) correlations with p-values
- [~] T042 [US3] Apply Benjamini-Hochberg FDR correction to p-values (FR-006)
- [~] T043 [US3] Generate scatter plots with regression lines and 95% CI for top 5 features (FR-005), DEPENDENT ON T040 and T041
- [ ] T044 [US3] Save `data/processed/feature_importance.csv` and `data/processed/corr_plot_top5.png`
- [ ] T045 [US3] Generate final analysis summary with adjusted p-values and top features, saving to `data/processed/analysis_summary.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [~] T046 [P] Documentation updates in `docs/` including reviewer feedback resolution
- [ ] T047 Code cleanup and refactoring
- [ ] T049 [P] Run full pipeline integration test on sample dataset, verifying execution time < 6 hours on 2-core CPU (FR-010)
- [ ] T050 Verify all artifacts match `contracts/` schemas
- [ ] T051 Run quickstart.md validation by executing all commands in `docs/quickstart.md` and logging success/failure to `state/validation_log.json`

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
- **User Story 2 (P2)**: Depends on US1 completion (needs descriptors)
- **User Story 3 (P3)**: Depends on US2 completion (needs trained models)

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
Task: "Write unit test code (expected to fail) for aromaticity index calculation on benzene"
Task: "Write unit test code (expected to fail) for conjugation path length on butadiene vs. butane"

# Launch all models for User Story 1 together:
Task: "Implement standard graph descriptors"
Task: "Implement Hückel aromaticity index calculation"
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
 - Developer A: User Story 1 (Descriptors & Resonance Proxies)
 - Developer B: User Story 2 (Model Training & Sensitivity)
 - Developer C: User Story 3 (Analysis & VIF)
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
- **Reviewer Feedback Addressed**: Tasks T015, T016, T020, T021, T022 explicitly implement the resonance proxies, bond-order annotations, and electronegativity descriptors recommended by reviewer linus-pauling-simulated. Task T039 implements the iterative VIF filtering with reproducibility constraints.
- **Target Variable Logic**: T026 implements the strict Spec requirement (Conductivity) with a conditional fallback (HOMO-LUMO) if Conductivity is missing, ensuring no silent relaxation of FR-003 while enabling the Plan's scope adjustment.