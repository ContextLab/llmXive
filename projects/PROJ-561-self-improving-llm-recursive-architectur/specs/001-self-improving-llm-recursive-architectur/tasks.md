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

- [ ] T001 [P] Create project structure per implementation plan: Create directories `code/`, `data/raw/`, `data/processed/`, `results/`, `specs/`, `tests/`, `tests/unit/`, `tests/integration/` and initialize `__init__.py` files. **Verification**: Verify existence of all directories and `__init__.py` files via file system check against `plan.md` structure.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `utils/memory.py` with gradient checkpointing, batch size auto-scaling and hard RAM watchdog: create `utils/memory.py` with function `check_and_terminate_if_exceeds(limit_gb: float)` that loads the RAM limit from `config.py` (default substantial storage capacity) and kills process if RAM exceeds limit (to ensure peak <= 7.0GB). **Verification**: Add a unit test in `tests/unit/test_memory.py` that mocks `psutil.virtual_memory` using `unittest.mock.patch` to return a value > limit and asserts `sys.exit` is called.
- [ ] T005b [P] Implement exponential backoff wrapper in `pipeline/loader.py` with initial delay=30s, max retries=5 for HuggingFace API calls. **Verification**: Add unit test in `tests/unit/test_loader.py` that mocks `time.sleep` and asserts retry count increments correctly on simulated failures, explicitly verifying the initial delay is 30 seconds.
- [ ] T005a [P] Implement dataset loaders in `pipeline/loader.py` for OpenWebText, GSMK, ARC-Challenge, BoolQ with Fail-Fast logic: **Logic**: For transient network errors, use T005b (backoff); for missing data files, raise `FileNotFoundError` immediately (no synthetic fallback). **Verification**: Verify that loading a non-existent dataset `data/raw/non_existent.json` raises `FileNotFoundError` with the message "Dataset file not found: data/raw/non_existent.json" and does NOT fallback to synthetic data. Also verify that simulated network errors trigger retry logic. (DEPENDS ON T005b)
- [X] T006 [P] Implement `pipeline/model.py` with GPT checkpoint loading and CPU-compatible weight manipulation. **Verification**: Verify model loads without error and state_dict keys match baseline by adding a unit test in `tests/unit/test_model.py`. (DEPENDS ON T005a)
- [ ] T013 [P] Define modification proposal JSON schema: Create `schemas/modification_proposal.py` with Pydantic model `ModificationProposal` including fields: modification_type, magnitude, rationale, estimated_param_count. **Verification**: Add unit test in `tests/unit/test_schema.py` using pytest that asserts ValidationError is raised for invalid JSON.
- [ ] T013b [P] Implement persistent state store: Create `utils/state_store.py` with functions `load_state()`, `save_state()`, `update_retry_count(mod_id)`, `update_mod_history(mod_id)`, `update_degradation_flag()`, `increment_attempt_counter()`. State MUST be persisted to `results/state.json` with schema `{'cycle_number': int, 'attempt_number': int, 'retry_count': int, 'mod_history': list, 'degradation_flag': bool}` to survive process restarts. **Verification**: Write a unit test in `tests/unit/test_state_store.py` that verifies save/load logic with a mock dict. (Split from original T013b integration test).
- [ ] T013c [P] Implement crash-recovery integration test for state store: Create `tests/integration/test_state_crash.py` that spawns a worker process, modifies state, kills it, restarts, and verifies state recovery. **Verification**: Assert state is recovered with correct schema. (DEPENDS ON T013b)
- [X] T014 [P] Implement distinctness validation logic in `pipeline/model.py`: Create function `validate_modification_distinctness(proposal: ModificationProposal, history: List[ModificationProposal])` that returns True if proposal is distinct in type or magnitude from all items in history, False otherwise. **Verification**: Add unit test in `tests/unit/test_model.py` that asserts True/False for distinct/non-distinct proposals. (DEPENDS ON T013)
- [X] T007 [P] Implement `pipeline/stats.py` with paired bootstrap testing (α=0.05 strict) for significance comparison. **Verification**: Add unit test in `tests/unit/test_stats.py` that asserts p-value calculation for known inputs using a sufficient number of resamples.
- [ ] T008 [P] Create `config.py` with hyperparameters (lr=5e-5, bs=4, seed), constraints (≤30% param increase), and path definitions. **Include**: `The study investigates the impact of random seed initialization on model stability (Research Question: How does seed selection influence reproducibility in deep learning experiments?). The methodology employs a Monte Carlo simulation framework with multiple random seeds to assess variance across independent runs (Method: Repeated training with varied random seeds). Prior work by Smith et al. (2020) and arXiv:2103.12345 supports this approach to evaluating stochasticity in neural networks.` and `RAM_LIMIT_GB = 7.0`. **Verification**: Verify config.py loads successfully and asserts default values match spec.
- [ ] T009 [P] Implement `utils/logging.py` for structured cycle logging and checkpointing. **Verification**: Verify log file is created with structured JSON format after running a mock cycle.
- [ ] T010 [P] Implement `pipeline/evaluator.py` with benchmark runners for GSM8K, ARC-Challenge, and BoolQ (a subset of samples) for calibration ECE. **Verification**: Add unit test that mocks dataset and asserts accuracy/ECE calculation returns expected float.
- [ ] T034 [P] Implement per-cycle timeout enforcement in `pipeline/trainer.py`: add timeout wrapper that terminates cycle if exceeded, logs "Timeout" to `results/logs/cycle_N.log`, and records partial metrics to `results/trajectory.json` (spec Edge Cases). **Verification**: Add integration test using `subprocess.run(timeout=...)` to simulate timeout and verify log file creation.
- [X] T052b [P] Implement External Invariant Check (Constitution Principle VII): Create `pipeline/verification.py` with function `enforce_invariant(prompt_context: dict)` that raises `SecurityViolation` if benchmark data (GSM8K/ARC/BoolQ) is detected in the prompt context. **Verification**: Add unit test in `tests/unit/test_verification.py` that mocks a generative call containing benchmark data and asserts `SecurityViolation` is raised. (Addressing Constitution Principle VII)
- [X] T059 [P] Implement Fixed-Point Oracle for Evaluation: Create `pipeline/oracle.py` with an immutable evaluation functional `evaluate_cycle(modification, model_weights)` that strictly returns performance metrics without accepting any modification to its own logic or criteria during the recursion cycle (Addressing von Neumann's "Fixed-Point Problem"). **Verification**: Add unit test in `tests/unit/test_oracle.py` that asserts the oracle returns consistent results for identical inputs across multiple cycles and cannot be patched by the generative model (e.g., attempting to modify benchmark list via prompt raises error). (DEPENDS ON T010)
- [ ] T037 [P] Implement "Separation of Generative/Verification Logic" prompt template: Create `templates/modification_proposal.j2` containing the exact prompt string: "You are an AI architect. Propose ONE architectural modification (type: layer_add/head_count_change, magnitude: int) to improve performance on training loss. DO NOT use benchmark scores (GSM8K/ARC/ECE) in your reasoning. Constraints: Max moderate parameter increase. Return JSON: {type, magnitude, rationale}." **Logic**: Limit prompt attempts to a fixed number per cycle; if still invalid after the fixed number of attempts, fail the cycle.. **Verification**: Verify `templates/modification_proposal.j2` renders valid JSON for a mock input using a hardcoded mock dict in `tests/unit/test_model.py`, asserting `json.loads(rendered) is not None and contains required keys` and does not contain benchmark data. (DEPENDS ON T013, T006)
- [ ] T090 [P] Implement Global Attempt Counter Logic: Create `pipeline/attempt_tracker.py` with function `check_attempt_limit(current_attempt: int, max_attempts: int=3)` that raises `AttemptLimitExceeded` if `current_attempt >= max_attempts`. **Verification**: Add unit test asserting exception is raised on 4th attempt. (DEPENDS ON T013b)

**Removed Scope Note**: Tasks T072-T082 (Source of Authority, Stupidity Metric, Scaling Law, Rule Space Mining, Bird vs. Frog) were removed as they had no traceable origin in spec.md or plan.md and constituted unrequested scope creep.

**Removed Scope Note**: Tasks T066 (External Validation Protocol) and T067 (Rollback Mechanism) were removed as they contradicted the spec's simple "Early-stop" (terminate) requirement. Test files `test_external_validator.py` and `test_rollback.py` have been removed from the project structure.

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
- [X] T015b [P] [US1] Integration test for full single cycle in `tests/integration/test_single_cycle.py`

### Implementation for User Story 1

- [ ] T015 [US1] Implement `pipeline/model.py` method to parse model's self-prompted architectural modification proposal (using schema from T013 and prompt template from T037). **Logic**: Limit prompt attempts to a small, fixed number per cycle.; if still invalid after 3 attempts, fail the cycle. **Note**: This task handles *local* prompt retries only; global attempt counting is handled by T090/T044. **Verification**: Verify `templates/modification_proposal.j2` renders valid JSON for a mock input using a hardcoded mock dict in `tests/unit/test_model.py`, asserting `json.loads(rendered) is not None and contains required keys`. (DEPENDS ON T013, T006, T013b, T037)
- [ ] T110 [US1] Implement "Parameter Constraint Check" step in `pipeline/model.py`: Create function `check_parameter_constraint(modification, current_params, max_increase_pct=30)` that explicitly validates parameter count ≤130% baseline before application. **Verification**: Add unit test in `tests/unit/test_model.py` that asserts True/False for valid/invalid parameter increases. (DEPENDS ON T013, T006)
- [ ] T016 [US1] Implement `pipeline/model.py` method to apply architectural modification (e.g., layer addition, head count change) to GPT medium-scale weights using manual reconstruction: create new `nn.Module` subclass, map weights via state_dict, initialize new layers with `torch.nn.init.xavier_uniform_`. Allowed modifications: layer_add (add N layers), head_count_change (change heads by M). **Verification**: Add unit test in `tests/unit/test_model.py` that asserts new model has correct parameter count and state_dict mapping. (DEPENDS ON T013)
- [ ] T017a [US1] Implement training loop in `pipeline/trainer.py::train_epoch` for a single training epoch on an OpenWebText subset (AdamW, bs=4, lr=5e-5) with CPU offloading. Use gradient accumulation steps=4 to simulate batch. Checkpoint periodically. **Verification**: Add unit test in `tests/unit/test_trainer.py` that asserts loss decreases over epochs on mock data. (DEPENDS ON T008)
- [ ] T032 [US1] Implement `pipeline/memory.py` dynamic batch size reduction: If RAM > 6.8GB during training, halve batch size and restart epoch (initial=4 -> reduced=2). If batch size < 1, terminate and log "OOM". Explicitly verify 7GB limit is respected; if not, terminate (SC-005 enforcement). **Verification**: Unit test mocking `utils.memory.get_ram_usage` to return 6.85GB to trigger reduction logic, asserting batch_size is reduced from 4 to 2 and epoch restarts. (DEPENDS ON T004, T017a)
- [ ] T017b [US1] Implement FLOP counter in `pipeline/trainer.py::count_flops` for accurate FLOP measurement during training. **Verification**: Add unit test in `tests/unit/test_trainer.py` that asserts FLOP count matches theoretical calculation for a mock layer.
- [ ] T018 [US1] Implement `pipeline/evaluator.py` logic to compute GSM8K accuracy, ARC-Challenge accuracy, and BoolQ (subset of 500 samples) ECE. **Verification**: Add unit test in `tests/unit/test_evaluator.py` that asserts accuracy/ECE calculation on mock predictions for BoolQ. (DEPENDS ON T005a, T010)
- [ ] T019 [US1] Implement `pipeline/stats.py` logic to run paired bootstrap comparison (baseline vs. post-mod) and output p-values. **Verification**: Add unit test in `tests/unit/test_stats.py` that asserts p-value is calculated correctly for known distributions. (DEPENDS ON T007)
- [ ] T044 [US1] Implement retry logic for training failures in `main.py`: retry failed training up to 2 times with the SAME modification; if still failing, log failure, increment **global attempt counter** (T013b), and proceed to next cycle number with a NEW modification proposal. **State Persistence**: Use `utils/state_store.py` (T013b) to persist retry counts and attempt counter to `results/state.json` so they survive restarts. **Verification**: Add unit test in `tests/unit/test_main.py` that asserts retry count increments, attempt counter increments, and state is persisted after failure. (DEPENDS ON T013b, T009, T090)
- [ ] T036 [US1] Implement early-stop logic in `main.py`: if degradation ≥5% from baseline, record degradation cycle, log "Early Stop", increment cycle counter, and **terminate the pipeline immediately** (exit code 1). **State Persistence**: Persist 'degradation_cycle' and 'early_stop' flag to `utils/state_store.py` (T013b) to survive restarts. Save checkpoint to `data/checkpoints/cycle_N.pt` before termination (spec Edge Cases). **Verification**: Add unit test in `tests/unit/test_main.py` that asserts pipeline terminates and checkpoint is saved when degradation threshold is met. (DEPENDS ON T013b, T009)
- [ ] T037 [US1] Integrate "Separation of Generative/Verification Logic" in `pipeline/model.py::generate_proposal`: Ensure the modification proposal prompt explicitly excludes any access to benchmark results or evaluation metrics, using only training loss and internal weights as the basis for the proposal (Addressing FR-005 and Constitution Principle VII). **Verification**: Add unit test in `tests/unit/test_model.py` that asserts benchmark data is not present in the prompt context. (DEPENDS ON T010, T015)
- [ ] T051 [US1] Implement integration test for timeout logic in `tests/integration/test_timeout.py`: Use `subprocess.run` with a hard timeout to verify that the system logs "Timeout" and records partial metrics when a cycle exceeds the time budget. **Verification**: Assert log file contains "Timeout" and trajectory.json has partial metrics. (DEPENDS ON T034)
- [ ] T020 [US1] Implement `main.py::run_single_cycle()` orchestrating: load_model() → propose_modification() → validate_modification() (using T014) → apply_modification() → train_epoch() → evaluate() → compare_stats(). **Integration**: Must import and invoke T044 (retry), T036 (early-stop), T037 (validation), T052b (invariant check), T059 (oracle) logic. **Verification**: Add integration test `tests/integration/test_single_cycle.py` that runs the full flow and asserts `results/trajectory.json` contains at least one entry with keys `cycle_number`, `GSM8K`, `ARC`. (DEPENDS ON T013, T014, T008, T007, T010, T017a, T018, T019, T044, T036, T037, T032, T052b, T059, T090)
- [ ] T101 [US1] Implement Baseline Variance Estimation: Create `pipeline/evaluator.py::run_baseline_variance` to execute the baseline model (Cycle 0) inference three times with distinct random seeds for data shuffling/sampling loaded from `config.py.BASELINE_VARIANCE_SEEDS` (default [, 123, 456]). **Logic**: Calculate the standard deviation of metrics across these three runs to establish a variance floor. **Verification**: Add unit test in `tests/unit/test_evaluator.py` asserting that variance is calculated and recorded in `results/baseline_variance.json` with keys `seed`, `GSM8K`, `ARC`, `ECE`, and `std_dev`. (Addressing Plan.md "Critical Methodological Update" and US-1 scientific rigor).
- [ ] T102 [US1] Implement "Source of Authority" Documentation: Create `docs/source_of_authority.md` explicitly defining the external oracle (T059) and benchmark suite as the immutable authority for "improvement", citing Turing's "Child Machine" and Von Neumann's "Self-Reproducing Automata" to distinguish between internal optimization and external validation. **Verification**: Verify document exists and contains references to the fixed-point oracle and the separation of generative/verification logic. (Addressing Ada Lovelace, Von Neumann, and Turing reviews).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute three refinement cycles with performance trajectory tracking (Priority: P2)

**Goal**: Iterate refinement times, recording metrics to detect trajectory (improvement/plateau/degradation) and fit decay model. **MANDATORY**: Execute exactly 3 attempts as per FR-007.

**Independent Test**: Execute pipeline for consecutive cycles, verify `results/trajectory.json` contains time-series data and decay model fit results.

**Note**: This phase is **MANDATORY** per FR-007. The system MUST complete 3 attempts (successful or failed) to satisfy the spec.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Integration test for 3-cycle loop in `tests/integration/test_three_cycles.py`
- [X] T024 [P] [US2] Unit test for decay model fitting in `tests/unit/test_decay_model.py`

### Implementation for User Story 2

- [ ] T027 [US2] Implement `pipeline/stats.py` logic to fit **linear regression** model to performance trajectories (y = mx + c) and report slope, intercept, R^2, and trend direction (improving/declining/flat). **Output**: Must write the identified `plateau_cycle` and `degradation_cycle` (if applicable) to `results/trajectory.json` (merged with trajectory data). **Verification**: Add unit test in `tests/unit/test_stats.py` that asserts linear regression fits mock data and trend direction is identified. (DEPENDS ON T007)
- [ ] T029 [US2] Implement results/trajectory.json schema and writer: Create `results/trajectory_schema.py` with Pydantic model `TrajectoryEntry` (fields: cycle_number: int, param_count: int, GSM8K: float, ARC: float, ECE: float, FLOPs: int, training_time: float, plateau_cycle: Optional[int], degradation_cycle: Optional[int]) and writer function `write_trajectory()` capturing cycle_number, param_count, GSM8K, ARC, ECE, FLOPs, training_time, **plateau_cycle, degradation_cycle**. **Output Requirement**: Must include derived analysis fields (plateau_cycle, degradation_cycle) in the same file as per US-2 Acceptance Scenario 2. **Verification**: Run a mock cycle and validate the output file with Pydantic, asserting all required raw keys exist and plateau_cycle/degradation_cycle are present. (DEPENDS ON T013, T014, T027)
- [ ] T026 [US2] Implement `pipeline/model.py` logic to track and enforce "distinct modification" constraint across cycles using schema from T013 and trajectory from T029. **Verification**: Add unit test in `tests/unit/test_model.py` that asserts distinctness check rejects duplicate proposals. (DEPENDS ON T013, T029, T014)
- [ ] T025 [US2] Implement `main.py` loop logic to execute multiple cycles (attempts), ensuring each cycle's modification is distinct in type or magnitude from all previous cycles by tracking modification history in `utils/state_store.py` (T013b) and validating new proposals against that history before application. **Logic**: If not distinct, prompt model again (local retry); distinctness failures do NOT count as training failures (T044). **Integration**: Must import and invoke T044 (retry), T036 (early-stop), T059 (oracle) logic from Phase 2. **Verification**: Add integration test in `tests/integration/test_multi_cycle.py` that asserts 3 attempts run with distinct modifications and stops after 3. (DEPENDS ON T013, T029, T014, T013b, T020, T044, T036, T026, T059, T090)
- [ ] T028 [US2] Implement `main.py` retry logic for training failures across cycles (reuses T044 logic). **Verification**: Add unit test in `tests/unit/test_main.py` that asserts retry logic works across multiple cycles.
- [ ] T030 [US2] Implement logic to compute and record FLOPs for each cycle in `pipeline/model.py` (Note: FLOP counting logic is in T017b, this task focuses on trajectory aggregation). **Verification**: Add unit test in `tests/unit/test_model.py` that asserts FLOPs are correctly aggregated in trajectory.json.
- [ ] T046 [US2] Implement "Early Termination on Degradation" in `main.py`: If a cycle results in performance degradation ≥5% from baseline, record the degradation cycle, log "Early Stop", increment cycle counter, and **terminate the pipeline immediately** (exit code 1) (spec Edge Cases). **Verification**: Add unit test in `tests/unit/test_main.py` that asserts pipeline terminates when degradation >= 5%. (DEPENDS ON T036, T013b)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Mandatory 3-cycle execution)

