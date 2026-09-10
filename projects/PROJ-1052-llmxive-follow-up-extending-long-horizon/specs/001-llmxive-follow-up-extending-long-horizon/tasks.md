# Tasks: llmXive Follow-up: Reward Fidelity vs. Error Recovery Density

**Input**: Design documents from `/specs/001-reward-fidelity-error-recovery/`
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

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-1052-llmxive-follow-up-extending-long-horizon/` by creating directories: `data/raw`, `data/processed`, `code`, `code/utils`, `code/tests`, `results`, `artifacts`, `specs/001-reward-fidelity-error-recovery/contracts`. Verify all directories exist via `ls`.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` containing pinned versions: `datasets==2.14.0`, `llama-cpp-python==0.2.0`, `scikit-learn==1.3.0`, `scipy==1.11.0`, `pandas==2.0.0`, `pyyaml==6.0.1`, `pytest==7.4.0`, `statsmodels==0.14.0`. Verify installation with `pip install -r requirements.txt --dry-run`.
- [X] T003 Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections. Verify setup by running `ruff check. --output-format=github` and `black --check.`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/download.py` to fetch the `lmz/agentbench` dataset (AgentBench) via `datasets.load_dataset` with cryptographic hash validation to `data/raw/`. Verify the checksum matches the expected value from the dataset documentation.
- [X] T004a Implement `code/download.py` validation logic to verify required variables (observations, actions, rewards) exist in the downloaded dataset. If missing, raise `ERR_MISSING_VAR` and log the missing variable name. Document the substitution of 'Long-Horizon-Terminal-Bench' with 'AgentBench' in the log.
- [ ] T005 Create data schema contracts in `specs/001-reward-fidelity-error-recovery/contracts/execution_log.schema.yaml` and `analysis_result.schema.yaml`
- [X] T006 Implement `code/utils/state_diff.py` for FR-007: Recovery segment identification using **cosine similarity of sentence embeddings** (proxy for attention-weighted overlap) to avoid circularity per Plan constraints. *Note: This is a staged deviation from FR-007's literal 'attention-weighted' requirement.*
- [X] T007 Implement `code/utils/pruning.py` for FR-003/FR-004: Context manager with coarsening logic (dense -> binary/3-bin) and pruning execution
- [X] T008 Implement `code/agent_runner.py`: Lightweight agent wrapper (llama-cpp-python) with CPU-only low-bit quantization fallback (Llama-3-8B -> Qwen-1.5-1.8B). Log the specific model used to quantify impact of the swap on ground truth.
- [ ] T009 Setup environment configuration and logging infrastructure by creating `config.yaml` and a logging handler that captures `reward_fidelity_level` and `recovery_segment_id`. Verify `logs/run.log` contains a line with `reward_fidelity_level=dense`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Execution & Ground Truth Establishment (Priority: P1) 🎯 MVP

**Goal**: Establish baseline success rates and identify "recovery-critical" context segments using full context and dense rewards.

**Independent Test**: Run all tasks with full context; verify logs contain exact recovery segments and baseline success rate.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [US1] Contract test `test_execution_log_schema_validates_task_id_field` in `code/tests/test_agent_runner.py` (Depends on: T012, T014) <!-- ATOMIZE: requested --> <!-- FAILED: unspecified -->
- [ ] T011 [US1] Integration test `test_baseline_execution_flow_logs_recovery_segments` in `code/tests/test_baseline.py` (Depends on: T012, T014) <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [X] T012 [US1] Implement baseline execution runner in `code/agent_runner.py` (full context, dense rewards) for all tasks in the benchmark suite.
- [X] T012a [US1] Implement task selection logic in `code/download.py` to filter the error-prone tasks. If the hourly/size constraint is hit, implement and log the sampling strategy (e.g., `itertools.islice` first N rows) as per Edge Cases.
- [ ] T013 [US1] Implement error injection mechanism in `code/inject_errors.py` by modifying the `observations` field in the trajectory to introduce a state mismatch. Output artifact: `data/processed/injected_trajectories.jsonl`.
- [ ] T014 [US1] Implement recovery segment tagging logic in `code/utils/state_diff.py` using **cosine similarity of sentence embeddings** (proxy for attention-weighted overlap) to identify segments contributing >5% to state change (FR-007). *Note: This is a staged deviation from FR-007's literal 'attention-weighted' requirement.*
- [ ] T015 [US1] Create `data/processed/baseline_execution_logs.csv` containing task ID, success status, and identified recovery segments
- [ ] T016 [US1] Add logic to exclude "unrecoverable errors" (baseline failures) from recovery success metric calculation but log them separately

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Reward Fidelity Manipulation & Pruning Execution (Priority: P2)

**Goal**: Execute agent with manipulated reward fidelities and dynamic pruning to test the hypothesis that low-fidelity signals remove critical context.

**Independent Test**: Run tasks with binary rewards; verify pruning removes segments identified as "recovery-critical" in US1.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test `test_pruning_logic_validates_fidelity_level` in `code/tests/test_pruning.py`
- [ ] T019 [P] [US2] Integration test `test_fidelity_manipulation_removes_recovery_segments` in `code/tests/test_fidelity.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement reward coarsening logic in `code/utils/pruning.py` (Dense -> Binary, 3-Bin)
- [ ] T021 [US2] Implement dynamic pruning executor in `code/agent_runner.py` that removes segments based *only* on manipulated reward signals
- [ ] T022 [US2] Implement "Random Pruning" control condition in `code/agent_runner.py` (FR-009) to isolate fidelity effects
- [ ] T023 [US2] Execute agent on all tasks under Binary and multi-bin fidelity conditions.
- [ ] T024 [US2] Generate `data/processed/pruned_execution_logs.csv` with token consumption, discarded segments, and success rates per fidelity level
- [ ] T025 [US2] Verify and log specific removal of "recovery-critical" segments identified in US1 (Depends on T015) during low-fidelity runs.
- [ ] T034 [US2] Execute "Random Pruning" control condition on all tasks (independent of reward signals) to isolate fidelity effects

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Identification & Statistical Analysis (Priority: P3)

