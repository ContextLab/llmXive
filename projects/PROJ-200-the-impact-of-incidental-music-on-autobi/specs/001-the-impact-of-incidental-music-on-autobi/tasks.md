# Tasks: The Impact of Incidental Music on Autobiographical Memory Retrieval

**Input**: Design documents from `/specs/001-impact-of-incidental-music/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` dependencies (`pandas`, `numpy`, `scikit-learn`, `statsmodels`, `python-Levenshtein`, `pyyaml`, `tqdm`, `scipy`)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `contracts/dataset.schema.yaml` defining Track, CohortListen, MemoryCue, and AggregatedMetric schemas
- [X] T005 Create `contracts/output.schema.yaml` for regression results and sensitivity analysis outputs
- [X] T006 [P] Implement `code/config.py` with paths, thresholds (Levenshtein ≤ 4), seeds, and fallback flags
- [X] T007 Setup `data/raw/`, `data/processed/`, and `data/final/` directories with `.gitkeep`
- [X] T008 Implement `code/__init__.py` and basic logging configuration in `code/utils.py`
- [ ] T009 Create `state.yaml` mechanism for checksum tracking of derived files

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Spec Finalization (CRITICAL PREREQUISITE)

**Purpose**: Update spec.md to resolve contradictions between the implementation plan and original requirements before code generation.

**⚠️ CRITICAL**: All tasks in Phases 3, 4, and 5 depend on the successful completion of these spec updates. The spec must reflect the "User-Track Pair" unit of analysis and the corrected statistical methods.

- [ ] T016a [SPEC UPDATE] Update `spec.md` FR-001 to define `residualized_exposure_score` as the primary predictor, including the regression formula (adolescent_exposure ~ overall_popularity).
- [ ] T016b [SPEC UPDATE] Update `spec.md` FR-005 to change the unit of analysis from "individual memory instance" to "User-Track Pair" and update the model formula to `mean_vividness ~ residualized_exposure + popularity + (1|user_id)`.
- [ ] T016c [SPEC UPDATE] Update `spec.md` FR-007 to explicitly define the permutation test as a **block-permutation** on **User-Track Pair** rows (shuffling exposure scores while preserving the User-Track grouping structure), replacing the invalid "shuffling memory outcomes" definition.
- [~] T016d [SPEC UPDATE] Update `spec.md` FR-004 to change aggregation from "per matched track" to "per User-Track Pair".
- [~] T016e [SPEC UPDATE] Update `spec.md` SC-004 to explicitly state: "Log unmatched cues and proceed with a warning if the match rate is < 80%; do not halt the pipeline."
- [~] T016f [SPEC UPDATE] Update `spec.md` FR-006 to explicitly mandate **re-aggregation** of data to User-Track pairs for each sensitivity threshold (2, 4, 6).
- [~] T016g [SPEC UPDATE] Update `spec.md` Edge Cases section to explicitly state: "The fallback check for missing birth years (>50%) MUST be performed BEFORE applying the Minimum Listen Threshold filter to prevent empty datasets."

**Checkpoint**: Spec is now consistent with the Plan and ready for implementation.

---

## Phase 3: User Story 1 - Data Ingestion and Cohort Exposure Scoring (Priority: P1) 🎯 MVP

**Goal**: Ingest MSD and AMT data, filter for valid birth years, and compute the `adolescent_exposure_score` and `residualized_exposure_score`.

**Independent Test**: Run ingestion on a small synthetic subset; verify output CSV has `adolescent_exposure_score` (0.0-1.0), excludes records without `birth_year`, and applies the minimum listen threshold.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [US1] Unit test for birth year filtering logic in `tests/unit/test_ingestion.py`
- [X] T011 [US1] Unit test for exposure score calculation (0 listens = 0.0) in `tests/unit/test_ingestion.py`
- [X] T012 [US1] Unit test for fallback "global exposure" trigger when >50% missing birth years in `tests/unit/test_ingestion.py` <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data_ingestion.py` function `download_datasets` to download/verify MSD and AMT datasets from canonical URLs
- [X] T013a [US1] Implement `code/data_ingestion.py` function `filter_cohort` to filter MSD logs for `birth_year` presence and calculate adolescent window (birth_year + early adolescence to late adolescence)
- [X] T023 [US1] Implement `code/data_ingestion.py` function `handle_fallback` for FR-008 (Global Exposure metric) if birth year data is insufficient (>50% missing). **ORDERING**: This check MUST run before any frequency filtering.
- [X] T015 [US1] Implement `code/data_ingestion.py` function `apply_frequency_threshold` to filter tracks with < 10 total listens. **ORDERING**: This runs AFTER the fallback check (T023).
- [X] T014 [US1] Implement `code/data_ingestion.py` function `calculate_ratio_score` to compute `adolescent_exposure_score` (adolescent listens / total valid listens) per track
- [X] T016 [US1] Implement `code/data_ingestion.py` function `calculate_residualized_score` to compute `residualized_exposure_score` by running OLS regression of `adolescent_exposure_score` ~ `overall_popularity_score` and extracting residuals. Formula: `residuals = observed - predicted`.
- [ ] T018 [US1] Generate `data/processed/ingested_cohort.parquet` with checksum and update `state.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cue Matching and Memory Attribute Aggregation (Priority: P2)

**Goal**: Parse AMT free-text cues, match to MSD tracks via fuzzy string matching (Levenshtein ≤ 4), and aggregate vividness/valence per User-Track pair.

**Independent Test**: Provide a small set of AMT cues with known MSD titles; verify matching accuracy and correct aggregation of mean vividness/valence.

### Tests for User Story 2

