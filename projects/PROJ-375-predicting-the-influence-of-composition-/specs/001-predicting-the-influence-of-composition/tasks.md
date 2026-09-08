# Tasks: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [ ] T001 [P] Create project directory structure: Execute `mkdir -p code/ingestion code/features code/modeling code/utils data/raw data/processed tests/unit tests/integration docs results code/models logs` in repository root.
- [X] T002 [P] Initialize Python 3.11 project: Create `code/requirements.txt` containing pinned versions for: pandas, scikit-learn, requests, pyyaml, mendeleev, statsmodels, pytest, memory_profiler, joblib.
- [ ] T003 [P] Configure linting and formatting: Install `ruff` and create `code/.ruff.toml` with rules `E4`, `E7`, `E9`, `F`, `I`, `UP` and formatting rules `line-length=88`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 [P] Setup environment configuration management: Create `code/utils/config.py` to load `MP_API_KEY`, `AFLOWlib_API_KEY`, and `ZENODO_ID` (fallback value: '1234567') from environment variables.
- [X] T005 [P] Implement logging infrastructure in `code/utils/io.py`: Configure `logging` module with `FileHandler` to `logs/pipeline.log` and `StreamHandler` to `sys.stdout`.
- [X] T005a [P] Implement checksumming utilities in `code/utils/io.py`: Define `def compute_sha256(path: str) -> str` that returns the hex digest of the file content.
- [ ] T006 [P] Create base data schema validation (`contracts/mg_dataset.schema.yaml`) and Pydantic models for `MetallicGlassEntry`.
- [X] T007 [P] Setup deterministic random seed management in `code/__init__.py`: Set `os.environ['PYTHONHASHSEED'] = '42'`, `numpy.random.seed(42)`, and `SEED = 42` global variable.
- [X] T008 [P] Implement "Fail Loud" data loader pattern (no synthetic fallbacks) in `code/utils/io.py`.
- [ ] T001-Sample [P] Implement streaming/sampling strategy for N > 10,000: Create `code/utils/io.py` function `stream_and_sample(dataset, max_rows=10000, seed=42)` that yields rows in chunks and performs random sampling if total > max_rows. Document sampling rule (e.g., "first 10k rows" or "random 10k with seed 42").

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

- [ ] T013-MP [US1] Implement `code/ingestion/fetch_mp.py` to query Materials Project API using env vars. **Logic**:
 1. Send GET request to `https://next-gen.materialsproject.org/materials/v2/` with `?elements=...&include=properties` filtering for `amorphous=true` or `phase_type=amorphous`.
 2. **Constraint**: Fetch ALL available valid entries. Do NOT stop at 50. Do NOT use count thresholds to switch sources.
 3. Parse JSON response for `composition` and `thermal_expansion_coefficient`.
 4. **Error Handling**: If API returns 403 or 404, log warning and return empty DataFrame. If connection fails, raise `ConnectionError`.
 5. **Fail Loud**: If MP returns 0 entries AND AFLOW returns 0 entries, proceed to Zenodo fallback ONLY as a last resort.
 **Output**: Write raw data to `data/raw/mp_data.csv` with columns `composition`, `cte`, `amorphous_flag`.
- [ ] T013-AF [US1] Implement `code/ingestion/fetch_af.py` to query AFLOWlib API using env vars. **Logic**:
 1. Send GET request to `https://aflowlib.org/api/` (or equivalent endpoint) filtering for `amorphous` structures.
 2. **Constraint**: Fetch ALL available valid entries. Do NOT stop at 50.
 3. Parse response for `composition` and `cte`.
 4. **Error Handling**: If API returns 403 or 404, log warning and return empty DataFrame. If connection fails, raise `ConnectionError`.
 **Output**: Write raw data to `data/raw/aflow_data.csv` with columns `composition`, `cte`, `amorphous_flag`.
- [ ] T013-ZF [US1] Implement `code/ingestion/fetch_zenodo.py` to fetch Zenodo fallback dataset ONLY if MP and AFLOW both fail (return 0 entries) OR raise connection errors. **Logic**:
 1. Check total entries from T013-MP and T013-AF.
 2. **Strict Condition**: If (MP_entries == 0 AND AFLOW_entries == 0) OR (MP_failed AND AFLOW_failed), THEN fetch Zenodo using `ZENODO_ID` from env.
 3. **Do NOT** use Zenodo if MP or AFLOW returned any valid entries (even if < 50).
 4. Map columns: `formula` -> `composition`, `cte` -> `cte`, `amorphous` -> `amorphous_flag`.
 **Output**: Write raw data to `data/raw/zenodo_data.csv` with columns `composition`, `cte`, `amorphous_flag`.
