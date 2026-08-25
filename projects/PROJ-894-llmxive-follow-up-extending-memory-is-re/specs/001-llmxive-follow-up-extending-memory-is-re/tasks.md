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
- [X] T001b [P] Initialize Python project with dependencies (`pandas`, `numpy`, `scipy`, `networkx`, `requests`, `tqdm`, `pyyaml`, `datasets`, `huggingface_hub`, `pytest`, `spacy`, `statsmodels`) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/requirements.txt`
- [X] T001c [P] Configure linting (ruff/flake8) and formatting (black) tools in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/`
- [ ] T011a-3 [P] **Download and Install spaCy Model**: Implement a script in `code/data_loader.py` to download and install the `en_core_web_sm` model using the programmatic `spacy.cli.download("en_core_web_sm", version="3.7.1")` API. **Constraint**: This task MUST run in a serial setup phase (do NOT mark as [P] if parallel execution risks race conditions in the model cache). **Dependency**: T001b. **Note**: Moved from Phase 3 to Phase 1 to ensure environment readiness before extraction logic. The `requirements.txt` (T001b) lists `spacy`, and this task ensures the model artifact is present in the CI environment before any extraction logic runs.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement robust graph construction and noise injection utilities in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/graph_utils.py`. **Note**: Noise injection logic here is the core function `inject_noise`.
- [X] T006 [P] **Implement Signal-Based Termination**: Implement the OS signal handler (e.g., `signal.SIGALRM` or `signal.SIGTERM`) in `code/runner.py` that enforces a configurable hard timeout per task. The handler must interrupt the execution thread and log a "TIMEOUT" status. **Constraint**: Ensure the handler is registered within a context manager or specific scope to prevent global state conflicts with parallel tasks. This task replaces the previous placeholder T006. **Dependency**: T001b.
- [X] T007 Create base data structures for Task, Memory Graph, and Execution Log in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/__init__.py`
- [X] T035 Enforce Strict Data Fetching: Modify `code/data_loader.py` to **remove any `try/except` blocks that fall back to synthetic data generation** when the real LoCoMo dataset fetch fails. If `datasets.load_dataset` or the HuggingFace Hub download fails, the script must **raise an explicit exception** and halt execution to prevent silent fabrication in the production research pipeline. **Exception Handling for Development**: In local development environments, if the dataset is unavailable, the script may log a "SKIP" status and proceed, but must never generate synthetic data. **Explicitly distinguish between 'injecting noise into real data' (required) and 'generating fake data to replace missing real data' (forbidden)**. Add a unit test in `tests/unit/test_data_loader.py` that verifies the script raises an error when provided with a non-existent dataset ID. **Note**: This enforces Constitution Principle III (Data Hygiene) and overrides the spec's assumption of availability for robustness.
- [X] T036 [P] **Implement Streaming Data Iterator**: Refactor `code/data_loader.py` to expose a `stream_locomo_tasks(chunk_size=10)` generator that yields task dictionaries one by one (or in small batches) without loading the full JSONL into RAM. **Constraint**: Must use `datasets.load_dataset(..., streaming=True)` and handle the iterator correctly for both clean and noisy graph generation. **Dependency**: T035.
- [X] T036b [P] **Integrate Streaming into Runner**: Update `code/runner.py` to consume the streaming iterator from T036 instead of a pre-loaded list. Ensure the runner processes tasks in a loop, writing results incrementally to the CSV to prevent memory buildup during long runs. **Dependency**: T036.
- [X] T037 [US1, US2, US3, US4] **Enhance Degenerate Graph Handling**: Add explicit logic in `code/graph_utils.py` to detect and handle **disconnected components** and **single-node graphs** before traversal. Ensure the `full.py` and `lazy.py` strategies explicitly check for graph connectivity and log a "DEGENERATE" flag rather than attempting traversal that might cause infinite loops or division-by-zero errors. **(Note: Modified file shared with T004; depends on T004)**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Active Reconstruction Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the "Full" active reconstruction strategy on LoCoMo benchmark tasks to establish a ground-truth baseline.

**Independent Test**: The system runs the baseline algorithm on a fixed subset of LoCoMo tasks and outputs a CSV containing `task_id`, `accuracy`, `nodes_visited`, and `inference_time_seconds`.

### Implementation for User Story 1

