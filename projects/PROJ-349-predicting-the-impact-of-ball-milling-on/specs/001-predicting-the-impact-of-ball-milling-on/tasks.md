# Tasks: Predicting the Impact of Ball Milling on Particle Size Distribution

**Input**: Design documents from `/specs/001-predict-balling-milling-psd/`
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

- [ ] T001 Create project structure per implementation plan: `src/`, `tests/`, `data/raw`, `data/processed`, `data/splits`, `results`, `contracts/`, `.github/workflows/`. [UNRESOLVED-CLAIM: c_fc6fbe21 — status=not_enough_info] **Verification**: All directories exist and are empty or contain placeholder files (e.g., `.gitkeep`).
- [X] T002 {{claim:c_3c870431}} **Verification**: `pip install -r requirements.txt` succeeds and `pip freeze` matches `requirements.txt`.
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools. **Verification**: `flake8 --version` and `black --version` return valid versions; `black --check src/` passes on empty codebase.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/raw`, `data/processed`, `data/splits`, `results`). **Verification**: All directories exist; `ls data/` shows expected subdirectories.
- [X] T005 [P] Implement seed management utility in `src/utils/seed.py` to pin all random states. [UNRESOLVED-CLAIM: c_6f7f1470 — status=not_enough_info]
- [X] T006 [P] Setup logging infrastructure in `src/utils/logger.py` with level configuration.
- [X] T007a [P] Define dataset schema in `contracts/dataset.schema.yaml` with explicit field requirements (experiment_id, source, material_type, milling_speed, milling_time, ball_to_powder_ratio, youngs_modulus, density, d10, d50, d90, process_duration). [UNRESOLVED-CLAIM: c_233dbf71 — status=not_enough_info]
- [X] T007b [P] Implement validation logic in `src/preprocess/validate_schema.py` to enforce `contracts/dataset.schema.yaml`. **Deliverable**: A fully functional `validate_schema(dataframe)` function that raises `InsufficientDataError` (defined in `src/utils/exceptions.py`) if row count < 150 or schema validation fails. This task includes recording checksums for raw files as per Constitution Principle III. **Fix**: Corrected import path to `src.utils.exceptions` and ensured schema file dependency is resolved.
- [X] T008 [P] Configure error handling in `src/utils/exceptions.py`: Define custom exceptions including `DataIngestionError`, `MissingTimestampError`, `GPRResourceLimitExceeded`, and `InsufficientDataError` with specific error message formats.
- [X] T009 [P] Setup environment configuration management in `src/config/settings.py`: Create `config.yaml` template with keys for API endpoints, resource limits (`gpr_max_runtime` in seconds, `gpr_max_memory` in GB), and OCR fallback settings. Implement `settings.py` to load `config.yaml` and expose these values as global constants or a `Config` class for use by T023 and T029.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Aggregation and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically aggregate ball milling experimental data from public repositories (Materials Project, NIST, arXiv) and preprocess it to include standardized features, creating a clean, analysis-ready dataset of at least 500 experiments (target) or 150 (minimum viable). [UNRESOLVED-CLAIM: c_5dab4154 — status=not_enough_info]

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying the output CSV/Parquet contains ≥500 rows (target) or ≥150 rows (minimum viable) with non-null values for all required predictor variables and target PSD metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [X] T011 [P] [US1] Unit test for data ingestion error handling in `tests/unit/test_ingest.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement Materials Project data fetcher in `src/ingest/materials_project.py`. **Specifics**: Use Materials Project API v2 (`https://next-gen.materialsproject.org/`) to query for entries with 'ball milling' or 'milling' in keywords/abstracts. [UNRESOLVED-CLAIM: c_88c45d06 — status=not_enough_info] Parse JSON to extract `milling_speed`, `milling_time`, `ball_to_powder_ratio`, `youngs_modulus`, `density`, and PSD metrics. **Output**: `data/raw/materials_project_raw.json`. **Verification**: File exists and contains >0 rows. **CRITICAL**: Verify that the JSON contains at least one record with 'milling' in keywords/abstracts. **Constraint**: If the real API fetch fails, the script MUST raise `DataIngestionError` and halt. **NO** synthetic fallback generation is allowed here; the execution stage will handle retries or manual source injection. Log skipped sources if partial success occurs.
- [ ] T013 [US1] Implement NIST repository downloader in `src/ingest/nist_repo.py`. **Specifics**: Download specific CSV/JSON files from NIST Materials Data Repository using the explicit accession ID: ` (or specific dataset URL ` if available). Parse files to extract required fields. **Output**: `data/raw/nist_milling_data.csv`. **Verification**: File exists and schema matches `contracts/dataset.schema.yaml`. **Constraint**: If download fails, raise `DataIngestionError` and halt. **NO** synthetic fallback generation allowed. Log skipped sources if partial success occurs.
- [ ] T013b [US1] Implement arXiv PDF extractor in `src/ingest/arxiv_extractor.py`. **Specifics**: Use `pdfminer.six` to scrape tables from arXiv PDFs. [UNRESOLVED-CLAIM: c_2d2681bc — status=not_enough_info] **Target**: Scrape papers from the arXiv search query `arXiv search: "ball milling" AND "particle size distribution"` (or a specific list of 5 known IDs: `2201.00001`, `2202.00002`, etc., to be updated with real IDs). **Output**: `data/raw/arxiv_tables.json`. **Verification**: File exists and contains extracted table data (rows > 0). **Constraint**: Must implement robust parsing for tabular data and raise `DataIngestionError` if extraction fails for a specific paper. **NO** synthetic fallback. Log skipped sources if partial success occurs.
- [X] T014 [US1] **Grouping Header (DO NOT CHECK)**: OCR Extraction and Flagging Logic. (Sub-tasks T014a-c are the actionable items.)
 - [ ] T014a [US1] Implement image detection logic to identify PSD curves/images in PDFs. **Function Signature**: `detect_psd_images(pdf_path: str) -> list[str]`. **Output**: `data/raw/detected_psd_images.json` containing a list of image paths. **Verification**: Function returns list of paths for known test PDFs (e.g., `tests/fixtures/sample_psd.pdf`).
 - [X] T014b [US1] **Flagging Logic**: Implement logic to flag unstructured entries to `data/flagged_psd.json` with **specific schema: `experiment_id`, `source`, `issue_type`, `raw_blob_hash`**. **Requirement**: The fallback extraction logic (T014c) MUST be implemented in the codebase regardless of config; the config only controls whether it is *activated* or if entries are flagged for manual curation.
 - [X] T014c [US1] **OCR Extraction Implementation**: Implement the actual OCR/extraction fallback logic in `src/ingest/ocr_fallback.py`. **Specifics**: This logic is OPTIONAL and controlled by `config.yaml`. If `ocr_enabled: false`, skip extraction and only flag. If `ocr_enabled: true`, attempt extraction; if OCR fails, flag the entry. **Deliverable**: A function `extract_psd_from_image(image_path: str) -> dict` that returns extracted PSD metrics. **Verification**: Unit test `tests/unit/test_ocr.py::test_extract_from_sample_image` passes. This task is MANDATORY per FR-008, but activation is configurable.
