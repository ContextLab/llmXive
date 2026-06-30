# Tasks: Reproduce & Validate Observation Masking Regime Map

**Input**: Design documents from `/specs/652-reproduce-observation-masking/`
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

- [X] T001 Create project structure per implementation plan (`src/cli`, `src/analysis`, `src/lib`, `data/artifacts`, `logs/trajectories`, `tests/`)
- [X] T002 Initialize Python 3.11 project with dependencies: `torch` (CPU), `transformers` (CPU), `datasets`, `pandas`, `matplotlib`, `scikit-learn`, `requests`, `pytest`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `src/lib/retry_utils.py`: Exponential backoff logic (with a configurable maximum number of retries) for API calls, logging rate-limit events to `TrajectoryLog`
- [X] T005 [P] Implement `src/lib/masking.py`: Core observation masking algorithm, truncation handling, and calculation of `tokens_saved`/`turns_added` metrics. **Note**: This is a pure function library with no CLI integration logic, ensuring it is independent of T019 and safe for parallel execution.
- [X] T006 [P] Define `contracts/evaluation-run.schema.yaml` and `contracts/trajectory-log.schema.yaml` with fields: `model_id` (string), `masking_status` (boolean), `accuracy` (float), `tokens_saved` (int), `turns_added` (int)
- [X] T007 [P] Create `src/data_loader.py`: Utility to fetch SWE-bench subset via `datasets.load_dataset` (no manual URL downloads) with error handling
- [X] T008 [P] Setup `src/cli/eval_runner.py` CLI entry point with `--masking-on`, `--masking-off`, `--model-id`, and `--sample-size` arguments
- [X] T009 [P] Create `tests/unit/test_retry.py` with test cases: `test_exponential_backoff_delays`, `test_max_retries_exceeded`, `test_rate_limit_logging`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Baseline Evaluation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Execute the vendored evaluation script on a CPU-only runner with a small sample to confirm valid output artifacts.

**Independent Test**: Run `python src/cli/eval_runner.py --dataset swe-bench --sample-size 10 --masking-off --model-id TinyLlama-1.1B` and verify `data/artifacts/baseline_run.json` is generated with 10 entries.

### Implementation for User Story 1

- [X] T012a [US1] Implement `src/cli/eval_runner.py` argument parsing for `--masking-off` and `--model-id`
- [X] T012b [US1] Implement dataset loading loop using `src/data_loader.py`
- [X] T012c [US1] Implement evaluation loop calling vendored `eval.py` with masking disabled, writing to `data/artifacts/baseline_run.json`. **Include logic**: Add metadata field `sample_size_warning` to the output JSON if `sample-size < 5` to flag insufficient sample size.
- [X] T013 [US1] Integrate `src/lib/retry_utils.py` into the evaluation loop to handle API rate limits without crashing
- [X] T014 [US1] Implement context truncation logic in `src/lib/masking.py` to handle context window limits safely (reuse T005 logic)
- [X] T015a [US1] Implement structured logging (JSON) for every tool call and observation to `logs/trajectories/` (masking decisions excluded here)

### Tests for User Story 1 (Contract & Integration)

- [X] T010 [P] [US1] Contract test in `tests/contract/test_schemas.py`: Validate output JSON against `trajectory-log.schema.yaml`
- [X] T011 [P] [US1] Integration test in `tests/integration/test_pipeline.py`: Run a multi-task sample, assert zero unhandled exceptions, verify log file existence

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Regime Map Construction (Priority: P2)

**Goal**: Run evaluation with masking enabled/disabled across two distinct models (TinyLlama, Phi-2) to reproduce the "rising limb" of the regime map.

**Independent Test**: Compare accuracy metrics of `masked_run` vs `baseline_run` for TinyLlama and Phi-2; verify positive accuracy gain for the "rising limb" regime.

### Implementation for User Story 2

