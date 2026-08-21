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
- [X] T015 [Foundational] [P] Verify DOI 10.1038/sdata.2014.22 exists in local reference registry [UNRESOLVED-CLAIM: c_1133c4ac — status=verified] and record its hash in `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` (depends on T090, T091). This is a prerequisite for US1.
- [X] T210 [P] [Doc] Update `research.md` to explicitly document scope boundaries: state that physical measurement validation (e.g., Stark-effect spectroscopy) is out-of-scope and that QM DFT reference data (BLYP/augmented basis set) serves as the sole ground truth (Addresses FR-011, Spec Assumptions).

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel

---

## Phase 3: User Story 1 – Dataset Preparation and Baseline Feature Extraction (Priority: P1)

**Goal**: Download QM9 dataset, filter to a random subset, extract both 3D coordinates and 2D descriptors for baseline comparison.

**Independent Test**: Verify data files exist, subset size is substantial, and both 3D and 2D feature matrices are generated with no missing values.

### Implementation for User Story 1

- [X] T016a [US1] Implement runtime monitoring wrapper in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/runtime_monitor.py` that tracks elapsed time against the 6h limit. If the limit is approached, it triggers a subset reduction flag. This flag is consumed by T016b to iteratively reduce the target subset size. (Note: Sequential dependency on T016b, not parallel).
- [X] T016b [US1] Implement subset reduction logic in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/create_subset.py` (seed 42). This task creates an initial subset, runs the monitor (T016a), and if the flag is set, re-executes with a smaller target to output `data/processed/subset_final.parquet` with the final molecule list. Depends on T016a.
- [X] T017 [US1] [P] Implement 3D coordinate, atom type, and bond connectivity extraction in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/preprocess_3d.py` (FR‑002, depends on T016b). This task also outputs the final processed features.
- [X] T018 [US1] [P] Implement 2D Morgan fingerprints and Coulomb matrix generation in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/extract_2d_descriptors.py` (FR‑003, depends on T016b). **Note**: Generates Coulomb matrices as 3D-derived artifacts for potential future use, but explicitly excludes them from the Random Forest baseline inputs which must use ONLY Morgan fingerprints and topological counts per plan.md methodology.
- [ ] T019 [US1] [P] Add validation for missing 3D coordinates in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/handle_missing_coords.py` – generates `data/reports/excluded_molecules.csv` with columns `molecule_id`, `exclusion_reason` (enum: `missing_3d`, `invalid_structure`), `exclusion_timestamp`.
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

**Goal**: Train lightweight SchNet‑style GNN and Random Forest baseline on identical train/test splits, evaluate both on held‑out test set using MAE and RMSE for dipole moments (50 epochs with early stopping patience=10) [UNRESOLVED-CLAIM: c_b422b767 — status=not_enough_info].

**Independent Test**: Verify training with 50 epochs and early stopping (patience=10), both models produce MAE and RMSE scores on test set, and Confidence intervals are computed across random seeds.

### Implementation for User Story 2

- [X] T026 [P] [US2] Implement SchNet‑style GNN architecture in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/models/schnet_gnn.py` (FR‑004, CPU‑only)
- [X] T027 [P] [US2] Implement Random Forest baseline in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/models/random_forest_baseline.py` (FR‑005)
- [X] T028 [US2] Implement GNN training with multiple seeds, 50 epochs, early stopping (hard-coded patience=10) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_gnn.py` – compute variance of RMSE across seeds, generate confidence intervals, and ensure they are recorded (fulfills SC‑005).
- [X] T029 [US2] Train Random Forest baseline with seeds in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_rf.py` – also records RMSE variance and confidence intervals. **Note**: Uses ONLY 2D features (Morgan fingerprints, topological counts) as defined in plan.md, explicitly excluding Coulomb matrices.
- [X] T030 [US2] Implement identical train/test split generation across seeds in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/split_data.py`
- [X] T031 [US2] Implement MAE and RMSE metric computation in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/evaluate.py` (FR‑006)
- [X] T032 [US2] Compute MAE/RMSE against QM9 DFT reference values (not experimental) [UNRESOLVED-CLAIM: c_19b82439 — status=not_enough_info] (fulfills FR‑011) using the DFT reference data already present in the QM9 dataset.
- [X] T033 [US2] Save model checkpoints to `data/checkpoints/model_seed_{N}.pt` and `rf_seed_{N}.pkl` – each checkpoint includes model state dict, training config, seed, and timestamp.
- [X] T034 [US2] Generate `results/metrics.csv` with columns `seed`, `model`, `mae`, `rmse`, `mae_ci_lower`, `mae_ci_upper`, `rmse_ci_lower`, `rmse_ci_upper` – {{claim:c_6ac9c374}} (0804.4361, https://arxiv.org/abs/0804.4361).

### Tests for User Story 2

- [X] T106 [P] [US2] Contract test for model_output schema (`tests/contract/test_model_output_schema.py`) – Implement `test_model_output_schema_validates_prediction_range` to assert predicted dipoles are within physical bounds.
- [X] T107 [P] [US2] Integration test for GNN training pipeline (`tests/integration/test_gnn_training.py`) – Implement `test_gnn_training_converges_within__epochs` to assert convergence criteria.
- [X] T108 [P] [US2] Integration test for Random Forest training pipeline (`tests/integration/test_rf_training.py`) – Implement `test_rf_training_rmse_variance_under_threshold` to assert stability across seeds.
- [X] T109 [P] [US2] Unit test for MAE/RMSE metric computation (`tests/unit/test_metrics.py`) – Implement `test_metrics_handles_empty_input_and_nan` to assert correct edge case handling.

**Checkpoint**: User Stories 1 & 2 functional

---

## Phase 5: User Story 3 – Feature Attribution and Statistical Significance Analysis (Priority: P3)

**Goal**: Apply permutation importance to Random Forest and saliency mapping to GNN embeddings, perform paired t‑tests to confirm statistical significance of the performance delta.

**Independent Test**: Verify feature importance rankings are generated, t-test p-values are computed, and structural contributions are ranked.

### Implementation for User Story 3

- [X] T038 [P] [US3] Implement permutation importance for Random Forest in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/attribution/permutation_importance.py` (FR‑007)
- [X] T039 [P] [US3] Implement saliency mapping for GNN node embeddings in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/attribution/saliency_mapping.py` (FR‑007)
- [X] T040 [US3] Rank structural contributions (e.g., electronegative atom placement, local bond angles) and (FR‑007, SC‑002). This task must explicitly count and verify at least 3 (2405.13996, https://arxiv.org/abs/2405.13996) distinct features.
- [X] T041 [US3] Implement paired t‑tests (α = 0.05) comparing RMSE distributions in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/statistical_tests.py` (FR‑008, SC‑004)
- [X] T042 [US3] Generate `results/attributions.json` with feature importance rankings
- [X] T043 [US3] Generate `results/significance.csv` with columns `seed`, `t_statistic`, `p_value`, `significant_at_alpha_threshold` (FR‑008)
- [X] T045 [US3] Visualize feature‑importance maps on representative molecules (e.g., `data/processed/attributions_*.png`) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/visualize_features.py` (FR‑009)

### Tests for User Story 3

- [X] T111 [P] [US3] Integration test for permutation importance pipeline (`tests/integration/test_permutation_importance.py`) – Implement `test_permutation_importance_generates_ranked_features` to assert correct ranking logic.
- [X] T112 [P] [US3] Integration test for saliency mapping pipeline (`tests/integration/test_saliency_mapping.py`) – Implement `test_saliency_mapping_produces_valid_gradients` to assert gradient validity.
- [X] T113 [P] [US3] Unit test for paired t‑test computation (`tests/unit/test_statistical_tests.py`) – Implement `test_t_test_handles_equal_variance_and_small_samples` to assert correct statistical handling.

**Checkpoint**: All user stories independently functional

---

## Phase 6: Validation and Requirements Alignment

**Purpose**: Verify that all functional requirements (FR‑001 – FR‑013) and success criteria (SC‑001 – SC‑005) are satisfied, and that documentation complies with the constitution. This phase includes physical rigor checks required by the Constitution Check table.

- [X] T053 [P] Run reference-validator script (T090, T091) to verify local DOI metadata matches registered references; no external URL fetching performed (satisfies Constitution Principle II and 'no URL fabrication' constraint).
- [X] T301 [P] [US2] Implement a geometric invariance test in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/geometry_invariance.py` that rotates molecules by random angles and Verify dipole magnitude prediction remains stable within 0.01 D when molecules are rotated by random angles [UNRESOLVED-CLAIM: c_b22801d1 — status=not_enough_info]. Output: `results/geometry_invariance_report.json`. (Addresses Constitution Principle VI and Plan.md Constitution Check).
- [X] T307 [P] [US3] Implement a "feature contribution visualization" in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/physical_contribution.py` that maps GNN attention weights to specific bond lengths and angles using matplotlib. Output: `data/processed/attention_heatmaps.png`. (Addresses FR-009, SC-002).
- [X] T054 [P] Populate documentation files with required sections (overview, installation, usage, results, limitations) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/specs/001-predicting-molecular-dipole-moments-with/`.
- [X] T057 [P] Quick‑start validation checks for existence of all data files, non‑NaN metrics, and at least one attribution visualisation; fails otherwise.
- [X] T058 [P] Summary includes MAE/RMSE with 95 % CI, top‑k feature importance entries, paired‑t‑test p‑values, and links to generated figures.
- [X] T059 [P] State file `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` follows YAML schema with `completed_at`, `artifact_hashes` (SHA‑256 per file), and `updated_at`.
- [X] T094 [P] Validate total pipeline runtime: Read `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` (updated_at) and `results/metrics.csv` to calculate total elapsed time from data download to final metric generation; Verify against a predefined time limit. (SC‑003, FR‑010). **Note**: Depends on T055 for start/end time logs.

