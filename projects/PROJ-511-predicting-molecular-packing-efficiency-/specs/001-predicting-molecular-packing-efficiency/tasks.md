# Tasks: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Input**: Design documents from `/specs/PROJ-511-predicting-molecular-packing-efficiency/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T001 Create project directory structure: Execute `python code/setup.py` which creates `code/`, `data/`, `data/raw_cif/`, `models/`, `results/`, `contracts/`, `specs/`. Verify existence of all directories.
- [X] T002 Initialize `requirements.txt` with pinned versions (rdkit, torch-cpu, scikit-learn, pandas, numpy, requests, tqdm, jinja2, statsmodels, scipy, matplotlib, seaborn, pyyaml, jsonschema, pymatgen)
- [ ] T003 Create `.gitignore` excluding `data/raw_cif/`, `*.pt`, `*.csv`, `__pycache__`, `.env`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `contracts/dataset.schema.yaml` defining SMILES, PC, CAPE, 3D descriptors, and confounder fields. **Status**: Must be completed before T010 and T019.
- [ ] T005 [P] Create `contracts/model.schema.yaml` and `contracts/validation_report.schema.yaml`
- [X] T006 Create `code/utils.py` with seed fixing, logging setup, and Bondi radii constants (FR-018)
- [X] T007 [P] Create `code/cif_parsing.py` with robust CIF parsing utilities. **Logic**: Use `pymatgen` to parse CIF files (as RDKit does not natively parse CIFs) to extract unit cell and atomic coordinates. This is an allowed exception to the `rdkit`-first rule for the specific step of file parsing. Pass extracted coordinates to RDKit for SMILES generation if needed. Implement explicit error handling for corrupt files (log specific error, raise exception, **never** fall back to synthetic data). (FR-001, FR-002)
- [X] T008 [P] Create `code/config.py` for environment configuration (COD URL, HuggingFace model path, random seeds). **Logic**: Load from `.env` or default to verified constants. (FR-017)
- [ ] T009 [P] Create `code/bondi_constants.py` containing the exact Bondi (1964) radii values and utility functions for volume calculation (FR-018, FR-003, FR-011).
- [ ] T022 [P] [US2] Create `contracts/model.schema.yaml` and `contracts/validation_report.schema.yaml` (Consolidated with T005). **Logic**: Define schema for model weights and validation report. (FR-019)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Build a reproducible SMILES-packing dataset (Priority: P1) 🎯 MVP

**Goal**: Obtain a clean dataset of ≥500 organic crystal structures with SMILES and packing coefficients.

**Independent Test**: The pipeline can be run on a fresh CI runner and must output `data/dataset.csv` with ≥500 rows, valid SMILES, and numeric packing coefficients.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST (TDD).
> **Dependency Note**: While code can be written in parallel, execution depends on T004 (schema) and T018 (implementation).

