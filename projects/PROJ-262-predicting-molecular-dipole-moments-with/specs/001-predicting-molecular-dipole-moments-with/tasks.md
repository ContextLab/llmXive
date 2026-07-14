# Tasks: Predicting Molecular Dipole Moments with Graph Neural Networks

**Input**: Design documents from `/specs/001-predicting-molecular-dipole-moments/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `- [ ] T### [P?] [Story] description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/`, `tests/`, `data/raw/`, `data/processed/`, `data/checkpoints/`, `data/reports/`, `results/`, `state/`, `specs/` in `projects/PROJ-262-predicting-molecular-dipole-moments-with/`
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- **Paths shown below match plan.md structure under `projects/PROJ-262-predicting-molecular-dipole-moments-with/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure per FR‑030 Constitution requirements for reproducibility and versioning discipline

- [X] T001 Create project structure with exact directories: `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/`, `tests/`, `data/raw/`, `data/processed/`, `data/checkpoints/`, `data/reports/`, `results/`, `state/`, `specs/` in `projects/PROJ-262-predicting-molecular-dipole-moments-with/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/requirements.txt`
- [X] T003 [P] Configure linting and formatting tools (black, flake8, isort) in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. All tasks trace to FR‑001 through FR‑013 requirements.

- [X] T004 Setup data directory structure (`data/raw/`, `data/processed/`, `data/checkpoints/`, `data/reports/`) per plan.md in `projects/PROJ-262-predicting-molecular-dipole-moments-with/`
- [X] T005 [P] Initialize state tracking with `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml`
- [X] T006 [P] Configure pytest with the current contract test framework in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/`.
- [X] T007 [P] Create YAML contract schema files in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/contracts/`
  - `molecule.schema.yaml`: `molecule_id (str)`, `atoms (list)`, `coordinates (list of [float,float,float])`, `dipole (float)`.
  - `feature_set.schema.yaml`: `molecule_id (str)`, `features_2d (list of float)`, `features_3d (list of float)`.
  - `model_output.schema.yaml`: `molecule_id (str)`, `predicted_dipole (float)`, `true_dipole (float)`.
- [X] T008 Configure environment configuration management with `.env.example` and `config.py` in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/`
- [X] T009 [P] Setup reproducibility framework in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/reproducibility.py` – pins `random.seed`, `numpy.random.seed`, `torch.manual_seed` with a consistent fixed value to ensure reproducibility..
- [X] T049 [P] Implement a time‑limit wrapper (`@time_limit(T*60*60)`) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/pipeline_time_limit.py` (FR‑010, SC‑003), where **T** represents a configurable time duration.
- [X] T050 [P] Enforce a CPU‑core constraint using the `@cpu_limit()` decorator in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/cpu_constraint.py` (FR‑010, SC‑003)
- [X] T052 [P] Enforce memory constraint (< 8 GB) (`@memory_limit(8*1024**3)`) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/memory_constraint.py` (FR‑013)

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel

---

## Phase 3: User Story 1 – Dataset Preparation and Baseline Feature Extraction (Priority: P1)

**Goal**: Download the QM9 dataset, create a 10 k random subset, extract 3D coordinates, atom types, bond connectivity, and generate 2D descriptors (Morgan fingerprints, Coulomb matrices). All outputs must be free of NaN values.

### Tests for User Story 1 (must be written before implementation)

- [ ] T100 [P] [US1] Contract test for molecule schema (`tests/contract/test_molecule_schema.py`)
- [ ] T101 [P] [US1] Contract test for feature_set schema (`tests/contract/test_feature_set_schema.py`)
- [ ] T102 [P] [US1] Integration test for QM9 download pipeline with memory profiling (`tests/integration/test_qm9_download.py`)
- [ ] T103 [P] [US1] Unit test for 3D coordinate extraction (`tests/unit/test_extract_3d_coords.py`)
- [ ] T104 [P] [US1] Unit test for 2D descriptor generation (`tests/unit/test_extract_2d_descriptors.py`)

### Implementation for User Story 1

- [X] T015 [US1] Implement QM9 download with integrity verification (`code/data/download_qm9.py`) (FR‑001)
- [X] T016 [US1] Create a reproducible random subset of molecules (`code/data/create_subset.py`) (FR‑001)
- [X] T017 [US1] Extract 3D coordinates, atom types, and bond connectivity (`code/data/preprocess_3d.py`) (FR‑002)
- [X] T018 [US1] Generate 2D Morgan fingerprints and Coulomb matrices (`code/data/extract_2d_descriptors.py`) (FR‑003)
- [X] T019 [US1] Handle missing 3D coordinates: Generate `data/reports/excluded_molecules.csv` containing `molecule_id`, `reason`, and a summary row with `excluded_count` to satisfy User Story 1 Acceptance Scenario 3 (FR‑002, edge‑case handling)
- [X] T020 [US1] Write processed outputs:
  - `data/processed/molecules_10k.parquet`
  - `data/processed/features_3d.parquet`
  - `data/processed/features_2d.parquet`

**Checkpoint**: User Story 1 fully functional and testable independently

---

## Phase 4: User Story 2 – Model Training and Evaluation Pipeline (Priority: P2)

**Goal**: Train a lightweight SchNet‑style GNN and a Random Forest baseline on identical train/test splits, evaluate both on a held-out test set using MAE and RMSE (fixed number of epochs with early stopping). Record 95 % confidence intervals across 5 random seeds.