**Checkpoint**: All functional requirements verified against spec and constitution.

---

## Phase 7: Documentation & Polish

**Purpose**: Final documentation, end‑to‑end validation, and project cleanup. This phase consolidates all documentation tasks, including explicit scope boundary documentation.

- [X] T250 [Doc] [US1/US2/US3] Update `research.md` to include a section titled "## Limitations and Scope Boundaries" that explicitly states: (1) Physical measurement validation is out-of-scope; (2) QM DFT data (BLYP/augmented split-valence basis set with polarization functions) is the sole ground truth; (3) Hydration effects and conformational ensembles are out-of-scope; (4) The model predicts DFT values, not experimental reality. (Addresses FR-011, Spec Assumptions, and replaces T210).

**Checkpoint**: All user stories independently functional, validated, and scope boundaries explicitly documented.

---

## Phase 8: Documentation & Scope Clarification

**Purpose**: Finalize documentation to ensure all scope boundaries and limitations are clearly communicated, aligning with the Constitution and Spec. This phase contains NO implementation tasks for out-of-scope features.

### Implementation for Documentation

- [X] T306 [Doc] Update `research.md` to include a "Validation Protocol" section that explicitly states: (1) Ground truth is QM DFT (BLYP/polarized double-zeta basis set) [UNRESOLVED-CLAIM: c_99b75d59 — status=not_enough_info], (2) Experimental validation is out-of-scope per FR-011, (3) The "evidentiary standard" is internal consistency across multiple seeds and geometric invariance, addressing Marie Curie's and Rosalind Franklin's requests for explicit validation standards.
- [X] T308 [Doc] Update `research.md` to explicitly state that out-of-scope items (hydration, ensembles, peptide constraints) are documented as limitations and future work, confirming no tasks implement them as core features.