- [X] T011a [US1] **Download LoCoMo Benchmark**: Implement a script in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/data_loader.py` to download the LoCoMo benchmark subset from HuggingFace dataset `locomo/locomo-benchmark` (split: `test`, config: `locomo`, trust_remote_code=True). **Output**: `data/raw/locomo.jsonl`. **Columns**: `question`, `context`, `answer`. **CRITICAL**: Verify the presence of expected columns; if missing, raise `ValueError("Dataset schema mismatch")`. **Config Validation**: Before proceeding, verify the `config` string exists in the dataset metadata; if not, raise a descriptive error indicating the valid configs. **FALLBACK**: If the real download fails, the script MUST **raise an explicit exception** and halt execution (do NOT generate synthetic data). **Dependency**: T035, T036.
- [X] T011a-1a [US1] **Extract and Persist Triples**: Implement NER/Rule-Based extraction logic in `code/data_loader.py` that parses the **Input: data/raw/locomo.jsonl** records. For each record, extract subject-verb-object triples from the `context` field using `en_core_web_sm` and spaCy dependency parser. **CRITICAL PERSISTENCE**: Immediately write the extracted triples to `data/intermediate/triples_raw.jsonl` (one JSON object per line) to ensure data is available for downstream tasks. **Output**: `data/intermediate/triples_raw.jsonl`. **Error Handling**: If the `context` field is empty or contains no extractable triples, log "EMPTY_CONTEXT" and skip graph construction for that task (do not crash). **Dependency**: T011a, T011a-3 (Phase 1 completion).
- [X] T011a-1b [US1] **Serialize Graph**: Convert extracted triples (from `data/intermediate/triples_raw.jsonl`) into JSON serialization: `data/intermediate/graphs_raw.json` where keys are `task_id` and values are lists of edges (dict: `{"source": "node_id", "target": "node_id", "relation_string": "flattened_relation_text"}`). **Verification**: Run `pytest tests/unit/test_graph_utils.py` to validate schema compliance against `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/contracts/dataset.schema.yaml`. **Error Handling**: If schema validation fails, raise an exception and halt execution (do not proceed). **Dependency**: T011a-1a (Must complete and write file before this task executes).
- [X] T011a-2 [US1] **Schema Validation**: Create a unit test `tests/unit/test_graph_utils.py::test_graph_schema_compliance` that verifies the output of T011a-1b matches the `dataset.schema.yaml` contract exactly before noise injection proceeds. **Dependency**: T011a-1b.
- [X] T011b [US1] **Implement Noise Injection Logic**: Implement the core function `inject_noise(graph, ratio, seed)` in `code/graph_utils.py` that **adds** a proportion of random edges to the original graph (increasing total edge count) to simulate noise. **Parameters**: `ratio` MUST be loaded from `config.yaml` (default 0.1) to ensure tunability; do NOT hardcode the ratio. **Selection Algorithm**: Randomly select `ratio * total_edges` new edges to add (excluding self-loops and existing edges). **Constraint**: The total edge count increases by the injected amount; edges are ADDED, not replaced, per FR-001 and Spec Edge Cases. **Output**: Function in `code/graph_utils.py`. **Unit Test**: `tests/unit/test_graph_utils.py::test_inject_noise_adds_edges`. **Dependency**: T004 (reuses logic), T011a-2 (validation of input).
- [X] T011c [US1] **Generate Noisy Graph Dataset**: Implement a script in `code/data_loader.py` that calls `inject_noise` (T011b) on the graph structure generated in T011a-1b to generate the synthetic noisy graph dataset by **adding** random edges (per Spec Edge Cases and FR-001). **Output**: `data/processed/graphs/graph_noise_42.json`. **Verification**: Run `pytest tests/unit/test_graph_utils.py::test_inject_noise_adds_edges` AND confirm `data/processed/graphs/graph_noise_42.json` exists, has non-zero size, and the total edge count is strictly greater than the clean graph. **Dependency**: T011a-1b, T011b.
- [X] T012 [US1] **Implement Full Active Reconstruction Strategy**: Implement the "Full" traversal algorithm in `code/strategies/full.py` that traverses the entire relevant subgraph for each query, logging `nodes_visited` and `execution_time`. **Robustness Requirement**: Must detect disconnected components before traversal; if the target node is unreachable, flag the task as "unresolved" or default to full traversal of the connected component without crashing. **Note**: Implementation can proceed independently, but runner tasks (T013) depend on T011a-1b completion. **Dependency**: T004, T007, T037.
- [X] T013 [US1] **Baseline Execution Runner**: Implement baseline execution runner using `code/runner.py` that logs `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, and `status` to `data/processed/baseline_results.csv`. **Implementation Requirement**: Explicitly map degenerate/unresolved states detected by T006/T037 to the CSV status column. **Valid Status Values**: "COMPLETED", "TIMEOUT", "DEGENERATE", "UNRESOLVED". **Dependency**: T011a, **T011a-1b**, T012, T006 (functional handler).
- [X] T013b [US1] **Noisy Baseline Execution Runner**: Implement noisy baseline execution runner using `code/runner.py` on the synthetic noisy graphs, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, and `status` to `data/processed/noisy_baseline_results.csv`. **Implementation Requirement**: Explicitly map degenerate/unresolved states detected by T006/T037 to the CSV status column. **Valid Status Values**: "COMPLETED", "TIMEOUT", "DEGENERATE", "UNRESOLVED". **Dependency**: T011a, **T011a-1b**, T011c, T012, T006 (functional handler).
- [ ] T039 [US1] [FR-001] [Constitution-I] **Add Deterministic Seed Verification**: Add a script `code/utils/verify_seeds.py` that **re-runs the noise injection process (T011b) on the clean graph data (from T011a-1b) AND the LLM inference/traversal logic** and compares the resulting **SHA-256** hash against the stored artifact hash in `state/projects/PROJ-894-llmxive-follow-up-extending-memory-is-re.yaml` under the key `artifact_hashes['graph_noise_42']` (which corresponds to the output of T011c) AND `artifact_hashes['baseline_results']` to ensure **reproducibility** of the synthetic noisy graph dataset AND the baseline results. **CRITICAL**: This task verifies that T011c's output is deterministic AND that the Full, Lazy, and Greedy results are reproducible. It MUST include the step to generate the initial hash and write it to the state file if it does not exist. **Input Data Scope**: The hash must be computed on the `data/processed/graphs/graph_noise_42.json` file AND the `data/processed/baseline_results.csv` file. **Explicit Requirement**: The re-run MUST restore the exact LLM model configuration (as defined in `code/config.yaml`, e.g., 'llama-3-8b-instruct-q4_0.gguf') and restore the random seed state using `numpy.random.seed()` and `torch.manual_seed()` with the value defined in `code/utils.py` to ensure deterministic verification. Applies to US1, US2, and US3. **Dependency**: T011a-1b, T011c, T013. **Note**: Runs after T011c/T013; hash generation is a side-effect of verification.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heuristic Strategy Comparison (Priority: P2)

