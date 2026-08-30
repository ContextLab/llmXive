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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-1062-llmxive-follow-up-extending-weak-to-stro/code/`)
- [ ] T002 Initialize Python 3.11 project with `transformers`, `scikit-learn`, `scipy`, `pandas`, `numpy`, `torch`, `bitsandbytes` dependencies. **Must explicitly install `torch` with `--index-url https://download.pytorch.org/whl/cpu` and pin version to enforce CPU-only build and prevent GPU wheel fallback.** (Arch-Constraint / Constitution Principle VII)
- [ ] T003 [P] Configure linting (ruff) and formatting (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `config/defaults.yaml` with hyperparameters, paths, seeds, and memory constraints (batch_size=1, gradient_accumulation steps)
- [X] T005.0 [P] Implement `code/data/download_aime_verified.py` to **first fetch** `HuggingFaceH4/aime_2024` from the HuggingFace Hub. **Check if the dataset contains a `human_verified_label` field.** If the field exists, output to `data/raw/aime_verified.jsonl`. **If the field is missing, immediately raise a `FileNotFoundError` with a message directing the user to verify the dataset source against the spec's Assumption about measurement validity (SC-006).** (SC-006, FR-009)
- [X] T006 Implement `code/data/preprocess.py` to format prompts and extract ground-truth reasoning steps for AIME subset
- [X] T006.1a [P] Implement `code/data/split_aime.py` to split the AIME dataset into training and held-out sets using a **stratified sampling strategy** based on problem difficulty/reasoning type, ensuring diverse representation in both splits. Save to `data/processed/aime_train.jsonl` and `data/processed/aime_holdout.jsonl`. (FR-009)
- [X] T006.1b [P] Implement validation logic in `code/data/validate_split.py` to confirm the held-out set contains no problems with overlapping reasoning steps to the training set, preventing data leakage in the small N=200 sample. (FR-009)
- [X] T007 Implement `code/models/teacher_loader.py` to load dense Transformer teacher (pre-RL and post-RL) in int8 precision with CPU offloading
- [X] T008 [P] Implement `code/models/moe_student.py` to load a verified **A medium-scale Dense Proxy student model

The research question, method, and references remain unchanged as per the planning document requirements. [UNRESOLVED-CLAIM: c_a9cf744f — status=not_enough_info]** (`HuggingFaceTB/SmolLM-135M`) from a canonical HuggingFace source. **Rationale**: A true 1B MoE model (e.g., Mixtral-8x7B) exceeds the 7GB RAM constraint even with int8 quantization. [UNRESOLVED-CLAIM: c_54b50feb — status=not_enough_info] This task uses a dense proxy to validate the *distillation methodology* within hardware limits. **Must include pre-load size verification** to confirm model ID, parameter count ~135M, and size < 7GB RAM before loading. **If the model exceeds 7GB RAM, the task must raise `ValueError` (do not fallback to larger models or synthetic models).** (FR-002, US1 - Modified for Feasibility)
- [X] T009 [P] Implement `code/models/ssm_student.py` to load the `mamba` SSM student model in low-precision format with CPU offloading. **Must include pre-load size verification.** If loading fails due to memory, raise `MemoryError` (no fallback to smaller synthetic models). (FR-002, US2)
- [X] T010 [P] Implement `code/core/reward_computation.py` with epsilon-smoothing (a small positive constant) for log-ratio implicit reward calculation
- [X] T011.5 [P] Implement `code/core/memory_monitor.py` as a standalone utility module with memory profiler and OOM handler to simulate out-of-memory conditions for testing. **Uses internal constants or config, does not depend on T010.**
- [X] T011.6 [P] Implement `code/core/hard_floor_enforcer.py` to enforce the hard limit of batch_size=1 as a fallback if the monitor fails or RAM usage exceeds limits. **Depends on T011.5 for monitoring data. Implements the split logic of `memory_guard.py` as per plan.md.**
- [X] T011.7 [P] Implement `code/tests/unit/test_fallback_logic.py` to **validate the fallback logic**: simulate a scenario where the memory monitor fails to detect OOM and verify that `hard_floor_enforcer` still triggers correctly. (FR-007)
- [X] T011.8 [P] Implement `code/core/time_budget_enforcer.py`: Calculate dynamic step count based on average training time per step and remaining time. Enforce a time limit with automatic termination and partial result saving.
- [X] T012 [P] Implement `code/core/evaluator.py` for log-probability improvement calculation and statistical testing
- [X] T013 [P] Implement `code/scripts/hash_artifacts.py` to generate SHA-256 hashes for data and artifacts per Constitution Principle V
- [X] T014 [P] Implement `code/tests/test_reward.py` unit tests for reward calculation logic and epsilon-smoothing
- [X] T015 [P] Implement `code/tests/test_memory.py` sanity checks for RAM usage under GB constraint and model size verification
- [X] T014.6 [US1] Implement `code/tests/test_evaluator_integration.py` to **integrate** independent human-verified labels (from T005.0) into log-probability metric calculation in `code/core/evaluator.py`. **Must use the `human_verified_label` field from `data/raw/aime_2024_verified.jsonl`, not derived labels.** (SC-006, FR-009)
- [X] T039 [P] [US3] Implement paired t-test/Wilcoxon signed-rank test logic in `code/core/statistical_tests.py` (FR-006)
- [X] T040.5 [P] [US3] Implement cluster-robust standard errors, multiple-comparison correction (Bonferroni/Holm), and significance classification logic in `code/core/statistical_tests.py` (FR-006, SC-004). **Consolidates T040, T041, T042.**
- [X] T042.5 [Foundational] Implement `code/core/results_aggregator.py` to calculate 'performance gain' delta (Direct-OPD metric minus Baseline metric) for MoE and SSM from `data/results/moe_results.json` and `data/results/ssm_results.json`. **This task aggregates results from US1 and US2 to prepare data for US3 statistical analysis.** (FR-006, SC-001). **Must depend on T024 and T034. This task is NOT parallel; it blocks US3 until US1/US2 results are available.**
- [X] T043 [US3] Run statistical analysis on MoE and SSM performance gain deltas using logic from T039, **T040.5** (FR-006). **Must depend on T042.5 and T040.5**.
- [X] T044 [US3] Generate statistical report with raw and adjusted p-values in `data/results/statistical_report.json` (depends on T043)
- [X] T045 [US3] Validate statistical report against SC-002 (adjusted p-value < 0.05) and SC-004 (multiple-comparison correction present) using standard statistical practice for small-N designs (FR-006). **Must not use 'Liang & Zeger (1986)' as primary reference for this design.**
- [X] T046 [P] Update documentation in `docs/` with experiment results and limitations (power analysis, MDES). (depends on T024, T034)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Cross-Architecture Signal Transfer Validation (Priority: P1) 🎯 MVP

**Goal**: Compute implicit reward from Transformer teacher and train MoE student to validate signal transfer across architectural families.

**Independent Test**: Execute distillation loop for MoE student using Transformer-derived implicit reward. Compare log-probability improvement on AIME subset against baseline MoE model.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US1] Contract test for MoE reward signal transfer in `code/tests/contract/test_moe_reward_transfer.py`
- [ ] T017 [P] [US1] Integration test for MoE distillation loop in `code/tests/integration/test_moe_distillation.py`

