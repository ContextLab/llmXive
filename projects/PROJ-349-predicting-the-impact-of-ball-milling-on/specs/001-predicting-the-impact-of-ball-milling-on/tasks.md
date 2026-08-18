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

- [X] T001 [P] Create setup script and manifest. **Action**: Generate `scripts/setup_manifest.txt` listing the required directory structure (`src/`, `tests/`, `data/raw`, `data/processed`, `data/splits`, `results`, `contracts/`, `.github/workflows/`). Then generate `scripts/setup.sh` to create the directory structure listed in the manifest. **Verification**: Both files exist and `setup.sh` successfully creates the directories.
- [X] T002 [P] Create `requirements.txt`. **Action**: Create `requirements.txt` with pinned versions of `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `statsmodels==0.14.*`, `matplotlib==3.9.*`, `seaborn==0.13.*`, `requests==2.32.*`, `tqdm==4.66.*`, `pyarrow==16.*`, `pdfminer.six==20231228`. **Optional Dependencies**: Create a separate `requirements-optional.txt` for `easyocr==1.7.*`, `opencv-python==4.8.*`, `pdf2image==1.16.*`. **Verification**: Files exist.
- [X] T002b [P] Verify `requirements.txt`. **Action**: Run `pip check` or similar to ensure all dependencies are resolvable. **Verification**: No dependency conflicts reported.
- [X] T003a [P] Configure linting (flake8). **Action**: Create `.flake8` with standard configs including `max-line-length = 88 `. **Verification**: File `.flake8` exists and contains `max-line-length = 88 `.
- [X] T003b [P] Configure formatting (black). **Action**: Create `pyproject.toml` (or `setup.cfg`) with black configuration. **Verification**: File exists and contains valid black config.
- [X] T004 [P] Initialize Git Repository. **Action**: Run `git init` in the project root and create an initial commit with `.gitignore`. **Verification**: `.git` directory exists and `git log` shows an initial commit.

---

## Phase 2: Foundational (Blocking Prerequisites & Source Resolution)

**Purpose**: Core infrastructure, data source resolution, and streaming utility that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement seed management utility in `src/utils/seed.py` to pin all random states.
- [X] T006 [P] Setup logging infrastructure in `src/utils/logger.py` with level configuration.
- [X] T008 [P] Configure error handling in `src/utils/exceptions.py`: Define custom exceptions including `DataIngestionError`, `MissingTimestampError`, `GPRResourceLimitExceeded`, `InsufficientDataError`, and `MissingDataError`.
- [X] T007a [P] Define dataset schema in `contracts/dataset.schema.yaml` with explicit field requirements.
- [X] T007b [P] Implement validation logic in `src/preprocess/validate_schema.py` to enforce `contracts/dataset.schema.yaml`.
- [X] T009 [P] Configure `config.yaml` template in `src/config/` with keys for API endpoints, resource limits (`gpr_max_runtime`, `gpr_max_memory`), and OCR fallback settings (`ocr.fallback_enabled`).
- [X] T009b [P] Implement `load_config()` function in `src/config/settings.py`.
- [X] T020 [P] [US1] Implement Streaming Utility in `src/ingest/streaming_utils.py`. **Action**: Create a generator-based utility that implements chunked HTTP/CSV/JSON/PDF reading for the specific formats of Materials Project (JSON/GraphQL), NIST (CSV/JSON), and arXiv (PDF). **Implementation Details**: Use `requests` for HTTP chunking, `csv`/`json` for parsing, and `pdfminer.six` for PDF text extraction. **Note**: Do NOT use `datasets.load_dataset(..., streaming=True)` as these sources are not hosted on Hugging Face. For the current dataset size (≤500 rows), this utility may process data in a single pass; streaming is implemented for future scalability. **Verification**: Unit test `test_streaming_loader.py` confirms memory usage remains constant (< 2GB) while processing a small real subset of data from the actual sources. The test must NOT use synthetic data.
- [X] T021 [P] [US1] Integrate Streaming Utility with Materials Project and NIST fetchers. **Action**: Modify `src/ingest/materials_project.py` and `src/ingest/nist_repo.py` to use `streaming_utils.py` for data ingestion. **Verification**: Integration test `test_streaming_ingest.py` confirms data is processed in chunks (or single pass if small) and the final merged dataset is identical to a non-streaming run on a small subset.
- [X] T022 [P] [US1] Implement Sample Size Reporting. **Action**: Add a function `report_sample_statistics()` in `src/preprocess/summary.py` that logs the total number of rows processed, the number of rows dropped due to missing values, and the final count of usable rows. **Verification**: Log output includes a clear statement of the final dataset size and any sampling limitations (e.g., "Final dataset: [count] (minimum viable threshold not met)").
- [X] T023 [P] [US1] Verify Real Data Source Integration. **Action**: Ensure that the ingestion process uses the verified real data sources (Materials Project, NIST, arXiv) and does not fall back to any synthetic or placeholder data. **Verification**: Code scan confirms no `generate_synthetic_*` or `mock_*` functions are present in the ingestion pipeline. **Note**: No runtime check is possible; rely on T053 static scan and verified source URLs.
- [X] T024 [P] [US1] Integrate Streaming with Unstructured Data Handling. **Action**: Update `src/ingest/streaming_utils.py` and the fetchers (T012, T013) to pass image/curve detection results (T014a) to the streaming pipeline, ensuring flagged entries are correctly identified and processed by the OCR fallback (T014c). **Verification**: Integration test `test_streaming_ocr_integration.py` confirms that unstructured data is correctly flagged and processed within the streaming context.
- [X] T060 [P] Verify NIST Endpoint or Disable with Error. **Action**: Update `src/ingest/nist_repo.py` to use the verified NIST API endpoint or, if unavailable, raise a specific error message. **Verification**: Code scan confirms URL is valid or error message is present.
- [X] T061 [P] Add Real Data Only Documentation. **Action**: Add a comment block starting with "REAL DATA ONLY:..." to `src/ingest/materials_project.py`, `nist_repo.py`, and `arxiv_extractor.py`. **Verification**: Code scan confirms the presence of the comment block in all three files.

---

## Phase 3: User Story 1 - Data Aggregation and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**:

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying the output CSV contains ≥500 (2506.09162, https://arxiv.org/abs/2506.09162) rows (target) or ≥150 rows (minimum viable) with non-null values for all required predictor variables and target PSD metrics.

- [X] T018 [P] [US1] Create main ingestion CLI entry point in `src/cli/ingest.py`. **Action**: Define the CLI orchestration that calls fetchers, merge, preprocess, and validation steps. **Verification**: CLI executes tasks in the exact order: Materials Project → NIST → arXiv → Image detection (T014a) → Flagging (T014b) → OCR (T014c) → Merge/Dedup (T015a) → Process duration (T016e) → Derivation (T067) → Imputation (T016a) → Encoding (T016b) → Scaling (T016c) → Schema validation (T017a) → Size checks (T017b). Note: T018 defines the flow; individual tasks implement the steps.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`. **Specifics**: Implement function `test_schema_validation_passes(df)`. **Action**: Use `jsonschema.validate(instance=df.to_dict(), schema=load_schema('contracts/dataset.schema.yaml'))`. **Verification**: Test passes if schema matches; fails with specific `jsonschema.ValidationError` if mismatch.
- [X] T011 [P] [US1] Unit test for data ingestion error handling in `tests/unit/test_ingest.py`.
- [X] T011b [P] [US1] Unit test for OCR extraction in `tests/unit/test_ocr.py`.
- [X] T011c [P] [US1] Unit test for streaming/chunking memory constraints in `tests/unit/test_streaming.py`.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement Materials Project data fetcher in `src/ingest/materials_project.py`. **Dependency**: Must use streaming utility from T020.
- [X] T013 [P] [US1] Implement NIST repository downloader in `src/ingest/nist_repo.py`. **Dependency**: Must use streaming utility from T020.
- [X] T013b [P] [US1] Implement arXiv PDF extractor in `src/ingest/arxiv_extractor.py`. **Dependency**: Must use streaming utility from T020 for text extraction.
- [X] T014a [P] [US1] Implement image detection logic to identify PSD curves/images in PDFs. **Verification**: Unit test `test_image_detection.py` confirms `detect_psd_images` returns correct lists for curated test PDFs (contains curves vs. none).
- [X] T014b [P] [US1] Flag unstructured PSD entries for manual curation. **Action**: Implement function `flag_unstructured_entry()` in `src/ingest/flagger.py`. Write flagged entries to `data/flagged_psd.log` with a specific schema. **Verification**: Unit test `test_flagging.py` confirms that `flag_unstructured_entry` writes to the log and returns the count of flagged entries. The log must include a summary count at the end of the run.
- [X] T014c [P] [US1] OCR fallback to extract data from flagged images. **Action**: If `ocr.fallback_enabled` is true, attempt extraction. If regex fails, extraction fails, or easyocr is not installed, flag the row for manual review (do NOT raise an error that halts the pipeline). **Crucial**: If extraction fails or is disabled, the row is flagged for manual review and logged, NOT dropped. The pipeline must verify remaining traceable rows >= 150 before proceeding. **Verification**: Unit test `test_ocr_extraction.py` passes, specifically verifying that `extract_psd_from_image` flags entries to `data/flagged_psd.log` when extraction fails or config is disabled, and does not drop the row.
- [X] T015a [P] [US1] Merge and deduplicate data from multiple sources. **Action**: Implement function `merge_and_deduplicate()` in `src/ingest/merge.py`. Combine data from T012, T013, T013b. Deduplicate by `experiment_id` (keeping the first occurrence or averaging conflicting values as per spec edge case). Write the result to `data/raw/merged_dataset_temp.parquet`. **Dependency**: T012, T013, T013b. **Verification**: Unit test `test_merge_logic.py` verifies that the output file exists, contains unique IDs, and that the row count matches the sum of unique inputs minus duplicates.
- [X] T016e [P] [US1] Extract 'process_duration' from source data. **Dependency**: T015a. **Verification**: Column `process_duration` exists in the processed parquet; values are taken directly from source fields; missing values remain `NaN`. No derivation from other columns is performed.
- [X] T067 [P] [US1] Derive 'process_duration' if missing. **Action**: Implement function `derive_process_duration()` in `src/preprocess/derive_duration.py`. If `process_duration` is missing in a row, attempt to derive it from start/end timestamps. If derivation is impossible, flag the row as missing (do not use silent defaults). **Dependency**: T016e. **Verification**: Unit test `test_duration_derivation.py` confirms the column is populated or correctly flagged as NaN, and that no silent default values are used.
- [X] T016a [P] [US1] Multiple imputation for missing values. **Action**: Use `IterativeImputer` with `random_state=SEED` (from T005) to impute missing values. **Crucial**: Exclude target variables `D10`, `D50`, `D90` from imputation to prevent leakage. **Dependency**: T067 (to ensure `process_duration` is available for imputation if needed). **Verification**: Verify that `D10`, `D50`, `D90` columns are NOT imputed and that `random_state` is explicitly set to the project seed.
- [X] T016b [P] [US1] One-hot encode categorical features. **Action**: One-hot encode `material_type` using `OneHotEncoder` with `drop='first'` and `handle_unknown='ignore'`. **Verification**: Verify `material_type` is encoded, first category is dropped, and unknown categories are handled.
- [X] T016c [P] [US1] Standard scale numeric features. **Action**: Define `StandardScaler` to be used in the model training loop. **Features**: Explicitly list `milling_speed`, `milling_time`, `ball_to_powder_ratio`, `youngs_modulus`, `density`, `process_duration` as features to be scaled. **Note**: Actual fitting occurs inside the Nested CV loop in T029a/T029b. **Verification**: Verify the list of features includes `process_duration` and that the scaler class is correctly defined.
- [X] T017a [P] [US1] Save preprocessed dataset. **Action**: Write the preprocessed data (after imputation, encoding, scaling config) to `data/processed/ball_milling_dataset.parquet`. **Verification**: File exists and contains all processed columns.
- [X] T017b [P] [US1] Post-processing size gate: halt if < 150 rows. **Action**: Validate the processed dataset against schema and check row count. **Verification**: `jsonschema.validate` is called on `data/processed/ball_milling_dataset.parquet` against `contracts/dataset.schema.yaml`; raises no errors. If < 150 rows, raise `SystemExit(1)` with message "Processed dataset size < 150 experiments (minimum viable) per spec SC-004". If 150 <= rows < 500, log a critical warning: "Warning: Dataset size ([count]) is below target (500) but meets minimum viable threshold (150). Proceeding with caution."

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean dataset produced)

