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

- [X] T002 (`requirements.txt`: pybullet, torch (cpu, `--index-url https://download.pytorch.org/whl/cpu`), cvxpy, diffcp, scipy, pandas, numpy, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools; create `ruff.toml` and `.pre-commit-config.yaml`
- [ ] T004 Setup data directory structure (`data/raw`, `data/generated`, `data/results`) and `.gitkeep` files
- [X] T005 [P] Implement `code/utils.py` with logging, deterministic seeding (numpy/torch), and SHA-256 hashing utilities
- [X] T006-frozen [P] **Implement** `code/gfm_wrapper.py` (Frozen Inference Mode) to **load frozen GFM weights** from `data/raw/gfm_weights.pt` (CPU-only, `eval()` mode) and **freeze all parameters**. **Requirement**: Must **fully implement** `encode`/`decode` methods (forward pass) to map 3D observations to latent space and latent vectors to 3D actions. **Constraint**: This wrapper MUST disable autograd (`torch.no_grad()`) to ensure it is used only for inference. **Output**: Functional `GFMWrapperFrozen` class ready for inference.
- [X] T006-diff [P] **Implement** `code/gfm_wrapper.py` (Differentiable Gradient Check Mode) to **load frozen GFM weights** from `data/raw/gfm_weights.pt`. **Requirement**: Must implement `encode`/`decode` methods that **enable autograd** (`requires_grad=True` on inputs) specifically for numerical gradient verification. This wrapper is used ONLY for T014's gradient check. **Output**: Functional `GFMWrapperDiff` class for gradient verification.
- [X] T005-baseline-fetch [P] **Fetch and Validate** `data/raw/gfm_baseline.pt`. **Logic**: 1. Read `baseline_model_url` from `code/config.yaml`. 2. If URL is present and valid, fetch the file using `huggingface_hub.hf_hub_download` or `requests`. 3. Verify SHA-256 checksum against `data/raw/baseline_checksums.json`. 4. If fetch fails or URL is missing, **EXIT WITH CODE 1** with a clear error message: "Baseline model URL not configured or fetch failed. Cannot proceed with comparative analysis (FR-005)." **Constraint**: Do NOT generate synthetic weights. **Output**: Valid `data/raw/gfm_baseline.pt` with checksum validation. **Note**: This task explicitly acquires the Baseline GAM weights required for FR-005, distinct from the GFM encoder/decoder weights used in the symbolic approach.
- [X] T007a [P] Create `code/config.yaml` defining experiment parameters: `topology_counts` (list of integers, default `[3, 10]`), `timeout_limits` (configurable duration), `seed`, `trial_count` (50), `sim_fps` (default 30), `max_attempts` (default 1000), `stiffness_range` (default `[0.1, 0.5]`), `target_zone` (dict with `center` and `radius`), `baseline_model_url` (string, optional, URL for baseline weights)
- [X] T007b [P] Implement `code/config.py` loader to parse `code/config.yaml` and expose parameters as a typed configuration object
- [ ] T008 [P] Create `.github/workflows/ci.yml` to match FR-004: Multi-core x86_64 runner, no GPU/CUDA, with a fixed timeout limit to constrain the duration of the experimental trial, ensuring environment matches the requirement.
- [X] T009a-fetch-stats [US1] [Depends on T007b] **Generate or Fetch** `data/raw/gam_reference_stats.json`. **Logic**: 1. **PRIORITY**: Attempt to **generate locally** by computing mean/covariance of latent vectors from a representative subset of the training set (or a synthetic proxy if the training set is inaccessible, but log this as a warning). 2. If local generation fails, **attempt to fetch** from `reference_stats_url` in `code/config.yaml`. 3. If both fail, **EXIT WITH CODE 1**. **Output**: Valid `data/raw/gam_reference_stats.json` with validation status. **Note**: This task prioritizes local generation to satisfy Plan Phase 1.4 requirements, ensuring FR-001 (zero overlap) can be verified without a hardcoded URL dependency.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Topology-Shift Test Set Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of manipulation tasks with novel kinematic chains and deformable materials using PyBullet, ensuring zero overlap with original GAM training data.

**Independent Test**: Run generation script; verify output contains valid physics states for a diverse set of distinct topologies; confirm checksum hash differs from original GAM metadata.

### Implementation for User Story 1

- [X] T010b-rev [US1] [Depends on T009a-fetch-stats] **Validate** that `data/raw/gam_reference_stats.json` exists and contains valid `topology_hashes` and `latent_stats`. **Compute** the Mahalanobis drift threshold from `latent_stats` (a high percentile of the Chi-squared distribution). **Output**: `data/raw/drift_threshold_validation.json` containing the calculated threshold and status "validated". **Note**: This task ensures the reference data exists *before* generation begins, breaking the circular dependency by relying on the **output artifact** of T009a-fetch-stats (the stats file), regardless of whether it was fetched or generated locally. **Note**: This task consolidates fetch and fallback into a single atomic step to avoid race conditions.
- [X] T009-gen-chains [US1] [Depends on T007a, T007b, T009a-fetch-stats] Implement `code/data_generation.py` logic to generate a diverse set of novel kinematic chains (hinge counts **3-10** as defined by `config.topology_counts` (default `range(3, 11)`)) in PyBullet. **Logic**: Generate chains until `len(unique_topology_ids) >= 50` (combined with deformable) or `config.max_attempts` (default 1000) is reached. If `max_attempts` reached without 50, **generate `data/generated/partial_chains.json`** (if any valid chains exist) and **EXIT WITH CODE 1**. **Output**: `data/generated/raw_chains.json` (or `partial_chains.json` on failure).
- [X] T009-gen-deformable [US1] [Depends on T007a, T007b] Implement `code/data_generation.py` logic to generate a diverse set of deformable materials (stiffness in range **0.1 to 0.5** as defined by `config.stiffness_range` (default `[0.1, 0.5]`)) in PyBullet. **Logic**: Generate materials until combined count with chains reaches a sufficient number of unique topologies. **Output**: `data/generated/raw_deformable.json` containing full physics states.
- [X] T009-verify-overlap [US1] [Depends on T009a-fetch-stats, T010b-rev, T009-gen-chains, T009-gen-deformable] **Implement logic to verify zero overlap** against `data/raw/gam_reference_stats.json`. **Input**: `data/raw/gam_reference_stats.json`, `data/generated/raw_chains.json` (or `partial_chains.json`), `data/generated/raw_deformable.json`. **Logic**: Check for existence of `raw_chains.json`; if missing, check for `partial_chains.json`. If neither exists, **EXIT WITH CODE 1**. **Output**: `data/generated/unique_topology_ids.json` (list of distinct topology IDs). **Constraint**: If < 50 distinct topologies are found OR ANY overlap is detected, **EXIT WITH CODE 1**, log a CRITICAL error to `data/results/errors.log` with the specific count and reason, and write a partial dataset manifest. **DO NOT** proceed with the inference phase (T017) to satisfy FR-001's "at least 50" mandate.
- [X] T009-serialize [US1] [Depends on T009-verify-overlap, T009-gen-chains, T009-gen-deformable] Implement logic to serialize the validated unique physics states into the final `data/generated/physics_states.json` and `data/generated/latent_trajectory.csv` (schema: `latent_vector`, `ground_truth_action`, `timestamp`).
- [X] T010a [US1] [Depends on T009-gen-chains, T009-gen-deformable] Implement logic to extract and serialize full physics simulation states (vertex positions for deformable objects, joint angles for kinematic chains) into `data/generated/physics_states.json` to satisfy US-1 Acceptance Scenario 2. Ensure schema explicitly differentiates between rigid and deformable object data types using fields: `object_type` (string: 'rigid' or 'deformable'), `vertex_data` (list of floats for deformable), `joint_angles` (list of floats for rigid).
- [X] T011 [US1] Implement error handling for physics simulation failures in `code/data_generation.py`: handle specific failure modes (PyBullet `p.loadURDF` returns an error indicator, simulation step returns NaN); recovery mechanism (retry with exponential backoff: initial=1s, multiplier=2, max=5 retries), log to `data/results/errors.log` and skip trial; verification (unit test `test_crash_recovery` passes).
- [X] T013 [US1] Create `scripts/generate_test_set.py` to execute generation with configurable seeds
- [X] T009b-generate-gt [US1] [Depends on T009-gen-chains, T009-gen-deformable] **Generate Ground Truth States** for Decoder Fidelity Validation. **Logic**: Select a diverse set of novel topologies from `data/generated/physics_states.json`. Run a high-fidelity PyBullet simulation **without** the decoder (using the same physics parameters as the test set) to generate ground-truth positions/velocities. **Output**: `data/generated/ground_truth_states.json` containing the simulated states for comparison. **Note**: This task explicitly produces the artifact required by T019b, resolving the hidden dependency.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Symbolic Latent Planner Execution (Priority: P2)

**Goal**: Execute frozen GFM encoder/decoder and inject a differentiable symbolic solver to enforce geometric constraints in 3D space, running entirely on CPU.

**Independent Test**: Load frozen GFM, run symbolic planner on a single P1 test case, decode action, verify constraint satisfaction in PyBullet without GPU.

### Implementation for User Story 2

- [X] T014 [US2] Implement `code/symbolic_solver.py` to **define constraint matrices** for 'non-penetration' and 'joint limits' in physical spatial coordinates (via decoded actions) using **`cvxpylayers`** (or `diffcp`) as the differentiable convex optimization layer. **Requirement**: The GFM decoder must be the **differentiable wrapper** (T006-diff) for this specific task. Differentiability is verified via a **numerical gradient check** on the composite map (Solver -> Decoder -> Physical Space): perturb the solver's input parameters (e.g., slack variables) by $\epsilon = 10^{-6}$ and measure the change in the constraint violation loss to verify the **existence** of a gradient path through the decoder's Jacobian, without backpropagating through the frozen decoder weights. **Output**: `data/results/gradient_flow_log.json` with schema: `{"path": "string", "decoder_grad_norm": float, "solver_grad_norm": float}`. **Verification**: Ensure `decoder_grad_norm > 0` and `solver_grad_norm > 0`. **Dependencies**: T006-diff, T009-serialize.
- [X] T014a-verify [US2] [FR-003] Implement and run gradient verification test to ensure gradients flow from constraint loss, through the decoder wrapper, to solver parameters. **Input**: `data/results/gradient_flow_log.json`. **Output**: `data/results/gradient_verification_report.md`. **Verification**: Assert `decoder_grad_norm > 0` and `solver_grad_norm > 0` from the JSON log. **Constraint**: Task must fail if `gradient_flow_log.json` is missing or contains zero norms.
- [X] T016 [US2] Integrate `code/gfm_wrapper.py` (T006-frozen for inference, T006-diff for check) and `code/symbolic_solver.py` (T014) to encode observations to latent space and decode solver outputs to 3D actions (Depends on T006-frozen, T014, T009-serialize)
- [X] T017 [US2] [Depends on T014, T016] Implement timeout mechanism for solver steps: read `timeout_limits` from `code/config.yaml` and enforce a configurable timeout per step; record timeout events to `data/results/trial_log.csv` with `timeout=true` and `timeout_reason: step_limit` flag; link to <300s/step assumption in spec's Assumptions and -hour total limit in SC-005. **Constraint**: This task implements the timeout logic *within* the execution loop orchestrated by T020. **Verification**: Run a mock trial and assert `trial_log.csv` contains at least one recorded entry (success, failure, or timeout).
- [X] T018 [US2] Implement "infeasible" flag logic when constraints cannot be satisfied: append `infeasible=true` to `data/results/trial_log.csv`; verification (assert that `trial_log.csv` contains at least one row with `infeasible=true` when constraints are unsatisfiable).
- [X] T019-verify-threshold [US2] [Depends on T010b-rev] Validate the Mahalanobis distance threshold calculated in T010b-rev. **Method**: Ensure the threshold is a positive float and corresponds to a high percentile of the Chi-squared distribution. **Output**: `data/raw/drift_threshold_validation.json` updated with `status: "validated"`.
- [X] T019 [US2] [Depends on T010b-rev, T019-verify-threshold, T009-serialize] Implement latent drift detection: compute Mahalanobis distance using the validated threshold from `data/raw/drift_threshold_validation.json`; flag out-of-distribution inputs and log to `data/results/drift_log.csv`.
- [X] T019-action [US2] [Depends on T019] Implement 'flag for manual review' action: if drift is detected, **write `data/results/drift_alert.json` with `status: 'flagged'` and exit with code 3**, and mark the trial as 'requires_review' in the final report. **Note**: Do NOT pause the entire pipeline; record and log for review.
- [X] T019b [US2] [Depends on T006-frozen, T009-gen-chains, T009b-generate-gt] **Implement Decoder Fidelity Validation** (Plan Phase 2.5). **Logic**: Select a diverse set of novel topologies from `data/generated/physics_states.json` (using topology definitions from T009-gen-chains). Decode latent states to physical space using `code/gfm_wrapper.py` (frozen mode). **Compare** decoded positions/velocities against `data/generated/ground_truth_states.json` (produced by T009b-generate-gt). **Metric**: Compute MSE. **Threshold**: If MSE > 0.05, flag as "Decoder Hallucination" and exclude from symbolic trials. **Output**: `data/results/decoder_fidelity_log.json` with MSE values and exclusion flags. **Note**: This validation is authorized by Plan Phase 2.5, which mandates validation against PyBullet ground truth for novel topologies.
- [X] T020 [US2] Create `code/inference_pipeline.py` to orchestrate encode -> solve -> decode -> simulate loop (Depends on T014, T016, T009-serialize, T017, T018, T019b). **Output**: `data/results/frame_log.csv` containing per-frame simulation states, collision flags, and timestamps for each trial.
- [X] T020a [US2] [Depends on T020] **Implement global CI time limit check** in `code/inference_pipeline.py`: monitor total elapsed time; if > 6 hours, **EXIT WITH CODE 2** and log `data/results/ci_timeout_error.json` with `timeout_reason: "ci_limit"` and record incomplete trials as 'timeout'.
- [X] T021 [US2] Add logging for inference latency (ms) and success/failure status for each trial
- [X] T021b [US2] [SC-001] [Depends on T020, T010a] Implement logic to measure and record the success metric: read `data/generated/physics_states.json` (T010a) and `data/results/frame_log.csv` (T020). **Logic**: For each trial, verify that `collision_flag == 0` AND `distance to target object center < 5cm` for **every frame** in a window of `success_frames >= int(config.sim_fps)` (approx 1 second). **Constraint**: If any frame in the window fails the collision or distance check, the trial is marked as failure. **Output**: `data/results/symbolic_results.csv` with schema: `trial_id`, `approach="Symbolic"`, `success`, `latency_ms`, `timeout`, `infeasible`, `timestamp`. **Note**: This task explicitly enforces the duration constraint from SC-001.
- [X] T021c [US2] [Depends on T020] Aggregate trial results from T021 and T021b into `data/results/symbolic_results.csv` with schema: `trial_id`, `approach="Symbolic"`, `success`, `latency_ms`, `timeout`, `infeasible`, `timestamp`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Statistical Analysis (Priority: P3)

**Goal**: Compare symbolic-latent approach vs. baseline GAM using Fisher's Exact Test and conditional survival analysis/t-test on success rates and latency.

**Independent Test**: Run analysis script on collected results; verify report includes p-values, CIs, and effect sizes for both metrics.

### Implementation for User Story 3

- [X] T022a [US3] [Depends on T005-baseline-fetch, T021c] Run `code/baseline_runner.py` on the test set generated in T009-serialize; load weights from `data/raw/gfm_baseline.pt` (acquired in T005-baseline-fetch); output results to `data/results/baseline_results.csv` (Schema: trial_id, success, latency_ms, approach="Baseline", timestamp)
- [X] T023 [P] [US3] [Depends on T021c, T022a] Implement `code/analysis.py` to load results from `data/results/symbolic_results.csv` (T021c) and `data/results/baseline_results.csv` (T022a); expect CSV schema: columns `trial_id`, `approach`, `success`, `latency_ms`, `timestamp` (verify schema existence).
- [X] T024a-load [US3] [Depends on T023] Implement data loading and schema verification in `code/analysis.py`.
- [X] T024a-detect-censor [US3] [Depends on T021c, T022a] **Detect Censored Data**. **Logic**: Inspect `data/results/symbolic_results.csv` and `data/results/baseline_results.csv` for the presence of the `timeout` flag set to `true`. **Output**: `data/results/censoring_status.json` with schema: `{"symbolic_censored": bool, "baseline_censored": bool, "any_censored": bool}`. **Constraint**: This task MUST run before T024a-select to inform the statistical test choice.
- [X] T024a-select [US3] [Depends on T024a-load, T024a-detect-censor] **Implement Conditional Statistical Test Selection**. **SPEC AMENDMENT**: This task implements the amended FR-006 (updated in spec.md) which authorizes conditional test selection. **Logic**: Read `data/results/censoring_status.json` (T024a-detect-censor).
 1. If `any_censored` is true: Perform **Stratified Log-Rank test** (using `lifelines.statistics.logrank_test` with `stratify='trial_id'` to maintain pairing) and report Hazard Ratio/Cliff's Delta.
 2. If `any_censored` is false: Perform **Paired t-test** (using `scipy.stats.ttest_rel`) and report mean difference, p-value, and effect size (Cohen's d) with a confidence interval.
 3. Perform Fisher's Exact Test for success rates and report p-value, Odds Ratio, and a confidence interval for the Odds Ratio.
 **Output**: `data/results/stat_test_selection.json` containing the chosen test name and the reason (e.g., 'censored_data_detected').
- [X] T024a-report [US3] [Depends on T024a-select] Implement report generation logic in `code/analysis.py` to create `data/results/analysis_report.md` as a Markdown table with columns: Metric, Symbolic, Baseline, Difference, P-value, 95% CI, Effect Size.
- [X] T024a-validate [US3] [Depends on T024a-report] Validate SC-001 (one-second duration) in the report and verify all p-values are present.

**Note**: Task T034 (Censored Data Handling) has been removed as its logic is fully implemented in T024a-select with the Spec Override clause, and Plan Phase 3.2 now explicitly maps this logic to T024a-select.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Update `README.md` with CLI usage instructions and project structure
- [ ] T030 Code cleanup and refactoring of `code/` modules
- [ ] T032 [P] Additional unit tests for solver constraints and latent drift detection in `tests/unit/`
- [X] T033 [P] Run `scripts/validate_quickstart.sh` (or equivalent) to ensure end-to-end reproducibility; verify exit code 0 and generate `data/results/quickstart_validation.json` with pass/fail status.

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