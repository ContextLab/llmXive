# Tasks: Quantifying the Effect of Alloying Elements on the Glass-Forming Ability of Metallic Glasses

**Input**: Design documents from `/specs/001-quantifying-the-effect-of-alloying-eleme/`
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

 Tasks MUST be organized by user story so each story can be independently
 implemented and tested.

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan by executing: `mkdir -p code/data code/models code/utils code/config data/raw data/processed state output tests/contract tests/integration tests/unit docs/paper docs/reports` (projects/PROJ-124-quantifying-the-effect-of-alloying-eleme/)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pymatgen, scikit-learn, pandas, numpy, shap, statsmodels, scipy)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004a [P] Create `data/raw/` and `data/processed/` directory structure (filesystem operation)
- [X] T004b [P] Implement `code/data/checksums.py` with functions `generate_checksum(file_path)` and `verify_checksum(file_path, expected_hash)` to generate `.sha256` files and verify data integrity (Constitution Principle III)
- [X] T005 [P] Implement `code/utils/state_manager.py` with function `update_artifact_hash(path)` that computes SHA-256 and appends to `state/artifact_hashes.yaml` (Constitution Principle V)
- [X] T006a [P] Create `code/utils/logger.py` implementing a structured logging utility with functions `get_logger(name)`, `log_info(msg)`, `log_warning(msg)`, `log_error(msg)`, and `log_critical(msg)` that writes to both console and `logs/pipeline.log` with timestamps. (FR-001, Edge Cases)
- [X] T006b [P] Configure log rotation and file size limits in `code/utils/logger.py` to prevent disk exhaustion.
- [X] T007a [P] Create `code/config/env.py` to manage environment variables (random seeds, paths) with a function `load_config()` that validates required keys and returns a `dict`. (Spec Assumptions)
- [X] T007b [P] Create `code/utils/novelty.py` (stub) and `code/utils/shap_utils.py` (stub) with placeholder functions to ensure importability.
- [X] T008a [P] Configure environment configuration management for random seeds in `code/config/env.py`. **Note**: The dataset URL is a fixed constant per spec assumptions (`https://huggingface.co/datasets/GFA-D2/pilot_flags`) and is NOT stored in this config file. (Spec Assumptions)
- [X] T008b [P] Define and save the list of the most abundant metallic elements to `data/config/elements.yaml` and `code/config/elements.py` (Al, Ca, Fe, Mg, Ti, Na, K, Zn, Si, Zr, Cu, Ni, Cr, Mn, V, Sn, Pb, Ag, Au, Pd, Pt, Mo, W, Nb, Ta, Hf, Y, La, Ce, Sc). **Verification**: Add a comment in the file noting that Si, Na, and K are included per spec assumption but may not form stable metallic glasses in all ternary systems. (FR-005)
- [X] T008c [P] Download or generate `data/known_alloys.csv` for novelty checks (FR-013). **Logic**: If external source is unavailable, create an empty file with a header row only (`composition,novelty_status`) and log a warning. **Requirement**: Ensure the file path exists before T036 runs. (Plan, Edge Cases)
- [X] T009a [P] Create `contracts/candidates_csv.schema.yaml` defining the schema for `output/candidates.csv` (columns: composition, predicted_log10_Rc, ci_lower, ci_upper, risk_score, final_score, novelty_status) (Plan, FR-006, FR-007)
- [X] T009b [P] Create `contracts/verification.schema.yaml` defining the schema for `output/verification_requests.json` (fields: composition, predicted_log10_Rc, confidence_interval, novelty_status, status) with `novelty_status` enum strictly ["novel", "known", "unverified_external"] (Plan, FR-008, FR-013)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Ingest raw composition data, parse elemental fractions, and compute physics-based descriptors and interaction features using Pymatgen.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying that the output CSV contains the original composition columns plus the computed descriptor columns with no null values for known elements, and that the row count matches the sum of source datasets.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test in `tests/contract/test_data_schema.py::test_schema_matches_contracts` validating against the *expected* schema defined in `contracts/data_schema.yaml` (derived from FR-001), ensuring the test can run before data download (US-1)
- [X] T011 [P] [US1] Integration test in `tests/integration/test_data_pipeline.py` for end-to-end data ingestion and feature engineering

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download.py` to fetch Dataset (Recent Experimental GFA) from HuggingFace (`https://huggingface.co/datasets/GFA-D2/pilot_flags`). **Requirements**: Use `huggingface_hub.hf_hub_download` (preferred) or `requests` with **explicit retry logic (3 attempts, 5s exponential backoff)**. **Output**: Save the raw file to `data/raw/gfa_dataset.csv`. **Schema Verification**: Immediately after download, verify the CSV contains `composition` and `log10_Rc` (or `Rc`) columns. **Failure Condition**: If columns are missing, raise an exception and halt execution. **Checksum**: Generate `data/raw/gfa_dataset.csv.sha` using `code/data/checksums.py` ONLY after schema verification passes. **Error Handling**: Explicitly handle authentication and permission errors and fail with a clear message if they persist. **CRITICAL**: Do NOT implement any fallback to synthetic data; if the download fails after retries or schema check fails, the script MUST raise an exception and halt execution. (FR-001, Edge Cases)
- [X] T013 [US1] Implement `code/data/ingest.py` to parse CSV, normalize elemental fractions to sum to 1.0 ± 0.01, and log warnings for unknown elements (US-1, FR-001)
- [ ] T014 [US1] Implement `code/data/features.py` to compute atomic radius, electronegativity, VEC_raw, and weighted mean VEC_avg using Pymatgen. **Output**: `data/processed/features.csv` matching the schema in `contracts/data_schema.yaml` (columns: composition, log10_Rc, atomic_radius_mean, electronegativity_mean, VEC_avg, size_mismatch, etc. as defined in contract). (FR-002) <!-- FAILED: unspecified -->
- [X] T015 [US1] Implement pairwise size mismatch descriptor calculation in `code/data/features.py` for every unique pair of elements within each composition row. **Logic**: Iterate through all unique element pairs in a row (e.g., for ternary A-B-C, calculate for A-B, A-C, B-C). Handle variable composition sizes (binary, ternary, etc.) by calculating pairs dynamically. **Verification**: Ensure the feature dimensionality matches the number of unique pairs in the composition (3 for ternary). (FR-002b)
- [ ] T016 [US1] Add validation logic to exclude rows with unknown elements and log specific warnings (US-1, Edge Cases)
- [ ] T017 [US1] Save processed feature-engineered dataset to `data/processed/features.csv` with `source_row_id` traceability (Constitution Principle IV)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting models, perform LOCO cross-validation, handle heteroscedasticity, and generate SHAP values.

