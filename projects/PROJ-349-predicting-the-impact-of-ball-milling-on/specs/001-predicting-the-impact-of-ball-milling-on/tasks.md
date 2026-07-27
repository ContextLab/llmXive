# Tasks: Predicting the Impact of Ball Milling on Particle Size Distribution

**Input**: Design documents from `/specs/001-predicting-the-impact-of-ball-milling-on/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[W]**: Writing/Documentation task (prose correction, not code)
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

- [ ] T001 Create project structure per implementation plan: `src/`, `tests/`, `data/raw`, `data/processed`, `data/splits`, `results`, `contracts/`, `.github/workflows/`. **Verification**: Run `test -d src && test -d tests && test -d data/raw && test -d data/processed && test -d data/splits && test -d results && test -d contracts && test -d .github && test -d .github/workflows` and verify all directories exist.
- [X] T002 **Verification**: `pip install -r requirements.txt` succeeds and `pip freeze` matches `requirements.txt`. **Action**: Create `requirements.txt` with pinned versions of `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `statsmodels==0.14.*`, `matplotlib==3.9.*`, `seaborn==0.13.*`, `requests==2.32.*`, `tqdm==4.66.*`, `pyarrow==16.*`, `pdfminer.six==20231228`.
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools. **Verification**: `flake8 --version` and `black --version` return valid versions; `black --check src/` passes on empty codebase. **Action**: Create `.flake8` and `pyproject.toml` (or `setup.cfg`) with standard configs.
- [X] T040 [W] [P] **Fix Documentation Typo**: Update `plan.md`, `quickstart.md`, AND `spec.md` to correct the typo "-hour" to "6-hour" in SC-005. **Verification**: `plan.md`, `quickstart.md`, and `spec.md` contain "6-hour" and no longer contain "-hour".

---

## Phase 2: Foundational (Blocking Prerequisites & Source Resolution)

**Purpose**: Core infrastructure and data source resolution that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement seed management utility in `src/utils/seed.py` to pin all random states.
- [ ] T006 [P] Setup logging infrastructure in `src/utils/logger.py` with level configuration.
- [ ] T008 [P] Configure error handling in `src/utils/exceptions.py`: Define custom exceptions including `DataIngestionError`, `MissingTimestampError`, `GPRResourceLimitExceeded`, `InsufficientDataError`, and `MissingDataError` with specific error message formats. **Verification**: Exception classes are defined and importable.
- [ ] T007a [P] Define dataset schema in `contracts/dataset.schema.yaml` with explicit field requirements (experiment_id, source, material_type, milling_speed, milling_time, ball_to_powder_ratio, youngs_modulus, density, d10, d50, d90, process_duration).
- [ ] T007b [P] Implement validation logic in `src/preprocess/validate_schema.py` to enforce `contracts/dataset.schema.yaml`. **Deliverable**: A fully functional `validate_schema(dataframe)` function that raises `InsufficientDataError` (defined in `src.utils.exceptions` via T008) ONLY if schema structure (field types, presence) fails. **Constraint**: This task does NOT check row count; row count validation is handled later in T015c and T017c. **Dependency**: Requires `InsufficientDataError` from T008.
- [ ] T009 [P] Setup environment configuration management in `src/config/settings.py`: Create `config.yaml` template with keys for API endpoints, resource limits (`gpr_max_runtime` in seconds, `gpr_max_memory` in GB), OCR fallback settings. **Verification**: `config.yaml` exists and contains resource limits.

### Source Resolution (Phase 2 - Prerequisites for Data Ingestion)

