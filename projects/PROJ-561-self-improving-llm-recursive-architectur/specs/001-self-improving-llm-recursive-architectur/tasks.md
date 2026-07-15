# Tasks: Self-improving LLM: recursive architecture refinement and re‑training

**Input**: Design documents from `/specs/001-self-improving-llm-recursive-architectur/`
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

- [ ] T001 Create project structure per implementation plan: Create directories `code/`, `data/raw/`, `data/processed/`, `results/`, `specs/`, `tests/`, `tests/unit/`, `tests/integration/` and initialize `__init__.py` files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `utils/memory.py` with gradient checkpointing, batch size auto-scaling (low-to-moderate range) and hard RAM watchdog: create `utils/memory.py` with function `check_and_terminate_if_exceeds(limit_gb: float)` that kills process if RAM exceeds limit
- [ ] T005a [P] Implement dataset loaders in `pipeline/loader.py` for OpenWebText, GSM8K, ARC-Challenge, Wikitext-2 with Fail-Fast logic (no synthetic fallbacks)
- [ ] T005b [P] Implement exponential backoff wrapper in `pipeline/loader.py` with initial delay=30s, max retries=5 for HuggingFace API calls
- [ ] T006 [P] Implement `pipeline/model.py` with GPT loading with a medium-sized parameter configuration and CPU-compatible weight manipulation (DEPENDS ON T005a)
- [ ] T013 [P] Define modification proposal JSON schema: Create `schemas/modification_proposal.py` with Pydantic model `ModificationProposal` including fields: modification_type, magnitude, rationale, estimated_param_count
- [~] T007 [P] Implement `pipeline/stats.py` with paired bootstrap testing (α=0.05 strict) and exponential decay curve fitting
- [~] T008 [P] Create `config.py` with hyperparameters (lr=5e-5, bs=4, seed), constraints (≤30% param increase), and path definitions
- [~] T009 [P] Implement `utils/logging.py` for structured cycle logging and checkpointing
- [~] T010 [P] Implement `pipeline/evaluator.py` with benchmark runners for GSM8K, ARC-Challenge, and Wikitext-2 ECE
- [~] T034 [P] Implement per-cycle timeout enforcement in `pipeline/trainer.py`: add timeout wrapper that terminates cycle if exceeded, logs "Timeout", and records partial metrics (spec Edge Cases)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute single refinement cycle with baseline comparison (Priority: P1) 🎯 MVP

**Goal**: Download GPT 124M, apply one architectural modification, re-train on OpenWebText subset, and evaluate on multiple benchmarks with statistical comparison.

**Independent Test**: Execute pipeline once, verify metrics recorded in `results/trajectory.json` and `data/` artifacts, and confirm CPU-only execution completes within 2 hours.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Unit test for memory watchdog in `tests/unit/test_memory.py`
- [X] T012 [P] [US1] Unit test for bootstrap significance logic in `tests/unit/test_stats.py`
- [~] T014 [P] [US1] Integration test for full single cycle in `tests/integration/test_single_cycle.py`

### Implementation for User Story 1

- [~] T015 [US1] Implement `pipeline/model.py` method to parse model's self-prompted architectural modification proposal (using schema from T013) and validate parameter count ≤130% baseline <!-- ATOMIZE: requested -->
- [~] T016 [US1] Implement `pipeline/model.py` method to apply architectural modification (e.g., layer addition, head count change) to GPT 124M weights using manual reconstruction and standard initialization (NO layer injection APIs)
- [~] T017a [US1] Implement training loop in `pipeline/trainer.py::train_epoch` for a single training epoch on an OpenWebText subset (AdamW, bs=4, lr=5e-5) with CPU offloading
- [~] T017b [US1] Implement FLOP counter in `pipeline/trainer.py::count_flops` for accurate FLOP measurement during training
- [ ] T018 [US1] Implement `pipeline/evaluator.py` logic to compute GSM8K accuracy, ARC-Challenge accuracy, and Wikitext-2 ECE
- [ ] T019 [US1] Implement `pipeline/stats.py` logic to run paired bootstrap comparison (baseline vs. post-mod) and output p-values
- [ ] T020 [US1] Implement `main.py::run_single_cycle()` orchestrating: load_model() → propose_modification() → validate_modification() → apply_modification() → train_epoch() → evaluate() → compare_stats()
- [ ] T021 [US1] Implement exponential backoff (initial delay, max retries) for HuggingFace API calls in `pipeline/loader.py`
- [ ] T022 [US1] Implement early-stop logic: if degradation ≥5% from baseline, record degradation cycle, log "Early Stop", and terminate gracefully (spec Edge Cases)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute three refinement cycles with performance trajectory tracking (Priority: P2)

