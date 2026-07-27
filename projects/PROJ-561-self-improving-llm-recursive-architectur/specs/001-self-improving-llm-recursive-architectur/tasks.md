# Tasks: Self-improving LLM: recursive architecture refinement and re‑training

**Input**: Design documents from `/specs/001-self-improving-llm-recursive-architectur/`
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

- [ ] T001 [P] Create project structure per implementation plan: Create directories `code/`, `data/raw/`, `data/processed/`, `results/`, `specs/`, `tests/`, `tests/unit/`, `tests/integration/` and initialize `__init__.py` files. **Verification**: Verify existence of all directories and `__init__.py` files via file system check.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `utils/memory.py` with gradient checkpointing, batch size auto-scaling (low-to-moderate range) and hard RAM watchdog: create `utils/memory.py` with function `check_and_terminate_if_exceeds(limit_gb: float)` that kills process if RAM exceeds limit. **Verification**: Add a unit test in `tests/unit/test_memory.py` that mocks `psutil.virtual_memory` using `unittest.mock.patch` to return a value > limit and asserts `sys.exit` is called.
- [ ] T005b [P] Implement exponential backoff wrapper in `pipeline/loader.py` with initial delay=30s, max retries=5 for HuggingFace API calls.
- [ ] T005a [P] Implement dataset loaders in `pipeline/loader.py` for OpenWebText, GSM8K, ARC-Challenge, Wikitext-2 with Fail-Fast logic: **Logic**: For transient network errors, use T005b (backoff); for missing data files, raise `FileNotFoundError` immediately (no synthetic fallback). **Verification**: Verify that loading a non-existent dataset raises `FileNotFoundError` and does NOT fallback to synthetic data. (DEPENDS ON T005b)
- [ ] T006 [P] Implement `pipeline/model.py` with GPT checkpoint loading and CPU-compatible weight manipulation (DEPENDS ON T005a)
- [ ] T013 [P] Define modification proposal JSON schema: Create `schemas/modification_proposal.py` with Pydantic model `ModificationProposal` including fields: modification_type, magnitude, rationale, estimated_param_count. **Verification**: Validate that the schema correctly rejects invalid JSON inputs.
- [ ] T013b [P] Implement persistent state store: Create `utils/state_store.py` with functions `load_state()`, `save_state()`, `update_retry_count(mod_id)`, `update_mod_history(mod_id)`, `update_degradation_flag()`. State MUST be persisted to `results/state.json` to survive process restarts. **Verification**: Write a unit test using `subprocess.run` to spawn a worker process, modify state, force termination via `os.kill(pid, signal.SIGKILL)`, restart a new subprocess, and verify state is recovered.
- [ ] T014 [P] Implement distinctness validation logic in `pipeline/model.py`: Create function `validate_modification_distinctness(proposal: ModificationProposal, history: List[ModificationProposal])` that returns True if proposal is distinct in type or magnitude from all items in history, False otherwise. (DEPENDS ON T013)
- [ ] T007 [P] Implement `pipeline/stats.py` with paired bootstrap testing (α=0.05 strict) and exponential decay curve fitting
- [ ] T008 [P] Create `config.py` with hyperparameters (lr=5e-5, bs=4, seed), constraints (≤30% param increase), and path definitions
- [ ] T009 [P] Implement `utils/logging.py` for structured cycle logging and checkpointing
- [ ] T010 [P] Implement `pipeline/evaluator.py` with benchmark runners for GSM8K, ARC-Challenge, and Wikitext-2 ECE
- [ ] T034 [P] Implement per-cycle timeout enforcement in `pipeline/trainer.py`: add timeout wrapper that terminates cycle if exceeded, logs "Timeout" to `results/logs/cycle_N.log`, and records partial metrics to `results/trajectory.json` (spec Edge Cases). **Verification**: Add integration test using `subprocess.run(timeout=...)` to simulate timeout and verify log file creation.
- [ ] T037 [P] Implement "Separation of Generative/Verification Logic" in `main.py`: Ensure the modification proposal prompt explicitly excludes any access to benchmark results or evaluation metrics, using only training loss and internal weights as the basis for the proposal (Addressing spec Edge Cases on logic separation). (DEPENDS ON T010)
- [ ] T050 [P] Document exception to FR-004 (fixed batch size): Create `docs/exception_log.md` to explicitly document the "Graceful Degradation" strategy (dynamic batch size reduction) required by the GB RAM constraint, distinguishing it from the strict "Fail-Fast" policy for data. **Verification**: Verify the document exists and explicitly references the storage constraint and the specific batch size reduction logic. (DEPENDS ON T004, T032)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute single refinement cycle with baseline comparison (Priority: P1) 🎯 MVP

