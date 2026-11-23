# Tasks: Evaluating the Effectiveness of Retrieval‑Augmented Generation for Code Search

**Input**: Design documents from `/specs/001-evaluating-rag-code-search/`
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

- [ ] T001a [S] Create project directory structure at repository root ensuring the following folders exist: `src/data`, `src/models`, `src/analysis`, `src/cli`, `src/lib`, `data/raw`, `data/processed`, `results`, `tests/unit`, `tests/integration`, `tests/contract`, `tests/conftest.py`.
- [ ] T001b [P] Create a `.gitignore` file at the repository root containing patterns for: `__pycache__/`, `*.pyc`, `.env`, `data/raw/`, `data/processed/`, `results/`, `.pytest_cache/`, and `*.log`.
- [ ] T002a [P] Create `.ruff.toml` at repository root with configuration: `target-version = "py311"`, `line-length = 88`.
- [ ] T002b [P] Create `.black.toml` at repository root with configuration: `line-length = 88`, `target-version = ['py311']`.
- [X] T002c [P] Create `setup.cfg` at repository root configuring: `pytest` (testpaths=tests), `black` (line-length=88), and `ruff` (target-version=py311).
- [X] T003 [P] Implement `src/lib/utils.py` with functions for: fixed random seed setting, tokenization logic (fixed-length truncation), ASCII stripping, and logging setup.
- [X] T004 [P] Implement `src/data/checksum.py` for raw data hash verification and state file management.
- [ ] T005 [S] Create `src/data/models.py` defining `CodeSnippet`, `QueryResult`, and `PerformanceDelta` dataclasses with exact schema alignment to spec. **Depends on**: None. **Consumed by**: T006, T007, T009, T010, T011.
- [X] T006 [P] Implement `src/data/download.py` using `ir_datasets.load("codesearchnet-python/train")`, `ir_datasets.load("codesearchnet-python/test")`, `ir_datasets.load("codesearchnet-java/train")`, and `ir_datasets.load("codesearchnet-java/test")` to fetch Python and Java subsets. MUST explicitly distinguish between 'Training Split' (for indexing) and 'Test Split' (for evaluation), saving them to separate directories (`data/raw/train`, `data/raw/test`). MUST raise on failure, NO synthetic fallback.
- [X] T007 [P] Implement `src/data/preprocess.py` to load raw data from `data/raw/train` and `data/raw/test` separately (using the specific split paths from T006), strip non-ASCII, truncate to tokens, and save processed JSONL/CSV to `data/processed/train` and `data/processed/test` respectively.
- [ ] T008 [P] Create `tests/conftest.py` with shared fixtures (mocked data paths, temp directories) for pytest environment configuration.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible RAG vs. Baseline Evaluation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Build the end-to-end pipeline that downloads CodeSearchNet, runs BM, Dual-Encoder, and RAG retrieval on a set of queries, and outputs nDCG@k/Precision@k metrics in a CSV.

**Independent Test**: The system can be tested by executing the pipeline on a subset of CodeSearchNet queries and verifying that it outputs a CSV file containing three distinct rows (one per method) with valid nDCG@K scores, without requiring any external API calls or GPU resources.

### Implementation for User Story 1

- [X] T009 [P] [US1] Implement `src/models/retriever_bm25.py` using `rank_bm25` on preprocessed data.
- [X] T010 [P] [US1] Implement `src/models/retriever_neural.py` using `sentence-transformers/all-MiniLM-L-v2` for dual-encoder retrieval.
- [ ] T011 [US1] Implement `src/models/rag_pipeline.py` using `Salesforce/codegen-350M-mono` (CPU mode) with fixed prompt template, temp=0.0, top-k retrieval. **CRITICAL**: The system MUST enforce CPU-only execution. If the model fails to load on CPU due to OOM, the system MUST attempt to load with 8-bit quantization (`load_in_8bit=True`). If OOM persists, the system MUST raise a `RuntimeError` with a clear message: "RAG execution failed: CPU OOM and quantization failed." This ensures FR-003 is met without non-reproducible GPU offload. Includes memory monitoring logic using `psutil`.
- [X] T012 [US1] Implement `src/models/metrics.py` to calculate Precision@K, Recall@K, and nDCG@K against ground truth labels.
- [ ] T032 [P] [US1] Implement `src/analysis/throughput_monitor.py` to measure and log throughput (queries/hour) to `results/throughput_report.json`. This file is separate from `results.csv` to preserve the per-query schema defined in FR-007.
- [ ] T032a [P] [US1] Ensure `src/analysis/throughput_monitor.py` outputs a JSON file `results/throughput_report.json` with the schema `{"total_queries": N, "total_time_seconds": T, "queries_per_hour": QPH}`.
- [ ] T013 [US1] Implement `src/cli/main.py` to orchestrate the multiple methods on a representative set of queries, handle edge cases (zero matches, truncation warnings), and output `results.csv`. **IMPORTANT**: `results.csv` MUST NOT contain throughput metrics; throughput is written to `results/throughput_report.json`. **Depends on**: T032, T011, T009, T010, T012.
- [ ] T014 [US1] Add deterministic seed enforcement and reproducibility checks in `src/cli/main.py`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation to verify the pipeline**

