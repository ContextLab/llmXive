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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create setup script and manifest. **Action**: Generate `scripts/setup_manifest.txt` listing the required directory structure (`src/`, `tests/`, `data/raw`, `data/processed`, `data/splits`, `results`, `contracts/`, `.github/workflows/`). Then generate `scripts/setup.sh` to create the directory structure listed in the manifest. **Verification**: Both files exist and `setup.sh` successfully creates the directories.
- [X] T002 [P] Create `requirements.txt`. **Action**: Create `requirements.txt` with pinned versions of `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `statsmodels==0.14.*`, `matplotlib==3.9.*`, `seaborn==0.13.*`, `requests==2.32.*`, `tqdm==4.66.*`, `pyarrow==16.*`, `pdfminer.six==20231228`. **Optional Dependencies**: Create a separate `requirements-optional.txt` for `easyocr==1.7.*`, `opencv-python==4.8.*`, `pdf2image==1.16.*`. **Justification**: These are required for the FR-008 OCR fallback path but not for the core pipeline. **Verification**: Files exist.
- [X] T002b [P] Verify `requirements.txt`. **Action**: Run `pip check` or similar to ensure all dependencies are resolvable. **Verification**: No dependency conflicts reported.
- [X] T003a [P] Configure linting (flake8). **Action**: Create `.flake8` with standard configs including `max-line-length = 88 `. **Verification**: File `.flake8` exists and contains `max-line-length = 88 `.
- [X] T003b [P] Configure formatting (black). **Action**: Create `pyproject.toml` (or `setup.cfg`) with black configuration. **Verification**: File exists and contains valid black config.
- [X] T004 [P] Initialize Git Repository. **Action**: Run `git init` in the project root and create an initial commit with `.gitignore`. **Verification**: `.git` directory exists and `git log` shows an initial commit.

---

## Phase 2: Foundational (Blocking Prerequisites & Source Resolution)

**Purpose**: Core infrastructure and data source resolution that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement seed management utility in `src/utils/seed.py` to pin all random states.
- [X] T006 [P] Setup logging infrastructure in `src/utils/logger.py` with level configuration.
- [X] T008 [P] Configure error handling in `src/utils/exceptions.py`: Define custom exceptions including `DataIngestionError`, `MissingTimestampError`, `GPRResourceLimitExceeded`, `InsufficientDataError`, `MissingDataError`, and `StratificationError` with specific error message formats. **Verification**: Exception classes are defined and importable.
- [X] T007a [P] Define dataset schema in `contracts/dataset.schema.yaml` with explicit field requirements. **Action**: Create `contracts/dataset.schema.yaml` with the following YAML content:
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
required:
 - experiment_id
 - source_name
 - source_id
 - material_type
 - milling_speed
 - milling_time
 - ball_to_powder_ratio
 - youngs_modulus
 - density
 - d10
 - d50
 - d90
 - process_duration
properties:
 experiment_id:
 type: string
 source_name:
 type: string
 enum: ["Materials Project", "NIST", "arXiv"]
 source_id:
 type: string
 material_type:
 type: string
 milling_speed:
 type: number
 milling_time:
 type: number
 ball_to_powder_ratio:
 type: number
 youngs_modulus:
 type: number
 density:
 type: number
 d10:
 type: number
 d50:
 type: number
 d90:
 type: number
 process_duration:
 type: number
```
**Verification**: File exists and contains valid YAML schema.
- [X] T007b [P] Implement validation logic in `src/preprocess/validate_schema.py` to enforce `contracts/dataset.schema.yaml`. **Deliverable**: A fully functional `validate_schema(dataframe)` function that raises `InsufficientDataError` (defined in `src.utils.exceptions` via T008) ONLY if schema structure (field types, presence) fails. **Constraint**: This task does NOT check row count; row count validation is handled later in T015a and T017c. **Dependency**: Requires `InsufficientDataError` from T008. **Verification**: Function `validate_schema` exists and raises `InsufficientDataError` when schema validation fails.
- [X] T009 [P] Create `config.yaml` template in `src/config/` with keys for API endpoints, resource limits (`gpr_max_runtime` in seconds, `gpr_max_memory` in GB), and OCR fallback settings (`ocr.fallback_enabled` boolean). **Verification**: File exists and contains required keys.
- [X] T009b [P] Implement `load_config()` function in `src/config/settings.py`. **Specifics**: Parse `config.yaml`, validate that required keys (`gpr_max_runtime`, `gpr_max_memory`, `ocr.fallback_enabled`) exist and are of correct types, and return the config object. **Verification**: Function `load_config` is implemented to parse `config.yaml` and validate keys. **Dependency**: Must run before any task using config values (T014c, T023b).

---

