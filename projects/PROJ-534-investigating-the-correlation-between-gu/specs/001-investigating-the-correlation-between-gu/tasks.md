# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility in Aging

**Input**: Design documents from `/specs/001-gut-microbiome-cognitive-flexibility/`
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

- [ ] T001a [P] Create project directory structure (`src/`, `tests/`, `data/raw`, `data/processed`, `data/results`)
- [ ] T001b [P] Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (pandas, scikit-learn, scipy, statsmodels, biom-format, numpy, matplotlib, seaborn, pyyaml)
- [ ] T002 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Create `contracts/dataset.schema.yaml` defining Participant and MicrobiomeProfile entities
- [ ] T004 Create `contracts/analysis_output.schema.yaml` defining AnalysisResult entity
- [ ] T005 [P] Implement `src/utils/config.py` with fixed random seeds and path configurations
- [~] T006 [P] Setup `pytest` configuration and test directory structure
- [~] T007 Implement data validation utilities in `src/utils/validation.py` to enforce schema contracts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Cohort Filtering (Priority: P1) 🎯 MVP

**Goal**: Ingest synthetic 16S and cognitive data, filter for age >= 65 with complete data, and validate against schema.

**Independent Test**: Run ingestion on a small synthetic dataset with mixed ages and missing values; verify output contains ONLY rows matching age >= 65 and non-null metrics.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T008 [P] [US1] Unit test for age filtering logic in `tests/unit/test_filtering.py`
- [~] T009 [P] [US1] Unit test for null-value exclusion in `tests/unit/test_filtering.py`
- [~] T010 [P] [US1] Contract test validating `data/processed/filtered_cohort.csv` against `contracts/dataset.schema.yaml` in `tests/contract/test_schemas.py` <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [~] T011 [US1] Implement `src/data/synthetic_gen.py` to generate independent (Null Hypothesis) 16S and cognitive data with fixed seeds, explicitly referencing Plan Amendment Task 0.1
- [~] T012 [US1] Implement `src/data/ingestion.py` to load synthetic data and merge on participant ID
- [~] T013 [US1] Implement `src/data/filtering.py` to filter for age >= 65, non-null Shannon/Cognitive scores, and required covariates (age, sex, BMI, fiber, antibiotics)
- [~] T014 [US1] Add logic in `src/data/filtering.py` to handle zero-variance datasets by flagging and skipping correlation (Edge Case)
- [~] T015 [US1] Add logic in `src/data/filtering.py` to handle missing covariates via listwise deletion (default) or mean imputation, with the choice explicitly logged to `logs/filtering.log`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Diversity Metric Calculation and Correlation Analysis (Priority: P2)

**Goal**: Calculate alpha/beta diversity, perform correlation/regression with covariates, apply FDR correction, and handle non-normality.

**Independent Test**: Provide pre-calculated metrics and scores; verify correlation coefficients match manual calculation, regression converges, and FDR is applied.

### Tests for User Story 2

- [~] T016 [P] [US2] Unit test for Shannon/Simpson/Chao1 calculation in `tests/unit/test_diversity.py`
- [ ] T017 [P] [US2] Unit test for Pearson/Spearman auto-switch logic (skewness/Shapiro-Wilk) and logging of the switch in `tests/unit/test_correlation.py`
- [ ] T018 [P] [US2] Unit test for Benjamini-Hochberg correction in `tests/unit/test_correlation.py`
- [ ] T027 [P] [US2] Contract test validating `data/results/correlation_results.json` against `contracts/analysis_output.schema.yaml` in `tests/contract/test_schemas.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `src/analysis/diversity.py` to calculate Alpha (Shannon, Simpson, Chao1) and Beta (Bray-Curtis, UniFrac) metrics from the filtered cohort
- [ ] T020 [US2] Implement `src/analysis/correlation.py` to perform Pearson/Spearman correlation (auto-switch if skewness > 1.0 or Shapiro-Wilk p < 0.05) with a specified confidence interval, including **logging of the switch**
- [ ] T021 [US2] Implement `src/analysis/correlation.py` to run Linear Regression (Cognitive ~ Diversity + Covariates) with Benjamini-Hochberg correction
- [ ] T022 [US2] Implement `src/analysis/beta_diversity.py` to perform PERMANOVA (using `skbio.stats.distance.permanova`) for Beta diversity with continuous cognitive scores
- [ ] T023 [US2] Save `data/results/correlation_results.json` containing coefficients, p-values, adjusted p-values, and CIs, verifying keys: `correlation_coefficient`, `p_value`, `adjusted_p_value`, `confidence_interval` against `contracts/analysis_output.schema.yaml`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Power Estimation (Priority: P3)

**Goal**: Generate visualizations of diversity by cognitive quartiles and calculate power/sample size for future studies.

**Independent Test**: Run viz module on sample data; verify plots render and power output includes effect size and required N for [deferred] power.

### Tests for User Story 3

- [ ] T025 [P] [US3] Unit test for power calculation logic in `tests/unit/test_power.py`
- [ ] T037 [P] [US3] Integration test verifying plot generation in `tests/integration/test_viz.py`
- [ ] T035 [P] [US3] Unit test for power estimation module output: Verify `required_sample_size` is calculated correctly for a given effect size in `tests/unit/test_power.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `src/viz/plots.py` to generate boxplots of alpha diversity stratified by cognitive flexibility quartiles (Q1-Q4)
- [ ] T029 [US3] Implement `src/power/estimation.py` to calculate required sample size for 80% power at α = 0.05. **Calculation MUST use the observed effect size from T023**. {{claim:c_7b2d3ace}} and log the comparison.
- [ ] T030 [US3] Implement `src/sensitivity/confounding.py` to calculate E-values manually using `scipy` and `statsmodels` (no external EValue library) for negative control tests
- [ ] T031 [US3] Generate summary table in `data/results/summary_table.csv` with effect sizes, CIs, and adjusted p-values

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Final Validation & Polish

