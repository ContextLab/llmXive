# Tasks: Statistical Analysis of Speedrun Data

**Input**: Design documents from `/specs/001-speedrun-statistics/`
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

- [X] T001 [P] Initialize project directory structure: Create `data/raw`, `data/processed`, `data/checkpoints`, `code/scripts`, `code/tests`, `contracts`, `paper`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `contracts/run_record.schema.yaml` defining RunRecord entity (run_time_seconds, runner_id, attempt_number, category, submission_date, game_id)
- [X] T005 [P] Create `contracts/distribution_fit.schema.yaml` defining DistributionFit entity (game_id, distribution_family, parameters, KS_D, KS_pvalue, AIC)
- [X] T006 Create `code/config.yaml` with:
 - `games`: List of target game IDs (e.g., `["super-mario-64", "zelda-oot"]`)
 - `min_sample_size`: Integer (default 100)
 - `salt`: String (project-specific salt for runner_id hashing)
 - `effect_size_assumptions`: Float (Cohen's d for power analysis)
- [X] T006b [P] Implement `code/scripts/load_game_metadata.py` to fetch/load game difficulty labels from external sources (Machin et al.) and save to `data/processed/game_metadata.csv` (FR-006, Key Entities)
 - *Output*: `data/processed/game_metadata.csv` with columns: `game_id`, `game_name`, `difficulty_label`, `active_runners_count`
- [X] T007 Implement `code/scripts/hash_artifacts.py` to compute SHA-256 checksums for all `data/` files (Constitution Principle V)
- [X] T008a Implement `code/scripts/utils/checkpoint.py` to save/load intermediate state (JSON) for resumption on CI timeout
- [X] T008b Implement `code/scripts/utils/bonferroni.py` to apply Bonferroni correction to a list of p-values with a configurable total test count
- [X] T009 [P] Setup `code/tests/conftest.py` with fixtures for mock speedrun.com API responses and sample data

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download, clean, and engineer features for speedrun data to ensure ≥95% completeness and compute runner experience metrics.

**Independent Test**: Verify script outputs a CSV with run times, runner IDs, attempt numbers, categories, and dates; duplicates removed; ≥95% record retention; per-runner metrics computed.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/scripts/fetch_data.py` to download raw JSON from speedrun.com API for 10–15 games (FR-001)
 - *Note*: Must handle pagination and save raw JSON to `data/raw/`
- [X] T013a [US1] Implement `code/scripts/preprocess.py` to:
 - Remove duplicates and filter incomplete runs (FR-002)
 - Compute `total_prior_runs` and `time_since_first_run_days` for every record (FR-003)
 - Validate output against `contracts/run_record.schema.yaml`
 - Save to `data/processed/run_records.csv`
- [ ] T013b [US1] Implement runner_id anonymization in `code/scripts/preprocess.py` using SHA-256 with project-specific salt (from `config.yaml`) to satisfy Constitution Principle III while preserving unique grouping for mixed-effects models (FR-006)
 - *Note*: The salted hash must be deterministic to allow grouping by `RunnerID` in T027.
 - *Output*: `runner_id` column in `run_records.csv` contains the salted hash.
- [ ] T013c [US1] Implement `code/scripts/preprocess.py` to generate `RunnerProfile` entity:
 - Aggregate per-runner statistics: `total_prior_runs`, `time_since_first_run_days`, `games_played_count`
 - Save to `data/processed/runner_profiles.csv` (Key Entities: RunnerProfile)
- [ ] T014 [US1] Implement lagged `competitive_pressure` calculation in `code/scripts/preprocess.py` (Plan: Phase 0 Step 3, FR-006)
 - *Note*: Must run AFTER T013c (full game data aggregation) to ensure valid 30-day rolling windows.
 - *Trigger*: Calculate `active_runners_count` in 30-day window prior to run date.
 - *Output*: Add column `lagged_competitive_pressure` to `data/processed/run_records.csv`.
 - *Dependency*: T014 must complete before T027 (US3) can run.
- [ ] T015 [US1] Integrate checkpoint mechanism into `fetch_data.py` and `preprocess.py` to save state after each game (FR-012, Plan: Phase 0 Step 5)
 - *Note*: Must handle -hour limit.
- [ ] T016 [US1] Implement robust data fetching with retry, caching, and logging in `code/scripts/fetch_data.py` (Plan: Risks & Mitigations, SC-005)
 - *Note*: Consolidates retry, caching, and logging logic into a single atomic implementation.
- [ ] T017 [US1] Add logging for data acquisition and preprocessing steps in `code/scripts/fetch_data.py` and `preprocess.py` (Plan: Risks & Mitigations, SC-005)
 - *Note*: Must ensure data acquisition completes within 6-hour limit.

### Tests for User Story 1 (Mandatory per Spec) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. Note: Tests must run AFTER implementation tasks.

- [ ] T010 [US1] Contract test for `run_record.schema.yaml` validation in `code/tests/test_preprocess.py`
 - *Note*: Depends on T004 (schema) and T012/T013 (data). Cannot run in parallel with T012/T013.
- [ ] T011 [US1] Integration test for data completeness (≥95% retention) and duplicate removal in `code/tests/test_fetch.py`
 - *Note*: Depends on T012 (fetch) and T013 (preprocess). Cannot run in parallel with T012/T013.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Distribution Fitting and Goodness-of-Fit Testing (Priority: P2)

**Goal**: Fit parametric distributions (log-normal, Weibull, gamma) to speedrun times and evaluate them with KS tests and AIC.

**Independent Test**: Verify script outputs max-likelihood estimates, KS statistics, and AIC; flags rejected distributions; selects best fit by AIC.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/scripts/fit_distributions.py` to:
 - Fit log-normal, Weibull, and gamma distributions using MLE (FR-004)
 - Perform KS tests and calculate AIC for each (FR-004)
 - Flag distributions with p < 0.05 and recommend next-best (FR-005)
 - Filter out games with <100 runs (Edge Case: Low-sample)
 - Read `min_sample_size` from `code/config.yaml` (T006)
 - Save results to `data/processed/distribution_fits.csv`
- [ ] T021 [US2] Implement logic to handle Anderson-Darling test for n < 100 (Spec: Edge Cases)
 - *Trigger*: If `n < 100`, use `scipy.stats.anderson` for descriptive purposes ONLY (no p-value threshold/rejection).
 - *Note*: Games with n < 100 are excluded from parametric fitting (KS test) but may be reported with Anderson-Darling for descriptive shape analysis only.
 - *Output*: Add descriptive statistics for excluded games to `data/processed/distribution_fits.csv`.
- [ ] T023 [US2] Validate `distribution_fits.csv` against `contracts/distribution_fit.schema.yaml`
- [ ] T024 [US2] Add checkpointing after each game's distribution fitting (Plan: Phase 1 Step 5)

### Tests for User Story 2 (Mandatory per Spec) ⚠️

- [ ] T018 [P] [US2] Contract test for `distribution_fit.schema.yaml` validation in `code/tests/test_models.py`
- [ ] T019 [P] [US2] Integration test for distribution fitting on a single game (KS p ≥ 0.05 check) in `code/tests/test_models.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Learning-Curve Modeling with Mixed-Effects Regression (Priority: P3)

**Goal**: Fit hierarchical mixed-effects models to quantify how experience and external factors modulate performance improvement.

**Independent Test**: Verify model convergence, interpretable coefficients, p-values, VIF checks, and associational framing.

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/scripts/fit_mixed_effects.py` to:
 - Fit `log(Time) ~ log(Attempt Number) + Game Difficulty + Lagged Pressure + (1 | RunnerID)` (FR-006, Plan: Complexity Tracking)
 - *Note*: Exclude `total_prior_runs` from fixed effects to avoid collinearity (Plan: Complexity Tracking)
 - Compute VIFs and flag if > 5 (FR-011)
 - Perform likelihood-ratio tests for nested models (FR-007)
 - *Note*: Apply Bonferroni correction in T038 (Phase N) using global test count.
 - Save results to `data/processed/model_results.csv`
- [ ] T028 [US3] Implement power analysis check for game-level predictors (N=10–15) and generate report statement (FR-009)
 - *Method*: Use G*Power parameters with effect size assumptions from `config.yaml` (T006).
 - *Input*: Model coefficients and sample sizes from `data/processed/model_results.csv`.
 - *Output*: Append section 'Power Analysis' to `paper/draft.md` with explicit power limitations.
- [ ] T029 [US3] Implement `code/scripts/generate_report.py` to:
 - Aggregate results from all phases
 - Enforce associational language framing (FR-010, SC-006)
 - Invoke Reference-Validator Agent for citations (Plan: Phase 2 Step 5)
 - Generate `paper/draft.md`
- [ ] T030 [US3] Add logic to exclude games without external difficulty labels from difficulty-modulation analysis (Edge Case: Missing labels)
 - *Source*: Check `data/processed/game_metadata.csv` (T006b) for difficulty labels.
 - *Output*: Log excluded games to `data/processed/excluded_games.log`.
- [ ] T031 [US3] Add checkpointing after model fitting for resumption (Plan: Phase 2 Step 5)

### Tests for User Story 3 (Mandatory per Spec) ⚠️

- [ ] T025 [P] [US3] Contract test for model output structure in `code/tests/test_models.py`
- [ ] T026 [P] [US3] Integration test for model convergence and VIF < 5 check in `code/tests/test_models.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates: Add `quickstart.md` with data fetching and analysis instructions
- [ ] T033a Code cleanup and refactoring: Refactor pagination logic in `fetch_data.py` for readability
- [ ] T033b Code cleanup and refactoring: Extract function `calculate_lagged_pressure` from `preprocess.py`
- [ ] T034 Performance optimization: Ensure memory usage < 7 GB and disk < 14 GB (SC-005)
 - *Strategy*: If data exceeds limits, implement downsampling of runners (e.g., keep top [deferred] by activity) before model fitting.
- [ ] T035 [P] Additional unit tests for edge cases (e.g., empty datasets, API rate limits)
- [ ] T038 [P] Apply Global Bonferroni Correction: Aggregate total hypothesis test count from US2 (T020) and US3 (T027) and apply correction to all p-values using `utils/bonferroni.py` (T008b) (FR-008, SC-004)
 - *Input*: All p-values from `data/processed/distribution_fits.csv` and `data/processed/model_results.csv`.
 - *Output*: Updated p-values in final report (`paper/draft.md`) and corrected result files.
- [ ] T036 Run `hash_artifacts.py` to finalize state and checksums (Constitution Principle V)
- [ ] T037 Run quickstart.md validation to ensure all steps execute correctly on CI

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires clean data from US1 but independent of US2 results
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires clean data from US1; independent of US2 results
 - *Note*: US3 requires `data/processed/run_records.csv` (produced by US1)
 - *Note*: US3 requires `lagged_competitive_pressure` column from T014 (US1). T014 must complete before T027.
 - *Note*: US3 requires `data/processed/game_metadata.csv` (produced by T006b).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Contracts before Services/Scripts
- Core implementation before integration
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
# Launch all models for User Story 1 together:
Task: "Create run_record.schema.yaml in contracts/"
Task: "Create distribution_fit.schema.yaml in contracts/"

# Note: Tests T010 and T011 cannot run in parallel with T012 (fetch) due to dependencies.
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Distribution)
 - Developer C: User Story 3 (Modeling)
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
- **CRITICAL**: All statistical claims must be associational; no causal language (FR-010, SC-006).
- **CRITICAL**: Ensure all tasks are CPU-tractable (no GPU, no large models) per SC-005.
- **CRITICAL**: Bonferroni correction (FR-008) is applied globally in T038 after all tests are complete.