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

- [X] T001 Create project directory structure: Execute `python code/setup.py` which creates `code/`, `data/`, `data/raw_cif/`, `models/`, `results/`, `contracts/`. Verify existence of all directories.
- [X] T002 Initialize `requirements.txt` with pinned versions (rdkit, torch-cpu, scikit-learn, pandas, numpy, requests, tqdm, jinja2, statsmodels, scipy, matplotlib, seaborn, pyyaml, jsonschema, pymatgen)
- [X] T003 [P] Create `.gitignore` excluding `data/raw_cif/`, `*.csv`, `*.npy`, `models/`, `results/`, `__pycache__`, `.env`. **Exact Content**:
 ```
 data/raw_cif/
 data/*.csv
 data/*.npy
 models/
 results/
 __pycache__/
 *.pyc
.env
.DS_Store
.venv/
 venv/
 ```
 Verify file creation and content match.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `contracts/dataset.schema.yaml`, `contracts/model.schema.yaml`, and `contracts/validation_report.schema.yaml`. **Status**: Completed. **Schema Content**:
 ```yaml
 # dataset.schema.yaml
 $schema: http://json-schema.org/draft-07/schema#
 type: object
 required:
 - cod_id
 - smiles
 - smiles_source
 - unit_cell_volume
 - n_atoms
 - raw_pc
 - cape
 - radius_of_gyration
 - asphericity
 - principal_moments
 - lattice_system
 - temperature_K
 - has_solvent
 properties:
 cod_id:
 type: string
 pattern: "^COD-\\d+$"
 smiles:
 type: string
 minLength: 1
 smiles_source:
 type: string
 enum: ["extracted", "generated"]
 unit_cell_volume:
 type: number
 exclusiveMinimum: 0
 n_atoms:
 type: integer
 minimum: 1
 raw_pc:
 type: number
 minimum: 0
 maximum: 1
 cape:
 type: number
 minimum: 0
 radius_of_gyration:
 type: number
 minimum: 0
 asphericity:
 type: number
 minimum: 0
 maximum: 1
 principal_moments:
 type: array
 items:
 type: number
 minItems: 3
 maxItems: 3
 lattice_system:
 type: string
 temperature_K:
 type: number
 minimum: 0
 has_solvent:
 type: boolean
 ```
 ```yaml
 # model.schema.yaml
 $schema: http://json-schema.org/draft-07/schema#
 type: object
 required:
 - model_path
 - architecture
 - parameters_count
 - training_config
 properties:
 model_path:
 type: string
 architecture:
 type: object
 required:
 - input_dim
 - hidden_layers
 - output_dim
 properties:
 input_dim:
 type: integer
 hidden_layers:
 type: array
 items:
 type: integer
 output_dim:
 type: integer
 parameters_count:
 type: integer
 maximum: 100000
 training_config:
 type: object
 properties:
 optimizer:
 type: string
 learning_rate:
 type: number
 epochs:
 type: integer
 batch_size:
 type: integer
 ```
 ```yaml
 # validation_report.schema.yaml
 $schema: http://json-schema.org/draft-07/schema#
 type: object
 required:
 - pearson_r
 - spearman_rho
 - mae
 - shapiro_wilk_p
 - partial_corr_r
 - partial_corr_p
 - vif_flags
 - permutation_p_value
 - permutation_shuffles
 - bonferroni_corrected_p
 properties:
 pearson_r:
 type: number
 spearman_rho:
 type: number
 mae:
 type: number
 shapiro_wilk_p:
 type: number
 partial_corr_r:
 type: number
 partial_corr_p:
 type: number
 vif_flags:
 type: object
 additionalProperties:
 type: number
 permutation_p_value:
 type: number
 permutation_shuffles:
 type: integer
 bonferroni_corrected_p:
 type: number
 minimum: 0
 maximum: 1
 ```
 **Dependency**: Must be completed before T010 and T022.
