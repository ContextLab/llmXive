# Tasks: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

**Input**: Design documents from `/specs/001-evaluating-the-correlation-between-compo/`
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-509-evaluating-the-correlation-between-compo/`) by executing: `mkdir -p data/{raw,elemental_properties,processed,evaluation,logs} code tests/contract tests/unit contracts`.
- [X] T002 Create `requirements.txt` at `projects/PROJ-509-evaluating-the-correlation-between-compo/code/` with pinned versions for: `pymatgen`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `pyyaml`, `mpdsapi`, `shap`, `eli5`, `statsmodels`, `psutil`.
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan):

- [X] T004 Create `data/` directory structure: `raw/`, `elemental_properties/`, `processed/`, `evaluation/`, `logs/` (if not done in T001).
- [X] T005 [P] Implement `contracts/` directory with `dataset.schema.yaml` and `model_output.schema.yaml` defining expected JSON/CSV schemas.
- [X] T006 [P] Setup `tests/` directory structure: `contract/`, `unit/`.
- [X] T007 Create `code/config.py` with functions `load_paths()` (returns dict of data/code paths), `load_env()` (loads environment variables), and explicit constants `ROW_THRESHOLD = 100000`, `MIN_ROWS = 5000`, `RANDOM_SEED = 42`, and `CAP_OUTLIERS = True` to manage configuration and support deterministic sampling.
- [X] T008 Configure error handling and logging infrastructure in `code/utils/logging.py`.
- [X] T008a [P] Implement `code/utils/logging.py` with a `PhaseTimer` class that logs start and end times for each pipeline phase to satisfy FR-007. **Note**: This task provides the tool; tasks T012i, T014i, T020i, T023i, T038i will invoke it. **Depends**: T008.
- [X] T009 [P] Implement `code/utils/sampling.py` with function `sample_by_chemical_family(df, target_rows, random_state)` including type hints, docstrings, and docstring examples. This function performs stratified sampling by the most abundant element.
- [X] T009a [P] Implement `code/utils/chemical_families.py` with a function `assign_chemical_family(element)` that maps the dominant element to a family (e.g., Group 1 -> Alkali, d-block -> Transition, O-containing -> Oxide) using a fixed set of rules, to be used for stratification (FR-004a).
- [X] T050a [P] Implement chunked reading logic in `code/utils/io.py` using `pandas.read_csv(chunksize=...)` to handle large datasets without loading the entire file into memory at once.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Download MP.1 dataset via MPDS API (with fallback), filter for inorganic compounds, compute multiple mean/variance descriptors, and output a clean CSV.

**Independent Test**: Run `code/ingest.py` and `code/descriptors.py` against the MPDS API; verify the output CSV contains a representative set of rows, no nulls in descriptor columns, and matches `contracts/dataset.schema.yaml`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`: Add function `test_schema_matches_yaml` that asserts `composition`, `formation_energy`, and all descriptor columns exist and are non-null.
- [X] T011 [P] [US1] Unit test for descriptor calculation logic (mean/variance of elemental properties) in `tests/unit/test_descriptors.py`: Add function `test_mean_variance_calculation` that asserts specific known values for a mock composition.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/ingest.py` to download the MP dataset using the MPDS API (requiring `MPDS_API_KEY` in CI). **Fallback Logic**: If the API fails, attempt to load from `data/raw/mp-2020.csv` (checksummed, versioned). **Failure**: If both fail, raise an exception (no synthetic fallback). **Output**: Save raw data to `data/raw/mp-2020.12.1.csv`.
- [X] T012a [US1] Implement checksum verification in `code/ingest.py`: Compute SHA-256 of the downloaded raw dataset. **Output**: Save the checksum to `data/evaluation/dataset_verification.json` and update `state/` artifact hashes. Fail if checksum mismatch.
- [X] T012b [US1] **[Critical Fail-Loudly Check]** Implement `code/ingest.py` to verify data availability AFTER T012a. **Logic**: If the dataset is empty or missing after T012/T012a, raise a `RuntimeError` with message "CRITICAL: No data available (API failed, local fallback missing). Pipeline cannot proceed." **Condition**: This task MUST run before T013a_pre. **Output**: If successful, proceed; if failed, stop pipeline. **Depends**: T012a.
- [X] T012i [US1] **[Phase Timer]** Wrap the execution of `code/ingest.py` (T012-T012b) with the `PhaseTimer` class from T008a to log start and end times for the "Ingest" phase (FR-007). **Depends**: T012b.
- [X] T013a_pre [US1] **[Assumption Validation]** Implement `code/ingest.py` to count rows in the raw dataset (after T012b) and validate against Spec Assumption 1 (>100k rows). **Output**: Log the row count to `data/logs/assumption_validation.log`. If < 100k, log a warning but proceed. **Depends**: T012b.
- [X] T013a [US1] Implement `code/ingest.py` to check the filtered dataset size against `ROW_THRESHOLD` (a predefined threshold value) defined in `code/config.py`. **Logic**: If the row count is below `ROW_THRESHOLD`, save the filtered dataset to `data/raw/mp-2020.12.1_filtered.csv`. **Output**: Log the row count. **Depends**: T012b.
- [X] T013b [US1] **[Conditional - Spec-Authorized Sampling]** If the row count exceeds `ROW_THRESHOLD`, implement `code/ingest.py` to perform stratified sampling by **Chemical Family** (using `code/utils/chemical_families.py`) using `RANDOM_SEED` (42) from `code/config.py`. **Target**: Sample to [deferred] rows. **Spec Authorization**: This sampling is explicitly authorized by Plan Assumption 2 ("Memory Constraints") and Constitution Data Hygiene rules to fit the ~7GB RAM constraint while preserving statistical power. **Failure Handling**: If sampling fails (e.g., MemoryError), raise an exception. **Output**: Save the sampled raw dataset to `data/processed/sampled_raw_data.csv` and generate a versioned manifest `data/processed/sampling_manifest.json` containing the row count, random seed, and SHA256 checksum. Log sampling stats to `data/logs/sampling.log`. **Depends**: T012b.
- [X] T013c [US1] **[Conditional]** If T013b executed, validate the impact of sampling on the "A large-scale dataset of inorganic compound entries" assumption. **Logic**: Compare sampled count to `ROW_THRESHOLD` and check if `row_count_sampled < MIN_ROWS` (a minimum threshold sufficient for statistical power). If `row_count_sampled < MIN_ROWS`, raise an exception ("Sampling reduced dataset below minimum statistical power"). **Output**: Document the data loss and representativeness in `data/logs/sampling_impact.log` as a JSON object containing: `{"row_count_original": int, "row_count_sampled": int, "sampling_ratio": float, "ks_p_value": float (if T013d ran)}`. **Depends**: T013b.
- [X] T013d [US1] **[Conditional]** If T013b executed, perform a Kolmogorov-Smirnov (KS) test comparing the distribution of `formation_energy` in the full dataset vs. the sampled subset to validate the *representativeness* of the *sampled* subset. **Parameters**: `alpha=0.05`. **Output**: Save KS statistic and p-value to `data/evaluation/sampling_statistics.json`. **Depends**: T013b.
- [X] T014 [US1] Implement `code/descriptors.py` to load `data/processed/sampled_raw_data.csv` (if T013b ran) OR `data/raw/mp-2020.12.1_filtered.csv` (if T013a ran). **Path Logic**: Check for existence of `sampled_raw_data.csv` first; if not found, use `filtered.csv`. Load elemental properties (electronegativity, radius, valence, melting point, ionization energy) using `pymatgen` or `matminer`. **Depends**: T012b AND (T013a OR T013b).
- [X] T014i [US1] **[Phase Timer]** Wrap the execution of `code/descriptors.py` (T014-T017) with the `PhaseTimer` class from T008a to log start and end times for the "Process" phase (FR-007). **Depends**: T014.
- [X] T014a [US1] Implement version hash check in `code/descriptors.py`: Verify `data/elemental_properties/` matches the expected version hash in `code/config.py`. **Condition**: If mismatch, raise an exception (Constitution Principle VI).
- [X] T015 [US1] Implement `code/descriptors.py` to compute mean and variance for the descriptors for every compound and handle missing elemental properties by excluding rows.
- [X] T015a [US1] Implement `code/descriptors.py` to apply `assign_chemical_family` (from T009a) to the dominant element of each compound and add a `chemical_family` column to the dataset. **Output**: Save to intermediate CSV before outlier detection. **Depends**: T015.
- [X] T016 [US1] Implement outlier detection in `code/descriptors.py` to calculate selected percentiles of formation energy. **Condition**: If `CAP_OUTLIERS` (from T007) is True and any values are outside these bounds, cap them to the bounds. **Else**: Log "0 capped" and save the dataset unchanged. **Output**: Save the resulting dataset (capped or uncapped) to `data/processed/computed_descriptors.csv` and log the count of capped rows to `data/logs/outliers.log`. **Depends**: T015a.
- [X] T017 [US1] Implement `code/descriptors.py` to validate the final processed dataset against `contracts/dataset.schema.yaml` and ensure all descriptor columns are non-null numeric values.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting models on CPU, evaluate with R²/MAE/RMSE, verify stratified split integrity, and perform statistical comparison.

**Independent Test**: Run `code/train.py` and `code/evaluate.py`; verify models complete within 3h on 2-core CPU, R² > 0.0, chemical family distribution TVD ≤ 0.05, and t-test results are saved.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`: Add function `test_metrics_schema` that asserts `r2`, `mae`, `rmse`, and `overfitting_ratio` keys exist in `model_metrics.json`.
- [X] T019 [P] [US2] Unit test for stratified split logic (TVD calculation) in `tests/unit/test_split_validation.py`: Add function `test_tvd_calculation` that asserts TVD is 0.0 for identical distributions and > 0.0 for different ones.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/train.py` to load `data/processed/computed_descriptors.csv` (from T016/T017) and perform a stratified split by **Chemical Family** using the algorithm in `code/utils/chemical_families.py` (FR-004a) to ensure structural diversity in the validation set. **Note**: Requires `chemical_family` column from T015a.
- [X] T020i [US2] **[Phase Timer]** Wrap the execution of `code/train.py` (T020-T022) with the `PhaseTimer` class from T008a to log start and end times for the "Train" phase (FR-007). **Depends**: T020.
- [X] T020b [US2] **[Internal Tuning Only]** Implement `code/train.py` to perform **5-fold stratified cross-validation** on the training set using the Random Forest model to estimate generalization performance, satisfying Constitution Principle VII. **Note**: This is for **internal tuning/debugging ONLY**. The **Single Source of Truth** for the final R² (per FR-004) is the hold-out validation split calculated in T023. This task does NOT contribute to the final R² metric. **Parameters**: `scoring='r2'`. **Output**: Save mean and std of CV scores to `data/evaluation/cv_scores.json` with schema: `{"mean_r2": float, "std_r2": float}`. **Depends**: T020.
- [X] T021 [US2] Implement `code/train.py` to train Random Forest Regressor (`n_estimators=200`, `max_depth=20`, `random_state=42`) on the training split.
- [X] T022 [US2] Implement `code/train.py` to train Gradient Boosting Regressor (`n_estimators=100`, `random_state=42`) on the training split.
- [X] T023 [US2] Implement `code/evaluate.py` to calculate R², MAE, and RMSE for both models on the **validation split** (hold-out). **Note**: This R² is the **Single Source of Truth** for FR-004.
- [X] T023i [US2] **[Phase Timer]** Wrap the execution of `code/evaluate.py` (T023-T027) with the `PhaseTimer` class from T008a to log start and end times for the "Evaluate" phase (FR-007). **Depends**: T023.
- [X] T023a [US2] Implement `code/evaluate.py` to compare the best model's R² against the baseline of 0.0. **Output**: Append `predictive_power` (True/False) to `data/evaluation/model_metrics.json`.
- [X] T023b [US2] Implement `code/evaluate.py` to explicitly verify and record negative R² values without converting them to null or zero, strictly adhering to FR-004b. **Output**: Ensure `model_metrics.json` contains the raw R² value even if negative, and log a specific "Negative R² Recorded" event.
- [X] T024 [US2] Implement `code/evaluate.py` to calculate Total Variation Distance (TVD) between training and validation chemical family distributions; flag if TVD > 0.05.
- [X] T025 [US2] Implement `code/evaluate.py` to detect overfitting. **Logic**: Load `train_r2` and `val_r2` (computed in T023 or re-evaluated). Calculate `overfitting_ratio = train_r2 - val_r2`. **Condition**: Always calculate and record this value, even if `val_r2 <= 0`, to preserve the record of negative performance as per FR-004b. **Output**: Append `overfitting_ratio` to `data/evaluation/model_metrics.json`.
- [X] T026 [US2] Save model artifacts to `data/evaluation/model_rf.pkl` (Random Forest) and `data/evaluation/model_gb.pkl` (Gradient Boosting) and metrics to `data/evaluation/model_metrics.json` (Single Source of Truth). **Note**: `model_metrics.json` MUST include `final_r2_source: "holdout"` to confirm compliance with FR-004.
- [X] T027 [US2] Implement `code/evaluate.py` to perform a paired t-test comparing RF vs. GB validation scores (from cross-validation or hold-out) with Benjamini-Hochberg correction, saving results to `data/evaluation/statistical_tests.json` as per Plan.md Phase 2, Step 5.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance Ranking and Sensitivity Analysis (Priority: P3)

**Goal**: Extract feature importances, validate with permutation importance, and generate Accumulated Local Effects (ALE) Plots for top features.

**Independent Test**: Run `code/importance.py` and `code/plots.py`; verify top ranked features, correlation r ≥ 0.8 between methods, and ALE plots generated for top-ranked instances with non-linearity score logged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T032 [P] [US3] Unit test for feature importance correlation calculation in `tests/unit/test_importance_validation.py`: Add function `test_correlation_threshold` that asserts the Pearson correlation logic works for known vectors.
- [X] T033 [P] [US3] Integration test for ALE generation in `tests/integration/test_ale_generation.py`: Add function `test_ale_plot_exists` that asserts a PNG file is created and non-empty.

### Implementation for User Story 3

- [X] T038 [US3] **[Depends: T026]** Implement `code/importance.py` to extract feature importances from the trained Random Forest model (artifact: `data/evaluation/model_rf.pkl`).
- [X] T038i [US3] **[Phase Timer]** Wrap the execution of `code/importance.py` (T038-T047) with the `PhaseTimer` class from T008a to log start and end times for the "Importance" phase (FR-007). **Depends**: T038.
- [X] T039 [US3] **[Mandatory FR-006 Gate]** Implement `code/importance.py` to calculate permutation importance using `sklearn.inspection.permutation_importance` with `scoring='r2'` and verify correlation (r ≥ 0.8) with tree-based importances using `scipy.stats.pearsonr`. **Condition**: If r < 0.8, log a warning and record `importance_correlation_pass` as False in `data/evaluation/permutation_importance.json`. **Output**: Save the correlation metric `r`, the permutation importance scores, and `importance_correlation_pass` (True/False). **Note**: This task is the mandatory validation for FR-006.
- [X] T040 [US3] Implement `code/importance.py` to rank and output the top descriptors to `data/evaluation/feature_ranking.json`.
- [X] T041a [US3] **[Exploratory ONLY]** **[Depends: T026, T040]** Implement `code/plots.py` to generate **SHAP Interaction Values** for the **top features** identified in T040 using `shap` to assess joint effects of correlated descriptors (Plan Phase 3 Step 4). **Note**: This is an **exploratory analysis** per the Plan, distinct from the mandatory FR-006 validation (T039). It does NOT satisfy FR-006 and does not block project advancement. **Output**: Save interaction plots or summary data to `data/evaluation/shap_interactions.json` or `data/evaluation/shap_interaction_*.png`.
- [X] T041 [US3] **[Depends: T026, T040]** Implement `code/plots.py` to generate **Accumulated Local Effects (ALE)** Plots for the top features using `shap` or `sklearn.inspection` (Plan Phase 3 Step 5). **Output**: Save PNG images to `data/evaluation/ale_*.png`.
- [X] T042 [US3] Implement `code/plots.py` to calculate a **non-linearity score** for ALE plots. **Logic**: For each ALE curve, extract the (x, y) data points. Fit linear and quadratic models to these points. Calculate `non_linearity_score = |R²_quad - R²_lin|`. **Note**: This is an **exploratory research observation** (Plan Phase 3 Step 7) to assess non-linearity; no threshold is enforced as no Success Criterion (SC) exists in spec.md. **Output**: Save `non_linear_score` to `data/evaluation/ale_metrics.json`.
- [X] T047 [US3] Implement a Multi-Collinearity Check (VIF) in `code/importance.py` using `statsmodels.stats.outliers_influence.variance_inflation_factor` to diagnose descriptor stability. **Threshold**: Flag if VIF > 10. **Output**: Save VIF scores to `data/evaluation/vif_scores.json`. (Diagnostic support for FR-005). **Depends**: T017 (Processed Descriptors).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T048a [P] Update `README.md` to include CLI usage examples (e.g., `python code/main.py --help`) and run instructions.
- [X] T048b [P] Update `README.md` to include the dependency list from `requirements.txt` and environment setup instructions.
- [ ] T049a1 [P] Refactor `code/utils/descriptors.py` to remove unused imports: Run `autoflake --in-place --remove-all-unused-imports code/utils/descriptors.py`.
- [ ] T049a2 [P] Refactor `code/utils/chemical_families.py` to remove unused imports: Run `autoflake --in-place --remove-all-unused-imports code/utils/chemical_families.py`.
- [ ] T049a3 [P] Refactor `code/utils/io.py` to remove unused imports: Run `autoflake --in-place --remove-all-unused-imports code/utils/io.py`.
- [ ] T049b [P] Refactor `code/` to enforce line length < 88: Run `black --line-length 88 code/`.
- [ ] T051a [P] Unit test for missing element edge case in `tests/unit/test_edge_cases.py`: Add function `test_missing_element_raises` that asserts the system raises an error when an element is not in the property table.
- [ ] T051b [P] Unit test for zero valence edge case in `tests/unit/test_edge_cases.py`: Add function `test_zero_valence_handling` that asserts correct handling when valence is 0.
- [ ] T051c [P] Unit test for extreme outlier edge case in `tests/unit/test_edge_cases.py`: Add function `test_extreme_outlier_capped` that asserts values outside bounds are capped correctly.
- [ ] T052a [P] Validate `research.md` content: Ensure `research.md` includes specific metrics from `model_metrics.json`, `vif_scores.json`, and `ale_metrics.json` and references the ALE plot files.
- [ ] T053a [US3] Aggregate metrics: Write a script to load `model_metrics.json`, `vif_scores.json`, and `ale_metrics.json` and prepare a summary dictionary.
- [ ] T053b [US3] Generate VIF section: Write the VIF results and interpretation to `research.md`, explicitly referencing `vif_scores.json`.
- [ ] T053c [US3] Generate ALE section: Write the ALE plot references and non-linearity scores to `research.md`, explicitly referencing `ale_metrics.json` and `ale_*.png` files.
- [ ] T053d [US3] Write final `research.md`: Combine sections into `research.md` ensuring all metrics trace to specific JSON artifacts (Constitution Principle IV).

---

## Phase 7: Plan & Spec Updates

**Purpose**: Documentation updates required by the implementation process

- [ ] T026a [Plan] Update `plan.md` "Single Source of Truth" section to explicitly include `permutation_importance.json`, `feature_ranking.json`, and `vif_scores.json` as required artifacts.
- [ ] T054 [Plan] Update `plan.md` "Phase 0: Data Ingestion" to explicitly mandate that the fallback mechanism (if API fails) must load from `data/raw/mp-2020.csv` ONLY if a valid SHA-256 checksum match is found; otherwise, raise an exception. This clarifies the "Fail Loudly" requirement in FR-001.
- [ ] T055 [Plan] Update `plan.md` "Phase 2: Model Training" to explicitly state that the stratified split must use the `chemical_family` column generated in T009a/T015a, and that the The split ratio must be configured with a majority portion for training and a minority portion for testing. unless `ROW_THRESHOLD` logic in T013b dictates a different sampling strategy.
- [ ] T056 [Plan] Update `plan.md` "Phase 3: Feature Importance" to clarify that SHAP interaction values (T041a) are exploratory and not part of the mandatory FR-006 validation, which is strictly permutation importance correlation.
- [ ] T057 [Plan] Update `plan.md` "Assumptions" section to document the specific sampling strategy (if T013b is triggered) including the target row count (50k) and the statistical test (KS test) used to validate representativeness, ensuring the "Large real datasets" rule is followed.
- [ ] T058 [Plan] Update `plan.md` "Non-Functional Requirements" to explicitly state that the pipeline must fail immediately (raise exception) if the `chemical_family` assignment logic in `code/utils/chemical_families.py` encounters an element not covered by the fixed rule set, preventing silent data corruption.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Plan Updates (Phase 7)**: Can be done after implementation

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`computed_descriptors.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output (`model_rf.pkl`)

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

### Model Training Checkpoint (Formal Gate)

The **Model Training Checkpoint** is a formal gate that must be passed before T038 can execute.
- **Entry Criteria**: T020, T021, T022, T023, T023a, T023b, T024, T025, T026, T027 must be completed successfully.
- **Artifact Verification**: `data/evaluation/model_rf.pkl`, `data/evaluation/model_gb.pkl`, and `data/evaluation/model_metrics.json` must exist and pass schema validation.
- **Failure Handling**: If T025 fails (e.g., due to `val_r2 <= 0`), the checkpoint is considered passed only if `overfitting_ratio` is correctly calculated and logged. If T026 fails to produce artifacts, the checkpoint fails and T038 is blocked.
- **Note**: T020b (Internal Tuning) is **NOT** a blocking entry criterion for this checkpoint.

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