**Purpose**: Cross-cutting concerns, final aggregation, and end-to-end validation

- [ ] T026a [P] [US2] Generate specific synthetic dataset with known independence for Null Hypothesis validation
- [ ] T026b [P] [US2] Run full pipeline on generated data and assert p > 0.05 in `tests/unit/test_null_hypothesis.py`
- [ ] T032 [P] Aggregate results from T023 (correlation) and T029 (power) into a single canonical `data/results/statistical_results.json` (enforcing Single Source of Truth)
- [ ] T033 [P] Code cleanup and refactoring for CPU/memory efficiency
- [ ] T034 [P] Run full pipeline validation in `tests/integration/test_pipeline.py` to ensure end-to-end reproducibility
- [ ] T038 [P] Additional unit tests for edge cases (zero variance, extreme skewness)
- [ ] T036 [P] Run `quickstart.md` validation
- [ ] T041 [P] Update `README.md` with installation instructions and usage examples
- [ ] T042 [P] Create `docs/api.md` with function signatures for `src/analysis/` modules

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Final Validation (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (filtered cohort)
 - T026a/T026b (Null Hypothesis Test) depends on T020 (Correlation) and T021 (Regression) and T023 (Results Saved)
 - T027 (Schema Validation) depends on T023 (Results Saved)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (results)
 - T029 (Power Estimation) depends on T023 (Results Saved)
 - T030 (Sensitivity) depends on T023 (Results Saved) and can run in parallel with T028 (Viz)
- **Phase 6 (Final Validation)**:
 - T032 (Aggregation) depends on T023 and T029
 - T026a/T026b (Null Hypothesis) depends on completion of US1 and US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Contracts before services
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
# Launch all tests for User Story 1 together:
Task: "Unit test for age filtering logic in tests/unit/test_filtering.py"
Task: "Unit test for null-value exclusion in tests/unit/test_filtering.py"
Task: "Contract test validating data/processed/filtered_cohort.csv in tests/contract/test_schemas.py"

# Launch implementation tasks (sequential due to data flow):
Task: "Implement src/data/synthetic_gen.py" -> "Implement src/data/ingestion.py" -> "Implement src/data/filtering.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Synthetic Gen + Filtering)
4. **STOP and VALIDATE**: Test US1 independently (Null Hypothesis check)
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Analysis Logic)
 - Developer C: User Story 3 (Viz & Power)
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
- **Critical Constraint**: All tasks must run on CPU-only CI with a limited number of cores and constrained RAM.

The research question remains: [Research Question].
The method remains: [Method].
References: [References]. No GPU, no 8-bit quantization, no large models.
- **Data Integrity**: All data is synthetic (Null Hypothesis) for this validation phase. No real UK Biobank data is used until the pipeline is proven.
- **Single Source of Truth**: T032 ensures a single canonical results file.
- **Null Hypothesis Validation**: T026b explicitly validates the pipeline returns p > 0.05 for independent variables.
- **Power Estimation Validation**: T029 uses the observed effect size for calculation and a literature-derived value for sanity check.