---

## Phase 4: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train and validate machine learning models (Gaussian Process Regression and Random Forest) on the aggregated dataset.

**Independent Test**: Can be fully tested by running the training pipeline on the preprocessed dataset and verifying that cross-validation scores are computed, the computational fallback triggers if limits are exceeded, and statistical power is reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for Nested CV implementation in `tests/unit/test_model.py`.
- [X] T065 [P] [US2] Integration test for model fallback logic in `tests/integration/test_model_fallback.py`.

### Implementation for User Story 2

- [X] T062 [P] [US2] Implement Dynamic Bin Calculation for Stratification. **Action**: Create `src/model/bin_calculator.py` to calculate the number of bins `q` dynamically based on the number of unique D50 values in the current fold. If `unique_D50 < 10`, set `q = max(2, unique_D50)`. **Verification**: Unit test `test_dynamic_stratification_bins.py` confirms that when a dataset with 5 unique D50 values is passed, the splitter uses 5 bins (or 2 if forced minimum), and no `ValueError` is raised.
- [X] T063 [P] [US2] Implement Fallback to Non-Stratified Split for Low-Cardinality Targets. **Action**: If the number of unique D50 values is 1 or 2 (making stratification impossible even with minimal bins), implement a fallback logic in `src/model/bin_calculator.py` to switch to standard `KFold` (non-stratified) for that specific fold, while logging a warning. **Verification**: Integration test `test_fallback_to_kfold.py` confirms that when a dataset with 1 unique D50 value is used, the pipeline switches to `KFold` and logs a specific warning message: "Stratification impossible (unique D50 < 2), falling back to KFold."
- [X] T021 [P] [US2] Implement stratified nested CV with multiple folds and enforced `q` bins. **Action**: Implement `NestedStratifiedKFold` in `src/model/train_gpr.py` and `src/model/train_rf.py` using the logic from T062 and T063. **Verification**: Unit test `test_splits_are_stratified_by_d50.py` confirms outer folds are stratified, that `reduce_bins` triggers only when unique D50 < 10, and that a `StratificationError` is raised if `q` would become 1. **Dependency**: T062, T063. **Note**: This is a library module implementation, not a runtime step.
- [X] T029a [P] [US2] Implement GPR training with ARD kernel in `src/model/train_gpr.py` using inner CV for tuning. **Action**: Train GPR with `StandardScaler` fit only on the training fold of each outer CV split. **Verification**: Verify that the scaler is fit only on the training fold and that GPR uses the same Nested CV scheme as T021 with a **5x2** configuration (5 outer folds, 2 inner folds).
- [X] T029b [P] [US2] Implement Random Forest training (≤1000 trees) in `src/model/train_rf.py`. **Action**: Train RF with `StandardScaler` fit only on the training fold of each outer CV split. **Verification**: Verify that the scaler is fit only on the training fold and that RF uses the same Nested CV scheme as T021 with a **5x2** configuration (5 outer folds, 2 inner folds).
- [X] T068 [P] [US2] Implement Resource Monitor for GPR Training. **Action**: Create a context manager or decorator `monitor_resources()` in `src/model/resource_monitor.py`. It must monitor CPU time and RAM usage during GPR training. If limits (time / storage) are exceeded, it must raise `GPRResourceLimitExceeded`. **Verification**: Integration test `test_resource_monitor_triggers_fallback.py` confirms that the exception is raised when simulated resource limits are hit.
- [X] T071 [P] [US2] Implement CLI orchestration for training. **Action**: Create `src/cli/train.py` to orchestrate the training pipeline. **Dependency**: T029a, T029b, T068. **Verification**: CLI executes the training flow and logs events.
- [X] T072 [P] [US2] Implement fallback trigger logic in `src/cli/train.py`. **Action**: Within `train.py`, implement the logic to catch `GPRResourceLimitExceeded` raised by T068 and switch to Random Forest only. **Dependency**: T068, T071. **Verification**: Integration test `test_fallback_on_resource_limit.py` confirms that when `GPRResourceLimitExceeded` is raised, the pipeline skips GPR and proceeds with RF only, logging the fallback event.
- [X] T025 [P] [US2] Implement Linear Regression baseline in `src/model/baseline_lr.py`. **Verification**: Verify `src/model/baseline_lr.py` implements Linear Regression using the same Nested CV scheme as T021 with a **5x2** configuration.
- [X] T026 [P] [US2] Implement evaluation metrics calculation (R², RMSE, MAE) on outer folds. **Verification**: `src/evaluate/metrics.py` writes `results/metrics.csv` containing the three metrics for each model.
- [X] T026b [P] [US2] Verify Nested CV Structure. **Action**: Generate a report of metrics on the outer folds of the Nested CV (x2). **Precondition**: Verify dataset size >= 150 rows before proceeding; if < 150, halt with error. **Dependency**: Must be implemented after T017b (Size Gate). **Verification**: Verify `src/evaluate/nested_cv_report.py` generates a report of metrics on the outer folds, confirming the **5x2** split structure and that no static hold-out split was used.
- [X] T027 [P] [US2] Implement Nadeau & Bengio corrected resampled t-test. **Verification**: `src/evaluate/statistical_tests.py` includes comments explaining variance correction and unit test `test_nadeau_bengio.py` validates against known examples.
- [X] T069 [P] [US2] Implement Corrected Resampled T-Test Validation. **Action**: Create a test `tests/unit/test_nadeau_bengio_validation.py` that validates the `src/evaluate/statistical_tests.py` implementation against a known synthetic dataset with a pre-calculated t-statistic and p-value (using the Nadeau & Bengio correction). **Verification**: Test passes only if the calculated values match the expected reference values within a specified tolerance.
- [X] T030 [P] [US2] Perform **a priori** power analysis to determine Minimum Detectable Effect Size (MDES). **Action**: Calculate MDES based on the actual dataset size (N), a fixed power of 0.80, and alpha = 0.05. **Verification**: Script writes `results/power_analysis_result.txt` containing the exact string: "Minimum Detectable Effect Size (MDES) calculated for N=[N], power=0.80, alpha=0.05: [value]".
- [X] T070 [P] [US2] Perform **post-hoc** power analysis for t-test. **Action**: Calculate the statistical power of the actual t-test performed in T027 based on the observed effect size. **Verification**: Script appends to `results/power_analysis_result.txt` or creates `results/t_test_power.txt` with the exact string: "Post-hoc statistical power for t-test (observed effect size): [value]".

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently (models trained, metrics computed)

