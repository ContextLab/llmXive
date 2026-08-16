# Tasks: Predicting Plant Disease Susceptibility from Publicly Available Genomic and Environmental Data

**Input**: Design documents from `/specs/001-plant-disease-susceptibility/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are REQUIRED - they are explicitly defined in the spec's acceptance scenarios.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
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

- [ ] T001a [P] Create directory structure: `src/`, `tests/`, `data/raw/`, `data/processed/`, `models/`, `templates/`
- [ ] T001b [P] Initialize core config files: `requirements.txt`, `.gitignore`, `pyproject.toml`

- [ ] T002a [P] Initialize Python 3.11 project with `requirements.txt` (pysam, scikit-learn, pandas, numpy, requests, h5py, matplotlib, statsmodels). **Note: minimap2 and bcftools are system binaries and handled in T002b.**
- [ ] T002b [P] Setup system dependencies: Install `minimap2` and `bcftools` via `apt-get` in `Dockerfile` or CI config (e.g., `ubuntu-latest` runner setup). **Must run before T011-T013.**
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup configuration management in `src/utils/config.py` (paths, seeds=42, species lists)
- [ ] T005 [P] Implement logging infrastructure in `src/utils/logger.py` (structured logs, error tracking)
- [ ] T006 Create base data models/entities in `src/models/` (Sample, Model, Feature)
- [ ] T007 Setup schema validation contracts (`data/contracts/feature_matrix.schema.yaml`, `data/contracts/model_output.schema.yaml`, `data/contracts/linkage_method.schema.yaml`, `data/contracts/variance_decomposition.schema.yaml`)
- [ ] T008 Implement retry logic with exponential backoff in `src/utils/retry.py` (for NCBI/ERA5 rate limits)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Integration and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw genomic data (NCBI SRA) and environmental metadata (ERA5/NOAA), align reads, call variants, merge, and impute missing values into a single feature matrix.

**Independent Test**: Run ingestion on a small, fixed subset of samples. Verify `feature_matrix.csv` exists, has correct columns (SNP freq, temp, humidity), zero missing values, and passes schema validation.

### Tests for User Story 1 ⚠️

- [ ] T009 [P] [US1] Contract test for `feature_matrix` schema in `tests/contract/test_schema_validation.py`
- [ ] T010 [P] [US1] Integration test for ingestion pipeline on 10-sample subset in `tests/integration/test_ingestion_pipeline.py`
- [ ] T015b [P] [US1] Contract test for `linkage_method.yaml` schema in `tests/contract/test_linkage_method.py`

### Implementation for User Story 1

- [ ] T011 [US1] Implement `src/ingestion/download_sra.py`: Fetch SRA reads for wheat, rice, maize, tomato, soybean using E-utilities/wget. Handle rate limits (**max 3 retries** with exponential backoff). **FAIL LOUDLY** if download fails (no synthetic fallback). **Ensure atomic writes and file locking for `data/raw/` to prevent race conditions.**
- [ ] T012 [US1] Implement `src/ingestion/download_env.py`: Fetch ERA5-Land data via Python script wrapping `curl` (subprocess) using coordinates/date. **Explicitly reuse retry logic from `src/utils/retry.py` (max 3 retries, exponential backoff)** for the ERA5 fetch. Fallback to NOAA if ERA5 fails. **Log fallback action** with level WARNING and message "Falling back to NOAA API for location X on date Y". **FAIL LOUDLY** if both fail. **Ensure atomic writes and file locking for `data/raw/` to prevent race conditions.**
- [ ] T013 [US1] Implement `src/ingestion/align_and_call.py`: Align SRA reads to reference genomes using minimap2. Call SNPs with bcftools. Output variant frequency vectors.
  - **Reference Genomes (Exact Accession IDs)**:
    - Wheat: RefSeq GCA_000003205.5
    - Rice: Ensembl GCA_001433935.2
    - Maize: RefSeq GCA_000005005.4
    - Tomato: Sol Genomics Network SL4.0 (GCA_000188115.5)
    - Soybean: Phytozome Wm82.a2.v1 (GCA_000004195.3)
- [ ] T015 [US1] Implement `src/ingestion/validate_labels.py`: Verify 'disease susceptibility' labels come from independent phenotypic sources (FR-010). **Input**: `data/processed/sample_metadata.csv` (output of T011/T012). **Validation Logic**: Check `phenotype_source` field in metadata against a whitelist of independent sources (e.g., field-trial-db, pathology-archive). Log linkage method. **Generate `data/processed/linkage_method.yaml` documenting the method and source.** Exclude ambiguous samples.
- [ ] T014 [US1] Implement `src/ingestion/merge_features.py`: Merge genomic variant vectors with environmental data. **Input**: `data/processed/sample_metadata.csv` (for coordinates) to calculate distances. **Apply k-NN imputation (sklearn.impute.KNNImputer, n_neighbors=5) per Constitution Principle VI (Override of FR-004). See Plan: Constitution Check Table VI.** Exclude samples with no environmental neighbors within 50km (log action). **Note: This task implements the Constitution VI override of FR-004; see T037 for spec update.**
- [ ] T016 [US1] Generate `data/processed/feature_matrix.csv` and `data/processed/label_validation.log`

**Checkpoint**: User Story 1 fully functional. `feature_matrix.csv` ready for modeling.

---

## Phase 4: User Story 2 - Model Training and Performance Evaluation (Priority: P2)

**Goal**: Train Random Forest and SVM models on the integrated dataset with stratified split, hyperparameter tuning, and generate performance metrics (AUC-ROC, PR curves, feature importance).

**Independent Test**: Run training on a fixed dataset. Verify `model_performance.json` (AUC > 0.5) and `feature_importance.csv` (top predictors) exist.

### Tests for User Story 2 ⚠️

- [ ] T017 [P] [US2] Contract test for `model_performance.json` schema in `tests/contract/test_model_output.py`
- [ ] T018 [P] [US2] Integration test for training pipeline on 100-row subset in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `src/modeling/preprocess.py`: **Always** perform LD pruning (r² > 0.8). **If collinearity remains or features > samples, apply PCA-based dimensionality reduction.** **Do not skip PCA solely based on feature count; check for collinearity regardless of p>>n ratio.** Split data into training, validation, and test sets stratified by disease status. Output `reduced_feature_matrix.csv`.
- [ ] T020 [US2] Implement `src/modeling/train_models.py`: Train Random Forest and SVM. **Input: `reduced_feature_matrix.csv` (output of T019)**. Grid search (≤50 combos). Save models to `models/`.
- [ ] T021 [US2] Implement `src/modeling/evaluate.py`: Calculate AUC-ROC (with 95% CI), Precision-Recall curves. Generate `pr_curve.png`. Save `model_performance.json`.
- [ ] T022 [US2] Implement `src/modeling/feature_importance.py`: Rank top predictors, distinguishing genomic vs. environmental. Save `feature_importance.csv`.

**Checkpoint**: User Stories 1 & 2 complete. Models trained and evaluated.

---

## Phase 5: User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform permutation tests (1000 permutations, seed=42) to validate significance and sensitivity analysis on thresholds.

**Independent Test**: Run permutation test on trained model. Verify p-value < 0.05 is reported or "Not Statistically Significant" is flagged. Verify sensitivity analysis reports FPR/FNR variation.

### Tests for User Story 3 ⚠️

- [ ] T023 [P] [US3] Contract test for `validation_report.json` schema in `tests/contract/test_validation.py`
- [ ] T024 [P] [US3] Integration test for permutation test and sensitivity analysis in `tests/integration/test_statistical_validation.py`
- [ ] T034 [P] [US3] Contract test for `variance_decomposition.json` schema in `tests/contract/test_variance_decomposition.py`: Assert presence of `total_variance_explained` and `group_percentages` fields.

### Implementation for User Story 3

- [ ] T025 [US3] Implement `src/modeling/validation.py`: Run permutation test (**1000 permutations, seed=42**). Calculate p-value. Flag if p ≥ 0.05. **Output**: Save p-value and sensitivity results to `data/processed/validation_report.json` and `sensitivity_analysis.json`.
- [ ] T026 [US3] Implement `src/modeling/sensitivity_analysis.py`: Sweep thresholds around the decision boundary. Report FPR/FNR variation.
- [ ] T027 [US3] Implement `src/modeling/variance_decomposition.py`: Calculate variance explained by genomic vs. environmental groups (SC-003). **Method: Variance Partitioning via RDA (Redundancy Analysis).** **Explicitly map RDA output to 'relative contribution of genomic vs. environmental predictors' as required by SC-003.** **Output JSON with keys: `total_variance_explained`, `group_percentages`**. Save `variance_decomposition.json`.
- [ ] T028 [US3] Generate `validation_report.json` and `sensitivity_analysis.json`.

**Checkpoint**: All user stories complete. Statistical validation done.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final reporting

- [ ] T029 [P] Generate `final_report.md` using `templates/final_report.md`. **Required Sections**: AUC-ROC (from `model_performance.json`), p-value (from `validation_report.json`), Variance Decomposition (from `variance_decomposition.json`), Linkage Method (from `linkage_method.yaml`). **Read values directly from these source files.**
- [ ] T030a [P] Run `ruff check --fix` and `black .` on all source files.
- [ ] T030b [P] Remove all debug prints and temporary variables; ensure clean logging.
- [ ] T031 [P] Run `pytest` suite to ensure all tests pass.
- [ ] T032 [P] Validate `quickstart.md` instructions work end-to-end.
- [ ] T033 [P] Document any assumptions or data gaps in `research.md`.
- [ ] T035 [P] [US3] Integration test for `final_report.md` in `tests/integration/test_final_report.py`: **Assert that the statistics (AUC, p-values, variance %) in the report match the source JSON/YAML files exactly.**
- [ ] T036 [P] [US3] Contract test for `variance_decomposition.json` schema in `tests/contract/test_variance_decomposition.py`: Assert presence of `total_variance_explained` and `group_percentages` fields and verify they contain numeric percentages.
- [ ] T037 [P] Update `spec.md` (FR-004, User Story 1 Acceptance Scenario 2, and Edge Cases) to reflect the Constitution Principle VI override: Change "missForest" to "k-NN imputation" to align with the single source of truth implemented in T014. **Ensure spec text matches the plan and tasks exactly.**

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Critical**: Must complete before US2/US3 as it produces the data.
- **User Story 2 (P2)**: Depends on US1 output (`feature_matrix.csv`) and T019 output (`reduced_feature_matrix.csv`).
- **User Story 3 (P3)**: Depends on US2 output (trained models).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data download (T011, T012) before alignment (T013)
- Alignment (T013) before label validation (T015)
- Label validation (T015) before merging (T014)
- Merging (T014) before modeling (US2)
- T015 generates `linkage_method.yaml` before T029 consumes it.
- T019 generates `reduced_feature_matrix.csv` before T020 consumes it.
- T027 generates `variance_decomposition.json` before T029 consumes it.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 and US3 can theoretically start in parallel if data is mocked for dev, but for production, US1 must finish first.
- Within US1: T011 (SRA) and T012 (Env) can run in parallel if network allows, but T013 depends on both.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Pipeline)
4. **STOP and VALIDATE**: Test ingestion on 10 samples. Verify `feature_matrix.csv` integrity.
5. If data is missing or invalid, halt at Feasibility Gate (Phase 0.5) and reframe as "Pipeline Validation".

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
   - Developer A: User Story 1 (Data Pipeline - Critical Path)
   - Developer B: Prepare US2/US3 test scaffolds (T009-T024, T015b, T034, T036)
3. Once US1 data is ready:
   - Developer A: US2 (Modeling)
   - Developer B: US3 (Validation)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- **Critical Constraint**: NO synthetic data fallbacks. If real data fetch fails, the task MUST fail loudly (T011, T012).
- **Critical Constraint**: Imputation must use k-NN (Constitution VI), not missForest (FR-004 override). See Plan: Constitution Check Table VI. **T037 updates spec to reflect this.**
- **Critical Constraint**: Permutation test seed must be 42 (FR-007).
- **Critical Constraint**: Stratified split with a majority allocation for training, with smaller portions for validation and testing. (FR-005).
- **Critical Constraint**: T013 must use specific accession IDs for all 5 species.
- **Critical Constraint**: T027 must use RDA for variance decomposition and output specific keys.
- **Critical Constraint**: T029 must read from source artifacts, not hand-type.
- **Critical Constraint**: T002b must install system binaries before T011-T013 run.
- **Critical Constraint**: T015 must run before T014 to ensure only validated samples are merged.
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence