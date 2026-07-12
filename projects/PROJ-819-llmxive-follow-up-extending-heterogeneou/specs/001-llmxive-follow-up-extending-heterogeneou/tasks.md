# Tasks: llmXive follow-up: extending "Heterogeneous Scientific Foundation Model Collaboration"

**Input**: Design documents from `/specs/001-llmxive-cache-optimization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directories per implementation plan: `projects/PROJ-819-llmxive-follow-up-extending-heterogeneou/` including `code/`, `data/`, `tests/`, `state/` and subdirectories `code/cache`, `code/pipeline`, `code/analysis`, `data/raw`, `data/derived`, `tests/unit`, `tests/integration` <!-- FAILED: unspecified -->
- [X] T001b [P] Create empty `__init__.py` files in all newly created `code/` and `tests/` directories to initialize Python packages
- [X] T002 Initialize Python project with `requirements.txt` (pinned `sentence-transformers`, `scikit-learn`, `numpy`, `pandas`, `pytest`, `cachetools`, `statsmodels`)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 [P] Setup `pytest` configuration and `pytest-benchmark` plugin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `code/data/generator.py` to generate the **Test Set** (500 (2509.23775, https://arxiv.org/abs/2509.23775) queries) for FR-007. **Deliverable**: Create `data/derived/synthetic_queries_test.json` containing a list of objects with keys `prompt`, `ground_truth`, `steps`, `seed`, and `domain`.
- [ ] T005a [P] Extend `code/data/generator.py` to generate the **Warm-up Set** (100 queries) for FR-007. **Deliverable**: Create `data/derived/synthetic_queries_warmup.json` with the same schema as T005.
- [ ] T006 [P] Define `BenchmarkQuery` entity schema (dataclass/pydantic model) and create stub `code/data/loaders.py` with placeholder functions for loading the schema.
- [X] T007 Implement `code/cache/semantic_cache.py`: Custom LRU class wrapping `cachetools` for `CacheEntry` objects (embedding, output, timestamp).
- [ ] T008 Implement `code/cache/utils.py`: Cosine similarity calculation and thresholding logic.
- [~] T009 Implement `code/pipeline/eywa_orchestra.py`: Mock/Wrapper for EywaOrchestra pipeline (CPU-tractable, deterministic).
- [~] T010 Implement `state/manifest.json` logic and `state/hashes/` directory structure for reproducibility (Principle V). **Deliverable**: Create `state/manifest.json` with schema `{ "files": [{ "path": "str", "sha256": "str" }] }` using SHA-256 hashing for all files in `data/` and `code/`.
- [~] T011 Create `data/raw/` and `data/derived/` directory structure with checksumming hooks

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Semantic Cache Implementation and Hit-Rate Measurement (Priority: P1) 🎯 MVP

**Goal**: Implement the lightweight semantic caching layer that intercepts queries, computes embeddings, and retrieves cached outputs.

**Independent Test**: Run a batch of synthetic iterative queries against the cache module in isolation to verify hit/miss logic and hit-rate calculation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. **Dependency**: T012/T013 depend on T007/T008 (stubs) being present.

- [~] T012 [P] [US1] Unit test for `semantic_cache.py` hit/miss logic in `tests/unit/test_cache.py` (depends on T007 stub)
- [~] T013 [P] [US1] Unit test for `utils.py` cosine similarity calculation in `tests/unit/test_cache.py` (depends on T008 stub)

### Implementation for User Story 1

- [~] T014 [US1] Implement full `BenchmarkQuery` entity parsing logic in `code/data/loaders.py` to ingest `data/derived/synthetic_queries_test.json` (Test Set).
- [~] T015 [US1] Implement embedding generation using a sentence-transformer model in `code/cache/utils.py` (CPU-only).
- [~] T016 [US1] Implement cache population logic (Warm-up Phase) in `code/cache/semantic_cache.py` using `data/derived/synthetic_queries_warmup.json`.
- [~] T017 [US1] Implement cache retrieval logic with a configurable similarity threshold in `code/cache/semantic_cache.py`. <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->
- [~] T018 [US1] Implement error handling for embedding failures (log as miss) in `code/cache/semantic_cache.py`. <!-- FAILED: unspecified -->
- [~] T019 [US1] Implement LRU eviction policy when cache limit is exceeded in `code/cache/semantic_cache.py` **AND** log every eviction event to `data/derived/cache_events.log` to satisfy Edge Case logging requirements.
- [~] T020 [US1] Create `code/pipeline/runner.py` to orchestrate the cache population and query processing loop.
- [~] T021 [US1] Add logging for Cache Hits and Cache Misses with exact similarity scores in `code/pipeline/runner.py`.
- [ ] T021a [US1] Define the data structure (e.g., a named tuple or class) in `code/pipeline/runner.py` to explicitly separate warm-up metrics from test set metrics.
- [ ] T021b [US1] Implement the aggregation function in `code/pipeline/runner.py` that filters metrics using the structure from T021a to isolate test set performance.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Efficiency and Accuracy Trade-off Quantification (Priority: P2)

**Goal**: Execute the EywaOrchestra pipeline with and without caching, comparing runtime, invocations, and accuracy.

**Independent Test**: Run the paired execution pipeline on the benchmark subset and generate a report with runtime reduction %, accuracy deviation %, and statistical test p-values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Integration test for baseline vs. cached execution in `tests/integration/test_pipeline.py`
- [ ] T023 [P] [US2] Unit test for statistical significance calculation (Permutation Test, Linear Regression) in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [ ] T024 [P] [US2] Implement `code/analysis/metrics.py` for calculating runtime reduction, invocation count, and accuracy deviation.
- [ ] T025 [US2] Implement `code/analysis/stats.py` for Permutation Test on accuracy differences. **Input**: List of accuracy diffs (Baseline - Cached). **Parameters**: `n_permutations=10000 `. **Output**: `data/derived/statistics.json` with key `p_value_permutation`. **Note**: Replaces McNemar's test per Plan Methodology Section 3 due to contingency table degeneracy.
- [ ] T026 [US2] Implement `code/analysis/stats.py` for Multi-variable Linear Regression on runtime vs. hits/misses. **Model**: `runtime ~ hits + misses`. **Library**: Use `statsmodels.api.OLS` (not `scipy.stats.linregress` which only supports 1 variable). **Output**: `data/derived/statistics.json` with key `regression_coefficients` and `p_value_runtime`. **Note**: Replaces paired t-test per Plan Methodology Section 3.
- [ ] T027 [US2] Implement `code/pipeline/runner.py` logic for Baseline execution (Warm-up cache ignored, load `synthetic_queries_test.json`). **Dependency**: Requires T005, T005a, T014-T019 completion.
- [ ] T028 [US2] Implement `code/pipeline/runner.py` logic for Cached execution (Warm-up cache populated, load `synthetic_queries_test.json`). **Dependency**: Requires T005, T005a, T014-T019 completion.
- [ ] T029a [US2] Implement pre-run validation in `code/data/generator.py` to verify the generator logic is epistemologically independent of EywaOrchestra inference logic (FR-008, FR-007). **Deliverable**: Raise error if dependency detected.
- [ ] T029b [US2] Implement static code inspection in `tests/unit/test_independence.py` to verify `code/data/generator.py` does not import `code/pipeline/eywa_orchestra.py` or rely on its internal logic. **Deliverable**: Unit test that asserts independence constraints on the generator source code.
- [ ] T030 [US2] Generate `data/derived/results.csv` containing aggregated metrics for both runs. **Schema**: Columns must be `run_type`, `total_time`, `hit_rate`, `accuracy`, `total_queries`.
- [ ] T031 [US2] Generate statistical report (p-values) in `data/derived/statistics.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis across thresholds and visualize the trade-off curve.

