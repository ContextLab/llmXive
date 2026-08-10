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

- [X] T037 [P] [US1, US2, US3] **Enhance Degenerate Graph Handling**: Add explicit logic in `code/graph_utils.py` to detect and handle **disconnected components** and **single-node graphs** before traversal. Ensure the `full.py` and `lazy.py` strategies explicitly check for graph connectivity and log a "DEGENERATE" flag rather than attempting traversal that might cause infinite loops or division-by-zero errors. **(Note: Modified file shared with T004; removed [P] tag)**
- [X] T004 [P] Implement robust graph construction and noise injection utilities in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/graph_utils.py`
- [X] T005 [P] Implement core LLM inference engine wrapper using `llama-cpp-python` (CPU only) that accepts a **configurable model path** (via `config.py`) for **real inference** (NO mocks) and **logging token counts and latency** as primary metrics. **Selection Logic**: If no path provided, download from `TheBloke/Llama-7B-Chat-GGUF` and select the file with the **largest file size** among files matching `*.Q4_K_M.gguf`. **Verification**: Must verify file existence and checksum before execution. in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/inference.py`
- [X] T006 [P] Implement hard timeout enforcement logic (fixed duration per task) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/runner.py` that logs the timeout event and **proceeds to the next task without hanging**
- [X] T007 Create base data structures for Task, Memory Graph, and Execution Log in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/__init__.py`
- [X] T008 [P] Setup unit test framework (`pytest`) and configure `tests/` directory structure
- [X] T035 Enforce Strict Data Fetching: Modify `code/data_loader.py` to **remove any `try/except` blocks that fall back to synthetic data generation** when the real LoCoMo dataset fetch fails. If `datasets.load_dataset` or the HuggingFace Hub download fails, the script must **raise an explicit exception** and halt execution to prevent silent fabrication. **Explicitly distinguish between 'injecting noise into real data' (required) and 'generating fake data to replace missing real data' (forbidden)**. Add a unit test in `tests/unit/test_data_loader.py` that verifies the script raises an error when provided with an invalid dataset ID.
- [X] T036 [P] [US1, US2, US3] **Implement Streaming for Large Datasets**: Refactor `code/data_loader.py` to support **streaming mode** for the LoCoMo dataset if the full download exceeds RAM limits (e.g., `load_dataset(..., streaming=True)`). Implement an iterator-based processing loop in `code/runner.py` that processes tasks in **configurable chunks** without loading the entire dataset into memory, ensuring compliance with the **~6GB RAM limit** (trigger streaming if estimated dataset size > 6GB).
- [X] T039 [P] **Add Deterministic Seed Verification**: Add a script `code/utils/verify_seeds.py` that re-runs the noise injection process (T011b) with the fixed seed and compares the output hash against the stored artifact hash to ensure **reproducibility** of the synthetic noisy graph dataset. Applies to US1, US2, and US3.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Active Reconstruction Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the "Full" active reconstruction strategy on LoCoMo benchmark tasks to establish a ground-truth baseline.

**Independent Test**: The system runs the baseline algorithm on a fixed subset of LoCoMo tasks and outputs a CSV containing `task_id`, `accuracy`, `nodes_visited`, and `inference_time_seconds`.

### Implementation for User Story 1

