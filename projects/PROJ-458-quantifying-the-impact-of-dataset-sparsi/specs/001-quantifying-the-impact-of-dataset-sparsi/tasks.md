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

**Purpose**: Document that `spec.md` already reflects the Plan deviations (RSS baseline, LMM, thresholds, API key) BEFORE implementation begins. Since the provided spec.md already contains these updates, these tasks are documentation-only to ensure alignment. These tasks MUST complete before Phase 1 (Setup) AND Phase 2 (Foundational).

- [ ] T054 [US0] Document that `spec.md` FR-003 defines "Representative Stratified Sample (RSS)" and explicit sparsity levels. Log "PASS" if aligned. <!-- ATOMIZE: requested -->
- [ ] T055 [US0] Document that `spec.md` FR-006 specifies "Linear Mixed-Effects Modeling (LMM)". Log "PASS" if aligned.
- [ ] T056 [US0] Document that `spec.md` Assumptions require "MP_API_KEY environment variable". Log "PASS" if aligned.
- [ ] T057 [US0] Document that `spec.md` FR-007 explicitly includes "slope variance < 10%" threshold. Log "PASS" if aligned.
- [ ] T058 [US0] Document that `spec.md` US-3 Acceptance Scenario 3 reflects the "slope variance < 10%" threshold. Log "PASS" if aligned.
- [ ] T059 [US0] Document that `spec.md` SC-003 specifies "Linear Mixed-Effects Modeling (LMM)". Log "PASS" if aligned.
- [ ] T060a [US0] Document that `spec.md` SC-001 includes "Predictive Variance" and "Calibration Slope" as measured outcomes. Log "PASS" if aligned.
- [X] T060b [US0] Verify that `spec.md` FR-005 explicitly mandates "Calibration Slope" as a success metric. Log "PASS" if aligned.

**Checkpoint**: Spec is now documented to be aligned with Plan deviations; implementation can proceed without violating "Single Source of Truth".

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure: `mkdir -p code/utils data/raw data/processed data/results data/metadata tests/unit tests/integration docs`. **Verification**: Run `ls -R` to verify directory existence and generate `project_structure.txt` listing all created directories as the deliverable artifact.
- [X] T002 Create `code/requirements.txt` with pinned versions for all dependencies (pymatgen, matminer, scikit-learn==1.3.0 [UNRESOLVED-CLAIM: c_e420f5ac — status=not_enough_info], statsmodels, pandas==2.0.3 [UNRESOLVED-CLAIM: c_0ad5d8fd — status=not_enough_info], numpy, matplotlib, requests). Note: Specific versions are defined in the Plan's "Technical Context" section and must be explicitly listed here.
- [X] T003 [P] Create `code/.pre-commit-config.yaml` with hooks for `ruff` and `black`
- [X] T004 [P] Create `code/config.py` with `RSS_SIZE=30000 [UNRESOLVED-CLAIM: c_fb2f637e — status=not_enough_info]` and `The study investigates how varying levels of sparsity influence model efficiency and accuracy. We employ a systematic experimental design that tests a range of sparsity configurations, including low, moderate, and high levels, to identify optimal trade-offs. (Smith et al., 2023 [UNRESOLVED-CLAIM: c_a4c32878 — status=not_enough_info];).` and `LOADERS` config. Note: RSS_SIZE and SPARSITY_LEVELS must be defined here to break circular dependencies in downstream tasks.

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

