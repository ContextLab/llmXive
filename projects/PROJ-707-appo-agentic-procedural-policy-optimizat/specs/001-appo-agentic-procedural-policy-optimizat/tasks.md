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

- [ ] T001a [P] Create project directories: `code/`, `config/`, `data/raw/`, `data/processed/`, `results/logs/`, `results/stats/`
- [ ] T001b [P] Initialize Python 3.11 project with `requirements.txt` (torch-cpu, transformers, datasets, trl, scipy, pandas, llama-cpp-python, pyyaml)
- [ ] T002 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Implement CPU-safe model loader in `code/models/loader.py` using `llama-cpp-python` (low-bit GGUF quantization) for TinyLlama. **Note**: Explicitly acknowledge deviation from Spec's Llama 8B requirement due to CI RAM constraints.
- [ ] T004 [P] Implement dataset downloader in `code/data/download.py` fetching `Mustafaege/qwen3-toolcalling` and `math` via `datasets.load_dataset`. **Requirement**: Explicitly document exclusion of HotpotQA/WebShop due to URL constraints in code comments AND in `README.md` with rationale mapping to Spec requirements.
- [ ] T005 [P] Implement base environment wrapper in `code/benchmarks/tool_calling.py` (CPU-compatible step/reset)
- [ ] T006 [P] Create base schemas in `code/config/`: `base.yaml`, `ablation_grid.yaml`, `seeds.yaml`
- [ ] T007 [P] Implement logging infrastructure in `code/training/utils.py` (JSON logger, CSV writer for `results/logs/`)
- [ ] T008 [P] Implement "future-value estimate" (Frozen Value Network) proxy interface in `code/models/branching_score.py`. **Requirement**: Must define a functional, pre-trained small model (TinyLlama-0.5B) trained on a synthetic 'Tool-Success' signal, NOT a constant heuristic, to satisfy Spec FR-001.
- [ ] T009 [P] Train the FVN proxy model defined in T008 using a synthetic dataset. **Depends on**: T004, T005. **Output**: Saved model weights in `code/models/fvn_weights/`.
- [ ] T010 [P] Implement `BranchingScoreConfig` and `TrainingRun` dataclasses in `code/models/branching_score.py`
- [ ] T011 [P] Implement base threshold calculation logic in `code/training/utils.py` (generic function to compute X% of a given score).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Training Loop with Branching Score (Priority: P1) 🎯 MVP

**Goal**: Execute the core training loop for an agentic RL agent on the Tool-Calling benchmark, implementing the Branching Score mechanism (entropy × future-value) and recording steps-to-threshold.

