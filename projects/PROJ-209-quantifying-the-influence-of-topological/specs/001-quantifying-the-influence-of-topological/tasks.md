# Tasks: Quantifying the Influence of Topological Defects on 2D Material Properties

**Input**: Design documents from `/specs/001-quantify-defect-influence/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
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

- [ ] T010 [P] [US1] Implement `code/01_data_acquisition.py`: Step 1.1 - Query **Materials Project REST API** for ≥50 pristine graphene and MoS₂ structures; cache locally under `data/raw/pristine_structures.csv`
- [ ] T011 [P] [US1] Implement `code/01_data_acquisition.py`: Step 1.2 - Attempt to download the **2022 Supplementary Defect Dataset** to `data/raw/defect_dataset_2022.csv`; verify columns (defect type, density, conductivity, elastic tensor, fracture energy) exist and row count > 0
- [ ] T013 [P] [US1] Implement `src/generators/synthetic_data_generator.py`: Primary Mode - Use Analytical Continuum Mechanics (Griffith criterion, Rule of Mixtures, Matthiessen's rule) to generate properties; output to `data/raw/synthetic_train.csv`; ensure seed=42 and versioned via git hash.
- [ ] T014 [P] [US1] Implement `src/generators/synthetic_data_generator.py`: Hold-Out Mode - Use a Gaussian GP Surrogate (trained on distinct public DFT data or distinct analytical params) to emulate a "Distinct Physics Engine" for the hold-out set; output to `data/raw/synthetic_holdout.csv`; **Note**: This mode triggers "Method Validation" scope shift per Plan's Critical Scope Limitation.
- [ ] T012 [US1] Implement `code/01_data_acquisition.py`: Step 1.2 Fallback - Invoke `src/generators/synthetic_data_generator.py` (seed=42, versioned via git hash) if primary dataset is missing/invalid; generate ≥100 entries with defect density ∈ [0.001, 0.1] and physical bounds; save to `data/raw/synthetic_defect_fallback.csv`; set internal flag `data_source = 'synthetic'` if fallback is used.
- [ ] T015 [US1] Implement `code/01_data_acquisition.py`: Step 1.3 - Add exponential backoff (max a limited number of retries) for API calls; on failure load cached pristine structures or abort with `[ERROR: API access unavailable and no cache present]`
- [X] T016 [US1] Implement `code/01_data_acquisition.py`: Step 2 - Data Integrity & Hygiene: Verify checksums, **verify all required fields**, flag missing values, **exclude entries** if mock DFTB+ fallback fails (≤300s), filter entries with defect density ≤0 or NaN; log count of excluded entries.
- [X] T017 [US1] Implement `scripts/update_state_hashes.py` integration to record checksums of raw files and synthetic generator version (git hash) in `state/projects/PROJ-209-...yaml`; also record `data_source` flag.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (real or synthetic data ready)

---

## Phase 4: User Story 2 - Statistical Modeling and Permutation Inference (Priority: P2)

**Goal**: Train Random Forest regressors for conductivity, Young's modulus, and fracture strength; perform 5-fold CV; generate p-values via permutation testing; apply Benjamini-Hochberg FDR control.

**Independent Test**: Can be fully tested by training the random forest models on a random split (80/20, seed=42), evaluating on the test split, and reporting R² and MAPE for all three target properties, including a comparison against a null model (mean prediction).

### Implementation for User Story 2

- [~] T018 [P] [US2] Implement `code/02_data_processing.py`: **Extract scalar reference values (σ₀, E₀, σ_f₀) from `data/raw/pristine_structures.csv` (T010)**; Normalize targets (Δσ/σ₀, ΔE/E₀, Δσ_f/σ_f₀); if pristine reference values are missing for an entry, **exclude it from normalization and log it** per FR-003; one-hot encode `defect_type`; retain geometric descriptors; save `data/processed/features.csv` and `targets.csv`.
- [X] T019 [P] [US2] Implement `code/02_data_processing.py`: Update state file with SHA-256 checksums of processed features/targets
- [~] T020 [US2] Implement `code/03_modeling.py`: Step 4 - **Collinearity Handling**: Compute VIF for all predictors. **Primary Strategy**: Apply **Ridge Regression** (L2 regularization) to handle collinearity in geometric descriptors. **Fallback**: ONLY if Ridge fails OR if a feature is physically redundant (VIF > 5 AND low importance determined by `feature_importances_` from an initial RF), exclude the lower-importance feature and re-train. Save `data/processed/feature_selection_log.json` listing excluded features and method used.
- [X] T021 [US2] Implement `code/03_modeling.py`: Step 5 - Model Training: Train 3 Random Forest regressors (conductivity, Young's modulus, fracture strength) with **80/20 split (seed=42)**
- [X] T022 [US2] Implement `code/03_modeling.py`: Step 5 - Cross-Validation: Perform k-fold cross-validation (k=5); compute mean R², MAPE, and **standard deviation of R² (`cv_std`)**; if `cv_std` > 0.1, **flag as high variance and trigger sensitivity analysis**; **report R² and MAPE** for all properties.
- [X] T023 [US2] Implement `code/03_modeling.py`: Step 5 - Baseline: Train null model (predict mean) and compare R² improvement
- [~] T024 [US2] Implement `code/03_modeling.py`: Step 5 - Hold-Out: Evaluate on distinct hold-out set (**distinct random seed for real data; `data/raw/synthetic_holdout.csv` generated by T014 (Gaussian GP Surrogate) for synthetic data**) as per FR-012.
- [X] T025 [P] [US2] Implement `code/04_inference.py`: Permutation Importance: Compute p-values via **a sufficient number of permutations** for each feature; **rank defect descriptor influence**
- [X] T026 [US2] Implement `code/04_inference.py`: FDR Control: Apply **Benjamini-Hochberg FDR control at q ≤ 0.05** to p-values across the three target-specific tests
- [X] T027 [US2] Implement `code/04_inference.py`: Sensitivity Analysis: **Sweep decision cutoffs** (e.g., defect density deciles) and **report FPR and FNR variation**
- [X] T028 [US2] Implement `code/04_inference.py`: Confounding Control (FR-013): If `synthesis_method` or `grain_size` exist, **stratify CV folds**; otherwise, **include them as covariates in the model**; if neither is possible, **flag inability to control confounding as a critical limitation** (do not simply log omission).
- [X] T029 [US2] Implement `code/04_inference.py`: Scope Note: If synthetic data used, label p-values as "Internal Consistency" measures only

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (models trained, inference complete)

---

## Phase 5: User Story 3 - Validation, Sensitivity Analysis, and Reproducibility (Priority: P3)

**Goal**: Conduct permutation importance stability analysis, sensitivity analysis on thresholds, and generate the Validation Report. Package workflow in a reproducible Jupyter notebook.

**Independent Test**: Can be fully tested by running the complete notebook end-to-end on a CPU-only runner, verifying that all analyses complete within 6 hours and the sensitivity analysis produces a table showing how False Positive Rate (FPR) and False Negative Rate (FNR) vary across the swept thresholds.

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement `code/05_validation.py`: Permutation Importance Stability: Compute stability metrics for top influential descriptors; report ranked list; **flag collinearity if VIF > 5**
- [~] T031 [US3] Implement `code/05_validation.py`: External Validation Logic: **Search path `data/validation/external/` for specific ID `exp_defect_graphene_mos2_v1`**. If found, evaluate. If not found, **check `data_source` flag from Phase 3**: if `synthetic`, generate `data/validation/Validation_Report.json` with **status: SYNTHETIC_FALLBACK**; if `real`, generate with **status: NO_EXTERNAL_DATA** and **method: internal_only**; verify schema keys.
- [X] T032 [US3] Implement `notebooks/01_full_workflow.ipynb`: Reproducible Jupyter notebook integrating all steps (Data Acquisition → Processing → Modeling → Inference → Validation)
- [X] T033 [US3] Implement `notebooks/01_full_workflow.ipynb`: Ensure notebook runs within **6-hour runtime limit** on GitHub Actions free-tier (CPU, ≤7 GB RAM)
- [X] T034 [US3] Implement `code/05_validation.py`: Sensitivity Analysis Report: Generate table of FPR/FNR vs. swept thresholds (deciles or sparse sets)
- [X] T035 [US3] Implement `scripts/run_ci_validation.sh`: CI script to execute the full workflow and validate runtime constraints (≤6h) and memory usage (≤7GB)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036a [P] Update `docs/README.md` with project overview and setup instructions
- [X] T036b [P] Update `docs/API.md` with synthetic generator API documentation
- [~] T037 Code cleanup and refactoring (ensure no hardcoded paths)
- [~] T038 Performance optimization (ensure Random Forest and Permutation tests fit within 6h limit)
- [~] T039 [P] Additional unit tests in `tests/unit/` for data generators and normalization logic <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 3, column 9:
 - path: tests/unit/test_data_processing.py
 ^) -->
- [~] T040 Run `quickstart.md` validation to ensure end-to-end reproducibility <!-- FAILED: unspecified -->

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
Task: "Query Materials Project REST API for ≥50 pristine graphene and MoS₂ structures"
Task: "Implement Physics-Based Synthetic Generator (Primary Mode)"
Task: "Implement Physics-Based Synthetic Generator (Hold-Out Mode)"
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
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: All tasks must run on CPU-only CI (limited cores, constrained RAM, 6h limit). No GPU, no 8-bit quantization, no large LLMs.
- **Critical**: Real data preferred; synthetic data is a fallback ONLY if primary source is missing. If synthetic, claims are restricted to "Method Validation".