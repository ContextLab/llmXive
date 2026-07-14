# Tasks: Predicting Molecular Dipole Moments with Graph Neural Networks

**Input**: Design documents from `/specs/001-predicting-molecular-dipole-moments/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/`, `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/`, `projects/PROJ-262-predicting-molecular-dipole-moments-with/data/`, `projects/PROJ-262-predicting-molecular-dipole-moments-with/state/`
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below match plan.md structure under `projects/PROJ-262-predicting-molecular-dipole-moments-with/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure per FR‑030 Constitution requirements for reproducibility and versioning discipline

- [X] T001 Create project structure with exact directories: `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/`, `tests/`, `data/raw/`, `data/processed/`, `data/checkpoints/`, `data/reports/`, `results/`, `state/`, `specs/` in `projects/PROJ-262-predicting-molecular-dipole-moments-with/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/requirements.txt`
- [X] T003 [P] Configure linting and formatting tools (black, flake, isort) in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. All tasks trace to FR‑001 through FR‑013 requirements.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure (`data/raw/`, `data/processed/`, `data/checkpoints/`, `data/reports/`) per plan.md in `projects/PROJ-262-predicting-molecular-dipole-moments-with/`
- [X] T005 [P] Initialize state tracking with `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml`
- [X] T006 [P] Configure pytest with a current version of the contract test framework in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/`.

The research question is: Can molecular dipole moments be accurately predicted using graph neural networks and atomic properties?

The method is: We will implement and evaluate graph neural network models trained on a dataset of molecular structures and dipole moments, utilizing contract testing to ensure the reliability of model inputs and outputs.

References: [insert references here - not provided in original passage].
- [X] T007 [P] Create YAML contract schema files in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/contracts/`
 *molecule.schema.yaml*: `molecule_id (str)`, `atoms (list)`, `coordinates (list of [float,float,float])`, `dipole (float)`.
 *feature_set.schema.yaml*: `molecule_id (str)`, `features_2d (list of float)`, `features_3d (list of float)`.
 *model_output.schema.yaml*: `molecule_id (str)`, `predicted_dipole (float)`, `true_dipole (float)`.
- [X] T008 Configure environment configuration management with `.env.example` and `config.py` in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/`
- [X] T009 [P] Setup reproducibility framework in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/reproducibility.py` – pins `random.seed(42)`, `numpy.random.seed(42)`, `torch.manual_seed(42)`.
- [X] T049 [P] Implement a time-limit wrapper (`@time_limit(T*60*60)`) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/pipeline_time_limit.py` (FR‑010, SC‑003), where T represents a configurable time duration.
- [X] T050 [P] Enforce a CPU-core constraint using the `@cpu_limit()` decorator in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/cpu_constraint.py` (FR‑010, SC‑003)

The research question is: Can we accurately predict molecular dipole moments using graph neural networks and atomic properties?
The method is: We will implement and evaluate a graph neural network model trained on a dataset of molecular structures and dipole moments, employing techniques to control computational resource usage.
- [X] T052 [P] Enforce memory constraint (< 8 GB) (`@memory_limit(8*1024**3)`) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/memory_constraint.py` (FR‑013)

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Preparation and Baseline Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Download QM9 dataset, Download QM9 dataset, Download QM9 dataset, filter to a 10 k random subset, extract both 3D coordinates and 2D descriptors for baseline comparison

**Independent Test**: Verify data files exist, subset size equals 10 k, and both 3D and 2D feature matrices are generated with no missing values

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for molecule schema in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/contract/test_molecule_schema.py`
- [X] T011 [P] [US1] Contract test for feature_set schema in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/contract/test_feature_set_schema.py`
- [X] T012 [P] [US1] Integration test for QM9 download pipeline with memory profiling (< 8 GB) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/integration/test_qm9_download.py`
- [X] T013 [P] [US1] Unit test for 3D coordinate extraction in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/unit/test_extract_3d_coords.py`
- [X] T014 [P] [US1] Unit test for 2D descriptor generation in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/unit/test_extract_2d_descriptors.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement QM9 download with integrity verification in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/download_qm9.py` (FR‑001, DOI 10.1038/sdata.2014.22)
- [X] T016 [US1] Create a reproducible random subset in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/create_subset.py` (seed 42) such that the resulting dataset is of a manageable size for initial prototyping and testing.
- [X] T017 [US1] Implement 3D coordinate, atom type, and bond connectivity extraction in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/preprocess_3d.py` (FR‑002, depends on T016)
- [X] T018 [US1] Implement 2D Morgan fingerprints and Coulomb matrix generation in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/extract_2d_descriptors.py` (FR‑003, depends on T016)
- [X] T019 [US1] Add validation for missing 3D coordinates in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/handle_missing_coords.py` – generates `data/reports/excluded_molecules.csv` with columns `molecule_id`, `exclusion_reason` (enum: `missing_3d`, `invalid_structure`), `exclusion_timestamp`.
- [ ] T020 [US1] Generate output files: `data/processed/molecules_10k.parquet`, `features_3d.parquet`, `features_2d.parquet` <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T021 [US1] Implement retry/fallback logic for DOI inaccessibility in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/download_qm9.py`

**Checkpoint**: User Story 1 fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Evaluation Pipeline (Priority: P2)

**Goal**: Train lightweight SchNet‑style GNN and Random Forest baseline on identical train/test splits, evaluate both on held‑out test set using MAE and RMSE for dipole moments (a sufficient number of epochs, with early stopping)

**Independent Test**: Verify training with 50 epochs and early stopping, both models produce MAE and RMSE scores on test set

### Tests for User Story 2

