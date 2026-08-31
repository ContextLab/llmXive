# Tasks: Quantify Dataset Sparsity Impact

**Input**: Design documents from `/specs/001-quantifying-the-impact-of-dataset-sparsity/`
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

## Phase 0.5: Spec Resolution (Critical: Align Spec with Plan Deviations)

**Purpose**: Formally update `spec.md` to reflect Plan deviations (RSS baseline, LMM, thresholds) BEFORE implementation begins. This resolves the "Single Source of Truth" violation by ensuring the Spec matches the implementation strategy. These tasks MUST complete before Phase 1 (Setup) AND Phase 2 (Foundational) to prevent foundational code from being written against a stale spec.

- [ ] T054 [US0] Update `spec.md` FR-003 to replace "full dataset (150k)" with "Representative Stratified Sample (RSS) of [deferred] entries" to match Plan Phase 1.1.
- [ ] T055 [US0] Update `spec.md` FR-006 to replace "Repeated Measures ANOVA" with "Linear Mixed-Effects Modeling (LMM)" to match Plan's nested data structure handling.
- [ ] T056 [US0] Update `spec.md` Assumptions to replace "no authentication barriers" with "Requires MP_API_KEY environment variable" to match Plan and T019.
- [ ] T057 [US0] Update `spec.md` FR-007 to explicitly include "slope variance < 10%" threshold for trend stability verification AND update `spec.md` US-3 Acceptance Scenario 3 to reflect the 10% threshold (resolving internal 5% vs [deferred] contradiction).
- [ ] T058 [US0] Update `spec.md` SC-003 to replace "Repeated Measures ANOVA" with "Linear Mixed-Effects Modeling (LMM)" to match FR-006 update.
- [ ] T059 [US0] Update `spec.md` SC-001 to explicitly include "Predictive Variance" and "Calibration Slope" as measured outcomes alongside RMSE and MAE. ALSO update `spec.md` FR-005 to explicitly mandate "Calibration Slope" as a success metric to close scope creep.

**Checkpoint**: Spec is now aligned with Plan deviations; implementation can proceed without violating "Single Source of Truth".

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure: `mkdir -p code/utils data/raw data/processed data/results data/metadata tests/unit tests/integration docs`
- [X] T002 Create `code/requirements.txt` with pinned versions for all dependencies (pymatgen, matminer, scikit-learn, statsmodels, pandas, numpy, matplotlib, requests). Note: Specific versions are defined in the Plan's "Technical Context" section.
- [X] T003 [P] Create `code/.pre-commit-config.yaml` with hooks for `ruff` and `black`

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

- [ ] T024 [US1] Implement `code/data_ingestion.py` to download a substantial corpus of entries via Materials Project API (using `MP_API_KEY`), with exponential backoff (limited retry attempts). Assert the downloaded count meets the `RSS_SIZE` configuration (default [deferred]) or fails. Output raw data to `data/raw/raw_pool.csv` with columns: `material_id`, `composition`, `formation_energy`, `dft_computed`.
- [ ] T020 [US1] [P] Implement `code/test_split.py` to partition a stratified sample from `data/raw/raw_pool.csv` (the ENTIRE raw pool) into a **Fixed Test Set** (a small, representative proportion of data) using stratified random sampling based on formation_energy bins and a fixed random seed. Output to `data/processed/test_set.csv` and `data/processed/test_set_indices.csv`. (FR-009, Plan Phase 0.5). Note: This task MUST run BEFORE T025 (Filtering) and T031 (RSS Capping) to ensure strict independence from the full raw pool.
- [ ] T021 [US1] [P] Verify test set independence and log metadata (row count, checksum) to `data/metadata/test_set_metadata.json` (FR-009)
- [ ] T025 [US1] Implement filtering logic in `code/data_ingestion.py` to retain only rows where `formation_energy` is not null and `dft_computed` is True (excluding indices in `data/processed/test_set_indices.csv`), saving to `data/processed/filtered_pool.csv`.
- [ ] T026 [US1] [P] Implement descriptor generation in `code/data_ingestion.py` using `matminer` `ElementalPropertyFeatureExtractor` with properties: `atomic_number`, `electronegativity`, `atomic_radius`, outputting to `data/processed/descriptors_pool.csv`. Note: Imputation statistics must be calculated ONLY on the training pool (filtered_pool), not the test set.
- [ ] T027 [US1] Implement imputation logic in `code/data_ingestion.py` to mean-fill missing numeric descriptors using statistics from the training pool; drop rows with >50% missing values and log count to `data/results/ingestion_log.json`. Output final training dataset to `data/processed/full_pool_final.csv`.
- [X] T028 [US1] Save cleaned full pool to `data/processed/full_pool_final.csv` with SHA-256 checksum generation (write to `data/processed/full_pool_final.csv.sha256`) (Constitution III)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Sparsity Subsampling and Model Training (Priority: P1)

**Goal**: Partition data, generate sparsity levels, and train CPU-only models to measure performance degradation.

