# Tasks: Assessing the Validity of Frequentist Confidence Intervals with Small Sample Sizes

**Input**: Design documents from `/specs/001-assessing-ci-coverage/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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
 IMPORTANT: This task list strictly adheres to the Feature Specification (spec.md).

 The Spec (FR-001, FR-010, Principle VII) MANDATES REAL UCI DATASETS and the
 FULL DATASET MEAN as operational ground truth. These tasks enforce the Spec.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`projects/PROJ-263-assessing-the-validity-of-frequentist-co/`)
- [X] T002 Initialize Python 3.11 project with `pandas`, `numpy`, `scipy`, `scikit-learn`, `pyyaml`, `pytest` dependencies
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `data/raw/` and `data/processed/` directories with `.gitkeep`
- [X] T005 Create `code/simulation.py` skeleton with Monte Carlo loop structure (depends on T012) <!-- ATOMIZE: requested -->
- [X] T006 Create `code/coverage.py` skeleton for coverage calculation logic (depends on T012)
- [X] T007 Create `code/sensitivity.py` skeleton for sensitivity analysis logic (depends on T012)
- [X] T008 Create `code/main.py` orchestration script entry point <!-- ATOMIZE: requested -->
- [ ] T009 Setup environment configuration management (load random seeds, config paths)
- [ ] T010 Implement deterministic random seed management (per Principle I) across all modules
- [ ] T011 Implement checksum generation for raw data upon creation (per Principle III)
- [ ] T012 Create base schemas for `data-models/schemas/` (SimulationRun, CoverageRecord, AggregateReport)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Monte Carlo Simulation Engine (Priority: P1) 🎯 MVP

**Goal**: Execute a Monte Carlo simulation that draws repeated small samples (n=10, n=20, n=30) from REAL UCI datasets, computes standard t-intervals and bootstrap percentile intervals, and checks empirical coverage against the known population mean (mean of the full UCI dataset array).

**Independent Test**: Run `code/main.py` with a single UCI dataset (e.g., Wine) and verify `outputs/coverage_results.json` contains coverage rates for both t-intervals and bootstrap intervals matching the true population mean of that dataset.

### Implementation for User Story 1

- [ ] T016 [US1] Implement UCI dataset downloader: fetch REAL numeric datasets from UCI Machine Learning Repository via HTTP (FR-001) and save to `data/raw/`. **Specific datasets to fetch**: Wine, Wine Quality Red, Wine Quality White, Ionosphere, Heart Disease (Cleveland).
- [~] T017 [US1] Implement data loader: parse downloaded UCI datasets and identify continuous numeric variables (FR-002).
- [ ] T017.5 [US1] Implement explicit variable type validation: verify selected variables are continuous numeric before simulation begins (FR-002).
- [~] T018 [US1] Implement data cleaner: exclude rows with missing values and filter for continuous variables only (FR-002, Edge Cases).
- [~] T019 [US1] Implement edge case handler: skip datasets with insufficient row counts, handle categorical variables, and log warnings (Edge Cases).
- [ ] T020 [US1] Implement population mean calculator: compute the mean of the FULL UCI DATASET ARRAY for each variable to serve as operational ground truth (Constitution Principle VII, FR-010) and save to `data/processed/population_means.json`.
- [~] T021 [US1] Implement sampling logic: draw samples of size n=10, 20, 30 *with replacement* from the cleaned UCI dataset array to approximate the super-population distribution for testing the t-interval's infinite population assumption (FR-010).
- [~] T022 [US1] Implement t-interval calculation using `scipy.stats.t.ppf` for critical values (FR-005).
- [~] T023 [US1] Implement bootstrap percentile interval calculation using A large number of bootstrap resamples and `numpy.random.choice` (FR-005).
- [~] T024 [US1] Implement coverage check logic: compare interval bounds against the **mean of the full UCI dataset array** (operational ground truth) (FR-003, Constitution Principle VII).
- [~] T025 [US1] Implement the main Monte Carlo loop: A large number of replications per configuration (dataset, n, confidence level) to ensure stable estimation (FR-003).
- [~] T026 [US1] Ensure all computations are CPU-only (no CUDA, no GPU libraries) (FR-004).
- [~] T027 [US1] Add logging for simulation progress and warnings for skipped configurations (Edge Cases).
- [ ] T028 [US1] Write raw coverage records to `data/processed/coverage_records.json` with schema: `dataset_id`, `sample_size`, `interval_lower`, `interval_upper`, `contains_mean` (FR-003).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Aggregation and Statistical Reporting (Priority: P2)

**Goal**: Aggregate coverage rates across multiple **UCI datasets** and sample sizes, apply Bonferroni correction for multiple comparisons, and frame findings as associational.

**Independent Test**: Feed pre-computed coverage data for a set of UCI datasets into the aggregation script and verify the output summary table includes Bonferroni-corrected p-values and explicit associational language.

### Implementation for User Story 2

- [~] T029 [US2] Implement aggregation logic to calculate mean deviation from nominal coverage across **multiple UCI datasets** (FR-006).
- [~] T030 [US2] Implement Bonferroni correction for family-wise error rate when testing significance across datasets (FR-006).
- [~] T031 [US2] Implement logic to flag "practically significant" deviations only if |deviation| > 1.0% (FR-011).
- [~] T032 [US2] Implement report generation that explicitly states findings are **associational** (FR-007).
- [ ] T033 [US2] Generate `outputs/aggregate_report.md` with summary tables and statistical tests, explicitly contrasting the scope of **multiple UCI datasets** against previous synthetic approaches to ensure clarity on generalization.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis on Confidence Thresholds (Priority: P3)

**Goal**: Perform a sensitivity analysis by sweeping the nominal confidence level across a range of standard thresholds to test robustness of coverage deviations.

**Independent Test**: Run `code/sensitivity.py` with fixed UCI dataset and sample size but varying confidence levels; verify output shows coverage rates for each level and identifies instability.

### Implementation for User Story 3

- [ ] T034 [US3] Implement confidence level sweep logic for {%, [deferred], [deferred]} (FR-008).
- [ ] T035 [US3] Integrate sweep into the simulation loop (reusing US1 engine).
- [ ] T036 [US3] Calculate and report non-coverage rate deviations for each confidence level, defining deviation as the difference between empirical non-coverage and nominal level, referencing FR-011's 1.0% deviation threshold for practical significance.
- [ ] T037 [US3] Generate `outputs/sensitivity_confidence.md` showing variation across levels.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Sensitivity Analysis on Sample Sizes (Priority: P3)

**Goal**: Explicitly compare coverage rates across sample sizes n=10, n=20, and n=30 to quantify the impact of sample size on interval validity.

**Independent Test**: Run `code/sensitivity.py` with fixed UCI dataset and confidence level but varying sample sizes; verify output quantifies the change in non-coverage rates between n=10 and n=30.

### Implementation for User Story 4

- [ ] T038 [US4] Implement sample size sweep logic for n=10, 20, 30 (FR-009).
- [ ] T039 [US4] Integrate sample size sweep into the simulation loop (reusing US1 engine).
- [ ] T040 [US4] Calculate and report the specific change in non-coverage rates between n=10 and n=30.
- [ ] T041 [US4] Generate `outputs/sensitivity_sample_size.md` quantifying the degradation of validity.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 Update documentation in `README.md` with usage examples and update `code/requirements.txt` (FR-001, FR-004).
- [ ] T043 Code cleanup and refactoring for readability
- [ ] T044 Profile simulation loop and optimize data loading to ensure runtime ≤ 6 hours on 2-core CPU (SC-002).
- [ ] T045 [P] Additional unit tests for edge cases (categorical variables, missing values) in `tests/unit/`
- [ ] T046 Verify memory usage ≤ 7 GB RAM during peak execution (SC-003)
- [ ] T047 Run quickstart.md validation
- [ ] T048 Ensure all output files (JSON, MD) contain content hashes and versioning info (Principle V)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 engine
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 engine

### Within Each User Story

- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T003, T004, T009-T012) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members

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
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3 & 4
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All simulations use **REAL UCI DATASETS** and the **mean of the full dataset array** as operational ground truth to satisfy FR-001, FR-010, and Constitution Principle VII. Sampling with replacement is used to approximate the super-population distribution for testing the t-interval's infinite population assumption.