---

## Phase 5: User Story 3 - Model Interpretability and Visualization (Priority: P3)

**Goal**: Generate partial dependence plots and export feature importance rankings to interpret how milling parameters influence particle size distribution.

**Independent Test**: Can be fully tested by running the visualization script and verifying that PNG plots are generated showing PSD response to individual parameters.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T032 [P] [US3] Unit test for plot generation in `tests/unit/test_interpret.py`.

### Implementation for User Story 3

- [X] T033 [P] [US3] Implement partial dependence plot generation in `src/interpret/partial_dependence.py`.
- [X] T034 [P] [US3] Implement feature importance export in `src/interpret/feature_importance.py` (JSON output with ranked features). **Verification**: JSON file `results/feature_importance.json` contains an ordered list of `{feature, importance}` objects; unit test `test_feature_importance_format.py` validates schema.
- [X] T035 [P] [US3] Create main interpret CLI entry point in `src/cli/interpret.py`. **Verification**: CLI runs partial dependence and feature importance steps; respects total plot size limit of a manageable storage threshold. Unit test `test_interpret_cli_flow.py` checks correct orchestration.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & CI Integration

**Purpose**: Assemble final results and ensure reproducibility on CI

- [X] T036 [X] Assemble `results/` folder contents. **Verification**: `results/` contains `metrics.csv`, `t_test_summary.txt`, all `partial_dependence_*.png` (≤10 MB total), `feature_importance.json`, `associational_disclaimer.txt`, and `power_analysis_result.txt`. **Action**: `generate_report.py` must include a runtime assertion that the total size of all `partial_dependence_*.png` files is ≤10MB; if exceeded, the script must fail with a clear error message.
- [X] T037 [X] Generate report with all metrics. **Verification**: `src/utils/generate_report.py` produces `results/final_report.md` that includes metrics, power analysis summary, and disclaimer.
- [X] T038 [X] Create GitHub Actions workflow for CI. **Verification**: `.github/workflows/ci.yml` runs the full pipeline, validates schema, and sets `timeout-minutes` to a value sufficient to enforce the computational stability constraint.
- [X] T039 [X] Update quickstart documentation. **Verification**: `quickstart.md` lists execution instructions for the full pipeline plus dry‑run commands.