**Goal**: Execute "Lazy" and "Greedy" traversal strategies and compare against baseline.

- [X] T017 [US2] **Implement Lazy Traversal**: Implement the "Lazy" traversal heuristic in `code/strategies/lazy.py` that defers edge expansion until an evidence threshold is triggered. **Logging Requirement**: Log the reduced node count and the **actual evidence threshold value used** (e.g., confidence score > 0.7) in the execution log to `data/processed/lazy_config.log`. **CRITICAL**: If the implementation dynamically adjusts or defaults the threshold during execution (e.g., due to edge cases or fallback logic), the code MUST capture and log the *actual* value used for that specific task execution, not just the configured default. **Dependency**: T012, T004.
- [X] T018 [US2] **Implement Greedy Traversal**: Implement the "Greedy" traversal heuristic in `code/strategies/greedy.py` that selects only the top-k confidence edges. **Logging Requirement**: Log the reduced node count, accuracy, and the **specific configured threshold value used** (e.g., top-k value or confidence score cutoff) in the execution log. **Dependency**: T012, T004.
- [X] T019a [US2] **Lazy Execution Runner**: Implement execution runner for Lazy strategy using `code/runner.py`, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, `evidence_threshold` (configured threshold value, float, 2 decimals), and `status` to `data/processed/lazy_results.csv`. **Dependency**: T011a, T011a-1b, T012, T017, T006.
- [X] T019b [US2] **Greedy Execution Runner**: Implement execution runner for Greedy strategy using `code/runner.py`, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, `evidence_threshold` (configured threshold value, float, 2 decimals), and `status` to `data/processed/greedy_results.csv`. **Dependency**: T011a, T011a-1b, T012, T018, T006.
- [X] T019c [US2] **Noisy Lazy Execution Runner**: Implement execution runner for Lazy strategy on noisy graphs, loading `data/processed/graphs/graph_noise_42.json`, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, `evidence_threshold` (configured threshold value, float, 2 decimals), and `status` to `data/processed/noisy_lazy_results.csv`. **Dependency**: T011a, **T011a-1b**, T011c, T017, T006. **Note**: This task cannot run in parallel with T011c; it strictly depends on T011c completion.
- [X] T019d [US2] **Noisy Greedy Execution Runner**: Implement execution runner for Greedy strategy on noisy graphs, loading `data/processed/graphs/graph_noise_42.json`, logging `task_id`, `accuracy`, `nodes_visited`, `latency_ms`, `evidence_threshold` (configured threshold value, float, 2 decimals), and `status` to `data/processed/noisy_greedy_results.csv`. **Dependency**: T011a, **T011a-1b**, T011c, T018, T006. **Note**: This task cannot run in parallel with T011c; it strictly depends on T011c completion.