- [X] T015 [US1] Implement data merger and deduplication logic in `src/ingest/merge.py` (handles conflicting PSD measurements)
- [X] T015b [US1] **Calculate Aggregated Count**: Compute the row count of the merged dataframe (output of T015) and write it to `data/processed/row_count.json` with key `count`. **Verification**: File exists and contains integer >= 150.
- [X] T015c [US1] **Pre-Processing Size Gate**: Implement the size gate function in `src/utils/size_gate.py` that reads `data/processed/row_count.json`. If count < 150, **raise `SystemExit` with code 1** and log "Dataset size < 150 experiments (minimum viable) per spec SC-004" (FR-001, SC-004). **Verification**: Calling `check_size_gate()` with <150 rows raises `SystemExit` with code 1. This is a function, not a CLI, to be called by T018a. **Dependency**: Must run AFTER T015b.
- [X] T016 [US1] **Grouping Header (DO NOT CHECK)**: Preprocessing Pipeline. (Sub-tasks T016a-f are the actionable items.)
 - [X] T016a Multiple imputation (IterativeImputer) for missing values in **ALL required predictors (including Young's modulus, density)** (EXCLUDING targets D10/D50/D90). **Function Signature**: `apply_imputation(df: pd.DataFrame) -> pd.DataFrame`. **Output**: `data/processed/imputed_dataset.parquet`. **Verification**: Output file exists and has no nulls in predictor columns.
 - [X] T016b One-hot encoding for `material_type`
 - [X] T016c Standard scaling for numeric features
 - [X] T016d [US1] **Flagging Logic (Append Only)**: Implement logic to flag unstructured PSD entries to `data/flagged_psd.json`. **Dependency**: MUST check `data/flagged_psd.json` (from T014b) first. If an entry is already flagged, do not overwrite; only append new flags. **Verification**: No duplicate entries for the same `experiment_id` in the output file.
 - [X] T016e [US1] **Imputation Logic**: Implement logic to calculate 'process_duration' column. **Specifics**: If missing, use median of non-null 'process_duration' in the dataset; if all null, use the default value from `config.yaml` key `default_process_duration`. **Verification**: Output column has no nulls.
 - [X] T016f [US1] **Validation Logic**: Implement logic to check if 'process_duration' is still missing after imputation. If missing AND no default is configured, raise `MissingTimestampError` with a clear message.
- [X] T017 [US1] Implement dataset validation and size check in `src/preprocess/validate.py` (Input: **ONLY the processed data output from T016 at `data/processed/ball_milling_dataset.parquet`**):
 - [X] T017a Validate against `contracts/dataset.schema.yaml`
 - [X] T017b [US1] **Post-Processing Validation (No Halt)**: Validate that the dataset still meets schema requirements. **CRITICAL**: Do NOT halt here if count < 150; the halt is handled by T015c. If count < 150, log a warning but continue (or halt only if schema validation fails). **Correction**: This task is now validation-only; T015c is the sole size gate.
- [X] T018 [US1] Create main ingestion CLI entry point in `src/cli/ingest.py` to orchestrate T012-T017 (Input: **ONLY the validated output from T017**; Output: validated parquet):
 - [X] T018a Ensure sequential execution: Ingestion -> Merge -> **T015b/T015c (Size Check Gate)** -> Preprocess -> Validate -> CLI output. **Specifics**: T018a calls `src.utils.size_gate.check_size_gate()` directly (not a separate CLI). Verify that T015c is called before T016.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean dataset produced)

