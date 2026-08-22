# Tasks: Predicting Plant Root Architecture from Soil Nutrient Profiles

**Input**: Design documents from `/specs/001-predict-root-architecture/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create directory structure: `code/`, `data/`, `data/raw`, `data/processed`, `data/logs`, `tests/`, `artifacts/`, `figures/`. **Implementation**: Use a Python script `setup_dirs.py` that calls `os.makedirs(path, exist_ok=True)` for each directory to ensure deterministic creation.
- [X] T001b [P] Create `code/requirements.txt` with pinned dependencies (scikit-learn, pandas, numpy, rasterio, geopandas, requests, pyyaml, pytest)
- [ ] T001c [P] Create `.gitignore` for Python and data artifacts
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/utils/` directory and `__init__.py`
- [X] T005 [P] Implement `code/utils/stats.py` with permutation test logic and metric calculation functions
- [X] T006 [P] Implement `code/utils/geocoding.py` for CRS alignment and coordinate validation
- [ ] T007a [P] Create `specs/001-predict-root-architecture/contracts/dataset.schema.yaml`
- [ ] T007b [P] Create `specs/001-predict-root-architecture/contracts/model_output.schema.yaml`
- [X] T008 Configure error handling infrastructure (custom `DataQualityError` in `code/utils/exceptions.py`)
- [ ] T009 Setup environment configuration management (`.env` handling for API keys if needed)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Geospatial Alignment (Priority: P1) 🎯 MVP

**Goal**: Produce a unified dataset of paired soil nutrients and root traits.

**Independent Test**: The pipeline can be executed end-to-end on a sample subset of coordinates, producing a single CSV file where every row contains a valid root trait measurement paired with extracted soil N, P, K, and pH values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**
> **Dependency**: Requires T007 (Schema Contracts) to be complete before execution. **T007 MUST be completed before T010/T011 start.**
> **Note**: T010 and T011 are NOT parallel-safe relative to T007. They must wait for T007 completion. The [P] tag applies only to parallelism within Phase 3 *after* T007 is done.

- [X] T010 [P] [US1] Contract test for merged dataset schema in `tests/contract/test_dataset_schema.py` (Requires T007 completion)
- [X] T011 [P] [US1] Integration test for geocoding alignment in `tests/integration/test_geocoding.py` (Requires T007 completion)

### Implementation for User Story 1

- [X] T016 [US1] Implement `code/ingestion/data_loader.py`: Create a robust data loader that attempts to fetch real root trait data from verified sources (Zenodo/Dryad/HuggingFace) using the exact IDs specified in `research.md`. **Constraint**:
 1. **Production Mode**: If `RUN_MODE=production` (default), **MUST NOT** implement a `try/except` fallback to synthetic/mock data. If the real fetch fails, the script **MUST** raise a `DataFetchError` and exit immediately.
 2. **Test Mode**: If `RUN_MODE=test` (set via environment variable), the script **MAY** fall back to a synthetic proxy dataset for pipeline structure testing only.
 **Dependency**: Runs before T013.

- [X] T013 [P] [US1] Implement `code/ingestion/trait_data.py`: Load root trait tabular data using `data_loader.py` (Requires T016 implementation), validate units, and filter for physically plausible values (depth > 0, pH range from acidic to alkaline conditions).

- [X] T012 [P] [US1] Implement `code/ingestion/soil_data.py`: Stream/extract SoilGrids N, P, K, pH values at specific coordinates. **MUST** reproject/resample rasters to a common CRS (WGS84) before extraction to satisfy Constitution Principle VI. **MUST** handle "No Data" or negative values by excluding the specific row. **MUST produce a derived dataset file** `data/processed/soil_extracted.csv` with a checksum and a derivation log entry for every row exclusion to satisfy Constitution Principle III (Data Hygiene).

- [X] T014 [US1] Implement `code/ingestion/merge.py`: Join soil and trait data, apply species filter (≥10 valid observations), and log excluded species per FR-007. **Dependency**: Runs after T012 and T013.