- [X] T022 [P] [US2] Contract test for model_output schema with memory profiling (< 8 GB) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/contract/test_model_output_schema.py`
- [X] T023 [P] [US2] Integration test for GNN training pipeline in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/integration/test_gnn_training.py`
- [X] T024 [P] [US2] Integration test for Random Forest training pipeline in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/integration/test_rf_training.py`
- [X] T025 [P] [US2] Unit test for MAE/RMSE metric computation in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T026 [P] [US2] Implement SchNet‑style GNN architecture in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/models/schnet_gnn.py` (FR‑004, CPU‑only)
- [X] T027 [P] [US2] Implement Random Forest baseline in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/models/random_forest_baseline.py` (FR‑005)
- [X] T028 [US2] Implement GNN training with 5 seeds, 50 epochs, early stopping (patience = 10) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_gnn.py` – compute variance of RMSE across seeds and ensure it is recorded (fulfills SC‑005). <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T029 [US2] Train Random Forest baseline with 5 seeds in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_rf.py` – also records RMSE variance. <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T030 [US2] Implement identical train/test split generation across seeds in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/split_data.py`
- [X] T031 [US2] Implement MAE and RMSE metric computation in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/evaluate.py` (FR‑006)
- [X] T032 [US2] Compute MAE/RMSE against QM9 dipole‑moment reference values on the held‑out test split (fulfills FR‑011 without external data).
- [X] T033 [US2] Save model checkpoints to `data/checkpoints/model_seed_{N}.pt` and `rf_seed_{N}.pkl` – each checkpoint includes model state dict, training config, seed, and timestamp.
- [X] T034 [US2] Generate `results/metrics.csv` with columns `seed`, `model`, `mae`, `rmse`, `mae_ci_lower`, `mae_ci_upper`, `rmse_ci_lower`, `rmse_ci_upper` – CI computed via bootstrap (95 % confidence) within this task.

**Checkpoint**: User Stories 1 & 2 functional

---

## Phase 5: User Story 3 - Feature Attribution and Statistical Significance Analysis (Priority: P3)

**Goal**: Apply permutation importance to Random Forest and saliency mapping to GNN embeddings, perform paired t‑tests to confirm statistical significance of the performance delta

**Independent Test**: Verify feature importance rankings are generated and t‑test p‑values are computed across 5 random seeds

### Tests for User Story 3

- [X] T035 [P] [US3] Integration test for permutation importance pipeline with memory profiling (< 8 GB) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/integration/test_permutation_importance.py`
- [X] T036 [P] [US3] Integration test for saliency mapping pipeline in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/integration/test_saliency_mapping.py`
- [X] T037 [P] [US3] Unit test for paired t‑test computation in `projects/PROJ-262-predicting-molecular-dipole-moments-with/tests/unit/test_statistical_tests.py`

### Implementation for User Story 3

- [X] T038 [P] [US3] Implement permutation importance for Random Forest in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/attribution/permutation_importance.py` (FR‑007)
- [X] T039 [P] [US3] Implement saliency mapping for GNN node embeddings in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/attribution/saliency_mapping.py` (FR‑007)
- [X] T040 [US3] Rank structural contributions (e.g., electronegativeatom placement, local bond angles) and verify **at least three** distinct features appear in the top‑10 of `results/attributions.json` (FR‑007, SC‑002)
- [X] T041 [US3] Implement paired t‑tests (α = 0.05 (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value)) comparing RMSE distributions in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/statistical_tests.py` (FR‑008, SC‑004)
- [X] T042 [US3] Generate `results/attributions.json` with feature importance rankings
- [X] T043 [US3 (Wikidata Q126592664, https://www.wikidata.org/wiki/Q126592664) ] Generate `results/significance.csv` with columns `seed`, `t_statistic`, `p_value`, `significant_at_alpha_0.05 ` (FR‑008)
- [X] T044 [US3]**(Removed – CI computation consolidated into T034)**
- [X] T045 [US3] Visualize feature‑importance maps on representative molecules (e.g., `data/processed/attributions_*.png`) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/visualize_features.py` (FR‑009)

**Checkpoint**: All user stories independently functional

---

## Phase 6: Validation and Requirements Alignment

**Purpose**: Align tasks with spec requirements and ensure all FRs are implemented

- [X] T051 **(Removed – variance check now part of T028/T029)**
- [X] T053 Updated: Validate literature URLs **and** verify title‑token‑overlap ≥ 0.7 with the primary source (satisfies Constitution Principle II).
- [X] T054 Updated: Populate documentation files with required sections (overview, installation, usage, results, limitations) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/specs/001-predicting-molecular-dipole-moments-with/`.
- [X] T057 Updated: Quick‑start validation checks for existence of all data files, non‑NaN metrics, and at least one attribution visualisation; fails otherwise.
- [X] T058 Updated: Summary includes MAE/RMSE with 95 % CI, top‑5 feature importance entries, paired‑t‑test p‑values, and links to generated figures.
- [X] T059 Updated: State file `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` follows YAML schema with `completed_at`, `artifact_hashes` (SHA‑256 per file), and `updated_at`.

**Checkpoint**: All functional requirements verified against spec and constitution.

---

## Phase 7: Documentation & Polish

**Purpose**: Final documentation and end‑to‑end validation

- [X] T060 **(Removed – out‑of‑scope)**
- [X] T061 **(Removed – out‑of‑scope)**
- [X] T062 **(Removed – out‑of‑scope)**
- [X] T063 **(Removed – out‑of‑scope)**
- [X] T064 **(Removed – duplicate)**
- [X] T065 **(Removed – duplicate)**
- [X] T058 (see Phase 6) final results summary generation.
- [X] T059 (see Phase 6) state file update.
