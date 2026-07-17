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

- [ ] T004 Create `data-model.md` in `specs/001-text-tone-emotional-support/` defining entities (Stimulus, Participant, Rating, AnalysisResult) and their relationships as required by the spec and plan.md, satisfying the Phase 1 documentation output requirement.
- [ ] T005 Create data directory structure: `data/raw/`, `data/processed/`, `data/consent/`
- [ ] T006 [P] Define and validate JSON/YAML schemas in `specs/001-text-tone-emotional-support/contracts/` (stimulus.schema.yaml, rating.schema.yaml, analysis_result.schema.yaml)
- [X] T007 Create base configuration management for random seed pinning and path resolution in `code/config.py`
- [ ] T008 Setup logging infrastructure to record pipeline steps and data exclusion reasons
- [X] T009 [P] Perform power analysis for LMM interaction effect (medium effect size, alpha=0.05, power=0.80) using simulation or `simr` and output `data/processed/power_analysis_results.json` containing the target sample size N.
- [X] T010 [US1] Contract test for stimulus schema in `tests/contract/test_stimulus_schema.py` (validates artifacts produced in T006; MUST run after T006 completes)
- [X] T011 [US1] Contract test for rating schema in `tests/contract/test_rating_schema.py` (validates artifacts produced in T006; MUST run after T006 completes)
- [X] T012 [US1] Unit test for straight-lining detection logic in `tests/unit/test_data_cleaning.py` (tests logic implemented in T016)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Stimulus Generation and Data Collection (Priority: P1) 🎯 MVP

**Goal**: Generate a controlled set of text message stimuli and simulate human ratings for perceived emotional support.

**Independent Test**: Verify that `01_generate_stimuli.py` produces a valid `data/raw/stimuli.csv` and `02_simulate_ratings.py` produces a valid `data/raw/ratings.csv` with correct schema and no missing fields.

**⚠️ NOTE ON CONSENT RECORDS**: Per Constitution Principle VI, real consent records are required for human participants. Since this study uses **simulated data** and **mock Prolific submission**, the generation of "mock consent records" is unconstitutional. Therefore, **no consent record generation task is included**. The `data/consent/` directory is created in T005 but will remain empty or contain only a placeholder log indicating the simulated nature of the study, not fake consent artifacts.

### Implementation for User Story 1

- [X] T013 [US1] Implement factorial stimulus generator in `code/01_generate_stimuli.py` (3 emoji levels × 2 punctuation × 2 length × 2 contexts = 24 unique variants)
- [ ] T014 [US1] Implement mock Prolific data collection in `code/02_simulate_ratings.py` (generates `data/raw/ratings.csv` with P-IDs, stimulus IDs, relationship context, Likert scores; **reads target N from `data/processed/power_analysis_results.json` produced by T009**; simulates Prolific ID format validation using regex `^P-[A-Z0-9]{8}$`)
- [ ] T016 [US1] Implement straight-lining detector in `code/03_clean_data.py` (flags participants with zero variance across the **full set of 24 stimuli** as defined in `data/raw/stimuli.csv` [3 emoji × 2 punctuation × 2 length × 2 contexts = 24]; **requires `data/raw/stimuli.csv` from T013 and `data/raw/ratings.csv` from T014**; outputting exclusion flags to `data/processed/cleaning_log.csv`)
- [X] T017 [US1] Add validation logic to ensure relationship context (friend/acquaintance) is randomized and logged in `code/02_simulate_ratings.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Stimuli and Ratings generated, Consent handling skipped for simulated data, Cleaning logic ready)

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline (Priority: P2)

**Goal**: Execute Linear Mixed-Effects Models (LMM) to test for interaction effects between relationship type and cue intensity.

**Independent Test**: Verify that `04_run_lmm.py` produces `data/processed/analysis_results.json` with fixed effect estimates, p-values, and Tukey-corrected post-hoc results without GPU usage.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for LMM model construction with mock data in `tests/unit/test_analysis_logic.py`
- [ ] T019 [P] [US2] Integration test for full LMM pipeline execution in `tests/integration/test_lmm_pipeline.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement data preprocessing step in `code/04_run_lmm.py` to handle listwise deletion of excluded participants (**reads exclusion flags from `data/processed/cleaning_log.csv` produced by T016**)
- [X] T021 [US2] Implement primary LMM script in `code/04_run_lmm.py` using `statsmodels` or `linearmodels` (Random intercepts for Participant and Stimulus)
- [X] T022 [US2] Implement Satterthwaite approximation for degrees of freedom and p-value calculation in `code/04_run_lmm.py`
- [X] T023 [US2] Implement validation check in `tests/unit/test_analysis_validation.py` that asserts the LMM model summary includes a variance component for Stimulus; if variance is negligible (< 0.001), log a warning but do NOT fail the build (aligns with FR-003 execution requirement without false positives)
- [X] T024 [US2] Implement Tukey-corrected post-hoc pairwise comparisons in `code/04_run_lmm.py` (triggered if interaction p < 0.05)
- [ ] T025 [US2] Implement result serialization to `data/processed/analysis_results.json` (JSON format for single source of truth)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Analysis results generated)

