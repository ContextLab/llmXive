# Tasks: llmXive follow-up: extending "TransitLM: A Large-Scale Dataset and Benchmark for Map-Free Transit Ro"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-transitlm-a/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3) or [Foundational] for shared prerequisites
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
- [X] T002 Initialize Python 3.11 project with `requirements.txt`. **Core deps (Lightweight Only)**: `datasets`, `pandas`, `networkx`, `scikit-learn`, `lifelines`, `pytest`, `numpy`. **Constraint**: Do NOT include `torch` or `transformers` here. The lightweight model is a deterministic lookup strategy requiring no deep learning stack. **Note**: Baseline LLM dependencies are separated in T002b.
- [X] T002b [P] [Foundational] Create `requirements-baseline.txt` containing `torch`, `transformers`, and `accelerate` strictly for the Baseline LLM (T013). **Constraint**: This file is ONLY used when executing T013. The lightweight model tasks (T012a/b) must NOT depend on this file.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. T006/T007 validation is a mandatory blocking gate for Phase 3.

- [ ] T004 [P] Implement `data/download.py` function `stream_dataset` to fetch TransitLM SFT dataset from Hugging Face (`load_dataset` with `streaming=True`), apply SHA256 checksum verification, and save to `data/raw/`. **Deliverable**: `data/raw/transitlm_ground_truth.json`.
- [ ] T004b [P] [Foundational] Implement `data/download.py` function `sample_routes` to handle datasets too large for RAM. **Logic**: Use `itertools.islice` to extract a fixed-seed random sample (e.g., first 50k routes) if the full dataset exceeds 7GB RAM, explicitly logging the sample size and seed. **Constraint**: NEVER fall back to synthetic data; if the stream fails, raise an error. **Dependency**: T004. **Deliverable**: `data/raw/transitlm_ground_truth.json` (full stream or validated sample).
- [ ] T006a [P] [Foundational] Implement `data/preprocess.py` function `filter_cities` to filter the dataset for four Chinese cities. **Deliverable**: `data/processed/city_filtered_routes.jsonl`.
- [ ] T006b [P] [Foundational] Implement `data/preprocess.py` function `apply_vocabulary_restriction` to apply top-N station vocabulary restriction (with `<UNKNOWN>` token handling) on the filtered routes. **Deliverable**: `data/processed/vocab_restricted_routes.jsonl`.
- [ ] T006c [P] [Foundational] Implement `data/preprocess.py` function `stratify_routes` to stratify routes into short (<15), medium (15-30), and long (>30) categories. **Deliverable**: `data/processed/stratified_routes.parquet`. **Verification**: Assert `row_count > 0` and categories are balanced (within 10% of the mean category count).
- [ ] T016 [US1] [FR-006] Implement logic in `data/preprocess.py` to handle `<UNKNOWN>` tokens: exclude them from station validity metrics unless ground truth matches. **Dependency**: Must run immediately after T006c data generation.

### Validation Gate: Graph Construction & Verification

**⚠️ CRITICAL**: T007b is a HARD BLOCKER. Phase 3 cannot start if T007b fails.

- [ ] T007a [P] [Foundational] Implement `data/graph_utils.py` function `build_adjacency_graph` to construct the local adjacency graph from the **filtered** routes (T006a-c output). **Dependency**: T004, T006a-c. **Deliverable**: `data/processed/adjacency_graph.pkl`.
- [ ] T007b [Foundational] [FR-008] Implement `data/graph_utils.py` function `validate_graph` to validate the graph from T007a against `data/raw/transitlm_ground_truth.json` for **edge overlap percentage** (defined as `|A ∩ B| / |A|` where A is ground truth edges) ≥95%. **Deliverable**: `data/processed/graph_validation_report.json` containing `{"edge_overlap_percentage": float, "status": "PASS|FAIL"}`. **Dependency**: T004, T006a-c, T007a. **CRITICAL**: If edge overlap percentage < 0.95, this task MUST fail, abort Phase 3, and log the error to `data/analysis/graph_validation_error.log` with a diagnostic report.

- [ ] T009 [P] Implement `config.py` for environment configuration, random seeds, and city mapping constants.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel (only if T007b validation passed)