---

## Phase 7: Review Resolution (COMPLETED)

**Status**: **COMPLETED** - Logic from T045-T050 has been merged into the original tasks. No separate tasks are required.

## Phase 8: Data Robustness & Streaming (COMPLETED)

**Purpose**: Address concerns regarding large dataset handling, streaming implementation, and strict adherence to "Real Data Only" principles.

**Goal**: Ensure the pipeline can handle datasets larger than RAM via streaming, strictly avoids synthetic data, and properly documents sampling strategies if full streaming is infeasible.

## Phase 9: Final Verification & Execution Readiness

**Purpose**: Ensure the entire pipeline is ready for execution on the CI runner, with all data flow, error handling, and resource constraints verified.

**Goal**: Conduct a final end-to-end verification of the task list, ensuring all dependencies are met, all "Real Data Only" constraints are enforced, and the pipeline can execute within the CI time limit.

- [X] T053 [P] Audit for Synthetic Fallbacks. **Action**: Create `scripts/check_synthetic_fallbacks.py`. **Verification**: `scripts/check_synthetic_fallbacks.py` exists and scans `src/ingest/*.py` and `src/preprocess/*.py` for `generate_synthetic_*` or `mock_*` patterns; script exits with code 0 if none are found.
- [X] T054 [P] Update Documentation. **Verification**: `README.md` and `quickstart.md` contain a section titled **"Chunked Data Loading & Minimum Viable Dataset Policy"** describing the streaming approach and the `<150 rows` halt behavior.
- [X] T055 [P] Final Data Flow Verification. **Verification**: Running `python src/cli/ingest.py --dry-run --input data/raw/sample_subset.json` completes without error and logs the ordered execution of all US‑1 tasks.
- [X] T056 [P] Final Model Pipeline Verification. **Verification**: Running `python src/cli/train.py --dry-run --input data/processed/small_sample.parquet` completes without error and logs the training flow, including any fallback events.
- [X] T057 [P] Final Interpretability Verification. **Verification**: Running `python src/cli/interpret.py --dry-run --model results/model_rf.pkl` completes without error and logs plot generation and feature‑importance export.
- [X] T058 [P] Final Documentation Update. **Verification**: `README.md` and `quickstart.md` include the dry‑run commands (T055‑T057) and the full pipeline execution command (`python src/cli/ingest.py && python src/cli/train.py && python src/cli/interpret.py`).