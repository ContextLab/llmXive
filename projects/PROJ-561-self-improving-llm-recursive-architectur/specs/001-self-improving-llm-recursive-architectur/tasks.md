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

- [ ] T001 Create project structure per implementation plan: Create directories `code/`, `data/raw/`, `data/processed/`, `results/`, `specs/`, `tests/`, `tests/unit/`, `tests/integration/` and initialize `__init__.py` files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004a [P] Implement `utils/memory.py` with graceful RAM watchdog: create `utils/memory.py` with function `check_and_terminate_if_exceeds(limit_gb: float = 7.0)` that logs current RAM usage, writes partial metrics if available, and then calls `sys.exit(1)` if RAM exceeds the limit. This ensures graceful termination with metric preservation, aligning with spec Edge Cases.
- [ ] T004b [P] Implement gradient checkpointing configuration: create `config.py` or `pipeline/model.py` config section that enables `gradient_checkpointing=True` for the GPT-2 124M model to ensure it fits within 7GB RAM with batch size 4.
- [ ] T005a [P] Implement dataset loaders in `pipeline/loader.py` for OpenWebText, GSM8K, ARC-Challenge, Wikitext-2 with Fail-Fast logic (no synthetic fallbacks). **Note**: The specific subset size (e.g., number of samples) MUST be read from `config.py` (key: `TRAIN_SAMPLE_SIZE`) to ensure deterministic loading.
- [ ] T005b [P] Implement exponential backoff wrapper in `pipeline/loader.py` with initial delay=30s, max retries=5, scoped EXCLUSIVELY to HuggingFace API calls (as per FR-011).
- [ ] T006 Implement `pipeline/model.py` with GPT loading with CPU-compatible weight manipulation (DEPENDS ON T005a, T004a, T004b).
- [ ] T013 [P] Define modification proposal JSON schema: Create `schemas/modification_proposal.py` with Pydantic model `ModificationProposal` including fields: modification_type, magnitude, rationale, estimated_param_count.
- [ ] T007 [P] Implement `pipeline/stats.py` with paired bootstrap testing (α=0.05 strict) and exponential decay curve fitting.
- [ ] T008 [P] Create `config.py` with hyperparameters (lr=5e-5, bs=4, seed), constraints (≤30% param increase), and path definitions.
- [ ] T009 [P] Implement `utils/logging.py` for structured cycle logging and checkpointing.
- [ ] T010 [P] Implement `pipeline/evaluator.py` with benchmark runners for GSM8K, ARC-Challenge, and Wikitext-2 ECE.
- [ ] T034 [P] Implement per-cycle timeout enforcement in `pipeline/trainer.py`: add timeout wrapper that terminates cycle if exceeded, logs "Timeout", and records partial metrics (spec Edge Cases).
- [ ] T035 [P] Implement separation of generative and verification logic: Create `pipeline/oracle.py` containing the fixed benchmark suite (GSM8K, ARC-Challenge, Wikitext-2) and metric calculation logic. **Constraint**: This oracle MUST be executed in a **separate subprocess** via `subprocess.run()` from the main pipeline to ensure physical isolation. The main process (generative logic) must NOT have direct import access to `pipeline/oracle.py` functions; data exchange must occur via JSON files or stdin/stdout. This addresses Constitution Principle VII and ensures the evaluation logic cannot be influenced by the generative logic.
- [ ] T036 [P] Implement "Distinct Modification" history tracker: Create `utils/history.py` with a list-based tracker to store applied modifications. **Requirement**: Implement `is_distinct(new_proposal: ModificationProposal) -> bool` which returns False if `new_proposal.modification_type` AND `new_proposal.magnitude` match any entry in the history. **Implementation Detail**: Serialize the comparison keys as `json.dumps({"type": new_proposal.modification_type, "magnitude": new_proposal.magnitude}, sort_keys=True)` to ensure deterministic hashing. This directly implements the spec's "distinct in type or magnitude" requirement (FR-002).
- [ ] T029 [P] Implement results/trajectory.json schema and writer: Create `results/trajectory_schema.py` with Pydantic model `TrajectoryEntry` and writer function `write_trajectory(entries: list, status: str)`. **Constraint**: This function MUST be callable at any point to write a valid JSON file, even if the pipeline terminates early (e.g., US-1 timeout or degradation), ensuring the artifact exists.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute single refinement cycle with baseline comparison (Priority: P1) 🎯 MVP