**Goal**: Analyze collected data to identify the non-linear inflection point where reward fidelity loss degrades recovery capability.

**Independent Test**: Run analysis script; verify output includes inflection point, logistic regression coefficients, and corrected p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T036 [P] [US3] Contract test `test_analysis_result_schema_validates_inflection_point` in `code/tests/test_analysis.py`
- [ ] T037 [P] [US3] Integration test `test_statistical_pipeline_identifies_threshold` in `code/tests/test_statistical_pipeline.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/analysis.py` for logistic regression modeling of success probability vs. fidelity and density
- [ ] T027 [US3] Implement inflection point detection logic using `scipy.optimize.curve_fit` (logistic function) and `numpy.gradient` to find max curvature. If fit fails (flat curve), fallback to 95% CI non-overlap check AND verify the drop exceeds a defined delta threshold (e.g., 10%) as per SC-002.
- [ ] T028 [US3] Implement multiple-comparison correction (Bonferroni or Benjamini-Hochberg) for p-values per FR-006
- [ ] T029 [US3] Implement fallback Cochran-Armitage trend test logic: First, calculate statistical power using `statsmodels.stats.power.tt_solve_power` (runtime check). If power < 0.8, switch to Cochran-Armitage and append a warning to `results/statistical_analysis_report.md` with the calculated EPV value.
- [ ] T030 [US3] Generate `results/statistical_analysis_report.md` containing inflection point, corrected p-values, and token savings metrics
- [ ] T031 [US3] Add error handling for missing variables (ERR_MISSING_VAR) as per Edge Cases

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T032 [P] Update `README.md` with execution instructions and dataset verification steps
- [ ] T033 Code cleanup and refactoring for memory efficiency using `memory_profiler` to reduce peak memory usage. Verify by running `memory_profiler` and recording output.
- [ ] T037 [P] Run full test suite and verify all contract tests pass
- [ ] T038 [P] Run quickstart.md validation to ensure reproducibility on a fresh runner

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data (recovery segments) for verification
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 execution logs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
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
Task: "Contract test for execution log schema in code/tests/test_agent_runner.py"
Task: "Integration test for baseline execution flow in code/tests/test_baseline.py"

# Launch all utilities for User Story 1 together:
Task: "Implement recovery segment tagging logic in code/utils/state_diff.py"
Task: "Implement baseline execution runner in code/agent_runner.py"
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
- **Compute Constraint**: All agent execution must be CPU-only (low-bit quantization). If 8B model fails, fallback to 1.8B. No GPU offloads.
- **Data Constraint**: Use real AgentBench dataset via HF. No synthetic data. If dataset fetch fails, raise error (no silent fallback).
- **Spec Conflict Note**: FR-007 requires 'attention-weighted token overlap' but Plan forbids model attention. Tasks T006/T014 implement 'cosine similarity of sentence embeddings' as a proxy. Spec.md must be amended to align.
- **Dataset Substitution Note**: FR-001 requires 'Long-Horizon-Terminal-Bench' which does not exist. Tasks implement 'AgentBench' (lmz/agentbench) with substitution logging. Spec.md must be amended.