# Tasks: The Impact of Text Message Tone on Perceived Emotional Support

**Input**: Design documents from `/specs/001-text-tone-emotional-support/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `specs/`)
- [X] T002 Initialize Python project with pinned dependencies in `code/requirements.txt` (pandas, numpy, scipy, statsmodels, linearmodels, pyyaml, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Define data model in `specs/001-text-tone-emotional-support/data-model.md` (Stimulus, Participant, Rating, AnalysisResult) and validate against spec/plan requirements.
- [ ] T005 Create data directory structure: `data/raw/`, `data/processed/`, `data/consent/`
- [ ] T006 [P] Define and validate JSON/YAML schemas in `specs/001-text-tone-emotional-support/contracts/` (stimulus.schema.yaml, rating.schema.yaml, analysis_result.schema.yaml)
- [X] T007 Create base configuration management for random seed pinning and path resolution in `code/config.py`
- [ ] T008 [P] Setup logging infrastructure by creating `code/logging_config.py` which configures a logger instance writing to `data/pipeline.log` to record pipeline steps and exclusion reasons (straight-lining, missing data). **Verification**: Run a dummy pipeline start/stop to ensure `data/pipeline.log` is created with entries.
- [X] T009 [P] Perform power analysis for LMM interaction effect (medium effect size, alpha=0.05, power=0.80) using simulation or `simr` and output `data/processed/power_analysis_results.json` containing the target sample size N. **Note**: This task MUST complete before Phase 3 begins.
- [ ] T009b [P] Document and publish power analysis results to `specs/001-text-tone-emotional-support/research.md` and generate `data/processed/power_curve.png` to verify N sufficiency. **Requirement**: Satisfies 'Verified Accuracy' gate.
- [ ] T037 [P] Benchmark pipeline duration by running the full pipeline with `--benchmark` flag (using mock data) and outputting timing metrics to `data/processed/benchmark.json`. **Requirement**: Output MUST include keys `total_duration_seconds`, `per_stage_duration`, and an assertion `total_duration < 21600` to verify SC-005. **Dependency**: Depends on T009 (Power Analysis) to set N, but uses mock data for speed.
- [X] T010 [US1] Contract test for stimulus data in `tests/contract/test_stimulus_schema.py` (validates `data/raw/stimuli.csv` produced by T013 against schema from T006; **MUST run after T013 completes**). <!-- FAILED: unspecified -->
- [ ] T011 [US1] Contract test for rating data in `tests/contract/test_rating_schema.py` (validates `data/raw/ratings.csv` produced by T014 against schema from T006; **MUST run after T014 completes**).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Stimulus Generation and Data Collection (Priority: P1) 🎯 MVP

**Goal**: Generate a controlled set of text message stimuli and collect human ratings for perceived emotional support (via simulation or real collection).

**Independent Test**: Verify that `01_generate_stimuli.py` produces a valid `data/raw/stimuli.csv` and `02_simulate_ratings.py` (or `04_collect_real_data.py`) produces a valid `data/raw/ratings.csv` with correct schema and no missing fields.

**⚠️ NOTE ON DATA PATHS**:
- **Mock Path (T014 + T014b)**: Generates synthetic data and mock consent records.
- **Real Path (T015 + T015b)**: Generates real data AND anonymized consent records in `data/consent/` as required by Constitution Principle VI.

### Implementation for User Story 1

- [X] T013 [US1] Implement factorial stimulus generator in `code/01_generate_stimuli.py`. **Requirement**: Generate a set of unique text message variants (targeting a sufficient number of stimuli by adjusting levels or base scenarios) to satisfy FR-006. Output `data/raw/stimuli.csv` with metadata linking features (emoji, punctuation, length) to base scenarios.
- [ ] T014 [US1] Implement mock Prolific data collection in `code/02_simulate_ratings.py` (generates `data/raw/ratings.csv` with P-IDs, stimulus IDs, relationship context, Likert scores; **reads target N from `data/processed/power_analysis_results.json` produced by T009**; simulates Prolific ID format validation). **Note**: This is for simulation/testing only.
- [ ] T014b [US1] Implement mock consent record generation in `code/02_simulate_ratings.py` (generates anonymized mock consent records in `data/consent/mock_consent_log.csv` for simulated participants; **executes alongside T014**). **Requirement**: Satisfies Constitution Principle VI for simulation path.
- [ ] T015 [US1] Implement real data collection pipeline in `code/04_collect_real_data.py` (handles survey deployment via Qualtrics/Prolific API, participant recruitment, and ingestion of real survey data; **must include CI-safe stubbing logic** to mock API calls for deterministic testing if external services are unavailable; handles API keys, rate limits, and failure modes). **Requirement**: Satisfies FR-002 for real human ratings; **verify artifact `data/raw/real_ratings.csv` exists with real P-ID format**. <!-- FAILED: unspecified -->
- [X] T015b [US1] Implement consent record generation in `code/04_collect_real_data.py` (generates anonymized consent records in `data/consent/` for real participants; **only executes if real data collection is active**). **Requirement**: Satisfies Constitution Principle VI.
- [X] T017 [US1] Implement validation logic to ensure relationship context (friend/acquaintance) is randomized and logged in `code/02_simulate_ratings.py` or `code/04_collect_real_data.py`. **Dependency**: MUST run before T016 to ensure data quality before cleaning.
- [ ] T016 [US1] Implement straight-lining detector in `code/03_clean_data.py` (flags participants with zero variance across the **full set of stimuli** as defined dynamically in `data/raw/stimuli.csv` generated by T013; **MUST validate count of stimuli against `data/raw/stimuli.csv` before flagging**; outputting exclusion flags to `data/processed/cleaning_log.csv`). **Verification**: Assert that participants with 0 variance are correctly flagged.
- [X] T012 [US1] Unit test for straight-lining detection logic in `tests/unit/test_data_cleaning.py` (tests logic implemented in T016; **MUST run after T016 completes**).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Stimuli and Ratings generated, Consent handling ready for real path)

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline (Priority: P2)

**Goal**: Execute Linear Mixed-Effects Models (LMM) to test for interaction effects between relationship type and cue intensity.

**Independent Test**: Verify that `04_run_lmm.py` produces `data/processed/analysis_results.json` with fixed effect estimates, p-values, and Tukey-corrected post-hoc results without GPU usage.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for LMM model construction with mock data in `tests/unit/test_analysis_logic.py`
- [ ] T019 [P] [US2] Integration test for full LMM pipeline execution in `tests/integration/test_lmm_pipeline.py`

### Implementation for User Story 2

- [~] T020 [US2] Implement data preprocessing step in `code/04_run_lmm.py` to handle listwise deletion of excluded participants (**reads exclusion flags from `data/processed/cleaning_log.csv` produced by T016**)
- [X] T021 [US2] Implement primary LMM script in `code/04_run_lmm.py` using `statsmodels` or `linearmodels` (Random intercepts for Participant and Stimulus)
- [X] T022 [US2] Implement Satterthwaite approximation for degrees of freedom and p-value calculation in `code/04_run_lmm.py`
- [X] T023 [US2] Implement validation check in `tests/unit/test_analysis_validation.py` that asserts the LMM model summary includes a variance component for Stimulus; **if variance is negligible (< 0.001), the script MUST FAIL (exit code 1), log the failure reason and variance value to `data/processed/analysis_validation_log.json`, AND append a structured exclusion record to `data/processed/cleaning_log.csv`** to satisfy Constitution Principle IV (Single Source of Truth) and SC-004.
- [X] T024 [US2] Implement Tukey-corrected post-hoc pairwise comparisons in `code/04_run_lmm.py` (triggered if interaction p < 0.05)
- [X] T025 [US2] Implement result serialization to `data/processed/analysis_results.json` (JSON format for single source of truth)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Analysis results generated)

---

## Phase 5: User Story 3 - Methodological Robustness and Sensitivity Reporting (Priority: P3)

**Goal**: Perform sensitivity analysis on "Cue Intensity" definitions using structural rules and report robustness of findings.

**Independent Test**: Verify that `05_sensitivity_analysis.py` re-runs LMM with Alternative cue definitions and outputs a stability report in `data/processed/sensitivity_report.csv`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for alternative cue definition logic in `tests/unit/test_sensitivity_logic.py`

### Implementation for User Story 3

- [ ] T027 [US3] Define three alternative **structural definitions** of "Cue Intensity" (e.g., Conjunctive: High Emoji AND High Punct; Disjunctive: High Emoji OR High Punct; Threshold-based) and document them in `data/processed/sensitivity_definitions.json` with a specific schema. **Note**: Simple re-weighting is excluded to align with FR-005 and Plan.md.
- [ ] T027b [US3] Define and document the explicit **mathematical formulas and weighting logic** for the multivariate operationalizations in `data/processed/sensitivity_formulas.md`. **Requirement**: Must specify exact formulas used for re-weighting (e.g., weighted sum of normalized features) to satisfy FR-005 and SC-002.
- [ ] T028 [US3] Implement sensitivity analysis engine in `code/05_sensitivity_analysis.py` (**reads operationalization definitions from `data/processed/sensitivity_definitions.json` produced by T027**; **reads formulas from `data/processed/sensitivity_formulas.json` produced by T027b**; **reads primary results from `data/processed/analysis_results.json` produced by T025**; **implements multivariate weighting logic and re-calculates LMM** for each definition).
- [ ] T029 [US3] Implement re-execution of LMM for each alternative definition in `code/05_sensitivity_analysis.py` (reusing Tukey logic from T024).
- [ ] T030 [US3] Implement stability metric calculation (variation in F-statistics and p-values across definitions) in `code/05_sensitivity_analysis.py`
- [ ] T031 [US3] Generate sensitivity report CSV in `data/processed/sensitivity_report.csv`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `specs/001-text-tone-emotional-support/quickstart.md`
- [ ] T034 [P] Run linting and formatting checks on `code/` to ensure 0 errors.
- [ ] T035 [P] Run full pipeline end-to-end test with fixed seed to verify reproducibility
- [ ] T036 [P] Additional unit tests for edge cases (missing data handling, randomization failure) in `tests/unit/`
- [ ] T038 [P] Run quickstart.md validation by executing `pytest tests/integration/test_quickstart.py` and verifying exit code 0.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion (T009 must complete before Phase 3)
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 (requires `data/raw/ratings.csv` and `data/raw/stimuli.csv`)
- **User Story 3 (P3)**: Depends on User Story 2 (requires primary analysis results to test robustness)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Generators before Simulators
- Simulators before Analyzers
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **except T010/T011 which depend on T013/T014**
- Tests for different user stories can run in parallel
- Within US1, stimulus generation and rating simulation can run in parallel once data schemas are defined

---

## Parallel Example: User Story 1

```bash
# Launch schema validation and generator in parallel (Phase 3):
Task: "Contract test for stimulus data in tests/contract/test_stimulus_schema.py" (T010, after T013)
Task: "Implement factorial stimulus generator in code/01_generate_stimuli.py" (T013)

# Launch rating simulation and cleaning logic in parallel:
Task: "Implement mock Prolific data collection in code/02_simulate_ratings.py" (T014)
Task: "Implement straight-lining detector in code/03_clean_data.py" (T016, after T013 and T014)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Generate stimuli and ratings)
4. **STOP and VALIDATE**: Test US1 independently (verify data schemas)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Analysis results)
4. Add User Story 3 → Test independently → Deploy/Demo (Sensitivity report)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (LMM Analysis) - *Wait for US1 data*
 - Developer C: User Story 3 (Sensitivity) - *Wait for US2 results*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except T010/T011 which depend on T013/T014)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Consent Records**: T014b (Mock) generates `data/consent/mock_consent_log.csv`. T015b (Real) generates `data/consent/real_consent_records/`.