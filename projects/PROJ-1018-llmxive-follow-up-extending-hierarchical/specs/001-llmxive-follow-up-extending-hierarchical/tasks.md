# Tasks: llmXive follow-up: extending "Hierarchical Sparse Attention Done Right: Toward Infinite Context Mode"

**Input**: Design documents from `/specs/001-llmxive-static-distillation/`
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

- [X] T001 Create project directory structure: Create directories `src/`, `tests/`, `data/raw/`, `data/interim/`, `data/processed/` within the project's code root as defined in plan.md (`projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/`).
- [X] T001b Create `requirements.txt`: Create `requirements.txt` at exact path `projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/requirements.txt` containing `transformers>=4.40.0`, `datasets>=2.18.0`, `scikit-learn>=1.3.0`, `pandas>=2.0.0`, `numpy>=1.24.0`, `torch>=2.0.0`, `pytest>=7.0.0`, `pyarrow>=12.0.0`
- [X] T001c Create `pyproject.toml`: Create `pyproject.toml` in `projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/` with explicit metadata fields (`name`, `version`, `description`, `authors`, `dependencies`) and build system configuration
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black/isort) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement robust data loader for `lmsys/pg-19-test` using `datasets.load_dataset` with streaming enabled (`streaming=True`). **Deliverable**: Create class `StreamingDataLoader` in `src/data_loader.py` with method `__iter__(self) -> Iterator[Dict[str, Any]]` returning `Dict[str, Any]` (keys: `text`, `id`, `source`). **Constraint**: If network fetch fails (timeout, 404), raise `RuntimeError`. If memory limits are exceeded during processing, implement a sampling fallback (e.g., `itertools.islice` first N rows) to ensure feasibility; log the sampling action. [Depends on T001b]
- [ ] T005b [P] Load/Define Validation Split: Add function `load_validation_split() -> StreamingDataLoader` in `src/data_loader.py` that explicitly fetches the `validation` split from `lmsys/pg-19-test` (distinct from test) and returns a `StreamingDataLoader` instance. **Output**: A loader instance ready for T005. [Depends on T004]
- [ ] T005 Implement document filtering logic: Add function `filter_documents(loader: StreamingDataLoader, min_tokens: int = 32000) -> List[Dict]` in `src/data_loader.py` that consumes the validation split loader. **Logic**: Retain only documents with token count ≥ 32,000. **Output**: Write filtered dataset to `projects/PROJ-1018-llmxive-follow-up-extending-hierarchical/code/data/interim/filtered_pg19.json` as a JSON list of dicts with schema: `{"document_id": str, "text": str, "token_count": int}`. **Logging**: Print exact string `WARNING: Skipping document {document_id}: length {token_count} < 32000` for each skipped document. **Fallback**: If memory limits are hit during filtering, sample the stream (e.g., first 100 docs) and log the sampling action. [Depends on T005b]
- [ ] T006 [P] Implement error handling for failed real data fetches: Add logic to `src/data_loader.py` to raise explicit exceptions (NO synthetic fallbacks) if the `datasets.load_dataset` call fails (network error, missing split). **Note**: This task depends on T004 establishing the stream context. [Depends on T004]
- [ ] T007 Create base configuration manager: Create `src/config.py` defining a `Config` dataclass with fields `seed`, `chunk_size`, `model_path`, `k_clusters`, `skip_short_documents` (bool, default True).
- [X] T007b Load/Initialize pre-trained HiLS checkpoint: Add function to load and validate the pre-trained HiLS model checkpoint in `src/model_loader.py`, ensuring compatibility before inference tasks begin
- [ ] T008 [P] Setup logging infrastructure: Create `src/logging_utils.py` implementing a logger that outputs JSON lines with fields `timestamp`, `level`, `message`, `version_hash`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dynamic Baseline Extraction (Priority: P1) 🎯 MVP

**Goal**: Extract retrieval score matrices from the dynamic HiLS model for every chunk in the validation set and aggregate them into canonical relevance profiles.

