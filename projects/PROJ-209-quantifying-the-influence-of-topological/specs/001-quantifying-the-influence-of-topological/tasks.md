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

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

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
- [X] T009 Configure error handling infrastructure with exponential backoff logic for API retries

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Synthetic Generation (Priority: P1) 🎯 MVP

**Goal**: Download pristine structures from Materials Project, attempt to fetch the 2022 Supplementary Defect Dataset, and generate a physics-based synthetic fallback if the real data is missing/invalid.

**Independent Test**: Can be fully tested by successfully downloading pristine structures, attempting to parse the defect dataset (or generating synthetic data if missing), and verifying that all required fields (defect type, defect density, conductivity, elastic tensor, fracture energy) are present and non-null in the resulting dataset.

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement `code/01_data_acquisition.py`: Step 1.1 - Query **Materials Project REST API** for ≥50 pristine graphene and MoS₂ structures; cache locally under `data/raw/pristine_structures.csv`; **Initialize** `data/state/data_source.json` with `{"status": "real", "source": "materials_project"}`.
- [ ] T011 [S] [US1] Implement `code/01_data_acquisition.py`: Step 1.2 - Attempt to download the **2022 Supplementary Defect Dataset** to `data/raw/defect_dataset_2022.csv`; verify columns (defect type, density, conductivity, elastic tensor, fracture energy) exist and row count > 0. **Dependency: T010**. **Constraint**: If the URL is unreachable or data is invalid, return a status code `MISSING` to trigger the fallback logic in T012c; do NOT raise an error that halts the workflow. <!-- FAILED: unspecified -->
- [ ] T012a [S] [US1] Implement `src/generators/mock_dftb_plus.py`: Mock DFTB+ Computation Logic. **Dependency: T011**. Logic: Accept a list of defect IDs with missing fracture energy. Simulate a computation with a hard timeout of 300 seconds; if successful, return pre-computed physically constrained values using a deterministic formula based on defect density and a fixed seed; if timeout occurs, **log the timeout event and return a status code `TIMEOUT`** (do not raise exception). **Output**: `data/processed/mock_dftb_results.csv` (schema: defect_id, computed_value, status) AND `data/state/mock_dftb_exclusions.json` (schema: {excluded_ids: [], count: N}). **Constraint**: Entries with `TIMEOUT` status MUST be excluded from the final dataset and logged in `mock_dftb_exclusions.json`.
- [ ] T012c [S] [US1] Implement `code/01_data_acquisition.py`: Step 1.2 Fallback Orchestrator. **Dependency: T011, T012a**. Logic: Read T011 status. If `MISSING`: Invoke T012a for missing values, then invoke T013 to generate synthetic data. Write `data/state/generation_status.json` with `{"status": "generated", "source": "synthetic"}`. If `FOUND`: Write `data/state/generation_status.json` with `{"status": "skip", "source": "real"}`. **Output**: `data/state/generation_status.json`.
- [ ] T012b [S] [US1] Implement `code/01_data_acquisition.py`: Step 1.2 Fallback Verification. **Dependency: T012c**. Verify that the number of log entries matching `[MISSING: timeout]` matches the number of entries excluded from the dataset (count in `mock_dftb_exclusions.json`). **Output**: `data/state/fallback_verification.json` with `{"status": "PASS" | "FAIL", "exclusion_count": N}`. **Constraint**: Exit code 0 on PASS, 1 on FAIL.
- [ ] T013 [S] [US1] Implement `code/01_data_acquisition.py`: Step 1.3 - Synthetic Data Generation (Conditional). **Dependency: T012c**. **Condition**: Only execute if `data/state/generation_status.json` indicates `source: synthetic`. Generate `data/raw/synthetic_train.csv` (N=1000+) and `data/raw/synthetic_holdout.csv` (N=200) using seed=42 and the Physics-Informed Parametric Surrogate. **Output**: `data/raw/synthetic_train.csv`, `data/raw/synthetic_holdout.csv`.
- [~] T014 [S] [US1] Implement `code/01_data_acquisition.py`: Step 1.3 - Hold-Out Generation (Conditional). **Dependency: T013**. **Condition**: Only execute if T013 generated synthetic data. Ensure `synthetic_holdout.csv` is generated with a distinct physics engine configuration (if applicable) or a distinct random seed split. **Output**: `data/raw/synthetic_holdout.csv`.
- [X] T015 [US1] Implement `code/01_data_acquisition.py`: Step 1.4 - Add exponential backoff (a limited number of retries) for API calls; on failure load cached pristine structures or abort with `[ERROR: API access unavailable and no cache present]`
- [X] T016a [S] [US1] Implement `code/01_data_acquisition.py`: Step 2 - Data Integrity & Hygiene: Verify checksums, **verify all required fields**, flag missing values. **Dependency: T010, T011**. Filter entries with defect density ≤0 or NaN; log count of excluded entries to `data/state/exclusion_log.json` (schema: {filtered_count: N, reason: "density_leq_0_or_nan"}). **Output**: `data/state/exclusion_log.json`.
- [X] T016b [S] [US1] Implement `code/01_data_acquisition.py`: Step 2 - Missing Value Handling: **If `data_source` is synthetic**, handle missing fracture energy by invoking T012a logic (if in fallback path) and logging; **if `data_source` is real**, flag missing entries for exclusion; **Dependency: T016a**.
- [X] T017 [US1] Implement `scripts/update_state_hashes.py` integration to record checksums of raw files and synthetic generator version (git hash) in `state/projects/PROJ-209-...yaml`; also record `data_source` flag.