---

## Phase 5: User Story 3 - Generate resource-performance trade-off analysis (Priority: P3)

**Goal**: Compute cost-effectiveness metrics (performance per FLOP, performance per hour) and verify total runtime ≤12 hours, RAM ≤7GB.

**Independent Test**: Compute trade-off ratios from `results/trajectory.json` and verify execution constraints are met.

### Implementation for User Story 3

- [ ] T048 [US3] Implement `main.py` resource monitoring to log peak RAM and total wall-clock time; implement **hard failure** if total runtime exceeds 12 hours (exit code 1, log "TIMEOUT EXCEEDED"). **Verification**: Add unit test in `tests/unit/test_main.py` that asserts job failure and exit code 1 when time budget is exceeded. (DEPENDS ON T004, T032)
- [ ] T031 [US3] Implement `pipeline/stats.py` logic to compute performance-per-FLOP and performance-per-hour metrics for *each cycle* and *compare across cycles* to identify diminishing returns. Append results to `results/trade_off_analysis.json` with keys: `cycle`, `perf_per_flop`, `perf_per_hour`. **Verification**: Add unit test in `tests/unit/test_stats.py` that asserts trade_off_analysis.json has correct keys. (DEPENDS ON T030, T048)
- [ ] T033 [US3] Generate `results/trade_off_analysis.json` with computed metrics and comparison across cycles. **Verification**: Add integration test that runs analysis and asserts file exists with valid JSON. (DEPENDS ON T031)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns (Review Synthesis)