- [ ] T014 [US1] Implement robust filtering logic in `code/ingestion/fetch_data.py` to exclude non-amorphous entries and missing CTE values. **Logic**: Merge T013-MP, T013-AF, T013-ZF outputs. Filter `amorphous_flag == True` and `cte` not null.
- [X] T020 [US1] Implement "Phase 0.5: No Data Termination" pipeline in `code/ingestion/fetch_data.py`: If N=0 after merging T013-MP, T013-AF, T013-ZF, log error "No valid metallic glass entries found", generate `results/metrics.json` with `{"status": "no_data"}`, and exit cleanly with code 0. **Dependency**: Requires T013-MP, T013-AF, T013-ZF.
- [ ] T016 [US1] Implement `code/features/descriptors.py` to calculate `weighted_mean_atomic_radius`, `electronegativity_var`, `vec`, and `size_mismatch`. **Logic**:
 1. `weighted_mean_atomic_radius` = Σ (atomic_fraction_i * atomic_radius_i).
 2. `electronegativity_var` = Σ (atomic_fraction_i * (electronegativity_i - mean_electronegativity)^2).
 3. `vec` = Σ (atomic_fraction_i * valence_electrons_i).
 4. `size_mismatch` = 1 - Σ (atomic_fraction_i * (1 - |atomic_radius_i - mean_radius| / mean_radius)).
 **Output**: DataFrame with columns `mean_atomic_radius`, `electronegativity_var`, `vec`, `size_mismatch`. **Requires**: T014.
- [ ] T017 [US1] Implement VIF check in `code/features/descriptors.py` to detect multicollinearity between `mean_atomic_radius` and `size_mismatch`. **Logic**:
 1. Calculate VIF.
 2. **If VIF > 5.0**: EXCLUDE `size_mismatch` from model input (log warning "High VIF detected for size_mismatch (VIF={vif_value})").
 3. **If VIF <= 5.0**: Retain `size_mismatch`.
 **Output**: Updated DataFrame with `size_mismatch` removed if VIF > 5.0. **Requires**: T016.
