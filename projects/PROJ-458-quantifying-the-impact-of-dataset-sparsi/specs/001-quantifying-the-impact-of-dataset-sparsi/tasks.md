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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure: `mkdir -p code/utils data/raw data/processed data/results data/metadata tests/unit tests/integration docs`. Run `ls -R > project_structure.txt`. **Verification**: Run `cat project_structure.txt` to verify directory existence and generate `project_structure.txt` listing all created directories as the deliverable artifact.
- [X] T002 Create `code/requirements.txt` with pinned versions for all dependencies: `pymatgen==2024.2.21`, `matminer==0.9.2`, `scikit-learn==1.3.0`, `statsmodels==0.14.0`, `pandas==2.0.3`, `gpytorch==2.0.1`, `numpy`, `matplotlib`, `requests`, `seaborn`. Note: All versions are explicitly pinned with `==` to satisfy Constitution Principle I (Reproducibility).
- [X] T003 [P] Create `code/.pre-commit-config.yaml` with hooks for `ruff` and `black`
- [X] T004 [P] Create `code/config.py` with `The research will investigate how varying sparsity levels affect model performance, employing a systematic experimental design across a range of configurations. References include [Citation].` and `LOADERS` config. Note: RSS_SIZE is NOT hardcoded here; it must be defined dynamically in T005.
- [X] T005 [P] Define RSS_SIZE: Create `code/define_rss_size.py` to perform a quick statistical power analysis or resource check (e.g., estimate memory for a large-scale dataset) and write the final integer value to `data/metadata/rss_config.json` with key `rss_size`. **Verification**: Ensure `data/metadata/rss_config.json` exists and contains a valid integer. This task MUST complete before T031.

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

