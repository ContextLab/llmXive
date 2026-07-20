# Tasks: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [ ] T001 Create project structure per implementation plan: Execute `mkdir -p code/ingestion code/features code/modeling code/utils data/raw data/processed tests/unit tests/integration docs` in repository root.
- [X] T002 Initialize Python 3.11 project: Create `code/requirements.txt` containing pinned versions for: pandas, scikit-learn, requests, pyyaml, mendeleev, statsmodels, pytest.
- [ ] T003 Configure linting and formatting: Install `ruff` and create `code/.ruff.toml` with rules `E4`, `E7`, `E9`, `F`, `I`, `UP` and formatting rules `line-length=88`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup environment configuration management: Create `code/utils/config.py` to load `MP_API_KEY`, `AFLOW_API_KEY`, and `ZENODO_ID` (fallback value: '1234567') from environment variables.
- [X] T005 Implement logging infrastructure in `code/utils/io.py`: Configure `logging` module with `FileHandler` to `logs/pipeline.log` and `StreamHandler` to `sys.stdout`.
- [X] T005a Implement checksumming utilities in `code/utils/io.py`: Define `def compute_sha256(path: str) -> str` that returns the hex digest of the file content.
- [ ] T006 Create base data schema validation (`contracts/mg_dataset.schema.yaml`) and Pydantic models for `MetallicGlassEntry`.
- [X] T007 Setup deterministic random seed management in `code/__init__.py`: Set `os.environ['PYTHONHASHSEED'] = '42'`, `numpy.random.seed(42)`, and `SEED = 42` global variable.
- [X] T008 Implement "Fail Loud" data loader pattern (no synthetic fallbacks) in `code/utils/io.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Retrieve metallic glass composition and CTE data from public repositories (Materials Project, AFLOWlib, or Zenodo fallback), filter for amorphous entries, and extract compositional descriptors.

**Independent Test**: Can be fully tested by running the data ingestion script and verifying that the output CSV contains exactly the required columns (composition, CTE, weighted mean atomic radius, electronegativity, VEC, atomic size mismatch) with no missing values for the selected metallic glass subset, and that the 'amorphous state flag' is present and used for filtering.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T009 [P] [US1] Unit test: Add `tests/unit/test_descriptors.py::test_parse_formula` to verify composition parsing. Assert: `parse_formula("Zr50Cu40Al10") == {'Zr': 0.5, 'Cu': 0.4, 'Al': 0.1}`.
- [X] T010 [P] [US1] Unit test: Add `tests/unit/test_descriptors.py::test_calculate_weighted_mean_radius` to verify radius calculation. Assert: `calculate_weighted_mean_radius({'Zr': 0.5, 'Cu': 0.4}, radii={'Zr': 160, 'Cu': 128}) == 147.2`.
- [X] T011 [P] [US1] Integration test: Add `tests/integration/test_ingestion.py::test_api_fetch` to verify API fetch and Zenodo fallback logic. Assert: `fetch_data()` returns a DataFrame with >= 0 rows and raises if all sources fail.
- [ ] T012 [P] [US1] Integration test: Add `tests/integration/test_ingestion.py::test_schema_validation` to verify output schema matches `contracts/mg_dataset.schema.yaml`. Assert: `df.columns` matches schema required fields.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `fetch_data.py` in `code/ingestion/` to query Materials Project and AFLOWlib APIs using env vars, prioritizing collection of ALL available valid entries.
- [X] T014 [US1] Implement Zenodo fallback fetcher in `code/ingestion/fetch_data.py` (Zhang et al.,) ONLY if APIs return < 50 entries OR fail; document this as a contingency, not a standard path.
- [X] T015 [US1] Implement robust filtering logic in `code/ingestion/fetch_data.py` to exclude non-amorphous entries and missing CTE values.
- [ ] T016 [US1] Implement `descriptors.py` in `code/features/` to calculate weighted mean atomic radius, electronegativity variance, VEC, and atomic size mismatch.
- [X] T017 [US1] Implement VIF check in `code/features/descriptors.py` to detect multicollinearity between `mean_atomic_radius` and `size_mismatch`. **Constraint**: If VIF > 5.0 (Config Key: `VIF_THRESHOLD=5.0`), DO NOT exclude `size_mismatch` (per Constitution Principle VI); instead, log a warning "High VIF detected for size_mismatch" and retain the feature.
- [ ] T017a [US1] Document the VIF conflict: Add a comment in `code/features/descriptors.py` explaining that `size_mismatch` is retained despite high VIF per Constitution Principle VI, and flag this as a known limitation in `results/metrics.json` if VIF > 5.0.
- [ ] T022 [US1] Save cleaned dataset to `data/processed/clean_mg_data.parquet` with checksum manifest using `compute_sha256` from T005a.
- [ ] T018 [US1] Implement data splitting logic in `code/modeling/train.py`: **Primary**: Stratified split by `alloy_family` (Zr, Pd, Fe) as required by FR-003. **Fallback**: If any family has < 5 samples causing empty test sets, revert to random split. Do NOT downgrade based on N < 50.
- [ ] T019 [US1] Implement conditional validation strategy selection in `code/modeling/train.py`: 5-fold (N≥50), Hold-Out (20≤N<50), LOO (N<20). **Log Format**: If stratification fails, log "DEV: FR-003 stratification failed, using random split". If N-based strategy is used, log "DEV: FR-003 5-fold skipped due to N<50" and write `{"spec_deviation_FR003": "N<50_downgrade"}` to `results/metrics.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 0.5: No Data Termination (If N = 0)