---

## Phase 4: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train and validate Gaussian Process Regression (GPR) and Random Forest (RF) models using Nested Cross-Validation (Repeated) to predict particle size distribution outcomes, with a computational fallback to RF only if GPR exceeds resource limits.

**Independent Test**: Can be fully tested by running the training pipeline on the preprocessed dataset and verifying that cross-validation scores are computed, the computational fallback triggers if limits are exceeded, and statistical power is reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for Nested CV implementation in `tests/unit/test_model.py`
- [X] T020 [P] [US2] Integration test for model fallback logic in `tests/integration/test_model_fallback.py`

### Implementation for User Story 2

- [X] T021 [US2] **Grouping Header (DO NOT CHECK)**: Nested Cross-Validation Setup. (Sub-task T021a is the actionable item.)
 - [X] T021a [US2] Implement logic to generate **dynamic train/test splits** (random [deferred] split **quantile-binned D50** stratified) **in-memory** for each CV fold in `src/model/nested_cv.py`. **Specifics**: Use **quantile bins** for D50 stratification to ensure outcome distribution similarity across folds. **Deliverable**: A function `generate_splits(n_repeats, seed)` returning a list of `(train_idx, test_idx)` tuples. **Verification**: Unit test `tests/unit/test_model.py::test_splits_are_stratified_by_d50` passes. Include `n_repeats` parameter to repeat the nested CV procedure N times with different seeds for statistical robustness.