**Independent Test**: Run extraction on a sample of documents; verify output JSON contains non-empty retrieval score matrices for every chunk ID with correct dimensions.

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `RelevanceProfile` data structure: Add class `RelevanceProfile` in `src/models.py` with fields `chunk_id: str`, `scores: List[float]`, `document_id: str`
- [X] T013 [US1] Implement chunking logic and edge case handling: Add function `chunk_document(text: str, chunk_size: int, tokenizer) -> List[Dict[str, Any]]` in `src/extraction.py`; load tokenizer from `model_path` (T007b) before execution. **Edge Case Handling**: If `len(tokens) < 2048`, check `config.skip_short_documents`. If True, **skip** the document and log to stdout; if False, **pad** to `chunk_size`. **Verification**: Ensure the logging output matches the expected format for skipped/padded documents. [Depends on T005, T007b]
- [X] T012 [X] [US1] Implement dynamic HiLS inference wrapper: Add class `DynamicHiLSWrapper` in `src/extraction.py` with methods `extract_scores(chunk)` and `handle_errors()` to extract raw retrieval score matrices. [Depends on T007b]
- [X] T012b [US1] Execute Dynamic Baseline Inference: Implement function `run_dynamic_inference(model, dataset, wrapper) -> List[Dict]` in `src/extraction.py` to load the pre-trained checkpoint (T007b), pass the `model` object to `wrapper`, execute the forward pass for every chunk in the validation set, and output **raw extraction results** (list of dicts: `chunk_id`, `document_id`, `raw_scores`) to `data/interim/raw_extraction_results.json`. **Output**: Do NOT aggregate here; only raw scores. [Depends on T012, T013, T007b, T005b]
- [ ] T014 [US1] Implement aggregation logic: Add function `aggregate_profiles(raw_results: List[Dict], chunk_metadata: List[Dict]) -> List[RelevanceProfile]` in `src/extraction.py`. **Input**: `raw_results` from T012b (JSON file) and `chunk_metadata` (chunk_id to token indices) from T013. **Logic**: Aggregate raw scores per `chunk_id` across the validation set to compute canonical relevance profiles. [Depends on T012b, T013]
- [ ] T016 [US1] Add validation: Add function `validate_profiles(profiles: List[RelevanceProfile])` in `src/extraction.py` to ensure no retrieval scores are null/NaN and dimensions match configuration. [Depends on T014]
- [ ] T015 [US1] Implement JSON serialization: Add function `save_profiles(profiles: List[RelevanceProfile], path: str)` in `src/extraction.py` that writes a JSON array of objects with keys `chunk_id`, `scores` to `data/interim/relevance_profiles.json`. [Depends on T016]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. Execution depends on code.

- [X] T009 [P] [US1] Contract test for extraction output format in `tests/test_extraction.py` (pytest function: `test_extraction_output_schema`)
- [X] T010 [P] [US1] Integration test for end-to-end extraction on sample data in `tests/test_extraction.py` (pytest function: `test_end_to_end_extraction`): Assert `len(scores) > 0` and `shape == (num_chunks, num_tokens)` where `num_chunks` and `num_tokens` are derived from the sample input

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Static Index Construction (Priority: P2)

**Goal**: Apply CPU-optimized K-Means clustering (with PCA reduction) to aggregated relevance profiles to generate a static lookup table (centroids + mappings).

**Independent Test**: Run clustering on extracted profiles; verify output maps every unique chunk ID to exactly one cluster centroid with $K$ clusters.

### Implementation for User Story 2

