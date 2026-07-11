# Tasks: llmXive follow-up: extending "Foundation Protocol: A Coordination Layer for Agentic Society"

**Input**: Design documents from `/specs/001-policy-compression-tradeoff/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `state/`)
- [ ] T002 Initialize Python project with `requirements.txt` (networkx, tiktoken, numpy, pandas, scipy, statsmodels, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `contracts/` directory and define `workflow.schema.yaml`
- [ ] T005 Create `contracts/` directory and define `execution_log.schema.yaml`
- [ ] T006 Create `contracts/` directory and define `analysis_results.schema.yaml`
- [~] T007 Implement `code/utils/token_counter.py` using `tiktoken cl100k_base` (FR-009)
- [~] T008 Initialize `state/` directory and create initial `state/projects/PROJ-866-llmxive-follow-up-extending-foundation-p.yaml`
- [~] T009 Create `data/raw/`, `data/processed/`, and `data/results/` directories

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Synthetic Workflow Baselines (Priority: P1) 🎯 MVP

**Goal**: Generate a set of deterministic synthetic workflows with varying depths/complexities and a ground-truth Oracle Policy Engine.

**Independent Test**: Run generator script; verify a set of unique IDs, uniform depth distribution (1-20), and that an Oracle Engine produces a distinct ground-truth log for each.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER defining the interface in T012/T013, ensuring they FAIL before implementation**

- [~] T010 [US1] Unit test for graph variance in `tests/unit/test_generator.py`
 - **Assertion**: Verify exactly 20 unique depth levels exist and each level has at least 25 workflows.
- [~] T011 [US1] Contract test for workflow JSON output in `tests/contract/test_workflow_schema.py`

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement `code/generators/synthetic_workflow.py` with deterministic seeding (FR-001)
 - Generates a collection of DAGs, depths 1-20, complexities 1-10.
 - Records budget caps and metadata.
- [~] T013 [P] [US1] Implement `code/engines/oracle_policy.py` as an independent rule-based validator (FR-008)
 - **Build the distinct Oracle logic** as a standalone module separate from execution engines.
 - Defines ground-truth validity; separate from execution engines.
- [~] T014 [US1] Implement `code/engines/full_context.py` (FR-002)
 - Executes workflows with full policy graphs.
 - **MUST invoke oracle_policy.py to validate each step and record specific 'policy-violation' flags in the log** (SC-001).
 - Produces ground-truth execution logs against Oracle.
- [~] T015 [US1] Create `main.py` orchestrator skeleton to generate and save raw workflows to `data/raw/`
- [~] T016 [US1] Implement edge case handling in `full_context.py` for single-node graphs and depth=0. **Set `context_reduction_pct` to the string marker '[deferred]' and `status` to 'edge_case' in the execution log** for these instances.
- [~] T017 [US1] Implement filter for "invalid workflows" (impossible even with full context) to exclude from error calculations
 - **Mechanism**: Add an `is_valid` boolean field to the ExecutionLog schema; set to `false` for invalid workflows and filter based on this flag during analysis.
- [ ] T018 [US1] **Update state registry** (`state/projects/PROJ-866-...yaml`) with checksums of generated workflows in `data/raw/` immediately after generation (Constitution Principle V).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Compressed Context Variants (Priority: P2)

**Goal**: Execute generated workflows using compressed context (BFS/DFS truncation) and measure token counts/violations.

**Independent Test**: Run execution engine with fixed depth=2 on a subset; verify reduced token count and logged violations vs. ground truth.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Integration test: Compare Full vs. Compressed logs for 10 workflows in `tests/integration/test_compression.py`
- [ ] T020 [P] [US2] Contract test for execution log JSON in `tests/contract/test_execution_log_schema.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/engines/compressed_context.py` (FR-003)
 - Uses constrained BFS/DFS to extract minimal policy subgraphs.
 - Configurable traversal depth parameter.
- [ ] T022 [US2] Integrate `code/utils/token_counter.py` into `compressed_context.py` to count actual tokens (FR-004, FR-009)
 - Do NOT use node count as a proxy.
- [ ] T023 [US2] Implement batch execution logic in `main.py` to run a substantial number of workflows across multiple compression levels
 - **Dependency**: Requires updated orchestrator logic from T015 and completed Compressed Engine from T021.
- [ ] T024 [US2] Log policy violations specifically when truncation cuts off required nodes (e.g., data sovereignty rules)
- [ ] T025 [US2] Save processed execution logs to `data/processed/` with compression level, token count, and violation flags
- [ ] T026 [US2] Implement logic to handle compression depth=0 (no context passed) gracefully

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Analyze Trade-off and Threshold (Priority: P3)

**Goal**: Perform statistical analysis to model the trade-off curve and identify the "safe operating zone" (≤1% error).

**Independent Test**: Feed pre-generated logs into analysis module; verify regression curve and specific threshold value output.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for regression calculation with known synthetic data in `tests/unit/test_tradeoff_model.py`
- [ ] T028 [P] [US3] Contract test for analysis results JSON in `tests/contract/test_analysis_results_schema.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/analysis/tradeoff_model.py` (FR-005)
 - Performs Logistic Regression on individual workflow observations.
 - Uses token reduction % as predictor; includes graph depth/complexity as covariates.
 - **Must handle non-monotonic regions** by modeling the full curve to correctly identify the "safe operating zone".
- [ ] T030 [US3] Implement Bonferroni or Benjamini-Hoch correction for multiple comparisons (FR-005)
- [ ] T031 [US3] Implement threshold detection logic to find max context reduction where error ≤ 1% (FR-006)
 - **Execute AFTER T030**: Ensure the threshold is derived from p-values corrected by the multiple-comparison correction.
 - **Implement bootstrapping (1000 resamples) to calculate the 95% confidence interval for the threshold**.
 - **Round threshold to exactly 2 decimal places** as required by FR-006 and SC-004.
 - **Write confidence interval bounds to `data/results/threshold_ci.json`**.
- [ ] T032 [US3] Generate raw regression data for the paper in `data/results/tradeoff_curve.csv`
 - **Deliverable**: Save `data/results/tradeoff_curve.csv` containing the regression curve data points. (Replaces visualization task to adhere to scope).
- [ ] T033 [US3] Update `main.py` to orchestrate the full pipeline: Generate → Full Exec → Compressed Exec → Analyze
 - **Integration**: Wire the completed Analysis module (T029-T031) into the existing partial orchestrator logic.
- [ ] T034 [US3] Finalize `state/projects/...yaml` with artifact hashes and `updated_at` timestamp

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Update `docs/api.md` with new engine signatures and analysis methods.
- [ ] T036 [P] Update `quickstart.md` with the 500-workflow generation command and analysis steps.
- [ ] T037 Code cleanup and refactoring
- [ ] T038 Performance optimization: Verify full 500-run suite completes < 6h on CPU (Conservative bound per Spec Assumptions)
- [ ] T039 [P] Run `pytest` full suite including contract tests
- [ ] T040 Security hardening (ensure no external API calls for synthetic data)

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
 - *Note*: Must complete before US2 can generate ground truth logs.
- **User Story 2 (P2)**: Depends on US1 completion (needs generated workflows and Oracle)
 - Must execute *after* US1 generates data.
- **User Story 3 (P3)**: Depends on US2 completion (needs execution logs)
 - Must execute *after* US2 produces `data/processed/` logs.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Generators before Engines
- Engines before Analysis
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
# Launch all models for User Story 1 together:
Task: "Implement code/generators/synthetic_workflow.py with deterministic seeding"
Task: "Implement code/engines/oracle_policy.py as an independent rule-based validator"

# Then write tests against the defined interface:
Task: "Unit test for graph variance in tests/unit/test_generator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Generate + Oracle)
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
 - Developer A: User Story 1 (Generator + Oracle)
 - Developer B: User Story 2 (Compressed Engine) - *Depends on A*
 - Developer C: User Story 3 (Analysis) - *Depends on B*
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