## Phase 3: User Story 1 - Data Aggregation and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**:

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying the output CSV/Parquet contains ≥500 rows (target) or ≥150 rows (minimum viable) with non-null values for all required predictor variables and target PSD metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`. **Specifics**: Implement function `test_schema_validation_passes(df)`. **Action**: Use `jsonschema.validate(instance=df.to_dict(), schema=load_schema('contracts/dataset.schema.yaml'))`. **Verification**: Test passes if schema matches; fails with specific `jsonschema.ValidationError` if mismatch. **Dependency**: Requires T007a to be completed.
- [ ] T011 [P] [US1] Unit test for data ingestion error handling in `tests/unit/test_ingest.py`. **Specifics**: Implement function `test_ingest_handles_missing_api_key`. **Action**: Mock `requests.get` to raise `requests.exceptions.HTTPError(401)`. **Verification**: Assert that `DataIngestionError` is raised with message "API key invalid or missing".
- [ ] T011b [P] [US1] Unit test for OCR extraction in `tests/unit/test_ocr.py`. **Specifics**: Implement function `test_extract_psd_from_image_handles_mixed_units`. **Action**: Create a mock PNG image (using `PIL.Image`) containing text "D10: 100um, D50: 500um". Call `extract_psd_from_image` with `ocr.fallback_enabled=True`. **Verification**: Assert returned dict has `d10=100.0`, `d50=500.0`. **Action 2**: Call `extract_psd_from_image` with `ocr.fallback_enabled=False`. **Verification**: Assert function raises `DataIngestionError` or returns `None` without attempting OCR, confirming logic handles disabled state.
- [ ] T011c [P] [US1] Unit test for streaming/chunking memory constraints in `tests/unit/test_streaming.py`. **Specifics**: Implement function `test_streaming_memory_limit`. **Action**: Use `tracemalloc` to profile memory while iterating a mock generator yielding a substantial dataset (simulating large stream). **Verification**: Assert `tracemalloc.get_traced_memory()[0]` (current memory) never exceeds 500MB.

### Implementation for User Story 1

- [ ] T012 [US1] Implement Materials Project data fetcher in `src/ingest/materials_project.py`. **Specifics**: Use Materials Project API v2 endpoint `https://next-gen.materialsproject.org/api/v2/materials`. **Query**: `keywords=ball+milling`. **Authentication**: Use `X-API-Key` header. **Algorithm**: Fetch in batches (manual chunking) to handle large responses without loading all into memory. Accumulate statistics (count, sum) online. **Field Mapping**: Extract `milling_speed`, `milling_time`, `ball_to_powder_ratio`, `youngs_modulus`, `density`, and PSD metrics (D10, D50, D90) from the JSON response. If fields are nested, use the full path (e.g., `properties.milling_speed`). **MANDATORY**: For every successfully fetched row, record `source_name="Materials Project"` and `source_id` (the specific API record ID). **CRITICAL**: If a row lacks `source_id`, it MUST be flagged for manual review and logged immediately, but NOT dropped from the count unless it lacks valid data in other fields. If the real API fetch fails or returns no rows, log a warning "Source skipped: Materials Project (no rows or error)" and skip this source; do NOT halt the entire pipeline. Log skipped sources if partial success occurs. **Output**: `data/raw/materials_project_raw.json`. **Schema**: JSON array of objects with keys: `experiment_id`, `source_name`, `source_id`, `milling_speed`, `milling_time`, `ball_to_powder_ratio`, `youngs_modulus`, `density`, `d10`, `d50`, `d90`, `material_type`, `process_duration`. **Verification**: Script `src/ingest/materials_project.py` exists and implements the API call logic; output file path is defined; output file contains at least one valid row with the required schema including `source_name` and `source_id`. **Constraint**: Rows without `source_id` are flagged, not immediately dropped. **Note**: API endpoints and regex patterns are implementation-specific and subject to change if APIs update.
- [ ] T013 [US1] Implement NIST repository downloader in `src/ingest/nist_repo.py`. **Specifics**: Use the NIST Search API base URL `https://www.nist.gov/publications/search`. **Query String**: `q=ball+milling AND datasetType:csv`. **Algorithm**: Iterate through paginated results to find ball milling datasets. Download the first valid CSV/JSON found. Use `requests` to fetch the search results and download links. Fetch in batches of a manageable size to handle large responses without loading all into memory (manual chunking). If the search returns 0 results or the fetch fails (404, 500, timeout), log a warning "Source skipped: NIST (no rows or error)" and skip this source. **MANDATORY**: For every successfully fetched row, record `source_name="NIST"` and `source_id` (the specific dataset ID or DOI). **CRITICAL**: If a row lacks `source_id`, it MUST be flagged for manual review and logged immediately, but NOT dropped from the count unless it lacks valid data in other fields. **Output**: `data/raw/nist_raw.json`. **Schema**: JSON array of objects with keys: `experiment_id`, `source_name`, `source_id`, `milling_speed`, `milling_time`, `ball_to_powder_ratio`, `youngs_modulus`, `density`, `d10`, `d50`, `d90`, `material_type`, `process_duration`. **Verification**: Script `src/ingest/nist_repo.py` exists and implements the search/download logic; output file path is defined; output file contains at least one valid row with the required schema including `source_name` and `source_id`. **Constraint**: Rows without `source_id` are flagged, not immediately dropped. **Note**: API endpoints and regex patterns are implementation-specific and subject to change if APIs update.
- [ ] T013b [US1] Implement arXiv PDF extractor in `src/ingest/arxiv_extractor.py`. **Specifics**: Use the `arxiv` Python package to search `cat:cond-mat.mtrl-sci AND ball milling`. **Algorithm**: **DO NOT limit to 50 papers.** Instead, implement a dynamic loop that fetches papers in batches (e.g., 50 at a time) and accumulates experiments until either the global target (total) is met, the local source contribution limit is reached, or the source is exhausted. Use `arxiv.Search(..., max_results=50, sort_by=arxiv.SortCriterion.Relevance, sort_order=arxiv.SortOrder.Descending)` in a loop, incrementing the start index. If the search returns no results, log a warning "Source skipped: arXiv (no results found)" and skip. For each paper, download PDF and use `pdfminer.six` to scrape tables. **Pagination**: Iterate through results until the target is met or no more results are found. **Extraction Logic**: Scan tables for headers containing 'D10', 'D50', or 'D90' and extract the corresponding row values. Use regex patterns `r'milling_speed[:\s]*(\d+)'`, `r'milling_time[:\s]*(\d+)'`, etc., to extract specific values. **MANDATORY**: For every successfully fetched row, record `source_name="arXiv"` and `source_id` (the arXiv ID, e.g., "2301.12345"). **CRITICAL**: If a row lacks `source_id`, it MUST be flagged for manual review and logged immediately, but NOT dropped from the count unless it lacks valid data in other fields. **Output**: `data/raw/arxiv_tables.json`. **Schema**: JSON array of objects with keys: `experiment_id`, `source_name`, `source_id`, `milling_speed`, `milling_time`, `ball_to_powder_ratio`, `youngs_modulus`, `density`, `d10`, `d50`, `d90`, `material_type`, `process_duration`. **Verification**: Script `src/ingest/arxiv_extractor.py` exists and implements `pdfminer.six` logic; output file path is defined; `data/raw/arxiv_tables.json` exists with at least one row. **Constraint**: Rows without `source_id` are flagged, not immediately dropped. **Note**: API endpoints and regex patterns are implementation-specific and subject to change if APIs update.
- [ ] T014a [US1] Implement image detection logic to identify PSD curves/images in PDFs. **Algorithm**: Use `pdf2image.convert_from_path` to convert PDF pages to images. Use `cv.Canny` with thresholds (low=50, high=150) followed by `cv2.findContours`. Flag a page as containing a PSD image if the number of contours > 10 AND the aspect ratio of the bounding box is within the range [0.5, 2.0]. **Note**: The Canny/contour algorithm is an implementation choice for the 'detection' step; the spec requires flagging but allows flexible detection methods. **Function Signature**: `detect_psd_images(pdf_path: str) -> list[str]`. **Output**: `data/raw/detected_psd_images.json` containing a list of image paths. **Verification**: Function `detect_psd_images` is defined with the correct signature and logic; test fixture file path is referenced.
- [ ] T014b [US1] **Flagging Logic**: Implement logic to flag unstructured entries to `data/flagged_psd.log` with **specific schema: `experiment_id`, `source`, `issue_type`, `raw_blob_hash`**. **Requirement**: The fallback extraction logic (T014c) MUST be implemented in the codebase regardless of config; the config only controls whether it is *activated* or if entries are flagged for manual curation. **Trigger**: Must run after T014a detects images. **Dependency**: T014a must precede T014b. **Verification**: `data/flagged_psd.log` exists with correct schema.
- [ ] T014c [US1] **OCR Extraction Implementation**: Implement the actual OCR/extraction fallback logic in `src/ingest/ocr_fallback.py`. **Specifics**: Read `config.yaml` key `ocr.fallback_enabled`. **Logic**: The extraction logic MUST be implemented and callable regardless of the config. **If `ocr.fallback_enabled` is false**: Do NOT execute OCR; skip extraction and flag entries for manual review only. **MUST explicitly log the flagged entry for manual curation as the only option.** Log "Flagged for Manual Curation: [experiment_id]" to `data/flagged_psd.log`. **If `ocr.fallback_enabled` is true**: Use `easyocr` to extract text from the image (input format: PNG, high-resolution, RGB). Apply regex pattern `r'D(10|50|90)[\s:]*([-+]?\\d+(?:\\.\\d+)?)'` to parse D-values from the OCR output string. **Mapping Logic**: If multiple D-values appear on one line, sort them by magnitude (smallest to largest) and map to D10, D50, D90 respectively. If ambiguous, default to D50. Validate that the extracted value is a valid float. If regex fails, extraction fails, or easyocr is not installed/raises an exception, flag the row for manual review (do NOT raise an error that halts the pipeline). **Function Signature**: `extract_psd_from_image(image_path: str, flagged_entry_id: str, config: dict) -> dict`. **Deliverable**: A function that conditionally attempts extraction based on config. **Verification**: Unit test file `tests/unit/test_ocr.py` exists and contains the specified test functions; the function successfully parses a mock image with known D-values. This task is MANDATORY per FR-008 but must be configurable. **Dependency**: T014b must precede T014c.
- [ ] T014d [US1] **Manual Curation Workflow**: Implement documentation for the manual curation process for flagged entries. **Specifics**: Create `docs/manual_curation.md` describing how to manually review and enter data for entries flagged by T014b/T014c. **Verification**: File `docs/manual_curation.md` exists and describes the workflow.
- [ ] T015a [US1] **Merge and Deduplicate**: Implement data merger and deduplication logic in `src/ingest/merge.py`. **Specifics**: Merge data from T012, T013, T013b, AND T014c (OCR output). **MANDATORY**: Validate that every row in the merged dataframe has non-null `source_name` and `source_id`. If any row lacks these, flag it for manual review and log "Row flagged: missing traceability metadata". **Traceability Count Check**: Immediately after merging, count the number of rows with valid `source_id`. **CRITICAL**: If the count of traceable rows is < 150, **Log critical warning: "Traceable dataset size < 150 experiments (minimum viable) per spec SC-004"** and **raise `InsufficientDataError`** (halting the pipeline) with the same message. **Pre-merge Check**: If the merged dataset has < 150 rows (excluding flagged rows that lack valid data), log a critical warning but do NOT halt if the traceable count is sufficient. **Output**: `data/raw/merged_dataset.parquet`. **Verification**: Script logic to merge, validate traceability, and check traceable count (halt if <150) is implemented; output file path is defined; output file contains at least one valid row with `source_name` and `source_id` columns. **Constraint**: This task halts if traceable rows < 150. **Dependency**: T015a depends on the completion of T012, T013, T013b, and the T014 phase (T014a, T014b, T014c if enabled). **Note**: If OCR is disabled, T015a proceeds immediately without waiting for T014c execution.
- [ ] T015c [US1] **Process Flagged Entries**: Implement logic to read `data/flagged_psd.log` (produced by T014b) and call `extract_psd_from_image` (T014c) if enabled. Update the merged dataframe with extracted values. **Output**: `data/raw/final_merged_dataset.parquet`. **Verification**: Logic to process flagged entries exists; output file `data/raw/final_merged_dataset.parquet` exists and contains updated data. **Dependency**: Must run after T015a and T014b. **Note**: T015a does not halt if total rows are sufficient; it only halts if traceable rows < 150. T015c runs only if T015a completes successfully.
- [ ] T016e [US1] **Process Duration Extraction**: Implement logic to extract 'process_duration' from the source data (Materials Project, NIST, arXiv). **Constraint**: If the value is missing in the source data, **set to NaN** (do NOT derive values from other features). If the column 'process_duration' is entirely absent from the dataframe, **create it with NaN values**. **Crucial Note**: While deriving defaults from other features is forbidden, **imputation (T016a) is explicitly permitted and required** for 'process_duration' if the source field is missing, as it is a required feature per FR-010. **Verification**: Output column exists; missing values are set to NaN; imputation has not yet run. **Dependency**: Must run AFTER T015a (Merge) and T015c (Process Flagged). **Clarification**: The NaN values set here are intended to be filled by T016a.
- [ ] T016a [US1] Multiple imputation (IterativeImputer) for missing values in **ALL required predictors (including Young's modulus, density, process_duration)** (EXCLUDING targets D10/D50/D90). **Function Signature**: `apply_imputation(df: pd.DataFrame) -> pd.DataFrame`. **Output**: `data/processed/imputed_dataset.parquet`. **Verification**: Output file exists and has no nulls in predictor columns. **Specific Verification**: Confirm that `process_duration` column is non-null after imputation. **Dependency**: Must run AFTER T016e. **Clarification**: This task imputes the NaN values set by T016e for `process_duration`.
- [ ] T016b [US1] One-hot encoding for `material_type`. **Specifics**: Create `src/preprocess/encoding.py` with function `apply_one_hot(df: pd.DataFrame) -> pd.DataFrame`. **Verification**: Output file exists; new columns are non-null; no data loss.
- [ ] T016c [US1] Standard scaling for numeric features. **Specifics**: Create `src/preprocess/scaling.py` with function `apply_scaling(df: pd.DataFrame) -> pd.DataFrame`. **Verification**: Output file exists; scaled columns have mean=0, std=1.
- [ ] T017a [US1] **Schema Validation**: Validate the processed dataset against `contracts/dataset.schema.yaml`. **Input**: `data/processed/ball_milling_dataset.parquet` (output of T016). **Verification**: Schema validation passes. **Dependency**: Must run BEFORE T017b.
- [ ] T017b [US1] **Pre-Halt Size Check (Warning Only)**: Check if the processed dataset has >= 150 rows. If < 150, log a critical warning but do NOT halt. **Verification**: Warning is logged if count < 150. **Dependency**: Must run AFTER T017a.
- [ ] T017c [US1] **Post-Processing Size Gate (HALT)**: Validate that the processed dataset still meets the minimum viable threshold of >= 150 rows. **CRITICAL**: If count < 150, **raise `SystemExit` with code 1** and log "Processed dataset size < 150 experiments (minimum viable) per spec SC-004". **Note**: Flagged rows that passed schema validation are included in this count. **Verification**: Function `check_processed_size` is implemented with the logic to raise `SystemExit(1)` with the specific error message if count < 150. This is the definitive size gate for SC-004. **Dependency**: Must run AFTER T017a and T017b.
- [ ] T018 [US1] Create main ingestion CLI entry point in `src/cli/ingest.py` to orchestrate T012-T017. **Specifics**: Implement the following sequence: 1) Ingestion (T012, T013, T013b) -> 2) Flagging (T014a -> T014b) -> 3) OCR (T014c if enabled) -> 4) Merge & Traceability Check (T015a) -> 5) Process Flagged (T015c) -> 6) Process Duration Extraction (T016e) -> 7) Preprocess (T016a-c) -> 8) Schema Validation (T017a) -> 9) Warning Check (T017b) -> 10) Halt Gate (T017c). **CRITICAL**: T018 must ensure T014b runs before T015a, and T014c runs before T015c if enabled. T015a must halt if traceable rows < 150. T017c must run last. **Verification**: Script `src/cli/ingest.py` exists and implements the correct orchestration flow.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean dataset produced)

