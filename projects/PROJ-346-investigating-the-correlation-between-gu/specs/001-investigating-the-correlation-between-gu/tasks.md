# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [X] T001a [P] Create project code structure: `projects/PROJ-346-investigating-the-correlation-between-gu/code/`, `projects/PROJ-346-investigating-the-correlation-between-gu/tests/`
- [X] T001b [P] Create project data structure: `projects/PROJ-346-investigating-the-correlation-between-gu/data/raw/`, `data/processed/`, `data/qc/`
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, scikit-learn, statsmodels, seaborn, matplotlib, requests, pyyaml) and configure linting (flake8/black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Setup environment variable management for dataset URLs (AGP, NHANES, UK Biobank)
- [X] T004 [P] Implement `code/utils.py` with shared constants (read thresholds, abundance filters, age strata) and logging helpers
- [X] T005 [P] Setup data schema validation using Pydantic or simple dict checks for `MicrobialTaxa` and `CognitiveScore` entities; output schema definitions to `contracts/dataset.schema.yaml` before T011 runs
- [ ] T006 [P] Create base data loading functions in `code/utils.py` with retry logic (retry up to 3 times with exponential backoff) for API failures
- [ ] T007 [P] Configure `pytest` configuration and basic test runner script

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and normalize publicly available gut microbiome and cognitive flexibility data; detect data linkage gaps.

**Independent Test**: Execute ingestion scripts and verify output files contain expected sample counts, filtered taxa, and z-scored cognitive scores with proper logging.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/01_ingest.py` to fetch microbiome data from ANY valid source defined in spec FR-001 (AGP, Qiita Study 10313, NHANES, or UK Biobank) and save raw parquet; apply FR-001 filters (<10k reads, <0.1% abundance). **MUST use Qiita Study 10313 or AGP as primary source.**
- [ ] T012 [US1] Implement `code/01_ingest.py` logic to fetch cognitive data from ANY valid source defined in spec FR-002 (NHANES Cognitive Battery or UK Biobank Field 20002) and save raw parquet. **MUST use UK Biobank Field 20002 or NHANES as primary source.** <!-- FAILED: unspecified -->
- [ ] T013 [US1] Implement `code/02_preprocess.py` to load cognitive data, handle missing values via MICE (per FR-002), compute z-scores, and save processed parquet
- [ ] T014 [US1] Implement `code/02_preprocess.py` logic to attempt individual-level merge of microbiome and cognitive data; if failed, invoke `code/07_gap_report.py` (T017)
- [~] T015 [US1] Implement `code/02_preprocess.py` logic to add robust outlier filtering (z-score > 3) with logging to `data/qc/filtering_log.json`
- [~] T016 [US1] Add validation to ensure output parquet files match `contracts/dataset.schema.yaml`
- [~] T017 [US1] Implement `code/07_gap_report.py` to execute the **Data Gap Report** path (FR-008 as redefined in plan.md): **DO NOT perform statistical synthesis**; instead, generate a structured "Data Gap Report" artifact documenting the inability to link individual-level data, logging the specific reason, and marking SC-001/SC-004 as "Not Measurable". This is the terminal step of Phase 3.

### Tests for User Story 1 (OPTIONAL) ⚠️

> **NOTE**: Write these tests AFTER implementation to verify specific logic.
> Note: These tasks depend on the existence of implementation code (T011-T017) to run, even if they fail.

- [~] T008a [US1] Unit test for data filtering logic in `tests/unit/test_filtering.py` (specifically `test_remove_low_read_samples` and `test_remove_rare_taxa`)
- [~] T009a [US1] Unit test for MICE imputation in `tests/unit/test_imputation.py` (specifically `test_mice_missing_values` and `test_zscore_normalization`)
- [~] T010a [US1] Integration test for data merge logic in `tests/integration/test_merge.py` (specifically `test_linkage_failure_detection` and `test_gap_report_trigger`)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (or correctly report data gap)

---

## Phase 4: User Story 2 - Correlation and Association Analysis (Priority: P2)

**Goal**: Compute Spearman correlations, apply FDR correction, and fit regularized regression models (only if data linked).

**Independent Test**: Run analysis on preprocessed data; verify correlation matrix, significant taxa list (q < 0.05), and regression coefficients.

**DEPENDS ON**: T014 (Merge Success) AND T017 (No Data Gap). If T017 triggered, skip this phase entirely.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [~] T018 [US2] Unit test for Spearman correlation calculation in `tests/unit/test_correlation.py`
- [~] T019 [US2] Unit test for Benjamini-Hochberg FDR correction in `tests/unit/test_fdr.py`
- [~] T020 [US2] Unit test for LASSO/Elastic Net regression in `tests/unit/test_regression.py`

### Implementation for User Story 2

- [~] T021 [US2] Implement `code/03_correlation.py` to compute Spearman rank correlations between taxa and cognitive scores (FR-003)
- [~] T022 [US2] Implement `code/03_correlation.py` logic to apply Benjamini-Hochberg FDR correction and flag significant taxa (q < 0.05) (FR-004)
- [~] T023 [US2] Implement `code/04_regression.py` to fit LASSO/Elastic Net models with CLR-transformed taxa, age, sex, BMI (FR-005). **MUST check for `data/processed/merged_dataset.parquet`; if missing, skip execution and log "N/A - Data Gap" to prevent runtime errors.**
- [~] T025 [US2] Ensure all outputs include explicit "associational" framing labels (FR-005, SC-005)
- [~] T026 [US2] Save correlation matrix and regression results to `data/processed/` with metadata

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (or correctly report N/A due to data gap)

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Stratify results by age, test normalization robustness, and generate visualizations.

**Independent Test**: Execute sensitivity scripts; verify stratified tables and plot files (heatmap, forest plot) are generated.

**DEPENDS ON**: T014 (Merge Success) AND T017 (No Data Gap). If T017 triggered, skip this phase entirely.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [~] T027 [US3] Unit test for age stratification logic in `tests/unit/test_stratification.py`
- [~] T028 [US3] Unit test for normalization comparison (DESeq2 vs rarefaction) in `tests/unit/test_normalization.py`

### Implementation for User Story 3

- [~] T029 [US3] Implement `code/05_sensitivity.py` to stratify correlations by age groups (<40, ≥40-<60, ≥60) (FR-006); Check for `data/processed/merged_dataset.parquet`; skip if missing
- [~] T030 [US3] Implement `code/05_sensitivity.py` to compare significant taxa counts across normalization methods (DESeq2 vs rarefaction); Check for `data/processed/merged_dataset.parquet`; skip if missing
- [~] T031 [US3] Implement `code/06_visualize.py` to generate heatmap of taxa-cognition correlation matrix (FR-007); Check for `data/processed/merged_dataset.parquet`; skip if missing
- [~] T032 [US3] Implement `code/06_visualize.py` to generate forest plot of regression coefficients with confidence intervals (FR-007); Check for `data/processed/merged_dataset.parquet`; skip if missing
- [~] T033 [US3] Ensure all visualizations include clear labels for age groups and confidence intervals

**Checkpoint**: All user stories should now be independently functional (or correctly report N/A due to data gap)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T034 [P] Documentation updates in `README.md` explaining the FR-008 fallback behavior (Data Gap Report)
- [~] T035 Code cleanup and refactoring for CPU efficiency (memory chunking if needed) <!-- SKIPPED: non-mapping output -->
- [~] T036 [P] Performance optimization: Implement memory chunking in `code/03_correlation.py` to ensure pipeline runs within 6 hours on N=10,000 samples (SC-003) for both full analysis and data gap paths
- [~] T037 [P] Additional unit tests for edge cases (zero significant taxa, rate-limiting) in `tests/unit/`
- [~] T038 Security hardening: Sanitize all external URLs and file paths
- [~] T039 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **DEPENDS on T014 (Merge Success) AND T017 (No Gap)**; skips if data gap
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **DEPENDS on T014 (Merge Success) AND T017 (No Gap)**; skips if data gap

### Within Each User Story

- Tests (if included) MUST be written AFTER implementation to verify specific logic (T008-T010 depend on T011-T017)
- Ingestion/Preprocessing (T011-T017) before Correlation (T021-T026)
- Correlation before Regression (T023)
- Regression before Visualization (T031-T032)
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately
- US2 and US3 can only start in parallel with US1 **IF** the Data Gap (T017) is NOT triggered. If T017 triggers, US2/US3 are blocked.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (conditional on data availability)

---

## Parallel Example: User Story 1

```bash
# Launch all implementation for User Story 1 together:
Task: "Fetch Qiita Study 10313 or AGP data in code/01_ingest.py"
Task: "Fetch UK Biobank Field 20002 or NHANES data in code/01_ingest.py"

# Launch all tests for User Story 1 together (after implementation):
Task: "Unit test for data filtering logic in tests/unit/test_filtering.py"
Task: "Unit test for MICE imputation in tests/unit/test_imputation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Ingestion + Gap Detection)
4. **STOP and VALIDATE**: Test Data Ingestion; verify if Data Gap Report (T017) is generated correctly.
5. Deploy/demo if ready (even if data gap is the result, the pipeline is working).

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (if data linked)
4. Add User Story 3 → Test independently → Deploy/Demo (if data linked)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Ingestion)
 - Developer B: User Story 2 (Correlation/Regression) - *Note: Can develop logic, but execution depends on US1 outcome (T017)*
 - Developer C: User Story 3 (Sensitivity/Vis) - *Note: Can develop logic, but execution depends on US1 outcome (T017)*
3. Stories complete and integrate independently. If data gap, US2/US3 correctly report N/A.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- **CRITICAL**: If FR-008 (Data Gap) is triggered (T017), US2 and US3 tasks must gracefully skip and report "Not Measurable" per SC-001/SC-004.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence.
- **CPU Constraint**: All tasks must be implementable on a multi-core CPU with sufficient memory. No GPU, no 8-bit models. Use `scikit-learn` and `scipy` only.