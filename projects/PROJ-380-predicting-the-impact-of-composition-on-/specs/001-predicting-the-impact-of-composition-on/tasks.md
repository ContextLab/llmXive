# Tasks: Predicting the Impact of Composition on the Shear Modulus of Bulk Metallic Glasses

**Input**: Design documents from `/specs/001-predicting-the-impact-of-composition-on-/`
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

- [X] T001 Create project structure at repository root per implementation plan (`code/`, `data/`, `tests/`, `docs/`, `state/`, `artifacts/`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black)
- [X] T004 [P] Setup `Makefile` entry point for full pipeline orchestration (FR-010)
- [X] T005 [P] Initialize `utils/config.py` with random seeds and path constants

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Implement `utils/provenance.py` for full checksum generation logic (including file hashing and `state/...yaml` recording) per Constitution Principle V. This module must provide a `record_artifact(file_path, state_file)` function that computes SHA-256 and writes to the state YAML.
- [X] T007a [P] [Foundational] Define schema structure for `contracts/bmg_entry.schema.yaml`. **Schema Definition**: Must include fields: `source` (enum: [MP, Inoue, Synthetic]), `composition` (object: {element: atomic_pct}), `modulus` (float, GPa), `phase` (string, must be "bulk metallic glass"), `family` (string). **Action**: Write the schema definition directly to `contracts/bmg_entry.schema.yaml`.
- [X] T007b [P] [Foundational] Write `contracts/bmg_entry.schema.yaml` to disk. **Action**: Create the file `contracts/bmg_entry.schema.yaml` with the exact schema defined in T007a. (Note: T007a and T007b are now consolidated steps for direct writing).
- [X] T008a [P] [Foundational] Define schema structure for `contracts/model_output.schema.yaml`. **Schema Definition**: Must include fields: `metrics` (object: {R2: float, MAE: float, RMSE: float}), `hyperparameters` (object), `statistical_test` (object: {method: string, p_value: float, confidence_interval: [float, float]}). **Action**: Write the schema definition directly to `contracts/model_output.schema.yaml`.
- [X] T008b [P] [Foundational] Write `contracts/model_output.schema.yaml` to disk. **Action**: Create the file `contracts/model_output.schema.yaml` with the exact schema defined in T008a. (Note: T008a and T008b are now consolidated steps for direct writing).
- [X] T009 Setup `data/` directory structure (`raw/`, `processed/`, `artifacts/`)
- [X] T010 [P] Implement `code/__init__.py` and basic logging configuration

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download/clean raw BMG data and compute compositional descriptors (δ, ΔHmix, VEC, Δχ) to create a ready-to-train feature matrix.

**Independent Test**: The pipeline can be fully tested by executing the data ingestion script on a small sample dataset and verifying that the output CSV contains exactly the expected columns with no missing values in the target variable.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Unit test for composition standardization (wt% to at%) in `tests/unit/test_clean.py`
- [X] T014 [P] [US1] Unit test for descriptor calculation (δ, ΔHmix, VEC, Δχ) in `tests/unit/test_features.py`
- [X] T015 [P] [US1] Integration test for full ingestion pipeline in `tests/integration/test_ingest_pipeline.py`

### Implementation for User Story 1

- [X] T016 [US1] Implement `code/data/ingest.py` to load data. **Logic**: **STRICTLY PRIORITY**: Attempt to fetch data from the Materials Project API using the configured API key. **IF FETCH FAILS OR DATA IS MISSING**, automatically invoke the synthetic data generator (previously T011) to generate a synthetic BMG dataset based on verified literature parameters. **DO NOT** halt or require manual intervention. Validate schema against `contracts/bmg_entry.schema.yaml` (created in T007b). Invoke `utils/provenance.py` (implemented in T006) to record checksums.
- [X] T017 [US1] Implement `code/data/clean.py` to filter for "bulk metallic glass" phase and standardize units (FR-002, FR-003)
- [X] T018 [US1] Implement `code/data/features.py` to calculate δ, ΔHmix, VEC, and electronegativity difference using `mendeleev` (FR-003)
- [X] T019 [US1] Calculate VIF in `code/data/features.py`. **Logic**: Calculate VIF for each descriptor. If VIF > 5, apply feature pruning. If < 2 features remain after pruning, **perform PCA** (variance threshold > 95%) to reduce dimensionality instead of halting. Output a list of retained features or principal components. **Note**: Do NOT implement Ridge fallback here; that belongs in T025.
- [X] T020 [US1] Implement `code/data/split.py` to perform **LOFO / GroupKFold Hybrid** cross-validation (FR-004). **Logic**: For families with N >= 2, use Leave-One-Family-Out (LOFO). For families with N < 2, switch to GroupKFold (k=5) to avoid empty folds. **Constraint**: If a family has < 2 samples, do NOT halt; log a warning and use GroupKFold for that family's fold.
- [X] T021 [US1] Add validation to ensure no missing values in target variable after cleaning and filtering
- [ ] T048 [US1] **CRITICAL DATA CONTINGENCY**: Implement a strict "Fail Loudly" check in `code/data/ingest.py` to ensure that if the Materials Project API returns data with zero valid BMG entries (or empty response), the code does NOT silently fall back to synthetic data without raising a clear, descriptive error first. **Logic**: The current T016 logic allows silent fallback. This task adds a guard: if `len(valid_bmg_entries) == 0` after API fetch, raise `ValueError("No valid BMG data found in Materials Project. Synthetic fallback disabled for this run.")` to force a manual review or verified data injection, preventing accidental fabrication of a "full" dataset when the real source is empty. *Note: This overrides the "automatic synthetic fallback" in T016 if the real source is truly empty, aligning with the "No Fabrication" rule.*

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Performance Evaluation (Priority: P2)

**Goal**: Train Linear Regression, Random Forest, and Gradient Boosting models with grid search (≤50 combos), evaluate via R²/MAE/RMSE, and perform statistical comparison (Wilcoxon Signed-Rank Test primary) and hybrid LOFO validation.

**Independent Test**: The training script can be tested by running it on a fixed subset of the data and verifying that it outputs a JSON report containing metrics and best hyperparameters.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US2] Unit test for grid search limit (≤50 combinations) in `tests/unit/test_train.py`
- [X] T023 [P] [US2] Unit test for hybrid LOFO split logic in `tests/unit/test_split.py`
- [X] T024 [US2] Integration test for model evaluation and statistical comparison in `tests/integration/test_model_eval.py`

### Implementation for User Story 2

- [X] T025 [US2] Implement `code/models/train.py` to train Linear Regression, Random Forest, and Gradient Boosting (FR-005). **Logic**: **Step 1**: If VIF > 5 is detected from T019, apply feature pruning. If pruning is insufficient, apply Ridge Regression as a fallback to handle collinearity. **Step 2**: Train models on the processed features.
- [X] T026 [US2] Implement grid search with 5-fold CV and ≤50 combinations limit in `code/models/train.py` (FR-006, Plan Constraints)
- [X] T027 [US2] Implement statistical comparison for model evaluation (FR-007). **Logic**: **PRIMARY**: Perform Wilcoxon Signed-Rank Test on the cross-validation folds to compare model performance (for small N and non-normal data). **CONTINGENCY**: Only if N >= 30 AND residuals pass normality test, use Corrected Resampled t-test as a fallback. Output p-value and confidence interval.
- [X] T028 [US2] Implement LOFO cross-validation in `code/models/evaluate.py` (FR-008)
- [X] T029 [US2] Generate `artifacts/model_report.json` containing keys: `metrics: {R2 (float), MAE (float), RMSE (float)}`, `hyperparameters: {...}`, `statistical_test: {method (string), p_value (float), confidence_interval: [float, float]}`. **Schema**: Must match `contracts/model_output.schema.yaml` (FR-007). **Dependency**: Must run strictly after T027 and T026.
- [X] T030 [US2] Implement **LOFO / GroupKFold Hybrid** in `code/models/evaluate.py` (FR-008). **Logic**: Re-use the splitter logic defined in T020. For families with N >= 2, use LOFO. For families with N < 2, use GroupKFold. Log a warning if family size is small (e.g., < 10) but N >= 2. Do NOT halt.
- [X] T031 [US2] Add error handling for empty folds in LOFO. **Logic**: If a family has < 2 samples, the test fold is handled by GroupKFold (see T030). Log a critical warning but proceed. If the entire dataset is < 2, log a critical warning.
- [ ] T049 [US2] **DATA FLOW INTEGRITY**: Ensure `code/models/train.py` explicitly validates that the input data file exists and is non-empty before attempting to load it, preventing silent crashes or empty model training if the upstream `clean.py` or `features.py` failed. **Logic**: Add a check at the start of `train.py`: `if not os.path.exists(input_path) or os.path.getsize(input_path) == 0: raise FileNotFoundError(...)`. This prevents the "degenerate CPU imitation" of training on empty data if the ingestion pipeline failed upstream.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance Analysis and Visualization (Priority: P3)

**Goal**: Extract feature importances, perform permutation testing to assess predictive contribution, and generate PDPs and correlation heatmaps. Verify SC-001.

**Independent Test**: The analysis script can be tested by running it on the trained model and verifying that it outputs a JSON file with importance scores and generates the required plot files.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T032 [US3] Unit test for permutation importance calculation in `tests/unit/test_importance.py`
- [X] T033 [P] [US3] Unit test for plot generation in `tests/unit/test_viz.py`

### Implementation for User Story 3

- [X] T034 [US3] Implement `code/models/importance.py` to extract feature importances from best tree-based model (FR-009)
- [X] T035 [US3] Implement permutation importance testing with a sufficient number of permutations for statistical stability. in `code/models/importance.py` (FR-009, Spec US-3). **Dependency**: Must run after US2 (T025/T026) completes.
- [X] T036 [US3] Ensure results are explicitly labeled as "predictive contribution within the trained model" (not 'statistical significance') in output JSON and plot captions (FR-009)
- [X] T037 [US3] Implement `code/viz/plots.py` to generate partial dependence plots for top 3 features (FR-011)
- [X] T038 [US3] Implement `code/viz/plots.py` to generate correlation heatmap of descriptors vs. shear modulus (FR-011)
- [X] T040 [US3] **Hypothesis Verification (SC-001)**. **Logic**: 1. Calculate R² of the **FULL model** (all descriptors) on the test set. 2. Calculate R² of a **restricted model** (only δ and ΔHmix) on the test set. 3. Compare the FULL model R² against the baseline (Linear Regression with no descriptors or mean prediction). 4. Output `full_model_r2`, `restricted_model_r2`, and `hypothesis_verified` (boolean: true if full_model_r2 meets the threshold) to `artifacts/hypothesis_report.json`. **Dependency**: Must run after T025.
- [X] T039 [US3] Save all visualizations to `artifacts/` with deterministic filenames. **Logic**: Filename format: `plot_{feature}_{seed}_{report_hash}.png`, where `report_hash` is the SHA-256 hash of the file content of `artifacts/model_report.json` (computed after T029 completes). **Dependency**: Must run strictly after T029, T037, T038.
- [X] T042 [US3] Generate `artifacts/importance_report.json` with ranked descriptors and p-values (FR-009)
- [ ] T050 [US3] **VISUALIZATION INTEGRITY**: Add a validation step in `code/viz/plots.py` to ensure that generated plots (PDPs, heatmaps) are not empty or contain only NaN/Inf values before saving. **Logic**: After generating a plot, check the underlying data array for `np.isnan()` or `np.isinf()`. If detected, raise a `ValueError` indicating "Invalid data for visualization: contains NaN/Inf". This prevents the generation of blank or misleading figures if the upstream model or data is corrupted.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T043 [P] Update `README.md` at repository root. **Content**: Add usage instructions for `make all` and a section explaining the automatic synthetic data fallback mechanism (integrated into T016).
- [X] T044 Code cleanup and refactoring of `code/` modules
- [X] T045 Verify pipeline completes within 6 hours on CPU-only runner (Plan: Performance Goals)
- [X] T046 [P] Run full pipeline end-to-end via `make all` and validate `artifacts/` against contracts
- [X] T047 [P] Run quickstart.md validation if available

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data output from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on trained model from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Ingestion/Cleaning (US1) before Feature Engineering (US1)
- Feature Engineering (US1) before Splitting (US1)
- Training (US2) before Evaluation (US2)
- Evaluation (US2) before Importance Analysis (US3)
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, and US3 can start in parallel if data/model dependencies are mocked or handled via staged execution
- All tests for a user story marked [P] can run in parallel

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint Reminder**: All models must run on CPU-only free-tier runners (limited CPU resources, constrained RAM). No GPU, no 8-bit/4-bit quantization.
- **Data Constraint**: Use code-generated synthetic data based on literature as an **automatic fallback** if real data fetch fails (T016). The pipeline is fully automated and reproducible.
- **Statistical Constraint**: Implement Wilcoxon Signed-Rank Test as primary method (T027), with Corrected Resampled t-test as fallback.
- **Splitting Constraint**: Use **LOFO / GroupKFold Hybrid** (T020/T030). Small families (<2) result in GroupKFold fallback, not HALT.
- **Hypothesis Verification**: T040 explicitly tests SC-001 by measuring the full model's performance and comparing it to the restricted model.
- **Collinearity Control**: VIF > 5 triggers feature pruning or PCA (T019). Ridge is a secondary fallback in T025.
- **Schema Creation**: Schemas are written directly to `contracts/` (T007a/T008a), no temporary files.
- **Critical Revision**: T048 addresses the "Silent Synthetic Fallback" risk by forcing an error if the real data source is empty, preventing accidental fabrication.
- **Critical Revision**: T049 ensures data flow integrity by validating input files before training, preventing empty model training.
- **Critical Revision**: T050 ensures visualization integrity by validating plot data before saving, preventing misleading figures.
