# Tasks: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

**Input**: Design documents from `/specs/001-structural-mismatch-cost/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001 Create project structure per implementation plan (code/, data/, tests/, specs/)
- [ ] T002 Initialize Python 3.11 project with dependencies: `pandas`, `numpy`, `scipy`, `statsmodels`, `pytest`, `pyyaml`, `rdflib`, `networkx`, `matplotlib`, `seaborn` in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create data schemas: `contracts/query_instance.schema.yaml`, `contracts/execution_metric.schema.yaml`, `contracts/analysis_result.schema.yaml`
- [ ] T005 [P] Implement `code/config.py` for seeds, paths, and CPU throttling configuration (cgroups logic)
- [ ] T006 [P] Implement `code/generators/synthetic_query.py` to generate queries with varying plan depths (1-2 low, 3+ high). This task MUST call `code/generators/reference_engine.py` (T007) to assign the `ground_truth_plan` attribute via deterministic rules (FR-008).
- [ ] T007 [P] Implement `code/generators/reference_engine.py` (FR-008) to generate independent, deterministic ground-truth execution plans for all query types.
- [ ] T008 [P] Implement `code/executors/base.py` with abstract base class for execution engines and timeout handling (60s limit). This class MUST utilize the throttling mechanism implemented in T016.
- [ ] T009 [P] Implement `code/executors/text_executor.py` using sequential chaining to simulate complexity on flat text (SPARQL-like logic on sampled MS MARCO subset).
- [ ] T010 [P] Implement `code/executors/relational_executor.py` wrapping SQLite with in-memory database for Spider benchmark subset.
- [ ] T011 [P] Implement `code/executors/graph_executor.py` using NetworkX/RDFLib for synthetic graph generation and multi-hop traversal simulation.
- [ ] T012 [P] Implement `code/main.py` orchestration script to load config, generate queries, route to executors, and log raw metrics.
- [ ] T016 [P] Implement CPU throttling logic in `code/utils/cpu_throttle.py` using `cgroups`. This task MUST enforce the strict CPU time limit and memory cap defined in FR-001.
- [ ] T016b [P] Implement CPU throttling validity check in `code/utils/cpu_throttle.py`. This task MUST detect if `cgroups` fails due to container permissions and abort the run with a specific error code (e.g., exit code 1) to prevent invalid data collection, as required by Edge Cases and Constitution Principle VI.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Quantify Latency Penalties (Priority: P1) 🎯 MVP

**Goal**: Measure end-to-end latency difference between low and high complexity queries on CPU-constrained environment.

**Independent Test**: Execute 500 synthetic queries (low/high split) against simulated CPU-throttled environment; verify latency logs are generated and ANOVA interaction term is calculable.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Contract test for `ExecutionMetric` schema validation in `tests/contract/test_execution_metric.py`
- [ ] T014 [P] [US1] Integration test for end-to-end query execution loop with CPU throttling in `tests/integration/test_latency_pipeline.py`
- [ ] T014b [P] [US1] Integration test for CPU throttling validity check in `tests/integration/test_throttling_abort.py`. Verify the system exits with a specific error code when `cgroups` is unavailable.

### Implementation for User Story 1

- [ ] T015 [US1] Implement `code/analysis/metrics.py` to record end-to-end latency (ms) and handle timeout flags (FR-003).
- [ ] T017 [US1] Implement query classification logic in `code/generators/synthetic_query.py` to tag queries as "low-complexity" (depth ≤ 2) or "high-complexity" (depth ≥ 3) (FR-002).
- [ ] T018 [US1] Implement `code/analysis/stats.py` to perform Two-Way ANOVA on `latency` vs `complexity` × `source_type`. This task MUST:
  1. Perform Levene and Shapiro-Wilk tests for variance validation (mandatory prerequisite per Constitution VII).
  2. Output F-statistic, p-value, and 95% CI for the interaction term.
  3. Calculate and report the **ratio of slopes (graph vs. text)** as required by SC-001.
  4. Perform post-hoc Tukey tests to identify pairwise differences between source types (FR-005).
  5. Flag the hypothesis as 'supported' only if p < 0.05.
- [ ] T020 [US1] Implement sensitivity analysis in `code/analysis/stats.py`. This task MUST sweep the complexity depth cutoff over a **configurable range of low integer values** (default 1-5) and output a JSON object for **each** cutoff in the range containing: `{"cutoff": <int>, "spike_point": <float>, "slope_change": <float>}` (FR-007, SC-004).
- [ ] T021 [US1] Add data persistence in `code/main.py` to write raw metrics to `data/processed/execution_logs.csv` and aggregated stats to `data/results/anova_results.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Measure Translation Error Rates (Priority: P2)

