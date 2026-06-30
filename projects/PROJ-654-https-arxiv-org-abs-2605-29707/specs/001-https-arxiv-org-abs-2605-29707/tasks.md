# Tasks: Reproduce & Validate Domino Speculative Decoding Framework

**Input**: Design documents from `/specs/001-https-arxiv-org-abs-2605-29707/`
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

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `external/Domino/`) including `git submodule init` and `git submodule update` for `external/Domino`
- [ ] T002 Initialize Python 3.10+ project with CPU-only `torch` and `transformers` dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup environment configuration management (`src/benchmark/config.py`) to handle model substitution (Qwen3 -> Qwen2-1.8B) and device detection
- [ ] T005 [P] Implement hardware detection utility in `src/benchmark/utils.py` to enforce CPU-only mode and prevent CUDA imports
- [ ] T005b Configure `device_map` parameter in model loader based on T005 detection results to satisfy FR-004
- [ ] T006 Create base metrics schema in `contracts/benchmark_metrics.schema.yaml`
- [ ] T007 Create logging infrastructure in `src/benchmark/logging.py` to capture library versions (FR-006) and hardware context (SC-004)
- [ ] T007b Implement code in `src/benchmark/logging.py` to explicitly query `transformers` and `torch` versions and write to log (FR-006)
- [ ] T008 Setup timeout wrapper mechanism in `src/benchmark/runner.py` to abort processes exceeding 45 minutes (FR-005)
- [ ] T009 Implement dataset fetcher in `src/benchmark/data.py` using `datasets.load_dataset("cnn_dailymail")` with token-length filtering to prevent OOM

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute End-to-End Validation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Execute the vendored `Domino` benchmark scripts on a standard CPU-only environment to confirm the implementation runs without modification and produces initial output artifacts.

**Independent Test**: The pipeline runs `run_hf_benchmark.sh` (or `benchmark.py`) and exits with status 0, producing at least one log file and one metrics JSON/CSV artifact in the `external/Domino/` directory.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for metrics JSON schema in `tests/contract/test_metrics_schema.py`: function `test_metrics_schema_validates_required_fields` validates `contracts/benchmark_metrics.schema.yaml`
- [ ] T011 [P] [US1] Integration test for CPU-only execution flow in `tests/integration/test_cpu_execution.py`: function `test_runner_enforces_cpu_only_mode` asserts no CUDA import errors raised

### Implementation for User Story 1

- [ ] T012 [US1] Implement `src/benchmark/runner.py` to wrap `external/Domino/run_hf_benchmark.sh` with timeout and CPU-enforcement logic
- [ ] T013 [US1] Create wrapper script `src/benchmark/patch_requirements.sh` to inject dependencies at runtime (excluding `bitsandbytes`) without modifying vendored `external/Domino/requirements-hf.txt` (Preserves US-1 'unmodified' constraint)
- [ ] T014 Implement `src/benchmark/metrics.py` to parse output logs and generate structured `results_*.json` artifacts (FR-003)
- [ ] T015 [US1] Add error handling for "Out of Memory" scenarios: catch `torch.OutOfMemoryError`, log "OOM: Subsampling dataset", and exit with code 137 with message suggesting model quantization or dataset subsampling
- [ ] T016 [US1] Add retry logic for `pip install` commands using `tenacity` library with 3 retries

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Verify Computational Feasibility & Resource Constraints (Priority: P2)

**Goal**: Confirm that the reproduction process completes within the GitHub Actions free-tier limits (standard CPU allocation, adequate RAM, 6 hours) without OOM errors or excessive runtime.

**Independent Test**: The benchmark run finishes in ≤45 minutes on a standard 2-core runner and stays under 6GB RAM usage peak.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for memory usage threshold in `tests/contract/test_resource_limits.py`: function `test_memory_usage_threshold` asserts `peak_rss < 6.5 * 1024**3`
- [ ] T019 [P] [US2] Integration test for timeout mechanism in `tests/integration/test_timeout.py`: function `test_runner_aborts_after_45_minutes` asserts process exit code indicates a timeout condition

### Implementation for User Story 2

- [ ] T020 [US2] Implement `src/benchmark/resource_monitor.py` to track peak RSS memory and log warnings if >6.5 GB
- [ ] T021 [US2] Refine `src/benchmark/runner.py` to enforce a reasonable hard timeout (FR-005) and log termination reasons
- [ ] T022 [US2] Implement sample dataset logic in `src/benchmark/data.py` to dynamically limit prompts to fit within 45-minute runtime target (no arbitrary 50-sample cap)
- [ ] T023 [US2] Integrate hardware detection (from T005b) to ensure `device_map` is correctly configured (CPU fallback if no GPU), preventing `CUDA_VISIBLE_DEVICES` errors (US-2, FR-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduce Paper Claims & Generate Comparison Report (Priority: P3)

**Goal**: Compare the reproduced metrics (speedup, throughput) against the paper's reported claims (up to 5.49x speedup) to validate the scientific accuracy of the vendored code, while explicitly flagging methodological conflicts.

**Independent Test**: A comparison report is generated that lists the reproduced speedup factor and explicitly states whether it matches the paper's range (considering hardware differences).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for validation report schema in `tests/contract/test_validation_report.py`: function `test_validation_report_schema_compliance` validates `contracts/validation_report.schema.yaml`
- [ ] T025 [P] [US3] Integration test for speedup calculation logic in `tests/integration/test_speedup_calc.py`: function `test_speedup_ratio_calculation_accuracy` verifies input/output pairs for speedup ratio

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/benchmark/analyzer.py` to calculate `speedup_ratio` (Baseline_Latency / Domino_Latency)
- [ ] T027 [US3] Implement `src/benchmark/reporter.py` to generate `validation_report.md` comparing results against the 5.49x claim (FR-007)
- [ ] T028 [US3] Add logic to `src/benchmark/reporter.py` to explicitly implement a tolerance check against the 5.49x claim and flag results as "Valid Scientific Outcome (Speedup < 1.0)" if CPU constraints prevent GPU-level speedup, citing hardware differences (Plan Note: Spec Conflict)
- [ ] T029 [US3] Implement acceptance rate analysis in `src/benchmark/analyzer.py` as the primary scientific validation metric (Plan Note: Mechanism Validation)
- [ ] T030 [US3] Log specific configuration parameters (draft size, model size) in the report if speedup < 1.0x (FR-007)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `README.md` detailing CPU-only constraints and model substitution logic
- [ ] T032 Code cleanup and refactoring of `src/benchmark` modules
- [ ] T033 [P] Additional unit tests for metrics parsing edge cases in `tests/unit/test_metrics.py`: functions `test_empty_log_file`, `test_nan_latency`, `test_missing_key`
- [ ] T034 Run `quickstart.md` validation to ensure all steps execute correctly on a fresh runner
- [ ] T035 [P] Validate `tasks.md` against the template structure

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T005, T005b, T007, T007b) can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for metrics JSON schema in tests/contract/test_metrics_schema.py: function test_metrics_schema_validates_required_fields"
Task: "Integration test for CPU-only execution flow in tests/integration/test_cpu_execution.py: function test_runner_enforces_cpu_only_mode"

# Launch all models for User Story 1 together:
Task: "Implement src/benchmark/runner.py to wrap external/Domino/run_hf_benchmark.sh"
Task: "Create wrapper script src/benchmark/patch_requirements.sh to inject dependencies at runtime"
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
- **Critical Constraint**: All tasks must be executable on CPU-only runners with limited computational resources (few vCPUs, moderate RAM) without CUDA dependencies.