# Tasks: Reproduce & Validate NEO-ov One-Vision Model

**Input**: Design documents from `/specs/001-reproduce-neo-ov/`
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

- [X] T001 Create project structure per implementation plan in `src/neo_ov/`, `src/scripts/`, `src/data/`, `src/outputs/`, and `tests/`
- [X] T002 Initialize Python 3.9+ project with `requirements.txt` including `torch` (CPU-only), `transformers`, `vlmevalkit`, `pandas`, `pyyaml`, `requests`, `scipy`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/neo_ov/config.py` to define sample limits (max 1000), CPU-only flags, and path constants
- [X] T005 Implement `src/neo_ov/utils.py` for structured logging, error handling, and CPU/GPU detection logic
- [X] T006 Implement `src/neo_ov/inference.py` as a wrapper enforcing CPU-only execution and sample caps
- [X] T007 Create `src/scripts/run_smoke_test.py` entry point for 5-sample validation
- [X] T008 Create `src/scripts/run_validation.py` entry point for 500-sample validation
- [X] T009 Create `src/scripts/generate_report.py` for compiling metrics and limitations
- [X] T010 Define prediction artifact schema in `contracts/prediction_schema.json` (fields: prediction, ground_truth, is_correct, confidence)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Validate Execution Pipeline on Sample Data (Priority: P1) 🎯 MVP

**Goal**: Confirm the NEO-ov pipeline initializes, runs on CPU, and produces valid output on a minimal subset.

**Independent Test**: The CI job runs `src/scripts/run_smoke_test.py` against 5 images from MMBench using only CPU. Success is defined by a successful exit code and a result file with a valid set of prediction entries.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for prediction schema in `tests/contract/test_prediction_schema.py`
- [X] T012 [P] [US1] Integration test for CPU inference loop in `tests/integration/test_cpu_inference.py`
- [X] T013 [P] [US1] Unit test for config sample limits in `tests/unit/test_config_limits.py`

### Implementation for User Story 1

- [X] T014 [US1] Implement dataset fetcher in `src/neo_ov/dataset_fetcher.py` to download MMBench samples from `https://huggingface.co/datasets/llm-bench/mmbench` (real URL) with error handling for missing files
- [X] T015 [US1] Implement `src/neo_ov/inference.py` to load model weights from submodule without CUDA/GPU dependencies, using `device="cpu"`
- [X] T016 [US1] Implement `src/scripts/run_smoke_test.py` to execute inference on 5 samples and write `outputs/predictions/smoke_test_results.json`
- [X] T017 [US1] Add validation logic to `src/neo_ov/utils.py` to verify non-empty predictions and finite scores
- [X] T018 [US1] Add explicit logging in `src/neo_ov/inference.py` for missing dependencies (torch, transformers) and CUDA import errors

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Reproduce Benchmark Metrics on a Representative Dataset (Priority: P2)

**Goal**: Validate the model produces competitive/plausible metrics on a medium-sized benchmark subset (500 samples).

**Independent Test**: The system runs `src/scripts/run_validation.py` on 500 samples of MMBench. Success is defined by a report with numeric scores matching the paper's range (±10%) and a valid JSON artifact.

### Tests for User Story 2

- [X] T019 [P] [US2] Contract test for validation report schema in `tests/contract/test_report_schema.py`
- [X] T020 [P] [US2] Integration test for metric calculation pipeline in `tests/integration/test_metric_calculation.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement `src/scripts/run_validation.py` to process 500 samples with a hard cap of 1000, writing `outputs/predictions/validation_results.json`
- [X] T022 [US2] Implement metric calculation in `src/neo_ov/metrics.py` using normalized string matching (lowercase, no punctuation, collapsed whitespace)
- [X] T023 [US2] Implement Wilson score interval calculation in `src/neo_ov/metrics.py` for 95% confidence intervals on accuracy
- [X] T024 [US2] Implement `src/scripts/generate_report.py` to compile metrics, format as Markdown, and save to `outputs/reports/validation_report.md`
- [X] T025 [US2] Add logic to `src/neo_ov/inference.py` to handle dataset preprocessing on CPU, skipping GPU-only preprocessing paths with warnings
- [X] T026 [US2] Add checkpointing logic to `src/scripts/run_validation.py` to handle 6-hour timeout and log "truncated due to time limit" if necessary

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Document Methodological Constraints and Scaling Limitations (Priority: P3)

**Goal**: Explicitly address the reviewer's critique regarding "at Scale" by documenting the absence of scaling law analysis.

**Independent Test**: The final validation report includes a dedicated section stating that no scaling exponents were computed and defining "Scale" as architectural size only.

### Tests for User Story 3

- [X] T027 [P] [US3] Contract test for report content (text search for "scaling law analysis" in negative context) in `tests/contract/test_report_content.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement "Methodological Notes" section generation in `src/scripts/generate_report.py`
- [X] T029 [US3] Add specific text in `src/scripts/generate_report.py` stating: "This validation is limited to functional reproduction on fixed-size models and datasets. No quantitative scaling law analysis (power-law fits, exponents) was performed. The term 'Scale' in the title refers to architectural capacity (parameter count) only."
- [X] T030 [US3] Update `src/neo_ov/config.py` to define "Scale" parameter explicitly as "model architecture scale" and not "data/compute scaling law"
- [X] T031 [US3] Add a task to `tasks.md` (this file) referencing the reviewer's concern: "Address Geoffrey West's critique on 'at Scale' by ensuring the report explicitly denies scaling law analysis"

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Configure GitHub Actions workflow `.github/workflows/ci.yml` to run on free-tier runner (2 CPU, 7 GB RAM) with 6-hour timeout
- [X] T033 [P] Add `README.md` with instructions for running smoke test and validation on CPU
- [X] T034 Code cleanup and refactoring of `src/neo_ov/` modules
- [X] T035 [P] Run `quickstart.md` validation if available
- [X] T036 Security hardening: ensure no hardcoded API keys in `src/scripts/` or `src/neo_ov/`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1's dataset fetcher and inference wrapper
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2's report generation logic

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services
- Services before scripts
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
Task: "Contract test for prediction schema in tests/contract/test_prediction_schema.py"
Task: "Integration test for CPU inference loop in tests/integration/test_cpu_inference.py"

# Launch all models for User Story 1 together:
Task: "Implement dataset fetcher in src/neo_ov/dataset_fetcher.py"
Task: "Implement inference wrapper in src/neo_ov/inference.py"
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
- **Critical Constraint**: All tasks MUST run on free-tier CPU-only CI (2 CPU, 7 GB RAM, no GPU). No 8-bit/4-bit quantization or CUDA-specific kernels.
- **Data Integrity**: All dataset downloads MUST use real, reachable URLs (e.g., HuggingFace, UCI). No synthetic/fake data generation.
- **Reviewer Concern**: Address Geoffrey West's critique by ensuring the report explicitly states "no scaling law analysis performed" (Task T029, T031).