- [X] T015 [US1] Implement `code/ingestion/validation.py`:
 1. Calculate match proportion = `count(valid_rows) / count(total_input_rows)` where valid rows are those with non-null soil data for all predictors.
 2. **Flag and exclude** individual rows with missing soil data (graceful degradation) as per Spec US-1 Acceptance Scenario 2.
 3. **Log excluded records** to `data/logs/record_exclusions.log` with columns `record_id`, `reason_code` (e.g., 'missing_soil_data', 'failed_geocoding', 'invalid_value').
 4. **Log validation summary** to `data/logs/validation_summary.log` with columns `timestamp`, `match_proportion`, `total_rows`, `valid_rows`, `excluded_rows`, `error_message`.
 5. **Hard Stop Enforcement**: If match proportion < 0.90, **MUST** raise `DataQualityError` with the specific reason and halt execution. **Do NOT** log a warning and continue.
 **Dependency**: Runs after T014.

- [ ] T017 [US1] Generate `data/processed/merged_dataset.csv`, `data/processed/excluded_species_summary.csv`, and `data/logs/species_exclusions.log`.
 **Logic**:
 1. Count valid observations per species (rows where all predictors and outcomes are non-null and physically plausible) from the **filtered dataset produced by T015**.
 2. Filter for species with count < 10.
 3. Generate `excluded_species_summary.csv` with columns `species_name`, `observation_count`, `reason`. The `reason` column MUST contain the specific reason for exclusion (e.g., 'observation_count < 10').
 4. Generate `species_exclusions.log` with columns `species_name`, `reason`, `observation_count`.
 5. **Output**: `data/processed/merged_dataset.csv` is the **species-filtered** version (post-T015 row filtering and post-species-count filtering).
 **Dependency**: Runs after T015 and T016.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train RF models and evaluate via Leave-One-Species-Out (LOSO) (Primary), Stratified 5-Fold CV (Secondary).

**Independent Test**: The training script executes on the merged dataset, outputs cross-validation metrics (mean R², mean RMSE) for both target variables, and generates a feature importance plot.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`
- [X] T019 [P] [US2] Integration test for LOSO cross-validation loop in `tests/integration/test_loso.py`

### Implementation for User Story 2

- [X] T020 [US2] **Implement** `code/modeling/train.py`:
 1. **Preprocessing**: Encode 'Species' as categorical.
 2. **Model Training**: Train Model B (Soil+Species) as the primary implementation of FR-003. Train Model A (Soil-Only) as a control experiment for ablation analysis.
 3. **Validation Strategy**: Execute **Leave-One-Species-Out (LOSO)** CV as the **PRIMARY** validation method to satisfy Spec US-2/FR-004. Execute **Stratified k-Fold CV** (k=5, stratified by Species) as **SECONDARY** validation.
 4. **Output**: Generate `observed_r2` and `observed_rmse` for both models and validation types.
 **Note**: This task focuses on the *implementation* of the script structure.
 **Dependency**: None (after Foundation).

- [X] T021 [US2] **Execute/Calculate** baseline R² using `code/modeling/train.py` (or a helper script). Apply a **mean-prediction model** on each held-out test fold. **Action**: For each fold, train a model that predicts the **mean of the training fold's target values** and evaluate on the **held-out test fold**. Calculate `delta_r2 = observed_r2 - baseline_r2`. **Output**: Write `artifacts/baseline_metrics.json` with schema `{"mean_baseline_r2": float, "per_fold_baseline_r2": [float]}`. **Rationale**: The 'mean-prediction' model is the standard interpretation of the 'null model' required by SC-002. **MUST** follow T020 execution.

- [X] T022 [US2] **Execute/Validate** nested permutation tests with a **configurable number of iterations (default a substantial sample size)** using `code/modeling/train.py`.
 - For Model A: permute target variable within training folds.
 - For Model B: permute soil features (N, P, K, pH) **stratified by species** within training folds.
 - Use a **fixed RANDOM_SEED** for determinism (pinned in `code/` and `requirements.txt`).
 - **Write** the distribution of R² scores to `artifacts/permutation_distributions.json`.
 **MUST** follow T021.

- [ ] T023 [US2] **Execute/Validate** SC-002 compliance. **Read and validate** `artifacts/permutation_distributions.json` (must contain A sufficient number of iterations will be performed to ensure convergence. and non-empty data). Calculate p-values and enforce SC-002 (ΔR² ≥ 0.05 AND p < 0.05). **Write** pass/fail status to `artifacts/sc002_status.json` with schema `{"pass": bool, "reason": string, "delta_r2": float, "p_value": float}`. **MUST** follow T022. <!-- ATOMIZE: requested -->

- [ ] T024 [US2] Write `artifacts/model_metrics.json` with explicit schema: `{"mean_r2": float, "mean_rmse": float, "loso_r2_sd": float, "per_target_metrics": {...}}`. **Dependency**: Must run after T023.

- [ ] T025a [US2] Generate raw feature importance scores in `artifacts/feature_importance.csv` with columns `feature_name`, `importance_score`. **Dependency**: Must run after T024.

- [ ] T025b [US2] Generate feature importance bar chart in `figures/feature_importance.png`. **Note**: This artifact is authorized by the plan's Phase 2 output section. **Dependency**: Must run after T025a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

**Goal**: Validate robustness of feature importance rankings across p-value thresholds.

**Independent Test**: The analysis script runs a loop over p-value thresholds and outputs a table showing stability of top-3 feature rankings.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_schema.py`