### Tests for User Story 2

- [ ] T106 [P] [US2] Contract test for model_output schema (`tests/contract/test_model_output_schema.py`)
- [ ] T107 [P] [US2] Integration test for GNN training pipeline (`tests/integration/test_gnn_training.py`)
- [ ] T108 [P] [US2] Integration test for Random Forest training pipeline (`tests/integration/test_rf_training.py`)
- [ ] T109 [P] [US2] Unit test for MAE/RMSE metric computation (`tests/unit/test_metrics.py`)

### Implementation for User Story 2

- [X] T026 [US2] Implement SchNet‑style GNN architecture (`code/models/schnet_gnn.py`) (FR‑004, CPU‑only)
- [X] T027 [US2] Implement Random Forest baseline (`code/models/random_forest_baseline.py`) (FR‑005)
- [X] T028 [US2] GNN training script with 5 seeds, 50 epochs, early stopping (patience = 10) (`code/training/train_gnn.py`) (FR‑005)
- [X] T029 [US2] Random Forest training script with multiple random seeds (`code/training/train_rf.py`); must produce 5 `.pkl` files in `data/checkpoints/` named `rf_seed_0.pkl` through `rf_seed_4.pkl` (FR‑005)
- [X] T030 [US2] Generate identical train/test splits (`code/training/split_data.py`) (FR‑005)
- [X] T031 [US2] Compute MAE and RMSE metrics (`code/training/evaluate.py`) (FR‑006)
- [X] T032 [US2] Compute metrics against QM9 dipole reference values (`code/training/evaluate.py`) (FR‑011)
- [X] T033 [US2] Save model checkpoints to `data/checkpoints/` (`model_seed_{N}.pt`, `rf_seed_{N}.pkl`) (FR‑005)
- [X] T034 [US2] Generate `results/metrics.csv` with seed‑wise MAE, RMSE, and 95 % CI columns (FR‑012)

**Checkpoint**: User Stories 1 & 2 functional

---

## Phase 5: User Story 3 – Feature Attribution and Statistical Significance Analysis (Priority: P3)

**Goal**: Apply permutation importance to the Random Forest and saliency mapping to GNN embeddings, then perform paired t‑tests to assess statistical significance of performance differences. Visualize top‑ranked features on representative molecules.

### Tests for User Story 3

- [ ] T111 [P] [US3] Integration test for permutation importance pipeline (`tests/integration/test_permutation_importance.py`)
- [ ] T112 [P] [US3] Integration test for saliency mapping pipeline (`tests/integration/test_saliency_mapping.py`)
- [ ] T113 [P] [US3] Unit test for paired t‑test computation (`tests/unit/test_statistical_tests.py`)

### Implementation for User Story 3

- [X] T038 [US3] Implement permutation importance for Random Forest (`code/attribution/permutation_importance.py`) (FR‑007)
- [X] T039 [US3] Implement saliency mapping for GNN node embeddings (`code/attribution/saliency_mapping.py`) (FR‑007)
- [X] T040 [US3] Rank structural contributions (e.g., electronegative atom placement, local bond angles) and store rankings (`results/feature_ranking.json`) (FR‑007, SC‑002)
- [X] T041 [US3] Implement paired t‑tests (α = 0.05) comparing RMSE distributions (`code/analysis/statistical_tests.py`) (FR‑008, SC‑004)
- [X] T042 [US3] Generate `results/attributions.json` containing full feature‑importance rankings (FR‑007)
- [X] T043 [US3] Generate `results/significance.csv` with columns `seed`, `t_statistic`, `p_value`, `significant_at_alpha_0.05` (FR‑008)
- [X] T045 [US3] Visualize feature‑importance maps on a representative subset of molecules (`code/analysis/visualize_features.py`) and save PNGs to `data/processed/attributions_{molecule_id}.png` (FR‑009)

**Checkpoint**: All user stories independently functional

---

## Phase 6: Validation and Requirements Alignment

**Purpose**: Verify that all functional requirements (FR‑001 – FR‑013) and success criteria (SC‑001 – SC‑005) are satisfied, and that documentation complies with the constitution.

- [X] T053 Verify all literature URLs cited in the repository and ensure title‑token overlap ≥ 0.7 with primary sources (Principle II)
- [X] T054 Populate documentation files (`README.md`, `quickstart.md`, `research.md`) with required sections (overview, installation, usage, results, limitations) (Principle IV)
- [X] T057 Quick‑start validation script checks existence of all data files, non‑NaN metrics, and at least one attribution visualisation; exits with error if any check fails (Principle I)
- [X] T058 Summary generation script produces a concise report (`results/summary.md`) including MAE/RMSE with 95 % CI, top‑5 feature importance entries, paired‑t‑test p‑values, and links to figures (Principle IV)
- [X] T059 Update `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` with `completed_at`, `artifact_hashes` (SHA‑256 per file), and `updated_at` (Principle V)

**Checkpoint**: All functional requirements verified against spec and constitution.

---

## Phase 7: Documentation & Polish

**Purpose**: Final documentation, end‑to‑end validation, and project cleanup.

- [X] T058 (see Phase 6) Final results summary generation.
- [X] T059 (see Phase 6) State file update.
- [X] T060 (Removed – out‑of‑scope) – no action required.
- [X] T061 (Removed – out‑of‑scope) – no action required.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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