**Goal**: Iterate refinement times, recording metrics to detect trajectory (improvement/plateau/degradation) and fit decay model.

**Independent Test**: Execute pipeline for consecutive cycles, verify `results/trajectory.json` contains time-series data and decay model fit results.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Integration test for 3-cycle loop in `tests/integration/test_three_cycles.py`
- [ ] T024 [P] [US2] Unit test for decay model fitting in `tests/unit/test_decay_model.py`

### Implementation for User Story 2

- [ ] T029 [US2] Implement results/trajectory.json schema and writer: Create `results/trajectory_schema.py` with Pydantic model `TrajectoryEntry` and writer function `write_trajectory()` capturing cycle_number, param_count, GSM8K, ARC, ECE, FLOPs, training_time
- [ ] T025 [US2] Implement `main.py` loop logic to execute multiple cycles, ensuring each cycle's modification is distinct in type or magnitude from all previous cycles by implementing logic to track modification history and validate new proposals against that history before application (DEPENDS ON T013, T029)
- [ ] T026 [US2] Implement `pipeline/model.py` logic to track and enforce "distinct modification" constraint across cycles using schema from T013 and trajectory from T029 (DEPENDS ON T013, T029)
- [ ] T027 [US2] Implement `pipeline/stats.py` logic to fit exponential decay model (y = a * e^(-bx) + c) and identify plateau/degradation cycle
- [ ] T028 [US2] Implement `main.py` retry logic: retry failed training up to 2 times; if still failing, log failure, increment cycle counter, proceed with new modification
- [ ] T030 [US2] Implement logic to compute and record FLOPs for each cycle in `pipeline/model.py` (Note: FLOP counting logic is in T017b, this task focuses on trajectory aggregation)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate resource-performance trade-off analysis (Priority: P3)

**Goal**: Compute cost-effectiveness metrics (performance per FLOP, performance per hour) and verify total runtime ≤6 hours, RAM ≤7GB.

**Independent Test**: Compute trade-off ratios from `results/trajectory.json` and verify execution constraints are met.

### Implementation for User Story 3

- [ ] T031 [US3] Implement `pipeline/stats.py` logic to compute performance-per-FLOP and performance-per-hour metrics for *each cycle* and *compare across cycles* to identify diminishing returns (SC-004)
- [ ] T032 [US3] Implement `main.py` resource monitoring to log peak RAM and total wall-clock time; implement graceful logging and early termination if total runtime exceeds a predefined threshold (log "Timeout", record partial metrics, exit gracefully) instead of hard assertion (spec Edge Cases)
- [ ] T033 [US3] Generate `results/trade_off_analysis.json` with computed metrics and comparison across cycles

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Time & Safety Logic (Consolidated)

**Purpose**: Implement critical timeout and safety logic mandated by spec Edge Cases.

*Note: T034 (per-cycle timeout) has been moved to Phase 2 (Foundational) to ensure it is active during core loop execution.*

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates: Update `README.md` with installation steps and `docs/rationale.md` with project rationale (aligned with SC-003)
- [ ] T039 Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - US1 (P1) is the MVP and must be verified before US2/US3
 - US2 (P2) depends on US1 components
 - US3 (P3) depends on US1 and US2 data
- **Time & Safety (Phase 7)**: Consolidated; T034 moved to Phase 2
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 components
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
- **CRITICAL**: No task may use GPU, quantization, or synthetic data. All tasks must run on CPU-only free-tier CI.
- **Removed**: Phase 6 (Reviewer Concerns) was removed as it contained unapproved scope creep not defined in spec.md.
- **Removed**: T036 (Code cleanup), T037 (Performance optimization), T038 (Additional unit tests) were removed as they were non-executable without specific targets.
- **Moved**: T034 (per-cycle timeout) moved from Phase 7 to Phase 2 (Foundational).
- **Split**: T005 split into T005a (loaders) and T005b (backoff); T017 split into T017a (training) and T017b (FLOPs).
- **Enhanced**: T025 now explicitly includes tracking and validation logic for modification distinctness.
- **Fixed**: T032 now implements graceful logging and termination instead of hard assertion.
- **Reordered**: T029 (schema) now appears before T026 (usage) in Phase 4.