- [X] T018 [P] [US2] Extend `src/cli/eval_runner.py` to support sequential execution of multiple model/masking combinations
- [X] T019 [US2] Implement CLI integration wrapper in `src/cli/eval_runner.py` to toggle observation masking by calling `src/lib/masking.py` (core logic). **Note**: This task orchestrates the use of T005's library functions but does not implement the core algorithm itself.
- [X] T019b [US2] Implement logic to handle "saturated model" acceptance scenario: Attempt to run with a proxy (e.g., TinyLlama with high temperature) or explicitly log "Inconclusive: Saturated Model Unavailable" in the regime data
- [X] T015b [US2] Implement logging of masking decisions (if any) to `logs/trajectories/` with a pre-check: Verify "stale observation" patterns exist in the current trajectory; if not, log "no-pattern-found" status instead of empty logs
- [X] T020 [US2] Implement `src/analysis/regime_analyzer.py` (Producer Phase): Load `baseline_run.json` and `masked_run.json`, calculate `accuracy_gain`, and output `data/artifacts/regime_comparison.json`. **Crucially**, include logic to detect if data points < 3 and set `trend_verification` status to "Skipped/Inconclusive" in the output to handle the impossibility of verifying a non-monotonic trend with only two models.
- [X] T021b [US2] [Concern Coverage] Add logic to `src/analysis/regime_analyzer.py` to explicitly document the inability to validate the Collapse Regime due to compute constraints in the `regime_comparison.json` metadata.
- [X] T021 [US2] Generate `data/artifacts/regime_comparison.json` containing accuracy gain for TinyLlama and Phi

**Data Flow Note**: T020 and T021b produce `regime_comparison.json`. T024 (Phase 5) consumes this file.

### Tests for User Story 2 (Optional)

- [X] T017 [P] [US2] Integration test in `tests/integration/test_pipeline.py`: Run masked and baseline for both models, assert data points exist for comparison

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Mechanistic Analysis Artifacts (Priority: P3)

**Goal**: Execute analysis scripts to generate visualizations and statistics explaining the "token-for-turn" mechanism.

**Independent Test**: Run `python src/analysis/regime_analyzer.py` on results from US2; verify output includes a scatter plot of accuracy gain vs model capacity and a correlation statistic.

### Implementation for User Story 3

- [X] T024 [P] [US3] Implement `src/analysis/regime_analyzer.py` (Consumer/Visualize Phase): Load `data/artifacts/regime_comparison.json` (output of T020/T021), calculate correlation between `tokens_saved` and `turns_added`, and generate plots.
- [X] T025 [US3] Generate `data/artifacts/regime_map_plot.png` (scatter plot of Model Capacity vs Accuracy Gain)
- [X] T026 [US3] Generate `data/artifacts/mechanism_summary.txt` containing the correlation coefficient and "token-for-turn" hypothesis validation status
- [X] T027 [US3] Implement `src/analysis/stale_detector.py` to scan `TrajectoryLog` for repeated tool calls within N turns, calculate a `stale_score`, and log the result to `logs/trajectories/stale_analysis.log`
- [X] T028 [US3] Generate `data/artifacts/regime_report.md`: A narrative report including the "Regime Map" visualization, the "Rising Limb" validation, and a dedicated section explicitly documenting the inability to validate the Collapse Regime due to compute constraints (satisfying FR-005 intent)

### Tests for User Story 3 (Optional)

- [X] T023 [P] [US3] Contract test in `tests/contract/test_schemas.py`: Validate analysis output schema

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Documentation updates: Update `quickstart.md` with CLI usage examples for masking toggle
- [X] T030 [P] Code cleanup: Remove debug prints, ensure consistent error messages
- [X] T031 [P] Run full integration test suite on CPU-only runner to verify the prescribed time limit and a constrained memory limit

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
- **User Story 2 (P2)**: Depends on US1 (requires baseline data and masking logic)
- **User Story 3 (P3)**: Depends on US2 (requires regime data points for analysis)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately
- US2 and US3 must be sequential due to data flow dependencies

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (CPU execution, no crashes)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (Masking toggle, two models) → Deploy/Demo
4. Add User Story 3 → Test independently (Analysis artifacts) → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: (Wait for US1 completion) User Story 2
   - Developer C: (Wait for US2 completion) User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks MUST run on free-tier CPU resources. No GPU, no 8-bit quantization, no large model training.
- **Data Flow**: T012a-c (Baseline) → T019/T019b (Masking) → T020/T021b (Regime Data) → T024/T028 (Analysis/Report). Ensure masking tasks come after baseline logic is stable.
- **Dataset**: Use `datasets.load_dataset("SWE-bench")` with `split="test"` and filtering for sample size. Do not manually download CSVs.