### Implementation for User Story 3

- [X] T027 [US3] Implement `code/modeling/sensitivity.py`: Calculate p-values for each feature importance score via permutation. **Input**: MUST consume `artifacts/feature_importance.csv` from T025a. **Action**: Append `p_value` column to `artifacts/feature_importance.csv`. **Dependency**: Cannot run in parallel with US2 tasks. **Must run after T025b**. <!-- ATOMIZE: requested -->

- [X] T028 [US3] Implement `code/modeling/sensitivity.py`: Sweep p-value thresholds across a range of significance levels and track top-3 feature stability. **Dependency**: Must run after T027.

- [X] T029 [US3] Implement `code/modeling/sensitivity.py`: Generate sensitivity analysis report (`artifacts/sensitivity_report.md`). <!-- FAILED: unspecified -->
 **Structure**: Must include sections: '## Threshold Stability' (containing the stability table) and '## Justification'.
 **Table Schema**: Columns `threshold`, `top_feature`, `rank_2`, `rank_3`, `stable`.
 **Content**: The '## Justification' section MUST cite a verified community standard.
 **Citation Logic**:
 1. **Primary**: If `research.md` (T035) is available and complete, cite the verified standard from there using "[Author, Year]" and a footnote.
 2. **Fallback**: If `research.md` is not available, cite the standard "p=0.05" with the justification "typical significance levels in ecological regression".
 **Constraint**: Ensure all findings are framed as associational (FR-006) within this report.
 **Dependency**: **Requires T035 completion** (or fallback logic). Must run after T028.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 0: Research & Documentation (Missing Artifact Resolution)

**Purpose**: Generate missing artifacts required by downstream tasks

- [ ] T035 [P] Generate `specs/001-predict-root-architecture/research.md`. **Content**: Must include verified community standards for significance levels (p=0.05) and citations for soil/root trait datasets. **Dependency**: None. **Required by**: T029.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates: Generate `quickstart.md` and finalize `research.md`
- [ ] T031 Code cleanup and refactoring in `code/`
- [ ] T032 Performance optimization: Ensure pipeline completes within -hour CI limit (SC-005)
- [ ] T033 [P] Additional unit tests in `tests/unit/` for helper functions
- [ ] T034 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (merged dataset)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (model metrics)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority
- **Sequential Dependencies**:
 - T016 -> T013 (Data Loader -> Trait Data)
 - T013 -> T012 (Trait Data -> Soil Data - parallelizable after T016)
 - T012/T013 -> T014 (Merge)
 - T014 -> T015 (Validation)
 - T015 -> T017 (Summary & Log)
 - T020 -> T021 -> T022 -> T023 (Training -> Baseline -> Permutation -> SC-002)
 - T023 -> T024 -> T025a -> T025b -> T027 -> T028 -> T029 (Model Metrics -> CSV -> PNG -> Sensitivity -> Report)
 - T035 -> T029 (Research -> Report)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (provided their dependencies like T007 are met)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
# Note: Requires T007 to be complete first.
Task: "Contract test for merged dataset schema in tests/contract/test_dataset_schema.py"
Task: "Integration test for geocoding alignment in tests/integration/test_geocoding.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingestion/soil_data.py"
Task: "Implement code/ingestion/trait_data.py"
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
- **Critical Ordering**: T016 must precede T013. T015 must precede T017. T020 must precede T021. T021 must precede T022. T022 must precede T023. T023 must precede T024. T024 must precede T025a. T025a must precede T025b. T025b must precede T027. T035 must precede T029 (or fallback logic used).