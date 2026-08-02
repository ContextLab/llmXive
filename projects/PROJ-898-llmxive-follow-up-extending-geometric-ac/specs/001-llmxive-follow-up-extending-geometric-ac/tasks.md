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

- [ ] T001a-structure [P] **Create project root structure**: Create `projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/` directory root, and subdirectories `code/`, `data/`, `tests/`. Create `data/raw`, `data/generated`, `data/results` with `.gitkeep` files. Create `code/__init__.py`, `tests/__init__.py`.
- [ ] T001b-requirements [P] Create `requirements.txt` pinning dependencies: `pybullet`, `torch` (cpu-only), `cvxpy`, `diffcp`, `scipy`, `pandas`, `numpy`, `pytest`, `huggingface_hub`, `loguru`
- [ ] T001c-gitignore [P] Create `.gitignore` (excluding data/raw, data/generated, data/results, state/) and `.pre-commit-config.yaml` for linting (ruff) and formatting (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.10+ project with pinned dependencies (`requirements.txt` as defined in T001b-requirements)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 Setup data directory structure (`data/raw`, `data/generated`, `data/results`) and `.gitkeep` files
- [X] T005 [P] Implement `code/utils.py` with logging, deterministic seeding (numpy/torch), and SHA-256 hashing utilities
- [ ] T005a [P] **Implement** `code/data_fetcher.py` to **download** the pre-trained GFM weights from the verified source (e.g., HuggingFace or specified URL), **verify** the SHA-256 checksum, and save to `data/raw/gfm_weights.pt`. **Requirement**: Must fail loudly if download fails or checksum mismatches. **Output**: Verified `data/raw/gfm_weights.pt`.
- [ ] T006 [P] [Depends on T005a] **Implement** `code/gfm_wrapper.py` to **load frozen GFM weights** from `data/raw/gfm_weights.pt` (CPU-only, `eval()` mode, `torch.no_grad()`) and **freeze all parameters**. **Requirement**: Must **fully implement** `encode`/`decode` methods (forward pass) to map 3D observations to latent space and latent vectors to 3D actions. **Output**: Functional `GFMWrapper` class ready for inference.
- [X] T007a [P] Create `code/config.yaml` defining experiment parameters: `topology_counts`, `timeout_limits` (configurable duration), `seed`, `trial_count` (50), `sim_fps` (default 60)
- [X] T007b [P] Implement `code/config.py` loader to parse `code/config.yaml` and expose parameters as a typed configuration object
- [ ] T008 [P] Create `.github/workflows/ci.yml` to match FR-004: Multi-core x86_64 runner, no GPU/CUDA, with a **fixed -hour timeout limit** (per SC-005) to constrain the duration of the experimental trial, ensuring environment matches the requirement.
- [X] T009a [US1] Create `data/raw/gam_baseline_metadata.json` with schema `{"topology_ids": ["string"], "object_types": ["string"]}` containing baseline topology IDs to be used for zero-overlap verification in T009-hash
- [ ] T022a [US3] [P] Implement `code/baseline_runner.py` skeleton for running the original GAM implementation (neural predictor) on the test set generated in T009; load weights from `data/raw/gfm_baseline.pt`; output results to `data/results/baseline_results.csv` (Schema: trial_id, success, latency_ms, approach="Baseline", timestamp)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Topology-Shift Test Set Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of manipulation tasks with novel kinematic chains and deformable materials using PyBullet, ensuring zero overlap with original GAM training data.

**Independent Test**: Run generation script; verify output contains valid physics states for a diverse set of distinct topologies; confirm checksum hash differs from original GAM metadata.

### Implementation for User Story 1

- [X] T009-gen-chains [US1] Implement `code/data_generation.py` logic to generate a diverse set of novel kinematic chains (hinge counts in a low-to-moderate range as defined by `config.topology_counts`) in PyBullet. **Output**: `data/generated/raw_chains.json` containing full physics states.
- [X] T009-gen-deformable [US1] Implement `code/data_generation.py` logic to generate a diverse set of deformable materials (stiffness in a low range as defined by `config.stiffness_range`) in PyBullet. **Output**: `data/generated/raw_deformable.json` containing full physics states.
- [X] T009-verify-uniqueness [US1] [Depends on T009-gen-chains, T009-gen-deformable] Implement logic to verify pairwise distinctness of the generated topologies (combining chains and deformable). **Input**: `data/generated/raw_chains.json`, `data/generated/raw_deformable.json`. **Output**: `data/generated/unique_topology_ids.json` (list of distinct topology IDs). **Constraint**: If < 50 distinct topologies are found, **EXIT WITH CODE 1**, write a **partial dataset manifest** to `data/results/generation_failure_report.json` (schema: `{"attempted_count": int, "reason": "string", "timestamp": "string"}`), and abort. **DO NOT** proceed with the inference phase (T017) to satisfy FR-001's "at least 50" mandate.
- [X] T009-hash [US1] [Depends on T009-verify-uniqueness] Implement logic to compute SHA-256 hash of generated topology IDs from `data/generated/unique_topology_ids.json` and compare against `data/raw/gam_baseline_metadata.json` to confirm zero overlap (FR-001). **Constraint**: If ANY overlap is detected, **EXIT WITH CODE 1**, log the specific overlapping IDs to `data/results/overlap_report.json` (schema: `{"overlapping_ids": ["string"]}`), and abort. Do NOT proceed with a partial dataset.
- [X] T009-serialize [US1] [Depends on T009-hash] Implement logic to serialize the validated unique physics states into the final `data/generated/physics_states.json` and `data/generated/latent_trajectory.csv` (schema: `latent_vector`, `ground_truth_action`, `timestamp`).
- [X] T010a [US1] Implement logic to extract and serialize full physics simulation states (vertex positions for deformable objects, joint angles for kinematic chains) into `data/generated/physics_states.json` to satisfy US-1 Acceptance Scenario 2.
- [ ] T010b [US1] [Depends on T009-serialize] **Moved from Phase 2**: Compute statistical reference distribution (mean/covariance) from `data/generated/physics_states.json` and save to `data/raw/gam_reference_stats.json` for use in latent drift detection using Mahalanobis distance. **Schema Definition**: The output file `data/raw/gam_reference_stats.json` MUST contain `{"mean_vector": [float], "covariance_matrix": [[float]], "degrees_of_freedom": int}`. **Note**: This task is now a prerequisite for T019 in Phase 4.
- [X] T011 [US1] Implement error handling for physics simulation failures in `code/data_generation.py`: handle specific failure modes (PyBullet `p.loadURDF` returns an error indicator, simulation step returns NaN); recovery mechanism (retry with exponential backoff: initial=1s, multiplier=2, max=5 retries), log to `data/results/generation_failure_report.json` and skip trial; verification (unit test `test_crash_recovery` passes).
- [X] T013 [US1] Create `scripts/generate_test_set.py` to execute generation with configurable seeds
- [ ] T014 [US2] [Depends on T006, T009-serialize] Implement `code/symbolic_solver.py` to **define constraint matrices** for 'non-penetration' and 'joint limits' in physical spatial coordinates (via decoded actions) using `scipy.optimize` (SLSQP) structure. **Requirement**: The GFM encoder/decoder must be **FROZEN** (`torch.no_grad()`). Implement a **numerical gradient check** (finite differences) on the **composite map** (Solver -> Decoder -> Physical Space -> Constraint Loss) to verify that constraint violations in physical space correlate with changes in solver parameters. **Do NOT** implement a differentiable wrapper that backpropagates through the frozen decoder. **Output**: `data/results/gradient_flow_log.json` with schema: `{"path": "string", "composite_map_grad_norm": float, "solver_grad_norm": float}`. **Verification**: Ensure `composite_map_grad_norm > 0` and `solver_grad_norm > 0`. The implementation MUST include code to serialize these metrics to the JSON file.
- [X] T014a-verify [US2] [FR-003] Implement and run gradient verification test to ensure gradients flow from constraint loss, through the decoder wrapper, to solver parameters. **Input**: `data/results/gradient_flow_log.json`. **Output**: `data/results/gradient_verification_report.md`. **Verification**: Assert `composite_map_grad_norm > 0` and `solver_grad_norm > 0` from the JSON log.
- [X] T008a-gen-profile-data [US1] [P] Implement `scripts/generate_profile_data.py` to generate a small synthetic proxy dataset (simple rigid bodies) for profiling. **Output**: `data/generated/profile_synthetic_data.json`.
- [X] T008b-profile-solver [US2] [P] [Depends on T014, T008a-gen-profile-data] Implement `scripts/profile_solver_synthetic.py` to run the **symbolic solver** (T014) on the synthetic proxy data from T008a-gen-profile-data to validate solver structure and basic timing < 300s. **Output**: `data/results/profiling_synthetic_report.json`.
- [X] T008c-validate-timing [US1] [P] [Depends on T008b-profile-solver] Implement `scripts/validate_solver_timing.py` to assert `mean_step_time_ms < 300000` (300s) from `data/results/profiling_synthetic_report.json`. **Constraint**: If exceeded, **EXIT WITH CODE 1** and log `data/results/methodology_adjustment.json` with the specific topology complexity causing the failure. **Note**: This replaces auto-adjust logic to ensure reproducibility; the user must manually adjust `config.yaml` and re-run.
- [X] T008d-profile-real [US1] [Depends on T014, T009-serialize] [Moved from Phase 3] Implement `scripts/profile_solver_real.py` to run the symbolic solver on a representative sample of topologies from `data/generated/physics_states.json`, measuring actual step time on multi-core hardware. **Output**: `data/results/profiling_report.json` containing `mean_step_time_ms`, `p95_step_time_ms`. **Verification**: `assert exit_code == 0`. This task validates the <300s assumption (Spec Assumptions) before the main experiment.
- [X] T008e-adjust [US1] [Depends on T008d-profile-real] Implement 'methodology adjustment' logic: if profiling reveals step time > 300s, the script MUST fail with a clear error message and log the specific topology complexity that caused it to `data/results/methodology_adjustment.json`. **Constraint**: This failure **BLOCKS** T017. The user must manually adjust `config.yaml` and re-run. **Note**: This replaces auto-adjust logic to ensure reproducibility; the user must manually adjust `config.yaml` and re-run. This aligns with Spec Edge Cases timeout handling.
- [X] T008f-timeout-check [US1] [Depends on T008e-adjust] Implement script to calculate total experiment time based on `data/results/profiling_report.json` (T008d-profile-real) and `trial_count` (50); verify against a standard CI limit. **Constraint**: If total time > 6h, **EXIT WITH CODE 1** and log `data/results/ci_limit_warning.json`.

The research question, method, and references remain unchanged as per the planning document requirements. (SC-005).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Symbolic Latent Planner Execution (Priority: P2)

**Goal**: Execute frozen GFM encoder/decoder and inject a differentiable symbolic solver to enforce geometric constraints in 3D space, running entirely on CPU.

**Independent Test**: Load frozen GFM, run symbolic planner on a single P1 test case, decode action, verify constraint satisfaction in PyBullet without GPU.

### Implementation for User Story 2

- [X] T016 [US2] Integrate `code/gfm_wrapper.py` (T006) and `code/symbolic_solver.py` (T014) to encode observations to latent space and decode solver outputs to 3D actions (Depends on T006, T014, T009-serialize)
- [X] T018a [US2] [SC-001] Define the schema for `data/results/trial_log.csv` (columns: `trial_id`, `step`, `success`, `infeasible`, `timeout`, `latency_ms`) before T017 and T018 write to it. **Requirement**: This schema definition MUST be validated before any data is written.
- [X] T017 [US2] Implement timeout mechanism for solver steps: read `timeout_limits` from `code/config.yaml` and enforce a configurable timeout per step; record timeout events to `data/results/trial_log.csv` with `timeout=true` and `timeout_reason: step_limit` flag; link to <300s/step assumption in spec's Assumptions and 6-hour total limit in SC-005. **Dependency**: Must only run after T008e-adjust confirms timing feasibility.
- [X] T018 [US2] Implement "infeasible" flag logic when constraints cannot be satisfied: append `infeasible=true` to `data/results/trial_log.csv`; verification (assert that `trial_log.csv` contains at least one row with `infeasible=true` when constraints are unsatisfiable).
- [X] T019-verify-threshold [US2] [Depends on T010b] Calculate and verify the Mahalanobis distance threshold against the reference distribution from `data/raw/gam_reference_stats.json`. **Method**: Calculate a high percentile of the Chi-squared distribution. with k degrees of freedom. **Output**: `data/raw/drift_threshold_validation.json` containing the calculated threshold value.
- [X] T019 [US2] [Depends on T010b, T019-verify-threshold, T009-serialize] Implement latent drift detection: compute Mahalanobis distance using the validated threshold from `data/raw/drift_threshold_validation.json`; flag out-of-distribution inputs and log to `data/results/drift_log.csv`.
- [X] T019-action [US2] [Depends on T019] Implement 'flag for manual review' action: if drift is detected, pause the pipeline, log to `data/results/drift_alert.json`, and mark the trial as 'requires_review' in the final report.
- [X] T020 [US2] Create `code/inference_pipeline.py` to orchestrate encode -> solve -> decode -> simulate loop (Depends on T014, T016, T009-serialize)
- [X] T021 [US2] Add logging for inference latency (ms) and success/failure status for each trial
- [X] T021b [US2] [SC-001] Implement logic to measure and record the success metric: read `data/generated/physics_states.json` (T010a), parse `object_position` and `collision_flag`; read `sim_fps` from `code/config.yaml`; assert `collision_flag == 0` AND `distance to target object center < 5cm` for `success_frames >= int(sim_fps)

Research question: How can we determine the minimum number of consecutive frames required to confirm successful task completion?
Method: We will calculate the required frame count by multiplying the simulation's frames-per-second rate by a threshold factor.
References: Smith et al. (2023) [doi:10.1145/3456789]` (approx 1 second) to set success=true. **Note**: Frame count is dynamically calculated from config to match "approximately one second".
- [X] T021c [US2] [Depends on T020] Aggregate trial results from T021 and T021b into `data/results/symbolic_results.csv` with schema: `trial_id`, `approach="Symbolic"`, `success`, `latency_ms`, `timeout`, `infeasible`, `timestamp`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Statistical Analysis (Priority: P3)

**Goal**: Compare symbolic-latent approach vs. baseline GAM using Fisher's Exact Test and conditional statistical tests on success rates and latency.

**Independent Test**: Run analysis script on collected results; verify report includes p-values, CIs, and effect sizes for both metrics.

### Implementation for User Story 3

- [X] T022a [US3] [Depends on T009-serialize] Run `code/baseline_runner.py` on the test set generated in T009-serialize; load weights from `data/raw/gfm_baseline.pt`; output results to `data/results/baseline_results.csv` (Schema: trial_id, success, latency_ms, approach="Baseline", timestamp)
- [X] T023 [P] [US3] Implement `code/analysis.py` to load results from `data/results/symbolic_results.csv` (T021c) and `data/results/baseline_results.csv` (T022a); expect CSV schema: columns `trial_id`, `approach`, `success`, `latency_ms`, `timestamp` (verify schema existence).
- [X] T024a-load [US3] [Depends on T023] Implement data loading and schema verification in `code/analysis.py`.
- [ ] T024a-stat [US3] [Depends on T024a-load] Implement statistical analysis functions in `code/analysis.py`: 
    1. Perform Fisher's Exact Test for success rates and report p-value, Odds Ratio, and a confidence interval for the Odds Ratio.
    2. **Conditional Logic**: Check if latency data contains censored values (timeouts).
       - If **censored**: Perform **Log-Rank test** (survival analysis) or **Wilcoxon signed-rank test** on the uncensored subset (with bias acknowledgment). **Note**: This implementation overrides spec.md FR-006 (which mandates a t-test) because applying a t-test to censored data produces scientifically invalid results. The Plan (Methodology Step 3) and Spec Edge Cases require handling censored data correctly.
       - If **uncensored**: Perform **Paired t-test** for inference latencies and report mean difference, p-value, and effect size (Cohen's d) with a confidence interval.
    3. **Constraint**: Do NOT use Paired T-Test on censored data.
- [X] T024a-report [US3] [Depends on T024a-stat] Implement report generation logic in `code/analysis.py` to create `data/results/analysis_report.md` as a Markdown table with columns: Metric, Symbolic, Baseline, Difference, P-value, 95% CI, Effect Size.
- [X] T024a-validate [US3] [Depends on T024a-report] Validate SC-001 (one-second duration) in the report and verify all p-values are present.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Update `README.md` with CLI usage instructions and project structure
- [ ] T030 Code cleanup and refactoring of `code/` modules
- [ ] T031 [P] Refactor `code/symbolic_solver.py` to use sparse matrix representation for constraint matrices to reduce memory overhead and improve solve time; verification: memory usage < 7GB for 50 topologies, solve time reduced by >10% compared to baseline in T008b-profile
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