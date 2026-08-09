# Tasks: llmXive Follow-up: Extending "Zone of Proximal Policy Optimization: Teacher in Prompts, Not Gradient"

**Input**: Design documents from `/specs/001-llmxive-zppo-extension/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/`
- Paths shown below assume single project structure as defined in `plan.md`

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

- [ ] T001 Create project structure per `plan.md` in `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/`
- [X] T002 Initialize Python project with dependencies (`numpy`, `pandas`, `scikit-learn`, `tqdm`, `pyyaml`, `datasets`, `pytest`) in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create schema contracts in `contracts/` (rollout_log, run_metadata, aggregated_metrics, convergence_result)
- [X] T005 [P] Implement config loader in `code/config.py` (seeds, thresholds, paths)
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging.py`
- [X] T007 Create base validation helpers in `code/utils/validation.py` (imports from `contracts/`)
- [ ] T008 Setup deterministic random seed management for all generators
- [X] T009 [P] Define in-memory buffer state schema and storage class in `code/models/state_store.py` (Explicitly defines the data structure for 'historical buffer cycles' including confidence history, prompt lengths, and cycle IDs; REQUIRED for T021 to function)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Static Baseline Simulation (Priority: P1) 🎯 MVP

**Goal**: Simulate the original ZPPO training loop using a static Negative Candidate-included Question (NCQ) prompt to establish a baseline convergence curve.

**Independent Test**: The system loads the generated synthetic rollout log, runs the static NCQ generation for all buffer cycles, and outputs a convergence curve (accuracy vs. cycles) that matches the expected behavior of the original ZPPO paper.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for rollout log schema in `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/tests/contract/test_schemas.py`
- [X] T011 [P] [US1] Unit test for static NCQ generation logic in `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/tests/unit/test_base_zppo.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement synthetic rollout log generator in `code/data/generators.py` (seeded by spec, includes LLM/VLM tasks based on `data-model.md` schema for VLM, confidence scores, ground truth)
- [X] T013 [US1] Implement MMLU held-out data loader in `code/data/loaders.py` (load MMLU dataset schema and synthetically generate negative candidates based on the task schema to ensure no data leakage; MUST fail loudly if MMLU schema is missing; generate synthetic labels/candidates as per Spec Assumptions)
- [X] T014 [US1] Implement static NCQ generator in `code/loops/base_zppo.py` (includes all known failure modes for every step)
- [X] T015 [US1] Implement simulated student model in `code/models/student_sim.py` (confidence update logic based on expert gap)
- [X] T016 [US1] Implement static ZPPO training loop in `code/loops/base_zppo.py` (A fixed number of buffer cycles, records accuracy per cycle; MUST utilize T009 state_store to record cycle history)
- [X] T017 [US1] Implement metrics calculation for baseline in `code/analysis/metrics.py` (AUCC, final accuracy on held-out data)
- [ ] T018 [US1] Create entry point script to run baseline simulation in `code/main.py` (outputting `data/metrics/baseline_results.csv`)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Confidence-Adaptive Pruning (CAP) Implementation (Priority: P2)

**Goal**: Implement the CAP mechanism that dynamically prunes "consistently rejected" negative candidates from the NCQ prompt based on the student's historical confidence scores.

