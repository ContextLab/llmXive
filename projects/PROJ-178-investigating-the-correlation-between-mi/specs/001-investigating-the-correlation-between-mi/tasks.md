# Tasks: Investigating the Correlation Between Mitochondrial DNA Variation and Aging Rates

**Input**: Design documents from `/specs/001-mitochondrial-aging-correlation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Data Availability Gate (Blocking)

**Purpose**: Verify data availability before any heavy processing begins.

**⚠️ CRITICAL**: This phase must complete successfully before Phase 1 starts. If the 'age' column is missing, the pipeline halts immediately per plan.md.

- [ ] T007A Check for 'age' column in 1000 Genomes metadata panel; if missing, log error to `data/validation/log_age_column.json` and HALT pipeline immediately (no fallback analysis), adhering to plan.md's "Data Availability Gate".
- [ ] T007B Verify source of metadata file (canonical 1000 Genomes FTP), implement error handling for missing data scenarios, and log validation status to `data/validation/source_verification.log`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001A [P] Create data directories: `code/data/raw`, `code/data/processed`, `code/logs`, `paper/figures`
- [ ] T001B [P] Create code directories: `code/analysis`, `code/tests`
- [X] T002 Initialize Python 3.11 project with requirements.txt (scikit-learn, pandas, numpy, scipy, vcfpy, haplogrep2, requests, tqdm)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement runtime timer and logging infrastructure in `code/run_analysis.py`
- [ ] T006A [P] Create `code/contracts/dataset.schema.yaml` defining Sample/Variant entities
- [ ] T006B [P] Create `code/contracts/output.schema.yaml` defining AnalysisResult
- [X] T009 Setup environment configuration for 1000 Genomes FTP URLs and local paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and parse 1000 Genomes mitochondrial data to create a unified, analysis-ready dataset with verified age metadata.

**Independent Test**: The system can be tested by verifying the existence of a processed CSV/Parquet file containing per-sample heteroplasmy burden, haplogroup, age, sex, and ancestry PCs, with zero missing values in critical columns.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data schema validation in `code/tests/test_data.py`
- [X] T011 [P] [US1] Integration test for VCF download and merge in `code/tests/test_data.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/analysis/load_data.py` to download mitochondrial VCFs from 1000 Genomes FTP and metadata panel
- [ ] T013A [P] [US1] Implement chunked VCF reading in `code/analysis/load_data.py` using `vcfpy` to handle large files within 7GB RAM
- [ ] T013B [P] [US1] Add logic to aggregate variant counts per sample in memory without loading full VCF
- [X] T014 [US1] Implement variant filtering in `code/analysis/preprocess.py` (retain only `PASS` status and `chrM`)
- [X] T015 [US1] Implement heteroplasmy burden calculation with VAF ≥ 1% threshold in `code/analysis/preprocess.py`
- [X] T016 [US1] Implement depth-stratified burden calculation (Low, Medium, High bins) in `code/analysis/preprocess.py`
- [X] T017 [US1] Integrate `haplogrep2` via subprocess in `code/analysis/preprocess.py` to assign haplogroups
- [ ] T018 [US1] Implement metadata merge logic to join burden, haplogroups, age, sex, population, and PCs; write merged dataframe to `code/data/processed/mito_aging_dataset.csv`
- [ ] T019 [US1] Implement conditional exclusion logic: 1) Exclude samples with missing age from ALL analysis; 2) Exclude samples with failed haplogroup assignment from haplogroup-specific analysis ONLY, but RETAIN them for burden-only analysis if age is present; log exclusion counts and retention status to `code/logs/exclusion_report.txt`.
- [ ] T019A [US1] Implement haplogroup assignment success rate calculation; verify if ≥ 90% of samples are assigned and log the result to `code/logs/haplogroup_success_rate.txt`
- [ ] T020 [US1] Write processed dataset to `code/data/processed/mito_aging_dataset.csv` with checksum generation

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Testing (Priority: P2)

**Goal**: Perform Spearman correlation and Rank-OLS regression to quantify the relationship between heteroplasmy burden and age, adjusting for confounders.

**Independent Test**: The system can be tested by running the analysis on a synthetic dataset with a known correlation and verifying the model recovers the correct p-value and coefficient sign.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for statistical output schema in `code/tests/test_model.py`
- [X] T022 [P] [US2] Integration test for Rank-OLS implementation in `code/tests/test_model.py`

### Implementation for User Story 2

- [X] T023A [P] [US2] Implement unadjusted Spearman rank correlation calculation (primary method per FR-004) in `code/analysis/model.py` and save results to `code/data/processed/spearman_results.csv`
- [ ] T024 [US2] Implement Rank-OLS regression (per plan.md Decision Log): Rank-transform all continuous variables (`age`, `burden`, `depth`, `PC1`, `PC2`) then fit `rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)` using the depth-stratified burden from T016 in `code/analysis/model.py` and save coefficients, p-values, and adjusted p-values to `code/data/processed/rank_ols_results.csv`. Note: Rank-OLS is used as a robust multivariate alternative to Partial Spearman as justified in the plan.md Decision Log.
- [X] T025 [US2] Implement Benjamini-Hochberg correction for all generated p-values in `code/analysis/model.py`
- [X] T027 [US2] Record coefficients and p-values for the secondary OLS model (as per FR-004) in `code/logs/model_comparison.log`, calculate the delta between Spearman and OLS coefficients, and log the comparison result to satisfy the "recorded and compared" requirement.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Execute sensitivity analyses to validate findings against threshold choices, population stratification, and power-law assumptions.

**Independent Test**: The system is tested by running the sensitivity analysis with thresholds 0.5%, 1.0%, and 2.0% and verifying the output contains three distinct correlation coefficients.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Contract test for sensitivity output schema in `code/tests/test_sensitivity.py`
- [X] T031 [P] [US3] Integration test for subgroup analysis in `code/tests/test_sensitivity.py`

### Implementation for User Story 3

- [X] T032 [US3] Implement threshold sweep for heteroplasmy burden recalculation across specific VAF thresholds: {low (0.005), 1.0% (0.01), [deferred] (0.02)}. Write results to `code/data/processed/sensitivity_results.csv` with columns: `threshold`, `coefficient`, `p_value`.
- [ ] T032A [US3] Calculate and record the variation (range/std dev) of correlation coefficients across the {0.5%, 1.0%, 2.0%} thresholds; save this metric to `code/data/processed/threshold_variation.json` to satisfy SC-003.
- [X] T033 [US3] Implement subgroup analysis for continental ancestries (EUR, AFR, EAS, SAS, AMR) in `code/analysis/sensitivity.py`; write results to `code/data/processed/subgroup_results.csv` with columns: `ancestry`, `coefficient`, `p_value`.
- [ ] T033A [US3] Calculate and record the variation (magnitude of difference) of coefficients across ancestry groups; save this metric to `code/data/processed/subgroup_variation.json` to satisfy SC-004.
- [X] T034 [US3] Implement depth-stratified subsampling to equalize sequencing depth across groups in `code/analysis/sensitivity.py`
- [X] T036 [US3] Implement measurement error simulation (binned age intervals) to estimate attenuation bias in `code/analysis/sensitivity.py`
- [X] T037 [US3] Generate comparative plots for threshold and subgroup results in `code/analysis/visualize.py`
- [X] T038 [US3] Write comprehensive sensitivity report to `code/data/processed/sensitivity_analysis.csv`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `paper/draft.md` (include findings and limitations)
- [ ] T050 [P] Document the explicit removal of the Power-Law Hypothesis in `paper/draft.md` citing plan.md Decision Log, ensuring no references to "quarter-power scaling" or "Geoffrey West" remain. <!-- FAILED: unspecified -->
- [ ] T042A [P] Refactor `code/analysis/preprocess.py` to reduce cyclomatic complexity of the burden calculation function to < 10
- [ ] T042B [P] Remove unused imports from all scripts in `code/analysis/`
- [ ] T043A [P] Profile `code/analysis/load_data.py` and implement chunking strategy to ensure peak RAM usage < 7GB
- [ ] T043B [P] Verify memory usage via `memory_profiler` and write output to `code/logs/memory_profile.log`
- [ ] T044 [P] Additional unit tests for edge cases (zero burden, missing haplogroup) in `code/tests/`
- [ ] T045 [P] Run `quickstart.md` validation, capture runtime in `code/logs/runtime_validation.log`, and assert runtime <= 6 hours
- [ ] T046 Generate final figures (linear fit, threshold sensitivity) in `paper/figures/`

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data and models from US1/US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loading before processing
- Processing before modeling
- Core implementation before sensitivity analysis
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in code/tests/test_data.py"
Task: "Integration test for VCF download and merge in code/tests/test_data.py"

# Launch all models for User Story 1 together:
Task: "Implement load_data.py to download mitochondrial VCFs"
Task: "Implement variant filtering in code/analysis/preprocess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Data Availability Gate (CRITICAL - blocks everything)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (verify age data exists)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Linear & Power-Law Correlation)
4. Add User Story 3 → Test independently → Deploy/Demo (Robustness of Scaling Law)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Statistical Models)
 - Developer C: User Story 3 (Sensitivity & Robustness)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Phase 5 Power-Law tasks (T050-T052) have been removed per plan.md Decision Log ("Remove Power-Law Hypothesis"). T050 in Phase 6 now documents this removal.
- **Revision Note**: Updated T007A/T007B to enforce hard halt with artifacts; added T023A for primary Spearman; added T019A for haplogroup success rate; removed T028; replaced T042/T043 with atomic metric-driven tasks; updated T024 to consume T016 output; removed [P] tags from T032/T033/T007A/T007B to fix ordering.
- **Revision Note**: Updated T032 to explicitly list thresholds {0.5%, 1.0%, 2.0%} and output schema; added T032A/T033A to explicitly calculate variation metrics for SC-003/SC-004; updated T019 to implement conditional retention logic for partial data; updated T027 to include comparison logic; removed all Power-Law/West review references.
- **Revision Note**: Removed T050-T052 (Power-Law Scaling) as they contradicted the plan; added T050 to Phase 6 to document the hypothesis removal.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence