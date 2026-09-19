# Tasks: Quantify Dataset Sparsity Impact

**Input**: Design documents from `/specs/001-quantifying-the-impact-of-dataset-sparsity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 0.5: Spec Resolution (Critical: Align Spec with Plan Deviations)

**Purpose**: Update `spec.md` and `plan.md` to reflect Plan deviations (RSS baseline, LMM, thresholds, API key, 7 sparsity levels) BEFORE implementation begins. This ensures the "Single Source of Truth" is aligned. These tasks MUST complete before Phase 1 (Setup).

- [ ] T054 [US0] Update `spec.md` FR-003 and FR-006 to explicitly define "Representative Stratified Sample (RSS)", the Multiple sparsity levels (1, 2, 5, 10, 25, 50, 100) [UNRESOLVED-CLAIM: c_b67a78d2 — status=not_enough_info], and "Linear Mixed-Effects Modeling (LMM)" with formula `error ~ sparsity_level + (1|seed)`. **Deliverable**: Updated `spec.md` sections FR-003, FR-006. **Verification**: `grep -q "1, 2, 5, 10, 25, 50, 100" spec.md && grep -q "Linear Mixed-Effects" spec.md`. <!-- FAILED: unspecified -->
- [ ] T055 [US0] Update `spec.md` FR-007, SC-003, and US-3 to explicitly include "slope variance < 10%" threshold and LMM references. **Deliverable**: Updated `spec.md` sections FR-007, SC-003, US-3. **Verification**: `grep -q "slope variance < 10%" spec.md`.
- [ ] T056 [US0] Update `spec.md` Assumptions to explicitly require "MP_API_KEY environment variable" and update `plan.md` Technical Context to list 7 sparsity levels. **Deliverable**: Updated `spec.md` Assumptions, `plan.md` Technical Context. **Verification**: `grep -q "MP_API_KEY" spec.md && grep -q "1, 2, 5, 10, 25, 50, 100" plan.md`.

**Checkpoint**: Spec and Plan are now aligned and documented; implementation can proceed without violating "Single Source of Truth".

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure: `mkdir -p code/utils data/raw data/processed data/results data/metadata tests/unit tests/integration docs`. Run `ls -R > project_structure.txt`. **Verification**: Run `cat project_structure.txt` to verify directory existence and generate `project_structure.txt` listing all created directories as the deliverable artifact.
- [X] T002 Create `code/requirements.txt` with pinned versions for all dependencies (pymatgen, matminer, scikit-learn==1.3.0 [UNRESOLVED-CLAIM: c_03f4af0f — status=not_enough_info], statsmodels, pandas==2.0.3 [UNRESOLVED-CLAIM: c_8477cdd8 — status=not_enough_info], numpy, matplotlib, requests). Note: Specific versions are defined in the Plan's "Technical Context" section and must be explicitly listed here.
- [X] T003 [P] Create `code/.pre-commit-config.yaml` with hooks for `ruff` and `black`
- [X] T004 [P] Create `code/config.py` with `RSS_SIZE=30000 [UNRESOLVED-CLAIM: c_1cbc3c80 — status=not_enough_info]` and `SPARSITY_LEVELS=[, 2, 5, 10, 25, 50, 100]` and `LOADERS` config. Note: RSS_SIZE and SPARSITY_LEVELS must be defined here to break circular dependencies in downstream tasks.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T015 Implement `code/utils/logging.py` with `get_logger()` returning a JSON formatter that writes to `data/results/`
- [X] T016 Implement `code/utils/cpu_constraints.py` with `enforce_memory_limit` to enforce a configurable memory constraint and `chunked_iterator()` function. Note: This utility is a blocking prerequisite for all memory-intensive tasks (T035, T039).
- [X] T017 [P] Implement `code/utils/contract_validator.py` with `validate_schema(data, schema_path)` returning bool and error handling
- [X] T018 Create base `MaterialEntry` data class (fields: id, composition, formation_energy, descriptors) and `SparsitySubset` data class (fields: level, seed, percentage, checksum) in `code/utils/data_models.py`
- [X] T019 Setup environment configuration: Create `code/.env.example` with `MP_API_KEY=placeholder` and `code/config.py` with `load_env()` that raises error if `MP_API_KEY` missing. Note: The spec's Assumption regarding 'no authentication barriers' is incorrect; this task implements the required API key configuration per the Plan.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Retrieval and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and engineer features for the Materials Project dataset to create a valid input pool.

**Independent Test**:

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T022 [P] [US1] Unit test `test_api_backoff_retries_on_rate_limit` in `tests/unit/test_data_ingestion.py`
- [X] T023 [P] [US1] Integration test `test_full_ingestion_pipeline` in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [ ] T024 [US1] [FR-001] Implement `code/data_ingestion.py` to download a substantial corpus of entries via Materials Project API (using `MP_API_KEY`), with exponential backoff (limited retry attempts). **Requirement**: Download at least 150,000 entries (FR-001) to provide sufficient buffer for test set and filtering. Output raw data to `data/raw/raw_pool.csv` with columns: `material_id`, `composition`, `formation_energy`, `dft_computed`. **Constraint**: If `MP_API_KEY` is missing or API fails, raise an exception immediately. Do NOT generate synthetic data.
- [ ] T020 [US1] [FR-009] Implement `code/test_split.py` to partition a stratified sample (5000 rows) from `data/raw/raw_pool.csv` (the ENTIRE raw pool, produced by T024) into a **Fixed Test Set** using stratified random sampling based on formation_energy bins (multiple quantile bins) and a fixed random seed. **Input**: Prerequisite: T024. **Output**: `data/processed/test_set.csv` and `data/processed/test_set_indices.csv`. **Note**: This task MUST run BEFORE T026, T027, and T031 to ensure strict independence from the training pool partitioning and to prevent data leakage in imputation statistics. (FR-009, Plan Phase 0.5).
- [ ] T021 [US1] Verify test set independence and log metadata (row count, checksum) to `data/metadata/test_set_metadata.json` (FR-009)
- [ ] T025 [US1] [FR-002] Implement filtering logic in `code/data_ingestion.py` to retain only rows from `data/raw/raw_pool.csv` where `formation_energy` is not null AND `dft_computed` is True. Save to `data/processed/filtered_pool.csv`. **Note**: This task MUST run BEFORE T026 to ensure the filtered pool exists for downstream steps.
- [ ] T026 [P] [US1] [FR-003] Implement descriptor generation in `code/data_ingestion.py` using `matminer` `ElementalPropertyFeatureExtractor` with properties: `atomic_number`, `electronegativity`, `atomic_radius`, reading input from `data/processed/filtered_pool.csv`, outputting to `data/processed/descriptors_pool.csv`. **Constraint**: Explicitly read `data/processed/test_set_indices.csv` (produced by T020) and exclude these indices from the training pool BEFORE calculating imputation statistics. Imputation statistics must be calculated ONLY on the training pool (filtered_pool minus test set), not the test set.
- [ ] T027 [US1] [FR-004] Implement imputation logic in `code/data_ingestion.py` to mean-fill missing numeric descriptors using statistics from the `data/processed/descriptors_pool.csv` (training pool, excluding test set indices); drop rows with >50% missing values [UNRESOLVED-CLAIM: c_0bd76aa7 — status=not_enough_info] and log count to `data/results/ingestion_log.json`. Output final training dataset to `data/processed/full_pool_final.csv`. **Note**: This task replaces T028 which was redundant. **Constraint**: Explicitly read `data/processed/test_set_indices.csv` (produced by T020) and exclude these indices from the dataset before imputation.
- [ ] T031 [US2] [FR-005] Implement `code/sparsity_generation.py` to cap the training pool at a Representative Stratified Sample (RSS) of `RSS_SIZE` entries (read from `config.py`). **Data Lineage**: Read `data/processed/full_pool_final.csv` (produced by T027), explicitly filter out indices found in `data/processed/test_set_indices.csv` (produced by T020), then perform stratified random sampling on the remaining data to create the RSS. **Verification**: Compare distribution of RSS against `full_pool_final.csv` to ensure representativeness. (Plan Phase 1.1). **Output**: `data/processed/rss_pool.csv`.
- [ ] T033 [US2] Implement stratification validation in `code/validate_stratification.py` using Jensen-Shannon divergence and KS-test; log metrics to `data/metadata/stratification_report.json` and do NOT block training (Spec compliance). **Input**: RSS pool from T031.
- [ ] T032 [US2] [FR-003] Implement K-Means clustering on elemental fingerprints in `code/sparsity_generation.py` to generate multiple strictly nested stratified subsets ([deferred], [deferred], [deferred], [deferred], [deferred], [deferred], [deferred] of the RSS pool) preserving chemical space (FR-003). **Input**: Read sparsity levels from `config.py` (SPARSITY_LEVELS) and `data/processed/rss_pool.csv` (produced by T031). **Algorithm**:
 1. Generate the [deferred] set first (copy of `rss_pool.csv`).
 2. For each subsequent level ([deferred], [deferred], etc.), use `pandas.DataFrame.sample(frac=level/100, random_state=seed)` on the INDICES of the previous level's subset to ensure strict nesting.
 3. Use `sklearn.model_selection.StratifiedKFold` logic if stratification is required on a specific target, otherwise use random sampling on indices.
 **Output**: `data/processed/sparsity_1pct.csv`, `data/processed/sparsity_2pct.csv`,..., `data/processed/sparsity_100pct.csv`.
 **Verification**: Assert `len(sparsity_100pct.csv) == RSS_SIZE`. Verify `sparsity_1pct.csv` is a subset of `sparsity_2pct.csv` by comparing checksums or row counts.
- [ ] T034 [US2] Generate `data/metadata/sparsity_<level>_<seed>.json` for each subset containing keys: `seed`, `percentage`, `criteria`, `checksum` (Constitution VII)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Sparsity Subsampling and Model Training (Priority: P1)

**Goal**: Partition data, generate sparsity levels, and train CPU-only models to measure performance degradation.

**Independent Test**: Run `code/test_split.py` and `code/model_training.py` for one sparsity level and verify `data/results/metrics.csv` is generated with RMSE/MAE without CUDA errors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US2] Contract test `test_test_set_independence` in `tests/contract/test_split.py`
- [ ] T030 [P] [US2] Integration test `test_gpr_training_on_30k_subset` in `tests/integration/test_training.py`

### Implementation for User Story 2

- [ ] T035 [US2] [FR-005] Implement `code/model_training.py` to train GPR (RBF kernel, `normalize_y=True`, `max_iter_predict=1000 [UNRESOLVED-CLAIM: c_c1da9146 — status=not_enough_info]`, `alpha=1e-6 [UNRESOLVED-CLAIM: c_a0ddd056 — status=not_enough_info]`) and Random Forest models (n_estimators=100 [UNRESOLVED-CLAIM: c_1c4153ee — status=not_enough_info], default params) on CPU only. **Input**: Read sparsity subsets from `data/processed/sparsity_<level>pct.csv` (produced by T032) and test set from `data/processed/test_set.csv` (produced by T020). **Output**: Save model artifacts and log metrics (RMSE, MAE) to `data/results/metrics.csv`. **Note**: Statistical analysis (LMM) is handled exclusively in T043 (statistical_analysis.py), not here.
- [ ] T036 [US2] Implement k-fold Cross-Validation with multiple independent seeds per sparsity level in `code/model_training.py` (FR-005)
- [ ] T037 [US2] [FR-006] [SC-001] Implement evaluation logic in `code/model_training.py` to score all models against the **Fixed Test Set** (not training subsets) and calculate RMSE, MAE, Predictive Variance, Calibration Slope. Note: Includes Predictive Variance and Calibration Slope per Constitution Principle VI and FR-005, exceeding SC-001.
- [ ] T038 [US2] [SC-001] Log metrics to `data/results/metrics.csv` with columns: `sparsity_level`, `model`, `seed`, `rmse`, `mae`, `variance`, `calibration_slope` (FR-005, SC-001)
- [ ] T039 [US2] Implement chunked processing in `code/model_training.py` with dynamic chunk size to handle OOM errors on large subsets (Edge Case). Note: Utilizes `chunked_iterator()` from T016.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P2)

**Goal**: Perform statistical validation, uncertainty calibration, and generate final research artifacts.

**Independent Test**: Run `code/statistical_analysis.py` and verify `data/results/plots/learning_curve.png` and `data/results/stat_summary.json` exist.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T040 [P] [US3] Unit test `test_lmm_formula` in `tests/unit/test_stats.py`
- [ ] T041 [P] [US3] Integration test `test_full_analysis_pipeline` in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T042 [US3] [SC-002] Implement `code/statistical_analysis.py` to generate learning curves (error vs. dataset size) with error bars using `matplotlib`, ensuring Multiple sparsity levels (ranging from [deferred] to [deferred]) are plotted. **Input**: Sparsity levels are read from `config.py`. **Requirement**: Calculate and plot standard deviation or confidence interval of the metrics as error bars. (FR-006, SC-002)
- [ ] T043 [US3] Implement Linear Mixed-Effects Modeling (LMM) using `statsmodels.MixedLM` with formula `error ~ sparsity_level + (1|seed)` to handle nested sparsity levels. **Input**: Read `metrics.csv` from `data/results/metrics.csv` (produced by T035). **Note**: This implements the Plan's approved deviation from FR-006 (ANOVA) due to nested data structure. Use an unstructured covariance matrix to handle heteroscedasticity (violated sphericity).
- [ ] T044 [US3] [SC-003] Apply pairwise contrasts with Tukey-adjusted p-values to LMM results to report p-values for differences between sparsity levels (threshold p < 0.05). **Note**: This is the correct post-hoc method for LMM, replacing ANOVA's Tukey HSD. Must use an unstructured covariance matrix to handle violated sphericity as per Plan constraints. (FR-006, SC-003).
- [ ] T045 [US3] Implement uncertainty calibration in `code/statistical_analysis.py` to generate calibration slope and predicted vs. squared residuals plots (Constitution VI, FR-005)
- [ ] T046 [US3] Save calibration reports to `data/results/calibration/` as JSON files containing slope and residuals comparison (Constitution VI)
- [ ] T047 [US3] [FR-007] Implement sensitivity analysis in `code/statistical_analysis.py` to measure slope variance between consecutive sparsity levels and log the result to `data/results/slope_variance.json`. **Input**: Derive consecutive level pairs dynamically from the sorted list in `config.py`. **Output**: Save calculated slope variance values to `data/results/slope_variance.json`. Note: This implements the <10% threshold from the Plan, exceeding FR-007's ambiguous requirement.
- [ ] T048 [US3] [FR-008] Generate final report `data/results/final_report.md` summarizing findings as associational evidence, avoiding causal claims (FR-008)
- [ ] T049 [US3] Add validation step in `code/statistical_analysis.py` to assert all random seeds are set to specific values before execution (Constitution I)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050 [P] Update `docs/quickstart.md` with instructions for running the full pipeline on CPU-only CI including `MP_API_KEY` setup
- [ ] T051 Refactor `code/data_ingestion.py` to use the new logging utility from T015
- [ ] T052 Run `pytest tests/ --cov=code --cov-report=xml` to verify all acceptance scenarios
- [ ] T053 Implement validation script `code/validate_artifacts.py` to check for existence of `metrics.csv`, plots, calibration reports, and metadata JSONs in `data/results/`
- [ ] T062 [US0] **Data Integrity**: Add a `try/except` block in `data_ingestion.py` that explicitly raises a `RuntimeError` with a clear message if the Materials Project API download fails, ensuring no synthetic fallback is ever triggered.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Spec Resolution (Phase 0.5)**: No dependencies - MUST be completed BEFORE Phase 1 (Setup) AND Phase 2 (Foundational) to ensure spec deviations are formally approved and foundational code is not written against a stale spec.
- **Setup (Phase 1)**: Depends on Spec Resolution - Must be completed AFTER Spec Resolution.
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all subsequent work until foundation is ready and spec is aligned.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Requires output from US1 (Full Pool)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Requires output from US2 (Metrics)

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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test test_api_backoff_retries_on_rate_limit in tests/unit/test_data_ingestion.py"
Task: "Integration test test_full_ingestion_pipeline in tests/integration/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement data_ingestion.py to download entries"
Task: "Implement descriptor generation using matminer"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0.5: Spec Resolution (Align Spec with Plan)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Spec Resolution + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Spec Resolution + Setup + Foundational together
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
- **Spec Alignment**: Where the Plan mandates a deviation from the Spec (e.g., LMM vs ANOVA, RSS vs Full), the Spec is updated in Phase 0.5 BEFORE implementation tasks run, ensuring the "Single Source of Truth" is maintained.
- **Plan Inconsistency Note**: The Plan's "Technical Context" lists sparsity levels as "20, 30, 40, 50, 100" (5 levels), while Task T032 implements 7 levels (1, 2, 5, 10, 25, 50, 100) as per the Spec's intent. Task T061 resolves this by updating `plan.md`.
- **Data Integrity**: All data loading tasks must fail loudly if the real source is unavailable; synthetic fallbacks are strictly forbidden.
- **Data Flow**: T020 (Test Set) MUST run after T024 (Raw Download) but BEFORE T026 (Descriptors) and T027 (Imputation) to prevent data leakage. T026 and T027 must explicitly exclude test set indices. T020 must operate on the raw pool to ensure independence from filtering.