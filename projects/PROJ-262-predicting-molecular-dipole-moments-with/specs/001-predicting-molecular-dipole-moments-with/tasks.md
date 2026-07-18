# Tasks: Predicting Molecular Dipole Moments with Graph Neural Networks

**Input**: Design documents from `/specs/001-predicting-molecular-dipole-moments/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `- [ ] T### [P?] [Story] description with file path`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- **[Doc]**: Documentation task (updates research.md, README, etc.)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/`, `tests/`, `data/`, `state/`, `specs/`
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- **Paths shown below match plan.md structure under `projects/PROJ-262-predicting-molecular-dipole-moments-with/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure per FR‑030 Constitution requirements for reproducibility and versioning discipline

- [X] T001 Create project structure with exact directories: `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/`, `tests/`, `data/raw/`, `data/processed/`, `data/checkpoints/`, `data/reports/`, `results/`, `state/`, `specs/` in `projects/PROJ-262-predicting-molecular-dipole-moments-with/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/requirements.txt` ({{claim:c_1a356c4e}})
- [X] T003 [P] Configure linting and formatting tools (black, flake, isort) in `.pre-commit-config.yaml`

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
- [X] T090 [P] Implement `reference-validator` script in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/reference_validator.py` to verify DOI strings against local registry and compute content hashes (supports T015, T053).
- [X] T091 [P] Run `reference-validator` to verify DOI 10.1038/sdata.2014.22 local metadata and record hash in `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` (no external URL fetching, satisfies Constitution Principle II).

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel

---

## Phase 3: User Story 1 – Dataset Preparation and Baseline Feature Extraction (Priority: P1)

**Goal**: Download QM9 dataset, filter to a 10 k random subset, extract both 3D coordinates and 2D descriptors for baseline comparison.

**Independent Test**: Verify data files exist, subset size equals 10 k, and both 3D and 2D feature matrices are generated with no missing values.

- [X] T100 [P] [US1] Contract test for molecule schema (`tests/contract/test_molecule_schema.py`) – Implement `test_molecule_schema_validates_missing_coordinates` to assert that molecules with missing 3D coordinates are flagged and excluded.
- [X] T101 [P] [US1] Contract test for feature_set schema (`tests/contract/test_feature_set_schema.py`) – Implement `test_feature_set_schema_validates_nan_values` to assert that feature vectors contain no NaN values.
- [X] T102 [P] [US1] Integration test for QM9 download pipeline with memory profiling (`tests/integration/test_qm9_download.py`) – Implement `test_qm9_download_memory_under_8gb` to verify memory usage stays within 8GB limit during download.
- [X] T103 [P] [US1] Unit test for 3D coordinate extraction (`tests/unit/test_extract_3d_coords.py`) – Implement `test_extract_3d_coords_handles_nan_and_missing_atoms` to assert correct handling of NaN values and missing atoms.
- [X] T104 [P] [US1] Unit test for 2D descriptor generation (`tests/unit/test_extract_2d_descriptors.py`) – Implement `test_2d_descriptors_verify_fingerprint_length_and_matrix_symmetry` to assert Morgan fingerprint length and Coulomb matrix symmetry.

### Implementation for User Story 1

