# Tasks: Claw-SWE-Bench Reproduction & Validation

**Input**: Design documents from `/specs/001-reproduce-claw-swe-bench/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directories: `src/evaluators`, `src/loaders`, `src/utils`, `src/config`, `tests/`
- [X] T001b [P] Initialize `__init__.py` files in all created directories
- [X] T001c [P] Create `.gitignore` with Python/venv patterns

- [X] T002a [P] Create `pyproject.toml` with Python 3.9+ requirement
- [X] T002b [P] Create `requirements.txt` with dependencies (`swebench`, `datasets`, `huggingface_hub`, `pandas`, `pyyaml`, `requests`, `tenacity`, `scipy`)

- [X] T003a [P] Create `.flake8` config file
- [X] T003b [P] Create `pyproject.toml` [tool.black] section
- [X] T003c [P] Add pre-commit hook configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Execution Order**: Strictly follow sub-phase order: 2.1 → 2.2 → 2.3 → 2.4.

### 2.1: Submodule & Validation
- [X] T004a [P] Add git submodule for `external/claw-swe-bench`
- [X] T004b [P] Implement `src/utils/submodule_validator.py` to check commit hash against a config constant (FR-007)
  - **⚠️ DEPENDS ON**: T004a

### 2.2: Dataset Loading
- [X] T005 [P] Create `src/config/multilingual.yaml` for full dataset configuration (FR-001)
- [X] T006 [P] Create `src/config/verified.yaml` for Lite subset configuration (FR-002)

- [X] T007a [P] Implement dataset loading logic using `datasets.load_dataset` in `src/loaders/dataset_loader.py`
- [X] T007b [P] Implement instance validation and filtering logic in `src/loaders/dataset_loader.py`
- [X] T007c Implement instance validation and filtering logic in `src/loaders/dataset_loader.py` (FR-004)
  - **⚠️ DEPENDS ON**: T004b (submodule must exist to validate paths), T005/T006 (config files)

### 2.3: Utilities
- [X] T008 [P] Implement `src/utils/retry_utils.py` with exponential backoff for API rate limits (HTTP 429) (FR-004, Edge Cases)

- [X] T009a [P] Implement token counting logic in `src/utils/cost_calculator.py`
- [X] T009b [P] Implement logic to distinguish cached vs. actual token usage for cost estimation in `src/utils/cost_calculator.py` (FR-003, Edge Cases)

### 2.4: Orchestration
- [X] T010a [P] Implement timeout enforcement logic in `src/evaluators/orchestrator.py`
- [X] T010b [P] Implement partial result saving mechanism in `src/evaluators/orchestrator.py`
- [X] T010c Implement job scheduling loop in `src/evaluators/orchestrator.py` (FR-006)
  - **⚠️ DEPENDS ON**: T007 (dataset loading), T008 (retry logic), T009 (cost logic), T004 (submodule existence)

- [X] T011 [P] Create `src/evaluators/adapters/base.py` abstract base class for adapters

**Checkpoint**: Foundation ready - Pre-Execution Validation (Phase 6) must run next.

---

## Phase 6: Pre-Execution Validation & Harness Verification (Plan Phase 0)

**Purpose**: Ensure dataset integrity and harness correctness before main execution.
**⚠️ BLOCKS**: All User Story phases (3, 4, 5) depend on this phase passing.
**Execution Order**: Must run after Phase 2, before Phase 3.

- [X] T034a [P] Implement dataset loading in `scripts/verify_dataset.py`
- [X] T034b [P] Implement instance count verification in `scripts/verify_dataset.py` against Spec SC-005 (350) AND Plan correction (100-150).
  - **Logic**: If count != 350 AND count != 100-150, fail. If count == 350, warn about Plan discrepancy. If count == 100-150, warn about Spec discrepancy. Document discrepancy in output log.
  - **⚠️ DEPENDS ON**: T007a, T005
- [X] T034c [P] Implement language distribution analysis in `scripts/verify_dataset.py`

- [X] T035a [P] Implement ground-truth instance selection in `scripts/validate_harness.py`
- [X] T035b [P] Implement harness execution logic in `scripts/validate_harness.py` (Plan Phase 0.5)
- [X] T035c [P] Implement result validation and reporting in `scripts/validate_harness.py`

- [X] T036 [P] Add CI pre-check step to run T034 and T035 before triggering main evaluation

**Checkpoint**: Validation passed - User Story implementation can now begin.

---

## Phase 3: User Story 1 - Execute Full Benchmark Pipeline (Priority: P1) 🎯 MVP

**Goal**: Execute `run_eval.py` against the full SWE-bench multilingual dataset using the vendored OpenClaw harness and default adapter, generating `results/full_eval_summary.json`.

**Independent Test**: CI runner executes script, processes instances, and outputs `results/full_eval_summary.json` with `pass@1` metric within 6 hours.
**⚠️ DEPENDS ON**: Phase 2 and Phase 6 must be complete.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tests are written as **Mock-based stubs** first to define the interface (TDD). Implementation tests follow after modules exist.
> **⚠️ DEPENDS ON**: T012 depends on T007 (dataset_loader); T013 depends on T015 (run_eval.py).

- [X] T012 [P] [US1] Integration test for dataset loading and validation in `tests/integration/test_dataset_loader.py`
  - **⚠️ DEPENDS ON**: T007
- [X] T013 [P] [US1] Contract test for `run_eval.py` output schema in `tests/contract/test_output_schema.py`
  - **⚠️ DEPENDS ON**: T015

### Implementation for User Story 1

- [X] T014 [US1] Implement `src/evaluators/adapters/minimal_adapter.py` (default adapter)
- [X] T015a [US1] Implement CLI argument parsing (argparse) in `src/evaluators/run_eval.py`
- [X] T015b [US1] Implement main evaluation loop with error skipping in `src/evaluators/run_eval.py` (FR-001, FR-004)
- [X] T015c [US1] Implement result aggregation and logging in `src/evaluators/run_eval.py`
- [X] T015d [US1] Implement dynamic stopping rule and subset selection logic to enforce 6-hour timeout in `src/evaluators/run_eval.py` (FR-001, US-1 Acceptance 1)
  - **⚠️ DEPENDS ON**: T010 (orchestrator timeout logic)
- [X] T016 [US1] Implement logic to handle repository cloning failures gracefully: log 'data_missing' tag, remove from active processing list, and record in summary exclusion count (Edge Cases)
- [X] T017 [US1] Implement logic to generate `patches/*.diff` files for successful agent runs (US-1 Acceptance 3)
- [X] T018a [US1] Implement Pass@1 calculation logic in `src/evaluators/run_eval.py`
- [X] T018b [US1] Implement JSON serialization and file writing for `results/full_eval_summary.json` in `src/evaluators/run_eval.py` (FR-005)
- [X] T019 [US1] Add logging for instance success/failure and skip reasons in `logs/eval_run.log`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Adapter & Model Sweep (Priority: P2)

**Goal**: Run comparative evaluation between "minimal direct-diff adapter" and "full adapter" using GLM backbone on the `Claw-SWE-Bench Lite` subset.

**Independent Test**: Two runs produce `results/lite_minimal_adapter.json` and `results/lite_full_adapter.json`, and a comparison script reports the delta.
**⚠️ DEPENDS ON**: Phase 2 and Phase 6 must be complete.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for adapter switching logic in `tests/unit/test_adapter_switching.py`
- [X] T021 [P] [US2] Integration test for paired comparison in `tests/integration/test_adapter_comparison.py`

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement `src/evaluators/adapters/full_adapter.py` (FR-002)
- [X] T023 [US2] Update `run_eval.py` to accept `--adapter` flag to switch between minimal and full modes (FR-002)
- [X] T024 [US2] Implement logic to restrict execution to `verified.yaml` (a representative subset) for Lite runs (US-2 Acceptance 1 & 2)
- [X] T025 [US2] Implement `src/utils/stats_utils.py` to calculate Pass@1 delta and flag if delta < 5% (configurable in `config.yaml`).
  - **Rationale**: 5% threshold defined in Plan Phase 2.1 (Statistical Analysis) as the tolerance for "substantial" difference.
- [X] T026 [US2] Generate `results/lite_full_adapter.json` and `results/lite_minimal_adapter.json` with specific metrics (FR-005)
- [X] T027a [US2] Implement data loading for adapter results in `scripts/compare_adapters.py`
- [X] T027b [US2] Implement McNemar's test calculation in `scripts/compare_adapters.py`
- [X] T027c [US2] Implement delta calculation and reporting logic in `scripts/compare_adapters.py` (Plan Phase 2.1)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cost & Efficiency Accounting (Priority: P3)

**Goal**: Capture and report total API cost and runtime duration for each agent run.

**Independent Test**: Evaluation run produces `results/cost_summary.csv` with `instance_id`, `api_cost_usd`, and `wall_time_seconds`.
**⚠️ DEPENDS ON**: Phase 2 and Phase 6 must be complete.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for cost calculation logic in `tests/unit/test_cost_calculator.py`

### Implementation for User Story 3

- [X] T029 [US3] Integrate `src/utils/cost_calculator.py` into `run_eval.py` to log per-instance costs (FR-003)
- [X] T030 [US3] Implement logic to track `wall_time_seconds` per instance and total run (FR-003)
- [X] T031 [US3] Generate `results/cost_summary.csv` with required columns (US-3 Acceptance 1)
- [X] T032 [US3] Implement logic to record `termination_reason: timeout` and partial cost if CI limit hit (US-3 Acceptance 3)
- [X] T033a [US3] Implement CSV data loading and aggregation in `scripts/summarize_costs.py`
- [X] T033b [US3] Implement cost calculation logic in `scripts/summarize_costs.py`
- [X] T033c [US3] Implement comparison with paper claims and reporting in `scripts/summarize_costs.py` (Plan Phase 2.2)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037a [P] Update `docs/quickstart.md` with installation and usage instructions
- [X] T037b [P] Update `docs/api.md` with API documentation
- [X] T037c [P] Update `docs/architecture.md` with system architecture

- [X] T038a [P] Refactor duplicate code in adapters
- [X] T038b [P] Optimize memory usage in dataset loading
- [X] T038c [P] Add type hints to all public functions

- [X] T039 [P] Additional unit tests for retry logic in `tests/unit/test_retry_utils.py`
- [X] T040 [P] Security hardening for API key handling in environment variables
- [X] T041 Run `quickstart.md` validation to ensure all steps work in CI

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Pre-Execution (Phase 6)**: Depends on Foundational (Phase 2) - **BLOCKS Phase 3, 4, 5**
- **User Stories (Phase 3+)**: All depend on Foundational (Phase 2) AND Pre-Execution (Phase 6)
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) AND Phase 6 - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) AND Phase 6 - Reuses `run_eval.py` from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) AND Phase 6 - Integrates cost logic into `run_eval.py`

### Within Each User Story

- Tests (if included) are written as Mock-based stubs first to define the interface, then implementation tests after modules exist.
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks within a sub-phase marked [P] can run in parallel (except where dependencies explicitly noted)
- Once Foundational and Phase 6 are complete, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for output schema in tests/contract/test_output_schema.py"
Task: "Integration test for dataset loading in tests/integration/test_dataset_loader.py"

# Launch foundational tasks for US1 in parallel (after Phase 2/6):
Task: "Implement minimal_adapter.py"
Task: "Implement run_eval.py entry point"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 6: Pre-Execution Validation
4. Complete Phase 3: User Story 1 (Full dataset run)
5. **STOP and VALIDATE**: Test User Story 1 independently with `run_eval.py`
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Complete Phase 6 → Validation ready
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo (Adapter comparison)
5. Add User Story 3 → Test independently → Deploy/Demo (Cost accounting)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Complete Phase 6 together
3. Once Foundational and Phase 6 are done:
   - Developer A: User Story 1 (Core execution)
   - Developer B: User Story 2 (Adapter comparison)
   - Developer C: User Story 3 (Cost accounting)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (after modules exist)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only CI (limited cores, constrained RAM). No GPU, no 8-bit/4-bit quantization, no large model training. Use sampled datasets or small models if needed.