**Goal**: Track frequency of translation errors (plan mismatch) under CPU throttling and compare low vs high complexity groups.

**Independent Test**: Compare generated plans against ground-truth plans for 100 high-complexity graph queries; verify error rate calculation and reporting.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Contract test for `QueryInstance` schema validation in `tests/contract/test_query_instance.py`
- [ ] T023 [P] [US2] Integration test for plan comparison logic in `tests/integration/test_translation_errors.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement plan comparison logic in `code/analysis/metrics.py` to calculate binary translation error (0=match, 1=mismatch) against ground truth (FR-004). This task depends on `ground_truth_plan` generated by T006/T007.
- [ ] T025 [US2] Implement error rate aggregation in `code/analysis/stats.py` to compute error rates for low vs high complexity groups (FR-004).
- [ ] T026 [US2] Update `code/main.py` to log translation errors alongside latency metrics in `data/processed/execution_logs.csv`.
- [ ] T027 [US2] Add validation logic to ensure ground-truth plans are generated by the independent reference engine (FR-008) before comparison.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualize Non-Linear Scaling (Priority: P3)

**Goal**: Generate interaction plots showing latency vs. query complexity for each source type.

**Independent Test**: Run visualization script on aggregated data; verify output PNG/PDF shows distinct lines for text, relational, and graph sources with correct slope differences.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for `AnalysisResult` schema validation in `tests/contract/test_analysis_result.py`
- [ ] T029 [P] [US3] Integration test for plot generation in `tests/integration/test_visualization.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/analysis/viz.py` to generate interaction plots (latency vs complexity, grouped by source type) using `matplotlib` or `seaborn`. This task depends on aggregated data from T021 and T026.
- [ ] T031 [US3] Add logic in `code/analysis/viz.py` to explicitly highlight the slope difference for graph sources and identify spike thresholds (FR-006).
- [ ] T032 [US3] Update `code/main.py` to save final plots to `data/results/interaction_plot.png` and `data/results/interaction_plot.pdf`.
- [ ] T033 [US3] Add logic to generate a summary report in `data/results/research_summary.md` containing the ANOVA results (including slope ratio), error rates, and links to plots.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates: Add `quickstart.md` with instructions to run the experiment on GitHub Actions
- [ ] T036 [P] Add unit tests for synthetic query generator edge cases (depth cap, timeout handling) in `tests/unit/`
- [ ] T037 [P] Run `quickstart.md` validation to ensure the full pipeline completes within 6 hours on free-tier runners
- [ ] T038 [P] Verify all dataset URLs in `code/config.py` are real and reachable (MS MARCO, Spider, DBpedia subsets)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **T016 and T016b MUST be complete before T008-T011.**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on `reference_engine` from Phase 2
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on aggregated data from US1 and US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Schemas before services/logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for ExecutionMetric schema in tests/contract/test_execution_metric.py"
Task: "Integration test for latency pipeline in tests/integration/test_latency_pipeline.py"
Task: "Integration test for throttling abort in tests/integration/test_throttling_abort.py"

# Launch all core logic for User Story 1 together:
Task: "Implement CPU throttling in code/utils/cpu_throttle.py"
Task: "Implement ANOVA logic in code/analysis/stats.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (ANOVA results, latency logs, slope ratio)
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
   - Developer A: User Story 1 (Latency & ANOVA)
   - Developer B: User Story 2 (Translation Errors)
   - Developer C: User Story 3 (Visualization)
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
- **Critical Constraint**: All tasks MUST run on CPU-only CI (2 cores, 7GB RAM). No GPU, no 8-bit quantization, no large model training.
- **Data Integrity**: All datasets must be fetched from real URLs (HuggingFace/GitHub) or generated synthetically with deterministic seeds. No fake data.
- **Statistical Validity**: Levene/Shapiro tests are mandatory prerequisites for ANOVA (Constitution VII).
- **Sensitivity Analysis**: Must use a configurable range of cutoffs, not hard-coded values.