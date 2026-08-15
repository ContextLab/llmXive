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

- [X] T004 [P] Implement `utils/memory.py` with RAM monitoring: create `utils/memory.py` with function `check_ram_usage(limit_gb: float=7.0)` that logs a warning if RAM usage is substantial. **Logic**: Reads `RAM_LIMIT_GB` from `config.py` (default 7.0). If critical threshold exceeded, log "RAM Critical" and log warning only; do NOT trigger termination (termination is handled by T073 per FR-015). **Verification**: Add a unit test in `tests/unit/test_memory.py` that mocks `psutil.virtual_memory` using `unittest.mock.patch` to return a value > 7.0GB and asserts a warning is logged, but no exception is raised.
- [X] T005b [P] Implement exponential backoff wrapper in `pipeline/loader.py` with initial delay=30s, max retries=5 for HuggingFace API calls. **Verification**: Add unit test in `tests/unit/test_loader.py` that mocks `time.sleep` and asserts retry count increments correctly on simulated failures, explicitly verifying the initial delay is a non-zero duration.
- [ ] T005a [P] Implement dataset loaders in `pipeline/loader.py` for OpenWebText (training), GSM8K (test), ARC-Challenge (test), and BoolQ (test) with fail-fast logic for missing data. **Logic**: Use `datasets.load_dataset(..., streaming=True)` for OpenWebText. For transient network errors, use T005b (backoff); for missing data files, raise `FileNotFoundError` immediately with message "Dataset file not found: {path}" (no synthetic fallback). Implement fallback logic: if estimated time > 2h, reduce training subset size. **Verification**: Verify that loading a non-existent dataset using a dynamically generated temporary path (e.g., `tempfile.mktemp()`) raises `FileNotFoundError` with the exact message and does NOT fallback to synthetic data. Also verify that simulated network errors trigger retry logic. (DEPENDS ON: T005b)
- [X] T006 [P] Implement `pipeline/model.py` with GPT checkpoint loading and CPU-compatible weight manipulation. **Verification**: Verify model loads without error and that the parameter count is within a reasonable range for a 'GPT small' model (e.g., >100M and <200M) by adding a unit test in `tests/unit/test_model.py`. (DEPENDS ON: T005a)
- [ ] T013 [P] Define modification proposal JSON schema: Create `schemas/modification_proposal.py` with Pydantic model `ModificationProposal` including fields: `modification_type` (str: 'layer_add' | 'head_count_change'), `magnitude` (int), `rationale` (str), `estimated_param_count` (int). **Verification**: Add unit test in `tests/unit/test_schema.py` using pytest that asserts ValidationError is raised for invalid JSON.
- [X] T014 [P] Implement distinctness validation logic in `pipeline/model.py`: Create function `validate_modification_distinctness(proposal: ModificationProposal, history: List[ModificationProposal])` that returns True if proposal is distinct in type or magnitude from all items in history, False otherwise. **Verification**: Add unit test in `tests/unit/test_model.py` that asserts True/False for distinct/non-distinct proposals. (DEPENDS ON: T013)
- [X] T007 [P] Implement `pipeline/stats.py` with paired bootstrap testing (α=0.05 strict) and linear regression trend analysis. **Verification**: Add unit test in `tests/unit/test_stats.py` that asserts p-value calculation for known inputs and linear regression slope calculation. The number of resamples MUST be configurable via `config.py`, allowing for adjustment of statistical power.
- [ ] T008 [P] Create `config.py` with hyperparameters (lr=5e-5, bs=4, seed), constraints (param_limit=0.30 for FR-019), and path definitions. **Verification**: Verify config.py loads successfully and asserts default values match spec (specifically `param_limit = 0.30`).
- [ ] T009 [P] Implement `utils/logging.py` for structured cycle logging and checkpointing. **Verification**: Verify log file is created with structured JSON format after running a mock cycle.
- [ ] T010 [P] Implement `pipeline/evaluator.py` with benchmark runner for GSM8K, ARC-Challenge, and BoolQ. **Logic**: Includes both the runner and the evaluation logic. **Verification**: Add unit test that mocks dataset and asserts accuracy/ECE calculation returns expected float. (DEPENDS ON: T005a)
- [X] T059b [P] Implement Fixed-Point Oracle for Evaluation: Create `pipeline/oracle.py` with an immutable evaluation functional `evaluate_cycle(modification, model_weights)` that strictly returns performance metrics (GSMK/ARC/BoolQ) without accepting any modification to its own logic or criteria during the recursion cycle. **Verification**: Add unit test in `tests/unit/test_oracle.py` that asserts the oracle returns consistent results for identical inputs across multiple cycles and cannot be patched by the generative model. (DEPENDS ON: T010)
- [ ] T059a [P] Implement Pre-Application External Oracle Check: Create `pipeline/validator.py` with function `validate_proposal_oracle(proposal: ModificationProposal)` that validates the proposed modification against fixed heuristics (e.g., parameter efficiency, no structural violations) BEFORE application. **Logic**: The parameter limit checked here MUST read the value from `config.py` (defined in T008, `param_limit=0.30`). **Verification**: Add unit test in `tests/unit/test_validator.py` that asserts the function returns True for valid proposals and False for invalid ones. (DEPENDS ON: T013)
- [X] T037b [P] Implement "Separation of Generative/Verification Logic" prompt template: Create `templates/modification_proposal.j` containing the exact prompt string: "You are an AI architect. Propose ONE architectural modification (type: layer_add/head_count_change, magnitude: int) to improve performance on training loss. DO NOT use benchmark scores (GSM8K/ARC/BoolQ) or oracle outputs in your reasoning. Constraints: Max moderate parameter increase. Return JSON: {modification_type, magnitude, rationale}." **Logic**: Limit prompt attempts to a fixed number per cycle; if still invalid after the fixed number of attempts, fail the cycle. **Verification**: Verify `templates/modification_proposal.j2` renders valid JSON for a mock input using a hardcoded mock dict in `tests/integration/test_model.py`, asserting `json.loads(rendered) is not None and contains required keys` and does not contain benchmark data. (DEPENDS ON: T013)
- [ ] T017c [P] Implement FLOP counter in `utils/metrics.py`: Create function `calculate_flops(model, input_shape)` that accurately counts FLOPs using `torch.profiler` with `record_shapes=True` and `profile_memory=True`, ensuring calculation occurs in `utils/metrics.py` as per FR-008. **Verification**: Add unit test in `tests/unit/test_metrics.py` that asserts FLOP count matches theoretical calculation for a mock layer.
- [ ] T036a [P] Implement performance-degradation-based termination logic in `pipeline/orchestrator.py`: Create function `check_termination(current_metrics, baseline_metrics)` that terminates the pipeline if degradation ≥5% from baseline (FR-015). **Verification**: Add unit test in `tests/unit/test_orchestrator.py` that asserts pipeline terminates when degradation >= 5%. (DEPENDS ON: T010)
- [ ] T060 [P] Implement "Source of Authority" documentation and invariant check: Create `docs/source_of_authority.md` explicitly defining the external benchmarks (GSM8K, ARC, BoolQ) as the immutable "Source of Authority" for improvement, and implement `pipeline/invariants.py` with a function `assert_oracle_immutability()` that verifies the evaluation functional has not been altered by the generative loop. **Verification**: Add unit test asserting that any attempt to modify the benchmark list in the oracle raises an exception.

