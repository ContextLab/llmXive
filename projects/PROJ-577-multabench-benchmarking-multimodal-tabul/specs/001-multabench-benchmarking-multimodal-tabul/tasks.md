# Tasks: MulTaBench: Benchmarking Multimodal Tabular Learning with Text and Image

**Input**: Design documents from `/specs/577-multabench-reproduction/`
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

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python project with virtual environment and dependencies (torch[cpu], transformers, scikit-learn, pandas, numpy, lightgbm, datasets)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: User Story 1 - Validate Environment Setup and Data Availability (Priority: P1) 🎯 MVP

**Goal**: Verify vendored codebase initialization, dependency installation, and dataset registry accessibility without full downloads.

**Independent Test**: Execute initialization script and run metadata listing command that outputs dataset names/types without downloading binary files.

**⚠️ TDD Flow**: Write tests (T010-T011) FIRST. Verify they FAIL. Then implement (T012-T016).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [US1] Contract test for registry listing in `tests/unit/test_registry_listing.py` (Verify JSON output format)
- [X] T011 [US1] Integration test for environment initialization in `tests/integration/test_env_init.py` (Verify `init.sh` runs without error)

### Implementation for User Story 1

- [X] T012 [US1] Modify `external/MulTaBench/src/multabench/datasets/registry.py` (or equivalent existing file) to expose `list_datasets()` function that returns list of dicts. **Success Criteria**: Running `python -m multabench.datasets.registry --list` exits with code 0 and prints valid JSON.
- [X] T013 [US1] Implement `init.sh` or Python equivalent in `external/MulTaBench/scripts/init.py` to install dependencies and verify `pip install` success.
- [X] T014 [US1] Integrate registry query with initialization script to verify `BIN_TEXT_FAKE_JOB_POSTING` and `MUL_IMAGE_CBIS_DDSM` exist. **Success Criteria**: Script exits 0 and logs "Dataset [ID] found" for both IDs.
- [X] T015 [US1] Add validation to abort run with fatal error if required dataset IDs are missing from registry.
- [X] T016 [US1] Add logging for successful environment setup and dataset availability.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Execute Reduced-Scale Reproduction Run (Priority: P2)

**Goal**: Execute benchmarking pipeline on a subset (2 datasets, 2 models) to validate end-to-end logic, CPU compatibility, and output artifact generation within 2 hours.

