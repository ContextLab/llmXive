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

- [X] T002 Initialize R 4.3+ project with `renv` and dependencies (`tidyverse`, `lme4`, `car`, `effectsize`, `pwr`, `rmarkdown`, `knitr`, `data.table`, `testthat`, `lintr`)
- [X] T003 [P] Configure `lintr` for code style and `renv.lock` generation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup `data/raw/`, `data/processed/`, `data/derived/`, and `logs/` directories and `.gitignore` rules
- [X] T005 [P] Create `code/measurements.md` with explicit sections for MEQ and MFQ: **exact version**, **item ordering**, and **scoring formula** (Constitution Principle VI)
- [X] T005.5 [P] Generate `quickstart.md` with setup instructions, data requirements, and run commands (Plan.md Phase 1 output, now generated here to ensure artifact exists for T032)
- [X] T006 [P] Create `code/00_config.R` to manage environment variables and file paths
- [X] T007 Create base data validation utilities in `code/utils_validation.R`
- [X] T008 Setup logging infrastructure in `code/utils_logging.R` (warnings, aborts)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Chronotype Classification (Priority: P1) 🎯 MVP

**Goal**: Ingest raw questionnaire data and obtain a reliable chronotype label for each participant.

**Independent Test**: Run the ingestion‑and‑classification script on a sample CSV and verify that the output table contains a `chronotype` column with values "morning", "intermediate", or "evening".

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for chronotype thresholds in `tests/test-classify.R` (verify MEQ >= 59, <= 41, else intermediate)
- [X] T010 [P] [US1] Unit test for missing data handling in `tests/test-classify.R` (verify NA handling and logging)

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/01_ingest.R`:
 1. Load CSV.
 2. Verify presence of ALL required columns (`MEQ_score`, `MFQ_*`, `PSQI`, `acute_sleepiness`, `age`, `sex`). **ABORT immediately** if any column is missing (FR-001) **BEFORE** any processing.
 3. Check for missing `acute_sleepiness`. Exclude rows with missing values and log them to `logs/ingest_exclusions.log` (format: `row_id,reason,step=ingest`). **DO NOT ABORT** immediately.
 4. **FINAL ABORT CHECK (End of Step)**: Calculate total exclusion rate (Excluded Rows / Total Rows). If rate > 20%, **ABORT immediately** with a clear error message. **DO NOT** save any intermediate files if this check fails.
 5. If rate <= 20%, save `data/processed/cleaned_data.csv`.
 6. **Data Contract**: Ensure the script exits with code 0 only if the file is saved; exits with code 1 if aborted.

- [X] T012 [US1] Implement `code/02_classify.R`:
 - **Depends on**: T005 (scoring docs), T011 (cleaned data).
 - Apply thresholds: `MEQ >= 59` -> "morning", `MEQ <= 41` -> "evening", else "intermediate".
 - Flag rows with `NA` or non-numeric `MEQ_score` (exclude and log to `logs/classify_exclusions.log` with format `row_id,reason,step=classify`).
 - Exclude rows with out-of-range MFQ scores (per FR-006), logging each exclusion to `logs/classify_exclusions.log` with format `row_id,reason,step=classify`.
 - **FINAL ABORT CHECK (End of Step)**: Calculate cumulative exclusion rate (Total Excluded so far / Original Rows). If rate > 20%, **ABORT immediately** with a clear error message. **DO NOT** save `classified_data.csv` if this check fails.
 - If rate <= 20%, save `data/derived/classified_data.csv`.

- [X] T014 [US1] [SC-001] Implement `code/06_benchmark_accuracy.R`:
 - **Depends on**: T012.
 - **[SC-001] See SC-001**. **STRICTLY FOR BENCHMARK ACCURACY TEST ONLY**.
 - **Generate** a synthetic benchmark dataset with known labels. **Scope**: Use ONLY for classifier accuracy testing (SC-001), NOT for primary analysis.
 - **WARNING**: This synthetic data is **NOT** for primary analysis or scientific claims.
 - **Method**: Generate data using Beta distributions with **hardcoded parameters** (shape1=2, shape2=5) to mimic real MEQ/MFQ score ranges. **Explicit Mapping**: Generate `MEQ_score` such that the known label is **deterministically derived** using the exact same thresholds as FR-002 (`>=59` -> morning, `<=41` -> evening). The "known label" is the result of applying FR-002 logic to the generated score, ensuring the benchmark is verifiable.
 - **Execution Constraint**: The script **MUST** require the CLI flag `--mode=test`. If invoked without this flag, **ABORT immediately**.
 - **Output Constraint**: The script **MUST** write output **only** to `data/derived/` (e.g., `data/derived/benchmark_results.csv`). If the target directory is `data/processed/`, **ABORT immediately** regardless of flags.
 - Run the classifier on this synthetic data.
 - Verify ≥95% accuracy (SC-001).

- [X] T018 [US1] Implement `code/02.6_reliability.R`:
 - **Depends on**: T012.
 - Calculate Cronbach's alpha for all five MFQ subscales using the classified data.
 - Save results to `data/derived/reliability_metrics.csv` with columns: `subscale`, `cronbach_alpha`, `n_items`.
 - **Verify**: Ensure `data/derived/reliability_metrics.csv` exists and contains valid alpha values.

- [X] T018.5 [US1] [Constitution Principle VI] Implement `code/02.7_meq_reliability.R`:
 - **Depends on**: T012.
 - **[Constitution Principle VI] See Constitution Principle VI**.
 - **Calculate Cronbach's alpha for the MEQ instrument**:
 - **Primary Path (Expected per FR-001)**: If the source data contains ONLY a total `MEQ_score` column (as per FR-001 and Assumptions), the task **MUST** write a row to `data/derived/meq_reliability.csv` with `subscale="MEQ_Total"`, `cronbach_alpha="N/A (single item)"`, `n_items=1`. **DO NOT attempt calculation.**
 - **Secondary Path**: If the source data contains individual MEQ items (e.g., `MEQ_item_1`...`MEQ_item_19`), calculate Cronbach's alpha and save to `data/derived/meq_reliability.csv`.
 - **Report Integration**: Ensure the final report (T026) explicitly states "MEQ Internal Consistency: N/A (single item)" or the calculated alpha value, fulfilling Constitution Principle VI.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Note: T014, T018, T018.5 depend on T012 completion and run sequentially after it.

---

## Phase 4: User Story 2 - Controlled ANCOVA with Multiplicity Control (Priority: P2)

**Goal**: Run ANCOVA for each MFQ subscale, controlling for covariates, and apply Bonferroni correction.

**Independent Test**: Execute the analysis module on a pre‑validated dataset and compare the generated ANCOVA table to a reference R script; all p‑values must match within 0.01.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for ANCOVA model formula in `tests/test-analysis.R`
- [X] T020 [P] [US2] Unit test for Bonferroni correction logic in `tests/test-analysis.R` (Renumbered from duplicate T018)

### Implementation for User Story 2

- [X] T019.5 [US2] [SC-002] Implement `code/reference_ancova.R`:
 - **Depends on**: T012.
 - **[SC-002] See SC-002**.
 - **Create** a reference script that embeds a small, fixed test dataset as a CSV string literal in the code to serve as the internal baseline for SC-002 verification (acknowledging the absence of an external merged dataset per Plan Data Availability Note).
 - **Embedded Data**: Include a minimal CSV string (5 rows) with **explicit values**:
   - Row 1: MEQ=65 (Morning), MFQ_care=4.5, PSQI=3, acute_sleepiness=2, age=30, sex="M"
   - Row 2: MEQ=35 (Evening), MFQ_care=3.0, PSQI=8, acute_sleepiness=5, age=25, sex="F"
   - Row 3: MEQ=50 (Intermediate), MFQ_care=4.0, PSQI=4, acute_sleepiness=3, age=35, sex="M"
   - Row 4: MEQ=60 (Morning), MFQ_care=4.2, PSQI=2, acute_sleepiness=2, age=28, sex="F"
   - Row 5: MEQ=40 (Evening), MFQ_care=3.2, PSQI=7, acute_sleepiness=4, age=32, sex="M"
 - Run the ANCOVA model on this embedded dataset to generate **dynamic** reference p-values.
 - **Output**: Save `data/derived/reference_p_values.csv` containing the results of this run.
 - **Purpose**: This provides a reproducible baseline generated by the actual statistical engine, not hardcoded constants, satisfying SC-002's "pre-validated dataset" requirement by ensuring internal consistency in the absence of an external merged dataset.

- [X] T019 [US2] Implement `code/03_analysis.R`:
 - **Depends on**: T012 (Hard Gate).
 - Run ANCOVA (`MFQ_subscale ~ chronotype + PSQI + acute_sleepiness + age + sex`) for all 5 subscales.
 - Apply Bonferroni correction (α = 0.05/5 = 0.01) to p-values **atomically** within this step (FR-003).
 - Calculate Cohen's d and 95% CI for significant contrasts (FR-004).
 - **Data Contract**: Explicitly output contrast definitions (e.g., `contrast_label="Morning_vs_Evening"`, `contrast_label="Morning_vs_Intermediate"`) for every significant result to `data/derived/ancova_results.csv`.
 - Calculate Variance Inflation Factors (VIF).
 - **If any VIF > 2**: Log warning to `logs/vif_warnings.log`, write "Invalid" flag to `data/derived/vif_flag.csv`, and **DO NOT ABORT** the pipeline (per FR-006), but mark the result as potentially unreliable for publication (honoring Assumptions).
 - If VIF OK, save `data/derived/ancova_results.csv` and `data/derived/effect_sizes.csv`.

- [X] T024 [US2] Implement `code/07_regression_test.R`:
 - **Depends on**: T019, T019.5 (Hard Gate).
 - **Execute** `code/reference_ancova.R` (T019.5) to generate `reference_p_values.csv`.
 - Compare pipeline p-values (from T019) with reference p-values (from T019.5).
 - Verify tolerance ≤0.01 (SC-002).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproducible Reporting & Sensitivity Analysis (Priority: P3)

**Goal**: Generate an R‑Markdown report with descriptive stats, effect sizes, power analysis, and sensitivity sweep.

**Independent Test**: Render the R‑Markdown report on the CI runner and run the validation script; it must confirm presence of all required sections and that the sensitivity table lists results for at least three alpha_corrected values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Validation test for report structure in `tests/test-report.R`

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/04_report.Rmd`: Include descriptive tables, ANCOVA results, Cohen's d, G*Power summary (FR-005). **Depends on**: T019, T018, T018.5, T012.
- [X] T027 [US3] [SC-004] Implement sensitivity analysis sweep in `code/04_report.Rmd`:
 - **[SC-004] See SC-004**.
 - **Depends on**: T019, T018, T012.
 - **Method**: Read existing p-values and **contrast labels** (e.g., `Morning_vs_Evening`) from `data/derived/ancova_results.csv`.
 - **Iterate** over each unique `contrast_label` and recalculate significance status for each alpha threshold (0.01, 0.0125, 0.015) **without re-fitting models**.
 - Generate a summary table listing significance status for **every MFQ subscale contrast** at each threshold.
 - **Output**: Save sensitivity table to `data/derived/sensitivity_sweep.csv` with columns: `subscale`, `contrast_label`, `alpha_threshold`, `p_value`, `significant` (boolean).
 - **Include**: Cronbach's alpha values (read from `data/derived/reliability_metrics.csv` calculated in T018 and T018.5) in the report.
 - **Include**: Data Exclusion Summary section (read from `data/derived/exclusion_counts.json` generated in T011/T012).

