# Tasks: Simulation-Based Sensitivity Analysis of Framing Effects on Perceived Severity of Online Misinformation

**Input**: Design documents from `/specs/001-the-impact-of-framing/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [ ] T001 Create project structure per implementation plan with exact directories: `projects/PROJ-399-the-impact-of-framing-on-perceived-sever/data/raw/`, `data/processed/`, `results/plots/`, `code/`, `tests/`, `.github/workflows/`. **Deliverable**: `docs/project_structure.md` (a verified directory tree log).
- [ ] T002 Initialize R 4.3+ project with `code/DESCRIPTION`, `code/NAMESPACE`, and `code/renv.lock` with dependencies version pinned (e.g., `lme4>=1.1-31`, `lmerTest>=3.1-3`, `pwr>=1.3-0`, `dplyr>=1.1.0`, `ggplot2>=3.4.0`, `tidyr>=1.3.0`, `data.table>=1.14.0`, `testthat>=3.1.0`). **Deliverable**: `code/DESCRIPTION`, `code/NAMESPACE`, `code/renv.lock`. <!-- ATOMIZE: requested -->
- [ ] T003 [P] Configure linting and formatting tools (e.g., `lintr` for R)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T005 [P] Implement deterministic random seed configuration: Create `code/config.yaml` with a seed value and `code/utils.R` with a function to load and apply this seed from the config file (do NOT hardcode in script). **Deliverable**: `code/config.yaml`, `code/utils.R`.
- [ ] T006 [P] Setup environment configuration management (e.g., `.Renviron` or `renv`)
- [ ] T007 Create base data validation utilities to check for required stimulus columns (`stimulus_id`, `content_domain`, `headline`)
- [~] T008 Configure error handling and logging infrastructure for R scripts
- [ ] T009 Setup CI workflow file (`.github/workflows/analyze.yml`) targeting GitHub Actions free tier (limited CPU, limited RAM)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Primary Analysis: Simulation of Framing Effect on Severity Perception (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic severity data based on MPSD-v2 stimuli and fit a mixed-effects linear model to test the framing effect.

**Independent Test**: Can be fully tested by running the mixed-effects linear model on the generated synthetic dataset and verifying the coefficient for the `framing_condition` variable is correctly calculated and reported, regardless of its statistical significance.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Contract test for synthetic data schema in `tests/test_data_generation.R` (validates `severity_rating` 1-7 range and `framing_condition` assignment) <!-- FAILED: unspecified -->
- [X] T011 [P] [US1] Integration test for mixed-effects model output format in `tests/test_statistics.R`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/01_data_prep.R`: Fetch MPSD-v2 stimulus data from the SPECIFIC OSF URL (validated) and verify checksums. Validate that all required stimulus columns (`stimulus_id`, `content_domain`, `headline`) are present. **DEPENDS ON**: T004, T009. <!-- ATOMIZE: requested -->
- [X] T013 [US1] Implement `code/01_data_prep.R`: Generate synthetic dataset (N=300) by sampling 10 unique stimuli. For each stimulus, generate 15 "harm" and 15 "fact" responses (Total N=300, between-subjects design). Use parametric generation: `severity_rating` ~ Normal(mean=base + delta*condition, SD=1.5), `sharing_intention` ~ Bernoulli(logit). **DEPENDS ON**: T012. <!-- FAILED: unspecified -->
- [X] T013b [US1] Implement `code/01_data_prep.R`: Implement sensitivity analysis loop. Iterate over a range of delta values (e.g., from a minimal baseline to a substantial upper bound in incremental steps) to generate multiple synthetic datasets. **Deliverable**: `data/processed/sensitivity_datasets/`. **DEPENDS ON**: T013. <!-- FAILED: unspecified -->
- [~] T013c [US1] Implement `code/01_data_prep.R`: Aggregate sensitivity loop results to generate a "Power vs. Delta" mapping table and visualization. **Deliverable**: `results/processed/sensitivity_curve_data.csv`, `results/plots/sensitivity_analysis.png`. **DEPENDS ON**: T013b.
- [X] T014 [US1] Implement `code/03_analysis.R`: Fit mixed-effects linear model (`lmer`) with formula `severity_rating ~ framing_condition + (1|stimulus_id)` using `lme4`. Handle singular fits gracefully. Extract coefficient, SE, and p-value. **DEPENDS ON**: T013. <!-- FAILED: unspecified -->
- [X] T015 [US1] Implement `code/03_analysis.R`: Calculate Cohen's d effect size for the difference in mean severity ratings between framing conditions. **DEPENDS ON**: T014. <!-- FAILED: unspecified -->
- [X] T016 [US1] Implement `code/03_analysis.R`: Apply Bonferroni correction to the p-value for the primary framing effect hypothesis. The correction factor MUST be dynamically calculated as (1 + number of interaction tests performed in US2). **DEPENDS ON**: T014.
- [~] T017 [US1] Implement `code/04_export.R`: Generate bar plot with confidence intervals for severity ratings by framing condition. **Deliverable**: `results/plots/us1_severity_barplot.png`. **DEPENDS ON**: T015.
- [~] T018 [US1] Implement `code/04_export.R`: Save primary analysis results (coefficient, p-value, effect size) to an intermediate file `results/intermediate/us1_results.json`. **DEPENDS ON**: T016, T017. **DO NOT APPEND TO ROOT**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Secondary Analysis: Simulation of Framing Effect on Sharing Intentions (Priority: P2)

**Goal**: Analyze the relationship between simulated framing conditions and binary sharing intentions, controlling for content domain.

