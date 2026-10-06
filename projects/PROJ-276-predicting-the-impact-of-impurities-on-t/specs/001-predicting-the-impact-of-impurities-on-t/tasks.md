# Tasks: Predicting the Impact of Impurities on the Superconductivity of Magnesium Diboride

**Input**: Design documents from `/specs/001-impurity-impact-mgb2/`
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

## Phase 0: Pre-Flight & Contradiction Resolution

**Purpose**: Address critical spec contradictions and document deviations before implementation begins. **BLOCKS ALL PHASES**.

- [ ] T000a [P] **CRITICAL**: Generate Contradiction Report. Create `state/contradictions/FR-006-runtime-bug.md`. The file MUST contain a valid, pretty-printed JSON object with keys: `original_spec_value` (a specified duration), `constitution_value` (30 mins), `resolution` ("Enforce 30 mins per Constitution"), and `rationale`.
- [ ] T000b [P] **CRITICAL**: Generate Corrected Spec Text. Create `state/contradictions/corrected_spec_text.md` containing the exact text to replace FR-006 ("30-minute runtime limit") and FR-004 ("Feature Permutation Test") in `spec.md`.
- [ ] T000c [P] **CRITICAL**: Apply Spec Update. Edit `projects/PROJ-276-predicting-the-impact-of-impurities-on-t/specs/001-impurity-impact-mgb2/spec.md`. Replace FR-006 text with "30-minute runtime limit" and FR-004 text with "Feature Permutation Test". Ensure the file is saved and the change is committed.
- [X] T000d [P] **CRITICAL**: Document Deviation. Create `docs/fr004_deviation_report.md` explicitly documenting why the Spec's original "Target Permutation Test" (shuffling Y) was not implemented (methodologically invalid) and confirming the use of "Feature Permutation" as per Plan. This task depends on T000b.
- [ ] T000e [P] **CRITICAL**: Re-Validate Tasks. Run the task validation logic against the *updated* `spec.md` to ensure all tasks align with the new text. <!-- ATOMIZE: requested -->

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure. **BLOCKED BY T000a, T000b, T000c, T000d, T000e**.

- [ ] T001 [P] Create project structure per implementation plan. Execute: `mkdir -p src/ingestion src/modeling src/visualization src/utils tests/contract tests/integration tests/unit data/raw data/processed docs`. Verify with `tree` output.
- [X] T002 [P] Initialize a Python project with requirements.txt. Execute: `pip freeze > code/requirements.txt` containing: pandas, scikit-learn, xgboost, pymatgen, requests, pyyaml, matplotlib, seaborn, statsmodels, pytest.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools. Create `py.toml` and `ruff.toml` with non-empty config.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **BLOCKED BY Phase 0**.

- [ ] T004 [P] Implement `src/utils/constants.py` with atomic weights, unit conversion factors (Kelvin, GPa), and VIF threshold constants (5.0).
- [ ] T005 [P] Implement `src/utils/logging.py` with standardized loggers for ingestion, modeling, and visualization.
- [ ] T006 [P] Implement `src/utils/data_provenance.py` with function `generate_provenance_header(source: str, timestamp: str, version: str) -> str`. The return value MUST be a UTF-8 encoded, minified JSON string formatted as `# PROVENANCE: {...}`. Create `tests/unit/test_provenance.py` to verify the output format.
- [ ] T007 [P] Setup `tests/unit/test_constants.py` and `tests/unit/test_logging.py` to verify utility modules.
- [ ] T008 [P] Configure environment variable handling for API keys (Materials Project) in `src/utils/config.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Consolidate MgB₂ data from Materials Project API and SuperCon dataset, standardize units, and filter for valid entries.

**Independent Test**: T015 (Integration Test) orchestrates T012, T013, and T014 sequentially to produce `data/processed/mgb2_clean.csv` with non-null Tc/impurities, standardized atomic %, and provenance header.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py` (verify columns: Tc, impurities_atomic_pct, temp_K, pressure_GPa)
- [X] T010 [P] [US1] Unit test for unit conversion logic in `tests/unit/test_preprocessing.py` (weight% to atomic% edge cases)
- [X] T011 [P] [US1] Unit test for data filtering in `tests/unit/test_ingestion.py` (verify rows with missing Tc/impurities are dropped).
- [X] T011b [P] [US1] Unit test for synthetic null generation. Create `tests/unit/data/synthetic_nulls.csv` with a representative set of rows and a fixed set of columns (Tc, impurity_C, impurity_O, temp_K, pressure_GPa, source). A subset of rows MUST have null `impurity_C` values to test data handling. The test verifies the file schema and null count.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `src/ingestion/download_materials_project.py` to fetch Mg-B entries via API, handling rate limits and empty responses (exit code 1 if empty). **Constraint**: Must raise `RuntimeError` if no MgB2 entries are found; do NOT generate synthetic fallback data. **Provenance**: If a cached file exists, verify its checksum; if valid, attach provenance header (from T006) immediately and exit. If checksum mismatch, abort with exit code 1. If no cache, fetch, verify checksum, then attach provenance header immediately.
- [ ] T013 [P] [US1] Implement `src/ingestion/download_supercon.py` to fetch `taqwa92/cm.mgb2` from HuggingFace; **FAIL with exit code 1 if >50% of entries lack impurity columns**. **Provenance**: If a cached file exists, verify its checksum; if valid, attach provenance header (from T006) immediately and exit. If checksum mismatch, abort with exit code 1. If no cache, fetch, verify checksum, then attach provenance header immediately.
- [X] T013b [P] [US1] Integration test for SuperCon exit code. Create `tests/integration/test_supercon_exit.py` that invokes `download_supercon.py` with the synthetic null dataset (T011b) and verifies `sys.exit(1)`.
- [ ] T014 [US1] Implement `src/ingestion/preprocess.py` to merge datasets, convert units (weight% -> atomic%), handle synthesis ranges (midpoint imputation), and attach provenance metadata. **Merge Logic**: The final CSV header MUST be a single-line minified JSON comment block `# PROVENANCE: {sources: [list of raw file headers], timestamp:...}` that aggregates provenance from T012 and T013 raw files. **Verification**: Ensure provenance metadata is attached to CACHED files (bypassing T012/T013) as per FR-001. This task depends on T012 and T013 completing and utilizes the `generate_provenance_header` function defined in T006.
- [X] T015 [US1] Implement `tests/integration/test_pipeline.py` to run full ingestion flow (T012->T013->T014) and verify `mgb2_clean.csv` integrity (count > 0, no nulls in target columns)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Selection (Priority: P2)

**Goal**: Train Linear Regression, Ridge Regression, Random Forest, and XGBoost models with strict CPU limits, select best via cross-validated R².

**Independent Test**: Running `src/modeling/train.py` produces `data/processed/best_model.pkl` and a metrics report listing R²/MAE for all models.

### Tests for User Story 2

- [X] T016 [P] [US2] Unit test for stratified splitting logic in `tests/unit/test_modeling.py` (verify rare impurity binning)
- [X] T017 [P] [US2] Unit test for hyperparameter grid limits in `tests/unit/test_modeling.py` (verify ≤10 combinations enforced)

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `src/modeling/train.py` to load `mgb2_clean.csv`, perform stratified split (impurity type), and train **Linear Regression**, **Ridge Regression** (Plan-authorized for collinearity), Random Forest, and XGBoost.
- [ ] T019 [US2] Implement hyperparameter tuning logic in `src/modeling/train.py` with a hard cap on the number of grid combinations. **Watchdog**: Implement a runtime watchdog using the `timeout` command wrapper (e.g., `timeout a sufficient duration python train.py`) to enforce the **time limit** mandated by Constitution Principle VII. If exceeded, the script MUST `sys.exit` with a clear error message indicating a non-zero termination status.
- [ ] T020 [US2] Implement model selection logic in `src/modeling/train.py` to choose best model by cross-validated R² and save `best_model.pkl`. **Output**: Save `best_model.pkl` and a summary JSON of all model scores.
- [ ] T021 [US2] Generate `data/processed/model_metrics.json` containing R², MAE, and hyperparameters for all trained variants
- [ ] T022 [US2] Implement `tests/integration/test_modeling.py` to verify `best_model.pkl` loads and predicts on held-out data

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Interpretation (Priority: P3)

**Goal**: Validate impurity impact significance (p < 0.05) and generate Partial Dependence Plots for top 3 impurities.

**Independent Test**: Running `src/modeling/significance_test.py` and `src/visualization/plot_pdp.py` produces a report with p-values and 3 PDF/PNG plots.

**Logical Flow**: T025 (Implement Test Logic) -> T026a (Generate Reduced Set) -> T026b (Execute Test on Reduced Set).

### Tests for User Story 3

- [X] T023 [P] [US3] Unit test for ANOVA calculation in `tests/unit/test_significance.py` (verify p-value output for linear model)
- [X] T024 [P] [US3] Unit test for Permutation Test in `tests/unit/test_significance.py` (verify null distribution generation for tree models)

### Implementation for User Story 3

- [ ] T025 [US3] Implement `src/modeling/significance_test.py` to perform ANOVA (Linear) or **Feature Permutation Importance** (shuffling feature column X, re-predicting, comparing to baseline) for tree models. **Logic**: This implements the Plan's correction to FR-004. Filter features by p < 0.05. **Output**: Functions `run_anova` and `run_feature_permutation` must be exported. **Reproducibility**: MUST save the full null distribution array (potentially thousands of values) to `data/processed/null_distribution.npy` using NumPy, and save the resampling parameters (seed, n_resamples, method) to `data/processed/permutation_params.json`. This ensures the exact p-value calculation can be reproduced. **Input**: `data/processed/mgb2_clean.csv` and `data/processed/best_model.pkl`.
- [ ] T026a [US3] Implement `src/modeling/significance_test.py` to calculate VIF for all predictors. If VIF ≥ 5.0, **group** collinear predictors by creating a composite feature `impurity_block` (sum of normalized values) or remove them. **Output**: Generate `data/processed/grouped_features.csv` (if grouping) or `data/processed/reduced_feature_set.csv` (if removal). **Strategy**: Select the strategy that yields lower VIF for the next step. This task depends on T025 for the core test logic.
- [ ] T026b [US3] **DEPENDS ON: T026a** [US3] **Execute Significance Test**. Re-run significance testing logic on the reduced feature set. **Input**: `data/processed/reduced_feature_set.csv` (if removal) OR `data/processed/grouped_features.csv` (if grouping) generated by T026a. **Call**: Explicitly call `run_anova` or `run_feature_permutation` from T025. **Output**: Generate `data/processed/significance_results_reduced.json` with schema: `{method: str, p_value: float, timestamp: str, features: [{name, p_value}]}`.
- [ ] T027 [US3] Implement `src/visualization/plot_pdp.py` to generate Partial Dependence Plots for the top significant impurities (ΔTc per atomic %)
- [ ] T028 [US3] Implement `src/modeling/significance_test.py` to generate a "Rule of Thumb" table. **Output**: `data/processed/rule_of_thumb.csv` with schema: `Impurity`, `ΔTc_per_atomic_pct`, `Method` (Coefficient or SHAP).
- [ ] T029 [US3] Implement `tests/integration/test_validation.py` to verify p-values are reported and plots are generated for significant impurities only

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates: Update `README.md` with Installation, Usage, Data Sources, and API Key Setup sections; update `docs/` with final architecture diagrams
- [ ] T031 [P] Code cleanup: Refactor `src/ingestion/preprocess.py` to reduce cyclomatic complexity < 10. Extract helper functions for data merging and unit conversion into separate modules to achieve this metric.
- [ ] T032 [P] Performance optimization: Profile pipeline runtime using `cProfile`; optimize data loading in `preprocess.py` and grid search in `train.py` to ensure total runtime < 30 mins on GitHub Actions.
- [ ] T033 [P] Run `quickstart.md` validation
- [ ] T034 Update `data-model.md` with final entity definitions derived from implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Pre-Flight)**: No dependencies - MUST start immediately. **BLOCKS Phase 1**.
- **Setup (Phase 1)**: **Depends on T000a, T000b, T000c, T000d, T000e completion**. Explicitly requires T000a-T000e to be resolved before any setup tasks begin.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on trained model from US2

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
# Launch all tests for User Story 1 together:
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Unit test for unit conversion logic in tests/unit/test_preprocessing.py"
Task: "Unit test for data filtering in tests/unit/test_ingestion.py"
Task: "Integration test for SuperCon exit code in tests/integration/test_supercon_exit.py"

# Launch implementation tasks (sequential dependency):
Task: "Implement download_materials_project.py" -> "Implement download_supercon.py" -> "Implement preprocess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Contradiction Resolution (T000a-T000e)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

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