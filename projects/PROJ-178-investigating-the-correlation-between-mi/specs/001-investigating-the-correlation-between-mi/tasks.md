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

**⚠️ CRITICAL**: This phase must complete successfully before Phase 1 starts. If the 'age' column is missing, the pipeline halts immediately.

- [ ] T007A [P] Check for 'age' column in 1000 Genomes metadata panel; if missing, log error and HALT pipeline immediately (no fallback analysis).
- [ ] T007B [P] Verify source of metadata file (canonical 1000 Genomes FTP), implement error handling for missing data scenarios, and log validation status.

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
- [ ] T011 [P] [US1] Integration test for VCF download and merge in `code/tests/test_data.py` <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/analysis/load_data.py` to download mitochondrial VCFs from 1000 Genomes FTP and metadata panel
- [ ] T013A [P] [US1] Implement chunked VCF reading in `code/analysis/load_data.py` using `vcfpy` to handle large files within 7GB RAM
- [ ] T013B [P] [US1] Add logic to aggregate variant counts per sample in memory without loading full VCF
- [X] T014 [US1] Implement variant filtering in `code/analysis/preprocess.py` (retain only `PASS` status and `chrM`)
- [ ] T015 [US1] Implement heteroplasmy burden calculation with VAF ≥ 1% threshold in `code/analysis/preprocess.py`
- [ ] T016 [US1] Implement depth-stratified burden calculation (Low, Medium, High bins) in `code/analysis/preprocess.py`
- [ ] T017 [US1] Integrate `haplogrep2` via subprocess in `code/analysis/preprocess.py` to assign haplogroups
- [ ] T018 [US1] Implement metadata merge logic to join burden, haplogroups, age, sex, population, and PCs
- [~] T019 [US1] Implement exclusion logic for samples with missing age or failed haplogroup assignment
- [~] T020 [US1] Write processed dataset to `code/data/processed/mito_aging_dataset.csv` with checksum generation

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Testing (Priority: P2)

**Goal**: Perform Spearman correlation and Rank-OLS regression to quantify the relationship between heteroplasmy burden and age, adjusting for confounders.

**Independent Test**: The system can be tested by running the analysis on a synthetic dataset with a known correlation and verifying the model recovers the correct p-value and coefficient sign.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T021 [P] [US2] Contract test for statistical output schema in `code/tests/test_model.py`
- [~] T022 [P] [US2] Integration test for Rank-OLS implementation in `code/tests/test_model.py`

### Implementation for User Story 2

- [~] T023 [P] [US2] Implement unadjusted Spearman correlation calculation in `code/analysis/model.py`
- [~] T024 [US2] Implement Rank-OLS regression: Rank-transform all continuous variables (`age`, `burden`, `depth`, `PC1`, `PC2`) then fit `rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)` in `code/analysis/model.py` and save coefficients, p-values, and adjusted p-values to `code/data/processed/model_results.csv`
- [~] T025 [US2] Implement Benjamini-Hochberg correction for all generated p-values in `code/analysis/model.py`
- [~] T027 [US2] Record coefficients and p-values for the secondary OLS model (as per FR-004) in `code/logs/model_comparison.log`
- [~] T028 [US2] Generate summary statistics (coefficient, p-value, adjusted p-value) for `code/data/processed/analysis_results.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Execute sensitivity analyses to validate findings against threshold choices, population stratification, and power-law assumptions.

**Independent Test**: The system is tested by running the sensitivity analysis with thresholds 0.5%, 1.0%, and 2.0% and verifying the output contains three distinct correlation coefficients.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T030 [P] [US3] Contract test for sensitivity output schema in `code/tests/test_sensitivity.py`
- [~] T031 [P] [US3] Integration test for subgroup analysis in `code/tests/test_sensitivity.py`

### Implementation for User Story 3

- [~] T032 [P] [US3] Implement threshold sweep for heteroplasmy burden recalculation across a range of low-level thresholds. in `code/analysis/sensitivity.py`
- [~] T033 [US3] Implement subgroup analysis for continental ancestries (EUR, AFR, EAS, SAS, AMR) in `code/analysis/sensitivity.py`
- [~] T034 [US3] Implement depth-stratified subsampling to equalize sequencing depth across groups in `code/analysis/sensitivity.py`
- [~] T036 [US3] Implement measurement error simulation (binned age intervals) to estimate attenuation bias in `code/analysis/sensitivity.py`
- [~] T037 [US3] Generate comparative plots for threshold and subgroup results in `code/analysis/visualize.py`
- [~] T038 [US3] Write comprehensive sensitivity report to `code/data/processed/sensitivity_analysis.csv`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T041 [P] Documentation updates in `paper/draft.md` (include findings and limitations)
- [~] T042 Code cleanup and refactoring of `code/analysis/` scripts <!-- ATOMIZE: requested -->
- [~] T043 Performance optimization: ensure VCF streaming does not exceed 7GB RAM
- [~] T044 [P] Additional unit tests for edge cases (zero burden, missing haplogroup) in `code/tests/`
- [~] T045 Run `quickstart.md` validation and verify total runtime ≤ 6 hours on 2 CPU runner
- [~] T046 Generate final figures (linear fit, threshold sensitivity) in `paper/figures/`

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
- **Critical**: Power-law hypothesis tasks have been removed per plan.md Decision Log ("Remove Power-Law Hypothesis").
- **Revision Note**: Updated T024 to explicitly include rank-transformation step; updated T007A/T007B to enforce hard halt; removed redundant T004 and T007B duplicates; removed T029A/B, T039, T040.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence