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

 Tasks MUST be organized by user story so each user story can be independently completable and testable.

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
- [X] T030 [P] [Foundational] Create `config.yaml` in the project root to store the R² ≥ 0.7 threshold justification. **MANDATORY REQUIREMENT**: The `config.yaml` MUST contain a non-empty string in the `thresholds.r2.citation` field referencing the community-standard benchmark (e.g., "Fundamentals and Catalytic Applications of CeO₂-Based Materials, 2016"). The pipeline MUST raise a validation error if this field is missing or empty (`if not config['thresholds']['r2']['citation']: raise ValueError`). Define the sensitivity sweep range in `thresholds.r2.sweep_range` as `{0.70 (moderate), 0.75 (high), 0.80 (very high)}` to strictly satisfy the spec's `{moderate, high, very high}` requirement (see SC-004 acceptance scenarios).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline & ML Model Training (Priority: P1) 🎯 MVP

**Goal**: Download atomistic simulation datasets, extract grain-boundary descriptors, and train a gradient-boosted tree model to predict atomic diffusivity.

**Independent Test**: Can be fully tested by successfully executing the data download, preprocessing, and model training script on a sample dataset, producing a trained model artifact with reported R², RMSE, and MAPE metrics on held-out test data.

### Implementation for User Story 1

- [X] T009a [US1] Implement `code/download_mp.py` to:
 - Fetch raw structures (POSCAR/CIF) from Materials Project API.
 - **Search Strategy**: Use query parameters `keywords=["grain boundary", "bicrystal"]` and `properties=["diffusivity"]`.
 - **Volume Goal**: Aim to retrieve a volume of raw records sufficient to yield at least 500 valid records after filtering (per FR-001).
 - Validate returned JSON schema and store raw files in `data/raw/mp/` with checksums.
 - **Strict Source Adherence**: Do NOT implement fallbacks to other repositories.
 - **Log** the raw record count but **DO NOT** perform the n >= 500 validation or exit here. Defer this check to T011.
 - **Sampling Fallback**: If the full dataset exceeds available RAM capacity, implement a deterministic sampling strategy (e.g., `itertools.islice` first N rows) as defined in `data/sample_config.yaml` (T040).
- [X] T009b [US1] Implement `code/download_kim.py` to:
 - Fetch raw structures from OpenKIM.
 - **Search Strategy**: Use keywords `grain boundary`, `diffusivity`.
 - Validate JSON schema and store raw files in `data/raw/kim/` with checksums.
 - **Log** raw record count.
 - **Sampling Fallback**: Same as T009a.
- [X] T009c [US1] Implement `code/download_nist.py` to:
 - Fetch raw structures from NIST.
 - **Search Strategy**: Use keywords `grain boundary`, `diffusivity`.
 - Validate JSON schema and store raw files in `data/raw/nist/` with checksums.
 - **Log** raw record count.
 - **Sampling Fallback**: Same as T009a.
- [X] T010 [US1] Implement `code/geometry_parser.py` to:
 - Parse POSCAR/CIF files using `pymatgen` (e.g., `Structure.from_file`).
 - **Derive Boundary Plane Normal**: Identify the interface plane in the bicrystal slab by locating the mid-plane of the simulation cell perpendicular to the growth direction. Calculate the normal vector and convert to Miller indices (hkl).
 - **Extract or Compute Σ Value**:
 - **Case A (Metadata Present)**: Extract Σ value if explicitly present.
 - **Case B (Metadata Absent)**: **Compute** it using `pymatgen.symmetry.analyzer.CSL` or `pymatgen.analysis.structure_matcher` to calculate the Coincidence Site Lattice (CSL) from the misorientation matrix. **Do NOT use simplified formulas.**
 - If calculation fails, set to `NaN`.
 - **Extract Boundary Width and Excess Volume**:
 - **Boundary Width**: Distance between atomic layers at interface.
 - **Excess Volume**: `slab_volume - (number_of_atoms * bulk_atomic_volume)`.
 - **Encode** misorientation angle as Rodrigues vectors. **Output the Rodrigues vector as a single structured feature array (e.g., a single column containing a tuple/array of [x, y, z] or a structured dtype) to preserve vector integrity and symmetry.** Do NOT output as three independent scalar columns.
 - **Encode** boundary plane normal as Miller indices.
 - Output intermediate parsed data to `data/processed/parsed_geometry.parquet` including: misorientation angle, Rodrigues vector (structured), boundary plane normal (h, k, l), Σ value, boundary width, excess volume, and all other raw features.
