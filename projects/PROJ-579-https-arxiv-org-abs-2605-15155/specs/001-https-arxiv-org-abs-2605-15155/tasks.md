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

- [ ] T004a [P] Create virtual environment at `.venv` using `python -m venv.venv`. <!-- FAILED: unspecified -->
- [X] T004b [P] Activate virtual environment and verify Python version is 3.10+.
- [X] T004c [P] Install dependencies from `external/SDAR/requirements.txt` into the active virtual environment.
- [X] T005 [P] Explicitly disable CUDA imports and set `CUDA_VISIBLE_DEVICES=""` in `scripts/setup_env.sh`.
- [X] T005b [P] **Model Proxy Configuration**: Configure the project to use `distilbert-base-uncased` as the CPU-tractable proxy model via environment variable `SDAR_MODEL_PROXY=distilbert-base-uncased` or config file override. If the default model in `external/SDAR` is GPU‑only and cannot be overridden via config, **ABORT pipeline** and generate `outputs/gaps/gpu_model_blocking_gap.txt` with content `{"reason": "GPU model detected", "action": "abort"}`. **If abort occurs, execute task T015c to patch the vendored code for CPU fallback.**
- [X] T006 [P] Configure Ray initialization script to bind exclusively to a limited number of CPU cores. (`ray init --num-cpus=2`).
- [X] T006c [P] **Global Timeout Wrapper**: Create `scripts/global_timeout_wrapper.sh` that enforces a hard timeout (e.g., a predefined duration per task/step) and logs the timeout event.
- [X] T006b [P] **Training Timeout Integration**: Modify `external/SDAR/agent_system/train.py` to wrap execution with the global timeout wrapper from T006c and include a verification step that simulates a hang to confirm the timeout triggers correctly. **Depends:** T006c.
- [X] T007 [P] Create base logging infrastructure at `src/logging_config.py` defining a JSON logger that explicitly outputs keys `SDAR Gate Loss`, `RL Loss`, `gate_activation_rate`, `kl_divergence`, `teacher_update_count`.
- [X] T007b [P] **Log KL Divergence & Teacher Updates**: Extend `src/logging_config.py` or the training script to emit `kl_divergence` and `teacher_update_count` each logging interval. **Depends:** T007.
- [X] T008 [P] Setup output directory structure (`outputs/health/`, `outputs/logs/`, `outputs/checkpoints/`, `outputs/gaps/`, `outputs/timing/`).

---

## Phase 3: User Story 1 - Environment Sanity & Entry Point Execution (Priority: P1) 🎯 MVP

**Goal**: Verify that the vendored SDAR repository is correctly cloned, dependencies are resolvable on a standard Linux CPU environment, and the minimal entry point (Ray worker health check) executes without GPU acceleration errors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**
> **NOTE: T009 depends on T009a to exist (even if stub) to run the test.**

- [ ] T009a [US1] **Create Ray Health‑Check Stub**: Write `scripts/stub_ray_check.py` that imports the Ray health‑check module (if present) and exits with code 1. This stub allows the contract test to exist before the real implementation.
- [ ] T009 [US1] Contract test for Ray CPU initialization in `tests/unit/test_ray_cpu_init.py`. **Depends:** T009a.

### Implementation for User Story 1

- [ ] T010 [US1] **Execute Vendored Entry Point**: Execute `external/SDAR/tests/ray_cpu/check_worker_alive/main.py` in the active virtual environment. Verify the script logs "2 CPUs detected" (or >= 2) and "Ray cluster healthy" without raising `ImportError` for `torch.cuda`. Generate `outputs/health/ray_health.json` with the exit code and detected CPU count.
- [ ] T011 [US1] Add logic to detect and report available CPU count (expecting >= 2) without raising `ImportError` for `torch.cuda`.
- [ ] T012 [US1] Ensure script exits with code 0 and generates `outputs/health/ray_health.json` on success.
- [~] T013 [US1] Verify no CUDA‑related errors occur when running on a GPU‑less runner.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Minimal Training Run on Subsampled Data (Priority: P2)

