# Tasks: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Input**: Design documents from `/specs/001-predicting-species-distribution-shifts/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Initialize project directory structure (Part 1): Create `projects/PROJ-181-predicting-species-distribution-shifts-u/` with subdirectories `data/`, `data/raw/`, `data/processed/`, `data/artifacts/`, `code/`, `code/utils/`. Ensure all directories contain `.gitkeep` files.

- [X] T001b [P] Initialize project directory structure (Part 2): Create `projects/PROJ-181-predicting-species-distribution-shifts-u/` with subdirectories `tests/unit/`, `tests/integration/`, `metrics/`, `reports/`, `logs/`, `state/`, `contracts/`. Ensure all directories contain `.gitkeep` files.

- [X] T002 [P] Initialize project with pinned dependencies (`requirements.txt`: `scikit-learn==1.5.0`, `geopandas==0.14.2`, `rasterio==1.3.9`, `pandas==2.2.2`, `numpy==1.26.4`, `requests==2.32.3`, `matplotlib==3.9.0`, `seaborn==0.13.2`); execute `pip install -r requirements.txt` in a fresh virtualenv to verify environment setup.
- [X] T003 [P] Configure linting (flake8) and formatting (black) tools: Create `.flake8` (max-line-length=100, exclude=venv,*.egg) and `pyproject.toml` (black config) at repository root.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` with paths, thresholds, random seeds, and `n_jobs=2` configuration. **Add `THINNING_DISTANCE_KM`** as a configurable float (default 10.0) for FR-002 compliance.
- [X] T005 [P] Initialize logging infrastructure: Configure logger to write to `logs/` with format `%(asctime)s - %(name)s - %(levelname)s - %(message)s`; ensure configuration supports immediate generation of `logs/preprocess_counts.yaml` by downstream tasks. Define the YAML schema for `logs/preprocess_counts.yaml` as: `species: str, before_count: int, after_count: int, timestamp: str, distance_used_km: float`.
- [X] T006 [P] Create utility module `code/utils/spatial_blocks.py` for spatial block cross-validation generation
- [X] T007 [P] Create `code/utils/data_utils.py` for coordinate validation, missing value imputation (nearest neighbor), and error handling
- [X] T009 [P] Create `contracts/` directory with JSON Schema files containing the following exact definitions:
 - `contracts/occurrence.schema.json`:
 ```json
 {
 "$schema": "http://json-schema.org/draft-07/schema#",
 "type": "object",
 "required": ["source_identifier", "download_timestamp", "original_dataset_name", "species", "decimalLatitude", "decimalLongitude", "eventDate"],
 "properties": {
 "source_identifier": {"type": "string"},
 "download_timestamp": {"type": "string", "format": "date-time"},
 "original_dataset_name": {"type": "string"},
 "species": {"type": "string"},
 "decimalLatitude": {"type": "number"},
 "decimalLongitude": {"type": "number"},
 "eventDate": {"type": "string"}
 }
 }
 ```
 - `contracts/model_metrics.schema.json`:
 ```json
 {
 "$schema": "http://json-schema.org/draft-07/schema#",
 "type": "object",
 "required": ["species", "algorithm", "auc", "tss", "threshold", "dataset_split"],
 "properties": {
 "species": {"type": "string"},
 "algorithm": {"type": "string"},
 "auc": {"type": "number"},
 "tss": {"type": "number"},
 "threshold": {"type": "number"},
 "dataset_split": {"type": "string"}
 }
 }
 ```
 Ensure files are valid JSON Schema and contain these required fields.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download historical occurrence records (1970-2000) and climate rasters, then preprocess (filter, thin, extract) to produce clean CSVs.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying that the output CSV contains unique coordinates where no two points are within the minimum distance defined in FR-002, and that climate variables are successfully extracted for every record.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/download.py` to fetch North American bird occurrence data (late th century) via GBIF API (**URL: `). **Logic**: Read target species list from `code/config.py`; use a **dynamic pagination loop** to fetch records until a target count is reached or the API returns no more results (do NOT use a hardcoded `maxResults=300` limit). Authenticate using `GBIF_API_KEY` environment variable. Map API response fields to CSV columns: `scientificName` -> `species`, `decimalLatitude` -> `decimalLatitude`, `decimalLongitude` -> `decimalLongitude`, `eventDate` -> `eventDate`, `basisOfRecord` -> `source_identifier`, `downloadDateTime` -> `download_timestamp`, `datasetKey` -> `original_dataset_name`. Save to `data/raw/occurrence_1970_2000.csv`. **Constraint**: Must include `source_identifier`, `download_timestamp`, and `original_dataset_name` metadata columns (Constitution Principle VI, FR-001).
- [ ] T011 [US1] Implement `code/download.py` to fetch recent occurrence data (from the early 2000s to 2020) for evaluation. **Logic**: Same as T010 but year filter 2005-2020; use **dynamic pagination loop** to ensure sufficient records. Save to `data/raw/occurrence_2005_2020.csv`. **Constraint**: Must include `source_identifier`, `download_timestamp`, and `original_dataset_name` metadata columns (Constitution Principle VI, FR-001).
- [ ] T015 [US1] Implement `code/download.py` to download WorldClim historical climate rasters (1970-2000) and CMIP6 SSP2-4.5 future climate rasters (2050) for **all 19 Bioclim variables** (bio1 through bio19), saving as individual rasters (e.g., `bio1.tif`) to `data/raw/climate_historical/` and `data/raw/cmip6_future/` respectively. **Logic**: Use `wget` or `requests` to download from WorldClim (https://worldclim.org/data/bioclim.html) and CMIP6 (https://esgf-node.llnl.gov/projects/cmip6/) mirrors. Validate that all 19 variables are present and non-null in both directories. **Constraint**: Must exit with code 1 if any variable is missing or partially downloaded (FR-001). **Dependency**: Logically independent of T010/T011 completion to allow parallel execution.

- [X] T013 [US1] Implement `code/preprocess.py` to filter records by breeding season, remove duplicates, and spatially thin points to a **configurable minimum distance**. **Logic**: **Read the threshold value explicitly from `config.THINNING_DISTANCE_KM`** (do not use a hardcoded value or vague terms). Use `geopandas.sjoin_nearest` with a buffer defined by this config value. **Modularity**: Must implement this logic as a reusable function `thin_occurrences(input_path, output_path, distance_km)` in `code/preprocess.py`. Write `logs/preprocess_counts.yaml` with `species`, `before_count`, `after_count`, `timestamp`, and `distance_used_km`. **Constraint**: Must run AFTER T010, T011 completion. **Dependency**: T005 (logging) must be complete.
- [ ] T013a [US1] Implement `code/preprocess.py` to check **historical (1970-2000)** data for FR-006 threshold (<100 records) **AFTER** T010 completion. **Logic**: Count raw records per species from `data/raw/occurrence_1970_2000.csv`; if <100, flag as 'INSUFFICIENT_DATA' in `metrics/data_sufficiency.json` with schema: `{"species": "str", "count": "int", "status": "INSUFFICIENT_DATA", "dataset_period": "historical"}`. **Dependency**: Must run AFTER T010 completion. **Note**: This runs in parallel with T013; it does not block T013 for species with sufficient data.
- [ ] T013b [US1] Implement `code/preprocess.py` to check **recent (2005-2020)** data for FR-006 threshold (<100 records) **AFTER** T011 completion. **Logic**: Count raw records per species from `data/raw/occurrence_2005_2020.csv`; if <100, flag as 'INSUFFICIENT_DATA' in `metrics/data_sufficiency.json` (appending to the same file as T013a) with schema: `{"species": "str", "count": "int", "status": "INSUFFICIENT_DATA", "dataset_period": "recent"}`. **Dependency**: Must run AFTER T011 completion. **Note**: This runs in parallel with T013; it does not block T013 for species with sufficient data.
- [X] T014 [US1] Implement `code/preprocess.py` to extract **ALL 19** climate variables from rasters (from T015) at occurrence coordinates (from T013), handling missing data via nearest neighbor imputation. **Logic**: Extract all variables first to satisfy FR-001 availability. **Dependency**: Must run AFTER T013, T015. <!-- FAILED: unspecified -->
- [X] T015a [US1] Implement `code/preprocess.py` (or new module `code/variable_selection.py`) to perform **Variance Inflation Factor (VIF)** analysis on the **extracted** climate variables (from T014) and select a non-collinear subset (target a reduced set of variables) for modeling. **Logic**: Load a **sample of 5000 occurrence points** (random stratified by species, seed=42) and extracted climate values; calculate VIF for all 19 variables; iteratively remove the highest VIF variable until all remaining variables have VIF < 5. Output the list of selected variable names to `metrics/selected_climate_variables.json`. **Note**: FR-001 is satisfied by T014's extraction of all 19 variables into `data/processed/`. T015a selects a subset for *modeling efficiency* only; the full dataset remains available. **Dependency**: Must run AFTER T014 completion.
- [X] T014b [US1] Implement `code/preprocess.py` to filter the extracted climate dataset (from T014) to **only include variables selected in T015a**, producing the final modeling dataset. **Dependency**: Must run AFTER T015a.
- [X] T017 [US1] Create `data/processed/occurrence_clean.csv` (using T014b output) and verify all records have non-null climate values; **exit with code 1 ONLY if unfixable missing data exists (e.g., coordinates outside raster bounds)**; otherwise log a warning for imputed values. **Dependency**: Must run AFTER T014b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train three SDM algorithms (Random Forest, Bioclim, Regularized Logistic Regression PB) using spatial block cross-validation on CPU.

**Independent Test**: Can be fully tested by training models on a single species subset and verifying that training completes successfully and outputs performance metrics (AUC, TSS) without CUDA errors.

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement `code/baseline.py` to create a null prevalence model for baseline expectation (SC-001), outputting `metrics/baseline_performance.csv`
- [X] T019 [US2] Implement `code/bias_null.py` to create a bias-only null model using random background sampling (replacing KDE layer). **Verification**: Ensure output file `metrics/bias_null_metrics.csv` is generated and contains columns `species`, `algorithm`, `auc`, `tss`. **Dependency**: Must run AFTER T013 (preprocessed data).
- [X] T020 [US2] Implement `code/power_analysis.py` to calculate minimum sample size for statistical power (post-thinning) using default parameters, outputting `metrics/power_analysis_report.json`
- [ ] T027 [US2] Implement **pre-training GPU check** in `code/train.py` (or `code/utils/gpu_check.py`). **Logic**: Run `torch.cuda.is_available()` and check `sklearn` device flags; log results to `logs/gpu_check.log`. **Constraint**: Exit with code 1 if CUDA is detected or if any GPU library is active. **Dependency**: Must run **BEFORE** T021, T022, T023 to prevent wasted compute.
- [ ] T021 [US2] Implement `code/train.py` to train Random RF (`sklearn.ensemble.RandomForestClassifier`) with `n_jobs=2` on CPU
- [ ] T022 [US2] Implement `code/train.py` to train Bioclim algorithm (custom percentile envelope)
- [ ] T023 [US2] Implement `code/train.py` to train Regularized Logistic Regression (Presence-Background) using `sklearn.linear_model.LogisticRegression` with L2 regularization. **Note: This implements the "MaxEnt-style" Presence-Background method described in US-2.**
- [ ] T024 [US2] Implement spatial block cross-validation logic in `code/train.py` using `code/utils/spatial_blocks.py` (FR-007)
- [X] T025 [US2] Save trained model artifacts to `data/artifacts/model_{species}_{algo}.pkl`. **Dependency**: Must run AFTER T021, T022, T023.
- [X] T026 [US2] Calculate and save AUC/TSS metrics to `metrics/training_metrics.csv`. **Dependency**: Must run AFTER T021, T022, T023.
- [ ] T046a [P] [US2] Implement `code/train.py` (or `code/utils/batch_reader.py`) to support **chunked processing** of large occurrence datasets. **Logic**: If `data/processed/occurrence_clean.csv` > 500MB, process in batches of **[deferred] rows**, accumulating model updates or statistics. **Constraint**: Must NOT use `try/except` to fall back to synthetic data; if the stream fails, raise an exception.
- [ ] T046b [P] [US2] Implement `code/train.py` to support **batched model training** if the feature matrix is too large. **Logic**: Use `sklearn`'s `partial_fit` (if available) or implement a batched training loop where the dataset is read in chunks, and the model is updated incrementally or statistics are aggregated before final training. **Constraint**: Must ensure model convergence is not compromised by batched updates. **Dependency**: Must run AFTER T046a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Future Projection and Evaluation (Priority: P3)

**Goal**: Project models onto CMIP6 SSP2-4.5 (2050) climate scenarios and evaluate against recent records (2005-2020) using statistical tests.

**Independent Test**: Can be fully tested by loading pre-trained models and running projections against the recent test set, producing a summary table of AUC/TSS improvements and niche stability metrics.

### Implementation for User Story 3

- [ ] T029b [US3] Implement `code/preprocess.py` (or extend existing) to filter, deduplicate, and thin the raw data (from T011) into `data/processed/occurrence_recent_clean.csv` for evaluation. **CRITICAL**: Read `metrics/data_sufficiency.json` (produced by T013b) to ensure consistency; **exclude** any species flagged as 'INSUFFICIENT_DATA' for the recent period. THEN apply thinning ONLY if the species is not flagged. **Logging**: For every excluded species, **log the specific count and reason directly to `logs/exclusion_log.csv`** (schema: `species, count, status, period`) at the moment of the exclusion decision. **Modularity**: Must call the reusable `thin_occurrences` function implemented in T013 (`code/preprocess.py:thin_occurrences`). **Dependency**: Must run AFTER T011 and T013b completion. **Note**: This task is a blocking dependency for US3 start.
- [ ] T028 [P] [US3] Implement `code/project.py` to load trained models and project onto future climate rasters (`data/raw/cmip6_future/`), saving `data/artifacts/projection_{species}_{algo}_2050.tif`. **Dependency**: Must run AFTER T021/T022/T023 and T015. (Note: T029b is NOT a dependency for T028).
- [ ] T047a [P] [US3] Update `code/project.py` to handle **large raster projections** by implementing **windowed reading** for rasters. **Logic**: Use `rasterio` windowed reading to avoid loading entire future climate rasters into memory.
- [ ] T047b [P] [US3] Update `code/project.py` to implement **windowed writing** for projections. **Logic**: Use `rasterio` windowed writing to save projection tiles incrementally.
- [ ] T047c [P] [US3] Update `code/project.py` to implement **tile stitching** for final projections. **Logic**: Combine windowed writes into a single coherent raster file. **Constraint**: Must NOT use `try/except` to fall back to synthetic data; if the stream fails, raise an exception.
- [ ] T029 [US3] Implement `code/evaluate.py` to evaluate projections against recent occurrence records from `data/processed/occurrence_recent_clean.csv` (produced by T029b). **Dependency**: Must run AFTER T029b AND T028 (projections must be available).
- [ ] T030 [US3] Implement `code/evaluate.py` to compute AUC and TSS for historical-to-future generalization (FR-009). **Dependency**: Must run AFTER T029.
- [ ] T031 [US3] Implement `code/evaluate.py` to perform niche stability checks by **comparing model performance on historical data projected to historical climate versus projected to future climate**, reporting the degradation as a measure of non-stationarity (FR-009). **Dependency**: Must run AFTER T029.
- [ ] T032 [US3] Implement `code/evaluate.py` to run non-parametric permutation tests or bootstrapped CI for model comparison (FR-010). **Logic**: Must read `metrics/data_sufficiency.json` and **exclude** any species flagged as 'INSUFFICIENT_DATA' before running tests. **Dependency**: Must run AFTER T019 (bias_null_metrics.csv) AND T029 (evaluation metrics).
- [ ] T034 [US3] Implement `code/sensitivity.py` to sweep suitability thresholds (low, low-moderate, moderate) and apply **multiple-comparison correction** for the family of tests. **Logic**: Input p-values from statistical tests run in T032 (format: list of dicts with `p_value`); apply correction (e.g., Holm-Bonferroni) to the **family of all pairwise model comparisons across all species**; output `metrics/sensitivity_report.csv` with corrected p-values (FR-005, SC-003).
- [X] T035 [US3] Save final results to `metrics/final_results.csv` and `metrics/sensitivity_report.csv`. **Dependency**: Must run AFTER T030, T031, T032, T034.
- [X] T036 [US3] Generate `reports/associational_disclaimer.txt` explicitly stating findings are associational (FR-008). **Dependency**: Must run AFTER T035.
- [X] T037 [US3] Verify total compute time stays within 6-hour limit (SC-002). **Logic**: Wrap pipeline execution in `time` command or log start/end timestamps to `metrics/runtime.log`; verify duration <= 360 minutes. **Action**: If duration > 360 minutes, log error, **exit with code 1**, and **generate a report of optimization recommendations** (e.g., "Reduce species count", "Increase chunk size") to `metrics/runtime_optimization_report.txt`. **Dependency**: Must run AFTER T035.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T038a [P] Write unit tests in `tests/unit/test_download.py` for download module
- [ ] T038b [P] Write unit tests in `tests/unit/test_preprocess.py` for preprocess module
- [ ] T038c [P] Write unit tests in `tests/unit/test_train.py` for train module
- [ ] T038d [P] Write unit tests in `tests/unit/test_project.py` for project module
- [ ] T038e [P] Write unit tests in `tests/unit/test_evaluate.py` for evaluate module
- [X] T039 [P] Write integration tests in `tests/integration/` for end-to-end pipeline on a single species subset
- [X] T040 [P] Run Reference-Validator Agent **on every artifact write that introduces or modifies citations** and **inside the Advancement-Evaluator before awarding any review point** (Constitution Principle II). **Constraint**: Execute unconditionally on the specified triggers; do NOT restrict to "only if files are modified".
- [X] T041 Update `README.md` with execution instructions and data provenance
- [X] T042 Run `quickstart.md` validation to ensure all artifacts are generated correctly
- [X] T043 Final review of `logs/preprocess_counts.yaml` and `metrics/` files for consistency

---

## Phase 7: Data Streaming & Robustness (Revision Pass)

**Goal**: Address review concerns regarding dataset size, streaming capability, and failure modes.

### Implementation for Robustness

- [ ] T044 [P] [US1] Update `code/download.py` to implement **streaming download** for large climate rasters (CMIP6) where file size > 2GB. **Logic**: Use `requests` with `stream=True` and write to disk in chunks (e.g., a fixed size) to `data/raw/cmip6_future/`. Do NOT load entire file into memory. **Constraint**: If a download fails, raise an explicit exception; DO NOT fall back to synthetic data or placeholder files.
- [ ] T045 [P] [US1] Update `code/download.py` to add a **verification step** after downloading climate rasters. **Logic**: Compute SHA-256 checksums of downloaded files and compare against known checksums (if available) or file size checks. Exit with code 1 if verification fails.
- [X] T048 [P] [General] Add a **`data/manifest.json`** file to track all downloaded datasets, their checksums, download timestamps, and source URLs. **Logic**: Update this manifest automatically upon successful download of any new dataset (T010, T011, T015).

---

## Phase 8: Streaming Data Pipeline Integration (Revision Pass)

**Goal**: Implement streaming ingestion for occurrence data to handle large datasets without loading them entirely into RAM, addressing the "Large real datasets" constraint.

### Implementation for Streaming Ingestion

- [ ] T049 [P] [US1] Refactor `code/download.py` to support **streamed occurrence data ingestion** when the GBIF API returns a large result set (e.g., > 1M records). **Logic**: Instead of buffering all records in memory, implement a generator-based fetcher that yields records in batches of **[deferred] rows** and writes them directly to a temporary CSV or database; process these batches incrementally for filtering/thinning rather than loading the full dataset. **Constraint**: Must NOT use `try/except` to fall back to synthetic data; if the stream fails, raise an exception.
- [ ] T050 [P] [US1] Refactor `code/preprocess.py` to support **streamed filtering and thinning**. **Logic**: Modify `thin_occurrences` to accept an input stream (generator) and process records in chunks, maintaining a spatial index (e.g., `rtree` or `geopandas` spatial index built incrementally) to efficiently check the distance constraint without holding all points in memory. **Dependency**: Must run AFTER T049.
- [ ] T051 [P] [US2] Refactor `code/train.py` to support **streamed model training** for Random Forest if the feature matrix is too large. **Logic**: Use `sklearn`'s `partial_fit` (if available for the estimator) or implement a batched training loop where the dataset is read in chunks, and the model is updated incrementally or statistics are aggregated before final training. **Dependency**: Must run AFTER T050.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Robustness (Phase 7)**: Depends on core implementation (Phases 3-6) but can be implemented in parallel with Polish tasks.
- **Streaming Pipeline (Phase 8)**: Depends on Phase 7 tasks for infrastructure readiness; can be implemented in parallel with other Phase 7 tasks.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output and US1 recent data processing

### Within Each User Story

- Models before services
- Services before endpoints (where applicable)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase 7 tasks are independent of each other and can run in parallel.
- Phase 8 tasks are independent of each other and can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Launch all parallel tasks for User Story 1:
Task: "Implement code/download.py to fetch North American bird occurrence data (1970-2000)"
Task: "Implement code/download.py to fetch recent occurrence data (2005-2020)"
Task: "Implement code/download.py to download WorldClim and CMIP6 climate rasters"
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
 - Developer B: User Story 2 (Training)
 - Developer C: User Story 3 (Projection/Eval)
 - Developer D: Phase 7 (Robustness/Streaming)
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
- **Critical**: All models must run on CPU-only libraries (scikit-learn) without CUDA/GPU dependencies.
- **Critical**: All data must be real (GBIF, WorldClim, CMIP6); no synthetic data fabrication.
- **Critical**: Constitution Principle VI requires `source_identifier`, `download_timestamp`, `original_dataset_name` in all raw CSVs.
- **Critical**: T015 must explicitly download all 19 Bioclim variables (bio1-bio19) and validate them.
- **Critical**: T014 extracts ALL 19 variables first; T015a performs VIF; T014b filters to selected variables.
- **Critical**: T013a and T013b are the canonical checks for FR-006, writing to `metrics/data_sufficiency.json`.
- **Critical**: T013 enforces a configurable thinning distance from `config.THINNING_DISTANCE_KM` (FR-002) and logs the actual distance used.
- **Critical**: T017 only fails on unfixable missing data (outside bounds), allowing imputation.
- **Critical**: T027 runs BEFORE training (T021-T023) and uses Python-level checks (`torch.cuda.is_available()`).
- **Critical**: T028 does NOT depend on T029b (projection only needs models and rasters).
- **Critical**: T029 depends on T028 (projections must exist).
- **Critical**: T040 runs Reference-Validator unconditionally on specified triggers.
- **Critical**: T034 mandates multiple-comparison correction (e.g., Holm-Bonferroni) on the family of all pairwise model comparisons.
- **Critical**: No bias correction via KDE/effort data (T010c, T012 removed); bias handled via random background sampling.
- **Critical**: T019 must generate `metrics/bias_null_metrics.csv` and is a dependency for T032.
- **Critical**: T037 must log runtime to `metrics/runtime.log`, exit with code 1 if limit exceeded, and generate optimization recommendations.
- **Critical**: T013 must implement a reusable `thin_occurrences` function.
- **Critical**: T029b must call the reusable `thin_occurrences` function from T013 and log exclusion counts to `logs/exclusion_log.csv` at the moment of exclusion.
- **Critical**: T044, T046a, T046b, T047a, T047b, T047c, T049, T050, T051 implement streaming/chunking to handle large datasets within memory constraints.
- **Critical**: T045, T048 ensure data integrity and provenance tracking.
- **Critical**: No fallback to synthetic data on download failure; explicit exceptions must be raised.
- **Critical**: T010 and T011 must use pagination loops, not hardcoded limits.
- **Critical**: T032 must exclude species flagged in `metrics/data_sufficiency.json`.
- **Critical**: T049, T050, T051 implement streaming ingestion and processing to handle occurrence datasets exceeding available RAM, ensuring the full real dataset (or a well-defined sample) is used without fabrication.
- **Critical**: T049 must raise an exception on stream failure; no synthetic fallback.
- **Critical**: T050 must maintain spatial index integrity across chunks to ensure accurate thinning.
- **Critical**: T051 must ensure model convergence is not compromised by batched updates.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T052 Reconcile run-book vs implementation for `code/bias_correction.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/bias_correction.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
