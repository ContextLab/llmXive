# Tasks: llmXive follow-up: extending "Weak-to-Strong Generalization via Direct On-Policy Distillation"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-weak-to-stro/`
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
- [ ] T002 Initialize Python 3.11 project with `transformers`, `accelerate`, `peft`, `scikit-learn`, `scipy`, `pandas`, `numpy`, `torch` dependencies
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `config/defaults.yaml` with hyperparameters, paths, seeds, and memory constraints (batch_size=1, gradient_accumulation steps)
- [ ] T005 [P] Implement `code/data/download_aime.py` to fetch the AIME dataset subset from HuggingFace dataset ID `HuggingFaceH4/aime_2024` with checksum validation. Output to `data/raw/aime_2024.jsonl`.
- [ ] T006 [P] Implement `code/data/preprocess.py` to format prompts and extract ground-truth reasoning steps for AIME subset. **Specifically**: extract the `solution` field to a `ground_truth` field in the output JSONL.
- [ ] T006.1 [P] Implement `code/data/split_aime.py` to split the AIME dataset into `train` and `val` sets using a fixed random seed. Save to `data/processed/aime_train.jsonl` and `data/processed/aime_val.jsonl`. **The `val` set serves as the held-out, human-verified evaluation set to satisfy FR-009 and SC-006.** (FR-009, SC-006)
- [ ] T006.2 [P] Implement `code/data/fetch_human_labels.py` to fetch human-verified correctness labels from a distinct external source (e.g., `HuggingFaceH4/human_eval` or a verified mirror) if `data/processed/aime_val.jsonl` lacks a `human_verified` field. **Must raise error if no distinct source is found.** (FR-009, SC-006)
- [X] T007 Implement `code/models/teacher_loader.py` to load dense Transformer teacher (pre-RL and post-RL) in int8 precision with CPU offloading
- [ ] T008 [P] Implement `code/models/moe_student.py` to load `mistralai/Mixtral-Instruct-v0.1` (MoE, large parameter count with active experts) with 4-bit quantization (`load_in_4bit=True`) and CPU offloading. **Must include pre-load size verification** to confirm model ID, parameter count, and estimated size < 7GB RAM before loading. (FR-002, FR-007)
- [ ] T009.1 [P] Implement `code/models/verify_mamba.py` to verify the existence and compatibility of the `state-spaces/mamba` repository. **Must raise FileNotFoundError if repo is missing or incompatible with int8**. (FR-002, FR-007)
- [ ] T009 [P] Implement `code/models/ssm_student.py` to load a B SSM student model from the `state-spaces/mamba-1.3b-hf` repository in int8 precision with CPU offloading. **Must depend on T009.1**. **Must include pre-load size verification** to confirm model ID, parameter count 1.3B, and size < 7GB RAM before loading. (FR-002, FR-007)
- [ ] T010 [P] Implement `code/core/reward_computation.py` with epsilon-smoothing for log-ratio implicit reward calculation. **Must output `data/processed/reward_signals.jsonl`**. (FR-001)
- [ ] T010.1 [P] Implement `code/core/vocab_aligner.py` to handle vocabulary alignment between Teacher and Student models. **Must mask out-of-vocabulary tokens** before log-ratio calculation to prevent errors. (FR-001, Edge Case 1)
- [ ] T010.2 [P] Implement `code/core/vocab_masking.py` to apply the alignment mask to the reward signal, ensuring only aligned tokens contribute to the loss. (FR-001, Edge Case 1)
- [X] T011 [P] Implement `code/core/trainer.py` with on-policy distillation loop supporting gradient accumulation and memory monitoring
- [ ] T011.5 [P] Implement `code/core/memory_monitor.py` as a standalone utility module with memory profiler and OOM handler to trigger automatic batch size reduction (FR-007). **No shared global state with trainer**. This task provides the monitoring mechanism required by T011.7.
- [ ] T011.6 [P] Implement `code/core/hard_floor_enforcer.py` to enforce the hard limit of batch_size=1 as a fallback if the monitor fails or if RAM usage stabilizes above the hard limit but below OOM. **No shared global state with trainer**. (FR-007)
- [ ] T011.7 [P] Implement `code/core/memory_integration.py` to create the wrapper logic in `trainer.py` that catches OOM exceptions, reduces batch size, and retries. **Must integrate T011.5 and T011.6**. (FR-007)
- [ ] T011.8 [P] Implement `code/core/oom_retry_logic.py` to explicitly define the control flow for catching OOM exceptions, reducing batch size, and retrying the step. **Must integrate T011.5, T011.6, and T011.7**. (FR-007)
- [X] T012 [P] Implement `code/core/evaluator.py` for log-probability improvement calculation and statistical testing
- [X] T013 [P] Implement `code/scripts/hash_artifacts.py` to generate SHA-256 hashes for data and artifacts per Constitution Principle V
- [ ] T014 [P] Implement `code/tests/test_reward.py` unit tests for reward calculation logic and epsilon-smoothing
- [ ] T015 [P] Implement `code/tests/test_memory.py` sanity checks for RAM usage under GB constraint and model size verification
- [ ] T039 [P] [US3] Implement paired t-test/Wilcoxon signed-rank test logic in `code/core/statistical_tests.py` (FR-006)
- [ ] T040 [P] [US3] Implement cluster-robust standard errors calculation (if n>5) or fallback logic (Wilcoxon) in `code/core/statistical_tests.py` (FR-006)
- [ ] T041 [P] [US3] Implement Bonferroni/Holm-Bonferroni multiple-comparison correction for multiple tests (MoE, SSM) (FR-006, SC-004)
- [ ] T042 [P] [US3] Implement significance classification logic in `code/core/statistical_tests.py` (FR-006)
- [ ] T055 [P] Instrument `code/main.py` with runtime timer and log execution time to `data/results/moe_results.json` and `data/results/ssm_results.json` under key `execution_time_ms` to verify SC-003 (6-hour limit). (SC-003)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Cross-Architecture Signal Transfer Validation (MoE) (Priority: P1) 🎯 MVP