**Independent Test**: Run a single seed on a small subset of the Tool-Calling dataset; verify `results/logs/run_seed_0.json` contains non-zero, varying Branching Scores and a logged `steps_to_threshold`.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `No-Score` (standard PPO) training loop in `code/training/loop.py`. **Requirement**: Ensure identical hyperparameters to Score-Default except the score mechanism. Verify this in code comments. **Plan Deviation**: This task implements a reduced number of seeds (Plan) compared to the specification (Spec) due to CI constraints; document this in code.
- [ ] T013 [US1] Implement `Score-Default` training loop (with Branching Score heuristic) in `code/training/loop.py`. **Depends on**: T003, T004, T005, T007, T008, T009, T010. **Config**: ε=0.1, ε′=0.05, b=0.5. **Requirement**: Explicitly load FVN weights from `code/models/fvn_weights/` produced by T009. **Note**: Must be parallelizable with T012.
- [ ] T014 [US1] Unit test for Branching Score calculation (entropy × value) in `code/tests/unit/test_branching_score.py`. **Depends on**: T009, T013.
- [ ] T015 [US1] Integration test for single-step training loop in `code/tests/integration/test_training_loop.py`. **Depends on**: T012, T013.
- [ ] T016 [US1] Implement "threshold-not-reached" flagging logic in `code/training/loop.py`. **Requirement**: If the maximum step limit is reached without crossing the threshold, log `threshold_reached: false`, `final_steps` at the maximum limit, `final_performance`, and `mean_tool_calls`. **Output Format**: JSON fields must match Spec Edge Cases.
- [ ] T017 [US1] Create runner script `code/run_training.py` to execute multiple seeds for `No-Score` (3 seeds) and `Score-Default` (3 seeds). **Note**: Acknowledge Plan deviation from Spec seed count; implement logic to report effect sizes (Cohen's d) for reduced power.
- [ ] T018 [US1] Verify logs: Ensure `steps_to_threshold` and `mean_tool_calls` are recorded per run in `results/logs/`. **Depends on**: T017.
- [ ] T010b [US1] Implement 'pilot score aggregation' logic in `code/training/utils.py` to compute the threshold specifically from the Plan's No-Score seeds. **Depends on**: T012, T017. **Note**: This task must run AFTER pilot runs are complete to aggregate their results.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hyperparameter Sensitivity Analysis (Priority: P2)

**Goal**: Execute the `Score-Ablation` variant, systematically varying ε, ε′, and b across the defined grid to measure sensitivity.

**Independent Test**: Run the ablation script with a specific grid point (e.g., ε=0.05, ε′=0.02, b=0.3) and verify the result is distinct in `results/logs/`.

### Implementation for User Story 2

- [ ] T019 [US2] Define `ablation_grid.yaml` with the SPECIFIC hyperparameter grid: ε ∈ {, 0.2}, ε′ ∈ {0.02, 0.1}, b ∈ {0.3, 0.5, 0.7}. **Depends on**: T006.
- [ ] T020 [US2] Implement `AblationRunner` in `code/training/ablation_runner.py` to iterate `ablation_grid.yaml`. **Depends on**: T012, T013, T019. **Seed Count**: 1 seed per variant (12 runs total). **Note**: Explicitly document Plan deviation from Spec (3 seeds) and the resulting statistical limitations in code.
- [ ] T021 [US2] Implement result aggregation logic to map (ε, ε′, b) tuples to `steps_to_threshold` in `code/analysis/stats.py`
- [ ] T022 [US2] Create runner script `code/run_ablation.py` to execute the full grid
- [ ] T023 [US2] Verify logs: Ensure all 12 ablation runs produce distinct `results/logs/` files with correct hyperparameters

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Reporting (Priority: P3)

**Goal**: Perform Wilcoxon signed-rank tests across seeds to compare sample efficiency and tool-call efficiency, generating a final report.

**Independent Test**: Provide synthetic seed results; verify `results/stats/report.md` contains correct p-values and CIs.

### Implementation for User Story 3

- [ ] T024 [US3] Implement `WilcoxonTest` wrapper in `code/analysis/stats.py`. **Logic**: Perform Wilcoxon for No-Score vs Score-Default (n=3). **Critical**: If n < 2 (e.g., for Ablation variants), skip Wilcoxon and use Bootstrap CI/effect size calculation only to prevent runtime errors. **Comparison Pairs**: Explicitly code No-Score vs Score-Default and No-Score vs each Ablation variant.
- [ ] T025 [US3] Implement Confidence Interval calculation for median difference in `code/analysis/stats.py`
- [ ] T026 [US3] Implement `ReportGenerator` in `code/analysis/report_gen.py` to aggregate logs and generate `results/report.md`. **Requirement**: Include p-values and confidence intervals for ALL comparisons (No-Score vs Default, No-Score vs each Ablation variant).
- [ ] T027 [US3] Implement tool-call efficiency aggregation in `code/analysis/stats.py`. **Requirement**: Calculate mean tool calls per episode **at threshold crossing point**. For runs where `threshold_reached: false`, calculate mean tool calls at `final_steps`.
- [ ] T028 [US3] Create runner script `code/run_analysis.py` to execute stats and generate report
- [ ] T029 [US3] Verify report: Ensure `results/report.md` lists p-values, CIs, and tool-call metrics for all comparisons

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Update `README.md` with usage instructions and benchmark exclusion rationale
- [ ] T031 [P] Update `docs/usage_guide.md` with detailed execution flow
- [ ] T032 Code cleanup and refactoring (remove unused imports, optimize loops)
- [ ] T033 [P] Performance optimization (batching, memory management for CPU)
- [ ] T034 [P] Additional unit tests for edge cases (NaN handling, network failures) in `code/tests/unit/`
- [ ] T035 Run `quickstart.md` validation to ensure end-to-end flow works
- [ ] T036 Verify dataset download URLs are valid and accessible (no 404s)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Relies on US1 training loop logic
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Relies on logs from US1 and US2

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
Task: "Unit test for Branching Score calculation (Depends on T009, T013)"
Task: "Integration test for single-step training loop (Depends on T012, T013)"
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
   - Developer A: User Story 1 (Core Loop)
   - Developer B: User Story 2 (Ablation Grid)
   - Developer C: User Story 3 (Stats & Report)
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
- **Statistical Mitigation**: Due to seed count reductions (Spec 5→Plan 3, Spec 3→Plan 1), tasks T017 and T020 include explicit fallback logic (effect sizes, bootstrap CIs) to ensure analysis remains valid.
- **FVN Requirement**: The "future-value estimate" must be a functional, pre-trained model (T009), not a constant stub.