# Tasks: KVarN Variance-Normalized KV-Cache Quantization

**Input**: Design documents from `/specs/001-kvarn-quantization/`
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

- [ ] T001 Create project structure per implementation plan in `code/`
- [ ] T002 Initialize Python 3.10+ project with `requirements.txt` (transformers, torch-cpu, datasets, scikit-learn, pandas, numpy, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/src/quantization/base.py` with abstract `Quantizer` class defining `quantize()` and `dequantize()` methods
- [ ] T005 [P] Implement `code/src/quantization/uniform.py` for the baseline 8-bit linear quantization logic (FR-002)
- [ ] T006 [P] Implement `code/src/inference/hooks.py` with `KVCacheInterceptor` class to capture hidden states during generation
- [ ] T007 [P] Create `code/src/benchmarks/loader.py` to load `math_dataset`, `aime`, `human_eval`, and `ifeval` via `datasets.load_dataset` using canonical IDs (FR-004, Constitution Principle VII)
- [ ] T008 [P] Setup `code/src/analysis/stats.py` with stubs for McNemar's test, paired t-test, and linear regression slope comparison
- [ ] T009 [P] Configure `code/run_experiment.py` entry point with argument parsing for model, dataset, and quantization method

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Implement Variance-Normalized KV-Cache Quantization (Priority: P1) 🎯 MVP

**Goal**: Implement the core KVarN algorithm to scale quantization parameters based on local variance, ensuring statistical distribution preservation.

**Independent Test**: Feed a fixed batch of key-value tensors through the quantizer and verify MSE is calculated and reported correctly without full LLM inference.

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test for variance clamping (var < 1e-8) in `code/tests/unit/test_kvarn.py`
- [ ] T011 [P] [US1] Unit test comparing MSE of KVarN vs Uniform on synthetic tensor slice in `code/tests/unit/test_kvarn.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/src/quantization/kvarn.py` with `KVarNQuantizer` class (FR-001, FR-008)
  - Logic: Calculate local variance, clamp to a small positive floor value, scale quantization parameters, apply 8-bit quantization.
- [ ] T013a [US1] Implement unit-testable logic in `code/src/quantization/kvarn.py` to process a fixed sequence of hidden states (US-1 Independent Test)
  - Must NOT require a full inference loop; verify reconstruction error on static input.
- [ ] T013b [US1] Implement `code/src/inference/engine.py` with `CustomGenerateLoop` that injects `KVarNQuantizer` into the forward pass (FR-003, Plan Deviation)
  - Must use `transformers` hooks to intercept KV caches before they are stored. Depends on T013a being verified.
- [ ] T014 [US1] Add logging for per-token reconstruction error (MSE) to `data/processed/results_{quantizer_type}.jsonl` (FR-005, Principle VI)
- [ ] T014b [US1] Add logging for raw cumulative per-token MSE data points to `data/processed/cumulative_mse_raw.jsonl` (FR-009, FR-010, Principle IV)
  - Ensures raw data exists for statistical analysis tasks T024/T025.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Comparative Inference on Reasoning Benchmarks (Priority: P2)

**Goal**: Run the quantized LLM inference engine on `math_dataset`, `aime`, `human_eval`, and `ifeval` using both quantizers to collect performance data.

**Independent Test**: Run a small subset of `math_dataset` through both pipelines and verify valid outputs and recorded accuracy metrics.

### Tests for User Story 2

- [ ] T015 [P] [US2] Integration test for `math_dataset` subset run with KVarN in `code/tests/integration/test_benchmark_run.py`
- [ ] T016 [P] [US2] Integration test for `math_dataset` subset run with Uniform baseline in `code/tests/integration/test_benchmark_run.py`

### Implementation for User Story 2

- [ ] T017 [US2] Implement `code/src/benchmarks/evaluator.py` to calculate exact-match accuracy and log results (FR-004, FR-005)
- [ ] T018 [US2] Implement `code/src/inference/engine.py` logic to load **Phi (compact)** model (`microsoft/phi-2`) in FP16 (Plan Deviation: Llama-2-7B excluded due to RAM)
  - Note: Spec Assumptions require update to reflect Phi-2 usage.
- [ ] T019 [US2] Create `code/run_benchmark.py` script to iterate through datasets, run both quantizers, and save `data/processed/benchmark_results.jsonl`
- [ ] T020 [US2] Add logic to measure and report KV-cache size reduction percentage (FR-007)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Analysis of Error Accumulation (Priority: P3)

**Goal**: Statistically compare reconstruction errors and task accuracies to determine significance and validate the error accumulation hypothesis.

**Independent Test**: Run analysis on synthetic paired results with known effect sizes to verify correct application of McNemar's test and slope comparison.

### Tests for User Story 3

- [ ] T021 [P] [US3] Unit test for McNemar's test implementation in `code/tests/unit/test_stats.py`
- [ ] T022 [P] [US3] Unit test for slope comparison regression in `code/tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T023 [US3] Implement `code/src/analysis/stats.py` fully: McNemar's test for binary accuracy (FR-006), t-test/Wilcoxon for MSE (FR-006)
- [ ] T024 [US3] Implement `code/src/analysis/stats.py` logic for Pearson correlation between cumulative MSE and accuracy (FR-009)
  - Input: `data/processed/cumulative_mse_raw.jsonl` (from T014b).
- [ ] T025 [US3] Implement `code/src/analysis/stats.py` logic for linear regression slope comparison of error accumulation trends (FR-010)
  - Input: `data/processed/cumulative_mse_raw.jsonl` (from T014b).
- [ ] T026 [US3] Create `code/run_analysis.py` to ingest `data/processed/benchmark_results.jsonl`, run all tests, and output `data/processed/analysis_summary.json` adhering to `contracts/analysis_summary_schema.schema.yaml` (FR-006, FR-009, FR-010)
- [ ] T027 [US3] Implement `code/src/analysis/plots.py` to generate error accumulation divergence plots (US-3, SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T028 [P] Documentation updates in `code/README.md` and `specs/001-kvarn-quantization/quickstart.md`
- [ ] T029 Code cleanup and refactoring for CPU efficiency (ensure no CUDA imports)
- [ ] T030 [P] Run `pytest` suite with coverage report
- [ ] T031 [P] Run quickstart.md validation to ensure all commands execute on CPU-only environment

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 implementation (Quantizer)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 implementation (Benchmark Results)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Classes before services/logic
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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for variance clamping (var < 1e-8) in code/tests/unit/test_kvarn.py"
Task: "Unit test comparing MSE of KVarN vs Uniform on synthetic tensor slice in code/tests/unit/test_kvarn.py"

# Launch all models for User Story 1 together:
Task: "Implement code/src/quantization/kvarn.py with KVarNQuantizer class"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Quantizer works, MSE is correct)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Inference on benchmarks)
4. Add User Story 3 → Test independently → Deploy/Demo (Statistical conclusions)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Quantizer & Hooks)
   - Developer B: User Story 2 (Benchmark Runner)
   - Developer C: User Story 3 (Analysis Scripts)
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
- **Hardware Constraint**: All tasks MUST run on CPU-only (limited cores, limited RAM). No CUDA, no bitsandbytes, no 8-bit/4-bit model loading that requires GPU. Use Phi-2 (2.7B) FP16.
- **Plan Deviation**: Spec FR-003 (vllm) and Assumptions (Llama-2-7B) are infeasible. Tasks implement `transformers` + `microsoft/phi-2`. Spec document requires update.