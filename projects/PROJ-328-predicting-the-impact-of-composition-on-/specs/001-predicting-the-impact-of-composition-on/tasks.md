# Tasks: Predicting the Impact of Composition on the Vickers Hardness of Solder Alloys

**Input**: Design documents from `/specs/001-predict-solder-hardness/`
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

 Tasks MUST be organized by user story so each story can:
 - Be implemented independently
 - Be tested independently
 - Be delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure per implementation plan: `projects/PROJ-328-predicting-the-impact-of-composition-on-/data/raw`, `data/processed`, `data/outputs`, `code/`, `code/ingestion`, `code/features`, `code/models`, `code/evaluation`, `code/visualization`, `tests/`, `models/`. **CRITICAL**: Create these exact directories.
- [X] T002 Create `requirements.txt` at `projects/PROJ-328-predicting-the-impact-of-composition-on-/code/` with dependencies (PIN EXACT VERSIONS): `pandas`, `scikit-learn`, `xgboost`, `shap`, `numpy`, `matplotlib`, `pyyaml`, `requests`, `compositional==0.2.0`, `pdfplumber`, `pytest`, `flake8`, `black`. **CRITICAL**: Verify Python 3.11 compatibility for all listed libraries before pinning.
- [ ] T003 Configure linting (flake8/black) and formatting tools (must run after T001)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/seed.py` to pin random seeds for reproducibility (numpy, random, xgboost)
- [ ] T007 Create base data models/entities (`SolderComposition`, `CompositionalDescriptor`) in `code/models/`
- [ ] T005 [Foundational] Create scaffolding for `code/ingestion/` directory structure. **CRITICAL**: This task establishes the folder structure and placeholder files: `__init__.py`, `aggregator.py`, `cleaner.py`, `validator.py`. It is foundational, not US1 specific.
- [ ] T006 [P] Setup `code/features/` directory structure for descriptor engineering
- [ ] T008 [Constitution] Integrate and run the Reference-Validator Agent. **CRITICAL**: `research.md` MUST exist and contain verified citations. If `research.md` is missing or contains unverified citations, raise a `ConstitutionError` and halt. Do NOT generate placeholders. This task ensures the Constitution Check 'PASS' status is backed by an actual verified artifact.
- [ ] T008b [P] Configure error handling and logging infrastructure in `code/utils/`
- [X] T009 Setup environment configuration management for paths and thresholds in `code/config.py`, including `MAX_ELEMENTS` (default 5), `R2_THRESHOLDS` (default set: {0.3, 0.5, 0.6, 0.7}), `ROOM_TEMP_THRESHOLD_C` (default 25), `ROOM_TEMP_TOLERANCE_C` (default 5), and `COMPOSITION_SUM_THRESHOLD` (default 0.95). **CRITICAL**: Create `data/config/sources.yaml` **template** listing required data sources (Materials Project API key, NIST URLs, and specific PDF URLs from `research.md` to be populated).
- [ ] T009b [P] **Populate sources.yaml**: Read the verified `research.md` (from T008) and populate `data/config/sources.yaml` with the specific, verified URLs and API endpoints. **CRITICAL**: This task MUST run after T008 and before T012.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Aggregate and validate solder hardness dataset (Priority: P1) 🎯 MVP

**Goal**: Aggregate ≥100 unique solder alloy compositions with Vickers hardness from open sources into a unified dataset with validation.

**Independent Test**: Execute ingestion pipeline on GitHub Actions free-tier runner and verify output dataset contains ≥100 unique compositions with non-null hardness values and complete elemental breakdowns. If 50 ≤ N < 100, verify warning is emitted.

### Test-First: User Story 1 (OPTIONAL - only if tests requested) ⚠️
*Note: These tasks define contracts for T012-T019 and must be written before implementation code exists.*

- [X] T010 [P] [US1] Contract test for data validation schema in `tests/contract/test_data_schema.py`
- [X] T011 [P] [US1] Integration test for ingestion pipeline in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/ingestion/aggregator.py` to fetch data from verified sources: 1) Materials Project API, 2) NIST/UCI repositories, 3) Direct URLs from `data/config/sources.yaml` (populated by T009b), and 4) **Published Literature** via PDF scraping using `pdfplumber`. **CRITICAL**: Pre-check: Verify `research.md` exists and is verified (from T008). If `sources.yaml` is missing or empty, raise a `ConfigError` immediately. **CRITICAL**: If a specific source fails, log connectivity status to `data/processed/ingestion_log.txt` (non-blocking) and aggregate whatever partial data was successfully retrieved from other sources. Do NOT crash on a single failure. Instead, check the total count N: if N < 100 but >= 50, proceed and flag for warning; if N < 50, flag for critical error (to be handled by T014). **Includes full fallback logic for partial data aggregation.**
- [X] T013 [US1] Implement data cleaning and filtering logic in `code/ingestion/cleaner.py` to:
 - Exclude alloys with >5 elements (read threshold from `code/config.py` `MAX_ELEMENTS`)
 - Standardize hardness to HV units
 - Filter for room-temperature measurements only: verify column `measurement_temp_c` exists in raw data; filter where `abs(measurement_temp_c - config.ROOM_TEMP_THRESHOLD_C) <= config.ROOM_TEMP_TOLERANCE_C`. **Defaults: ROOM_TEMP_THRESHOLD_C=25, ROOM_TEMP_TOLERANCE_C=5**.
 - **Manual Review Flagging**: Identify records where `abs(measurement_temp_c - config.ROOM_TEMP_THRESHOLD_C) > config.ROOM_TEMP_TOLERANCE_C` but `<= 2 * config.ROOM_TEMP_TOLERANCE_C` and write them to `data/processed/manual_review_queue.csv` with a flag `MANUAL_REVIEW_TEMP`.
 - Validate elemental composition sums to `config.COMPOSITION_SUM_THRESHOLD` (default 0.95).
 - **Record Validation**: Log the specific records that failed the composition sum check to `data/processed/validation_logs/filtered_records.csv` with reason codes. **CRITICAL**: Generate a SHA256 checksum for `filtered_records.csv` and append the hash to `data/checksums.txt`.
 - **CRITICAL**: Write the intermediate validation status (total N, filtered count, threshold_status) to a temporary state file `data/processed/.ingestion_status.json` to ensure downstream tasks can read the exact counts.
 - Implement streaming or chunked processing for large datasets to stay within available memory constraints, using `itertools.islice` or `pandas.read_csv(chunksize=...)` if necessary.
- [X] T014 [US1] Implement validation logic in `code/ingestion/validator.py` to check for non-null hardness and complete composition. **CRITICAL**:
 1. **Calculate Composition Sums**: Explicitly calculate the sum of elemental compositions for every record.
 2. **Enforce Threshold**: If a record's composition sum is < 95%, mark it as invalid.
 3. **Threshold Check**: If total N < 50, raise `DataInsufficientError` with a clear message to halt the pipeline. If 50 <= N < 100, proceed but flag the dataset for the power limitation report.
 4. **Write Status**: Explicitly write the `threshold_status` ('N>=100', '50<=N<100', 'N<50') and the exact `warning_text` string to `data/processed/.ingestion_status.json` to ensure T019 can generate a valid report.
- [ ] T015 [US1] Save raw immutable data to `data/raw/solder_hardness_raw.csv` with checksums in `data/checksums.txt`
- [ ] T016 [US1] Save validated dataset to `data/processed/solder_hardness_validated.csv` (must run after T014)
- [ ] T016b [US1] **Generate Validation Report Script**: Write a Python script `code/ingestion/generate_validation_report.py` that reads `data/processed/.ingestion_status.json` and generates `data/processed/validation_report.yaml`. **CRITICAL**: The script must explicitly read the `threshold_status`, `warning_text`, and manual review counts from the JSON file to ensure data consistency.
- [ ] T019 [US1] **Execute Validation Report Generation**: Run the script generated in T016b to produce `data/processed/validation_report.yaml`. This task must depend on T014 to ensure the validation is complete.
- [ ] T017 [US1] Add logging for ingestion operations and data source citations in `code/ingestion/`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and compare composition-to-hardness regression models (Priority: P2)

**Goal**: Train XGBoost and linear regression models with cross-validation, bootstrap comparison, SHAP analysis, and VIF diagnostics.

**Independent Test**: Run model training on validated dataset and verify cross-validation metrics (R², RMSE) are computed, VIF scores are reported, and feature importance rankings are generated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T021 [P] [US2] Integration test for model training pipeline in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement CLR transform utility in `code/features/transformer.py` using `compositional` library to handle closure problem. **Output**: A function to apply CLR to a vector of values.
- [X] T023 [US2] Implement descriptor computation in `code/features/descriptor_engine.py` to calculate weighted mean atomic mass, electronegativity variance, atomic radius variance, weighted average melting point, and valence electron concentration. **Method**:
 1. **Compute Descriptors**: Use the **raw** elemental composition fractions (which sum to 1) as weights to compute the weighted means/variances of elemental properties (atomic mass, radius, etc.).
 2. **Apply CLR**: Apply the CLR transform (from T022) to the **resulting descriptor vector** (or the raw composition vector if required by the model input spec, but NOT as weights).
 3. **The resulting descriptor vector IS the feature vector for the model.**
 4. Ensure the output is a clean, tabular feature matrix ready for T024 (VIF) and T025 (Training). **Do NOT use CLR-transformed log-ratios as weights for physical properties.**
- [X] T024 [US2] Implement VIF calculation in `code/features/collinearity.py` to flag predictors with VIF ≥ 5 (requires output from T023)
- [ ] T024b [US2] **Configure CPU-Only Execution**: Create `code/models/config_cpu.py` to explicitly set all XGBoost and Linear Regression parameters to enforce CPU-only execution (e.g., `n_jobs=1`, `device='cpu'`, disable GPU acceleration flags). **CRITICAL**: This file must be imported by T025 and T026.
- [ ] T025 [US2] Implement XGBoost training with grid search (≤10 combinations) in `code/models/xgboost_trainer.py`. **CRITICAL**: This script MUST import and use the configuration from `code/models/config_cpu.py` to enforce CPU-only execution.
- [ ] T026 [US2] Implement Linear Regression baseline training in `code/models/linear_trainer.py`. **CRITICAL**: This script MUST import and use the configuration from `code/models/config_cpu.py` to enforce CPU-only execution.
- [ ] T027 [US2] Implement k-fold cross-validation for both models in `code/evaluation/cv.py` (requires T025/T026)
- [ ] T028 [US2] Implement bootstrap resampling for confidence intervals on held-out test set in `code/evaluation/bootstrap.py`
- [ ] T029 [US2] Implement **Bootstrap Model Comparison** and **Sensitivity Analysis** in `code/evaluation/model_comparison.py` and `code/evaluation/sensitivity.py`. **CRITICAL**:
 1. Compare XGBoost vs Linear Regression performance distributions using bootstrap resampling.
 2. **Sensitivity Analysis**: Sweep R² thresholds over the **specific set {0.3, 0.5, 0.6, 0.7}**.
 3. Calculate the fraction of bootstrap samples exceeding each threshold.
 4. **Explicitly generate the visual output** `data/outputs/sensitivity_plot.png` alongside the `data/processed/sensitivity_analysis.yaml`. **T029 must generate both the data and the plot.**
- [ ] T030 [US2] Implement SHAP value calculation and top-3 feature ranking in `code/evaluation/shap_analysis.py`
- [ ] T031 [US2] Save model artifacts, metrics, and diagnostics to `models/` and `data/processed/`
- [ ] T032 [US2] Add associational framing warnings in ALL model outputs, visualizations, and the final report per FR-007. **Specific Deliverables**:
 1. Append "NOTE: Results are associational, not causal" to the header of `data/processed/report.yaml`.
 2. Add a footer to all plots in `data/outputs/` stating "Associational Analysis Only".
 3. **Embed the associational disclaimer** in the metadata/header of all intermediate artifacts generated by T029 (metrics YAML) and T030 (SHAP YAML).
 4. **Read** the disclaimer from `data/processed/report.yaml` to include in the `README.md` and the generated paper draft (T035). **CRITICAL**: T032 must run BEFORE T036-T038 (visualizations) and BEFORE T035 (Paper Draft). It does NOT write to the paper draft; it writes to existing files and T035 reads them.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate interpretable visualizations and partial dependence plots (Priority: P3)

**Goal**: Generate scatter plot of predicted vs. measured hardness with error bars and partial dependence plots for top features.

**Independent Test**: Execute visualization pipeline and verify output files (scatter plot, partial dependence plots) are generated with correct axis labels and units.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Contract test for visualization output schema in `tests/contract/test_viz_output.py`
- [X] T034 [P] [US3] Integration test for visualization pipeline in `tests/integration/test_visualization.py`

