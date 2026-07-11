# Tasks: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Input**: Design documents from `/specs/001-visual-salience-moral-judgments/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
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
  - Be implemented independently
  - Be tested independently
  - Be delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `data/raw/`, `data/processed/`, `data/survey/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (numpy, pandas, scipy, statsmodels, Pillow, requests, matplotlib, seaborn)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup random seed configuration module (`code/config.py`) to ensure reproducibility across all scripts
- [ ] T005 [P] Create data directory structure and checksum verification script (`code/verify_data_integrity.py`)
- [ ] T006 [P] Implement basic logging infrastructure (`code/logging_config.py`)
- [ ] T007 [US1] Create base data models/entities in `code/models.py`: Define `Scenario` (id, image_path, ambiguity_label), `StimulusVariant` (id, scenario_id, salience_level, image_path), `Response` (id, participant_id, stimulus_id, rating, timestamp), and `Participant` (id, status) classes with explicit attributes per spec.
- [ ] T008 [P] Setup environment variable management for dataset paths and API keys

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Preparation and Salience Manipulation (Priority: P1) 🎯 MVP

**Goal**: Ingest open visual datasets, identify morally ambiguous images, and generate manipulated variants with controlled luminance contrast.

**Independent Test**: Run pipeline on a set of raw images; verify metadata filter, human coding reliability (≥80%), and pixel-level contrast changes without semantic alteration.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Unit test for metadata filtering logic in `tests/unit/test_data_prep.py`
- [ ] T011 [P] [US1] Unit test for luminance manipulation (SSIM/IoU check) in `tests/unit/test_manipulation.py`
- [ ] T012 [P] [US1] Integration test for full data prep pipeline on sample subset in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement dataset ingestion and URL verification in `code/data_prep.py` (Target: Visual Genome or verified alternative)
- [ ] T014 [US1] Implement metadata filtering for 'social'/'conflict' tags in `code/data_prep.py`
- [ ] T015 [US1] Implement human coding workflow script (`code/human_coding.py`) to calculate Cohen's κ from annotations, apply the ≥0.8 threshold, and **exclude** scenarios failing the threshold. Output the filtered list of valid scenarios to `data/processed/valid_scenarios.csv`.
- [ ] T014a [US1] Orchestrate Pilot Execution: Run `code/human_coding.py` against a pilot set (N=10). **If real human annotations are unavailable, invoke `code/synthetic_data_gen.py` with a known kappa parameter to generate synthetic annotations.** Output `data/processed/human_coding_annotations.csv` and ensure the filtering logic from T015 is applied to generate the final valid scenario list.
- [ ] T016 [US1] Implement salience manipulation function (low/med/high luminance) in `code/data_prep.py` ensuring no semantic change
- [ ] T017 [US1] Implement semantic preservation verification (object detection/IoU) in `code/validation.py`
- [ ] T018 [US1] Implement failure logging and exclusion logic for unmanipulatable images in `code/data_prep.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Survey Deployment and Data Collection (Priority: P2)

**Goal**: Present manipulated images in a randomized within-subject design and collect blame ratings.

