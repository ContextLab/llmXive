# Tasks: Quantifying the Influence of Topological Defects on 2D Material Properties

**Input**: Design documents from `/specs/001-quantify-defect-influence/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must run after specific dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

 Tasks MUST be organized by user story so each story can be independently completable and testable.

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize project directory structure: Create `src/`, `data/raw/`, `data/processed/`, `scripts/`, `tests/`, `notebooks/`, `data/validation/`, and `code/` directories

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `scripts/update_state_hashes.py` to record SHA-256 checksums for raw/processed data and feature matrices
- [X] T005 [P] Implement `src/config.py` for environment configuration (API keys, paths, seeds)
- [X] T006 [P] Create `src/logging_config.py` for structured logging of workflow steps and errors
- [X] T007 Create base data models: `src/models/defect_entry.py` (DefectEntry entity) and `src/models/material_property.py` (MaterialProperty entity)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Synthetic Generation (Priority: P1) 🎯 MVP

**Goal**: Download pristine structures from Materials Project, attempt to fetch the 2022 Supplementary Defect Dataset, and generate a physics-based synthetic fallback if the real data is missing/invalid.

**Independent Test**: Can be fully tested by successfully downloading pristine structures, attempting to parse the defect dataset (or generating synthetic data if missing), and verifying that all required fields (defect type, defect density, conductivity, elastic tensor, fracture energy) are present and non-null in the resulting dataset.

### Implementation for User Story 1

- [ ] T010 [S] [US1] Implement `code/01_data_acquisition.py`: Step 1 - **Pristine Structure Download**. Query **Materials Project REST API** for ≥50 pristine graphene and MoS₂ structures; cache locally under `data/raw/pristine_structures.csv`. **Logic**: Implement exponential backoff with a configurable retry limit for API calls. **On Failure**: Load cached pristine structures if available; if no cache exists, abort with `[ERROR: API access unavailable and no cache present]`. **Output**: `data/raw/pristine_structures.csv`, `data/state/data_source.json` (initially `{"status": "real", "source": "materials_project"}`).
- [ ] T011 [S] [US1] Implement `code/01_data_acquisition.py`: Step 2 - **Defect Dataset Download & Validation**. Attempt to download the **2022 Supplementary Defect Dataset** to `data/raw/defect_dataset_2022.csv`. **Logic**: Validate file existence and basic schema (presence of required columns: `defect_type`, `defect_density`, `conductivity`, `elastic_tensor`, `fracture_energy`). **Missing Value Logic**: For entries with missing `fracture_energy` or other critical fields, **EXCLUDE** the entry. **DO NOT** use a hardcoded formula or mock simulation to fill missing values. Log excluded entries. **Output**: `data/raw/defect_dataset_2022.csv` (with exclusions), `data/state/source_validation.json` (schema: `{"valid": boolean, "reason": "string", "exclusions": int}`).
- [ ] T011b [S] [US1] Implement `code/01_data_acquisition.py`: Step 2b - **Exclusion Logging**. **Dependency: T011**. Generate `data/state/exclusion_log.json` containing the list of excluded entry IDs and reasons (e.g., `missing_fracture_energy`, `invalid_density`). This artifact is required for FR-002 compliance.
- [ ] T012 [S] [US1] Implement `code/01_data_acquisition.py`: Step 3 - **Source Validity Check & Branching**. **Dependency: T011, T011b**. Read `data/state/source_validation.json`.
 - **If `valid: false`** (Source missing or invalid): Mark source as invalid. Write `data/state/generation_status.json` with `{"status": "generated", "source": "synthetic"}`.
 - **If `valid: true`** (Source exists but may have minor gaps handled in T011): Mark source as valid. Write `{"status": "valid", "source": "real"}`.
 **Output**: `data/state/generation_status.json`. **Note**: This task does NOT generate data; it only sets the state for the runner to trigger T013a/b if needed.
- [ ] T013a [S] [US1] Implement `code/01_data_acquisition.py`: Step 4a - **Synthetic Training Set Generation**. **Dependency: T012**. **Condition**: Read `data/state/generation_status.json`. If `source: synthetic`, generate `data/raw/synthetic_train.csv` (N=1000+) using seed=42. **Surrogate Model**: Analytical signal = Continuum elasticity (`E = E0 * (1 - k*density)`); Noise = Gaussian (`sigma=0.05`) calibrated from DFT dataset. **Output**: `data/raw/synthetic_train.csv`.
- [ ] T013b [S] [US1] Implement `code/01_data_acquisition.py`: Step 4b - **Synthetic Hold-out Set Generation**. **Dependency: T012, T024a**. **Condition**: Read `data/state/generation_status.json`. If `source: synthetic`, generate `data/raw/synthetic_holdout.csv`. **Size Logic**: Calculate hold-out size based on power analysis result from T024a (if available) or use a robust default (N=200) if T024a is not yet run. **Output**: `data/raw/synthetic_holdout.csv`.
- [ ] T016a [S] [US1] Implement `code/01_data_acquisition.py`: Step 5 - **Data Integrity & Hygiene**. **Dependency: T010 (if real) OR T013a (if synthetic), T012**. Verify checksums, **verify all required fields**, flag missing values. Filter entries with defect density ≤0 or NaN; log count of excluded entries to `data/state/exclusion_log.json` (schema: `{filtered_count: N, reason: "density_leq_0_or_nan"}`). **Output**: `data/state/exclusion_log.json`.
- [ ] T016b [S] [US1] Implement `code/01_data_acquisition.py`: Step 6 - **Missing Value Handling (Synthetic)**. **Dependency: T013a**. **Condition**: **Only if `data_source` is synthetic**. Check for missing `fracture_energy` in synthetic data. **Action**: If missing, **EXCLUDE** the entry and log it to `data/state/mock_dftb_exclusions.json`. **DO NOT** re-generate or impute. **Output**: `data/state/mock_dftb_exclusions.json`, `data/state/fallback_verification.json`.
- [X] T017 [US1] Implement `scripts/update_state_hashes.py` integration to record checksums of raw files and synthetic generator version (git hash) in `state/projects/PROJ-209-...yaml`; also record `data_source` flag.

**Sequential Execution Note**: T010 runs first. T011 downloads and handles missing values by exclusion. T012 checks validity and sets state. T013a/b generate synthetic data if needed. T016a and T016b handle integrity and synthetic missing values.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (real or synthetic data ready)

---

## Phase 4: User Story 2 - Statistical Modeling and Permutation Inference (Priority: P2)

**Goal**: Train Random Forest regressors for conductivity, Young's modulus, fracture strength; perform 5-fold CV; generate p-values via permutation testing; apply Benjamini-Hochberg FDR control.

**Independent Test**: Can be fully tested by training the random forest models on a random split (80/20, seed=42), evaluating on the test split, and reporting R² and MAPE for all three target properties, including a comparison against a null model (mean prediction).

### Implementation for User Story 2

- [ ] T018 [S] [US2] Implement `code/02_data_processing.py`: **Dependency: T010, T013a**. Extract scalar reference values (σ₀, E₀, σ_f₀) from `data/raw/pristine_structures.csv` (T010). **Normalization**: Compute relative changes (Δσ/σ₀, ΔE/E₀, Δσ_f/σ_f₀). **Exclusion**: **If pristine reference values are missing for an entry, exclude it from normalization and log it** per FR-003. **Output**: `data/processed/features.csv`, `data/processed/targets.csv`, `data/state/normalization_log.json` (including excluded IDs).
- [X] T019 [P] [US2] Implement `code/02_data_processing.py`: Update state file with SHA-256 checksums of processed features/targets
- [ ] T020 [S] [US2] Implement `code/03_modeling.py`: Step 1 - **Collinearity Check & Feature Selection**. **Dependency: T018**. Load `features.csv`. **Loop**: **While VIF > 5 AND iteration < 10**:
 1. Compute **Permutation Importance** for all features using a preliminary Random Forest (low n_estimators).
 2. Identify feature with the **lowest importance score**.
 3. **Exclude** the feature with the lowest importance score (Tie-breaking: if equal, exclude first encountered).
 4. Exclude feature, re-calculate VIF on remaining features.
 5. Log exclusion in `data/processed/feature_selection_log.json` (schema: `[{iteration: int, removed_feature: str, vif_before: float, vif_after: float, timestamp: str, feature_set_hash: str}]`).
 **Output**: `data/processed/final_features.csv`, `data/processed/feature_selection_log.json`. **Constraint**: If VIF > 5 after 10 iterations, flag as `VIF_FAILURE` and halt.
- [ ] T021 [S] [US2] Implement `code/03_modeling.py`: Step 2 - **Model Training & CV**. **Dependency: T020, T027a**. Read `data/processed/final_features.csv` and `data/processed/confounding_config.json`. Train Random Forest regressors (conductivity, Young's modulus, fracture strength) with **a standard train-test split (seed=42)**. Apply stratification or covariates as configured in `confounding_config.json`. **Output**: Trained models, `data/processed/model_outputs.json` (intermediate).
- [ ] T022 [S] [US2] Implement `code/03_modeling.py`: Step 3 - **Cross-Validation**. **Dependency: T021**. Perform k-fold cross-validation (k=5) on the models trained in T021; compute mean R², MAPE, and **standard deviation of R² (`cv_std`)**. **If `cv_std` > 0.1, flag as HIGH_VARIANCE**. **Report R² and MAPE** for all properties.
- [ ] T023 [S] [US2] Implement `code/03_modeling.py`: Step 4 - **Baseline**. Train null model (predict mean) and compare R² improvement.
- [ ] T024a [S] [US2] Implement `code/04_inference.py`: Step 1a - **Power Analysis for Permutations**. **Dependency: T021**. Perform a power analysis to determine the **sufficient number of permutations** (N) required to achieve statistical robustness (e.g., power > 0.8) for the expected effect size. **Output**: `data/state/permutation_count.json` with `{"n_permutations": int}`.
- [ ] T024b [S] [US2] Implement `code/04_inference.py`: Step 1b - **Permutation Testing**. **Dependency: T024a**. **Generate p-values via N permutations** (from T024a) for **every feature for every target property**; **rank defect descriptor influence**.
- [ ] T025 [S] [US2] Implement `code/04_inference.py`: Step 2 - **FDR Correction**. **Dependency: T024b**. **Apply Benjamini-Hochberg FDR control at q ≤ 0.05** to p-values across **all hypothesis tests** (every feature for every target property). Output `data/processed/model_outputs.json` with `fdr_adjusted_p` and `is_significant`.
- [ ] T026-real [S] [US2] Implement `code/04_inference.py`: Step 3a - **Hold-Out Evaluation (Real)**. **Dependency: T011**. Evaluate final models on `data/raw/real_holdout.csv` (if real data was used). **Output**: `data/processed/holdout_metrics.json` with `{"source_type": "real", "R2":..., "MAPE":..., "label": "External Validation"}`.
- [ ] T026-synthetic [S] [US2] Implement `code/04_inference.py`: Step 3b - **Hold-Out Evaluation (Synthetic)**. **Dependency: T013b**. Evaluate final models on `data/raw/synthetic_holdout.csv` (if synthetic data was used). **Output**: `data/processed/holdout_metrics.json` with `{"source_type": "synthetic", "R2":..., "MAPE":..., "label": "Method Validation"}`.
- [ ] T027a [S] [US2] Implement `code/04_inference.py`: Step 4 - **Confounding Control Configuration**. **Dependency: T018**. Check for presence of 'synthesis_method' or 'grain_size' columns.
 - **If Present**: Configure stratified CV folds by these variables OR include them as **linear terms (covariates)** in the model.
 - **If Absent**: Check for *any* other available confounders. If found, configure them to be included as **linear terms** (covariates) in the model. **Verification**: Explicitly verify that the 'covariates' branch is sufficient to control confounding (or document the limitation).
 - **If No Confounders**: Log a limitation in `data/processed/confounding_report.json` but proceed. **Verification**: Explicitly verify that the 'covariates' branch is sufficient to control confounding (or document the limitation).
 **Output**: `data/processed/confounding_config.json` (JSON file specifying stratification strategy or covariate list) and `data/processed/confounding_report.json`. **Note**: T021 must read `confounding_config.json` to apply these settings.
- [ ] T027b [S] [US2] Implement `code/04_inference.py`: Step 5 - **Sensitivity Analysis**. **Dependency: T021**. **Sweep decision cutoffs over {low, medium, high} OR defect density deciles** and **report FPR and FNR variation** across the swept set. **Output**: `data/validation/sensitivity_table.csv`.
- [ ] T028 [S] [US2] Implement `code/04_inference.py`: Step 6 - **Scope Note**. If synthetic data used, label p-values as "Internal Consistency" measures only in all reports.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (models trained, inference complete)

---

## Phase 5: User Story 3 - Validation, Sensitivity Analysis, and Reproducibility (Priority: P3)

**Goal**: Conduct permutation importance stability analysis, sensitivity analysis on thresholds, and generate the Validation Report. Package workflow in a reproducible Jupyter notebook.

**Independent Test**: Can be fully tested by running the complete notebook end-to-end on a CPU-only runner, verifying that all analyses complete within 6 hours and the sensitivity analysis produces a table showing how False Positive Rate (FPR) and False Negative Rate (FNR) vary across the swept thresholds.

### Implementation for User Story 3

- [ ] T029 [S] [US3] Implement `code/05_validation.py`: Step 1 - **Permutation Importance Stability**. Compute stability metrics for top influential descriptors; report ranked list; **flag collinearity if VIF > 5**.
- [ ] T030 [S] [US3] Implement `code/05_validation.py`: Step 2 - **External Validation Logic**. **Dependency: T010, T011, T018**. Read `data/state/data_source.json`. **Scan** `data/validation/external/` for **any** valid dataset (CSV/JSON) matching the criteria (experimental or distinct DFT).
 - **If External Data Found**: Run validation and report results.
 - **If No External Data Found**: Generate `data/validation/Validation_Report.json` with **status: NO_EXTERNAL_DATA**, **method: internal_only**.
 - **Exclusion Count**: **If data_source is synthetic, set exclusion_count to 0**. **Else**, read `exclusion_count` from `mock_dftb_exclusions.json` (if exists, else 0).
 **Output**: `data/validation/Validation_Report.json`.
- [X] T031 [US3] Implement `notebooks/01_full_workflow.ipynb`: **Reproducible Jupyter notebook** integrating all steps (Data Acquisition → Processing → Modeling → Inference → Validation).
- [X] T032 [US3] Implement `notebooks/01_full_workflow.ipynb`: Ensure notebook runs within **6-hour runtime limit** on GitHub Actions free-tier (CPU, ≤7 GB RAM).
- [X] T034 [US3] Implement `scripts/run_ci_validation.sh`: CI script to execute the full workflow and validate runtime constraints (≤6h) and memory usage (≤7GB).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035a [P] Update `docs/README.md` with project overview and setup instructions
- [X] T035b [P] Update `docs/API.md` with synthetic generator API documentation
- [X] T036 [P] Refactor `code/01_data_acquisition.py` to remove hardcoded paths and use `config.py`
- [X] T037 [P] Add unit test `tests/unit/test_synthetic_generator.py` for synthetic data generation logic
- [X] T038 [P] Add unit test `tests/unit/test_data_processing.py` for normalization logic
- [X] T039 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on models from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tasks for User Story 1 together (data acquisition and generation):
# Note: T011 is Sequential (S) and depends on T010.
# T012, T013, T016 are conditional but listed sequentially; the runner script checks state to decide execution.
Task: "Query Materials Project REST API for ≥50 pristine graphene and MoS₂ structures " (T010)
# T011 must run after T010.
# T012 runs after T011 and determines the next step.
# T013 and T016 run after T012, conditional on T012's output.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify data real or synthetic with correct fields)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Models trained, inference done)
4. Add User Story 3 → Test independently → Deploy/Demo (Validation complete)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Validation)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = Sequential (must run after specific dependencies)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: All tasks must run on CPU-only CI (limited cores, constrained RAM, 6h limit). No GPU, no 8-bit quantization, no large LLMs.
- **Critical**: Real data preferred; synthetic data is a fallback ONLY if primary source is missing. If synthetic, claims are restricted to "Method Validation".