**Goal**: Compute implicit reward from Transformer teacher and train MoE student to validate signal transfer

**Independent Test**: Execute distillation loop for MoE student using Transformer-derived implicit reward. Compare log-probability improvement on AIME subset against baseline MoE.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T016 [P] [US1] Contract test for MoE reward signal transfer in `code/tests/contract/test_moe_reward_transfer.py`
- [ ] T017 [P] [US1] Integration test for MoE distillation loop in `code/tests/integration/test_moe_distillation.py`

### Implementation for User Story 1

- [ ] T018 [P] [US1] Implement MoE-specific data loading pipeline in `code/data/moe_loader.py` (depends on T005, T006, T006.1)
- [ ] T019.5 [US1] Implement MoE architecture compatibility check in `code/core/moe_compat_check.py` to verify output dimensions match the reward calculation logic; **MUST halt the process** with a specific error `RuntimeError("MoE Architecture Mismatch")` if mismatch > 0. (Edge Case 3)
- [ ] T019.6 [US1] Implement MoE-specific training loop logic in `code/core/moe_trainer.py` to handle sparse activation and routing updates specific to Mixtral architecture. **Must depend on T019.5**. (FR-003, US-1)
- [ ] T019 [US1] Implement MoE baseline training in `code/core/moe_baseline.py` using only teacher's final distribution (FR-004) (depends on T018, T019.5, T019.6)
- [ ] T020 [US1] Implement MoE Direct-OPD training in `code/core/moe_direct_opd.py` using implicit reward signal from `data/processed/reward_signals.jsonl` (FR-001, FR-003). **Must depend on `data/processed/aime_train.jsonl` (T006.1), T010, T010.1, T010.2, and T019.6**. (depends on T018, T010, T010.1, T010.2, T006.1, T019.6)
- [ ] T021 [US1] Implement MoE evaluation script in `code/scripts/evaluate_moe.py` to compute log-probability improvement on `data/processed/aime_val.jsonl` and `data/processed/human_labels.jsonl` (FR-005, SC-006). **Must depend on `data/processed/aime_val.jsonl` (T006.1) and T006.2**. (depends on T012, T006.1, T006.2)
- [ ] T022 [US1] Add memory constraint enforcement logic to MoE training loop using `code/core/memory_integration.py` (T011.7) and `code/core/oom_retry_logic.py` (T011.8) (FR-007). **Must trigger batch size reduction on OOM event or RAM usage > 90%, and enforce hard floor batch_size=1**. (depends on T011.7, T011.8)
- [ ] T023 [US1] Add epsilon-smoothing verification in MoE reward computation to handle numerical instability (Edge Case 1) (depends on T010)
- [ ] T024 [P] [US1] Run MoE experiment on AIME subset for **500 training steps** with **batch_size=1**, **seed=42**, and **gradient_accumulation_steps=4** and save results to `data/results/moe_results_seed42.json`. (depends on T020, T022, T055)
- [ ] T025 [P] [US1] Run MoE experiment on AIME subset for **500 training steps** with **batch_size=1**, **seed=43**, and **gradient_accumulation_steps=4** and save results to `data/results/moe_results_seed43.json`. (depends on T020, T022, T055)
- [ ] T026 [P] [US1] Run MoE experiment on AIME subset for **500 training steps** with **batch_size=1**, **seed=44**, and **gradient_accumulation_steps=4** and save results to `data/results/moe_results_seed44.json`. (depends on T020, T022, T055)
- [ ] T027 [P] [US1] Run MoE experiment on AIME subset for **500 training steps** with **batch_size=1**, **seed=45**, and **gradient_accumulation_steps=4** and save results to `data/results/moe_results_seed45.json`. (depends on T020, T022, T055)
- [ ] T028 [P] [US1] Run MoE experiment on AIME subset for **500 training steps** with **batch_size=1**, **seed=46**, and **gradient_accumulation_steps=4** and save results to `data/results/moe_results_seed46.json`. (depends on T020, T022, T055)
- [ ] T029 [US1] Validate MoE results against held-out AIME problems (`data/processed/aime_val.jsonl`) and human labels (`data/processed/human_labels.jsonl`) to ensure distinct validation target (FR-009) (depends on T024, T025, T026, T027, T028, T006.1, T006.2)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - State-Space Model (SSM) Signal Transfer Validation (Priority: P2)

