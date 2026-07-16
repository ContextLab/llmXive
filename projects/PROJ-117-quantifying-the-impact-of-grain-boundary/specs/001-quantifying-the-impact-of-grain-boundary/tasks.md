# Tasks: Quantifying Grain Boundary Character on Diffusivity

**Input**: Design documents from `/specs/001-grain-boundary-diffusivity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
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

 Tasks MUST be organized by user story so each story can be independently completable and testable.

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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `data/metadata.yaml` schema for provenance (source, version tag, checksum, retrieval date)
- [X] T005 [P] Implement `code/utils.py` with helpers for checksumming (SHA-256), logging, and random seed setting
- [X] T006 Create base `GrainBoundaryRecord` dataclass/schema in `code/models/grain_boundary_record.py`
- [X] T007 Setup error handling infrastructure for `Data Insufficiency` halt (exit code 1) ensuring the error message logs the exact count of retrieved vs. required records (implementation in T011)
- [X] T008 Configure environment variables for API keys (Materials Project, OpenKIM) in `.env` (not committed)
- [X] T030 [P] [Foundational] Create `config.yaml` in the project root to store the R² ≥ 0.7 threshold justification. **MANDATORY REQUIREMENT**: The `config.yaml` MUST contain a non-empty string in the `citation` field referencing the community-standard benchmark (e.g., "Fundamentals and Catalytic Applications of CeO₂-Based Materials, 2016"). The pipeline MUST raise a validation error if this field is missing or empty, ensuring the 'Verified Accuracy' principle is enforced programmatically. Also define the threshold sweep range (0.65, 0.70, 0.75).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline & ML Model Training (Priority: P1) 🎯 MVP

**Goal**: Download atomistic simulation datasets, extract grain-boundary descriptors, and train a gradient-boosted tree model to predict atomic diffusivity.

**Independent Test**: Can be fully tested by successfully executing the data download, preprocessing, and model training script on a sample dataset, producing a trained model artifact with reported R², RMSE, and MAPE metrics on held-out test data.

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/download.py` to:
 - Fetch raw structures (POSCAR/CIF) from Materials Project API, OpenKIM, and NIST.
 - **Search Strategy**: Use query parameters `keywords=["grain boundary", "bicrystal"]` and `properties=["diffusivity"]` to identify relevant records. If specific material IDs are not known, use the Materials Project search endpoint to filter by these keywords.
 - Validate returned JSON schema and store raw files in `data/raw/` with checksums.
 - **Strict Source Adherence**: Do NOT implement fallbacks to other repositories (e.g., HuggingFace) if the primary sources fail. If the required data is not available from the specified sources, the pipeline must proceed to preprocessing and halt there if the count is insufficient.
 - **Log** the raw record count (e.g., "Raw records retrieved: X") but **DO NOT** perform the n >= 500 validation or exit here. Defer this check to T011 (Preprocessing) where filtering for missing values occurs.
- [X] T010 [US1] Implement `code/geometry_parser.py` to:
 - Parse POSCAR/CIF files using `pymatgen` (e.g., `Structure.from_file`).
 - **Derive Boundary Plane Normal**: Identify the interface plane in the bicrystal slab by locating the mid-plane of the simulation cell perpendicular to the growth direction. Calculate the normal vector to this plane and convert it to Miller indices (hkl) using the lattice basis vectors.
 - **Extract Ground-Truth Σ Value**: Attempt to extract the Σ value **only if explicitly present** in the raw data metadata (e.g., as a comment tag in the CIF/POSCAR header). **DO NOT** derive the Σ value from the misorientation angle in this step. If the raw data does not contain a pre-calculated Σ value, set the field to `NaN` (missing).
 - Extract boundary width (using slab dimensions) and excess volume (using geometric calculation).
 - **Encode** misorientation angle as Rodrigues vectors (using `pymatgen.symmetry.analyzer` or custom rotation matrix logic).
 - **Encode** boundary plane normal as Miller indices (using `pymatgen.core.lattice` methods).
 - Output intermediate parsed data to `data/processed/parsed_geometry.parquet`.
- [X] T011 [US1] Implement `code/preprocess.py` to:
 - **Execute after T010**: Load parsed geometry and raw data.
 - Filter records with missing required features (misorientation, boundary plane, **ground-truth** Σ value (if available), temperature, composition, diffusivity, boundary width, excess volume).
 - **Tag** `simulation_method` (DFT, MD, KMC) and `potential_id` as features.
 - **Enforce** `n >= 500` constraint: If fewer than 500 valid records remain (after filtering for missing values), log "Data Insufficiency: {valid_count} < 500. Missing features: {missing_feature_list}" and exit with code 1. The error must explicitly list which features (e.g., 'boundary plane normal', 'Σ value') caused the insufficiency.
 - Output `data/processed/cleaned_dataset.parquet`.
