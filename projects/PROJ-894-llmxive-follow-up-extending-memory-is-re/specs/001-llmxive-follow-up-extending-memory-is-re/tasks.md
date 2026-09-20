# Tasks: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-memory-optimization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directory structure per implementation plan (`projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/`) including `code/`, `data/`, `tests/`, `data/raw`, `data/intermediate`, `data/processed`. **Specifics**: Ensure `data/intermediate` directory is created. **Verification**: Run a shell script `scripts/verify_dirs.sh` or Python check to assert all directories exist.
- [X] T001b [P] Initialize Python project with dependencies in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/requirements.txt`. **Specifics**: Include `pandas==2.0.3`, `numpy==1.24.3`, `scipy==1.11.1`, `networkx==3.1`, `pytest==7.4.0`, `spacy==3.7.0`, `statsmodels==0.14.0`, `datasets==2.14.0`, `huggingface_hub==0.17.0`, `llama-cpp-python==0.2.0`, `psutil==5.9.5`. **Verification**: Run `pip install -r requirements.txt --dry-run` or a test script that imports all listed packages.
- [X] T001c [P] Configure linting and formatting tools. **Specifics**: Create `ruff.toml` with `select = ["E", "F", "I"]` and `pyproject.toml` with `[tool.black]` section in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/`. **Verification**: Run `ruff check .` and `black --check .` to verify configuration.
- [X] T011a-3 [P] **Download and Install spaCy Model**: Create a script `code/scripts/setup_spacy.py` that runs `spacy.cli.download("en_core_web_sm", version="latest")`. **Constraint**: This task MUST run AFTER T001b (package installation). **Dependency**: T001b. **Note**: Moved from Phase 3 to Phase 1 to ensure environment readiness.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Create base data structures for Task, Memory Graph, and Execution Log in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/__init__.py`. **Specifics**: Define `dataclasses` for `Task` (fields: `task_id: str`, `question: str`, `context: str`, `answer: str`), `MemoryGraph` (fields: `nodes: list`, `edges: list`), and `ExecutionLog` (fields: `task_id: str`, `strategy: str`, `accuracy: float`, `nodes_visited: int`, `latency_ms: float`, `evidence_threshold: float`, `token_count: int`). **Verification**: Create a unit test in `tests/unit/test_data_structures.py::test_dataclasses_defined` that imports and instantiates the `Task`, `MemoryGraph`, and `ExecutionLog` dataclasses to verify they are correctly defined.
- [X] T035 [P] **Enforce Strict Data Fetching**: Modify `code/data_loader.py` to **remove any `try/except` blocks that fall back to synthetic data generation**. Implement function `load_locomo_strict()` that raises `FileNotFoundError` with a descriptive message if `datasets.load_dataset` fails. **Dependency**: T001b, T007.
- [X] T036-NEW [P] **Implement In-Memory Data Loader**: Refactor `code/data_loader.py` to implement `load_locomo()` using `datasets.load_dataset(..., split=..., trust_remote_code=True)`. **Constraint**: Add a check using `psutil.virtual_memory().percent`; if > 80%, raise a `RuntimeError` and trigger the streaming fallback (T087). **Constraint**: NO SYNTHETIC FALLBACK - if load fails, raise exception. **Dependency**: T035, T007. **Verification**: Create a unit test `tests/unit/test_data_loader.py::test_no_synthetic_fallback` that asserts the function raises an exception on failure and never returns synthetic data.
- [X] T076 [P] **Implement Streaming Loader Fallback**: Refactor `code/data_loader.py` to include `load_locomo_streaming()` which uses `datasets.load_dataset(..., streaming=True)`. **Constraint**: If the in-memory load (T036-NEW) triggers a memory warning, this function must be the fallback. It must NOT generate synthetic data; if streaming fails, raise an exception. **Dependency**: T035, T036-NEW. **Verification**: Create a unit test `tests/unit/test_data_loader.py::test_streaming_no_fallback` that asserts the function raises an exception on failure and never returns synthetic data.
- [X] T004 [P] Implement robust graph construction and noise injection utilities in `code/graph_utils.py`. **Specifics**: Implement `inject_noise(graph, density, seed)` function.
- [ ] T006 [P] **Implement Signal-Based Termination**: Implement the OS signal handler (e.g., `signal.SIGALRM` or `signal.SIGTERM`) in `code/runner.py` that enforces a configurable hard timeout per task. **Constraint**: Ensure the handler is registered within a context manager. **Verification**: The handler must log a "TIMEOUT" event and raise a `TimeoutError` after 30 minutes. **Dependency**: T001b.
- [ ] T070 [P] **Fix Data Flow Dependency**: Modify `code/runner.py` to verify the existence of `data/intermediate/graphs_raw.json` (relative to project root) before initiating execution. **Dependency**: T011a-1b-serialize.
- [X] T037 [P] **Enhance Degenerate Graph Handling**: Add explicit logic in `code/graph_utils.py` to detect and handle **disconnected components** and **single-node graphs** before traversal. Ensure the `full.py` and `lazy.py` strategies explicitly check for graph connectivity and log a "DEGENERATE" flag. **Dependency**: T004.
- [ ] T085 [P] **Update Noisy Graph Generation Script**: Create `code/scripts/generate_noisy_graphs.py` to implement function `generate_noisy_graphs()` which reads clean graphs (`data/intermediate/graphs_raw.json`), applies `inject_noise` (T004) with **edge replacement** (density 0.05), and outputs `data/processed/graphs/graph_noise_42.json`. **Constraint**: Verify that the noisy graph has the same number of edges as the clean graph but different edge weights/targets. **Dependency**: T004, T011a-1b-serialize.
- [ ] T085-verify [P] **Verify Noisy Graph Generation**: Create a unit test in `tests/unit/test_graph_utils.py::test_noise_reproducibility` that verifies `inject_noise` replaces edges and that the output file `data/processed/graphs/graph_noise_42.json` exists and has the correct schema. **Dependency**: T085.
- [ ] T011a [P] **Download LoCoMo Benchmark**: Create file `code/scripts/download_locomo.py` which calls `load_locomo_strict()` to download the LoCoMo benchmark subset from HuggingFace dataset `locomo/locomo` (split: `test`, config: `default`, trust_remote_code=True). **Output**: `data/raw/locomo.jsonl`. **Columns**: `question`, `context`, `answer`. **Constraint**: Verify presence of expected columns; if missing, raise `ValueError("Dataset schema mismatch")`. **Dependency**: T035, T007. **Verification**: Verify file `code/scripts/download_locomo.py` exists and runs successfully.
- [X] T011a-1a [P] **Extract Triples**: Create file `code/data_loader.py` if it doesn't exist. Implement NER/Rule-Based extraction logic in `code/data_loader.py` that parses `data/raw/locomo.jsonl` and extracts subject-verb-object triples using spaCy. **Output**: `data/intermediate/triples_raw.jsonl`. **Dependency**: T011a, T011a-3. **Verification**: Verify file `code/data_loader.py` exists and contains the extraction logic, and run unit test `tests/unit/test_data_loader.py::test_triple_extraction` to confirm `data/intermediate/triples_raw.jsonl` is generated.
- [ ] T011a-1b-serialize [P] **Serialize Graph**: Create file `code/graph_utils.py` if it doesn't exist. Convert extracted triples into JSON serialization: `data/intermediate/graphs_raw.json` with keys as `task_id` and values as lists of edges. **Dependency**: T011a-1a. **Verification**: Verify file `code/graph_utils.py` exists and contains the serialization logic, and run unit test `tests/unit/test_graph_utils.py::test_serialization` to confirm `data/intermediate/graphs_raw.json` is generated.
- [X] T011a-1b-SCHEMA [P] **Validate Graph Schema**: Create a unit test in `tests/unit/test_graph_schema.py::test_schema_matches_contract` that verifies the output graph schema matches the defined contract. **Dependency**: T011a-1b-serialize.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Active Reconstruction Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the "Full" active reconstruction strategy on LoCoMo benchmark tasks to establish a ground-truth baseline on **clean** graphs.

**Independent Test**: The system runs the baseline algorithm on a fixed subset of LoCoMo tasks and outputs a CSV containing `task_id`, `accuracy`, `nodes_visited`, `inference_time_seconds`, and `token_count`.

### Implementation for User Story 1

- [X] T012 [P] **Implement Full Active Reconstruction Strategy**: Create file `code/strategies/full.py`. Implement the "Full" traversal algorithm in `code/strategies/full.py`. **Verification**: The algorithm must traverse the entire relevant subgraph for each query. Verify file `code/strategies/full.py` exists and run unit test `tests/unit/test_strategies.py::test_full_traversal` to verify the algorithm traverses a known graph structure correctly. **Dependency**: T007.
- [X] T012-verify [P] **Verify Full Strategy**: Create a unit test in `tests/unit/test_strategies.py::test_full_traversal` that verifies the algorithm traverses a known graph structure correctly. **Dependency**: T012.
- [X] T012a [P] **Integrate Quantized LLM Engine**: Implement the inference wrapper using `llama-cpp-python` in `code/utils/llm_engine.py`. **Specifics**: Define `model_path` variable pointing to a local `.gguf` file, use `q4_0` quantization, and implement function `run_inference(model_path, prompt) -> str` which returns both the text response and the `token_count` from the model metadata. **Dependency**: T001b.
- [ ] T013 [P] **Baseline Execution Runner**: Create `code/run_baseline.py` to implement function `run_baseline()` which executes the Full strategy on the **clean** LoCoMo subset (using `data/intermediate/graphs_raw.json`). **Output**: `data/processed/baseline_results.csv`. **Constraint**: The script MUST check for the existence of `data/intermediate/graphs_raw.json` before execution and raise `FileNotFoundError` if missing. **Specifics**: The output CSV MUST contain exactly the columns: `task_id`, `accuracy`, `nodes_visited`, `inference_time_seconds`, `token_count`. **Dependency**: T012, T012a, T070, T087, T011a-1b-serialize. **Verification**: Verify it produces `data/processed/baseline_results.csv` with the exact columns `task_id`, `accuracy`, `nodes_visited`, `inference_time_seconds`, `token_count` via a test `tests/unit/test_baseline_schema.py::test_baseline_columns`.
- [X] T013a [P] **Verify Baseline CSV Schema**: Create a unit test in `tests/unit/test_baseline_schema.py::test_baseline_columns` that verifies the output CSV from T013 contains the correct columns. **Dependency**: T013.
- [ ] T013b [P] **Noisy Baseline Execution Runner**: Create `code/run_noisy_baseline.py` to execute the Full strategy on the **noisy** graphs (generated in T085). **Output**: `data/processed/noisy_baseline_results.csv`. **Dependency**: T012, T012a, T070, T085.
- [ ] T013c [P] **Lazy Execution Runner on Noisy Graphs**: Create `code/run_lazy.py` and execute the Lazy strategy on the noisy graphs (generated in T085). **Output**: `data/processed/lazy_noisy_results.csv`. **Dependency**: T017, T012a, T085.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heuristic Strategy Comparison (Priority: P2)

**Goal**: Execute "Lazy" and "Greedy" traversal strategies and compare against baseline.

- [X] T017 [P] **Implement Lazy Traversal**: Implement the "Lazy" traversal heuristic in `code/strategies/lazy.py`. **Constraint**: Must log the specific evidence threshold value used for that run (e.g., confidence score > 0.7) in the `ExecutionLog`. **Dependency**: T007.
- [X] T018 [P] **Implement Greedy Traversal**: Implement the "Greedy" traversal heuristic in `code/strategies/greedy.py`. **Dependency**: T007.
- [X] T106 [P] **Implement Sensitivity Sweep Loop**: Modify `code/run_lazy.py` to accept a `--thresholds` argument (e.g., `0.5,0.6,0.7,0.8`) and iterate through them, running the Lazy strategy for each threshold value on the full task set. **Constraint**: Each run must be logged separately with the specific `evidence_threshold` used. **Output**: A combined CSV `data/processed/lazy_sweep_results.csv` with an additional column `threshold_value`. **Dependency**: T017, T012a.
- [ ] T107 [P] **Analyze Threshold Sensitivity**: Create `code/scripts/analyze_sensitivity.py` to compare accuracy and node counts across the different threshold values from T106. **Goal**: Identify if the optimal threshold (balancing accuracy and efficiency) is stable or highly variable. **Output**: `data/processed/sensitivity_analysis.json`. **Dependency**: T106.
- [X] T108 [P] **Visualize Threshold Trade-offs**: Create `code/scripts/plot_sensitivity.py` to generate a plot showing Accuracy vs. Nodes Visited for each threshold value. **Output**: `docs/plots/threshold_sensitivity.png`. **Dependency**: T107.
- [ ] T019a [P] **Lazy Execution Runner**: Implement execution runner for Lazy strategy using `code/run_lazy.py`, logging results to `data/processed/lazy_results.csv`. **Dependency**: T017, T012a, T070, T087, T011a-1b-serialize, T106. **Verification**: Verify the output CSV from T019a contains the correct columns including `evidence_threshold`: `task_id`, `strategy`, `accuracy`, `nodes_visited`, `latency_ms`, `evidence_threshold`, `token_count` via a test `tests/unit/test_runner_schemas.py::test_lazy_columns`.
- [X] T019a-verify [P] **Verify Lazy Runner Output**: Create a unit test in `tests/unit/test_runner_schemas.py::test_lazy_columns` that verifies the output CSV from T019a contains the correct columns. **Dependency**: T019a.
- [ ] T019b [P] **Greedy Execution Runner**: Implement execution runner for Greedy strategy using `code/run_greedy.py`, logging results to `data/processed/greedy_results.csv`. **Dependency**: T018, T012a, T070, T087, T011a-1b-serialize. **Verification**: Verify the output CSV from T019b contains the correct columns: `task_id`, `strategy`, `accuracy`, `nodes_visited`, `latency_ms`, `token_count` via a test `tests/unit/test_runner_schemas.py::test_greedy_columns`.
- [X] T019b-verify [P] **Verify Greedy Runner Output**: Create a unit test in `tests/unit/test_runner_schemas.py::test_greedy_columns` that verifies the output CSV from T019b contains the correct columns. **Dependency**: T019b.

---

## Phase 5: User Story 3 - Statistical Significance and Threshold Analysis (Priority: P3)

**Goal**: Perform statistical hypothesis testing and threshold analysis.

- [ ] T024a [P] **Statistical Analysis (Clean)**: Implement `code/stats.py::run_ttest_clean()` which performs paired t-test/Wilcoxon on accuracy distributions of heuristics vs baseline (clean data) and outputs `data/processed/stats_clean.json`. **Dependency**: T013, T019a, T019b. **Verification**: Verify `data/processed/stats_clean.json` contains `p-value` and `test_statistic` keys via a test `tests/unit/test_stats.py::test_statistical_outputs`.
- [ ] T024b [P] **Statistical Analysis (Noisy)**: Implement `code/stats.py::run_ttest_noisy()` which performs paired t-test/Wilcoxon on accuracy distributions of heuristics vs baseline (noisy data) and outputs `data/processed/stats_noisy.json`. **Dependency**: T013b, T019a, T019b. **Verification**: Verify `data/processed/stats_noisy.json` contains `p-value` and `test_statistic` keys via a test `tests/unit/test_stats.py::test_statistical_outputs`.
- [X] T025 [P] **Point-Biserial Correlation**: Implement `code/stats.py::calc_point_biserial()` to calculate the Point-Biserial correlation coefficient between `nodes_visited` and reasoning success rate across all tasks. **Dependency**: T013, T019a, T019b.
- [X] T094 [P] **Implement Robust Binning Algorithm**: Implement `code/stats.py::bin_tasks_by_nodes(tasks_df, min_bin_size=3)` which sorts tasks by `nodes_visited`, creates bins ensuring `n >= 3` tasks per bin, and returns the list of bins. **Constraint**: Must enforce `n >= 3` strictly. **Dependency**: T024a, T024b.
- [X] T027 [P] **Threshold & Inflection Analysis**: Implement `code/stats.py::find_inflection_point()` which calls `bin_tasks_by_nodes` (T094), checks the p-value from T024a/T024b. **Constraint**: It MUST perform binning regardless of p-value. If p-value >= 0.05, report "No inflection point detected" (suppress the claim). If p < 0.05, identify the first bin with mean accuracy < 95% of baseline. **Dependency**: T024a, T024b, T094.
- [X] T095 [P] **Implement Power Analysis**: Add a function in `code/stats.py` to perform a post-hoc power analysis on the accuracy distributions. **Dependency**: T024a, T024b.
- [X] T096 [P] **Validate Statistical Test Selection Logic**: Implement logic in `code/stats.py` to automatically check for normality (Shapiro-Wilk) and select between paired t-test and Wilcoxon signed-rank test accordingly. **Dependency**: T024a.
- [ ] T097 [P] **Generate Statistical Report**: Create `code/scripts/generate_stats_report.py` to aggregate all statistical outputs (T024a, T024b, T025, T027, T095) into a single JSON report `data/processed/stats_final.json`. **Dependency**: T094, T095, T096, T027.

---

## Phase 6: Validation & Audit (Priority: P1)

**Goal**: Ensure data integrity, reproducibility, and compliance.

- [X] T040 [P] **Audit Data Loader**: Create `tests/integration/test_data_loader_audit.py` that verifies `code/data_loader.py` downloads the correct file hash. **Specifics**: Compute SHA-256 of `data/raw/locomo.jsonl` dynamically using `hashlib` and assert it matches the hash computed from the dataset manifest or a verified source URL. **Dependency**: T011a.
- [X] T041 [P] **Validate In-Memory Loading**: Create `tests/unit/test_data_loader_memory.py` that asserts `load_locomo` fits in <7GB RAM. **Dependency**: T036-NEW.
- [X] T042 [P] **Verify Noise Injection Reproducibility**: Create a unit test in `tests/unit/test_graph_utils.py::test_noise_reproducibility` that verifies running `inject_noise` twice with the same seed produces identical noisy graphs. **Dependency**: T083.
- [X] T043 [P] **Implement Robustness Test**: Create file `code/scripts/generate_edge_case_dataset.py` to generate a dataset containing disconnected graphs, zero-edge graphs, and tasks designed to exceed the timeout limit. **Verification**: Run the script and verify the output file exists. **Dependency**: T037.

---

## Phase 7: Robustness & Edge Case Validation (Priority: P1)

**Goal**: Explicitly validate edge cases defined in spec (disconnected graphs, timeouts, degenerate inputs) to ensure pipeline stability.
- [X] T044 [P] **Implement Disconnected Graph Handler**: Create files `code/strategies/lazy.py` and `code/strategies/greedy.py` if they don't exist. Implement logic to detect when the target node is unreachable in the current component. **Constraint**: If unreachable, log "UNREACHABLE" and optionally default to full traversal of the connected component. **Dependency**: T037.
- [X] T045 [P] **Implement Timeout Handler Unit Test**: Create file `tests/unit/test_timeout_handler.py` that injects a real blocking operation to trigger the signal-based termination logic. **Constraint**: Must verify the time limit is strictly enforced. **Dependency**: T006.
- [X] T046 [P] **Implement Degenerate Graph Handler**: Create file `tests/unit/test_degenerate_graphs.py` that passes single-node, zero-edge, and self-loop graphs and verifies that no division-by-zero or infinite loop errors occur. **Dependency**: T037.
- [X] T047-1 [P] **Generate Mixed Robustness Dataset**: Create file `code/scripts/generate_mixed_robustness_dataset.py` to generate a mixed dataset containing disconnected, degenerate, and timeout-prone tasks for regression testing.
- [X] T047 [P] **End-to-End Robustness Test**: Create file `tests/integration/test_end_to_end_robustness.py` to run the full pipeline on the mixed dataset generated by T047-1.

---

## Phase 8: Documentation & Reporting (Priority: P3)

**Goal**: Synthesize results into a coherent report and update documentation.
- [ ] T060a [P] **Aggregate Results Data**: Implement a script to read all results and create an intermediate JSON file `data/processed/report_data.json` with keys: `accuracy_delta`, `node_reduction_pct`, `statistical_significance`, `inflection_point`. **Specifics**: Create `code/scripts/aggregate_results.py` and verify via a test `tests/unit/test_report_data.py::test_report_schema`. **Dependency**: T024a, T024b, T025, T027.
- [X] T060b [P] **Extract Limitations**: Create file `code/scripts/extract_limitations.py` to extract study limitations from the plan document.
- [ ] T060c [P] **Generate Final Report**: Create file `code/report/generate_report.py` which reads `data/processed/limitation_text.md` and `data/processed/report_data.json` to produce `docs/research_report.md`.

---

## Phase 9: Final Integration & Verification (Priority: P1)

**Goal**: Ensure all components work together and the pipeline is production-ready for the research phase.
- [X] T065 [P] **End-to-End Pipeline Verification**: Create file `tests/integration/test_e2e_pipeline.py::test_full_pipeline_run` to execute the full pipeline from a small subset of the LoCoMo benchmark. **Specifics**: Execute `code/scripts/run_pipeline.py` on a small subset and verify the existence of all expected artifacts (CSVs, JSONs, report) and their schemas. **Dependency**: T105a.
- [X] T066 [P] **Final Subset Reproducibility Check**: Create file `code/scripts/verify_reproducibility.py` to re-run the pipeline and compare artifacts against stored hashes.

---

## Phase 10: Revision & Gap Resolution (Priority: P1)

**Goal**: Address specific analysis gaps and ensure data flow correctness.
- [X] T076a [P] **Verify Streaming Fallback (OOM Trigger)**: Create file `tests/unit/test_streaming_fallback.py` to simulate an OOM condition during T036-NEW execution and verify the correct fallback behavior.
- [X] T076b [P] **Verify Streaming Fallback (Execution)**: Create file `tests/integration/test_streaming_execution.py` to verify that streaming mode is activated under memory pressure.
- [ ] T078 [P] **Validate Evidence Threshold Logging**: Create file `code/runner.py` if it doesn't exist. Modify `code/runner.py` to include a post-run validation function `validate_evidence_threshold(results_df)` that ensures the `evidence_threshold` column is populated for every task, raising `ValueError` if empty. **Dependency**: T019a, T019b.
- [X] T079 [P] **Verify Binning Logic Edge Cases**: Create file `tests/unit/test_binning_edge_cases.py` to verify correct binning behavior with small datasets.
- [X] T080a [P] **Implement Bin-Merging Logic**: Create file `code/stats.py` if it doesn't exist. Implement function `merge_bins()` in `code/stats.py` to implement the specified bin merging algorithm. **Constraint**: Must enforce `n >= 3`.
- [X] T080b [P] **Verify Bin-Merging Logic**: Create file `tests/unit/test_bin_merging.py` to verify the implementation of T080a.
- [ ] T082 [P] **Enforce Strict Data Flow in Runner**: Create file `code/runner.py` if it doesn't exist. Update `code/runner.py` to enforce a strict execution order.

---

## Phase 11: Noise Injection Correction & Reproducibility (Priority: P1)

**Goal**: Correct the noise injection logic to strictly follow the specification (Edge Replacement) and ensure reproducibility.
- [X] T084 [P] **Validate Noise Injection Determinism**: Create a unit test in `tests/unit/test_graph_utils.py::test_noise_reproducibility` that verifies running `inject_noise` twice with the same seed produces identical noisy graphs. **Dependency**: T083.
- [X] T084-verify [P] **Verify Noise Injection Determinism Test**: Create file `tests/unit/test_noise_determinism.py` to verify the implementation of T084. **Dependency**: T084.
- [X] T085-verify [P] **Verify Noisy Graph Generation Script Update**: Create file `tests/unit/test_noisy_graph_generation.py` to verify the implementation of T085. **Dependency**: T085.

---

## Phase 12: Streaming Data Processing & Large Dataset Handling (Priority: P1)

**Goal**: Implement robust streaming logic for the LoCoMo dataset to handle potential memory constraints without fabricating data.
- [X] T087 [P] **Implement Streaming Execution Runner**: Create files `code/run_baseline.py` and `code/run_lazy.py` if they don't exist. Modify them to accept a `streaming=True` flag that processes tasks in batches, writing intermediate results to disk to avoid memory overflow. **Dependency**: T086, T013, T019a.
- [X] T088 [P] **Verify Streaming Data Integrity**: Create file `tests/integration/test_streaming_integrity.py` to compare the results of the in-memory loader (T036-NEW) vs. the streaming loader (T086) on a small, fixed subset to ensure statistical equivalence. **Dependency**: T086, T087.

---

## Phase 13: Comprehensive Robustness & Timeout Validation (Priority: P1)

**Goal**: Rigorously test the system's ability to handle timeouts, disconnected graphs, and degenerate inputs without crashing.
- [X] T089 [P] **Implement Disconnected Graph Fallback Strategy**: Create files `code/strategies/lazy.py` and `code/strategies/greedy.py` if they don't exist. Update them to explicitly detect disconnected components. If the target is unreachable, the strategy MUST log a "UNREACHABLE" flag and optionally default to a full traversal of the connected component. **Dependency**: T044, T037.
- [X] T090 [P] **Implement Hard Timeout Integration Test**: Create file `tests/integration/test_hard_timeout.py` to simulate a task taking longer than a substantial duration and verify that the signal handler (T006) terminates the task and logs "TIMEOUT" without crashing the runner. **Constraint**: Must verify the 30-minute limit is strictly enforced. **Dependency**: T006, T045.
- [X] T091 [P] **Validate Degenerate Graph Handling**: Create file `tests/unit/test_degenerate_handling.py` to feed single-node, zero-edge, and self-loop graphs into all traversal strategies and verify that no division-by-zero or infinite loop errors occur. **Dependency**: T046, T037.
- [X] T092 [P] **Generate Synthetic Edge-Case Dataset**: Create file `code/scripts/generate_edge_case_dataset.py` that generates a small dataset specifically containing disconnected, degenerate, and timeout-prone tasks for regression testing. **Dependency**: T089, T090, T091.
- [X] T093 [P] **Run End-to-End Edge Case Regression**: Create file `tests/integration/test_edge_case_regression.py` to execute the full pipeline on the dataset generated by T092 and verify that all tasks are processed (either successfully or with expected failure flags) and the pipeline completes without crashing. **Dependency**: T092, T089, T090, T091.

---

## Phase 14: Documentation & Reporting (Priority: P3)

**Goal**: Ensure the entire pipeline is reproducible, documented, and ready for the research phase.
- [X] T098a [P] **Final Reproducibility Audit**: Create file `code/scripts/final_audit.py` to run the entire pipeline from scratch (clean environment) and verify that all outputs (graphs, results, stats) match the expected hashes. **Dependency**: T066, T084, T088.
- [X] T099a [P] **Update Documentation**: Create/Update files `README.md` and `docs/research_report.md` to include `--streaming` flag and `--noise-density` parameter. Update `docs/research_report.md` with the corrected noise injection methodology (edge replacement). **Dependency**: T098a.
- [X] T100a [P] **Final Code Review & Cleanup**: Create file `code/scripts/final_review.py` to remove any debug prints, ensure all type hints are present, and verify that all `try/except` blocks adhere to the "fail loud" principle. **Dependency**: T099a.

---

## Phase 15: Final Verification & Documentation (Priority: P1)

**Goal**: Ensure the entire pipeline is reproducible, documented, and ready for the research phase.
- [X] T098b [P] **Final Reproducibility Audit (Verification)**: Create file `code/scripts/final_audit_verify.py` to re-run the pipeline to confirm T098a results. **Dependency**: T098a.
- [X] T099b [P] **Update Documentation (Verification)**: Create file `code/scripts/verify_docs.py` to verify that `README.md` and `docs/research_report.md` are correctly updated. **Dependency**: T099a.
- [X] T100b [P] **Final Code Review (Verification)**: Create file `code/scripts/verify_code.py` to verify that all debug prints are removed and type hints are present. **Dependency**: T100a.

---

## Phase 16: Data Flow & Dependency Resolution (Priority: P1)

**Goal**: Resolve critical data flow gaps identified in prior analysis where tasks depend on outputs that do not yet exist or are generated in the wrong order.

- [X] T105a [P] **Create Pipeline Script**: Create file `code/scripts/run_pipeline.py`. Implement the main orchestration script that runs the full pipeline. **Verification**: Verify file `code/scripts/run_pipeline.py` exists and runs successfully on a minimal subset. **Dependency**: T011a-1b-serialize, T085.
- [ ] T105b [P] **Implement Dependency Checks**: Modify file `code/scripts/run_pipeline.py` to explicitly assert that `data/intermediate/graphs_raw.json` exists and is non-empty BEFORE calling `run_baseline.py` (T013) or `run_lazy.py` (T019a). If missing, abort with a descriptive error. **Dependency**: T011a-1b-serialize. **Verification**: Verify file `code/scripts/run_pipeline.py` contains the dependency check logic.
- [X] T105c [P] **Add Pipeline Test**: Create file `tests/integration/test_pipeline_order.py::test_pipeline_order` to verify the correct execution order of the pipeline steps. **Dependency**: T105a, T105b. **Verification**: Verify file `tests/integration/test_pipeline_order.py` exists and the test passes.
- [X] T109 [P] **Verify No Synthetic Fallbacks**: Create file `code/scripts/audit_no_fallbacks.py` that scans `code/data_loader.py` and `code/strategies/*.py` for any `try/except` blocks or `if` conditions that might lead to synthetic data generation. **Constraint**: The script must raise an error if any potential fallback logic is found. **Dependency**: T035, T076.
- [X] T110 [P] **Full Clean-Run Reproducibility Test**: Create file `code/scripts/run_full_repro.py` to execute the entire pipeline from a clean `data/` directory in a fresh virtual environment. **Constraint**: Verify that all output files are generated and their SHA-256 hashes match the expected values stored in `state/`. **Dependency**: T105.
- [X] T111 [P] **Document Reproducibility Steps**: Update files `README.md` and `docs/research_report.md` with a step-by-step guide for reproducing the entire study, including exact commands and expected outputs. **Dependency**: T110.
- [ ] T112 [P] **Enforce Graph Serialization Before Execution**: Create file `code/scripts/run_pipeline.py` if it doesn't exist. Modify `code/scripts/run_pipeline.py` to explicitly assert that `data/intermediate/graphs_raw.json` exists and is non-empty BEFORE calling `run_baseline.py` (T013) or `run_lazy.py` (T019a). If missing, abort with a descriptive error. **Dependency**: T011a-1b-serialize.
- [ ] T113 [P] **Enforce Noisy Graph Generation Before Noisy Execution**: Modify file `code/scripts/run_pipeline.py` to ensure `data/processed/graphs/graph_noise_42.json` is generated before `run_noisy_baseline.py` (T013b) is invoked. **Dependency**: T085.
- [X] T114 [P] **Verify Result Aggregation Order**: Modify file `code/scripts/run_pipeline.py` to ensure `code/scripts/run_pipeline.py` runs T013, T019a, and T019b *before* calling statistical analysis. **Dependency**: T013, T019a, T019b, T024a, T024b.
- [ ] T115 [P] **Add Intermediate Artifact Validation**: Create file `code/scripts/run_pipeline.py` if it doesn't exist. Create a helper function `validate_intermediate_artifacts()` in `code/scripts/run_pipeline.py` that checks for the existence and valid schema of `graphs_raw.json`, `triples_raw.jsonl`, and `graph_noise_42.json` before proceeding to the execution phase. **Dependency**: T011a-1a, T011a-1b-serialize, T085.