**Goal**: Download a GPT model of moderate scale, apply one architectural modification, re-train on OpenWebText subset, and evaluate on multiple benchmarks with statistical comparison.

**Independent Test**: Execute pipeline once, verify metrics recorded in `results/trajectory.json` and `data/` artifacts, and confirm CPU-only execution completes within 2 hours.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Unit test for memory watchdog in `tests/unit/test_memory.py`
- [X] T012 [P] [US1] Unit test for bootstrap significance logic in `tests/unit/test_stats.py`
- [X] T014b [P] [US1] Unit test for distinctness validation in `tests/unit/test_model.py`
- [X] T015 [P] [US1] Integration test for full single cycle in `tests/integration/test_single_cycle.py`

### Implementation for User Story 1

- [ ] T015 [US1] Implement `pipeline/model.py` method to parse model's self-prompted architectural modification proposal (using schema from T013) and validate parameter count ≤130% baseline. **Prompt Template**: Create `templates/modification_proposal.j2` containing the exact prompt string. **Logic**: Limit prompt attempts to a reasonable number per cycle; if still invalid after the maximum allowed attempts, fail the cycle. Training retries (up to 2) are handled by T044. **Verification**: Verify `templates/modification_proposal.j2` renders valid JSON for a mock input using a hardcoded mock dict in `tests/integration/test_model.py`. (DEPENDS ON T013, T006, T013b, T037)
- [ ] T016 [US1] Implement `pipeline/model.py` method to apply architectural modification (e.g., layer addition, head count change) to GPT 124M weights using manual reconstruction: create new `nn.Module` subclass, map weights via state_dict, initialize new layers with `torch.nn.init.xavier_uniform_`. Allowed modifications: layer_add (add N layers), head_count_change (change heads by M). (DEPENDS ON T013)
- [ ] T017a [US1] Implement training loop in `pipeline/trainer.py::train_epoch` for a single training epoch on an OpenWebText subset (AdamW, bs=4, lr=5e-5) with CPU offloading. Use gradient accumulation steps=4 to simulate batch. Checkpoint periodically. (DEPENDS ON T008)
- [ ] T032 [US1] Implement `pipeline/memory.py` dynamic batch size reduction: If RAM > 6.5GB during training, halve batch size and restart epoch. If batch size < 1, terminate and log "OOM". Explicitly verify GB limit is respected; if not, terminate (SC-005 enforcement). **Verification**: Unit test mocking `utils.memory.get_ram_usage` to return > 6.5GB to trigger reduction logic. (DEPENDS ON T004, T017a, T049)
- [ ] T017b [US1] Implement FLOP counter in `pipeline/trainer.py::count_flops` for accurate FLOP measurement during training
- [ ] T018 [US1] Implement `pipeline/evaluator.py` logic to compute GSM8K accuracy, ARC-Challenge accuracy, and Wikitext-2 ECE
- [ ] T019 [US1] Implement `pipeline/stats.py` logic to run paired bootstrap comparison (baseline vs. post-mod) and output p-values (DEPENDS ON T007)
- [ ] T044 [US1] Implement retry logic for training failures in `main.py`: retry failed training up to 2 times with the SAME modification; if still failing, log failure, increment cycle counter, and proceed to next cycle number with a NEW modification proposal. **State Persistence**: Use `utils/state_store.py` (T013b) to persist retry counts to `results/state.json` so they survive restarts. **Note**: This implements the training retry logic from spec Edge Cases, distinct from T005b (API backoff). (DEPENDS ON T013b, T009)
- [ ] T036 [US1] Implement early-stop logic in `main.py`: if degradation ≥5% from baseline, record degradation cycle, log "Early Stop", increment cycle counter, and terminate gracefully. **State Persistence**: Persist 'degradation_cycle' and 'early_stop' flag to `utils/state_store.py` (T013b) to survive restarts. Save checkpoint to `data/checkpoints/cycle_N.pt` before termination (spec Edge Cases). (DEPENDS ON T013b, T009)
- [ ] T051 [US1] Implement integration test for timeout logic in `tests/integration/test_timeout.py`: Use `subprocess.run` with a hard timeout to verify that the system logs "Timeout" and records partial metrics when a cycle exceeds the time budget. (DEPENDS ON T034)
- [ ] T020 [US1] Implement `main.py::run_single_cycle()` orchestrating: load_model() → propose_modification() → validate_modification() (using T014) → apply_modification() → train_epoch() → evaluate() → compare_stats(). **Integration**: Must import and invoke T044 (retry), T036 (early-stop), and T037 (validation) logic. **Verification**: Add integration test `tests/integration/test_single_cycle.py` that runs the full flow and asserts `results/trajectory.json` contains at least one entry. (DEPENDS ON T013, T014, T008, T007, T010, T017a, T018, T019, T044, T036, T037, T032, T050)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute three refinement cycles with performance trajectory tracking (Priority: P2)

