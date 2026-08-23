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
- [X] T002 Initialize Python project with `requirements.txt` in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/requirements.txt` (pins exact versions per spec.md Technical Context: PyTorch, PyTorch Geometric, RDKit, scikit-learn, pandas, numpy)
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
- [X] T050 [P] Enforce a CPU‑core constraint using the `@cpu_limit()` decorator in `projects/PROJ-predicting-molecular-dipole-moments-with/code/utils/cpu_constraint.py` (FR‑010, SC‑003)
- [X] T052 [P] Enforce memory constraint (< 8 GB) (`@memory_limit(8*1024**3)`) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/memory_constraint.py` (FR‑013)
- [X] T055 [P] Implement the aggregate pipeline execution wrapper in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/pipeline_orchestrator.py` that wraps the entire pipeline execution, enforces the total runtime limit (FR‑010, SC‑003), logs start/end times and peak memory usage, and fails loudly if the limit is exceeded. This task consumes the decorators from T049, T050, T052.
- [X] T090 [P] Implement `reference-validator` script in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/reference_validator.py` to verify DOI strings against local registry and compute content hashes (supports T015, T053).
- [X] T091 [P] Run `reference-validator` to verify DOI 10.1038/sdata.2014.22 local metadata and record hash in `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` (no external URL fetching, satisfies Constitution Principle II).
- [X] T015 [Foundational] [P] Verify DOI 10.1038/sdata.2014.22 exists in local reference registry and record its hash in `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` (depends on T090, T091). This is a prerequisite for US1.
- [X] T210 [Foundational] [P] [Doc] Update `research.md` to explicitly document scope boundaries: state that physical measurement validation (e.g., Stark-effect spectroscopy) is out-of-scope and that QM DFT reference data (BLYP/level per the dataset specification) serves as the sole ground truth (Addresses FR-011, Spec Assumptions).

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel

---

## Phase 3: User Story 1 – Dataset Preparation and Baseline Feature Extraction (Priority: P1)

**Goal**: Download QM9 dataset, filter to a random subset, extract both 3D coordinates and 2D descriptors for baseline comparison.

**Independent Test**: Verify data files exist, subset size is substantial, and both 3D and 2D feature matrices are generated with no missing values.

### Implementation for User Story 1