- [X] T005 [P] Create `code/utils.py` with seed fixing, logging setup, and Bondi radii constants (FR-018)
- [X] T009 [PLAN-CORRECTION] [P] **Update Plan.md Summary**: Edit `plan.md` to correct the Summary section. Change the text from "predicts Raw Packing Coefficient (PC_raw)" to "predicts Composition-Adjusted Packing Efficiency (CAPE)". Ensure the Summary explicitly states that PC_raw is a diagnostic metric only, aligning the plan with spec.md FR-011 and FR-006. **Verification**: Verify `plan.md` no longer contains contradictions regarding the target variable. (FR-011, FR-006, SC-002) **Status**: COMPLETED. Plan.md has been updated to reflect CAPE as the target.
- [X] T006 [P] Create `code/cif_parsing.py` with robust CIF parsing utilities. **Logic**: Use `pymatgen` to parse CIF files (as RDKit does not natively parse CIFs) to extract unit cell and atomic coordinates. Pass extracted coordinates to RDKit for SMILES generation if needed. Implement explicit error handling for corrupt files (log specific error, raise exception, **never** fall back to synthetic data). (FR-001, FR-002)
- [X] T007 [P] Create `code/config.py` for environment configuration (COD URL, HuggingFace model path, random seeds). **Logic**: Load from `.env` or default to verified constants. (FR-017)
- [X] T008 [P] Create `code/bondi_constants.py` containing the exact Bondi radii values and utility functions for volume calculation. **Source**: Bondi, A. (1964) *J. Phys. Chem.*, 68, 441–452, DOI:10.1021/j100785a001. **Constraint**: Must match the primary source exactly to satisfy Constitution Principle II (Verified Accuracy) and FR-018. (FR-018, FR-003, FR-011)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Build a reproducible SMILES-packing dataset (Priority: P1) 🎯 MVP

**Goal**: Obtain a clean dataset of ≥500 organic crystal structures with SMILES and packing coefficients.

**Independent Test**: The pipeline can be run on a fresh CI runner and must output `data/dataset.csv` with ≥500 rows, valid SMILES, and numeric packing coefficients.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST (TDD).
> **Dependency Note**: While code can be written in parallel, execution depends on T004 (schema) and T018 (dataset generation) complete.

