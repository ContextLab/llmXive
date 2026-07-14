# Tasks: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

**Input**: Design documents from `/specs/001-llmxive-noise-scaling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create `src/` directory structure
- [ ] T002 [P] Create `tests/` directory structure
- [ ] T003 [P] Create `data/` directory structure
- [ ] T004 [P] Create `scripts/` directory structure
- [ ] T005 [P] Create `docs/` directory structure
- [ ] T006 [P] Create `src/derivation/__init__.py`
- [ ] T007 [P] Create `src/simulation/__init__.py`
- [ ] T008 [P] Create `src/analysis/__init__.py`
- [ ] T009 [P] Create `tests/unit/__init__.py`
- [ ] T010 [P] Create `tests/contract/__init__.py`
- [ ] T011 [P] Create `tests/integration/__init__.py`
- [ ] T012 [P] Create `data/raw/.gitkeep`
- [ ] T013 [P] Create `data/processed/.gitkeep`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T014 [P] Create `src/config/defaults.yaml` with hyperparameters: `N` (5, 10, 20, 50), `k` (window size ratios), `seeds`, `noise_correlation` (ρ ∈ {0, 0.2, 0.5})
- [ ] T015 [P] Implement `src/simulation/synthetic_mdp.py` with: (1) tabular MDP generation with N objectives using random linear combinations of state features, (2) explicit support for noise correlation parameter ρ ∈ {0, 0.2, 0.5} as required by FR-009, (3) deterministic seeded random state management
- [ ] T016 [P] Implement `src/simulation/heuristic.py` for the "Moving-Window Heuristic" variance estimation using last k steps (configurable k < rollout group size)
- [ ] T017 [P] Create `src/simulation/runner.py` with main() function accepting --n-objectives, --seed, --noise-correlation arguments, executing CPU-constrained training loops with memory checks (<7GB), and exiting with code 0 on success
- [ ] T018 [P] Implement `src/derivation/variance_scaling.py` for symbolic derivation of noise accumulation using sympy, returning a sympy Expr object representing Var(A) as function of N and ε_i
- [ ] T019 [P] Implement `src/derivation/sample_complexity.py` to invert variance equations to sample complexity bounds, returning closed-form equation as string
- [ ] T020 [P] Implement `src/analysis/pareto.py` to calculate distance to theoretical Pareto frontier for given policy and reward functions
- [ ] T021 [P] Implement `src/analysis/stats.py` with: (1) one-sample t-test function for deviation from theoretical bound, (2) paired t-test function for heuristic vs full-batch, (3) sensitivity analysis functions
- [ ] T022 [P] Create `tests/unit/test_derivation.py` to verify symbolic equations simplify correctly
- [ ] T023 [P] Create `tests/unit/test_mdp.py` to verify MDP generation determinism and objective counts
- [ ] T024 [P] Create `tests/unit/test_heuristic.py` to verify windowed variance calculation logic
- [ ] T025 [P] Create `scripts/update_state.py` to compute checksums for `data/` and `code/` (Constitution Principle V)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Theoretical Derivation of Noise Scaling Law (Priority: P1) 🎯 MVP

**Goal**: Mathematically derive the theoretical lower bound on sample complexity for Pareto optimality as a function of N and independent noise.

**Independent Test**: The system generates a mathematical document containing the closed-form derivation of variance accumulation as a function of N.

### Implementation for User Story 1

- [ ] T026 [US1] Verify `src/derivation/variance_scaling.py` outputs correct closed-form equation for Var(A) as function of N and ε_i
- [ ] T027 [US1] Verify `src/derivation/sample_complexity.py` correctly inverts variance to sample complexity bound
- [ ] T028 [US1] Add explicit assumption logging (i.i.d. noise) to derivation output
- [ ] T029 [US1] Create `docs/theoretical_derivation.md` with required sections: (1) closed-form equation for Var(A) as function of N and ε_i, (2) sample complexity bound derivation, (3) explicit assumptions list, (4) verification results from sympy
- [ ] T030 [US1] Create `docs/peer_review_checklist.md` with verification criteria for SC-001 alternative path, including algebraic consistency checklist and peer review sign-off template

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Synthetic Environment Generation & Heuristic Implementation (Priority: P2)

**Goal**: Generate synthetic multi-objective tabular MDPs (N ∈ {5, 10, 20, 50}) and implement the Moving-Window Heuristic for variance estimation.

**Independent Test**: The system runs a simulation script that instantiates environments for N=50 and executes multiple episodes using the Moving-Window Heuristic without memory errors.

### Implementation for User Story 2

- [ ] T031 [US2] Verify `src/simulation/synthetic_mdp.py` generates correct tabular MDPs with N objectives and noise correlation parameter ρ
- [ ] T032 [US2] Verify `src/simulation/heuristic.py` correctly calculates variance using only last k steps
- [ ] T033 [US2] Integrate `src/simulation/runner.py` with memory footprint checks (<7GB) and CPU constraints, ensuring it uses foundational MDP and heuristic modules
- [ ] T034 [US2] Add logic to handle edge case where N > 50 by degrading state space size or sampling
- [ ] T035 [US2] Add logging calls to output empirical variance and distance to Pareto frontier in `data/processed/empirical_results.json` with schema: {n_objectives, empirical_variance, pareto_distance, timestamp}
- [ ] T036 [US2] Extend `src/simulation/synthetic_mdp.py` to support sensitivity analysis for noise correlation structure (ρ ∈ {0, 0.2, 0.5}) as required by FR-009
- [ ] T037 [US2] Verify MDP generation is deterministic with seeded random states

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation & Sensitivity Analysis (Priority: P3)

**Goal**: Perform statistical validation (one-sample t-test against theoretical bound AND paired t-test) and sensitivity analysis on window size k.

**Independent Test**: The system outputs a statistical report containing p-values from one-sample t-test, paired t-test results, and a table showing variation in convergence rates as k varies.

### Implementation for User Story 3

- [ ] T038 [US3] Implement one-sample t-test in `src/analysis/stats.py` comparing mean deviation of heuristic variance from theoretical lower bound for each N (FR-006 requirement)
- [ ] T039 [US3] Implement paired t-test in `src/analysis/stats.py` comparing Heuristic variance vs. Full-Batch Empirical variance as additional validation
- [ ] T040 [US3] Implement stability check: ratio of heuristic/full-batch variance must remain within [0.9, 1.1] for ≥ 95% of steps
- [ ] T041 [US3] Implement sensitivity analysis sweep for window size k over a range of rollout sizes
- [ ] T042 [US3] Calculate and log false-positive rates where heuristic reports stable but deviation > 5%
- [ ] T043 [US3] Compute correlation between variance estimation error and distance to Pareto frontier
- [ ] T044 [US3] Calculate and verify coincidence point (within ±1 objective count) between statistical failure (p < 0.05) and Pareto frontier distance threshold (>5%) as required by SC-002
- [ ] T045 [US3] Generate final statistical report in `data/processed/statistical_report.json` with required keys: p_value_one_sample, p_value_paired, n_objectives, k_window, correlation_coefficient, coincidence_flag, failure_point_n
- [ ] T046 [US3] Add logic to handle non-Gaussian noise distributions and log deviations (Assumptions)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T047 [P] Update `docs/quickstart.md` with instructions for running the full experiment suite
- [ ] T048 Code cleanup and refactoring for memory efficiency in `src/simulation/runner.py` using generators instead of lists for trajectory storage
- [ ] T049 Refactor `src/analysis/stats.py` to use batch processing for variance calculations to reduce memory footprint
- [ ] T050 [P] Add comprehensive unit tests for `src/analysis/pareto.py`
- [ ] T051 Run `scripts/update_state.py` to verify artifact checksums and update `state/` files
- [ ] T052 Validate `quickstart.md` by running a full end-to-end execution on a local CPU-only environment

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together (if tests requested):
Task: "Contract test for synthetic_mdp in tests/contract/test_synthetic_mdp.py"
Task: "Integration test for runner in tests/integration/test_runner.py"

# Launch all models for User Story 2 together:
Task: "Verify synthetic_mdp.py"
Task: "Verify heuristic.py"
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
- **CPU Constraint**: All simulation tasks must strictly adhere to 7GB RAM limit; avoid storing full history for large N.
- **Real Data**: All synthetic data must be generated deterministically with seeds; no external downloads required for this feature.
- **Validation Independence**: Ensure `src/derivation` and `src/simulation` remain separate to prevent circular logic.
- **FR-006 Compliance**: One-sample t-test against theoretical bound must be implemented as primary validation, paired t-test as additional validation.
- **SC-002 Compliance**: Coincidence point verification (within ±1 objective count) between statistical failure and Pareto distance threshold is mandatory.
- **FR-009 Compliance**: Noise correlation parameter ρ ∈ {0, 0.2, 0.5} must be supported from foundational phase.
- **SC-001 Compliance**: Both symbolic math engine verification AND peer review checklist must be implemented.