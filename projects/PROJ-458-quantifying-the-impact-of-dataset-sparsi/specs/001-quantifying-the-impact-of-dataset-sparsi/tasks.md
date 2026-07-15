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

- [ ] T001 Create project structure: `mkdir -p code/utils data/raw data/processed data/results data/metadata tests/unit tests/integration docs`
- [X] T002 Create `code/requirements.txt` with pinned versions for all dependencies (pymatgen, matminer, scikit-learn, statsmodels, pandas, numpy, matplotlib, requests). Note: Specific versions are defined in the Plan's "Technical Context" section.
- [X] T003 [P] Create `code/.pre-commit-config.yaml` with hooks for `ruff` and `black`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T015 Implement `code/utils/logging.py` with `get_logger()` returning a JSON formatter that writes to `data/results/`
- [ ] T016 Implement `code/utils/cpu_constraints.py` with `enforce_memory_limit` to enforce a configurable memory constraint and `chunked_iterator()` function. Note: This utility is a blocking prerequisite for all memory-intensive tasks (T035, T039).
- [ ] T017 [P] Implement `code/utils/contract_validator.py` with `validate_schema(data, schema_path)` returning bool and error handling
- [X] T018 Create base `MaterialEntry` data class (fields: id, composition, formation_energy, descriptors) and `SparsitySubset` data class (fields: level, seed, percentage, checksum) in `code/utils/data_models.py`
- [X] T019 Setup environment configuration: Create `code/.env.example` with `MP_API_KEY=placeholder` and `code/config.py` with `load_env()` that raises error if `MP_API_KEY` missing. Note: The spec's Assumption regarding 'no authentication barriers' is incorrect; this task implements the required API key configuration per the Plan.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 1.6: Kickback & Spec Alignment

**Purpose**: Generate formal artifacts documenting deviations between Spec and Plan. These tasks do NOT modify spec.md directly, preserving the "Single Source of Truth" principle.

- [X] T010 [Kickback] Generate `docs/kickback_log.md` entry for FR-003: Log the deviation where the Plan defines a 'Representative Stratified Sample (RSS)' baseline while the Spec uses '[deferred]' full dataset terminology.
- [X] T011 [Kickback] Generate `docs/kickback_log.md` entry for Assumptions: Log the deviation where the Plan requires `MP_API_KEY` while the Spec assumes 'no authentication barriers'.
- [X] T012 [Kickback] Generate `docs/kickback_log.md` entry for FR-006: Log the deviation where the Plan mandates 'Linear Mixed-Effects Modeling (LMM)' while the Spec mandates 'Repeated Measures ANOVA' due to nested data structure.
- [X] T013 [Kickback] Generate `docs/kickback_log.md` entry for SC-001: Log the deviation where the Plan includes 'Predictive Variance' and 'Calibration Slope' metrics which are not explicitly listed in the Spec's SC-001.
- [X] T014 [Kickback] Generate `docs/kickback_log.md` entry for FR-007: Log the deviation where the Plan specifies a 'slope variance < 10% ' threshold for sensitivity analysis, whereas the Spec's FR-007 lacks this explicit metric. Note: Implementation of this check is handled by T047.

**Checkpoint**: Kickback log generated; Spec deviations formally recorded for next phase.

---

## Phase 3: User Story 1 - Data Retrieval and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and engineer features for the Materials Project dataset to create a valid input pool.

**Independent Test**: Execute `code/data_ingestion.py` and verify `data/processed/full_pool_final.csv` contains >150,000 rows with non-null formation energy and feature vectors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T022 [P] [US1] Unit test `test_api_backoff_retries_on_rate_limit` in `tests/unit/test_data_ingestion.py`
- [X] T023 [P] [US1] Integration test `test_full_ingestion_pipeline` in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [~] T024 [US1] Implement `code/data_ingestion.py` to download a substantial corpus of entries via Materials Project API. (using `MP_API_KEY`), with exponential backoff (limited retry attempts), outputting raw data to `data/raw/raw_pool.csv` with columns: `material_id`, `composition`, `formation_energy`, `dft_computed`.
- [~] T025 [US1] Implement filtering logic in `code/data_ingestion.py` to retain only rows where `formation_energy` is not null and `dft_computed` is True, saving to `data/processed/filtered_pool.csv`.
- [~] T026 [US1] Implement descriptor generation in `code/data_ingestion.py` using `matminer` `ElementalPropertyFeatureExtractor` with properties: `atomic_number`, `electronegativity`, `atomic_radius`, outputting to `data/processed/descriptors_pool.csv`.
- [~] T027 [US1] Implement imputation logic in `code/data_ingestion.py` to mean-fill missing numeric descriptors; drop rows with >50% missing values and log count to `data/results/ingestion_log.json`. Output final dataset to `data/processed/full_pool_final.csv`. <!-- FAILED: unspecified -->
- [ ] T028 [US1] Save cleaned full pool to `data/processed/full_pool_final.csv` with SHA-256 checksum generation (write to `data/processed/full_pool_final.csv.sha256`) (Constitution III)
- [~] T020 [US1] [P] Implement `code/test_split.py` to partition a subset of the `full_pool_final.csv` into a **Fixed Test Set** for model evaluation, following the research question and method outlined in prior work [Citation]. (`data/processed/test_set.csv`) using a fixed random seed. (FR-009, Plan Phase 0.5). Note: This task now correctly depends on T027.
- [~] T021 [US1] [P] Verify test set independence and log metadata (row count, checksum) to `data/metadata/test_set_metadata.json` (FR-009)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Sparsity Subsampling and Model Training (Priority: P1)

