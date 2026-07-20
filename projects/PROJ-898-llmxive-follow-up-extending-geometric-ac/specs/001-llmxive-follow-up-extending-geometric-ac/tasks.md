# Tasks: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

**Input**: Design documents from `/specs/001-llmxive-gam-symbolic-planner/`
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

- [ ] T001a [P] Create project root structure per implementation plan (`projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/`)
- [ ] T001b [P] Create `code/`, `data/`, `tests/` directories
- [ ] T001c [P] Create `.gitkeep` files in all data subdirectories (`data/raw`, `data/generated`, `data/results`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.11 project with pinned dependencies (`requirements.txt`: pybullet, torch (cpu, `--index-url https://download.pytorch.org/whl/cpu`), cvxpy, diffcp, scipy, pandas, numpy, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 Setup data directory structure (`data/raw`, `data/generated`, `data/results`) and `.gitkeep` files
- [X] T005 [P] Implement `code/utils.py` with logging, deterministic seeding (numpy/torch), and SHA-256 hashing utilities
- [X] T006 [P] Create `code/gfm_wrapper.py` skeleton for loading frozen GFM weights (CPU-only, `eval()` mode)
- [X] T007a [P] Create `code/config.yaml` defining experiment parameters: `topology_counts`, `timeout_limits` (configurable duration), `seed`, `trial_count` (50)
- [X] T007b [P] Implement `code/config.py` loader to parse `code/config.yaml` and expose parameters as a typed configuration object
- [ ] T008 [P] Create `.github/workflows/ci.yml` to match FR-004: Multi-core x86_64 runner, no GPU/CUDA, with a fixed timeout limit to constrain the duration of the experimental trial, ensuring environment matches the requirement.
- [X] T009a [US1] Create `data/raw/gam_baseline_metadata.json` with schema `{"topology_ids": ["string"], "object_types": ["string"]}` containing baseline topology IDs to be used for zero-overlap verification in T009-hash
- [X] T022a [US3] [P] Implement `code/baseline_runner.py` skeleton for running the original GAM implementation (neural predictor) on the test set generated in T009; load weights from `data/raw/gfm_baseline.pt`; output results to `data/results/baseline_results.csv` (Schema: trial_id, success, latency_ms)
- [ ] T014 [US2] Implement `code/symbolic_solver.py` using `cvxpy` to define constraint matrices for 'non-penetration' and 'joint limits' in physical 3D coordinates (via decoded actions). **Requirement**: Must define the problem structure ONLY; MUST output a `ConstraintMatrix` interface object.
- [ ] T014a [US2] [FR-003] Implement the differentiable convex optimization layer wrapper (using `diffcp` or PyTorch wrapper) for the solver defined in T014. **Critical Constraint**: Implement a custom autograd function that treats the decoded 3D action as a constant input (no gradient through decoder), ensuring gradients flow ONLY from constraint loss to solver parameters (not through the frozen decoder). **Output**: `data/results/gradient_flow_log.json` verifying the gradient path.
- [ ] T014a-verify [US2] [FR-003] Implement and run gradient verification test to ensure gradients flow ONLY to solver parameters via the custom autograd wrapper, validating that the decoder weights remain frozen and no gradients flow into the GFM backbone. **Output**: `data/results/gradient_verification_report.md`.
- [ ] T008a-synthetic [US2] [P] Implement `scripts/profile_solver_synthetic.py` to run the symbolic solver (T014) on a synthetic proxy dataset (simple rigid bodies) to validate solver structure and basic timing < 300s. **Output**: `data/results/profiling_synthetic_report.json`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Topology-Shift Test Set Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of manipulation tasks with novel kinematic chains and deformable materials using PyBullet, ensuring zero overlap with original GAM training data.

**Independent Test**: Run generation script; verify output contains valid physics states for a diverse set of distinct topologies; confirm checksum hash differs from original GAM metadata.

### Implementation for User Story 1

- [ ] T009-gen [US1] Implement `code/data_generation.py` logic to generate a diverse set of novel kinematic chains (hinge counts -10) and deformable materials (stiffness in a low-to-moderate range) in PyBullet. **Logic**: Loop iteratively to generate a unique topology configuration per iteration. **Output**: `data/generated/raw_physics_states.json` containing full physics states (vertex positions, joint angles, timestamps) for every timestep. **Note**: This task generates the raw data; distinctness is verified in T009-verify-uniqueness.
- [ ] T009-verify-uniqueness [US1] [Depends on T009-gen] Implement logic to verify pairwise distinctness of the generated topologies. **Input**: `data/generated/raw_physics_states.json`. **Output**: `data/generated/unique_topology_ids.json` (list of 50 distinct topology IDs). **Abort Condition**: If < 50 distinct topologies are found, exit with code 1.
- [ ] T009-hash [US1] [Depends on T009-verify-uniqueness] Implement logic to compute SHA-256 hash of generated topology IDs from `data/generated/unique_topology_ids.json` and compare against `data/raw/gam_baseline_metadata.json` to confirm zero overlap (FR-001). **Abort Condition**: If overlap is detected, exit with code 1 and halt generation.
- [ ] T009-serialize [US1] [Depends on T009-hash] Implement logic to serialize the validated unique physics states into the final `data/generated/physics_states.json` and `data/generated/latent_trajectory.csv` (schema: `latent_vector`, `ground_truth_action`, `timestamp`).
- [ ] T010a [US1] Implement logic to extract and serialize full physics simulation states (vertex positions for deformable objects, joint angles for kinematic chains) into `data/generated/physics_states.json` to satisfy US-1 Acceptance Scenario 2.
- [ ] T010b [US1] Compute statistical reference distribution (mean/covariance) from `data/generated/physics_states.json` and save to `data/raw/gam_reference_stats.json` for use in latent drift detection using Mahalanobis distance (Spec Edge Cases).
- [ ] T011 [US1] Implement error handling for physics simulation failures in `code/data_generation.py`: handle specific failure modes (PyBullet `p.loadURDF` returns an error indicator, simulation step returns NaN); recovery mechanism (retry times with exponential backoff, log to `data/results/errors.log` and skip trial); verification (unit test `test_crash_recovery` passes).
- [X] T013 [US1] Create `scripts/generate_test_set.py` to execute generation with configurable seeds
- [ ] T008a-profile [US1] [Depends on T009-serialize] Implement `scripts/profile_solver.py` to run the symbolic solver (T014) on a representative sample of topologies from `data/generated/physics_states.json`, measuring actual step time on multi-core hardware. **Output**: `data/results/profiling_report.json` containing `mean_step_time_ms`, `p95_step_time_ms`. **Verification**: `assert exit_code == 0` and `mean_step_time_ms < 300000` (300s). This task validates the <300s assumption (Spec Assumptions) before the main experiment.
- [ ] T008b [US1] [Depends on T008a-profile] Implement script to calculate total experiment time based on `data/results/profiling_report.json` (T008a-profile) and `trial_count` (50); verify against 6-hour CI limit (SC-005).
- [ ] T008c-escape [US1] [Depends on T008b] Implement 'methodology adjustment' logic: if profiling reveals step time > 300s, automatically reduce topology complexity or trial count and output `data/results/methodology_adjustment.json` documenting the change to ensure SC-005 feasibility. **Note**: This replaces abort logic to maintain reproducibility.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Symbolic Latent Planner Execution (Priority: P2)

**Goal**: Execute frozen GFM encoder/decoder and inject a differentiable symbolic solver to enforce geometric constraints in 3D space, running entirely on CPU.

**Independent Test**: Load frozen GFM, run symbolic planner on a single P1 test case, decode action, verify constraint satisfaction in PyBullet without GPU.

### Implementation for User Story 2

- [ ] T016 [US2] Integrate `code/gfm_wrapper.py` (T006) and `code/symbolic_solver.py` (T014/T014a) to encode observations to latent space and decode solver outputs to 3D actions (Depends on T006, T014a, T009-serialize)
- [ ] T018a [US2] [SC-001] Define the schema for `data/results/trial_log.csv` (columns: `trial_id`, `step`, `success`, `infeasible`, `timeout`, `latency_ms`) before T017 and T018 write to it.
- [ ] T017 [US2] Implement timeout mechanism for solver steps: read `timeout_limits` from `code/config.yaml` and enforce a configurable timeout per step; record timeout events to `data/results/trial_log.csv` with `timeout=true` and `timeout_reason: step_limit` flag; link to <300s/step assumption in spec's Assumptions and 6-hour total limit in SC-005.
- [ ] T018 [US2] Implement "infeasible" flag logic when constraints cannot be satisfied: append `infeasible=true` to `data/results/trial_log.csv`; verification (assert that `trial_log.csv` contains at least one row with `infeasible=true` when constraints are unsatisfiable).
- [ ] T019-verify-threshold [US2] [Depends on T010b] Calculate and verify the Mahalanobis distance threshold against the reference distribution from `data/raw/gam_reference_stats.json`. **Output**: `data/raw/drift_threshold_validation.json` containing the calculated p-value and confidence interval to prove validity.
- [ ] T019 [US2] [Depends on T010b, T019-verify-threshold, T009-serialize] Implement latent drift detection: compute Mahalanobis distance using the validated threshold from `data/raw/drift_threshold_validation.json`; flag out-of-distribution inputs and log to `data/results/drift_log.csv`.
- [ ] T019-action [US2] [Depends on T019] Implement 'flag for manual review' action: if drift is detected, pause the pipeline, log to `data/results/drift_alert.json`, and mark the trial as 'requires_review' in the final report.
- [ ] T020 [US2] Create `code/inference_pipeline.py` to orchestrate encode -> solve -> decode -> simulate loop (Depends on T014, T016, T009-serialize)
- [ ] T021 [US2] Add logging for inference latency (ms) and success/failure status for each trial
- [ ] T021b [US2] [SC-001] Implement logic to measure and record the success metric: read `data/generated/physics_states.json` (T010a), parse `object_position` and `collision_flag`; assert `collision_flag == 0` AND `distance to target object center < 5cm` for >= 1.0s (verified by maintaining state for 60 consecutive frames at 60Hz) to set success=true.
- [ ] T021c [US2] [Depends on T020] Aggregate trial results from T021 and T021b into `data/results/symbolic_results.csv` with schema: `trial_id`, `success`, `latency_ms`, `timeout`, `infeasible`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Statistical Analysis (Priority: P3)

**Goal**: Compare symbolic-latent approach vs. baseline GAM using Fisher's Exact Test and paired t-test on success rates and latency.

**Independent Test**: Run analysis script on collected results; verify report includes p-values, CIs, and effect sizes for both metrics.

### Implementation for User Story 3

- [ ] T022a [US3] [Depends on T009-serialize] Run `code/baseline_runner.py` on the test set generated in T009-serialize; load weights from `data/raw/gfm_baseline.pt`; output results to `data/results/baseline_results.csv` (Schema: trial_id, success, latency_ms)
- [ ] T023 [P] [US3] Implement `code/analysis.py` to load results from `data/results/symbolic_results.csv` (T021c) and `data/results/baseline_results.csv` (T022a); expect CSV schema: columns `trial_id`, `approach`, `success`, `latency_ms`, `timestamp` (verify schema existence).
- [ ] T024 [US3] Implement Fisher's Exact Test for binary success/failure outcomes (FR-006)
- [ ] T025 [US3] Implement paired t-test for inference latency comparisons (FR-006)
- [ ] T026 [US3] Calculate and report confidence intervals and effect sizes (Cohen's d for t-test, Odds Ratio for Fisher's as the effect size metric per FR-006).
- [ ] T027 [US3] Generate final report `data/results/analysis_report.md` as a Markdown table with columns: Metric, Symbolic, Baseline, Difference, P-value, 95% CI, Effect Size; state null hypothesis rejection status (α=0.05) and validate SC-001 (one-second duration)
- [ ] T028 [US3] Create `scripts/run_analysis.py` to execute the full statistical comparison pipeline

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Update `README.md` with CLI usage instructions and project structure
- [ ] T030 Code cleanup and refactoring of `code/` modules
- [ ] T031 [P] Refactor `code/symbolic_solver.py` to use sparse matrix representation for constraint matrices to reduce memory overhead and improve solve time; verification: memory usage < 7GB for 50 topologies, solve time reduced by >10%
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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T009-serialize (US1 completion) for input data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T021c/T022a (inference results) for input data

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