**Goal**: Iterate refinement times, recording metrics to detect trajectory (improvement/plateau/degradation) and fit decay model.

**Independent Test**: Execute pipeline for consecutive cycles, verify `results/trajectory.json` contains time-series data and decay model fit results.

**Note**: This phase is a conditional "Scaling Study". Execution of these tasks depends on the successful completion of US-1 within the 1.5-hour time budget.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Integration test for 3-cycle loop in `tests/integration/test_three_cycles.py`
- [X] T024 [P] [US2] Unit test for decay model fitting in `tests/unit/test_decay_model.py`

### Implementation for User Story 2

- [ ] T027 [US2] Implement `pipeline/stats.py` logic to fit exponential decay model (y = a * e^(-bx) + c) and identify plateau/degradation cycle. **Output**: Must write the identified `plateau_cycle` and `degradation_cycle` to `results/decay_summary.json` and update `results/trajectory.json`. (DEPENDS ON T007)
- [ ] T029 [US2] Implement results/trajectory.json schema and writer: Create `results/trajectory_schema.py` with Pydantic model `TrajectoryEntry` and writer function `write_trajectory()` capturing cycle_number, param_count, GSM8K, ARC, ECE, FLOPs, training_time. **Output Requirement**: Must also include keys `plateau_cycle` and `degradation_cycle` as identified by T027. **Verification**: Run a mock cycle and validate the output file with Pydantic. (DEPENDS ON T013, T014, T027)
- [ ] T026 [US2] Implement `pipeline/model.py` logic to track and enforce "distinct modification" constraint across cycles using schema from T013 and trajectory from T029. (DEPENDS ON T013, T029, T014)
- [ ] T025 [US2] Implement `main.py` loop logic to execute multiple cycles, ensuring each cycle's modification is distinct in type or magnitude from all previous cycles by tracking modification history in `utils/state_store.py` (T013b) and validating new proposals against that history before application. If not distinct, prompt model again. **Integration**: Must import and invoke T044 (retry) and T036 (early-stop) logic from Phase 3. (DEPENDS ON T013, T029, T014, T013b, T020, T044, T036, T026)
- [ ] T028 [US2] Implement `main.py` retry logic for training failures across cycles (reuses T044 logic)
- [ ] T030 [US2] Implement logic to compute and record FLOPs for each cycle in `pipeline/model.py` (Note: FLOP counting logic is in T017b, this task focuses on trajectory aggregation)
- [ ] T046 [US2] Implement "Early Termination on Degradation" in `main.py`: If a cycle results in performance degradation ≥5% from baseline, record the degradation cycle, log "Early Stop", increment cycle counter, and terminate the pipeline (spec Edge Cases). (DEPENDS ON T036, T013b)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (conditional on US-1 success)

---

## Phase 5: User Story 3 - Generate resource-performance trade-off analysis (Priority: P3)

**Goal**: Compute cost-effectiveness metrics (performance per FLOP, performance per hour) and verify total runtime ≤6 hours, RAM ≤7GB.

**Independent Test**: Compute trade-off ratios from `results/trajectory.json` and verify execution constraints are met.

### Implementation for User Story 3

- [ ] T048 [US3] Implement `main.py` resource monitoring to log peak RAM and total wall-clock time; implement graceful logging and early termination if total runtime exceeds a significant duration (log "Timeout", record partial metrics, exit gracefully) instead of hard assertion (spec Edge Cases). (DEPENDS ON T004, T032)
- [ ] T031 [US3] Implement `pipeline/stats.py` logic to compute performance-per-FLOP and performance-per-hour metrics for *each cycle* and *compare across cycles* to identify diminishing returns. Append results to `results/trade_off_analysis.json` with keys: `cycle`, `perf_per_flop`, `perf_per_hour`. **Verification**: Verify the file contains keys `cycle`, `perf_per_flop`, `perf_per_hour` for each cycle. (DEPENDS ON T030, T048)
- [ ] T033 [US3] Generate `results/trade_off_analysis.json` with computed metrics and comparison across cycles (DEPENDS ON T031)