**Goal**: Partition data, generate sparsity levels, and train CPU-only models to measure performance degradation.

**Independent Test**: Run `code/test_split.py` and `code/model_training.py` for one sparsity level and verify `data/results/metrics.csv` is generated with RMSE/MAE without CUDA errors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US2] Contract test `test_test_set_independence` in `tests/contract/test_split.py`
- [X] T030 [P] [US2] Integration test `test_gpr_training_on_30k_subset` in `tests/integration/test_training.py`

### Implementation for User Story 2

- [ ] T031 [US2] Implement `code/sparsity_generation.py` to cap the training pool at a Representative Stratified Sample (RSS) by reading the baseline size from `config.RSS_SIZE` (resolving the '[deferred]' placeholder from the Plan). Implement stratified random sampling based on formation_energy bins. (Plan Phase 1.1).
- [ ] T032 [US2] Implement K-Means clustering on elemental fingerprints in `code/sparsity_generation.py` to generate multiple stratified subsets ([deferred], [deferred], [deferred], [deferred], [deferred], [deferred], [deferred] of the RSS pool) preserving chemical space (FR-003)
- [ ] T033 [US2] Implement stratification validation in `code/validate_stratification.py` using Jensen-Shannon divergence (threshold < 0.05) and KS-test (p > 0.05); block training if thresholds exceeded (Plan Phase 1.3)
- [ ] T034 [US2] Generate `data/metadata/sparsity_<level>_<seed>.json` for each subset containing keys: `seed`, `percentage`, `criteria`, `checksum` (Constitution VII)
- [ ] T035 [US2] Implement `code/model_training.py` to train GPR (RBF kernel, `normalize_y=True`, `max_iter_predict=1000`) and Random Forest models (n_estimators=100) on CPU only. Implement Linear Mixed-Effects Modeling (LMM) using `statsmodels.MixedLM` for statistical analysis as per Plan 'Note on Spec Contradictions' (FR-010).
- [ ] T036 [US2] Implement k-fold Cross-Validation with multiple independent seeds per sparsity level in `code/model_training.py` (FR-005)
- [ ] T037 [US2] Implement evaluation logic in `code/model_training.py` to score all models against the **Fixed Test Set** (not training subsets) and calculate RMSE, MAE, Predictive Variance, Calibration Slope. Note: Includes Predictive Variance and Calibration Slope per Constitution Principle VI and FR-005, exceeding SC-001.
- [ ] T038 [US2] Log metrics to `data/results/metrics.csv` with columns: `sparsity_level`, `model`, `seed`, `rmse`, `mae`, `variance`, `calibration_slope` (FR-005, SC-001)
- [ ] T039 [US2] Implement chunked processing in `code/model_training.py` with dynamic chunk size to handle OOM errors on large subsets (Edge Case)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P2)

**Goal**: Perform statistical validation, uncertainty calibration, and generate final research artifacts.

**Independent Test**: Run `code/statistical_analysis.py` and verify `data/results/plots/learning_curve.png` and `data/results/stat_summary.json` exist.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T040 [P] [US3] Unit test `test_lmm_formula` in `tests/unit/test_stats.py`
- [ ] T041 [P] [US3] Integration test `test_full_analysis_pipeline` in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T042 [US3] Implement `code/statistical_analysis.py` to generate learning curves (error vs. dataset size) with error bars using `matplotlib` (FR-006, SC-002)
- [ ] T043 [US3] Implement Linear Mixed-Effects Modeling (LMM) using `statsmodels.MixedLM` with formula `error ~ sparsity_level + (1|seed)` to handle nested sparsity levels. Note: This implements the Plan's approved deviation from FR-006 (ANOVA) due to nested data structure.
- [ ] T044 [US3] Apply Tukey post-hoc test to report p-values for differences between sparsity levels (threshold p < 0.05) (FR-006, SC-003)
- [ ] T045 [US3] Implement uncertainty calibration in `code/statistical_analysis.py` to generate calibration slope and predicted vs. squared residuals plots (Constitution VI, FR-005)
- [ ] T046 [US3] Save calibration reports to `data/results/calibration/` as JSON files containing slope and residuals comparison (Constitution VI)
- [ ] T047 [US3] Implement sensitivity analysis in `code/statistical_analysis.py` to verify elbow point stability (slope variance < 10%) across adjacent levels. Note: This implements the <10% threshold from the Plan, exceeding FR-007's ambiguous requirement.
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

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Kickback (Phase 1.6)**: Depends on Setup - Must be completed before Foundational to ensure spec deviations are recorded.
- **Foundational (Phase 2)**: Depends on Kickback - BLOCKS all subsequent work until foundation is ready and spec deviations are logged.
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

1. Complete Phase 1: Setup
2. Complete Phase 1.6: Kickback (Record spec deviations)
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Kickback + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Kickback + Foundational together
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
- **Spec Deviations**: Where the Plan mandates a deviation from the Spec (e.g., LMM vs ANOVA, RSS vs Full), the task implements the Plan's authority and notes the deviation. A formal `docs/kickback_log.md` is generated in Phase 1.6 to document these deviations for the next phase, ensuring the Spec is not retroactively rewritten by code tasks.