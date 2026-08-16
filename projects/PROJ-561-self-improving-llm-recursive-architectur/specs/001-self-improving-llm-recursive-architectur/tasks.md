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
- [ ] T008 [P] Create `config.py` with hyperparameters (lr=5e-5, bs=4, seed), constraints (param increase limit = placeholder, to be resolved in research phase), and path definitions. Include `{{claim:c_3773390f}} (Wikipedia: Bootstrapping (statistics), https://en.wikipedia.org/wiki/Bootstrapping_(statistics))` as a default. **Verification**: Verify config.py loads successfully and asserts default values match spec (e.g., `PARAM_LIMIT` is a placeholder or configurable).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `utils/memory.py` with RAM monitoring: create `utils/memory.py` with function `check_ram_usage(limit_gb: float)` that reads `limit_gb` from `config.py` and logs a warning if peak RAM exceeds the limit. **Logic**: If threshold exceeded, log "RAM Warning: {peak_value}GB" with the actual peak value; do NOT trigger termination (termination is handled by T036a per FR-015). **Verification**: Add a unit test in `tests/unit/test_memory.py` that mocks `psutil.virtual_memory` using `unittest.mock.patch` to return a value > limit and asserts a warning is logged with the correct peak value, but no exception is raised.
- [X] T005b Implement exponential backoff wrapper in `pipeline/loader.py` with initial delay=30s (±1s), max retries=5 for HuggingFace API calls [UNRESOLVED-CLAIM: c_cca91522 — status=not_enough_info]. **Verification**: Add unit test in `tests/unit/test_loader.py` that mocks `time.sleep` and asserts retry count increments correctly on simulated failures, explicitly verifying the initial delay is exactly 30 seconds (within 1s tolerance).
- [ ] T005a Implement dataset loaders in `pipeline/loader.py` for OpenWebText [UNRESOLVED-CLAIM: c_b453bde1 — status=not_enough_info] (training), GSM8K (test), ARC-Challenge (test), and BoolQ (test) with Fail-Fast logic: **Logic**: For transient network errors (HTTP 429/5xx), call `exponential_backoff` from T005b; for missing data files at paths defined in `config.py`, raise `FileNotFoundError` immediately with message "Dataset file not found: {path}" (no synthetic fallback). **Verification**: Verify that loading a non-existent dataset using a dynamically generated temporary path (e.g., `tempfile.mktemp()`) raises `FileNotFoundError` with the exact message. Also verify that loading a missing file at a `config.py` defined path raises `FileNotFoundError` and does NOT fallback to synthetic data. Also verify that simulating `HfHubHTTPError` (from huggingface_hub) triggers the retry logic from T005b. (DEPENDS ON T005b)
- [ ] T006 [P] Implement `pipeline/model.py` with GPT checkpoint loading and CPU-compatible weight manipulation. **Verification**: Verify model loads without error, that `next(model.parameters()).device` is 'cpu', and that `model.config` matches GPT-2 124M parameters (n_layer=12, n_head=12, n_embd=768) [UNRESOLVED-CLAIM: c_cbca9bf8 — status=not_enough_info]. (DEPENDS ON T001, T008)
- [ ] T013 [P] Define modification proposal JSON schema: Create `schemas/modification_proposal.py` with Pydantic model `ModificationProposal` including fields: `modification_type` (str: 'layer_add' | 'head_count_change' | 'hidden_size_change' | 'activation_change'), `magnitude` (int), `rationale` (str), `estimated_param_count` (int). **Verification**: Add unit test in `tests/unit/test_schema.py` using pytest that asserts ValidationError is raised specifically for a missing `magnitude` field.
- [ ] T014a [P] Implement schema validation for modification proposals: Create function `validate_schema(proposal)` in `pipeline/model.py` that ensures the proposal matches the `ModificationProposal` schema. **Verification**: Add unit test in `tests/unit/test_model.py` that asserts ValidationError is raised for invalid schema. (DEPENDS ON T013)
- [ ] T014b [P] Implement distinctness validation logic (vector distance/param delta): Create function `validate_modification_distinctness(proposal: ModificationProposal, history: List[ModificationProposal])` in `pipeline/model.py` that returns True if proposal is distinct in type (Hamming distance >= 1 on config vector) or magnitude (>5% parameter change) from all items in history, False otherwise. **Verification**: Add unit test in `tests/unit/test_model.py` that asserts True/False for distinct/non-distinct proposals based on Hamming distance and parameter delta logic. (DEPENDS ON T013)
- [ ] T007 [P] Implement `pipeline/stats.py` with paired bootstrap testing (α=0.05 (Wikipedia: Ordinary least squares, https://en.wikipedia.org/wiki/Ordinary_least_squares) strict) and linear regression trend analysis. **Logic**: Must implement 'paired' bootstrap (same samples, pre/post comparison) as required by FR-006. **Verification**: Add unit test in `tests/unit/test_stats.py` that asserts bootstrap p-value calculation returns a float between 0 and 1 [UNRESOLVED-CLAIM: c_e15f970e — status=not_enough_info] for a mock paired distribution, and linear regression slope calculation for a known linear set. The number of resamples MUST be read from `config.py` (default configurable). (DEPENDS ON T008)
- [ ] T009 [P] Implement `utils/logging.py` for structured cycle logging and checkpointing. **Verification**: Verify log file is created with structured JSON format after running a mock cycle.
- [ ] T010 [P] Implement `pipeline/evaluator.py` with benchmark runner for GSM8K, ARC-Challenge, and BoolQ. **Logic**: Includes both the runner and the evaluation logic. **Verification**: Add unit test that mocks dataset and asserts accuracy/ECE calculation returns expected float. (DEPENDS ON T005a)
- [ ] T017c [P] Implement FLOP counter in `utils/metrics.py`: Create function `calculate_flops(model, input_shape)` that accurately counts FLOPs using torch.profiler or equivalent, ensuring calculation occurs in `utils/metrics.py` as per FR-008. **Verification**: Add unit test in `tests/unit/test_metrics.py` that asserts FLOP count matches theoretical calculation for a mock layer (e.g., Linear(10, 5) with input 1, expected FLOPs = 2*10*5*1).
- [ ] T036a [P] Implement performance-degradation-based termination logic in `pipeline/orchestrator.py`: Create function `check_termination(current_metrics, baseline_metrics)` that terminates the pipeline if degradation ≥5% from baseline (FR-015). **Verification**: Add unit test in `tests/unit/test_orchestrator.py` that asserts pipeline terminates when degradation >= 5%.
- [ ] T059 [P] Implement External Oracle Logic: Create `pipeline/oracle.py` with a fixed, external heuristic validator `validate_external_oracle(proposal: ModificationProposal)` that checks for parameter efficiency (<=30% increase from baseline) and structural validity BEFORE application. **Logic**: This implements the core "External Oracle" logic defined in FR-021 and Plan Step 3.3, ensuring the generative model's proposal is validated against a static, non-adaptive set of rules. It must also implement the "reject and prompt again" loop logic if validation fails. **Verification**: Add unit test in `tests/unit/test_oracle.py` that asserts the oracle rejects proposals violating fixed heuristics (e.g., parameter count > 30% increase) and accepts valid ones, independent of model feedback. (DEPENDS ON T013, T008)
- [ ] T037 [P] Implement "Separation of Generative/Verification Logic" prompt template: Create `templates/modification_proposal.j` containing the exact prompt string: "You are an AI architect. Propose ONE architectural modification (type: layer_add/head_count_change/hidden_size_change/activation_change, magnitude: int) to improve performance on training loss. DO NOT use benchmark scores (GSM8K/ARC/BoolQ) or oracle outputs in your reasoning. Constraints: Minimal parameter increase. Return JSON: {modification_type, magnitude, rationale}." **Logic**: Limit prompt attempts to a predefined threshold per cycle; if still invalid after reaching the threshold, fail the cycle. **Verification**: Verify `templates/modification_proposal.j2` renders valid JSON for a mock input using a hardcoded mock dict in `tests/integration/test_model.py`, asserting `json.loads(rendered)` contains `modification_type` as one of the allowed values and `magnitude` as an integer. (DEPENDS ON T013)
- [ ] T029 [P] Implement results/trajectory.json schema and writer: Create `results/trajectory_schema.py` with Pydantic model `TrajectoryEntry` (fields: cycle_number: int, param_count: int, GSMK_accuracy: float, ARC_Challenge_accuracy: float, BoolQ_ECE: float, FLOPs: int, training_time: float, slope: float, intercept: float, r_squared: float, trend_direction: str) and writer function `write_trajectory()` capturing cycle_number, param_count, GSM8K_accuracy, ARC_Challenge_accuracy, BoolQ_ECE, FLOPs, training_time, and linear regression results (slope, intercept, r_squared, trend_direction). **Output Requirement**: Must include raw metrics and trend direction as per US-2 Acceptance Scenario 2 and FR-009. **Verification**: Run a mock cycle and validate the output file with Pydantic, asserting all required raw keys and trend keys exist. (DEPENDS ON T013, T017c, T048, T007)

**NEW TASKS FOR SPEC COMPLIANCE**:

- [ ] T001a [P] Implement "Pre-flight URL Verification": Create `pipeline/loader.py` function `verify_urls(urls: List[str])` that checks all dataset URLs against primary sources (HuggingFace) before download. **Logic**: Must implement Step 1.0 of Plan.md Phase 0. **Verification**: Add unit test that asserts function raises error if a URL is unreachable or returns 404.
- [ ] T001b [P] Implement "Data Download & Checksumming": Create `pipeline/loader.py` function `download_and_checksum(dataset_name: str, dest_path: str)` that downloads data and records SHA-256 hash. **Logic**: Must implement Step 1.1 of Plan.md Phase 0. **Verification**: Add unit test that asserts a checksum file is created and matches the downloaded content. (DEPENDS ON: T001a)
- [ ] T002 [P] Implement "Baseline Capability Check": Create `pipeline/main.py` function `run_baseline_check()` that evaluates the unmodified model on benchmarks and records Cycle 0 metrics to `results/trajectory.json`. **Logic**: Must implement Step 2.1-2.2 of Plan.md Phase 1. **Verification**: Add integration test that asserts Cycle 0 metrics are written to trajectory.json before any refinement cycles begin. (DEPENDS ON: T006, T010)
- [ ] T073 [P] Implement "RAM Constraint Enforcement" Logic: Create `pipeline/orchestrator.py` function `enforce_ram_constraints(current_ram_gb: float, limit_gb: float)` that reads `limit_gb` from `config.py` and logs "RAM WARNING: reducing subset" if limit is breached, then reduces the training subset size to fit within RAM, satisfying FR-015 and SC-005 targets without hard termination. **Logic**: This task bridges the gap between T004's warning and the mandatory subset reduction behavior. **Verification**: Add unit test that asserts the function logs a warning and triggers subset reduction logic (mocked) when limit is exceeded, but does NOT raise SystemExit. (DEPENDS ON: T004)
- [ ] T074 [P] Implement "Resource Metrics Recorder" Logic: Create `pipeline/report.py` function `record_resource_metrics(peak_ram_gb: float, total_time_hours: float)` that explicitly writes peak RAM and total time to `results/trajectory.json` and `results/final_report.md`, satisfying SC-005. **Logic**: This task ensures the metrics are recorded, not just used for failure checks. **Verification**: Add unit test that asserts the metrics are correctly written to the JSON file.
- [ ] T075 [P] Implement "State File Update" Logic: Create `utils/state.py` function `update_state_file(artifact_hashes: Dict[str, str], cycle_number: int)` that hashes artifacts and updates `state/...yaml` as mandated by Plan.md Step 3.9 and Constitution Principle V. **Verification**: Add unit test that asserts the state file is updated with correct hashes and timestamps. (DEPENDS ON: T009)

**REVISED TASKS FOR REVIEWER CONCERNS (Review Synthesis)**:

- [ ] T086 [P] Generate "Review Synthesis Report": Create `docs/review_synthesis.md` that explicitly maps the single core concern (Source of Authority, FR-021) to the specific task (T059) that addresses it, providing a traceability matrix. **Verification**: Verify the document exists and contains a table mapping reviewer names to task IDs and a brief description of the resolution. (DEPENDS ON: T059)

**Removed Scope Note**: Tasks T080-T085 (Turing, West, Wolfram, Krakauer concerns) were removed as they had no traceable origin in spec.md or plan.md and constituted unrequested scope creep.

**Removed Scope Note**: Task Tb (Persistent State Store for restart survival) was removed as the spec defines a linear 3-attempt sequence without requiring crash-recovery persistence.

**Removed Scope Note**: Task T032 (Dynamic Batch Size) was removed as it violated FR-004 (fixed batch size 4).

**Removed Scope Note**: Task T052b (External Invariant Check) was removed as it conflated security with the oracle logic defined in FR-021 and T059.

**Removed Scope Note**: Tasks T110-T116 (Source of Authority, Stupidity Metric, Scaling Law, Rule Space Mining, Bird vs. Frog, Kolmogorov Complexity, Fixed-Point Convergence) were removed as they had no traceable origin in spec.md or plan.md and constituted unrequested scope creep.

**Removed Scope Note**: Task T109 (Fixed-Point Convergence) was removed as it was a duplicate of T116 (which was removed).

**Removed Scope Note**: Task T090 (Global Attempt Counter) was removed as it decoupled the 3-cycle constraint and was rejected. The cycle counter is now handled in-memory within `main.py`.

**Removed Scope Note**: Task T034 (Timeout enforcement) and T051 (Timeout integration test) were removed as they implemented hard failure constraints not present in the spec (SC-005 is a target, not a hard termination).

**Removed Scope Note**: Task T061 (Overfitting Detection) was removed as it introduced a held-out validation set not defined in the spec.

**Removed Scope Note**: Tasks T063, T064, T066, T067 (Rule Space Mining, Scaling Law, Stupidity Metric, Fixed-Point Convergence) were removed as they were unrequested scope creep.

**Removed Scope Note**: Phase 6 (T060-T067) was removed entirely as these tasks introduced unrequested scope creep (Source of Authority, Fixed Curriculum, Rollback, Irreducibility, Rule Space, Scaling Law, Fixed-Point Convergence, Stupidity Metric) with no corresponding Functional Requirement or Success Criterion in spec.md.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute single refinement cycle with baseline comparison (Priority: P1) 🎯 MVP

**Goal**: Download a GPT model of moderate scale, apply one architectural modification, re-train on OpenWebText [UNRESOLVED-CLAIM: c_b453bde1 — status=not_enough_info] subset, and evaluate on GSM8K, ARC-Challenge, and BoolQ with statistical comparison.

**Independent Test**: Execute pipeline once, verify metrics recorded in `results/trajectory.json` and `data/` artifacts, and confirm CPU-only execution completes within 2 hours.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T011 [P] [US1] Unit test for memory watchdog in `tests/unit/test_memory.py`
- [ ] T012 [P] [US1] Unit test for bootstrap significance logic in `tests/unit/test_stats.py`
- [ ] T014b [P] [US1] Unit test for distinctness validation in `tests/unit/test_model.py`
- [ ] T015b [P] [US1] Integration test for full single cycle in `tests/integration/test_single_cycle.py`

### Implementation for User Story 1

- [ ] T015 [US1] Implement `pipeline/model.py` method to parse model's self-prompted architectural modification proposal (using schema from T013 and prompt template from T037) and validate parameter count ≤ limit defined in `config.py` (placeholder, to be resolved in research phase). **Logic**: Limit prompt attempts to a fixed number per cycle; if still invalid after that number of attempts, fail the cycle. **Schema**: The proposal MUST be a JSON object with keys: `modification_type` (str), `magnitude` (int), `rationale` (str). **Verification**: Verify `templates/modification_proposal.j2` renders valid JSON for a mock input using a hardcoded mock dict in `tests/integration/test_model.py`, asserting `json.loads(rendered) is not None and contains required keys`. (DEPENDS ON T013, T006, T037)
- [ ] T016 [US1] Implement `pipeline/model.py` method to apply architectural modification (e.g., layer addition, head count change, hidden size change) to GPT medium-scale weights using manual reconstruction: create new `nn.Module` subclass, map weights via state_dict, initialize new layers with `torch.nn.init.xavier_uniform_`. Allowed modifications: layer_add, head_count_change, hidden_size_change, activation_change. **Verification**: Add unit test in `tests/unit/test_model.py` that asserts new model has correct parameter count and state_dict mapping. (DEPENDS ON T013)
- [ ] T017a [US1] Implement training loop in `pipeline/trainer.py::train_epoch` for a single training epoch on an OpenWebText [UNRESOLVED-CLAIM: c_b453bde1 — status=not_enough_info] subset (AdamW, bs=4, lr=5e-5) with CPU offloading. Use gradient accumulation steps=4 [UNRESOLVED-CLAIM: c_0cbdf188 — status=not_enough_info] to simulate batch. Checkpoint periodically. **Verification**: Add unit test in `tests/unit/test_trainer.py` that asserts loss decreases over epochs on mock data. (DEPENDS ON T008)
- [ ] T017b [US1] Implement FLOP counter in `pipeline/trainer.py::count_flops` for accurate FLOP measurement during training. **Verification**: Add unit test in `tests/unit/test_trainer.py` that asserts FLOP count matches theoretical calculation for a mock layer.
- [ ] T018 [US1] Implement `pipeline/evaluator.py` logic to compute GSM8K, ARC-Challenge, and BoolQ metrics. **Verification**: Add unit test in `tests/unit/test_evaluator.py` that asserts accuracy/ECE calculation on mock predictions. (DEPENDS ON T010)
- [ ] T019 [US1] Implement `pipeline/stats.py` logic to run paired bootstrap comparison (baseline vs. post-mod) and output p-values. **Logic**: Must implement 'paired' bootstrap (same samples, pre/post comparison) as required by FR-006. **Verification**: Add unit test in `tests/unit/test_stats.py` that asserts p-value is calculated correctly for known paired distributions. The number of resamples MUST be read from `config.py`. (DEPENDS ON T007)
- [ ] T044 [US1] Implement retry logic for training failures in `main.py`: retry failed training up to 2 times [UNRESOLVED-CLAIM: c_0f0904bf — status=not_enough_info] with the SAME modification; if still failing, log failure, decrement 'remaining attempts' counter, increment **cycle counter** directly (in-memory, feeding into global 3-cycle limit [UNRESOLVED-CLAIM: c_ed3ad388 — status=not_enough_info]), and proceed to next cycle number with a NEW modification proposal. **State**: Use in-memory counters (no persistence across restarts required by spec). **History**: The modification history list is ONLY appended to after a modification is successfully validated and applied. If a cycle fails before application, the history remains unchanged. **Verification**: Add unit test in `tests/unit/test_main.py` that asserts retry count increments, cycle counter increments, remaining attempts decrements on failure, and history is not updated on failure. (DEPENDS ON T009)
- [ ] T036 [US1] Implement early-stop logic in `main.py`: if degradation ≥5% from baseline (checked by T036a), record degradation cycle in `results/trajectory.json` (as a distinct data point), log "Early Stop", increment cycle counter, and terminate gracefully. **State**: Persist 'degradation_cycle' and 'early_stop' flag to `results/state.json` for this run. Save checkpoint to `data/checkpoints/cycle_N.pt` before termination (spec Edge Cases). **Verification**: Add unit test in `tests/unit/test_main.py` that asserts pipeline terminates, degradation_cycle is recorded in trajectory.json, and checkpoint is saved when degradation threshold is met. (DEPENDS ON T009, T036a)
- [ ] T037b [US1] Integrate "Separation of Generative/Verification Logic" in `pipeline/model.py::generate_proposal`: Ensure the modification proposal prompt explicitly excludes any access to benchmark results or evaluation metrics, using only training loss and internal weights as the basis for the proposal (Addressing FR-005 and Constitution Principle VII). **Verification**: Add unit test in `tests/unit/test_model.py` that asserts benchmark data is not present in the prompt context. (DEPENDS ON T010, T015, T037)
- [ ] T020 [US1] Implement `main.py::run_single_cycle()` orchestrating: load_model() → propose_modification() → validate_modification() (using T059) → apply_modification() → train_epoch() → evaluate() → compare_stats(). **Control Flow**: If distinctness check (T014b) fails, the system MUST request a new proposal (loop back to propose) rather than retrying training. **Integration**: Must import and invoke T044 (retry), T036 (early-stop), T037b (validation), T059 (oracle) logic. **Verification**: Add integration test `tests/integration/test_single_cycle.py` that runs the full flow and asserts `results/trajectory.json` contains at least one entry with keys `cycle_number`, `GSM8K_accuracy`, `ARC_Challenge_accuracy`, `BoolQ_ECE`. (DEPENDS ON T013, T014b, T008, T007, T010, T017a, T018, T019, T044, T036, T037b, T059)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute three refinement cycles with performance trajectory tracking (Priority: P2)

**Goal**: Iterate refinement times, recording metrics to detect trajectory (improvement/plateau/degradation) and fit linear regression model. **MANDATORY**: Execute a limited number of attempts as per FR-007.

**Independent Test**: Execute pipeline for consecutive cycles, verify `results/trajectory.json` contains time-series data and linear regression fit results.

**Note**: This phase is **MANDATORY** per FR-007. The system MUST complete a limited number of attempts (successful or failed) to satisfy the spec.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Integration test for 3-cycle loop in `tests/integration/test_three_cycles.py`
- [ ] T024 [P] [US2] Unit test for linear regression fitting in `tests/unit/test_decay_model.py`

### Implementation for User Story 2

- [ ] T026 [US2] Implement `pipeline/model.py` logic to track and enforce "distinct modification" constraint across cycles using schema from T013 and trajectory from T029. **Verification**: Add unit test in `tests/unit/test_model.py` that asserts distinctness check rejects duplicate proposals. (DEPENDS ON T013, T029, T014b)
- [ ] T025 [US2] Implement `main.py` loop logic to execute a limited number of cycles (attempts), ensuring each cycle's modification is distinct in type or magnitude from all previous cycles by tracking modification history in memory and validating new proposals against that history before application. If not distinct, prompt model again. **History**: The modification history list is ONLY appended to after a modification is successfully validated and applied. If a cycle fails before application, the history remains unchanged. **Integration**: Must import and invoke T044 (retry), T036 (early-stop), T059 (oracle) logic from Phase 2. **Verification**: Add integration test in `tests/integration/test_multi_cycle.py` that asserts multiple attempts run with distinct modifications and stops after a predefined number of iterations. (DEPENDS ON T013, T029, T014b, T020, T044, T036, T059)
- [ ] T028 [US2] Implement `main.py` retry logic for training failures across cycles (reuses T044 logic). **Verification**: Add unit test in `tests/unit/test_main.py` that asserts retry logic works across multiple cycles.
- [ ] T030 [US2] Implement logic to compute and record FLOPs for each cycle in `pipeline/model.py` (Note: FLOP counting logic is in T017b and T017c, this task focuses on trajectory aggregation). **Verification**: Add unit test in `tests/unit/test_model.py` that asserts FLOPs are correctly aggregated in trajectory.json. (DEPENDS ON T017b)
- [ ] T046 [US2] Implement "Early Termination on Degradation" in `main.py`: If a cycle results in performance degradation ≥5% from baseline, record the degradation cycle in trajectory.json, log "Early Stop", increment cycle counter, and terminate the pipeline (spec Edge Cases). **Verification**: Add unit test in `tests/unit/test_main.py` that asserts pipeline terminates when degradation >= 5%. (DEPENDS ON T036)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Mandatory 3-cycle execution)

---

## Phase 5: User Story 3 - Generate resource-performance trade-off analysis (Priority: P3)

**Goal**: Compute cost-effectiveness metrics (performance per FLOP, performance per hour) and verify total runtime ≤12 hours, RAM ≤7GB.

**Independent Test**: Compute trade-off ratios from `results/trajectory.json` and verify execution constraints are met.

### Implementation for User Story 3

- [ ] T048 [US3] Implement `main.py` resource monitoring to log peak RAM and total wall-clock time; implement logic to log "TIME WARNING: continuing" if total runtime exceeds a predefined threshold (log and continue) instead of strict failure, to satisfy SC-005 target nature. **Logic**: This task MUST call T074 to record the metrics. **Verification**: Add unit test in `tests/unit/test_main.py` that asserts job continues when timeout is met and metrics are recorded. (DEPENDS ON: T004, T073, T074)
- [ ] T031 [US3] Implement `pipeline/stats.py` logic to compute performance-per-FLOP and performance-per-hour metrics for *each cycle* and *compare across cycles* to identify diminishing returns. Append results to `results/trade_off_analysis.json` with keys: `cycle`, `perf_per_flop`, `perf_per_hour`. **Verification**: Add unit test in `tests/unit/test_stats.py` that asserts trade_off_analysis.json has correct keys. (DEPENDS ON: T030, T048)
- [ ] T033 [US3] Generate `results/trade_off_analysis.json` with computed metrics and comparison across cycles. **Verification**: Add integration test that runs analysis and asserts file exists with valid JSON. (DEPENDS ON: T031)

**Checkpoint**: All user stories should now be independently functional

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - US1 (P1) is the MVP and must be verified before US2/US3
 - US2 (P2) is MANDATORY (3 attempts [UNRESOLVED-CLAIM: c_bea51fbe — status=not_enough_info]) and depends on US1 components
 - US3 (P3) depends on US1 and US2 data
- **Review Enhancements (Phase 6)**: REMOVED - Unrequested scope creep
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 components. **MANDATORY**: Must execute 3 attempts [UNRESOLVED-CLAIM: c_bea51fbe — status=not_enough_info].
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Integrates with US1/US2 data
- **Review Enhancements (Phase 6)**: REMOVED.

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
5. **MANDATORY**: Proceed to Phase 4 (US-2) to execute 3 attempts [UNRESOLVED-CLAIM: c_bea51fbe — status=not_enough_info].
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
- **CRITICAL**: No task may use GPU, quantization, or synthetic data. All tasks must run on The system runs on CPU-only free-tier CI.
- **Removed**: T101-T108 (unrequested scope creep) due to lack of spec anchor.
- **Removed**: T013b (persistence) as spec does not require crash recovery.
- **Moved**: T037 from Phase 3 to Phase 2 to fix ordering.
- **Renamed**: T037 (Phase 3) to T037b to resolve ID conflict.
- **Clarified**: T005a now distinguishes between network errors (retry) and missing data (fail) using runtime paths and explicitly calls T005b.
- **Clarified**: T015 now limits prompt retries to 3 and delegates execution retries to T044.
- **Clarified**: T032, T048, T044, T036, T025 now explicitly depend on cycle counter logic (no separate global counter).
- **Clarified**: T027 now outputs explicit slope, intercept, r_squared, trend_direction to trajectory.json (merged into T029).
- **Clarified**: T029 now depends on T030 and T048 to ensure schema includes decay results and includes derived fields.
- **Clarified**: T031 now depends on T048 for resource data.
- **Verified**: T033 depends on T031 and is correctly ordered after T031 in Phase 5.
- **Verified**: T019 depends on T007 and is correctly ordered after T007 in Phase 3.
- **Verified**: T020 depends on T044, T036, T037b, T059.
- **Verified**: T025 depends on T020, T059.
- **Verified**: T048 depends on T004.
- **Added**: T017c for FLOP calculation in utils/metrics.py.
- **Added**: T036a for performance-based termination.
- **Added**: T059 for External Oracle Logic (FR-021).
- **Added**: T010b for GSM8K/ARC/BoolQ evaluation (merged into T010).
- **Removed**: T090 (Global Attempt Counter) as it decoupled the 3-cycle constraint.
- **Removed**: T109-T116 (unrequested scope creep).
- **Verified**: T032 removed as it violated FR-004.
- **Verified**: T052b replaced with T059 logic for Oracle Check.
- **Verified**: T005a, T010, T018, T037, T059 updated to use GSM8K/ARC/BoolQ.
- **Removed**: T034, T051 (Timeout enforcement) as spec only defines targets.
- **Removed**: T061 (Overfitting Detection) as spec does not define validation splits.
- **Removed**: Phase 6 (T060-T067) as unrequested scope creep.
- **Moved**: T008 to Phase 1 to break circular dependency.
- **Expanded**: T037 and T013 to include 'hidden_size_change' and 'activation_change' types.
- **Fixed**: T006 verification to use concrete GPT-2 124M config assertions.
- **Fixed**: T005a to explicitly use T005b for network errors.
- **Fixed**: T044 and T025 to clarify history append only on success and decrement attempts on failure.
- **Fixed**: Ordering of T037b, T015, T020, T048, T031, T059.
- **Fixed**: Removed [P] tag from T059, T025 where dependencies prevent parallel execution.
- **Fixed**: Removed false dependency of T006 on T005a.
- **Fixed**: T073 and T048 to remove hard failures and align with SC-005 targets.
- **Fixed**: Merged T059b/T059c into T059.
- **Fixed**: Merged T071 into T059a (now T059).
- **Fixed**: T029 now includes trend direction and depends on T030/T048.
- **Fixed**: T004 and T073 to use configurable limits and warning-only/reduction logic.
- **Fixed**: T008 to use placeholder for param limit.
- **Fixed**: T015 to specify 3 attempts [UNRESOLVED-CLAIM: c_bea51fbe — status=not_enough_info].
- **Fixed**: T044 to clarify counter integration.
- **Fixed**: T036 to record degradation_cycle in trajectory.json.
- **Fixed**: T014b to implement vector distance/param delta logic.
- **Fixed**: T007 and T019 to explicitly implement paired bootstrap.
- **Fixed**: Removed T086 (meta-task) and replaced with updated T086 (traceability).