### Implementation for User Story 1

- [ ] T018 [P] [US1] Implement MoE-specific data loading pipeline in `code/data/moe_loader.py` (depends on T005, T006, T006.1a, T006.1b)
- [ ] T019 [US1] Implement MoE baseline training in `code/core/moe_baseline.py` using only teacher's final distribution (FR-004) (depends on T018)
- [ ] T020 [US1] Implement MoE Direct-OPD training in `code/core/moe_direct_opd.py` using implicit reward signal (FR-001, FR-003) (depends on T018, T010, **T011.5, T011.6**). **Must invoke `hard_floor_enforcer.enforce()` within the training loop's try/except OOM block and pre-step RAM check**.
- [ ] T021 [US1] Implement MoE evaluation script in `code/scripts/evaluate_moe.py` to compute log-probability improvement validated against human labels (FR-005, SC-006) (depends on T014.6, **T020**)
- [ ] T022 [US1] Add memory constraint enforcement logic to MoE training loop using `code/core/memory_monitor.py` and `code/core/hard_floor_enforcer.py` (FR-007). **Must trigger batch size reduction on OOM event or RAM usage > 90%, and enforce hard floor batch_size=1**. (depends on T011.5, T011.6, T011.7)
- [ ] T023 [US1] Add epsilon-smoothing verification in MoE reward computation to handle numerical instability (Edge Case 1) (depends on T010)
- [ ] T024 [US1] Run MoE experiment on AIME subset for **dynamic training steps** (calculated by `time_budget_enforcer` to fit within 6 hours) with **batch_size=1**, **seed=42**, and **gradient_accumulation_steps=4** and save results to `data/results/moe_results.json`. **Must implement a hard timeout using signal.alarm or time.time() loop; if the specified time limit is reached, save partial results to `data/results/moe_results_partial.json` and exit gracefully**. (depends on T020, T022, **T011.8**)
- [ ] T025 [US1] Validate MoE results against held-out AIME problems (`data/processed/aime_holdout.jsonl`) to ensure distinct validation target (FR-009) (depends on T024, T006.1b)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - State-Space Model (SSM) Signal Transfer Validation (Priority: P2)

