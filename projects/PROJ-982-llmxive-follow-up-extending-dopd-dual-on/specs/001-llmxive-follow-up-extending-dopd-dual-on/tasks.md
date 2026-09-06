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

- [X] T001 [P] Initialize Project Directory Structure: Create root directories `code/`, `specs/`, `tests/`, `data/`, `docs/` and subdirectories `code/env/`, `code/agents/`, `code/training/`, `code/analysis/`, `code/tests/`, `data/raw/`, `data/processed/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `code/env/__init__.py` package initialization
- [X] T006 [P] Implement `code/agents/__init__.py` package initialization
- [X] T007 [P] Implement `code/training/__init__.py` package initialization
- [X] T008 [P] Implement `code/analysis/__init__.py` package initialization
- [X] T009 [P] Setup `code/tests/conftest.py` with strict seed pinning fixtures
- [X] T010 [P] Implement `code/utils/seeding.py` for deterministic random state management
- [X] T011 [P] Initialize `requirements.txt` with core dependencies (gymnasium, numpy, pandas, scipy) and dev dependencies (pytest, ruff, black)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct Discrete Privilege Illusion MDP Environment (Priority: P1) 🎯 MVP

**Goal**: Create a synthetic, discrete-state MDP where a Teacher has a hidden privileged signal `H` and a Student only sees `O`, ensuring information asymmetry.

**Independent Test**: The environment can be instantiated and queried to confirm that the Student's observation space strictly excludes the privileged variable while the Teacher's does not, and that optimal policy requires the privileged variable.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/env/privilege_mdp.py`: Define discrete grid-world with hidden state `H` and observable `O`, enforcing max grid dimension 10x10 (RAM < 7GB) per FR-008. Explicitly project state vector to first 2 dimensions for Student observation (`O = state[:, 0:2]`) per FR-001.
- [X] T013 [US1] Implement `code/env/privilege_mdp.py`: Define transition logic where `H` dictates optimal action to ensure Student fails without it
- [X] T014 [US1] Implement `code/agents/teacher.py`: Create Oracle policy with full state access `(O, H)`
- [X] T015 [US1] Implement `code/agents/student.py`: Create Tabular Q-table agent with partial state access `O`

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T016 [P] [US1] Contract test: Add test function `test_teacher_student_observation_spaces` to `code/tests/test_env.py` verifying Teacher observes `(O, H)` and Student observes only `O`
- [X] T017 [P] [US1] Contract test: Add test function `test_optimal_action_dependency` to `code/tests/test_env.py` verifying optimal action depends on `H` and asserting `reward_student_masked < reward_teacher`
- [X] T018 [P] [US1] Reproducibility test: Add test function `test_seed_consistency` to `code/tests/test_env.py` verifying state distribution consistency across multiple seeds

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Implement DOPD vs. Uniform Supervision Training Loops (Priority: P2)

**Goal**: Implement Uniform On-Policy Distillation (baseline) and DOPD (dynamic weighting based on advantage gap) training regimes.

**Independent Test**: The training loops can be executed on the discrete MDP, logging the Student's policy updates and action distributions to verify that DOPD reduces reliance on the Teacher's actions when the advantage gap is low.

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/training/uniform_distillation.py`: Fixed-weight distillation loss logic (independent of advantage gap)
- [X] T022a [US2] Implement `code/agents/baseline_estimator.py`: Simulate random policy over a sufficient number of steps using Monte Carlo estimation (a sufficient number of episodes per batch) to generate state trajectories and compute state-value function `V_baseline(s)` per FR-002. Convergence check: Stop if std dev < 0.01 for 100 consecutive batches.
- [X] T022 [US2] [Depends: T022a] Implement `code/training/dopd_distillation.py`: Calculate Teacher advantage gap (Q(s,a) - V_baseline(s)) using output from T022a per FR-002
- [X] T023 [US2] Implement `code/training/dopd_distillation.py`: Measure dynamic range of advantage gap (max - min) over the **current batch**; if dynamic range < 0.1, trigger min-max normalization switch per FR-002
- [X] T024 [US2] Implement `code/training/dopd_distillation.py`: Dynamic weighting logic for distillation loss vs. self-supervision
- [X] T028 [US2] Implement `code/training/dopd_distillation.py`: Add epsilon-guarded division (epsilon=1e-8) to prevent ZeroDivisionError when self-supervision signal is sparse or zero per Edge Cases and FR-002
- [X] T025 [US2] Implement `code/utils/logging.py`: Log training accuracy, convergence steps, and action entropy per FR-006
- [X] T019 [US2] Implement `code/analysis/generalization_test.py`: Masked evaluation logic to remove `H` during inference
- [X] T020 [US2] Implement `code/analysis/generalization_test.py`: Calculate performance drop metric: `(acc_unmasked - acc_masked) / R_max`
- [X] T057a [US2] [Edge Case] Implement `code/tests/test_dopd.py`: Unit test for 'noise signal H' scenario where privileged signal is uncorrelated with optimal action; verify system handles this without crashing per Edge Cases
- [X] T022b [US2] Implement `code/agents/baseline_estimator.py`: Fallback logic if T022a fails to converge within 2000 steps; log warning, set `is_converged=False`, and return last valid estimate to prevent silent bias per FR-002

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T029 [P] [US2] Integration test: Verify Uniform regime mimics Teacher actions regardless of advantage in `code/tests/test_dopd.py`
- [X] T030 [P] [US2] Integration test: Verify DOPD regime switches weighting when advantage gap < 0.1 per FR-002
- [X] T031 [P] [US2] Integration test: Verify DOPD Student shows higher entropy/self-correction when Teacher advantage is low
- [X] T028_test [P] [US2] Unit test: Verify epsilon-guarded division prevents ZeroDivisionError in `code/tests/test_dopd.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Execute Statistical Generalization Analysis (Priority: P3)