- [X] T011 [US1] Implement `code/preprocess.py` to:
 - **Execute after T010**: Load parsed geometry and raw data.
 - Filter records with missing required features (misorientation, boundary plane, **calculated or extracted** Σ value, temperature, composition, diffusivity, boundary width, excess volume).
 - **Tag** `simulation_method` (DFT, MD, KMC) and `potential_id` as features.
 - **Enforce** `n >= 500` constraint: If fewer than 500 valid records remain, **MUST** log "Data Insufficiency: Retrieved {retrieved_count}, Valid {valid_count}, Required 500. Missing features: {missing_feature_list}" and exit with code 1.
 - **Write Exclusion Report**: **MUST** write the exclusion count and details to `artifacts/reports/exclusion_report.json` (or update `data/metadata.yaml`) to satisfy the 'report' clause of FR-006 and the Single Source of Truth principle.
 - **Apply Sampling**: If dataset is large, apply the deterministic sampling strategy defined in `data/sample_config.yaml`.
 - Output `data/processed/cleaned_dataset.parquet`.
- [X] T016 [US1] Implement `code/diagnostics.py` to:
 - Compute Mutual Information (MI) between **misorientation angle** (scalar) and **Σ value**.
 - **Logic**:
 - **Case A (Valid Σ Available)**: Compute MI.
 - **Case B (No Valid Σ)**: **DO NOT SKIP**. Generate a report with `{"status": "unavailable", "message": "No valid Σ values in dataset after preprocessing.", "count": <int>}`.
 - **Log** a descriptive note: "MI > 0.8 indicates strong dependency; relationship is descriptive, not causal."
 - **Output** `artifacts/reports/collinearity_diagnostic.json` (or the specific 'unavailable' report) to inform feature selection before training.
 - **Note**: Do NOT halt execution or flag errors based on MI thresholds; strictly report and frame descriptively as per FR-007. **T012b must explicitly use this report for framing, not for feature dropping.**
 - **Dependency**: Must run AFTER T011 (Preprocessing) and BEFORE T012 (Training).
 - **Parallel Status**: **Removed [P] tag**. This task is sequential to T012.
- [X] T012a [US1] Implement `code/train_tuning.py` to:
 - Perform a **70/15/15** train/validation/test split.
 - **Save Split Indices**: **MUST** save the split indices (e.g., `data/processed/split_indices.pkl`) to ensure T012b reuses the exact same split.
 - Execute `RandomizedSearchCV` (k=5) for XGBoost hyperparameter tuning **on the training set only**.
 - **Search space**: `max_depth` [3, 10], `learning_rate` [0.01, 0.3], `n_estimators` [50, 300].
 - **Scoring metric**: `r2`.
 - Save best hyperparameters to `models/best_params.json`.
 - **Measure and log** peak RAM usage (MB) using `psutil` and total runtime (seconds) to `artifacts/reports/compute_metrics.json`.
- [X] T012b [US1] Implement `code/train_final.py` to: <!-- FAILED: unspecified -->
 - **Dependency**: Must run AFTER T012a.
 - **Load Split Indices**: **MUST** load `data/processed/split_indices.pkl` to ensure the held-out test set is identical to the one used in T012a.
 - Train final XGBoost model on the training set using best hyperparameters from T012a.
 - **Evaluate**: Evaluate the final model **ONLY** on the held-out test set.
 - **Calculate Metrics**: Calculate R², RMSE, MAPE on the held-out test set.
 - **Calculate SD**: **MUST** calculate the **standard deviation of R² across k=5 folds of the held-out test set** (using repeated k-fold CV on the test set, or nested CV outer loop on test) to satisfy SC-001.
 - **Collinearity Framing**: **MUST** read `artifacts/reports/collinearity_diagnostic.json` from T016. **Unconditionally** write a framing statement for the joint relationship of misorientation and Σ value in `artifacts/reports/training_metrics.json` stating: "The relationship between misorientation and Σ value is descriptive, not causal, as Σ is derived from misorientation. [UNRESOLVED-CLAIM: c_31c070b9 — status=not_enough_info]" (This applies regardless of the MI score).
 - Save `models/best_model.json`.
 - Log R², RMSE, MAPE, and SD to `artifacts/reports/training_metrics.json`.
