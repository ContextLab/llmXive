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

- [ ] T001a [P] Create project directory structure per implementation plan (`projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/`) including `code/`, `data/`, `tests/`, `data/raw`, `data/processed`, `data/processed/graphs`, `data/processed/results`. **Specifics**: Ensure `data/intermediate` directory is created.
- [ ] T001b [P] Initialize Python project with dependencies in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/requirements.txt`. **Specifics**: Include `pandas==2.0.3`, `numpy==1.24.3`, `scipy==1.11.1`, `networkx==3.1`, `pytest==7.4.0`, `spacy==3.7.0`, `statsmodels==0.14.0`, `datasets==2.14.0`, `huggingface_hub==0.17.0`, `llama-cpp-python==0.2.0`, `psutil==5.9.5`.
- [X] T001c [P] Configure linting and formatting tools. **Specifics**: Create `ruff.toml` with `select = ["E", "F", "I"]` and `pyproject.toml` with `[tool.black]` section in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/`.
- [X] T011a-3 [P] **Download and Install spaCy Model**: Create a script `code/scripts/setup_spacy.py` that runs `spacy.cli.download("en_core_web_sm", version="3.7.0")`. **Constraint**: This task MUST run AFTER T001b (package installation). **Dependency**: T001b. **Note**: Moved from Phase 3 to Phase 1 to ensure environment readiness.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Create base data structures for Task, Memory Graph, and Execution Log in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/__init__.py`. **Specifics**: Define `dataclasses` for `Task` (fields: `task_id: str`, `question: str`, `context: str`, `answer: str`), `MemoryGraph` (fields: `nodes: list`, `edges: list`), and `ExecutionLog` (fields: `task_id: str`, `strategy: str`, `accuracy: float`, `nodes_visited: int`, `latency_ms: float`, `evidence_threshold: float`).
- [X] T035 [P] **Enforce Strict Data Fetching**: Modify `code/data_loader.py` to **remove any `try/except` blocks that fall back to synthetic data generation**. Implement function `load_locomo_strict()` that raises `FileNotFoundError` with a descriptive message if `datasets.load_dataset` fails. **Dependency**: T001b, T007.
- [ ] T036-NEW [P] **Implement In-Memory Data Loader**: Refactor `code/data_loader.py` to implement `load_locomo()` using `datasets.load_dataset(..., split=..., trust_remote_code=True)`. **Constraint**: Add a check using `psutil.virtual_memory().percent`; if > 80%, raise a `MemoryWarning` and trigger the streaming fallback (T076). **Dependency**: T035, T007.
- [X] T076 [P] **Implement Streaming Loader Fallback**: Refactor `code/data_loader.py` to include `load_locomo_streaming()` which uses `datasets.load_dataset(..., streaming=True)`. **Constraint**: If the in-memory load (T036-NEW) triggers a memory warning, this function must be the fallback. It must NOT generate synthetic data; if streaming fails, raise an exception. **Dependency**: T035, T036-NEW.
- [X] T004 [P] Implement robust graph construction and noise injection utilities in `code/graph_utils.py`. **Specifics**: Implement `inject_noise(graph, density, seed)` function.
- [ ] T011a [P] **Download LoCoMo Benchmark**: Implement `code/scripts/download_locomo.py` which calls `load_locomo_strict()` to download the LoCoMo benchmark subset from HuggingFace dataset `locomo/locomo` (split: `test`, config: `default`, trust_remote_code=True). **Output**: `data/raw/locomo.jsonl`. **Columns**: `question`, `context`, `answer`. **Constraint**: Verify presence of expected columns; if missing, raise `ValueError("Dataset schema mismatch")`. **Dependency**: T035, T007.
- [ ] T011a-1a [P] **Extract Triples**: Implement NER/Rule-Based extraction logic in `code/data_loader.py` that parses `data/raw/locomo.jsonl` and extracts subject-verb-object triples using spaCy. **Output**: `data/intermediate/triples_raw.jsonl`. **Dependency**: T011a, T011a-3.
- [ ] T011a-1b-serialize [P] **Serialize Graph**: Convert extracted triples into JSON serialization: `data/intermediate/graphs_raw.json` with keys as `task_id` and values as lists of edges. **Dependency**: T011a-1a.
- [ ] T011a-1b-SCHEMA [P] **Validate Graph Schema**: Create a unit test in `tests/unit/test_graph_schema.py::test_schema_matches_contract` that verifies the output graph schema matches the defined contract. **Dependency**: T011a-1b-serialize.
- [X] T083 [P] **Implement Edge Addition Logic**: Modify `code/graph_utils.py::inject_noise` to **add** random edges to the existing set at a fixed density (e.g., [deferred] of original edge count), ensuring the total edge count **increases**. **Constraint**: The function must accept `seed` for determinism and `density` as parameters. **Note**: The Spec (FR-001) mentions 'replacing' but the 'Edge Cases' and 'Assumptions' sections explicitly mandate 'adding' edges. This task implements the 'adding' logic as the robustness test. **Dependency**: T004.
- [X] T006 [P] **Implement Signal-Based Termination**: Implement the OS signal handler (e.g., `signal.SIGALRM` or `signal.SIGTERM`) in `code/runner.py` that enforces a configurable hard timeout per task. **Constraint**: Ensure the handler is registered within a context manager. **Dependency**: T001b.
- [ ] T070 [P] **Fix Data Flow Dependency**: Modify `code/runner.py` to verify the existence of `data/intermediate/graphs_raw.json` before initiating execution. **Dependency**: T011a-1b-serialize, T007. <!-- FAILED: unspecified -->
- [X] T037 [P] **Enhance Degenerate Graph Handling**: Add explicit logic in `code/graph_utils.py` to detect and handle **disconnected components** and **single-node graphs** before traversal. Ensure the `full.py` and `lazy.py` strategies explicitly check for graph connectivity and log a "DEGENERATE" flag. **Dependency**: T004.
- [X] T086 [P] **Implement Streaming Graph Construction**: Refactor `code/data_loader.py` to implement `stream_load_locomo(chunk_size=100)` which yields triples and updates `stats` dict incrementally. **Constraint**: The streaming logic must accumulate statistics online without holding the full dataset in memory. **Dependency**: T076, T036-NEW.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Active Reconstruction Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the "Full" active reconstruction strategy on LoCoMo benchmark tasks to establish a ground-truth baseline on **clean** graphs.

**Independent Test**: The system runs the baseline algorithm on a fixed subset of LoCoMo tasks and outputs a CSV containing `task_id`, `accuracy`, `nodes_visited`, and `inference_time_seconds`.

### Implementation for User Story 1

- [X] T012 [P] **Implement Full Active Reconstruction Strategy**: Implement the "Full" traversal algorithm in `code/strategies/full.py`. <!-- FAILED: unspecified -->
- [X] T012a [P] **Integrate Quantized LLM Engine**: Implement the inference wrapper using `llama-cpp-python` in `code/utils/llm_engine.py`. **Specifics**: Define `model_path` variable pointing to a local `.gguf` file, use `q4_0` quantization, and implement function `run_inference(model_path, prompt) -> str`. **Dependency**: T001b.
- [ ] T013 [P] **Baseline Execution Runner**: Create `code/run_baseline.py` to implement function `run_baseline()` which executes the Full strategy on the **clean** LoCoMo subset (using `graphs_raw.json`). **Output**: `data/processed/baseline_results.csv`. **Dependency**: T012, T012a, T070. <!-- FAILED: unspecified -->
- [X] T013b [P] **Noisy Baseline Execution Runner**: Create `code/run_noisy_baseline.py` to execute the Full strategy on the **noisy** graphs (generated in Phase 11). **Output**: `data/processed/noisy_baseline_results.csv`. **Dependency**: T012, T012a, T070, T011c.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heuristic Strategy Comparison (Priority: P2)

**Goal**: Execute "Lazy" and "Greedy" traversal strategies and compare against baseline.

- [X] T017 [P] **Implement Lazy Traversal**: Implement the "Lazy" traversal heuristic in `code/strategies/lazy.py`.
- [X] T018 [P] **Implement Greedy Traversal**: Implement the "Greedy" traversal heuristic in `code/strategies/greedy.py`.
- [ ] T019a [P] **Lazy Execution Runner**: Implement execution runner for Lazy strategy using `code/run_lazy.py`, logging results to `data/processed/lazy_results.csv`. **Dependency**: T017, T012a, T070.
- [ ] T019b [P] **Greedy Execution Runner**: Implement execution runner for Greedy strategy using `code/run_greedy.py`, logging results to `data/processed/greedy_results.csv`. **Dependency**: T018, T012a, T070.
- [ ] T011c [P] **Generate Noisy Graph Dataset**: Create `code/scripts/generate_noisy_graphs.py` to implement function `generate_noisy_graphs()` which reads clean graphs, applies `inject_noise` (T083), and outputs `data/processed/graphs/graph_noise_42.json`. **Dependency**: T083, T011a-1b-serialize. <!-- FAILED: unspecified -->

---

## Phase 5: User Story 3 - Statistical Significance and Threshold Analysis (Priority: P3)

**Goal**: Perform statistical hypothesis testing and threshold analysis.

- [ ] T024a [P] **Statistical Analysis (Clean)**: Implement `code/stats.py::run_ttest_clean()` which performs paired t-test/Wilcoxon on accuracy distributions of heuristics vs baseline (clean data) and outputs `data/processed/stats_clean.json`. **Dependency**: T013, T019a, T019b. <!-- FAILED: unspecified -->
- [~] T024b [P] **Statistical Analysis (Noisy)**: Implement `code/stats.py::run_ttest_noisy()` which performs paired t-test/Wilcoxon on accuracy distributions of heuristics vs baseline (noisy data) and outputs `data/processed/stats_noisy.json`. **Dependency**: T013b, T019a, T019b.
- [X] T025 [P] **Point-Biserial Correlation**: Implement `code/stats.py::calc_point_biserial()` to calculate the Point-Biserial correlation coefficient between `nodes_visited` and reasoning success rate across all tasks. **Dependency**: T013, T019a, T019b.
- [ ] T094 [P] **Implement Robust Binning Algorithm**: Implement `code/stats.py::bin_tasks_by_nodes(tasks_df, min_bin_size=3)` which sorts tasks by `nodes_visited`, creates bins ensuring `n >= 3` tasks per bin, and returns the list of bins. **Dependency**: T024a, T024b.
- [ ] T027 [P] **Threshold & Inflection Analysis**: Implement `code/stats.py::find_inflection_point()` which calls `bin_tasks_by_nodes` (T094), checks the p-value from T024a/T024b. **Constraint**: If p-value >= 0.05, report "No inflection point detected" and suppress the value. If p < 0.05, identify the first bin with mean accuracy < 95% of baseline. **Dependency**: T024a, T024b, T094.
- [ ] T095 [P] **Implement Power Analysis**: Add a function in `code/stats.py` to perform a post-hoc power analysis on the accuracy distributions. **Dependency**: T024a, T024b.
- [ ] T096 [P] **Validate Statistical Test Selection Logic**: Implement logic in `code/stats.py` to automatically check for normality (Shapiro-Wilk) and select between paired t-test and Wilcoxon signed-rank test accordingly. **Dependency**: T024a.
- [ ] T097 [P] **Generate Statistical Report**: Create `code/scripts/generate_stats_report.py` to aggregate all statistical outputs into a single JSON report. **Dependency**: T094, T095, T096, T027.

---

## Phase 6: Validation & Audit (Priority: P1)

**Goal**: Ensure data integrity, reproducibility, and compliance.

- [ ] T013a [P] **Verify Baseline CSV Schema**: Create a unit test in `tests/unit/test_baseline_schema.py::test_baseline_columns` that verifies the output CSV from T013 contains exactly the columns: `task_id`, `accuracy`, `nodes_visited`, `inference_time_seconds`. **Dependency**: T013.
- [ ] T040 [P] **Audit Data Loader**: Create `tests/integration/test_data_loader_audit.py` that verifies `code/data_loader.py` downloads the correct file hash. **Dependency**: T011a.
- [ ] T041 [P] **Validate In-Memory Loading**: Create `tests/unit/test_data_loader_memory.py` that asserts `load_locomo` fits in <7GB RAM. **Dependency**: T036-NEW.
- [ ] T042 [P] **Verify Noise Injection Reproducibility**: Verify reproducibility of noise injection and baseline results using SHA-256 hashes.
- [ ] T043 [P] **Implement Robustness Test**: Create a script to run tests against edge cases (disconnected graphs, zero-edge graphs) and tasks designed to exceed the timeout limit.

---

## Phase 7: Robustness & Edge Case Validation (Priority: P1)

**Goal**: Explicitly validate edge cases defined in spec (disconnected graphs, timeouts, degenerate inputs) to ensure pipeline stability.
- [ ] T044 [P] **Implement Disconnected Graph Handler**: Implement logic in `code/strategies/lazy.py` and `code/strategies/greedy.py` to detect when the target node is unreachable in the current component.
- [ ] T045 [P] **Implement Timeout Handler Unit Test**: Create a unit test that injects a real blocking operation to trigger the signal-based termination logic.
- [ ] T046 [P] **Implement Degenerate Graph Handler**: Create a unit test that passes single/zero-node graphs and verifies no errors occur.
- [ ] T047-1 [P] **Generate Mixed Robustness Dataset**: Create a script to generate a mixed dataset containing clean, disconnected, and degenerate tasks.
- [ ] T047 [P] **End-to-End Robustness Test**: Implement an integration test that runs the full pipeline on the mixed dataset generated by T047-1.

---

## Phase 8: Documentation & Reporting (Priority: P3)

**Goal**: Synthesize results into a coherent report and update documentation.
- [ ] T060a [P] **Aggregate Results Data**: Implement a script to read all results and create an intermediate JSON file `data/processed/report_data.json` with keys: `accuracy_delta`, `node_reduction_pct`, `statistical_significance`, `inflection_point`. **Dependency**: T024a, T024b, T025, T027, T094.
- [ ] T060b [P] **Extract Limitations**: Implement a script to extract study limitations from the plan document.
- [ ] T060c [P] **Generate Final Report**: Implement `code/report/generate_report.py` which reads `data/processed/limitation_text.md` and `data/processed/report_data.json` to produce `docs/research_report.md`.

---

## Phase 9: Final Integration & Verification (Priority: P1)

**Goal**: Ensure all components work together and the pipeline is production-ready for the research phase.
- [ ] T065 [P] **End-to-End Pipeline Verification**: Execute the full pipeline from data download to final report generation on a small subset of the LoCoMo benchmark.
- [ ] T066 [P] **Final Subset Reproducibility Check**: Re-run the pipeline and compare artifacts against stored hashes.

---

## Phase 10: Revision & Gap Resolution (Priority: P1)

**Goal**: Address specific analysis gaps and ensure data flow correctness.
- [ ] T076a [P] **Verify Streaming Fallback (OOM Trigger)**: Create a test script that simulates an OOM condition during T036-NEW execution and verifies the correct fallback behavior.
- [ ] T076b [P] **Verify Streaming Fallback (Execution)**: Verify that streaming mode is activated under memory pressure.
- [ ] T078 [P] **Validate Evidence Threshold Logging**: Modify `code/runner.py` to include a post-run validation function `validate_evidence_threshold(results_df)` that ensures the `evidence_threshold` column is populated for every task, raising `ValueError` if empty. **Dependency**: T019a, T019b.
- [ ] T079 [P] **Verify Binning Logic Edge Cases**: Implement a unit test that verifies correct binning behavior with small datasets.
- [ ] T080a [P] **Implement Bin-Merging Logic for Threshold Analysis**: Implement function `merge_bins()` in `code/stats.py` to implement the specified bin merging algorithm.
- [ ] T080b [P] **Verify Bin-Merging Logic**: Create `tests/unit/test_stats.py::test_bin_merging_logic` to verify the implementation of T080a.
- [ ] T082 [P] **Enforce Strict Data Flow in Runner**: Update `code/runner.py` to enforce a strict execution order.

---

## Phase 11: Noise Injection Correction & Reproducibility (Priority: P1)

**Goal**: Correct the noise injection logic to strictly follow the specification (Edge Addition) and ensure reproducibility.
- [ ] T084 [P] **Validate Noise Injection Determinism**: Create a unit test in `tests/unit/test_graph_utils.py` that verifies running `inject_noise` twice with the same seed produces identical noisy graphs. **Dependency**: T083.
- [ ] T085 [P] **Update Noisy Graph Generation Script**: Update `code/scripts/generate_noisy_graphs.py` to utilize the corrected `inject_noise` (T083) and regenerate `data/processed/graphs/graph_noise_42.json`. **Dependency**: T083, T011c.

---

## Phase 12: Streaming Data Processing & Large Dataset Handling (Priority: P1)

**Goal**: Implement robust streaming logic for the LoCoMo dataset to handle potential memory constraints without fabricating data.
- [ ] T087 [P] **Implement Streaming Execution Runner**: Modify `code/run_baseline.py` and `code/run_lazy.py` to accept a `streaming=True` flag that processes tasks in batches, writing intermediate results to disk to avoid memory overflow. **Dependency**: T086, T013, T019a.
- [ ] T088 [P] **Verify Streaming Data Integrity**: Create an integration test that compares the results of the in-memory loader (T036-NEW) vs. the streaming loader (T086) on a small, fixed subset to ensure statistical equivalence. **Dependency**: T086, T087.

---

## Phase 13: Comprehensive Robustness & Timeout Validation (Priority: P1)

**Goal**: Rigorously test the system's ability to handle timeouts, disconnected graphs, and degenerate inputs without crashing.
- [ ] T089 [P] **Implement Disconnected Graph Fallback Strategy**: Update `code/strategies/lazy.py` and `code/strategies/greedy.py` to explicitly detect disconnected components. If the target is unreachable, the strategy MUST log a "UNREACHABLE" flag and optionally default to a full traversal of the connected component. **Dependency**: T044, T037.
- [ ] T090 [P] **Implement Hard Timeout Integration Test**: Create an integration test that simulates a task taking longer than 30 minutes and verifies that the signal handler (T006) terminates the task and logs "TIMEOUT" without crashing the runner. **Dependency**: T006, T045.
- [ ] T091 [P] **Validate Degenerate Graph Handling**: Create a unit test suite that feeds single-node, zero-edge, and self-loop graphs into all traversal strategies and verifies that no division-by-zero or infinite loop errors occur. **Dependency**: T046, T037.
- [ ] T092 [P] **Generate Synthetic Edge-Case Dataset**: Create a script `code/scripts/generate_edge_case_dataset.py` that generates a small dataset specifically containing disconnected, degenerate, and timeout-prone tasks for regression testing. **Dependency**: T089, T090, T091.
- [ ] T093 [P] **Run End-to-End Edge Case Regression**: Execute the full pipeline on the dataset generated by T092 and verify that all tasks are processed (either successfully or with expected failure flags) and the pipeline completes without crashing. **Dependency**: T092, T089, T090, T091.

---

## Phase 14: Statistical Analysis & Threshold Refinement (Priority: P3)

**Goal**: Refine the statistical analysis to ensure robust threshold detection and proper handling of small sample sizes.
- [ ] T098a [P] **Final Reproducibility Audit**: Run the entire pipeline from scratch (clean environment) and verify that all outputs (graphs, results, stats) match the expected hashes and formats. **Dependency**: T066, T084, T088.
- [ ] T099a [P] **Update Documentation**: Update `README.md` section "Usage" to include `--streaming` flag and `--noise-density` parameter. Update `docs/research_report.md` with the corrected noise injection methodology (edge addition). **Dependency**: T098a, T097.
- [ ] T100a [P] **Final Code Review & Cleanup**: Perform a final code review to remove any debug prints, ensure all type hints are present, and verify that all `try/except` blocks adhere to the "fail loud" principle. **Dependency**: T099a.

---

## Phase 15: Final Verification & Documentation (Priority: P1)

**Goal**: Ensure the entire pipeline is reproducible, documented, and ready for the research phase.
- [ ] T098b [P] **Final Reproducibility Audit (Verification)**: Re-run the pipeline to confirm T098a results. **Dependency**: T098a.
- [ ] T099b [P] **Update Documentation (Verification)**: Verify that `README.md` and `docs/research_report.md` are correctly updated. **Dependency**: T099a.
- [ ] T100b [P] **Final Code Review (Verification)**: Verify that all debug prints are removed and type hints are present. **Dependency**: T100a.