- [ ] T010 [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`. **Dependency**: Must run AFTER T018 completes. **Depends on**: T004 (schema creation). (FR-019)
- [X] T011 [P] [US1] Integration test for download and parse pipeline in `tests/integration/test_download_parse.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download_cif.py` to fetch organic CIFs (≤50 non-H atoms) from COD with logging (FR-001, FR-017)
- [X] T013 [US1] Implement `code/parse_cif.py` to extract/generate SMILES via RDKit, flag source, and record confounders. **Specific Logic**:
 - Extract SMILES from `_chemical_structure_SMILES` if present; else generate from 3D geometry **using ONLY 2D connectivity** (bond data from CIF) to prevent data leakage into the target.
 - **Confounders**: Extract `lattice_system` from `_symmetry_space_group_name_H-M`, `temperature_K` from `_exptl_temperature` or `_cell_measurement_reflns_temperature` (or default K), and `has_solvent` by checking `_chemical_formula_sum` for solvent patterns.
 - **Output**: `data/dataset_intermediate.csv` with columns: `cod_id`, `smiles`, `smiles_source`, `unit_cell_volume`, `n_atoms`, `lattice_system`, `temperature_K`, `has_solvent`. (FR-002, FR-013)
- [ ] T015 [US1] Implement `code/compute_RAW_metrics.py` to calculate **Raw Packing Coefficient (PC_raw)** (Target) and **Composition-Adjusted Packing Efficiency (CAPE)** (Diagnostic). **Logic**: 
 1. Calculate `PC_raw = Unit-cell volume / Sum(V_vdW)`. **This is the regression target.**
 2. Calculate `CAPE = PC_raw / (Sum(V_vdW) / N_atoms)`. **This is a diagnostic covariate.**
 3. **Target Definition**: PC_raw is the regression target. CAPE is a diagnostic. 
 4. **Dependency**: Requires T009 (Bondi constants) to be complete.
 **Reads `data/dataset_intermediate.csv` and produces `data/dataset_with_metrics.csv`.** (FR-003, FR-011)
- [ ] T016 [US1] Implement `code/filter_dataset.py` to filter records with missing SMILES, invalid PC_raw, or invalid CAPE from `data/dataset_with_metrics.csv`, producing `data/dataset_filtered.csv` (FR-003, SC-001). Explicitly ensure PC_raw is valid before filtering.
- [ ] T017 [US1] Add logging for download statistics, parsing failures, and filtering counts (FR-001, FR-017). **Specific Logic**: Log the results of T016 filtering (counts of removed records and reasons) to ensure traceability.
- [ ] T018 [US1] Implement `code/add_3d_descriptors.py` to calculate 3D descriptors (radius of gyration, asphericity, principal moments) using **experimental CIF coordinates**. **Logic**: Read `cod_id` from `data/dataset_filtered.csv`. Re-load the original CIF file from `data/raw_cif/` using `pymatgen`. **Verify existence and validity of CIF file for each cod_id; raise FileNotFoundError if missing.** Compute descriptors (radius of gyration, asphericity, principal moments) from the **raw CIF coordinates** (experimental data) as mandated by FR-004 and FR-012. **Note**: SMILES generation (T013) uses 2D connectivity to prevent leakage; 3D descriptors use experimental coordinates to model the physical state. **Reads `data/dataset_filtered.csv` to get `cod_id` and merges 3D descriptors to produce final `data/dataset.csv`.** **Output columns must include**: `cod_id`, `smiles`, `smiles_source`, `unit_cell_volume`, `n_atoms`, `lattice_system`, `temperature_K`, `has_solvent`, `radius_of_gyration`, `asphericity`, `principal_moments`, `cape`, `raw_pc`. **Provenance**: Must retain `cod_id` and `smiles_source` tags to satisfy Constitution Principle VI. (FR-004, FR-012, FR-017)
- [ ] T019 [US1] Implement `code/validate_dataset.py` to check `data/dataset.csv` against `contracts/dataset.schema.yaml` (SC-001). **Includes**: 1) Cross-referencing COD IDs in the CSV against the list of downloaded CIF files to ensure data integrity per FR-017. 2) Explicitly recording and verifying the COD source URL and version identifier used for the download (FR-017). **Dependency**: Must run after T018. (FR-017)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and evaluate a lightweight predictor (Priority: P2)

**Goal**: Train a multi-layer perceptron on SMILES-transformer features + D descriptors + confounders to predict PC_raw, with rigorous statistical validation.

**Independent Test**: Running the training script on `dataset.csv` must produce `model.pt` and `results/validation_report.json` with MAE, Pearson r, Spearman ρ, Shapiro-Wilk, and a permutation p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [US2] Contract test for model output schema in `tests/contract/test_model_schema.py`. **Dependency**: Must run AFTER T025 and T029 complete. (FR-019)
- [X] T023 [P] [US2] Integration test for training and evaluation pipeline in `tests/integration/test_train_evaluate.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement `code/feature_assembly.py` to encode SMILES using frozen `seyonec/PubChem10M_SMILES_BPE_60k` (CPU) and **assemble the final feature matrix**. **Inputs**: `data/dataset.csv`. **Features**: `smiles_transformer_embedding` + `radius_of_gyration`, `asphericity`, `principal_moments` + confounders (`lattice_system`, `temperature_K`, `has_solvent`). **Logic**: Use **mean pooling over token embeddings** to produce a fixed-length vector from the variable-length SMILES input. **Critical Dependency**: Use ONLY the 3D descriptors produced by T018 (CIF coordinates). **Output**: `data/features_matrix.npy` and `data/targets.npy` (where targets are PC_raw values). **Note**: This task produces the input for T025. (FR-004, FR-013)
- [ ] T025 [US2] Implement `code/train.py` to train a **multi-layer perceptron** (Input -> Hidden -> Hidden -> Output) to predict **PC_raw** (Raw Packing Coefficient). **Architecture**: Two hidden layers with 32 units each, ReLU activation, Dropout 0.1. **Constraint**: Total trainable parameters must be ≤ 100k as per FR-005. **Optimizer**: Adam (lr=1e-3), Batch Size 32. **Inputs**: `data/features_matrix.npy`, `data/targets.npy`. **Outputs**: `models/mlp.pt`. (FR-005)
- [ ] T026 [US2] Implement `code/evaluate.py` to compute MAE, Pearson r, Spearman ρ on validation set. (FR-006, FR-015)
- [ ] T027 [US2] Implement `code/evaluate.py` to run a **fixed two-sided permutation test** with **10,000** shuffles (FR-006, FR-016). **Logic**: Shuffle labels [deferred] times, compute correlation for each, calculate the two-sided p-value as the fraction of shuffled correlations with absolute value ≥ observed absolute correlation. **Output**: Final p-value and total shuffle count in `results/validation_report.json`. (FR-016, SC-005)
- [ ] T028 [US2] Implement `code/evaluate.py` to perform VIF diagnostics on **ALL predictor variables** (fingerprint dimensions, 3D descriptors, confounders) as mandated by FR-009. **Use `statsmodels.stats.outliers_influence.variance_inflation_factor` on the full feature matrix. Do NOT omit any raw dimensions.** **Note**: If the transformer embedding dimension is too high for stable VIF, apply PCA to reduce dimensions to a manageable number before VIF calculation, and report the variance retained. (FR-009)
- [ ] T029 [US2] Implement `code/evaluate.py` to compute **all evaluation metrics** and write a single `results/validation_report.json`. **Primary Metrics**: `pearson_r`, `spearman_rho`, `mae`. **Diagnostics**: `shapiro_wilk_p` (Perform Shapiro-Wilk test on PC_raw residuals), `partial_corr_r`, `partial_corr_p` (partial correlation controlling for atom-type composition as per FR-014), `vif_flags`, `permutation_p_value` (computed with **[deferred]** shuffles). **Output**: Complete JSON object with all keys listed above, ensuring schema compliance with `contracts/validation_report.schema.yaml`. (FR-006, FR-014, FR-015, FR-009, FR-016)
- [ ] T030 [US2] Implement `code/generate_report.py` to produce `results/report.html` validated against schema (FR-010, FR-019)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Assess robustness to threshold choices (Priority: P3)

**Goal**: Verify that predictive conclusions are not driven by arbitrary packing efficiency cutoffs.

**Independent Test**: Executing the sensitivity script must sweep thresholds across the specific set {0.5, 0.6, 0.7} and output a table of r, MAE, and p-values with Bonferroni correction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_schema.py`
- [ ] T032 [P] [US3] Integration test for threshold sweep in `tests/integration/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/sensitivity.py` to perform a comprehensive sensitivity analysis. **Logic**: 1) Sweep high-packing threshold over the specific set **{0.5, 0.6, 0.7}** (FR-007). 2) Compute r, ρ, MAE, and p-values for each threshold. 3) Apply Bonferroni correction: **multiply raw p-value by 3 (number of tests) and cap at 1.0** (FR-008). 4) Verify variation in r is ≤ ±0.05 (SC-004). **Input**: Model predictions from T025. **Output**: `results/sensitivity_sweep.csv` containing columns: `threshold`, `r`, `rho`, `mae`, `p_value`, `bonferroni_corrected_p`. (FR-007, FR-008, SC-004)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T051 [P] Run full end-to-end pipeline on CI and verify runtime ≤ 6 hours (SC-005). **Logic**: If runtime exceeds **5 hours**, detect timeout, reduce permutation count to **1,000** shuffles (with explicit logging of deviation and statistical power impact), and continue to ensure the pipeline completes within the budget while maintaining statistical validity. (SC-005)
- [ ] T052c [P] **Compute Feasibility**: Verify that the pipeline (download → report) completes within the time budget on the free-tier runner. Log any steps exceeding hours. (SC-005)
- [ ] T053 [P] Performance optimization: parallelize permutation test shuffles if needed (within CPU limits)
- [ ] T054 [P] Additional unit tests for feature extraction logic in `tests/unit/`
- [ ] T057 [US1, US2, US3] Validate SC-004 for the single model by checking the variation in r across thresholds.

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

---

## Parallel Example: User Story 1

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
 - Developer B: User Story 2 (initial implementation)
 - Developer C: User Story 3 (initial implementation)
3. Integrate and test each story independently
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Revision Note**: T018 now correctly uses **experimental CIF coordinates** as mandated by FR-004, removing the previous 'gas-phase' deviation. SMILES generation (T013) is restricted to 2D connectivity to prevent data leakage.
- **Critical Revision Note**: T025 now correctly implements a 2-layer MLP (2 hidden layers) with explicit constraints: 'two hidden layers with 32 units each' and 'total parameters ≤ 100k' as per FR-005, and explicitly targets **PC_raw** as the regression variable.
- **Critical Revision Note**: T027 and T029 now correctly mandate **[deferred]** shuffles as per FR-016, replacing all placeholder claims.
- **Critical Revision Note**: T024 now explicitly mandates sourcing 3D descriptors ONLY from T018's CIF-coordinate output.
- **Critical Revision Note**: T051 and T052c now include a specific mechanism to handle runtime timeouts (reduce to [deferred] shuffles after 5 hours) as per the spec's 'deferred' clause.
- **Critical Revision Note**: T009 description has been corrected to remove copy-paste errors and unresolved claims.
- **Critical Revision Note**: T015 now explicitly quotes the PC_raw/CAPE formulas from FR-003/FR-011 to ensure deterministic implementation and clarifies PC_raw is the target.
- **Critical Revision Note**: Phase 6 (T040-T045) has been **REMOVED** to eliminate scope creep and unrequested features.
- **Critical Revision Note**: T004 is marked [ ] (pending) to reflect that the schema file must be created before dependent tasks.
- **Critical Revision Note**: T010 and T022 are marked [ ] (pending) and their descriptions updated to reflect they must run after their respective producer tasks (T018, T025/T029).
- **Critical Revision Note**: T033 now explicitly specifies the Bonferroni correction method (multiply by 3).