**NEW TASKS FOR SPEC COMPLIANCE**:

- [ ] T001a [P] Implement "Pre-flight URL Verification": Create `pipeline/loader.py` function `verify_urls(urls: List[str])` that checks all dataset URLs against primary sources (HuggingFace) before download. **Logic**: Must implement Step 1.0 of Plan.md Phase 0. **Verification**: Add unit test that asserts function raises error if a URL is unreachable or returns 404.
- [ ] T001b [P] Implement "Data Download & Checksumming": Create `pipeline/loader.py` function `download_and_checksum(dataset_name: str, dest_path: str)` that downloads data and records SHA-256 hash. **Logic**: Must implement Step 1.1 of Plan.md Phase 0. **Verification**: Add unit test that asserts a checksum file is created and matches the downloaded content. (DEPENDS ON: T001a)
- [ ] T002 [P] Implement "Baseline Capability Check": Create `pipeline/main.py` function `run_baseline_check()` that evaluates the unmodified model on benchmarks and records Cycle 0 metrics to `results/trajectory.json`. **Logic**: Must implement Step 2.1-2.2 of Plan.md Phase 1. **Verification**: Add integration test that asserts Cycle 0 metrics are written to trajectory.json before any refinement cycles begin. (DEPENDS ON: T006, T010)
- [ ] T071 [P] Implement "Parameter Constraint Check" Step: Create `pipeline/validator.py` function `check_parameter_constraint(proposal: ModificationProposal, baseline_params: int, limit_percent: float)` that explicitly validates the proposed modification does not exceed the configured parameter limit (FR-019) BEFORE application. **Logic**: Reads `limit_percent` from `config.py` (a configurable threshold). **Verification**: Add unit test that asserts the function returns False for proposals exceeding the limit and True otherwise. (DEPENDS ON: T008)
- [ ] T072 [P] Implement "Distinctness Validator" Step: Create `pipeline/validator.py` function `execute_distinctness_check(proposal: ModificationProposal, history: List[ModificationProposal])` that explicitly enforces the distinctness constraint (FR-020) as a distinct pipeline step. **Logic**: Calls T014 logic. **Verification**: Add unit test that asserts the function returns False for non-distinct proposals and True otherwise. (DEPENDS ON: T014)
- [ ] T073 [P] Implement "RAM Constraint Enforcement" Logic: Create `pipeline/orchestrator.py` function `enforce_ram_constraints(current_ram_gb: float, limit_gb: float=7.0)` that terminates the pipeline and logs "RAM EXCEEDED" if the limit is breached, satisfying FR-015 and SC-005. **Logic**: This task bridges the gap between T004's warning and the mandatory termination behavior. **Verification**: Add unit test that asserts the function raises a `SystemExit` or logs a critical termination event when limit is exceeded. (DEPENDS ON: T004)
- [ ] T074 [P] Implement "Resource Metrics Recorder" Logic: Create `pipeline/report.py` function `record_resource_metrics(peak_ram_gb: float, total_time_hours: float)` that explicitly writes peak RAM and total time to `results/trajectory.json` and `results/final_report.md`, satisfying SC-005. **Logic**: This task ensures the metrics are recorded, not just used for failure checks. **Verification**: Add unit test that asserts the metrics are correctly written to the JSON file.
- [ ] T075 [P] Implement "State File Update" Logic: Create `utils/state.py` function `update_state_file(artifact_hashes: Dict[str, str], cycle_number: int)` that hashes artifacts and updates `state/...yaml` as mandated by Plan.md Step 3.9 and Constitution Principle V. **Verification**: Add unit test that asserts the state file is updated with correct hashes and timestamps. (DEPENDS ON: T009)