**Goal**: Replicate signal transfer experiment using SSM student to verify consistency across non-Transformer families

**Independent Test**: Execute identical distillation loop for SSM student using the same Transformer-derived implicit reward. Compare performance gains against SSM baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US2] Contract test for SSM reward signal transfer in `code/tests/contract/test_ssm_reward_transfer.py`
- [ ] T031 [P] [US2] Integration test for SSM distillation loop in `code/tests/integration/test_ssm_distillation.py`

### Implementation for User Story 2

- [ ] T028 [P] [US2] Implement SSM-specific data loading pipeline in `code/data/ssm_loader.py` (depends on T005, T006, T006.1a, T006.1b)
- [ ] T029 [US2] Implement SSM baseline training in `code/core/ssm_baseline.py` using only teacher's final distribution (FR-004) (depends on T028)
- [ ] T030 [US2] Implement SSM Direct-OPD training in `code/core/ssm_direct_opd.py` using implicit reward signal (FR-001, FR-003) (depends on T028, T010, **T011.5, T011.6**). **Must invoke `hard_floor_enforcer.enforce()` within the training loop's try/except OOM block and pre-step RAM check**.
- [ ] T031 [US2] Implement SSM evaluation script in `code/scripts/evaluate_ssm.py` to compute log-probability improvement validated against human labels (FR-005, SC-006) (depends on T014.6)
- [ ] T032 [US2] Implement SSM architecture compatibility check for output dimensions and log-probability variance; **MUST halt the process** with a RuntimeError indicating the specific architecture mismatch if **output dimension mismatch > 0** (Edge Case 3). **Removed arbitrary variance check.**
- [ ] T033 [US2] Add memory constraint enforcement logic to SSM training loop using `code/core/memory_monitor.py` and `code/core/hard_floor_enforcer.py` (FR-007). **Must trigger batch size reduction on OOM event or RAM usage > 90%, and enforce hard floor batch_size=1 (2507.07101, https://arxiv.org/abs/2507.07101)**. (depends on T011.5, T011.6, T011.7)
- [ ] T034 [US2] Run SSM experiment on AIME subset for **dynamic training steps** (calculated by `time_budget_enforcer` to fit within 6 hours) with **batch_size=1**, **seed=42**, and **gradient_accumulation_steps=4** and save results to `data/results/ssm_results.json`. **Must implement a hard timeout using signal.alarm or time.time() loop; if the time limit is reached, save partial results to `data/results/ssm_results_partial.json` and exit gracefully**. (depends on T030, T033, **T011.8**)
- [ ] T035 [US2] Validate SSM results against held-out AIME problems (`data/processed/aime_holdout.jsonl`) to ensure distinct validation target (FR-009) (depends on T034, T006.1b)
- [ ] T036 [US2] Implement comparative summary generator in `code/scripts/generate_summary.py` to aggregate MoE and SSM results (FR-008) (depends on T024, T034)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Multiplicity Correction (Priority: P3)

**Goal**: Perform statistical significance testing with multiple-comparison correction to validate findings

**Independent Test**: Calculate p-values for performance gains, apply Bonferroni/Holm-Bonferroni correction, and classify significance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T045 [P] [US3] Contract test for statistical significance calculation in `code/tests/contract/test_statistical_significance.py`
- [ ] T046 [P] [US3] Integration test for multiple-comparison correction in `code/tests/integration/test_multiple_comparison.py`

### Implementation for User Story 3

- [X] T043 [US3] Run statistical analysis on MoE and SSM performance gain deltas using logic from T039, **T040.5** (FR-006). **Must depend on T042.5 and T040.5**.
- [X] T044 [US3] Generate statistical report with raw and adjusted p-values in `data/results/statistical_report.json` (depends on T043)
- [X] T045 [US3] Validate statistical report against SC-002 (adjusted p-value < 0.05) and SC-004 (multiple-comparison correction present) using standard statistical practice for small-N designs (FR-006). **Must not use 'Liang & Zeger (1986)' as primary reference for this design.**
- [X] T046 [P] Update documentation in `docs/` with experiment results and limitations (power analysis, MDES). (depends on T024, T034)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T047.1 [P] Refactor `code/core/moe_direct_opd.py` for memory efficiency (target: **ensure peak RAM usage ≤7GB by implementing chunked processing**). (FR-007)
- [ ] T047.2 [P] Refactor `code/core/ssm_direct_opd.py` for memory efficiency (target: **ensure peak RAM usage ≤7GB by implementing chunked processing**). (FR-007)
- [ ] T048 Performance optimization for CPU-only execution (gradient accumulation tuning)
- [ ] T049.1 [P] Add unit test for epsilon-smoothing edge case in `code/core/reward_computation.py` (Edge Case 1)
- [ ] T049.2 [P] Add unit test for OOM handling in `code/core/memory_monitor.py` (Edge Case 2)
- [ ] T049.3 [P] Add unit test for time-out handling in `code/core/time_budget_enforcer.py` (Edge Case 4)
- [ ] T050 Security hardening for data loading and model checkpoint verification
- [ ] T051 Run `quickstart.md` validation to ensure full pipeline reproducibility
- [ ] T054 Run `hash_artifacts.py` to update state file with SHA-256 hashes and timestamp per Constitution Principle V

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US1 and US2. **Specifically, T042.5 (Data Aggregation) must complete first, blocking the start of T043.**

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

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All training must run on CPU-only runner with ≤7GB RAM; use low-bit quantization for MoE (small variant) and int for SSM (MambaB), batch size 1 with gradient accumulation
- **Critical Constraint**: No synthetic data fallback; failed real data fetch must raise error (never generate synthetic). **T005.0 will raise `FileNotFoundError` if `human_verified_label` is missing; no heuristic fallback is permitted.**
- **Critical Constraint**: Streaming real AIME dataset; if full dataset exceeds resources, use well-defined real sample with stated limitations
- **Statistical Note**: Sample size n=5 (seeds in a moderate range) is used to fit -hour time limit. [UNRESOLVED-CLAIM: c_d6c2ae09 — status=not_enough_info] Wilcoxon test is used due to small n. [UNRESOLVED-CLAIM: c_58ff0632 — status=not_enough_info] MDES will be reported to acknowledge power limitations. [UNRESOLVED-CLAIM: c_2833946c — status=not_enough_info] 