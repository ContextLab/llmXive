# Tasks: The Impact of Perspective-Taking on Moral Outrage in Online Discourse

**Input**: Design documents from `/specs/001-perspective-taking-moral-outrage/`
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

- [ ] T001 Create project structure per implementation plan: Execute `mkdir -p code/data code/analysis tests contracts data/raw data/processed data/human` and create `__init__.py` in all `code/` subfolders.
- [ ] T002 Create virtual environment: Run `python -m venv venv` and verify activation works.
- [ ] T003 Install dependencies: Run `pip install -r requirements.txt` (pandas, scipy, statsmodels, numpy, requests, pyyaml) and verify imports in a fresh shell.
- [ ] T004 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create `code/config.py` with random seed pinning, path constants, and dataset URL configuration
- [ ] T006 [P] Initialize `data/raw/`, `data/processed/`, and `data/human/` directories with `.gitkeep`
- [ ] T007 [P] Create `contracts/stimulus.schema.yaml` and `contracts/response.schema.yaml` defining data structures
- [ ] T008 Create base `code/__init__.py` and analysis `code/analysis/__init__.py` modules
- [ ] T009 [P] Implement formal power analysis function in `code/analysis/stats.py` and RUN it to calculate required sample size N for d=0.4, power=0.8; write the resulting N to `code/config.py` to inform recruitment (FR-010).
- [ ] T010 [P] Setup `tests/` directory structure with `pytest` configuration

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Stimulus Curation and Randomization (Priority: P1) 🎯 MVP

**Goal**: Ingest the "Against the Others!" dataset, filter for high-outrage posts on climate/immigration, and generate a set of randomized stimuli with paired instructions.

**Independent Test**: The system can be tested by executing the data ingestion script and verifying the output JSON contains a representative set of unique posts, split evenly by topic, with both instruction variants correctly attached to each post ID.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. These validate structures produced by T015/T018.

- [ ] T011 Unit test for data ingestion validation in `tests/test_ingest.py` (check n=40, topic split) - depends on T015
- [ ] T012 Unit test for stimulus generation in `tests/test_stimuli.py` (check 2 variants per ID) - depends on T018

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/data/ingest.py` to download dataset from verified URL and parse CSV/JSON (FR-001)
- [ ] T014 [US1] Implement filtering logic in `code/data/ingest.py` for `outrage_label == "high"` and `topic in ["climate", "immigration"]` (FR-002)
- [ ] T015 [US1] Add error handling in `code/data/ingest.py` to raise `DataInsufficientError` with specific message: "Insufficient data: Found X posts, required 40. Topics: climate, immigration." if <40 posts found (Edge Case 1)
- [ ] T016 [US1] Implement `code/data/stimuli.py` to generate "Perspective-Taking" and "Control Summarization" prompt templates (FR-003)
- [ ] T017 [US1] Implement random sampling logic in `code/data/stimuli.py` to select a representative sample of posts per topic
- [ ] T018 [US1] Save final curated stimuli to `data/processed/stimuli.json` with all metadata and instruction variants
- [ ] T019 [P] [US1] Add logging for data ingestion and filtering steps

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Pipeline Simulation & Validation (Priority: P2)

**Goal**: Simulate a cohort of synthetic participants, assign conditions, generate synthetic outrage scores, and validate the analysis pipeline logic.

**Independent Test**: The system can be tested by running a simulation where 200 synthetic participants are assigned to conditions, provided with stimuli, and generating synthetic outrage scores; the output dataset must reflect the correct condition labels and score ranges.

### Tests for User Story 2

- [ ] T020 [P] [US2] Unit test for randomization balance in `tests/test_simulation.py` (check 50/50 split ±5%)
- [ ] T021 [P] [US2] Unit test for synthetic score generation in `tests/test_simulation.py` (check a defined range, mean calculation)

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/data/simulation.py` to generate a set of synthetic participant IDs
- [ ] T023 [US2] Implement random assignment logic in `code/data/simulation.py` to split participants into PT and Control groups (FR-004)
- [ ] T024 [US2] Implement generative noise model in `code/data/simulation.py` for -item Likert scores (H0 and H1 scenarios)
- [ ] T025 [US2] Implement attention check injection logic (5 items) and failure flagging (>2 missed) in `code/data/simulation.py` (FR-008)
- [ ] T026 [US2] Calculate mean outrage score per participant and aggregate by condition (FR-005)
- [ ] T027 [US2] Save synthetic dataset to `data/processed/simulated_responses.json` ensuring separation from human data (FR-009)
- [ ] T028 [P] [US2] Add deterministic seed logging to ensure reproducibility of simulation runs

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Compute LMM (Primary), t-test (Secondary), effect sizes, and power analysis to validate the hypothesis.

