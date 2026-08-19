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

- [ ] T001a [P] Create directory structure: `code/`, `data/`, `data/raw`, `data/processed`, `data/logs`, `tests/`, `artifacts/`, `figures/`
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
> **Dependency**: Requires T007 (Schema Contracts) to be complete before execution.
> **Note**: T010 and T011 are marked [P] only if T007 is guaranteed complete; otherwise, they must wait.

- [X] T010 [P] [US1] Contract test for merged dataset schema in `tests/contract/test_dataset_schema.py` (Requires T007)
- [X] T011 [P] [US1] Integration test for geocoding alignment in `tests/integration/test_geocoding.py` (Requires T007)

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/ingestion/soil_data.py`: Stream/extract SoilGrids N, P, K, pH values at specific coordinates. **MUST** reproject/resample rasters to a common CRS (WGS84) before extraction to satisfy Constitution Principle VI. **MUST** handle "No Data" or negative values by excluding the specific row and logging it, not by imputation.
- [X] T013 [P] [US1] Implement `code/ingestion/trait_data.py`: Load root trait tabular data (Zenodo/Dryad), validate units, and filter for physically plausible values (depth > 0, pH 3.0-9.0)
- [X] T014 [US1] Implement `code/ingestion/merge.py`: Join soil and trait data, apply species filter (≥10 valid observations), and log excluded species per FR-007
- [X] T015 [US1] Implement `code/ingestion/validation.py`:
 1. Calculate match proportion = `count(valid_rows) / count(total_input_rows)` where valid rows are those with non-null soil data for all predictors.
 2. **Flag and exclude** individual rows with missing soil data (graceful degradation) as per Spec US-1 Acceptance Scenario 2.
 3. **Log excluded records** to `data/logs/record_exclusions.log` with columns `record_id`, `reason_code` (e.g., 'missing_soil_data', 'failed_geocoding', 'invalid_value').
 4. If the aggregate match proportion < 0.90, raise `DataQualityError` (a subclass of `Exception` with signature `DataQualityError(message: str, match_proportion: float)`) and write the specific failure reason to `data/logs/validation_error.log` with format `ERROR: Match proportion {match_proportion} < 0.90. Pipeline halted.`. Otherwise, proceed with valid data.
 5. **Rationale**: This 'hard fail' is the required operationalization of SC-001's 'pass criterion' in a CI/CD context to ensure data quality gates are enforced.
- [ ] T017 [US1] Generate `data/processed/merged_dataset.csv`, `data/processed/excluded_species_summary.csv`, and `data/logs/species_exclusions.log`.
 **Logic**:
 1. Count valid observations per species (rows where all predictors and outcomes are non-null and physically plausible).
 2. Filter for species with count < 10.
 3. Generate `excluded_species_summary.csv` with columns `species_name`, `observation_count`, `reason`. The `reason` column MUST contain the specific reason for exclusion (e.g., 'observation_count < 10').
 4. Generate `species_exclusions.log` with columns `species_name`, `reason`, `observation_count`.
 **Dependency**: Runs after T015.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train RF models and evaluate via Stratified 5-Fold CV (Primary), LOSO (Secondary).

**Independent Test**: The training script executes on the merged dataset, outputs cross-validation metrics (mean R², mean RMSE) for both target variables, and generates a feature importance plot.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`
- [X] T019 [P] [US2] Integration test for LOSO cross-validation loop in `tests/integration/test_loso.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/modeling/train.py`:
 1. **Preprocessing**: Encode 'Species' as categorical.
 2. **Model Training**: Train Model B (Soil+Species) as the primary implementation of FR-003. Train Model A (Soil-Only) as a control experiment for ablation analysis.
 3. **Validation**: Execute **Stratified k-Fold CV** (k=5, stratified by Species) and **Leave-One-Species-Out (LOSO)** CV to satisfy Constitution Principle VII.
 4. **Output**: Generate `observed_r2` and `observed_rmse` for both models and validation types.
 **Note**: This task consolidates preprocessing and training into a single sequential step.
 **Dependency**: None (after Foundation).