- [X] T016 [US1] [P] Implement `code/diagnostics.py` to:
 - Compute Mutual Information (MI) between **misorientation angle** and **Σ value**.
 - **Logic for T010 Output**:
 - **Case A (Ground-Truth Available)**: If the dataset contains a ground-truth Σ value (extracted in T010), compute MI between misorientation and this ground-truth value to diagnose non-linear dependency.
 - **Case B (No Ground-Truth)**: If the dataset lacks a ground-truth Σ (all values are `NaN` from T010), **SKIP** the MI calculation and log a warning: "No ground-truth Σ value available. Skipping MI diagnostic to avoid tautological self-correlation." Do NOT calculate theoretical Σ or claim a data-driven relationship.
 - **Log** a descriptive note: "MI > 0.8 indicates strong dependency; relationship is descriptive, not causal."
 - **Output** `artifacts/reports/collinearity_diagnostic.json` to inform feature selection before training.
 - **Note**: Do NOT halt execution or flag errors based on MI thresholds; strictly report and frame descriptively as per FR-007.
 - **Dependency**: Must run AFTER T011 (Preprocessing) and BEFORE T012 (Training).
- [X] T012 [US1] Implement `code/train.py` to:
 - Perform a **70/15/15** train/validation/test split.
 - Execute `RandomizedSearchCV` (k=5) for XGBoost hyperparameter tuning **on the training set only**. The internal k-fold CV must not touch the validation or test sets.
 - **Search space**: `max_depth` [3, 10], `learning_rate` [0.01, 0.3], `n_estimators` [50, 300].
 - **Scoring metric**: `r2`.
 - Train final model on the training set.
 - **Measure and log** peak RAM usage (MB) and total runtime (seconds) to `artifacts/reports/compute_metrics.json` to satisfy SC-005.
 - **Evaluation**: Evaluate the final model **ONLY** on the held-out [deferred] test set (never on the validation set used for tuning) to avoid optimistic bias.
 - Save `models/best_model.json`.
 - Log R², RMSE, MAPE on held-out test set to `artifacts/reports/training_metrics.json`.
- [X] T013 [P] [US1] Add unit tests in `tests/unit/test_geometry_parser.py` for parsing logic and encoding correctness (including boundary plane normal derivation).
- [X] T014 [P] [US1] Add unit tests in `tests/unit/test_preprocess.py` for feature engineering, Σ value extraction logic, and missing value handling.
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
 - Apply Bonferroni correction (α_adj = 0.05 / 3 ≈ 0.017) for multiple hypothesis tests.
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

- [X] T021 [US3] Implement `code/interpret.py` to:
 - **Dependency**: This task MUST run AFTER T017 (Validation) to ensure `validation_report.json` is available. Do NOT mark as [P].
 - Generate SHAP summary plot and ranked feature-importance list.
 - Perform sensitivity analysis sweeping R² threshold across a range of moderate-to-high values.
 - **Define Pass**: Model R² > threshold.
 - **Define Sensitivity Metrics**: Instead of FPR (which is invalid for regression), calculate and report:
 1. **Pass Rate**: Proportion of bootstrap samples (or folds) where R² > threshold.
 2. **Prediction Distribution Shift**: At each threshold, report the proportion of predicted values exceeding the threshold vs. the proportion of actual values exceeding the threshold. This measures the model's tendency to over/under-predict at different cutoffs.
 - **Generate** `threshold-sensitivity-table.csv` artifact showing Pass Rate and Distribution Shift vs. Threshold.
 - **Include** a one-line justification for the R² ≥ 0.7 threshold by loading the `citation` field from `config.yaml` (created in T030) and embedding it in the report.
 - Save plots to `artifacts/figures/` and reports to `artifacts/reports/`.
- [X] T022 [US3] Add logic to `code/interpret.py` to load the R² threshold justification from `config.yaml` (created in T030) and include it in the final report.
- [X] T023 [P] [US3] Add unit tests in `tests/unit/test_interpret.py` for SHAP value extraction.
- [X] T024 [US3] Add integration test in `tests/integration/test_interpretability.py` to verify plot generation and sensitivity table accuracy.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T025a [P] Documentation updates: Write API usage and data schema sections in `README.md` and `docs/`, ensuring traceability to `data/metadata.yaml` as per Constitution Principle IV.
- [X] T025b [P] Documentation updates: Write Installation and Environment setup sections in `README.md`.
- [X] T026a [P] Code cleanup: Remove unused imports from `code/utils.py`.
- [X] T026b [P] Code cleanup: Standardize logging format in `code/utils.py`.
- [ ] T027 Performance optimization: ensure all heavy loops use vectorized numpy/pandas operations to stay within 6h runtime.
- [ ] T028 [P] Run `quickstart.md` validation.
- [X] T029 Verify `state.yaml` updates with content hashes after successful pipeline run.
- [X] T034 [US1] Add unit tests in `tests/unit/test_download.py` to verify that the download script logs the raw count but does NOT halt on insufficiency (delegating to T011), ensuring no synthetic fallback is used (addressing edge case: data insufficiency).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **User Story 2 (P2)**: **Depends on US1 completion** (requires model artifact)
 - **User Story 3 (P3)**: **Depends on US1 completion** (requires model artifact) and **Depends on T017** (Validation) for report context
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
- **Note on T016**: T016 (Diagnostics) can run in parallel with T012 (Training) **only if** feature selection is not performed based on the MI score. If the MI score is used to drop features, T016 must complete before T012.

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
- **Data Source Constraint**: The pipeline strictly adheres to Materials Project, OpenKIM, and NIST. No fallbacks are permitted.
- **Σ Value Constraint**: Σ value must be extracted from raw data if available; otherwise, it is marked as missing. Theoretical derivation is only used for diagnostic labeling, not data generation.