**Independent Test**: Run the pipeline with the specified thresholds, verify the generated CSV/JSON report and the trade-off plot.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Integration test for sensitivity analysis loop in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T033 [P] [US3] Implement `code/analysis/visualization.py` for generating trade-off curve plots (hit-rate, runtime, accuracy).
- [ ] T034 [US3] Implement sensitivity analysis loop in `code/main.py` iterating through the **exact** discrete threshold set: `[0.90, 0.95, 0.99] `. **Dependency**: Requires completion of T027, T028, T024-T026.
- [ ] T035 [US3] Generate `data/derived/sensitivity_analysis.csv` with metrics per threshold.
- [ ] T036 [US3] Identify optimal threshold based on the defined optimization rule: maximize `score = runtime_reduction - 10 * accuracy_deviation `, where the weight (10) reflects the high priority of accuracy stability.
- [ ] T037 [US3] Generate final visualization plot (PNG/SVG) in `data/derived/trade_off_curve.png`.
- [ ] T038 [US3] Implement Bonferroni correction for multiple comparisons in `code/analysis/stats.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Update `README.md` with execution instructions and environment setup
- [ ] T040a [P] Run `black --check` on all Python files to verify formatting
- [ ] T040b [P] Resolve all `ruff` warnings to ensure code cleanliness
- [ ] T041 Verify all data artifacts in `data/derived/` are checksummed in `state/manifest.json`
- [ ] T042 [P] Add additional unit tests for edge cases (embedding failure, memory limit) in `tests/unit/`
- [ ] T043 Run `quickstart.md` validation (if applicable)
- [ ] T044 Final documentation review for FR-007 (synthetic generator logic) and FR-008 (independence)

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for the cache mechanism to test (Requires full implementation T014-T019, not just stubs).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for the execution logic to sweep thresholds

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Data loaders before services
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
Task: "Unit test for semantic_cache.py hit/miss logic in tests/unit/test_cache.py"
Task: "Unit test for utils.py cosine similarity calculation in tests/unit/test_cache.py"

# Launch all models for User Story 1 together:
Task: "Implement BenchmarkQuery entity parsing in code/data/loaders.py"
Task: "Implement embedding generation in code/cache/utils.py"
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
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All models must run on CPU (no CUDA, no 8-bit quantization) to ensure compatibility with free-tier CI.
- **CRITICAL**: Synthetic ground truth must be epistemologically independent of the EywaOrchestra pipeline.
- **Statistical Methodology**: The Permutation Test and Linear Regression replace McNemar's and t-test per Plan Methodology Section 3 (justified by degeneracy of contingency table and need for multi-variable regression).
- **Data Sets**: Two distinct datasets are generated: `synthetic_queries_test.json` (T005) and `synthetic_queries_warmup.json` (T005a).
- **Independence Check**: Validated via static code inspection in `tests/unit/test_independence.py` (T029b) prior to execution.