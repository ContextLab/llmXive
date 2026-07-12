# Tasks: llmXive follow-up: extending "Agents' Last Exam"

**Input**: Design documents from `/specs/001-llmxive-ale-extension/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this user story belongs to (e.g., US1, US2, US3)
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

- [X] T001 Create project directory structure for `code/`, `tests/`, `data/`, `docs/` as defined in `specs/001-llmxive-ale-extension/plan.md` (`projects/PROJ-840-llmxive-follow-up-extending-agents-last/`)
- [X] T002 Initialize Python project with `llama-cpp-python`, `datasets`, `scikit-learn`, `pandas`, `pyyaml`, `pytest`, `statsmodels` in `requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement deterministic seed pinning utility in `code/utils/seeds.py` (FR-008)
- [X] T004b [P] [FR-008] Extend T004 to include a `verify_pairing` function that generates checksums for task instances and seeds; this function MUST be called by T015 before data generation to ensure strict pairing (FR-005 precondition).
- [X] T005 [P] Implement configuration loader in `code/utils/config.py` to handle model paths and checkpoint intervals, loading from a YAML schema defined in `code/utils/config_schema.yaml`.
- [X] T015 [P] [US1] Create synthetic ALE execution traces with known ground truth using `code/data/generator.py` (Assumption: Dataset availability) - **MUST precede test tasks**. This task MUST call `verify_pairing` from T004b to ensure strict pairing and generate `data/raw/golden_subset.json` with schema: `[trace_id, ground_truth_label, step_state, task_description]`.
- [X] T006 Create base data structures for Execution Trace and Failure Label in `code/data/generator.py` <!-- FAILED: unspecified -->
- [X] T007 Setup logging infrastructure to capture timeouts and memory usage in `code/utils/logging_config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Failure Mode Classification (Priority: P1) 🎯 MVP

**Goal**: Parse ALE logs, reconstruct state, and classify failures as "State Persistence Error" or "Reasoning Deficit" using a local LLM.

**Independent Test**: Can be fully tested by feeding a pre-annotated "golden set" of 10 synthetic traces with known failure modes and verifying the script's classification accuracy against the ground truth labels.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T008 [P] [US1] Contract test for parser normalization in `tests/unit/test_heuristics.py`
- [ ] T009 [P] [US1] Integration test for classification accuracy on golden set in `tests/integration/test_classification_golden.py`

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement ALE log parser in `code/classification/parser.py` to extract environment state and agent actions
- [ ] T011 [US1] Implement Normalization Protocol in `code/classification/heuristics.py` (Float tolerance MUST be exactly **1e-6**, timestamp/ID stripping, reference canonicalization) (FR-001)
- [~] T012 [US1] Implement Task Goal Validator in `code/classification/goal_validator.py` using a **deterministic regex-based template matcher** to extract static constraints (file paths, variable names) from `task_description`. **Note: This explicitly overrides the Plan.md's 'local LLM' approach for this step to satisfy FR-007.** (FR-007)
- [~] T014 [US1] Implement Local LLM classifier in `code/classification/semantic_classifier.py` using `llama-cpp-python` (Q4_K_M) to label failures, **with deterministic seed pinning** (FR-002, FR-008) <!-- FAILED: unspecified -->
- [~] T013 [US1] Implement State Reconstruction validator in `code/classification/state_validator.py` to calculate accuracy against `data/raw/golden_subset.json` (generated by T015) using the schema defined in T015 (FR-009)
- [~] T013b [US1] **Gate**: Execute State Reconstruction validation in `code/classification/state_validator.py`, parse the JSON output for `reconstruction_accuracy`, and **halt pipeline** if accuracy < 0.95 (FR-009)
- [~] T016 [US1] Generate JSON report with `state_persistence_count`, `reasoning_deficit_count`, `total_failures`, `classification_confidence`, and **calculate the proportion** of State Persistence Errors (SC-001)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Context Checkpointing Intervention (Priority: P2)

**Goal**: Implement a lightweight wrapper around a 7B model to regenerate and inject state summaries every N steps.

**Independent Test**: Can be tested by running a fixed set of short ALE tasks with the checkpointing wrapper enabled vs. disabled. and comparing the "Step Success Rate" for the specific steps where state persistence is critical.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T017 [P] [US2] Contract test for checkpoint injection logic in `tests/unit/test_wrapper.py`
- [~] T018 [P] [US2] Integration test for memory limit compliance (defined threshold) in `tests/integration/test_memory_limit.py`

### Implementation for User Story 2

- [~] T019 [US2] Implement Context-Checkpointing wrapper in `code/intervention/wrapper.py` to force state summary regeneration at configurable interval N (FR-003)
- [~] T020 [US2] Implement summary compression heuristic to handle context window limits in `code/intervention/wrapper.py`
- [~] T021 [US2] Implement CPU-only task runner in `code/intervention/runner.py` using `llama-cpp-python` with Q4_K_M quantization (FR-004)
- [~] T022 [US2] Add memory monitoring and timeout logging in `code/intervention/runner.py` to ensure execution stays within 7GB RAM and 6h limit
- [~] T023 [US2] Execute baseline tasks (no wrapper) and intervention tasks (wrapper enabled) on the synthetic dataset. **Output**: Generate `data/processed/baseline_results.json` and `data/processed/intervention_results.json` containing pass/fail outcomes per task. (FR-004, FR-008) <!-- ATOMIZE: requested -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Reporting (Priority: P3)

**Goal**: Aggregate pass rates, perform statistical significance testing (McNemar's), and generate a final report with sensitivity analysis.

**Independent Test**: Can be tested by providing the system with two sets of binary outcomes (Pass/Fail) for the same tasks (Baseline vs. Intervention) and verifying the calculated p-value matches the expected result from a standard statistical library.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T024 [P] [US3] Contract test for statistical significance calculation in `tests/unit/test_stats.py`
- [~] T025 [P] [US3] Integration test for sensitivity analysis output in `tests/integration/test_sensitivity.py` <!-- FAILED: unspecified -->

### Implementation for User Story 3

- [~] T026 [P] [US3] Implement **McNemar's test** (primary) for paired binary outcomes in `code/analysis/stats.py`. **Note: This explicitly replaces the Plan.md's 'Mixed-Effects Logistic Regression' to satisfy FR-005.** (FR-005)
- [~] T027 [US3] Implement multiple-comparison correction (Bonferroni or FDR) in `code/analysis/stats.py`
- [~] T028 [US3] Implement sensitivity analysis module in `code/analysis/sensitivity.py` to test **exactly N=1, N=3, and N=5**. This task MUST re-run the experiment logic (T023) for each N value or consume pre-generated data for these specific intervals, then report the variation in pass rates. (FR-006)
- [~] T029 [US3] Generate final report including p-values, pass rates, and sensitivity analysis in `docs/report.md`
- [~] T031 [P] Documentation updates in `docs/` including `quickstart.md`
- [~] T032 Refactor `code/classification/heuristics.py` to remove magic numbers and hardcode constants in config
- [~] T033 Refactor `code/intervention/wrapper.py` to enforce context window limits explicitly
- [~] T034 [P] Additional unit tests in `tests/unit/` <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->
- [~] T035 Run quickstart.md validation <!-- FAILED: unspecified -->

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T031 [P] Documentation updates in `docs/` including `quickstart.md`
- [~] T032 Refactor `code/classification/heuristics.py` to remove magic numbers and hardcode constants in config
- [~] T033 Refactor `code/intervention/wrapper.py` to enforce context window limits explicitly
- [~] T034 [P] Additional unit tests in `tests/unit/`
- [~] T035 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
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
Task: "Contract test for parser normalization in tests/unit/test_heuristics.py"
Task: "Integration test for classification accuracy on golden set in tests/integration/test_classification_golden.py"

# Launch all models for User Story 1 together:
Task: "Implement ALE log parser in code/classification/parser.py"
Task: "Implement Normalization Protocol in code/classification/heuristics.py"
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
- **Critical**: T013b is a blocking gate; do not proceed to T014 until T013b passes.
- **Critical**: T028 must test exactly N=1, N=3, N=5.
- **Critical**: T026 must use McNemar's test or Bootstrap, not Mixed-Effects Logistic Regression.
- **Critical**: T004b and T015 enforce strict pairing as a precondition before data generation; T030 has been removed.
- **Critical**: T012 uses a deterministic regex matcher, overriding Plan.md's LLM approach for FR-007 compliance.
- **Critical**: T011 uses exactly 1e-6 tolerance.