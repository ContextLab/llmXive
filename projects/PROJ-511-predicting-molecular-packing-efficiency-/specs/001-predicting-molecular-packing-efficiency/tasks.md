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
- [ ] T002 Initialize `requirements.txt` with pinned versions (rdkit, torch-cpu, scikit-learn, pandas, numpy, requests, tqdm, jinja2, statsmodels, scipy, matplotlib, seaborn, pyyaml, jsonschema)
- [ ] T003 Create `.gitignore` excluding `data/raw_cif/`, `*.pt`, `*.csv`, `__pycache__`, `.env`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `contracts/dataset.schema.yaml` defining SMILES, PC, CAPE, 3D descriptors, H-bond count, aromatic ring count, and confounder fields
- [ ] T005 [P] Create `contracts/model.schema.yaml` and `contracts/validation_report.schema.yaml`
- [X] T006 Create `code/utils.py` with seed fixing, logging setup, and Bondi radii constants (FR-018)
- [ ] T007 [P] Create base data loading utilities for CIF parsing and SMILES generation in `code/`
- [~] T008 [P] Configure error handling for corrupt CIFs and missing metadata in `code/`
- [~] T009 [P] Setup environment configuration for COD URL and HuggingFace model path in `code/`
- [~] T013b [P] [US1] Implement `code/extract_physics_features.py` to calculate H-bond capacity (donor/acceptor counts), aromatic ring fraction, and thermodynamic confounders (temperature, solvent presence) from CIF metadata and 3D geometry. **Reads raw CIFs and produces `data/physics_features.csv`**. (FR-013, FR-002, Pauling/Curie requirements integrated into core flow)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Build a reproducible SMILES-packing dataset (Priority: P1) 🎯 MVP

**Goal**: Obtain a clean dataset of ≥500 organic crystal structures with SMILES and packing coefficients.

**Independent Test**: The pipeline can be run on a fresh CI runner and must output `data/dataset.csv` with ≥500 rows, valid SMILES, and numeric packing coefficients.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST (TDD).
> **Dependency Note**: While code can be written in parallel, execution depends on T004 (schema) and T012-T018 (implementation).

