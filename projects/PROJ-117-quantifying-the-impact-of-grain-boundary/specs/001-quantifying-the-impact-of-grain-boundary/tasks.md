# Tasks: Quantifying Grain Boundary Character on Diffusivity

**Input**: Design documents from `/specs/001-grain-boundary-diffusivity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [X] T001 Create project structure per implementation plan (`code/`, `data/raw/`, `data/processed/`, `models/`, `artifacts/`)
- [X] T002 Initialize Python project with pinned dependencies in `requirements.txt` (pandas, numpy, scikit-learn, xgboost, shap, matplotlib, requests, pymatgen)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `data/metadata.yaml` schema for provenance (source, version tag, checksum, retrieval date)
- [X] T005 [P] Implement `code/utils.py` with helpers for checksumming (SHA-256), logging, and random seed setting
- [X] T006 Create base `GrainBoundaryRecord` dataclass/schema in `code/models/grain_boundary_record.py`
- [X] T007 Setup error handling infrastructure for `Data Insufficiency` halt (exit code 1) ensuring the error message logs the exact count of retrieved vs. required records (implementation in T011)
- [X] T008 Configure environment variables for API keys (Materials Project, OpenKIM) in `.env` (not committed)
- [X] T016 [P] [US1/Foundational] Implement `code/diagnostics.py` to: <!-- ATOMIZE: requested --> <!-- FAILED: unspecified -->
 - Compute Mutual Information (MI) between **misorientation angle** and **Σ value** (calculated from misorientation) on the raw dataset.
 - **Algorithm**: Calculate Σ value using the Coincidence Site Lattice (CSL) definition for the given misorientation angle.
 - **Log** a warning: "MI > 0.8 indicates strong dependency; relationship is descriptive, not causal."
 - **Output** `artifacts/reports/collinearity_diagnostic.json` to inform feature selection before training.
 - **Dependency**: Must run BEFORE T012 (Training) to allow feature engineering adjustments.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline & ML Model Training (Priority: P1) 🎯 MVP

**Goal**: Download atomistic simulation datasets, extract grain-boundary descriptors, and train a gradient-boosted tree model to predict atomic diffusivity.

**Independent Test**: Can be fully tested by successfully executing the data download, preprocessing, and model training script on a sample dataset, producing a trained model artifact with reported R², RMSE, and MAPE metrics on held-out test data.

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/download.py` to: <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->
 - Fetch raw structures (POSCAR/CIF) from Materials Project API, OpenKIM, and NIST.
 - **Search Strategy**: Use query parameters `keywords=["grain boundary", "bicrystal"]` and `properties=["diffusivity"]` to identify relevant records. If specific material IDs are not known, use the Materials Project search endpoint to filter by these keywords.
 - Validate returned JSON schema and store raw files in `data/raw/` with checksums.
 - **Verify** the count of raw records is >= 500 before proceeding; if < 500, log "Data Insufficiency: Retrieved {count} < 500" and exit with code 1.
- [X] T010 [US1] Implement `code/geometry_parser.py` to:
 - Parse POSCAR/CIF files using `pymatgen` (e.g., `Structure.from_file`).
 - **Derive Boundary Plane Normal**: Identify the interface plane in the bicrystal slab by locating the mid-plane of the simulation cell perpendicular to the growth direction. Calculate the normal vector to this plane and convert it to Miller indices (hkl) using the lattice basis vectors.
 - **Derive Σ Value**: Calculate the Σ value from the misorientation angle using the Coincidence Site Lattice (CSL) definition (e.g., Σ = 1 / (1 - cos(θ)) approximation or lookup table for common angles).
 - Extract boundary width (using slab dimensions) and excess volume (using geometric calculation).
 - **Encode** misorientation angle as Rodrigues vectors (using `pymatgen.symmetry.analyzer` or custom rotation matrix logic).
 - **Encode** boundary plane normal as Miller indices (using `pymatgen.core.lattice` methods).
 - Output intermediate parsed data to `data/processed/parsed_geometry.parquet`.
- [X] T011 [US1] Implement `code/preprocess.py` to: <!-- FAILED: unspecified -->
 - **Execute after T010**: Load parsed geometry and raw data.
 - Filter records with missing required features (misorientation, boundary plane, Σ value, temperature, composition, diffusivity, boundary width, excess volume).
 - **Tag** `simulation_method` (DFT, MD, KMC) and `potential_id` as features.
 - **Enforce** `n >= 500` constraint: If fewer than 500 valid records remain, log "Data Insufficiency: {valid_count} < 500. Missing features: {missing_feature_list}" and exit with code 1. The error must explicitly list which features (e.g., 'boundary plane normal', 'Σ value') caused the insufficiency.
 - Output `data/processed/cleaned_dataset.parquet`.
