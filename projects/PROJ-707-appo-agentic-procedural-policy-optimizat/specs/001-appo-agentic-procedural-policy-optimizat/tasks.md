# Tasks: APPO: Agentic Procedural Policy Optimization

**Input**: Design documents from `/specs/001-appo-branching-score/`
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

- [ ] T001a [P] Create project directories: `code/`, `config/`, `data/raw/`, `data/processed/`, `results/logs/`, `results/stats/`. **Requirement**: Create a `.gitkeep` file in every empty directory to ensure version control tracking. Paths are relative to repository root.
- [ ] T001b [P] Initialize Python 3.11 project with `requirements.txt` (torch-cpu, transformers, datasets, trl, scipy, pandas, llama-cpp-python, pyyaml)
- [ ] T002 [P] Configure linting (ruff) and formatting (black) tools. **Requirement**: Explicitly define rules for unused imports and loop optimization in `ruff.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Implement CPU-safe model loader in `code/models/loader.py` using `llama-cpp-python` (low-bit GGUF quantization) for TinyLlama. **Note**: Explicitly acknowledge deviation from Spec's Llama 8B requirement due to CI RAM constraints.
- [ ] T004 [P] Implement dataset downloader in `code/data/download.py` fetching `Mustafaege/qwen3.5-toolcalling-v2` and `math` via `datasets.load_dataset`. **Requirement**: Explicitly document exclusion of HotpotQA/WebShop due to URL constraints in code comments AND in `README.md` with rationale mapping to Spec requirements.
- [ ] T005 [P] Implement base environment wrapper in `code/benchmarks/tool_calling.py` (CPU-compatible step/reset)
- [ ] T006 [P] Create base schemas in `code/config/`: `base.yaml`, `ablation_grid.yaml`, `seeds.yaml`. **Requirement**: `base.yaml` MUST define specific hyperparameters: `learning_rate: 3e-4`, `batch_size: 4`, `ppo_clip: 0.2`, `sequence_length: 256`, `max_steps: 2000000`.
- [ ] T007 [P] Implement logging infrastructure in `code/training/utils.py` (JSON logger, CSV writer for `results/logs/`)
- [ ] T008a [P] Implement `BranchingScoreConfig` and `TrainingRun` dataclasses in `code/models/branching_score.py`. **Requirement**: Define architecture as TinyLlama, Loss as Binary Cross Entropy, Data as Synthetic Tool-Success.
- [ ] T008b [P] Implement Branching Score calculation logic (entropy × value) in `code/models/branching_score.py`. **Requirement**: Must handle zero entropy gracefully (return 0).
- [ ] T009 [P] Train the FVN proxy model defined in T008a using a synthetic dataset. **Depends on**: T003, T004, T005, T006, T008a. **Output**: Saved model weights in `code/models/fvn_weights/`. **Requirement**: 3 epochs, lr=1e-4, early stopping on val loss.
- [ ] T010 [P] Implement "future-value estimate" (Frozen Value Network) proxy interface in `code/models/branching_score.py`. **Requirement**: Must define a functional, pre-trained small model (TinyLlama-0.5B) trained on a synthetic 'Tool-Success' signal, NOT a constant heuristic, to satisfy Spec FR-001.
- [ ] T011 [P] Implement base threshold calculation logic in `code/training/utils.py` (generic function to compute X% of a given score).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Pilot Execution & Threshold Finalization (Blocking for US1)

**Purpose**: Execute preliminary runs to establish the performance threshold required for US1.

- [ ] T012b [US1] Execute Pilot Runs: Run 3 seeds of the `No-Score` baseline. **Depends on**: T003, T004, T005, T006, T007, T010, T011. **Output**: `results/logs/pilot_seed_0.json`, `results/logs/pilot_seed_1.json`, `results/logs/pilot_seed_2.json`. **Requirement**: Use hyperparameters from `config/base.yaml`.
- [ ] T012c [US1] Aggregate & Verify Threshold. **Depends on**: T012b. **Logic**: Read pilot logs, calculate max pilot score, compute 80% threshold. **Requirement**: Run a 'Stability Verification' (bootstrap check). If the 3-seed CI width > 10% of mean, FAIL and halt. [UNRESOLVED-CLAIM: c_06d34550 — status=not_enough_info] Output `results/threshold.json` with `threshold_value`, `seed_count`, `stability_status`.

**Checkpoint**: Threshold is now defined and verified. US1 can proceed.

---

## Phase 3: User Story 1 - Core Training Loop with Branching Score (Priority: P1) 🎯 MVP

**Goal**: Execute the core training loop for an agentic RL agent on the Tool-Calling benchmark, implementing the Branching Score mechanism (entropy × future-value) and recording steps-to-threshold.

**Independent Test**: Run a single seed on a small subset of the Tool-Calling dataset; verify `results/logs/run_seed_0.json` contains non-zero, varying Branching Scores and a logged `steps_to_threshold`.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `No-Score` (standard PPO) training loop in `code/training/loop.py`. **Requirement**: Ensure identical hyperparameters to Score-Default except the score mechanism. Verify this in code comments. Load config from `config/base.yaml`. **Plan Deviation**: This task implements a reduced number of seeds (Plan) compared to the specification (Spec) due to CI constraints; document this in code.
- [ ] T014 [US1] Implement `Score-Default` training loop (with Branching Score heuristic) in `code/training/loop.py`. **Depends on**: T003, T004, T005, T007, T008a, T008b, T009, T010, T012c. **Config**: ε=0.1, ε′=0.05, b=0.5. **Requirement**: Explicitly load FVN weights from `code/models/fvn_weights/` produced by T009. **Note**: Must be parallelizable with T013.
- [ ] T015 [US1] Unit test for Branching Score calculation (entropy × value) in `code/tests/unit/test_branching_score.py`. **Depends on**: T008a, T008b.
- [ ] T016 [US1] Integration test for single-step training loop in `code/tests/integration/test_training_loop.py`. **Depends on**: T013, T014.
- [ ] T017 [US1] Implement "threshold-not-reached" flagging logic in `code/training/loop.py`. **Requirement**: If the maximum step limit is reached without crossing the threshold, log `threshold_reached: false`, `final_steps` at the maximum limit, and `final_performance: { "metric": "success_rate", "value": <float> }`. **Output Format**: JSON fields must match Spec Edge Cases. `steps_to_threshold` must be logged as `null`.
- [ ] T018 [US1] Create runner script `code/run_training.py` to execute multiple seeds for `No-Score` (3 seeds) and `Score-Default` (3 seeds). **Note**: Acknowledge Plan deviation from Spec seed count; implement logic to report effect sizes (Cohen's d) for reduced power. **Requirement**: Include a 'Statistical Power Check' step; if power < 0.8, force 'Effect Size Only' reporting.
- [ ] T019 [US1] Verify logs: Ensure `steps_to_threshold` and `mean_tool_calls` are recorded per run in `results/logs/`. **Depends on**: T018.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hyperparameter Sensitivity Analysis (Priority: P2)

**Goal**: Execute the `Score-Ablation` variant, systematically varying ε, ε′, and b across the defined grid to measure sensitivity.

**Independent Test**: Run the ablation script with a specific grid point (e.g., ε=0.05, ε′=0.02, b=0.3) and verify the result is distinct in `results/logs/`.

### Implementation for User Story 2

- [ ] T020 [US2] Define `ablation_grid.yaml` with the SPECIFIC hyperparameter grid: ε ∈ {0.05, 0.2}, ε′ ∈ {0.02, 0.1}, b ∈ {0.3, 0.5, 0.7}. **Depends on**: T006.
- [ ] T021 [US2] Implement `AblationRunner` in `code/training/ablation_runner.py` to iterate `ablation_grid.yaml`. **Depends on**: T013, T014, T020. **Seed Count**: 1 seed per variant (12 runs total). **Note**: Explicitly document Plan deviation from Spec (multiple seeds) and the resulting statistical limitations in code. **Requirement**: Include a 'Statistical Power Check' step; if power < 0.8, force 'Effect Size Only' reporting.
- [ ] T022 [US2] Implement result aggregation logic to map (ε, ε′, b) tuples to `steps_to_threshold` in `code/analysis/stats.py`
- [ ] T023 [US2] Create runner script `code/run_ablation.py` to execute the full grid
- [ ] T024 [US2] Verify logs: Ensure all 12 ablation runs produce distinct `results/logs/` files with correct hyperparameters

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Reporting (Priority: P3)

**Goal**: Perform Wilcoxon signed-rank tests across seeds to compare sample efficiency and tool-call efficiency, generating a final report.

**Independent Test**: Provide synthetic seed results; verify `results/stats/report.md` contains correct p-values and CIs.

### Implementation for User Story 3

- [ ] T025 [US3] Implement `WilcoxonTest` wrapper in `code/analysis/stats.py`. **Logic**: Perform Wilcoxon for No-Score vs Score-Default (n=3). [UNRESOLVED-CLAIM: c_453a2231 — status=not_enough_info] **Critical**: If n < 2 (e.g., for Ablation variants), skip Wilcoxon and use Bootstrap CI/effect size calculation only to prevent runtime errors. **Comparison Pairs**: Explicitly code No-Score vs Score-Default and No-Score vs each Ablation variant. **Requirement**: Use `scipy.stats.wilcoxon(..., zero_method='pratt', alternative='two-sided')`.
- [ ] T026 [US3] Implement Bootstrap CI calculation in `code/analysis/stats.py`. **Requirement**: 1000 (2307.16168, https://arxiv.org/abs/2307.16168) iterations, percentile method. Used for n<2 cases.
- [ ] T027 [US3] Implement `ReportGenerator` in `code/analysis/report_gen.py` to aggregate logs and generate `results/report.md`. **Requirement**: Include p-values and confidence intervals for ALL comparisons (No-Score vs Default, No-Score vs each Ablation variant).
- [ ] T028 [US3] Implement tool-call efficiency aggregation in `code/analysis/stats.py`. **Requirement**: Calculate mean tool calls per episode **at threshold crossing point**. For runs where `threshold_reached: false`, calculate mean tool calls at `final_steps`.
- [ ] T029 [US3] Create runner script `code/run_analysis.py` to execute stats and generate report
- [ ] T030 [US3] Verify report: Ensure `results/report.md` lists p-values, CIs, and tool-call metrics for all comparisons
- [ ] T031 [US3] Sanitize Log Data for Statistics. **Depends on**: T017, T019, T024. **Logic**: Read all log files. If `steps_to_threshold` is `null`, replace with `MAX_STEPS_LIMIT + 1` for statistical analysis. **Requirement**: Document this sentinel value in `results/stats/sanitizer_log.md`.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Update `README.md` with usage instructions and benchmark exclusion rationale
- [ ] T033 [P] Update `docs/usage_guide.md` with detailed execution flow
- [ ] T034 [P] Verify Proxy Semantic Equivalence. **Requirement**: Compare Tool-Calling dataset 'agentic' properties against Spec's HotpotQA/WebShop requirements. Document equivalence in `docs/proxy_verification.md`.
- [ ] T035 [P] Verify FVN Signal Correlation. **Requirement**: Correlate synthetic 'Tool-Success' signal with actual benchmark success. Document in `docs/fvn_correlation.md`.
- [ ] T036 [P] Model Scale Verification. **Requirement**: Compare TinyLlama performance against Spec's Llama 8B requirement. Document deviation as 'Feasibility Constraint' in `docs/model_deviation.md`.
- [ ] T037 Code cleanup and refactoring (remove unused imports, optimize loops)
- [ ] T038 [P] Performance optimization (batching, memory management for CPU)
- [ ] T039 [P] Additional unit tests for edge cases (NaN handling, network failures) in `code/tests/unit/`
- [ ] T040 Run `quickstart.md` validation to ensure end-to-end flow works
- [ ] T041 Verify dataset download URLs are valid and accessible (no 404s)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Pilot Execution (Phase 2.5)**: Depends on Foundational - BLOCKS US1
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational + Pilot Execution (Phase 2.5) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational + Pilot Execution (Phase 2.5) - Relies on US1 training loop logic
- **User Story 3 (P3)**: Can start after Foundational + Pilot Execution (Phase 2.5) - Relies on logs from US1 and US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services/logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement BranchingScoreConfig in code/models/branching_score.py"
Task: "Implement TrainingRun dataclass in code/models/branching_score.py"

# Launch all implementation for User Story 1 together (after T008/T009/T010):
Task: "Implement No-Score training loop in code/training/loop.py"
Task: "Implement Score-Default training loop in code/training/loop.py"

# Launch tests AFTER implementation:
Task: "Unit test for Branching Score calculation (Depends on T008a, T008b)"
Task: "Integration test for single-step training loop (Depends on T013, T014)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2.5: Pilot Execution (Critical for Threshold)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add Pilot Execution → Threshold defined
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: Pilot Execution & Threshold (Phase 2.5)
 - Developer B: User Story 1 (Core Loop)
 - Developer C: User Story 2 (Ablation Grid)
 - Developer D: User Story 3 (Stats & Report)
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
- **CPU Constraint**: All tasks must run on multi-core CPU runners.; no GPU or heavy quantization kernels allowed.
- **Data Constraint**: Use `Mustafaege/qwen3.5-toolcalling-v2` and `math` datasets; ensure URLs are verified.
- **Model Constraint**: Use TinyLlama as the executable proxy; do not attempt Llama 8B.
- **Statistical Mitigation**: Due to seed count reductions (Spec > Plan, Spec > Plan), tasks T018 and T021 include explicit fallback logic (effect sizes, bootstrap CIs) to ensure analysis remains valid.
- **FVN Requirement**: The "future-value estimate" must be a functional, pre-trained model (T009), not a constant stub.
- **Threshold Logic**: Threshold is defined by Pilot Execution (T012b) and Finalization (T012c) before US1 main loops begin.