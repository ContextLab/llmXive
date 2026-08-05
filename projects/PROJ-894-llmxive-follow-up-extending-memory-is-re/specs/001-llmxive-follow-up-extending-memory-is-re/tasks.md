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
- [ ] T035 Enforce Strict Data Fetching: Modify `code/data_loader.py` to **remove any `try/except` blocks that fall back to synthetic data generation** when the real LoCoMo dataset fetch fails. If `datasets.load_dataset` or the HuggingFace Hub download fails, the script must **raise an explicit exception** and halt execution to prevent silent fabrication. **Explicitly distinguish between 'injecting noise into real data' (required) and 'generating fake data to replace missing real data' (forbidden)**. Add a unit test in `tests/unit/test_data_loader.py` that verifies the script raises an error when provided with an invalid dataset ID. **(Note: T035 must be completed before T011a and T011c to avoid merge conflicts; removed [P] tag)**
- [ ] T036 [P] [US1, US2, US3] **Implement Streaming for Large Datasets**: Refactor `code/data_loader.py` to support **streaming mode** for the LoCoMo dataset if the full download exceeds RAM limits (e.g., `load_dataset(..., streaming=True)`). Implement an iterator-based processing loop in `code/runner.py` that processes tasks in **configurable chunks** without loading the entire dataset into memory, ensuring compliance with the **~6GB RAM limit** (trigger streaming if estimated dataset size > 6GB). **(Note: Modified file shared with T035; removed [P] tag)**
- [X] T037 [P] [US1, US2, US3] **Enhance Degenerate Graph Handling**: Add explicit logic in `code/graph_utils.py` to detect and handle **disconnected components** and **single-node graphs** before traversal. Ensure the `full.py` and `lazy.py` strategies explicitly check for graph connectivity and log a "DEGENERATE" flag rather than attempting traversal that might cause infinite loops or division-by-zero errors. **(Note: Modified file shared with T004; removed [P] tag)**
- [X] T039 [P] **Add Deterministic Seed Verification**: Add a script `code/utils/verify_seeds.py` that re-runs the noise injection process (T011b) with the fixed seed and compares the output hash against the stored artifact hash to ensure **reproducibility** of the synthetic noisy graph dataset. **Applies to US1, US2, and US3** to fulfill Constitution Principle I.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Active Reconstruction Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the "Full" active reconstruction strategy on LoCoMo benchmark tasks to establish a ground-truth baseline.

**Independent Test**: The system runs the baseline algorithm on a fixed subset of LoCoMo tasks and outputs a CSV containing `task_id`, `accuracy`, `nodes_visited`, and `inference_time_seconds`.

### Implementation for User Story 1

