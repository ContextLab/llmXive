# Tasks: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Input**: Design documents from `/specs/PROJ-511-predicting-molecular-packing-efficiency/`
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

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure: `code/`, `data/`, `data/raw_cif/`, `models/`, `results/`, `contracts/`, `specs/`
- [X] T002 Initialize `requirements.txt` with pinned versions (rdkit, torch-cpu, scikit-learn, pandas, numpy, requests, tqdm, jinja2, statsmodels, scipy, matplotlib, seaborn, pyyaml, jsonschema)
- [ ] T003 Create `.gitignore` excluding `data/raw_cif/`, `*.pt`, `*.csv`, `__pycache__`, `.env`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `contracts/dataset.schema.yaml` defining SMILES, PC, CAPE, 3D descriptors, and confounder fields
- [ ] T005 [P] Create `contracts/model.schema.yaml` and `contracts/validation_report.schema.yaml`
- [X] T006 Create `code/utils.py` with seed fixing, logging setup, and Bondi radii constants (FR-018)
- [ ] T007 [P] Create base data loading utilities for CIF parsing and SMILES generation in `code/`
- [ ] T008 [P] Configure error handling for corrupt CIFs and missing metadata in `code/`
- [ ] T009 [P] Setup environment configuration for COD URL and HuggingFace model path in `code/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Build a reproducible SMILES-packing dataset (Priority: P1) 🎯 MVP

**Goal**: Obtain a clean dataset of ≥500 organic crystal structures with SMILES and packing coefficients.

**Independent Test**: The pipeline can be run on a fresh CI runner and must output `data/dataset.csv` with ≥500 rows, valid SMILES, and numeric packing coefficients.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST (TDD).
> **Dependency Note**: While code can be written in parallel, execution depends on T004 (schema) and T012-T018 (implementation).

- [X] T010 [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py` (Depends on T004; must run after T018 completes)
- [X] T011 [P] [US1] Integration test for download and parse pipeline in `tests/integration/test_download_parse.py` (Depends on T012-T018; fails until implementation)

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download_cif.py` to fetch organic CIFs (≤50 non-H atoms) from COD with logging (FR-001, FR-017)
- [X] T013 [US1] Implement `code/parse_cif.py` to extract/generate SMILES via RDKit, flag source, and record confounders. **Specific Logic**:
 - Extract SMILES from `_chemical_structure_SMILES` if present; else generate from 3D geometry.
 - **Confounders**: Extract `lattice_system` from `_symmetry_space_group_name_H-M`, `temperature_K` from `_exptl_temperature` or `_cell_measurement_reflns_temperature` (or default K), and `has_solvent` by checking `_chemical_formula_sum` for solvent patterns.
 - **Output**: `data/dataset_intermediate.csv` with columns: `cod_id`, `smiles`, `smiles_source`, `unit_cell_volume`, `n_atoms`, `lattice_system`, `temperature_K`, `has_solvent`. (FR-002, FR-013)
- [ ] T015 [US1] Implement `code/compute_RAW_metrics.py` to calculate **Raw Packing Coefficient (PC)** (diagnostic only) and **CAPE** (target) using Bondi radii (FR-003, FR-011, FR-018). **Reads `data/dataset_intermediate.csv` and produces `data/dataset_with_metrics.csv`**. This task must output both metrics clearly to allow downstream filtering.
- [ ] T016 [US1] Implement `code/filter_dataset.py` to filter records with missing SMILES, invalid CAPE, or invalid Raw PC from `data/dataset_with_metrics.csv`, producing `data/dataset_filtered.csv` (FR-003, SC-001). Explicitly ensure CAPE is valid before filtering.
- [ ] T017 [US1] Add logging for download statistics, parsing failures, and filtering counts (FR-001, FR-017). **Specific Logic**: Log the results of T016 filtering (counts of removed records and reasons) to ensure traceability.
- [ ] T018 [US1] Implement `code/add_3d_descriptors.py` to calculate 3D descriptors (radius of gyration, asphericity, moments) from RDKit conformers using **ETKDG parameters, seed=42, max_attempts=50**. **Reads `data/dataset_filtered.csv` and merges 3D descriptors to produce final `data/dataset.csv`**. (FR-012)
- [ ] T019 [US1] Implement `code/validate_dataset.py` to check `data/dataset.csv` against `contracts/dataset.schema.yaml` (SC-001). **Includes cross-referencing COD IDs in the CSV against the original CIF filenames to ensure data integrity per FR-017**. (FR-017)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and evaluate a lightweight predictor (Priority: P2)

**Goal**: Train a multi-layer perceptron on SMILES-transformer features + 3D descriptors + confounders to predict CAPE, with rigorous statistical validation.

**Independent Test**: Running the training script on `dataset.csv` must produce `model.pt` and `results/validation_report.json` with MAE, Pearson r, Spearman ρ, Shapiro-Wilk, and a permutation p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [US2] Contract test for model output schema in `tests/contract/test_model_schema.py` (Depends on T026; must run after implementation)
- [X] T023 [P] [US2] Integration test for training and evaluation pipeline in `tests/integration/test_train_evaluate.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement `code/feature_assembly.py` to encode SMILES using frozen `seyonec/PubChem10M_SMILES_BPE_60k` (CPU) and **assemble the final feature matrix**. **Inputs**: `data/dataset.csv`. **Features**: ONLY `smiles_transformer_embedding` + `radius_of_gyration`, `asphericity`, `principal_moments`. **Exclusion**: DO NOT include H-bond counts, aromatic ring counts, or any physics/dynamic features. **Output**: `data/features_matrix.npy` and `data/targets.npy`. **Note**: Depends on T018 completion. (FR-004, FR-013)
- [ ] T025 [US2] Implement `code/train.py` to train three distinct multi-layer perceptron models (Baseline, Control, Upper Bound) to predict CAPE. **Architecture**: 2-layer MLP (1 hidden layer, 128 units), ReLU activation, Dropout 0.1. **Optimizer**: Adam (lr=1e-3), Batch Size 32. **Inputs**: `data/features_matrix.npy`, `data/targets.npy`. **Outputs**: `models/baseline_checkpoint.pt` (SMILES only), `models/control_3d_checkpoint.pt` (3D only), `models/upper_bound_checkpoint.pt` (SMILES+3D). (FR-005)
- [ ] T026 [US2] Implement `code/evaluate.py` to compute MAE, Pearson r, Spearman ρ, Shapiro-Wilk test (FR-006, FR-015)
- [ ] T027 [US2] Implement `code/evaluate.py` to run a **fixed 10,000-shuffle permutation test** (FR-006, FR-016):
 - **Logic**: Execute [deferred] label shuffles to compute the p-value. No conditional stages or early exits.
 - **Output**: Final p-value and shuffle count ([deferred]) in `results/validation_report.json`. (FR-016)