### Implementation for User Story 3

- [ ] T035 [US3] **Generate Paper Draft**: Create `docs/paper_draft.md` containing the methodology, results, and discussion sections. **CRITICAL**: This task must **read** the associational warnings from `data/processed/report.yaml` (generated by T032) and include them prominently in the Discussion section. **Depends on T029, T030, T032**: US2 artifacts must be fully generated and validated before this task runs.
- [ ] T036 [US3] Implement scatter plot generation in `code/visualization/scatter.py` with % CI error bars (requires T025/T026 predictions)
- [ ] T037 [US3] Implement partial dependence plot generation in `code/visualization/pdp.py` for top-ranked SHAP features (requires T030 output)
- [ ] T038 [US3] Save all plots to `data/outputs/` with correct labels and units
- [ ] T039 [US3] Add axis labels, titles, and legends to all visualizations, including associational warnings as defined in T032

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `README.md` and `docs/`
- [ ] T041 Code cleanup and refactoring
- [ ] T042 Performance optimization to ensure <6h runtime on free-tier
- [ ] T043 [P] Additional unit tests in `tests/unit/`
- [ ] T044 Run quickstart.md validation
- [ ] T045 Verify all tasks respect CPU-only constraints (no CUDA, no GPU, no 8-bit quantization)
- [ ] T046 Verify dataset size handling (streaming/sampling logic implemented in T013)
- [ ] T047 [P] Verify all data loading tasks fail loudly on missing sources (no synthetic fallbacks) but handle partial data gracefully per T012
- [ ] T049 [P] [US2] Ensure `code/features/descriptor_engine.py` explicitly handles the case where the input dataset has N < 50 by raising a specific `DataInsufficientError` with a clear message, preventing downstream model training on statistically invalid data. (Note: This logic is now primarily enforced in T014, but this task ensures robustness in the feature engine if called independently).
- [ ] T050 [P] [US2] Add a "Model Performance Sanity Check" in `code/evaluation/model_comparison.py` to verify that the bootstrap R² distribution is not degenerate (e.g., all values identical or NaN) before reporting results, flagging potential data or model issues

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (except T003 which depends on T001, T005 depends on T007)
- All Foundational tasks marked [P] can run in parallel (within Phase 2, except T005 depends on T007)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data validation schema in tests/contract/test_data_schema.py"
Task: "Integration test for ingestion pipeline in tests/integration/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement data cleaning and filtering logic in code/ingestion/cleaner.py"
Task: "Implement validation logic in code/ingestion/validator.py"
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

- [P] tasks = different files, no dependencies (except T003 which depends on T001, T005 depends on T007)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All data must be real (no fabrication); all models must run on CPU-only; all datasets must be sampled or streamed if needed to fit available system memory; data loaders MUST fail loudly on missing sources but handle partial data gracefully per FR-001.
- **CRITICAL**: T012 requires `data/config/sources.yaml` to be populated by T009b before execution.
- **CRITICAL**: T014 enforces N >= 50 threshold and validates composition sums >= 95%; T019 generates the required power limitation report.
- **CRITICAL**: T023 logic corrected: Compute descriptors using **raw** fractions as weights, then apply CLR transform. Do NOT use CLR values as weights.
- **CRITICAL**: T013 now explicitly logs failed records to `filtered_records.csv` for verifiability and mandates checksumming, and flags records for manual review.
- **CRITICAL**: T018 has been removed; its logic is now explicitly part of T013 and T014.
- **CRITICAL**: T024b configures CPU-only execution, and T025/T026 explicitly import it.
- **CRITICAL**: T029 generates both the sensitivity data AND the plot; T036 (Sensitivity Plot) has been removed to avoid redundancy.
- **CRITICAL**: T032 applies warnings to existing files (report.yaml, plots) and intermediate artifacts. T035 (Paper Draft) reads from T032's outputs.
- **CRITICAL**: T008 ensures `research.md` is verified before the Constitution Check passes; no placeholders allowed.
- **CRITICAL**: T009b populates `sources.yaml` from verified `research.md` before T012 runs.
- **Note**: Tasks T047 and T048 have been removed. T047 logic is fully consolidated into T012. T048 logic (non-blocking logging) is now part of T012.