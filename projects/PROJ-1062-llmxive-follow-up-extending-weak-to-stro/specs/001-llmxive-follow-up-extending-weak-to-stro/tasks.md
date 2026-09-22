# Tasks: llmXive follow-up: extending "Weak-to-Strong Generalization via Direct On-Policy Distillation"

**Input**: Design documents from `/specs/001-cross-arch-distillation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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

- [ ] T001 Create project structure per implementation plan: Create directories `src/data/`, `src/models/`, `src/training/`, `src/analysis/`, `src/config/`, `tests/unit/`, `tests/integration/`, `contracts/`, `data/raw/`, `data/processed/`, `data/results/`, `artifacts/`. (Plan: Project Structure)
- [X] T002 Initialize Python project with `transformers`, `datasets`, `torch`, `bitsandbytes==0.43.0 `, `scikit-learn`, `scipy`, `pandas`, `numpy`, `statsmodels`, `pyyaml`, `ruff`, `black` dependencies. **Verify**: `requirements.txt` exists and contains these packages; run `pip install -r requirements.txt` successfully. **Constraint**: FR-007 (CPU-only, int8).
- [ ] T003 [P] Configure linting (ruff) and formatting (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `config/hyperparams.yaml` with hyperparameters, paths, seeds, and memory constraints ( (2507.07101, https://arxiv.org/abs/2507.07101), gradient_accumulation steps). **Must include pinned `epsilon` value for reward smoothing.**
- [ ] T004.1 [P] Implement `src/core/config_validator.py` to verify `config/hyperparams.yaml` exists and contains required keys (e.g., `epsilon`, `batch_size`, `accumulation_steps`). **Halt if missing.** (Reproducibility) **DEPENDENCY: T004**
- [ ] T005.0 [P] [Foundational] Implement `src/data/download_aime_verified.py` to **first fetch** `HuggingFaceH4/aime_2024` from the HuggingFace Hub. **Check if the dataset contains a `human_verified_label` field.** **If the field is missing, log a WARNING and proceed using intrinsic metrics (log-prob of ground-truth tokens).** **If the field exists, validate it.** **Output**: `data/processed/dataset_validation_status.json` recording the check result and fallback mode. (SC-006, FR-009)
- [ ] T006 Implement `src/data/preprocess.py` to format prompts and extract ground-truth reasoning steps for AIME subset. **Logic**: Extract reasoning steps from the `solution` field using regex patterns (e.g., `r'### Solution:.*?(?=### Answer|$)'`) to isolate the final answer and reasoning chain. (FR-001)
- [ ] T006.1a [P] Implement `src/data/split_aime.py` to split the AIME dataset into training and held-out sets. **Stratification Logic**: If the dataset contains a `difficulty` or `reasoning_type` field, stratify by that field. **If these fields are missing (as is common in raw AIME datasets), stratify deterministically by `hash(problem_id) % 2`** to ensure a balanced 50/50 split of problem IDs between train and holdout sets, preventing data leakage. Save to `data/processed/aime_train.jsonl` and `data/processed/aime_holdout.jsonl`. (FR-009)
- [ ] T006.1b [US1] Implement validation logic in `src/data/validate_split.py` to confirm the held-out set contains no problems with overlapping reasoning steps to the training set, preventing data leakage in the small N=200 sample. **Output**: `data/processed/split_validation_report.json` with Jaccard index < 0.01 (or warning if higher). **DEPENDENCY**: T006.1a, T005.0. (FR-009, Edge Case)
- [ ] T006.1c [Foundational] Implement `src/data/check_reasoning_overlap.py` to explicitly calculate token-level overlap (Jaccard index) between train and holdout reasoning steps. **Output**: `data/processed/reasoning_overlap_report.json`. **DEPENDENCY**: T006.1a, T005.0. (FR-009, Edge Case)
- [ ] T006.1d [Foundational] Implement `src/data/enforce_overlap_policy.py` to check the output of T006.1c. **Logic**: If overlap > 0.01, log a WARNING but do NOT halt. (FR-009, Edge Case) **DEPENDENCY**: T006.1c.
- [ ] T007 Implement `src/models/teacher_loader.py` to load dense Transformer teacher (pre-RL and post-RL) in low-precision integer format with CPU offloading
- [ ] T008 [P] [US1] Implement `src/models/moe_student.py` to load a verified **~1B parameter MoE** student model from HuggingFace using int8 quantization and CPU offloading to fit within 7GB RAM (See US1). **Must include pre-load size verification** to confirm model ID, parameter count <= 2B (active params ~1B), and size < 7GB RAM before loading. **Logic**: Search HuggingFace for models matching "Mixtral" or "MoE" with ~1B active params; verify size; raise `ValueError` if no match or size > 7GB. **If the model exceeds 7GB RAM or is not found, raise `ValueError` (do not fallback to larger models or synthetic models).** (FR-002, US1 - Modified for Feasibility)
- [ ] T008.1 [P] [US1] Implement `src/models/verify_moe_size.py` to perform pre-load memory estimation for T008. **Output**: `data/processed/moe_size_check.json`. **HALT** if estimated size > 7GB. (FR-007)
- [ ] T009 [P] [US2] Implement `src/models/ssm_student.py` to load the **~1.3B parameter SSM** student model (e.g., Mamba variant) in int precision with CPU offloading. **Must include pre-load size verification** to confirm parameter count is in the 1.3B range. **Logic**: Search HuggingFace for "Mamba" or "SSM" models with ~1.3B params; verify size; raise `ValueError` if mismatch or size > 7GB. **If int8 fails (e.g., custom kernel error), raise `ValueError` and halt; DO NOT fallback to NF4 or GGUF.** **Log the error.** (FR-002, FR-007, US2)
- [ ] T009.1 [P] [US2] Implement `src/models/verify_ssm_size.py` to perform pre-load memory estimation for T009. **Output**: `data/processed/ssm_size_check.json`. **HALT** if estimated size > 7GB. (FR-007)
- [ ] T010 Implement `src/core/reward_computation.py` with epsilon-smoothing (a small positive constant) for log-ratio implicit reward calculation. **DEPENDENCY: T004 (config for epsilon value).**
- [ ] T011.5 [P] Implement `src/core/memory_monitor.py` as a standalone utility module with memory profiler and OOM handler for testing.
- [ ] T011.6 [P] Implement `src/core/hard_floor_enforcer.py` to enforce the hard limit of batch_size=1.
- [ ] T011.7 [US1] Implement `tests/unit/test_hard_floor.py::test_oom_fallback_triggers` to **validate the fallback logic**: simulate a scenario where the memory monitor fails to detect OOM and verify that `hard_floor_enforcer` still triggers correctly. **DEPENDENCY: T011.6**
- [ ] T011.8 [P] Implement `src/core/time_budget_enforcer.py`: Calculate dynamic step count based on average training time per step and remaining time. Enforce a time limit with automatic termination and partial result saving.
- [ ] T011.9 [Foundational] Implement `src/core/memory_profiler.py` to profile memory usage for the specific model/dataset combination and **output `data/processed/memory_config.json`** with the maximum safe `accumulation_steps`. **DEPENDENCY: T008.1, T009.1.** (Removed [P] to enforce sequential order)
- [ ] T011.9.1 [Foundational] Implement `src/core/accumulation_calculator.py` to calculate `accumulation_steps` such that `effective_batch_size = batch_size * accumulation_steps = 1`. **Logic**: Read `max_safe_accumulation` from `memory_config.json` (T011.9). If `max_safe_accumulation` < 1, set `accumulation_steps = 1` and log warning. **Output**: `data/processed/accumulation_config.json`. **DEPENDENCY**: T011.9. (FR-007)
- [ ] T011.9.2 [Foundational] Implement `src/core/effective_batch_size_enforcer.py` to explicitly calculate and enforce `accumulation_steps = 1` for `effective_batch_size = 1`. **Logic**: Read `accumulation_config.json`; if `accumulation_steps` != 1, set to 1 and log warning. **Output**: `data/processed/final_accumulation_config.json`. **DEPENDENCY**: T011.9.1. (FR-007)
- [ ] T012 [P] Implement `src/core/evaluator.py` for log-probability improvement calculation and statistical testing
- [ ] T013 [P] Implement `src/scripts/hash_artifacts.py` to generate SHA-256 hashes for data and artifacts
- [ ] T014 [P] Implement `src/tests/test_reward.py` unit tests for reward calculation logic and epsilon-smoothing
- [ ] T015 [P] Implement `src/tests/test_memory.py` sanity checks for RAM usage under GB constraint and model size verification
- [ ] T014.6 [US1] Implement `src/tests/test_evaluator_integration.py` to **integrate** independent human-verified labels (from T005.0) into log-probability metric calculation.
- [ ] T039 [P] [US3] Implement paired t-test/Wilcoxon signed-rank test logic in `src/core/statistical_tests.py`
- [ ] T040.5 [P] [US3] Implement cluster-robust standard errors, multiple-comparison correction (Bonferroni/Holm-Bonferroni), and significance classification logic in `src/core/statistical_tests.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Cross-Architecture Signal Transfer Validation (Priority: P1) 🎯 MVP