---

## Phase 4: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train and validate Gaussian Process Regression (GPR) and Random Forest (RF) models using Nested Cross-Validation (Repeated) to predict particle size distribution outcomes, with a computational fallback to RF only if GPR exceeds resource limits.

**Independent Test**: Can be fully tested by running the training pipeline on the preprocessed dataset and verifying that cross-validation scores are computed, the computational fallback triggers if limits are exceeded, and statistical power is reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for Nested CV implementation in `tests/unit/test_model.py`. **Specifics**: Implement function `test_generate_splits_stratified_by_d50`. **Action**: Call `generate_splits` with `q=10`. **Verification**: Assert that splits are stratified by binned D50 (check distribution similarity across folds).
- [ ] T020 [P] [US2] Integration test for model fallback logic in `tests/integration/test_model_fallback.py`. **Specifics**: Implement function `test_fallback_on_resource_limit`. **Action**: Mock `psutil` to report runtime > 1800s. **Verification**: Assert that `GPRResourceLimitExceeded` is raised, RF is trained, and GPR is not re-trained.

### Implementation for User Story 2

- [ ] T021 [US2] Implement stratified nested CV with fallback logic in `src/model/nested_cv.py`. **Specifics**: Use `pandas.qcut` with `q=10` for D50 stratification. **Pre-check**: Before calling `qcut`, verify that the number of unique D50 values is >= q. If unique values < q, immediately call `reduce_bins(q)` logic (reduce q by half: 10 -> 5 -> 2). If `q=1`, log warning "Stratification disabled: insufficient unique values" and **HALT the pipeline with a critical error** (raise `StratificationError`) to prevent biased random splits. **Algorithm for `reduce_bins(q)`**: If q is odd, round down to nearest even number; if q < 2, raise error. Merge adjacent bins if q is reduced. **Enforce 5x2 structure**: Outer loop = 5 folds, Inner loop = 2 folds. **Deliverable**: A function `generate_splits(n_repeats, seed)` returning a list of `(train_idx, test_idx)` tuples that handles ties and reduces bins as needed. **Verification**: Unit test `tests/unit/test_model.py::test_splits_are_stratified_by_d50` is defined and passes; logic reduces `q` and raises `StratificationError` when `q=1`.
- [ ] T029a [US2] Implement GPR training with ARD kernel in `src/model/train_gpr.py` using inner CV for tuning. **Specifics**: Use `sklearn.gaussian_process.GaussianProcessRegressor` with ARD kernel. Monitor runtime and memory; if limits breached, raise `GPRResourceLimitExceeded` (defined in T023b). **Note**: This task defines the GPR training logic as a module for T029c to import and execute. **Dependency**: Must run AFTER T023b.
- [ ] T029b [US2] Implement Random Forest training (≤1000 trees) in `src/model/train_rf.py` using same Nested CV scheme (standalone, no fallback logic needed here). **Output**: `results/model_rf.pkl`. **Note**: This task defines the RF training logic as a module for T029c to import and execute.
- [ ] T029c [US2] **Orchestration**: Implement the CLI logic in `src/cli/train.py` that: 1) Imports and *calls* the GPR training logic defined in T029a in a try/except block; 2) Catches `GPRResourceLimitExceeded`; 3) **MUST ALWAYS attempt GPR first**. **If GPR SUCCEEDS**: Log success and **MUST NOT train Random Forest** (RF is skipped to satisfy FR-009 fallback constraint). **If GPR FAILS** (raises `GPRResourceLimitExceeded`): Log fallback event and train Random Forest (T029b) as the **ONLY** model (fallback path). 4) Proceeds with evaluation. **Specifics**: RF training is executed **ONLY** in the failure path. **Verification**: Integration test `tests/integration/test_model_fallback.py::test_fallback_on_resource_limit` is defined and passes; script `src/cli/train.py` catches the exception and logs the fallback event; RF is trained in the failure path. **Dependency**: T029a and T029b are **module implementations** ready for T029c to invoke.
- [ ] T025 [US2] Implement Linear Regression baseline in `src/model/baseline_lr.py` using same Nested CV scheme
- [ ] T026 [US2] Implement evaluation metrics calculation (R², RMSE, MAE) on **outer folds** (using dynamic splits) in `src/evaluate/metrics.py`
- [ ] T027 [US2] Implement Nadeau & Bengio corrected resampled t-test in `src/evaluate/statistical_tests.py` (α = 0.05) to compare ML models vs baseline. **Specifics**: Implement the formula: `t = (mean_diff) / sqrt( (var_diff / n) * (1 + n * rho) )` where `rho` is the correlation between training and test errors. **Calculation of rho**: `rho = cov(e_train, e_test) / (std(e_train) * std(e_test))`. **Verification**: Implementation of Nadeau & Bengio formula is present in `src/evaluate/statistical_tests.py` with comments explaining the variance correction.
- [ ] T030 [US2] Implement a priori and a posteriori power analysis in `src/evaluate/power_analysis.py`. **Specifics**:
 1. **A Priori**: Calculate the minimum detectable effect size (MDES) for a target power level of adequate statistical power and (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value) based on the dataset size, assuming a hypothesized effect size (Cohen's f² = 0.15). **Documentation**: Explicitly document the limitation of this fixed assumption in code comments and output file: "Power analysis based on fixed effect size assumption (f²=0.15) for exploratory ML; results are indicative, not definitive."
 2. **A Posteriori**: Calculate the **achieved statistical power** (1 - beta) based on the **observed effect size** derived from the cross-validation results (R² difference between ML and baseline). **Adjustment**: If the observed effect size deviates > 50% from f²=0.15, recalculate achieved power using the observed effect size and log the adjustment. **Output**: `results/power_analysis_result.txt` containing MDES, the achieved power value, and a note on limitations. **Verification**: Script `src/evaluate/power_analysis.py` is implemented to calculate and write MDES, achieved power, and a note on limitations to `results/power_analysis_result.txt`.
- [ ] T031 [US2] Implement dynamic split evaluation reporting in `src/evaluate/held_out_report.py` (if distinct from T026)

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently (models trained, metrics computed)

---

## Phase 5: User Story 3 - Model Interpretability and Visualization (Priority: P3)

**Goal**: Generate partial dependence plots and export feature importance rankings to interpret how milling parameters influence particle size distribution.

**Independent Test**: Can be fully tested by running the visualization script and verifying that PNG plots are generated showing PSD response to individual parameters.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Unit test for plot generation in `tests/unit/test_interpret.py`. **Specifics**: Implement function `test_generate_partial_dependence_plot`. **Action**: Call `generate_partial_dependence_plot(model, feature='milling_speed')`. **Verification**: Assert that a PNG file is generated with x-axis label "Milling Speed" and file size < 5MB.

### Implementation for User Story 3

- [ ] T033 [US3] Implement partial dependence plot generation in `src/interpret/partial_dependence.py` (plots for speed, time, ratio, Young's modulus, Process Duration)
- [ ] T034 [US3] Implement feature importance export in `src/interpret/feature_importance.py` (JSON output with ranked features)
- [ ] T035 [US3] Create main interpret CLI entry point in `src/cli/interpret.py` to orchestrate T033-T034:
 - [ ] T035a Generate partial dependence plots
 - [ ] T035b Export feature importance JSON
 - [ ] T035c **Validate total plot size ≤ 10MB ** and raise error if exceeded (US-3 acceptance criteria). **Verification**: Integration test `tests/integration/test_interpret.py::test_plot_size_limit_enforced` is defined.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & CI Integration

**Purpose**: Assemble final results and ensure reproducibility on CI

- [ ] T036 [P] Assemble `results/` folder contents: `metrics.csv`, `t_test_summary.txt`, `partial_dependence_*.png`, `feature_importance.json`, `associational_disclaimer.txt`, **AND `power_analysis_result.txt`** (from T030).
- [ ] T037 [P] Implement `src/utils/generate_report.py` to consolidate all outputs, **explicitly formatting and including the power analysis metrics (MDES and achieved power) from T030 in the final human-readable report text alongside the t-test results**.
- [ ] T038 [P] Create GitHub Actions workflow `.github/workflows/ci.yml`:
 - [ ] T038a Run full pipeline
 - [ ] T038b Validate schema
 - [ ] T038c **Enforce a job time limit of a predefined duration.** using `timeout-minutes: 360` in the workflow definition at the **job level** (e.g., `jobs: build: timeout-minutes: 360`). (SC-005, Constitution Principle VI) **Note**: While the plan targets a '≤ 5 h wall-clock' runtime for optimization, the hard CI limit MUST be 360 minutes (6 hours) to align with the spec's SC-005 and prevent rejecting valid runs that fall between 5h and 6h. **Verification**: Run `scripts/validate_ci_timeout.py` to confirm `timeout-minutes` is set to 360. If the job is killed by the runner before the script can log the timeout, the CI system will log 'Job exceeded 360 minute limit' and the task will be marked as failed with exit code 1.
 - [ ] T038d [P] Create `scripts/validate_ci_timeout.py` to check `.github/workflows/ci.yml` for `timeout-minutes: 360`. **Verification**: Script exists and returns 0 if timeout is set correctly.

- [ ] T039 [P] Update `quickstart.md` with execution instructions

---

## Phase 7: Review Resolution (COMPLETED)

**Status**: **COMPLETED** - Logic from T045-T050 has been merged into the original tasks. No separate tasks are required.

- [X] T045 [US1] **Fix Data Flow Order**: Ensure `src/ingest/merge.py` (T015a) completes **before** `src/utils/size_gate.py` (T015c - removed, logic merged) is invoked. **Action**: Update `src/cli/ingest.py` (T018) to strictly enforce the sequence: Ingestion -> Merge -> Size Gate (Halt) -> Preprocess -> Size Gate (Halt). **Verification**: Unit test `tests/integration/test_ingest_flow.py::test_merge_precedes_size_gate` is defined.
- [X] T046 [US2] **Fix Stratification Logic**: Update `src/model/nested_cv.py` (T021) to handle the case where `pandas.qcut` fails on the target `D50` due to insufficient unique values (ties). **Action**: Implement a fallback mechanism that reduces the number of bins (`q`) by half (10 -> 5 -> 2) until a valid split is possible. If `q=1` is reached, log a warning "Stratification disabled: insufficient unique values" and **HALT the pipeline** (raise `StratificationError`) to prevent biased random splits. **Verification**: Unit test `tests/unit/test_model.py::test_stratification_fallback_on_ties` is defined.
- [X] T047 [US2] **Fix Statistical Test Implementation**: Update `src/evaluate/statistical_tests.py` (T027) to explicitly implement the **Nadeau & Bengio corrected resampled t-test** formula, ensuring the variance correction term accounts for the overlap between training and test sets in cross-validation. **Action**: Do not use `scipy.stats.ttest_rel` directly; implement the corrected variance formula manually using the outer fold predictions. **Verification**: Implementation of Nadeau & Bengio formula is present in `src/evaluate/statistical_tests.py` with comments explaining the variance correction.
- [X] T048 [US1] **Hardening: Real Data Only**: Audit all ingestion scripts (`src/ingest/*.py`) to ensure **NO** `try/except` blocks fall back to `generate_synthetic_*`, `mock_*`, or random data generators. **Action**: If a real fetch fails, the script MUST log a warning and skip that source (partial success) or raise a specific error if *all* sources fail. **Verification**: Code scan confirms absence of synthetic fallback patterns in ingestion logic.
- [X] T049 [US2] **Hardening: Power Analysis Context**: Update `src/evaluate/power_analysis.py` (T030) to explicitly document the limitation of using a **fixed** hypothesized effect size (Cohen's f² = 0.15) given the observational nature of the data. **Action**: Add a comment in the code and a line in the output file (`results/power_analysis_result.txt`) stating: "Power analysis based on fixed effect size assumption (f²=0.15) for exploratory ML; results are indicative, not definitive." **Verification**: Script `src/evaluate/power_analysis.py` and `results/power_analysis_result.txt` are created with the required documentation.
- [X] T050 [US3] **Hardening: Plot Size Validation**: Ensure `src/cli/interpret.py` (T035c) calculates the total file size of all generated plots **after** generation but **before** returning success. **Action**: If total size > 10MB, raise a `SystemExit` with a clear error message listing the offending files. **Verification**: Integration test `tests/integration/test_interpret.py::test_plot_size_limit_enforced` is defined.

---

## Phase 8: Data Robustness & Streaming (COMPLETED)

**Purpose**: Address concerns regarding large dataset handling, streaming implementation, and strict adherence to "Real Data Only" principles without synthetic fallbacks.

**Goal**: Ensure the pipeline can handle datasets larger than RAM via streaming, strictly avoids synthetic data, and properly documents sampling strategies if full streaming is infeasible.

- [X] T051 [US1] **Removed**: Streaming logic integrated into T012/T013.
- [X] T052 [US1] **Removed**: Sampling fallback is NOT permitted. The pipeline must halt if <150 rows.
- [X] T053 [US1] **Audit for Synthetic Fallbacks**: Perform a rigorous code audit of `src/ingest/*.py` and `src/preprocess/*.py` to ensure **zero** `try/except` blocks that instantiate `generate_synthetic_*`, `mock_*`, or `random.*` data when a real fetch fails. **Action**: If a real fetch fails, the code must either skip the source (logging a warning) or raise a specific error. **Verification**: Static analysis script `scripts/check_synthetic_fallbacks.py` returns 0 errors.
- [X] T054 [US1] **Update Documentation for Streaming**: Update `quickstart.md` and `README.md` to explicitly document the **manual chunking** strategy used in T012/T013 and the **halt** policy if <150 rows are found (no sampling fallback is used). **Verification**: Documentation accurately reflects the chunking/halt logic.

---

## Phase 9: Final Verification & Execution Readiness

**Purpose**: Ensure the entire pipeline is ready for execution on the CI runner, with all data flow, error handling, and resource constraints verified.

**Goal**: Conduct a final end-to-end verification of the task list, ensuring all dependencies are met, all "Real Data Only" constraints are enforced, and the pipeline can execute within the 6-hour CI limit.

- [X] T055 [P] [US1] **Final Data Flow Verification**: Execute a dry-run of `src/cli/ingest.py` with a small, known subset of data. **Specifics**: Command: `python src/cli/ingest.py --dry-run --input data/raw/sample_subset.json`. **Verification**: Dry-run completes without error, and logs confirm the correct execution order (Ingestion -> Merge -> Flagging -> OCR -> Preprocess -> Schema Validation -> Size Gate). **Dependency**: Requires T018 to be implemented.
- [X] T056 [P] [US2] **Final Model Pipeline Verification**: Execute a dry-run of `src/cli/train.py` with a small, pre-processed dataset. **Specifics**: Command: `python src/cli/train.py --dry-run --input data/processed/small_sample.parquet`. **Verification**: Dry-run completes without error, and logs confirm the correct execution flow and fallback logic. **Dependency**: Requires T029c to be implemented.
- [X] T057 [P] [US3] **Final Interpretability Verification**: Execute a dry-run of `src/cli/interpret.py` with a pre-trained model. **Specifics**: Command: `python src/cli/interpret.py --dry-run --model results/model_rf.pkl`. **Verification**: Dry-run completes without error, and logs confirm the correct execution flow and size validation. **Dependency**: Requires T035 to be implemented.
- [X] T058 [W] **Final Documentation Update**: Update `README.md` and `quickstart.md` to include the final execution instructions, including the dry-run commands (T055-T057) and the full pipeline execution command. **Specifics**: Clearly state the minimum viable dataset size and the consequences of falling below it. Document the "Real Data Only" policy and the lack of synthetic fallbacks. **Verification**: Documentation is up-to-date and accurate.
- [X] T059 [P] **CI Workflow Final Check**: Run validation script `scripts/validate_ci_timeout.py` against `.github/workflows/ci.yml`. **Specifics**: Script must verify `timeout-minutes: 360` is present at the job level. **Verification**: Script execution returns 0 (success).

---

## Phase 10: Final Analysis & Cleanup (Revision Pass)

**Purpose**: Address final concerns from the analysis phase regarding the strictness of the "Real Data Only" policy and the specific implementation of the NIST fetcher.

**Goal**: Ensure the NIST fetcher uses a verified, working endpoint and that the "Real Data Only" policy is explicitly documented in the code comments of the ingestion scripts.

- [ ] T060 [US1] **Verify NIST Endpoint Implementation**: Review `src/ingest/nist_repo.py` to ensure it uses a **verified, working** NIST Search API endpoint. **Action**: Replace any placeholder or unverified URL with the actual NIST Search API endpoint (e.g., `https://www.nist.gov/...` or a specific DOI-based resolver if available). If no public API is found, **document the limitation** in `docs/data_sources.md` and **halt the NIST fetcher** with a clear error message "NIST API unavailable; skipping source" rather than attempting a fallback. **Verification**: Code scan confirms the URL is a real, documented NIST endpoint or the fallback logic is explicitly disabled.
- [ ] T061 [US1] **Explicit "Real Data Only" Documentation**: Add a **prominent comment block** at the top of `src/ingest/materials_project.py`, `src/ingest/nist_repo.py`, and `src/ingest/arxiv_extractor.py`. **Action**: The comment must state: "REAL DATA ONLY: This script fetches data from a verified public source. If the fetch fails, the script logs a warning and skips this source. NO synthetic or mock data is generated or used. The pipeline will halt if the total traceable dataset size is < 150 rows." **Verification**: Code scan confirms the presence of this comment block in all three files.

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
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Explicit Sequential Chains (Critical for Data Flow)

- **Data Pipeline (US1)**: T012/T013/T013b (Ingestion) → T014a (Image Detection) → T014b (Flagging) → T014c (OCR if enabled) → T015a (Merge & Traceability Check/Halt) → T015c (Process Flagged) → **T016e (Process Duration Extraction)** → **T016a (Imputation)** → **T016b (Encoding)** → **T016c (Scaling)** → **T017a (Schema Validation)** → **T017b (Warning Check)** → **T017c (Halt Gate)** → **T018 (CLI)**. **T015a depends on T012/T013/T013b AND the T014 phase completion**. **T015c depends on T015a and T014b**. **T016e depends on T015a and T015c**. **T016a depends on T016e**. **T017a depends on T016c**. **T017b depends on T017a**. **T017c depends on T017b**. **T018 depends on T017c**. **T014a -> T014b -> T014c (conditional) -> T015a**.
- **Source Resolution (Phase 2)**: None (Removed UCI Fallback chain).
- **Model Pipeline (US2)**: T021 (CV Setup) → **T029 (Orchestration: Try GPR, Catch Exception, Train RF ONLY if GPR fails)** → T026 (Eval). T029a and T029b are **module implementations** ready for T029c to invoke. **T029c invokes T029a/T029b**.
- **Review Resolution (Phase 7)**: Logic merged into T018a, T021, T027, T030, T035c.
- **Data Robustness (Phase 8)**: T053 (Audit) and T054 (Documentation) are the final steps. T051 logic is integrated into T012/T013. **Sampling fallback is removed; pipeline must halt if <150 rows.**
- **Final Verification (Phase 9)**: T055-T059 are the final steps to ensure execution readiness.
- **Final Analysis (Phase 10)**: T060 and T061 are the final steps to ensure strict adherence to "Real Data Only" and verified endpoints.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Unit test for data ingestion error handling in tests/unit/test_ingest.py"
Task: "Unit test for OCR extraction in tests/unit/test_ocr.py"
Task: "Unit test for streaming memory constraints in tests/unit/test_streaming.py"

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
- **Critical**: Every fetched row MUST include `source_name` and `source_id` (traceability). Rows lacking these MUST be flagged for manual review, not immediately dropped unless they lack valid data in other fields.
- **Critical**: GPR fallback to Random Forest must be automatic and logged if >30min (1800s) or >5GB RAM (configurable). **Only train RF if GPR fails.** RF is trained in the failure path.
- **Critical**: All findings must be framed as associational (not causal).
- **Critical**: 'Process Duration' must be extracted from source data in T016e. If missing, set to NaN. **Imputation (T016a) is permitted for this feature** if the source field is missing.
- **Critical**: Unstructured PSD data (images) must be detected and flagged for manual curation in T014; **OCR is conditional** (T014c) and must respect the `ocr.fallback_enabled` config flag, but the logic must be implemented regardless.
- **Critical**: The test set split must be generated dynamically (no static file) and stratified by **quantile-binned D50** (the target) to prevent material-specific bias.
- **Critical**: The fallback logic in T029c must explicitly catch `GPRResourceLimitExceeded` and train RF **only in the failure path** to satisfy FR-003.
- **Critical**: CI workflow must enforce a **reasonable** job time limit. to align with the spec, while noting the 5-hour internal target.
- **Critical**: Dataset size check: T015a (pre-processing) is the **halt** gate for traceable rows. T017c (post-processing) is the final halt gate for SC-004. **T007b (Schema Validation) does NOT check row count; it only validates schema structure.**
- **Critical**: No task may implement a `try/except` block that falls back to `generate_synthetic_*()` or `mock_*()` data when a real fetch fails. The execution stage handles retries; the code must fail loudly OR skip and log.
- **Parent Task Status**: Tasks T014, T016, T021, and T029 are grouping headers only. Their sub-tasks (e.g., T014a-c) are the actionable items. Do not check the parent boxes.
- **Critical**: T043 and T044 (UCI Fallback) have been REMOVED. The pipeline must strictly adhere to FR-001 (Materials Project, NIST, arXiv) and halt if <150 rows.
- **Critical**: T013 now explicitly uses the resolved NIST Search API and does NOT fallback to UCI.
- **Critical**: T016e strictly extracts 'Process Duration' and sets to NaN if missing. **Imputation is permitted.**
- **Critical**: T030 includes a fixed effect size of 0.15 for MDES and calculates the achieved power based on observed effect sizes.
- **Critical**: T045-T050 address specific data flow, statistical validity, and robustness concerns raised in the review phase.
- **Critical (New)**: T053 (Audit) and T054 (Documentation) address the requirement for strict avoidance of synthetic data. T051 logic is integrated into T012/T013. **Sampling fallback is removed; pipeline must halt if <150 rows.**
- **Critical (New)**: T055-T059 ensure the entire pipeline is ready for execution, with all data flow, error handling, and resource constraints verified.
- **Critical (New)**: T060 and T061 address the final concerns regarding the NIST endpoint verification and explicit "Real Data Only" documentation.