**Independent Test**: Pilot survey with small cohort; verify randomization, within-subject constraints, and correct data logging.

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement survey randomization engine (within-subject design) in `code/survey_sim.py` to generate sequences where no scenario appears twice with the same salience level for a participant.
- [ ] T023 [US2] Implement survey deployment interface using Streamlit in `code/survey_deploy.py`. **MUST** enforce the 'never the same one twice' constraint by implementing a `SessionState` dictionary to track `seen_scenarios` per participant. Before rendering an image, check `session_state['seen_scenarios'][participant_id]`; if the current scenario is present, skip to the next available salience level from the randomization engine (T022). Output schema: `participant_id`, `image_id`, `salience_level`, `rating`, `timestamp`.
- [ ] T024 [US2] Implement data collection handler to log responses to `data/survey/pilot_responses.csv`
- [ ] T026 [US2] Implement pilot data simulation script (`code/survey_sim.py`) to generate synthetic data for pipeline validation

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for randomization logic (within-subject constraint) in `tests/unit/test_survey_logic.py`
- [ ] T020 [P] [US2] Unit test for data schema validation (participant_id, image_id, salience, rating) in `tests/unit/test_data_schema.py`
- [ ] T021 [P] [US2] Integration test for pilot data collection flow in `tests/integration/test_survey_flow.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Perform Linear Mixed-Effects Model (LMM) analysis (per plan.md update), apply corrections, and generate reports.

**Independent Test**: Run analysis on synthetic datasets with known effects; verify F-statistics, p-values, effect sizes, and confidence intervals.

### Implementation for User Story 3

- [ ] T029a [US3] Document Methodological Deviation: Update `docs/paper_draft.md` under section **3.2 'Methodological Deviations'**. Explicitly document the shift from FR-004's mandated Repeated-Measures ANOVA to the Plan's Linear Mixed-Effects Model (LMM). Cite the 'Critical Methodological Update' in `plan.md` and justify the change based on the nested data structure (responses nested within scenarios/participants). **This task must be completed BEFORE any analysis implementation.**
- [ ] T031 [US3] Implement Primary Analysis: Implement the Linear Mixed-Effects Model (`Rating ~ Salience + (1|Participant) + (1|Scenario)`) in `code/analysis.py` using `statsmodels` (per plan.md update). This is the primary analysis method.
- [ ] T030a [US3] Implement Comparative Validation (FR-004): Implement a Repeated-Measures ANOVA (with Mauchly's test and Greenhouse-Geisser corrections) in `code/analysis.py` **solely for comparative validation purposes**. This task satisfies the verification requirement of FR-004 by running the mandated method, but the results are secondary to the primary LMM analysis.
- [ ] T033 [US3] Implement LMM assumption checks (residual normality, homoscedasticity) in `code/analysis.py` (replacing ANOVA sphericity tests).
- [ ] T034 [US3] Implement Bonferroni-corrected pairwise comparisons (Low vs Med, Med vs High, Low vs High) in `code/analysis.py`
- [ ] T035 [US3] Implement effect size (partial eta-squared) and 95% CI calculation in `code/analysis.py`
- [ ] T045 [US3] Execute Data Cleaning: Run the straight-lining detection routine on `data/survey/pilot_responses.csv` to exclude participants with identical ratings across all items; output cleaned dataset `data/processed/cleaned_responses.csv`.
- [ ] T046 [US3] Implement Precision Threshold Derivation: Add `PRECISION_THRESHOLD` constant to `code/config.py` (default a placeholder value as a placeholder). **Crucially, implement a `derive_threshold()` function in `code/analysis.py`** that calculates the threshold based on a target power (e.g., adequate statistical power) and expected effect size (even if default values are used), satisfying the requirement to define the *method* to derive the value. Calculate 95% CI width, compare against this threshold, and log the result in `data/analysis/results.json`.
- [ ] T036 [US3] Implement pipeline validation script (Positive Control/Negative Control) in `code/validation.py`
- [ ] T037 [US3] Implement report generator to output `data/analysis/results.json` and console summary, explicitly documenting the LMM vs ANOVA deviation rationale and the comparative ANOVA results.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for LMM model fitting (Positive/Negative control) in `tests/unit/test_analysis.py`
- [ ] T028 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_corrections.py`
- [ ] T029 [P] [US3] Unit test for effect size (partial eta-squared) calculation in `tests/unit/test_metrics.py`
- [ ] T030 [P] [US3] Integration test for full analysis pipeline on synthetic data in `tests/integration/test_analysis_pipeline.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/paper_draft.md`
- [ ] T039 Code cleanup and refactoring
- [ ] T050 [P] Add profiling script to measure runtime of the full pipeline (`code/profile_pipeline.py`)
- [ ] T051 Refactor code to ensure <6h runtime on 2 CPU/7GB RAM, verified by running `code/profile_pipeline.py` on full dataset
- [ ] T040 [P] Additional unit tests for edge cases (sample size < planned) in `tests/unit/`
- [ ] T041 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for stimuli data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for response data

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
Task: "Unit test for metadata filtering logic in tests/unit/test_data_prep.py"
Task: "Unit test for luminance manipulation (SSIM/IoU check) in tests/unit/test_manipulation.py"

# Launch all models for User Story 1 together:
Task: "Implement dataset ingestion and URL verification in code/data_prep.py"
Task: "Implement human coding workflow script in code/human_coding.py"
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