# Tasks: llmXive Follow-up: Extending "Zone of Proximal Policy Optimization: Teacher in Prompts, Not Gradient"

**Input**: Design documents from `/specs/001-llmxive-zppo-extension/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

 Tasks MUST be organized by user story so each story can:
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

- [ ] T004a [P] Create `contracts/rollout_log.schema.yaml` defining fields for student responses, confidence scores, and task IDs. This is the Single Source of Truth for T012 and T033.
- [ ] T004b [P] Create `contracts/run_metadata.schema.yaml` defining fields for seeds, timestamps, and hyperparameters.
- [ ] T004c [P] Create `contracts/aggregated_metrics.schema.yaml` defining fields for AUCC, final accuracy, and prompt length stats.
- [ ] T004d [P] Create `contracts/convergence_result.schema.yaml` defining fields for per-cycle accuracy and prompt content.
- [X] T005 [P] Implement config loader in `code/config.py` (seeds, thresholds, paths)
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging.py`
- [X] T007 [P] Create base validation helpers in `code/utils/validation.py` (imports from `contracts/`) - DEPENDS on T004a-d completion
- [X] T008 [P] Setup deterministic random seed management in `code/utils/seeds.py`. MUST implement a singleton pattern `get_rng(seed: int) -> numpy.random.Generator` to ensure reproducibility (Constitution Principle I) and statistical variance (FR-008). MUST be implemented before T026, T016, and T023.
- [X] T026 [P] Implement per-step Gaussian noise injection in `code/utils/noise.py`. MUST define function `inject_noise(confidence: float, sigma: float = 0.05) -> float` to inject noise into confidence scores as per FR-008. DEPENDS on T008. MUST be implemented before T016 and T023.
- [X] T013 [P] Implement MMLU held-out data loader in `code/data/loaders.py`. MUST fail loudly with clear error message if REAL training data is missing (NO synthetic fallback). HOWEVER, for held-out test data generation, if the specific MMLU subset is unavailable, MUST fall back to a synthetic expert distribution as per Spec Assumptions to ensure simulation resilience.
- [ ] T009 [P] Implement State Store utility in `code/utils/state_store.py` to manage `state/projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox.yaml` (required for T021 to track historical confidence). DEPENDS on T004a-d.
- [X] T021 [US2] Implement CAP classifier in `code/models/cap_classifier.py`. Calculates mean/variance of confidence, classifies as rejected (<0.1), fluctuating ([0.1, 0.9]), or accepted (>0.9). MUST explicitly exclude BOTH 'consistently rejected' (<0.1) AND 'consistently accepted' (>0.9) candidates from the prompt as per FR-003 and Constitution Principle VI, retaining only 'fluctuating' candidates. MUST implement fallback to full set if resulting set is empty per FR-007. MUST be implemented before T023. DEPENDS on T009.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Static Baseline Simulation (Priority: P1) 🎯 MVP

**Goal**: Simulate the original ZPPO training loop using a static Negative Candidate-included Question (NCQ) prompt to establish a baseline convergence curve.

**Independent Test**: The system loads the generated synthetic rollout log, runs the static NCQ generation for all buffer cycles, and outputs a convergence curve (accuracy vs. cycles) that matches the expected behavior of the original ZPPO paper.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for rollout log schema in `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/tests/contract/test_schemas.py` - DEPENDS on T004a
- [X] T011 [P] [US1] Unit test for static NCQ generation logic in `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/tests/unit/test_base_zppo.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement synthetic rollout log generator in `code/data/generators.py`. MUST implement explicit learning dynamics: student confidence updates based on 'expert gap' and 'prompt length' variables as defined in Plan Step 1. Formula: `new_conf = current_conf + alpha * (expert_conf - current_conf) * (1 - prompt_length_factor)`. Includes LLM/VLM tasks, confidence scores, ground truth.
- [X] T014 [US1] Implement static NCQ generator in `code/loops/base_zppo.py` (includes all known failure modes for every step)
- [ ] T015 [US1] Implement simulated student model in `code/models/student_sim.py`. MUST implement confidence update logic using the formula from T012.
- [ ] T016 [US1] Implement static ZPPO training loop in `code/loops/base_zppo.py`. A fixed number of buffer cycles, records accuracy per cycle. MUST include per-step Gaussian noise injection (σ=0.05) into confidence scores as defined in T026. DEPENDS on T008 and T026.
- [ ] T018 [US1] Implement single-run simulation ENGINE for baseline in `code/main.py`. This task implements the internal function `run_baseline_simulation(seed)` to execute a single baseline simulation cycle (to be called by the batch runner T031). It does NOT handle CLI argument parsing or batch orchestration; it strictly returns the convergence curve data structure.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Confidence-Adaptive Pruning (CAP) Implementation (Priority: P2)

**Goal**: Implement the CAP mechanism that dynamically prunes "consistently rejected" negative candidates from the NCQ prompt based on the student's historical confidence scores.

**Independent Test**: The system runs the CAP-ZPPO loop, verifies that the NCQ prompt content changes at each step (excluding candidates based on thresholds), and produces a distinct convergence curve.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for CAP classification logic (thresholds /0.9) in `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/tests/unit/test_cap_logic.py`
- [ ] T020 [P] [US2] Unit test for edge cases: specifically verify that if ALL candidates are pruned (due to high confidence), the system defaults to the full set (or minimal set) to avoid empty prompts; also test empty prompt fallback generally in `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/tests/unit/test_cap_logic.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement dynamic NCQ generator in `code/loops/cap_zppo.py` (filters candidates based on CAP output; MUST enforce FR-007 min threshold; MUST implement specific fallback to full set if pruning results in zero candidates; REQUIRES T021 logic to be implemented first; depends on T021 output)
- [ ] T023 [US2] Implement CAP-ZPPO training loop in `code/loops/cap_zppo.py`. Updates student confidence using attention-weighted rule, records prompt length per cycle. MUST include per-step Gaussian noise injection (σ=0.05) into confidence scores as defined in T026. DEPENDS on T021 and T026.
- [ ] T024 [US2] Implement metrics calculation for CAP in `code/analysis/metrics.py` (AUCC, final accuracy, average prompt length mid-training)
- [ ] T025 [US2] Implement single-run simulation ENGINE for CAP in `code/main.py`. This task implements the internal function `run_cap_simulation(seed)` to execute a single CAP simulation cycle (to be called by the batch runner T031). It does NOT handle CLI argument parsing or batch orchestration; it strictly returns the convergence curve data structure.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Statistical Analysis (Priority: P3)

**Goal**: Perform a statistical comparison between the static baseline and the CAP-ZPPO variant to determine differences in data efficiency (AUCC) and final performance.