**Independent Test**: Can be fully tested by running a logistic regression model predicting `sharing_intention` from `framing_condition` and `content_domain`, and verifying the odds ratio and p-value is correctly calculated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for logistic regression output in `tests/test_statistics.R` (validates odds ratio and p-value presence)

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/03_analysis.R`: Fit logistic regression model (`glm`) predicting `sharing_intention` from `framing_condition` and `content_domain`. **DEPENDS ON**: T013.
- [X] T021 [US2] Implement `code/03_analysis.R`: Calculate odds ratios and p-values for the `framing_condition` coefficient. **DEPENDS ON**: T020.
- [X] T022 [US2] Implement `code/03_analysis.R`: Test and report the interaction coefficient between `framing_condition` and `content_domain`. **DEPENDS ON**: T020.
- [~] T023 [US2] Implement `code/04_export.R`: Save logistic regression results (odds ratios, p-values) to an intermediate file `results/intermediate/us2_results.json`. **DEPENDS ON**: T021, T022. **DO NOT APPEND TO ROOT**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - A Priori Power Analysis (Priority: P3)

**Goal**: Perform an *a priori* power analysis to VERIFY that the planned sample size (N=300) is sufficient to detect a small-to-medium effect size (d=0.3) with ≥80% power.

**Independent Test**: Can be fully tested by running the `pwr` package calculation using the target effect size (d=0.3) and sample size (N=300), and verifying the calculated power meets or exceeds 80%.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for power calculation logic in `tests/test_statistics.R` (verifies power >= 0.80 for d=0.3, N=300)

### Implementation for User Story 3

- [~] T025 [US3] Implement `code/02_power_analysis.R`: Execute *a priori* power analysis using `pwr` package with d=0.3, alpha=0.05, N=300. **VERIFY** that the calculated power for the planned N=300 is ≥ 0.80. If power < 0.80, log a critical warning and halt. **Deliverable**: `results/processed/power_analysis_verification.json`. **DEPENDS ON**: T005.
- [ ] T026 [US3] Implement `code/02_power_analysis.R`: Confirm that N=300 achieves ≥80% power; if not, flag a warning in logs and halt execution. **DEPENDS ON**: T025.
- [ ] T027 [US3] Implement `code/04_export.R`: Save power analysis results (calculated power, target effect size, sample size justification) to an intermediate file `results/intermediate/us3_results.json`. **DEPENDS ON**: T026. **DO NOT APPEND TO ROOT**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [US1/US2/US3] Implement `code/04_export.R`: Aggregate all intermediate results (us1_results.json, us2_results.json, us3_results.json) and visualizations into a single `projects/PROJ-399-the-impact-of-framing-on-perceived-sever/results.md` file in the PROJECT ROOT. **DEPENDS ON**: T018, T023, T027.
- [ ] T028 [P] Documentation updates in `quickstart.md` (include instructions for running `01_data_prep.R`, `02_power_analysis.R`, `03_analysis.R`)
- [ ] T029 Code cleanup and refactoring in `code/` to ensure `lme4` and `pwr` usage is optimal for CPU-only CI
- [ ] T030 Performance optimization: Ensure memory usage stays < 2GB during peak processing (validate synthetic N=300 limits)
- [ ] T031 [P] Additional unit tests for data generation logic in `tests/test_data_generation.R` (edge cases: singular fit handling, missing columns)
- [ ] T032 Run `quickstart.md` validation to ensure all scripts execute successfully on a fresh runner

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. T013 (Data Generation) is independent of Power Analysis. T013 must complete before T014.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Reuses synthetic data from T013.
- **User Story 3 (P3)**: T025/T026/T027 are in Phase 5. T027 (Export) depends on T026.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models (data prep) before services (analysis)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (except T025 which blocks T013) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for synthetic data schema in tests/test_data_generation.R"
Task: "Integration test for mixed-effects model output format in tests/test_statistics.R"

# Launch all models for User Story 1 together:
Task: "Implement code/01_data_prep.R: Fetch MPSD-v2 stimulus data"
Task: "Implement code/01_data_prep.R: Generate synthetic dataset"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Prep -> Mixed Effects Model -> Export)
4. **STOP and VALIDATE**: Test User Story 1 independently on GitHub Actions runner.
5. Deploy/demo if ready.

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
 - Developer A: User Story 1 (Data Prep + Model)
 - Developer B: User Story 2 (Logistic Regression)
 - Developer C: User Story 3 (Power Analysis)
3. Stories complete and integrate independently into `results.md` via T033.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks must run on CPU-only GitHub Actions free tier (limited CPU, constrained RAM). No GPU, no 8-bit quantization, no large model training.
- **Data Integrity**: T012 must fetch real data (MPSD-v2 proxy) via specific OSF URL with checksum; no hardcoded fake data.
- **Order**: T013 (Data Generation) MUST precede T014 (Model Fitting). T014 MUST precede T018 (Intermediate Export). T018/T023/T027 MUST precede T033 (Final Aggregation).
- **Reproducibility**: T005 mandates seed pinning via `code/config.yaml` (system-managed, not hardcoded).
- **Sensitivity Analysis**: T013b/T013c implement the loop over delta values and aggregation as required by the plan.
- **Export Path**: Final report is `projects/PROJ-399-the-impact-of-framing-on-perceived-sever/results.md` in project root (T033), not `results/results.md`.
- **Power Analysis**: T025/T026 explicitly VERIFY that N=300 achieves ≥80% power.
- **Bonferroni**: T016 dynamically calculates the correction factor based on total tests.