- [X] T013 [P] [US1] Add unit tests in `tests/unit/test_geometry_parser.py` for parsing logic and encoding correctness (including boundary plane normal derivation).
- [X] T014 [P] [US1] Add unit tests in `tests/unit/test_preprocess.py` for feature engineering, Σ value extraction/calculation logic, and missing value handling. <!-- FAILED: unspecified -->
- [X] T015 [US1] Add integration test in `tests/integration/test_pipeline.py` to verify end-to-end execution (T009a-c -> T010 -> T011 -> T016 -> T012a -> T012b) within 6 hours and <7 GB RAM. **Removed [P] tag**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Validation & Bias Assessment (Priority: P2)

**Goal**: Perform k-fold cross-validation, regression-based bias testing, and report average metrics with family-wise error correction.

**Independent Test**: Can be fully tested by running the validation script on a pre-trained model and producing a validation report with k-fold metrics, regression bias test results, and bias assessment.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/validate.py` to:
 - **Dependency**: Must run AFTER T012b. **Removed [P] tag**.
 - Perform k=5 cross-validation **on the held-out test set** (repeated split) to assess generalization stability and measure test-set performance variance.
 - Report average R², RMSE, MAPE and **calculate standard deviation of R² across the k=5 folds on the test set** (must be <= 0.05). **This metric satisfies SC-001.**
 - Execute regression bias test (y_true ~ y_pred) on the **held-out test set** to calculate intercept, slope, and p-values.
 - Apply Bonferroni correction (α_adj = 0.05 / 3 ≈ 0.017) for multiple hypothesis tests. [UNRESOLVED-CLAIM: c_3af9f8fd — status=not_enough_info]
 - Generate `artifacts/reports/validation_report.json`.
- [X] T018 [P] [US2] Add unit tests in `tests/unit/test_diagnostics.py` for MI calculation (if not covered in T013). <!-- FAILED: unspecified -->
- [ ] T019 [P] [US2] Add unit tests in `tests/unit/test_validate.py` for bias test logic and FWER correction. <!-- FAILED: unspecified -->
- [X] T020 [US2] Add integration test in `tests/integration/test_validation.py` to verify report generation and metric thresholds.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Interpretability & Sensitivity Analysis (Priority: P3)

**Goal**: Visualize SHAP values for feature importance and perform sensitivity analysis on the R² threshold.

**Independent Test**: Can be fully tested by running the interpretability script on a trained model and producing SHAP plots plus a sensitivity table showing how model performance varies across R² thresholds.

### Implementation for User Story 3

- [ ] T021 [US3] Implement `code/interpret.py` to: <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
 - **Dependency**: This task MUST run AFTER T017 (Validation) to ensure `validation_report.json` is available. **Removed [P] tag**.
 - Generate SHAP summary plot and ranked feature-importance list.
 - Perform sensitivity analysis sweeping R² threshold across the range **defined in `config.yaml` (`thresholds.r2.sweep_range`)**. **Do NOT hardcode values.**
 - **Define Pass**: Model R² > threshold.
 - **Define Sensitivity Metrics**: Calculate and report:
 1. **Pass Rate**: Proportion of bootstrap samples (or folds) where R² > threshold.
 2. **False Positive Rate (FPR) Proxy**: For a regression context, define this as the proportion of test records where `predicted > threshold` AND `actual <= threshold`.
 - **Generate** `threshold-sensitivity-table.csv` artifact with columns: `threshold, pass_rate, fpr_proxy, sample_size`.
 - **Include** a one-line justification for the R² ≥ 0.7 threshold by loading the `thresholds.r2.citation` field from `config.yaml` (created in T030) and embedding it in the report.
 - Save plots to `artifacts/figures/` and reports to `artifacts/reports/`.
- [ ] T022 [P] [US3] Add logic to `code/interpret.py` to load the R² threshold justification from `config.yaml` (created in T030) and include it in the final report. <!-- FAILED: unspecified -->
- [ ] T023 [P] [US3] Add unit tests in `tests/unit/test_interpret.py` for SHAP value extraction. <!-- FAILED: unspecified -->
- [ ] T024 [US3] Add integration test in `tests/integration/test_interpretability.py` to verify plot generation and sensitivity table accuracy.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T025a [P] Documentation updates: Write API usage and data schema sections in `README.md` and `docs/`, ensuring traceability to `data/metadata.yaml` as per Constitution Principle IV.
- [X] T025b [P] Documentation updates: Write Installation and Environment setup sections in `README.md`.
- [X] T026a [P] Code cleanup: Remove unused imports from `code/utils.py`.
- [X] T026b [P] Code cleanup: Standardize logging format in `code/utils.py`.
- [X] T029 Verify `state.yaml` updates with content hashes after successful pipeline run.
- [ ] T034 [US1] Add unit tests in `tests/unit/test_download.py` to verify that the download script logs the raw count but does NOT halt on insufficiency (delegating to T011), ensuring no synthetic fallback is used (addressing edge case: data insufficiency).
- [ ] T036 [US1] Update `code/download.py` (and sub-modules) to include exponential backoff logic for API rate limits (Materials Project, OpenKIM) to prevent premature failures during bulk fetches.
- [ ] T037 [US1] Update `code/preprocess.py` to explicitly log the count of excluded records due to missing `Σ value` or `boundary plane normal` and verify these counts are non-zero if the dataset is incomplete, ensuring transparency in data filtering.
- [ ] T038 [US2] Add a unit test in `tests/unit/test_validate.py` to verify the Bonferroni correction calculation (α_adj = 0.05 / 3) and ensure the p-value adjustment logic is correctly applied to the bias test results.
- [ ] T039 [US3] Add a unit test in `tests/unit/test_interpret.py` to verify the "False Positive Rate Proxy" metric calculation logic (predicted > threshold AND actual <= threshold), ensuring it correctly measures the rate of incorrect high predictions.
- [ ] T040 [US1] Implement a `data/sample_config.yaml` that defines a specific, reproducible sampling strategy (e.g., `itertools.islice` first N rows or fixed-seed random sample) with explicit documentation of the sample size and its representativeness limitations, to be used only if the full dataset cannot be processed within compute constraints.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **User Story 2 (P2)**: **Depends on US1 completion** (requires model artifact)
 - **User Story 3 (P3)**: **Depends on US1 completion** (requires model artifact) and **Depends on T017** (Validation) for report context
 - *Note: US2 and US3 can proceed in parallel once US1 artifacts (T012) are available. They do not depend on the implementation phase of US1, only the completion of its artifacts.*
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Sequential Execution Order (Phase 3)

- T009a-c (Download) -> T010 (Geometry Parsing) -> T011 (Preprocessing) -> T016 (Diagnostics) -> T012a (Tuning) -> T012b (Final Training)
- T015 (Integration Test) depends on T009-T012 completion.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 and US3 can start in parallel (if US1 is complete)
- All tests for a user story marked [P] can run in parallel (T013, T014, T018, T019, T022, T023)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (once dependencies are met)
- **Note on T016**: T016 (Diagnostics) MUST complete before T012 (Training) begins. T016 is NOT parallel to T012. The dependency is sequential: T011 -> T016 -> T012a -> T012b.
- **Note on Internal US1 Dependencies**: While US2 and US3 can start after US1's *artifacts* are ready, the internal US1 tasks (T011 -> T016 -> T012a -> T012b) remain strictly sequential and cannot be parallelized.

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
- **Data Source Constraint**: {{claim:c_919349f5}} (Wikidata Q37499364, https://www.wikidata.org/wiki/Q37499364) No fallbacks are permitted.
- **Σ Value Constraint**: Σ value must be calculated from misorientation if not in metadata; it is a required feature. Missing values result in record exclusion.
- **Reproducibility Constraint**: All datasets must be downloaded, chunked if necessary, and checksummed locally. Streaming without local storage is prohibited. **Exception**: For datasets >7GB, sampling with immediate processing (T040) is required to maintain RAM limits, but MUST result in a static, checksummed local copy.
- **New Task Rationale**: T034-T040 address specific reviewer concerns regarding API robustness (backoff), data transparency (missing value logging), statistical rigor (Bonferroni verification), metric correctness (FPR proxy for regression), and reproducible sampling strategies for out-of-memory scenarios. T027 and T028 were removed as they were ungrounded scope creep.