**Independent Test**: The system executes a paired t-test on the AUCC data from Multiple runs (multiple tasks x multiple seeds) and generates a report with p-values and difference metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for paired t-test implementation in `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/tests/unit/test_stats.py`
- [ ] T028 [P] [US3] Integration test for full comparison pipeline in `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/tests/integration/test_full_loop.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement paired t-test logic in `code/analysis/stats.py` (comparing AUCC distributions; MUST calculate and return the Standard Deviation of the AUCC distribution as per SC-002)
- [ ] T030 [US3] Implement catastrophic forgetting check in `code/analysis/stats.py` (comparing final accuracy on held-out data)
- [ ] T031 [US3] Create batch runner script in `code/main.py`. Orchestrates 100 runs (10 tasks x 10 seeds) with distinct random seeds per FR-008. MUST call the internal `run_baseline_simulation` (T018) and `run_cap_simulation` (T025) engines directly in a loop to generate the statistical distribution. MUST select the 10 tasks deterministically (first 10 subjects alphabetically from MMLU, or random sample with seed=42 if order is non-deterministic). MUST generate output file `data/metrics/batch_results.csv` with columns [task_id, seed, aucc, final_accuracy, prompt_length_avg].
- [ ] T032 [US3] Generate comparative report in `code/analysis/report.py` (p-values, AUCC difference, Standard Deviation of AUCC distribution, prompt length reduction, plots)
- [ ] T033 [US3] Validate results against `contracts/aggregated_metrics.schema.yaml`. DEPENDS on T004c completion.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure compliance with Constitution Principles

- [ ] T034 [P] Implement `code/versioning.py` to checksum `data/` and update `state/projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox.yaml` (Principle V). DEPENDS on T001 (Project Structure) and data generation completion.
- [ ] T035b [P] Refactor `code/analysis/` to separate metric calculation from reporting logic, ensuring `metrics.py` contains no plotting code
- [ ] T035c [P] Update `code/main.py` to modularize batch execution flow, reducing file length to < 200 lines
- [ ] T036 Verify all data loaders fail loudly on missing real data (no synthetic fallbacks) per Principle III
- [ ] T037 [P] Additional unit tests for noise injection and seed reproducibility
- [ ] T038 Run quickstart.md validation to ensure full pipeline execution

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Order**: T004a-d -> T008 -> T026 -> T009 -> T007 -> T013 -> T021
 - **Order**: T008 must precede T026, T016, T023
 - **Order**: T026 must precede T016, T023
 - **Order**: T009 must precede T021
 - **Order**: T004a-d must precede T007, T033
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - DEPENDS on T009 (State Store) and T021 (CAP Classifier) logic being ready before T023
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, EXCEPT T021 which depends on T009 and loop data, T004 which is missing, T008 which is missing, T026 which is missing)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **NOTE**: T021 (CAP Classifier) CANNOT run in parallel with T016/T023 (Loops) as it requires the data they produce. T026 MUST precede T016/T023.

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
 - **Ensure T004a-d (Schema Contracts) is complete**
 - **Ensure T008 (Seed Management) is complete**
 - **Ensure T026 (Noise Injection) is complete**
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

1. Team completes Setup + Foundational together (including T004a-d, T008, T026)
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
- **Data Integrity**: All data loaders must use real sources (MMLU via `datasets`, synthetic via seeded generators). NO synthetic fallbacks for training data; synthetic expert fallback allowed for held-out test data per spec Assumptions.
- **Compute Constraints**: Simulation must complete within 6 hours on CPU (2 cores, 7GB RAM). [UNRESOLVED-CLAIM: c_0c8ab567 — status=not_enough_info] Use streaming for MMLU if needed.
- **Noise Injection**: Per-step noise (FR-008) is handled in T026 within the loops, applied to both baseline and CAP variants. T026 MUST be completed before T016/T023.
- **CAP Logic**: T021/T022 explicitly handle exclusion of 'consistently accepted' (>0.9) and 'consistently rejected' (<0.1), and 'all pruned' fallback.
- **State Management**: T009 is required to persist historical confidence scores for the CAP classifier (T021) to calculate mean/variance across cycles.
- **Schema Contracts**: T004a-d are currently incomplete and MUST be completed to enable T007, T010, T033.
- **Seed Management**: T008 is currently incomplete and MUST be completed to enable T016, T023, T026.
- **Entry Points**: T018 and T025 now define internal simulation engines; T031 is the sole CLI entry point for the batch study.
- **Batch Execution**: T031 orchestrates the 100 runs (10 tasks x 10 seeds) by directly invoking the engines from T018/T025, ensuring the statistical distribution requirement is met without logical ordering violations.
- **Output Schema**: T031 must generate `data/metrics/batch_results.csv` with columns [task_id, seed, aucc, final_accuracy, prompt_length_avg].
- **Learning Dynamics**: T012/T015 use the formula `new_conf = current_conf + alpha * (expert_conf - current_conf) * (1 - prompt_length_factor)`.