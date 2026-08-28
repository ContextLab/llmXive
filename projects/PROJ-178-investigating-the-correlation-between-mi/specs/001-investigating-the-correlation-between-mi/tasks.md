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

- [ ] T001A [P] Create data directories at **repository root**: `data/raw`, `data/processed`, `logs`, `paper/figures` (aligning with plan.md Project Structure).
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
- [X] T013 [P] [US1] Implement chunked VCF reading and in-memory aggregation in `code/analysis/load_data.py` using `vcfpy` to handle large files within 7GB RAM. The function must stream variants, filter for `chrM` and `PASS`, and accumulate heteroplasmy counts per sample without loading the full VCF into memory.
- [X] T014 [US1] Implement variant filtering in `code/analysis/preprocess.py` (retain only `PASS` status and `chrM`)
- [X] T015 [US1] Implement heteroplasmy burden calculation with VAF ≥ 1% threshold in `code/analysis/preprocess.py`
- [X] T016 [US1] Implement depth-stratified burden calculation (Low, Medium, High bins) in `code/analysis/preprocess.py`
- [X] T017 [US1] Integrate `haplogrep2` via subprocess in `code/analysis/preprocess.py` to assign haplogroups
- [ ] T019A [US1] Implement haplogroup assignment success rate calculation; verify if ≥ 90% of samples are assigned and log the result to `code/logs/haplogroup_success_rate.txt`. **Depends on T017 (individual flags)**.
- [X] T019 [US1] **ONLY IF Phase 0 (T007A) PASSES**: Implement conditional exclusion logic for **individual samples**: 1) Exclude samples with missing age from ALL analysis; 2) Exclude samples with failed haplogroup assignment from haplogroup-specific analysis ONLY, but RETAIN them for burden-only analysis if age is present; log exclusion counts and retention status to `code/logs/exclusion_report.txt`. **Depends on T007A (age validation) and T019A (aggregate validation)**.
- [X] T018 [US1] Implement metadata merge logic to join burden, haplogroups, age, sex, population, and PCs; write merged dataframe to `code/data/processed/mito_aging_dataset.csv`
- [X] T020 [US1] Write processed dataset to `code/data/processed/mito_aging_dataset.csv` with checksum generation

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Testing (Priority: P2)

**Goal**: Perform Rank-OLS and Spearman analysis to quantify the relationship between heteroplasmy burden and age, adjusting for confounders.

**Independent Test**: The system can be tested by running the analysis on a synthetic dataset with a known correlation and verifying the model recovers the correct p-value and coefficient sign.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for statistical output schema in `code/tests/test_model.py`
- [X] T022 [P] [US2] Integration test for Rank-OLS implementation in `code/tests/test_model.py`

### Implementation for User Story 2

- [X] T023A [P] [US2] Implement unadjusted Spearman rank correlation calculation (primary method per FR-004) in `code/analysis/model.py` and save results to `code/data/processed/spearman_results.csv`
- [X] T024 [US2] Implement **Rank-OLS** (per plan.md Decision Log) as the primary adjusted analysis: Rank-transform `heteroplasmy_burden`, `age`, `sequencing_depth`, `PC1`, `PC2`. Fit OLS: `rank(age) ~ rank(burden) + sex + PC1 + PC2 + rank(depth)`. Extract coefficient and p-value for `rank(burden)`. Save results to `code/data/processed/rank_ols_results.csv`. **Note**: This task implements the plan's chosen method (Rank-OLS) to satisfy the spec's requirement for multivariate adjustment (FR-004), resolving the methodological contradiction between the spec's "Partial Spearman" mention and the plan's "Rank-OLS" decision.
- [X] T025 [US2] Implement Benjamini-Hochberg correction for all generated p-values in `code/analysis/model.py`
- [X] T027 [US2] Record coefficients and p-values for the secondary OLS model (as per FR-004) in `code/logs/model_comparison.log`, calculate the delta between Rank-OLS and unadjusted Spearman coefficients, and log the comparison result to satisfy the "recorded and compared" requirement.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Execute sensitivity analyses to validate findings against threshold choices, population stratification, and power-law assumptions.

**Independent Test**: The system is tested by running the sensitivity analysis with thresholds 0.5%, 1.0%, and 2.0% and verifying the output contains three distinct correlation coefficients.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Contract test for sensitivity output schema in `code/tests/test_sensitivity.py`
- [X] T031 [P] [US3] Integration test for subgroup analysis in `code/tests/test_sensitivity.py`

### Implementation for User Story 3