- [X] T024 [US1] [FR-001] Implement `code/data_ingestion.py` to download a substantial corpus of entries via Materials Project API (using `MP_API_KEY`, with exponential backoff with sufficient max retries to guarantee the 150k target). **Requirement**: Download at least 150,000 (Wikipedia: Google Chrome, https://en.wikipedia.org/wiki/Google_Chrome) entries (FR-001) to provide sufficient buffer for test set and filtering. Output raw data to `data/raw/raw_pool.csv` with columns: `material_id`, `composition`, `formation_energy`, `dft_computed`. **Constraint**: If `MP_API_KEY` is missing or API fails, raise an exception immediately. Do NOT generate synthetic data.
- [X] T020 [US1] [FR-009] Implement `code/test_split.py` to partition a stratified sample of size defined in `data/metadata/test_config.json` from `data/raw/raw_pool.csv` (the ENTIRE raw pool, produced by T024) into a **Fixed Test Set** using stratified random sampling based on formation_energy bins. **Algorithm**: Use `pd.qcut` with multiple quantile bins on `formation_energy` to define strata, then sample the specified number of rows stratified by these bins with a fixed random seed. **Input**: Prerequisite: T024. **Output**: `data/processed/test_set.csv` and `data/processed/test_set_indices.csv`. **Verification**: Check existence of `data/raw/raw_pool.csv` before proceeding. **CRITICAL**: If `data/raw/raw_pool.csv` is missing, raise a `RuntimeError` immediately. Do NOT proceed, do NOT generate synthetic data, do NOT hang. This enforces the 'fail loudly' rule. **Note**: This task MUST run BEFORE T025, T026, T027, and T031 to ensure strict independence from the training pool partitioning and to prevent data leakage in imputation statistics. (FR-009, Plan Phase 0.5).
- [X] T021 [US1] Verify test set independence and log metadata (row count, checksum) to `data/metadata/test_set_metadata.json` (FR-009)
- [ ] T025 [US1] [FR-002] Implement filtering logic in `code/data_ingestion.py` to retain only rows from `data/raw/raw_pool.csv` where `formation_energy` is not null AND `dft_computed` is True. Save to `data/processed/filtered_pool.csv`. **Note**: This task MUST run AFTER T020 to ensure the test set is already separated from the pool being filtered.
- [ ] T026 [P] [US1] [FR-003] Implement descriptor generation in `code/data_ingestion.py` using `matminer` `ElementalPropertyFeatureExtractor` with properties: `atomic_number`, `electronegativity`, `atomic_radius`, reading input from `data/processed/filtered_pool.csv`, outputting to `data/processed/descriptors_pool.csv`. **Constraint**: Explicitly read `data/processed/test_set_indices.csv` (produced by T020) and exclude these indices from the training pool BEFORE calculating imputation statistics. Imputation statistics must be calculated ONLY on the training pool (filtered_pool minus test set), not the test set. **Prerequisite**: T020. **Verification**: Check existence of `data/processed/test_set_indices.csv` before proceeding. If missing, abort with error. Additionally, verify that `descriptors_pool.csv` contains the expected columns and non-null counts. <!-- ATOMIZE: requested -->
- [ ] T027 [US1] [FR-004] Implement imputation logic in `code/data_ingestion.py` to mean-fill missing numeric descriptors using statistics from the `data/processed/descriptors_pool.csv` (training pool, excluding test set indices); drop rows with >50% missing values and log count to `data/results/ingestion_log.json`. Output final training dataset to `data/processed/full_pool_final.csv`. **Note**: This task replaces T028 which was redundant. **Constraint**: Explicitly read `data/processed/test_set_indices.csv` (produced by T020) and exclude these indices from the dataset before imputation. **Prerequisite**: T020.
- [ ] T031 [US2] [FR-005] Implement `code/sparsity_generation.py` to cap the training pool at a Representative Stratified Sample (RSS) of `rss_size` entries (read from `data/metadata/rss_config.json` produced by T005). **Data Lineage**: Read `data/processed/full_pool_final.csv` (produced by T027), explicitly filter out indices found in `data/processed/test_set_indices.csv` (produced by T020), then perform stratified random sampling on the remaining data to create the RSS. **Verification**: Compare distribution of RSS against `full_pool_final.csv` to ensure representativeness. (Plan Phase 1.1). **Output**: `data/processed/rss_pool.csv`. **Prerequisite**: T020, T027, T005.
- [ ] T033 [US2] Implement stratification validation in `code/validate_stratification.py` using Jensen-Shannon divergence and KS-test; log metrics to `data/metadata/stratification_report.json`. **Constraint**: If validation fails (divergence > 0.05), raise an error and block further execution to ensure data hygiene. **Input**: RSS pool from T031.
- [ ] T032a [US2] [FR-003] Implement K-Means clustering on elemental fingerprints in `code/sparsity_generation.py` to generate the **[deferred] sparsity baseline (RSS)** as a stratified subset. **Input**: Read `data/processed/rss_pool.csv` (produced by T031). **Output**: `data/processed/sparsity_100pct.csv`. **Verification**: Assert `len(sparsity_100pct.csv) == rss_size`. **Prerequisite**: T031. <!-- FAILED: unspecified -->
- [ ] T032b [US2] [FR-005] Implement nested subset generation in `code/sparsity_generation.py` to generate strictly nested stratified subsets from the RSS. **Algorithm**: Generate levels in descending order: full (already generated in T032a), and progressively reduced fractions. For each level X% (where X < 100), sample X% of the *indices from the immediately larger parent set* (e.g., [deferred] is sampled from [deferred], [deferred] is sampled from [deferred]). This ensures strict nesting: [deferred] ⊂ [deferred] ⊂ [deferred] ⊂ [deferred] ⊂ [deferred] ⊂ [deferred] ⊂ [deferred]. **Output**: `data/processed/sparsity_1pct.csv`, `data/processed/sparsity_2pct.csv`,..., `data/processed/sparsity_50pct.csv`. **Verification**: Assert `sparsity_1pct.csv` is a strict subset of `sparsity_2pct.csv`, which is a subset of `sparsity_5pct.csv`, etc., by comparing row counts and indices. **Prerequisite**: T032a.
- [ ] T032c [US2] Verify strict nesting of all sparsity subsets. **Input**: All `sparsity_<level>pct.csv` files. **Output**: `data/metadata/nesting_verification.json` with boolean `is_strictly_nested`. **Prerequisite**: T032b.
- [ ] T034 [US2] Generate `data/metadata/sparsity_<level>_<seed>.json` for each subset containing keys: `seed`, `percentage`, `criteria`, `checksum` (Constitution VII). **Prerequisite**: T032b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Sparsity Subsampling and Model Training (Priority: P1)

**Goal**: Partition data, generate sparsity levels, and train CPU-only models to measure performance degradation.

**Independent Test**: Run `code/test_split.py` and `code/model_training.py` for one sparsity level and verify `data/results/metrics.csv` is generated with RMSE/MAE without CUDA errors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US2] Contract test `test_test_set_independence` in `tests/contract/test_split.py`
- [X] T030 [P] [US2] Integration test `test_gpr_training_on_30k_subset` in `tests/integration/test_training.py`

### Implementation for User Story 2

- [ ] T035 [US2] [FR-005] Implement `code/model_training.py` to train GPR (RBF kernel, `normalize_y=True`, `max_iter_predict=1000`, `alpha=1e-6`) and Random Forest models (n_estimators=100, default params) on CPU only. **Input**: Read sparsity subsets from `data/processed/sparsity_<level>pct.csv` (produced by T032b) and test set from `data/processed/test_set.csv` (produced by T020). **Output**: Save model artifacts AND calculate RMSE, MAE, Predictive Variance, Calibration Slope. Append these metrics (sparsity_level, seed, model, rmse, mae, variance, calibration_slope) to `data/results/metrics.csv`. **CRITICAL**: The 'rmse' column represents the 'error' metric required for the LMM formula `error ~ sparsity_level`. **Prerequisite**: T020, T032b. **Note**: Statistical analysis (LMM) is handled exclusively in T043 (statistical_analysis.py), not here. **Note**: Phase 4 cannot begin until Phase 3's data generation tasks (specifically T032b) are complete and verified.
- [ ] T036 [US2] Implement k-fold Cross-Validation with multiple independent seeds per sparsity level in `code/model_training.py` (FR-005). **Input**: Model artifacts from T035. **Output**: CV metrics.
- [ ] T037 [US2] [FR-006] [SC-001] Implement evaluation logic in `code/model_training.py` to score all models against the **Fixed Test Set** (not training subsets) and calculate RMSE, MAE, Predictive Variance, Calibration Slope. **Output**: Generate `data/results/calibration_report.json` containing the calibration slope and a comparison of predicted variance to squared residuals (Constitution Principle VI). **Input**: Model artifacts and CV metrics. **Prerequisite**: T035. **Note**: This task is the SOLE generator of `calibration_report.json`. **Verification**: Ensure `calibration_slope` is present in both `calibration_report.json` and `metrics.csv`.
- [ ] T038 [US2] [SC-001] Finalize `data/results/metrics.csv` with columns: `sparsity_level`, `model`, `seed`, `rmse`, `mae`, `variance`, `calibration_slope` (FR-005, SC-001). **Input**: Evaluation results from T035. **Action**: If T035 wrote the file, ensure it is complete; if T035 only appended, finalize the file. **Prerequisite**: T035.
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

- [ ] T042 [US3] [SC-002] Implement `code/statistical_analysis.py` to generate learning curves (error vs. dataset size) with error bars using `matplotlib`, ensuring Multiple sparsity levels (ranging from low to high) are plotted. **Input**: Sparsity levels are read from `SPARSITY_LEVELS` in `config.py`. **Requirement**: Calculate and plot standard deviation or confidence interval of the metrics as error bars. (FR-006, SC-002). **Verification**: Ensure `SPARSITY_LEVELS` in `config.py` matches the generated subset filenames.
- [ ] T043a [US3] [FR-006] Implement Linear Mixed-Effects Modeling (LMM) using `statsmodels.MixedLM` with formula `error ~ sparsity_level + (1|seed)` to handle nested sparsity levels. **Input**: Read `metrics.csv` from `data/results/metrics.csv` (produced by T038). **Note**: This implements the Plan's approved deviation from FR-006 (ANOVA) due to nested data structure. Use an unstructured covariance matrix as an implementation choice to handle heteroscedasticity (violated sphericity). **Output**: Save LMM results and **fixed-effect predictions (predicted_mean per sparsity level)** to `data/results/lmm_fixed_effects.json`. Log justification for unstructured covariance choice to `data/metadata/lmm_validation.json`. **Prerequisite**: T038.
- [ ] T043b [US3] Validate covariance structure and heteroscedasticity handling in LMM results. **Input**: LMM results from T043a. **Output**: Log validation status to `data/metadata/lmm_validation.json`. **Prerequisite**: T043a.
- [ ] T044 [US3] [SC-003] Apply pairwise contrasts with Tukey-adjusted p-values to LMM results to report p-values for differences between sparsity levels (threshold p < 0.05). **Note**: This is the correct post-hoc method for LMM, replacing ANOVA's Tukey HSD. Must use an unstructured covariance matrix to handle violated sphericity as per Plan constraints. (FR-006, SC-003). **Prerequisite**: T043a.
- [ ] T045 [US3] Implement uncertainty calibration validation in `code/statistical_analysis.py` to verify the generation of `data/results/calibration_report.json` (generated by T037) and generate plots of predicted variance vs squared residuals (Constitution VI, FR-005). **Input**: `data/results/calibration_report.json` from T037. **Note**: This task consumes the report; it does not generate it.
- [ ] T045a [US3] [Constitution VI] Validate the existence and content of `data/results/calibration_report.json` generated by T037. **Input**: `data/results/calibration_report.json`. **Output**: Log validation status. **Prerequisite**: T037. **Note**: This task does NOT generate the report; it validates T037's output.
- [ ] T046 [US3] Save calibration reports to `data/results/calibration/` as JSON files containing slope and residuals comparison (Constitution VI)
- [ ] T047 [US3] [FR-007] Implement sensitivity analysis in `code/statistical_analysis.py` to measure slope variance between consecutive sparsity levels and log the result to `data/results/slope_variance.json`. **Algorithm**: 1. Read `data/results/lmm_fixed_effects.json` (produced by T043a) to extract the 'predicted_mean' for each sparsity level (key path: `predicted_mean`). 2. Calculate the 'slope' as the finite difference between consecutive levels: `slope_i = (predicted_mean_{i+1} - predicted_mean_i) / (level_{i+1} - level_i)`. 3. Calculate the variance of these slopes across all consecutive pairs. 4. Determine if `variance < 0.10 `. **Input**: `data/results/lmm_fixed_effects.json`. **Output**: Save calculated slope variance values AND a boolean `threshold_met` to `data/results/slope_variance.json`. Note: This implements the <10% threshold from the Plan, exceeding FR-007's ambiguous requirement. **Prerequisite**: T043a.
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

