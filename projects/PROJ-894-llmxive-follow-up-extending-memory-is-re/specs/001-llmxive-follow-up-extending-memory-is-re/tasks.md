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

- [ ] T001a [P] Create project directory structure per implementation plan (`projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/`) including `code/`, `data/`, `tests/`. **Clarification**: Paths are relative to the project root defined in plan.md.
- [ ] T001b [P] Initialize Python project with dependencies (`pandas`, `numpy`, `scipy`, `networkx`, `pytest`, `spacy`, `statsmodels`, `datasets`, `huggingface_hub`, `llama-cpp-python`, `psutil`) in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/requirements.txt`
- [ ] T001c [P] Configure linting (ruff/flake8) and formatting (black) tools in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/`
- [ ] T011a-3 **Download and Install spaCy Model**: Implement a script in `code/data_loader.py` to download and install the `en_core_web_sm` model using the programmatic `spacy.cli.download("en_core_web_sm", version=".1")` API. **Constraint**: This task MUST run in a serial setup phase (do NOT mark as [P] if parallel execution risks race conditions in the model cache). **Dependency**: T001b. **Note**: Moved from Phase 3 to Phase 1 to ensure environment readiness before extraction logic. The `requirements.txt` (T001b) lists `spacy`, and this task ensures the model artifact is present in the CI environment before any extraction logic runs.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement robust graph construction and noise injection utilities in `code/graph_utils.py`. **Note**: Noise injection logic here is the core function `inject_noise`.
- [ ] T006 [P] **Implement Signal-Based Termination**: Implement the OS signal handler (e.g., `signal.SIGALRM` or `signal.SIGTERM`) in `code/runner.py` that enforces a configurable hard timeout per task. **Constraint**: Ensure the handler is registered within a context manager or specific scope to prevent global state conflicts with parallel tasks. **Dependency**: T001b.
- [ ] T007 Create base data structures for Task, Memory Graph, and Execution Log in `projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/code/__init__.py`
- [ ] T035 Enforce Strict Data Fetching: Modify `code/data_loader.py` to **remove any `try/except` blocks that fall back to synthetic data generation** when the real LoCoMo dataset fetch fails. If `datasets.load_dataset` or the HuggingFace Hub download fails, the script must **raise an explicit exception** and halt execution to prevent silent fabrication in the production research pipeline. **Exception Handling for Development**: In local development environments, if the dataset is unavailable, the script may log a "SKIP" status and proceed, but must never generate synthetic data. **Dependency**: T001b, T007.
- [ ] T036-NEW [P] **Implement In-Memory Data Loader**: Refactor `code/data_loader.py` to load the LoCoMo dataset into memory using `datasets.load_dataset(..., split=..., trust_remote_code=True)` without streaming. **Constraint**: The dataset size is assumed to fit within the RAM limit of the free-tier runner. **Dependency**: T035.
- [ ] T037 [US1, US2, US3, US4] **Enhance Degenerate Graph Handling**: Add explicit logic in `code/graph_utils.py` to detect and handle **disconnected components** and **single-node graphs** before traversal. Ensure the `full.py` and `lazy.py` strategies explicitly check for graph connectivity and log a "DEGENERATE" flag rather than attempting traversal that might cause infinite loops or division-by-zero errors. **(Note: Modified file shared with T004; depends on T004)**
- [ ] T011a-1b-serialize [US1] **Serialize Graph**: Convert extracted triples into JSON serialization: `data/intermediate/graphs_raw.json` with keys as `task_id` and values as lists of edges. **Dependency**: T011a-1a.
- [ ] T070 [US1, US2, US3, US4] **Fix Data Flow Dependency**: Modify `code/runner.py` to verify the existence of `data/intermediate/graphs_raw.json` before initiating execution, ensuring a valid upstream dependency is met. **Dependency**: T011a-1b-serialize, T007.
- [ ] T076 [US1, US2] **Implement Streaming Loader Fallback**: Refactor `code/data_loader.py` to include a fallback mechanism that detects memory pressure (e.g., `psutil.virtual_memory().percent > 80`) and switches to `datasets.load_dataset(..., streaming=True)` for the LoCoMo dataset if the in-memory load (T036-NEW) would exceed available RAM. **Constraint**: The streaming path MUST still adhere to the "no synthetic fallback" rule; if the stream fails, the script must raise an exception. **Dependency**: T035, T036-NEW.
- [ ] T077 [US1, US4] **Implement In-Memory Data Loader**: Refactor `code/data_loader.py` to load the LoCoMo dataset into memory using `datasets.load_dataset(..., split=..., trust_remote_code=True)` without streaming.
**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Active Reconstruction Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the "Full" active reconstruction strategy on LoCoMo benchmark tasks to establish a ground-truth baseline.