- [X] T016a [US1] Implement runtime monitoring wrapper in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/runtime_monitor.py` that tracks elapsed time against the time limit. If the limit is approached, it triggers a subset reduction flag. This flag is consumed by T016b to iteratively reduce the target subset size. (Note: Sequential dependency on T016b, not parallel).
- [X] T016b [US1] Implement subset reduction logic in `projects/PROJ-predicting-molecular-dipole-moments-with/code/data/create_subset.py` (seed 42). This task creates an initial subset, runs the monitor (T016a), and if the flag is set, re-executes with a smaller target to output `data/processed/subset_final.parquet` with the final molecule list. Depends on T016a.
- [X] T017 [US1] [P] Implement 3D coordinate, atom type, and bond connectivity extraction in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/preprocess_3d.py` (FR‑002, depends on T016b). This task also outputs the final processed features.
- [X] T018 [US1] [P] Implement 2D Morgan fingerprints and Coulomb matrix generation in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/extract_2d_descriptors.py` (FR‑003, depends on T016b). **Note**: Generates Coulomb matrices to `data/processed/coulomb_matrices_archive.parquet` (archival only) and explicitly EXCLUDES them from the Random Forest baseline inputs which must use ONLY Morgan fingerprints and topological counts per plan.md.
- [X] T019 [US1] [P] Verify existence of excluded_molecules.csv in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/handle_missing_coords.py` – generates `data/reports/excluded_molecules.csv` with columns `molecule_id`, `exclusion_reason` (enum: `missing_3d`, `invalid_structure`), `exclusion_timestamp` and updates `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` with the artifact hash.
- [X] T021 [US1] [P] Implement retry logic for DOI inaccessibility in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/download_qm9.py` (FAIL LOUDLY on persistent failure, no synthetic fallback).

### Tests for User Story 1

- [X] T100 [P] [US1] Contract test for molecule schema (`tests/contract/test_molecule_schema.py`) – Implement `test_molecule_schema_validates_missing_coordinates` to assert that molecules with missing 3D coordinates are flagged and excluded.
- [X] T101 [P] [US1] Contract test for feature_set schema (`tests/contract/test_feature_set_schema.py`) – Implement `test_feature_set_schema_validates_nan_values` to assert that feature vectors contain no NaN values.
- [X] T102 [P] [US1] Integration test for QM9 download pipeline with memory profiling (`tests/integration/test_qm9_download.py`) – Implement `test_qm9_download_memory_under_8gb` to verify verify memory usage stays within 8GB limit during download.
- [X] T103 [P] [US1] Unit test for 3D coordinate extraction (`tests/unit/test_extract_3d_coords.py`) – Implement `test_extract_3d_coords_handles_nan_and_missing_atoms` to assert correct handling of NaN values and missing atoms.
- [X] T104 [P] [US1] Unit test for 2D descriptor generation (`tests/unit/test_extract_2d_descriptors.py`) – Implement `test_2d_descriptors_verify_fingerprint_length_and_matrix_symmetry` to assert Morgan fingerprint length and Coulomb matrix symmetry.

**Checkpoint**: User Story 1 fully functional and testable independently

---

## Phase 4: User Story 2 – Model Training and Evaluation Pipeline (Priority: P2)

**Goal**: Train lightweight SchNet‑style GNN and Random Forest baseline on identical train/test splits, evaluate both on held‑out test set using MAE and RMSE for dipole moments (50 epochs with early stopping patience=10).

**Independent Test**: Verify training with 50 epochs and early stopping (patience=10), both models produce MAE and RMSE scores on test set, and Confidence intervals are computed across random seeds.

### Implementation for User Story 2

- [X] T026 [P] [US2] Implement SchNet‑style GNN architecture in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/models/schnet_gnn.py` (FR‑004, CPU‑only)
- [X] T027 [P] [US2] Implement Random Forest baseline in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/models/random_forest_baseline.py` (FR‑005)
- [X] T028 [US2] Implement GNN training with multiple seeds, 50 epochs, early stopping (hard-coded patience=10) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_gnn.py` – compute variance of RMSE across seeds, generate confidence intervals, and ensure they are recorded (fulfills SC‑005).
- [X] T029 [US2] Train Random Forest baseline with seeds in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_rf.py` – also records RMSE variance and confidence intervals. **Note**: Uses ONLY 2D features (Morgan fingerprints, topological counts) as defined in plan.md, explicitly excluding Coulomb matrices.
- [X] T030 [US2] Implement identical train/test split generation across seeds in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/split_data.py`
- [X] T031 [US2] Implement MAE and RMSE metric computation in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/evaluate.py` (FR‑006)
- [X] T032 [US2] Compute MAE/RMSE against QM9 DFT reference values (not experimental) (fulfills FR-011) using the DFT reference data already present in the QM9 dataset.
- [X] T033 [US2] Save model checkpoints to `data/checkpoints/model_seed_{N}.pt` and `rf_seed_{N}.pkl` – each checkpoint includes model state dict, training config, seed, and timestamp.
- [X] T034 [US2] Generate `results/metrics.csv` with columns `seed`, `model`, `mae`, `rmse`, `mae_ci_lower`, `mae_ci_upper`, `rmse_ci_lower`, `rmse_ci_upper` (per FR-012 and Plan.md Technical Context).

### Tests for User Story 2

- [X] T106 [P] [US2] Contract test for model_output schema (`tests/contract/test_model_output_schema.py`) – Implement `test_model_output_schema_validates_prediction_range` to assert predicted dipoles are within physical bounds.
- [X] T107 [P] [US2] Integration test for GNN training pipeline (`tests/integration/test_gnn_training.py`) – Implement `test_gnn_training_converges_within__epochs` to assert convergence criteria.
- [X] T108 [P] [US2] Integration test for Random Forest training pipeline (`tests/integration/test_rf_training.py`) – Implement `test_rf_training_rmse_variance_under_threshold` to assert stability across seeds.
- [X] T109 [P] [US2] Unit test for MAE/RMSE metric computation (`tests/unit/test_metrics.py`) – Implement `test_metrics_handles_empty_input_and_nan` to assert correct edge case handling.

**Checkpoint**: User Stories 1 & 2 functional

---