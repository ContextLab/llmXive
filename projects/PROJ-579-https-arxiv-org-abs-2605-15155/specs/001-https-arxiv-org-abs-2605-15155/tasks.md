# Tasks: Self-Distilled Agentic Reinforcement Learning (SDAR) Reproduction

**Input**: Design documents from `/specs/579-https-arxiv-org-abs-2605-15155-repro/`
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

**Purpose**: Project initialization, constitution generation, and basic structure

- [X] T000 [Plan-Phase-0] Generate minimal project constitution at `projects/PROJ-579-https-arxiv-org-abs-2605-15155/.specify/memory/constitution.md` based on spec principles (Execution Verification, CPU-tractability) and verify its existence.
- [X] T001 [Plan-Phase-0] Create project structure per implementation plan: Create directories `src/`, `tests/`, `outputs/`, `scripts/`, `external/SDAR/` as defined in plan.md 'Project Structure' section.
- [X] T002a [P] Create `requirements.txt` in `external/SDAR/` with exact versions for Ray, PyTorch (CPU), ALFWorld, and transformers.
- [X] T002b [P] Verify `requirements.txt` installation by running `pip install -r requirements.txt` in a fresh venv and checking exit code 0.
- [X] T003 [P] Configure linting and formatting tools: Create `pyproject.toml` with `black` and `flake8` configuration sections.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Create virtual environment at `.venv` using `python -m venv .venv`.
- [X] T004b [P] Activate virtual environment and verify Python version is 3.10+.
- [X] T004c [P] Install dependencies from `external/SDAR/requirements.txt` into the active virtual environment.
- [X] T005 [P] Explicitly disable CUDA imports and set `CUDA_VISIBLE_DEVICES=""` in `scripts/setup_env.sh`.
- [X] T005b [P] **Model Proxy Configuration**: Configure the project to use `distilbert-base-uncased` as the CPU-tractable proxy model via environment variable `SDAR_MODEL_PROXY=distilbert-base-uncased` or config file override. If the default model in `external/SDAR` is GPU-only and cannot be overridden via config, **ABORT pipeline** and generate `outputs/gaps/gpu_model_blocking_gap.txt` with content `{"reason": "GPU model detected", "action": "abort"}`.
- [X] T006 [P] Configure Ray initialization script to bind exclusively to a limited number of CPU cores. (`ray init --num-cpus=2`).
- [X] T006b [P] **Training Timeout Integration**: Modify `external/SDAR/agent_system/train.py` to wrap execution with the global timeout wrapper (T006c) and include a verification step that simulates a hang to confirm the timeout triggers correctly.
- [X] T006c [P] **Global Timeout Wrapper**: Create `scripts/global_timeout_wrapper.sh` that enforces a hard timeout (e.g., a predefined duration per task/step) and logs the timeout event.
- [X] T007 [P] Create base logging infrastructure at `src/logging_config.py` defining a JSON logger that explicitly outputs keys `SDAR Gate Loss`, `RL Loss`, and `gate_activation_rate`.
- [X] T008 [P] Setup output directory structure (`outputs/health/`, `outputs/logs/`, `outputs/checkpoints/`, `outputs/gaps/`, `outputs/timing/`).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Sanity & Entry Point Execution (Priority: P1) 🎯 MVP

**Goal**: Verify that the vendored SDAR repository is correctly cloned, dependencies are resolvable on a standard Linux CPU environment, and the minimal entry point (Ray worker health check) executes without GPU acceleration errors.

**Independent Test**: Execute the Ray CPU test script `external/SDAR/tests/ray_cpu/check_worker_alive/main.py` in a fresh virtual environment. The test must pass if the environment is correctly configured.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**
> **NOTE: T009 depends on T010 to exist (even if empty) to run the test.**

- [X] T009 [US1] Contract test for Ray CPU initialization in `tests/unit/test_ray_cpu_init.py`. **Depends: T010**

### Implementation for User Story 1

- [X] T010 [US1] **Execute Vendored Entry Point**: Execute `external/SDAR/tests/ray_cpu/check_worker_alive/main.py` in the active virtual environment. Verify the script logs "2 CPUs detected" (or >= 2) and "Ray cluster healthy" without raising `ImportError` for `torch.cuda`. Generate `outputs/health/ray_health.json` with the exit code and detected CPU count.
- [X] T011 [US1] Add logic to detect and report available CPU count (expecting >= 2) without raising `ImportError` for `torch.cuda`.
- [X] T012 [US1] Ensure script exits with code 0 and generates `outputs/health/ray_health.json` on success.
- [X] T013 [US1] Verify no CUDA-related errors occur when running on a GPU-less runner.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Minimal Training Run on Subsampled Data (Priority: P2)

**Goal**: Execute a truncated SDAR training loop on a single ALFWorld task with a small batch size to verify that the core algorithm (Self-Distillation gating + RL) runs end-to-end and produces loss logs and model checkpoints.

**Independent Test**: Run the SDAR training script with hardcoded parameters for a limited number of steps on a single ALFWorld environment instance. The run must produce a loss curve file and a checkpoint file.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T014 [P] [US2] Contract test for training loss logging in `tests/unit/test_training_logs.py`.

### Implementation for User Story 2

- [X] T015 [US2] Configure `external/SDAR/agent_system/train.py` with `num_steps=10`, `batch_size=1`, `env=alfworld`, and `device="cpu"`.
- [X] T015b [US2] **Model Proxy Enforcement**: Ensure the `distilbert-base-uncased` model is loaded by setting `SDAR_MODEL_PROXY=distilbert-base-uncased` in the environment before running the training script. Verify the log confirms the proxy model is active.
- [X] T017 [US2] Ensure training loop logs "SDAR Gate Loss" and "RL Loss" for at least 5 steps using the schema defined in T007.
- [X] T017b [US2] **Logging Enforcement**: If the vendored `train.py` does not log "SDAR Gate Loss" or "RL Loss" by default, create a wrapper script `scripts/patch_train_logging.py` that monkey-patches the logger or modifies the output stream to inject these keys with actual values from the training step.
- [X] T018 [US2] Implement checkpoint saving to `outputs/checkpoints/step_5.pt` upon completion.
- [X] T019 [US2] Verify `gate_activation_rate > 0.0%` is logged to confirm the self-distillation gate is active.
- [X] T020 [US2] Generate a summary report in `outputs/logs/train_log.json` with final average loss.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluation & Metric Reporting (Priority: P3)

**Goal**: Run the evaluation script on a tiny subset of the ALFWorld test set to confirm that the system can interact with the environment, parse rewards, and output success rate metrics.

**Independent Test**: Execute the evaluation script on a representative subset of ALFWorld tasks. The system must output a JSON or text report with a "success_rate" metric.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US3] Contract test for evaluation timeout handling in `tests/unit/test_eval_timeout.py`.

### Implementation for User Story 3

- [X] T022 [US3] Configure `external/SDAR/agent_system/eval.py` with `num_tasks=5` and `task_timeout=60` seconds.
- [X] T023 [US3] Implement hard timeout enforcement per task by integrating the global wrapper from T006c to prevent infinite loops (FR-005).
- [X] T024 [US3] Ensure the evaluation loop attempts to solve each task and records success/failure.
- [X] T025 [US3] Implement logging of failure reasons (e.g., "Max steps exceeded") in `outputs/logs/eval_log.json`.
- [X] T026 [US3] Calculate and output "Success Rate" (0.0 to 1.0) to console and log file.
- [X] T027 [US3] Verify the script continues to the next task if a timeout occurs, rather than crashing.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Corrective Actions (Addressing Research Reviewer Concerns)

**Purpose**: Replace fabricated/simulated artifacts with actual execution of the SDAR codebase on ALFWorld, as mandated by multiple research-stage reviewers (Code Quality, Data Quality, Implementation Correctness, Idea Quality).

### Task: Replace Simulation with Actual Execution (Reviewers: Code Quality, Data Quality, Implementation Correctness)

- [X] T033 [US2] **CREATE SANITY CHECK SCRIPT**: Create `scripts/run_sanity_check.py` that executes `external/SDAR/tests/ray_cpu/check_worker_alive/main.py` and verifies CPU-only initialization. **Depends: T010**
- [X] T034 [US2] **CREATE MINI TRAIN SCRIPT**: Create `scripts/run_mini_train.py` that invokes `external/SDAR/agent_system/train.py` with `--num-steps=10 --batch-size=1 --device=cpu`, ensuring it imports `alfworld.agents.environment`. **Depends: T015b**
- [X] T035 [US2] **LOGGING INTEGRATION**: Verify that `run_mini_train.py` explicitly logs "SDAR Gate Loss" and "RL Loss" keys as defined in `spec.md` FR-002/FR-003, derived from actual training steps, not synthetic values. **Depends: T017b**

### Task: Decompose Logic & Enforce Modularity (Reviewer: Code Quality)

- [X] T036b [US2] **MODULARIZE ACTUAL EXECUTION**: If the vendored `external/SDAR` code is monolithic, split the *actual* execution logic into:
  - `code/src/sdar_runner.py` (logic only, <200 lines)
  - `code/src/data_loader.py` (data loading only, <200 lines)
  - `code/src/plotting.py` (visualization only, <200 lines)
  Ensure no file mixes I/O with algorithm logic. **Depends: T034**

### Task: Data Hygiene & Artifact Regeneration (Reviewers: Data Quality, Implementation Completeness, Idea Quality)

- [X] T037 [US2] **DELETE FABRICATED ARTIFACTS**: Remove `data/sdar_results.csv`, `data/sdar_summary.json`, and the entire `figures/` directory as they contain fabricated data not derived from actual execution.
- [X] T038 [US2] **REGENERATE ARTIFACTS**: Re-run the pipeline (`scripts/run_sanity_check.py` → `scripts/run_mini_train.py` → `scripts/run_evaluation.py`) to produce real `outputs/logs/train_log.json` and `outputs/logs/eval_log.json`. **Depends: T033, T034**
- [X] T039 [US2] **PARSE REAL LOGS**: Create `code/parse_logs.py` to extract actual metrics (Success Rate, Gate Activation, Loss values) from the real execution logs. **Expected Format**: JSON lines with keys "SDAR Gate Loss", "RL Loss", "success". Populate `data/sdar_results.csv` and `data/sdar_summary.json` with empirically derived values. **Depends: T033, T034**
- [X] T040 [US2] **REGENERATE FIGURES**: If visualization is required, regenerate `figures/gate_attenuation.png` and `figures/success_rate_vs_noise.png` using the new, empirically derived data, ensuring consistency with actual results.

### Task: Documentation Correction (Reviewers: Filesystem Hygiene, Idea Quality, Implementation Completeness)

- [X] T041 [US2] **UPDATE REPRODUCIBILITY REPORT**: Rewrite `docs/reproducibility/reproducibility_report.md` to:
  - Correct all file paths (e.g., `code/sdar_sim.py` → `scripts/run_mini_train.py`, `code/requirements.txt` → `requirements.txt`).
  - Align "Environment" section with `spec.md` constraints: Change "Steps: 1000" to "Steps: 10", "Batch Size: 32" to "Batch Size: 1".
 - Remove all claims of "[deferred] ALFWorld coverage" or "Measured metrics" until actual execution proves them.
  - Add a "Gap Analysis" section detailing the current inability to run the full pipeline on CPU and the specific steps taken to enable it.
  - Explicitly state that results are from a multi-step diagnostic run, not a full statistical validation.
  **Depends: T032, T033, T034, T038, T039**
- [X] T042 [US2] **VERIFY ARTIFACT PATHS**: Ensure `data/sdar_results.csv` exists at the root `data/` directory (or update report to reflect actual location if it differs, e.g., `outputs/logs/`).

### Task: Baseline Comparison Implementation (Reviewers: Implementation Completeness, Idea Quality)

- [X] T043b [US4] **VERIFY/CHECK PPO BASELINE**: Check if `external/SDAR` contains a PPO baseline script. If not, create `code/baseline_ppo.py` using `stable-baselines3` or equivalent to implement a standard PPO agent for ALFWorld.
- [X] T043 [US4] **CREATE BASELINE SCRIPT**: Create `scripts/run_baseline.py` that executes a standard PPO training run (without self-distillation) for 5 independent random seeds with `num_steps=1000` (aggressively downscaled) to enable statistical comparison. **Depends: T043b**
- [X] T044 [US4] **STATISTICAL ANALYSIS**: Create `code/analyze_results.py` to perform a paired t-test on the results from 5 seeds comparing SDAR vs. PPO, outputting a p-value and significance conclusion to `data/statistical_analysis.json`.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T028 [P] Aggregate all logs and checkpoints into `outputs/final_report.json` containing keys: `total_time`, `success_rate`, `gate_loss_avg`, `rl_loss_avg`.
- [X] T029a [P] Verify total wall-clock time for the pipeline is ≤ 6 hours (expected < 30 mins).
- [X] T029b [P] **Measure Pipeline Time**: Create `scripts/measure_pipeline_time.sh` that wraps the full pipeline execution and writes `outputs/pipeline_timing.json` with start/end timestamps and duration.
- [X] T030 [P] Run full pipeline validation script to ensure SC-001 through SC-005 are met.
- [X] T031 [P] Update `quickstart.md` with instructions for running the CPU-only reproduction pipeline.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Revision (Phase 6)**: Depends on completion of Phase 2 and initial execution of Phases 3-5. **MUST** be completed before any statistical claims are made.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **User Story 4 (P1)**: Depends on US2 and US3 completion; requires real execution logs for statistical analysis.

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
# Launch all models for User Story 1 together:
Task: "Execute vendored entry point at external/SDAR/tests/ray_cpu/check_worker_alive/main.py"
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
- **CRITICAL**: All tasks in Phase 6 (Revision) MUST be completed before any statistical claims or reproducibility reports are finalized. Fabricated data is strictly prohibited.