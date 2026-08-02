# Tasks: llmXive follow-up: extending "SpatialClaw: Rethinking Action Interface for Agentic Spatial Reasoning"

**Input**: Design documents from `/specs/001-llmxive-spatialclaw-restriction/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per plan.md structure)
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

- [ ] T001 Create project structure per implementation plan (code/, data/, results/, tests/)
- [ ] T002 Initialize Python 3.11 project with requirements.txt (shapely, numpy, scipy, pandas, pytest, statsmodels, datasets, huggingface_hub)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes data streaming and verification logic.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/kernel/blockers.py`: Define `RestrictedActionError` and the whitelist/blacklist of libraries (allow: shapely, numpy; block: trimesh, pytorch3d, open3d)
- [ ] T005 Implement `code/kernel/restricted_kernel.py`: Intercepts imports and function calls to enforce the 2D constraint policy (FR-001)
- [ ] T006 Implement `code/data/generator.py`: Create the "Synthetic SpatialClaw Proxy" with procedural generation logic preserving 3D invariants (occlusion, depth variance)
- [ ] T007 Implement `code/data/loader.py`: Load the Synthetic Proxy data; ensure it fails loudly on missing data (no synthetic fallback)
- [ ] T008 Implement `code/data/projector.py`: Convert 3D point clouds/scenes to 2D symbolic representations (bounding boxes, depth histograms) without 3D libraries (FR-002)
- [ ] T008b [P] [US1] Unit test in `tests/unit/test_projector.py`: Assert no 3D libraries (trimesh, pytorch3d) are imported or called during projection (FR-002 verification)
- [ ] T009 Implement `code/main.py`: Orchestration entry point with random seed pinning and temperature=0 enforcement (FR-008)
- [ ] T010 [P] Create `contracts/dataset.schema.yaml` and `contracts/baseline_run.schema.yaml`
- [ ] T011 [P] Setup logging infrastructure to capture execution logs with seed values and blocked operation details
- [ ] T035 [P] [Edge] Implement memory fallback in `code/data/loader.py`: Stream data in chunks if memory limit is approached (CPU-first constraint, SC-004)
- [ ] T036 [P] [Edge] Log memory usage and warnings during large point cloud processing

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 2D Action Space Restriction & Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the agent logic on the SpatialClaw benchmark dataset using a restricted execution kernel that allows only 2D geometric operations and blocks all 3D libraries, with rigorous stochasticity control.

**Independent Test**: Run a subset of tasks through the restricted kernel; verify `grep "trimesh"` returns 0 in logs, verify no crashes on blocked imports, and verify fixed seeds are logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Unit test for `RestrictedActionError` in `tests/unit/test_kernel.py`: Verify importing `trimesh` raises the error
- [ ] T013 [P] [US1] Unit test for `RestrictedActionError` in `tests/unit/test_kernel.py`: Verify importing `pytorch3d` raises the error
- [ ] T014 [US1] Integration test in `tests/integration/test_kernel_2d.py`: Run a task with `shapely` code and verify success
- [ ] T015 [US1] Integration test in `tests/integration/test_kernel_2d.py`: Verify blocked 3D calls log the error and do not crash the process

### Implementation for User Story 1