- [X] T010 [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py` (Depends on T004; must run after T018 completes)
- [ ] T011 [P] [US1] Integration test for download and parse pipeline in `tests/integration/test_download_parse.py` (Depends on T012-T018; fails until implementation)

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download_cif.py` to fetch organic CIFs (≤50 non-H atoms) from COD with logging (FR-001, FR-017)
- [X] T013 [US1] Implement `code/parse_cif.py` to extract/generate SMILES via RDKit, flag source, and record confounders (FR-002, FR-013)
- [ ] T015 [US1] Implement `code/compute_raw_metrics.py` to calculate **Raw Packing Coefficient (PC)** (diagnostic only) and **CAPE** (target) using Bondi radii (FR-003, FR-011, FR-018). **Reads `data/dataset_intermediate.csv` and produces `data/dataset_with_metrics.csv`**. This task must output both metrics clearly to allow downstream filtering.
- [ ] T016 [US1] Implement `code/filter_dataset.py` to filter records with missing SMILES, invalid CAPE, or invalid Raw PC from `data/dataset_with_metrics.csv`, producing `data/dataset_filtered.csv` (FR-003, SC-001). Explicitly ensure CAPE is valid before filtering.
- [ ] T017 [US1] Add logging for download statistics, parsing failures, and filtering counts (FR-001, FR-017)
- [ ] T018 [US1] Implement `code/add_3d_descriptors.py` to calculate 3D descriptors (radius of gyration, asphericity, moments) from RDKit conformers using **ETKDG parameters, seed=42, max_attempts=50**. **Reads `data/dataset_filtered.csv` and merges 3D descriptors to produce final `data/dataset.csv`**. (FR-012)
- [ ] T019 [US1] Implement `code/validate_dataset.py` to check `data/dataset.csv` against `contracts/dataset.schema.yaml` (SC-001). **Includes cross-referencing unit-cell dimensions and symmetry from CIFs against calculated CAPE to ensure data is anchored in measured diffraction parameters** (FR-017, Franklin requirement integrated into validation).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and evaluate a lightweight predictor (Priority: P2)

**Goal**: Train a multi-layer perceptron on SMILES-transformer features + D descriptors + confounders to predict CAPE, with rigorous statistical validation.

**Independent Test**: Running the training script on `dataset.csv` must produce `model.pt` and `results/validation_report.json` with MAE, Pearson r, Spearman ρ, Shapiro-Wilk, and a permutation p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [US2] Contract test for model output schema in `tests/contract/test_model_schema.py` (Depends on T026; must run after implementation)
- [ ] T023 [P] [US2] Integration test for training and evaluation pipeline in `tests/integration/test_train_evaluate.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement `code/feature_assembly.py` to encode SMILES using frozen `seyonec/PubChem10M_SMILES_BPE_60k` (CPU) and **assemble the final feature matrix** by loading `data/dataset.csv` (from T018/T019) and merging the embedding with 3D descriptors, H-bond count, aromatic ring count, and confounders (FR-004, FR-013). **Note**: Only spec-mandated features are used; no external physics features are added. **Depends on T013b for physics features**.
- [ ] T025 [US2] Implement `code/train_mlp.py` to train a 2-layer MLP (≤100k params) on 80/20 split (FR-005)
- [ ] T026 [US2] Implement `code/evaluate.py` to compute MAE, Pearson r, Spearman ρ, Shapiro-Wilk test (FR-006, FR-015)
- [ ] T027 [US2] Implement `code/evaluate.py` to run a **permutation test with exactly 10,000 shuffles** to achieve 0.0001 resolution (FR-006, FR-016, Constitution VII). **Mandate [deferred] shuffles. If runtime exceeds the time budget, the pipeline MUST fail with an explicit error message and deviation log., rather than reducing the shuffle count, to preserve statistical rigor per FR-016**. Report the final p-value and the number of shuffles used, ensuring the quantity is sufficient for robust permutation testing.
- [ ] T028 [US2] Implement `code/evaluate.py` to perform VIF diagnostics on **all predictor variables** (fingerprint dimensions, 3D descriptors, and confounders) as mandated by FR-009. **Use `statsmodels.stats.outliers_influence.variance_inflation_factor` on the full feature matrix. Do NOT omit raw dimensions or default to PCA reduction. If dimensionality is high, implement batching to handle the calculation, but NEVER omit raw dimensions or default to PCA reduction without explicit justification**. (FR-009)
- [ ] T029 [US2] Implement `code/evaluate.py` to perform partial-correlation analysis controlling for atom-type counts (FR-014)
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

- [ ] T033 [US3] Implement `code/sensitivity.py` to sweep high-packing threshold over the specific set **{0.5, 0.6, 0.7}** as required by FR-007 (FR-007)
- [ ] T034 [US3] Implement `code/sensitivity.py` to compute r, ρ, MAE, and p-values for each threshold (FR-007)
- [ ] T035 [US3] Implement `code/sensitivity.py` to apply Bonferroni correction for three hypothesis tests (FR-008)
- [ ] T036 [US3] Implement `code/sensitivity.py` to compute and report the variation in r across the set {0.5, 0.6, 0.7} and verify it is ≤ ±0.05 (SC-004)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T051 [P] Run full end-to-end pipeline on CI and verify runtime ≤ 6 hours [UNRESOLVED-CLAIM: c_a2899dbc — status=not_enough_info] (SC-005)
- [ ] T052a [P] Run `black --check` on `code/` and fix formatting violations
- [ ] T052b [P] Run `flake8` on `code/` and fix linting errors
- [ ] T052c [P] Run automated linting: `pylint --max-line-length=100 --max-branches=10 --max-returns=10 code/` and `radon cc -m code/` ensuring max cyclomatic complexity is ≤ 10. Log results in `code/REFACTORING_LOG.txt`.
- [ ] T052d [P] Refactor code for readability based on T052c logs: Ensure all functions have < 50 lines [UNRESOLVED-CLAIM: c_bb528aad — status=not_enough_info], docstrings present, and variable names are descriptive. Pass criterion: T052c logs show max complexity ≤ 10 and function length < 50 lines.
- [ ] T053 [P] Performance optimization: parallelize permutation test shuffles if needed (within CPU limits)
- [ ] T054 [P] Additional unit tests for feature extraction logic in `tests/unit/`
- [ ] T055 Security hardening: sanitize external data inputs
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
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on dataset from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model from US2

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
 - **Physics Integration**: H-bond capacity, aromaticity, and thermodynamic confounders (T013b) are now core features calculated in Phase 2, not post-hoc revisions.
 - **Data Integrity**: No synthetic data or fabricated metrics are used. All features are derived from real COD data or standard physical constants (Bondi radii).
 - **Statistical Rigor**: Permutation test uses 10,000 shuffles (T027) with a strict failure mode if timeout occurs.
 - **VIF Compliance**: VIF computed on all variables without omission (T028).