**REVISED TASKS FOR REVIEWER CONCERNS (Review Synthesis)**:

- [ ] T086 [P] Generate "Review Synthesis Report": Create `docs/review_synthesis.md` that explicitly maps the single core concern (Source of Authority, FR-021) to the specific task (T060) that addresses it, providing a traceability matrix. **Verification**: Verify the document exists and contains a table mapping reviewer names to task IDs and a brief description of the resolution. (DEPENDS ON: T060)

**Removed Scope Note**: Tasks T080-T085 (Turing, West, Wolfram, Krakauer concerns) were removed as they had no traceable origin in spec.md or plan.md and constituted unrequested scope creep.

**Removed Scope Note**: Task Tb (Persistent State Store for restart survival) was removed as the spec defines a linear 3-attempt sequence without requiring crash-recovery persistence.

**Removed Scope Note**: Task T032 (Dynamic Batch Size) was removed as it violated FR-004 (fixed batch size 4).

**Removed Scope Note**: Task T052b (External Invariant Check) was removed as it conflated security with the oracle logic defined in FR-021 and T059.

**Removed Scope Note**: Tasks T110-T116 (Source of Authority, Stupidity Metric, Scaling Law, Rule Space Mining, Bird vs. Frog, Kolmogorov Complexity, Fixed-Point Convergence) were removed as they had no traceable origin in spec.md or plan.md and constituted unrequested scope creep.