- [ ] T011a [US1] **Download LoCoMo Benchmark**: Implement a script in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py` to download the LoCoMo benchmark subset from HuggingFace dataset `locomo/locomo-benchmark` (split: `test`, columns: `question`, `context`, `answer`). **Output**: `data/raw/locomo.csv`. **CRITICAL**: This task MUST NOT include graph parsing logic; it only downloads and saves the raw CSV. If the dataset fetch fails, the script must raise an exception (per T035). **Dependency**: T035.
- [ ] T011a-1 [US1] **Graph Construction**: Implement a script in `code/data_loader.py` that parses the **Input: data/raw/locomo.csv** context strings into a directed graph using NER/Rule-Based extraction. **Algorithm**: Use `en_core_web_sm` and spaCy dependency parser to identify subject-verb-object triples; for multi-hop, concatenate relation strings with a pipe delimiter (|) and treat the first noun phrase as source and last as target. **Output Schema**: JSON object where keys are `task_id` and values are lists of edges. Each edge is a dict: `{"source": "node_id", "target": "node_id", "relation_string": "flattened_relation_text"}`. **Output File**: `data/intermediate/graphs_raw.json`. **Dependency**: T011a.
- [X] T011b [US1] **Implement Noise Injection Logic**: Implement the core function `inject_noise(graph, ratio, seed)` in `code/graph_utils.py` that **adds** a proportion of random distractor edges to the original graph. **Parameters**: `ratio = 0.1`. **Selection Algorithm**: Generate `ratio * total_edges` random edges between non-adjacent node pairs (excluding self-loops) and **add** them to the existing graph structure. **Output**: Function in `code/graph_utils.py`. **Unit Test**: `tests/unit/test_graph_utils.py::test_inject_noise_adds_edges`. **Dependency**: T004.
- [X] T011d [US1] [FR-001, US1, US2, US3] **Verify noise injection logic**: Implement a unit test in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/unit/test_graph_utils.py` that checks **edge addition ratio** (adding, not replacing) and randomness against FR-001 definition (adding edges), ensuring the noise injection logic is correct and reproducible before strategy execution. **Tolerance**: ±1%; **Test**: Chi-square test for randomness. **Dependency**: T011b. **(Note: Moved before T011c to act as a gate for logic verification; T011d is a gate task, not a data producer)**
- [ ] T011c [US1] **Generate Noisy Graph Dataset**: Implement a script in `code/data_loader.py` that calls `inject_noise` (T011b) on the **graph structure generated in T011a-1** to generate the synthetic noisy graph dataset by **adding** a proportion of random distractor edges. **Output**: `data/processed/graphs/graph_noise_42.json`. **Dependency**: T011a-1, T011b, T011d. **(Note: T011d must pass before T011c runs)**
- [ ] T042 [US1, US2, US3] **Verify Noise Injection Reproducibility**: Execute `code/utils/verify_seeds.py` (T039) and confirm that the generated `data/processed/graphs/graph_noise_42.json` produces the **exact same SHA-256 hash** on two separate runs with the same seed. If the hash differs, investigate and fix the random number generator seeding in `code/graph_utils.py` (T011b). Document the hash in `docs/reproducibility.md`. **Dependency**: T011b, T011c, T039. **(Note: Moved from Phase 6 to Phase 3 for immediate reproducibility verification)**
- [X] T012 [US1] Implement "Full" active reconstruction algorithm (traverse entire relevant subgraph) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/strategies/full.py`
- [ ] T013 [US1] Implement baseline execution runner using `code/runner.py` that logs `task_id`, `accuracy` (normalized exact string match: lowercasing, stripping punctuation), `nodes_visited`, `latency_ms`, and `status` (values: 'completed', 'timeout', 'degenerate', 'unresolved') to `data/processed/baseline_results.csv`. **Output Schema**: `task_id` (str), `accuracy` (float), `nodes_visited` (int), `latency_ms` (float), `status` (str). **Dependency**: T011a, T012, T006.
- [ ] T013b [US1] Implement noisy baseline execution runner using `code/runner.py` on the **synthetic noisy graphs** (generated in T011c, output file: `data/processed/graphs/graph_noise_42.json`) that logs `task_id`, `accuracy` (normalized exact string match), `nodes_visited`, `latency_ms`, and `status` to `data/processed/noisy_baseline_results.csv`. **Output Schema**: `task_id` (str), `accuracy` (float), `nodes_visited` (int), `latency_ms` (float), `status` (str). **Dependency**: T011a-1, T011c, T012, T004, T006.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heuristic Strategy Comparison (Priority: P2)

**Goal**: Execute "Greedy" and "Lazy" traversal strategies on the same benchmark tasks to quantify efficiency/accuracy trade-offs.

**Independent Test**: The system runs the two heuristic implementations and generates a comparison report showing accuracy delta and efficiency gain relative to the P1 baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Unit test for "Lazy" traversal logic with evidence threshold in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/unit/test_strategies.py`
- [X] T016 [P] [US2] Unit test for "Greedy" traversal logic with top-k selection in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/unit/test_strategies.py`

### Implementation for User Story 2

- [X] T017 [US2] Implement "Lazy" traversal heuristic (defer edge expansion until threshold) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/strategies/lazy.py`. **Requirement**: Log the **specific evidence threshold value used for each task execution** (e.g., confidence score > 0.7) in the execution log. **CRITICAL**: This value MUST be written to the final `lazy_results.csv` output schema defined in T019a to ensure it is available for statistical analysis.
- [X] T018 [US2] Implement "Greedy" traversal heuristic (select top-k confidence edges) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/strategies/greedy.py`
- [ ] T019a [US2] Implement execution runner for **Lazy** strategy using `code/runner.py` logging to `data/processed/lazy_results.csv`. **Parameters**: Lazy uses a **default evidence threshold of 0.7**. **Output Schema**: `task_id` (str), `accuracy` (float), `nodes_visited` (int), `latency_ms` (float), `status` (str). **Dependency**: T011a, T012, T017, T006.
- [ ] T019b [US2] Implement execution runner for **Greedy** strategy using `code/runner.py` logging to `data/processed/greedy_results.csv`. **Parameters**: Greedy uses a **default top-k value of 3**. **Output Schema**: `task_id` (str), `accuracy` (float), `nodes_visited` (int), `latency_ms` (float), `status` (str). **Dependency**: T011a, T012, T018, T006. **(Note: Removed dependency on T019a to allow parallel execution)**
- [ ] T019c [US2] Implement noisy execution runner for **Lazy** strategy using `code/runner.py` on the **synthetic noisy graphs** (generated in T011c, output file: `data/processed/graphs/graph_noise_42.json`) logging to `data/processed/noisy_lazy_results.csv`. **Output Schema**: `task_id` (str), `accuracy` (float), `nodes_visited` (int), `latency_ms` (float), `status` (str). **Dependency**: T011a-1, T011c, T017, T006. **(Note: Removed dependency on T019a to allow parallel execution)**
- [ ] T019d [US2] Implement noisy execution runner for **Greedy** strategy using `code/runner.py` on the **synthetic noisy graphs** (generated in T011c, output file: `data/processed/graphs/graph_noise_42.json`) logging to `data/processed/noisy_greedy_results.csv`. **Output Schema**: `task_id` (str), `accuracy` (float), `nodes_visited` (int), `latency_ms` (float), `status` (str). **Dependency**: T011a-1, T011c, T018, T006. **(Note: Removed dependency on T019b to allow parallel execution)**
- [ ] T020 [US2] Implement sensitivity analysis sweep for **Lazy heuristic evidence threshold** (values `[0.5, 0.7, 0.9]`) and output results to `data/processed/sweep_results.csv` in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/strategies/lazy.py`. **Output Schema**: `threshold` (float), `accuracy` (float, mean), `nodes_visited` (int, mean), `latency_ms` (float, mean). **Dependency**: T019c (Noisy) OR T019a (Clean). **Note**: Can run independently on noisy data without waiting for clean data if T019a fails. **Dependency Note**: T020 can proceed as soon as *either* T019a or T019c is complete.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4b: User Story 4 - System Robustness (Priority: P1)