- [ ] T019 [US2] Implement PCA dimensionality reduction: Add function `apply_pca(profiles: List[RelevanceProfile]) -> np.ndarray` in `src/clustering.py` (Depends on T015)
- [ ] T020 [US2] Implement K-Means clustering algorithm: Add function `run_kmeans(data: np.ndarray, k: int, retry_count: int = 3)` in `src/clustering.py` with retry logic for empty cluster convergence (Depends on T019)
- [ ] T021 [US2] Implement generation of `StaticIndex`: Add class `StaticIndex` in `src/clustering.py` with fields `centroids: np.ndarray`, `chunk_to_cluster: Dict[str, int]`, `k: int`
- [ ] T022 [US2] Serialize static index: Add function `save_static_index(index: StaticIndex, path: str)` in `src/clustering.py` to write to `data/processed/static_index.json` with metadata (K, seed, PCA components)
- [ ] T023 [US2] Add performance check: Add function `benchmark_lookup(index: StaticIndex, token_count: int)` in `src/clustering.py` that returns True if latency < 50ms on a multi-core CPU

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for static index structure in `tests/test_clustering.py`
- [X] T018 [P] [US2] Integration test for K-Means convergence and retry logic in `tests/test_clustering.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Evaluation & Statistical Significance (Priority: P3)

**Goal**: Execute modified "Static-HiLS" inference using the static index, compute metrics against dynamic baseline, and perform statistical significance testing.

**Independent Test**: Run evaluation on a small subset; verify output includes perplexity, QA accuracy, p-value, and latency comparison.

**Note**: Spec FR-005 mandates a 'paired t-test' for statistical significance. The plan.md 'Complexity Tracking' suggests a Wilcoxon test due to normality assumptions. Per the Constitution, the Spec (FR-005) takes precedence for task execution. The task below implements the paired t-test as required by the Spec.

### Implementation for User Story 3

- [ ] T026 [US3] Implement "Static-HiLS" inference pipeline: Add function `static_inference(model, static_index, input_ids)` in `src/inference.py` that **modifies the internal attention mask generation logic** of the HiLS model to **bypass dynamic retrieval** and use the `static_index.chunk_to_cluster` lookup table for attention sparsity patterns. **Constraint**: Do not wrap the model; modify the attention mechanism directly. (Depends on T022)
- [ ] T027 [US3] Implement perplexity calculation: Add function `calculate_perplexity(model, dataset)` in `src/evaluation.py` for both dynamic and static models on held-out test set (Depends on T026)
- [ ] T028 [US3] Implement downstream long-context QA evaluation: Add function `evaluate_qa(model, dataset)` in `src/evaluation.py`. **Primary Dataset**: `hotpotqa` (HF ID: `hotpotqa`, split: `validation`). **Fallback**: If `hotpotqa` is unavailable, use `narrativeqa` (HF ID: `narrativeqa`, split: `validation`). **Requirement**: Verify dataset availability; if both fail, raise an explicit error. Calculate and report QA accuracy degradation against dynamic baseline (Depends on T026)
- [ ] T029 [US3] Implement statistical significance testing: Add function `run_statistical_tests(dynamic_scores: List[float], static_scores: List[float]) -> Dict[str, float]` in `src/evaluation.py` that performs a **paired t-test** using `scipy.stats.ttest_rel` and returns p-value and test_type. Implements spec FR-005 requirement. (Depends on T027)
- [ ] [P] T030 [US3] Implement latency measurement protocol: Add function `measure_latency(model, dataset)` in `src/evaluation.py` using `time` module on a multi-core CPU with specific protocol: **large token input context**, **10 runs**, **2 warm-up iterations**, 2 cores. Write results to `data/processed/latency_metrics.json` (Depends on T026)
- [ ] T030b [US3] Implement memory footprint measurement: Add function `measure_retrieval_memory(static_index, dynamic_wrapper)` in `src/evaluation.py`. **Target**: Measure memory of the `DynamicHiLSWrapper` (T012) specifically. **Method**: Use `tracemalloc` in a **single process** context. Wrap the `extract_scores` call in `with tracemalloc.start(): ... tracemalloc.get_traced_memory()` to isolate retrieval overhead from model weights. Write results to `data/processed/memory_metrics.json` (Depends on T026, T012)
- [ ] T031a [US3] Implement sensitivity analysis sweep (Index Generation): Add function `sweep_k_values(k_values: List[int] = [50, 100, 200])` in `src/evaluation.py` that iterates K, **re-executes the clustering logic (T020)** for each K value on the validation profiles, and **writes unique output files** (e.g., `static_index_K50.json`, `static_index_K100.json`, `static_index_K200.json`) to `data/processed/`. (Depends on T015, T020)
- [ ] T031b [US3] Implement sensitivity analysis report (Report Generation): Add function `generate_sensitivity_report(index_files: List[str]) -> Dict` in `src/evaluation.py` that loads the K-specific indexes, runs evaluation (T027, T028) for each, and aggregates results into a structured report of perplexity and QA accuracy trade-offs. Write to `data/processed/sensitivity_report.json`. (Depends on T031a, T027, T028)
- [ ] T033a [US3] Execute Test Set Evaluation: Implement function `run_test_evaluation(dynamic_model, static_model, test_dataset, static_index)` in `src/evaluation.py` to explicitly orchestrate the execution of the dynamic baseline inference AND the static variant inference on the held-out test set. **Scope**: Single-run evaluation (T027-T030). Aggregate results into final comparison data. (Depends on T027, T028, T029, T030, T030b)
- [ ] T032 [US3] Generate structured `EvaluationReport`: Add function `generate_report(metrics: Dict, sensitivity_report: Dict) -> EvaluationReport` in `src/evaluation.py` that serializes to `data/processed/evaluation_report.json` with keys `perplexity`, `qa_accuracy`, `p_value`, `latency`, `memory_footprint`, `sensitivity_analysis` (Depends on T033a, T031b)

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for evaluation report schema in `tests/test_evaluation.py`: Assert `set(report.keys()) == {'perplexity', 'qa_accuracy', 'p_value', 'latency', 'memory_footprint'}`
- [ ] T025 [P] [US3] Integration test for paired t-test execution in `tests/test_evaluation.py`: Assert `isinstance(p_value, float) and 0 <= p_value <= 1`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029b [P] Resolve Plan Contradiction: Update `plan.md` to replace the 'Wilcoxon test' recommendation in the 'Complexity Tracking' section and 'Test Coverage Matrix' with 'paired t-test' to align with Spec FR-005. **Verification**: Run `grep -r "Wilcoxon" plan.md` and ensure it returns 0 matches. (No code dependencies)
- [ ] T033 [P] Documentation updates in `docs/` including `quickstart.md` and `research.md`
- [ ] T034 Code cleanup and refactoring for type hints and docstrings
- [ ] T035 Performance optimization for streaming data processing
- [ ] T036 [P] Additional unit tests for edge cases (short docs, convergence failures) in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces** `data/interim/relevance_profiles.json`.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on** output of US1 (`relevance_profiles.json`). **Produces** `data/processed/static_index.json`.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on** output of US2 (`static_index.json`) and US1 (for baseline comparison).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- In Phase 2 (Foundational), T004, T005b, T005 form a **sequential dependency chain** (T004->T005b->T005) and **CANNOT** run in parallel. T004 must complete to establish a stable data stream before T005b can execute. T005 depends on T005b. T006 (error handling) is [P] and can run in parallel with the T004-T005b-T005 chain.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for extraction output format in tests/test_extraction.py"
Task: "Integration test for end-to-end extraction on sample data in tests/test_extraction.py"

# Launch all models for User Story 1 together:
Task: "Implement RelevanceProfile data structure definition in src/models.py"
Task: "Implement dynamic HiLS inference wrapper in src/extraction.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify real data extraction).
5. Deploy/demo if ready.

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
 - Developer B: User Story 2 (can start once US1 data is available)
 - Developer C: User Story 3 (can start once US2 index is available)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Data Hygiene**: Never fall back to synthetic data; if real fetch fails, raise an error. If memory limits are hit, sample the stream.
- **Streaming**: Use `datasets.load_dataset(..., streaming=True)` for PG-19 to handle large contexts within RAM limits.
- **Avoid**: Vague tasks, same file conflicts, cross-story dependencies that break independence.
- **Statistical Method**: T029 explicitly mandates 'paired t-test' per spec FR-005.
- **Memory Isolation**: T030b explicitly mandates `tracemalloc` in a single process to isolate retrieval module memory.
- **QA Benchmark**: T028 allows `hotpotqa` (primary) or `narrativeqa` (fallback) per Spec Assumptions.
- **Hardware Constraints**: T023 and T030 explicitly enforce 2-core CPU constraints and 32k token context.
- **Sweep Values**: T031a uses explicit values `[50, 100, 200]` for sensitivity analysis as per spec FR-008, with **unique output filenames** to preserve artifacts.
- **Plan Note**: The plan.md Test Coverage Matrix currently lists 'Wilcoxon test execution' for FR-005, which contradicts spec FR-005 (paired t-test). This is a plan artifact issue flagged for update; tasks follow the spec (FR-005) which takes precedence. T029b resolves this in Phase N.