---

## Phase 5: User Story 3 - Methodological Robustness and Sensitivity Reporting (Priority: P3)

**Goal**: Perform sensitivity analysis on "Cue Intensity" definitions and report robustness of findings.

**Independent Test**: Verify that `05_sensitivity_analysis.py` re-runs LMM with Alternative cue definitions and outputs a stability report in `data/processed/sensitivity_report.csv`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for alternative cue definition logic in `tests/unit/test_sensitivity_logic.py`

### Implementation for User Story 3

- [ ] T027 [US3] Define three alternative multivariate operationalizations of "Cue Intensity" based on **varying relative weights** (e.g., High-Emoji/Low-Punct, Low-Emoji/High-Punct, Balanced) and document them in `data/processed/sensitivity_definitions.json` ({{claim:c_5a9236ae}}). **Note: Structural definitions like Conjunctive/Disjunctive are excluded to align with FR-005.**
- [ ] T028 [US3] Implement sensitivity analysis engine in `code/05_sensitivity_analysis.py` (**reads operationalization definitions from `data/processed/sensitivity_definitions.json` produced by T027**; **reads primary results from `data/processed/analysis_results.json` produced by T025**; sweeps the defined weight variations)
- [ ] T029 [US3] Implement re-execution of LMM for each alternative definition in `code/05_sensitivity_analysis.py`
- [ ] T030 [US3] Implement stability metric calculation (variation in F-statistics and p-values across definitions) in `code/05_sensitivity_analysis.py`
- [ ] T031 [US3] Generate sensitivity report CSV in `data/processed/sensitivity_report.csv`
- [ ] T032 [US3] Implement family-wise error rate correction reporting for all comparisons in `code/05_sensitivity_analysis.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `specs/001-text-tone-emotional-support/quickstart.md`
- [ ] T034 Code cleanup and refactoring (ensure no unused imports, consistent naming)
- [ ] T035 [P] Run full pipeline end-to-end test with fixed seed to verify reproducibility
- [ ] T036 [P] Additional unit tests for edge cases (missing data handling, randomization failure) in `tests/unit/`
- [ ] T037 Verify all tasks complete within 6 hours on CPU-only runner (performance check)
- [ ] T038 Run `quickstart.md` validation to ensure all artifacts are present

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **except T010/T011 which depend on T006**
- Tests for different user stories can run in parallel
- Within US1, stimulus generation and rating simulation can run in parallel once data schemas are defined

---

## Parallel Example: User Story 1

```bash
# Launch schema validation and generator in parallel:
Task: "Contract test for stimulus schema in tests/contract/test_stimulus_schema.py" (after T006)
Task: "Implement factorial stimulus generator in code/01_generate_stimuli.py"

# Launch rating simulation and cleaning logic in parallel:
Task: "Implement mock Prolific data collection in code/02_simulate_ratings.py"
Task: "Implement straight-lining detector in code/03_clean_data.py"
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

- [P] tasks = different files, no dependencies (except T010/T011 which depend on T006)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Consent Records**: No mock consent records are generated for this simulated study to comply with Constitution Principle VI.