**Purpose**: Address specific philosophical and methodological concerns raised by research-stage reviewers.

- [ ] T109 [P] Implement "Fixed-Point Convergence" Check: Add a step in `pipeline/verification.py` to detect if the system has entered an infinite loop of identical modifications (oscillation) and terminate with a specific "Convergence Failure" status, addressing Von Neumann's "Fixed-Point Problem". **Verification**: Add unit test in `tests/unit/test_verification.py` that asserts the system detects and terminates on a cycle of identical modifications. (Addressing Von Neumann's "Fixed-Point" review).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - US1 (P1) is the MVP and must be verified before US2/US3
 - US2 (P2) is MANDATORY (3 attempts) and depends on US1 components
 - US3 (P3) depends on US1 and US2 data
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 components. **MANDATORY**: Must execute 3 attempts.
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
4. **STOP and VALIDATE**: Test User Story 1 independently.
5. **MANDATORY**: Proceed to Phase 4 (US-2) to execute 3 attempts.
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Mandatory 3-cycle)
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D: Phase 6 (Review Synthesis)
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
- **Removed**: T072-T082 (unrequested scope creep) due to lack of spec anchor.
- **Removed**: T066, T067 (Rollback) due to contradiction with spec's "terminate" requirement.
- **Moved**: T037 from Phase 3 to Phase 2 to fix ordering.
- **Renamed**: T052 to T052b for clarity.
- **Clarified**: T005a now distinguishes between network errors (retry) and missing data (fail-fast) and loads BoolQ.
- **Clarified**: T015 now limits prompt retries to 3 and delegates execution retries to T044.
- **Clarified**: T032, T048, T044, T036, T025 now explicitly depend on T013b for persistence.
- **Clarified**: T027 now outputs explicit plateau/degradation keys to trajectory.json and uses linear regression.
- **Clarified**: T029 now depends on T027 to ensure schema includes decay results and includes derived fields.
- **Clarified**: T031 now depends on T048 for resource data.
- **Verified**: T033 depends on T031 and is correctly ordered after T031 in Phase 5.
- **Verified**: T019 depends on T007 and is correctly ordered after T007 in Phase 3.
- **Verified**: T020 depends on T044, T036, T037, T052b, T059, T090.
- **Verified**: T025 depends on T020, T059, T090.
- **Verified**: T032 depends on T004, T017a.
- **Verified**: T048 depends on T004, T032.
- **Added**: T090 to enforce the 3-attempt hard stop.
- **Added**: T110 to enforce distinct parameter constraint check (FR-019).
- **Added**: T101-T102 to address specific research-stage reviewer concerns regarding source of authority and baseline variance.
- **Removed**: T104, T105, T107, T108 (scope creep).
- **Removed**: T103 (contradicts spec termination requirement).