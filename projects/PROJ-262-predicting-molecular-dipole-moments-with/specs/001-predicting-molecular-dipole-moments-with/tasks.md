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
- [X] T050 [P] Enforce a CPU‑core constraint using the `@cpu_limit()` decorator in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/cpu_constraint.py` (FR‑010, SC‑003)
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

- [ ] T016 [US1] Implement deterministic subset generation in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/create_subset.py` (seed 42). This task creates a fixed subset of 5000 molecules from the downloaded QM9 data and outputs `data/processed/subset_final.parquet`. **Note**: The subset size is fixed at 5000 to ensure reproducibility and meet the 6h runtime constraint (Plan: Complexity Tracking). No runtime monitoring or dynamic reduction logic is used.
- [ ] T019 [US1] Generate `data/reports/excluded_molecules.csv` in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/handle_missing_coords.py` – produces a report with columns `molecule_id`, `exclusion_reason` (enum: `missing_3d`, `invalid_structure`), `exclusion_timestamp` and updates `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml` with the artifact hash. **Must run after T016 (depends on T016)**.
- [ ] T105 [US1] [P] Verify existence and schema of `excluded_molecules.csv` generated by T019 in `tests/contract/test_excluded_molecules.py` – assert columns match spec and update state hash.
- [ ] T017 [US1] [P] Implement 3D coordinate, atom type, and bond connectivity extraction in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/preprocess_3d.py` (FR‑002, depends on T016, T019). This task also outputs the final processed features.
- [ ] T018 [US1] [P] Implement 2D Morgan fingerprints and Coulomb matrix generation in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/extract_2d_descriptors.py` (FR‑003, depends on T016, T019). **Note**: Generates both Morgan fingerprints and Coulomb matrices, and includes BOTH in the Random Forest baseline inputs (T029) to satisfy FR-003 baseline comparison requirement.
- [ ] T021 [US1] [P] Implement retry logic for DOI inaccessibility in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/data/download_qm9.py` (FAIL LOUDLY on persistent failure, no synthetic fallback).

### Tests for User Story 1

- [ ] T100 [P] [US1] Contract test for molecule schema (`tests/contract/test_molecule_schema.py`) – Implement `test_molecule_schema_validates_missing_coordinates` to assert that molecules with missing 3D coordinates are flagged and excluded.
- [ ] T101 [P] [US1] Contract test for feature_set schema (`tests/contract/test_feature_set_schema.py`) – Implement `test_feature_set_schema_validates_nan_values` to assert that feature vectors contain no NaN values.
- [ ] T102 [P] [US1] Integration test for QM9 download pipeline with memory profiling (`tests/integration/test_qm9_download.py`) – Implement `test_qm9_download_memory_under_8gb` to verify verify memory usage stays within 8GB limit during download.
- [ ] T103 [P] [US1] Unit test for 3D coordinate extraction (`tests/unit/test_extract_3d_coords.py`) – Implement `test_extract_3d_coords_handles_nan_and_missing_atoms` to assert correct handling of NaN values and missing atoms.
- [ ] T104 [P] [US1] Unit test for 2D descriptor generation (`tests/unit/test_extract_2d_descriptors.py`) – Implement `test_2d_descriptors_verify_fingerprint_length_and_matrix_symmetry` to assert Morgan fingerprint length and Coulomb matrix symmetry.

**Checkpoint**: User Story 1 fully functional and testable independently

---

## Phase 4: User Story 2 – Model Training and Evaluation Pipeline (Priority: P2)

**Goal**: Train lightweight SchNet‑style GNN and Random Forest baseline on identical train/test splits, evaluate both on held‑out test set using MAE and RMSE for dipole moments (50 epochs with early stopping patience=10).

**Independent Test**: Verify training with 50 epochs and early stopping (patience=10), both models produce MAE and RMSE scores on test set, and Confidence intervals are computed across random seeds.

### Implementation for User Story 2

