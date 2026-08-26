---
description: "Task list template for feature implementation"
---

# Tasks: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-memory-optimization/`
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
- [X] T001b [P] Initialize Python project with dependencies (`pandas`, `numpy`, `scipy`, `networkx`, `requests`, `tqdm`, `pyyaml`, `datasets`, `huggingface_hub`, `pytest`, `spacy`, `statsmodels`) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/requirements.txt`
- [X] T001c [P] Configure linting (ruff/flake8) and formatting (black) tools in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/`
- [X] T011a-3 **Download and Install spaCy Model**: Implement a script in `code/data_loader.py` to download and install the `en_core_web_sm` model using the programmatic `spacy.cli.download("en_core_web_sm", version="3.7.1")` API. **Constraint**: This task MUST run in a serial setup phase (do NOT mark as [P] if parallel execution risks race conditions in the model cache). **Dependency**: T001b. **Note**: Moved from Phase 3 to Phase 1 to ensure environment readiness before extraction logic. The `requirements.txt` (T001b) lists `spacy`, and this task ensures the model artifact is present in the CI environment before any extraction logic runs.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement robust graph construction and noise injection utilities in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/graph_utils.py`. **Note**: Noise injection logic here is the core function `inject_noise`.
- [X] T006 [P] **Implement Signal-Based Termination**: Implement the OS signal handler (e.g., `signal.SIGALRM` or `signal.SIGTERM`) in `code/runner.py` that enforces a configurable hard timeout per task. **Constraint**: Ensure the handler is registered within a context manager or specific scope to prevent global state conflicts with parallel tasks. This task replaces the previous placeholder T006. **Dependency**: T001b.
- [X] T007 Create base data structures for Task, Memory Graph, and Execution Log in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/__init__.py`
- [X] T035 Enforce Strict Data Fetching: Modify `code/data_loader.py` to **remove any `try/except` blocks that fall back to synthetic data generation** when the real LoCoMo dataset fetch fails. If `datasets.load_dataset` or the HuggingFace Hub download fails, the script must **raise an explicit exception** and halt execution to prevent silent fabrication in the production research pipeline. **Exception Handling for Development**: In local development environments, if the dataset is unavailable, the script may log a "SKIP" status and proceed, but must never generate synthetic data. **Dependency**: T035.
- [X] T036-NEW [P] **Implement In-Memory Data Loader**: Refactor `code/data_loader.py` to load the LoCoMo dataset into memory using `datasets.load_dataset(..., split=..., trust_remote_code=True)` without streaming. **Constraint**: The dataset size is assumed to fit within the RAM limit of the free-tier runner. **Dependency**: T035.
- [X] T036b-NEW [P] **Integrate In-Memory Loader into Runner**: Update `code/runner.py` to consume the in-memory list from T036-NEW. Ensure the runner processes tasks in a loop, writing results incrementally to the CSV to prevent memory buildup during long runs. **Dependency**: T036-NEW.
- [X] T037 [US1, US2, US3, US4] **Enhance Degenerate Graph Handling**: Add explicit logic in `code/graph_utils.py` to detect and handle **disconnected components** and **single-node graphs** before traversal. Ensure the `full.py` and `lazy.py` strategies explicitly check for graph connectivity and log a "DEGENERATE" flag rather than attempting traversal that might cause infinite loops or division-by-zero errors. **(Note: Modified file shared with T004; depends on T004)**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Active Reconstruction Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the "Full" active reconstruction strategy on LoCoMo benchmark tasks to establish a ground-truth baseline.

**Independent Test**: The system runs the baseline algorithm on a fixed subset of LoCoMo tasks and outputs a CSV containing `task_id`, `accuracy`, `nodes_visited`, and `inference_time_seconds`.

### Implementation for User Story 1