**Goal**: Run a statistical comparison (Mann-Whitney U test) of generalization accuracy between DOPD and Uniform regimes across multiple seeds.

**Independent Test**: The analysis script can take the accuracy logs from the training runs and output a p-value and effect size, confirming or refuting the hypothesis.

### Implementation for User Story 3

- [X] T035 [US3] Create `code/scripts/run_experiment.py`: Orchestrate multiple independent seeds with distinct training/test seeds. Algorithm: `seed_test = seed_train + offset`, where `offset` is a fixed positive integer distinct from zero.. Verification: Assert `len(set(train_seeds) & set(eval_seeds)) == 0`. Log to `data/raw/`, ensuring count >= 50 per FR-005 & FR-007
- [X] T036 [US3] Create `code/scripts/aggregate_results.py`: Aggregate logs and generate `data/processed/` metrics
- [X] T032 [US3] Implement `code/analysis/stats.py`: Execute one-tailed Mann-Whitney U test (H0: mean(DOPD) <= mean(Uniform)) on accuracy logs per FR-005
- [X] T033 [US3] Implement `code/analysis/stats.py`: Calculate effect size; if effect size < 0.5, log entry "Study is exploratory" and write to `data/processed/` per FR-005
- [X] T039 [US3] Implement `code/analysis/stats.py`: Calculate and compare convergence steps between DOPD and Uniform regimes. Convergence defined as: when action entropy stabilizes (std dev < 0.01 over 50 steps) OR reward variance < 0.05 per SC-003

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T040 [P] [US3] Contract test: Verify Mann-Whitney U test output format (p-value, direction) in `code/tests/test_stats.py`
- [X] T041 [P] [US3] Integration test: Verify distinct random seeds for training vs. evaluation per FR-007
- [X] T060 [P] [US3] Contract test: Add test function `test_seed_separation` to `code/tests/test_stats.py` asserting `seed_train != seed_test` per FR-007

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T055 [P] Calculate and Report CV: Implement Coefficient of Variation (CV) calculation in `code/analysis/stats.py`. Generate final reproducibility report JSON at `data/processed/reproducibility_metrics.json` containing keys: `cv_value`, `mean_accuracy`, `std_dev`, linking CV calculation to artifact per SC-005
- [X] T043 [P] Implement checksumming utility in `code/utils/checksum.py` to generate hashes for artifacts
- [X] T044 [P] Create `code/scripts/record_hashes.py` to invoke checksum utility and record hashes in `state/projects/...yaml` per Constitution Principle III & V
- [X] T045 [P] Refactor logging to structured JSON format for easier parsing
- [X] T062 [P] Remove unused imports and dead code from all modules
- [X] T047 [P] Documentation updates in `docs/` and `README.md`
- [X] T053 [P] Profile simulation speed to verify the performance constraint for multiple seeds per Plan Performance Goals
- [X] T054 [P] Optimize simulation loop to meet temporal constraints if profiling fails
- [X] T057 [P] Additional unit tests for edge cases (noise signal `H`, sparse rewards) - *Note: Core noise test moved to T057a*
- [X] T058 [P] Run `quickstart.md` validation
- [X] T059 [P] Verify all artifacts checksummed and versioned per Constitution Principle V

---

## Phase 7: Data Integrity & Execution Safety (Revision)

**Purpose**: Address execution gate concerns regarding data loading safety, reproducibility verification, and failure modes.

- [ ] T063 [US1] [Depends: T012] Implement `code/env/privilege_mdp.py`: Add explicit assertion in `reset()` and `step()` to raise `RuntimeError` if `H` is accidentally exposed in `student_obs` to enforce strict information asymmetry at runtime
- [ ] T064 [US2] [Depends: T022a] Implement `code/agents/baseline_estimator.py`: Add explicit assertion that `V_baseline` convergence check (std dev < 0.01) is met before returning, raising `RuntimeError` if max iterations are exceeded to prevent noisy baselines
- [ ] T065 [US2] [Depends: T022] Implement `code/training/dopd_distillation.py`: Add explicit logging of the `lambda` switch event (Uniform vs. Min-Max) to `data/raw/training_log.json` for every seed to verify FR-002 fallback logic
- [ ] T066 [US3] [Depends: T035] Implement `code/scripts/run_experiment.py`: Add explicit check to verify `seed_train` and `seed_test` sets are disjoint before execution, raising `RuntimeError` if intersection is non-empty per FR-007
- [ ] T067 [US3] [Depends: T032] Implement `code/analysis/stats.py`: Add explicit check for `n_samples >= 50`. If `n_samples < 50`, log "Study is exploratory due to insufficient samples", set `is_exploratory=True`, and proceed with Mann-Whitney U test (do NOT raise RuntimeError) per FR-005
- [ ] T068 [US3] [Depends: T033] Implement `code/analysis/stats.py`: Add explicit logging of "Study is exploratory" flag to `data/processed/statistical_summary.json` when Cliff's Delta < 0.5 per FR-005

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Integrity (Phase 7)**: Must be integrated into all previous phases before final execution

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
- Phase 7 safety tasks are NOT parallel with their target modules; they depend on them.

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
- **Critical**: All Phase 7 tasks are mandatory for execution gate approval to ensure no synthetic fallbacks or data integrity violations.