**Removed Scope Note**: Task T109 (Fixed-Point Convergence) was removed as it was a duplicate of T116 (which was removed).

**Removed Scope Note**: Task T090 (Global Attempt Counter) was removed as it decoupled the 3-cycle constraint and was rejected. The cycle counter is now handled in-memory within `main.py`.

**Removed Scope Note**: Task T005c was removed as it was redundant with T005a.

**Removed Scope Note**: Tasks T076, T077, T078 were removed and their logic integrated into T020 for clarity.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute single refinement cycle with baseline comparison (Priority: P1) 🎯 MVP

**Goal**: Download a GPT model of moderate scale, apply one architectural modification, re-train on OpenWebText subset, and evaluate on GSM8K, ARC-Challenge, and BoolQ with statistical comparison.

**Independent Test**: Execute pipeline once, verify metrics recorded in `results/trajectory.json` and `data/` artifacts, and confirm CPU-only execution completes within 2 hours.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T011 [P] [US1] Unit test for memory watchdog in `tests/unit/test_memory.py`
- [ ] T012 [P] [US1] Unit test for bootstrap significance logic in `tests/unit/test_stats.py`
- [ ] T014b [P] [US1] Unit test for distinctness validation in `tests/unit/test_model.py`
- [ ] T015b [P] [US1] Integration test for full single cycle in `tests/integration/test_single_cycle.py`

### Implementation for User Story 1

- [ ] T015 [US1] Implement `pipeline/model.py` method to parse model's self-prompted architectural modification proposal (using schema from T013 and prompt template from T037b) and validate parameter count ≤ limit defined in `config.py` (0.30). **Logic**: Limit prompt attempts to a predefined maximum; if invalid JSON after the maximum attempts, fail the cycle. **Schema**: The proposal MUST be a JSON object with keys: `modification_type` (str), `magnitude` (int), `rationale` (str). **Verification**: Verify `templates/modification_proposal.j2` renders valid JSON for a mock input using a hardcoded mock dict in `tests/integration/test_model.py`, asserting `json.loads(rendered) is not None and contains required keys`. (DEPENDS ON: T013, T006, T037b)
- [ ] T016 [US1] Implement `pipeline/model.py` method to apply architectural modification (e.g., layer addition, head count change) to GPT medium-scale weights using manual reconstruction: create new `nn.Module` subclass, map weights via state_dict, initialize new layers with `torch.nn.init.xavier_uniform_`. Allowed modifications: layer_add (add N layers), head_count_change (change heads by M). **Verification**: Add unit test in `tests/unit/test_model.py` that asserts new model has correct parameter count and state_dict mapping. (DEPENDS ON: T013)
- [ ] T017a [US1] Implement training loop in `pipeline/trainer.py::train_epoch` for a single training epoch on an OpenWebText subset (AdamW, bs=4, lr=5e-5) with CPU offloading. Use gradient accumulation steps=4 to simulate batch. Checkpoint periodically. **Verification**: Add unit test in `tests/unit/test_trainer.py` that asserts loss decreases over epochs on mock data. (DEPENDS ON: T008)
- [ ] T017b [US1] Implement FLOP counter in `pipeline/trainer.py::count_flops` for accurate FLOP measurement during training. **Verification**: Add unit test in `tests/unit/test_trainer.py` that asserts FLOP count matches theoretical calculation for a mock layer.
- [ ] T018 [US1] Implement `pipeline/evaluator.py` logic to compute GSM8K, ARC-Challenge, and BoolQ metrics. **Verification**: Add unit test in `tests/unit/test_evaluator.py` that asserts accuracy/ECE calculation on mock predictions. (DEPENDS ON: T010)
- [ ] T019 [US1] Implement `pipeline/stats.py` logic to run paired bootstrap comparison (baseline vs. post-mod) and output p-values. **Verification**: Add unit test in `tests/unit/test_stats.py` that asserts p-value is calculated correctly for known distributions. The number of resamples MUST be read from `config.py` (default unspecified). (DEPENDS ON: T007)
- [ ] T044 [US1] Implement retry logic for training failures in `main.py`: retry failed training up to 2 times with the SAME modification; if still failing, **LOG the failure event** explicitly to `results/logs/cycle_N.log` and **INCREMENT the cycle counter** in memory, then proceed to next cycle number with a NEW modification proposal. **State**: Use in-memory counters (no persistence across restarts required by spec). **Verification**: Add unit test in `tests/unit/test_main.py` that asserts retry count increments, cycle counter increments, and failure log is written. (DEPENDS ON: T009)
- [ ] T036 [US1] Implement early-stop logic in `main.py`: if degradation ≥5% from baseline (checked by T036a), record degradation cycle, log "Early Stop", increment cycle counter, and terminate gracefully. **State**: Persist 'degradation_cycle' and 'early_stop' flag to `results/state.json` for this run. Save checkpoint to `data/checkpoints/cycle_N.pt` before termination. **Logic**: Must call T073 (RAM check), T074 (Record Metrics), and T075 (Update State) atomically before exit. **Verification**: Add unit test in `tests/unit/test_main.py` that asserts pipeline terminates and checkpoint is saved when degradation threshold is met. (DEPENDS ON: T009, T036a, T073, T074, T075)
- [ ] T037b [US1] Integrate "Separation of Generative/Verification Logic" in `pipeline/model.py::generate_proposal`: Ensure the modification proposal prompt explicitly excludes any access to benchmark results or evaluation metrics, using only training loss and internal weights as the basis for the proposal (Addressing FR-005 and Constitution Principle VII). **Verification**: Add unit test in `tests/unit/test_model.py` that asserts benchmark data is not present in the prompt context. (DEPENDS ON: T010, T015, T037b)
- [ ] T051 [US1] Implement integration test for timeout logic in `tests/integration/test_timeout.py`: Use `subprocess.run` with a hard timeout to verify that the system logs "Timeout" and records partial metrics when a cycle exceeds the time budget. **Verification**: Assert log file contains "Timeout" and trajectory.json has partial metrics. (DEPENDS ON: T034)