- [ ] T030 [US2] [P] Implement identical train/test split generation across seeds in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/split_data.py`
- [ ] T026 [P] [US2] Implement SchNet‑style GNN architecture in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/models/schnet_gnn.py` (FR‑004, CPU‑only)
- [ ] T027 [P] [US2] Implement Random Forest baseline in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/models/random_forest_baseline.py` (FR‑005)
- [ ] T028 [US2] Implement GNN training with **5 random seeds**, 50 epochs, early stopping (hard-coded patience=10) in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_gnn.py` – compute variance of RMSE across seeds, generate confidence intervals, and ensure they are recorded (fulfills SC‑005).
- [ ] T029 [US2] Train Random Forest baseline with **5 seeds** in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_rf.py` – also records RMSE variance and confidence intervals. **Note**: Uses BOTH Morgan fingerprints and Coulomb matrices as defined in plan.md and FR-003.
- [ ] T031 [US2] Implement MAE and RMSE metric computation in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/evaluate.py` (FR‑006)
- [ ] T032 [US2] Compute MAE/RMSE against QM9 DFT reference values (not experimental) (fulfills FR-011) using the DFT reference data already present in the QM9 dataset.
- [ ] T033 [US2] Save model checkpoints to `data/checkpoints/model_seed_{N}.pt` and `rf_seed_{N}.pkl` – each checkpoint includes model state dict, training config, seed, and timestamp.
- [ ] T034 [US2] Generate `results/metrics.csv` with columns `seed`, `model`, `mae`, `rmse`, `mae_ci_lower`, `mae_ci_upper`, `rmse_ci_lower`, `rmse_ci_upper` (per FR-012 and Plan.md Technical Context).

### Ablation Study & Combined Baseline (Plan.md Phase 2 Requirements)

- [ ] T042 [US2] [P] Implement SchNet-Randomized architecture in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/models/schnet_randomized.py` – shuffles 3D coordinates to isolate geometry contribution.
- [ ] T043 [US2] [P] Implement SchNet-2D architecture in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/models/schnet_2d.py` – identical architecture without 3D coordinates.
- [ ] T044 [US2] [P] Train SchNet-Randomized and SchNet-2D models with **5 seeds**, 50 epochs, early stopping in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/train_ablation.py` – records metrics for causal control analysis.

### Tests for User Story 2

- [ ] T106 [P] [US2] Contract test for model_output schema (`tests/contract/test_model_output_schema.py`) – Implement `test_model_output_schema_validates_prediction_range` to assert predicted dipoles are within physical bounds.
- [ ] T107 [P] [US2] Integration test for GNN training pipeline (`tests/integration/test_gnn_training.py`) – Implement `test_gnn_training_converges_within__epochs` to assert convergence criteria.
- [ ] T108 [P] [US2] Integration test for Random Forest training pipeline (`tests/integration/test_rf_training.py`) – Implement `test_rf_training_rmse_variance_under_threshold` to assert stability across seeds.
- [ ] T109 [P] [US2] Unit test for MAE/RMSE metric computation (`tests/unit/test_metrics.py`) – Implement `test_metrics_handles_empty_input_and_nan` to assert correct edge case handling.

**Checkpoint**: User Stories 1 & 2 functional

---

## Phase 5: User Story 3 – Feature Attribution, Physics Constraints, and Statistical Validation (Priority: P3)

**Goal**: Apply feature attribution and perform rigorous statistical significance testing to address reviewer concerns regarding physical realism, experimental validation standards, and conformational ensembles.

**Independent Test**: Verify that at least 3 structural features are identified, and t-tests confirm significance with explicit reporting of error margins.

### Implementation for User Story 3

- [ ] T039 [US3] [P] Implement enhanced attribution analysis in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/analysis/attribution.py` using **Permutation Importance** for Random Forest and **Saliency Mapping (Input Gradients and Integrated Gradients)** for GNN. The output must explicitly rank features by type (e.g., "Electronegativity of Atom X", "Bond Angle Y", "Hybridization Z") based on the model's learned weights and data-driven importance scores, verifying that at least 3 distinct physical features (per SC-002) have statistically significant attribution scores. **Mapping Logic**: Use RDKit to map feature indices to chemical descriptions. **Dependencies**: T017, T018, T028, T029. **Note**: SHAP is explicitly excluded to comply with Spec FR-007; Input Gradients and Integrated Gradients are included as per Plan Methodology.
- [ ] T040 [US3] [P] Implement a "Validation Protocol & Limitations" report generator in `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/utils/validation_report.py`. This tool must generate a `data/reports/validation_protocol.md` that explicitly states: (1) The ground truth is QM9 DFT data (not experimental), (2) The limitations regarding hydration state and the use of a **Single Lowest-Energy Conformer** per molecule (documenting that conformational ensemble sampling is out-of-scope per Spec Assumptions), and (3) The specific error margins (MAE/RMSE) achieved against the DFT standard. It must also document the "evidentiary standard" used (statistical significance across multiple seeds) to satisfy the demand for explicit measurement standards. **Dependencies**: T017, T018.
- [ ] T041 [US3] [P] Update `projects/PROJ-262-predicting-molecular-dipole-moments-with/code/training/evaluate.py` to compute and report the **Wilcoxon signed-rank test** (primary) comparing RMSE distributions between GNN and baseline, as mandated by Plan.md Methodology and FR-008/SC-004. This task depends on T028 (GNN training), T029 (RF training), and T030 (splits). **Note**: Paired t-tests are not required as the primary deliverable; Wilcoxon is the primary method.