- [X] T021 [US2] Implement `code/modeling/train.py`: Calculate baseline R² by applying a **mean-prediction model** (predicting the mean of the training fold) on each held-out test fold. Calculate `delta_r2 = observed_r2 - baseline_r2`. **Rationale**: The 'mean-prediction' model is the standard interpretation of the 'null model' required by SC-002 for calculating R² gain. **MUST** complete after T020.
- [X] T022 [US2] Implement `code/modeling/train.py`: Perform nested permutation tests with a **configurable number of iterations (default 1000)**.
 - For Model A: permute target variable within training folds.
 - For Model B: permute soil features (N, P, K, pH) **stratified by species** within training folds.
 - Use a **fixed RANDOM_SEED** for determinism.
 - **Write** the distribution of R² scores to `artifacts/permutation_distributions.json`.
 **MUST** follow T021.
- [X] T023 [US2] Implement `code/modeling/train.py`: **Read and validate** `artifacts/permutation_distributions.json` (must contain 1000 iterations and non-empty data). Calculate p-values and enforce SC-002 (ΔR² ≥ 0.05 AND p < 0.05). **Write** pass/fail status to `artifacts/sc002_status.json` with schema `{\"pass\": bool, \"reason\": string}`. **MUST** follow T022.
- [ ] T024 [US2] Write `artifacts/model_metrics.json` with explicit schema: `{"mean_r2": float, "mean_rmse": float, "loso_r2_sd": float, "per_target_metrics": {...}}`.
- [ ] T025 [US2] Generate feature importance bar chart in `figures/feature_importance.png` and raw scores in `artifacts/feature_importance.csv` with columns `feature_name`, `importance_score`. **Note**: `p_value` column will be added by T027 in Phase 5.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

**Goal**: Validate robustness of feature importance rankings across p-value thresholds.

**Independent Test**: The analysis script runs a loop over p-value thresholds and outputs a table showing stability of top-3 feature rankings.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_schema.py`

### Implementation for User Story 3

- [X] T027 [US3] Implement `code/modeling/sensitivity.py`: Calculate p-values for each feature importance score via permutation. **Input**: MUST consume `artifacts/feature_importance.csv` from T025. **Action**: Append `p_value` column to `artifacts/feature_importance.csv`. **Dependency**: Cannot run in parallel with US2 tasks.
- [X] T028 [US3] Implement `code/modeling/sensitivity.py`: Sweep p-value thresholds across a range of significance levels and track top-3 feature stability. **Dependency**: Must run after T027.
- [X] T029 [US3] Implement `code/modeling/sensitivity.py`: Generate sensitivity analysis report (`artifacts/sensitivity_report.md`).
 **Structure**: Must include sections: '## Threshold Stability' (containing the stability table) and '## Justification'.
 **Table Schema**: Columns `threshold`, `top_feature`, `rank_2`, `rank_3`, `stable`.
 **Content**: The '## Justification' section MUST cite a verified community standard from `research.md` or the literature review for the significance level. **Do NOT hard-code generic text**. Ensure all findings are framed as associational (FR-006) within this report.
 **Constraint**: Ensure all findings are framed as associational (FR-006) within this report.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates: Generate `quickstart.md` and finalize `research.md`
- [ ] T031 Code cleanup and refactoring in `code/`
- [ ] T032 Performance optimization: Ensure pipeline completes within 6-hour CI limit (SC-005)
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
 - T015 -> T017 (Validation -> Summary & Log)
 - T020 -> T021 -> T022 -> T023 (Training -> Baseline -> Permutation -> SC-002)
 - T027 -> T028 -> T029 (p-values -> Sweep -> Report)

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
- **Critical Ordering**: T015 must precede T017. T020 must precede T021. T021 must precede T022. T022 must precede T023. T027 must follow T025.