# Tasks: GateMem Benchmarking Memory Governance

**Input**: Design documents from `/specs/001-gatemem-benchmark/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per `plan.md`)
- Paths shown below assume single project structure defined in `plan.md`

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

- [ ] T001 Create project structure per `plan.md` (mkdir `code/`, `data/raw/`, `data/generated/`, `data/results/`, `tests/`)
- [ ] T002 Initialize Python project with `requirements.txt` (transformers, llama-cpp-python, sentence-transformers, pandas, statsmodels, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` with hyperparameters: `N_VALUES = [2, 4, 8, 16]`, `ITEMS_PER_PRINCIPAL = 500`, `SEEDS = 5`, `MODEL_PATH = "Llama-8B-Instruct.Q4_K_M.gguf"`. Verify by running `python -c "from code.config import N_VALUES; assert N_VALUES == [2, 4, 8, 16]"`.
- [ ] T005 [P] Create `code/data_gen.py` as an empty file with a `generate_context` function stub accepting `n_principals` and `items_per_principal` and returning a list.
- [ ] T006 [P] Create `code/evaluator.py` as an empty file with `evaluate_utility`, `evaluate_leak`, and `evaluate_suppression` function stubs.
- [ ] T007 Create `code/metrics.py` as an empty file with a `calculate_governance_score` function stub accepting a list of results and returning a float.
- [ ] T008 [P] Setup `tests/contract/` directory and `data/schema.yaml` for generated JSON validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Simulate Multi-Principal Memory Injection (Priority: P1) 🎯 MVP

**Goal**: Programmatically generate and inject synthetic memory items from $N$ distinct principals into a single shared context window.

**Independent Test**: A script can be run to generate a substantial set of memory items per principal for a specific $N$ (e.g., $N=4$) and output a single JSON file containing the interleaved context. The test passes if the file exists, contains a sufficient number of items, and the items are tagged with the correct principal ID.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data_gen.py` `generate_context` function to generate synthetic memory items in `Fact: [ID] | Value: [Text]` format (FR-001, FR-007). Ensure unique IDs and correct principal tagging.
- [ ] T013 [US1] Implement `code/data_gen.py` `interleave_context` function to interleave items from $N$ principals into a single context list (FR-002).
- [ ] T014 [US1] Implement `code/data_gen.py` `write_context` function to save `data/generated/context_N{N}_seed{S}.json`.
- [ ] T015 [US1] Implement `code/data_gen.py` `check_overflow` function: detect when total items > 4096 (configurable), log "Context Overflow" event as JSON to `data/results/overflow.log` (Edge Case).
- [ ] T015b [US1] **EXECUTE**: Run `code/data_gen.py` to generate seed data for all N values and seeds, ensuring files exist for T020.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009a [P] [US1] Scaffold test file `tests/unit/test_data_gen.py` with empty test functions (Scaffold-only)
- [ ] T009 [P] [US1] Unit test `test_generate_context_counts` in `tests/unit/test_data_gen.py` verifying item count = $N \times 500$
- [ ] T010a [P] [US1] Scaffold test file `tests/unit/test_data_gen.py` with empty test functions (Scaffold-only)
- [ ] T010 [P] [US1] Unit test `test_generate_context_ids` in `tests/unit/test_data_gen.py` verifying unique IDs and correct principal tags
- [ ] T011a [P] [US1] Scaffold test file `tests/contract/test_generated_schema.py` with empty test functions (Scaffold-only)
- [ ] T011 [P] [US1] Contract test `test_schema_validation` in `tests/contract/test_generated_schema.py` validating JSON structure against `data/schema.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Governance Task Loop (Priority: P1)

**Goal**: Execute a deterministic loop where an open-weight LLM agent processes the shared context and responds to Utility, Access Control, and Active Suppression tasks.