**Goal**: Execute a truncated SDAR training loop on a single ALFWorld task with a small batch size to verify that the core algorithm (Self‑Distillation gating + RL) runs end‑to‑end and produces loss logs and model checkpoints.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T014 [P] [US2] Contract test for training loss logging in `tests/unit/test_training_logs.py`.

### Implementation for User Story 2

- [~] T015 [US2] Configure `external/SDAR/agent_system/train.py` with `num_steps=10`, `batch_size=1`, `env=alfworld`, and `device="cpu"`. <!-- ATOMIZE: requested -->
- [~] T015b [US2] **Model Proxy Enforcement**: Ensure the `distilbert-base-uncased` model is loaded by setting `SDAR_MODEL_PROXY=distilbert-base-uncased` in the environment before running the training script. Verify the log confirms the proxy model is active.
- [~] T015c [US2] **Patch Training for Required Logs**: If `train.py` does not emit `kl_divergence` or `teacher_update_count`, modify it to log these values (using the logger from T007). This ensures real values are captured rather than synthetic injection.
- [~] T017 [US2] Ensure training loop logs "SDAR Gate Loss", "RL Loss", "kl_divergence", and "teacher_update_count" for at least 5 steps using the schema defined in T007.
- [~] T018 [US2] Implement checkpoint saving to `outputs/checkpoints/step_5.pt` upon completion.
- [~] T019 [US2] Verify that the logs contain entries for `gate_activation_rate`, `kl_divergence`, and `teacher_update_count` (presence check only; no hard numeric threshold).
- [~] T020 [US2] Generate a summary report in `outputs/logs/train_log.json` with final average loss and the newly logged metrics.

**Checkpoint**: User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluation & Metric Reporting (Priority: P3)

**Goal**: Run the evaluation script on a tiny subset of the ALFWorld test set to confirm that the system can interact with the environment, parse rewards, and output success rate metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T021 [P] [US3] Contract test for evaluation timeout handling in `tests/unit/test_eval_timeout.py`.

### Implementation for User Story 3

- [~] T022 [US3] Configure `external/SDAR/agent_system/eval.py` with `num_tasks=5` and `task_timeout=60` seconds.
- [~] T023 [US3] Implement hard timeout enforcement per task by integrating the global wrapper from T006c to prevent infinite loops (FR-005).
- [~] T024 [US3] Ensure the evaluation loop attempts to solve each task and records success/failure.
- [~] T025 [US3] Implement logging of failure reasons (e.g., "Max steps exceeded") in `outputs/logs/eval_log.json`.
- [~] T026 [US3] Calculate and output "Success Rate" (0.0 to 1.0) to console and log file.
- [~] T027 [US3] Verify the script continues to the next task if a timeout occurs, rather than crashing the entire evaluation suite.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Corrective Actions (Addressing Research Reviewer Concerns)

**Purpose**: Replace fabricated/simulated artifacts with actual execution of the SDAR codebase on ALFWorld, and ensure full compliance with FR‑007 / Constitution Principle VI.

- [ ] T033_create [US2] **Create Sanity‑Check Script**: Write `scripts/run_sanity_check.py` that executes `external/SDAR/tests/ray_cpu/check_worker_alive/main.py` and writes results to `outputs/health/ray_health.json`. **No dependency on T010** (script creation independent).
- [ ] T033_exec [US2] **Execute Sanity‑Check**: Run `scripts/run_sanity_check.py` and verify successful completion. **Depends:** T033_create.
- [ ] T034_create [US2] **Create Mini‑Train Script**: Write `scripts/run_mini_train.py` that invokes `external/SDAR/agent_system/train.py` with the parameters from T015‑T015c. Ensure it redirects stdout/stderr to `outputs/logs/train_raw.log`.
- [ ] T034_exec [US2] **Execute Mini‑Train**: Run `scripts/run_mini_train.py` to produce `outputs/logs/train_raw.log` and checkpoint `outputs/checkpoints/step_5.pt`. **Depends:** T034_create, T015c.
- [~] T036a [US2] **Analyse Vendored Code Structure**: Scan `external/SDAR/agent_system/` to identify logical boundaries (data loading, algorithm, I/O). Produce a brief report `outputs/timing/code_structure_report.txt`. This informs subsequent modularisation.
- [~] T036b [US2] **Modularise Execution**: Refactor vendored code into separate modules under `src/`: <!-- ATOMIZE: requested -->
 - `src/sdar_runner.py` (training loop entry point)
 - `src/data_loader.py` (environment and data handling)
 - `src/logging_utils.py` (logging configuration)
 Ensure each file <200 lines and no I/O is mixed with core algorithm. **Depends:** T036a.