- [X] T010 [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`. **Dependency**: Test code written in parallel; execution requires T018 (dataset generation) and T004 (schema). **Note**: Execution is strictly sequential; authoring is parallel. (FR-019)
- [X] T011 [P] [US1] Integration test for download and parse pipeline in `tests/integration/test_download_parse.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download_cif.py` to fetch organic CIFs (≤50 non-H atoms) from COD with logging (FR-001, FR-017)
- [X] T013 [US1] Implement `code/parse_cif.py` to extract or generate SMILES via RDKit, flag source, and record confounders. **Specific Logic**:
 - Extract SMILES from `_chemical_structure_SMILES` if present.
 - **Fallback**: If absent, **generate a canonical SMILES from the 3D geometry** using RDKit. **CRITICAL CONSTRAINT**: Generation MUST use **only bond-connectivity information**. **Implementation**: Parse the CIF block using `rdkit.Chem.MolFromMolBlock` with `removeHs=False` to get the 2D/3D block, then use `rdkit.Chem.rdmolops.AssignBondOrdersFromTemplate` with a generic 2D template or a distance-based bond inference algorithm **BEFORE** any conformational optimization or energy minimization. **DO NOT** use the final optimized 3D coordinates used for the target calculation. This ensures the SMILES predictor is independent of the experimental 3D coordinates used to calculate the target.
 - **Confounders**: Extract `lattice_system` from `_symmetry_space_group_name_H-M`, `temperature_K` from `_exptl_temperature` or `_cell_measurement_reflns_temperature` (or default K), and `has_solvent` by checking `_chemical_formula_sum` for solvent patterns.
 - **Output**: `data/dataset_intermediate.csv` with columns: `cod_id`, `smiles`, `smiles_source`, `unit_cell_volume`, `n_atoms`, `lattice_system`, `temperature_K`, `has_solvent`. (FR-002, FR-013)
- [X] T015 [US1] Implement `code/compute_RAW_metrics.py` to calculate **Raw Packing Coefficient (PC_raw)** (Diagnostic) and **Composition-Adjusted Packing Efficiency (CAPE)** (Target). **Logic**:
 1. Calculate `PC_raw = Unit-cell volume / Sum(V_vdW)`. **This is a diagnostic metric only.** (Corrected formula per FR-003).
 2. Calculate `CAPE = PC_raw / (Sum(V_vdW) / N_atoms)`. **This is the regression target.**
 3. **Target Definition**: CAPE is the regression target. PC_raw is diagnostic.
 4. **Dependency**: Requires T008 (Bondi constants) to be complete.
 **Reads `data/dataset_intermediate.csv` and produces `data/dataset_with_metrics.csv`.** (FR-003, FR-011)
- [X] T016 [US1] Implement `code/filter_dataset.py` to filter records with missing SMILES, invalid PC_raw, or invalid CAPE from `data/dataset_with_metrics.csv`, producing `data/dataset_filtered.csv` (FR-003, SC-001). **Logic**:
 - Remove rows where `smiles` is null or empty.
 - Remove rows where `raw_pc` is not in [0, 1] or is NaN.
 - Remove rows where `cape` is NaN or infinite.
 - Log counts of removed records and reasons.
 **Verification**: Verify `data/dataset_filtered.csv` exists with N rows (N >= 500) and assert no rows with null CAPE values. **Exit with code 1 if N < 500.** (FR-003, SC-001)
- [X] T017 [US1] Add logging for download statistics, parsing failures, and filtering counts (FR-001, FR-017). **Specific Logic**: Log the results of T016 filtering (counts of removed records and reasons) to ensure traceability.
- [X] T018 [US1] Implement `code/add_3d_descriptors.py` to calculate 3D descriptors (radius of gyration, asphericity, principal moments) using **experimental CIF coordinates**. **Logic**: Read `cod_id` from `data/dataset_filtered.csv`. Re-load the original CIF file from `data/raw_cif/` using `pymatgen`. **Verify existence and validity of CIF file for each cod_id; raise FileNotFoundError if missing.** Compute descriptors (radius of gyration, asphericity, principal moments) from the **raw CIF coordinates** (experimental data) as mandated by FR-004 and FR-012. **Note**: SMILES generation (T013) uses 3D geometry as fallback to prevent data leakage (as per spec); 3D descriptors use experimental coordinates to model the physical state. **Reads `data/dataset_filtered.csv` to get `cod_id` and merges 3D descriptors to produce final `data/dataset.csv`.** **Output columns must include**: `cod_id`, `smiles`, `smiles_source`, `unit_cell_volume`, `n_atoms`, `lattice_system`, `temperature_K`, `has_solvent`, `radius_of_gyration`, `asphericity`, `principal_moments`, `cape`, `raw_pc`. **Provenance**: Must retain `cod_id` and `smiles_source` tags to satisfy Constitution Principle VI. (FR-004, FR-012, FR-013). **Verification**: Verify `data/dataset.csv` exists, row count matches input from T016, and all required columns are present.
- [X] T019 [US1] Implement `code/validate_dataset.py` to check `data/dataset.csv` against `contracts/dataset.schema.yaml` (SC-001). **Includes**: 1) Cross-referencing COD IDs in the CSV against the list of downloaded CIF files to ensure data integrity per FR-017. 2) Explicitly recording and verifying the COD source URL and version identifier used for the download (FR-017). **Dependency**: Must run after T018. (FR-017). **Verification**: Verify that `data/dataset.csv` passes `contracts/dataset.schema.yaml` and that the script exits with code 0 only if validation succeeds. Log the count of valid records.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and evaluate a lightweight predictor (Priority: P2)

**Goal**: Train a multi-layer perceptron on SMILES-transformer features + D descriptors + confounders to predict CAPE, with rigorous statistical validation.

**Independent Test**: Running the training script on `dataset.csv` must produce `model.pt` and `results/validation_report.json` with MAE, Pearson r, Spearman ρ, Shapiro-Wilk, and a permutation p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [US2] Contract test for model output schema in `tests/contract/test_model_schema.py`. **Dependency**: Test code written in parallel; execution requires T025 and T029 complete. **Note**: Execution is strictly sequential; authoring is parallel. (FR-019)
- [X] T023 [P] [US2] Integration test for training and evaluation pipeline in `tests/integration/test_train_evaluate.py`

### Implementation for User Story 2

- [X] T024 [US2] Implement `code/feature_assembly.py` to encode SMILES using frozen `seyonec/ChemBERTa-zinc-base-v1` (CPU) and **assemble the base feature matrix**. **Inputs**: `data/dataset.csv`. **Features**: `smiles_transformer_embedding` + `radius_of_gyration`, `asphericity`, `principal_moments` + confounders (`lattice_system`, `temperature_K`, `has_solvent`). **Logic**: Use **mean pooling over token embeddings** to produce a fixed-length vector from the variable-length SMILES input. **Critical Dependency**: Use ONLY the 3D descriptors produced by T018 (CIF coordinates). **Read `data/dataset.csv` to access all features including confounders**. **Output**: `data/features_matrix.npy` (base) and `data/targets.npy` (where targets are CAPE values). **Verification**: Verify `data/features_matrix.npy` and `data/targets.npy` exist, shapes are (N, D) and (N,), and values are finite. (FR-004, FR-013).
- [X] T025 [US2] Implement `code/train.py` to train a **multi-layer perceptron** (Input -> Hidden -> Hidden -> Output) to predict **CAPE** (Composition-Adjusted Packing Efficiency). **Architecture**: Two hidden layers with **64 and 32 units**, ReLU activation, Dropout 0.1. **Constraint**: Total trainable parameters must be ≤ 100k as per FR-005. **Optimizer**: Adam (lr=1e-3), Batch Size 32. **Inputs**: `data/features_matrix.npy`, `data/targets.npy` (CAPE). **Outputs**: `models/mlp.pt`.
 **Note**: This task targets CAPE as defined in spec FR-011. (FR-005)
- [X] T026 [US2] Implement `code/evaluate.py` to compute MAE, Pearson r, Spearman ρ on validation set. (FR-006, FR-015)
- [X] T027 [US2] Implement `code/evaluate.py` to run a **fixed two-sided permutation test** with **10000** shuffles (FR-006, FR-016). **Logic**: Shuffle labels 10000 times, compute correlation for each, calculate the two-sided p-value as the fraction of shuffled correlations with absolute value ≥ observed absolute correlation. **Output**: Final p-value and total shuffle count in `results/validation_report.json`. (FR-016, SC-005)
- [X] T028 [US2] Implement `code/evaluate.py` to perform VIF diagnostics on **ALL predictor variables** (fingerprint dimensions, 3D descriptors, confounders) as mandated by FR-009. **Use `statsmodels.stats.outliers_influence.variance_inflation_factor` on the full feature matrix. Do NOT omit any raw dimensions.** **Additionally**: Perform **partial-correlation analysis** between predicted CAPE and observed CAPE while controlling for **atom-type composition features**. **Implementation**: Generate these features by **one-hot encoding the elemental counts** (C, N, O, S, P, Halogens) derived from the SMILES string. Report the adjusted correlation coefficient. (FR-009, FR-014)
- [X] T029 [US2] Implement `code/evaluate.py` to compute **all evaluation metrics** and write a single `results/validation_report.json`. **Primary Metrics**: `pearson_r`, `spearman_rho`, `mae`. **Diagnostics**: `shapiro_wilk_p` (Perform Shapiro-Wilk test on CAPE residuals), `partial_corr_r`, `partial_corr_p` (partial correlation controlling for atom-type composition as per FR-014), `vif_flags`, `permutation_p_value` (computed with **10000** shuffles). **Bonferroni Correction**: Calculate `bonferroni_corrected_p` for the **threshold sensitivity analysis** (3 tests: 0.5, 0.6, 0.7) as `min(p_value_from_T033 * 3, 1.0)`. **Output**: Complete JSON object with all keys listed above, ensuring schema compliance with `contracts/validation_report.schema.yaml`. **Note**: This task applies Bonferroni correction to the sensitivity sweep p-values (from T033) to satisfy SC-002 and FR-008. (FR-006, FR-014, FR-015, FR-009, FR-016, SC-002)
- [X] T030 [US2] Implement `code/generate_report.py` to produce `results/report.html` validated against schema (FR-010, FR-019)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Assess robustness to threshold choices (Priority: P3)

**Goal**: Verify that predictive conclusions are not driven by arbitrary packing efficiency cutoffs.

**Independent Test**: Executing the sensitivity script must sweep thresholds across the specific set {0.5, 0.6, 0.7 } and output a table of r, MAE, and p-values with Bonferroni correction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T035 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_schema.py`
- [X] T032 [P] [US3] Integration test for threshold sweep in `tests/integration/test_sensitivity.py`

### Implementation for User Story 3

- [X] T033 [US3] Implement `code/sensitivity.py` to perform a comprehensive sensitivity analysis. **Logic**: 1) Sweep high-packing threshold over a set of representative values (FR-007). 2) Compute r, ρ, MAE, and p-values for each threshold. 3) Apply Bonferroni correction: **multiply raw p-value by the number of tests (3) and cap at 1.0** (FR-008). 4) Verify variation in r is ≤ ±0.05 (SC-004). **Input**: Model predictions from T025. **Output**: `results/sensitivity_sweep.csv` containing columns: `threshold`, `r`, `rho`, `mae`, `p_value`, `bonferroni_corrected_p`. **Verification**: Assert that `max(r) - min(r) <= 0.05`. Exit with error if not met. (FR-007, FR-008, SC-004)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns (Original)

