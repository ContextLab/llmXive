# Tasks: The Relationship Between Sleep Chronotype and Moral Judgement

**Input**: Design documents from `/specs/chronotype-moral-judgement/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-046-the-relationship-between-sleep-chronotyp/`). **Note**: Spec Assumption "Data Source Strategy" (Prolific integration) contradicts Plan.md (user-provided data). Flag for plan update.
- [X] T002 Initialize R 4.3+ project with `renv` and dependencies (`tidyverse`, `lme4`, `car`, `effectsize`, `pwr`, `rmarkdown`, `knitr`, `data.table`, `testthat`, `lintr`)
- [X] T003 [P] Configure `lintr` for code style and `renv.lock` generation <!-- FAILED: unspecified -->

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup `data/raw/`, `data/processed/`, `data/derived/`, and `logs/` directories and `.gitignore` rules
- [X] T005 [P] Create `code/measurements.md` with explicit sections for MEQ and MFQ: **exact version**, **item ordering**, and **scoring formula** (Constitution Principle VI)
- [X] T006 [P] Create `code/00_config.R` to manage environment variables and file paths
- [X] T007 Create base data validation utilities in `code/utils_validation.R`
- [ ] T008 Setup logging infrastructure in `code/utils_logging.R` (warnings, aborts)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Chronotype Classification (Priority: P1) 🎯 MVP

**Goal**: Ingest raw questionnaire data and obtain a reliable chronotype label for each participant.

**Independent Test**: Run the ingestion-and-classification script on a sample CSV and verify that the output table contains a `chronotype` column with values "morning", "intermediate", or "evening".

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for chronotype thresholds in `tests/test-classify.R` (verify MEQ >= 59, <= 41, else intermediate)
- [X] T010 [P] [US1] Unit test for missing data handling in `tests/test-classify.R` (verify NA handling and logging)

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/01_ingest.R`:
 1. Load CSV.
 2. Verify presence of ALL required columns (`MEQ_score`, `MFQ_*`, `PSQI`, `acute_sleepiness`, `age`, `sex`). **ABORT** immediately if any column is missing (FR-001).
 3. For rows with missing `acute_sleepiness`: exclude the row, log to `logs/ingest_exclusions.log`, and track count.
 4. **Save** `data/processed/cleaned_data.csv` and a provisional count to `data/derived/ingest_exclusion_count.json`.
 5. **Do NOT check 20% threshold here**; this is a provisional step.
- [X] T012 [US1] Implement `code/02_classify.R`:
 - **Depends on**: T005 (scoring docs), T011 (cleaned data).
 - Apply thresholds: `MEQ >= 59` -> "morning", `MEQ <= 41` -> "evening", else "intermediate".
 - Flag rows with `NA` or non-numeric `MEQ_score` (exclude and log to `logs/classify_exclusions.log`).
 - **Exclude rows with out-of-range MFQ scores** (per FR-006), logging each exclusion to `logs/classify_exclusions.log`.
 - Save classified data to `data/derived/classified_data.csv`.
 - **Do NOT check 20% threshold here**; this is a provisional step.
- [ ] T012.5 [US1] Implement `code/02.5_aggregate_exclusions.R`:
 - **Depends on**: T011, T012.
 - Read `data/derived/ingest_exclusion_count.json` and count lines in `logs/classify_exclusions.log`.
 - Calculate **cumulative exclusion rate** (Total Excluded / Original Rows).
 - **ABORT** pipeline if cumulative rate > 20% (FR-006, FR-007).
 - If OK, write final `data/derived/exclusions.log` (merged logs) and `data/derived/exclusion_counts.json` (final counts).
 - **Verify**: Ensure `data/derived/exclusions.log` exists and contains all exclusion details.
- [ ] T014 [US1] [P] Implement `code/06_benchmark_accuracy.R`: <!-- FAILED: unspecified -->
 - **Depends on**: T012.
 - **Generate** a synthetic benchmark dataset with known labels. **Scope**: Use ONLY for classifier accuracy testing (SC-001), NOT for primary analysis.
 - Run the classifier on this synthetic data.
 - Verify ≥95% accuracy (SC-001).
- [X] T018 [US1] [P] Implement `code/02.6_reliability.R`:
 - **Depends on**: T012.5.
 - Calculate Cronbach's alpha for all five MFQ subscales using the classified data.
 - Save results to `data/derived/reliability_metrics.csv` with columns: `subscale`, `cronbach_alpha`, `n_items`.
 - **Verify**: Ensure `data/derived/reliability_metrics.csv` exists and contains valid alpha values.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Controlled ANCOVA with Multiplicity Control (Priority: P2)

**Goal**: Run ANCOVA for each MFQ subscale, controlling for covariates, and apply Bonferroni correction.

**Independent Test**: Execute the analysis module on a pre-validated dataset and compare the generated ANCOVA table to a reference R script; all p-values must match within 0.01.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T017 [P] [US2] Unit test for ANCOVA model formula in `tests/test-analysis.R`
- [~] T018 [P] [US2] Unit test for Bonferroni correction logic in `tests/test-analysis.R`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/03_analysis.R`: <!-- FAILED: unspecified -->
 - **Depends on**: T012.5.
 - Run ANCOVA (`MFQ_subscale ~ chronotype + PSQI + acute_sleepiness + age + sex`) for all 5 subscales.
 - Apply Bonferroni correction (α = 0.05/5 = 0.01) to p-values **atomically** within this step (FR-003).
 - Calculate Cohen's d and 95% CI for significant contrasts (FR-004).
 - Calculate Variance Inflation Factors (VIF).
 - **If any VIF > 2**: Log warning to `logs/vif_warnings.log`, write error flag to `logs/vif_error.flag`, and **ABORT** pipeline (Spec Assumptions: VIFs must be < 2).
 - If VIF OK, save `data/derived/ancova_results.csv` and `data/derived/effect_sizes.csv`.