**Independent Test**: A single run with $N=2$ and a pre-defined seed can be executed. The test passes if the system produces a log file containing the appropriate number of response entries per memory item and correctly identifies the principal ID in the prompt.

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/runner.py` `load_model` function to load `llama.cpp` GGUF model in CPU mode (FR-006).
- [ ] T020 [US2] Implement `code/runner.py` `run_task_loop` function: iterate over context items, generate prompts for Utility, Access Control, and Active Suppression (FR-003).
- [ ] T021 [US2] Implement `code/evaluator.py` `evaluate_utility` and `evaluate_leak` using rule-based scoring (Pass/Fail) (FR-004).
- [ ] T022 [US2] Implement `code/evaluator.py` `evaluate_suppression` using `all-MiniLM-L-v2` with $\ge 0.85$ threshold for refusals; logic: Pass if Oracle AND Semantic Verifier pass; Fail otherwise (FR-008, FR-009, SC-002, SC-003).
- [ ] T023 [US2] Implement `code/evaluator.py` `oracle_evaluator` to compare model output against ground-truth context state (JSON input) for Leak metric, outputting boolean leak flag (FR-008).
- [ ] T024 [US2] Implement `code/runner.py` "Active Suppression" logic: detect "Active Suppression" commands, implement suppression (log status), handle ambiguous commands (If command matches `^forget.*unknown$`, log WARNING and skip; else proceed) (Edge Case). Ensure output terminology is "suppressed", not "deleted".
- [ ] T025 [US2] Implement `code/runner.py` `write_results` function to save `data/results/run_N{N}_seed{S}.log` with structured JSON entries.
- [ ] T025b [US2] **EXECUTE**: Run `code/runner.py` for all N values and seeds to produce log files required for T028.

### Tests for User Story 2

- [ ] T016 [P] [US2] Unit test `test_prompt_construction` in `tests/unit/test_runner.py` verifying correct inclusion of context and task type
- [ ] T017 [P] [US2] Unit test `test_rule_evaluator_regex` in `tests/unit/test_evaluator.py` verifying keyword detection for "access denied"
- [ ] T018 [P] [US2] Integration test `test_inference_cpu` in `tests/integration/test_inference.py` verifying CPU-only inference completes without CUDA errors

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Compute Governance Metrics & Statistical Significance (Priority: P2)

**Goal**: Aggregate results to calculate core metrics and perform statistical trend analysis (LMM) across $N$.

**Independent Test**: A script can be run against a pre-generated log file containing results for $N \in \{2, 4, 8, 16\}$. The test passes if the script outputs a CSV with the calculated rates and a p-value for the statistical test, without requiring manual calculation.

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/metrics.py` `parse_logs` function to parse `data/results/*.log` files and aggregate Utility, Leak, and Forgetting rates per $N$ (FR-005).
- [ ] T029 [US3] Implement `code/metrics.py` `calculate_governance_score` function to calculate composite Governance Score $G = \frac{U + \text{normalized\_leakage\_term} + \text{Forget}}{3}$

The research question investigates the optimal balance between utility, leakage, and forgetting in machine unlearning. The method involves constructing a composite governance metric to evaluate system performance. References: [Insert Citation]. (FR-005, SC-001, SC-002, SC-003).
- [ ] T030 [US3] Implement `code/metrics.py` `run_lmm` function using `statsmodels` with model formula `Governance ~ N + (|Seed)` to fit Linear Mixed-Effects Model (Plan Correction).
- [ ] T031 [US3] Implement `code/metrics.py` `extract_lmm_results` function to extract p-values, fixed effects, and random effects variance from LMM fit. Calculate Effect Sizes (Cohen's d) and confidence intervals. (Plan Correction).
- [ ] T032 [US3] Implement `code/metrics.py` `calculate_effect_sizes` function to compute Effect Sizes (Cohen's d) and 95% Confidence Intervals using parametric methods or bootstrap if needed.
- [ ] T033 [US3] Implement `code/main.py` CLI with argparse, loops over N and seeds, aggregation logic, and full run orchestration. Verify by running `python code/main.py --help` and `python code/main.py --dry-run`.
- [ ] T034 [US3] Implement `code/metrics.py` `write_summary` function to output `data/results/summary.csv` with columns: `N`, `mean`, `std`, `confidence_interval_lower`, `confidence_interval_upper`, `p_value`, `effect_size` (SC-004).

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test `test_metric_calculation` in `tests/unit/test_metrics.py` verifying Governance Score formula
- [ ] T027 [P] [US3] Unit test `test_lmm_significance` in `tests/unit/test_metrics.py` verifying LMM execution on synthetic data

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `specs/001-gatemem-benchmark/quickstart.md`
- [ ] T036 Code cleanup and refactoring
- [ ] T037 Implement timer wrapper in `code/main.py` that raises an error if execution exceeds a predefined time limit (SC-005).
- [ ] T038 [P] Additional unit tests for edge cases (ambiguous suppression, seed variance) in `tests/unit/`
- [ ] T039 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 execution output

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
# Launch implementation tasks for User Story 1 together:
Task: "Implement code/data_gen.py generate_context function"
Task: "Implement code/data_gen.py interleave_context function"

# Launch tests for User Story 1 together (after implementation scaffolding):
Task: "Unit test test_generate_context_counts in tests/unit/test_data_gen.py"
Task: "Unit test test_generate_context_ids in tests/unit/test_data_gen.py"
Task: "Contract test test_schema_validation in tests/contract/test_generated_schema.py"
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