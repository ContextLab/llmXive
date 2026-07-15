# Tasks: Statistical Analysis of Publicly Available Election Poll Aggregates

**Input**: Design documents from `/specs/001-statistical-poll-aggregation/`
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

- [X] T001a [P] Create `src/` directory (root)
- [X] T001b [P] Create `tests/` directory (root)
- [X] T001c [P] Create `data/` directory (root)
- [X] T001d [P] Create `state/` directory (root)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002a [P] Create `requirements.txt` at repository root with pinned dependencies (pandas, numpy, scipy, pymc, arviz, requests, pyyaml, statsmodels, pytest)
- [ ] T002b [P] Install dependencies from `requirements.txt` in a virtual environment <!-- FAILED: unspecified -->
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [ ] T004 Setup data directory structure: `data/raw/`, `data/processed/`, `state/projects/`
- [ ] T005 [P] Implement configuration management in `src/utils/config.py` (seed pinning, path resolution)
- [ ] T006 [P] Implement logging infrastructure in `src/utils/logging.py`
- [ ] T007 Create base data validation schemas in `specs/001-statistical-poll-aggregation/contracts/` (dataset.schema.yaml, forecast.schema.yaml)
- [~] T008 Implement state management utility to compute SHA-256 hashes and update `state/projects/PROJ-206-*.yaml` on derived artifact creation <!-- SKIPPED: YAML+regex parse failed (while parsing a block mapping
 in "<unicode string>", line 1, column 1:
 def main():
 ^
expected <block end>, but found '<scalar>'
 in "<unicode string>", line 2, column 13:
 """
 ^) -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Ingest raw poll data from FiveThirtyEight, harmonize dates, calculate historical RMSE weights, and enforce data sufficiency checks. **Note**: RCP is excluded per Plan's 'Verified Accuracy' principle (see T009b).

**Independent Test**: Verify `src/data/download.py` and `src/data/harmonize.py` produce a single `data/processed/poll_data_cleaned.csv` with columns `date`, `pollster`, `vote_share`, `sample_size`, `historical_rmse` and no duplicate dates per pollster.

### Implementation for User Story 1

- [X] T009a [P] [US1] Implement `src/data/download.py` to fetch FiveThirtyEight poll CSVs from `https://projects.fivethirtyeight.com/polls/` and election outcomes from MIT Election Data and Science Lab (MEDSL) or FEC. **Do not** attempt to fetch RealClearPolitics (RCP) data.
- [X] T009b [P] [US1] Implement `src/data/download.py` logic to log a "Source Excluded" warning for RCP, explicitly citing the Plan's 'Verified Accuracy' principle and FR-001 deviation. Document this exclusion in `research.md` as a sanctioned architectural exception.
- [ ] T010 [P] [US1] Implement `src/data/harmonize.py` to parse raw CSVs, unify date formats, and bin data into weekly intervals.
- [ ] T011 [US1] Implement `src/data/weights.py` to calculate pollster-specific historical RMSE using out-of-sample data (strict temporal split: weights for cycle T use only cycles < T).
- [ ] T012 [US1] Add logic in `src/data/weights.py` to assign default median weight for pollsters with no history and prevent division by zero.
- [ ] T013 [US1] Implement FR-008: Data sufficiency check in `src/data/harmonize.py` to halt with warning if <5 polls in the 30 days preceding the election day or <3 distinct cycles.
- [ ] T014 [US1] Implement FR-010: Global poll count check in `src/data/harmonize.py` to halt with error if total count across all ingested election cycles is <500.
- [ ] T015 [US1] Implement system-level blocking gate in `src/main.py` to check for data sufficiency flags (generated by T013/T014) before executing downstream tasks (T016+), ensuring the entire pipeline halts if data is insufficient.
- [~] T016 [US1] Integrate hash generation in `src/data/` scripts to update `state/projects/PROJ-206-*.yaml` upon writing `poll_data_cleaned.csv` and `historical_weights.csv`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Frequentist Aggregation Execution (Priority: P2)

**Goal**: Compute point forecasts using Simple Unweighted Averaging and Accuracy-Weighted Averaging.

**Independent Test**: Verify `src/models/frequentist.py` produces `data/processed/frequentist_forecasts.csv` with `simple_avg_forecast` and `weighted_avg_forecast` columns that match the arithmetic mean and inverse-RMSE weighted mean respectively.

### Implementation for User Story 2

- [ ] T017 [P] [US2] Implement `src/models/frequentist.py` function `simple_average()` to calculate arithmetic mean of vote shares per weekly bin (FR-003).
- [ ] T018 [P] [US2] Implement `src/models/frequentist.py` function `weighted_average()` to calculate inverse-RMSE weighted mean, normalizing weights to sum to 1.0 (FR-004).
- [ ] T019 [US2] Implement evaluation logic in `src/evaluation/metrics.py` to compute RMSE and MAE for both frequentist methods against actual election outcomes (SC-001).
- [X] T020 [US2] Add unit tests in `tests/unit/test_frequentist.py` verifying edge cases (e.g., single poll, missing weights).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Bayesian Hierarchical Modeling and Evaluation (Priority: P3)

**Goal**: Fit a Bayesian hierarchical model, generate posterior distributions, and perform rigorous statistical comparison.

**Independent Test**: Verify `src/models/bayesian.py` completes MCMC sampling without divergence (R-hat ≤ 1.05), produces 95% credible intervals with ≥90% coverage, and outputs a Diebold-Mariano comparison matrix.

### Implementation for User Story 3

- [ ] T021 [P] [US3] Implement `src/models/bayesian.py` with a **Random Walk** hierarchical model: latent weekly preference θₜ ~ Normal(θₜ₋₁, σₜ²) and observation noise τᵢ². **Sanctioned Exception**: This task implements the Spec's FR-005 Random Walk requirement, overriding the Plan's 'Static Parameter' decision. Document this architectural deviation in `research.md` as a hypothesis test (Random Walk vs. Static). <!-- FAILED: unspecified -->
- [~] T022 [P] [US3] Configure PyMC NUTS sampler for CPU-only execution (no GPU/CUDA) with appropriate tuning steps and random seeds.
- [ ] T023 [US3] Implement convergence checks in `src/models/bayesian.py` to halt and report error if R-hat > 1.05.
- [ ] T024 [US3] Implement `src/evaluation/metrics.py` function `calculate_coverage()` to verify credible interval coverage rate against outcomes (FR-009, SC-002).
- [ ] T025 [US3] Implement binomial test in `src/evaluation/metrics.py` against the null hypothesis (p0=0.95) for coverage reliability, using significance level **alpha=0.05 (Wikipedia: One- and two-tailed tests, https://en.wikipedia.org/wiki/One-_and_two-tailed_tests)** (as required by SC-002). Note: The '[deferred]' tag in the Spec refers to the research phase determination of this value, which is now established as 0.95 for 95% CI.
- [ ] T026 [US3] Implement `src/evaluation/meta_analysis.py` to perform pairwise **Diebold-Mariano tests** with **Westfall-Young correction** (FR-006, SC-003). Use **1000 permutations** with a **step-down max-t** strategy. If `statsmodels.stats.multitest` does not support Westfall-Young directly, implement a custom permutation-based correction. **Sanctioned Exception**: This task implements the Spec's FR-006 DM test, overriding the Plan's rejection of DM for static forecasts. Document this architectural deviation in `research.md`. This is the **sole** implementation of SC-003.
- [~] T028 [US3] Add logic to frame findings as "predictive accuracy" and "associational uncertainty" in output reports (FR-007).
- [X] T029 [US3] Implement unit tests in `tests/unit/test_bayesian.py` for model convergence and synthetic data edge cases.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [~] T030 [P] [Polish] Generate `research.md` documenting mathematical formulations for all three methods (Random Walk Bayesian, Simple Avg, Weighted Avg) and explicitly documenting the sanctioned architectural exceptions (T021, T026, T009b).
- [~] T031 [P] [Polish] Create `quickstart.md` with instructions to run the full pipeline on CPU.
- [X] T032 [Polish] Run end-to-end integration test in `tests/integration/test_pipeline.py` to verify full data flow from download to final metrics.
- [~] T033 [Polish] Verify all artifacts have valid checksums in `state/projects/` and no manual data fabrication occurred.
- [~] T034 [P] [Polish] Documentation updates in `README.md` summarizing the comparative results and limitations.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data output and US2 metrics for comparison

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
- **Critical Constraint**: All tasks must run on CPU-only (a limited number of cores, constrained RAM). No GPU, no 8-bit/4-bit quantization, no large LLMs.
- **Data Integrity**: No fabrication of data. All inputs must come from real, verified sources (FiveThirtyEight, official election records).
- **Spec vs Plan Alignment**: Where the Spec mandates specific methods (RCP, Random Walk, DM Test) and the Plan excludes or modifies them, tasks implement the Spec's mandate while adding a 'Sanctioned Architectural Exception' note to document the deviation in `research.md`. The Spec's requirements take precedence for the implementation, with the Plan's concerns addressed as documented risks/hypotheses.