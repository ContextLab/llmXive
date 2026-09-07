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

- [ ] T001a [P] Create project directory structure: Create directories `code/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`, `state/`, `state/projects/`, `contracts/`.
- [ ] T001b [P] Initialize git tracking for data directories: Ensure `data/` subdirectories contain `.gitkeep` files to be tracked by git.
- [X] T002 Initialize Python project with `requirements.txt` (networkx, tiktoken, numpy, pandas, scipy, statsmodels, pytest)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections defining line-length=88, target-version=py311.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `contracts/workflow.schema.yaml`: Define a JSON Schema (YAML format) for `Workflow`. Must include `type: object`, `required: [id, nodes, edges, metadata]`, and `properties` defining `nodes` as array of objects with `id`, `type`, `constraints`.
- [ ] T005 [P] Create `contracts/execution_log.schema.yaml`: Define a JSON Schema (YAML format) for `ExecutionLog`. Must include `type: object`, `required: [workflow_id, compression_depth, token_count, policy_violations]`, and `properties` defining:
 - `context_reduction_pct`: `type: [number, string]` (to allow numeric values or the literal string "[deferred]").
 - `is_valid`: `type: boolean`.
 - `status`: `type: string` (to allow values like 'edge_case', 'normal').
 - `policy_violations`: array of objects.
 - `violation_details`: array of objects with `node_id` and `rule_id`.
- [ ] T006 [P] Create `contracts/analysis_results.schema.yaml`: Define a JSON Schema (YAML format) for `AnalysisResult`. Must include `type: object`, `required: [threshold_pct, ci_lower, ci_upper, regression_coefficients]`, and `properties` defining `threshold_pct` as `number`, `ci_lower/upper` as `number`.
- [X] T007 Implement `code/utils/token_counter.py` using `tiktoken cl100k_base` (FR-009)
- [X] T008 Initialize `state/` directory and create initial `state/projects/PROJ-866-llmxive-follow-up-extending-foundation-p.yaml`
- [X] T015 [P] [Foundational] Create `main.py` orchestrator skeleton: Create `code/main.py` with `argparse` setup defining CLI arguments `--generate`, `--compress`, `--analyze`. Define function stubs `generate_workflows()`, `run_full_context()`, `run_compressed_context()`, `analyze_tradeoff()` with correct signatures. **Note**: These stubs define the interface that Phase 3/4 modules MUST implement.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Synthetic Workflow Baselines (Priority: P1) 🎯 MVP

**Goal**: Generate a set of deterministic synthetic workflows with varying depths/complexities and a ground-truth Oracle Policy Engine.

**Independent Test**: Run generator script; verify a set of unique IDs, uniform depth distribution (1-20), and that an Oracle Engine produces a distinct ground-truth log for each.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER defining the interface in T012/T013, ensuring they FAIL before implementation**

- [X] T010 [US1] Unit test for graph variance in `tests/unit/test_generator.py`
 - **Assertion**: Verify exactly 20 unique depth levels exist and each level has at least 25 workflows. [UNRESOLVED-CLAIM: c_8ffff2c0 — status=not_enough_info]
- [X] T011 [P] [US1] Contract test for workflow JSON output in `tests/contract/test_workflow_schema.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/generators/synthetic_workflow.py` with deterministic seeding (FR-001)
 - Generates a collection of DAGs, depths 1-20, complexities 1-10.
 - Records budget caps and metadata.
 - **Must conform to the interface defined in T015**.
- [X] T013 [P] [US1] Implement `code/engines/oracle_policy.py` as an independent rule-based validator (FR-008)
 - **Build the distinct Oracle logic** as a standalone module separate from execution engines.
 - Defines ground-truth validity; separate from execution engines.
- [X] T014 [US1] Implement `code/engines/full_context.py` (FR-002)
 - Executes workflows with full policy graphs.
 - **MUST invoke oracle_policy.py to validate each step and record specific 'policy-violation' flags in the log** (SC-001).
 - Produces ground-truth execution logs against Oracle.
 - **Edge Case Handling**: For single-node graphs or depth=0, set `context_reduction_pct` to the literal string `"[deferred]"` and `status` to `"edge_case"` in the execution log (per T005 schema).
 - **Invalid Workflow Handling**: Detect workflows impossible to satisfy even with full context; set `is_valid` to `false` in the log and flag for exclusion in analysis.
 - **Must conform to the interface defined in T015**.
