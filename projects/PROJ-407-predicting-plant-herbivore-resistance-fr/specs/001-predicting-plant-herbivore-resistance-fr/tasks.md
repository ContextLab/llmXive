# Tasks: Predicting Plant Herbivore Resistance from Publicly Available Metabolomic Data

**Input**: Design documents from `/specs/001-predicting-plant-herbivore-resistance-fr/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [X] T001 [P] Create project structure and generate tree output: Execute `mkdir -p code data/raw data/interim data/processed data/results tests/unit tests/integration tests/contract` in `projects/PROJ-407-predicting-herbivore-resistance-fr/` and generate `tree_output.txt` listing the directory structure.
- [X] T002 Initialize Python 3.11 project with dependencies in `requirements.txt`: Create file with exact content: `pandas==2.0.3`, `scikit-learn==1.3.0`, `requests==2.31.0`, `numpy==1.24.3`, `scipy==1.11.1`, `datasets==2.14.0`, `jsonschema==4.19.0`, `pytest==7.4.0`, `tenacity==8.2.3`.
- [X] T003 [P] Configure linting (flake8/black/isort) and jsonschema validation hooks in `.pre-commit-config.yaml`: Create file with hooks for `black`, `flake8`, `isort`, and `jsonschema` (using `check-jsonschema` or similar) to enforce schema validation on commit.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` defining exact keys: `RANDOM_SEED = 42`, `DATA_ROOT = 'data'`, `N_PERMUTATIONS = 1000`, `MAX_RUNTIME_HOURS = 6`, `MAX_MEMORY_GB = 7`.
- [X] T005 [P] Implement `code/versioning.py` to compute `sha256` hashes of `data/` and `code/` artifacts and update `state/projects/PROJ-407-predicting-plant-herbivore-resistance-fr.yaml` (specifically `artifact_hashes` map and `updated_at` timestamp).
- [X] T007 Create base configuration for `pytest` including `pytest-cov` and `jsonschema` validation hooks in `pytest.ini`
- [X] T008 [P] Implement robust retry logic with exponential backoff (1s, 2s, 4s) for network requests in `code/ingest.py` utilities using the `tenacity` library. Define function signature `retry_request(url, max_retries=3)` returning response or raising exception.
- [X] T009 [P] Create `contracts/dataset.schema.yaml` defining required columns: `sample_id`, `genotype_id`, `resistance`, `metabolite_*`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Resistance Score Extraction (Priority: P1) 🎯 MVP

**Goal**: Locate, download, and parse publicly available plant metabolomic datasets to extract paired observations of metabolite abundance and herbivore resistance scores.