- [ ] T011a [US1] **Download LoCoMo Benchmark**: Implement a script in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py` to download the LoCoMo benchmark subset from HuggingFace dataset `locomo/locomo-benchmark` (split: `test`, columns: `question`, `context`, `answer`). **Output**: `data/raw/locomo.csv`. **CRITICAL**: This task MUST NOT include graph parsing logic; it only downloads and saves the raw CSV. If the dataset fetch fails, the script must **raise `ValueError("Dataset fetch failed")`** (per T035). **Dependency**: T035.
- [ ] T011a-1a [US1] **Graph Construction - NER Extraction**: Implement the NER/Rule-Based extraction logic in `code/data_loader.py` that parses the **Input: data/raw/locomo.csv** context strings into subject-verb-object triples using `en_core_web_sm` and spaCy dependency parser. For multi-hop, concatenate relation strings with a pipe delimiter (|) and treat the first noun phrase as source and last as target. **Dependency**: T011a.
- [ ] T011a-1b [US1] **Graph Construction - JSON Serialization**: Implement the JSON serialization logic in `code/data_loader.py` that converts the extracted triples into the output schema: JSON object where keys are `task_id` and values are lists of edges. Each edge is a dict: `{"source": "node_id", "target": "node_id", "relation_string": "flattened_relation_text"}`. **Output File**: `data/intermediate/graphs_raw.json`. **Dependency**: T011a-1a.
- [ ] T011a-1c [US1] **Graph Construction - Verification**: Write a unit test in `tests/unit/test_graph_utils.py` that verifies the output schema matches `contracts/dataset.schema.yaml`. **Verification Step**: Run `python -c "import json; json.load(open('data/intermediate/graphs_raw.json'))"` and assert schema compliance. **Dependency**: T011a-1b.
- [ ] T011b [US1] **Implement Noise Injection Logic**: Implement the core function `inject_noise(graph, ratio, seed)` in `code/graph_utils.py` that **replaces** a proportion of random edges to the original graph. **Parameters**: `ratio = 0.1`. **Selection Algorithm**: Generate `ratio * total_edges` random edges between non-adjacent node pairs (excluding self-loops), **remove** the corresponding original edges, and **add** the new random edges. **Output**: Function in `code/graph_utils.py`. **Unit Test**: `tests/unit/test_graph_utils.py::test_inject_noise_replaces_edges`. **Dependency**: T004, T011a-1a, T011a-1b, T011a-1c. **(Note: Status changed from [X] to [ ] due to dependency on pending T011a-1)**.
- [ ] T011d [US1] **Verify noise injection logic**: Implement a unit test in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/unit/test_graph_utils.py` that checks edge replacement ratio (replacing, not adding) and randomness against FR-001 definition. **Dependency**: T011b. **(Note: Status changed from [X] to [ ] due to dependency on pending T011a-1)**.
- [ ] T011c [US1] **Generate Noisy Graph Dataset**: Implement a script in `code/data_loader.py` that calls `inject_noise` (T011b) on the graph structure generated in T011a-1 to generate the synthetic noisy graph dataset by **replacing** edges with random edges. **Output**: `data/processed/graphs/graph_noise_42.json`. **Verification**: Run `pytest tests/unit/test_graph_utils.py::test_inject_noise_replaces_edges` and confirm exit code 0 before proceeding. **Dependency**: T011a-1a, T011a-1b, T011a-1c, T011b, T011d. **(Note: T011a-1 is a hard blocker for this task)**.
- [ ] T013 [US1] **Baseline Execution Runner**: Implement baseline execution runner using `code/runner.py` that logs `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, and `status` (values: 'completed', 'timeout', 'degenerate', 'unresolved') to `data/processed/baseline_results.csv`. **Implementation Requirement**: Explicitly map degenerate/unresolved states detected by T006/T037 to the CSV status column. **Dependency**: T011a, T012, T006. **(Note: T011a is a hard blocker for this task)**.
- [ ] T013b [US1] **Noisy Baseline Execution Runner**: Implement noisy baseline execution runner using `code/runner.py` on the synthetic noisy graphs, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, and `status` (values: 'completed', 'timeout', 'degenerate', 'unresolved') to `data/processed/noisy_baseline_results.csv`. **Implementation Requirement**: Explicitly map degenerate/unresolved states detected by T006/T037 to the CSV status column. **Dependency**: T011a-1a, T011a-1b, T011a-1c, T011c, T012, T004, T006. **(Note: T011a-1 and T011c are hard blockers for this task)**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heuristic Strategy Comparison (Priority: P2)

**Goal**: Execute "Lazy" and "Greedy" traversal strategies and compare against baseline.

- [ ] T017 [US2] **Implement Lazy Traversal**: Implement the "Lazy" traversal heuristic in `code/strategies/lazy.py` that defers edge expansion until an evidence threshold is triggered. **Logging Requirement**: Log the reduced node count and the specific evidence threshold value used (e.g., confidence score > 0.7) in the execution log. **Dependency**: T012, T004.
- [ ] T018 [US2] **Implement Greedy Traversal**: Implement the "Greedy" traversal heuristic in `code/strategies/greedy.py` that selects only the top-k confidence edges. **Logging Requirement**: Log the reduced node count and accuracy. **Dependency**: T012, T004.
- [ ] T019a [US2] **Lazy Execution Runner**: Implement execution runner for Lazy strategy using `code/runner.py`, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, `evidence_threshold`, and `status` to `data/processed/lazy_results.csv`. **Dependency**: T011a, T012, T017, T006. **(Note: T011a is a hard blocker for this task)**.
- [ ] T019b [US2] **Greedy Execution Runner**: Implement execution runner for Greedy strategy using `code/runner.py`, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, and `status` to `data/processed/greedy_results.csv`. **Dependency**: T011a, T012, T018, T006. **(Note: T011a is a hard blocker for this task)**.
- [ ] T019c [US2] **Noisy Lazy Execution Runner**: Implement execution runner for Lazy strategy on noisy graphs, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, `evidence_threshold`, and `status` to `data/processed/noisy_lazy_results.csv`. **Dependency**: T011a-1a, T011a-1b, T011a-1c, T011c, T017, T006. **(Note: T011a-1 and T011c are hard blockers for this task)**.
- [ ] T019d [US2] **Noisy Greedy Execution Runner**: Implement execution runner for Greedy strategy on noisy graphs, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, and `status` to `data/processed/noisy_greedy_results.csv`. **Dependency**: T011a-1a, T011a-1b, T011a-1c, T011c, T018, T006. **(Note: T011a-1 and T011c are hard blockers for this task)**.

---

## Phase 5: User Story 3 - Statistical Significance and Threshold Analysis (Priority: P3)

**Goal**: Perform statistical hypothesis testing and threshold analysis.

- [ ] T020 [US3] **Sensitivity Analysis**: Implement sensitivity analysis for Lazy heuristic thresholds across a range of values.. **Dependency**: T019a or T019c. **(Note: Blocked by execution runners)**.
- [ ] T024a [US3] **Statistical Analysis (Clean)**: Perform paired t-test/Wilcoxon on accuracy distributions of heuristics vs baseline (clean data). **Dependency**: T033, T013, T019a, T019b. **(Note: Blocked by execution runners)**.
- [ ] T024b [US3] **Statistical Analysis (Noisy)**: Perform paired t-test/Wilcoxon on accuracy distributions of heuristics vs baseline (noisy data). **Dependency**: T033, T013b, T019c, T019d. **(Note: Blocked by execution runners)**.
- [ ] T027b-1 [US3] **Binning Logic Implementation**: Implement the binning algorithm for threshold analysis: Calculate N = total rows in input CSV; bin tasks by `nodes_visited` count such that each bin contains at least 3 tasks (n >= 3). If distinct(node_counts) > 0.5 * N, merge adjacent bins until n >= 3 per bin. **Dependency**: T024a, T024b.
- [ ] T027b-2 [US3] **Inflection Point Detection**: Implement logic to identify the first bin with mean accuracy < 95% of the baseline. **Dependency**: T027b-1.
- [ ] T027b-3 [US3] **Threshold Analysis File Update**: Implement logic to write the inflection point and correlation coefficient to `data/processed/threshold_analysis.json`. **Dependency**: T027b-2.

---

## Phase 6: Validation & Audit (Priority: P1)

**Goal**: Ensure data integrity, reproducibility, and compliance.

- [ ] T040 [FR-001] [Constitution-III] **Audit Data Loader**: Implement a test that mocks `datasets.load_dataset` to fail and asserts the script exits with a non-zero code. **Command**: Run `pytest tests/unit/test_data_loader.py::test_no_fallback_on_failure`. **Clarification**: This test enforces code integrity (Constitution Principle III) by ensuring the script fails fast on data fetch errors, not a research pipeline fallback. The spec's assumption of availability is for the research phase, not the implementation phase. **Dependency**: T035. **(Note: Blocked by T035)**.
- [ ] T041 [FR-001] [Constitution-III] **Validate Streaming**: Implement a test that verifies streaming mode works correctly for large datasets. **Command**: Run `pytest tests/unit/test_data_loader.py::test_streaming_mode`. **Dependency**: T036. **(Note: Blocked by T036)**.
- [ ] T042 [US1] [FR-001] **Verify Noise Injection Reproducibility**: Execute `code/utils/verify_seeds.py` (T039) and confirm that the generated `data/processed/graphs/graph_noise_42.json` produces the exact same SHA-256 hash on two separate runs with the same seed. **If T039 is not complete, create `code/utils/verify_seeds.py` as part of this task**. **Dependency**: T011c, T039. **(Note: Moved from Phase 3 to Phase 6 to ensure T011c is complete)**.
- [ ] T043 [FR-001] [Constitution-III] **Confirm Real Data Source**: Verify that the LoCoMo dataset is fetched from the correct HuggingFace source and no synthetic fallback is used. **Command**: Run `pytest tests/unit/test_data_loader.py::test_real_data_source`. **Dependency**: T011a. **(Note: Blocked by T011a)**.