---

## Phase 3: User Story 1 - Local vs. Global Performance Threshold Identification (Priority: P1) 🎯 MVP

**Goal**: Evaluate the lightweight, encoder-only retrieval-augmented model against the original LLM baseline across stratified route lengths to identify the "cognitive horizon".

**Independent Test**: The system can be tested by running the evaluation pipeline on the stratified test set and generating a performance comparison report that clearly shows the divergence in route validity between the lightweight model and the LLM baseline at specific stop counts.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for `data/preprocess.py` output schema in `tests/contract/test_preprocess_schema.py`
- [X] T011 [P] [US1] Integration test for stratified route validity scoring in `tests/integration/test_stratified_validity.py`

### Implementation for User Story 1

- [ ] T015a [US1] [FR-009] Implement `data/graph_utils.py` function `prepare_route_sequences` to load the stratified routes from T006 (`data/processed/stratified_routes.parquet`) and prepare the route sequences. **Dependency**: T006.
- [ ] T015b [US1] [FR-009] Implement `data/graph_utils.py` function `compute_route_topological_complexity` to compute an independent measure of topological complexity for each route: **path-level betweenness centrality calculated on the local adjacency subgraph (filtered to nodes present in the specific route)**. **Algorithm**: Use `networkx.betweenness_centrality` with `k=100` (or similar) for path-level estimation. **CRITICAL**: This task MUST also compute the **correlation coefficient** between the `betweenness_score` and the `validity_drop` (computed in T014) and include this correlation in the final deliverable. **Dependency**: T015a, T007a, **T014** (requires validity data for correlation). **Deliverable**: `data/analysis/route_complexity_metrics.json` containing `route_id`, `betweenness_score`, and **correlation_coefficient_with_validity_drop**. **Note**: This task runs in parallel with T012a/T013 but depends on T014 completion for the correlation step.
- [ ] T012a [P] [US1] [FR-002] Implement `data/graph_utils.py` function `build_adjacency_index` to construct a retrieval index of top-N neighbors for each station. **Deliverable**: `data/processed/adjacency_index.pkl`. **Note**: This is the retrieval component, not the model.
- [ ] T012b [US1] [FR-002] Implement `models/lightweight.py` function `predict_next_station(current_station: int, context_history: List[int]) -> int`. **Constraint**: **NO NEURAL NETWORK. NO TENSORFLOW/PyTorch. NO BERT**. This MUST be a **Deterministic Fixed Lookup Strategy** as per Constitution Principle VII and Plan. **Logic**:
 1. Load `data/processed/adjacency_index.pkl` (T012a).
 2. Retrieve top-N neighbors for `current_station`.
 3. Calculate transition frequencies from the `context_history` (last N stations) to candidates using a **pure numpy frequency matrix**.
 4. Select the neighbor with the highest frequency.
 5. **Tie-breaking**: If multiple neighbors have the same frequency, select the one with the lowest station ID.
 **Deliverable**: `models/lightweight.py` with working inference logic returning a single station ID. **Dependency**: T012a.
- [ ] T013 [P] [US1] Implement `models/baseline.py` to load the CPU-quantized baseline LLM (Qwen or similar) and run inference on the stratified test set. **Constraint**: Must enforce a configurable timeout and memory limit per route batch. If the model fails to load or run within limits, log `timeout/infeasible` and continue. **Dependency**: T002b (requires `requirements-baseline.txt`). **Note**: This task requires `transformers` and `torch`.
- [ ] T014 [US1] [FR-007, FR-002] Implement `analysis/evaluation.py` to: (1) Compute route validity for each individual route length L (point-wise scan) by iterating L from 1 to max; (2) **Apply Bonferroni correction to the p-values of the Chi-squared test for every L ** to control family-wise error rate *during* the scan; (3) Identify the **shortest route length L** (inflection point) where the lightweight model's validity drops **≥15% (absolute drop)** AND the **corrected** p-value < 0.05; (4) Flag predictions as "high risk" based on this inflection point; (5) Aggregate results per stratified category. **Input Schema**: List of dicts with `route_id`, `length`, `is_valid`. **Statistical Function**: Use `scipy.stats.chi2_contingency`. **Deliverable**: `data/analysis/raw_inflection_data.json` containing **corrected** p-values per length, the exact inflection point L, and stratified summaries. **Dependency**: T012b, T013.
- [ ] T017 [US1] [FR-002] Implement logging and reporting in `analysis/evaluation.py`. **Requirement**: Logs MUST be written in **JSON format** to `logs/evaluation.log` at **INFO level** to satisfy US-1 Independent Test requirement. Each log entry MUST contain the fields: `route_id`, `predicted_station`, `validity_score`, `risk_flag`. **Additionally**, generate the **performance comparison report** artifact required by the Independent Test. **Input**: `data/analysis/raw_inflection_data.json` from T014 AND `data/analysis/route_complexity_metrics.json` from T015b. **Deliverable**: `data/analysis/performance_report.json` containing route validity percentages per category, the identified inflection point, risk flag summaries, and topological complexity correlation. **Dependency**: T014, T015b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Significance of Topological Limits (Priority: P2)