- [X] T028 [US3] Generate `reports/chronotype_moral_analysis.html` (or PDF).
- [X] T029 [US3] Implement `code/05_validate_report.R`: Parse report, verify presence of all required sections (SC-003).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030 [P] Create `docs/README.md` with Setup, Run, and Data Source Note sections (replaces vague "Update documentation")
- [X] T031 [P] Code cleanup and refactoring: Run `lintr` on all code using `lintr::lint_dir(..., linters = list(cyclocomp_linter(limit = 10)))` to ensure cyclomatic complexity < 10, remove unused imports, and verify no TODOs remain (Specific, Executable Criteria).
- [X] T032 [P] [US3] Validate `quickstart.md` (Depends on T005.5)
- [X] T033 [P] [US1/US2/US3] Verify CI runner compatibility: Create `.github/workflows/ci.yml` and execute it to produce `logs/ci_run.log` as evidence of compatibility with constrained CPU and limited RAM environments.
- [X] T034 [P] [US1/US2/US3] Add explicit "Data Source Note" to `README.md` and `code/01_ingest.R` header clarifying that the pipeline requires a user-provided merged CSV and will abort if columns are missing, preventing accidental synthetic fallbacks.
- [X] T035 [P] [US3] Add a "Limitations" section to `reports/chronotype_moral_analysis.html` explicitly stating the observational nature of the study and the lack of causal inference, per Spec Assumptions.
- [X] T036 [US1] Implement `code/08_low_balance_alert.R`:
 - **Depends on**: T012.
 - **Logic**: Read `data/derived/classified_data.csv`. Calculate the proportion of participants in the "intermediate" chronotype group.
 - **Action**: If proportion > 0.70, generate a warning file `data/derived/low_balance_alert.txt` with a clear message suggesting recruitment of extreme-type participants.
 - **Report Integration**: **Add a code chunk in `code/04_report.Rmd` (T026) that reads `data/derived/low_balance_alert.txt` and prints its content if the file exists.**