**Checkpoint**: Foundation and Source Resolution ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Aggregation and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically aggregate ball milling experimental data from public repositories (Materials Project, NIST, arXiv) and preprocess it to include standardized features, creating a clean, analysis-ready dataset of at least 500 experiments (target) or 150 (minimum viable).

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying the output CSV/Parquet contains ≥500 rows (target) or ≥150 rows (minimum viable) with non-null values for all required predictor variables and target PSD metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [X] T011 [P] [US1] Unit test for data ingestion error handling in `tests/unit/test_ingest.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement Materials Project data fetcher in `src/ingest/materials_project.py`. **Specifics**: Use Materials Project API v2 (`https://next-gen.materialsproject.org/`) to query for entries with 'ball milling' or 'milling' in keywords/abstracts. Parse JSON to extract `milling_speed`, `milling_time`, `ball_to_powder_ratio`, `youngs_modulus`, `density`, and PSD metrics. **Output**: `data/raw/materials_project_raw.json`. **Verification**: File exists and contains >0 rows. **Constraint**: If the real API fetch fails or returns no rows, log a warning "Source skipped: Materials Project (no rows or error)" and skip this source; do NOT halt the entire pipeline. Log skipped sources if partial success occurs.
- [ ] T013 [US1] Implement NIST repository downloader in `src/ingest/nist_repo.py`. **Specifics**: Use the NIST Search API (`https://data.nist.gov/api/v1/search`) with query string `q=ball+milling AND datasetType:csv`. Iterate through paginated results to find ball milling datasets. Download the first valid CSV/JSON found. **Algorithm**: Use `requests` to fetch the search results and download links. If the search returns 0 results or the fetch fails (404, 500, timeout), log a warning "Source skipped: NIST (no rows or error)" and skip this source. **Verification**: File exists and schema matches `contracts/dataset.schema.yaml`. **Constraint**: If the fetch fails or returns 0 rows, log a warning and skip; do NOT fallback to UCI or any other dataset. Log skipped sources if partial success occurs.
- [ ] T013b [US1] Implement arXiv PDF extractor in `src/ingest/arxiv_extractor.py`. **Specifics**: Use the `arxiv` Python package to search `cat:cond-mat.mtrl-sci AND ball milling`. **Algorithm**: Limit the corpus to a representative subset of papers. If the search returns 0 results, log a warning "Source skipped: arXiv (no results found)" and skip. For each paper, download PDF and use `pdfminer.six` to scrape tables. **Pagination**: Iterate through results until 50 papers are processed or no more results are found. **Extraction Logic**: Scan tables for headers containing 'D10', 'D50', or 'D90' and extract the corresponding row values. **Output**: `data/raw/arxiv_tables.json`. **Verification**: File exists and contains extracted table data (rows > 0). **Constraint**: If extraction fails for a specific paper or returns an empty result set, log a warning "Source skipped: arXiv (no rows or error)" and skip that paper; do NOT halt the pipeline. Log skipped sources if partial success occurs.
- [ ] T014 [US1] **Grouping Header (DO NOT CHECK)**: This is a non-actionable container for T014a-c (OCR Extraction and Flagging Logic).
 - [ ] T014a [US1] Implement image detection logic to identify PSD curves/images in PDFs. **Algorithm**: Use `pdf2image` to convert PDF pages to images. Use `cv2.Canny` with thresholds (50, 150) followed by `cv2.findContours`. Flag a page as containing a PSD image if the number of contours > 10 AND the aspect ratio of the bounding box is between 0.5 and 2.0. **Function Signature**: `detect_psd_images(pdf_path: str) -> list[str]`. **Output**: `data/raw/detected_psd_images.json` containing a list of image paths. **Verification**: Function returns list of paths for known test PDFs (e.g., `tests/fixtures/sample_psd.pdf`).
 - [ ] T014b [US1] **Flagging Logic**: Implement logic to flag unstructured entries to `data/flagged_psd.json` with **specific schema: `experiment_id`, `source`, `issue_type`, `raw_blob_hash`**. **Requirement**: The fallback extraction logic (T014c) MUST be implemented in the codebase regardless of config; the config only controls whether it is *activated* or if entries are flagged for manual curation. **Trigger**: Must run after T014a detects images. **Dependency**: T014a must precede T014b.
 - [ ] T014c [US1] **OCR Extraction Implementation**: Implement the actual OCR/extraction fallback logic in `src/ingest/ocr_fallback.py`. **Specifics**: The **flagging fallback** is MANDATORY and always active. The **OCR extraction attempt** is MANDATORY for flagged images. If `ocr_enabled: false`, skip extraction and only flag. **Algorithm**: Use `easyocr` to extract text from the image (input format: PNG/JPG). Apply regex pattern `r'D(10|50|90)[\s:]*([0-9]+(?:\.[0-9]+)?)'` to parse D-values from the OCR output string. Validate that the extracted value is a valid float. If regex fails, attempt linear interpolation on the image pixels if a curve is detected. Raise an error if no match is found. **Function Signature**: `extract_psd_from_image(image_path: str, flagged_entry_id: str) -> dict`. **Deliverable**: A function `extract_psd_from_image(image_path: str, flagged_entry_id: str) -> dict` that returns extracted PSD metrics. **Verification**: Unit test `tests/unit/test_ocr.py::test_extract_from_sample_image` passes. This task is MANDATORY per FR-008.
