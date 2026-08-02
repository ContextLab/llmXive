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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a-reqs [P] Create `requirements.txt` with pinned dependencies (pybullet, torch (cpu), cvxpy, diffcp, scipy, pandas, numpy, pytest)
- [ ] T001a-gitignore [P] Create `.gitignore` file excluding `data/`, `__pycache__`, `*.pyc`, and environment files
- [ ] T001a-init [P] Create `code/__init__.py` and `tests/__init__.py`
- [ ] T001b [P] Create `code/`, `data/`, `tests/` directories
- [ ] T001c [P] Create `.gitkeep` files in all data subdirectories (`data/raw`, `data/generated`, `data/results`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.11 project with pinned dependencies (`requirements.txt`: pybullet, torch (cpu, `--index-url https://download.pytorch.org/whl/cpu`), cvxpy, diffcp, scipy, pandas, numpy, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools; create `ruff.toml` and `.pre-commit-config.yaml`
- [ ] T004 Setup data directory structure (`data/raw`, `data/generated`, `data/results`) and `.gitkeep` files
- [X] T005 [P] Implement `code/utils.py` with logging, deterministic seeding (numpy/torch), and SHA-256 hashing utilities
- [X] T006 [P] **Implement** `code/gfm_wrapper.py` to **load frozen GFM weights** from `data/raw/gfm_weights.pt` (CPU-only, `eval()` mode) and **freeze all parameters**. **Requirement**: Must **fully implement** `encode`/`decode` methods (forward pass) to map 3D observations to latent space and latent vectors to 3D actions. **Output**: Functional `GFMWrapper` class ready for inference.
- [X] T007a [P] Create `code/config.yaml` defining experiment parameters: `topology_counts` (list of integers, default `[3, 10]`), `timeout_limits` (configurable duration), `seed`, `trial_count` (50), `sim_fps` (default 60)
- [X] T007b [P] Implement `code/config.py` loader to parse `code/config.yaml` and expose parameters as a typed configuration object
- [ ] T008 [P] Create `.github/workflows/ci.yml` to match FR-004: Multi-core x86_64 runner, no GPU/CUDA, with a fixed timeout limit to constrain the duration of the experimental trial, ensuring environment matches the requirement.
- [X] T009a-gen [US1] **Fetch** `data/raw/gam_reference_stats.json` from the verified external URL `https://huggingface.co/datasets/llmXive/gam-baseline-stats/resolve/main/gam_reference_stats.json`. **Constraint**: If the fetch fails, the script MUST raise an exception and exit with code 1. **DO NOT** generate synthetic data or use a mock fallback. **Requirement**: The fetched file must contain `topology_hashes` (list of SHA-256) and `latent_stats` (mean/covariance). **Output**: Valid `data/raw/gam_reference_stats.json`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Topology-Shift Test Set Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of manipulation tasks with novel kinematic chains and deformable materials using PyBullet, ensuring zero overlap with original GAM training data.

**Independent Test**: Run generation script; verify output contains valid physics states for a diverse set of distinct topologies; confirm checksum hash differs from original GAM metadata.

### Implementation for User Story 1

- [X] T010b-rev [US1] [Depends on T009a-gen] **Validate** that `data/raw/gam_reference_stats.json` exists and contains valid `topology_hashes` and `latent_stats`. **Compute** the Mahalanobis drift threshold from `latent_stats` (99th percentile of Chi-squared distribution). **Output**: `data/raw/drift_threshold_validation.json` containing the calculated threshold and status "validated". **Note**: This task ensures the reference data exists *before* generation begins, breaking the circular dependency.
- [X] T009-verify-overlap [US1] [Depends on T009a-gen, T010b-rev] **Implement logic to verify zero overlap** against `data/raw/gam_reference_stats.json`. **Input**: `data/raw/gam_reference_stats.json`. **Output**: `data/generated/unique_topology_ids.json` (list of distinct topology IDs). **Constraint**: If < 50 distinct topologies are found OR ANY overlap is detected, **EXIT WITH CODE 1**, log a CRITICAL error to `data/results/errors.log` with the specific count and reason, and write a partial dataset manifest. **DO NOT** proceed with the inference phase (T017) to satisfy FR-001's "at least 50" mandate.
- [X] T009-gen-chains [US1] Implement `code/data_generation.py` logic to generate a diverse set of novel kinematic chains (hinge counts **3-10** as defined by `config.topology_counts` (default `range(3, 11)`)) in PyBullet. **Output**: `data/generated/raw_chains.json` containing full physics states.
- [X] T009-gen-deformable [US1] Implement `code/data_generation.py` logic to generate a diverse set of deformable materials (stiffness in a low range as defined by `config.stiffness_range`) in PyBullet. **Output**: `data/generated/raw_deformable.json` containing full physics states.
- [X] T009-serialize [US1] [Depends on T009-verify-overlap] Implement logic to serialize the validated unique physics states into the final `data/generated/physics_states.json` and `data/generated/latent_trajectory.csv` (schema: `latent_vector`, `ground_truth_action`, `timestamp`).
- [X] T010a [US1] Implement logic to extract and serialize full physics simulation states (vertex positions for deformable objects, joint angles for kinematic chains) into `data/generated/physics_states.json` to satisfy US-1 Acceptance Scenario 2. Ensure schema explicitly differentiates between rigid and deformable object data types.
- [X] T011 [US1] Implement error handling for physics simulation failures in `code/data_generation.py`: handle specific failure modes (PyBullet `p.loadURDF` returns an error indicator, simulation step returns NaN); recovery mechanism (retry with exponential backoff: initial=1s, multiplier=2, max=5 retries), log to `data/results/errors.log` and skip trial; verification (unit test `test_crash_recovery` passes).
- [X] T013 [US1] Create `scripts/generate_test_set.py` to execute generation with configurable seeds
- [X] T008a-gen-profile-data [US1] [Depends on T014] Implement `scripts/generate_profile_data.py` to generate a small synthetic proxy dataset (simple rigid bodies) for profiling. **Output**: `data/generated/profile_synthetic_data.json`.
- [X] T008b-profile-solver [US2] [Depends on T014, T008a-gen-profile-data] Implement `scripts/profile_solver_synthetic.py` to run the **differentiable symbolic solver** (T014) on the synthetic proxy data from T008a-gen-profile-data to validate solver structure and basic timing < 300s. **Output**: `data/results/profiling_synthetic_report.json` with schema: `{"mean_step_time_ms": float, "p95_step_time_ms": float}`.
- [X] T008-validate-timing [US1] [Depends on T008b-profile-solver] Implement `scripts/validate_solver_timing.py` to assert `report.mean_step_time_ms < 300000` (300s) from `data/results/profiling_synthetic_report.json` (key path: `mean_step_time_ms`). **Constraint**: If exceeded, **EXIT WITH CODE 1** and log `data/results/methodology_adjustment.json` with the specific topology complexity causing the failure. **Note**: This replaces auto-adjust logic to ensure reproducibility; the user must manually adjust `config.yaml` and re-run.
- [X] T008d-profile-real [US1] [Depends on T009-serialize, T014] Implement `scripts/profile_solver_real.py` to run the symbolic solver on a representative sample of topologies from `data/generated/physics_states.json`, measuring actual step time on multi-core hardware. **Output**: `data/results/profiling_report.json` containing `mean_step_time_ms`, `p95_step_time_ms`. **Verification**: `assert exit_code == 0`. This task validates the <300s assumption (Spec Assumptions) before the main experiment.
- [X] T008f-timeout-check [US1] [Depends on T008d-profile-real] Implement script to calculate total experiment time based on `data/results/profiling_report.json` (T008d-profile-real) and `trial_count` (50); verify against a standard CI limit. **Constraint**: If total time > 6h, **EXIT WITH CODE 1** and log `data/results/ci_limit_warning.json`.

The research question, method, and references remain unchanged as per the planning document requirements. (SC-005).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Symbolic Latent Planner Execution (Priority: P2)

**Goal**: Execute frozen GFM encoder/decoder and inject a differentiable symbolic solver to enforce geometric constraints in 3D space, running entirely on CPU.

**Independent Test**: Load frozen GFM, run symbolic planner on a single P1 test case, decode action, verify constraint satisfaction in PyBullet without GPU.

### Implementation for User Story 2

- [X] T014 [US2] Implement `code/symbolic_solver.py` to **define constraint matrices** for 'non-penetration' and 'joint limits' in physical spatial coordinates (via decoded actions) using **`cvxpylayers`** (or `diffcp`) as the differentiable convex optimization layer. **Requirement**: The GFM decoder must remain **frozen** (`torch.no_grad()`). Differentiability is verified via a **numerical gradient check** on the composite map (Solver -> Decoder -> Physical Space), ensuring gradients flow from the constraint loss, through the decoder's Jacobian, to the solver parameters. **Output**: `data/results/gradient_flow_log.json` with schema: `{"path": "string", "decoder_grad_norm": float, "solver_grad_norm": float}`. **Verification**: Ensure `decoder_grad_norm > 0` and `solver_grad_norm > 0`.
- [X] T014a-verify [US2] [FR-003] Implement and run gradient verification test to ensure gradients flow from constraint loss, through the decoder wrapper, to solver parameters. **Input**: `data/results/gradient_flow_log.json`. **Output**: `data/results/gradient_verification_report.md`. **Verification**: Assert `decoder_grad_norm > 0` and `solver_grad_norm > 0` from the JSON log. **Constraint**: Task must fail if `gradient_flow_log.json` is missing or contains zero norms.
- [X] T016 [US2] Integrate `code/gfm_wrapper.py` (T006) and `code/symbolic_solver.py` (T014) to encode observations to latent space and decode solver outputs to 3D actions (Depends on T006, T014, T009-serialize)
- [X] T018a [US2] [SC-001] Define the schema for `data/results/trial_log.csv` (columns: `trial_id`, `step`, `success`, `infeasible`, `timeout`, `latency_ms`) before T017 and T018 write to it. **Requirement**: This schema definition MUST be validated before any data is written.
- [X] T017 [US2] [Depends on T014, T016] Implement timeout mechanism for solver steps: read `timeout_limits` from `code/config.yaml` and enforce a configurable timeout per step; record timeout events to `data/results/trial_log.csv` with `timeout=true` and `timeout_reason: step_limit` flag; link to <300s/step assumption in spec's Assumptions and 6-hour total limit in SC-005. **Constraint**: This task implements the timeout logic *within* the execution loop orchestrated by T020. **Verification**: Run a mock trial and assert `trial_log.csv` contains at least one recorded entry (success, failure, or timeout).
- [X] T018 [US2] Implement "infeasible" flag logic when constraints cannot be satisfied: append `infeasible=true` to `data/results/trial_log.csv`; verification (assert that `trial_log.csv` contains at least one row with `infeasible=true` when constraints are unsatisfiable).
- [X] T019-verify-threshold [US2] [Depends on T010b-rev] Validate the Mahalanobis distance threshold calculated in T010b-rev. **Method**: Ensure the threshold is a positive float and corresponds to the 99th percentile of the Chi-squared distribution. **Output**: `data/raw/drift_threshold_validation.json` updated with `status: "validated"`.
- [X] T019 [US2] [Depends on T010b-rev, T019-verify-threshold, T009-serialize] Implement latent drift detection: compute Mahalanobis distance using the validated threshold from `data/raw/drift_threshold_validation.json`; flag out-of-distribution inputs and log to `data/results/drift_log.csv`.
- [X] T019-action [US2] [Depends on T019] Implement 'flag for manual review' action: if drift is detected, pause the pipeline, log to `data/results/drift_alert.json`, and mark the trial as 'requires_review' in the final report.
- [X] T020 [US2] Create `code/inference_pipeline.py` to orchestrate encode -> solve -> decode -> simulate loop (Depends on T014, T016, T009-serialize)
- [X] T021 [US2] Add logging for inference latency (ms) and success/failure status for each trial
- [X] T021b [US2] [SC-001] Implement logic to measure and record the success metric: read `data/generated/physics_states.json` (T010a), parse `object_position` and `collision_flag`; read `sim_fps` from `code/config.yaml`; assert `collision_flag == 0` AND `distance to target object center < 5cm` for `success_frames >= int(sim_fps)

Research Question: How can we determine the minimum number of consecutive frames required to confirm a simulation state as successful?
Method: We will implement a threshold-based verification logic where the count of consecutive successful frames must meet or exceed a normalized factor of the simulation's frame rate.
References: [Citation Placeholder]` (approx 1 second) to set success=true. **Note**: Frame count is dynamically calculated from config to match "approximately one second".
- [X] T021c [US2] [Depends on T020] Aggregate trial results from T021 and T021b into `data/results/symbolic_results.csv` with schema: `trial_id`, `approach="Symbolic"`, `success`, `latency_ms`, `timeout`, `infeasible`, `timestamp`.
- [X] T020-timeout-check [US2] [Depends on T020] Implement global CI time limit check in `code/inference_pipeline.py`: monitor total elapsed time; if > 6 hours, **EXIT WITH CODE 2** and log `data/results/ci_timeout_error.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Statistical Analysis (Priority: P3)

**Goal**: Compare symbolic-latent approach vs. baseline GAM using Fisher's Exact Test and conditional survival analysis/t-test on success rates and latency.

**Independent Test**: Run analysis script on collected results; verify report includes p-values, CIs, and effect sizes for both metrics.

### Implementation for User Story 3

- [X] T022a [US3] [Depends on T009-serialize] Run `code/baseline_runner.py` on the test set generated in T009-serialize; load weights from `data/raw/gfm_baseline.pt`; output results to `data/results/baseline_results.csv` (Schema: trial_id, success, latency_ms, approach="Baseline", timestamp)
- [X] T023 [P] [US3] Implement `code/analysis.py` to load results from `data/results/symbolic_results.csv` (T021c) and `data/results/baseline_results.csv` (T022a); expect CSV schema: columns `trial_id`, `approach`, `success`, `latency_ms`, `timestamp` (verify schema existence).
- [X] T024a-load [US3] [Depends on T023] Implement data loading and schema verification in `code/analysis.py`.
- [ ] T024a-stat [US3] [Depends on T024a-load] Implement statistical analysis functions in `code/analysis.py`: 
    1. Perform Fisher's Exact Test for success rates and report p-value, Odds Ratio, and a confidence interval for the Odds Ratio.
    2. **Conditional Latency Test**: Check if latency data contains censored values (timeouts). 
       - If censored: Perform **Stratified Log-Rank test** (using `lifelines.statistics.logrank_test` with `stratify='trial_id'` to maintain pairing) and report Hazard Ratio/Cliff's Delta.
       - If uncensored: Perform **Paired t-test** (using `scipy.stats.ttest_rel`) and report mean difference, p-value, and effect size (Cohen's d) with a confidence interval.
    3. **Constraint**: Do NOT forbid Survival Analysis; it MUST be used if censored data is present.
- [X] T024a-report [US3] [Depends on T024a-stat] Implement report generation logic in `code/analysis.py` to create `data/results/analysis_report.md` as a Markdown table with columns: Metric, Symbolic, Baseline, Difference, P-value, 95% CI, Effect Size.
- [X] T024a-validate [US3] [Depends on T024a-report] Validate SC-001 (one-second duration) in the report and verify all p-values are present.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Update `README.md` with CLI usage instructions and project structure
- [ ] T030 Code cleanup and refactoring of `code/` modules
- [ ] T031 [Optional/Future] Refactor `code/symbolic_solver.py` to use sparse matrix representation for constraint matrices to reduce memory overhead and improve solve time; verification: memory usage < 7GB for topologies, solve time reduced by >10% compared to baseline in T008b-profile
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

The research question, method, and references remain unchanged as per the planning document requirements.