- [X] T037 [US1/US2] Implement `code/09_vif_visualization.R`:
 - **Depends on**: T019.
 - **Logic**: Read `data/derived/ancova_results.csv` (which contains VIF flags). Generate a bar plot of VIF values for all predictors across all 5 models.
 - **Output**: Save plot to `reports/vif_visualization.png`.
 - **Report Integration**: Include `reports/vif_visualization.png` in `code/04_report.Rmd` (T026) to provide visual evidence of collinearity checks.

- [X] T038 [US3] Implement `code/10_power_analysis.R`:
 - **Depends on**: T019.
 - **Logic**: Use the `pwr` package to conduct a post-hoc power analysis for the observed effect sizes (Cohen's f) from the ANCOVA results, assuming α = 0.01.
 - **Output**: Save power summary to `data/derived/power_analysis.csv` and generate a text summary for the report.
 - **Report Integration**: Ensure the G*Power summary section in `code/04_report.Rmd` (T026) reads and displays these calculated power values instead of generic placeholders.

---

## Phase 7: Final Verification & Handoff

**Purpose**: Final checks to ensure the pipeline is ready for execution on the free-tier runner with real data.

- [ ] T039 [US1/US2/US3] [FR-001] [FR-006] [FR-007] Create `tests/testdata/sample_valid.csv` with a representative set of valid, synthetic data rows that passes all ingestion and classification gates. (used for CI smoke tests).
 - **[FR-001] [FR-006] [FR-007] See FR-001, FR-006, FR-007**.
 - **Strict Isolation**: This file is **ONLY** for CI smoke tests. The script generating it **MUST** require `--mode=test`. The file **MUST** be listed in `.gitignore` for production runs or the pipeline must explicitly check for a test flag before loading it.
 - **Content**: Valid columns and values that pass all gates.

- [ ] T040 [US1/US2/US3] [FR-001] Create `tests/testdata/sample_invalid_columns.csv` with missing `acute_sleepiness` column to verify T011 aborts correctly.
 - **[FR-001] See FR-001**.
 - **Strict Isolation**: This file is **ONLY** for CI smoke tests. Must require `--mode=test`.

- [ ] T041 [US1/US2/US3] [FR-006] [FR-007] Create `tests/testdata/sample_high_exclusion.csv` with [deferred] missing `acute_sleepiness` values to verify T011/T012 aborts correctly.
 - **[FR-006] [FR-007] See FR-006, FR-007**.
 - **Strict Isolation**: This file is **ONLY** for CI smoke tests. Must require `--mode=test`.

- [ ] T042 [US1/US2/US3] Write `run_all_tests.sh` script that executes `testthat::test_dir("tests")`, runs `code/06_benchmark_accuracy.R --mode=test`, and renders `code/04_report.Rmd` using `tests/testdata/sample_valid.csv`.
- [ ] T043 [US3] Update `quickstart.md` to include a "Troubleshooting" section explaining the specific abort conditions (missing columns, >20% exclusion) and how to fix them.

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

### Hard Gates

- **T011 & T012**: Must complete successfully (exclusion rate <= 20%) before T019 (ANCOVA) or T026 (Report) can start. If T011 or T012 aborts, the pipeline stops immediately.
- **T019.5**: Must complete before T024 (Regression Test) can start.

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
- **Psychometric Transparency**: Cronbach's alpha must be calculated and reported in the final output for **both** MEQ and MFQ (T018 and T018.5).
- **VIF Handling**: Pipeline must **Flag as Invalid** (not abort) if VIF > 2, per FR-006 and Assumptions.
- **Exclusion Reporting**: All exclusions (missing acute_sleepiness, out-of-range MFQ) must be logged and summarized in the final report.
- **Reliability Metrics**: Cronbach's alpha must be computed for all MFQ subscales (T018) and MEQ (T018.5) and saved to `data/derived/reliability_metrics.csv` for inclusion in the report (T027).
- **Sensitivity Analysis**: The sensitivity sweep must explicitly re-calculate significance status from existing p-values **without re-fitting models** to ensure efficiency, and must iterate over **contrast labels** (T019 output) to cover every required pairwise comparison (SC-004).
- **Exclusion Threshold**: The 20% exclusion rate check is a **hard gate** performed **at the end of each step** (T011, T012) after all exclusions are complete, not immediately upon encountering missing data.
- **Reference Baseline**: T019.5 provides an independent reference script for T024 to ensure SC-002 is met without circular dependency, using a dynamic dataset rather than hardcoded values.
- **Synthetic Data**: T014 uses synthetic data ONLY for SC-001 testing with a hard `--mode=test` flag and strict output path enforcement (`data/derived/`) to prevent leakage.
- **Low Group Balance**: T036 implements the specific alert mechanism for >70% intermediate group dominance, ensuring the report reflects this limitation.
- **Collinearity Visualization**: T037 adds a visual check for VIFs to complement the numeric flags, improving transparency for reviewers.
- **Power Analysis**: T038 ensures the post-hoc power analysis is calculated from the actual observed effect sizes, providing a more accurate G*Power summary than generic estimates.
- **Test Data Generation**: T039-T041 ensure robust CI testing by covering valid, missing column, and high exclusion scenarios, with strict isolation constraints.
- **CI Automation**: T042 provides a single entry point for running all verification steps.
- **Documentation**: T043 ensures users understand failure modes via `quickstart.md`.