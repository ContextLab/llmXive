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
- [X] T038 [P] Implement Seed Manager: Create `code/utils/seed_manager.py` to define and generate distinct seed ranges: Train (0-49), Eval (50-99), Baseline (1000-1099). **Implementation**: Use `np.random.RandomState(master_seed=42)` to generate these ranges deterministically. Output a `seed_manifest.json` with these ranges. Assert `len(set(train_seeds) & set(eval_seeds)) == 0` and `len(set(train_seeds) & set(baseline_seeds)) == 0`. This task defines the seed constraints used by all downstream tasks.
- [ ] T066 [P] Reconcile run-book vs implementation: Verify `code/main.py` exists or the run-book (quickstart.md/plan.md) has been updated to invoke the correct script (`code/scripts/run_experiment.py`). If `code/main.py` is missing, update the run-book to use the existing script. Mark complete once verified. **This task is a prerequisite for T035.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct Discrete Privilege Illusion MDP Environment (Priority: P1) 🎯 MVP

**Goal**: Create a synthetic, discrete-state MDP where a Teacher has a hidden privileged signal `H` and a Student only sees `O`, ensuring information asymmetry.

**Independent Test**: The environment can be instantiated and queried to confirm that the Student's observation space strictly excludes the privileged variable while the Teacher's does not, and that optimal policy requires the privileged variable.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/env/privileged_grid.py`: Define discrete grid-world with hidden state `H` and observable `O`, enforcing max grid dimension 10x10 (RAM < 7GB) per FR-008. Explicitly project state vector to first 2 dimensions for Student observation (`O = state[:, 0:2]`) per FR-001. Add explicit assertion in `reset()` and `step()` to raise `RuntimeError` if `H` is accidentally exposed in `student_obs` to enforce strict information asymmetry at runtime.
- [X] T013 [US1] Implement `code/env/privileged_grid.py`: Define transition logic where `H` dictates optimal action to ensure Student fails without it
- [X] T014 [US1] Implement `code/agents/teacher.py`: Create Oracle policy with full state access `(O, H)`
- [X] T014b [US1] [Depends: T012, T014] Implement `code/agents/teacher.py`: Implement the **Oracle Policy Logic** using Value Iteration. **Algorithm**: Value Iteration with discount factor `gamma=0.99`. **Convergence**: Stop when max difference between successive value functions < 1e-6. **Output**: Compute and cache the optimal Q-table `Q(s, a)` for all states using the full state (O, H). This Q-table is required for T022's advantage gap calculation.
- [ ] T015 [US1] Implement `code/agents/student.py`: Create Tabular Q-table agent with partial state access `O`

### Tests for User Story 1

> **NOTE: Tests must be written and fail before implementation tasks run.**

- [X] T016 [US1] Contract tests: Add test functions `test_teacher_student_observation_spaces`, `test_optimal_action_dependency`, and `test_seed_consistency` to `code/tests/test_env.py` verifying Teacher observes `(O, H)`, Student observes only `O`, optimal action depends on `H`, and state distribution consistency across seeds.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Implement DOPD vs. Uniform Supervision Training Loops (Priority: P2)

**Goal**: Implement Uniform On-Policy Distillation (baseline) and DOPD (dynamic weighting based on advantage gap) training regimes.

**Independent Test**: The training loops can be executed on the discrete MDP, logging the Student's policy updates and action distributions to verify that DOPD reduces reliance on the Teacher's actions when the advantage gap is low.

### Implementation for User Story 2

- [X] T021a [US2] Implement `code/agents/random_policy.py`: Create a Random Policy Agent that generates actions uniformly at random from the action space for all states. This agent is required for baseline estimation (T022a).
- [X] T022a [US2] [Depends: T012, T021a, T038] Implement `code/agents/baseline_estimator.py`: Instantiate Random Policy Agent (T021a) to generate trajectories. Run Monte Carlo simulation using these trajectories until std dev of returns < 0.01 for 100 consecutive batches to compute state-value function `V_baseline(s)` per FR-002. **Parameters**: Batch size = 10 episodes per batch. Max iterations = 10,000. Convergence check: Stop if std dev < 0.01 for 100 consecutive batches. Safety: If max iterations exceeded and no valid estimate exists, log warning, set `is_converged=False`, and return last valid estimate to prevent silent bias per FR-002. **MANDATORY**: Use seed range 1000-1099 as defined in T038.
- [ ] T022 [US2] [Depends: T014b, T022a, T024] Implement `code/training/dopd_distillation.py`: Calculate Teacher advantage gap (Q(s,a) - V_baseline(s)) using output from T022a and T014b per FR-002. Return the calculated gap for the current state-action pair. Log `lambda` switch event (Uniform vs. Min-Max) to `data/raw/training_log.json` for every seed to verify FR-002 fallback logic. **Note**: Logging is a side-effect; the calculation logic does not depend on T025 initialization.
- [ ] T023 [US2] [Depends: T022, T025] Implement `code/training/dopd_distillation.py`: Implement Dynamic Weighting & Min-Max Fallback. Measure dynamic range of advantage gap (max - min) over the **current episode's batch** (rolling window of a fixed number of episodes to ensure stability). If dynamic range < 0.1, trigger min-max normalization switch per FR-002. Formula: `lambda = (A_gap - min) / (max - min)`. Add epsilon-guarded division (epsilon=1e-8) to prevent ZeroDivisionError; if division fails, set `lambda=1.0` per Edge Cases and FR-002. Log `lambda` switch event to `data/raw/training_log.json` for every seed to verify FR-002 fallback logic.
- [X] T028 [US2] [Depends: T023] Implement `code/training/dopd_distillation.py`: Implement Safety Checks for Sparse Signals. Wrap division operations in `try/except ZeroDivisionError`. Fallback: If error, set `lambda = 1.0` (Uniform mode). Test: Unit test with zero denominator inputs.
- [X] T024 [US2] Implement `code/training/uniform_distillation.py`: Fixed-weight distillation loss logic (independent of advantage gap). Add epsilon-guarded division (epsilon=1e-8) to prevent ZeroDivisionError; if division fails, set `lambda=1.0` per Edge Cases and FR-002.
- [ ] T025 [US2] [Depends: T011] Implement `code/utils/logging.py`: Initialize `data/raw/training_log.json` file structure with schema. Log training accuracy, convergence steps, and action entropy at every training step to `data/raw/training_log.json` in JSON format per FR-006.
- [X] T019 [US2] Implement `code/analysis/generalization_test.py`: Masked evaluation logic to remove `H` during inference
- [X] T020 [US2] Implement `code/analysis/generalization_test.py`: Calculate performance drop metric: `(acc_unmasked - acc_masked) / R_max`
- [X] T057a [US2] [Edge Case] Implement `code/tests/test_dopd.py`: Unit test for 'noise signal H' scenario where privileged signal is uncorrelated with optimal action; verify system handles this without crashing per Edge Cases

### Tests for User Story 2

> **NOTE: Tests must be written and fail before implementation tasks run.**

- [X] T029 [US2] Integration test: Verify Uniform regime mimics Teacher actions regardless of advantage in `code/tests/test_dopd.py`
- [ ] T030 [US2] [Depends: T028, T025] Integration test: Verify DOPD regime switches weighting when advantage gap < 0.1 per FR-002. Run DOPD with low advantage gap and verify `lambda` switch event is logged to `data/raw/training_log.json`.
- [X] T031 [US2] [Depends: T028, T025] Integration test: Verify DOPD Student shows higher entropy/self-correction when Teacher advantage is low. Run DOPD with low advantage gap and verify Student entropy increases in logs.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Execute Statistical Generalization Analysis (Priority: P3)

**Goal**: Run a statistical comparison (Mann-Whitney U test) of generalization accuracy between DOPD and Uniform regimes across multiple seeds.

**Independent Test**: The analysis script can take the accuracy logs from the training runs and output a p-value and effect size, confirming or refuting the hypothesis.

### Implementation for User Story 3

- [X] T035 [US3] [Depends: T038, T028, T024, T022, T066] Create `code/scripts/run_experiment.py`: Orchestrate multiple independent seeds with distinct training/test seeds. **MANDATORY**: Invoke the training loops defined in T022 (DOPD) and T024 (Uniform). **Seed Allocation**: Generate multiple distinct seeds for DOPD and multiple distinct seeds for Uniform to conduct a comprehensive set of runs.. **Algorithm**: Generate distinct sets using T038 (Train 0-49, Eval 50-99). **Verification**: Assert `len(set(train_seeds) & set(eval_seeds)) == 0`. **Hard Constraint**: If the total number of successful runs for either regime is < 50, raise `RuntimeError` and abort execution immediately. Log to `data/raw/`, ensuring count >= 50 per FR-005 & FR-007. Add explicit check to verify `seed_train` and `seed_test` sets are disjoint before execution, raising `RuntimeError` if intersection is non-empty per FR-007. **MANDATORY**: Ensure distinct state generation processes (e.g., different seed offsets for MDP initialization vs. action sampling) as required by FR-007.
- [X] T036 [US3] Create `code/scripts/aggregate_results.py`: Aggregate logs and generate `data/processed/` metrics
- [X] T032 [US3] Implement `code/analysis/stats.py`: Execute one-tailed Mann-Whitney U test (H0: mean(DOPD) <= mean(Uniform)) on accuracy logs per FR-005. **Assumption**: This task assumes >=50 samples per group as enforced by T035. If `n_samples < 50` is detected (should not happen), raise `RuntimeError` as the hard constraint was violated upstream. Do NOT proceed with exploratory mode.
- [X] T033 [US3] Implement `code/analysis/stats.py`: Calculate effect size; if effect size < 0.5, log entry "Study is exploratory" and write to `data/processed/` per FR-005. Calculate convergence steps between DOPD and Uniform regimes. Convergence defined as: when action entropy stabilizes (std dev < 0.01 over 50 steps) OR reward variance < 0.05 per SC-003. Add explicit logging of "Study is exploratory" flag to `data/processed/statistical_summary.json` when Cliff's Delta < 0.5 per FR-005.
- [X] T034 [US3] [Depends: T036, T033] Implement `code/analysis/stats.py`: Calculate Coefficient of Variation (CV) for generalization accuracy. Formula: $CV = \frac{\sigma}{\mu}$. Write CV value to `data/processed/statistical_summary.json` per SC-005.
- [X] T055 [US3] [Depends: T034, T036, T044] Calculate and Report CV: Implement Coefficient of Variation (CV) calculation in `code/analysis/stats.py`. Generate final reproducibility report JSON at `data/processed/reproducibility_metrics.json` containing keys: `cv_value`, `mean_accuracy`, `std_dev`, linking CV calculation to artifact per SC-005. **MANDATORY**: Ensure `reproducibility_metrics.json` is included in the `state/` artifact hashing process (Constitution Principle V). **Implementation**: Compute SHA-256 hash of `reproducibility_metrics.json` and record it in `state/projects/PROJ-982-llmxive-follow-up-extending-dopd-dual-on.yaml` under `artifact_hashes`.
- [ ] T065 [US3] [Depends: T035, T028] Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist. Update T035 to explicitly invoke T022 and T024.

### Tests for User Story 3

> **NOTE: Tests must be written and fail before implementation tasks run.**

- [X] T040 [US3] Contract test: Verify Mann-Whitney U test output format (p-value, direction) in `code/tests/test_stats.py`
- [X] T041 [US3] Integration test: Verify distinct random seeds for training vs. evaluation per FR-007
- [X] T060 [US3] Contract test: Add test function `test_seed_separation` to `code/tests/test_stats.py` asserting `seed_train != seed_test` per FR-007

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

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
- [X] T064 [US2] [Depends: T022a] Implement `code/tests/test_baseline.py`: Add contract test for `V_baseline` convergence. Assert V_baseline convergence (std dev < 0.01) is met; if max iterations exceeded per FR-002/T022a, raise RuntimeError. Ensure test explicitly validates the error condition logic defined in FR-002.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Safety Logic**: Integrated into implementation tasks (T012, T022a, T022, T035, T032) during their implementation, not as a separate phase.

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
Task: "Add test functions test_teacher_student_observation_spaces, test_optimal_action_dependency, test_seed_consistency to code/tests/test_env.py"

# Launch all models for User Story 1 together:
Task: "Implement code/env/privileged_grid.py"
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
- **Critical**: All safety logic is integrated into implementation tasks to ensure execution gate approval.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T065 Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.

<!-- Revision: Addressed T022 missing implementation status -->
- [ ] T066 [US3] [Depends: T035, T028] Create `code/scripts/run_experiment.py` (if not already covered by T035) or update T035 to explicitly invoke the DOPD and Uniform training loops defined in T022 and T024, ensuring the 50-seed loop correctly calls both regimes and logs results to `data/raw/training_log.json` before aggregation.