**Checkpoint**: All user stories should now be independently functional

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - US1 (P1) is the MVP and must be verified before US2/US3
 - US2 (P2) depends on US1 components and is conditional on time budget
 - US3 (P3) depends on US1 and US2 data
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 components. **Conditional**: Only runs if US-1 completes within 1.5 hours.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Integrates with US1/US2 data

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) except T006 which depends on T005a
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for memory watchdog in tests/unit/test_memory.py"
Task: "Unit test for bootstrap significance logic in tests/unit/test_stats.py"
Task: "Unit test for distinctness validation in tests/unit/test_model.py"
Task: "Integration test for full single cycle in tests/integration/test_single_cycle.py"

# Launch all models for User Story 1 together:
Task: "Define modification proposal JSON schema and prompt template"
Task: "Implement pipeline/model.py method to parse model's self-prompted architectural modification proposal"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently. Check time budget.
5. **Conditional**: If US-1 completed < 1.5h, proceed to Phase 4 (US-2). Else, log "Incomplete - Timeout" and stop.
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. **Conditional**: Add User Story 2 → Test independently → Deploy/Demo (only if time budget met)
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2 (conditional)
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
- **CRITICAL**: No task may use GPU, quantization, or synthetic data. All tasks must run on CPU-only free-tier CI.
- **Removed**: Phase 6 (T040-T043) entirely to eliminate scope creep and unlinked reviewer logic.
- **Removed**: T040-T051 as they were unexecutable scope creep (philosophical concepts without FRs).
- **Removed**: T036 (Code cleanup), T037 (Performance optimization), T038 (Additional unit tests) as they were non-executable without specific targets.
- **Moved**: T034 (per-cycle timeout) moved from Phase 7 to Phase 2 (Foundational).
- **Split**: T005 split into T005a (loaders) and T005b (backoff); T017 split into T017a (training) and T017b (FLOPs).
- **Enhanced**: T025 now explicitly includes tracking and validation logic for modification distinctness using persistent state.
- **Fixed**: T032 now implements dynamic batch size reduction in Phase 3 for enforcement, and graceful logging in Phase 5 for total runtime.
- **Reordered**: T027 before T029, T026, T025, T046 in Phase 4.
- **New**: T014 added in Phase 2 for distinctness validation.
- **New**: T013b added in Phase 2 for persistent state store.
- **New**: T044 added in Phase 3 for retry logic with persistent state (renamed from T035).
- **New**: T036 added in Phase 3 for early-stop logic with persistent state.
- **Deleted**: T021 (duplicate backoff) removed.
- **Deleted**: T040-T045 (unapproved scope) removed.
- **Deleted**: T042 (unapproved rollback) removed.
- **Deleted**: Duplicate T032 in Phase 5 removed.
- **New**: T037 added in Phase 2 for Separation of Generative/Verification Logic (Constitution Principle VII).
- **New**: T050 added in Phase 2 for documenting batch size exceptions (Constraint Preservation).
- **Renamed**: Phase 3 T014 (test) to T014b to avoid duplicate ID.
- **Renamed**: Phase 5 T032 (resource monitoring) to T048 to avoid duplicate ID.
- **Renamed**: Phase 3 T035 (retry) to T044.
- **Renamed**: Phase 4 T039 (early stop) to T046.
- **Renamed**: Phase N T035 (docs) to T045.
- **Renamed**: Phase N T039 (validation) to T047.
- **Reordered**: T005b before T005a in Phase 2.
- **Reordered**: T027 before T029, T026, T025, T046 in Phase 4.
- **Reordered**: T048 before T031 in Phase 5.
- **Verified**: T033 depends on T031 and is correctly ordered after T031 in Phase 5.
- **Verified**: T019 depends on T007 and is correctly ordered after T007 in Phase 3.
- **Verified**: T020 depends on T044, T036, T037.
- **Verified**: T025 depends on T020.
- **Verified**: T032 depends on T004, T017a.
- **Verified**: T048 depends on T004, T032.
- **Clarified**: T005a now distinguishes between network errors (retry) and missing data (fail-fast).
- **Clarified**: T015 now limits prompt retries and delegates execution retries to T044.
- **Clarified**: T032, T048, T044, T036, T025 now explicitly depend on T013b for persistence.
- **Clarified**: T027 now outputs explicit plateau/degradation keys.
- **Clarified**: T045 now specifies `make validate-quickstart`.
- **Clarified**: T029 now depends on T027 to ensure schema includes decay results.
- **Clarified**: T031 now depends on T048 for resource data.
- **Clarified**: T050 documents the exception to FR-004 (batch size) to preserve constraint integrity.