- [~] T037 [US2] **Delete Fabricated Artifacts**: If `data/sdar_results.csv` or `figures/` exist, delete them and log the action to `outputs/gaps/fabrication_cleanup.log`. If they do not exist, log “No fabricated artifacts found”. **Depends:** T034_exec (ensures real artifacts now exist).
- [~] T038b [US2] **Parse Real Training Logs**: Run `code/parse_logs.py` to extract `SDAR Gate Loss`, `RL Loss`, `kl_divergence`, `teacher_update_count`, and `gate_activation_rate` from `outputs/logs/train_raw.log` into `data/sdar_results.csv` and `data/sdar_summary.json`. **Depends:** T034_exec.
- [~] T039 [US2] **Regenerate Figures** (optional): Using the newly created CSV, generate any required plots (e.g., `figures/gate_vs_kl.png`). **Depends:** T038b.
- [~] T040 [US2] **Update Reproducibility Report**: Revise `docs/reproducibility/reproducibility_report.md` to reference real artifact paths, include the new log‑parsing steps, and add a “Gap Analysis” section describing limitations of the 10‑step run. **Depends:** T038b, T039.

### Baseline Comparison Implementation

- [ ] T043b_check [US4] **Check for Existing PPO Baseline**: Scan `external/SDAR/` for a PPO training script. Log result to `outputs/logs/ppo_check.log`.
- [ ] T043b_impl [US4] **Create PPO Baseline (if missing)**: If no PPO script exists, implement `code/baseline_ppo.py` using `stable-baselines3` to train a PPO agent on the same ALFWorld environment with `num_steps=1000` and seeds 0‑4. **Depends:** T043b_check.
- [ ] T043c [US4] **Verify Baseline Parity**: Ensure PPO script uses identical environment configuration, random seeds, and step count as the SDAR run. Generate a config diff report `outputs/logs/ppo_config_match.log`. **Depends:** T043b_impl (or existing script).
- [ ] T044 [US4] **Run PPO Baseline**: Execute `scripts/run_baseline.py` for the 5 seeds, producing logs in `outputs/logs/ppo_seed_{i}.log`. **Depends:** T043c.
- [ ] T045b [US4] **Parse PPO Logs**: Extract final success rates from PPO logs into `data/ppo_results.csv`. **Depends:** T044.
- [ ] T046 [US4] **Statistical Analysis Script**: Implement `code/analyze_results.py` to perform a paired t‑test (or Wilcoxon signed‑rank if non‑normal) between SDAR and PPO success rates from `data/sdar_results.csv` and `data/ppo_results.csv`. Output `data/statistical_analysis.json` with p‑value and significance flag. **Depends:** T038b, T045b.
- [ ] T047 [US4] **Statistical Report Verification**: Verify that `data/statistical_analysis.json` contains a valid p‑value and that the significance conclusion matches the data. **Depends:** T046.

---

## Phase 7: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T028 [P] Aggregate all logs and checkpoints into `outputs/final_report.json` containing keys: `total_time`, `success_rate`, `gate_loss_avg`, `rl_loss_avg`, `kl_divergence_avg`, `teacher_update_count_total`.
- [ ] T029a [P] Verify total wall‑clock time for the pipeline is ≤ 6 hours (expected < 30 mins).
- [ ] T029b [P] **Measure Pipeline Time**: Create `scripts/measure_pipeline_time.sh` that wraps the full pipeline execution and writes `outputs/pipeline_timing.json` with start/end timestamps and duration.
- [ ] T030 [P] Run full pipeline validation script to ensure SC‑001 through SC‑005 are met.
- [ ] T031 [P] Update `quickstart.md` with instructions for running the CPU‑only reproduction pipeline.

---