**Purpose**: Improvements that affect multiple user stories

- [X] T051 [P] Run full end-to-end pipeline on CI and verify runtime ≤ 6 hours (SC-005). **Logic**: The pipeline must complete within 6 hours using **10000** permutation shuffles as mandated by FR-016. **Fallback Mechanism**: If the pipeline runtime approaches the 6-hour limit (e.g., at 5.5 hours), the pipeline script **MUST** detect this, reduce the number of permutation shuffles to **1,000** (as permitted by the Spec Assumptions), log the deviation explicitly: "Runtime exceeded threshold with 10000 shuffles. Reduced to 1000 shuffles to meet SC-005.", and continue execution. **DO NOT** abort the pipeline. The task must verify that the final report includes the adjusted shuffle count and the corresponding p-value. (SC-005, FR-016, Spec Assumptions)
- [X] T052c [P] **Compute Feasibility**: Verify that the pipeline (download → report) completes within the time budget on the free-tier runner. Log any steps exceeding hours. (SC-005)
- [X] T053 [P] Performance optimization: parallelize permutation test shuffles if needed (within CPU limits)
- [X] T054 [P] Additional unit tests for feature extraction logic in `tests/unit/`
- [X] T057 [US1, US2, US3] Validate SC-004 for the single model by checking the variation in r across thresholds.

**Checkpoint**: All user stories and polish tasks are complete. Phase 7 (Review Enhancements) has been removed as it constituted scope creep.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Review Enhancements (Phase 7)**: **REMOVED** - These tasks were identified as scope creep and are not part of the approved functional requirements.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable. **Dependency**: T009 (Plan Correction) must be verified before T025.
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
- **Scope Integrity**: All tasks strictly adhere to FR-001 to FR-019. No unapproved features or metrics have been added.
- **Review-Specific Logic**: Phase 7 (Review Enhancements) has been removed as it constituted scope creep. The pipeline now strictly follows the approved functional requirements.