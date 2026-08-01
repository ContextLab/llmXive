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

**Purpose**: Project initialization, basic structure, and schema definition

- [X] T001a [P] Create project code structure: `projects/PROJ-346-investigating-the-correlation-between-gu/code/`, `projects/PROJ-346-investigating-the-correlation-between-gu/tests/`
- [X] T001b [P] Create project data structure: `projects/PROJ-346-investigating-the-correlation-between-gu/data/raw/`, `data/processed/`, `data/qc/`
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, scikit-learn, statsmodels, seaborn, matplotlib, requests, pyyaml) and configure linting (flake8/black)
- [ ] T005 [P] Setup data schema validation: Create and output `contracts/dataset.schema.yaml` (YAML format, Pydantic model dump) containing fields: `taxon_name`, `relative_abundance`, `sample_id` for MicrobialTaxa and `task_type`, `z_score`, `participant_id` for CognitiveScore. **Must complete before T011 and T016.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Setup environment variable management for dataset URLs (AGP, NHANES, UK Biobank)
- [X] T004 [P] Implement `code/utils.py` with shared constants (read thresholds, abundance filters, age strata) and logging helpers
- [X] T006 [P] Create base data loading functions in `code/utils.py` with retry logic (retry up to 3 times with exponential backoff) for API failures
- [X] T007 [P] Configure `pytest`: Create `pytest.ini`, `tests/conftest.py`, and `tests/run_tests.sh` to enable test execution.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and normalize publicly available gut microbiome and cognitive flexibility data; detect data linkage gaps; execute FR-008 fallback (Data Gap Report) if linkage fails.

**Independent Test**: Execute ingestion scripts and verify output files contain expected sample counts, filtered taxa, z-scored cognitive scores, and verify proper logging. If linkage fails, verify the Data Gap Report is generated.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/_ingest.py` to fetch microbiome data from **Qiita Study 10313** (URL: ` or direct download link provided in study metadata) and save raw parquet; apply FR-001 filters (<10k reads, <0.1% abundance).
- [X] T012 [US1] Implement code logic to fetch cognitive data from **UK Biobank Field 20002** (Composite Cognitive Score) or **NHANES Cognitive Battery** (specific variables: `CXT` or equivalent) and save raw parquet.
- [X] T013 [US1] Implement `code/02_preprocess.py` to load cognitive data, handle missing values via MICE (per FR-002), compute z-scores, and save processed parquet.
- [X] T014 [US1] Implement `code/02_preprocess.py` logic to attempt individual-level merge of microbiome and cognitive data; **if merge fails (no common participant IDs), immediately trigger T017a (Data Gap Report) and skip remaining US2/US3 steps.**
- [X] T015 [US1] Implement `code/02_preprocess.py` logic to add robust outlier filtering (z-score > 3 on merged dataset) with logging to `data/qc/filtering_log.json`. **Output JSON schema: `{ "total_samples": int, "removed_outliers": int, "threshold": float }`**.
- [X] T016 [US1] Add validation using `pandera` to ensure output parquet files match `contracts/dataset.schema.yaml`. **Fail hard on schema mismatch.**
- [ ] T017a [US1] Implement `code/07_gap_report.py` to execute the **FR-008 Data Gap Fallback**: **DO NOT** compute pooled effect sizes or heterogeneity. Instead, if T014 detects a data gap, generate a structured report documenting the inability to link individual-level data between cohorts. **Output**: `data/processed/data_gap_report.json`.
- [ ] T017b [US1] Generate `reports/data_gap_report.md` based on T017a output. This document MUST:
 1. State that individual-level data linkage failed.
 2. Explain that FR-008 fallback (Data Gap Report) was executed.
 3. Mark SC-001/SC-004 as "Not Measurable" due to data gap.
 4. **Avoid causal claims**; frame all findings as "associational" (or note that no association could be measured).

### Tests for User Story 1 (OPTIONAL) ⚠️

> **NOTE**: Write these tests AFTER implementation to verify specific logic.
> Note: These tasks depend on the existence of implementation code (T011-T017b) to run, even if they fail.

- [X] T008a [US1] Unit test for data filtering logic in `tests/unit/test_filtering.py` (specifically `test_remove_low_read_samples` and `test_remove_rare_taxa`)
- [X] T009a [US1] Unit test for MICE imputation in `tests/unit/test_imputation.py` (specifically `test_mice_missing_values` and `test_zscore_normalization`)
- [X] T010a [US1] Integration test for data merge logic in `tests/integration/test_merge.py` (specifically `test_linkage_failure_detection` and `test_gap_report_trigger`)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (or correctly report data gap)

---

## Phase 4: User Story 2 - Correlation and Association Analysis (Priority: P2)

**Goal**: Compute Spearman correlations, apply FDR correction, and fit regularized regression models (only if data linked). **Strictly maintain 'associational only' framing.**

**Independent Test**: Run analysis on preprocessed data; verify correlation matrix, significant taxa list (q < 0.05), regression coefficients, and verify outputs.

**DEPENDS ON**: T014 (Merge Success). If T014 fails, skip this phase.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T018 [US2] Unit test for Spearman correlation calculation in `tests/unit/test_correlation.py`
- [X] T019 [US2] Unit test for Benjamini-Hochberg FDR correction in `tests/unit/test_fdr.py`
- [X] T020 [US2] Unit test for LASSO/Elastic Net regression in `tests/unit/test_regression.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/03_correlation.py` to compute Spearman rank correlations between taxa and cognitive scores (FR-003). **Explicitly label outputs as 'associational'**.
- [X] T022 [US2] Implement `code/03_correlation.py` logic to apply Benjamini-Hochberg FDR correction and flag significant taxa (q < 0.05) (FR-004).
- [X] T023 [US2] Implement `code/04_regression.py` to fit LASSO/Elastic Net models with CLR-transformed taxa, age, sex, BMI (FR-005). **MUST check for `data/processed/merged_dataset.parquet`; if missing, skip execution and log "N/A - Data Gap" to prevent runtime errors.** **Explicitly label outputs as 'associational'**.
- [X] T025 [US2] Ensure all outputs include explicit "associational" framing labels (FR-005, SC-005).
- [X] T026 [US2] Save correlation matrix and regression results to `data/processed/` with metadata.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (or correctly report N/A due to data gap)

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Stratify results by age, test normalization robustness, and generate visualizations. **Strictly maintain 'associational only' framing.**