- **Setup (Phase 1)**: No dependencies - MUST be completed first.
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all subsequent work until foundation is ready.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Requires output from US1 (Full Pool)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Requires output from US2 (Metrics)

### Within Each User Story (Artifact Flow)

- **T024** (Raw Download) -> **T020** (Test Set) -> **T026/T027** (Descriptors/Imputation) -> **T031** (RSS) -> **T032a** ([deferred] Baseline) -> **T032b** (Nested Subsets) -> **T032c** (Nesting Verification)
- **T035** (Training) depends on **T020** (Test Set) and **T032b** (Sparsity Subsets)
- **T038** (Metrics Finalization) depends on **T035** (Training/Evaluation)
- **T043a** (LMM) depends on **T038** (Metrics)
- **T047** (Sensitivity) depends on **T043a** (LMM Predictions)

### Explicit Dependency Chains (Critical for Execution)

- **T024** -> **T020**: T020 requires `data/raw/raw_pool.csv` from T024. T020 must verify file existence before running. **CRITICAL**: If T024 fails or file is missing, T020 must raise `RuntimeError` immediately.
- **T020** -> **T026/T027**: T026/T027 require `data/processed/test_set_indices.csv` from T020 to exclude test indices.
- **T020** -> **T031**: T031 requires `data/processed/test_set_indices.csv` from T020 to filter RSS.
- **T005** -> **T031**: T031 requires `data/metadata/rss_config.json` from T005.
- **T031** -> **T032a**: T032a requires `data/processed/rss_pool.csv` from T031.
- **T032a** -> **T032b**: T032b requires `data/processed/sparsity_100pct.csv` from T032a for nested sampling.
- **T032b** -> **T032c**: T032c requires all sparsity subsets from T032b for verification.
- **T020** + **T032b** -> **T035**: T035 requires test set (T020) and sparsity subsets (T032b).
- **T035** -> **T038**: T038 finalizes metrics.csv generated/appended by T035.
- **T038** -> **T043a**: T043a requires `data/results/metrics.csv` from T038.
- **T043a** -> **T043b**: T043b requires LMM results from T043a.
- **T043a** -> **T047**: T047 requires `data/results/lmm_fixed_effects.json` (predicted_mean) from T043a.

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

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
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
- **Data Integrity**: All data loading tasks must fail loudly if the real source is unavailable; synthetic fallbacks are strictly forbidden.
- **Data Flow**: T024 -> T020 -> T026/T027 -> T031 -> T032 -> T035 -> T038 -> T043 -> T047 is the critical path.
- **Strict Nesting**: T032b generates subsets by sampling from the *immediately larger parent set* to ensure [deferred] ⊂ [deferred] ⊂... ⊂ [deferred].
- **Artifact Ownership**: T037 generates `calibration_report.json`; T045/T045a validate it. T035 writes initial metrics; T038 finalizes.
- **Stage Expectation**: The unimplemented status of tasks (marked `- [ ]`) is expected at the 'tasked' stage and does not indicate a failure to plan. The tasks are defined to cover all FRs/SCs, and their implementation will proceed as the project advances.
- **Note on T001**: T001 is a single logical unit but could be split into 'Create directories' and 'Generate listing' for better atomicity if desired.