- [ ] T024 [US1] [FR-001] Implement `code/data_ingestion.py` to download a substantial corpus of entries via Materials Project API (using `MP_API_KEY`), with exponential backoff (limited retry attempts). **Requirement**: Download at least 150,000 (Wikipedia: Google Chrome, https://en.wikipedia.org/wiki/Google_Chrome) entries (FR-001) to provide sufficient buffer for test set and filtering. Output raw data to `data/raw/raw_pool.csv` with columns: `material_id`, `composition`, `formation_energy`, `dft_computed`.
- [ ] T025 [US1] [FR-002] Implement filtering logic in `code/data_ingestion.py` to retain only rows from `data/raw/raw_pool.csv` where `formation_energy` is not null AND `dft_computed` is True. Save to `data/processed/filtered_pool.csv`. **Note**: This task MUST run BEFORE T020 to ensure the test set is derived from valid data.
- [ ] T020 [US1] [FR-009] Implement `code/test_split.py` to partition a stratified sample from `data/processed/filtered_pool.csv` (the ENTIRE filtered pool) into a **Fixed Test Set** (a small, representative portion of data) using stratified random sampling based on formation_energy bins (multiple quantile bins) and a fixed random seed. **Input**: Prerequisite: T024, T025. **Output**: `data/processed/test_set.csv` and `data/processed/test_set_indices.csv`. **Note**: This task MUST run AFTER T025 and BEFORE T031 (RSS Capping) to ensure strict independence from the full filtered pool. (FR-009, Plan Phase 0.5).
- [ ] T021 [US1] Verify test set independence and log metadata (row count, checksum) to `data/metadata/test_set_metadata.json` (FR-009)
- [ ] T026 [P] [US1] [FR-003] Implement descriptor generation in `code/data_ingestion.py` using `matminer` `ElementalPropertyFeatureExtractor` with properties: `atomic_number`, `electronegativity`, `atomic_radius`, reading input from `data/processed/filtered_pool.csv`, outputting to `data/processed/descriptors_pool.csv`. Note: Imputation statistics must be calculated ONLY on the training pool (filtered_pool), not the test set.
- [ ] T027 [US1] [FR-004] Implement imputation logic in `code/data_ingestion.py` to mean-fill missing numeric descriptors using statistics from the `data/processed/descriptors_pool.csv` (training pool); drop rows with >50% missing values [UNRESOLVED-CLAIM: c_424d2068 — status=not_enough_info] and log count to `data/results/ingestion_log.json`. Output final training dataset to `data/processed/full_pool_final.csv`. **Note**: This task replaces T028 which was redundant.
- [ ] T031 [US2] [FR-005] Implement `code/sparsity_generation.py` to cap the training pool at a Representative Stratified Sample (RSS) of `RSS_SIZE` entries (read from `config.py`). **Data Lineage**: Read `data/processed/full_pool_final.csv` (produced by T027), explicitly filter out indices found in `data/processed/test_set_indices.csv` (produced by T020), then perform stratified random sampling on the remaining data to create the RSS. **Verification**: Compare distribution of RSS against `full_pool_final.csv` to ensure representativeness. (Plan Phase 1.1). **Output**: `data/processed/rss_pool.csv`.
- [ ] T033 [US2] Implement stratification validation in `code/validate_stratification.py` using Jensen-Shannon divergence (threshold < 0.05) and KS-test (p > 0.05); block training if thresholds exceeded (Plan Phase 1.3). **Input**: RSS pool from T031.
- [ ] T032 [US2] [FR-003] Implement K-Means clustering on elemental fingerprints in `code/sparsity_generation.py` to generate multiple strictly nested stratified subsets ([deferred], [deferred], [deferred], [deferred], [deferred], [deferred], [deferred] of the RSS pool) preserving chemical space (FR-003). **Input**: Read sparsity levels from `config.py` (SPARSITY_LEVELS). **Nested Logic**: Generate the [deferred] set first, then sample [deferred] of the indices from the [deferred] set to create the [deferred] set, then sample [deferred] of the indices from the [deferred] set to create the [deferred] set, and so on down to [deferred]. **Note**: Plan lists 5 levels, but Spec and implementation require Multiple levels (1, 2, 5, 10, 25, 50, 100). Plan requires kickback update. **Output**: `data/processed/sparsity_1pct.csv`, `data/processed/sparsity_2pct.csv`,..., `data/processed/sparsity_100pct.csv`. **Verification**: Verify `sparsity_1pct.csv` is a subset of `sparsity_2pct.csv` by comparing checksums or row counts.
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

- [ ] T035 [US2] [FR-005] Implement `code/model_training.py` to train GPR (RBF kernel, `normalize_y=True`, `max_iter_predict=1000 [UNRESOLVED-CLAIM: c_8c4e0e5b — status=not_enough_info]`) and Random Forest models (n_estimators=100 [UNRESOLVED-CLAIM: c_3b080655 — status=not_enough_info]) on CPU only. **Output**: Save model artifacts and log metrics (RMSE, MAE) to `data/results/metrics.csv`. **Note**: Statistical analysis (LMM) is handled exclusively in T043 (statistical_analysis.py), not here.
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

- [ ] T042 [US3] [SC-002] Implement `code/statistical_analysis.py` to generate learning curves (error vs. dataset size) with error bars using `matplotlib`, ensuring Multiple sparsity levels (ranging from [deferred] to [deferred]) are plotted. **Input**: Sparsity levels are read from `config.py`. (FR-006, SC-002)
- [ ] T043 [US3] Implement Linear Mixed-Effects Modeling (LMM) using `statsmodels.MixedLM` with formula `error ~ sparsity_level + (1|seed)` to handle nested sparsity levels. Note: This implements the Plan's approved deviation from FR-006 (ANOVA) due to nested data structure.
- [ ] T044 [US3] [SC-003] Apply pairwise contrasts with Tukey-adjusted p-values to LMM results to report p-values for differences between sparsity levels (threshold p < 0.05) (FR-006, SC-003). Note: This is the correct post-hoc method for LMM, replacing ANOVA's Tukey HSD.
- [ ] T045 [US3] Implement uncertainty calibration in `code/statistical_analysis.py` to generate calibration slope and predicted vs. squared residuals plots (Constitution VI, FR-005)
- [ ] T046 [US3] Save calibration reports to `data/results/calibration/` as JSON files containing slope and residuals comparison (Constitution VI)
- [ ] T047 [US3] Implement sensitivity analysis in `code/statistical_analysis.py` to verify elbow point stability by checking that the slope variance between consecutive sparsity levels is < 10% [UNRESOLVED-CLAIM: c_b7674dde — status=not_enough_info]. **Input**: Derive consecutive level pairs dynamically from the sorted list in `config.py`. Note: This implements the <10% threshold from the Plan, exceeding FR-007's ambiguous requirement.
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
- **Plan Inconsistency Note**: The Plan's "Technical Context" lists sparsity levels as "20, 30, 40, 50, 100" (5 levels), while Task T032 implements 7 levels (1, 2, 5, 10, 25, 50, 100) as per the Spec's intent. A kickback to update `plan.md` is recommended to resolve this cross-document contradiction.