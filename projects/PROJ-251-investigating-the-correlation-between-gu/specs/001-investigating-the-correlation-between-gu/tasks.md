# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Immune Response to Influenza Vaccination

**Input**: Design documents from `/specs/001-investigating-the-correlation-between-gu/`
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

- [ ] T001 Create project structure per implementation plan (code/, data/raw, data/processed, data/results, specs/)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, scikit-learn, pyyaml, requests, biom-format, qiime2, dada2)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create configuration module `code/utils/config.py` with paths, seeds, and thresholds
- [ ] T005 [P] Implement schema validators `code/utils/validators.py` for dataset, correlation, and model metrics
- [ ] T006 [P] Setup logging infrastructure in `code/utils/logging_config.py` to capture exclusion counts and errors
- [ ] T007 Create base data loading helpers in `code/utils/data_loader.py`
- [ ] T008 Setup environment configuration management (`.env` handling for API keys if needed)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Validation (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-processed 16S rRNA OTU tables and serology metadata, filtering for complete records.

**Independent Test**: The system can be tested by running the ingestion script against a known valid subset and verifying the output CSV contains exactly N rows (N ≥ 50) with no nulls in required columns.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for data schema validation in `code/tests/test_ingest.py`
- [ ] T010 [P] [US1] Integration test for data filtering logic in `code/tests/test_ingest.py`

### Implementation for User Story 1

- [ ] T011 [US1] Implement Strategy A: Fetch pre-processed 16S/serology CSV/Parquet from specific HuggingFace dataset or NCBI SRA pre-processed archive. If fetch fails, trigger T011b (Strategy B).
- [ ] T011b [US1] Implement Strategy B: Download raw FASTQ files from NCBI SRA (using `prefetch`/`fasterq-dump` from SRA Toolkit) for the target study if Strategy A fails.
- [ ] T011c [US1] Implement Strategy B: Run 16S processing pipeline (QIIME2 or DADA2 via Docker or lightweight Python wrapper) on raw FASTQ to generate OTU table.
- [ ] T011d [US1] Implement Strategy B: Merge generated OTU table with serology metadata using `subject_id` to create the initial dataset.
- [ ] T012 [US1] Implement filtering logic in `code/01_ingest.py` to exclude subjects missing baseline or post-vaccination titers
- [ ] T013 [US1] Implement data type validation in `code/01_ingest.py` (ensure numeric abundances and titers)
- [ ] T014 [US1] Add logic to handle subjects with titers below limit of detection (impute to half detection limit or exclude)
- [ ] T015a [US1] Implement logic in `code/01_ingest.py` to calculate N (count of subjects with complete data)
- [ ] T015b [US1] Implement logic in `code/01_ingest.py` to log N to console and file
- [ ] T015c [US1] Implement conditional check in `code/01_ingest.py`: If N < 50, prepare error condition
- [ ] T015d [US1] Implement exception raising in `code/01_ingest.py`: Raise `ValueError("ERR_NO_DATA: Insufficient Sample Size (N < 50)")` if check fails
- [ ] T016 [US1] Write filtered dataset to `data/processed/filtered_data.csv` and log exclusion counts
- [ ] T017 [US1] Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlation Analysis and Multiple Testing Correction (Priority: P2)

**Goal**: Calculate diversity metrics, apply CLR transformation, and perform Spearman correlation with BH correction.

**Independent Test**: The system can be tested by running analysis on a synthetic dataset with known correlations and verifying correct identification of significant taxa and adjusted p-values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for CLR transformation logic in `code/tests/test_correlation.py`
- [ ] T019 [P] [US2] Unit test for Benjamini-Hochberg correction in `code/tests/test_correlation.py`

### Implementation for User Story 2

- [ ] T019a [US2] Implement zero-variance taxa exclusion in `code/02_preprocess.py`: Filter out taxa with 0 variance across all subjects BEFORE transformation to avoid division-by-zero.
- [ ] T020 [US2] Implement Centered Log-Ratio (CLR) transformation in `code/02_preprocess.py` (handle zeros with pseudocount)
- [ ] T021 [US2] Implement Shannon diversity index calculation in `code/02_preprocess.py`
- [ ] T022 [US2] Implement log-transformation of antibody titers in `code/02_preprocess.py`
- [ ] T023 [US2] Implement Spearman rank correlation test in `code/03_correlation.py` (exclude zero-variance taxa)
- [ ] T024 [US2] Implement Benjamini-Hochberg FDR correction in `code/03_correlation.py`
- [ ] T025 [US2] Write correlation results (coeff, raw p, adj p) to `data/results/correlation_results.csv`
- [ ] T025a [US2] Implement logic in `code/03_correlation.py` to calculate the count of taxa with adjusted p < 0.05
- [ ] T025c [US2] Implement logic in `code/03_correlation.py` to explicitly calculate the count of significant taxa and compare it against the expected range defined in the spec, logging the result
- [ ] T026 [US2] Write diversity metrics to `data/results/diversity_metrics.csv`
- [ ] T027 [US2] Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/correlation_results.schema.yaml`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Nested Cross-Validation (Priority: P3)

**Goal**: Train Random Forest classifier with nested CV, ensuring feature selection occurs inside the training loop.

**Independent Test**: The system can be tested by running training on the ingested dataset and verifying that feature selection is logged within each fold and accuracy is reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for nested CV structure in `code/tests/test_modeling.py`
- [ ] T029 [P] [US3] Integration test for model performance metrics in `code/tests/test_modeling.py`

### Implementation for User Story 3

- [ ] T030a [US3] Implement seroconversion logic (≥4-fold rise in titer) in `code/04_modeling.py`
- [ ] T030b [US3] Implement absolute titer logic (e.g., HAI ≥ 40) in `code/04_modeling.py`
- [ ] T030c [US3] Implement threshold parameterization for responder definition in `code/04_modeling.py`
- [ ] T030d [US3] Apply responder definition to dataset in `code/04_modeling.py`
- [ ] T031 [US3] Implement nested 5-fold cross-validation loop in `code/04_modeling.py`
- [ ] T032 [US3] Implement feature selection (top taxa) strictly inside the inner training loop of each outer fold
- [ ] T033 [US3] Implement Random Forest classifier training in `code/04_modeling.py` (CPU-only, default precision)
- [ ] T034a [US3] Implement permutation baseline testing: Generate null distribution of accuracy scores by shuffling labels in `code/04_modeling.py`
- [ ] T034b [US3] Implement logic in `code/04_modeling.py` to compare Random Forest accuracy against the permutation baseline null distribution
- [ ] T034c [US3] Implement explicit statistical comparison in `code/04_modeling.py` between Random Forest accuracy and the permutation baseline null distribution (p < 0.05)
- [ ] T034d [US3] Implement halt/flag logic in `code/04_modeling.py` if the comparison condition (p < 0.05) is not met, satisfying SC-003
- [ ] T035 [US3] Calculate and log confusion matrix, precision, recall, F1-score for high/low responders
- [ ] T036 [US3] Write model metrics to `data/results/model_metrics.json`
- [ ] T037 [US3] Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/model_metrics.schema.yaml`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5.5: Sensitivity Analysis (Priority: P3 - Assumptions)

**Goal**: Perform sensitivity analysis on responder thresholds and generate final reports.

- [ ] T050 [US3] Implement sensitivity analysis in `code/05_sensitivity.py`: Sweep responder threshold at ±10% of defined cutoff and re-run model training for each threshold
- [ ] T051 [US3] Implement logic in `code/05_sensitivity.py` to aggregate results across thresholds and calculate stability metrics
- [ ] T052 [US3] Generate stability report (accuracy vs threshold) and save to `data/results/sensitivity_report.json`

**Checkpoint**: Sensitivity analysis complete, robustness verified.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 Code cleanup and refactoring
- [ ] T040 [P] Additional unit tests for edge cases (zero variance, missing data)
- [ ] T041 Run quickstart.md validation
- [ ] T042 Verify runtime < 6h AND memory usage < 7GB on GitHub Actions free-tier runner using `memory_profiler` or similar tool

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
- **User Story 2 (P2)**: Depends on User Story 1 (requires `data/processed/filtered_data.csv`)
- **User Story 3 (P3)**: Depends on User Story 2 (requires `data/results/correlation_results.csv` for feature selection)
  - *Note*: While US3 depends on US2 results for feature selection, the *code* for US3 can be written in parallel, but execution must be sequential.
- **Sensitivity Analysis (Phase 5.5)**: Depends on User Story 3 (requires model logic to sweep thresholds)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (N/A for data pipeline)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (code-wise), but execution remains sequential.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in code/tests/test_ingest.py"
Task: "Integration test for data filtering logic in code/tests/test_ingest.py"

# Launch all models for User Story 1 together:
Task: "Implement Strategy A: Fetch pre-processed data in code/01_ingest.py"
Task: "Implement Strategy B: Download raw FASTQ in code/01_ingest.py"
Task: "Implement Strategy B: Run 16S pipeline in code/01_ingest.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Verify N ≥ 50)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Sensitivity Analysis → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data Ingestion)
   - Developer B: User Story 2 (Correlation Logic)
   - Developer C: User Story 3 (Modeling Logic)
3. Stories complete and integrate independently (execution order enforced by data flow)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only GitHub Actions free-tier runners (≤7GB RAM, ≤6h). No GPU, no 8-bit quantization.
- **Data Strategy**: T011 (Strategy A) is preferred; T011b/T011c/T011d (Strategy B) is mandatory fallback if no pre-processed data exists.