**Independent Test**: The system runs the baseline algorithm on a fixed subset of LoCoMo tasks and outputs a CSV containing `task_id`, `accuracy`, `nodes_visited`, and `inference_time_seconds`.

### Implementation for User Story 1

- [ ] T011a [US1] **Download LoCoMo Benchmark**: Implement a script in `code/scripts/download_locomo.py` to download the LoCoMo benchmark subset from HuggingFace dataset `locomo/locomo` (split: `test`, config: `default`, trust_remote_code=True). **Output**: `data/raw/locomo.jsonl`. **Columns**: `question`, `context`, `answer`. **CRITICAL**: Verify the presence of expected columns; if missing, raise `ValueError("Dataset schema mismatch")`. **Config Validation**: Before proceeding, verify the `config` string exists in the dataset metadata; if not, raise a descriptive error indicating the valid configs. **FALLBACK**: If the real download fails, the script MUST **raise an explicit exception** and halt execution (do NOT generate synthetic data). **Dependency**: T035, T036-NEW.
- [ ] T011a-1a [US1] **Extract Triples**: Implement NER/Rule-Based extraction logic in `code/data_loader.py` that parses the `data/raw/locomo.jsonl` records and extracts subject-verb-object triples using spaCy. Include prepositional phrases and named entities to support multi-hop reasoning. **Output**: `data/intermediate/triples_raw.jsonl`.
- [ ] [ ] T011a-1b-SCHEMA [US1] **Validate Graph Schema**: Create a unit test that verifies the output graph schema matches the defined contract. **Dependency**: T011a-1b-serialize.
- [ ] T011b [US1] **Implement Noise Injection Logic (Edge Replacement)**: Implement noise injection by *adding* random edges to maintain constant density using `inject_noise` in `code/graph_utils.py`.
- [ ] T011c [US1] **Generate Noisy Graph Dataset**: Create `code/scripts/generate_noisy_graphs.py` to implement function `generate_noisy_graphs()` which reads clean graphs and outputs `data/processed/graphs/graph_noise_42.json`. **Dependency**: T011b, T011a-1b-serialize.
- [ ] T012 [US1] **Implement Full Active Reconstruction Strategy**: Implement the "Full" traversal algorithm in `code/strategies/full.py`.
- [ ] T012a [US1] **Integrate Quantized LLM Engine**: Implement the inference wrapper using `llama-cpp-python` to load a quantized model (CPU-only mode).
- [ ] T013 [US1] **Baseline Execution Runner**: Create `code/run_baseline.py` to implement function `run_baseline()` which executes the Full strategy on the LoCoMo subset. **Output**: `data/processed/baseline_results.csv`. **Dependency**: T012, T012a, T070.
- [ ] T013b [US1] **Noisy Baseline Execution Runner**: Implement noisy baseline execution runner using `code/run_noisy_baseline.py`, logging data to `data/processed/noisy_baseline_results.csv`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heuristic Strategy Comparison (Priority: P2)

**Goal**: Execute "Lazy" and "Greedy" traversal strategies and compare against baseline.

- [ ] T017 [US2] **Implement Lazy Traversal**: Implement the "Lazy" traversal heuristic in `code/strategies/lazy.py`.
- [ ] T018 [US2] **Implement Greedy Traversal**: Implement the "Greedy" traversal heuristic in `code/strategies/greedy.py`.
- [ ] T019a [US2] **Lazy Execution Runner**: Implement execution runner for Lazy strategy using `code/run_lazy.py`, logging results to `data/processed/lazy_results.csv`.
- [ ] T019b [US2] **Greedy Execution Runner**: Implement execution runner for Greedy strategy using `code/run_greedy.py`, logging results to `data/processed/greedy_results.csv`.

---

## Phase 5: User Story 3 - Statistical Significance and Threshold Analysis (Priority: P3)

**Goal**: Perform statistical hypothesis testing and threshold analysis.

- [ ] T024a [US3] **Statistical Analysis (Clean)**: Perform paired t-test/Wilcoxon on accuracy distributions of heuristics vs baseline (clean data).
- [ ] T024b [US3] **Statistical Analysis (Noisy)**: Perform paired t-test/Wilcoxon on accuracy distributions of heuristics vs baseline (noisy data).
- [ ] T025 [US3] **Point-Biserial Correlation**: Calculate Point-Biserial correlation coefficient between `nodes_visited` and reasoning success rate across all tasks.
- [ ] T027 [US3] **Threshold & Inflection Analysis**: Implement dynamic binning algorithm to identify the first bin with mean accuracy < 95% of the baseline.

---

## Phase 6: Validation & Audit (Priority: P1)

**Goal**: Ensure data integrity, reproducibility, and compliance.

- [ ] T040 [FR-001] **Audit Data Loader**: Implement a check to ensure data download works as expected.
- [ ] T041 [FR-001] **Validate In-Memory Loading**: Implement a test that verifies the in-memory loader works correctly for the expected dataset size.
- [ ] T042 [US1, US2] **Verify Noise Injection Reproducibility**: Verify reproducibility of noise injection and baseline results using SHA-256 hashes.
- [ ] T043 [US4] **Implement Robustness Test**: Create a script to run tests against edge cases (disconnected graphs, zero-edge graphs) and tasks designed to exceed the timeout limit.

---

## Phase 7: Robustness & Edge Case Validation (Priority: P1)

**Goal**: Explicitly validate edge cases defined in spec (disconnected graphs, timeouts, degenerate inputs) to ensure pipeline stability.
- [ ] T044 [US4] **Implement Disconnected Graph Handler**: Implement logic in `code/strategies/lazy.py` and `code/strategies/greedy.py` to detect when the target node is unreachable in the current component.
- [ ] T045 [US4] **Implement Timeout Handler Unit Test**: Create a unit test that injects a real blocking operation to trigger the signal-based termination logic.
- [ ] T046 [US4] **Implement Degenerate Graph Handler**: Create a unit test that passes single/zero-node graphs and verifies no errors occur.
- [ ] T047-1 [US4] **Generate Mixed Robustness Dataset**: Create a script to generate a mixed dataset containing clean, disconnected, and degenerate tasks.
- [ ] T047 [US4] **End-to-End Robustness Test**: Implement an integration test that runs the full pipeline on the mixed dataset generated by T047-1.

---

## Phase 8: Documentation & Reporting (Priority: P3)

**Goal**: Synthesize results into a coherent report and update documentation.
- [ ] T060a [US3] **Aggregate Results Data**: Implement a script to read all results and create an intermediate JSON file `data/processed/report_data.json` with keys: `accuracy_delta`, `node_reduction_pct`, `statistical_significance`, `inflection_point`. **Dependency**: T024a, T024b, T025, T027.
- [ ] T060b [US3] **Extract Limitations**: Implement a script to extract study limitations from the plan document.
- [ ] T060c [US3] **Generate Final Report**: Implement `code/report/generate_report.py` which reads `data/processed/limitation_text.md` and `data/processed/report_data.json` to produce `docs/research_report.md`.

---

## Phase 9: Final Integration & Verification (Priority: P1)

**Goal**: Ensure all components work together and the pipeline is production-ready for the research phase.
- [ ] T065 [US1, US2, US3, US4] **End-to-End Pipeline Verification**: Execute the full pipeline from data download to final report generation on a small subset of the LoCoMo benchmark.
- [ ] T066 [FR-001] **Final Subset Reproducibility Check**: Re-run the pipeline and compare artifacts against stored hashes.

---

## Phase 10: Revision & Gap Resolution (Priority: P1)

**Goal**: Address specific analysis gaps and ensure data flow correctness.
- [ ] T076a [US1, US2] **Verify Streaming Fallback (OOM Trigger)**: Create a test script that simulates an OOM condition during T036-NEW execution and verifies the correct fallback behavior.
- [ ] T076b [US1, US2] **Verify Streaming Fallback (Execution)**: Verify that streaming mode is activated under memory pressure.
- [ ] T078 [US2] **Validate Evidence Threshold Logging**: Modify `code/runner.py` to include a post-run validation function `validate_evidence_threshold()` that ensures the `evidence_threshold` column is populated for every task.
- [ ] T079 [US3] **Verify Binning Logic Edge Cases**: Implement a unit test that verifies correct binning behavior with small datasets.
- [ ] T080a [US3] **Implement Bin-Merging Logic for Threshold Analysis**: Implement function `merge_bins()` in `code/stats.py` to implement the specified bin merging algorithm.
- [ ] T080b [US3] **Verify Bin-Merging Logic**: Create `tests/unit/test_stats.py::test_bin_merging_logic` to verify the implementation of T080a.
- [ ] T081 [US3] **Verify Statistical Test Selection**: Add logic to automatically select between t-test and Wilcoxon based on normality (removed).
- [ ] T082 [US1, US2] **Enforce Strict Data Flow in Runner**: Update `code/runner.py` to enforce a strict execution order.