**Independent Test**: The system runs the CAP-ZPPO loop, verifies that the NCQ prompt content changes at each step (excluding candidates based on thresholds), and produces a distinct convergence curve.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for CAP classification logic (thresholds / high confidence thresholds / high confidence) in `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/tests/unit/test_cap_logic.py`
- [X] T020 [P] [US2] Unit test for edge cases: specifically verify that if ALL candidates are pruned (due to high confidence), the system defaults to the full set (or minimal set) to avoid empty prompts; also test empty prompt fallback generally in `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/tests/unit/test_cap_logic.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement CAP classifier in `code/models/cap_classifier.py` (calculates mean/variance of confidence from T009 state_store, classifies as rejected (<0.1), fluctuating ([0.1, 0.9]), or accepted (>0.9); MUST explicitly exclude 'consistently accepted' (mastered) candidates from the prompt as per FR-003 and Constitution Principle VI; DEPENDS ON T009 (schema) AND T016/T023 (data generation); CANNOT run in parallel with loop tasks)
- [X] T022 [US2] Implement dynamic NCQ generator in `code/loops/cap_zppo.py` (filters candidates based on CAP output; MUST enforce FR-007 min threshold; MUST implement specific fallback to full set if pruning results in zero candidates)
- [X] T023 [US2] Implement CAP-ZPPO training loop in `code/loops/cap_zppo.py` (updates student confidence using attention-weighted rule, records prompt length per cycle; MUST utilize T009 state_store to record cycle history)
- [X] T024 [US2] Implement metrics calculation for CAP in `code/analysis/metrics.py` (AUCC, final accuracy, average prompt length mid-training)
- [X] T025 [US2] Create entry point script to run CAP simulation in `code/main.py` (outputting `data/metrics/cap_results.csv`)
- [X] T026 [US1/US2] Implement synthetic rollout log generator (initial state only) in `code/data/generators.py` (seeded random state; NO per-step noise here; only initial seed setup)
- [X] T027 [US1/US2] Implement per-step Gaussian noise injection (σ=0.05) into confidence scores within the training loops (`code/loops/cap_zppo.py` and `code/loops/base_zppo.py`) at each buffer cycle to ensure statistical variance per FR-008 (must execute after T016 and T023)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Statistical Analysis (Priority: P3)

**Goal**: Perform a statistical comparison between the static baseline and the CAP-ZPPO variant to determine differences in data efficiency (AUCC) and final performance.

**Independent Test**: The system executes a paired t-test on the AUCC data from Multiple runs (multiple tasks x multiple seeds) and generates a report with p-values and difference metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for paired t-test implementation in `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/tests/unit/test_stats.py`
- [X] T029 [P] [US3] Integration test for full comparison pipeline in `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/tests/integration/test_full_loop.py`

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement paired t-test logic in `code/analysis/stats.py` (comparing AUCC distributions; MUST calculate and return the Standard Deviation of the AUCC distribution as per SC-002)
- [X] T031 [US3] Implement catastrophic forgetting check in `code/analysis/stats.py` (comparing final accuracy on held-out data)
- [X] T032 [US3] Create batch runner script in `code/main.py` to execute multiple independent simulation runs (multiple tasks x multiple seeds), each running for a fixed number of buffer cycles, and aggregate the resulting AUCC values for the paired t-test per FR-008
- [X] T033 [US3] Generate comparative report in `code/analysis/report.py` (p-values, AUCC difference, Standard Deviation of AUCC distribution, average prompt length specifically for mid-training cycles, plots)
- [ ] T034 [US3] Validate results against `contracts/aggregated_metrics.schema.yaml`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure compliance with Constitution Principles

- [ ] T035 [P] Run versioning script in `code/versioning.py` to checksum `data/` and update `state/projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox.yaml` (Principle V)
- [ ] T036a [P] Refactor `code/loops/` modules to extract common ZPPO logic into a shared base class, reducing cyclomatic complexity of `cap_zppo.py` and `base_zppo.py` to < 15
- [ ] T036b [P] Refactor `code/analysis/` to separate metric calculation from reporting logic, ensuring `metrics.py` contains no plotting code
- [ ] T036c [P] Update `code/main.py` to modularize batch execution flow, reducing file length to < 200 lines
- [ ] T037 Verify all data loaders fail loudly on missing real data (no synthetic fallbacks) per Principle III
- [ ] T038 [P] Additional unit tests for noise injection and seed reproducibility
- [ ] T039 Run quickstart.md validation to ensure full pipeline execution

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **NEW**: T009 (State Store) is critical for T021 (CAP Classifier)
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - DEPENDS on T009 (State Store) and T016/T023 (Loop Data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, EXCEPT T021 which depends on T009 and loop data)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **NOTE**: T021 (CAP Classifier) CANNOT run in parallel with T016/T023 (Loops) as it requires the data they produce.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for rollout log schema in tests/contract/test_schemas.py"
Task: "Unit test for static NCQ generation logic in tests/unit/test_base_zppo.py"

# Launch all models for User Story 1 together:
Task: "Implement synthetic rollout log generator in code/data/generators.py"
Task: "Implement MMLU held-out data loader in code/data/loaders.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - **Ensure T009 (State Store) is complete before T021**
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
 - **Note**: T021 must wait for T009 and T016/T023 data
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (including T009)
2. Once Foundational is done:
 - Developer A: User Story 1 (T012-T018)
 - Developer B: User Story 2 (T022-T025) - *T021 must be assigned to Developer B but executed AFTER T016/T023 data is available or after T009 is ready if mocking data for logic tests*
 - Developer C: User Story 3 (T030-T034)
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
- **Data Integrity**: All data loaders must use real sources (MMLU via `datasets`, synthetic via seeded generators). For held-out sets, generate synthetic candidates from real MMLU schema as per Spec Assumptions.
- **Compute Constraints**: Simulation must complete within 6 hours on CPU (2 cores, 7GB RAM). Use streaming for MMLU if needed.
- **Noise Injection**: Per-step noise (FR-008) is handled in T027 within the loop, not T026 (initial generation).
- **CAP Logic**: T021/T022 explicitly handle exclusion of 'consistently accepted' (>0.9) and 'all pruned' fallback.
- **State Management**: T009 defines the buffer history structure required by T021. T021 is NOT parallel with T016/T023.
- **Data Model**: Ensure `data-model.md` is finalized before T012 and T013 execution.