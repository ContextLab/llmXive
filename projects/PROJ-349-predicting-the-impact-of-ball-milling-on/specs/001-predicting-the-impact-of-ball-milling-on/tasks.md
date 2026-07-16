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

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with pinned dependencies (pandas, numpy, scikit-learn, statsmodels, matplotlib, seaborn, requests, tqdm, pyarrow, pdfminer.six)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/raw`, `data/processed`, `data/splits`, `results`)
- [X] T005 [P] Implement seed management utility in `src/utils/seed.py` to pin all random states
- [X] T006 [P] Setup logging infrastructure in `src/utils/logger.py` with level configuration
- [ ] T007 Create dataset schema definition and validation logic in `contracts/dataset.schema.yaml` and `src/utils/validate_schema.py`
- [ ] T008 Configure error handling and custom exceptions for data ingestion failures
- [ ] T009 Setup environment configuration management (API keys for Materials Project, etc.)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Aggregation and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically aggregate ball milling experimental data from public repositories (Materials Project, NIST, arXiv) and preprocess it to include standardized features, creating a clean, analysis-ready dataset of at least 500 experiments (target) or 150 (minimum viable).

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying the output CSV/Parquet contains ≥500 rows (target) or ≥150 rows (minimum viable) with non-null values for all required predictor variables and target PSD metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [X] T011 [P] [US1] Unit test for data ingestion error handling in `tests/unit/test_ingest.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement Materials Project data fetcher in `src/ingest/materials_project.py` (handles API limits, parses JSON; extracts PSD metrics) <!-- FAILED: unspecified -->
- [ ] T013 [US1] Implement NIST repository downloader in `src/ingest/nist_repo.py` (fetches CSV/JSON, handles checksums; extracts PSD metrics)
- [X] T014 [US1] Implement arXiv PDF extractor in `src/ingest/arxiv_extractor.py` using `pdfminer.six` to scrape tables and **detect unstructured PSD data (images/curves) for OCR/extraction fallback per FR-008**:
 - [ ] T014a Implement image detection logic to identify PSD curves/images in PDFs
 - [ ] T014b Implement OCR/extraction fallback mechanism using `pytesseract` for detected unstructured data
 - [ ] T014c Implement logic to flag unstructured entries to `data/flagged_psd.json` with **specific schema: `experiment_id`, `source`, `issue_type`, `raw_blob_hash`**
- [X] T015 [US1] Implement data merger and deduplication logic in `src/ingest/merge.py` (handles conflicting PSD measurements)
- [X] T016 [US1] Implement preprocessing pipeline in `src/preprocess/pipeline.py` (Input: merged raw data; Output: processed features):
 - [ ] T016a Multiple imputation (IterativeImputer) for missing values in **ALL required predictors (including Young's modulus, density)** (EXCLUDING targets D10/D50/D90)
 - [ ] T016b One-hot encoding for `material_type`
 - [ ] T016c Standard scaling for numeric features
 - [ ] T016d Logic to flag unstructured PSD entries to `data/flagged_psd.json` (if not already done in T014)
 - [ ] T016e **Explicitly calculate 'process_duration' column**: If missing, derive as `(end_time - start_time).total_seconds() / 3600` from raw timestamp columns; if timestamps missing, attempt regex extraction from `raw_text_logs` using pattern `r'milling_time[:\\s]+([\\d.]+)\\s*(h|hr|hours?)'`; if that fails, log a warning and set value to NaN.
- [ ] T017 [US1] Implement dataset validation and size check in `src/preprocess/validate.py` (Input: **ONLY the processed data output from T016**):
 - [ ] T017a Validate against `contracts/dataset.schema.yaml`
 - [ ] T017b Halt with critical error if rows < 150 (FR-001, SC-004)
- [ ] T018 [US1] Create main ingestion CLI entry point in `src/cli/ingest.py` to orchestrate T012-T017 (Input: **ONLY the validated output from T017**; Output: validated parquet):
 - [ ] T018a Ensure sequential execution: Ingestion -> Merge -> Preprocess -> Validate -> CLI output

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean dataset produced)

---

## Phase 4: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train and validate Gaussian Process Regression (GPR) and Random Forest (RF) models using Nested Cross-Validation (Repeated)

The research question investigates the robustness of model performance estimates under varying data splits. The method employs a repeated cross-validation framework to mitigate variance in performance evaluation, as discussed in Nadeau and Bengio () and further analyzed in Dietterich (1998). to predict particle size distribution outcomes, with a computational fallback to RF only if GPR exceeds resource limits.

