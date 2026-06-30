# Tasks: Reproduction of MM-OCEAN Benchmark

**Input**: Design documents from `/specs/620-reproduce-mm-ocean-benchmark/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [X] T001 Create project structure per implementation plan (`src/runners`, `src/metrics`, `src/viz`, `tests/`)
- [X] T002 Initialize Python 3.10+ project with dependencies (`torch`, `transformers`, `accelerate`, `pandas`, `matplotlib`, `pyyaml`, `jsonschema`, `statsmodels`) in `requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup JSON Schema contracts for data integrity in `contracts/evaluation_result.schema.yaml` and `contracts/aggregated_metrics.schema.yaml`
- [X] T005 [P] Implement base logging infrastructure in `src/utils/logger.py` with standardized error codes for timeouts and model load failures
- [X] T006 [P] Create `src/utils/streaming_video_loader.py` to handle on-the-fly frame extraction without disk exhaustion (Addressing Edge Case: Dataset Variable Fit)
- [X] T007 Create `src/utils/timeout_decorator.py` to enforce the 600s per-sample limit (Addressing Edge Case: Timeout Handling)
- [X] T008 Configure environment variable management for `data/test` paths and model selection in `src/config/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute End-to-End Evaluation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Run the vendored `MM-OCEAN` evaluation script against the test dataset with CPU constraints, timeouts, and graceful error handling.

**Independent Test**: Execute `python src/runners/evaluate_runner.py --subset test --limit 10` and verify `results/test_subset_results.json` exists and is non-empty, with no CUDA errors.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for `timeout_decorator.py` in `tests/unit/test_timeout_decorator.py` (verify kill signal after 600s)
- [X] T010 [P] [US1] Unit test for `streaming_video_loader.py` in `tests/unit/test_streaming_video_loader.py` (verify low memory footprint)
- [X] T011 [P] [US1] Integration test for CPU-only model loading in `tests/integration/test_cpu_model_load.py` (verify no CUDA initialization)
- [X] T012 [P] [US1] Integration test for graceful skip on model error in `tests/integration/test_graceful_skip.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `src/runners/evaluate_runner.py` wrapper that initializes `external/MM-OCEAN/evaluate.py` with CPU flags and timeout logic
- [X] T014 [US1] Implement logic to disable CUDA (`device_map="cpu"`, `torch.set_num_threads(2)`) in `src/runners/evaluate_runner.py` (FR-003)
- [X] T015 [US1] Integrate `streaming_video_loader.py` into the runner to feed frames to the model without full video caching (FR-001)
- [X] T016 [US1] Implement per-sample timeout wrapping using `timeout_decorator.py` to prevent CI hangs (FR-005)
- [X] T017 [US1] Implement graceful error handling: catch model load failures, log to `results/errors.log`, and continue to next sample (FR-003)
- [X] T018 [US1] Ensure output `results/test_subset_results.json` conforms to `contracts/evaluation_result.schema.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Quantitative Metrics and Reproduce Key Findings (Priority: P2)

**Goal**: Compute the four sample-level failure-mode metrics (Prejudice Rate, Confabulation Rate, Integration-failure Rate, Holistic-grounding Rate) and compare against paper baselines.

**Independent Test**: Run `python src/metrics/failure_mode_calculator.py --input results/test_subset_results.json` and verify output matches `contracts/aggregated_metrics.schema.yaml` with values within ±5% of paper baselines.

### Tests for User Story 2

- [X] T019 [P] [US2] Unit test for `failure_mode_calculator.py` in `tests/unit/test_failure_mode_calculator.py` (verify formula logic against mock data)
- [X] T020 [P] [US2] Unit test for schema validation in `tests/unit/test_metrics_schema.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement `src/metrics/failure_mode_calculator.py` to parse `results/test_subset_results.json` and calculate PR, CR, IR, HR (FR-002)
- [X] T022 [US2] Implement aggregation logic to compute rates per model and overall (FR-004)
- [X] T023 [US2] Integrate comparison logic to calculate variance against paper baselines (deferred values) and flag if > ±5% (US-2)
- [X] T024 [US2] Generate `results/aggregated_metrics.json` conforming to `contracts/aggregated_metrics.schema.yaml` (FR-004)
- [X] T025 [US2] Implement dropout analysis logic: compare video duration of processed vs. skipped samples (Plan: Statistical Rigor)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Diagnostic Reports and Visualizations (Priority: P3)

**Goal**: Generate human-readable diagnostic reports and summary visualizations (bar charts of failure rates) for qualitative assessment.

**Independent Test**: Run `python src/viz/report_generator.py` and verify existence of `reports/summary_report.md` and `reports/failure_mode_distribution.png` with non-placeholder content.

### Tests for User Story 3

- [X] T026 [P] [US3] Unit test for `report_generator.py` in `tests/unit/test_report_generator.py` (verify markdown structure)
- [X] T027 [P] [US3] Unit test for chart generation in `tests/unit/test_viz_generation.py` (verify PNG creation)

### Implementation for User Story 3

- [X] T028 [US3] Implement `src/viz/report_generator.py` to parse `results/aggregated_metrics.json` (FR-006)
- [X] T029 [US3] Generate `reports/summary_report.md` listing top 3 failure modes by frequency (US-3)
- [X] T030 [US3] Generate `reports/failure_mode_distribution.png` comparing Prejudice Rate across model families (US-3)
- [X] T031 [US3] Ensure report includes the "Prejudice Gap" and "Holistic-Grounding Rate" comparison sections (US-3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T032 [P] Update `README.md` with instructions for running the CPU-only evaluation pipeline
- [X] T033 [P] Add GitHub Actions workflow `.github/workflows/reproduction-ci.yml` to run the full pipeline on the free-tier runner (2 CPU, 7 GB RAM)
- [X] T034 Code cleanup and refactoring of `src/utils` and `src/metrics` modules
- [X] T035 Run `quickstart.md` validation to ensure all steps are reproducible
- [X] T036 Verify SC-001 (≥90% video processing) and SC-002 (±5% metric variance) against the final run

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
- **User Story 2 (P2)**: Depends on User Story 1 completion (needs `results/test_subset_results.json` to calculate metrics)
- **User Story 3 (P3)**: Depends on User Story 2 completion (needs `results/aggregated_metrics.json` to generate reports)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utils before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T005, T006, T007) can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- Models/Utils within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for timeout_decorator.py"
Task: "Unit test for streaming_video_loader.py"
Task: "Integration test for CPU-only model loading"
Task: "Integration test for graceful skip on model error"

# Launch all implementation tasks for User Story 1 (sequential due to dependencies):
Task: "Implement evaluate_runner.py"
Task: "Implement CPU flag logic"
Task: "Integrate streaming loader"
Task: "Implement timeout wrapping"
Task: "Implement graceful error handling"
Task: "Ensure JSON schema conformance"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify CPU execution and timeout logic)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Metrics validated)
4. Add User Story 3 → Test independently → Deploy/Demo (Reports generated)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Pipeline execution)
   - Developer B: User Story 2 (Metrics calculation - can start once T013 is done)
   - Developer C: User Story 3 (Visualization - can start once T024 is done)
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
- **Critical Constraint**: All tasks must run on free CPU-only CI with limited CPU cores and RAM.. No GPU, no 8-bit quantization, no large model loading without streaming.