- [X] T032 [US3] Implement threshold sweep for heteroplasmy burden recalculation across VAF thresholds: **{0.5%, 1.0%, 2.0%}**. Write results to `code/data/processed/sensitivity_results.csv` with columns: `threshold`, `coefficient`, `p_value`.
- [ ] T032A [US3] Calculate and record the variation (range and standard deviation) of correlation coefficients across the set of low-level thresholds.; save this metric to `code/data/processed/threshold_variation.json` with schema: `{"range": float, "std_dev": float, "thresholds": [float]}` to satisfy SC-003.
- [X] T033 [US3] Implement subgroup analysis for continental ancestries (EUR, AFR, EAS, SAS, AMR) in `code/analysis/sensitivity.py`; write results to `code/data/processed/subgroup_results.csv` with columns: `ancestry`, `coefficient`, `p_value`.
- [ ] T033A [US3] Calculate and record the variation (magnitude of difference) of coefficients across ancestry groups; save this metric to `code/data/processed/subgroup_variation.json` to satisfy SC-004.
- [X] T034 [US3] Implement depth-stratified subsampling to equalize sequencing depth across groups in `code/analysis/sensitivity.py`
- [X] T036 [US3] Implement measurement error simulation (binned age intervals) to estimate attenuation bias in `code/analysis/sensitivity.py`
- [X] T037 [US3] Generate comparative plots for threshold and subgroup results in `code/analysis/visualize.py`
- [X] T038 [US3] Write comprehensive sensitivity report to `code/data/processed/sensitivity_analysis.csv`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: DELETED (Power-Law Analysis - Original)

**Note**: This phase has been removed per plan.md Decision Log ("Remove Power-Law Hypothesis"). All tasks related to Power-Law analysis have been deleted.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Generate `paper/draft.md` including findings, limitations, and the explicit note that the Power-Law hypothesis was removed per the plan's Decision Log. (Addresses spec requirement for a paper draft).
- [X] T049 [P] Refactor `code/analysis/preprocess.py` to reduce cyclomatic complexity of the `calculate_heteroplasmy_burden` function to < 10. **Execution Steps**: 1) Run `radon cc code/analysis/preprocess.py` to record the current baseline complexity of `calculate_heteroplasmy_burden` in `code/logs/complexity_baseline.log`. 2) Refactor the function (e.g., extract helper functions, simplify nested conditionals). 3) Re-run `radon cc` to verify the new complexity is < 10 and log the delta in `code/logs/complexity_reduction.log`. The task is incomplete without the baseline and final verification logs. (Target function identified).
- [ ] T050 [P] Remove unused imports from all scripts in `code/analysis/`.
- [X] T051 [P] Profile `code/analysis/load_data.py` and implement chunking strategy to ensure peak RAM usage < 7GB.
- [X] T052 [P] Verify memory usage via `memory_profiler` and write output to `code/logs/memory_profile.log`.
- [X] T053 [P] Implement unit tests for edge cases in `code/tests/test_data.py`, `code/tests/test_model.py`, and `code/tests/test_sensitivity.py`: specifically test (1) zero heteroplasmic burden, (2) samples with failed haplogroup assignment, and (3) samples with missing age. (Addresses spec Edge Cases).
- [ ] T054A [P] Implement runtime measurement for the **entire analysis pipeline** (Phases 0-5) in `code/run_analysis.py`. **Log total execution time to `code/logs/runtime.log` and flag if > 6 hours** to satisfy SC-005. Do NOT assert/fail the pipeline; the spec requires measurement against the constraint, not a hard crash.
- [ ] T055 [P] Generate final figures (Rank-OLS fit, threshold sensitivity, subgroup comparison) in `paper/figures/`. (Note: Power-Law figure removed from original plan).

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
3. Add User Story 2 → Test independently → Deploy/Demo (Rank-OLS & Spearman Correlation)
4. Add User Story 3 → Test independently → Deploy/Demo (Robustness of Correlation)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Statistical Models)
 - Developer C: User Story 3 (Sensitivity, Robustness)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Phase 6 (Power-Law) has been removed per plan.md Decision Log.
- **Revision Note**: Updated T007A/T007B to enforce hard halt with artifacts; added T023A for primary Spearman; added T019A for haplogroup success rate; removed T028; updated T024 to implement Rank-OLS per plan.md (resolving spec-plan contradiction); removed all Power-Law/West review references (T056, T057, T055, T060, T039).
- **Revision Note**: Updated T032 to explicitly list thresholds {0.5%, 1.0%, 2.0%} from plan.md Decision Log and log spec discrepancy; added T032A/T033A to explicitly calculate variation metrics for SC-003/SC-004; updated T019 to implement conditional retention logic for partial data; updated T027 to include comparison logic.
- **Revision Note**: Updated T001A to use correct repository root paths (`data/raw` vs `code/data/raw`).
- **Revision Note**: Reordered T019A before T019 to ensure aggregate validation precedes row-wise filtering logic.
- **Revision Note**: Merged T013A and T013B into T013 to resolve interface ambiguity.
- **Revision Note**: Replaced T049 with a specific target function and T053 with specific test cases.
- **Revision Note**: Added T041 to generate the paper draft as required by the spec.
- **Revision Note**: Removed T056, T057, T055 (original), T060 as they implemented the deleted Power-Law hypothesis.
- **Revision Note**: Updated T049 to include baseline measurement and verification steps for cyclomatic complexity to resolve executability concerns.
- **Revision Note**: Updated T054A to log and flag runtime violations instead of asserting, aligning with spec SC-005.
- **Revision Note**: Removed T019B to align with the binary halt logic defined in plan.md (no re-scope deliverable defined).
- **Revision Note**: Removed T039 and updated T055/T041 to remove all references to the deleted Power-Law hypothesis, resolving plan contradiction and ordering violations.
- **Revision Note**: Removed T039 (Power-Law Scaling) and T055 (Power-Law Figure) to resolve plan contradiction and ordering violations.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence