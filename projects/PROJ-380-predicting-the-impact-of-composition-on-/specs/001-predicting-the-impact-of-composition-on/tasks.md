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
- [ ] T005 [P] Initialize `utils/config.py` with random seeds and path constants

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 [P] Implement `utils/provenance.py` for full checksum generation logic (including file hashing and `state/...yaml` recording) per Constitution Principle V. This module must provide a `record_artifact(file_path, state_file)` function that computes SHA-256 and writes to the state YAML.
- [ ] T007 Create `contracts/bmg_entry.schema.yaml` defining the BMGEntry schema (source, composition, modulus)
- [ ] T008 Create `contracts/model_output.schema.yaml` defining the ModelPerformance schema
- [ ] T009 Setup `data/` directory structure (`raw/`, `processed/`, `artifacts/`)
- [X] T010 [P] Implement `code/__init__.py` and basic logging configuration
- [ ] T011 [US1] Implement `code/data/synthetic_generator.py` to generate a Synthetic BMG Dataset based on verified literature parameters (Inoue et al. 2003, Miracle 2006) for common BMG families (Zr-based, Pd-based, Mg-based). **Logic**: Use specific ranges: atomic radii within a moderate interval, electronegativity 1.6-2.4, shear modulus 30-80 GPa. [UNRESOLVED-CLAIM: c_7f4d6003 — status=not_enough_info] Generate data with a fixed `random_state=42 `. Output to `data/raw/synthetic_bmg_seed.csv`. Invoke `utils/provenance.py` (T006) to record checksums immediately after generation. **Dependency**: Must run strictly after T006 completes.

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

- [ ] T016 [US1] Implement `code/data/ingest.py` to load data. **Logic**: First, attempt to fetch data from the Materials Project API using the configured API key. If the fetch fails (e.g., API unavailable or no BMG data), fall back to reading `data/raw/synthetic_bmg_seed.csv`. Validate schema against `contracts/bmg_entry.schema.yaml`. Invoke `utils/provenance.py` (T006) to record checksums. <!-- FAILED: unspecified -->
- [X] T017 [US1] Implement `code/data/clean.py` to filter for "bulk metallic glass" phase and standardize units (FR-002, FR-003)
- [X] T018 [US1] Implement `code/data/features.py` to calculate δ, ΔHmix, VEC, and electronegativity difference using `mendeleev` (FR-003)
- [X] T019 [US1] Calculate VIF in `code/data/features.py`. **Logic**: Calculate VIF for each descriptor. {{claim:c_68ab6cc0}} (Wikidata Q113106917, https://www.wikidata.org/wiki/Q113106917) If < 2 features remain, flag for PCA (variance threshold > 95%). Output a list of retained features. **Note**: Do NOT implement Ridge fallback here; that belongs in T025.
- [ ] T020 [US1] Implement `code/data/split.py` to perform hybrid stratified train/test split by alloy family (FR-004). **Logic**: Define 'small' families as those with <10 samples. [UNRESOLVED-CLAIM: c_6b74dffa — status=not_enough_info] For families with >=10 samples, use Leave-One-Family-Out (LOFO). For families with <10 samples, use GroupKFold (k=5) to ensure they are included in the validation set. Do NOT exclude any families.
- [X] T021 [US1] Add validation to ensure no missing values in target variable after cleaning and filtering

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Performance Evaluation (Priority: P2)

**Goal**: Train Linear Regression, Random Forest, and Gradient Boosting models with grid search (≤50 combos), evaluate via R²/MAE/RMSE, and perform statistical comparison (Corrected Resampled t-test OR Paired Permutation Test) and hybrid LOFO/GroupKFold validation.

**Independent Test**: The training script can be tested by running it on a fixed subset of the data and verifying that it outputs a JSON report containing metrics and best hyperparameters.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US2] Unit test for grid search limit (≤50 combinations) in `tests/unit/test_train.py`
- [X] T023 [P] [US2] Unit test for hybrid LOFO/GroupKFold split logic in `tests/unit/test_split.py`
- [ ] T024 [US2] Integration test for model evaluation and statistical comparison in `tests/integration/test_model_eval.py`

### Implementation for User Story 2

- [X] T025 [US2] Implement `code/models/train.py` to train Linear Regression, Random Forest, and Gradient Boosting (FR-005). **Logic**: If VIF > 5 is detected from T019, apply Ridge Regression as a fallback to handle collinearity.
- [X] T026 [US2] Implement grid search with 5-fold CV and ≤50 combinations limit in `code/models/train.py` (FR-006, Plan Constraints)
- [ ] T027 [US2] Implement statistical comparison for model evaluation (FR-007). **Logic**: Perform Shapiro-Wilk test on residuals. If p < 0.05 (non-normal), use Wilcoxon Signed-Rank Test. Otherwise, use Corrected Resampled t-test OR Paired Permutation Test (choose one based on dataset size).
- [X] T028 [US2] Implement LOFO cross-validation and GroupKFold for small families in `code/models/evaluate.py` (FR-008)
- [ ] T029 [US2] Generate `artifacts/model_report.json` containing keys: `metrics: {R2 (float), MAE (float), RMSE (float)}`, `hyperparameters: {...}`, `statistical_test: {method (string), p_value (float), confidence_interval (list[float])}`. **Schema**: Must match `contracts/model_output.schema.yaml` (FR-007). **Dependency**: Must run strictly after T027 and T026.
- [X] T030 [US2] Implement hybrid Leave-One-Family-Out (LOFO) for large families and GroupKFold for small families in `code/models/evaluate.py` (FR-008, Plan: Complexity Tracking). **Logic**: Re-use the splitter logic defined in T020.
- [ ] T031 [US2] Add error handling for small alloy families (empty folds) during splitting. **Logic**: Families with <10 samples are handled via the hybrid LOFO/GroupKFold strategy defined in T020 (GroupKFold k=5). Do NOT exclude them.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance Analysis and Visualization (Priority: P3)

**Goal**: Extract feature importances, perform permutation testing to assess predictive contribution, and generate PDPs and correlation heatmaps.

**Independent Test**: The analysis script can be tested by running it on the trained model and verifying that it outputs a JSON file with importance scores and generates the required plot files.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [US3] Unit test for permutation importance calculation in `tests/unit/test_importance.py`
- [X] T033 [P] [US3] Unit test for plot generation in `tests/unit/test_viz.py`

### Implementation for User Story 3

- [X] T034 [US3] Implement `code/models/importance.py` to extract feature importances from best tree-based model (FR-009)
- [X] T035 [US3] Implement permutation importance testing with a sufficient number of permutations for statistical stability. in `code/models/importance.py` (FR-009, Spec US-3). **Dependency**: Must run after US2 (T025/T026) completes.
- [ ] T036 [US3] Ensure results are explicitly labeled as "predictive contribution within the trained model" (not 'statistical significance') in output JSON and plot captions (FR-009)
- [X] T037 [US3] Implement `code/viz/plots.py` to generate partial dependence plots for top 3 features (FR-011)
- [X] T038 [US3] Implement `code/viz/plots.py` to generate correlation heatmap of descriptors vs. shear modulus (FR-011)
- [ ] T039 [US3] Save all visualizations to `artifacts/` with deterministic filenames. **Logic**: Filename format: `plot_{feature}_{seed}_{report_hash}.png`, where `report_hash` is the SHA-256 hash of the file content of `artifacts/model_report.json`. **Dependency**: Must run strictly after T029.
- [ ] T040 [US3] Generate `artifacts/importance_report.json` with ranked descriptors and p-values (FR-009)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Update `README.md` at repository root. **Content**: Add usage instructions for `make all` and a section explaining the synthetic data fallback mechanism.
- [ ] T042 Code cleanup and refactoring of `code/` modules
- [ ] T043 Verify pipeline completes within 6 hours on CPU-only runner (Plan: Performance Goals)
- [ ] T044 [P] Run full pipeline end-to-end via `make all` and validate `artifacts/` against contracts
- [ ] T045 [P] Run quickstart.md validation if available

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
- **Data Constraint**: Use code-generated synthetic data based on literature as a fallback ONLY if real data fetch fails. Synthetic generation is handled by T011.
- **Statistical Constraint**: Implement Corrected Resampled t-test OR Paired Permutation Test (T027). Wilcoxon is fallback ONLY for non-normal data (Shapiro-Wilk p < 0.05).
- **Splitting Constraint**: Use hybrid LOFO/GroupKFold (T020/T030) to handle small families. T020/T031 handle all families (LOFO for >=10, GroupKFold for <10).