- [ ] T024 [US2] [P] Implement `code/07_regression_test.R`: <!-- FAILED: unspecified -->
 - **Depends on**: T019.
 - **Generate** `reference_p_values.csv` using a hardcoded R script logic (simulating a reference run) to ensure the artifact exists.
 - Compare pipeline p-values (from T019) with reference p-values.
 - Verify tolerance ≤0.01 (SC-002).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproducible Reporting & Sensitivity Analysis (Priority: P3)

**Goal**: Generate an R-Markdown report with descriptive stats, effect sizes, power analysis, and sensitivity sweep.

**Independent Test**: Render the R-Markdown report on the CI runner and run the validation script; it must confirm presence of all required sections and that the sensitivity table lists results for at least three alpha_corrected values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T025 [P] [US3] Validation test for report structure in `tests/test-report.R`

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/04_report.Rmd`: Include descriptive tables, ANCOVA results, Cohen's d, G*Power summary (FR-005). **Depends on**: T019, T018, T012.5. <!-- ATOMIZE: requested -->
- [X] T027 [US3] Implement sensitivity analysis sweep in `code/04_report.Rmd`:
 - **Depends on**: T019, T018, T012.5.
 - **Method**: Re-run ANCOVA models for each alpha threshold (0.01, 0.0125, 0.015) to ensure accuracy within 6h runtime.
 - Generate a summary table listing significance status for every MFQ subscale contrast at each threshold.
 - **Output**: Save sensitivity table to `data/derived/sensitivity_sweep.csv` with columns: `subscale`, `alpha_threshold`, `p_value`, `significant` (boolean).
 - **Include**: Cronbach's alpha values (read from `data/derived/reliability_metrics.csv` calculated in T018) in the report.
 - **Include**: Data Exclusion Summary section (read from `data/derived/exclusions.log` generated in T012.5).
- [ ] T028 [US3] Generate `reports/chronotype_moral_analysis.html` (or PDF).
- [ ] T029 [US3] Implement `code/05_validate_report.R`: Parse report, verify presence of all required sections (SC-003).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Update documentation in `docs/` with run instructions
- [ ] T031 Code cleanup and refactoring
- [ ] T032 [P] Run `quickstart.md` validation
- [ ] T033 Verify CI runner compatibility (2 CPU, 7GB RAM, no GPU)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (`classified_data.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (`ancova_results.csv`)

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for chronotype thresholds in tests/test-classify.R"
Task: "Unit test for missing data handling in tests/test-classify.R"

# Launch all models for User Story 1 together:
Task: "Implement code/01_ingest.R"
Task: "Implement code/02_classify.R"
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
- **Data Constraint**: The pipeline requires a user-provided merged dataset. No synthetic data generation is permitted for primary analysis.
- **Compute Constraint**: All tasks must run on free CPU-only CI with limited resources. No GPU or heavy model loading.
- **Data Hygiene**: Raw data in `data/raw/` must never be modified. All derived files go to `data/derived/`.
- **Psychometric Transparency**: Cronbach's alpha must be calculated and reported in the final output.
- **VIF Handling**: Pipeline must ABORT if VIF > 2.
- **Exclusion Reporting**: All exclusions (missing acute_sleepiness, out-of-range MFQ) must be logged and summarized in the final report.
- **Reliability Metrics**: Cronbach's alpha must be computed for all MFQ subscales and saved to `data/derived/reliability_metrics.csv` for inclusion in the report (T027).
- **Sensitivity Analysis**: The sensitivity sweep must explicitly re-fit models for each alpha threshold to ensure statistical accuracy, rather than approximating from a single run.
- **Exclusion Threshold**: The 20% exclusion rate check is a **final gate** performed by T012.5 after aggregating exclusions from T011 and T012.