**Goal**: Apply Kaplan-Meier survival analysis and point-wise Chi-squared tests to statistically confirm performance degradation thresholds.

**Independent Test**: The system can be tested by executing the statistical analysis module and verifying that a survival curve is generated with a log-rank test p-value comparing the lightweight model and the baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for statistical output schema in `tests/contract/test_statistical_schema.py`
- [X] T019 [P] [US2] Integration test for survival analysis and log-rank test in `tests/integration/test_survival_analysis.py`

### Implementation for User Story 2

- [ ] T020 [US2] [FR-004] Implement `analysis/survival.py` to execute a **unified** Kaplan-Meier survival analysis. **Logic**: (1) Handle censored data (routes truncated or reaching max hops) **during** estimation; (2) Compute KM survival curves; (3) Perform log-rank test using **`lifelines.statistics.logrank_test`** to compare lightweight model and baseline curves. **Input**: Validity status per route from T017. **Dependency**: T017 (US1 completion). **Deliverable**: `data/analysis/survival_analysis_results.json` containing `survival_curve_data` (time, probability, CI) and `log_rank_p_value`. **Output Schema**: `{"survival_curve": [...], "log_rank_p_value": float, "median_survival_lengths": {...}}`.
- [ ] T023a [US2] [FR-007] Implement `analysis/statistics.py` to consume `data/analysis/raw_inflection_data.json` from T014 and verify the Bonferroni correction was applied. **Requirement**: Must identify the final inflection point where validity gap ≥15% AND adjusted p-value < 0.05. **Error Handling**: If T014 data is missing, log error and halt with status 'data_missing'. **Deliverable**: `data/analysis/final_inflection_report.json`. **Dependency**: T014.
- [ ] T023b [US2] [FR-007] Implement `analysis/statistics.py` to report the adjusted p-values and compare them to the nominal alpha level (standard significance threshold) to determine significance. **Dependency**: T023a.
- [ ] T025a [US2] [FR-004] Generate `data/analysis/survival_curves.pdf` from `data/analysis/survival_analysis_results.json`. **Verification**: PDF file exists, contains two curves (lightweight vs. baseline), and includes a legend and log-rank p-value annotation. **Dependency**: T020.
- [ ] T025b [US2] Generate `data/analysis/statistical_report.json` with p-values, confidence intervals, and the identified inflection point. **Dependency**: T023a, T025a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Resource Feasibility and Edge-Device Simulation (Priority: P3)

**Goal**: Profile inference latency and memory usage of the lightweight model on a simulated 2-core CPU environment.

**Independent Test**: The system can be tested by running the model inference on a GitHub Actions free-tier runner (simulating the target environment) and logging the peak memory usage and average inference time per route.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for profiling output schema in `tests/contract/test_profiling_schema.py`
- [ ] T027 [P] [US3] Integration test for memory and time constraints in `tests/integration/test_resource_constraints.py`

### Implementation for User Story 3