**Goal**: Compute implicit reward from Transformer teacher and train MoE student to validate signal transfer across architectural families.

**Independent Test**: Execute distillation loop for MoE student using Transformer-derived implicit reward. Compare log-probability improvement on AIME subset against baseline MoE model.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US1] Contract test for MoE reward signal transfer. **File**: `tests/unit/test_moe_reward.py::test_reward_shape`. **Assert**: Reward shape matches `(batch_size, seq_len)` and values are finite. Schema: `contracts/reward_schema.yaml`.
- [ ] T017 [P] [US1] Integration test for MoE distillation loop. **File**: `tests/integration/test_moe_distillation.py::test_training_loop`. **Assert**: Training loop completes a set number of steps and saves a checkpoint to `data/checkpoints/moe_test.pt`.

### Implementation for User Story 1

- [ ] T018 [P] [US1] Implement MoE-specific data loading pipeline.
- [ ] T019 [US1] Implement MoE baseline training. **Algorithm**: Load teacher final distribution; compute KL-divergence loss; **Gradient Accumulation**: Read `accumulation_steps` from `data/processed/final_accumulation_config.json` (T011.9.2); **Constraint**: Respect hard floor `batch_size=1` from T011.6 (enforced by T011.6); **Output**: Save checkpoint to `data/checkpoints/moe_baseline_final.pt`. **DEPENDENCY**: T010, T008, T011.9, T011.9.1, T011.9.2, T011.6.
- [ ] T020 [US1] Implement MoE Direct-OPD training. **Algorithm**: Compute log-ratio implicit reward (post-RL vs pre-RL); apply epsilon-smoothing; maximize log-prob ratio (minimize negative reward); **Gradient Accumulation**: Read `accumulation_steps` from `data/processed/final_accumulation_config.json` (T011.9.2); **Constraint**: Respect hard floor `batch_size=1` from T011.6 (enforced by T011.6); **Output**: Save checkpoint to `data/checkpoints/moe_opd_final.pt`. **DEPENDENCY**: T010, T008, T011.9, T011.9.1, T011.9.2, T011.6.
- [ ] T021 [US1] Implement MoE evaluation script. **Metric**: Calculate log-probability improvement of ground-truth reasoning steps (prefix-only) on held-out set. **Output**: Save to `data/results/moe_eval_metrics.json`. **DEPENDENCY**: T020, T019.
- [ ] T022 [US1] Add memory constraint enforcement logic to MoE training loop.
- [ ] T023 [US1] Add epsilon-smoothing verification in MoE reward computation.
- [ ] T024 [US1] Implement experiment runner script for MoE. **Logic**: Calculate dynamic training steps based on `time_budget_enforcer`; set `batch_size=1`, `seed=42`, `gradient_accumulation_steps` from `final_accumulation_config.json`.
- [ ] T025 [US1] Execute MoE experiment using runner from T024; save results to `data/results/moe_results.json`. **DEPENDENCY**: T024, T021.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - State-Space Model (SSM) Signal Transfer Validation (Priority: P2)