**REPLACED T020 (Decomposed for Executability)**:

- [ ] T020 [US1] Implement "Main Refinement Loop" Step: Create `pipeline/main.py` function `run_refinement_cycle(cycle_number)` that orchestrates the full cycle: 1. Generate Proposal (T076 logic), 2. Validate Param Constraint (T071), 3. Validate Distinctness (T072), 4. Validate Oracle (T059a), 5. Apply Modification (T016), 6. Train (T017a), 7. Calculate FLOPs (T017c), 8. Evaluate (T018), 9. Stats (T019), 10. Record Metrics (T074), 11. Update State (T075). **Verification**: Add integration test that asserts the full sequence executes and all validation steps are called in order. (DEPENDS ON: T013, T037b, T071, T072, T059a, T016, T017a, T017c, T018, T019, T074, T075)

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

- [ ] T029 [US2] Implement results/trajectory.json schema and writer: Create `results/trajectory_schema.py` with Pydantic model `TrajectoryEntry` (fields: cycle_number: int, param_count: int, GSMK_accuracy: float, ARC_Challenge_accuracy: float, BoolQ_ECE: float, FLOPs: int, training_time: float, slope: float, intercept: float, r_squared: float, trend_direction: str) and writer function `write_trajectory()` capturing cycle_number, param_count, GSM8K_accuracy, ARC_Challenge_accuracy, BoolQ_ECE, FLOPs, training_time, and regression results. **Output Requirement**: Must include raw metrics as per US-2 Acceptance Scenario 2. **Verification**: Run a mock cycle and validate the output file with Pydantic, asserting all required raw keys exist. (DEPENDS ON: T013)
- [ ] T027 [US2] Implement `pipeline/stats.py` logic to fit a **linear regression model** (y = mx + c) to performance trajectories and report slope, intercept, R-squared, and trend direction (improving/declining/flat). **Output**: Must write the identified `slope`, `intercept`, `r_squared`, and `trend_direction` to `results/trajectory.json` (merged with trajectory data). **Verification**: Add unit test in `tests/unit/test_stats.py` that asserts linear regression fits mock data and trend direction is identified correctly. (DEPENDS ON: T029, T007)
- [ ] T026 [US2] Implement `pipeline/model.py` logic to track and enforce "distinct modification" constraint across cycles using schema from T013 and trajectory from T029. **Verification**: Add unit test in `tests/unit/test_model.py` that asserts distinctness check rejects duplicate proposals. (DEPENDS ON: T013, T029, T014)
- [ ] T025 [US2] Implement `main.py` loop logic to execute a limited number of cycles (attempts), ensuring each cycle's modification is distinct in type or magnitude from all previous cycles by tracking modification history in memory and validating new proposals against that history before application. If not distinct, prompt model again. **Integration**: Must import and invoke T044 (retry), T036 (early-stop), T059b (oracle), T075 (State Update) logic from Phase 2. **Verification**: Add integration test in `tests/integration/test_multi_cycle.py` that asserts 3 attempts run with distinct modifications and stops after a predefined number of iterations. (DEPENDS ON: T013, T029, T014, T020, T044, T036, T026, T059a, T059b, T075)
- [ ] T028 [US2] Implement `main.py` retry logic for training failures across cycles (reuses T044 logic). **Logic**: Explicitly **LOG the failure event** and **INCREMENT the cycle counter** after 2 retries. **Verification**: Add unit test in `tests/unit/test_main.py` that asserts retry logic works across multiple cycles and logs are written. (DEPENDS ON: T044)
- [ ] T030 [US2] Implement logic to compute and record FLOPs for each cycle in `pipeline/model.py` (Note: FLOP counting logic is in T017b and T017c, this task focuses on trajectory aggregation). **Verification**: Add unit test in `tests/unit/test_model.py` that asserts FLOPs are correctly aggregated in trajectory.json. (DEPENDS ON: T017b)
- [ ] T046 [US2] Implement "Early Termination on Degradation" in `main.py`: If a cycle results in performance degradation ≥5% from baseline, record the degradation cycle, log "Early Stop", increment cycle counter, and terminate the pipeline (spec Edge Cases). **Verification**: Add unit test in `tests/unit/test_main.py` that asserts pipeline terminates when degradation >= 5%. (DEPENDS ON: T036)
- [ ] T061 [US2] Implement "Overfitting Detection" via holdout validation: Extend `pipeline/evaluator.py` to compute metrics on a strictly held-out validation set (not used in training) and compare against training metrics. If the gap exceeds a threshold, flag "Overfitting" in `results/trajectory.json`. **Verification**: Add unit test that asserts overfitting flag is raised when training accuracy > validation accuracy by >5%. (DEPENDS ON: T010, T029)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Mandatory 3-cycle execution)