## Phase 8: Final Verification & Gap Resolution (Addressing Remaining Reviewer Concerns)

**Purpose**: Final validation of the reproduction pipeline to ensure all reviewer concerns (Code Quality, Data Quality, Implementation Correctness, Idea Quality, Filesystem Hygiene) are fully resolved and the project is ready for research completion.

- [ ] T045 [US2] **FINAL EXECUTION VERIFICATION**: Validate that artifacts produced by prior execution tasks exist and are well‑formed:
 - `outputs/health/ray_health.json` (from T033_exec)
 - `outputs/checkpoints/step_5.pt` (from T034_exec)
 - `outputs/logs/train_log.json` (from T020)
 - `data/sdar_results.csv` (from T038b)
 - `data/statistical_analysis.json` (from T046)
 No re‑execution of the pipeline is performed; this task only inspects existing outputs. **Depends:** T033_exec, T034_exec, T038b, T046.
- [ ] T046 [US2] **LOG VERIFICATION**: Ensure `outputs/logs/train_log.json` contains real values for `SDAR Gate Loss`, `RL Loss`, `kl_divergence`, and `teacher_update_count` (no synthetic placeholders). **Depends:** T045.
- [ ] T047 [US2] **CHECKPOINT VERIFICATION**: Verify that `outputs/checkpoints/step_5.pt` is a valid PyTorch checkpoint file (loadable with `torch.load`). **Depends:** T045.
- [ ] T048 [US2] **DATA PROVENANCE CHECK**: Confirm that `data/sdar_results.csv` and `data/sdar_summary.json` are generated solely from parsing `outputs/logs/train_raw.log` (no manual edits). **Depends:** T038b.
- [ ] T049 [US2] **FABRICATION SCAN**: Run `scripts/scan_for_synthetic_data.py` over all data artifacts to ensure no patterns like `random.*` or hard‑coded placeholders exist. Log findings to `outputs/gaps/fabrication_scan.log`. **Depends:** T048.
- [ ] T050 [US2] **METRIC CONSISTENCY**: Cross‑check that metrics in `data/sdar_results.csv` match those reported in `outputs/logs/train_log.json` and `outputs/logs/eval_log.json`. **Depends:** T048.
- [ ] T051 [US2] **FINAL REPRODUCIBILITY REPORT**: Update `docs/reproducibility/reproducibility_report.md` to:
 - Confirm all file paths are correct.
 - Verify execution parameters (Steps: 10, Batch Size: minimal) match actual runs.
 - Include a “Gap Analysis” section detailing limitations of the 10‑step run and diagnostic nature of statistical results.
 - Remove any unsupported claims of statistical significance. **Depends:** T045, T050.
- [ ] T052 [US2] **ARTIFACT INVENTORY**: Generate `outputs/artifact_inventory.yaml` listing all files under `data/`, `outputs/`, and `figures/` with SHA‑256 hashes and generation timestamps. **Depends:** T045.
- [ ] T053 [US2] **REPORT CONSISTENCY CHECK**: Verify that every figure/table in `docs/reproducibility/reproducibility_report.md` is produced from the actual data artifacts listed in the inventory. Log any mismatches to `outputs/gaps/report_consistency.log`. **Depends:** T052, T051.

---

## Phase 9: Optional Extensions (Future Work)

- [ ] T060 [P] Explore scaling the training to a sufficient number of steps per seed on a larger runner (if resources permit) and re‑run statistical analysis for higher power.
- [ ] T061 [P] Integrate GPU‑enabled optional path for full‑scale reproduction (outside CI constraints).

---

## Dependency Summary

- **Foundational Phase** must complete before any User Story work.
- **User Stories** can run in parallel after Foundational.
- **Revision Phase** (Phase 6) depends on initial User Story implementations to have real artifacts to replace.
- **Baseline Comparison** tasks ensure parity before statistical analysis.
- **Final Verification** (Phase 8) only inspects artifacts; it does not re‑run heavy computations.
- **Polish Phase** aggregates results and prepares documentation.

---

*All tasks respect the CPU‑only, ≤ 7 GB RAM, ≤ 6 h CI constraints. No GPU‑only libraries are used, and all data artifacts are derived from real execution logs.*