- [ ] T016 [DEPRECATED] [US1] Edge case handling logic: Logic for edge cases (single-node, depth=0) is now integrated into T014. This task is retained for reference only. <!-- ATOMIZE: requested -->
 - **Note**: See T014 for implementation details.
- [ ] T017 [DEPRECATED] [US1] Filter for invalid workflows: Logic for filtering invalid workflows is now integrated into T014. This task is retained for reference only. <!-- ATOMIZE: requested -->
 - **Note**: See T014 for implementation details.
- [ ] T018 [US1] **Update state registry** (`state/projects/PROJ-866-...yaml`) with checksums of generated workflows in `data/raw/` immediately after generation (Constitution Principle V). **Dependencies**: T014 (Execution/Validation). Use SHA-256 hashing and update the `artifact_hashes` key in the YAML file. **Must run immediately after T014 completes.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Compressed Context Variants (Priority: P2)

**Goal**: Execute generated workflows using compressed context (BFS/DFS truncation) and measure token counts/violations.

**Independent Test**: Run execution engine with fixed depth=2 on a subset; verify reduced token count and logged violations vs. ground truth.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Integration test: Compare Full vs. Compressed logs for multiple workflows in `tests/integration/test_compression.py`
- [X] T020 [P] [US2] Contract test for execution log JSON in `tests/contract/test_execution_log_schema.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `code/engines/compressed_context.py` (FR-003)
 - Uses constrained BFS/DFS to extract minimal policy subgraphs.
 - Configurable traversal depth parameter.
 - **Violation Logging**: For every truncation that cuts off a required node (e.g., data sovereignty), record a specific "policy-violation" error in the log, including `node_id` and `rule_id` in the `violation_details` field (per T005 schema).
 - **Edge Case Handling**: For compression depth=0 or single-node graphs, set `context_reduction_pct` to the literal string `"[deferred]"` and `status` to `"edge_case"`.
 - **Must conform to the interface defined in T015**.
- [X] T022 [US2] Integrate `code/utils/token_counter.py` into `compressed_context.py` to count actual tokens (FR-004, FR-009)
 - Do NOT use node count as a proxy.
- [ ] T023 [US2] Implement batch execution logic in `main.py` to run a substantial number of workflows across multiple compression levels
 - **Dependency**: T015 (Orchestrator Skeleton), T021 (Compressed Engine).
 - **Deliverable**: Loop logic that iterates over `data/raw/`, applies compression levels (e.g., 1-5), and calls `compressed_context.py`. Output format: JSON files.
- [ ] T024 [DEPRECATED] [US2] Log policy violations: Logic for logging policy violations is now integrated into T021. This task is retained for reference only.
 - **Note**: See T021 for implementation details.
- [ ] T025 [US2] Save processed execution logs to `data/processed/` with compression level, token count, and violation flags
 - **Deliverable**: Write JSON files named `log_{workflow_id}_{depth}.json` conforming to T005 schema.
 - **Dependency**: T023 (Batch Logic). T023 produces the logs that T025 saves.
 - **Note**: This task ensures the batch output from T023 is correctly persisted and named.
- [ ] T026 [DEPRECATED] [US2] Handle compression depth=0: Logic for depth=0 edge cases is now integrated into T021. This task is retained for reference only.
 - **Note**: See T021 for implementation details.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Analyze Trade-off and Threshold (Priority: P3)

**Goal**: Perform statistical analysis to model the trade-off curve and identify the "safe operating zone" (≤1% error).

**Independent Test**: Feed pre-generated logs into analysis module; verify regression curve and specific threshold value output.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for regression calculation with known synthetic data in `tests/unit/test_tradeoff_model.py`
- [X] T028 [P] [US3] Contract test for analysis results JSON in `tests/contract/test_analysis_results_schema.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/analysis/tradeoff_model.py` (FR-005)
 - Performs Logistic Regression on individual workflow observations.
 - Uses token reduction % as predictor; includes graph depth/complexity as covariates.
 - **Output**: Must output raw regression statistics including p-values for all covariates and the model intercept to a temporary file for the correction step.
 - **Must handle non-monotonic regions** by modeling the full curve to correctly identify the "safe operating zone".
- [ ] T030 [US3] Apply Bonferroni correction to regression p-values (FR-005)
 - **Dependency**: T029 (must output raw stats).
 - **Method**: Apply Bonferroni correction specifically to the p-values of the **covariate coefficients** (depth, complexity) derived from the Logistic Regression model.
 - **Output**: Save corrected p-values to `data/processed/corrected_pvalues.json`.
 - **Note**: This is a secondary robustness check on the covariate significance, not a pairwise aggregation test.
- [ ] T031 [US3] Implement threshold detection and bootstrapping (FR-006, SC-004)
 - **Dependency**: T030 (corrected stats).
 - **Method**: Identify the specific context reduction percentage where the policy-violation error rate first exceeds a nominal threshold.
 - **Bootstrapping**: Perform bootstrapping with **exactly 1000 resamples** to calculate the Confidence interval for the threshold.
 - **Rounding**: Round the final threshold value to **2 decimal places**.
 - **Output**: Write threshold value and CI bounds to `data/results/threshold_ci.json`.
- [ ] T032 [US3] Generate raw regression data for the paper in `data/results/tradeoff_curve.csv`
 - **Deliverable**: Save `data/results/tradeoff_curve.csv` containing regression curve data points.
 - **Columns**: `reduction_pct`, `error_rate`, `depth`, `ci_lower`, `ci_upper`.
 - **Note**: `ci_lower` and `ci_upper` represent the 95% confidence interval bands for the **regression curve** (derived from the model in T029/T031 via bootstrapping), distinct from the single threshold CI.
 - **Dependency**: T025 (Processed Logs), T031 (Threshold Logic).
- [ ] T033 [US3] Update `main.py` to orchestrate the full pipeline: Generate → Full Exec → Compressed Exec → Analyze
 - **Integration**: Wire the completed Analysis module (T029-T031) into the existing orchestrator logic.
 - **Deliverable**: Implement the `--generate`, `--compress`, `--analyze` CLI flags defined in T015 to call the full pipeline.
 - **Dependency**: T015 (Skeleton), T023 (Batch Logic).
- [ ] T034 [US3] Finalize `state/projects/...yaml` with artifact hashes and `updated_at` timestamp
 - **Deliverable**: Update `state/projects/...yaml` with SHA-256 hashes of all files in `data/` (raw, processed, results) and set `updated_at`.
 - **Dependency**: T032 (Regression Data), T018 (Initial Checksums).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Update `docs/api.md` with new engine signatures and analysis methods.
- [ ] T036 [P] Update `quickstart.md` with the 500-workflow generation command and analysis steps.
 - **Deliverable**: Include exact command string `python code/main.py --generate 500 --analyze` and expected output paths.
 - **Dependency**: T033 (CLI Implementation).
- [ ] T037a [P] Code cleanup: Run `ruff check --fix` on the entire `code/` directory and fix all linting errors.
- [ ] T037b [P] Code formatting: Run `black` on the entire `code/` directory to ensure consistent formatting.
- [ ] T037c [P] Import audit: Audit all imports in `code/` to ensure no unused or external API calls are present.
- [ ] T038 [P] Run benchmark for a large-scale workflow suite
The research question remains: How does the proposed system perform under varying workflow complexities? The method remains: Systematic benchmarking against established baselines. References: [Author et al., 2023; ].: Execute the full pipeline on the target runner and measure wall-clock time. Record result in `data/results/benchmark.log`.
 - **Deliverable**: Write a single JSON object to `data/results/benchmark.log` containing `{"total_wall_clock_seconds": <float>, "timestamp": "<ISO8601>"}`.
 - **Acceptance**: If `total_wall_clock_seconds` > 21600 (6 hours), the build fails.
- [ ] T039 [P] Optimize if benchmark > 6h: If T038 result > 6h, implement optimization (e.g., parallel processing, caching) and re-run benchmark.
 - **Dependency**: T038.
- [ ] T040 [P] Run `pytest` full suite including contract tests
- [ ] T041 [P] Security hardening: Audit imports and network calls; ensure no external API calls are made for synthetic data generation. Add network isolation check in `main.py`.
- [ ] T042 [P] Validate data against schemas: Run a script to validate all generated JSON files in `data/processed/` and `data/results/` against the schemas defined in `contracts/`. Fail the build if any validation error occurs.

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
- [DEPRECATED] tasks are logic that has been merged into a parent task and are kept for reference only.