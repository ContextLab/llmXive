# Tasks: Reproduce & Validate LocateAnything (Eagle)

**Input**: Design documents from `/specs/636-reproduce-locateanything/`
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

- [X] T001a [P] Create `src/` directory structure
- [X] T001b [P] Create `tests/` directory structure
- [X] T001c [P] Create `contracts/` directory structure
- [X] T002 [P] Initialize Python 3.10+ project with `requirements.txt` (include `llama-cpp-python>=0.2.0`, `transformers`, `Pillow`, `pandas`, `pytest`, `numpy`, `pyyaml`)
- [X] T002b [P] Download or verify specific GGUF model file: `external/Eagle/models/eagle-7b-q4_0.gguf` (Target model path example)
- [X] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No work on User Story 1, User Story 2, User Story 3, or any associated Test tasks can begin until this phase is complete.

- [X] T004 [P] Setup `contracts/` directory and define `inference_result.schema.yaml` (fields: image_id, prompt, predicted_boxes, inference_time_ms, status, pbd_serial_overhead_ms)
- [X] T005 [P] Setup `contracts/` directory and define `evaluation_metric.schema.yaml` (fields: benchmark_name, subset_size, mean_iou, throughput_images_per_sec, memory_limit_pass, validation_mode, ground_truth_source)
- [X] T006 [P] Create `src/config/settings.yaml` for dataset paths, batch size (default 1), and model config
- [X] T006b [P] Create and populate `src/config/paper_claims.yaml` with specific numerical values from the paper (e.g., claimed throughput, baseline IoU) for comparison
- [X] T007 [P] [Depends: T004, T005, T006] Implement `src/inference/utils.py` for CPU device handling, memory logging (peak RAM), and GGUF loading helpers
- [X] T008 [P] [Depends: T004, T005, T006] Implement `src/evaluation/metrics.py` for IoU calculation (supporting Synthetic Ground Truth)
- [X] T009 [P] [Depends: T004, T005, T006] Create `src/evaluation/synthetic_gt_generator.py` to programmatically inject known bounding boxes into images for validation
  - **Logic**: Use random uniform distribution within image bounds (0-1 normalized) or fixed grid.
  - **Validation**: MUST validate generated boxes against `inference_result.schema.yaml` format before output.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Validate Model Inference on Sample Data (Priority: P1) 🎯 MVP

**Goal**: Load the vendored Eagle model in CPU-only mode (GGUF), execute PBD (or Serial Fallback), and output valid bounding box coordinates.

**Independent Test**: Execute `run_smoke_test.py` with a 512x512 sample image and prompt "Locate the dog". Verify output JSON contains valid boxes and no CUDA errors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for `InferenceResult` schema in `tests/contract/test_inference_schema.py`
- [X] T011 [P] [US1] Integration test for CPU-only loading in `tests/integration/test_cpu_load.py`

### Implementation for User Story 1

- [X] T012 [US1] [Depends: T004, T005, T006, T007] Implement `src/inference/run_smoke_test.py`
  - **Implements FR-001** by loading the model using `llama-cpp-python` with `device="cpu"` and GGUF quantization.
  - **Implements FR-002** by executing Parallel Box Decoding (PBD) as the primary target.
  - **Fallback Logic**: If PBD fails (e.g., raises CUDA error or fails to execute), execute CPU-Serial Fallback (iterative decoding) as a conditional contingency.
  - **Metric Tag**: `PLAN-PBD-SERIAL-OVERHEAD` - Run Serial Baseline to measure `pbd_serial_overhead_ms` (Serial Time - PBD Time).
  - Log memory/time and validate output JSON against schema.
  - **Validation Link**: Passing this test confirms that T012 correctly implements the model loading and inference logic.

- [X] T012c [US1] [Depends: T012] Implement logic to calculate and set `memory_limit_pass` field in the output schema based on peak RAM usage (Step 3.1.1).

- [X] T013 [US1] [Depends: T012] Add error handling in `run_smoke_test.py` to detect missing/corrupted weights and fail fast with clear message (Addresses Edge Case: Missing weights in spec.md).
- [X] T014 [US1] [Depends: T012] Add logic in `run_smoke_test.py` to handle zero-detected boxes (return empty list `[]`) (Addresses Edge Case: Zero detected boxes in spec.md).
- [X] T015 [US1] [Depends: T012] Add logging for peak RAM usage and total inference time (FR-004).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Benchmark Evaluation on a Subset (Priority: P2)

**Goal**: Run the evaluation pipeline on a small subset using Synthetic Ground Truth to verify IoU scoring logic.