- [X] T016 [P] [US1] Contract test for CSV output schema in `tests/contract/test_output_schema.py`.
- [X] T017 [P] [US1] Integration test for full pipeline execution on queries in `tests/integration/test_pipeline_e2e.py`.
- [X] T018 [P] [US1] Unit test for nDCG calculation logic in `tests/unit/test_metrics.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Semantic Descriptor Correlation Analysis (Priority: P2)

**Goal**: Compute semantic descriptors (API density, doc density, naming consistency) for test set queries and ground truth snippets and correlate them with performance deltas using Spearman/Pearson tests.

**Independent Test**: The system can be tested by feeding it a pre-computed CSV of performance deltas and code descriptors, verifying that it outputs a JSON report containing Spearman correlation coefficients and p-values for each descriptor against the performance delta.

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `src/data/descriptors.py` to calculate API density, doc density, and Naming-consistency score (using `CodeBERT-base` embeddings) for the union of ground truth snippets AND the top-K retrieved snippets for each query (to ensure correlation covers the actual data used in delta calculation). The performance delta (RAG - Baseline) is a function of the retrieved set, but the descriptors explain the code properties. MUST compute for the union of ground truth and retrieved snippets, not just ground truth.
- [ ] T020 [US2] Implement `src/analysis/correlation.py` to compute Spearman's rho and Pearson's r. MUST perform a normality test to select between paired t-test and Wilcoxon signed-rank test. MUST format the final `correlation_results.json` and `results.csv` to explicitly flag correlations with p < 0.05 as "statistically significant" and others as "non-significant". **Output**: `results/correlation_results.json` and `results/results.csv`.
- [ ] T020b [US2] Implement `src/analysis/save_baseline_artifacts.py` to persist the **unmasked baseline retrieval artifacts** (raw scores, descriptors, and query IDs) to `data/processed/unmasked_baseline_raw.json`. This file is required by T022 for the control experiment comparison. **Depends on**: T019, T007. **Schema**: Must include `query_id`, `snippet_id`, `score`, `api_density`, `doc_density`, `naming_consistency`.
- [ ] T021 [US2] Implement `src/data/masking.py` to implement token masking logic (regex/token-level replacement) for API and documentation tokens as required by FR-009. Explicitly reference FR-009 in the docstring. **Depends on**: T020b, T007.
- [ ] T022 [US2] Implement `src/analysis/control_experiment.py` to consume masked data generated by `src/data/masking.py` (T021) AND the unmasked baseline artifacts from `data/processed/unmasked_baseline_raw.json` (T020b) to compare results and verify correlations are not artifacts (FR-009). Explicitly reference FR-009 in the docstring. **Depends on**: T020b, T021.
- [ ] T025 [US2] Update `src/cli/main.py` to trigger descriptor calculation and correlation analysis after retrieval, outputting `correlation_results.json`. **Depends on**: T020, T020b, T022. **Note**: T025 orchestrates the run that produces data for T023a review.
- [ ] T026 [US2] Ensure `src/data/descriptors.py` handles `NaN` gracefully and excludes invalid points from correlation while retaining them for retrieval metrics.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Resource Constraint Degradation Study (Priority: P3)

**Goal**: Run the pipeline with strict resource limits (a constrained FAISS index, a lightweight 2-layer model) and generate a degradation report comparing results to the standard run.

**Independent Test**: The system can be tested by running the pipeline with the "strict resource" flags enabled, verifying that the FAISS index size stays within acceptable memory constraints and the model parameter count is reduced, while still producing valid (though potentially lower) nDCG scores.

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `src/analysis/resource_study.py` to configure FAISS with `IndexFlatIP` and memory cap (limited capacity) via `psutil` monitoring.
- [ ] T028 [US3] Implement logic in `src/models/rag_pipeline.py` to load a custom multi-layer transformer (~150M params) when `--strict-resources` flag is set. **CRITICAL**: The task MUST verify `model.config.num_hidden_layers == 2` AND `model.num_parameters() >= 140_000_000` (approx 150M) before proceeding. If a verified ~150M 2-layer model is not available in the HuggingFace Hub, the task MUST fall back to `prajjwal1/bert-tiny` (14M) with an explicit warning logged that the parameter constraint is approximated, rather than raising a fatal error. **DO NOT** fall back to `prajjwal1/bert-tiny` silently; log the parameter count and constraint violation.
- [ ] T029 [US3] Implement logic to enforce GB RAM limit by subsampling dataset or using a quantized index type if memory cap is approached (PREREQUISITE for T030). MUST depend on T006/T007 for dataset loading logic.
- [ ] T030 [US3] Update `src/cli/main.py` to support `--strict-resources` mode, run both standard and constrained pipelines, and output `degradation_report.json` with absolute percentage point drops. **Depends on**: T028, T029.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Human-in-the-Loop (Priority: P3)

**Purpose**: Automated noise estimation and validation of results.

- [ ] T023a [P] [US2] Implement `src/analysis/noise_estimator.py` to automatically estimate label noise. **Protocol**: Randomly sample a subset of records from `data/processed/test` using random seed 42. Calculate label noise using entropy and agreement heuristics on a sample of records. Save the result to `results/manual_noise_input.json` with the format `{"noise_estimate": <estimated_value>, "sample_size": 50, "method": "automated_heuristic"}`.
- [ ] T023b [P] [US2] Implement `src/cli/gates.py` to create a blocking gate mechanism. This script MUST check for the existence of `results/manual_noise_input.json` before allowing T023c to proceed. If missing, it must raise a `SystemExit` with a clear error: "Human input artifact `manual_noise_input.json` missing. Please complete T023a." **Depends on**: T023a.
- [ ] T023c [US2] Implement `src/analysis/integrate_noise.py` to load the noise estimate from `results/manual_noise_input.json` (produced by T023a) and integrate it into the final `results.csv` and `correlation_results.json` outputs (FR-010, FR-007). This task MUST run after T023b (gate) confirms T023a is complete. **Depends on**: T023b.

**Checkpoint**: Validation complete

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033a [P] Implement batched inference in `src/models/retriever_neural.py` and `src/models/rag_pipeline.py` to meet ≥33 queries/hour throughput target.
- [ ] T033b [P] Implement streaming logic in `src/data/download.py` and `src/data/preprocess.py` to process large datasets in chunks, verifying throughput targets with benchmarks.
- [ ] T034a [P] Update `docs/quickstart.md` with specific instructions on running the pipeline, expected outputs, and resource constraints.
- [ ] T034b [P] Update `docs/data-model.md` with specific entity definitions and data flow diagrams.
- [ ] T035a [P] Refactor `src/models/rag_pipeline.py` to separate retrieval and generation logic into distinct classes. Verification: Passes linting with no circular imports.
- [ ] T035b [P] Refactor `src/models/metrics.py` to ensure modularity and testability. Verification: Unit tests cover all edge cases.
- [ ] T036 [P] Additional unit tests for edge cases (zero matches, truncation, NaN handling) in `tests/unit/`.
- [ ] T037a [P] Implement pre-commit hook to scan for `requests` library usage and external API calls in `src/`.
- [ ] T037b [P] Implement seed enforcement check in `src/cli/main.py` to assert `random.seed` is called at the start of execution.
- [ ] T038 Create a `requirements.txt` file pinning all dependencies: `ir-datasets`, `sentence-transformers`, `faiss-cpu`, `rank_bm25`, `scikit-learn`, `pandas`, `numpy`, `psutil`, `transformers`, `torch`, `accelerate`, `pytest`, `ruff`, `black`.

---

## Phase 8: Verification & Validation

**Purpose**: Ensure all critical requirements and constraints are explicitly tested and verified before finalization.

- [ ] T039 [P] [US1/US2] Implement `tests/integration/test_data_integrity.py` to verify that `src/data/download.py` raises an exception on network failure and does NOT fall back to synthetic data (FR-001, Data Hygiene Rule).
- [ ] T040 [P] [US1] Implement `tests/integration/test_retrieval_order.py` to verify that the *execution* of the CLI script (T013) producing `results.csv` occurs strictly before any verification tasks that consume `results.csv`, preventing race conditions in the pipeline.
- [ ] T041 [P] [US2] Implement `tests/unit/test_descriptor_scope.py` to assert that `src/data/descriptors.py` only processes query and ground truth snippets (and retrieved snippets as per T019), raising an error if invalid data is passed (FR-008, Circularity prevention).
- [ ] T042 [P] [US3] Implement `tests/integration/test_resource_limits.py` to verify that `psutil` monitoring in `src/models/rag_pipeline.py` (T011, T027) correctly triggers subsampling or index quantization when RAM exceeds 1.05GB (FR-006).
- [ ] T043 [P] [US2] Implement `tests/unit/test_statistical_significance.py` to verify that `src/analysis/correlation.py` correctly switches from t-test to Wilcoxon when normality is violated (FR-005, US-2).
- [ ] T044 [P] [US2] Implement `tests/integration/test_control_experiment.py` to verify that the masked token correlation (T022) produces a distinct result from the unmasked baseline, confirming the correlation is not an artifact (FR-009).
- [ ] T045 [P] [US2] Implement `tests/integration/test_human_gate.py` to verify that T023b correctly blocks T023c if `results/manual_noise_input.json` is missing.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Verification (Phase 8)**: Depends on the completion of all corresponding implementation tasks in Phases 3-7

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 results (performance deltas)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 implementation to run constrained mode

### Within Each User Story

- Tests (if included) MUST be written AFTER implementation
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
- All Verification tasks (Phase 8) can run in parallel once their respective implementation tasks are complete

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement src/models/retriever_bm25.py using rank_bm25 on preprocessed data"
Task: "Implement src/models/retriever_neural.py using sentence-transformers/all-MiniLM-L-v2 for dual-encoder retrieval"
Task: "Implement src/models/rag_pipeline.py using Salesforce/codegen-350M-mono (CPU mode)..."

# After implementation, launch all tests for User Story 1 together:
Task: "Contract test for CSV output schema in tests/contract/test_output_schema.py"
Task: "Integration test for full pipeline execution on 50 queries in tests/integration/test_pipeline_e2e.py"
Task: "Unit test for nDCG@10 calculation logic in tests/unit/test_metrics.py"
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
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Integrity**: `src/data/download.py` MUST raise on failure; NO synthetic fallback allowed.
- **Resource Limits**: `psutil` must be used to monitor RAM in all retrieval tasks.
- **Reproducibility**: Fixed random seeds must be set at the start of every script.
- **Descriptor Scope**: `src/data/descriptors.py` MUST compute descriptors for the union of ground truth and retrieved snippets, not just ground truth.
- **Human Task**: Task T023a is now an automated heuristic; the pipeline must wait for `results/manual_noise_input.json` to be present (verified by T023b) before proceeding to T023c. Sampling protocol is fixed (50 records, seed 42).
- **Verification Priority**: Tasks T039-T045 are critical to prevent common failure modes (synthetic fallback, data race, circularity, human-input missing) and must be completed before the project is considered "analyzed".
- **Throughput**: Throughput metrics are written to `results/throughput_report.json`, NOT `results.csv`.
- **RAG Execution**: T011 enforces RAG execution via CPU quantization; it does not offload to GPU.
- **Resource Model**: T028 enforces ~150M 2-layer model with fallback to `prajjwal1/bert-tiny` if unavailable.
- **Control Experiment**: T020b generates the unmasked baseline artifact required by T022.