- [X] T015 [US1] Verify DOI 10.1038/sdata.2014.22 exists in local reference registry and record its hash in `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` (depends on T090, T091)
- [X] T016 [US1] Create a reproducible random subset in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/create_subset.py` (seed 42) such that the resulting dataset is of a manageable size for initial prototyping and testing.
- [X] T017 [US1] Implement 3D coordinate, atom type, and bond connectivity extraction in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/preprocess_3d.py` (FR‑002, depends on T016)
- [X] T018 [US1] Implement 2D Morgan fingerprints and Coulomb matrix generation in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/extract_2d_descriptors.py` (FR‑003, depends on T016)
- [X] T019 [US1] Add validation for missing 3D coordinates in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/handle_missing_coords.py` – generates `data/reports/excluded_molecules.csv` with columns `molecule_id`, `exclusion_reason` (enum: `missing_3d`, `invalid_structure`), `exclusion_timestamp`.
- [X] T020 [US1] Generate output files: `data/processed/molecules_10k.parquet`, `features_3d.parquet`, `features_2d.parquet`
- [X] T021 [US1] Implement retry/fallback logic for DOI inaccessibility in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/download_qm9.py`

**Checkpoint**: User Story 1 fully functional and testable independently

---

## Phase 4: User Story 2 – Model Training and Evaluation Pipeline (Priority: P2)

**Goal**: Train lightweight SchNet‑style GNN and Random Forest baseline on identical train/test splits, evaluate both on held‑out test set using MAE and RMSE for dipole moments (a sufficient number of epochs with early stopping).

**Independent Test**: Verify training with 50 epochs and early stopping (patience=10), both models produce MAE and RMSE scores on test set, and Confidence intervals are computed across random seeds.

### Tests for User Story 2

- [ ] T106 [P] [US2] Contract test for model_output schema (`tests/contract/test_model_output_schema.py`) – Implement `test_model_output_schema_validates_prediction_range` to assert predicted dipoles are within physical bounds.
- [ ] T107 [P] [US2] Integration test for GNN training pipeline (`tests/integration/test_gnn_training.py`) – Implement `test_gnn_training_converges_within_50_epochs` to assert convergence criteria.
- [ ] T108 [P] [US2] Integration test for Random Forest training pipeline (`tests/integration/test_rf_training.py`) – Implement `test_rf_training_rmse_variance_under_10_percent` to assert stability across seeds.
- [ ] T109 [P] [US2] Unit test for MAE/RMSE metric computation (`tests/unit/test_metrics.py`) – Implement `test_metrics_handles_empty_input_and_nan` to assert correct edge case handling.

### Implementation for User Story 2

- [X] T026 [P] [US2] Implement SchNet‑style GNN architecture in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/models/schnet_gnn.py` (FR‑004, CPU‑only)
- [X] T027 [P] [US2] Implement Random Forest baseline in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/models/random_forest_baseline.py` (FR‑005)
- [X] T028 [US2] Implement GNN training with multiple seeds, 50 epochs, early stopping (patience = 10) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_gnn.py` – compute variance of RMSE across seeds and ensure it is recorded (fulfills SC‑005).
- [X] T029 [US2] Train Random Forest baseline with seeds in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_rf.py` – also records RMSE variance.
- [X] T030 [US2] Implement identical train/test split generation across seeds in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/split_data.py`
- [X] T031 [US2] Implement MAE and RMSE metric computation in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/evaluate.py` (FR‑006)
- [X] T032 [US2] Compute MAE/RMSE against QM9 dipole‑moment reference values on the held‑out test split (fulfills FR‑011 without external data).
- [X] T033 [US2] Save model checkpoints to `data/checkpoints/model_seed_{N}.pt` and `rf_seed_{N}.pkl` – each checkpoint includes model state dict, training config, seed, and timestamp.
- [X] T034 [US2] Generate `results/metrics.csv` with columns `seed`, `model`, `mae`, `rmse`, `mae_ci_lower`, `mae_ci_upper`, `rmse_ci_lower`, `rmse_ci_upper` – CI computed via bootstrap (95 % confidence) within this task.

**Checkpoint**: User Stories 1 & 2 functional

---

## Phase 5: User Story 3 – Feature Attribution and Statistical Significance Analysis (Priority: P3)

**Goal**: Apply permutation importance to Random Forest and saliency mapping to GNN embeddings, perform paired t‑tests to confirm statistical significance of the performance delta.

**Independent Test**: Verify feature importance rankings are generated, t-test p-values are computed, and structural contributions are ranked.

### Tests for User Story 3

- [ ] T111 [P] [US3] Integration test for permutation importance pipeline (`tests/integration/test_permutation_importance.py`) – Implement `test_permutation_importance_generates_ranked_features` to assert correct ranking logic.
- [ ] T112 [P] [US3] Integration test for saliency mapping pipeline (`tests/integration/test_saliency_mapping.py`) – Implement `test_saliency_mapping_produces_valid_gradients` to assert gradient validity.
- [ ] T113 [P] [US3] Unit test for paired t‑test computation (`tests/unit/test_statistical_tests.py`) – Implement `test_t_test_handles_equal_variance_and_small_samples` to assert correct statistical handling.

### Implementation for User Story 3

- [X] T038 [P] [US3] Implement permutation importance for Random Forest in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/attribution/permutation_importance.py` (FR‑007)
- [X] T039 [P] [US3] Implement saliency mapping for GNN node embeddings in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/attribution/saliency_mapping.py` (FR‑007)
- [X] T040 [US3] Rank structural contributions (e.g., electronegative atom placement, local bond angles) and (FR‑007, SC‑002)
- [X] T041 [US3] Implement paired t‑tests (α = 0.05) comparing RMSE distributions in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/statistical_tests.py` (FR‑008, SC‑004)
- [X] T042 [US3] Generate `results/attributions.json` with feature importance rankings
- [X] T043 [US3] Generate `results/significance.csv` with columns `seed`, `t_statistic`, `p_value`, `significant_at_alpha_0.05` (FR‑008)
- [X] T045 [US3] Visualize feature‑importance maps on representative molecules (e.g., `data/processed/attributions_*.png`) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/visualize_features.py` (FR‑009)

**Checkpoint**: All user stories independently functional

---

## Phase 6: Validation and Requirements Alignment

**Purpose**: Verify that all functional requirements (FR‑001 – FR‑013) and success criteria (SC‑001 – SC‑005) are satisfied, and that documentation complies with the constitution.

- [X] T053 [P] Run reference-validator script (T090, T091) to verify local DOI metadata matches registered references; no external URL fetching performed (satisfies Constitution Principle II and 'no URL fabrication' constraint).
- [X] T054 [P] Populate documentation files with required sections (overview, installation, usage, results, limitations) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/specs/001-predicting-molecular-dipole-moments-with/`.
- [X] T057 [P] Quick‑start validation checks for existence of all data files, non‑NaN metrics, and at least one attribution visualisation; fails otherwise.
- [X] T058 [P] Summary includes MAE/RMSE with 95 % CI, top‑k feature importance entries, paired‑t‑test p‑values, and links to generated figures.
- [X] T059 [P] State file `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` follows YAML schema with `completed_at`, `artifact_hashes` (SHA‑256 per file), and `updated_at`.
- [X] T094 [P] Validate total pipeline runtime: Read `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` (updated_at) and `results/metrics.csv` to calculate total elapsed time from data download to final metric generation; Verify against a predefined time limit. (SC‑003, FR‑010).

**Checkpoint**: All functional requirements verified against spec and constitution.

---

## Phase 7: Documentation & Polish

**Purpose**: Final documentation, end‑to‑end validation, and project cleanup. This phase consolidates all documentation tasks, including explicit scope boundary documentation.

- [X] T093 [P] Update `research.md` with explicit limitations: gas-phase DFT data only, single conformer per molecule, no experimental validation or hydration analysis performed (aligns with spec assumptions).
- [ ] T210 [P] [Doc] Update `research.md` to explicitly document scope boundaries: state that physical measurement validation (e.g., Stark-effect spectroscopy) is out-of-scope and that QM DFT reference data (BLYP/6-31G(2df,p)) serves as the sole ground truth; confirm conformational ensembles and hydration state sampling are out-of-scope per spec assumptions (Addresses FR-011, Spec Assumptions).

**Checkpoint**: All user stories independently functional, validated, and scope boundaries explicitly documented.