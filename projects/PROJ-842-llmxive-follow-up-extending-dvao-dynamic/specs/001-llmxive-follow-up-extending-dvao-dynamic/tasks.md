# Tasks: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

**Input**: Design documents from `/specs/001-llmxive-noise-scaling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [ ] T001 [P] Initialize project directory structure: Create `src/`, `tests/`, `data/`, `scripts/`, `docs/` directories and their subdirectories (`src/derivation`, `src/simulation`, `src/analysis`, `tests/unit`, `tests/contract`, `tests/integration`, `data/raw`, `data/processed`) along with `__init__.py` files for all Python packages and `.gitkeep` files for data directories.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes critical memory optimizations to ensure a constrained memory environment is met from the start.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T014 [P] Create `src/config/defaults.yaml` with hyperparameters: `N` (a range of values including 10, 20, 50), `k` (window size ratios), `seeds`, `noise_correlation` (ρ ∈ {, 0.2, 0.5})
- [X] T015 [P] Implement `src/simulation/synthetic_mdp.py` with: (1) tabular MDP generation with N objectives using random linear combinations of state features, (2) explicit support for noise correlation parameter ρ across a range of values including the absence of correlation as required by FR-009, (3) deterministic seeded random state management
- [X] T016 [P] Implement `src/simulation/heuristic.py` for the "Moving-Window Heuristic" variance estimation using last k steps (configurable k < rollout group size)
- [X] T017 [P] Create `src/simulation/runner.py` with main() function accepting --n-objectives, --seed, --noise-correlation arguments, executing CPU-constrained training loops with memory checks (<7GB), and exiting with code 0 on success
- [X] T018 [P] Implement `src/derivation/variance_scaling.py` for symbolic derivation of noise accumulation using sympy, returning a sympy Expr object representing Var(A) as function of N and ε_i
- [ ] T019a [P] Implement inversion logic in `src/derivation/sample_complexity.py` to calculate sample complexity bounds from variance equations. **Deliverable**: Function `calculate_bound(variance_expr, N, epsilon)` returning a sympy expression.
- [ ] T019b [P] Implement string formatting for sample complexity bound in `src/derivation/sample_complexity.py`. **Deliverable**: Function `format_bound_expression(bound_expr)` returning a human-readable string.
- [ ] T019c [P] Create `tests/unit/test_sample_complexity.py` to verify the inversion logic and string formatting. **Deliverable**: Unit tests for `calculate_bound` and `format_bound_expression`.
- [ ] T021a [P] Implement **PAIRED T-TEST** function `run_paired_ttest(heuristic_vals, fullbatch_vals)` in `src/analysis/stats.py` comparing Heuristic variance vs. Full-Batch Empirical variance. **Deliverable**: Function returning p-value and statistic. **Note**: This implements the Plan's revision (Paired T-Test). **Overrides Spec FR-006**.
- [ ] T021b [P] Implement stability check function `run_stability_check(heuristic_vals, fullbatch_vals)` in `src/analysis/stats.py`. **Deliverable**: Function returning boolean and ratio stats; verifies ratio remains within [0.9, 1.1] for ≥ 95% of steps. **Note**: Explicitly implements SC-003.
- [ ] T021c [P] Implement sensitivity analysis sweep logic in `src/analysis/stats.py` for window size k. **Deliverable**: Function `run_sensitivity_sweep(...)` returning aggregated results.
- [X] T022 [P] Create `tests/unit/test_derivation.py` to verify symbolic equations simplify correctly
- [X] T023 [P] Create `tests/unit/test_mdp.py` to verify MDP generation determinism and objective counts
- [X] T024 [P] Create `tests/unit/test_heuristic.py` to verify windowed variance calculation logic
- [X] T025 [P] Create `scripts/update_state.py` to compute checksums for `data/` and `code/` (Constitution Principle V)
- [ ] T053 [P] Refactor `src/simulation/runner.py` to use generators instead of lists for trajectory storage to ensure memory efficiency (<7GB) under large N. **Deliverable**: Generator-based trajectory iterator.
- [ ] T054 [P] Create `tests/unit/test_runner_memory.py` to verify memory usage remains <7GB with generators for N=50.
- [ ] T055 [P] Refactor `src/analysis/stats.py` to use batch processing for variance calculations to reduce memory footprint. **Deliverable**: Batched variance calculation function.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Theoretical Derivation of Noise Scaling Law (Priority: P1) 🎯 MVP

**Goal**: Mathematically derive the theoretical lower bound on sample complexity for Pareto optimality as a function of N and independent noise.

**Independent Test**: The system generates a mathematical document containing the closed-form derivation of variance accumulation as a function of N.

### Implementation for User Story 1

- [ ] T026 [US1] Verify `src/derivation/variance_scaling.py` outputs correct closed-form equation for Var(A) as function of N and ε_i
- [ ] T027 [US1] Verify `src/derivation/sample_complexity.py` correctly inverts variance to sample complexity bound. **Depends on**: T019a, T019b, T019c.
- [ ] T028 [US1] Add explicit assumption logging (i.i.d. noise) to derivation output. **Format**: Add JSON field `assumptions: ["i.i.d. noise"]` in `docs/theoretical_derivation.md` and log to stdout. **Verification**: Run `python src/derivation/sample_complexity.py --verify-assumptions`.
- [X] T029 [US1] Create `docs/theoretical_derivation.md` with required sections: (1) closed-form equation for Var(A) as function of N and ε_i, (2) sample complexity bound derivation, (3) explicit assumptions list, (4) verification results from sympy. **Depends on**: T027 completion.
- [X] T030 [US1] Create `docs/peer_review_checklist.md` with verification criteria for SC-001 alternative path, including algebraic consistency checklist and peer review sign-off template.
- [ ] T031b [US1] **Execute Peer Review**: Run the peer review checklist defined in T030 against the derivation in T029. **Deliverable**: Update `docs/peer_review_checklist.md` with timestamp, reviewer initials, and `status: PASSED` or `status: FAILED`. **Verification**: File must contain `status: PASSED`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Synthetic Environment Generation & Heuristic Implementation (Priority: P2)

**Goal**: Generate synthetic multi-objective tabular MDPs (N ∈ {, 10, 20, 50}) and implement the Moving-Window Heuristic for variance estimation.

**Independent Test**: The system runs a simulation script that instantiates environments for N=50 and executes multiple episodes using the Moving-Window Heuristic without memory errors.

### Implementation for User Story 2

- [X] T031 [US2] Verify `src/simulation/synthetic_mdp.py` generates correct tabular MDPs with N objectives and noise correlation parameter ρ
- [X] T032 [US2] Verify `src/simulation/heuristic.py` correctly calculates variance using only last k steps
- [X] T033 [US2] Integrate `src/simulation/runner.py` with memory footprint checks (<7GB) and CPU constraints, ensuring it uses foundational MDP and heuristic modules
- [ ] T034 [US2] Add logic to handle edge case where N > 50. **Behavior**: If N > 50, reduce N to 50, log warning "N reduced to 50 for memory constraints", and proceed. **Verification**: Run with N=100 and verify warning log and successful completion with N=50.
- [ ] T035 [US2] Add logging calls to output empirical variance and distance to Pareto frontier in `data/processed/empirical_results.json`. **Trigger**: After every N sweep completion. **Schema**: `{n_objectives, empirical_variance, pareto_distance, timestamp}`. **Verification**: Run `python src/simulation/runner.py --n=50` and verify file exists with schema.
- [X] T036 [US2] Extend `src/simulation/synthetic_mdp.py` to support sensitivity analysis for noise correlation structure (ρ ∈ {0, 0.2, 0.5}) as required by FR-009
- [ ] T037 [US2] Verify MDP generation is deterministic with seeded random states
- [ ] T052b [US2] **Run Noise Correlation Sweep**: Execute simulation with noise correlation parameter ρ ∈ {0.2, 0.5} and log results to verify if the scaling law holds. **Deliverable**: `data/processed/correlation_sweep_results.json`. **Verification**: File exists with results for all three ρ values.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation & Sensitivity Analysis (Priority: P3)

**Goal**: Perform statistical validation (Paired T-Test: Heuristic vs. Full-Batch) and sensitivity analysis on window size k. **Note**: The Plan explicitly revises the validation strategy to use Paired T-Test and Correlation Analysis, replacing the Spec's one-sample t-test and coincidence metrics.

**Independent Test**: The system outputs a statistical report containing p-values from paired t-tests and a table showing variation in convergence rates as k varies.

### Implementation for User Story 3

- [ ] T038 [US3] Implement **PAIRED T-TEST** in `src/analysis/stats.py` comparing Heuristic variance vs. Full-Batch Empirical variance for each N. **Deliverable**: Function `run_paired_ttest` returning p-value. **Note**: This implements the Plan's revision (Paired T-Test). **Overrides Spec FR-006/SC-002**.
- [ ] T039 [US3] Implement stability check: ratio of heuristic/full-batch variance must remain within [0.9, 1.1] for ≥ 95% of steps. **Deliverable**: Function `run_stability_check` and output file `data/processed/stability_report.json`. **Note**: Explicitly implements SC-003.
- [ ] T040a [US3] Define window size k sweep parameters (k ∈ {small values} of rollout size) in `src/config/defaults.yaml`.
- [ ] T040b [US3] Implement sensitivity analysis sweep loop for window size k in `src/analysis/stats.py`.
- [ ] T040c [US3] Implement result aggregation for sensitivity sweep. **Deliverable**: Function `aggregate_sweep_results(...)` returning a summary table.
- [ ] T040d [US3] Create unit test for sweep output. **Deliverable**: `tests/unit/test_sensitivity_sweep.py`.
- [ ] T042 [US3] Compute **Pearson/Spearman correlation coefficient** between variance estimation error (Heuristic vs. Full-Batch) and distance to Pareto frontier. **Note**: This implements Plan's revised SC-002 (Correlation), replacing Spec's coincidence metric. **Plan Revision Note**: Overrides Spec SC-002.
- [ ] T043 [US3] Determine failure point N (smallest N where p-value < 0.05 for paired test) and verify correlation with Pareto distance. **Note**: Verify correlation, not exact coincidence. **Plan Revision Note**: Overrides Spec SC-002.
- [ ] T044 [US3] Generate final statistical report in `data/processed/statistical_report.json`. **Command**: `python src/main.py --run-full-sweep`. **Keys**: `p_value_paired`, `n_objectives`, `k_window`, `correlation_coefficient`, `failure_point_n`, `stability_ratio`. **Verification**: Verify all keys present. **Depends on**: T035. **Plan Revision Note**: Overrides Spec SC-002.
- [ ] T045 [US3] Add logic to handle non-Gaussian noise distributions and log deviations (Assumptions)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 [P] Update `docs/quickstart.md` with instructions for running the full experiment suite
- [ ] T050 [P] Run `scripts/update_state.py` to verify artifact checksums and update `state/` files
- [ ] T051 Validate `quickstart.md` by running a full end-to-end execution on a local CPU-only environment

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
- **FR-006 Compliance**: **Paired T-Test** (Heuristic vs. Full-Batch) is the PRIMARY validation method. One-sample t-test is FORBIDDEN per Plan.
- **SC-002 Compliance**: **Correlation** analysis is the success metric. Exact coincidence is DISCARDED per Plan.
- **FR-009 Compliance**: Noise correlation parameter ρ ∈ {0, 0.2, 0.5} must be supported from foundational phase.
- **SC-001 Compliance**: Both symbolic math engine verification AND peer review checklist must be implemented.
- **Plan vs Spec Note**: This tasks.md follows the **Plan's** methodological revisions (Paired T-Test, Correlation) which supersede the **Spec's** original requirements (One-sample T-Test, Coincidence) to avoid tautology.
- **Memory Optimization**: Tasks T053, T054, T055 (Phase 2) ensure memory efficiency is implemented before heavy runs.