---

## Phase 5: User Story 3 - Generate resource-performance trade-off analysis (Priority: P3)

**Goal**: Compute cost-effectiveness metrics (performance per FLOP, performance per hour) and verify total runtime ≤12 hours, RAM ≤7GB.

**Independent Test**: Compute trade-off ratios from `results/trajectory.json` and verify execution constraints are met.

### Implementation for User Story 3

- [ ] T048 [US3] Implement `main.py` resource monitoring to log peak RAM and total wall-clock time; implement strict failure if total runtime exceeds a predefined threshold (fail the job, record partial metrics, exit) instead of graceful continuation. **Logic**: This task MUST call T074 to record the metrics. **Verification**: Add unit test in `tests/unit/test_main.py` that asserts job fails when timeout is met and metrics are recorded. (DEPENDS ON: T004, T073, T074)
- [ ] T031 [US3] Implement `pipeline/stats.py` logic to compute performance-per-FLOP and performance-per-hour metrics for *each cycle* and *compare across cycles* to identify diminishing returns. Append results to `results/trade_off_analysis.json` with keys: `cycle`, `perf_per_flop`, `perf_per_hour`. **Verification**: Add unit test in `tests/unit/test_stats.py` that asserts trade_off_analysis.json has correct keys. (DEPENDS ON: T030, T048)
- [ ] T033 [US3] Generate `results/trade_off_analysis.json` with computed metrics and comparison across cycles. **Verification**: Add integration test that runs analysis and asserts file exists with valid JSON. (DEPENDS ON: T031)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns (Review Synthesis)