**Goal**: Ensure system robustness and error handling for edge cases, timeouts, and degenerate inputs.

**Independent Test**: The system is run against a dataset containing known edge cases and logs all errors.

### Implementation for User Story 4

- [ ] T034 [US4] **Implement timeout aggregation script**: Count tasks that timed out versus completed from **results CSVs** (T013, T019a, T019b, T019c, T019d) by filtering rows where `status` == 'timeout'. Aggregate into `stats_report.json` in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/analysis/stats.py`, fulfilling SC-005 requirement. **Dependency**: T006, T013, T019a, T019b, T019c, T019d.

**Checkpoint**: System robustness verified

---

## Phase 5: User Story 3 - Statistical Significance and Threshold Analysis (Priority: P3)

**Goal**: Perform statistical hypothesis testing and correlation analysis to validate research hypotheses.

**Independent Test**: The system ingests results CSVs and generates a statistical report containing p-values, confidence intervals, and correlation coefficients.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Unit test for paired t-test/Wilcoxon implementation on mock data in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/unit/test_stats.py`
- [X] T023 [P] [US3] Unit test for **Point-Biserial correlation** calculation (binary success vs continuous node count) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/unit/test_stats.py`

### Implementation for User Story 3

- [X] T033a [US3] **Create JSON Schema**: Create `contracts/results.schema.yaml` (JSON Schema format) defining the required columns for all result CSVs: `task_id` (string), `accuracy` (number), `nodes_visited` (integer), `latency_ms` (number), `status` (string). **Dependency**: None.
- [X] T033 [US3] **Implement schema validation script**: Implement a script in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/utils/validate_results.py` to verify all result CSVs strictly adhere to the schema defined in T033a. **Dependency**: T033a.
- [ ] T024a [US3] **Implement statistical analysis script (paired t-test/Wilcoxon)** comparing heuristic vs. baseline accuracy on the **primary LoCoMo benchmark dataset** (inputs: `baseline_results.csv`, `lazy_results.csv`, `greedy_results.csv` produced by T013 and T019a/T019b), outputting p-values, test statistics, and **confidence intervals** to `data/processed/stats_report.json` in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/analysis/stats.py`. **Method Selection**: Run Shapiro-Wilk test; if p < 0.05, use Wilcoxon; otherwise, use paired t-test. **Dependency**: T033.
- [ ] T024b [US3] **Implement robustness check script** to compare heuristic vs. baseline accuracy on the **synthetic noisy graph dataset** (inputs: `data/processed/noisy_baseline_results.csv`, `data/processed/noisy_lazy_results.csv`, `data/processed/noisy_greedy_results.csv` produced by T013b and T019c/T019d), calculating **paired t-test/Wilcoxon statistical tests (p-value, test statistic, and confidence intervals)** and accuracy deltas to `data/processed/noisy_stats_report.json` in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/analysis/stats.py`. **Method Selection**: Run Shapiro-Wilk test; if p < 0.05, use Wilcoxon; otherwise, use paired t-test. **Dependency**: T033, T013b, T019c, T019d.
- [X] T025 [US3] Implement correlation analysis script (Point-Biserial) between `nodes_visited` and reasoning success rate across all tasks in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/analysis/stats.py`. **Output**: Correlation coefficient and **95% Confidence Intervals**.
- [X] T027a [US3] **Perform Power Analysis**: Implement a script to calculate the Minimum Detectable Effect Size (MDES) and statistical power for the planned sample size (LoCoMo subset). Output `power_analysis.json` with MDES and power values. **Dependency**: T024a.
- [ ] T027b [US3] **Implement Threshold Analysis Logic**: Implement the binning algorithm to identify the **inflection point** where accuracy drops below a high-performance threshold relative to the baseline. **Algorithm**: (1) Read `p_value` from `data/processed/stats_report.json`; (2) **Always bin all tasks** by `nodes_visited` count (initial binning: unique node counts or deciles if sparse, where 'sparse' is defined as **if the number of distinct node-count values exceeds 50% of the total task count**); (3) Iteratively merge adjacent bins until every bin contains **at least 3 tasks (n ≥ 3)**; (4) Calculate mean accuracy per bin; (5) Identify the **first bin** with mean accuracy < 95% of the baseline mean (computed from `baseline_results.csv` considering only `status=completed` tasks); (6) **Read -> Modify -> Write**: Read `stats_report.json` into memory, append/update `inflection_point` and `threshold_significance` fields (where `threshold_significance` is True if p < 0.05, otherwise False), write to a temporary file, then rename the temp file to `data/processed/stats_report.json` to avoid race conditions. **Output**: Updated `data/processed/stats_report.json`. **Dependency**: T024a, T024b. **(Note: T027b must detect missing T024a output and proceed with a warning, setting significance to null, rather than skipping calculation)**
- [X] T026a [US3] **Create Jinja2 template**: Create the Jinja2 template at `code/analysis/templates/results.md.j2` defining the structure for `docs/results.md`, including placeholders for p-values, confidence intervals, correlation coefficients, and inflection points.
- [ ] T026b [US3] **Implement report generator**: Implement a script to **auto-generate** `docs/results.md` strictly from `data/processed/stats_report.json` (no hand-typed numbers) using the Jinja2 template created in T026a in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/analysis/report_generator.py`. **Output**: `docs/results.md`. **Dependency**: T024a, T024b, T027b, T034, T026a.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T028a [P] Update `README.md` with execution instructions and environment setup in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/`
- [X] T028b [P] **Review and finalize** `docs/results.md` generated by T026b and ensure documentation is complete in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/`. **Dependency**: T026b.
- [X] T029a [P] Refactor strategy modules (`full.py`, `lazy.py`, `greedy.py`) to inherit from a common base class in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/strategies/`
- [X] T031 [P] Additional unit tests for edge cases (zero edges, single node) in `tests/unit/`
- [X] T032 [P] Run `quickstart.md` validation and verify all results are reproducible

---

## Phase 6: Research Integrity & Reproducibility Audit (Priority: P1)

**Goal**: Ensure the project strictly adheres to the "No Fabrication" and "Real Data Only" constitution rules, specifically addressing the risk of synthetic fallbacks and ensuring streaming logic is robust.

**Independent Test**: A manual audit of `code/data_loader.py` and `code/runner.py` confirms no `try/except` blocks swallow network errors, and that streaming logic is triggered correctly for large inputs.

### Implementation for Research Integrity

- [ ] T040 [US1, US2, US3] **Audit Data Loader for Silent Fallbacks**: Execute a re-run of `code/data_loader.py` in a simulated network failure environment. **Mechanism**: Use `pytest` with a specific fixture to mock `datasets.load_dataset`. **Fixture Code**: `@pytest.fixture(autouse=True) def mock_load_dataset(mocker): mocker.patch('datasets.load_dataset', side_effect=ConnectionError("Simulated network failure")); return mock`. **Execution**: Run the script with this fixture active. **Verification**: Assert that the script **exits with a non-zero code** (e.g., `pytest` must capture `SystemExit` or check `returncode != 0`). **File Check**: Assert that **no new .json files** have been created in the `data/` directory since the start of the test (check modification timestamps of all files in `data/` before and after execution). **Output**: Generate an audit report `data/audit/audit_report.json` documenting the exit code, the absence of new files, and the timestamp of the check. **Dependency**: T035. **(Note: Distinct from T035 which implements the logic; T040 verifies it via execution and produces an audit report artifact)**
- [ ] T041 [US1, US2, US3] **Validate Streaming Logic Implementation**: Execute `code/runner.py` with `streaming=True` on a large subset. **Mechanism**: Use `tracemalloc` and `psutil` to monitor memory usage. **Sampling**: Sample memory usage at **1-second intervals** using `psutil.Process.memory_info.rss`. **Stability Criteria**: Ensure that peak memory usage does not exceed **[deferred] of available RAM** and that the memory trace remains stable (defined as: **max deviation from the median < 50MB** and **slope of linear regression on the memory trace < 0.01 MB/s**). **Output**: Generate a log `data/audit/streaming_log.json` containing the memory trace data, the calculated stability metrics, and a boolean `is_stable` flag. **Dependency**: T036. **(Note: Distinct from T036 which implements the logic; T041 validates it via execution and produces a memory log artifact)**
- [ ] T043 [US1, US2, US3] **Confirm Real Data Source Usage**: Verify that `code/data_loader.py` uses the **exact** HuggingFace dataset ID `locomo/locomo-benchmark` as specified in the plan and spec. Ensure there are no hard-coded paths to local CSVs or alternative mirrors that could lead to data drift. **Do NOT accept any 'injected' or 'verified' source from the execution stage**; the code MUST use the canonical LoCoMo ID. If a drift is detected, fail the audit. **Dependency**: T011a.

**Checkpoint**: Research integrity verified; no fabrication risks remain.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → US4 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Research Integrity (Phase 6)**: Must be completed after all data loading and generation tasks (T011a-c, T035-T039) are implemented but before final execution.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 4 (P1)**: Can start after Foundational (Phase 2) - Depends on T006, T013, T019
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2/US4 but should be independently testable

### Within Each User Story

- **Ordering Note**: T035, T036, T037 MUST complete before T011a. T011a and T011a-1 MUST complete before T011b (Noise Logic). T011b and T011d (Verify) MUST complete before T011c (Generation). T011c must also complete before T013b, T019c, and T019d (noisy runners). T033a (Schema) MUST complete before T033 (Validation). T033 MUST complete before T024a, T024b, and T027b. T020 (sweep) MUST complete before T027b. T027a (Power Analysis) MUST complete before T027b. T026a (template) MUST complete before T026b (generator). T026b MUST complete before T028b.
- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Foundational tasks (T035-T039) can be implemented in parallel with ongoing development if the specific modules are ready.
- **Phase 6 Tasks (T040, T041, T043)**: Can be run in parallel as they are audit/validation tasks on already implemented code, provided T035, T036, and T011a are complete.

**Note on Parallel Coordination**: While T035, T036, T037, T039 are marked [P] and modify different files, developers must coordinate to avoid merge conflicts on shared dependencies (e.g., `data_loader.py`). T035 must be completed before T011a and T011c.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for 'Full' traversal logic on a synthetic small graph in projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/unit/test_strategies.py"
Task: "Integration test for baseline execution pipeline with timeout handling in projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement 'Full' active reconstruction algorithm (traverse entire relevant subgraph) in projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/strategies/full.py"
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
4. Add User Story 4 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

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
- **Critical**: T035 is mandatory to prevent data fabrication; T036 ensures scalability; T037-T039 ensure scientific rigor.
- **Critical**: T011a includes graph construction; T011b/T011d use edge addition (not replacement); T013/T013b use normalized exact string match; T019a/b/c/d are independent; T027b depends on T024a for significance.
- **New**: Phase 6 (T040, T041, T043) added to explicitly audit against the "No Fabrication" and "Real Data Only" rules, ensuring the execution stage does not encounter silent fallbacks or streaming failures. T042 moved to Phase 3 for immediate reproducibility verification.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T044 Reconcile run-book vs implementation for `code/analysis.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/analysis.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T045 Reconcile run-book vs implementation for `code/utils/hash_artifacts.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/utils/hash_artifacts.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