- [X] T011a [US1] **Download LoCoMo Benchmark**: Implement a script in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py` to download the LoCoMo benchmark subset from HuggingFace dataset `locomo/locomo-benchmark` (split: `test`, config: `locomo`, trust_remote_code=True). **Output**: `data/raw/locomo.jsonl`. **Columns**: `question`, `context`, `answer`. **CRITICAL**: Verify the presence of expected columns; if missing, raise `ValueError("Dataset schema mismatch")`. **Config Validation**: Before proceeding, verify the `config` string exists in the dataset metadata; if not, raise a descriptive error indicating the valid configs. **FALLBACK**: If the real download fails, the script MUST **raise an explicit exception** and halt execution (do NOT generate synthetic data). **Dependency**: T035, T036-NEW.
- [X] T011a-1a [US1] **Extract and Persist Triples**: Implement NER/Rule-Based extraction logic in `code/data_loader.py` that parses the **Input: data/raw/locomo.jsonl** records. For each record, extract subject-verb-object triples from the `context` field using `en_core_web_sm` and spaCy dependency parser. **Extraction Rules**: Subject is identified as 'nsubj', object is 'dobj'. If no direct objects are found, skip triple extraction for that sentence. This ensures deterministic output consistent with the chosen parsing rules. **CRITICAL PERSISTENCE**: Immediately write the extracted triples to `data/intermediate/triples_raw.jsonl` (one JSON object per line) to ensure data is available for downstream tasks. **Output**: `data/intermediate/triples_raw.jsonl`. **Error Handling**: If the `context` field is empty or contains no extractable triples, log "EMPTY_CONTEXT" and skip graph construction for that task (do not crash). **Dependency**: T011a, T011a-3 (Phase 1 completion).
- [X] T011a-1b [US1] **Serialize Graph**: Convert extracted triples (from `data/intermediate/triples_raw.jsonl`) into JSON serialization: `data/intermediate/graphs_raw.json` where keys are `task_id` and values are lists of edges (dict: `{"source": "node_id", "target": "node_id", "relation_string": "flattened_relation_text"}`). **Pre-Run Check**: Before reading `data/intermediate/triples_raw.jsonl`, the script MUST verify the file exists and is non-empty; if the file is missing or empty, raise a descriptive `FileNotFoundError` or `ValueError` indicating the upstream extraction (T011a-1a) failed. **Verification**: Run `pytest tests/unit/test_graph_utils.py` to validate schema compliance against `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/contracts/dataset.schema.yaml`. **Error Handling**: If schema validation fails, raise an exception and halt execution (do not proceed). **Dependency**: T011a, T011a-1a, T011a-3. **Note**: This task produces the artifact that T011a-2 validates; T011a-2 does not block T011a-1b.
- [X] T011a-2 [US1] **Schema Validation**: Create a unit test `tests/unit/test_graph_utils.py::test_graph_schema_compliance` that verifies the output of T011a-1b matches the `dataset.schema.yaml` contract exactly before noise injection proceeds. **Dependency**: T011a-1b.
- [X] T011b [US1] **Implement Noise Injection Logic**: Implement the core function `inject_noise(graph, ratio, seed)` in `code/graph_utils.py` that **adds** a proportion of random edges to the graph structure (edge addition) to simulate noise. **Parameters**: `ratio` MUST be loaded from `config.yaml` (default 0.1) to ensure tunability; do NOT hardcode the ratio. **Selection Algorithm**: Randomly select `ratio * total_edges` existing nodes and add a random edge between them, ensuring no self-loops or duplicate edges are created. **Constraint**: The total edge count will increase by the added edges. **Output**: Function in `code/graph_utils.py`. **Unit Test**: `tests/unit/test_graph_utils.py::test_inject_noise_adds_edges`. **Dependency**: T004 (reuses logic), T011a-2.
- [X] T011c [US1] **Generate Noisy Graph Dataset**: Implement a script in `code/data_loader.py` that calls `inject_noise` (T011b) on the graph structure generated in T011a-1b to generate the synthetic noisy graph dataset by **adding** random edges. **Output**: `data/processed/graphs/graph_noise_42.json`. **Verification**: Run `pytest tests/unit/test_graph_utils.py::test_inject_noise_adds_edges` AND confirm `data/processed/graphs/graph_noise_42.json` exists, has non-zero size, and the total edge count is greater than the original graph. **Dependency**: T011a-1b, T011b, T011a-2
- [X] T012 [US1] **Implement Full Active Reconstruction Strategy**: Implement the "Full" traversal algorithm in `code/strategies/full.py` that traverses the entire relevant subgraph for each query, logging `nodes_visited` and `execution_time`. **Robustness Requirement**: Must detect disconnected components before traversal; if the target node is unreachable, flag the task as "unresolved" or default to full traversal of the connected component without crashing. **Note**: Implementation can proceed independently, but runner tasks (T013) depend on T011a-1b completion. **Dependency**: T004, T007, T037.
- [X] T013 [US1] **Baseline Execution Runner**: Implement baseline execution runner using `code/runner.py` that logs `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, and `status` to `data/processed/baseline_results.csv`. **Implementation Requirement**: Explicitly map degenerate/unresolved states detected by T006/T037 to the CSV status column. **Valid Status Values**: "COMPLETED", "TIMEOUT", "DEGENERATE", "UNRESOLVED". **Dependency**: T011a, **T011a-1b**, T012, T006 (functional handler).
- [X] T013b [US1] **Noisy Baseline Execution Runner**: Implement noisy baseline execution runner using `code/runner.py` on the synthetic noisy graphs, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, and `status` to `data/processed/noisy_baseline_results.csv`. **Dependency**: T011a, **T011a-1b**, T011c, T012, T006.
- [X] T039 [US1] [FR-001] [Constitution-I] **Add Deterministic Seed Verification**: Add a script `code/utils/verify_seeds.py` that **re-runs the noise injection process (T011b) on the clean graph data (from T011a-1b) AND the LLM inference/traversal logic on a small subset** and compares the resulting **SHA-256 hash** against the stored artifact hash in `state/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re.yaml` under the key `artifact_hashes['graph_noise_42']` (which corresponds to the output of T011c) AND `artifact_hashes['baseline_results']` to ensure **reproducibility** of the synthetic noisy graph dataset AND the baseline results.   The script also generates an initial hash and writes it to the state file if it does not exist. The seed is set using `numpy.random.seed()` and `torch.manual_seed()`.  **Input Data Scope**: Hash is computed on `data/processed/graphs/graph_noise_42.json` and `data/processed/baseline_results.csv`. **Dependency**: T013, T011a-1b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heuristic Strategy Comparison (Priority: P2)