- [ ] T028 [US3] [FR-005, SC-003] Implement `analysis/profiling.py` to measure peak memory usage and inference latency on the lightweight model (FR-005). **Constraint**: **Simulated 2-core CPU**. **Mechanism**: The script MUST be executed via `taskset -c 0-1 python analysis/profiling.py`. The code MUST include a runtime check: `assert os.cpu_count() == 2 ` (or equivalent logic to verify active cores) and raise `RuntimeError("CPU constraint violation: expected 2 cores")` if the count differs. **Tools**: Use `tracemalloc` for memory and `time.perf_counter` for latency. **Batch Size**: 100 routes. **Dependency**: T012b. **Deliverable**: `data/analysis/profiling_report.json` containing `latency_ms`, `peak_memory_mb`, `cpu_cores_used`.
- [ ] T030a [US3] [Plan] [SC-003] Implement `analysis/profiling.py` to wrap the baseline LLM inference (T013) in a **`multiprocessing` timeout** and a **try/except block for OOM errors**. **Logic**: If T013 fails to load or run, catch the exception and set `baseline_status` to 'timeout' or 'inconclusive' WITHOUT crashing the pipeline. **Note**: Use `multiprocessing` for cross-platform compatibility (Windows/Linux). **Dependency**: T013.
- [ ] T030b [US3] [Plan] [SC-003] Update `data/analysis/profiling_report.json` to include the `baseline_status` field (values: 'success', 'timeout', 'inconclusive'). **Dependency**: T030a.
- [ ] T031 [US3] [Plan] [SC-003] Generate `data/analysis/profiling_report.json` with latency, memory, and feasibility status. **Dependency**: T028, T030a, T030b.
- [ ] T032 [US3] Update `docs/research.md` to document the feasibility findings and any "inconclusive" markers (Addressing tension in Plan vs Spec).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates: Update `docs/research.md` with the final inflection point value from `data/analysis/statistical_report.json` and `docs/quickstart.md` with execution steps.
- [ ] T034 Code cleanup: Refactor `data/preprocess.py` to extract city-filtering logic into a separate function.
- [ ] T035 [P] Performance optimization: Profile and optimize the top-N neighbor retrieval in `data/graph_utils.py` to reduce latency to ≤60 seconds per batch.
- [ ] T036 [P] Additional unit tests: Add unit tests for `graph_utils.py::compute_route_topological_complexity` in `tests/unit/test_graph_utils.py`.
- [ ] T037 [P] Run `quickstart.md` validation: Execute the commands in `docs/quickstart.md` in a fresh virtualenv and verify that `data/analysis/profiling_report.json` is generated with no errors.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
 - **CRITICAL**: Task T007b validation is a **hard blocking gate**. If T007b validation fails, Phase 3 tasks (T012+) are strictly prohibited from starting.
 - **Sequential Flow**: T004 (Download) → T004b (Sample) → T006a-c (Preprocess) → T007a (Build Graph) → T007b (Validate Graph). T007a and T007b depend on T006a-c.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion (specifically T007b passing)
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - **Depends on T007b (graph validation)**. T014 and T015b run in parallel after T007b, but T015b depends on T014 for correlation.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T017 (US1 completion)** to ensure validity data is available.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T006a-c) can run in parallel
- **T007a and T007b are NOT parallel with T006a-c** (they depend on T006a-c).
- Once Foundational phase completes (and T007b passes), all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **T014 (Evaluation) and T012a/T013 run in parallel** in Phase 3, but T015b depends on T014.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for `data/preprocess.py` output schema in `tests/contract/test_preprocess_schema.py`"
Task: "Integration test for stratified route validity scoring in `tests/integration/test_stratified_validity.py`"

# Launch all data prep for User Story 1 together:
Task: "Implement `data/graph_utils.py` function `prepare_route_sequences` (T015a)"
Task: "Implement `data/graph_utils.py` function `build_adjacency_index` (T012a)"
Task: "Implement `models/lightweight.py` function `predict_next_station` (T012b)"
Task: "Implement `models/baseline.py` (T013)"
Task: "Implement `analysis/evaluation.py` (T014)"

# Note: T015b depends on T014, so it cannot run in parallel with T014.
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
 - Developer A: User Story 1 (T012b, T013, T014)
 - Developer B: User Story 2 (T020-T025)
 - Developer C: User Story 3 (T028-T032)
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