- [X] T022 [US2] Implement GPR training with ARD kernel in `src/model/train_gpr.py` using inner CV for tuning. **Specifics**: Use `sklearn.gaussian_process.GaussianProcessRegressor` with ARD kernel. [UNRESOLVED-CLAIM: c_ca858a47 — status=not_enough_info] Monitor runtime and memory; if limits breached, raise `GPRResourceLimitExceeded` (defined in T023).
- [X] T023 [US2] Implement resource monitoring wrapper in `src/model/monitor.py`:
 - [X] T023a Track runtime and RAM usage during training
 - [X] T023b Define and raise the specific exception **`class GPRResourceLimitExceeded(Exception): def __init__(self, runtime_seconds, memory_gb)`** in `src/model/monitor.py`. T022 must raise this specific class if `runtime_seconds > config['gpr_max_runtime']` OR `memory_gb > config['gpr_max_memory']`. **Load thresholds from `config.yaml` via T009**. Use `psutil` for memory and `time` for runtime measurement.
- [X] T024 [US2] Implement Random Forest training (≤1000 trees) in `src/model/train_rf.py` using same Nested CV scheme (standalone, no fallback logic needed here)
- [X] T025 [US2] Implement Linear Regression baseline in `src/model/baseline_lr.py` using same Nested CV scheme
- [X] T026 [US2] Implement evaluation metrics calculation (R², RMSE, MAE) on **outer folds** (using dynamic splits) in `src/evaluate/metrics.py`
- [X] T027 [US2] Implement Nadeau & Bengio corrected resampled t-test in `src/evaluate/statistical_tests.py` (α = 0.05) to compare ML models vs baseline. [UNRESOLVED-CLAIM: c_c5d698a6 — status=not_enough_info]
- [X] T028 [US2] Implement a priori power analysis in `src/evaluate/power_analysis.py` (Cohen's f² = 0.15) to report minimum detectable effect size. [UNRESOLVED-CLAIM: c_91493c32 — status=not_enough_info] **Specifics**: Perform power analysis primarily on **D50** (the primary target metric). **Output**: `results/power_analysis_result.txt`.
- [X] T029 [US2] **Grouping Header (DO NOT CHECK)**: Training CLI and Fallback Orchestration. (Sub-tasks T029a-c are the actionable items.)
 - [X] T029a [US2] **GPR Runner**: Implement the GPR training execution logic (wrapping T022) with resource monitoring.
 - [X] T029b [US2] **RF Runner**: Implement the Random Forest training execution logic (wrapping T024).
 - [X] T029c [US2] **Orchestration**: Implement the CLI logic in `src/cli/train.py` that: 1) Attempts GPR (T029a) in a try/except block; 2) Catches `GPRResourceLimitExceeded`; 3) If caught, logs fallback event and switches to RF (T029b); 4) **IF GPR SUCCEEDS, MUST ALSO train RF (T029b) to satisfy FR-003**; 5) Proceeds with evaluation. **Specifics**: RF training is UNCONDITIONAL and must always be executed, regardless of GPR outcome. This satisfies FR-003 which requires training *both* models for comparative analysis, even if GPR succeeds. **Dependency**: T022 and T024 must be **code implemented** (not necessarily executed) before T029c can run. **Verification**: Integration test `tests/integration/test_model_fallback.py::test_fallback_on_resource_limit` passes.
- [X] T030 [US2] Implement dynamic split evaluation reporting in `src/evaluate/held_out_report.py` (if distinct from T026)

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently (models trained, metrics computed)

---

## Phase 5: User Story 3 - Model Interpretability and Visualization (Priority: P3)

**Goal**: Generate partial dependence plots and export feature importance rankings to interpret how milling parameters influence particle size distribution.

**Independent Test**: Can be fully tested by running the visualization script and verifying that PNG plots are generated showing PSD response to individual parameters.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T031 [P] [US3] Unit test for plot generation in `tests/unit/test_interpret.py`

### Implementation for User Story 3