**Purpose**: Handle the case where no data is found

- [ ] T020 [US1] Implement "Phase 0.5: No Data Termination" pipeline in `code/ingestion/fetch_data.py`: If N=0, log error "No valid metallic glass entries found", generate `results/metrics.json` with `{"status": "no_data"}`, and exit cleanly with code 0.

---

## Phase 0.6: Qualitative Trend Analysis (If 20 <= N < 50)

**Purpose**: Handle the case where data is insufficient for robust statistical testing

- [ ] T021 [US1] Implement "Phase 0.6: Qualitative Trend Analysis" pipeline in `code/modeling/train.py`: If 20 <= N < 50, skip permutation testing, perform simple linear regression/correlation, and generate `results/metrics.json` with `{"status": "qualitative"}`.

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train baseline linear regression and random forest models using scikit-learn on CPU, performing k-fold cross-validation to tune hyperparameters within strict resource limits.

**Independent Test**: Can be fully tested by executing the training pipeline on a sample subset and verifying that the 5-fold cross-validation scores (R², MAE) are generated as non-null, finite numbers, and that the final model is saved without exceeding standard RAM or CPU core constraints.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test: Add `tests/unit/test_baseline.py::test_null_model_predicts_mean` to verify null model baseline calculation. Assert: `NullModel().predict(X) == y_train.mean()`.
- [ ] T024 [P] [US2] Integration test: Add `tests/integration/test_training.py::test_training_pipeline_5fold_cv` to verify full training pipeline with 5-fold CV. Assert: `cv_scores` are finite and `model` is saved.

### Implementation for User Story 2

- [ ] T025 [US2] Implement `train.py` in `code/modeling/` to load `clean_mg_data.parquet` and prepare feature matrix.
- [ ] T026 [US2] Implement "Null Model" baseline (predicts mean CTE) in `code/modeling/train.py`.
- [ ] T026a [US2] Implement "Elemental Weighted Average" baseline in `code/modeling/train.py`: Use `mendeleev` to fetch elemental CTEs, calculate weighted average by stoichiometry, and use this as the primary baseline for SC-001.
- [ ] T027 [US2] Log Spec-Root Cause flag: If elemental CTEs are unavailable, use Null Model and write `{"baseline_type": "null_model"}` to `results/metrics.json`. If elemental CTEs are available, write `{"baseline_type": "elemental_weighted_average"}`.
- [ ] T028 [US2] Implement Linear Regression training with 5-fold CV (or selected strategy) in `code/modeling/train.py`.
- [ ] T029 [US2] Implement Random Forest training with 5-fold CV and grid search over `max_depth` and `n_estimators` in `code/modeling/train.py`.
- [ ] T030 [US2] Enforce resource constraints: Add `n_jobs=2` and `memory_limit` to sklearn config in `code/modeling/train.py` to ensure training runs on ≤2 CPU cores and ≤7 GB RAM (no GPU).
- [ ] T031 [US2] Implement model serialization to `models/` directory with metadata (hyperparameters, CV scores).
- [ ] T032 [US2] Implement evaluation script in `code/modeling/evaluate.py` to calculate R², MAE, RMSE on held-out test set.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Feature Importance Analysis (Priority: P3)

**Goal**: Perform permutation testing to validate model performance exceeds random chance and generate feature importance rankings to identify key compositional drivers.

**Independent Test**: Can be fully tested by running the significance analysis script on the trained model and verifying that a p-value is reported for all models (flagging 'Null Result' if R² ≤ 0.3), and that a ranked list of feature importances is generated where the Top-ranked features match the top-ranked features by correlation coefficient magnitude.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test: Add `tests/unit/test_significance.py::test_permutation_p_value_convergence` to verify permutation test logic and p-value calculation. Assert: `p_value` is between 0 and 1.
- [ ] T034 [P] [US3] Integration test: Add `tests/integration/test_analysis.py::test_divergence_ranking_match` to verify Divergence Analysis (Importance vs. Correlation). Assert: `divergence_score` is calculated.

### Implementation for User Story 3

- [ ] T035 [US3] Implement permutation test in `code/modeling/evaluate.py` with exactly 1000 iterations for all datasets with N >= 20, as required by FR-005.
- [ ] T035a [US3] Handle N < 20 case: If N < 20, skip permutation test, log warning "N < 20: Permutation test skipped", and write `{"permutation_status": "skipped_low_n"}` to `results/metrics.json`.
- [ ] T036 [US3] Implement significance flagging logic: Flag 'Null Result' if performance does not exceed random chance (p-value > 0.05). If R² <= 0.3, write `{"sc003_match_status": "insufficient_data_for_significance"}` to `results/metrics.json`.
- [ ] T037 [US3] Implement feature importance extraction from Random Forest model.
- [ ] T038 [US3] Implement Pearson correlation calculation for each feature against CTE on a distinct validation set.
- [ ] T039 [US3] Implement Divergence Analysis in `code/modeling/evaluate.py` to compare feature importance ranks vs. correlation ranks. **Output Format**: Generate `results/divergence.csv` with columns `feature, importance_rank, correlation_rank, divergence_score`.
- [ ] T039b [US3] Implement SC-003 Match Check: Compare top-ranked features by importance vs. top-ranked features by correlation. **Output**: Write `{"sc003_match_status": "pass"}` or `{"sc003_match_status": "fail"}` to `results/metrics.json` based on the match.
- [ ] T040 [US3] Generate final `results/metrics.json` with R², MAE, RMSE, p-values, significance status, divergence findings, and all Spec-Root Cause flags. **Required Keys**: `baseline_type`, `spec_deviation_FR003`, `sc003_match_status`, `permutation_status`, `vif_warning`.
- [ ] T041 [US3] Handle edge case: If N < 50, skip permutation test and output "Qualitative Trend" status only (see T021).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `docs/` including `quickstart.md` and `research.md`
- [ ] T043 Code cleanup and refactoring of `code/ingestion/` and `code/features/`
- [ ] T044 Performance optimization: Ensure streaming/processing fits within 7 GB RAM for large datasets (if applicable)
- [ ] T045 [P] Additional unit tests for edge cases (empty API responses, malformed formulas) in `tests/unit/`
- [ ] T046 Run quickstart.md validation to ensure end-to-end pipeline execution

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **T022 (Save cleaned dataset) must complete before T025 (Load clean_mg_data.parquet)**.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **T031 (Model serialization) must complete before T035 (Permutation test)**.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data fetching and cleaning (T013-T015) must complete before Feature Engineering (T016-T017) in production flow (T016/T017 are NOT [P] in production).
- Models (T028-T029) must complete before Evaluation (T032)
- Evaluation (T032) must complete before Significance Analysis (T035-T040)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Descriptor calculation (T016) and API Fetching (T013) can be parallelized if data is mocked for testing, but sequential in production flow.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test: Add tests/unit/test_descriptors.py::test_parse_formula"
Task: "Unit test: Add tests/unit/test_descriptors.py::test_calculate_weighted_mean_radius"

# Launch all models for User Story 1 together:
Task: "Implement fetch_data.py in code/ingestion/ to query Materials Project and AFLOWlib APIs using env vars"
Task: "Implement descriptors.py in code/features/ to calculate weighted mean atomic radius, electronegativity variance, VEC, and atomic size mismatch"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify data ingestion and feature extraction)
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
 - Developer A: User Story 1 (Data & Features)
 - Developer B: User Story 2 (Modeling) - can start once US1 data schema is defined
 - Developer C: User Story 3 (Analysis) - can start once US2 model interface is defined
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
- **Critical Constraint**: Do NOT use synthetic data fallbacks. If real data fetch fails, the script must raise an error.
- **Critical Constraint**: Respect the 7 GB RAM limit; use streaming or sampling if N > 10,000.
- **Critical Constraint**: All Spec-Root Cause deviations (baseline substitution, N-based validation, Divergence Analysis) MUST be explicitly documented in `results/metrics.json`.