---

## Phase 5: User Story 3 - Statistical Significance and Threshold Analysis (Priority: P3)

**Goal**: Perform statistical hypothesis testing and threshold analysis.

- [X] T024a [US3] **Statistical Analysis (Clean)**: Perform paired t-test/Wilcoxon on accuracy distributions of heuristics vs baseline (clean data). **Output**: `data/processed/statistical_results.json` containing p-value and test statistic. **Dependency**: T013, T019a, T019b.
- [X] T024b [US3] **Statistical Analysis (Noisy)**: Perform paired t-test/Wilcoxon on accuracy distributions of heuristics vs baseline (noisy data). **Dependency**: T013b, T019c, T019d.
- [X] T025 [US3] **Point-Biserial Correlation**: Calculate Point-Biserial correlation coefficient between `nodes_visited` and reasoning success rate across all tasks. **Output**: `data/processed/correlation_results.json`. **Dependency**: T013, T019a, T019b.
- [ ] T027 [US3] **Threshold & Inflection Analysis**: Implement **adaptive/quantile-based binning** algorithm (n >= 3 per bin) to identify the first bin with mean accuracy < 95% of the baseline. **CRITICAL STEP**: Before reporting an `inflection_point`, the code MUST perform a statistical significance test (t-test or Wilcoxon) on the binned trend data to confirm the trend is significant (p < 0.05). **Test Selection**: Implement logic to choose between t-test and Wilcoxon based on data distribution (normality check) or zero-difference handling to ensure executability. **Binning Strategy**: Use **adaptive/quantile-based bins** for `nodes_visited` to guarantee each bin contains at least 3 tasks (n >= 3). **Order of Operations**: Apply the quantile-based binning FIRST to ensure n>=3. If the last bin has fewer than 3 tasks, **merge it with the previous bin**. **Output**: `data/processed/threshold_analysis.json` containing the following keys: `inflection_point` (node count), `correlation_coefficient`, `trend_summary`, `is_significant` (boolean), `p_value`. **Constraint**: Calculate p-value using `scipy.stats` (t-test or Wilcoxon) with alpha=0.05. **CRITICAL**: Only report `inflection_point` if `is_significant` is true (p < 0.05). If `is_significant` is false, set `inflection_point` to null and report the overall trend. **Error Handling**: If the dataset is too small to form valid bins (n < 3), report "INSUFFICIENT_DATA" and skip binning. **Dependency**: T024a, T024b, T025.
- [X] T028 [US3] **Calculate Node Reduction Percentage**: Calculate the percentage reduction in nodes visited for Lazy and Greedy strategies relative to the Baseline. **Output**: `data/processed/reduction_analysis.json` with keys: `lazy_reduction_pct`, `greedy_reduction_pct`. **Dependency**: T013, T019a, T019b.
- [X] T029 [US3] **Calculate Accuracy Delta**: Calculate the accuracy delta (heuristic - baseline) for Lazy and Greedy strategies. **Output**: `data/processed/accuracy_delta.json` with keys: `lazy_delta`, `greedy_delta`. **Dependency**: T013, T019a, T019b.

---

## Phase 6: Validation & Audit (Priority: P1)

**Goal**: Ensure data integrity, reproducibility, and compliance.

- [X] T040 [FR-001] [Constitution-III] **Audit Data Loader**: Implement a comprehensive test that mocks `datasets.load_dataset` to fail and asserts the script exits with a non-zero code (enforcing "no synthetic fallback" for real data in production), AND verifies that the script uses the correct real data source when available. **Command**: Run `pytest tests/unit/test_data_loader.py::test_no_fallback_on_failure_and_real_source`. **Clarification**: This test enforces code integrity (Constitution Principle III) by ensuring the script fails fast on data fetch errors in production and uses real data when available, not a synthetic fallback. The spec's assumption of availability is for the research phase, not the implementation phase. **Dependency**: T035.
- [X] T041 [FR-001] [Constitution-III] **Validate Streaming**: Implement a test that verifies streaming mode works correctly for large datasets. **Command**: Run `pytest tests/unit/test_data_loader.py::test_streaming_mode`. **Dependency**: T036.
- [X] T042 [US1] [FR-001] **Verify Noise Injection Reproducibility**: Execute `code/utils/verify_seeds.py` (T039) **after T039 completes its re-run and hash generation** and confirm that the generated `data/processed/graphs/graph_noise_42.json` produces the exact same SHA-256 hash on two separate runs with the same seed. **Dependency**: T011c, T039.
- [X] T043 [FR-001] [Constitution-III] **Confirm Real Data Source**: Verify that the LoCoMo dataset is fetched from the correct HuggingFace source and no synthetic fallback is used. **Command**: Run `pytest tests/unit/test_data_loader.py::test_real_data_source`. **Dependency**: T011a.

---

## Phase 7: Robustness & Edge Case Validation (Priority: P1)

**Goal**: Explicitly validate edge cases defined in spec (disconnected graphs, timeouts, degenerate inputs) to ensure pipeline stability.

- [X] T044 [US4] **Implement Disconnected Graph Handler**: Implement logic in `code/strategies/lazy.py` and `code/strategies/greedy.py` to detect when the target node is unreachable in the current component. **Action**: If unreachable, default to a full traversal of the connected component or flag as "unresolved" in the results CSV without crashing. **Dependency**: T037, T017, T018.
- [X] T045 [US4] **Implement Timeout Handler Unit Test**: Create `tests/integration/test_timeout_handler.py` that injects a **real blocking operation** (e.g., `time.sleep()`) to trigger the actual signal-based termination logic in `runner.py` and asserts the runner logs "TIMEOUT", records the status, and proceeds to the next task. **Dependency**: T006.
- [X] T046 [US4] **Implement Degenerate Graph Handler**: Create a unit test `tests/unit/test_graph_utils.py::test_degenerate_graph_handling` that passes a single-node and zero-edge graph to the traversal strategies and asserts no division-by-zero errors occur, returning a specific "degenerate" flag. **Dependency**: T037.
- [X] T047-1 [US4] **Generate Mixed Robustness Dataset**: Create a script in `code/utils/generate_mixed_dataset.py` to generate a mixed dataset containing clean tasks, disconnected graphs, and degenerate inputs for robustness testing. **Output**: `data/processed/mixed_robustness_dataset.json`. **Dependency**: T011a.
- [X] T047 [US4] **End-to-End Robustness Test**: Implement an integration test `tests/integration/test_robustness_e2e.py` that runs the full pipeline on the mixed dataset generated by T047-1, verifying that the final CSV contains a complete record for every input task (either a result or a failure flag) and the process exits with code 0. **Dependency**: T012, T017, T018, T044, T045, T046, T047-1.

---

## Phase 8: Documentation & Reporting (Priority: P3)

**Goal**: Synthesize results into a coherent report and update documentation.