**Independent Test**: The system can be tested by running the ingestion script against the primary HuggingFace source. The output must be a CSV file with at least 10 rows of complete data without manual intervention.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/ingest.py` to fetch data. **Primary**: Use `wget` or `curl` to download from NCBI GEO using a verified accession ID (e.g., GSE12345) as per FR-001. **Fallback**: If NCBI GEO fails after 3 retries, use `datasets.load_dataset("plant-metabolomics/herbivore-resistance-v1")` as a verified fallback. **Fail Loud**: If both fail, raise a `RuntimeError` with the message "Failed to fetch dataset from NCBI GEO and HuggingFace. Aborting." **Output**: Save raw bytes/CSV to `data/raw/raw_dataset.csv`. **Note**: Load all data into memory (no streaming required for ≤500 samples).
- [X] T011 [US1] Implement logic in `code/ingest.py` to parse metadata and extract `resistance` column; raise explicit error "No quantifiable resistance metric found" if missing or non-numeric
- [ ] T012 [US1] **Depends on**: T011. Implement categorical-to-ordinal conversion (Low=1, Medium=2, High=3) in `code/ingest.py`. **Canonical Keys**: Use exact case-sensitive keys: 'Low', 'Medium', 'High'. **MUST** log the exact mapping dictionary to `data/interim/ordinal_mapping.json` (e.g., `{"Low": 1, "Medium": 2, "High": 3}`) in JSON format. **Verification**: Ensure the converted data in `data/interim/harmonized.csv` reflects this conversion. **FR-008**: If `herbivore_density` is missing, add a row to `data/interim/ordinal_mapping.json` with key `{"herbivore_density_missing": true}`.
- [X] T013 [US1] Implement `herbivore_density` handling in `code/ingest.py`. **If present**: Normalize resistance score by herbivore density. **If missing**: Add a row to `data/interim/metadata.json` with exact key `{"herbivore_density_missing": true}` per FR-008.
- [ ] T014 [US1] Save raw downloaded data to `data/raw/` with checksum verification. **Output**: File `data/raw/raw_dataset.csv` and checksum file `data/raw/raw_dataset.csv.sha256`. **Depends on**: T010 (Data Fetch).
- [ ] T015 [US1] Save harmonized dataset (with imputation flag column) to `data/interim/harmonized.csv`. **Verification**: Ensure the `resistance` column contains only numeric values (1, 2, 3) if categorical conversion was applied.
- [X] T016 [P] [US1] Implement unit test `tests/unit/test_ingest.py` to verify schema validation and error handling for missing resistance metrics
- [ ] T017 [P] [US1] Implement integration test `tests/integration/test_data_ingestion.py` to run full download and verify output CSV structure. **Depends on**: T014 (Raw data saved). **Skip Logic**: Before execution, check for existence of `data/raw/raw_dataset.csv.sha256`. If missing, log "SKIP: No data artifact found" and exit with code 0 (success). **Note**: This test requires T014 to be complete and produce the artifact before execution.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling and Feature Importance (Priority: P2)

**Goal**: Train a CPU-tractable Random Forest model to predict resistance scores and extract a ranked list of the most predictive metabolites.

**Independent Test**: The system can be tested by training the model on a subset of the data, evaluating the R² score on a held-out test set, and verifying that the output includes a sorted list of metabolite names with their corresponding importance scores.

### Implementation for User Story 2

- [ ] T018 [US2] Implement `code/preprocess.py` to filter metabolites with variance < 0.001
- [ ] T019 [US2] Implement `code/preprocess.py` to apply k-Nearest Neighbors (k=5) imputation for missing values and set `imputation_flag`
- [ ] T020 [US2] Implement dimensionality reduction logic in `code/preprocess.py`: **Condition**: If features > samples, apply PCA to top variance components. **Output**: **ONLY** save resulting matrix to `data/processed/pca_reduced.csv` if the condition is met. If features <= samples, skip artifact creation and log "PCA skipped: features <= samples".
- [ ] T021 [US2] Implement genotype-stratified train/test split in `code/preprocess.py` ensuring no genotype leakage. **Logic**: Use `sklearn.model_selection.train_test_split` with `stratify=genotype_id` (if classification) or `stratify=resistance` (if regression) to ensure balanced representation. **Output**: Save split indices to `data/interim/split_indices.json` and log the train/test split ratio and sample counts to `data/interim/split_log.txt`.
- [ ] T022 [US2] Implement `code/model.py` to train Random Forest Regressor (n_estimators=100, max_depth=10) on training set. **Logic**: If `n_features > n_samples` (p>>n), automatically trigger PCA reduction (T020) before training. **Output**: Save model to `data/processed/model.pkl`.
- [ ] T023 [US2] Implement evaluation logic in `code/model.py` to calculate R², MSE, and accuracy (if classification) on test set. **Output**: Save metrics to `data/processed/model_metrics.json`.
- [ ] T024 [US2] Implement feature importance extraction in `code/model.py` to rank top metabolites. **Output**: Save feature importance table to `data/processed/feature_importance.csv` with columns: `metabolite_name`, `importance_score`, `unadjusted_p_value`, `correlation_coefficient`.
- [ ] T027a [P] [US2] Implement unit test `tests/unit/test_knn_imputation.py` to verify k-NN imputation logic
- [ ] T027b [P] [US2] Implement unit test `tests/unit/test_pca_reduction.py` to verify PCA reduction logic
- [ ] T028 [P] [US2] Implement unit test `tests/unit/test_model.py` to verify model training and metric calculation

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Multiplicity Correction (Priority: P3)

**Goal**: Perform permutation testing to validate model performance against random chance and apply Benjamini-Hochberg correction to correlation p-values.

**Independent Test**: The system can be tested by running the permutation test (1,000 iterations) and verifying that the p-value for the model's R² score is < 0.05, and that the final list of significant metabolites includes the adjusted p-values (q-values).

### Implementation for User Story 3

- [ ] T029a [US3] **Depends on**: T021 (Split), T022 (Model), T029b (Batch Correction). Implement exactly `config.N_PERMUTATIONS` permutation iterations in `code/validation.py` (shuffling resistance scores). **Stratification Logic**: Check for `study_id` or `batch` columns in metadata. If present, stratify by that field; otherwise, stratify by `genotype_id`. **Data Source**: If T029b produced `data/interim/batch_corrected_data.csv`, use it; otherwise, use `data/interim/harmonized.csv`. **Output**: Save null distribution to `data/interim/null_distribution.csv` (columns: `iteration`, `r2_score`), calculated p-value to `data/interim/permutation_p_value.json`, and execution log (containing iteration count) to `data/interim/permutation_run.log`.
- [ ] T029b [US3] **Depends on**: T015 (Harmonized Data). Implement batch covariate adjustment logic. **Condition**: If `study_id` or `batch` metadata exists: One-hot encode and add as covariates to model input (save to `data/interim/batch_corrected_data.csv`). **If metadata is MISSING**: Do nothing (pipeline proceeds with `harmonized.csv`). **Note**: SVA is explicitly NOT authorized per Constitution Principle VII; the Plan's SVA requirement is overridden by this constraint.
- [X] T029c [US3] **Depends on**: T029a. Enforce `n_permutations=1000` constraint. Read config, verify `data/interim/permutation_run.log` contains the configured number of iterations, and fail if mismatched.
- [X] T031 [US3] **Depends on**: T029a. Implement logic in `code/validation.py` to halt biomarker listing if global p-value ≥ 0.05 and report "Null Result". **Note**: BH correction (T033) must still be performed and logged even if global test fails.
- [ ] T032 [US3] **Depends on**: T021, T029a. Implement univariate correlation calculation (Pearson/Spearman) for each metabolite in `code/validation.py` on the **training set**. **Logic**: Use Pearson for continuous resistance scores and Spearman for ordinal/categorical scores. **Output**: Save correlation table to `data/interim/correlations.csv` (columns: `metabolite_name`, `correlation_coefficient`, `p_value`).
- [X] T033 [US3] **Depends on**: T032. Implement Benjamini-Hochberg correction in `code/validation.py` to generate q-values from unadjusted p-values.
- [X] T034 [US3] **Depends on**: T033. Filter and output significant metabolites (q < 0.10) to `data/processed/significant_biomarkers.csv`.
- [X] T036 [P] [US3] Implement unit test `tests/unit/test_validation.py` to verify permutation logic and BH correction. **Depends on**: T029a, T032.
- [ ] T047 [P] [US3] Implement integration test `tests/integration/test_statistical_validation.py` to verify end-to-end validation flow. **Logic**: Use a small synthetic dataset with known properties (e.g., correlation = 0.8) to test the full pipeline. **Pass/Fail**: Check for specific p-value thresholds (e.g., p < 0.05 for known signal) and correct artifact generation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Finalization (Priority: P3)

**Goal**: Compile results into a summary report, verify feasibility constraints, and finalize versioning.

### Implementation for Reporting

- [X] T037 [US1/US2/US3] Create `templates/report_template.md` defining the required fields: R², MSE, Null Result status, Biomarker list.
- [ ] T048 [US1/US2/US3] **Depends on**: T031, T034. Implement `code/report.py` to compile metrics, feature importance, and validation results into `results/summary_report.md`. **Template**: Use `templates/report_template.md`. **Fields**: R², MSE, Null Result status, Biomarker list.
- [ ] T049 [US1/US2/US3] **Depends on**: T034. Implement logic in `code/report.py` to explicitly state the "Null Result" if applicable, or list biomarkers with q-values if significant.
- [ ] T050 [US1/US2/US3] **Depends on**: T048. Implement feasibility check in `code/report.py`. **Logic**: Parse runtime/memory logs, compare against 6h/7GB limits. **Action**: Generate `results/feasibility_report.json` containing `runtime_hours`, `peak_memory_gb`, and `status` (PASS/FAIL). **Do NOT exit with code 1 on failure**; report status only.
- [X] T041 [P] Execute `code/versioning.py` to hash final artifacts and update project state file
- [ ] T042 [P] [US1/US2/US3] Run end-to-end integration test `pytest -q tests/integration/`. **Expectation**: Exit code 0 if all stages pass. **Depends on**: T048, T050.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T043 [P] Documentation updates in `README.md` and `docs/`
- [X] T044 Code cleanup and refactoring of `code/` modules
- [X] T045 Performance optimization for data loading (ensure standard load works for ≤500 samples)
- [X] T046 [P] Additional unit tests for edge cases (e.g., p >> n scenarios) in `tests/unit/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Reporting (Phase 6)**: Depends on all user stories being complete
- **Polish (Final Phase)**: Depends on Reporting completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires model results from US2

### Within Each User Story

- Models/Preprocessing before Training/Validation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for ingestion schema in tests/contract/test_ingest.py"
Task: "Integration test for data ingestion in tests/integration/test_data_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Create ingestion script in code/ingest.py"
Task: "Create harmonization logic in code/ingest.py"
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
 - Developer A: User Story 1 (Ingestion)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Validation)
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