- [ ] T028 [US2] Implement `code/evaluate.py` to perform VIF diagnostics on **all predictor variables** (fingerprint dimensions, 3D descriptors, and confounders) as mandated by FR-009. **Use `statsmodels.stats.outliers_influence.variance_inflation_factor` on the full feature matrix in batches of 100 features if memory is constrained. Do NOT omit raw dimensions**. (FR-009)
- [ ] T028b [US2] Implement `code/evaluate.py` to perform **Comparative Analysis** of Baseline vs. Control vs. Upper Bound models. **Output**: `results/comparative_analysis.csv` containing MAE, r, and p-values for all three models, and generate delta plots in `results/report.html`. (Plan Phase 1, Step 7)
- [ ] T029 [US2] Implement `code/evaluate.py` to perform partial-correlation analysis controlling for atom-type counts (FR-014) AND calculate **Spearman's rank correlation (rho) between predicted CAPE and observed CAPE** (monotonicity check) AND **Shapiro-Wilk test on CAPE residuals**. **Output**: `residual_spearman_rho` (if applicable), `spearman_rho`, `shapiro_wilk_p` in `results/validation_report.json`. (FR-014, FR-015)
- [ ] T030 [US2] Implement `code/generate_report.py` to produce `results/report.html` validated against schema (FR-010, FR-019)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Assess robustness to threshold choices (Priority: P3)

**Goal**: Verify that predictive conclusions are not driven by arbitrary packing efficiency cutoffs.

