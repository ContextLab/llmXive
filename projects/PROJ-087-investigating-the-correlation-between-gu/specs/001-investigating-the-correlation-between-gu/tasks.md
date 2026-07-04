# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

## Phase 0: Data Ingestion & Feasibility Check (FR-001, FR-009, SC-002)

**Purpose**: Validate data availability, define mapping, and download raw data. **CRITICAL**: No processing or diversity calculation can occur until Phase 0 and Phase 0.5 are complete.

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `results/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, scikit-bio, scipy, seaborn, matplotlib, requests, numpy, pyyaml, pingouin)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 Setup `code/config.py` for path configuration, seed management, and constant definitions
- [ ] T005 [P] Implement 'Variable Existence Check' in `code/ingestion.py` (Plan Phase 0). Verify `sleep_efficiency` OR `sleep_quality` (proxy) and `antibiotic_use_last_3mo` exist in metadata. **HALT** with "Data Unavailable" error if missing. Log "Scope Narrowed: Using Self-Reported Sleep Quality" if only proxy exists. **Dependency**: None.
- [X] T007a [P] Define schema for `data/data_mapping_table.yaml` in `code/ingestion.py` (Plan Phase 0). **Dependency**: T005.
- [~] T007b [P] Implement generation logic for `data/data_mapping_table.yaml` in `code/ingestion.py` (Plan Phase 0). Document sample ID alignment. **Dependency**: T007a.
- [~] T006 [P] Implement data download with retry/backoff logic in `code/ingestion.py` (FR-001). **Source**: American Gut Project (URL from `code/config.py`). **Format**: CSV/TSV. **Output**: `data/raw/otu_counts.csv` and `data/raw/metadata.csv`. **HALT** with error log if dataset unavailable after retries. **Dependency**: T005.

**Checkpoint**: Phase 0 Complete. Data is available, validated, and mapped.

---

## Phase 0.5: Power & Sample Size Check (FR-008, SC-004)

**Purpose**: Verify statistical power before proceeding to diversity calculation. **CRITICAL GATE**.

- [~] T018 [P] Implement power analysis and sample size check in `code/ingestion.py` (Plan Phase 0.5). Calculate Minimum Detectable Effect Size (MDES) and verify statistical power ≥0.8 for r=0.3. **Implement explicit HALT logic**: If N < 30 OR MDES > 0.3, stop pipeline execution and log "Insufficient Power" error. **Dependency**: T006 (Download) and T016 (Filter - see Phase 2). **Note**: This task must run after initial filtering but before Diversity Calculation (T019).

**Checkpoint**: Power sufficient. Proceed to Phase 1 (Diversity).

---

## Phase 1: Foundational (Shared Infrastructure)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T008 Setup `data/raw/` and `data/processed/` directory structure with checksum validation hooks
- [~] T009 Setup environment configuration management for CI (GitHub Actions)
- [~] T010 [P] Implement `code/utils.py` with helper functions for logging, error handling, and retry logic

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Ingestion and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and merge raw 16S rRNA OTU count tables with sleep metadata, excluding antibiotic users, to produce a clean analysis-ready dataset.

**Independent Test**: Run `code/ingestion.py` and verify `data/processed/analysis_data.csv` exists, contains ≥30 samples, has no null alpha-diversity/sleep metrics, and zero samples with `antibiotic_use_last_3mo == True`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T013 [P] [US1] Unit test for antibiotic filtering logic in `tests/test_ingestion.py`
- [~] T014 [P] [US1] Unit test for proxy variable fallback logic in `tests/test_ingestion.py`
- [~] T015 [P] [US1] Integration test for full ingestion pipeline (download → filter → merge) in `tests/test_ingestion.py`

### Implementation for User Story 1

- [ ] T016 [P] [US1] Implement filtering logic to remove `antibiotic_use_last_3mo == True` and missing sleep data in `code/ingestion.py` (FR-001). **Dependency**: T006 (Download).
- [ ] T017 [P] [US1] Implement proxy variable fallback (sleep quality score) if `sleep_efficiency` is missing in `code/ingestion.py` (FR-009). **Dependency**: T005 (Variable Check).
- [ ] T011 [P] [US1] Ingest confounder variables (age, BMI, diet, medication) from metadata in `code/ingestion.py` (FR-008). **Dependency**: T006 (Download).
- [ ] T012 [P] [US1] Merge confounder variables into the analysis DataFrame in `code/ingestion.py` (FR-008). **Dependency**: T011, T016.
- [ ] T019 [P] [US1] Compute alpha-diversity indices (Shannon, Simpson) using `scikit-bio` in `code/diversity.py` (FR-002). **Dependency**: T016 (Filter). Exclude samples with zero OTU counts.
- [ ] T020 [P] [US1] Merge diversity metrics with sleep metrics and confounders into `data/processed/analysis_data.csv` in `code/ingestion.py` (FR-003). **Dependency**: T019, T012.
- [ ] T021 [P] [US1] Re-run Power Analysis (T018) on final merged dataset to confirm N ≥ 30 before proceeding. **Dependency**: T020. **HALT** if N < 30.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Compute Spearman correlations (diversity vs. sleep, taxon vs. sleep), apply Benjamini-Hochberg correction, and adjust for confounders.

**Independent Test**: Run `code/correlation.py` and `code/confounder_adjustment.py` on `analysis_data.csv` and verify `results/correlation_results.csv` and `results/adjusted_correlation_results.csv` contain correct `r`, `p`, and `p_adjusted` values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Unit test for Benjamini-Hochberg correction logic in `tests/test_correlation.py`
- [ ] T023 [P] [US2] Unit test for CLR transformation in `tests/test_correlation.py`
- [ ] T024 [P] [US2] Integration test for partial correlation with `pingouin` in `tests/test_confounder_adjustment.py`

### Implementation for User Story 2

- [ ] T025 [P] [US2] Implement Spearman correlation between diversity indices and sleep metrics in `code/correlation.py` (FR-004). **Dependency**: T020 (Analysis Data).
- [ ] T026 [P] [US2] Implement Benjamini-Hochberg correction for alpha-diversity p-values in `code/correlation.py` (FR-004). **Dependency**: T025.
- [ ] T027 [P] [US2] Implement CLR transformation for OTU count tables in `code/correlation.py` (FR-007). **Dependency**: T020.
- [ ] T025_new [P] [US2] Validate CLR transformation (check for NaN/Inf) in `code/correlation.py`. **HALT** if invalid values found. **Dependency**: T027.
- [ ] T028 [P] [US2] Implement taxon-level Spearman correlations (OTU vs. sleep) in `code/correlation.py` (FR-007). **Dependency**: T025_new.
- [ ] T029 [P] [US2] Implement Benjamini-Hochberg correction for taxon-level p-values in `code/correlation.py` (FR-007). **Dependency**: T028.
- [ ] T030 [P] [US2] Implement permutation-based partial correlation (adjusting for age, BMI, diet, medication) using `pingouin` in `code/confounder_adjustment.py` (FR-008). **Dependency**: T020 (Analysis Data with confounders).
- [ ] T031 [P] [US2] Implement 'FAIL-STOP' logic for confounder adjustment in `code/confounder_adjustment.py` (Plan Phase 4). **HALT** with "Confounder Adjustment Failed" error if `pingouin` is unavailable, permutation test fails, or N < 20 for stratification. **No custom fallback allowed**. **Dependency**: T030.
- [ ] T032 [P] [US2] Save `results/correlation_results.csv` and `results/adjusted_correlation_results.csv` in `code/correlation.py` and `code/confounder_adjustment.py`. **Dependency**: T026, T029, T031.
- [ ] T033 [P] [US2] Implement sensitivity analysis script in `code/sensitivity.py` (SC-004). Sweep p-value cutoffs across standard significance thresholds on correlation results. Save `results/sensitivity_analysis.csv`. **Dependency**: T032.
- [ ] T034 [P] [US2] Implement variance detection and 'Inconclusive' flagging logic in `code/sensitivity.py` (Plan Phase 5). Flag study as "Inconclusive" if results show high variance (e.g., sign flips across cutoffs). **Dependency**: T033.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate scatter plots with regression lines and boxplots comparing diversity across sleep quartiles.

**Independent Test**: Run `code/visualization.py` and verify `results/scatter_shannon_sleep.png` and `results/boxplot_diversity_sleep_quartile.png` exist, are >0 bytes, and have valid PNG headers.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T035 [P] [US3] Unit test for plot generation logic in `tests/test_visualization.py`
- [ ] T036 [P] [US3] Integration test for file existence and header validation in `tests/test_visualization.py`

### Implementation for User Story 3

- [ ] T037 [P] [US3] Implement scatter plot generation (diversity vs. sleep) with regression lines in `code/visualization.py` (FR-005). **Dependency**: T032 (Correlation Results).
- [ ] T038 [P] [US3] Implement sleep quartile binning logic in `code/visualization.py`. **Dependency**: T020 (Analysis Data).
- [ ] T039 [P] [US3] Implement boxplot generation (diversity by sleep quartile) in `code/visualization.py` (FR-005). **Dependency**: T038, T020.
- [ ] T040 [P] [US3] Save all generated plots to `results/` directory with metric-based filenames in `code/visualization.py`. **Dependency**: T037, T039.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T041 [P] Generate final summary report including power analysis, sensitivity results, and adjusted findings
- [ ] T042 [P] Code cleanup and refactoring across `code/`
- [ ] T043 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T044 [P] Run full pipeline end-to-end on CI to verify < 6h runtime and < 7GB RAM usage
- [ ] T045 [P] Verify all requirements (FR-001 to FR-009) are met by generated artifacts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data Ingestion & Feasibility)**: No dependencies - can start immediately
- **Phase 0.5 (Power Check)**: Depends on Phase 0 (Download/Filter) - **GATE** for Phase 1
- **Phase 1 (Foundational)**: Depends on Phase 0 - BLOCKS user story implementation
- **User Stories (Phase 2+)**: All depend on Phase 0.5 and Phase 1 completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 0.5 and Phase 1 - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 (needs `analysis_data.csv`)
- **User Story 3 (P3)**: Depends on User Story 2 (needs `correlation_results.csv`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Helpers before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Phase 0 tasks marked [P] can run in parallel
- All Phase 1 tasks marked [P] can run in parallel
- Once Phase 0.5 and Phase 1 complete, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for antibiotic filtering logic in tests/test_ingestion.py"
Task: "Unit test for proxy variable fallback logic in tests/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement filtering logic to remove antibiotic users in code/ingestion.py"
Task: "Implement proxy variable fallback in code/ingestion.py"
Task: "Ingest confounder variables in code/ingestion.py"
Task: "Merge confounder variables in code/ingestion.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Data Ingestion & Feasibility
2. Complete Phase 0.5: Power Check (GATE)
3. Complete Phase 1: Foundational
4. Complete Phase 2: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + 0.5 + 1 → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + 0.5 + 1 together
2. Once Phase 0.5 and 1 are done:
 - Developer A: User Story 1
 - Developer B: User Story 2 (after US1 data is ready)
 - Developer C: User Story 3 (after US2 results are ready)
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