**Goal**: Replicate signal transfer experiment using SSM student to verify consistency across non-Transformer families

**Independent Test**: Execute identical distillation loop for SSM student using the same Transformer-derived implicit reward. Compare performance gains against SSM baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US2] Contract test for SSM reward signal transfer. **File**: `tests/unit/test_ssm_reward.py::test_reward_shape`. **Assert**: Reward shape matches `(batch_size, seq_len)` and values are finite. Schema: `contracts/reward_schema.yaml`.
- [ ] T031 [P] [US2] Integration test for SSM distillation loop. **File**: `tests/integration/test_ssm_distillation.py::test_training_loop`. **Assert**: Training loop completes a set number of steps and saves a checkpoint to `data/checkpoints/ssm_test.pt`.

### Implementation for User Story 2

- [ ] T028 [P] [US2] Implement SSM-specific data loading pipeline.
- [ ] T029 [US2] Implement SSM baseline training. **Algorithm**: Load teacher final distribution; compute KL-divergence loss; **Gradient Accumulation**: Read `accumulation_steps` from `data/processed/final_accumulation_config.json` (T011.9.2); **Constraint**: Respect hard floor `batch_size=1` from T011.6 (enforced by T011.6); **Output**: Save checkpoint to `data/checkpoints/ssm_baseline_final.pt`. **DEPENDENCY**: T010, T009, T011.9, T011.9.1, T011.9.2, T011.6.
- [ ] T030 [US2] Implement SSM Direct-OPD training. **Algorithm**: Compute log-ratio implicit reward (post-RL vs pre-RL); apply epsilon-smoothing; maximize log-prob ratio (minimize negative reward); **Gradient Accumulation**: Read `accumulation_steps` from `data/processed/final_accumulation_config.json` (T011.9.2); **Constraint**: Respect hard floor `batch_size=1` from T011.6 (enforced by T011.6); **Output**: Save checkpoint to `data/checkpoints/ssm_opd_final.pt`. **DEPENDENCY**: T010, T009, T011.9, T011.9.1, T011.9.2, T011.6.
- [ ] T031 [US2] Implement SSM evaluation script. **Metric**: Calculate log-probability improvement of ground-truth reasoning steps (prefix-only) on held-out set. **Output**: Save to `data/results/ssm_eval_metrics.json`. **DEPENDENCY**: T030, T029.
- [ ] T032 [US2] Implement SSM architecture compatibility check.
- [ ] T033 [US2] Add memory constraint enforcement logic to SSM training loop.
- [ ] T034 [US2] Implement experiment runner script for SSM. **Logic**: Calculate dynamic training steps based on `time_budget_enforcer`; set `batch_size=1`, `seed=42`, `gradient_accumulation_steps` from `final_accumulation_config.json`.
- [ ] T035 [US2] Execute SSM experiment using runner from T034; save results to `data/results/ssm_results.json`. **DEPENDENCY**: T034, T031.
- [ ] T036 [US2] Implement comparative summary generator. **Requirement**: Generate a text block explicitly stating whether signal degradation is consistent across architectures (MoE vs SSM) based on the performance gains. **Output**: `data/results/comparative_summary.txt`. **DEPENDENCY**: T025, T035.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Multiplicity Correction (Priority: P3)