- [ ] T064 [US3, US4] **Implement Comprehensive Timeout & Degenerate Reporting**: Implement a script `code/report/categorize_status_counts.py` that reads all raw result CSVs (T013, T013b, T019a, T019b, T019c, T019d) and categorizes the counts of tasks that resulted in "TIMEOUT", "DEGENERATE", and "UNRESOLVED" statuses. **Output**: `data/processed/status_counts.json` with keys broken down by strategy (Baseline, Lazy, Greedy) and by dataset (Clean, Noisy). **CRITICAL**: This output MUST contain the specific SC-005 evidence (count of timed-out tasks) required by the spec. **Dependency**: T013, T013b, T019a, T019b, T019c, T019d. **Note**: This task must run BEFORE T060a to provide the categorized counts. T064 depends ONLY on the raw CSVs, not on T060a.
- [ ] T060a [US3] **Aggregate Results Data**: Implement a script `code/report/aggregate_results.py` that reads all JSON/CSV results (T024a, T024b, T025, T027, T028, T029) AND the `status_counts.json` from T064 (which contains the SC-005 evidence) to produce a single intermediate JSON file `data/processed/report_data.json` containing all metrics, including the count of tasks that timed out (SC-005). **Output**: `data/processed/report_data.json`. **Dependency**: T024a, T024b, T025, T027, T028, T029, T064.
- [ ] T060b [US3] **Extract Limitations**: Implement a script `code/report/extract_limitations.py` that reads the `plan.md` Assumptions section to extract study limitations (e.g., CPU constraints, fixed sample size). **Constraint**: If empirical values (e.g., sample size) are deferred in `plan.md`, the script MUST extract the text stating the limitation and format it explicitly as 'Sample size: [deferred] - to be determined at runtime' (or similar specific placeholder) rather than attempting to calculate a value or leaving it blank. **Output**: `data/processed/limitation_text.md`. **Dependency**: T060a.
- [ ] T060c [US3] **Generate Final Report**: Implement a script `code/report/generate_report.py` that combines `data/processed/report_data.json` and `data/processed/limitation_text.md` into a single Markdown report `docs/research_report.md`. **Content**: Must include sections for Baseline Performance, Heuristic Comparison, Statistical Significance, Threshold Analysis (with inflection point logic), and Robustness Findings. **Constraint**: Must explicitly state the limitations of the study as extracted in T060b. **Dependency**: T060a, T060b.
- [ ] T061 [P] **Update README**: Update `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/README.md` with instructions on how to run the full pipeline, including the new streaming and robustness features. **Dependency**: T036b, T047.
- [ ] T062a [US3] **Implement Sensitivity Analysis Loop**: Implement a script `code/analysis/sensitivity_analysis.py` that sets up the loop to re-run the statistical comparison (T024a) across a range of evidence thresholds (e.g., 0.5, 0.6, 0.7, 0.8) for the Lazy strategy. **Dependency**: T017, T024a.
- [ ] T062b [US3] **Execute Sensitivity Analysis**: Run the sensitivity analysis loop from T062a and save the results. **Output**: `data/processed/sensitivity_analysis.json` containing accuracy and node counts per threshold. **Dependency**: T062a.
- [ ] T063a [US3] **Implement Power Analysis Logic**: Implement a script `code/analysis/power_analysis.py` to calculate the post-hoc statistical power of the observed effects (t-tests) given the actual sample size of the LoCoMo subset used. **Dependency**: T024a, T024b.
- [ ] T063b [US3] **Execute Power Analysis**: Run the power analysis from T063a and save the results. **Output**: `data/processed/power_analysis.json` containing power values for each comparison. **Dependency**: T063a.

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
- **Data Pipeline & Streaming Integration (Phase 8)**: Merged into Foundational (Phase 2) to ensure streaming is available before execution.
- **Documentation & Reporting (Phase 8)**: Depends on completion of all statistical analysis tasks (Phase 5) and status categorization (T064).

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

- All Setup tasks marked [P] can run in parallel (except T011a-3 which is moved to Phase 1 and marked [P] but requires serial execution in clean env)
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
6. **CRITICAL**: Ensure noise injection logic in T011b uses **edge addition** (per FR-001 and Spec Edge Cases).
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3 / Robustness
 - Developer D: Data Pipeline (Phase 2)
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
- **CRITICAL NOTE**: T005 (LLM Inference Wrapper) and T052 (Memory Monitoring) removed as they were identified as scope creep not mandated by the spec. T020 (Dense Sweep) removed as it was identified as gold-plating not mandated by the spec.
- **Dependency Clarification**: T013, T013b, T019c, T019d now explicitly list T011a-1b as a dependency to ensure the clean graph artifact exists before noisy generation. T027 no longer depends on T020. T047 now explicitly depends on strategy implementations (T012, T017, T018).
- **New Task Note**: T060a, T060b, T060c, T062a, T062b, T063a, and T063b added to Phase 8 to ensure final results are synthesized into a report, documentation is updated, and sensitivity/power analyses are performed, addressing the need for a complete and robust deliverable. T064 added to Phase 8 to break circular dependency and ensure SC-005 evidence is generated.
- **Removed Duplicate Tasks**: T050 and T051 have been removed as they were duplicates of T036 and T036b.
- **Moved Task**: T039 has been moved from Phase 2 to Phase 3 to resolve circular dependencies with T011c. T011a-3 moved to Phase 1.
- **Updated Noise Injection**: T011b and T011c now correctly specify "adding" random edges to match FR-001 and Spec Edge Cases.
- **Revision Note**: T064 added to Phase 8 to explicitly address the requirement for detailed reporting on timeout and degenerate graph handling, ensuring SC-005 is fully met with granular breakdowns by strategy and dataset type. T060b updated to handle deferred values with specific formatting.
- **Dependency Resolution**: T064 dependency on T060a removed to resolve circular dependency. T064 now depends only on raw CSVs; T060a depends on T064.