- [ ] T015 [US1] Implement data merger and deduplication logic in `src/ingest/merge.py` (handles conflicting PSD measurements). **Specifics**: Merge data from T012, T013, T013b. **Integration Step**: After merging, check for entries flagged in `data/flagged_psd.json`. For each flagged entry, call `extract_psd_from_image` (T014c) to attempt extraction. Update the merged dataframe with extracted values. **Output**: `data/raw/merged_dataset.parquet`. **Verification**: File exists and contains all unique experiments.
- [ ] T015b [US1] **Calculate Aggregated Count**: Compute the row count of the merged dataframe (output of T015) and write it to `data/processed/row_count.json` with key `count`. **Verification**: File exists and contains integer >= 0.
- [ ] T015c [US1] **Pre-Processing Size Gate (Warning Only) & OCR Trigger**: Implement the size gate function in `src/utils/size_gate.py` that reads `data/processed/row_count.json`. If count < 150, **log a critical warning** but do NOT halt. **CRITICAL**: If `data/flagged_psd.json` (from T014b) exists and contains entries, this task MUST call `src/ingest/ocr_fallback.py` (T014c) function `extract_psd_from_image` for each flagged entry to attempt extraction before proceeding. **Verification**: Calling `check_size_gate()` with <150 rows logs a warning but returns normally. This is a function, not a CLI, to be called by T018a. **Dependency**: Must run AFTER T015b and T014b.
- [ ] T016 [US1] **Grouping Header (DO NOT CHECK)**: This is a non-actionable container for T016a-f (Preprocessing Pipeline).
 - [X] T016a Multiple imputation (IterativeImputer) for missing values in **ALL required predictors (including Young's modulus, density)** (EXCLUDING targets D10/D50/D90). **Function Signature**: `apply_imputation(df: pd.DataFrame) -> pd.DataFrame`. **Output**: `data/processed/imputed_dataset.parquet`. **Verification**: Output file exists and has no nulls in predictor columns.
 - [X] T016b One-hot encoding for `material_type`
 - [X] T016c Standard scaling for numeric features
 - [X] T016d [US1] **Flagging Logic (Append Only)**: Implement logic to flag unstructured PSD entries to `data/flagged_psd.json`. **Dependency**: MUST check `data/flagged_psd.json` (from T014b) first. If an entry is already flagged, do not overwrite; only append new flags. **Verification**: No duplicate entries for the same `experiment_id` in the output file. **Dependency**: T014b must precede T016d.
 - [ ] T016e [US1] **Process Duration Extraction**: Implement logic to extract 'process_duration' from the source data (Materials Project, NIST, arXiv). **Constraint**: Do NOT use a default value from config. If the value is missing in the source data, **raise `MissingDataError`** with a clear message "Process Duration missing and cannot be imputed". **Verification**: Output column has no nulls OR the process halts with `MissingDataError`.
 - [ ] T016f [US1] **Validation Logic**: Implement logic to check if 'process_duration' is still missing after extraction. If missing, raise `MissingDataError` with a clear message.
- [X] T017a [US1] **Schema Validation**: Validate the processed dataset against `contracts/dataset.schema.yaml`. **Input**: `data/processed/ball_milling_dataset.parquet` (output of T016). **Verification**: Schema validation passes. **Dependency**: Must run BEFORE T017c.
- [X] T017b [US1] **Pre-Halt Size Check (Warning Only)**: Check if the processed dataset has >= 150 rows. If < 150, log a critical warning but do NOT halt. **Verification**: Warning is logged if count < 150. **Dependency**: Must run AFTER T017a.
- [X] T017c [US1] **Post-Processing Size Gate (HALT)**: Validate that the processed dataset still meets the minimum viable threshold of >= 150 rows. **CRITICAL**: If count < 150, **raise `SystemExit` with code 1** and log "Processed dataset size < 150 experiments (minimum viable) per spec SC-004". **Verification**: Calling `check_processed_size()` with <150 rows raises `SystemExit` with code 1. This is the definitive size gate for SC-004. **Dependency**: Must run AFTER T017a and T017b.
- [ ] T018 [US1] Create main ingestion CLI entry point in `src/cli/ingest.py` to orchestrate T012-T017 (Input: **ONLY the validated output from T017**; Output: validated parquet):
 - [X] T018a Ensure sequential execution: Ingestion -> Merge -> **T015b/T015c (Warning Gate + OCR Trigger)** -> Preprocess -> **T017a -> T017b -> T017c (Halt Gate)** -> Validate -> CLI output. **Specifics**: T018a calls `src.utils.size_gate.check_size_gate()` (T015c) and `src.preprocess.validate.check_processed_size()` (T017c). Verify that T017c is called after T017a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean dataset produced)

---

## Phase 4: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train and validate Gaussian Process Regression (GPR) and Random Forest (RF) models using Nested Cross-Validation (Repeated) to predict particle size distribution outcomes, with a computational fallback to RF only if GPR exceeds resource limits.