**Goal**: Execute "Lazy" and "Greedy" traversal strategies and compare against baseline.

- [X] T017 [US2] **Implement Lazy Traversal**: Implement the "Lazy" traversal heuristic in `code/strategies/lazy.py` that defers edge expansion until an evidence threshold is triggered. **Logging Requirement**: Log the reduced node count and the **actual evidence threshold value used** (e.g., confidence score > 0.7) in the execution log to `data/processed/lazy_config.log`. **Dependency**: T012, T004.
- [X] T018 [US2] **Implement Greedy Traversal**: Implement the "Greedy" traversal heuristic in `code/strategies/greedy.py` that selects only the top-k confidence edges. **Logging Requirement**: Log the reduced node count and accuracy. **Dependency**: T012, T004.
- [X] T019a [US2] **Lazy Execution Runner**: Implement execution runner for Lazy strategy using `code/runner.py`, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, and `status` to `data/processed/lazy_results.csv`. **Dependency**: T011a, T011a-1b, T012, T017, T006.
- [X] T019b [US2] **Greedy Execution Runner**: Implement execution runner for Greedy strategy using `code/runner.py`, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, and `status` to `data/processed/greedy_results.csv`. **Dependency**: T011a, T011a-1b, T012, T018, T006.

---

## Phase 5: User Story 3 - Statistical Significance and Threshold Analysis (Priority: P3)

**Goal**: Perform statistical hypothesis testing and threshold analysis.

- [X] T024a [US3] **Statistical Analysis (Clean)**: Perform paired t-test/Wilcoxon on accuracy distributions of heuristics vs baseline (clean data). **Output**: `data/processed/statistical_results.json` containing p-value and test statistic. **Dependency**: T013, T019a, T019b.
- [X] T024b [US3] **Statistical Analysis (Noisy)**: Perform paired t-test/Wilcoxon on accuracy distributions of heuristics vs baseline (noisy data). **Dependency**: T013b, T019a, T019b.
- [X] T025 [US3] **Point-Biserial Correlation**: Calculate Point-Biserial correlation coefficient between `nodes_visited` and reasoning success rate across all tasks. **Output**: `data/processed/correlation_results.json`. **Dependency**: T013, T019a, T019b.
- [X] T027 [US3] **Threshold & Inflection Analysis**: Implement dynamic binning algorithm to identify the first bin with mean accuracy < 95% of the baseline. **Algorithm**: Sort tasks by `nodes_visited`. Create bins such that each bin contains at least 3 tasks (n ≥ 3). If the initial binning results in fewer than 3 tasks in a bin, merge it with the adjacent bin until the n≥3 constraint is satisfied. Iterate through bins to find the first bin where mean accuracy < 95% of baseline. **Output**: `data/processed/threshold_analysis.json` containing inflection point (node count), correlation coefficient, trend summary, is_significant (boolean), and p-value. **Dependency**: T024a, T024b, T025.