**Checkpoint**: All documentation aligned with spec constraints.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Validation (Phase 6)**: Depends on completion of Phase 5 (User Story 3) to ensure baseline metrics are established before final sign-off.
- **Documentation (Phase 7-8)**: Depends on completion of Phase 6 to ensure all results are finalized.

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
- Documentation tasks (Phase 8) can be implemented in parallel by different team members focusing on specific documentation sections.

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
5. Add Phase 6-7 Enhancements → Refine documentation → Deploy/Demo
6. Add Phase 8 Documentation → Finalize scope boundaries → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently
4. Developer D: Phase 8 Documentation tasks (Scope Boundaries, Validation Protocol)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Note on Scope**: All tasks strictly adhere to the spec's defined scope (QM9 DFT data, single conformer, lightweight SchNet). No experimental validation, conformational ensembles, or hydration analysis are implemented as core features, but their limitations are explicitly documented in T250, T306, and T308. Phase 9 (out-of-scope tasks) has been removed.
- **Revision Note**: Removed all tasks (T401-T415) that implemented unauthorized scope-creep features (hydration analysis, stereoisomer breakdown, experimental validation) which violated FR-011 and spec assumptions. Corrected state inconsistency for T210 (replaced by T250). Updated T016 to split into T016a (monitoring) and T016b (reduction logic) with correct sequential dependency (T016a must run before T016b). Reordered Phase 3 to list Implementation before Tests for clarity of dependency flow. Updated T032 to explicitly state "DFT reference values (not experimental)". Moved T301 and T307 to Phase 6 to ensure validation occurs before completion. Added T055 to enforce aggregate pipeline runtime. Updated T018 to clarify Coulomb matrix exclusion from 2D baseline. Removed T210 from task list and ensured T250 is present.
- **Documentation Note**: Phase 8 now focuses exclusively on documenting scope boundaries and validation protocols, ensuring alignment with the Constitution and Spec without introducing unauthorized features. T308 explicitly confirms out-of-scope items are documented as limitations.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T402 Reconcile run-book vs implementation for `code/download_data.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/download_data.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T403 Reconcile run-book vs implementation for `code/train.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/train.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T404 Reconcile run-book vs implementation for `code/attribution.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/attribution.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T405 Reconcile run-book vs implementation for `code/stats.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/stats.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