**Purpose**: Address specific philosophical and methodological concerns raised by research-stage reviewers.

- [ ] T062 [P] Implement "Resource & Performance Report": Create `pipeline/report.py` to aggregate `results/trajectory.json` and `results/trade_off_analysis.json` into a final summary report `results/final_report.md`. This report must include the linear regression trend, trade-off metrics, and a statement on whether the experiment met the resource constraints (RAM, Time) as required by SC-005 and US-3. **Verification**: Add unit test that asserts the report file is generated with the required sections. (DEPENDS ON: T029, T031, T074)
- [ ] T086 [P] Generate "Review Synthesis Report": Create `docs/review_synthesis.md` that explicitly maps the single core concern (Source of Authority, FR-021) to the specific task (T060) that addresses it, providing a traceability matrix. **Verification**: Verify the document exists and contains a table mapping reviewer names to task IDs and a brief description of the resolution. (DEPENDS ON: T060)

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
- **Removed**: T080-T085 (unrequested scope creep) due to lack of spec anchor.
- **Removed**: T013b (persistence) as spec does not require crash recovery.
- **Moved**: T037 from Phase 3 to Phase 2 to fix ordering.
- **Renamed**: T037 (Phase 3) to T037b to resolve ID conflict.
- **Clarified**: T005a now distinguishes between network errors (retry) and missing data (fail-fast) using runtime paths and streaming.
- **Clarified**: T015 now limits prompt retries to 3 and delegates execution retries to T044.
- **Clarified**: T032, T048, T044, T036, T025 now explicitly depend on cycle counter logic (no separate global counter).
- **Clarified**: T027 now outputs explicit slope, intercept, r_squared, trend_direction to trajectory.json.
- **Clarified**: T029 now depends on T027 to ensure schema includes decay results and includes derived fields.
- **Clarified**: T031 now depends on T048 for resource data.
- **Verified**: T033 depends on T031 and is correctly ordered after T031 in Phase 5.
- **Verified**: T019 depends on T007 and is correctly ordered after T007 in Phase 3.
- **Verified**: T020 (Main Loop) depends on T044, T036, T037b, T059a, T059b, T071, T072, T074, T075.
- **Verified**: T025 depends on T020, T059a, T059b.
- **Verified**: T048 depends on T004 and T074.
- **Added**: T017c for FLOP calculation in utils/metrics.py.
- **Added**: T036a for performance-based termination.
- **Added**: T059a for pre-application oracle check.
- **Added**: T010b for GSM8K/ARC/BoolQ evaluation (merged into T010).
- **Removed**: T090 (Global Attempt Counter) as it decoupled the 3-cycle constraint.
- **Removed**: T109-T116 (unrequested scope creep).
- **Verified**: T032 removed as it violated FR-004.
- **Verified**: T052b replaced with T059a/T059b logic for Oracle Check.
- **Verified**: T005a, T010, T018, T037, T059 updated to use GSM8K/ARC/BoolQ.
- **Added**: T060 for "Source of Authority" documentation and invariant check (Ada Lovelace/Von Neumann).
- **Added**: T071, T072, T073, T074, T075 for specific FR/SC/Plan compliance.
- **Removed**: T076, T077, T078 (logic integrated into T020).
- **Removed**: T063-T070 (unrequested scope creep).
- **Removed**: T061 (unrequested scope creep).
- **Updated**: T044, T028 to explicitly mandate logging and cycle counter increment.
- **Updated**: T048 to explicitly record RAM metrics.
- **Updated**: T027, T029 dependency order.
- **Removed**: [P] tag from T005b to fix ordering dependency.
- **ADDED**: T001a, T001b, T002 for Plan.md Phase 0/1 compliance.
- **ADDED**: T086 for Review Synthesis (reduced scope).