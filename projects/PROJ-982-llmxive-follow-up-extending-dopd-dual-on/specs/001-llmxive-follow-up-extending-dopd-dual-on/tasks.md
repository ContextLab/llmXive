# Tasks: 001-dopd-discrete-mdp

**Input**: Design documents from `/specs/001-dopd-discrete-mdp/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create root directories: `code/`, `specs/`, `tests/`, `data/`, `docs/`
- [ ] T001b [P] Create `code/env/`, `code/agents/`, `code/training/`, `code/analysis/` directories
- [ ] T001c [P] Create `code/tests/` and `docs/` directories
- [ ] T001d [P] Create `data/raw/` and `data/processed/` directories

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement `code/env/__init__.py` package initialization
- [ ] T006 [P] Implement `code/agents/__init__.py` package initialization
- [ ] T007 [P] Implement `code/training/__init__.py` package initialization
- [ ] T008 [P] Implement `code/analysis/__init__.py` package initialization
- [ ] T009 [P] Setup `code/tests/conftest.py` with strict seed pinning fixtures
- [ ] T010 [P] Implement `code/utils/seeding.py` for deterministic random state management
- [ ] T011a [P] Initialize `requirements.txt` with core dependencies: gymnasium, numpy, pandas, scipy
- [ ] T011b [P] Initialize `requirements.txt` with dev dependencies: pytest, ruff, black

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct Discrete Privilege Illusion MDP Environment (Priority: P1) 🎯 MVP

**Goal**: Create a synthetic, discrete-state MDP where a Teacher has a hidden privileged signal `H` and a Student only sees `O`, ensuring information asymmetry.

**Independent Test**: The environment can be instantiated and queried to confirm that the Student's observation space strictly excludes the privileged variable while the Teacher's does not, and that optimal policy requires the privileged variable.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/env/privilege_mdp.py`: Define discrete grid-world with hidden state `H` and observable `O`, enforcing max grid dimension constraint (RAM < 7GB) per FR-008 and ensuring `H` is strictly masked from Student observations per FR-001
- [ ] T013 [US1] Implement `code/env/privilege_mdp.py`: Define transition logic where `H` dictates optimal action to ensure Student fails without it
- [ ] T014 [US1] Implement `code/agents/teacher.py`: Create Oracle policy with full state access `(O, H)`
- [ ] T015 [US1] Implement `code/agents/student.py`: Create Tabular Q-table agent with partial state access `O`

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T016 [P] [US1] Contract test: Add test function `test_teacher_student_observation_spaces` to `code/tests/test_env.py` verifying Teacher observes `(O, H)` and Student observes only `O`
- [ ] T017 [P] [US1] Contract test: Add test function `test_optimal_action_dependency` to `code/tests/test_env.py` verifying optimal action depends on `H` and asserting `reward_student_masked < reward_teacher`
- [ ] T018 [P] [US1] Reproducibility test: Add test function `test_seed_consistency` to `code/tests/test_env.py` verifying state distribution consistency across multiple seeds

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Implement DOPD vs. Uniform Supervision Training Loops (Priority: P2)

**Goal**: Implement Uniform On-Policy Distillation (baseline) and DOPD (dynamic weighting based on advantage gap) training regimes.

