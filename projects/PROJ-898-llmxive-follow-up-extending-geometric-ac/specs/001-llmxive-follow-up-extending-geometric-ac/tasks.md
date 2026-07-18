# Tasks: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

**Input**: Design documents from `/specs/001-llmxive-gam-symbolic-planner/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
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

- [ ] T001a [P] Create project root structure per implementation plan (`projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/`)
- [ ] T001b [P] Create `code/`, `data/`, `tests/` directories
- [ ] T001c [P] Create `.gitkeep` files in all data subdirectories (`data/raw`, `data/generated`, `data/results`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.11 project with pinned dependencies (`requirements.txt`: pybullet, torch (cpu), cvxpy, diffcp, scipy, pandas, numpy, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 Setup data directory structure (`data/raw`, `data/generated`, `data/results`) and `.gitkeep` files
- [X] T005 [P] Implement `code/utils.py` with logging, deterministic seeding (numpy/torch), and SHA-256 hashing utilities
- [X] T006 [P] Create `code/gfm_wrapper.py` skeleton for loading frozen GFM weights (CPU-only, `eval()` mode)
- [ ] T007a [P] Create `code/config.yaml` defining experiment parameters: `topology_counts`, `timeout_limits` (300s), `seed`, `trial_count` (50)
- [ ] T007b [P] Implement `code/config.py` loader to parse `code/config.yaml` and expose parameters as a typed configuration object
- [ ] T008 Configure CI workflow for GitHub Actions (multi-core x_64, timeout period, no GPU)
- [ ] T008a [P] Implement CPU-only profiling script to simulate solver execution and verify <300 seconds/step assumption on 2-core hardware (FR-004)
- [ ] T008b [P] Implement script to calculate total experiment time (per_step_time * steps_per_trial * number_of_trials) and verify against a predefined confidence interval limit

The research question, method, and references remain unchanged as per the planning document requirements. (SC-005)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Topology-Shift Test Set Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of manipulation tasks with novel kinematic chains and deformable materials using PyBullet, ensuring zero overlap with original GAM training data.

**Independent Test**: Run generation script; verify output contains valid physics states for a diverse set of distinct topologies; confirm checksum hash differs from original GAM metadata.

### Implementation for User Story 1

- [X] T006a [US1] Implement logic to ingest and validate 'original GAM training metadata' from `data/raw/gam_baseline_metadata.json` for baseline comparison (Prerequisite for T012)
- [X] T009 [US1] Implement `code/data_generation.py` to generate a unified 'Topology-Shift Test Set' containing BOTH novel kinematic chains (variable hinge counts) AND deformable materials (soft ropes, cloth) in PyBullet, generating at least 50 distinct topologies, ensuring zero overlap with original GAM training data (FR-001) by computing SHA-256 of generated topology IDs and comparing against `data/raw/gam_baseline_metadata.json`
- [ ] T010 [US1] Add logic to record latent inputs and ground-truth actions for every timestep in `data/generated/`
- [ ] T011 [US1] Implement error handling for physics simulation failures (crash recovery, state logging)
- [X] T012 [US1] Implement metadata checksumming for the unified test set and verify its hash against the baseline metadata at `data/raw/gam_baseline_metadata.json` to confirm zero overlap (FR-001)
- [X] T013 [US1] Create `scripts/generate_test_set.py` to execute generation with configurable seeds
- [ ] T022a [US1] [US3] Implement script `code/baseline_runner.py` to run the original GAM implementation (neural predictor) on the test set generated in T009; load weights from `data/raw/gfm_baseline.pt`; output results to `data/results/`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Symbolic Latent Planner Execution (Priority: P2)

**Goal**: Execute frozen GFM encoder/decoder and inject a differentiable symbolic solver to enforce geometric constraints in 3D space, running entirely on CPU.

**Independent Test**: Load frozen GFM, run symbolic planner on a single P1 test case, decode action, verify constraint satisfaction in PyBullet without GPU.

### Implementation for User Story 2

- [X] T014 [US2] Implement `code/symbolic_solver.py` using `cvxpy`/`diffcp` for differentiable constraint satisfaction (rigid/soft body) including explicit logic for 'non-penetration' and 'joint limits' in physical 3D coordinates (Prerequisite for T016, T017, T018)
- [X] T016 [US2] Integrate `code/gfm_wrapper.py` (T006) and `code/symbolic_solver.py` (T014) to encode observations to latent space and decode solver outputs to 3D actions (Depends on T006 and T014)
- [ ] T017 [US2] Implement timeout mechanism for solver steps (A maximum time limit per step will be established.) to prevent CI hangs (Edge Case handling)
- [ ] T018 [US2] Implement "infeasible" flag logic when constraints cannot be satisfied, recording trial as failure
- [ ] T019 [US2] Implement latent drift detection (Mahalanobis distance) and flagging for out-of-distribution inputs
- [ ] T019b [US2] [FR-003] Implement and run gradient verification test to ensure gradients flow from the constraint violation loss ONLY to the solver parameters, with NO backpropagation through frozen GFM decoder weights, validating the decoupling of symbolic logic from decoder fidelity
- [X] T020 [US2] Create `code/inference_pipeline.py` to orchestrate encode -> solve -> decode -> simulate loop (Depends on T019b)
- [ ] T021 [US2] Add logging for inference latency (ms) and success/failure status for each trial
- [ ] T021b [US2] [SC-001] Implement logic to measure and record the success metric: count consecutive timesteps where collision_flag=0; if (count * timestep_interval) >= 1.0s, set success=true; verify manipulated object reaches 'target zone (center within 5cm)' in raw data logs for each trial

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Statistical Analysis (Priority: P3)

**Goal**: Compare symbolic-latent approach vs. baseline GAM using Fisher's Exact Test and paired t-test on success rates and latency.

**Independent Test**: Run analysis script on collected results; verify report includes p-values, CIs, and effect sizes for both metrics.

### Implementation for User Story 3

- [ ] T023 [P] [US3] Implement `code/analysis.py` to load results from `data/results/` for both symbolic (T021/T021b) and baseline (T022a) approaches; expect CSV schema: columns `trial_id`, `approach`, `success`, `latency_ms`, `timestamp`
- [ ] T024 [US3] Implement Fisher's Exact Test for binary success/failure outcomes (FR-006)
- [ ] T025 [US3] Implement paired t-test for inference latency comparisons (FR-006)
- [ ] T026 [US3] Calculate and report % confidence intervals and Cohen's d effect sizes
- [ ] T027 [US3] Generate final report `data/results/analysis_report.md` as a Markdown table with columns: Metric, Symbolic, Baseline, Difference, P-value, 95% CI, Effect Size; state null hypothesis rejection status (α=0.05) and validate SC-001 (one-second duration)
- [ ] T028 [US3] Create `scripts/run_analysis.py` to execute the full statistical comparison pipeline

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Update `README.md` with CLI usage instructions and project structure
- [ ] T030 Code cleanup and refactoring of `code/` modules
- [ ] T031 [P] Refactor `code/symbolic_solver.py` to use sparse matrix representation for constraint matrices to reduce memory overhead and improve solve time
- [ ] T032 [P] Additional unit tests for solver constraints and latent drift detection in `tests/unit/`
- [ ] T033 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T009 (data gen) for input data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T021/T021b (inference results) and T022a (baseline results) for input data

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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