**Independent Test**: Run `run_subset_eval.py` on 50 synthetic images. Verify results JSON contains per-sample IoU and aggregate mean IoU.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for `EvaluationMetric` schema in `tests/contract/test_evaluation_schema.py`
- [X] T017 [P] [US2] Integration test for batch processing in `tests/integration/test_batch_eval.py`

### Implementation for User Story 2

- [X] T018 [US2] [Depends: T004, T005, T006, T008] Implement `src/evaluation/run_subset_eval.py`
  - **Implements FR-003** by calculating IoU against Real Benchmark GT if available.
  - **Implements US-2** by running subset evaluation on 50 images.
  - **Branching Logic**: 
    1. If Real GT exists: Calculate IoU, set `validation_mode: 'real'`.
    2. If Real GT missing but Synthetic GT available: Calculate IoU, set `validation_mode: 'synthetic'`.
    3. If neither available: Skip IoU calculation, set `validation_mode: 'pipeline_only'`.

- [X] T018c [US2] [Depends: T018] Implement the specific logic branch for `validation_mode: 'pipeline_only'` (no GT available) to ensure distinct handling from synthetic mode.

- [X] T018e [US2] [Depends: T018] Implement logic to calculate and set `memory_limit_pass` field in the output schema based on peak RAM usage (Step 3.1.1).

- [X] T019 [US2] [Depends: T018] Implement logic to detect if real Ground Truth is missing and set `validation_mode: 'synthetic'` in output metrics.
- [X] T020 [US2] [Depends: T018] Add memory usage logging for the evaluation batch (FR-004).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Reproduction Report Artifacts (Priority: P3)

**Goal**: Compile inference and evaluation outputs into a structured report comparing observed metrics against paper claims.

**Independent Test**: Run `generate_report.py`. Verify `reproduction_report.md` contains tables of metrics and a pass/fail summary.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US3] Integration test for report generation in `tests/integration/test_report_gen.py`

### Implementation for User Story 3

- [X] T022 [US3] [Depends: T004, T005, T006, T006b, T012, T018] Implement `src/reporting/generate_report.py`
  - **Implements FR-004** by aggregating logs from inference and evaluation steps.
  - **Implements US-3** by generating a structured report.
  - **Constitution Check**: Explicitly check for `constitution.md` existence. If missing, inject a warning note into the report.
  - Compare observed throughput (images/sec) and mean IoU against paper claims (SC-001, SC-002) using values from `src/config/paper_claims.yaml`.
  - Explicitly note CPU vs. GPU limitations and sample size caveats.
  - Compare model output against a Trivial Baseline (random box) for relative quality.
  - Generate `reproduction_report.md` with pass/fail status on claims (SC-004).
  - **Limitation Note**: Explicitly state if 'Real GT Unavailable' or 'Accuracy Unverified' in the report summary.

- [X] T023 [US3] [Depends: T022] Add logic to include "Constitution Missing" note in the report if `constitution.md` is absent (per plan.md).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Verification & Final Reporting (Polish)

**Purpose**: Run the full pipeline on CI and validate against success criteria.

- [X] T024a [P] Create GitHub Actions workflow file `.github/workflows/reproduce_eagle.yml`
- [X] T024b [P] Configure install step in workflow (dependencies, GGUF verification)
- [X] T024c [P] Configure test steps in workflow (run smoke test, run subset eval, generate report, validate schemas)
- [X] T025 [P] Implement memory threshold validation in CI: Parse logs, verify `peak_memory_mb` < 7000 MB. Record Pass/Fail for SC-003.
- [X] T026 [P] Review `reproduction_report.md` for completeness and explicit limitations.
- [X] T027 [P] Finalize `plan.md` and close the feature.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on outputs from US1 and US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utils before services
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
Task: "Contract test for InferenceResult schema in tests/contract/test_inference_schema.py"
Task: "Integration test for CPU-only loading in tests/integration/test_cpu_load.py"

# Launch implementation tasks:
Task: "Implement src/inference/run_smoke_test.py"
Task: "Add error handling in run_smoke_test.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Smoke test passes, CPU-only, valid JSON)
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
   - Developer A: User Story 1 (Inference)
   - Developer B: User Story 2 (Evaluation)
   - Developer C: User Story 3 (Reporting)
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
- **Critical Constraint**: All tasks must be executable on CPU-only resources with limited memory capacity. No CUDA, no bitsandbytes, no float32 loading for 7B+ models. Use GGUF quantization and Synthetic Ground Truth where necessary.