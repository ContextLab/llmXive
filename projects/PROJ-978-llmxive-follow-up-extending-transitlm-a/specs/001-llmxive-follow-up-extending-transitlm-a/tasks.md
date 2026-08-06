# Tasks: llmXive follow-up: extending "TransitLM: A Large-Scale Dataset and Benchmark for Map-Free Transit Ro"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-transitlm-a/`
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

- [ ] T001 Create project structure: directories `code/`, `data/raw/`, `data/processed/`, `data/analysis/`, `models/`, `analysis/`, `tests/`, `docs/` per implementation plan
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (datasets, pandas, networkx, scikit-learn, lifelines, transformers, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. T006 is a mandatory blocking gate for Phase 3.

Examples of foundational tasks (adjust based on plan.md):

- [X] T004 [P] Implement `data/download.py` to fetch TransitLM SFT dataset from Hugging Face (`load_dataset` with `streaming=True`), apply SHA256 checksum verification, and save to `data/raw/`
- [ ] T006 [P] Implement `data/preprocess.py` to filter the dataset for four Chinese cities, apply top-N vocabulary restriction (with `<UNKNOWN>` token handling), and stratify routes into short (<15), medium (15-30), and long (>30) categories. **This task is a mandatory blocking gate: Phase 3 tasks (T011+) cannot start until T006 validation passes.**
- [ ] T007 [P] Implement `data/graph_utils.py` to build the local adjacency graph and validate it against `data/raw/transitlm_ground_truth.json` for edge overlap (≥95%) (FR-008). **This task depends on T006 completion.**
- [X] T008 Create `data/contracts/dataset.schema.yaml` and `data/contracts/output.schema.yaml` to validate data integrity
- [ ] T009 [P] Implement `config.py` for environment configuration, random seeds, and city mapping constants

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel (only if T006 validation passed)

---

## Phase 3: User Story 1 - Local vs. Global Performance Threshold Identification (Priority: P1) 🎯 MVP

**Goal**: Evaluate the lightweight, encoder-only retrieval-augmented model against the original LLM baseline across stratified route lengths to identify the "cognitive horizon".

**Independent Test**: The system can be tested by running the evaluation pipeline on the stratified test set and generating a performance comparison report that clearly shows the divergence in route validity between the lightweight model and the LLM baseline at specific stop counts.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for `data/preprocess.py` output schema in `tests/contract/test_preprocess_schema.py`
- [X] T011 [P] [US1] Integration test for stratified route validity scoring in `tests/integration/test_stratified_validity.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `models/lightweight.py` with a deterministic fixed-lookup strategy (retrieving top-N neighbors and selecting highest frequency transition) without GPU acceleration
- [ ] T013 [P] [US1] Implement `models/baseline.py` to load the CPU-quantized baseline LLM (Qwen-1.8B or similar) and run inference on the stratified test set <!-- FAILED: unspecified -->
- [ ] T014 [US1] Implement `analysis/evaluation.py` to: (1) Compute route validity for each category; (2) Perform point-wise Chi-squared scans on **connectivity** (Constitution Principle VI) to identify the inflection point where validity drops ≥15% **AND is statistically significant (p < 0.05)**; (3) Flag predictions as "high risk" based on this inflection point and confidence intervals; (4) **Consume** per-route topological complexity metrics from T015 output.
- [ ] T015 [US1] [FR-009] Implement `data/graph_utils.py` to compute path-level betweenness centrality for **each individual route** in the dataset (FR-009) using the filtered data from T006. **Note: This task depends on T006 completion and cannot run in parallel with T006.**
- [ ] T016 [US1] Add validation for `<UNKNOWN>` tokens in `data/preprocess.py` to exclude them from station validity metrics unless ground truth matches (FR-006)
- [ ] T017 [US1] Add logging for model predictions, validity scores, and risk flags

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Significance of Topological Limits (Priority: P2)

**Goal**: Apply Kaplan-Meier survival analysis and point-wise Chi-squared tests to statistically confirm performance degradation thresholds.

**Independent Test**: The system can be tested by executing the statistical analysis module and verifying that a survival curve is generated with a log-rank test p-value comparing the lightweight model and the baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for statistical output schema in `tests/contract/test_statistical_schema.py`
- [ ] T019 [P] [US2] Integration test for survival analysis and log-rank test in `tests/integration/test_survival_analysis.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] [FR-004] Implement `analysis/survival.py` to execute Kaplan-Meier survival analysis on route validity decay across route lengths (FR-004)
- [ ] T021 [US2] [FR-004] Implement `analysis/survival.py` to perform log-rank test comparing lightweight model and baseline survival curves (FR-004)
- [ ] T022 [US2] [FR-004] Implement `analysis/survival.py` to handle censored data (routes truncated or reaching max hops) correctly (US-2, Scenario 1)
- [ ] T023 [US2] [FR-004] [FR-007] Implement `analysis/statistics.py` to perform point-wise Chi-squared scans on **connectivity** metrics (Constitution Principle VI) across every route length (L=1 to L=max) to detect the % validity gap threshold (Plan: Dual-Method) and apply Bonferroni correction for multiple comparisons (FR-007)
- [ ] T024 [US2] Add diagnostic checks for proportional hazards assumptions in `analysis/survival.py` and implement non-parametric fallback if violated (Edge Case)
- [ ] T025 [US2] Generate `data/analysis/survival_curves.pdf` and `data/analysis/statistical_report.json` with p-values and confidence intervals

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Resource Feasibility and Edge-Device Simulation (Priority: P3)

**Goal**: Profile inference latency and memory usage of the lightweight model on a simulated 2-core CPU environment.

**Independent Test**: The system can be tested by running the model inference on a GitHub Actions free-tier runner (simulating the target environment) and logging the peak memory usage and average inference time per route.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for profiling output schema in `tests/contract/test_profiling_schema.py`
- [ ] T027 [P] [US3] Integration test for memory and time constraints in `tests/integration/test_resource_constraints.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `analysis/profiling.py` to measure peak memory usage and inference latency on the lightweight model (FR-005)
- [ ] T029 [US3] Implement `analysis/profiling.py` to enforce and log a constrained time limit and a constrained RAM limit (US-3, Scenario 1)
- [ ] T030 [US3] Implement logic to record "timeout/infeasible" status if the baseline LLM exceeds a predefined runtime or memory limit, marking divergence claims as "inconclusive" (Plan: Resource-Constrained Baseline)
- [ ] T031 [US3] [Plan] [SC-003] Generate `data/analysis/profiling_report.json` with latency, memory, and feasibility status
- [ ] T032 [US3] Update `docs/research.md` to document the feasibility findings and any "inconclusive" markers (Addressing tension in Plan vs Spec)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates: Update `docs/research.md` with the final inflection point value from `data/analysis/statistical_report.json` and `docs/quickstart.md` with execution steps
- [ ] T034 Code cleanup: Refactor `data/preprocess.py` to extract city-filtering logic into a separate function
- [ ] T035 [P] Performance optimization: Profile and optimize the top-N neighbor retrieval in `models/lightweight.py` to reduce latency to ≤60 seconds per batch
- [ ] T036 [P] Additional unit tests: Add unit tests for `graph_utils.py::compute_betweenness_centrality` in `tests/unit/test_graph_utils.py`
- [ ] T037 [P] Run `quickstart.md` validation: Execute the commands in `docs/quickstart.md` in a fresh virtualenv and verify that `data/analysis/profiling_report.json` is generated with no errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
 - **CRITICAL**: Task T006 is a **hard blocking gate**. If T006 validation fails, Phase 3 tasks (T012+) are strictly prohibited from starting.
 - **Sequential Flow**: T004 (Download) → T006 (Preprocess) → T007 (Graph Validation). T007 cannot run in parallel with T006.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion (specifically T006 passing)
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - **Depends on T007 (graph validation) and T015 (per-route metrics)**
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T007 which depends on T006**
- Once Foundational phase completes (and T006 passes), all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for `data/preprocess.py` output schema in `tests/contract/test_preprocess_schema.py`"
Task: "Integration test for stratified route validity scoring in `tests/integration/test_stratified_validity.py`"

# Launch all models for User Story 1 together:
Task: "Implement `models/lightweight.py` with a deterministic fixed-lookup strategy"
Task: "Implement `models/baseline.py` to load the CPU-quantized baseline LLM"
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