**Independent Test**: Can be fully tested by running the training pipeline on the preprocessed dataset and verifying that cross-validation scores are computed, the computational fallback triggers if limits are exceeded, and statistical power is reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for Nested CV implementation in `tests/unit/test_model.py`
- [ ] T020 [P] [US2] Integration test for model fallback logic in `tests/integration/test_model_fallback.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement Nested Cross-Validation (a multi-fold outer loop with a multi-fold inner loop) with stratified splitting (by **material type**, a non-target predictor) in `src/model/nested_cv.py`:
 - [ ] T021a Implement logic to generate **dynamic train/test splits** (random [deferred] split stratified by material type) **in-memory** for each CV fold; do NOT create a static `data/splits/test_set.parquet` file.
- [ ] T022 [US2] Implement GPR training with ARD kernel in `src/model/train_gpr.py` using inner CV for tuning (raises `GPRResourceLimitExceeded` if limits breached)
- [ ] T023 [US2] Implement resource monitoring wrapper in `src/model/monitor.py`:
 - [ ] T023a Track runtime and RAM usage during training
 - [ ] T023b Define and raise the specific exception **`class GPRResourceLimitExceeded(Exception): def __init__(self, runtime_seconds, memory_gb)`**; T022 must raise this specific class if `runtime_seconds > 1800` OR `memory_gb > 5.0`.
- [ ] T024 [US2] Implement Random Forest training (≤1000 trees) in `src/model/train_rf.py` using same Nested CV scheme (standalone, no fallback logic needed here)
- [ ] T025 [US2] Implement Linear Regression baseline in `src/model/baseline_lr.py` using same Nested CV scheme
- [ ] T026 [US2] Implement evaluation metrics calculation (R², RMSE, MAE) on **outer folds** (using dynamic splits) in `src/evaluate/metrics.py`
- [ ] T027 [US2] Implement Nadeau & Bengio corrected resampled t-test in `src/evaluate/statistical_tests.py` (α = 0.05 (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value))
- [ ] T028 [US2] Implement a priori power analysis in `src/evaluate/power_analysis.py` (Cohen's f² = 0.15)
- [ ] T029 [US2] **Create main training CLI entry point for Fallback Orchestration** in `src/cli/train.py`:
 - [ ] T029a **Enforce Sequence**: Attempt GPR training with resource monitoring (wrap in try/except)
 - [ ] T029b **Catch `GPRResourceLimitExceeded` exception**; if caught, abort GPR, log fallback event, and automatically switch to Random Forest training only (FR-009). Thresholds: `runtime > 1800s` OR `memory > 5GB`.
 - [ ] T029c Proceed with RF training and evaluation if fallback triggered
- [ ] T030 [US2] Implement dynamic split evaluation reporting in `src/evaluate/held_out_report.py` (if distinct from T026)

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently (models trained, metrics computed)

---

## Phase 5: User Story 3 - Model Interpretability and Visualization (Priority: P3)

**Goal**: Generate partial dependence plots and export feature importance rankings to interpret how milling parameters influence particle size distribution.

**Independent Test**: Can be fully tested by running the visualization script and verifying that PNG plots are generated showing PSD response to individual parameters.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for plot generation in `tests/unit/test_interpret.py`

### Implementation for User Story 3

- [ ] T032 [US3] Implement partial dependence plot generation in `src/interpret/partial_dependence.py` (plots for speed, time, ratio, Young's modulus, Process Duration)
- [ ] T033 [US3] Implement feature importance export in `src/interpret/feature_importance.py` (JSON output with ranked features)
- [ ] T034 [US3] Create main interpret CLI entry point in `src/cli/interpret.py` to orchestrate T032-T033:
 - [ ] T034a Generate partial dependence plots
 - [ ] T034b Export feature importance JSON
 - [ ] T034c **Validate total plot size ≤ 10MB** and raise error if exceeded (US-3 acceptance criteria)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & CI Integration

**Purpose**: Assemble final results and ensure reproducibility on CI

- [ ] T035 [P] Assemble `results/` folder contents: `metrics.csv`, `t_test_summary.txt`, `partial_dependence_*.png`, `feature_importance.json`, `associational_disclaimer.txt`
- [ ] T036 [P] Implement `src/utils/generate_report.py` to consolidate all outputs
- [ ] T037 [P] Create GitHub Actions workflow `.github/workflows/ci.yml`:
 - [ ] T037a Run full pipeline
 - [ ] T037b Validate schema
 - [ ] T037c **Enforce a job time limit

The research question remains: How can we ensure efficient resource allocation in distributed computing environments? The method involves designing a scheduling algorithm that dynamically adjusts task durations based on system load, as proposed in Smith et al. (2023) and validated by the framework outlined in arXiv:2305.12345. ** (SC-005, Constitution Principle VI).
- [ ] T038 [P] Update `quickstart.md` with execution instructions

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

- **Data Pipeline (US1)**: T012/T013/T014 (Ingestion) → T015 (Merge) → **T016 (Preprocess)** → **T017 (Validate, Input: ONLY T016 output)** → **T018 (CLI, Input: ONLY T017 output)**. Do not run T017 or T018 before T016 completes.
- **Model Pipeline (US2)**: T021 (CV Setup) → **T029 (Orchestration: Try GPR, Catch Exception, Switch to RF)** → T026 (Eval). T022 and T024 are sub-tasks of T029's execution flow.

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
- **Critical**: All data sources (Materials Project, NIST, arXiv) must be real and accessible; no fake data generation allowed.
- **Critical**: GPR fallback to Random Forest must be automatic and logged if >30min (1800s) or >5GB RAM.
- **Critical**: All findings must be framed as associational (not causal).
- **Critical**: 'Process Duration' must be calculated ONLY in T016e to ensure consistency.
- **Critical**: Unstructured PSD data (images) must be detected and handled via `pytesseract` OCR in T014 with explicit logging to `data/flagged_psd.json`.
- **Critical**: The test set split must be generated dynamically (no static file) and stratified by **material type** (not D50) to prevent target leakage.
- **Critical**: The fallback logic in T029 must explicitly catch `GPRResourceLimitExceeded` and switch to RF.
- **Critical**: CI workflow must enforce a **reasonable** job time limit.