### Tests for User Story 3

- [ ] T113 [P] [US3] Unit test for attribution ranking (`tests/unit/test_attribution_ranking.py`) – Implement `test_physical_features_ranked_significant` to verify that electronegativity and bond angle features appear in the top 3 attributed features.
- [ ] T114 [P] [US3] Contract test for validation report (`tests/contract/test_validation_report.py`) – Implement `test_validation_report_contains_limitations_and_error_bounds` to assert the report explicitly states the DFT ground truth and single-conformer limitations.

**Checkpoint**: User Story 3 complete; all reviewer concerns regarding physical constraints, stereoisomer differentiation, and validation standards addressed.

---

## Phase 6: Removal of Out-of-Scope Tasks

**Note**: Phase 6 (Tasks T220-T225) has been removed from this tasks file. These tasks implemented features (hydration controls, experimental benchmark protocols, physics-informed loss with hardcoded constants) that were explicitly declared out-of-scope by the Spec Assumptions and FR-011. Their implementation would constitute a scope violation. The project will proceed with the core comparative study (2D vs 3D) as defined in the Spec and Plan.

---

## Phase 7: Polish & Documentation

**Purpose**: Finalize reports, update documentation with new physical constraints, and ensure all artifacts are hashed.

- [ ] T115 [P] [Doc] Update `research.md` to synthesize the "Physics-Informed" approach, explicitly citing the bond length/angle constraints and the validation protocol against DFT standards. Address the "hydration state" and "conformational ensemble" limitations as future work.
- [ ] T116 [P] [Doc] Update `quickstart.md` to explain the new physical descriptor features and how to interpret the **ablation variant results** and **Input Gradient maps**. Add specific sections: "Interpreting Ablation Results" (explaining SchNet-Randomized vs SchNet-2D) and "Reading Input Gradient Maps" (explaining saliency visualization).
- [ ] T117 [P] Run `code/utils/hygiene.py` to compute SHA-256 hashes for all new artifacts (`results/attribution.json`, `data/reports/excluded_molecules.csv`, `results/metrics.csv`, model checkpoints) and update `state/projects/PROJ-262-predicting-molecular-dipole-moments-with.yaml`.
- [ ] T118 [P] Run the full pipeline end-to-end with the new constraints to verify the runtime limit is still met and the RMSE variance remains < 10% (verify the value in `results/metrics.csv`).

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (data) and US2 (model outputs) for attribution and statistical analysis. **Specifically requires T018 (2D descriptors) and T017 (3D features) to be implemented before T039 (attribution) can be fully effective.**
- **Revision Phase (P3-Revision)**: Removed. Tasks T220-T225 were deleted due to scope violations.

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

## Parallel Example: User Story 3

```bash
# Launch all attribution and reporting tasks together:
Task: "Implement enhanced attribution analysis in code/analysis/attribution.py"
Task: "Implement validation protocol report generator in code/utils/validation_report.py"

# Launch all ablation study tasks together:
Task: "Implement SchNet-Randomized and SchNet-2D architectures in code/models/"
Task: "Train ablation variants in code/training/train_ablation.py"
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
4. Add User Story 3 → Test independently → Deploy/Demo (Addresses all reviewer concerns)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data Prep)
   - Developer B: User Story 2 (Model Training)
   - Developer C: User Story 3 (Physics Constraints & Attribution)
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
- **Reviewers Addressed**:
  - **Scientific Rigor**: Tasks T039, T040, T041 (Feature attribution, validation protocol, Wilcoxon test).
  - **Ablation Study**: Tasks T042-T044 (Geometry isolation).
  - **Data Integrity**: Tasks T018, T029 (Full descriptor usage per FR-003).
  - **Scope Compliance**: Task T040 (Explicit documentation of single-conformer limitation).
  - **Constraint Preservation**: All tasks now use 5 seeds (T028, T029, T044) and Spec-mandated methods (T039, T041).
  - **Out-of-Scope Removal**: Phase 6 (T220-T225) removed to comply with Spec Assumptions and FR-011.