**Independent Test**: Can be fully tested by running the training pipeline on the preprocessed dataset and verifying that cross-validation scores are computed, the computational fallback triggers if limits are exceeded, and statistical power is reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for Nested CV implementation in `tests/unit/test_model.py`
- [X] T020 [P] [US2] Integration test for model fallback logic in `tests/integration/test_model_fallback.py`

### Implementation for User Story 2

- [X] T021 [US2] **Grouping Header (DO NOT CHECK)**: This is a non-actionable container for T021a (Nested Cross-Validation Setup).
 - [X] T021a [US2] Implement logic to generate **dynamic train/test splits** (random [deferred] split **quantile-binned D50** stratified) **in-memory** for each CV fold in `src/model/nested_cv.py`. **Specifics**: Use **quantile bins** for D50 stratification to ensure outcome distribution similarity across folds. **Algorithm**: Use `pandas.qcut` with `q=10` (10 bins). If `qcut` fails due to ties or insufficient unique values, reduce `q` by half (e.g., 5, then 2) until a valid split is achieved. If `q` reduces to 1, log a warning "Stratification disabled: insufficient unique values" and fall back to random split. **Deliverable**: A function `generate_splits(n_repeats, seed)` returning a list of `(train_idx, test_idx)` tuples. **Verification**: Unit test `tests/unit/test_model.py::test_splits_are_stratified_by_d50` passes. Include `n_repeats` parameter to repeat the nested CV procedure N times with different seeds for statistical robustness.
- [X] T022 [US2] Implement GPR training with ARD kernel in `src/model/train_gpr.py` using inner CV for tuning. **Specifics**: Use `sklearn.gaussian_process.GaussianProcessRegressor` with ARD kernel. Monitor runtime and memory; if limits breached, raise `GPRResourceLimitExceeded` (defined in T023). **Note**: This task defines the GPR training logic as a module for T029c to import and execute.
- [X] T023 [US2] Implement resource monitoring wrapper in `src/model/monitor.py`:
 - [X] T023a Track runtime and RAM usage during training
 - [X] T023b Define and raise the specific exception **`class GPRResourceLimitExceeded(Exception): def __init__(self, runtime_seconds, memory_gb)`** in `src/model/monitor.py`. T022 must raise this specific class if `runtime_seconds > config['gpr_max_runtime']` OR `memory_gb > config['gpr_max_memory']`. **Load thresholds from `config.yaml` via T009**. Use `psutil` for memory and `time` for runtime measurement.
- [X] T024 [US2] Implement Random Forest training (≤1000 trees) in `src/model/train_rf.py` using same Nested CV scheme (standalone, no fallback logic needed here). **Output**: `results/model_rf.pkl`. **Note**: This task defines the RF training logic as a module for T029c to import and execute.
- [X] T025 [US2] Implement Linear Regression baseline in `src/model/baseline_lr.py` using same Nested CV scheme
- [X] T026 [US2] Implement evaluation metrics calculation (R², RMSE, MAE) on **outer folds** (using dynamic splits) in `src/evaluate/metrics.py`
- [X] T027 [US2] Implement Nadeau & Bengio corrected resampled t-test in `src/evaluate/statistical_tests.py` (α = 0.05 (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value)) to compare ML models vs baseline.
- [X] T028a [US2] **Derive Effect Size**: Implement logic to search domain literature for ball milling effect sizes (using keywords: 'ball milling', 'effect size', 'Cohen's f'). **Algorithm**: Query `arxiv` or `semantic_scholar` APIs with specific keywords. Log the search parameters and result count. **Fallback**: If the search yields **zero** relevant results, use a hardcoded default value of Cohen's f² = 0.15 (based on standard exploratory ML studies) and **log a warning** "Literature search yielded zero results; using default effect size 0.15". **Output**: `results/effect_size_derivation.txt` containing the derived value, rationale, search parameters, and result count. **Verification**: File exists and contains a numeric value, rationale, and search log. **Dependency**: Must precede T028.
- [X] T028 [US2] Implement a priori power analysis in `src/evaluate/power_analysis.py`. **Specifics**: Perform power analysis primarily on **D50** (the primary target metric) using the **derived effect size from T028a**. **Output**: `results/power_analysis_result.txt`. **Verification**: Output file contains the calculated minimum detectable effect size based on the derived value.
- [X] T029 [US2] **Grouping Header (DO NOT CHECK)**: This is a non-actionable container for T029a-c (Training CLI and Fallback Orchestration).
 - [X] T029a [US2] **GPR Runner**: Implement the GPR training execution logic (wrapping T022) with resource monitoring.
 - [X] T029b [US2] **RF Runner**: Implement the Random Forest training execution logic (wrapping T024).
 - [X] T029c [US2] **Orchestration**: Implement the CLI logic in `src/cli/train.py` that: 1) Imports and *calls* the GPR training logic defined in T022 (via T029a) in a try/except block; 2) Catches `GPRResourceLimitExceeded`; 3) If caught, logs fallback event and switches to RF (T029b); 4) **IF GPR SUCCEEDS, MUST ALSO train RF (T029b) to satisfy FR-003**; 5) Proceeds with evaluation. **Specifics**: RF training is UNCONDITIONAL and must always be executed, regardless of GPR outcome. **Verification**: After GPR success path, explicitly verify that `src/model/train_rf.py` is invoked, completes successfully, and the model artifact (`results/model_rf.pkl`) exists and is non-empty before proceeding to T026. This ensures FR-003 is satisfied. **Dependency**: T022 and T024 must be **code implemented** (not necessarily executed) before T029c can run. **Verification**: Integration test `tests/integration/test_model_fallback.py::test_fallback_on_resource_limit` passes.
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
 - [X] T037c **Enforce a job time limit of several hours to prevent indefinite execution.** using `timeout-minutes: 360` in the workflow definition. (SC-005, Constitution Principle VI)
- [X] T038 [P] Update `quickstart.md` with execution instructions

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

- **Data Pipeline (US1)**: T012/T013/T013b (Ingestion) → T015 (Merge & Trigger OCR) → **T015b (Write Count)** → **T015c (Warning Gate + OCR Trigger)** → **T016 (Preprocess)** → **T017a (Schema Validation)** → **T017b (Warning Check)** → **T017c (Halt Gate)** → **T018 (CLI)**. **T015c depends on T015b and T014b**. **T016 depends on T015**. **T017a depends on T016**. **T017b depends on T017a**. **T017c depends on T017b**. **T016d depends on T014b**. **T014b -> T016d**. **T014b (Flag) -> T015 (Merge & Trigger OCR) -> T014c (Extraction) -> T016 (Preprocess)**.
- **Source Resolution (Phase 2)**: None (Removed UCI Fallback chain).
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
- [W] tasks = Writing/Documentation tasks (prose correction, not code)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: All data sources (Materials Project, NIST, arXiv) must be real and accessible. If a real fetch fails, the script MUST log a warning and skip that source (partial success). **Synthetic fallbacks (e.g., `generate_synthetic_*`) are strictly prohibited.**
- **Critical**: GPR fallback to Random Forest must be automatic and logged if >30min (1800s) or >5GB RAM (configurable).
- **Critical**: All findings must be framed as associational (not causal).
- **Critical**: 'Process Duration' must be extracted from source data ONLY in T016e. If missing, raise `MissingDataError`. **Do NOT use default values.**
- **Critical**: Unstructured PSD data (images) must be detected and flagged for manual curation in T014; **OCR is mandatory** (T014c) and must attempt extraction if enabled.
- **Critical**: The test set split must be generated dynamically (no static file) and stratified by **quantile-binned D50** (the target) to prevent material-specific bias.
- **Critical**: The fallback logic in T029 must explicitly catch `GPRResourceLimitExceeded` and switch to RF, AND MUST train RF if GPR succeeds to satisfy FR-003. RF training is UNCONDITIONAL to ensure comparative data exists. T029c must verify RF artifact completion.
- **Critical**: CI workflow must enforce a **reasonable** job time limit.
- **Critical**: Dataset size check: T015c (pre-processing) is a warning only. T017c (post-processing) is the definitive HALT gate for SC-004. **T007b (Schema Validation) does NOT check row count; it only validates schema structure.**
- **Critical**: No task may implement a `try/except` block that falls back to `generate_synthetic_*()` or `mock_*()` data when a real fetch fails. The execution stage handles retries; the code must fail loudly OR skip and log.
- **Parent Task Status**: Tasks T014, T016, T021, and T029 are grouping headers only. Their sub-tasks (e.g., T014a-c) are the actionable items. Do not check the parent boxes.
- **Critical**: T043 and T044 (UCI Fallback) have been REMOVED. The pipeline must strictly adhere to FR-001 (Materials Project, NIST, arXiv) and halt if <150 rows.
- **Critical**: T013 now explicitly uses the resolved NIST Search API and does NOT fallback to UCI.
- **Critical**: T016e strictly extracts 'Process Duration' and raises `MissingDataError` if missing.
- **Critical**: T028a includes a literature search step and logs a warning if the default effect size is used.