**Independent Test**: The system can be tested by feeding it a dataset with known group differences; the output must correctly identify the p-value, confidence interval, and effect size.

### Tests for User Story 3

- [ ] T029 [P] [US3] Unit test for LMM output accuracy in `tests/test_stats.py` (check coefficients, p-values)
- [ ] T030 [P] [US3] Unit test for Mann-Whitney U robustness in `tests/test_stats.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `code/analysis/stats.py` for Linear Mixed-Effects Model (LMM) with fixed effects (Condition, Topic) and random effects (Stimulus, Participant) as PRIMARY analysis (FR-006, Plan Phase 3).
- [ ] T032 [US3] Implement Cohen's d calculation and Confidence interval reporting

The research question is: How does perceived social support mediate the relationship between exercise and mental well-being in young adults? The method is: A cross-sectional survey will be administered to a sample of young adults (ages 18-25) assessing exercise habits, perceived social support, and mental well-being. Statistical mediation analysis will be used to test the hypothesized model. Confidence intervals will be reported to indicate the precision of estimated effects (Smith, 2018). in `code/analysis/stats.py`; explicitly compare calculated d against SC-002 threshold (d >= 0.2) and output pass/fail status to the report.
- [ ] T033 [US3] Implement independent-samples t-test in `code/analysis/stats.py` as secondary/robustness check (FR-006 context).
- [ ] T034 [US3] Implement Mann-Whitney U test in `code/analysis/stats.py` as non-parametric robustness check (FR-007).
- [ ] T035 [US3] Create `code/analysis/pipeline.py` to orchestrate loading simulated data and running LMM (primary), t-test (secondary), and robustness checks.
- [ ] T036 [US3] Generate final analysis report in `data/processed/analysis_report.json` containing all metrics (SC-001, SC-002, SC-003).
- [ ] T037 [P] [US3] Add visualization logic (optional) for distribution of scores by condition

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Human Experiment Interface (Priority: P4)

**Goal**: Define the data schema and logic for human data collection interface (not the collection itself).

**Independent Test**: The system can be tested by deploying a pilot with a cohort of real humans and verifying that the collected data is stored in a distinct "human" dataset.

### Tests for User Story 4

- [ ] T038 [P] [US4] Integration test for human data ingestion format in `tests/test_human_ingest.py`

### Implementation for User Story 4

- [ ] T039 [US4] Create placeholder `code/human_interface.py` defining the input schema and module structure for human responses (US-4).
- [ ] T040 [US4] Implement `assign_human_participants()` function in `code/human_interface.py` to assign human participants to two groups with a balanced split (FR-011). Verify split in `tests/test_simulation.py`.
- [ ] T041 [US4] Implement data validation logic in `code/human_interface.py` to ensure human data conforms to `contracts/response.schema.yaml`.
- [ ] T042 [US4] Add logic to tag human data records as 'human' and store in `data/human/` (FR-009).
- [ ] T043 [US4] Implement attention check exclusion logic for human data in `code/human_interface.py` (FR-008).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates in `README.md` explaining the pipeline flow and dataset requirements
- [ ] T045 Code cleanup and refactoring of `code/` modules
- [ ] T046 Vectorize simulation loop in `code/data/simulation.py` using numpy to ensure pipeline completes < 1 hour on CPU (SC-005); verify by running benchmark and logging time.
- [ ] T047 [P] Additional unit tests for edge cases (e.g., empty dataset, failed attention checks)
- [ ] T048 Run `pytest --ci` validation and fix any CI failures reported by GitHub Actions

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for simulated data
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Independent of simulation data

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
# Launch all tests for User Story 1 together:
Task: "Unit test for data ingestion validation in tests/test_ingest.py"
Task: "Unit test for stimulus generation in tests/test_stimuli.py"

# Launch all implementation for User Story 1 together (if dependencies met):
Task: "Implement code/data/ingest.py"
Task: "Implement code/data/stimuli.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify 40 stimuli)
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
   - Developer A: User Story 1 (Data Ingestion)
   - Developer B: User Story 2 (Simulation)
   - Developer C: User Story 3 (Analysis)
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
- **Critical**: The dataset URL in `code/config.py` must be verified before running T013. If the URL is unreachable, the pipeline must halt with a clear error.
- **Critical**: Power Analysis (T009) must be completed before any recruitment or simulation to determine sample size N.
- **Critical**: LMM (T031) is the PRIMARY analysis; t-test (T033) is secondary.