**Independent Test**: Can be fully tested by running the training script and verifying that two distinct model artifacts are saved, cross-validation scores are printed, the selected model has an MAE lower than a baseline mean-predictor, and a SHAP feature importance report is generated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model artifact schema in `tests/contract/test_model_artifacts.py` <!-- FAILED: unspecified -->
- [X] T019 [P] [US2] Integration test for LOCO CV and model selection in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/models/train.py` to train RandomForestRegressor and GradientBoostingRegressor with hyperparameter grids ≤30; output: `best_model.pkl` and `best_model_weighted.pkl` (if applicable) and print LOCO-MAE scores (FR-003) <!-- FAILED: unspecified -->
- [ ] T021 [US2] Implement LOCO cross-validation logic in `code/models/train.py` based on primary metallic element families; **CRITICAL**: Fit a StandardScaler on the training features, save the fitted scaler as `data/processed/scaler.pkl`, and save the transformed `X_train.pkl` and `y_train.pkl` (FR-004)
- [ ] T022 [US2] Implement model selection logic to save `best_model.pkl` based on lowest LOCO-MAE (US-2, FR-003)
- [ ] T023 [US2] Implement `code/models/validate.py` to perform Breusch-Pagan test for heteroscedasticity; output: `state/heteroscedasticity_test.json` containing `p_value` and `heteroscedasticity_flag` (boolean) (FR-010)
- [ ] T024 [US2] Implement weighted loss retraining in `code/models/validate.py` **ONLY IF** `heteroscedasticity_flag` is true. **Logic**: Bin residuals by feature-space quantiles (ensure sufficient samples per bin), fit a local variance estimator, derive weights inversely proportional to the estimated local variance. Retrain the model with these weights. Save as `best_model_weighted.pkl`. **Fallback**: If binning is unstable, use a global log-variance model or Huber loss, **BUT** explicitly log this as a "deviation from strict FR-010 binning requirement" and flag the model accordingly. (FR-010)
- [ ] T025 [US2] Implement `code/utils/shap_utils.py` to generate global SHAP values for the best model (FR-011)
- [ ] T026 [US2] Save `shap_feature_importance.json` with global SHAP values (FR-012)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Novel Composition Screening and Ranking (Priority: P3)

**Goal**: Generate unique ternary combinations, predict GFA, check novelty, apply Domain of Applicability penalties, and rank candidates.

**Independent Test**: Can be fully tested by running the screening script and verifying that the output CSV contains up to 10 rows, sorted by predicted $log_{10}(R_c)$, with confidence intervals and novelty status fields.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for candidates CSV schema in `tests/contract/test_candidates_schema.py`
- [ ] T029 [P] [US3] Integration test for screening and ranking pipeline in `tests/integration/test_screening.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/models/predict.py` to generate all unique ternary combinations from the most abundant metallic elements defined in `data/config/elements.yaml` (FR-005)
- [ ] T031 [US3] Implement prediction logic using the best model (or weighted if applicable) for all ternary combinations (FR-005)
- [ ] T032a [US3] **Depends on: T021, T030, T031** Implement `code/models/predict.py::calculate_doa` to calculate the Domain of Applicability (DoA). **Logic**:
 1. **Load the PCA model fitted on training data** (from T021) and **load `X_train.pkl`**.
 2. Reduce candidate features to PCA components (retaining [deferred] variance).
 3. Calculate the **Convex Hull** of the training feature space in the reduced PCA space.
 4. **Calculate Mahalanobis distance** for each candidate using the covariance matrix of the training data and the mean of the training data in PCA space.
 5. **Threshold**: Flag as "high_extrapolation_risk" if the candidate is outside the Convex Hull OR if the Mahalanobis distance exceeds the 95th percentile of the chi-squared distribution (df = num_pca_components).
 **Artifacts**: Save `state/convex_hull_model.pkl`. **Verification**: Ensure `output/candidates.csv` contains the `high_extrapolation_risk` column. (FR-009, Plan Phase 3 Step 3)
- [ ] T033 [US3] Apply +1.0 penalty to $log_{10}(R_c)$ for candidates where `high_extrapolation_risk` is true before ranking (FR-009)
- [ ] T034 [US3] **Depends on: T030, T031, T017, T021** Implement filtering logic: **Step 1**: Calculate the 10th percentile of the `log10_Rc` distribution in the training data (from T017/T021). **Step 2**: If the 10th percentile can be calculated, retain candidates with `predicted_log10_Rc` < 10th percentile. **Fallback**: If the percentile cannot be calculated (e.g., insufficient data), **use the absolute cutoff of 4.0** as specified in FR-006. **Verification**: Ensure `output/candidates.csv` contains the filtered list. (FR-006)
- [ ] T035 [US3] **Depends on: T022, T030, T031, T021** Generate an ensemble of bootstrapped Random Forest models on the training data. **Requirements**: Load the **exact hyperparameters** (n_estimators, max_depth, etc.) from `best_model.pkl` (T022). **Load `X_train` and `y_train` from T021**. Train 10 models on **resampled subsets** (bootstrapping with replacement) of the training data using these fixed hyperparameters. Save each model as `state/bootstrapped_models/ensemble_{i}.pkl` (i=0..9). Predict on candidates; calculate confidence intervals (lower and upper percentiles) from the variance of these 10 predictions; output confidence intervals for each candidate. **Verification**: Ensure `output/candidates.csv` contains `ci_lower` and `ci_upper` columns. Verify hyperparameters match `best_model.pkl`. (FR-003, FR-007)
- [ ] T036 [US3] **Depends on: T030, T031** Implement novelty check in `code/utils/novelty.py` against `data/known_alloys.csv`. **Logic**: If the list exists, check and set `novelty_status` to `"novel"` or `"known"`. **Fallback**: If `data/known_alloys.csv` is missing or empty, set `novelty_status` to `"unverified_external"` and log a warning. **Do NOT fail the pipeline** if the list is missing. **Verification**: Ensure `output/verification_requests.json` contains `novelty_status: unverified_external` for all rows when the list is missing. (FR-013, Plan Phase 3 Step 5)
- [ ] T037 [US3] Rank candidates by ascending `final_score` (predicted + penalty) and select a representative subset of top-ranked items (FR-006)
- [ ] T038 [US3] Generate `output/candidates.csv` with top-ranked candidates, predictions, CIs, and risk scores (FR-006, FR-007)
- [ ] T039 [US3] Generate `output/verification_requests.json` containing a list of verification request objects. with fields: `composition`, `predicted_log10_Rc`, `confidence_interval`, `novelty_status` (strictly "novel", "known", or "unverified_external" per FR-008), `status` ("pending_verification"). **Validation**: Run schema validator against `contracts/verification.schema.yaml`. **Error Handling**: If validation fails, log the error, set a `validation_status` flag to "failed" in the output, and save the file. Do not abort the pipeline unless the file cannot be written. (FR-008, FR-013)
- [ ] T040 [US3] Handle edge case of zero candidates below threshold by outputting empty CSV with header (Edge Cases)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041a [P] Draft `docs/paper/01-introduction.md` (background, problem statement)
- [ ] T041b [P] Draft `docs/paper/02-methods.md` (data pipeline, model training, screening)
- [ ] T042 Code cleanup and refactoring across `code/` modules
- [ ] T043a [P] Refactor `code/models/predict.py` to use vectorized operations for the prediction loop to reduce runtime (Performance optimization)
- [ ] T043b [P] Refactor DoA calculation to process candidates in batches to reduce memory usage (Performance optimization)
- [ ] T043c [P] Profile the pipeline and optimize bottlenecks to ensure total runtime < 6 hours on CPU-only runner. **Deliverable**: Generate `output/profiling_report.json` with runtime metrics for each phase and memory usage peaks. (SC-004)
- [ ] T043d [P] **Depends on: T043c** Verify the runtime of the combinatorial generation step ([deferred] combinations) against the 6-hour constraint in `output/profiling_report.json`. If exceeded, flag for further optimization. (SC-004)
- [ ] T044 [P] Additional unit tests for feature engineering logic in `tests/unit/test_features.py`
- [ ] T045 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T046 Verify all artifacts in `state/artifact_hashes.yaml` are correctly updated

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model from US2 and data from US1

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
- **Phase 5 Parallelism**: T030 and T031 can run in parallel. T032a is sequential after T030/T031. T035 is sequential after T022 and T030/T031. T036 is sequential after T030/T031.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema validation in tests/contract/test_data_schema.py::test_schema_matches_contracts"
Task: "Integration test for data ingestion and feature engineering in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py"
Task: "Implement code/data/ingest.py"
Task: "Implement code/data/features.py"
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

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