**Goal**: Perform statistical significance testing with multiple-comparison correction to validate findings

**Independent Test**: Calculate p-values for performance gains, apply Bonferroni/Holm-Bonferroni correction, and classify significance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T045 [P] [US3] Contract test for statistical significance calculation. **File**: `tests/unit/test_stats.py::test_pvalue_calculation`.
- [ ] T046 [P] [US3] Integration test for multiple-comparison correction. **File**: `tests/integration/test_stats_integration.py::test_bonferroni_correction`.

### Implementation for User Story 3

- [ ] T042.5 [US3] Implement `src/core/results_aggregator.py` to calculate 'performance gain' delta for MoE and SSM. **DEPENDENCY**: T025, T035.
- [ ] T043 [US3] Run statistical analysis on MoE and SSM performance gain deltas using logic from T039, T040.5. **DEPENDENCY**: T042.5.
- [ ] T044 [US3] Generate statistical report with raw and adjusted p-values in `data/results/statistical_report.json`. **DEPENDENCY**: T043. **Constraint**: Use fixed sample size n=5 seeds as per SC-002.
- [ ] T045 [US3] Validate statistical report against SC-002 and SC-004 using standard statistical practice. **DEPENDENCY**: T044.
- [ ] T046 [P] Update documentation in `docs/` with experiment results and limitations.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] [Polish] Refactor MoE/SSM training logic into `src/training/distillation_loop.py`, `src/training/moe_training.py`, and `src/training/ssm_training.py` per plan.md structure. **Remove any references to non-existent `src/core/moe_direct_opd.py` or `src/core/ssm_direct_opd.py`.** Move functions `compute_reward`, `train_step`, `evaluate` to respective files. (Writing)
- [ ] T049.1 [P] Add unit test for epsilon-smoothing edge case.
- [ ] T049.2 [P] Add unit test for OOM handling.
- [ ] T049.3 [P] Add unit test for time-out handling.
- [ ] T050 Security hardening for data loading and model checkpoint verification
- [ ] T051 Run `quickstart.md` validation to ensure full pipeline reproducibility
- [ ] T053 [P] [US1/US2] Add a pre-training validation step in `src/models/moe_student.py` and `src/models/ssm_student.py` to verify that the loaded model's vocabulary size matches the tokenizer's vocabulary size used in `src/data/preprocess.py`. **If mismatch > 0, log a critical error and halt to prevent silent alignment failures.** (Edge Case: Architecture Incompatibility)
- [ ] T054 [US1] Integrate signal stability monitoring INTO the training loop of T019/T020. **Monitor log-ratio reward distribution during first steps. If std dev > threshold or mean -> -inf, log warning. DO NOT adjust epsilon (use pinned value from T004).** (Edge Case: Numerical Instability)
- [ ] T055 [US2] Integrate signal stability monitoring INTO the training loop of T029/T030. **Monitor log-ratio reward distribution during the initial steps of the trajectory.. If std dev > threshold or mean -> -inf, log warning. DO NOT adjust epsilon (use pinned value from T004).** (Edge Case: Numerical Instability)
- [ ] T056 [P] [US2] Add a specific check in `src/models/ssm_student.py` to verify that the SSM's output projection layer dimensions align with the reward computation logic. **If dimensions mismatch, raise a `ArchitectureIncompatibilityError` with specific details on the mismatch.** (Edge Case: SSM Architecture Mismatch)
- [ ] T058 [P] [US3] Update `src/core/statistical_tests.py` to explicitly handle the case where the normality assumption fails for the t-test (Shapiro-Wilk test). **If normality fails, automatically switch to the Wilcoxon signed-rank test and log the switch in the report.** (US-3, FR-006)
- [ ] T059 [P] [US3] Ensure the `src/core/results_aggregator.py` explicitly logs the "Family-Wise Error Rate" (FWER) control method used (Bonferroni vs. Holm) in the final JSON report to ensure transparency. (US-3, FR-006)
- [ ] T060 [P] [Polish] Implement dynamic checkpointing in `src/scripts/run_experiment.py` using `time_budget_enforcer` to save checkpoints at intervals that fit within the remaining time budget. **Remove fixed interval logic.** (FR-007)
- [ ] T061 [P] [US1/US2] Add a "dry-run" mode to `src/scripts/run_experiment.py` that loads the models and data, computes one batch of reward, and estimates total time/memory usage **without** starting the full training loop. **This prevents wasting the time budget on misconfigured runs.** (FR-007)
- [ ] T062 [P] [Polish] Update `docs/README.md` to include a "Known Limitations" section explicitly stating the CPU-only constraint, the sample size limitation (n=5 seeds), and the specific MoE/SSM model variants used. (SC-001, SC-003)
- [ ] T063 [P] [Polish] Generate a `data/results/experiment_config_snapshot.json` at the start of every run containing the exact git commit hash, Python version, and library versions used. (SC-001)
- [ ] T064 [P] [US1/US2] Implement `src/data/validate_human_labels.py` to perform the actual cross-reference validation of model outputs against `human_verified_label` from T005.0. **Logic**: If `validation_mode` is 'intrinsic' (from T005.0), skip label validation and log 'Skipped (Intrinsic Mode)'. If 'verified', compare model predictions on held-out set against human labels; calculate accuracy/precision; save to `data/results/human_label_validation.json`. **DEPENDENCY**: T005.0, T021, T031. (SC-006)
- [ ] T065 [P] [Polish] Run `hash_artifacts.py` (T013 logic) to update state file with SHA-256 hashes and timestamp of final artifacts. **DEPENDENCY**: T025, T035, T044.

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US1 and US2.

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
- Different user stories can be worked on in parallel by different team members

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All training must run on CPU-only runner with ≤7GB RAM; use low-bit quantization for MoE (small variant) and int for SSM (Mamba), batch size = 1 with gradient accumulation
- **Critical Constraint**: No synthetic data fallback; failed real data fetch must raise error (never generate synthetic).
- **Critical Constraint**: Streaming real AIME dataset; if full dataset exceeds resources, use well-defined real sample with stated limitations
- **Statistical Note**: Sample size n=5 seeds is used to fit -hour time limit.