**Independent Test**: Run `benchmark.py` with subset config, verify completion without GPU errors, and confirm `results_subset.csv` contains valid numeric metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for result schema in `tests/unit/test_result_schema.py`
- [X] T019 [P] [US2] Integration test for reduced-scale run in `tests/integration/test_reduced_run.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Modify `external/MulTaBench/src/multabench/config.py` to set default `DEVICE='cpu'` and `BATCH_SIZE=8`.
- [X] T021 [P] [US2] Modify `external/MulTaBench/src/multabench/datasets/config_loader.py` to load subset configuration from `external/MulTaBench/configs/config_subset.yaml`.
- [X] T022 [P] [US2] Modify `external/MulTaBench/src/multabench/datasets/device_manager.py` to enforce CPU-only execution and handle device fallback.
- [X] T023 [P] [US2] Modify `external/MulTaBench/src/multabench/datasets/error_handler.py` to catch `MemoryError` and reduce `batch_size` by half before retry.
- [X] T024 [P] [US2] Modify `external/MulTaBench/src/multabench/datasets/error_handler.py` to catch `DownloadError` and log "Skipping dataset [ID] due to download error".
- [X] T025 [P] [US2] Modify `external/MulTaBench/src/multabench/datasets/metric_validator.py` to ensure metrics (accuracy/AUC) are in [0, 1] before writing. **Configuration Requirement**: The subset run MUST include both `--mode frozen` and `--mode tuned` for selected datasets.
- [X] T026 [P] [US2] Modify `external/MulTaBench/src/multabench/benchmark.py` to accept `--config` argument and load `config_subset.yaml`.
- [X] T027 [P] [US2] Modify `external/MulTaBench/src/multabench/benchmark.py` to generate `multabench/leaderboard/data/results_subset.csv` with columns: `dataset_id`, `model_id`, `accuracy`, `auc`, `mse` and validate numeric ranges. **Validation Logic**: Verify that `results_subset.csv` contains paired rows (same dataset/model ID, different mode) before proceeding to directional consistency check.
 - [X] T028 [P] [US3] Modify `external/MulTaBench/src/multabench/benchmark.py` to perform the paired-row validation on `results_subset.csv` prior to running the directional consistency check (T031).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Compare Reproduction Metrics Against Paper Claims (Priority: P3)

**Goal**: Compare generated metrics against paper claims (tuned > frozen) to validate the scientific hypothesis on the subset.

**Independent Test**: Calculate delta between frozen and tuned baselines and verify direction of effect matches paper abstract.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Contract test for directional consistency in `tests/unit/test_directional_consistency.py`
- [X] T029 [P] [US3] Integration test for paper claim validation in `tests/integration/test_paper_validation.py`

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement results parser in `external/MulTaBench/src/multabench/utils.py` (or existing file) to load `results_subset.csv`.
- [X] T031 [US3] Implement directional consistency checker in `external/MulTaBench/src/multabench/benchmark.py` (or existing file) to compare tuned vs. frozen metrics. **Logic**: If `tuned_metric > frozen_metric`, pass. If count < 2, flag as "inconclusive". **Constraint**: Do NOT create new files; modify existing vendor files only.
- [X] T032 [US3] Generate validation report `multabench/leaderboard/data/claim_validation_report.md` indicating pass/fail and delta values.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates in `external/MulTaBench/README.md` regarding CPU-only execution and subset configuration (Add section "Running on CPU").
- [X] T036 [P] Code cleanup: Add type hints to `benchmark.py` and `loader.py` in `external/MulTaBench/src/multabench/`.
- [X] T037 [P] Performance optimization: Add simple LRU cache to dataset loading in `external/MulTaBench/src/multabench/datasets/loader.py` to prevent redundant downloads.
- [X] T038 [P] Additional unit tests for edge cases (empty results, invalid metric ranges) in `tests/unit/`.
- [X] T039 [P] Verify error handling: Run `benchmark.py` with a fake dataset ID to ensure `external/MulTaBench/src/multabench/datasets/loader.py` logs "Skipping dataset [ID] due to download error" and continues.
- [X] T040 Run quickstart.md validation and ensure all scripts are executable.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **User Story 1 (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 2 (Phase 3)**: Depends on Setup completion - May integrate with US1 but should be independently testable
- **User Story 3 (Phase 4)**: Depends on US2 results generation
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Setup - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Setup - Depends on US2 results generation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All User Story tasks marked [P] can run in parallel (within their phases)
- Once Setup phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for registry listing in tests/unit/test_registry_listing.py"
Task: "Integration test for environment initialization in tests/integration/test_env_init.py"

# Launch all models for User Story 1 together:
Task: "Implement init script in external/MulTaBench/scripts/init.py"
Task: "Implement dataset registry query in external/MulTaBench/src/multabench/datasets/registry.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: User Story 1
3. **STOP and VALIDATE**: Test User Story 1 independently
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together
2. Once Setup is done:
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
- **Critical Constraint**: All tasks must run on CPU-only CI (vCPU, 7GB RAM, no GPU). No 8-bit quantization or CUDA-specific device maps allowed.
- **Constraint**: Do NOT create new source files in `external/MulTaBench`. Modify existing files only.
- **Correction**: T023 and T007 use `MUL_IMAGE_CBIS_DDSM` (not CIFAR10) per spec.md US2.
- **Correction**: T027 validates metrics via CSV (not internal `requires_grad` hooks).
- **Correction**: T039 verifies error logging (not security hardening).
- **Note**: Plan.md references `MUL_IMAGE_CIFAR10` which contradicts spec.md; tasks.md follows spec.md. Plan.md requires update.
- **Note**: Plan.md references `requires_grad` check which contradicts spec.md; tasks.md follows spec.md (metric comparison only). Plan.md requires update.
- **Note**: T037 removed arbitrary [deferred] metric; task is now functional (implement caching).