**Independent Test**: Executing the sensitivity script must sweep thresholds across a specific set of values and output a table of r, MAE, and p-values with Bonferroni correction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_schema.py`
- [ ] T032 [P] [US3] Integration test for threshold sweep in `tests/integration/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/sensitivity.py` to sweep high-packing threshold over the specific set **{0.5, 0.6, 0.7}** as required by FR-007. **Input**: Model predictions from Baseline, Control, and Upper Bound models. **Output**: `results/sensitivity_sweep.csv` containing columns: `model_type`, `threshold`, `r`, `rho`, `mae`, `p_value`. (FR-007)
- [ ] T034 [US3] Implement `code/sensitivity.py` to compute r, ρ, MAE, and p-values for each threshold (FR-007)
- [ ] T035 [US3] Implement `code/sensitivity.py` to apply Bonferroni correction for three hypothesis tests (FR-008)
- [ ] T036 [US3] Implement `code/sensitivity.py` to compute and report the variation in r across the set {0.5, 0.6, 0.7} and verify it is ≤ ±0.05 (SC-004)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision - Addressing Research Review Concerns (Priority: P2)

**Goal**: Augment the feature set and methodology to address reviewer concerns regarding conformational dynamics, physical constraints, and thermodynamic grounding.

**Independent Test**: The revised pipeline must demonstrate that dynamic descriptors and physical constraints improve model interpretability or robustness, and that the model respects known chemical principles (e.g., H-bonding energy, van der Waals radii).

### Tests for Revision Concerns (OPTIONAL - only if tests requested) ⚠️

- [ ] T037 [P] [US2] Unit test for conformational ensemble generation (T038)
- [ ] T038 [P] [US2] Contract test for physical constraint schema (T039)

### Implementation for Revision Concerns

- [ ] T039 [US2] **Conformational Ensemble Generation**: Implement `code/generate_conformers.py` to generate a conformational ensemble for each molecule in `data/dataset.csv`. **Logic**: Use RDKit `ETKDGv3` to generate 10-20 low-energy conformers per molecule. Calculate **dynamic descriptors** (mean radius of gyration, variance of asphericity, max/min principal moments) across the ensemble. **Output**: Append these dynamic descriptors to `data/dataset.csv` (renamed `data/dataset_enhanced.csv`). Addresses **Eric Kandel** (dynamic behavior) and **Rosalind Franklin** (conformational variability) concerns.
- [ ] T040 [US2] **Physical Feature Engineering**: Implement `code/compute_physical_features.py` to calculate **Hydrogen Bonding Capacity** (count of donors/acceptors using RDKit `CalcNumHBD`/`CalcNumHBA` and estimate energy contribution ~-5 kcal/mol per bond) and **Planarity Index** (deviation of aromatic rings from planarity). **Output**: Append these features to `data/dataset_enhanced.csv`. Addresses **Linus Pauling** (H-bonding, planarity) and **Marie Curie** (physical parameters) concerns.
- [ ] T041 [US2] **Re-assembly of Feature Matrix**: Modify `code/feature_assembly.py` to include the new **dynamic descriptors** (T039) and **physical features** (T040) alongside the original SMILES embeddings and static 3D descriptors. **Output**: `data/features_matrix_enhanced.npy`. Addresses **Eric Kandel** (synaptic modulation analogy) and **Stephen Wolfram** (complex rules from simple interactions) concerns by enriching the input space.
- [ ] T042 [US2] **Re-training with Enhanced Features**: Modify `code/train.py` to train the Baseline, Control, and Upper Bound models using `features_matrix_enhanced.npy`. **Logic**: Ensure the Baseline model still primarily tests SMILES topology, but now with the added context of dynamic/physical features if the "Upper Bound" includes them. Specifically, create a new "Baseline+Physics" model variant to isolate the impact of the new features. Addresses **Linus Pauling** (specificity) and **Marie Curie** (thermodynamic grounding) concerns.
- [ ] T043 [US2] **Re-evaluation and Comparative Analysis**: Modify `code/evaluate.py` to re-run all metrics (MAE, r, ρ, p-values) on the new models. **Output**: Update `results/validation_report.json` and `results/comparative_analysis.csv` to include the new "Baseline+Physics" model. **Analysis**: Explicitly compare the performance of the original Baseline vs. Baseline+Physics to quantify the value of dynamic/physical descriptors. Addresses **Rosalind Franklin** (validation against measured parameters) and **Stephen Wolfram** (simple rules) concerns.
- [ ] T044 [US2] **Thermodynamic Consistency Check**: Implement `code/thermodynamic_check.py` to verify that the model's predictions for CAPE correlate with the calculated H-bonding energy and planarity indices. **Output**: Add a section to `results/report.html` discussing the correlation between these physical parameters and the model's error residuals. Addresses **Marie Curie** (physical conditions) and **Linus Pauling** (modeling physics) concerns.

**Checkpoint**: Revision concerns addressed; model now includes dynamic and physical descriptors.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T051 [P] Run full end-to-end pipeline on CI and verify runtime ≤ 6 hours (SC-005)
- [ ] T052c [P] **Compute Feasibility**: Verify that the pipeline (download -> report) completes within the time budget on the free-tier runner. Log any steps exceeding hour. (SC-005)
- [ ] T053 [P] Performance optimization: parallelize permutation test shuffles if needed (within CPU limits)
- [ ] T054 [P] Additional unit tests for feature extraction logic in `tests/unit/`
- [ ] T054d [P] **Robustness Validation**: Validate SC-004 for Control and Upper Bound models by checking the variation in r across thresholds in `results/sensitivity_sweep.csv`. Flag pass/fail for all three models. (SC-004)
- [ ] T055 [P] **Input Validation**: Sanitize external data inputs in `code/parse_cif.py` and `code/download_cif.py`. **Specific Logic**:
 - For CIF parsing: Use RDKit's `Chem.MolFromXYZBlock` or similar with `sanitize=False` initially to inspect structure.
 - Explicitly call `Chem.SanitizeMol(mol, sanitizeOps=Chem.SanitizeFlags.SANITIZE_ALL ^ Chem.SanitizeFlags.SANITIZE_SETAROMATICITY)` (or appropriate flags) to verify valency and connectivity without auto-correcting anomalies.
 - If `MolSanitizeException` is raised, log the specific error (e.g., "Invalid valence on atom X") and fail the record with a clear error message, **never** falling back to synthetic data or skipping the check.
 - For SMILES strings: Validate canonicalization using `Chem.MolToSmiles(Chem.MolFromSmiles(s))` and ensure round-trip consistency; fail on `MolSanitizeException`. (FR-001, FR-002)
- [ ] T056 Run `quickstart.md` validation to ensure reproducibility
- [ ] T057 [US3] Validate SC-004: Check if variation in r ≤ ±0.05 from T036 results and flag pass/fail in final report

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Revision (Phase 6)**: Depends on US2 completion (T025, T026)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on dataset from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model from US2
- **Revision (Phase 6)**: Depends on US2 completion

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
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Integration test for download and parse pipeline in tests/integration/test_download_parse.py"

# Launch all models for User Story 1 together:
Task: "Implement download_cif.py to fetch organic CIFs"
Task: "Implement parse_cif.py to extract/generate SMILES"
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
- **Critical Constraint**: All tasks must run on CPU-only CI with a limited number of cores and constrained RAM. No GPU, no 8-bit quantization, no large model training.
- **Reviewer Compliance**:
 - **Scope Control**: T013b-d removed. Feature set strictly limited to SMILES + 3D descriptors (FR-004).
 - **Statistical Rigor**: Conditional permutation test implemented in T027 to balance runtime and resolution.
 - **VIF Compliance**: VIF computed on all variables without omission (T028).
 - **Robustness**: Sensitivity sweep covers all three models (T033, T054d).
 - **Data Integrity**: Explicit confounder extraction and COD ID validation (T013, T019).
 - **Revision Compliance**:
 - **Dynamic Descriptors**: T039 addresses **Eric Kandel** (conformational ensemble) and **Rosalind Franklin** (variability).
 - **Physical Features**: T040 addresses **Linus Pauling** (H-bonding, planarity) and **Marie Curie** (thermodynamics).
 - **Enhanced Models**: T041-T043 integrate these features and re-evaluate, addressing **Stephen Wolfram** (simple rules/complexity) and **Eric Kandel** (synaptic modulation analogy).
 - **Thermodynamic Check**: T044 ensures physical grounding as requested by **Marie Curie** and **Linus Pauling**.