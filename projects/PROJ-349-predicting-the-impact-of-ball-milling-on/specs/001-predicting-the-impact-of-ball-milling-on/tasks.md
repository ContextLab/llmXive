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
- [X] T008 [P] Configure error handling in `src/utils/exceptions.py`: Define custom exceptions including `DataIngestionError`, `MissingTimestampError`, `GPRResourceLimitExceeded`, `InsufficientDataError`, and `MissingDataError`.
- [X] T007a [P] Define dataset schema in `contracts/dataset.schema.yaml` with explicit field requirements.
- [X] T007b [P] Implement validation logic in `src/preprocess/validate_schema.py` to enforce `contracts/dataset.schema.yaml`.
- [X] T009 [P] Configure `config.yaml` template in `src/config/` with keys for API endpoints, resource limits (`gpr_max_runtime`, `gpr_max_memory`), and OCR fallback settings (`ocr.fallback_enabled`).
- [X] T009b [P] Implement `load_config()` function in `src/config/settings.py`.
- [X] T060 [P] Verify NIST Endpoint or Disable with Error. **Action**: Update `src/ingest/nist_repo.py` to use the verified NIST API endpoint or, if unavailable, raise a specific error message. **Verification**: Code scan confirms URL is valid or error message is present.
- [X] T061 [P] Add Real Data Only Documentation. **Action**: Add a comment block starting with "REAL DATA ONLY: ..." to `src/ingest/materials_project.py`, `nist_repo.py`, and `arxiv_extractor.py`. **Verification**: Code scan confirms the presence of the comment block in all three files.

---

## Phase 3: User Story 1 - Data Aggregation and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**:

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying the output CSV contains ≥500 (2506.09162, https://arxiv.org/abs/2506.09162) rows (target) or ≥150 rows (minimum viable) with non-null values for all required predictor variables and target PSD metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`. **Specifics**: Implement function `test_schema_validation_passes(df)`. **Action**: Use `jsonschema.validate(instance=df.to_dict(), schema=load_schema('contracts/dataset.schema.yaml'))`. **Verification**: Test passes if schema matches; fails with specific `jsonschema.ValidationError` if mismatch.
- [X] T011 [P] [US1] Unit test for data ingestion error handling in `tests/unit/test_ingest.py`.
- [X] T011b [P] [US1] Unit test for OCR extraction in `tests/unit/test_ocr.py`.
- [X] T011c [P] [US1] Unit test for streaming/chunking memory constraints in `tests/unit/test_streaming.py`.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement Materials Project data fetcher in `src/ingest/materials_project.py`.
- [X] T013 [P] [US1] Implement NIST repository downloader in `src/ingest/nist_repo.py`.
- [X] T013b [P] [US1] Implement arXiv PDF extractor in `src/ingest/arxiv_extractor.py`.
- [X] T014a [P] [US1] Implement image detection logic to identify PSD curves/images in PDFs. **Verification**: Unit test `test_image_detection.py` confirms `detect_psd_images` returns correct lists for curated test PDFs (contains curves vs. none).
- [X] T014b [P] [US1] Flag unstructured PSD entries for manual curation. **Action**: Always flag entries to `data/flagged_psd.log` with a specific schema. **Verification**: Log file is populated with flagged entries.
- [X] T014c [P] [US1] OCR fallback to extract data from flagged images. **Action**: If `ocr.fallback_enabled` is true, attempt extraction. If regex fails, extraction fails, or easyocr is not installed, flag the row for manual review (do NOT raise an error that halts the pipeline). **Crucial**: If extraction fails or is disabled, the row is dropped from the final count. The pipeline must verify remaining traceable rows >= 150 before proceeding. **Verification**: Unit test `test_ocr_extraction.py` passes, specifically verifying that `extract_psd_from_image` flags entries to `data/flagged_psd.log` when extraction fails or config is disabled.
- [X] T015a [P] [US1] Merge and deduplicate data from multiple sources. **Verification**: Script either raises `InsufficientDataError` with message `"Processed dataset size < 150 experiments (minimum viable) per spec SC-004"` or produces `data/raw/merged_dataset.parquet` with ≥150 rows and unique `experiment_id` entries.
- [X] T015c [P] [US1] Process flagged entries (OCR or manual curation).
- [X] T016e [P] [US1] Extract 'process_duration' from source data. **Verification**: Column `process_duration` exists in the processed parquet; values are taken directly from source fields; missing values remain `NaN`. No derivation from other columns is performed.
- [X] T016a [P] [US1] Multiple imputation for missing values.
- [X] T016b [P] [US1] One-hot encode categorical features.
- [X] T016c [P] [US1] Standard scale numeric features.
- [X] T017a [P] [US1] Validate the processed dataset against schema. **Verification**: `jsonschema.validate` is called on `data/processed/ball_milling_dataset.parquet` against `contracts/dataset.schema.yaml`; raises no errors.
- [X] T017b [P] [US1] Pre-halt size check to ensure minimum viable data.
- [X] T017c [P] [US1] Post-processing size gate: halt if < 150 rows. **Verification**: Verify `SystemExit(1)` is raised with message "Processed dataset size < 150 experiments (minimum viable) per spec SC-004".
- [X] T018 [X] [US1] Create main ingestion CLI entry point in `src/cli/ingest.py`. **Verification**: CLI executes tasks in the exact order: Materials Project → NIST → arXiv → Image detection (T014a) → Flagging (T014b) → OCR (T014c) → Merge/Dedup (T015a) → Process duration (T016e) → Imputation (T016a) → Encoding (T016b) → Scaling (T016c) → Schema validation (T017a) → Size checks (T017b/c).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean dataset produced)