**Independent Test**: Run `code/test_split.py` and `code/model_training.py` for one sparsity level and verify `data/results/metrics.csv` is generated with RMSE/MAE without CUDA errors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US2] Contract test `test_test_set_independence` in `tests/contract/test_split.py`
- [X] T030 [P] [US2] Integration test `test_gpr_training_on_30k_subset` in `tests/integration/test_training.py`

### Implementation for User Story 2

- [X] T031 [US2] Implement `code/sparsity_generation.py` to cap the training pool at a Representative Stratified Sample (RSS) of [deferred] entries (config key RSS_SIZE=30000) by reading from `data/processed/filtered_pool.csv` (EXCLUDING test set indices). Implement stratified random sampling based on formation_energy bins. (Plan Phase 1.1). Note: This task depends on T020 (Test Set Partitioning) being complete.
- [X] T032 [US2] Implement K-Means clustering on elemental fingerprints in `code/sparsity_generation.py` to generate 7 stratified subsets ([deferred], [deferred], [deferred], [deferred], [deferred], [deferred], [deferred] of the 30k RSS pool) preserving chemical space (FR-003). Note: The 7 levels correspond to the Plan's "Technical Context" section.
- [X] T033 [US2] Implement stratification validation in `code/validate_stratification.py` using Jensen-Shannon divergence (threshold < 0.05) and KS-test (p > 0.05); block training if thresholds exceeded (Plan Phase 1.3)
- [ ] T034 [US2] Generate `data/metadata/sparsity_<level>_<seed>.json` for each subset containing keys: `seed`, `percentage`, `criteria`, `checksum` (Constitution VII)
- [X] T035 [US2] Implement `code/model_training.py` to train GPR (RBF kernel, `normalize_y=True`, `max_iter_predict=1000`) and Random Forest models (n_estimators=100) on CPU only. Implement Linear Mixed-Effects Modeling (LMM) using `statsmodels.MixedLM` for statistical analysis as per Plan 'Note on Spec Contradictions' (FR-010).
- [X] T036 [US2] Implement k-fold Cross-Validation with multiple independent seeds per sparsity level in `code/model_training.py` (FR-005)
- [X] T037 [US2] Implement evaluation logic in `code/model_training.py` to score all models against the **Fixed Test Set** (not training subsets) and calculate RMSE, MAE, Predictive Variance, Calibration Slope. Note: Includes Predictive Variance and Calibration Slope per Constitution Principle VI and FR-005, exceeding SC-001.
- [ ] T038 [US2] Log metrics to `data/results/metrics.csv` with columns: `sparsity_level`, `model`, `seed`, `rmse`, `mae`, `variance`, `calibration_slope` (FR-005, SC-001)
- [X] T039 [US2] Implement chunked processing in `code/model_training.py` with dynamic chunk size to handle OOM errors on large subsets (Edge Case)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P2)

**Goal**: Perform statistical validation, uncertainty calibration, and generate final research artifacts.

**Independent Test**: Run `code/statistical_analysis.py` and verify `data/results/plots/learning_curve.png` and `data/results/stat_summary.json` exist.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T040 [P] [US3] Unit test `test_lmm_formula` in `tests/unit/test_stats.py`
- [X] T041 [P] [US3] Integration test `test_full_analysis_pipeline` in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [X] T042 [US3] Implement `code/statistical_analysis.py` to generate learning curves (error vs. dataset size) with error bars using `matplotlib`, ensuring ALL 7 sparsity levels ([deferred], [deferred], [deferred], [deferred], [deferred], [deferred], [deferred]) are plotted (FR-006, SC-002)
- [X] T043 [US3] Implement Linear Mixed-Effects Modeling (LMM) using `statsmodels.MixedLM` with formula `error ~ sparsity_level + (1|seed)` to handle nested sparsity levels. Note: This implements the Plan's approved deviation from FR-006 (ANOVA) due to nested data structure.
- [X] T044 [US3] Apply Tukey post-hoc test to report p-values for differences between sparsity levels (threshold p < 0.05) (FR-006, SC-003)
- [X] T045 [US3] Implement uncertainty calibration in `code/statistical_analysis.py` to generate calibration slope and predicted vs. squared residuals plots (Constitution VI, FR-005)
- [ ] T046 [US3] Save calibration reports to `data/results/calibration/` as JSON files containing slope and residuals comparison (Constitution VI)
- [ ] T047 [US3] Implement sensitivity analysis in `code/statistical_analysis.py` to verify elbow point stability by checking that the slope variance between consecutive sparsity levels ([deferred] vs [deferred], [deferred] vs [deferred], [deferred] vs [deferred], [deferred] vs [deferred], [deferred] vs [deferred], [deferred] vs [deferred]) is < 10%. Note: This implements the <10% threshold from the Plan, exceeding FR-007's ambiguous requirement.
- [ ] T048 [US3] Generate final report `data/results/final_report.md` summarizing findings as associational evidence, avoiding causal claims (FR-008)
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
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
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