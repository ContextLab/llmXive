---
description: "Task list template for feature implementation"
---

# Tasks: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

**Input**: Design documents from `/specs/001-llmxive-memory-optimization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directory structure per implementation plan (`projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/`) including `code/`, `data/`, `tests/`. (Note: `specs/` exists at repo root, do not create nested `specs/` inside project root)
- [X] T001b [P] Initialize Python project with dependencies (`pandas`, `numpy`, `scipy`, `networkx`, `requests`, `tqdm`, `pyyaml`, `llama-cpp-python`, `datasets`, `huggingface_hub`, `pytest`, `spacy`, `statsmodels`) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/requirements.txt`
- [X] T001c [P] Configure linting (ruff/flake8) and formatting (black) tools in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement robust graph construction and noise injection utilities in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/graph_utils.py`. **Note**: Noise injection logic here is the core function `inject_noise`.
- [X] T005 [P] Implement core LLM inference engine wrapper using `llama-cpp-python` (CPU only) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/inference.py`. **CRITICAL CONDITIONAL LOGIC**: The model download and inference MUST ONLY occur if the benchmark task explicitly requires generation (no ground-truth answer provided). If the benchmark provides ground-truth answers (as per Spec Assumption 2), the engine MUST skip generation, log a "SKIPPED_INFERENCE" flag, and explicitly log `token_count` and `latency` as "N/A" to ensure CSV consistency and avoid unnecessary CI resource consumption. **Model Resolution**: If generation is required, resolve the latest stable commit hash for `TheBloke/Llama-Chat-GGUF` from HuggingFace at runtime or use a known stable hash; do NOT use placeholders like 'abc123'. **Verification**: Must verify file existence and checksum before execution.
- [X] T006 [P] **Placeholder**: Hard timeout enforcement logic (logic only, no signal handler). Marked complete as a placeholder for T006-1.
- [ ] T006-1 [P] **Implement Signal-Based Termination**: Implement the actual OS signal handler (e.g., `signal.SIGALRM` or `signal.SIGTERM`) in `code/runner.py` that enforces a configurable hard timeout per task. The handler must interrupt the execution thread and log a "TIMEOUT" status. **Sequential Refinement**: This task refines T006; T006 logic must be present before T006-1. **Dependency**: T006 (sequential refinement, not parallel).
- [X] T007 Create base data structures for Task, Memory Graph, and Execution Log in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/__init__.py`
- [X] T035 Enforce Strict Data Fetching: Modify `code/data_loader.py` to **remove any `try/except` blocks that fall back to synthetic data generation** when the real LoCoMo dataset fetch fails. If `datasets.load_dataset` or the HuggingFace Hub download fails, the script must **raise an explicit exception** and halt execution to prevent silent fabrication. **Explicitly distinguish between 'injecting noise into real data' (required) and 'generating fake data to replace missing real data' (forbidden)**. Add a unit test in `tests/unit/test_data_loader.py` that verifies the script raises an error when provided with an invalid dataset ID.
- [X] T036 [P] **Implement Streaming for Large Datasets**: Refactor `code/data_loader.py` to support **streaming mode** for the LoCoMo dataset if the full download exceeds RAM limits (e.g., `load_dataset(..., streaming=True)`). Implement an iterator-based processing loop in `code/runner.py` that processes tasks in **configurable chunks** without loading the entire dataset into memory, ensuring compliance with the **~6GB RAM limit** (trigger streaming if estimated dataset size > 6GB).
- [X] T037 [US1, US2, US3, US4] **Enhance Degenerate Graph Handling**: Add explicit logic in `code/graph_utils.py` to detect and handle **disconnected components** and **single-node graphs** before traversal. Ensure the `full.py` and `lazy.py` strategies explicitly check for graph connectivity and log a "DEGENERATE" flag rather than attempting traversal that might cause infinite loops or division-by-zero errors. **(Note: Modified file shared with T004; depends on T004)**
- [X] T039 [P] **Add Deterministic Seed Verification**: Add a script `code/utils/verify_seeds.py` that re-runs the noise injection process (T011b) on the clean graph data (from T011a-1b) with the fixed seed and compares the output hash against the stored artifact hash in `state/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re.yaml` under the key `artifact_hashes['graph_noise_42']` (generated by T011c) to ensure **reproducibility** of the synthetic noisy graph dataset. Applies to US1, US2, and US3. **Dependency**: T011a-1b, T011c.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Active Reconstruction Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the "Full" active reconstruction strategy on LoCoMo benchmark tasks to establish a ground-truth baseline.

**Independent Test**: The system runs the baseline algorithm on a fixed subset of LoCoMo tasks and outputs a CSV containing `task_id`, `accuracy`, `nodes_visited`, and `inference_time_seconds`.

### Implementation for User Story 1

- [ ] T011a [US1] **Download LoCoMo Benchmark**: Implement a script in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py` to download the LoCoMo benchmark subset from HuggingFace dataset `locomo/locomo-benchmark` (split: `test`, config: `locomo`, trust_remote_code=True). **Output**: `data/raw/locomo.jsonl`. **Columns**: `question`, `context`, `answer`. **CRITICAL**: Verify the presence of expected columns; if missing, raise `ValueError("Dataset schema mismatch")`. **Dependency**: T035, T036. <!-- FAILED: unspecified -->
- [X] T011a-3 [US1] **Record Raw Data Checksum**: Implement a script in `code/utils/checksum.py` to generate the SHA-256 checksum of `data/raw/locomo.jsonl` **immediately after T011a completes** and before any graph construction. **Output**: Record the hash in `state/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re.yaml` under `artifact_hashes['locomo_raw']`. **Dependency**: T011a.
- [ ] T011a-1a [US1] **Extract Triples**: Implement NER/Rule-Based extraction logic in `code/data_loader.py` that parses the **Input: data/raw/locomo.jsonl** records. For each record, extract subject-verb-object triples from the `context` field using `en_core_web_sm` and spaCy dependency parser. **Output**: Intermediate list of triples per task. **Dependency**: T011a.
- [ ] T011a-1b [US1] **Serialize Graph**: Convert extracted triples (from T011a-1a) into JSON serialization: `data/intermediate/graphs_raw.json` where keys are `task_id` and values are lists of edges (dict: `{"source": "node_id", "target": "node_id", "relation_string": "flattened_relation_text"}`). **Verification**: Run `pytest tests/unit/test_graph_utils.py` to validate schema compliance against `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/contracts/dataset.schema.yaml`. **Dependency**: T011a-1a.
- [X] T011a-2 [US1] **Schema Validation**: Create a unit test `tests/unit/test_graph_utils.py::test_graph_schema_compliance` that verifies the output of T011a-1b matches the `dataset.schema.yaml` contract exactly before noise injection proceeds. **Dependency**: T011a-1b.
- [X] T011b [US1] **Implement Noise Injection Logic**: Implement the core function `inject_noise(graph, ratio, seed)` in `code/graph_utils.py` that **replaces** a proportion of existing edges with random edges (noise injection). **Parameters**: `ratio = 0.1`. **Selection Algorithm**: Select `ratio * total_edges` existing edges uniformly at random and **replace** them with random edges between arbitrary node pairs (excluding self-loops). **Constraint**: The total edge count remains constant; existing edges are removed and replaced. **Output**: Function in `code/graph_utils.py`. **Unit Test**: `tests/unit/test_graph_utils.py::test_inject_noise_replaces_edges`. **Dependency**: T004 (reuses logic), T011a-2 (validation of input).
- [ ] T011c [US1] **Generate Noisy Graph Dataset**: Implement a script in `code/data_loader.py` that calls `inject_noise` (T011b) on the graph structure generated in T011a-1b to generate the synthetic noisy graph dataset by **replacing** edges (per Spec Edge Cases and FR-001). **Output**: `data/processed/graphs/graph_noise_42.json`. **Verification**: Run `pytest tests/unit/test_graph_utils.py::test_inject_noise_replaces_edges` AND confirm `data/processed/graphs/graph_noise_42.json` exists and has non-zero size. **Dependency**: T011a-1b, T011b.
- [X] T012 [US1] **Implement Full Active Reconstruction Strategy**: Implement the "Full" traversal algorithm in `code/strategies/full.py` that traverses the entire relevant subgraph for each query, logging `nodes_visited` and `execution_time`. **Robustness Requirement**: Must detect disconnected components before traversal; if the target node is unreachable, flag the task as "unresolved" or default to full traversal of the connected component without crashing. **Note**: Implementation can proceed independently, but runner tasks (T013) depend on T011a-1 completion. **Dependency**: T004, T007, T037.
- [ ] T013 [US1] **Baseline Execution Runner**: Implement baseline execution runner using `code/runner.py` that logs `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, and `status` to `data/processed/baseline_results.csv`. **Implementation Requirement**: Explicitly map degenerate/unresolved states detected by T006/T037 to the CSV status column. **Dependency**: T011a, T011a-1b, T012, T006, T006-1.
- [ ] T013b [US1] **Noisy Baseline Execution Runner**: Implement noisy baseline execution runner using `code/runner.py` on the synthetic noisy graphs, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, and `status` to `data/processed/noisy_baseline_results.csv`. **Implementation Requirement**: Explicitly map degenerate/unresolved states detected by T006/T037 to the CSV status column. **Dependency**: T011a-1b, T011c, T012, T006, T006-1.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heuristic Strategy Comparison (Priority: P2)

**Goal**: Execute "Lazy" and "Greedy" traversal strategies and compare against baseline.

- [X] T017 [US2] **Implement Lazy Traversal**: Implement the "Lazy" traversal heuristic in `code/strategies/lazy.py` that defers edge expansion until an evidence threshold is triggered. **Logging Requirement**: Log the reduced node count and the **specific dynamic evidence threshold value used** (e.g., confidence score > 0.7 calculated per run) in the execution log. **Dependency**: T012, T004.
- [X] T018 [US2] **Implement Greedy Traversal**: Implement the "Greedy" traversal heuristic in `code/strategies/greedy.py` that selects only the top-k confidence edges. **Logging Requirement**: Log the reduced node count, accuracy, and the **specific threshold value used** (e.g., top-k value or confidence score cutoff) in the execution log. **Dependency**: T012, T004.
- [ ] T019a [US2] **Lazy Execution Runner**: Implement execution runner for Lazy strategy using `code/runner.py`, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, `evidence_threshold` (dynamic value), and `status` to `data/processed/lazy_results.csv`. **Dependency**: T011a, T011a-1b, T012, T017, T006, T006-1.
- [ ] T019b [US2] **Greedy Execution Runner**: Implement execution runner for Greedy strategy using `code/runner.py`, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, `evidence_threshold` (threshold value used for top-k selection), and `status` to `data/processed/greedy_results.csv`. **Dependency**: T011a, T011a-1b, T012, T018, T006, T006-1. <!-- FAILED: unspecified -->
- [ ] T019c [US2] **Noisy Lazy Execution Runner**: Implement execution runner for Lazy strategy on noisy graphs, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, `evidence_threshold` (dynamic value), and `status` to `data/processed/noisy_lazy_results.csv`. **Dependency**: T011a-1b, T011c, T017, T006, T006-1.
- [ ] T019d [US2] **Noisy Greedy Execution Runner**: Implement execution runner for Greedy strategy on noisy graphs, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, `evidence_threshold` (threshold value used), and `status` to `data/processed/noisy_greedy_results.csv`. **Dependency**: T011a-1b, T011c, T018, T006, T006-1.

---

## Phase 5: User Story 3 - Statistical Significance and Threshold Analysis (Priority: P3)

**Goal**: Perform statistical hypothesis testing and threshold analysis.

- [ ] T020 [US3] **Sensitivity Analysis**: Implement sensitivity analysis for Lazy heuristic thresholds across values **{0.5, 0.7, 0.9}** as mandated by Spec Assumptions. **Output**: `data/processed/sensitivity_analysis.csv` with schema: `task_id, threshold, accuracy, nodes_visited, latency_ms`. **Verification**: Ensure the file exists and contains rows for all three thresholds. **Dependency**: T017, T019a (runner logic).
- [X] T024a [US3] **Statistical Analysis (Clean)**: Perform paired t-test/Wilcoxon on accuracy distributions of heuristics vs baseline (clean data). **Output**: `data/processed/statistical_results.json` containing p-value and test statistic. **Dependency**: T013, T019a, T019b.
- [X] T024b [US3] **Statistical Analysis (Noisy)**: Perform paired t-test/Wilcoxon on accuracy distributions of heuristics vs baseline (noisy data). **Dependency**: T013b, T019c, T019d.
- [ ] T025 [US3] **Point-Biserial Correlation**: Calculate Point-Biserial correlation coefficient between `nodes_visited` and reasoning success rate across all tasks. **Output**: `data/processed/correlation_results.json`. **Dependency**: T013, T019a, T019b.
- [ ] T027 [US3] **Threshold & Inflection Analysis**: Implement binning algorithm (n >= 3 per bin) to identify the first bin with mean accuracy < 95% of the baseline. **Output**: `data/processed/threshold_analysis.json` containing the following keys: `inflection_point` (node count), `correlation_coefficient`, `trend_summary`, `is_significant` (boolean), `p_value`. **Constraint**: Calculate p-value using `scipy.stats.ttest_ind` with alpha=0.05. **CRITICAL**: Only report `inflection_point` if `is_significant` is true (p < 0.05). **Dependency**: T024a, T024b, T025.

---

## Phase 6: Validation & Audit (Priority: P1)

**Goal**: Ensure data integrity, reproducibility, and compliance.

- [ ] T040 [FR-001] [Constitution-III] **Audit Data Loader**: Implement a test that mocks `datasets.load_dataset` to fail and asserts the script exits with a non-zero code. **Command**: Run `pytest tests/unit/test_data_loader.py::test_no_fallback_on_failure`. **Clarification**: This test enforces code integrity (Constitution Principle III) by ensuring the script fails fast on data fetch errors, not a research pipeline fallback. The spec's assumption of availability is for the research phase, not the implementation phase. **Dependency**: T035.
- [ ] T041 [FR-001] [Constitution-III] **Validate Streaming**: Implement a test that verifies streaming mode works correctly for large datasets. **Command**: Run `pytest tests/unit/test_data_loader.py::test_streaming_mode`. **Dependency**: T036.
- [ ] T042 [US1] [FR-001] **Verify Noise Injection Reproducibility**: Execute `code/utils/verify_seeds.py` (T039) and confirm that the generated `data/processed/graphs/graph_noise_42.json` produces the exact same SHA-256 hash on two separate runs with the same seed. **Dependency**: T011c, T039.
- [ ] T043 [FR-001] [Constitution-III] **Confirm Real Data Source**: Verify that the LoCoMo dataset is fetched from the correct HuggingFace source and no synthetic fallback is used. **Command**: Run `pytest tests/unit/test_data_loader.py::test_real_data_source`. **Dependency**: T011a.

---

## Phase 7: Robustness & Edge Case Validation (Priority: P1)

**Goal**: Explicitly validate edge cases defined in spec (disconnected graphs, timeouts, degenerate inputs) to ensure pipeline stability.

- [X] T044 [US4] **Implement Disconnected Graph Handler**: Implement logic in `code/strategies/lazy.py` and `code/strategies/greedy.py` to detect when the target node is unreachable in the current component. **Action**: If unreachable, default to a full traversal of the connected component or flag as "unresolved" in the results CSV without crashing. **Dependency**: T037, T017, T018.
- [ ] T045 [US4] **Implement Timeout Handler Unit Test**: Create `tests/integration/test_timeout_handler.py` that injects a **real blocking operation** (e.g., `time.sleep()`) to trigger the actual signal-based termination logic in `runner.py` and asserts the runner logs "TIMEOUT", records the status, and proceeds to the next task. **Dependency**: T006, T006-1.
- [X] T046 [US4] **Implement Degenerate Graph Handler**: Create a unit test `tests/unit/test_graph_utils.py::test_degenerate_graph_handling` that passes a single-node and zero-edge graph to the traversal strategies and asserts no division-by-zero errors occur, returning a specific "degenerate" flag. **Dependency**: T037.
- [X] T047 [US4] **End-to-End Robustness Test**: Implement an integration test `tests/integration/test_robustness_e2e.py` that runs the full pipeline on a mixed dataset containing clean tasks, disconnected graphs, and degenerate inputs, verifying that the final CSV contains a complete record for every input task (either a result or a failure flag) and the process exits with code 0. **Dependency**: T044, T045, T046.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Validation & Audit (Phase 6)**: Depends on all desired user stories being complete
- **Robustness & Edge Case Validation (Phase 7)**: Depends on Foundational and core Strategy implementations (US1, US2)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **User Story 4 (P1 - Robustness)**: Can start after Foundational and Strategy implementations (US1, US2) to validate edge cases in those strategies.

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
5. Add Phase 7 (Robustness) → Validate edge cases → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3 / Robustness
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