- [X] T012 [US1] Implement `code/train.py` to:
 - Perform a **70/15/15** train/validation/test split. *Note: Corrected from ambiguous spec notation '/15/15' to ensure sufficient training data for XGBoost.*
 - Execute `RandomizedSearchCV` (k=5) for XGBoost hyperparameter tuning.
 - **Search space**: `max_depth` [3, 10], `learning_rate` [0.01, 0.3], `n_estimators` [50, 300].
 - **Scoring metric**: `r2`.
 - Train final model on training set.
 - Save `models/best_model.json`.
 - Log R², RMSE, MAPE on held-out test set to `artifacts/reports/training_metrics.json`.
- [X] T013 [P] [US1] Add unit tests in `tests/unit/test_geometry_parser.py` for parsing logic and encoding correctness (including boundary plane normal derivation).
- [X] T014 [P] [US1] Add unit tests in `tests/unit/test_preprocess.py` for feature engineering, Σ value calculation, and missing value handling.
- [X] T015 [US1] Add integration test in `tests/integration/test_pipeline.py` to verify end-to-end execution (T009 -> T010 -> T011 -> T016 -> T012) within 6 hours and <7 GB RAM.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Validation & Bias Assessment (Priority: P2)

**Goal**: Perform k-fold cross-validation, regression-based bias testing, and report average metrics with family-wise error correction.

**Independent Test**: Can be fully tested by running the validation script on a pre-trained model and producing a validation report with k-fold metrics, regression bias test results, and bias assessment.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/validate.py` to:
 - Perform k=5 cross-validation on the trained model.
 - Report average R², RMSE, MAPE and **calculate standard deviation of R²** (must be <= 0.05).
 - Execute regression bias test (y_true ~ y_pred) to calculate intercept, slope, and p-values.
 - Apply Bonferroni correction (α_adj = 0.017) for multiple hypothesis tests.
 - Generate `artifacts/reports/validation_report.json`.
- [X] T018 [P] [US2] Add unit tests in `tests/unit/test_diagnostics.py` for MI calculation (if not covered in T013).
- [X] T019 [P] [US2] Add unit tests in `tests/unit/test_validate.py` for bias test logic and FWER correction.
- [X] T020 [US2] Add integration test in `tests/integration/test_validation.py` to verify report generation and metric thresholds.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Interpretability & Sensitivity Analysis (Priority: P3)

**Goal**: Visualize SHAP values for feature importance and perform sensitivity analysis on the R² threshold.

**Independent Test**: Can be fully tested by running the interpretability script on a trained model and producing SHAP plots plus a sensitivity table showing how model performance varies across R² thresholds.

### Implementation for User Story 3

- [X] T021 [P] [US3] Implement `code/interpret.py` to:
 - Generate SHAP summary plot and ranked feature-importance list.
 - Perform sensitivity analysis sweeping R² threshold across a range of moderate-to-high values.
 - **Define Pass**: Model R² > threshold.
 - **Define Threshold Sensitivity**: Report the proportion of folds where the model passes the threshold for each value.
 - **Remove** any undefined "False-Positive Rate" or "null hypothesis" calculations.
 - **Generate** `threshold-variation-table.csv` artifact showing Pass Rate vs. Threshold.
 - **Include** a one-line justification for the R² ≥ 0.7 threshold referencing the configuration file or documentation source that cites community-standard model performance benchmarks for materials property prediction.
 - Save plots to `artifacts/figures/` and reports to `artifacts/reports/`.
- [X] T022 [US3] Add logic to `code/interpret.py` to reference a configuration file or documentation for the R² ≥ 0.7 threshold justification.
- [X] T023 [P] [US3] Add unit tests in `tests/unit/test_interpret.py` for SHAP value extraction.
- [X] T024 [US3] Add integration test in `tests/integration/test_interpretability.py` to verify plot generation and sensitivity table accuracy.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T025a [P] Documentation updates: Write API usage and data schema sections in `README.md` and `docs/`.
- [ ] T025b [P] Documentation updates: Write Installation and Environment setup sections in `README.md`.
- [X] T026a [P] Code cleanup: Remove unused imports from `code/utils.py`.
- [X] T026b [P] Code cleanup: Standardize logging format in `code/utils.py`.
- [ ] T027 Performance optimization: ensure all heavy loops use vectorized numpy/pandas operations to stay within 6h runtime.
- [ ] T028 [P] Run `quickstart.md` validation.
- [ ] T029 Verify `state.yaml` updates with content hashes after successful pipeline run.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **User Story 2 (P2)**: **Depends on US1 completion** (requires model artifact)
 - **User Story 3 (P3)**: **Depends on US1 completion** (requires model artifact)
 - *Note: US2 and US3 cannot run in parallel with US1 implementation.*
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Sequential Execution Order (Phase 3)

- T009 (Download) -> T010 (Geometry Parsing) -> T011 (Preprocessing) -> T016 (Diagnostics) -> T012 (Training)
- T015 (Integration Test) depends on T009-T012 completion.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 and US3 can start in parallel (if US1 is complete)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (once dependencies are met)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only CI (limited cores, constrained RAM, within a fixed time budget). No GPU/CUDA, no 8-bit quantization, no large LLMs.
- **CPU Limit**: The GitHub Actions free-tier limit is a hard constraint of **2 CPU cores**.