---

## Phase 6: Validation & Audit (Priority: P1)

**Goal**: Ensure data integrity, reproducibility, and compliance.

- [X] T040 [FR-001] [Constitution-I] **Audit Data Loader**: Implement a comprehensive test that mocks `datasets.load_dataset` to fail and asserts the script exits with a non-zero code (enforcing "no synthetic fallback" for real data in production), AND verifies that the script uses the correct real data source when available.
- [X] T041 [FR-001] **Validate In-Memory Loading**: Implement a test that verifies the in-memory loader works correctly for the expected dataset size.
- [X] T042 [US1] [FR-001] **Verify Noise Injection Reproducibility**: Execute `code/utils/verify_seeds.py` (T039) after T039 completes its re-run and hash generation and confirm that the generated `data/processed/graphs/graph_noise_42.json` produces the exact same SHA-256 hash on two separate runs with the same seed.
- [X] T043 [US4] **Implement Robustness Test**: Create a script to run tests against edge cases (disconnected graphs, zero-edge graphs) and tasks designed to exceed the timeout limit.

---

## Phase 7: Robustness & Edge Case Validation (Priority: P1)

**Goal**: Explicitly validate edge cases defined in spec (disconnected graphs, timeouts, degenerate inputs) to ensure pipeline stability.
- [X] T044 [US4] **Implement Disconnected Graph Handler**: Implement logic in `code/strategies/lazy.py` and `code/strategies/greedy.py` to detect when the target node is unreachable in the current component.
- [X] T045 [US4] **Implement Timeout Handler Unit Test**: Create `tests/integration/test_timeout_handler.py` that injects a real blocking operation (e.g., `time.sleep()`) to trigger the actual signal-based termination logic in `runner.py` and asserts the runner logs "TIMEOUT", records the status, and proceeds to the next task.
- [X] T046 [US4] **Implement Degenerate Graph Handler**: Create a unit test `tests/unit/test_graph_utils.py::test_degenerate_graph_handling` that passes a single-node and zero-edge graph to the traversal strategies and asserts no division-by-zero errors occur, returning a specific "degenerate" flag.
- [X] T047-1 [US4] **Generate Mixed Robustness Dataset**: Create a script in `code/utils/generate_mixed_dataset.py` to generate a mixed dataset containing clean tasks, disconnected graphs, and degenerate inputs for robustness testing.
- [X] T047 [US4] **End-to-End Robustness Test**: Implement an integration test `tests/integration/test_robustness_e2e.py` that runs the full pipeline on the mixed dataset generated by T047-1, verifying that the final CSV contains a complete record for every input task (either a result or a failure flag) and the process exits with code 0.

---

## Phase 8: Documentation & Reporting (Priority: P3)

**Goal**: Synthesize results into a coherent report and update documentation.
- [X] T064 [US3, US4] **Implement Comprehensive Timeout & Degenerate Reporting**: Implement a script `code/report/categorize_status_counts.py` that reads all raw result CSVs and logs status counts to `data/processed/status_counts.json`. **Dependency**: T013, T013b, T019a, T019b.
- [X] T060a [US3] **Aggregate Results Data**: Implement a script `code/report/aggregate_results.py` that reads all JSON/CSV results AND the `status_counts.json` from T064 to produce an intermediate JSON file `data/processed/report_data.json`. **Dependency**: T024a, T024b, T025, T064.
- [X] T060b [US3] **Extract Limitations**: Implement a script `code/report/extract_limitations.py` that reads the `plan.md` Assumptions section to extract study limitations.
- [X] T060c [US3] **Generate Final Report**: Implement a script `code/report/generate_report.py` that combines `data/processed/report_data.json` and `data/processed/limitation_text.md` into a single Markdown report `docs/research_report.md`.

---

## Phase 9: Final Integration & Verification (Priority: P1)

**Goal**: Ensure all components work together and the pipeline is production-ready for the research phase.
- [X] T065 [US1, US2, US3, US4] **End-to-End Pipeline Verification**: Execute the full pipeline from data download to final report generation on a small subset of the LoCoMo benchmark.
- [X] T066 [FR-001] [Constitution-I] **Final Subset Reproducibility Check**: Re-run the pipeline and compare artifacts against stored hashes.