**Independent Test**: Execute sensitivity scripts; verify stratified tables and plot files (heatmap, forest plot) are generated.

**DEPENDS ON**: T014 (Merge Success). If T014 fails, skip this phase.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T027 [US3] Unit test for age stratification logic in `tests/unit/test_stratification.py`
- [X] T028 [US3] Unit test for normalization comparison (DESeq2 vs rarefaction) in `tests/unit/test_normalization.py`

### Implementation for User Story 3

- [X] T029 [US3] Implement `code/05_sensitivity.py` to stratify correlations by age groups (<40, ≥40-<60, ≥60) (FR-006); Check for `data/processed/merged_dataset.parquet`; skip if missing.
- [X] T030 [US3] Implement `code/05_sensitivity.py` to compare significant taxa counts across normalization methods (DESeq2 vs rarefaction); Check for `data/processed/merged_dataset.parquet`; skip if missing.
- [X] T031 [US3] Implement `code/06_visualize.py` to generate heatmap of taxa-cognition correlation matrix (FR-007); Check for `data/processed/merged_dataset.parquet`; skip if missing.
- [X] T032 [US3] Implement `code/06_visualize.py` to generate forest plot of regression coefficients with confidence intervals (FR-007); Check for `data/processed/merged_dataset.parquet`; skip if missing.
- [X] T033 [US3] Ensure all visualizations include clear labels for age groups and confidence intervals.

**Checkpoint**: All user stories should now be independently functional (or correctly report N/A due to data gap)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates in `README.md` explaining the FR-008 fallback behavior (Data Gap Report) and the strict 'associational only' framing.
- [X] T035 [P] Code cleanup and refactoring for CPU efficiency (memory chunking if needed)
- [X] T036 [P] Performance optimization: Implement memory chunking in `code/03_correlation.py` to ensure pipeline runs within 6 hours on N=10,000 samples (SC-003) for both full analysis and data gap paths. **Note**: If N=10,000 is not feasible, document the specific N-value used and the sampling strategy (e.g., `itertools.islice` first N rows) in `code/utils.py`.
- [X] T037 [P] Additional unit tests for edge cases (zero significant taxa, rate-limiting) in `tests/unit/`
- [X] T038 [P] Security hardening: Sanitize all external URLs and file paths
- [X] T039 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility and verify that all outputs are explicitly labeled 'associational only' as per SC-005.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **DEPENDS on T014 (Merge Success)**; skips if data gap.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **DEPENDS on T014 (Merge Success)**; skips if data gap.

### Within Each User Story

- Tests (if included) MUST be written AFTER implementation to verify specific logic (T008-T010 depend on T011-T017b)
- Ingestion/Preprocessing (T011-T017b) before Correlation (T021-T026)
- Correlation before Regression (T023)
- Regression before Visualization (T031-T032)
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately
- US2 and US3 can only start in parallel with US1 **IF** the Data Gap (T017a/b) is NOT triggered. If T017a/b triggers, US2/US3 are blocked.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (conditional on data availability)

---

## Parallel Example: User Story 1

```bash
# Launch all implementation for User Story 1 together:
Task: "Fetch Qiita Study 10313 data in code/01_ingest.py"
Task: "Fetch UK Biobank Field 20002 data in code/01_ingest.py"

# Launch all tests for User Story 1 together (after implementation):
Task: "Unit test for data filtering logic in tests/unit/test_filtering.py"
Task: "Unit test for MICE imputation in tests/unit/test_imputation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (including T005 schema definition)
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Ingestion + Data Gap Report)
4. **STOP and VALIDATE**: Test Data Ingestion; verify if Data Gap Report (T017b) is generated correctly.
5. Deploy/demo if ready (even if data gap is the result, the pipeline is working).

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (if data linked; otherwise report N/A)
4. Add User Story 3 → Test independently → Deploy/Demo (if data linked; otherwise report N/A)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Ingestion + Data Gap Report)
 - Developer B: User Story 2 (Correlation/Regression) - *Note: Can develop logic, but execution depends on US1 outcome*
 - Developer C: User Story 3 (Sensitivity/Vis) - *Note: Can develop logic, but execution depends on US1 outcome*
3. Stories complete and integrate independently. If data gap, US2/US3 correctly report N/A.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- **CRITICAL**: If FR-008 (Data Gap Report) is triggered (T017a/b), US2 and US3 tasks must gracefully skip and report N/A.
- **Strict Constraint**: All analysis must be labeled 'associational only'. No causal inference or mechanistic claims (e.g., 'cellular alphabet', 'synaptic plasticity') are permitted in the *results* of the correlation study.
- **Data Sources**: Only AGP, Qiita, UK Biobank, and NHANES are allowed. No fallback to HMP/MetaHIT or synthetic data.
- **CPU Constraint**: All tasks must be implementable on a multi-core CPU with sufficient memory. No GPU, no 8-bit models. Use `scikit-learn`, `scipy`, `statsmodels` only.
- **Sampling Strategy**: If N=10,000 is not feasible, explicitly define the sampling strategy (e.g., `itertools.islice` first N rows) in `code/utils.py` and document the N-value in the final report.