**Independent Test**: The training loops can be executed on the discrete MDP, logging the Student's policy updates and action distributions to verify that DOPD reduces reliance on the Teacher's actions when the advantage gap is low.

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/analysis/generalization_test.py`: Masked evaluation logic to remove `H` during inference
- [ ] T020 [US2] Implement `code/analysis/generalization_test.py`: Calculate performance drop metric: `(acc_unmasked - acc_masked) / R_max`
- [ ] T021 [US2] Implement `code/training/uniform_distillation.py`: Fixed-weight distillation loss logic
- [ ] T022a [US2] Implement `code/agents/baseline_estimator.py`: Compute `V_baseline(s)` as the state-value of a random policy per FR-002
- [ ] T022 [US2] Implement `code/training/dopd_distillation.py`: Calculate Teacher advantage gap (Q(s,a) - V_baseline(s)) using output from T022a
- [ ] T023 [US2] Implement `code/training/dopd_distillation.py`: Implement min-max normalization for low dynamic range gaps per FR-002
- [ ] T024 [US2] Implement `code/training/dopd_distillation.py`: Dynamic weighting logic for distillation loss vs. self-supervision
- [ ] T025 [US2] Implement `code/utils/logging.py`: Log training accuracy, convergence steps, and action entropy per FR-006
- [ ] T026 [US2] Implement `code/training/dopd_distillation.py`: Masked evaluation logic to remove `H` during inference (moved from Phase 4 start to follow training logic)
- [ ] T027 [US2] Implement `code/training/dopd_distillation.py`: Calculate performance drop metric (moved from Phase 4 start to follow training logic)
- [ ] T028 [US2] Add safety checks for sparse self-supervision signals (division-by-zero prevention) per Edge Cases

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T029 [P] [US2] Integration test: Verify Uniform regime mimics Teacher actions regardless of advantage in `code/tests/test_dopd.py`
- [ ] T030 [P] [US2] Integration test: Verify DOPD regime switches weighting when advantage gap < 0.1 per FR-002
- [ ] T031 [P] [US2] Integration test: Verify DOPD Student shows higher entropy/self-correction when Teacher advantage is low

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Execute Statistical Generalization Analysis (Priority: P3)

**Goal**: Run a statistical comparison (Mann-Whitney U test) of generalization accuracy between DOPD and Uniform regimes across multiple seeds.

**Independent Test**: The analysis script can take the accuracy logs from the training runs and output a p-value and effect size, confirming or refuting the hypothesis.

### Implementation for User Story 3

- [ ] T032 [US3] Implement `code/analysis/stats.py`: Execute one-tailed Mann-Whitney U test (H0: mean(DOPD) <= mean(Uniform)) on accuracy logs per FR-005
- [ ] T033 [US3] Implement `code/analysis/stats.py`: Calculate effect size and log exploratory status if < 0.5 per FR-005
- [ ] T034 [US3] Implement `code/analysis/stats.py`: Compute Coefficient of Variation (CV) for reproducibility per SC-005
- [ ] T035 [US3] Create `code/scripts/run_experiment.py`: Orchestrate 50 independent seeds, logging to `data/raw/`
- [ ] T036 [US3] Create `code/scripts/aggregate_results.py`: Aggregate logs and generate `data/processed/` metrics
- [ ] T037 [US3] Ensure evaluation uses distinct seeds from training per FR-007 (Configuration)
- [ ] T038 [US3] Create `code/scripts/run_experiment.py`: Implement explicit loop for 50 seeds and verify count >= 50 per FR-005 (Refined T035)
- [ ] T039 [US3] Implement `code/analysis/stats.py`: Calculate and compare convergence steps between DOPD and Uniform regimes per SC-003

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T040 [P] [US3] Contract test: Verify Mann-Whitney U test output format (p-value, direction) in `code/tests/test_stats.py`
- [ ] T041 [P] [US3] Integration test: Verify distinct random seeds for training vs. evaluation per FR-007
- [ ] T046 [P] [US3] Contract test: Add test function `test_seed_separation` to `code/tests/test_stats.py` asserting `seed_train != seed_test` per FR-007

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Log and report Coefficient of Variation (CV) metric to `data/processed/reproducibility_metrics.json` per SC-005
- [ ] T043 [P] Implement checksumming utility in `code/utils/checksum.py` to generate hashes for artifacts
- [ ] T044 [P] Create `code/scripts/record_hashes.py` to invoke checksum utility and record hashes in `state/projects/...yaml` per Constitution Principle III & V
- [ ] T045 [P] Refactor logging to structured JSON format for easier parsing
- [ ] T046 [P] Remove unused imports and dead code from all modules
- [ ] T047 [P] Documentation updates in `docs/` and `README.md`
- [ ] T053 [P] Profile simulation speed to verify the performance constraint for 50 seeds per Plan Performance Goals
- [ ] T054 [P] Optimize simulation loop to meet temporal constraints if profiling fails
- [ ] T055 [P] Implement CV calculation logic in `code/analysis/stats.py` (consolidated from T034)
- [ ] T056 [P] Generate final reproducibility report JSON at `data/processed/reproducibility_metrics.json` linking CV calculation to artifact per SC-005
- [ ] T057 [P] Additional unit tests for edge cases (noise signal `H`, sparse rewards)
- [ ] T058 [P] Run `quickstart.md` validation
- [ ] T059 [P] Verify all artifacts checksummed and versioned per Constitution Principle V

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 environment/agents
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 training/analysis outputs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Environment before Agents
- Agents before Training Loops
- Training Loops before Analysis/Stats
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
Task: "Add test function test_teacher_student_observation_spaces to code/tests/test_env.py"
Task: "Add test function test_optimal_action_dependency to code/tests/test_env.py"

# Launch all models for User Story 1 together:
Task: "Implement code/env/privilege_mdp.py"
Task: "Implement code/agents/teacher.py"
Task: "Implement code/agents/student.py"
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