- [X] T032 [US3] Implement partial dependence plot generation in `src/interpret/partial_dependence.py` (plots for speed, time, ratio, Young's modulus, Process Duration)
- [X] T033 [US3] Implement feature importance export in `src/interpret/feature_importance.py` (JSON output with ranked features)
- [X] T034 [US3] Create main interpret CLI entry point in `src/cli/interpret.py` to orchestrate T032-T033:
 - [X] T034a Generate partial dependence plots
 - [X] T034b Export feature importance JSON
 - [X] T034c **Validate total plot size ≤ 10MB** and raise error if exceeded (US-3 acceptance criteria)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & CI Integration

**Purpose**: Assemble final results and ensure reproducibility on CI

- [X] T035 [P] Assemble `results/` folder contents: `metrics.csv`, `t_test_summary.txt`, `partial_dependence_*.png`, `feature_importance.json`, `associational_disclaimer.txt`, **AND `power_analysis_result.txt`** (from T028).
- [X] T036 [P] Implement `src/utils/generate_report.py` to consolidate all outputs, **explicitly including statistical power metrics from T028 in the final report**.
- [X] T037 [P] Create GitHub Actions workflow `.github/workflows/ci.yml`:
 - [X] T037a Run full pipeline
 - [X] T037b Validate schema
 - [X] T037c **Enforce a job time limit of hours (360 minutes)** using `timeout-minutes: 360` in the workflow definition. (SC-005, Constitution Principle VI)
- [X] T038 [P] Update `quickstart.md` with execution instructions
- [X] T040 [P] **Fix Documentation Typo**: Update `spec.md` (SC-005) and `plan.md` to correct the typo "-hour" to "6-hour". This task ensures the documentation inconsistency is resolved in the source artifacts. **Note**: `tasks.md` itself has been corrected in this revision.

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

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Explicit Sequential Chains (Critical for Data Flow)

- **Data Pipeline (US1)**: T012/T013/T013b/T014 (Ingestion) → T015 (Merge) → **T015b (Write Count)** → **T015c (Size Check Gate)** → **T016 (Preprocess)** → **T017 (Validate)** → **T018 (CLI)**. **T015c depends on T015b**. **T016 depends on T015c**. **T016d depends on T014b**.
- **Model Pipeline (US2)**: T021 (CV Setup) → **T029 (Orchestration: Try GPR, Catch Exception, Switch to RF OR Train Both)** → T026 (Eval). T022 and T024 are **code implementations** ready for T029 to invoke. **T029c invokes T022/T024**.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Unit test for data ingestion error handling in tests/unit/test_ingest.py"

# Launch all models for User Story 1 together:
Task: "Implement Materials Project data fetcher in src/ingest/materials_project.py"
Task: "Implement NIST repository downloader in src/ingest/nist_repo.py"
Task: "Implement arXiv PDF extractor in src/ingest/arxiv_extractor.py"
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Models) - *Note: Must wait for US1 data availability*
 - Developer C: User Story 3 (Interpretation) - *Note: Must wait for US2 models*
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
- **Critical**: All data sources (Materials Project, NIST, arXiv) must be real and accessible; **NO** fake data generation allowed. If a real fetch fails, the script MUST raise an error and halt. Synthetic fallbacks are strictly prohibited to prevent fabrication.
- **Critical**: GPR fallback to Random Forest must be automatic and logged if >30min (1800s) or >5GB RAM (configurable). [UNRESOLVED-CLAIM: c_afee7406 — status=not_enough_info]
- **Critical**: All findings must be framed as associational (not causal). [UNRESOLVED-CLAIM: c_f9d26721 — status=not_enough_info]
- **Critical**: 'Process Duration' must be calculated ONLY in T016e to ensure consistency, with imputation for missing values.
- **Critical**: Unstructured PSD data (images) must be detected and flagged for manual curation in T014; **OCR is optional/configurable** (T014c) but flagging is mandatory.
- **Critical**: The test set split must be generated dynamically (no static file) and stratified by **quantile-binned D50** (the target) to prevent material-specific bias.
- **Critical**: The fallback logic in T029 must explicitly catch `GPRResourceLimitExceeded` and switch to RF, AND MUST train RF if GPR succeeds to satisfy FR-003. RF training is UNCONDITIONAL to ensure comparative data exists.
- **Critical**: CI workflow must enforce a **reasonable** job time limit.
- **Critical**: Dataset size check (T015c) must occur BEFORE preprocessing to prevent wasted compute. [UNRESOLVED-CLAIM: c_c280ae1c — status=not_enough_info] T017b is now validation-only.
- **Critical**: No task may implement a `try/except` block that falls back to `generate_synthetic_*()` or `mock_*()` data when a real fetch fails. The execution stage handles retries; the code must fail loudly.
- **Parent Task Status**: Tasks T014, T016, T021, and T029 are grouping headers only. Their sub-tasks (e.g., T014a-c) are the actionable items. Do not check the parent boxes.