---

## Phase 4: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train and validate machine learning models (Gaussian Process Regression and Random Forest) on the aggregated dataset.

**Independent Test**: Can be fully tested by running the training pipeline on the preprocessed dataset and verifying that cross-validation scores are computed, the computational fallback triggers if limits are exceeded, and statistical power is reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for Nested CV implementation in `tests/unit/test_model.py`.
- [X] T020 [P] [US2] Integration test for model fallback logic in `tests/integration/test_model_fallback.py`.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement stratified nested CV (5×2) with enforced `q=10` bins when ≥10 unique D50 values exist; otherwise reduce to the maximum feasible number of bins (minimum 2). **Verification**: Unit test `test_splits_are_stratified_by_d50.py` confirms outer folds are stratified, that `reduce_bins` triggers only when unique D50 < 10, and that a `StratificationError` is raised if `q` would become 1.
- [X] T029a [P] [US2] Implement GPR training with ARD kernel in `src/model/train_gpr.py` using inner CV for tuning.
- [X] T029b [P] [US2] Implement Random Forest training (≤1000 trees) in `src/model/train_rf.py`.
- [X] T029c [P] [US2] Orchestrate GPR and RF training with fallback logic in `src/cli/train.py`. **Dependency**: Must run after T029a and T029b are COMPLETED (checked off). **Verification**: Integration test `test_fallback_on_resource_limit.py` confirms that when `GPRResourceLimitExceeded` is raised, the pipeline skips GPR and proceeds with RF only, logging the fallback event.
- [X] T025 [P] [US2] Implement Linear Regression baseline in `src/model/baseline_lr.py`. **Verification**: Verify `src/model/baseline_lr.py` implements Linear Regression using the same Nested CV scheme as T021.
- [X] T026 [P] [US2] Implement evaluation metrics calculation (R², RMSE, MAE) on outer folds. **Verification**: `src/evaluate/metrics.py` writes `results/metrics.csv` containing the three metrics for each model.
- [X] T027 [P] [US2] Implement Nadeau & Bengio corrected resampled t-test. **Verification**: `src/evaluate/statistical_tests.py` includes comments explaining variance correction and unit test `test_nadeau_bengio.py` validates against known examples.
- [X] T030 [P] [US2] Perform **a priori** power analysis based solely on dataset size and a hypothesized effect size (Cohen's f² = 0.15). **Verification**: Script writes `results/power_analysis_result.txt` containing the exact string: "Power analysis based on fixed effect size assumption (f²=0.15) for exploratory ML; results are indicative, not definitive."
- [X] T031 [P] [US2] Dynamic Split Evaluation. **Action**: Generate a report of metrics on the dynamic split. **Verification**: Verify `src/evaluate/held_out_report.py` generates a report of metrics on the dynamic split.

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

- [X] T036 [X] Assemble `results/` folder contents. **Verification**: `results/` contains `metrics.csv`, `t_test_summary.txt`, all `partial_dependence_*.png` (≤10 MB total), `feature_importance.json`, `associational_disclaimer.txt`, and `power_analysis_result.txt`.
- [X] T037 [X] Generate report with all metrics. **Verification**: `src/utils/generate_report.py` produces `results/final_report.md` that includes metrics, power analysis summary, and disclaimer.
- [X] T038 [X] Create GitHub Actions workflow for CI. **Verification**: `.github/workflows/ci.yml` runs the full pipeline, validates schema, and sets `timeout-minutes` to a sufficiently long duration to accommodate extended processing (e.g., several hours).
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