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

- [X] T001a [P] Create project directories per implementation plan: `projects/PROJ-819-llmxive-follow-up-extending-heterogeneou/` including `code/`, `data/`, `tests/`, `state/` and subdirectories `code/cache`, `code/pipeline`, `code/analysis`, `data/raw`, `data/derived`, `tests/unit`, `tests/integration`. **Verification**: Run `ls -R projects/PROJ-819-llmxive-follow-up-extending-heterogeneou/` and confirm all directories exist.
- [X] T001b [P] Create empty `__init__.py` files in all newly created `code/` and `tests/` directories to initialize Python packages
- [X] T002 Initialize Python project with `requirements.txt` (pinned `sentence-transformers`, `scikit-learn`, `numpy`, `pandas`, `pytest`, `cachetools`, `statsmodels`)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 [P] Setup `pytest` configuration and `pytest-benchmark` plugin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data generation, spec alignment, and reproducibility hooks.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes data generation and reproducibility hooks.

- [X] T005 [P] Implement `code/data/generator.py` to generate the **Test Set** (500 (2509.23775, https://arxiv.org/abs/2509.23775) queries) for FR-007. **Deliverable**: Create `data/derived/synthetic_queries_test.json` containing a list of objects with keys `prompt`, `ground_truth`, `steps`, `seed`, and `domain`. **Note**: Reference arXiv:2509.23775 for context, do not embed citation in description.
- [X] T005a [P] Extend `code/data/generator.py` to generate the **Warm-up Set** (100 queries) for FR-007. **Deliverable**: Create `data/derived/synthetic_queries_warmup.json`. **Logic**: Use a distinct seed range `1000-1099`. Stratify by domain (Physics, Chemistry, Biology) with an equal distribution per domain and equal step distribution across varying step counts to ensure representativeness. **Dependency**: None.
- [X] T005b [P] [Unit Test] Implement `tests/unit/test_generator.py` to assert that `synthetic_queries_test.json` contains exactly 3 distinct values in the `domain` field: Physics, Chemistry, Biology. **Dependency**: T005.
- [X] T006 [P] Define `BenchmarkQuery` entity schema (dataclass/pydantic model) and create stub `code/data/loaders.py` with placeholder functions for loading the schema.
- [X] T007 Implement `code/cache/semantic_cache.py`: Custom LRU class wrapping `cachetools` for `CacheEntry` objects (embedding, output, timestamp).
- [X] T008 Implement `code/cache/utils.py`: Cosine similarity calculation and thresholding logic.
- [X] T009 Implement `code/pipeline/eywa_orchestra.py`: Mock/Wrapper for EywaOrchestra pipeline (CPU-tractable). **Constraint**: Must be deterministic but support configurable latency.
- [X] T009a [P] Modify `code/pipeline/eywa_orchestra.py` (from T009) to accept a `latency_variance` parameter and implement a random delay distribution that exhibits sufficient variance (Coefficient of Variation > 10%) to ensure statistical significance in T026 (Linear Regression). **Dependency**: T009.
- [X] T025a [P] [Spec Alignment] Update `spec.md` to align Success Criteria SC-004 and FR-006 with the Plan's methodology. **Action**: Edit `spec.md` to replace "paired t-test" and "McNemar's test" with "Permutation Test" and "Linear Regression". **Verification:** Confirm that spec.md now reflects Permutation Test / Linear Regression for accuracy/runtime analysis. **Dependency**: None (Must be done before T025/T026).
- [X] T010 [P] Implement `state/manifest.json` logic as a **continuous hook**. **Trigger**: Execute automatically after every data generation or code modification task in this phase. **Logic**: Recursively traverse `data/` and `code/` directories. For each file, compute SHA-256 hash using `hashlib.sha256`. **Deliverable**: Create/Update `state/manifest.json` with schema `{ "files": [{ "path": "str", "sha256": "str" }] }`.
- [X] T010a [P] Trigger T010 hook after T005 (Test Set generation).
- [X] T010b [P] Trigger T010 hook after T005a (Warm-up Set generation).
- [X] T010c [P] Trigger T010 hook after T009a (Mock variance implementation).
- [X] T011 [P] Create `data/raw/` and `data/derived/` directory structure with checksumming hooks. **Logic**: Ensure directories exist and are writable.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel (subject to specific data dependencies in Phase 3)

---

## Phase 3: User Story 1 - Semantic Cache Implementation and Hit-Rate Measurement (Priority: P1) 🎯 MVP

**Goal**: Implement the lightweight semantic caching layer that intercepts queries, computes embeddings, and retrieves cached outputs.

### Implementation for User Story 1

- [X] T014 [US1] Implement full `BenchmarkQuery` entity parsing logic in `code/data/loaders.py` to ingest `data/derived/synthetic_queries_test.json`.
- [X] T015 [US1] Implement embedding generation using a sentence-transformer model in `code/cache/utils.py` (CPU-only).
- [X] T016 [US1] Implement cache population logic (Warm-up Phase) in `code/cache/semantic_cache.py`. **Input**: `data/derived/synthetic_queries_warmup.json`. **Strategy**: Load a representative set of queries SEQUENTIALLY to populate the cache before the test set runs. **Dependency**: T005a, T007.
- [X] T017 [US1] Implement cache retrieval logic with a configurable similarity threshold in `code/cache/semantic_cache.py`.
- [X] T018 [US1] Implement error handling for embedding failures in `code/cache/semantic_cache.py`. **Logic**: Catch `ValueError` and `RuntimeError` from the embedding model. Log event to `stderr` with level `ERROR`. Treat as "Cache Miss" and proceed to standard inference.
- [X] T019 [US1] Implement LRU eviction policy in `code/cache/semantic_cache.py`. **Trigger**: When cache size exceeds 1GB (or 1000 entries if memory estimation is unavailable). **Logging**: Log every eviction event to `data/derived/cache_events.log` in JSON Lines format (`{"event": "eviction", "evicted_key": "...", "timestamp": "..."}`).
- [X] T020 [US1] Create `code/pipeline/runner.py` to orchestrate the cache population and query processing loop.
- [X] T021 [US1] Add logging for Cache Hits and Cache Misses with exact similarity scores in `code/pipeline/runner.py`.
- [X] T021a [US1] Define the data structure (e.g., a named tuple or class) in `code/pipeline/runner.py` to explicitly separate warm-up metrics from test set metrics.
- [X] T021b [US1] Implement the aggregation function in `code/pipeline/runner.py` that filters metrics using the structure from T021a to isolate test set performance.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️
**Note**: Moved after implementation to test full logic, not just stubs.

- [X] T012 [P] [US1] Unit test for `semantic_cache.py` hit/miss logic in `tests/unit/test_cache.py` (depends on T016, T017).
- [X] T013 [P] [US1] Unit test for `utils.py` cosine similarity calculation in `tests/unit/test_cache.py` (depends on T015).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Efficiency and Accuracy Trade-off Quantification (Priority: P2)

**Goal**: Execute the EywaOrchestra pipeline with and without caching, comparing runtime, invocations, and accuracy.

### Implementation for User Story 2

- [X] T024 [P] [US2] Implement `code/analysis/metrics.py` for calculating runtime reduction, invocation count, and accuracy deviation.
- [X] T025 [US2] Implement `code/analysis/stats.py` for Permutation Test on accuracy differences. **Input**: List of accuracy diffs (Baseline - Cached). **Parameters**: `n_permutations=10000 (OEIS A000012, https://oeis.org/A000012) `. **Output**: `data/derived/statistics.json` with key `p_value_permutation`. **Note**: Bonferroni correction for multiple thresholds will be applied in T038.- [X] T026 [US2] Implement `code/analysis/stats.py` for Multi-variable Linear Regression on runtime vs. hits/misses. **Model**: `runtime ~ hits + misses`. **Library**: Use `statsmodels.api.OLS`. **Requirement**: Implement Bonferroni correction for runtime coefficients when comparing across thresholds. **Output**: `data/derived/statistics.json` with key `regression_coefficients`. **Dependency**: T009a (Mock Variance).
- [X] T027 [US2] Implement `code/pipeline/runner.py` logic for Baseline execution (Warm-up cache ignored). **Dependency**: Requires T005, T005a, T014-T019, T024-T026 (to know output schema).
- [X] T028 [US2] Implement `code/pipeline/runner.py` logic for Cached execution (Warm-up cache populated). **Dependency**: Requires T005, T005a, T014-T019, T024-T026 (to know output schema).
- [X] T029a [US2] Implement pre-run validation in `code/data/generator.py` to verify the generator logic is epistemologically independent of EywaOrchestra inference logic (FR-008, FR-007). **Logic**: Perform static analysis to detect any `import` statements or function calls referencing `code/pipeline/eywa_orchestra.py`. **Deliverable**: Raise `ValueError` if dependency detected.
- [X] T029b [US2] Implement static code inspection in `tests/unit/test_independence.py` to verify `code/data/generator.py` does not import `code/pipeline/eywa_orchestra.py` or rely on its internal logic. **Deliverable**: Unit test that asserts independence constraints on the generator source code.
- [X] T030 [US2] Generate `data/derived/results.csv` containing aggregated metrics for both runs. **Schema**: Columns must be `run_type`, `total_time`, `hit_rate`, `accuracy`, `total_queries`.
- [X] T031 [US2] Generate statistical report (p-values) in `data/derived/statistics.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis across thresholds and visualize the trade-off curve.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T032 [P] [US3] Integration test for sensitivity analysis loop in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [X] T033 [P] [US3] Implement `code/analysis/visualization.py` for generating trade-off curve plots (hit-rate, runtime, accuracy).
- [X] T034 [US3] Implement sensitivity analysis loop in `code/main.py` iterating through the **exact** discrete threshold set: `[0.90, 0.95, 0.99]`. **Requirement**: The execution logic MUST clear the cache state (reset memory) before each threshold iteration to ensure independent measurements. The execution logic will call reusable functions for Baseline and Cached Execution (T027/T028) with the specified threshold. **Dependency**: Requires completion of T027, T028, T024-T026.
- [X] T035 [US3] Generate `data/derived/sensitivity_analysis.csv` with metrics per threshold.
- [X] T036 [US3] Identify optimal threshold based on the defined optimization rule: maximize `score = runtime_reduction - weight * accuracy_deviation`, where `weight` is a **user-defined parameter** read from a CLI argument or configuration file (default 10). **Dependency**: T035.
- [X] T036a [US3] **Documentation**: Document the justification for the optimization weight mechanism in `docs/research_decisions.md`. **Content**: Explain the formula derivation, how the user-defined weight is passed (CLI/Config), and the trade-off tolerance.
- [X] T037 [US3] Generate final visualization plot (PNG/SVG) in `data/derived/trade_off_curve.png`.
- [X] T038 [US3] Implement Bonferroni correction for multiple comparisons on the **Permutation Test** p-values (from T025) across the discrete threshold set. **Dependency**: T025, T034.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Update `README.md` with execution instructions and environment setup
- [X] T040a [P] Run `black --check` on all Python files to verify formatting
- [X] T040b [P] Resolve all `ruff` warnings to ensure code cleanliness
- [ ] T041 [P] Final verification of all data artifacts in `data/derived/` against `state/manifest.json` (Continuous hook T010 ensures this is mostly done, this is a final sanity check).
- [ ] T042 [P] Add additional unit tests for edge cases (embedding failure, memory limit) in `tests/unit/`
- [ ] T043 Run `quickstart.md` validation (if applicable)
- [ ] T044 Final documentation review for FR-007 (synthetic generator logic) and FR-008 (independence)
- [ ] T047 [P] **Review Concern**: Add task to ensure the `code/analysis/stats.py` handles hit_rate of 0 or [deferred] gracefully.
- [ ] T048 [P] **Review Concern**: Add task to generate a `data/derived/audit_log.json` that records the exact random seed used for every data generation and permutation test run to ensure full reproducibility of the statistical results.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed) **ONLY IF** data dependencies are met (see below)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for the cache mechanism to test.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for the execution logic to sweep thresholds

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Data loaders before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- **IMPORTANT**: User Stories 2 and 3 CANNOT start in parallel with User Story 1 until the Warm-up data generation and Cache Population are complete. The data flow is strictly sequential: T005a -> T016 -> T019 -> T027/T028.

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
 - Developer A: User Story 1 (T014-T019)
 - **WAIT** for T005a and T016 completion before Developer B/C start US2/US3.
 - Developer B: User Story 2 (starts after T016)
 - Developer C: User Story 3 (starts after T027/T028)
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
- **Statistical Methodology**: The Permutation Test and Linear Regression replace McNemar's and t-test per Plan Methodology Section 3 (justified by degeneracy of contingency table).
- **Data Sets**: Two distinct datasets are generated: `synthetic_queries_test.json` and `synthetic_queries_warmup.json`.
- **Independence Check**: Validated via static code inspection in tests/unit/test_independence.py
- **Revision Concerns Addressed**: See comments above for details on how each concern was resolved.