**Goal**: Replicate signal transfer experiment using SSM student to verify consistency across non-Transformer families

**Independent Test**: Execute identical distillation loop for SSM student using same Transformer-derived implicit reward. Compare performance gains against SSM baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US2] Contract test for SSM reward signal transfer in `code/tests/contract/test_ssm_reward_transfer.py`
- [ ] T031 [P] [US2] Integration test for SSM distillation loop in `code/tests/integration/test_ssm_distillation.py`

### Implementation for User Story 2

- [ ] T032 [P] [US2] Implement SSM-specific data loading pipeline in `code/data/ssm_loader.py` (depends on T005, T006, T006.1)
- [ ] T033 [US2] Implement SSM baseline training in `code/core/ssm_baseline.py` using only teacher's final distribution (FR-004) (depends on T032)
- [ ] T034 [US2] Implement SSM Direct-OPD training in `code/core/ssm_direct_opd.py` using implicit reward signal from `data/processed/reward_signals.jsonl` (FR-001, FR-003). **Must depend on `data/processed/aime_train.jsonl` (T006.1) and T010.2**. (depends on T032, T010, T010.1, T010.2, T006.1)
- [ ] T035 [US2] Implement SSM evaluation script in `code/scripts/evaluate_ssm.py` to compute log-probability improvement on `data/processed/aime_val.jsonl` and `data/processed/human_labels.jsonl` (FR-005, SC-006). **Must depend on `data/processed/aime_val.jsonl` (T006.1) and T006.2**. (depends on T012, T006.1, T006.2)
- [ ] T036 [US2] Implement SSM architecture compatibility check for output dimensions and log-probability variance; **MUST halt the process** with a specific error `RuntimeError("SSM Architecture Mismatch")` on mismatch (Edge Case 3). (Note: MoE check is in T019.5, this task covers SSM).
- [ ] T037 [US2] Add memory constraint enforcement logic to SSM training loop using `code/core/memory_integration.py` (T011.7) and `code/core/oom_retry_logic.py` (T011.8) (FR-007). **Must trigger batch size reduction on OOM event or RAM usage > 90%, and enforce hard floor batch_size=1 (2507.07101, https://arxiv.org/abs/2507.07101)**. (depends on T011.7, T011.8)
- [ ] T038 [P] [US2] Run SSM experiment on AIME subset for **500 training steps** with **batch_size=1**, **seed=42**, and **gradient_accumulation_steps=4** and save results to `data/results/ssm_results_seed42.json`. (depends on T034, T037, T055)
- [ ] T039 [P] [US2] Run SSM experiment on AIME subset for **500 training steps** with **batch_size=1**, **seed=43**, and **gradient_accumulation_steps=4** and save results to `data/results/ssm_results_seed43.json`. (depends on T034, T037, T055)
- [ ] T040 [P] [US2] Run SSM experiment on AIME subset for **500 training steps** with **batch_size=1**, **seed=44**, and **gradient_accumulation_steps=4** and save results to `data/results/ssm_results_seed44.json`. (depends on T034, T037, T055)
- [ ] T041 [P] [US2] Run SSM experiment on AIME subset for **500 training steps** with **batch_size=1**, **seed=45**, and **gradient_accumulation_steps=4** and save results to `data/results/ssm_results_seed45.json`. (depends on T034, T037, T055)
- [ ] T042 [P] [US2] Run SSM experiment on AIME subset for **500 training steps** with **batch_size=1**, **seed=46**, and **gradient_accumulation_steps=4** and save results to `data/results/ssm_results_seed46.json`. (depends on T034, T037, T055)
- [ ] T043 [US2] Validate SSM results against held-out AIME problems (`data/processed/aime_val.jsonl`) and human labels (`data/processed/human_labels.jsonl`) to ensure distinct validation target (FR-009) (depends on T038, T039, T040, T041, T042, T006.1, T006.2)
- [ ] T044 [US2] Implement comparative summary generator in `code/scripts/generate_summary.py` to aggregate MoE and SSM results (FR-008) (depends on T024-T028, T038-T042)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Multiplicity Correction (Priority: P3)

**Goal**: Perform statistical significance testing with multiple-comparison correction to validate findings

**Independent Test**: Calculate p-values for performance gains, apply Bonferroni/Holm-Bonferroni correction, and classify significance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T045 [P] [US3] Contract test for statistical significance calculation in `code/tests/contract/test_statistical_significance.py`
- [ ] T046 [P] [US3] Integration test for multiple-comparison correction in `code/tests/integration/test_multiple_comparison.py`

### Implementation for User Story 3

- [ ] T047 [US3] Calculate 'performance gain' delta (Direct-OPD metric minus Baseline metric) for MoE and SSM from `data/results/moe_results_seed*.json` and `data/results/ssm_results_seed*.json` (FR-006, SC-001). **Must depend on T024-T028 and T038-T042**. (depends on T024, T025, T026, T027, T028, T038, T039, T040, T041, T042)
- [ ] T048 [US3] Run statistical analysis on MoE and SSM performance gain deltas using Wilcoxon signed-rank test (due to n=5) and Bonferroni correction (FR-006). **Must depend on T047**. (depends on T047, T039, T041, T042)
- [ ] T049 [US3] Calculate Minimum Detectable Effect Size (MDES) for n=5 and update report with power limitations (FR-006, SC-002). (depends on T048)
- [ ] T050 [US3] Generate statistical report with raw and adjusted p-values in `data/results/statistical_report.json` (depends on T048, T049)
- [ ] T051 [US3] Validate statistical report against SC-002 (adjusted p-value < 0.05) and SC-004 (multiple-comparison correction present) (depends on T050)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T052 [P] Update documentation in `docs/` with experiment results and limitations (power analysis, MDES). (depends on T024-T028, T038-T042, T050)
- [ ] T053 [P] Verify execution time logging in `data/results/moe_results_seed*.json` and `data/results/ssm_results_seed*.json` to confirm SC-003 (6-hour limit) is met. (depends on T055, T024-T028, T038-T042)
- [ ] T054 Code cleanup and refactoring for memory efficiency across all training loops
- [ ] T055 Performance optimization for CPU-only execution (gradient accumulation tuning)
- [ ] T056 [P] Additional unit tests for edge cases in `code/tests/unit/`
- [ ] T057 Security hardening for data loading and model checkpoint verification
- [ ] T058 Run `quickstart.md` validation to ensure full pipeline reproducibility
- [ ] T059 Generate final comparative summary text block with explicit statement on signal degradation consistency (FR-008)
- [ ] T060 Run `hash_artifacts.py` to update state file with SHA-256 hashes and timestamp per Constitution Principle V

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US1 and US2 (T024-T028, T038-T042)

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
Task: "Contract test for MoE reward signal transfer in code/tests/contract/test_moe_reward_transfer.py"
Task: "Integration test for MoE distillation loop in code/tests/integration/test_moe_distillation.py"

# Launch all models for User Story 1 together:
Task: "Implement MoE-specific data loading pipeline in code/data/moe_loader.py"
Task: "Implement MoE baseline training in code/core/moe_baseline.py" (Note: T019 depends on T018 completion)
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
 - Developer A: User Story 1 (MoE)
 - Developer B: User Story 2 (SSM)
 - Developer C: User Story 3 (Statistics) - depends on A & B results
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
- **Critical Constraint**: All training must run on CPU-only runner with ≤7GB RAM; use 4-bit quantization for MoE (Mixtral-8x7B) and int8 for SSM (Mamba-1.3B), batch size 1 with gradient accumulation
- **Critical Constraint**: No synthetic data fallback; failed real data fetch must raise error (never generate synthetic)
- **Critical Constraint**: Streaming real AIME dataset; if full dataset exceeds resources, use well-defined real sample with stated limitations
- **Statistical Note**: Sample size n=5 (seeds 42-46) is used to fit 6-hour time limit. [UNRESOLVED-CLAIM: c_0d435ad0 — status=not_enough_info] Wilcoxon test is used due to small n. [UNRESOLVED-CLAIM: c_8cab451d — status=not_enough_info] MDES will be reported to acknowledge power limitations.