**Goal**: Download GPT 124M, apply one architectural modification, re-train on OpenWebText subset, and evaluate on multiple benchmarks with statistical comparison.

**Independent Test**: Execute pipeline once, verify metrics recorded in `results/trajectory.json` and `data/` artifacts, and confirm CPU-only execution completes within 2 hours.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Unit test for memory watchdog in `tests/unit/test_memory.py`
- [X] T012 [P] [US1] Unit test for bootstrap significance logic in `tests/unit/test_stats.py`
- [ ] T014 [P] [US1] Integration test for full single cycle in `tests/integration/test_single_cycle.py`

### Implementation for User Story 1

- [ ] T015a [P] [US1] Implement `pipeline/model.py` method to run model inference for self-prompted architectural modification proposal: Run model inference using the following inline prompt template: "You are a research assistant. Suggest ONE architectural modification for a GPT-2 124M model to improve reasoning. Output ONLY a JSON object with keys: 'modification_type' (one of: 'add_layer', 'remove_layer', 'increase_hidden', 'decrease_hidden', 'change_heads'), 'magnitude' (integer), and 'rationale' (string). Ensure the change keeps total params ≤ 130% of original."
- [ ] T015b [P] [US1] Implement `pipeline/model.py` method to parse JSON proposal: Extract JSON using regex or JSON block parsing from the model output.
- [ ] T015c [P] [US1] Implement `pipeline/model.py` method to validate parameter count: Validate parameter count ≤130% baseline using the schema from T013.
- [ ] T016 [US1] Implement `pipeline/model.py` method to apply architectural modification (specific types: layer count, head count, hidden size) to GPT 124M weights: Use manual reconstruction. **Algorithm**: Copy existing weights; initialize new dimensions with Kaiming uniform; truncate excess weights if shrinking; ensure deterministic initialization with fixed seed.
- [ ] T017a [US1] Implement training loop in `pipeline/trainer.py::train_epoch` for a single training epoch on an OpenWebText subset (AdamW, bs=4, lr=5e-5) with gradient checkpointing enabled (configuration provided by T004b) and CPU offloading.
- [ ] T017b [US1] Implement FLOP counter in `pipeline/trainer.py::count_flops` for accurate FLOP measurement during training.
- [ ] T018 [US1] Implement `pipeline/evaluator.py` logic to compute GSM8K accuracy, ARC-Challenge accuracy, and Wikitext-2 ECE.
- [ ] T019 [US1] Implement `pipeline/stats.py` logic to run paired bootstrap comparison (baseline vs. post-mod) and output p-values.
- [ ] T020 [US1] Implement `main.py::run_single_cycle()` orchestrating: load_model() → propose_modification() → validate_modification() → apply_modification() → train_epoch() → evaluate() → compare_stats().
- [ ] T022 [US1] Implement early-stop logic: if degradation ≥5% from baseline, **immediately** call `write_trajectory()` from T029 with status "Early Stop - Degradation" and the current cycle data, then terminate the process. **Constraint**: Do NOT attempt to complete cycle setup or training if degradation is detected; save state first, then exit.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute three refinement cycles with performance trajectory tracking (Priority: P2)

**Goal**: Iterate refinement times, recording metrics to detect trajectory (improvement/plateau/degradation) and fit decay model.

**Independent Test**: Execute pipeline for consecutive cycles, verify `results/trajectory.json` contains time-series data and decay model fit results.

**Note**: This phase is a conditional "Scaling Study". Execution of these tasks depends on the successful completion of US-1 within the 1.5-hour time budget.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T023 [P] [US2] Integration test for 3-cycle loop in `tests/integration/test_three_cycles.py`
- [X] T024 [P] [US2] Unit test for decay model fitting in `tests/unit/test_decay_model.py`

### Implementation for User Story 2

- [ ] T029 [P] [US2] Implement results/trajectory.json schema and writer: Create `results/trajectory_schema.py` with Pydantic model `TrajectoryEntry` and writer function `write_trajectory(entries: list, status: str)`. **Constraint**: This function MUST be callable at any point to write a valid JSON file, even if the pipeline terminates early (e.g., US-1 timeout or degradation), ensuring the artifact exists.
- [ ] T025 [US2] Implement `main.py` loop logic to execute multiple cycles (ONLY if US-1 completed within time budget). Ensure each cycle's modification is distinct in type or magnitude from all previous cycles by calling `is_distinct()` from T036 before application (DEPENDS ON T013, T029, T036). **Note**: This logic is conditional on US-1 success. Use an in-memory set of serialized modification signatures (from T036) stored in `main.py` state to track history.
- [ ] T026 [US2] Implement `pipeline/model.py` logic to track and enforce "distinct modification" constraint across cycles using schema from T013 and trajectory from T029 (DEPENDS ON T013, T029, T036).
- [ ] T027 [US2] Implement `pipeline/stats.py` logic to fit exponential decay model (y = a * e^(-bx) + c) using `scipy.optimize.curve_fit` with initial guesses `[1.0, 0.1, 0.0]` and report the cycle number where performance first plateaus (≤1% improvement) or degrades (≥1% drop). Output format: `{"plateau_cycle": int}`.
- [ ] T028 [US2] Implement `main.py` retry logic: retry failed training up to 2 times; if still failing, log failure, increment cycle counter, proceed with new modification.
- [ ] T031 [US2] Implement `pipeline/stats.py` logic to compute performance-per-FLOP and performance-per-hour metrics for *each cycle* and *compare across cycles* to identify diminishing returns (SC-004). This task consumes FLOP data from T017b.
- [ ] T052 [US2] Implement timeout/incomplete reporting: Create logic in `main.py` to handle the case where the total runtime exceeds the predefined duration limit or a cycle exceeds the 1.5-hour limit. Log "Incomplete - Timeout", record partial metrics in `results/trajectory.json` using T029, and exit gracefully.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (conditional on US-1 success)

---

## Phase 5: User Story 3 - Generate resource-performance trade-off analysis (Priority: P3)

**Goal**: Compute cost-effectiveness metrics (performance per FLOP, performance per hour) and verify total runtime ≤6 hours, RAM ≤7GB.

**Independent Test**: Compute trade-off ratios from `results/trajectory.json` and verify execution constraints are met.

### Implementation for User Story 3

- [ ] T032 [US3] Implement `main.py` resource monitoring to log peak RAM and total wall-clock time; implement graceful logging and early termination if total runtime exceeds a predefined threshold (log "Timeout", record partial metrics, exit gracefully) instead of hard assertion (spec Edge Cases).
- [ ] T033 [US3] Generate `results/trade_off_analysis.json`: Read `results/trajectory.json`, compute performance-per-FLOP and performance-per-hour metrics (as defined in SC-004) for each cycle, and write the results to `results/trade_off_analysis.json`. This task directly implements the computation required by SC-004.

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
- Phase 6 (Research Review Compliance) has been removed as it was scope creep.

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
- **Removed**: Phase 6 (T035-T041) entirely to eliminate scope creep and unlinked reviewer logic.
- **Removed**: T040-T051 as they were unexecutable scope creep (philosophical concepts without FRs).
- **Removed**: T036 (Code cleanup), T037 (Performance optimization), T038 (Additional unit tests) as they were non-executable without specific targets.
- **Moved**: T034 (per-cycle timeout) moved from Phase 7 to Phase 2 (Foundational).
- **Split**: T005 split into T005a (loaders) and T005b (backoff); T017 split into T017a (training) and T017b (FLOPs); T004 split into T004a (Watchdog) and T004b (Checkpointing); T015 split into T015a (Inference), T015b (Parsing), and T015c (Validation).
- **Enhanced**: T025 now explicitly includes tracking and validation logic for modification distinctness (direct field comparison).
- **Fixed**: T032 now implements graceful logging and termination instead of hard assertion.
- **Reordered**: T029 (schema) now appears before T025/T026 in Phase 4.
- **Fixed**: T004 now enforces fixed batch size 4 per FR-004 and removes auto-scaling, but ADDS gradient checkpointing config.
- **Removed**: T021 (duplicate exponential backoff) and T030 (ambiguous FLOP logic).
- **Fixed**: T006 [P] tag removed as it depends on T005a, T004a, T004b.
- **Added**: T052 for timeout/incomplete reporting path.
- **Clarified**: T015 and T016 now include specific prompt template reference and weight initialization algorithms.
- **Fixed**: T022 now calls `write_trajectory()` before exit.
- **Fixed**: T035 now specifies benchmark suite and subprocess isolation.
- **Fixed**: T036 now specifies field comparison (type/magnitude only).
- **Fixed**: T025 now specifies data structure (in-memory set).
- **Fixed**: T027 now specifies library and output format.
- **Cleaned**: Notes section removed contradictory "Added T040-T051" statements.