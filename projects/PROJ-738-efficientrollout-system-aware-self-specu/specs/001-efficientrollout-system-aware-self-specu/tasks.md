# Tasks: EfficientRollout: System-Aware Self-Speculative Decoding for RL Rollouts

**Input**: Design documents from `/specs/001-efficientrollout-validation/`
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

- [X] T001 Create project structure per implementation plan: `mkdir -p src/{models,services,cli,data,utils} tests/{unit,contract,integration} contracts artifacts data results docs`
- [X] T002 Initialize Python project: Create `pyproject.toml` with `[project.dependencies]` containing `torch`, `transformers`, `accelerate`, `datasets`, `pandas`, `matplotlib`, `pytest`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/utils/memory_monitor.py` to detect RAM pressure and enforce dynamic batch size capping based on available memory thresholds. API: `check_available_ram() -> bool`, `get_peak_usage() -> int`. Log message: "RAM check passed: {mb}MB available".
- [X] T004b [P] Implement OOM fail-safe: Add pre-flight check in `src/utils/memory_monitor.py` to abort if available RAM < 6.5GB with clear error "OOM Risk: Insufficient memory for 8B model".
- [X] T005 [P] Implement `src/data/loaders.py` to load `prompts.jsonl` (SSoT) and filter subsets; fail-fast if file missing
- [X] T006 Create `src/models/drafter.py` wrapper interface for both quantized and full-precision models
- [X] T007 Setup `src/services/latency_tracker.py` for structured JSON logging of per-token acceptance and end-to-end timing
- [X] T008 Configure environment configuration management (CLI args for model paths, subset size, trials)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Initialization and CPU-Feasible Quantization (Priority: P1) 🎯 MVP

**Goal**: Initialize the codebase and generate a CPU-compatible quantized drafter without CUDA dependencies.

**Independent Test**: Run `src/cli/quantize.py` on a CPU-only runner; verify output file exists and loads without `bitsandbytes` or CUDA errors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for `src/utils/memory_monitor.py` in `tests/unit/test_memory_monitor.py` (simulate OOM, verify fallback)
- [X] T010 [P] [US1] Contract test for quantization output schema in `tests/contract/test_quantization_schema.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement CPU-native dynamic quantization logic in `src/cli/quantize.py` using `torch.ao.quantization.quantize_dynamic`. **Deliverable**: Save quantized model to `artifacts/quantized_drafter.pt` AND save the **quantization configuration** (qconfig) to `artifacts/quant_config.json`. The config must contain the mapping of modules to quantization types to ensure reproducibility during loading.
- [X] T011b [P] [US1] Implement `src/models/drafter.py` logic to load the quantized model on CPU only. **Critical**: The loader MUST read `artifacts/quant_config.json` to reconstruct the quantization context before loading `artifacts/quantized_drafter.pt`, ensuring the model is loadable without the original training script or GPU kernels.
- [X] T013 [US1] Add error handling in `src/cli/quantize.py` to fail-fast with clear message if CUDA-specific imports are detected
- [X] T014 [US1] Add logging in `src/models/drafter.py` to report memory footprint upon load (log only: "Model loaded: {size}MB")

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execution of System-Aware SD Toggle on Sample Data (Priority: P2)

**Goal**: Run the `sd_toggle` prediction workflow on a small subset of prompts. to verify logic and latency artifacts.

**Independent Test**: Run `src/cli/run_sd.py` with `--max-num-seqs` set to a configurable limit.; verify JSON log contains "speculation" and "verification" phases and toggle decisions.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Unit test for `src/services/sd_toggle.py` in `tests/unit/test_sd_toggle.py` (verify toggle logic on synthetic high-memory load)
- [X] T016 [P] [US2] Integration test for end-to-end toggle execution in `tests/integration/test_end_to_end_sd.py`

### Implementation for User Story 2