**Sequential Execution Note**: T010 runs first to initialize the state. T011 runs next. If T011 returns `MISSING`, T012c is triggered. T012c orchestrates T012a (for missing values) and T013 (for synthetic generation). T012b verifies the fallback. T016a and T016b handle integrity checks.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (real or synthetic data ready)

---

## Phase 4: User Story 2 - Statistical Modeling and Permutation Inference (Priority: P2)

**Goal**: Train Random Forest regressors for conductivity, Young's modulus, fracture strength; perform 5-fold CV; generate p-values via permutation testing; apply Benjamini-Hochberg FDR control.

**Independent Test**: Can be fully tested by training the random forest models on a random split (80/20, seed=42), evaluating on the test split, and reporting R² and MAPE for all three target properties, including a comparison against a null model (mean prediction).

### Implementation for User Story 2

- [~] T018 [S] [US2] Implement `code/02_data_processing.py`: **Dependency: T010, T013**. Extract scalar reference values (σ₀, E₀, σ_f₀) from `data/raw/pristine_structures.csv` (T010); Normalize targets (Δσ/σ₀, ΔE/E₀, Δσ_f/σ_f₀); if pristine reference values are missing for an entry, **exclude it from normalization and log it** per FR-003; one-hot encode `defect_type`; retain geometric descriptors; save `data/processed/features.csv` and `targets.csv`. <!-- FAILED: unspecified -->
- [X] T019 [P] [US2] Implement `code/02_data_processing.py`: Update state file with SHA-256 checksums of processed features/targets
- [~] T020a [S] [US2] Implement `code/03_modeling.py`: Step 4.1 - **Preliminary Model Training**. Train a preliminary Random Forest on the training split (seed=42) to derive initial feature importances. **Output**: `data/processed/preliminary_importance.json`. **Dependency: T018**.
- [~] T020 [S] [US2] Implement `code/03_modeling.py`: Step 4 - **Collinearity Handling**. **Dependency: T020a**. Compute VIF for all predictors. **While VIF > 5 AND iteration < 10**: Exclude the lower-importance feature (based on `preliminary_importance.json` or current model), re-train model, re-calculate VIF. Log exclusion in `data/processed/feature_selection_log.json` (include iteration count and final VIF). **Output**: `data/processed/final_features.csv` and `data/processed/feature_selection_log.json`. **Constraint**: Max 10 iterations; if VIF > 5 after 10 iterations, flag as `VIF_FAILURE` and log. **Note**: Exclusion/re-training is the ONLY path; do not apply Ridge Regression or other alternatives.
- [X] T021 [US2] Implement `code/03_modeling.py`: Step 5 - Model Training: Train 3 Random Forest regressors (conductivity, Young's modulus, fracture strength) with **A standard train-test split (seed=42)**
- [X] T022 [US2] Implement `code/03_modeling.py`: Step 5 - Cross-Validation: Perform k-fold cross-validation (k=5); compute mean R², MAPE, and **standard deviation of R² (`cv_std`)**; **If `cv_std` > 0.1, flag as HIGH_VARIANCE and trigger T027a (Sensitivity Analysis)**; **report R² and MAPE** for all properties.
- [X] T023 [US2] Implement `code/03_modeling.py`: Step 5 - Baseline: Train null model (predict mean) and compare R² improvement
- [~] T024 [S] [US2] Implement `code/04_inference.py`: **Hold-Out Evaluation**. **Dependency: T014 (if synthetic) OR T011 (if real)**. Evaluate final models on `data/raw/synthetic_holdout.csv` (if synthetic) or `data/raw/real_holdout.csv` (if real). **Output**: `data/processed/holdout_metrics.json` with `{"source_type": "synthetic|real", "R2":..., "MAPE":..., "label": "Method Validation|External Validation"}`. **Constraint**: Must run on the distinct physics engine split or distinct real data split.
- [X] T025 [S] [US2] Implement `code/04_inference.py`: Permutation Importance & FDR: **Generate p-values via a sufficient number of permutations** for each feature; **rank defect descriptor influence**; **Apply Benjamini-Hochberg FDR control at q ≤ 0.05** to p-values across the three target-specific tests. **Dependency: T021**.
- [ ] T026 [S] [US2] Implement `code/04_inference.py`: Sensitivity Analysis: **Sweep decision cutoffs over {low, medium, high} OR defect density deciles** and **report FPR and FNR variation** across the swept set.
- [ ] T027a [S] [US2] Implement `code/04_inference.py`: Confounding Control (FR-013). **Dependency: T018**. Check for presence of 'synthesis_method' or 'grain_size' columns. **If present**: Stratify CV folds by these variables and report metrics per stratum. **If absent**: Include them as covariates in the model. **If neither possible**: Flag inability to control confounding as a critical limitation in `data/processed/feature_selection_log.json`. **Output**: `data/processed/confounding_report.json`.
- [X] T028 [US2] Implement `code/04_inference.py`: Scope Note: If synthetic data used, label p-values as "Internal Consistency" measures only

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (models trained, inference complete)

---

## Phase 5: User Story 3 - Validation, Sensitivity Analysis, and Reproducibility (Priority: P3)

**Goal**: Conduct permutation importance stability analysis, sensitivity analysis on thresholds, and generate the Validation Report. Package workflow in a reproducible Jupyter notebook.

**Independent Test**: Can be fully tested by running the complete notebook end-to-end on a CPU-only runner, verifying that all analyses complete within 6 hours and the sensitivity analysis produces a table showing how False Positive Rate (FPR) and False Negative Rate (FNR) vary across the swept thresholds.

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/05_validation.py`: Permutation Importance Stability: Compute stability metrics for top influential descriptors; report ranked list; **flag collinearity if VIF > 5**
- [ ] T030 [S] [US3] Implement `code/05_validation.py`: External Validation Logic. **Dependency: T010, T012c, T012a**. Read `data/state/data_source.json`. Check for `data/state/mock_dftb_exclusions.json` (from T012a). Search path `data/validation/external/` for specific ID `exp_defect_graphene_mos2_v1`. If external data NOT found, generate `data/validation/Validation_Report.json` with **status: NO_EXTERNAL_DATA**, **method: internal_only**, and include **exclusion_count** from T012a. If found, report validation results.
- [ ] T033 [S] [US2/US3] Implement `code/04_inference.py`: Sensitivity Analysis Report. **Dependency: T022**. **Condition**: Only execute if T022 flagged `HIGH_VARIANCE`. Generate table of FPR/FNR vs. swept thresholds (deciles or {low, medium, high}) and save to `data/validation/sensitivity_table.csv`. **Output**: `data/validation/sensitivity_table.csv`.
- [X] T031 [US3] Implement `notebooks/01_full_workflow.ipynb`: Reproducible Jupyter notebook integrating all steps (Data Acquisition → Processing → Modeling → Inference → Validation)
- [X] T032 [US3] Implement `notebooks/01_full_workflow.ipynb`: Ensure notebook runs within **6-hour runtime limit** on GitHub Actions free-tier (CPU, ≤7 GB RAM)
- [X] T034 [US3] Implement `scripts/run_ci_validation.sh`: CI script to execute the full workflow and validate runtime constraints (≤6h) and memory usage (≤7GB)

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
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tasks for User Story 1 together (data acquisition and generation):
# Note: T012c is Sequential (S) and depends on T011, so it CANNOT be run in parallel with T011.
# Only T010, T015 can be launched in parallel.
Task: "Query Materials Project REST API for ≥50 pristine graphene and MoS₂ structures" (T010)
Task: "Add exponential backoff for API calls" (T015)
# T011 must run after T010.
# T012c must run after T011.
# T012a and T012b are conditional and run only if T012c determines fallback is needed.
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