- [ ] T017a [US1] Document the VIF conflict: Add a comment in `code/features/descriptors.py` explaining the VIF handling logic and flag this as a known limitation in `results/metrics.json` if VIF > 5.0. **Requires**: T017.
- [ ] T022 [US1] Save cleaned dataset to `data/processed/clean_mg_data.parquet` with checksum manifest using `compute_sha256` from T005a. **Validation**: Verify that columns `composition`, `cte`, `mean_atomic_radius`, `electronegativity_var`, `vec`, `size_mismatch` (if retained) are present. **Requires**: T016, T017.
- [ ] T018 [US1] Implement data splitting logic in `code/modeling/train.py`: **Primary**: Stratified split by `alloy_family` (Zr, Pd, Fe) as required by FR-003. **Fallback**: If any family has < 5 samples causing empty test sets, revert to random split. **Condition**: If N < 50, allow downgrading to Hold-Out or LOO as per Plan Phase 2. **Requires**: T022.
- [X] T019 [US1] Implement conditional validation strategy selection in `code/modeling/train.py`: 5-fold (N≥50), Hold-Out (20≤N<50), LOO (N<20). **Log Format**: If stratification fails, log "DEV: FR-003 stratification failed, using random split". If N-based strategy is used, log "DEV: FR-003 5-fold skipped due to N<50" and write `{"spec_deviation_FR003": "N<50_downgrade"}` to `results/metrics.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train baseline linear regression and random forest models using scikit-learn on CPU, performing k-fold cross-validation to tune hyperparameters within strict resource limits.

**Independent Test**: Can be fully tested by executing the training pipeline on a sample subset and verifying that the 5-fold cross-validation scores (R², MAE) are generated as non-null, finite numbers, and that the final model is saved without exceeding standard RAM or CPU core constraints.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test: Add `tests/unit/test_baseline.py::test_null_model_predicts_mean` to verify null model baseline calculation. Assert: `NullModel().predict(X) == y_train.mean()`.
- [X] T024 [P] [US2] Integration test: Add `tests/integration/test_training.py::test_training_pipeline_5fold_cv` to verify full training pipeline with 5-fold CV. Assert: `cv_scores` are finite and `model` is saved.

### Implementation for User Story 2

- [ ] T025-Load [US2] Implement `code/modeling/train.py` to load `data/processed/clean_mg_data.parquet`. **Logic**: Read parquet, drop rows with NaN. **Output**: DataFrame `df`. **Requires**: T022.
- [ ] T025-Feat [US2] Implement feature matrix preparation in `code/modeling/train.py`. **Features**: Select `mean_atomic_radius`, `electronegativity_var`, `vec`, `size_mismatch` (if retained). **Output**: Save preprocessed X, y to `data/processed/train_test_split.npz`. **Requires**: T025-Load.
- [ ] T026 [US2] Implement "Null Model" baseline (predicts mean CTE) in `code/modeling/train.py`.
- [ ] T026a [US2] Implement "Null Model" baseline as the primary baseline for SC-001. **Logic**:
 1. **Verify**: Check if elemental CTE data is available in source (MP/AFLOW/Zenodo).
 2. **If Unavailable**: Use Null Model. Log "SC-001: Elemental CTE data unavailable, using Null Model".
 3. **If Available**: Use Linear Weighted Average.
 **Note**: Explicitly acknowledge SC-001 spec-root cause if using Null Model; do not attempt to fetch elemental CTEs if not present. **Requires**: T025-Load.
- [ ] T027 [US2] Log Spec-Root Cause flag: **Always** use "Null Model" as the baseline type if elemental CTEs are unavailable per Plan Phase 2. Write `{"baseline_type": "null_model", "spec_root_cause_SC001": "elemental_cte_data_unavailable"}` to `results/metrics.json`. **Do not** check for availability dynamically; rely on T026a verification. **Requires**: T026a.
- [ ] T028 [US2] Implement Linear Regression training with k-fold cross-validation. (or selected strategy) in `code/modeling/train.py`. **Requires**: T025-Feat.
- [ ] T029 [US2] Implement Random Forest training with 5-fold CV and grid search over `max_depth` and `n_estimators` in `code/modeling/train.py`. **Requires**: T025-Feat.
- [X] T030 [US2] Enforce resource constraints: Add `n_jobs=2` and `memory_limit` to sklearn config in `code/modeling/train.py` to ensure training runs on ≤2 CPU cores and ≤7 GB RAM (no GPU).
- [ ] T031 [US2] Implement model serialization to `code/models/` directory with metadata. **Format**: Joblib (`.pkl`). **Naming**: `code/models/linear_regression_v1.pkl`, `code/models/random_forest_v1.pkl`. **Metadata**: Save as `code/models/linear_regression_v1_meta.json`, `code/models/random_forest_v1_meta.json`. **Schema**: `{model_type, hyperparams, cv_scores, timestamp}`. **Requires**: T028, T029.
- [ ] T032 [US2] Implement evaluation script in `code/modeling/evaluate.py` to calculate R², MAE, RMSE on held-out test set. **Requires**: T031.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Feature Importance Analysis (Priority: P3)

**Goal**: Perform permutation testing to validate model performance exceeds random chance and generate feature importance rankings to identify key compositional drivers.

**Independent Test**: Can be fully tested by running the significance analysis script on the trained model and verifying that a p-value is reported for all models (flagging 'Null Result' if R² ≤ 0.3), and that a ranked list of feature importances is generated where the Top-ranked features match the top-ranked features by correlation coefficient magnitude.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Unit test: Add `tests/unit/test_significance.py::test_permutation_p_value_convergence` to verify permutation test logic and p-value calculation. Assert: `p_value` is between 0 and 1.
- [X] T034 [P] [US3] Integration test: Add `tests/integration/test_analysis.py::test_divergence_ranking_match` to verify Divergence Analysis (Importance vs. Correlation). Assert: `divergence_score` is calculated.

### Implementation for User Story 3

- [ ] T035 [US3] Implement permutation test in `code/modeling/evaluate.py` with iterative convergence check. **Logic**:
 1. Start with 100 iterations.
 2. Calculate p-value.
 3. Increase iterations by 100 until p-value stabilizes (change < 0.01) or max 1000 reached.
 4. **Guard**: If N < 50, skip this step, log "Permutation test skipped for N < 50", and write `{"permutation_status": "skipped_low_n"}` to `results/metrics.json`.
 5. **Not Converged**: If loop reaches 1000 without stability, log "Permutation test did not converge at 1000 iterations" and record the final p-value.
 **Dependency**: Requires model output from T032.
- [X] T035a [US3] Handle N < 20 case: If N < 20, skip permutation test, log warning "N < 20: Permutation test skipped", and write `{"permutation_status": "skipped_low_n"}` to `results/metrics.json`.
- [X] T036 [US3] Implement significance flagging logic: Flag 'Null Result' if performance does not exceed random chance (p-value > 0.05). **Output**: Write `{"sc003_match_status": "insufficient_data_for_significance"}` to `results/metrics.json` if R² <= 0.3.
- [ ] T037 [US3] Implement feature importance extraction from Random Forest model. **Output**: Write `results/feature_importance.csv` with columns `feature`, `importance_score`, sorted by `importance_score` descending. **Requires**: T031.
- [ ] T038 [US3] Implement Pearson correlation calculation for each feature against CTE on the test split (`data/processed/test_split.parquet`). **Output**: Write `results/correlations.csv` with columns `feature`, `correlation_coefficient`, precision 4 decimals. **Requires**: T031.
- [ ] T039 [US3] Implement SC-003 Divergence Analysis in `code/modeling/evaluate.py`. **Logic**:
 1. **Verify Match**: Compare Top 3 features by importance vs. correlation.
 2. **If Match**: Report "SC-003: Match confirmed".
 3. **If Mismatch**: Perform Divergence Analysis. Calculate Spearman rank correlation coefficient between `importance_score` ranks and `correlation_coefficient` ranks.
 4. **Output**: Write `results/divergence.csv` with columns `feature, importance_rank, correlation_rank, divergence_score`.
 5. **Mandatory**: Explicitly flag `{"spec_root_cause_SC003": "linear_match_unsound_for_nonlinear_models"}` in `results/metrics.json` to acknowledge that SC-003's requirement for a match is scientifically unsound and that divergence magnitude is the valid finding per Plan Phase 3. **Requires**: T037, T038.
- [X] T040 [US3] Generate final `results/metrics.json` with R², MAE, RMSE, p-values, significance status, divergence findings, and all Spec-Root Cause flags. **Required Keys**: `baseline_type`, `spec_deviation_FR003`, `sc003_divergence_metric`, `permutation_status`, `vif_warning`, `spec_root_cause_SC003`.
- [X] T047 [US3] Implement efficiency measurement: Profile runtime and peak memory usage using `memory_profiler` during pipeline execution. **Output**: Write `{"runtime_seconds": X, "peak_memory_mb": Y}` to `results/metrics.json`. **Gate**: If `peak_memory_mb` > 7000 or `runtime_seconds` > 21600, raise `ResourceLimitExceeded` and exit with code 1. Verify against SC-004 limits (≤2 cores, ≤7 GB RAM, ≤6 hours).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `docs/` including `quickstart.md` (include API key setup, run commands, and example outputs) and `research.md` (include data sources, citations for Zhang et al., and MP/AFLOW).
- [ ] T043 Code cleanup and refactoring of `code/ingestion/` and `code/features/`: Remove unused imports, enforce line length < 88, and ensure consistent error handling.
- [X] T044 Performance optimization: Profile with `memory_profiler` (added to T002) to ensure peak RAM < 6GB for large datasets (if applicable). **Command**: `python -m memory_profiler code/main.py --train`.
- [~] T045 [P] Additional unit tests for edge cases (empty API responses, malformed formulas) in `tests/unit/`: Add `test_empty_formula`, `test_malformed_json` with specific assertions.
- [X] T046 Run quickstart.md validation: Execute `python code/main.py --validate`. **Success Criteria**: Exit code 0, `results/metrics.json` generated, no errors in logs.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **T022 (Save cleaned dataset) must complete before T025-Load (Load clean_mg_data.parquet)**.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **T032 (Evaluation) must complete before T035 (Permutation test)**.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data fetching and cleaning (T013-MP, T013-AF, T013-ZF, T014) must complete before Feature Engineering (T016) in production flow (T016 is NOT [P] in production).
- Models (T028, T029) must complete before Serialization (T031)
- Serialization (T031) must complete before Evaluation (T032)
- Evaluation (T032) must complete before Significance Analysis (T035-T040)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Descriptor calculation (T016) is sequential after T014.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test: Add tests/unit/test_descriptors.py::test_parse_formula"
Task: "Unit test: Add tests/unit/test_descriptors.py::test_calculate_weighted_mean_radius"

# Launch all models for User Story 1 together:
Task: "Implement fetch_data.py in code/ingestion/ to query Materials Project and AFLOWlib APIs using env vars"
Task: "Implement descriptors.py in code/features/ to calculate weighted mean atomic radius, electronegativity variance, VEC, size mismatch"
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
- **Critical Constraint**: FR-005 mandates a convergence check for permutation test iterations (max 1000) for any dataset with N >= 50. For N < 50, skip as per Plan Phase 0.6.
- **Critical Constraint**: 'size_mismatch' MUST be excluded from model input if VIF > 5.0 per Plan.md Phase 2.