- [X] T017 [US2] Implement `src/services/sd_toggle.py` logic to monitor batch size/memory and dynamically enable/disable speculation. **Contract**: `def should_enable_speculation(batch_size: int, current_ram_mb: int) -> bool`.
- [X] T018 [US2] Implement `src/cli/run_sd.py` entry point to orchestrate the speculative decoding loop using the quantized drafter
- [X] T019 [US2] Integrate `src/services/latency_tracker.py` into `run_sd.py` to log per-token acceptance rates and timing
- [X] T020 [US2] Implement "Synthetic Regime" test hook in `src/services/sd_toggle.py` to force "Enable" decision for validation (SC-005)
- [X] T021 [US2] Add logic in `src/cli/run_sd.py` to limit batch size to 1 or 2 if memory pressure detected (per `memory_monitor`)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduction of Latency Reduction Metrics (Priority: P3)

**Goal**: Compare EfficientRollout (SD) vs. Baseline (AR) latency on the same subset to validate directionality.

**Independent Test**: Run `src/cli/run_baseline.py` and `src/cli/run_sd.py` on the same subset of prompts.; calculate ratio and verify output chart/table.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Unit test for latency calculation logic in `tests/unit/test_latency_tracker.py`
- [X] T023 [P] [US3] Integration test for comparative analysis in `tests/integration/test_comparison_analysis.py`

### Implementation for User Story 3

- [X] T024 [US3] Implement `src/cli/run_baseline.py` entry point to run standard autoregressive generation on the **same quantized 8B model** (Mode A) to isolate algorithmic overhead.
- [X] T025 [US3] Implement `src/cli/run_baseline.py` for the Small-Model Proxy (TinyLlama-1.1B) full-precision baseline (Mode B).
- [X] T026 [US3] Create `src/cli/analyze_results.py` to aggregate JSON logs from T024 and T025, calculate speedup ratio, and output `results/metrics_summary.json`.
- [X] T027 [US3] Implement logic in `analyze_results.py` to explicitly **flag** "negative speedup" or "insignificant" results if SD > Baseline, overriding any implicit "showing <" requirement.
- [X] T028 [US3] Add statistical reporting in `analyze_results.py` to calculate Coefficient of Variation (CV) across multiple data points derived from repeated trials across several prompts
- [X] T035 [US3] Implement validation logic for TinyLlama speedup comparison (Mode B) to confirm results are recorded in `results/tinyllama_validation.json` as per Plan SC-006.
- [X] T036 [US3] Create `src/cli/generate_plots.py` to generate `results/speedup_chart.png` and `results/toggle_decision_chart.png` from aggregated data.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Documentation updates: Update `README.md` to include CLI usage examples for `quantize.py`, `run_sd.py`, and `run_baseline.py`, and update `docs/` with API docs for `sd_toggle.py`.
- [X] T030 Code cleanup and refactoring: Refactor all log statements to use JSON format with keys: `timestamp`, `level`, `message`, `latency_ms`.
- [X] T031 Performance optimization for batch processing in `run_sd.py`
- [X] T032 [P] Additional unit tests for edge cases (empty dataset, load failure) in `tests/unit/`
- [X] T033 Security hardening for file path inputs in `loaders.py`
- [X] T034 Run `quickstart.md` validation to ensure end-to-end workflow documentation is accurate

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T011 completion** (Quantized Drafter artifact)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for the SD implementation and US1 for the model

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (except T004b which depends on T004 logic) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Phase 5 Dependency Graph
- T024 (8B Baseline) and T025 (TinyLlama Baseline) can run in parallel.
- T026 (Analysis) **MUST** wait for both T024 and T025 to complete.
- T035 (TinyLlama Validation) depends on T025.
- T036 (Plots) depends on T026.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for memory_monitor in tests/unit/test_memory_monitor.py"
Task: "Contract test for quantization output schema in tests/contract/test_quantization_schema.py"

# Launch all models for User Story 1 together:
Task: "Create drafter wrapper in src/models/drafter.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (CPU quantization works)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Toggle logic works)
4. Add User Story 3 → Test independently → Deploy/Demo (Speedup validated)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Quantization)
   - Developer B: User Story 2 (SD Toggle)
   - Developer C: User Story 3 (Analysis)
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
- **Critical Constraint**: All tasks must run on CPU-only free-tier CI with limited CPU and RAM resources. No `bitsandbytes`, no CUDA, no 8-bit/4-bit loading flags requiring GPU.