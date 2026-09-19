# Tasks: Predicting the Impact of Processing Temperature on the Grain Size of Rolled Aluminum Alloys

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per plan.md structure)
- Paths shown below assume single project - adjusted based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per `plan.md` (directories: `code/`, `data/raw/`, `data/processed/`, `data/artifacts/`, `tests/`, `state/`, `state/projects/`). **Verification**: Run `ls -R` to confirm all directories exist.
- [X] T002 Initialize Python 3.11 project with `code/requirements.txt` (pandas, scikit-learn, numpy, requests, pyyaml, memory-profiler, seaborn, pytest)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data ingestion infrastructure required by FR-001.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` with paths, `GITHUB_ACTIONS_TIMEOUT=5h`, and hyperparameter grids
- [ ] T005 [P] Implement `code/main.py` orchestration entry point with hard timeout enforcement (signal/alarm or `signal` module) and runner verification (check `ubuntu-latest`, no GPU, CPU count)
- [X] T006 [P] Create `code/__init__.py` and `tests/__init__.py`
- [X] T007 Setup `state/projects/PROJ-386-predicting-the-impact-of-processing-temp.yaml` schema. **Action**: Create file with keys `artifact_hashes` (map) and `updated_at` (timestamp). **Verification**: Validate YAML structure.
- [X] T008 Implement `code/data/__init__.py` and `code/modeling/__init__.py`
- [X] T043 [P] [Foundational] Implement `code/data/ingestion.py` **Streaming Loader Function**. **Function**: `load_streaming_dataset(url, chunk_size=10000)`. **Logic**: Use `pandas.read_csv(..., chunksize=...)` or `datasets.load_dataset(..., streaming=True)` to process large files without loading into RAM. **Constraint**: Must NOT fall back to synthetic data; raise `RuntimeError` on failure. **Output**: Returns a `pandas.DataFrame` (if small) or a `datasets.Dataset` streaming object. **Verification**: Confirm memory usage remains flat (<1GB) during load.
- [X] T044 [P] [Foundational] Implement `code/data/ingestion.py` **URL Verification Function**. **Function**: `verify_source_urls(urls)`. **Logic**: Send HEAD requests to all configured public dataset URLs (NOMAD, OpenML) to confirm accessibility. **Output**: Returns a list of valid URLs or raises `ValueError` with "Source Unreachable". **Verification**: Confirm script exits with error if any URL fails.
- [X] T049 [P] [Foundational] Implement `code/data/ingestion.py` **Online Statistics Aggregator**. **Function**: `accumulate_streaming_stats(chunk_iterable)`. **Logic**: Iterate over chunks from T043, updating running mean, count, and null counts for critical columns (Temp, Composition, Grain Size) in memory without storing the full dataset. **Output**: Returns a `dict` of statistics to be saved in `data/artifacts/streaming_stats.json`. **Verification**: Confirm stats match a full-load calculation on a small test set.
- [X] T050 [P] [Foundational] Implement `code/data/ingestion.py` **Schema Pre-check Function**. **Function**: `check_schema_preconditions(url)`. **Logic**: Fetch a small sample (first 100 rows) of the dataset at `url` and verify the presence of 'rolling temperature', 'full alloy composition', and 'grain size' columns. **Output**: Returns `True` if schema matches, `False` otherwise. **Verification**: Confirm function returns `False` for a mock CSV with missing columns.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and Variable Verification (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and validate availability of rolling temperature, alloy composition, and grain size data from public sources. Halt with clear error if data is missing.

**Independent Test**: Execute `code/data/ingestion.py` and verify output CSV has non-empty columns for temperature, Mg/Si/Cu, and grain size, OR system halts with Exit Code 1 and specific "Data Missing" log.

### Tests for User Story 1

- [X] T009 [P] [US1] Contract test for schema pre-check logic in `tests/contract/test_ingestion_schema.py` (verify skip logic for missing fields)
- [X] T010 [P] [US1] Unit test for filtering logic in `tests/unit/test_filtering.py` (verify rows with missing temp/grain_size are excluded)
- [X] T011 [P] [US1] Integration test for "Data Missing" halt scenario in `tests/integration/test_data_halt.py` (verify Exit Code 1 when all sources fail)

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data/ingestion.py` schema pre-check logic (aggregate list of missing variables across all skipped sources to support error logging)
- [X] T013 [US1] Implement `code/data/ingestion.py` download and parsing logic (fetch real data from verified URLs; handle CSV/JSON formats; use T043 streaming loader for large files)
- [X] T014 [US1] Implement `code/data/ingestion.py` filtering and validation logic (exclude rows with null critical variables; report final dataset size)
- [X] T014b [US1] Implement `code/data/ingestion.py` **Pure Aluminum Check**. **Function**: `check_purity(df)`. **Logic**: Filter rows where all alloying elements (Mg, Si, Cu, etc.) are zero or missing. If >90% of data is pure aluminum, raise `ValueError` with message: "Dataset insufficient for interaction analysis: >90% pure aluminum". **Verification**: Confirm script halts with specific error on pure-Al test data. **Dependency**: T014 must be complete.
- [X] T015 [US1] Implement `code/data/ingestion.py` "Critical Variables Missing" halt logic (**Raise SystemExit(1) after logging to stderr** with message: "Critical variables missing from all sources: [list of missing variables]")
- [X] T016 [P] [US1] Create `data/raw/` storage logic with SHA-256 checksum generation in `code/data/ingestion.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Interaction Feature Engineering and Baseline Modeling (Priority: P2)

**Goal**: Generate interaction features (Temp × Element), normalize data, and train a baseline linear regression model on residuals to establish main effects.

**Independent Test**: Run `code/data/preprocessing.py` and `code/modeling/baseline.py` on a small sample; verify output includes interaction columns and a model object with coefficients for main effects and interactions.

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for interaction feature generation in `tests/unit/test_feature_engineering.py` (verify `Temp × Mg` column creation)
- [X] T018 [P] [US2] Unit test for residualization logic in `tests/unit/test_residualization.py` (verify residuals against Alloy Series and Composition)
- [X] T019 [P] [US2] Contract test for baseline model output schema in `tests/contract/test_baseline_output.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/data/preprocessing.py` interaction feature generation (`Temperature × %Mg`, `Temperature × %Si`, etc.) with verification step to confirm columns exist.
- [ ] T021 [P] [US2] Implement `code/data/preprocessing.py` normalization (StandardScaler) for all numeric features with verification step to confirm scaling.
- [ ] T022 [US2] Implement `code/data/preprocessing.py` residualization logic (Regress Grain Size vs. Alloy Series + Composition; store residuals) with verification step to confirm residuals are uncorrelated with Alloy Series.
- [ ] T022c [P] [US2] Implement `code/data/preprocessing.py` **Alloy Series Extraction**. **Function**: `extract_alloy_series(df)`. **Logic**: Identify or derive the 'Alloy Series' column from the preprocessed data (handle missing/encoded series). **Output**: Returns a numpy array of group labels. **Verification**: Confirm the array is non-empty and matches the number of rows. **Dependency**: T022 (Residualization) must be complete to ensure 'Alloy Series' is available. <!-- FAILED: unspecified -->
- [ ] T022d [P] [US2] Implement `code/data/preprocessing.py` **GroupKFold Splitter Logic**. **Function**: `create_group_kfold_splitter(groups)`. **Logic**: Instantiate `sklearn.model_selection.GroupKFold` with the groups from T022c. **Output**: Return the `GroupKFold` splitter object. **Verification**: Confirm the splitter produces non-overlapping train/test sets where no 'Alloy Series' appears in both. **Dependency**: T022c must be complete.
- [ ] T023 [US2] Implement `code/data/preprocessing.py` collinearity detection. **Function**: `detect_collinearity(df)`. **Input**: Preprocessed DataFrame. **Logic**: Compute correlation matrix, flag pairs with correlation > 0.8. **Output**: Write `data/artifacts/collinearity_report.json` with schema `{ "flagged_pairs": [ ["feature1", "feature2"],... ] }`. **Verification**: Confirm file exists and contains valid JSON with `flagged_pairs`.
- [X] T024 [US2] Implement `code/modeling/baseline.py` Linear Regression training on residuals with interaction terms. **Dependency**: T022d must be complete to provide the `GroupKFold` splitter for validation.
- [X] T025 [US2] Implement `code/modeling/baseline.py` coefficient extraction and logging (R², MAE, coefficients for Temp, Composition, Interactions) **AND** logic to check `data/artifacts/collinearity_report.json` (from T023) to suppress independent interpretation for flagged pairs, framing them descriptively as joint effects. **Runtime Dependency**: T023 must complete and generate `data/artifacts/collinearity_report.json` before T025 executes. **Dependency**: T023 must be complete.
- [X] T026 [US2] Implement `code/modeling/baseline.py` "Limited Interaction Effects" flagging logic (if interaction coefficients ~0)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Non-Linear Interaction Modeling and Sensitivity Analysis (Priority: P3)

**Goal**: Train a Random Forest model with grid search to capture non-linear interactions, perform sensitivity analysis on thresholds, and generate partial dependence plots.

**Independent Test**: Run `code/modeling/rf_model.py` with grid search; verify best hyperparameters selected, R² recorded, and sensitivity report generated showing stability of top-5 terms across thresholds.

### Tests for User Story 3

- [X] T027 [P] [US3] Unit test for grid search timeout fallback in `tests/unit/test_rf_timeout.py` (verify fallback to single-pass if >4h simulated)
- [X] T028 [P] [US3] Unit test for sensitivity analysis logic in `tests/unit/test_sensitivity.py` (verify threshold sweep across a range of low-magnitude values)
- [X] T029 [P] [US3] Integration test for full RF pipeline in `tests/integration/test_rf_pipeline.py`

### Implementation for User Story 3

- [X] T030 [US3] Implement `code/modeling/rf_model.py` Random Forest training with GridSearchCV (n_estimators: 50-200, max_depth: -20) **AND** hard timeout enforcement: detect -hour elapsed time, interrupt GridSearchCV, and re-run with n_estimators=100, max_depth=10 if timeout occurs. **Consume residuals from T022 and collinearity report from T023.** **Dependency**: T023 must be complete before T030 execution.
- [X] T032 [US3] Implement `code/analysis/diagnostics.py` **Unified Sensitivity Analysis**. **Function**: `run_sensitivity_analysis(model)`. **Logic**: (1) **Threshold Sweep**: identify **top-k significant interaction terms by Feature Importance**, sweep thresholds {0.01, 0.05, 0.1}, calculate **stability percentage** (>80% required). Handle both grid-search and single-pass (fallback) models. **Output**: Generate `data/artifacts/sensitivity_report.json` with schema `{ "threshold_sweep": {...}, "stability_pct": float }`. **Verification**: Confirm file exists and contains valid JSON. **Dependency**: T030 must be complete.
- [X] T046 [US3] Implement `code/analysis/reporting.py` **Confounder Proxy Detection and Report**. **Function**: `generate_confounder_report(df, model)`. **Logic**: (1) **Detection**: Scan dataset columns for proxy variables (e.g., 'strain_rate', 'cooling_rate'). (2) **Analysis**: If proxies exist, refit model and calculate R² delta. If absent, set status to "N/A". (3) **Artifact**: Generate `data/artifacts/confounder_report.json` with schema `{ "status": "computed" | "N/A", "proxy_variables": [...], "r2_delta": float | null }`. **Verification**: Confirm file exists and matches schema. **Dependency**: T030 must be complete.
- [X] T033 [US3] Implement `code/analysis/reporting.py` partial dependence plot generation (visualize Grain Size vs. Temp for specific compositions)
- [X] T034 [US3] Implement `code/analysis/reporting.py` **Permutation Test** for R² improvement significance (p < 0.05) as required by SC-001. **Function**: `run_permutation_test(baseline_model, rf_model, X_test, y_test)`. **Logic**: n=1000 iterations, shuffle target, compute R² diff. **Output**: Generate `data/artifacts/permutation_test_results.json` with schema `{ "p_value": float }`. **Verification**: Confirm file exists and contains `p_value`. **Dependency**: T030 must be complete.
- [X] T047 [US3] Implement `code/analysis/reporting.py` **Collinearity Framing Logic**. **Function**: `format_collinearity_message(report)`. **Logic**: Read `data/artifacts/collinearity_report.json`. For every flagged pair, generate a text string: "Features [A] and [B] are highly correlated (r > 0.8). Their effects are reported as a joint contribution, not independent coefficients." **Verification**: Confirm final report includes these specific phrasing blocks for flagged pairs. **Dependency**: T023 must be complete.
- [ ] T035 [US3] Implement `code/analysis/reporting.py` final metrics aggregation. **Function**: `aggregate_final_metrics()`. **Logic**: Consume R²/MAE from T024/T030, **p-value from T034**, stability scores from T032, **confounder report from T046**, and **collinearity framing from T047** to enforce descriptive framing. **Output**: Generate `data/artifacts/final_report.json` with schema `{ "r2_baseline": float, "r2_rf": float, "p_value": float, "stability_score": float, "collinearity_notes": string, "confounder_status": string }`. **Verification**: Confirm file exists and contains all required keys. **Dependency**: T023, T032, T034, T046, T047 must be complete.
- [X] T036 [US3] Implement `code/analysis/reporting.py` "Associational Nature" disclaimer injection in final report

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T038 [P] [Polish] Update `state/projects/PROJ-386-predicting-the-impact-of-processing-temp.yaml` with final artifact hashes and checksums. **Action**: Read `data/raw/*`, `data/processed/*`, `data/artifacts/*`, compute SHA-256, update `artifact_hashes` map. **Verification**: Confirm YAML is valid and hashes match.
- [ ] T039 [Polish] Run end-to-end integration test on `ubuntu-latest` runner with memory profiling (`memory-profiler`) to verify ≤6.5 GB RAM usage. **Test File**: `tests/integration/test_memory_profile.py`. **Command**: `python -m memory_profiler code/main.py`. **Verification**: Parse logs for "Maximum RSS" <= 6.5GB.
- [X] T040 [Polish] Verify pipeline completion time ≤5 hours in CI simulation. **Method**: Parse CI logs for total duration. **Verification**: Confirm duration <= 5 hours.
- [X] T041 [P] [Polish] Documentation updates in `docs/` (README, quickstart.md). **Files**: `docs/README.md`, `docs/quickstart.md`. **Content**: Add installation, usage, and output description sections.
- [X] T042 [P] [Polish] Code cleanup and refactoring. **Scope**: All files in `code/`. **Action**: Remove debug prints, optimize imports. **Verification**: Run `grep -r "print(" code/` (excluding test files) to ensure 0 matches.
- [X] T048 [US3] Implement `code/analysis/reporting.py` **Threshold Stability Visualization**. **Function**: `plot_threshold_stability(report)`. **Logic**: Generate a plot showing the number of "significant" interaction terms vs. threshold value (0.01, 0.05, 0.1). Highlight the stability metric (>80%). **Verification**: Confirm `data/artifacts/threshold_stability.png` is generated. **Dependency**: T032 must be complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T043, T044, T049, T050 are in Phase 2 to support US1 ingestion.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - US1 (Data) must complete before US2 (Preprocessing) and US3 (Modeling) can run effectively, though code for US2/US3 can be written in parallel.
 - US2 (Baseline) must complete before US3 (RF) to establish the baseline comparison.
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (Code only)
- **User Story 2 (P2)**: Depends on US1 data output (Runtime dependency); Code can start after Foundational.
- **User Story 3 (P3)**: Depends on US2 baseline output (Runtime dependency); Code can start after Foundational.

### Within Each User Story

- Tests (T009-T011, T017-T019, T027-T029) MUST be written and FAIL before implementation
- Models/Preprocessing (T020-T022) before Modeling (T024-T026)
- Core implementation before integration
- Story complete before moving to next priority (for execution order)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Once Foundational phase completes, code for US1, US2, US3 can be written in parallel by different team members
- All tests for a user story marked [P] can run in parallel
- Implementation tasks within a story marked [P] (e.g., T012, T017, T020) can run in parallel if file conflicts are avoided
- **Note on Execution Order**: While T012, T013, T014 can be developed in parallel, their **runtime execution** is strictly sequential: T012 (Pre-check) -> T013 (Download) -> T014 (Filter). T013 and T014 are NOT marked [P] to prevent execution parallelism.

### Critical Runtime Execution Order

- **T012 (Pre-check) -> T013 (Download) -> T014 (Filter) -> T014b (Purity Check)**: Strict sequential execution required for data ingestion.
- **T022 (Residualization)** MUST complete and produce residuals **before** T024 (Baseline Training) can consume them.
- **T022c (Extraction)** -> **T022d (Splitter)** -> **T024/T030**: Strict sequential execution for GroupKFold logic.
- **T023 (Collinearity Report)** MUST be generated before T025 (Coefficient Extraction) and T030 (RF Training) can consume it to enforce framing.
- **T030 (Model Training)** MUST complete and produce model artifact **before** T032 (Sensitivity Analysis), T034 (Permutation Test), and T046 (Confounder Report) can load it.
- **T032, T034, T046, T047** MUST complete before T035 (Final Metrics) can aggregate results.
- **T001 (Project Structure)** and **T007 (State Schema)** MUST be complete before T016 (Checksum generation) and T038 (Final State update) can execute.
- **T043 (Streaming)**, **T044 (URL Verification)**, **T049 (Stats)**, **T050 (Pre-check)** MUST be implemented before T013 (Download) in the final execution flow to handle large datasets safely.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
pytest tests/contract/test_ingestion_schema.py
pytest tests/unit/test_filtering.py
pytest tests/integration/test_data_halt.py

# Launch implementation tasks in parallel (different files/functions):
# Task: "Implement schema pre-check function in code/data/ingestion.py"
# Task: "Implement download and parsing logic in code/data/ingestion.py"
# Task: "Implement filtering and validation logic in code/data/ingestion.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Ingestion & Validation)
4. **STOP and VALIDATE**: Test User Story 1 independently (Verify data availability or "Data Missing" halt)
5. Deploy/demo if ready (as a data validation tool)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (Data Validation MVP)
3. Add User Story 2 → Test independently → Demo (Baseline Modeling)
4. Add User Story 3 → Test independently → Demo (Full Pipeline)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Preprocessing & Baseline)
 - Developer C: User Story 3 (RF & Analysis)
3. Stories complete and integrate independently (Data flows from A → B → C)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must be executable on GitHub Actions free-tier (CPU-only, cores, ~7GB RAM, ≤6h). No GPU, no 8-bit quantization, no large models.
- **Critical Constraint**: No fabricated data. All data must come from real, verified public sources (NOMAD, OpenML, etc.) as per `plan.md`.
- **Execution Flow**: Runtime dependencies (e.g., T022 -> T024) are strict; implementation tasks (e.g., T020, T021) can be developed in parallel.
- **Revision Note**: T043/T044/T049/T050 moved to Phase 2 to support FR-001 streaming requirements. T014b added to Phase 3 for purity check. T022c/T022d added to Phase 4 for GroupKFold atomization. T046/T047 moved to Phase 5 to resolve data-flow dependency for T035. T037 removed.