- [ ] T016 [P] [US1] Implement `code/agents/agent_2d.py`: Restricted agent logic using only `shapely` and `numpy` (FR-002, FR-008)
- [ ] T017a [P] [US1] Implement stochasticity control mechanism in `code/main.py`: Fix random seeds, set temperature=0 (FR-008 mechanism)
- [ ] T017b [US1] Implement orchestration loop in `code/main.py`: Execute the agent N≥5 times per task instance, logging each run ID (FR-008 execution)
- [ ] T018 [US1] Add logging for blocked operations and seed values in `code/kernel/restricted_kernel.py`
- [ ] T019 [US1] Verify execution logs for the string "trimesh" count is 0 in `tests/integration/test_kernel_2d.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Performance Metric Collection & Baseline Comparison (Priority: P2)

**Goal**: Automatically record success rate, wall-clock inference time, and task type for the restricted 2D agent, and re-run the original 3D baseline agent on the exact same task instances for paired comparison.

**Independent Test**: Process a fixed dataset with both agents; generate a CSV with `task_id`, `task_type`, `success_flag`, `wall_clock_time_ms`, `agent_type`; verify paired comparison logic.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Contract test for results CSV schema in `tests/contract/test_results.py`
- [ ] T021 [P] [US2] Integration test for paired comparison in `tests/integration/test_comparison.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/metrics/collector.py`: Record wall-clock time per step (excluding blocked init time) and success flags (FR-003). **Depends on T016 and T023 completion.**
- [ ] T023 [P] [US2] Implement `code/agents/baseline_3d.py`: Logic for the 3D baseline agent (FR-007 logic). **Moved from Phase 2 to Phase 4.**
- [ ] T023b [US2] Execute `code/agents/baseline_3d.py` on the generated task instances and save results to `data/baseline_spatialclaw.csv` (FR-007 execution, SC-001)
- [ ] T024 [US2] Implement `code/metrics/comparator.py`: Paired comparison logic to calculate differences between 2D and 3D results for each task type (FR-004)
- [ ] T025 [US2] Generate the summary CSV file with columns `task_id`, `task_type`, `success_flag`, `wall_clock_time_ms`, `agent_type`
- [ ] T026 [US2] Implement logic to exclude blocked 3D library initialization time from step latency calculations

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Threshold Sensitivity Analysis (Priority: P3)

**Goal**: Perform paired statistical tests (Wilcoxon/t-test) to determine significance of performance degradation, and conduct sensitivity analysis on depth-estimation thresholds.

**Independent Test**: Run statistical module on paired results; output p-values with Bonferroni correction; generate sensitivity report CSV.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for Wilcoxon test implementation in `tests/unit/test_stats.py`
- [ ] T028 [P] [US3] Unit test for Bonferroni correction in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/stats/tests.py`: Perform McNemar's test for binary success/failure outcomes AND Wilcoxon signed-rank test for continuous error metrics, selecting the test based on the metric type (FR-005)
- [ ] T030 [US3] Implement Bonferroni correction for multiple comparisons (occlusion, depth, relative position) in `code/stats/tests.py`
- [ ] T031 [US3] Implement `code/stats/sensitivity.py`: Sweep depth-estimation threshold over a defined set of values (FR-006)
- [ ] T031b [US3] Implement logic to calculate false-positive and false-negative rates from raw execution logs to populate the sensitivity CSV (SC-003)
- [ ] T032 [US3] Generate sensitivity analysis CSV with columns `threshold_value`, `false_positive_rate`, `false_negative_rate`
- [ ] T033 [US3] Implement logic to log failure reasons ("projection loss" vs "action restriction") using original 3D ground truth as reference

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Edge Cases & Robustness (Non-Blocking)

**Purpose**: Handle specific edge cases mentioned in spec.md (T035 moved to Phase 2)

- [ ] T034 [P] [Edge] Handle flat objects (zero depth variance) in `code/data/projector.py`: Treat as valid 2D inputs without crashing

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` and `research.md`
- [ ] T038 Code cleanup and refactoring
- [ ] T039 Performance optimization across all stories
- [ ] T040 [P] Run full integration test suite in `tests/integration/`
- [ ] T041 Run `quickstart.md` validation
- [ ] T042 Verify `grep "trimesh"` returns 0 in all execution logs

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T022 (Collector) which depends on US1 execution and T023 (Baseline Logic)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US2

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
Task: "Unit test for RestrictedActionError in tests/unit/test_kernel.py"
Task: "Unit test for RestrictedActionError in tests/unit/test_kernel.py"

# Launch all models for User Story 1 together:
Task: "Implement agent_2d.py in code/agents/agent_2d.py"
Task: "Implement stochasticity control mechanism in code/main.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify 2D restriction works)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Paired comparison)
4. Add User Story 3 → Test independently → Deploy/Demo (Statistical significance)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Restricted Kernel & Agent)
   - Developer B: User Story 2 (Metrics & Baseline Re-run)
   - Developer C: User Story 3 (Stats & Sensitivity)
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
- **Data Integrity**: The `loader.py` MUST fail loudly if the Synthetic SpatialClaw Proxy cannot be generated/loaded; no synthetic fallback allowed.
- **Compute**: The entire pipeline is designed for CPU-first execution; GPU escape hatch only if baseline model requires CUDA (not expected for this restricted 2D task).
- **Memory Safety**: Streaming fallback (T035) is implemented in Phase 2 to prevent OOM crashes during baseline re-run or data loading.