- [X] T019 [US2] Unit test for text normalization (lowercase, remove punctuation) in `tests/unit/test_matching.py`
- [X] T020 [US2] Unit test for fuzzy matching logic (Levenshtein distance ≤ 4) in `tests/unit/test_matching.py`
- [X] T021 [US2] Unit test for aggregation logic (mean vividness/valence per User-Track) in `tests/unit/test_matching.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/cue_matching.py` function `normalize_cues` to normalize AMT cues and load MSD track titles into a searchable index
- [X] T023 [US2] Implement `code/cue_matching.py` function `match_cues` to perform fuzzy matching with Levenshtein distance ≤ 4 and log unmatched cues
- [X] T024 [US2] Implement `code/cue_matching.py` function `resolve_collisions` to resolve ambiguous matches (same title/artist) and log collisions
- [X] T025 [US2] Implement `code/aggregation.py` function `join_exposure_data` to join matched cues with exposure data (Track-level exposure joined to User-Track pairs)
- [X] T026 [US2] Implement `code/aggregation.py` function `aggregate_to_user_track` to aggregate data to **User-Track Pair** level (mean vividness, mean valence) as per plan.md update
- [X] T027 [US2] Implement `code/aggregation.py` function `filter_zero_variance` to filter out tracks with high exposure but no memory cues
- [X] T036 [US2] [P] Implement `code/aggregation.py` function `enforce_match_rate` to verify SC-004 (Match Rate ≥ 80%); **LOG WARNING** and proceed if threshold is missed, do NOT raise exception. This task MUST run before any modeling tasks.
- [ ] T029 [US2] Generate `data/processed/user_track_pairs.parquet` with checksum and update `state.yaml`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling and Hypothesis Testing (Priority: P3)

**Goal**: Fit linear mixed-effects models on User-Track pairs, run sensitivity analysis, and perform permutation tests.

**Independent Test**: Run analysis on the aggregated dataset; verify regression summary includes p-values, sensitivity table shows stability across thresholds, and permutation test confirms significance.

### Tests for User Story 3

- [X] T030 [US3] Unit test for model formula construction in `tests/unit/test_modeling.py`
- [X] T031 [US3] Unit test for sensitivity analysis loop (thresholds, 4, 6) in `tests/unit/test_modeling.py`
- [X] T032 [US3] Unit test for permutation test logic (block-permutation) in `tests/unit/test_modeling.py`

### Implementation for User Story 3

- [X] T033 [US3] Implement `code/modeling.py` function `fit_mixed_model` to fit `statsmodels` MixedLM: `mean_vividness ~ residualized_exposure + popularity + (1|user_id)` on **User-Track pairs**
- [X] T034 [US3] Implement `code/modeling.py` function `fit_valence_model` to fit the same model for `mean_valence`
- [X] T035 [US3] Implement `code/modeling.py` function `check_collinearity` to calculate Variance Inflation Factor (VIF) and check for multicollinearity (VIF > 5)
- [X] T044 [US3] Implement `code/modeling.py` function `run_sensitivity_analysis` to re-match, **re-aggregate to User-Track pairs**, and re-model with Levenshtein thresholds 2 and 6.
- [X] T045 [US3] Implement `code/modeling.py` function `run_permutation_test` to perform a **block-permutation** on the **User-Track Pair** dataset. Shuffle the `residualized_exposure_score` values among tracks while preserving the User-Track grouping structure (i.e., keep the mean_vividness and user_id intact for each pair, shuffle the exposure score assigned to the pair). Run a sufficient number of iterations to establish a null distribution. Compare observed statistic to null distribution.
- [ ] T038 [US3] Generate `data/final/regression_summary.csv` containing coefficients, SEs, p-values, and VIFs
- [ ] T039 [US3] Generate `data/final/sensitivity_analysis.csv` and `data/final/permutation_results.csv`
- [~] T040 [US3] Generate diagnostic plots (residual checks, QQ plots) and save to `data/final/plots/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T041 [P] Documentation updates in `README.md` and `code/` docstrings
- [X] T042 Code cleanup and refactoring of `code/main.py` orchestration script
- [~] T043 Performance optimization: ensure chunking is used if memory > 5GB during ingestion
- [X] T044 [P] Add integration test in `tests/integration/test_pipeline.py` to run full flow on synthetic data
- [~] T045 Security hardening: ensure no PII leaks in logs or output files
- [ ] T046 Run `quickstart.md` validation to ensure pipeline runs end-to-end within 6 hours

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Spec Finalization (Phase 2.5)**: Depends on Foundational - BLOCKS all User Stories
- **User Stories (Phase 3+)**: All depend on Foundational + Spec Finalization phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational + Spec Finalization (Phase 2.5) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational + Spec Finalization (Phase 2.5) - Depends on US1 output (exposure scores)
- **User Story 3 (P3)**: Can start after Foundational + Spec Finalization (Phase 2.5) - Depends on US2 output (User-Track pairs)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational + Spec Finalization phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for birth year filtering logic in tests/unit/test_ingestion.py"
Task: "Unit test for exposure score calculation in tests/unit/test_ingestion.py"
Task: "Unit test for fallback 'global exposure' trigger in tests/unit/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_ingestion.py function download_datasets"
Task: "Implement code/data_ingestion.py function filter_cohort"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2.5: Spec Finalization (CRITICAL - ensures spec matches plan)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational + Spec Finalization → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + Spec Finalization together
2. Once Foundational + Spec Finalization is done:
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
- **Constraint**: All data processing must run on CPU-only CI (no GPU, no 8-bit models)
- **Constraint**: All datasets must be fetched from real, verified URLs (no fabrication)
- **Constraint**: Spec updates (Phase 2.5) are mandatory prerequisites for implementation.