---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Molecular Dipole Moments with Graph Neural Networks

**Input**: Design documents from `/specs/001-predicting-molecular-dipole-moments/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/001-predicting-molecular-dipole-moments/code/`, `projects/001-predicting-molecular-dipole-moments/tests/`, `projects/001-predicting-molecular-dipole-moments/data/`, `projects/001-predicting-molecular-dipole-moments/state/`
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below match plan.md structure under `projects/001-predicting-molecular-dipole-moments/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in `projects/001-predicting-molecular-dipole-moments/`
- [ ] T002 Initialize Python 3.11 project with requirements.txt in `projects/001-predicting-molecular-dipole-moments/code/requirements.txt`
- [ ] T003 [P] Configure linting and formatting tools (black, flake8, isort) in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (data/raw/, data/processed/, data/checkpoints/) per plan.md in `projects/001-predicting-molecular-dipole-moments/`
- [ ] T005 [P] Initialize state tracking with state/projects/001-predicting-molecular-dipole-moments.yaml
- [ ] T006 [P] Configure pytest 7.4.3 with contract test framework in `projects/001-predicting-molecular-dipole-moments/tests/`
- [ ] T007 [P] Create YAML contract schema files in `projects/001-predicting-molecular-dipole-moments/tests/contracts/` (molecule.schema.yaml, feature_set.schema.yaml, model_output.schema.yaml)
- [ ] T008 Configure environment configuration management with .env.example and config.py in `projects/001-predicting-molecular-dipole-moments/code/`
- [ ] T009 Setup reproducibility framework with pinned random seeds in `projects/001-predicting-molecular-dipole-moments/code/utils/reproducibility.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Preparation and Baseline Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Download QM9 dataset, filter to 10k random subset, extract 3D coordinates and 2D descriptors for baseline comparison

**Independent Test**: Verify data files exist, subset size equals 10k, and both 3D and 2D feature matrices are generated with no missing values

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for molecule schema in `projects/001-predicting-molecular-dipole-moments/tests/contract/test_molecule_schema.py`
- [ ] T011 [P] [US1] Contract test for feature_set schema in `projects/001-predicting-molecular-dipole-moments/tests/contract/test_feature_set_schema.py`
- [ ] T012 [P] [US1] Integration test for QM9 download pipeline with memory profiling (< 8GB constraint) in `projects/001-predicting-molecular-dipole-moments/tests/integration/test_qm9_download.py`
- [ ] T013 [P] [US1] Unit test for 3D coordinate extraction in `projects/001-predicting-molecular-dipole-moments/tests/unit/test_extract_3d_coords.py`
- [ ] T014 [P] [US1] Unit test for 2D descriptor generation in `projects/001-predicting-molecular-dipole-moments/tests/unit/test_extract_2d_descriptors.py`

### Implementation for User Story 1

- [ ] T015 [US1] Implement QM9 download with integrity verification in `projects/001-predicting-molecular-dipole-moments/code/data/download_qm9.py` (FR-001, DOI 10.1038/sdata.2014.22 via HuggingFace datasets.load_dataset())
- [ ] T016 [US1] Create 10k random subset with reproducibility seed in `projects/001-predicting-molecular-dipole-moments/code/data/create_subset.py` (MUST precede T017/T018 per spec computational efficiency requirement FR-010)
- [ ] T017 [US1] Implement 3D coordinate, atom type, and bond connectivity extraction in `projects/001-predicting-molecular-dipole-moments/code/data/preprocess_3d.py` (FR-002, depends on T016)
- [ ] T018 [US1] Implement 2D Morgan fingerprints and Coulomb matrix generation in `projects/001-predicting-molecular-dipole-moments/code/data/extract_2d_descriptors.py` (FR-003, depends on T016)
- [ ] T019 [US1] Add validation for missing 3D coordinates handling in `projects/001-predicting-molecular-dipole-moments/code/data/handle_missing_coords.py` (edge case acceptance criteria)
- [ ] T020 [US1] Generate output files: data/processed/molecules_10k.parquet, features_3d.parquet, features_2d.parquet
- [ ] T021 [US1] Handle QM9 DOI link inaccessible edge case with retry/fallback in `projects/001-predicting-molecular-dipole-moments/code/data/download_qm9.py` (Edge Case: DOI inaccessible)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Evaluation Pipeline (Priority: P2)

**Goal**: Train lightweight SchNet-style GNN and Random Forest baseline on same train/test splits, evaluate both on held-out test set using MAE and RMSE for dipole moments

**Independent Test**: Verify training with 50 epochs and early stopping, both models produce MAE and RMSE scores on test set

### Tests for User Story 2

- [ ] T022 [P] [US2] Contract test for model_output schema with memory profiling (< 8GB constraint) in `projects/001-predicting-molecular-dipole-moments/tests/contract/test_model_output_schema.py`
- [ ] T023 [P] [US2] Integration test for GNN training pipeline in `projects/001-predicting-molecular-dipole-moments/tests/integration/test_gnn_training.py`
- [ ] T024 [P] [US2] Integration test for Random Forest training pipeline in `projects/001-predicting-molecular-dipole-moments/tests/integration/test_rf_training.py`
- [ ] T025 [P] [US2] Unit test for MAE/RMSE metric computation in `projects/001-predicting-molecular-dipole-moments/tests/unit/test_metrics.py`

### Implementation for User Story 2

- [ ] T026 [P] [US2] Implement SchNet-style GNN architecture in `projects/001-predicting-molecular-dipole-moments/code/models/schnet_gnn.py` (FR-004, CPU-only mode)
- [ ] T027 [P] [US2] Implement Random Forest baseline in `projects/001-predicting-molecular-dipole-moments/code/models/random_forest_baseline.py` (FR-005)
- [ ] T028 [US2] Implement GNN training with 5 random seeds, 50 epochs, early stopping (patience=10) in `projects/001-predicting-molecular-dipole-moments/code/training/train_gnn.py` (FR-005)
- [ ] T029 [US2] Implement Random Forest training with 5 random seeds in `projects/001-predicting-molecular-dipole-moments/code/training/train_rf.py` (FR-005)
- [ ] T030 [US2] Implement identical train/test split generation across seeds in `projects/001-predicting-molecular-dipole-moments/code/training/split_data.py`
- [ ] T031 [US2] Implement MAE and RMSE metric computation in `projects/001-predicting-molecular-dipole-moments/code/training/evaluate.py` (FR-006)
- [ ] T032 [US2] Validate predictions against QM9 DFT reference data (B3LYP/6-31G(2df,p)) in `projects/001-predicting-molecular-dipole-moments/code/analysis/validate_dft.py` (FR-011, during evaluation phase)
- [ ] T033 [US2] Save model checkpoints to data/checkpoints/model_seed_{N}.pt and rf_seed_{N}.pkl
- [ ] T034 [US2] Generate results/metrics.csv with performance across all 5 seeds (SC-005, FR-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Attribution and Statistical Significance Analysis (Priority: P3)

**Goal**: Apply permutation importance to Random Forest and saliency mapping to GNN embeddings, perform paired t-tests to confirm statistical significance of the performance delta

**Independent Test**: Verify feature importance rankings are generated and t-test p-values are computed across 5 random seeds

### Tests for User Story 3

- [ ] T035 [P] [US3] Integration test for permutation importance pipeline with memory profiling (< 8GB constraint) in `projects/001-predicting-molecular-dipole-moments/tests/integration/test_permutation_importance.py`
- [ ] T036 [P] [US3] Integration test for saliency mapping pipeline in `projects/001-predicting-molecular-dipole-moments/tests/integration/test_saliency_mapping.py`
- [ ] T037 [P] [US3] Unit test for paired t-test computation in `projects/001-predicting-molecular-dipole-moments/tests/unit/test_statistical_tests.py`

### Implementation for User Story 3

- [ ] T038 [P] [US3] Implement permutation importance for Random Forest in `projects/001-predicting-molecular-dipole-moments/code/attribution/permutation_importance.py` (FR-007)
- [ ] T039 [P] [US3] Implement saliency mapping for GNN node embeddings in `projects/001-predicting-molecular-dipole-moments/code/attribution/saliency_mapping.py` (FR-007)
- [ ] T040 [US3] Rank structural contributions (electronegative atom placement, local bond angles) in `projects/001-predicting-molecular-dipole-moments/code/attribution/rank_contributions.py` (FR-007, SC-002)
- [ ] T041 [US3] Implement paired t-tests (α=0.05) comparing RMSE distributions in `projects/001-predicting-molecular-dipole-moments/code/analysis/statistical_tests.py` (FR-008, SC-004)
- [ ] T042 [US3] Generate results/attributions.json with feature importance rankings
- [ ] T043 [US3] Generate results/significance.csv with t-test p-values across 5 seeds
- [ ] T044 [US3] Compute confidence intervals (95%) for MAE and RMSE metrics in `projects/001-predicting-molecular-dipole-moments/code/analysis/confidence_intervals.py` (FR-012, SC-001)
- [ ] T045 [US3] Visualize feature importance maps on representative molecules in `projects/001-predicting-molecular-dipole-moments/code/analysis/visualize_features.py` (FR-009, responsible for feature attribution visualizations only)
- [ ] T046 [US3] Generate results/figures/*.png for model performance charts and general result visualizations (responsible for non-feature-attribution visualizations)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation and Requirements Alignment

**Purpose**: Align tasks with spec requirements and ensure all FRs are implemented

- [ ] T049 [US1+US2+US3] Implement global 6h CPU time limit enforcement wrapper in `projects/001-predicting-molecular-dipole-moments/code/utils/pipeline_time_limit.py` (FR-010, SC-003, applies to entire pipeline not just training)
- [ ] T050 [US1+US2+US3] Enforce 2 CPU cores constraint across entire pipeline in `projects/001-predicting-molecular-dipole-moments/code/utils/cpu_constraint.py` (FR-010, SC-003)
- [ ] T051 [US1+US2+US3] Validate RMSE variance < 10% threshold across 5 seeds in `projects/001-predicting-molecular-dipole-moments/code/analysis/validate_variance.py` (SC-005)
- [ ] T052 [US1+US2+US3] Enforce memory constraint (< 8GB) across entire pipeline in `projects/001-predicting-molecular-dipole-moments/code/utils/memory_constraint.py` (FR-013)
- [ ] T053 [US1+US2+US3] Validate all cited literature URLs are accessible in `projects/001-predicting-molecular-dipole-moments/code/utils/validate_urls.py` (spec.md Assumptions)

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T054 [P] Documentation updates in specs/001-predicting-molecular-dipole-moments/ (README.md, quickstart.md, research.md) per plan.md structure
- [ ] T055 [P] Code cleanup and refactoring across all modules (FR-001 through FR-013 traceability)
- [ ] T056 [P] Additional unit tests in tests/unit/ for edge cases
- [ ] T057 [P] Run quickstart.md validation to verify end-to-end pipeline in `specs/001-predicting-molecular-dipole-moments/quickstart.md` per plan.md structure
- [ ] T058 [P] Generate final results summary with all metrics, attributions, and visualizations
- [ ] T059 [P] Update state/projects/001-predicting-molecular-dipole-moments.yaml with completion timestamps and content hashes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup **(Phase 1): No dependencies - can start immediately
- **Foundational **(Phase 2): Depends on Setup completion - BLOCKS all user stories
- **User Stories **(Phase 3+): All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Validation **(Phase 6): Depends on all user stories being complete
- **Polish **(Phase 7): Depends on all desired user stories and validation being complete

### User Story Dependencies

- **User Story 1 **(P1): Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 **(P2): Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 **(P3): Can start after Foundational (Phase 2) - Depends on US2 model outputs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data download before subset creation (T015 before T016)
- Subset creation before feature extraction (T016 before T017/T018)
- Feature extraction before model training
- Model training before evaluation
- Evaluation before attribution analysis
- Attribution before statistical tests
- Validation before visualization

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Model implementation tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for molecule schema in tests/contract/test_molecule_schema.py"
Task: "Contract test for feature_set schema in tests/contract/test_feature_set_schema.py"
Task: "Integration test for QM9 download pipeline with memory profiling in tests/integration/test_qm9_download.py"
Task: "Unit test for 3D coordinate extraction in tests/unit/test_extract_3d_coords.py"
Task: "Unit test for 2D descriptor generation in tests/unit/test_extract_2d_descriptors.py"

# Launch all models for User Story 1 together (in correct order):
Task: "Implement QM9 download with integrity verification in code/data/download_qm9.py"
Task: "Create 10k random subset with reproducibility seed in code/data/create_subset.py"
Task: "Implement 3D coordinate, atom type, and bond connectivity extraction in code/data/preprocess_3d.py"
Task: "Implement 2D Morgan fingerprints and Coulomb matrix generation in code/data/extract_2d_descriptors.py"
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
5. Add Validation (Phase 6) → Address all reviewer concerns
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (data pipeline)
   - Developer B: User Story 2 (model training)
   - Developer C: User Story 3 (attribution + statistics)
3. Stories complete and integrate independently
4. Phase 6: All developers collaborate on validation protocol

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Path conventions now match plan.md under projects/001-.../code/ and projects/001-.../tests/
- **Critical**: Contract schemas are YAML files in tests/contracts/ per plan.md (T007 updated)
- **Critical**: Documentation paths updated from docs/ to specs/001-predicting-molecular-dipole-moments/ per plan.md structure
- **Critical**: T031 (metric computation) maps to FR-006, not SC-001
- **Critical**: T034 (metrics.csv) maps to FR-006 and SC-005
- **Critical**: T044 (confidence intervals) maps to FR-012 and SC-001
- **Critical**: T045 (feature importance visualizations) and T046 (performance charts) have clear division of responsibility
- **Critical**: T047/T048 removed - hydration and conformational assumptions documented directly in spec.md
- **Critical**: T049 (global time limit) added to Phase 6 to enforce FR-010/SC-003 across entire pipeline
- **Critical**: Task IDs renumbered sequentially to eliminate gaps and ensure T001-T059 continuous numbering
- **Critical**: All FR-001 through FR-013 now have explicit task references in task descriptions
- **Critical**: All Success Criteria SC-001 through SC-005 now have explicit task mappings
- **Critical**: Edge case for QM9 DOI inaccessible now addressed by T021
- **Critical**: Memory footprint constraint (< 8GB) documented in spec.md and enforced in tasks T012, T022, T035, T052
- **Critical**: 3D geometry preservation requirements traceable to T009 (reproducibility) and T017 (coordinate preprocessing)
- **Critical**: T050 enforces 2 CPU cores constraint across entire pipeline (FR-010, SC-003)
- **Critical**: T051 validates RMSE variance < 10% threshold (SC-005)
- **Critical**: T053 validates all cited literature URLs (spec.md Assumptions)
- **Critical**: quickstart.md documented in plan.md structure for T054/T057 reference