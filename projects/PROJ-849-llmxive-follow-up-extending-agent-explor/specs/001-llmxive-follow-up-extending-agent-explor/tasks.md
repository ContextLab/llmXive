# Tasks: Semantic Divergence Diagnostic for Agentic Reasoning

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-agent-explor/`
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

- [ ] T001-struct-src Create `projects/PROJ-849-llmxive-follow-up-extending-agent-explor/code/src/` and subdirs (`models/`, `services/`, `lib/`, `cli/`)
- [ ] T001-struct-data Create `data/`, `data/raw/`, `data/tool_mappings/`, `data/cached/`, `results/`, `state/`, `contracts/` directories
- [ ] T001-struct-state Create `state/projects/` directory
- [ ] T001-tests-main Create `tests/`, `tests/unit/`, `tests/contract/`, `tests/integration/` directories
- [ ] T001-tests-subdirs Create `tests/unit/__init__.py` and `tests/contract/__init__.py`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (transformers, rank_bm25, scikit-learn, pandas, datasets, pyyaml)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `src/lib/config.py` with constants, seeds, paths, and basic limits (FR-007, FR-010)
- [ ] T004-ext [P] Implement `src/lib/resource_tracker.py` to enforce a hard timeout (using `signal`/`threading`) and GB memory limit (using `psutil`). **CRITICAL**: You MUST DEFINE the custom exception classes `TimeoutExceededError` and `MemoryLimitExceededError` within this module itself (do not import them from elsewhere). These exceptions will be raised when limits are exceeded. This file is imported by `run_diagnostic.py` and `data_loader.py` (FR-007)
- [ ] T004-integration [P] Implement `src/cli/run_diagnostic.py` entry point wrapper that imports `resource_tracker` and **wraps the main execution loop** in a context manager or decorator to **actively enforce** the Timeout duration of hours and 7 GB memory limits. **Must implement error reporting**: on timeout/memory limit, write a specific error message "Timeout Exceeded" or "Memory Limit Exceeded" to `results/error_log.txt` and update `state/projects/PROJ-849-llmxive-follow-up-extending-agent-explor.yaml` with the error code before exiting. (FR-007)
- [ ] T005 [P] Create `src/lib/data_loader.py` with strict real-data fetch logic: HEAD request pre-check for URLs, `ERR_DATASET_UNREACHABLE` halt on failure, NO synthetic fallback. **Must implement**: Load a substantial number of records. **For local files**: use chunked loading (e.g., `pandas.read_json(..., lines=True, chunksize=...)` or `datasets.load_dataset(..., streaming=True)`). If memory usage > 7GB during load, downsample to a subset of records using `itertools.islice` on the chunked iterator with a fixed seed. (FR-001, FR-007, Constitution Principle II)
- [ ] T005-ext [P] Extend `src/lib/data_loader.py` to explicitly extract, parse, and validate the 'problem_type' attribute from `record['metadata']['problem_type']` or `record['problem_type']`. **CRITICAL**: If the field is missing/null, skip the record and log `ERR_STRATIFICATION_FIELD_MISSING` using `logging.error()` with format `[ERROR] ERR_STRATIFICATION_FIELD_MISSING: {problem_id or record_index}`. **Do not halt here**; simply filter the record. (US-3, FR-010, Constitution Principle II)
- [ ] T006 [P] Create `src/lib/tool_mapper.py` to load `data/tool_mappings/mathvista_tool_map.json`, extract the 'tool_descriptions' list for each problem, and raise `ERR_TOOL_MAPPING_MISSING` if the file or problem ID is absent (FR-002, FR-009)
- [ ] T008-prep [P] Attempt to fetch `data/cached_axpo_results.json` from a verified remote source (if available). If not available, this task fails loudly, requiring T008-sim-wrapper or T008-exec-axpo to run first. (FR-008)
- [ ] T008-sim-wrapper [P] Implement `code/scripts/run_axpo_simulation.py` to generate ground-truth outcomes if the original AXPO agent is missing. **Logic**: For each problem, simulate success/failure deterministically: if `metadata.problem_difficulty` exists, use it; else use `hash(problem_id) % 2` to determine failure. Output `data/cached_axpo_results.json` with schema `{'problem_id': str, 'simulated_failure': bool, 'failure_reason': str}`. (FR-008, US-2, US-3)
- [ ] T008-exec-axpo [P] Execute the original AXPO agent script (if present in repo) on the target problem subset to generate ground-truth outcomes. Output MUST be written to `data/cached_axpo_results.json`. If the original agent is missing, this task is skipped and T008-sim-wrapper is used. (FR-008, US-2, US-3)
- [ ] T008-impl-cache Implement `src/lib/simulation_runner.py` to load `data/cached_axpo_results.json` generated by T008-sim-wrapper or T008-exec-axpo (or T008-prep if fetched). **CRITICAL**: Perform a pre-flight check to ensure the file exists and is non-empty. If missing or empty, raise `ERR_NO_SIMULATION_DATA` and halt. **Do not generate synthetic data**. Validate schema (`problem_id`, `simulated_failure`). Store in memory for downstream tasks. **This task MUST run AFTER T008-exec-axpo or T008-sim-wrapper completes; it cannot run in parallel with them.** (FR-008, US-2, US-3)
- [ ] T008-impl-schema [P] Define the data schema for `simulated_failure_rate` (e.g., `{'problem_id': str, 'simulated_failure': bool, 'failure_reason': str}`) in `src/lib/simulation_runner.py` or a dedicated schema file, ensuring it generates ground-truth outcomes for US2/US3 (FR-008, US-2, US-3)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Semantic Divergence Metrics (Priority: P1) 🎯 MVP

**Goal**: Compute the "Semantic Divergence Score" for a static subset of problems using BM25 retrieval and DistilBERT embeddings.

**Independent Test**: The system processes a fixed set of problems and outputs a JSON with `thinking_embedding`, `tool_centroid_embedding`, `cosine_similarity`, and `semantic_divergence_score` without RL loops.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for divergence output schema in `tests/contract/test_divergence_schema.py`
- [X] T011 [P] [US1] Unit test for zero-retrieval edge case (returns zero vector, score=1.0) in `tests/unit/test_retrieval.py`
- [X] T012 [P] [US1] Unit test for synthetic orthogonal inputs (similarity ≤ 0.05) in `tests/unit/test_metrics.py`
- [X] T013 [P] [US1] Unit test for synthetic identical inputs (similarity ≥ 0.99) in `tests/unit/test_metrics.py`

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `src/services/retrieval_service.py`: Build BM25 index from tool descriptions **using the loaded data from T006 (`src/lib/tool_mapper.py`)**. **Input**: `corpus` (list of lists of strings, where each inner list is the tool descriptions for a problem). **Logic**: Retrieve **up to 10** (`top_k=10`) plausible tool descriptions per problem. Handle empty results (return empty list). (FR-002, FR-009)
- [ ] T015 [US1] Implement `src/models/divergence_model.py`: Load DistilBERT, encode thinking prefix, **compute centroid of retrieved tool descriptions** (from T014), calculate cosine similarity. **Input**: thinking string, list of retrieved tool descriptions. **Dependency**: Must run AFTER T014 completes. (FR-003, FR-004)
- [ ] T016 [US1] Implement `src/cli/run_diagnostic.py` entry point: Orchestrate loading, retrieval, and scoring for the full dataset. **Must import and wrap execution with `resource_tracker` from T004-ext** (FR-001)
- [ ] T017 [US1] Add error handling for missing "thinking" prefix (skip record, log error code `ERR_MISSING_THINKING`). **Note**: The N ≥ 30 check is handled in T024-verify (FR-010)
- [ ] T018 [US1] Add logging for retrieval stats (number of tools retrieved per problem) and embedding dimensions

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlate Divergence with Simulated RL Failure Rates (Priority: P2)

**Goal**: Correlate computed divergence scores with simulated RL failure rates to validate the "thinking-acting gap" hypothesis.

**Independent Test**: The system outputs a Pearson correlation coefficient and p-value, flagging significant negative correlations.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for correlation output schema in `tests/contract/test_correlation_schema.py`
- [X] T020 [P] [US2] Unit test for random data (p-value > 0.05) in `tests/unit/test_analysis.py`
- [X] T021 [P] [US2] Unit test for strong negative correlation detection in `tests/unit/test_analysis.py`

### Implementation for User Story 2

- [ ] T022 [US2] Extend `src/lib/simulation_runner.py` to **load** `simulated_failure_rate` from `data/cached_axpo_results.json` (generated by **T008-impl-cache**). Do not attempt to generate outcomes dynamically. Merge with divergence scores. **Depends on T008-impl-cache**
- [ ] T023 [US2] Implement `src/services/analysis_service.py`: Merge divergence scores with failure rates, perform Pearson correlation test. **Depends on T016/T017**
- [ ] T024 [US2] Add logic to check sample size N ≥ 30 before correlation; raise "Statistical Power Insufficient" if N < 30 (FR-010)
- [ ] T024-verify [US2] Add explicit check to verify that the dataset size **after** T017 and T005-ext filtering is ≥ 30. **Input**: Read the filtered dataset from `state/intermediate/filtered_dataset.json` (produced by T017/T005-ext). If N < 30, halt execution with "Insufficient Sample Size for Power Analysis" error. **Depends on T005-ext, T017** (FR-010)
- [ ] T025 [US2] Add logic to flag "Significant Negative Correlation" if p < 0.05 and correlation < 0 (SC-001)
- [ ] T026 [US2] Integrate US1 and US2 in `run_diagnostic.py` to produce a combined report

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predict Failure via Logistic Regression (Priority: P3)

**Goal**: Train a Logistic Regression classifier to predict RL failure based on semantic divergence metrics.

**Independent Test**: The model achieves accuracy > 60% and AUC-ROC ≥ 0.65 on a held-out test set.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for classifier output schema in `tests/contract/test_classifier_schema.py`
- [ ] T028 [P] [US3] Unit test for stratified train/test split logic in `tests/unit/test_analysis.py`
- [ ] T029 [P] [US3] Unit test for AUC-ROC threshold validation in `tests/unit/test_analysis.py`

### Implementation for User Story 3

- [ ] T030 [US3] Extend `src/services/analysis_service.py` to split data (stratified by **problem_type extracted in T005-ext**) into train/test sets. **Logic**: If `problem_type` is missing for a record, skip it for stratification (log warning) and fall back to a simple random split for that record using `train_test_split(..., random_state=42, shuffle=True)`. **Depends on T005-ext**
- [ ] T031 [US3] Implement Logistic Regression training using `scikit-learn` on divergence scores to predict binary failure. **Depends on T023**
- [ ] T032 [US3] Add evaluation logic: Calculate accuracy, precision, recall, and AUC-ROC on the test set (SC-002, SC-003)
- [ ] T032-schema [US3] Create `contracts/output_schema.yaml` defining the exact schema for `results/classifier_metrics.json` with top-level keys `train` and `test`, each containing `accuracy`, `precision`, `recall`, `auc`. (SC-002)
- [ ] T032-verify [US3] Add logic to verify/assert that the accuracy > 60% threshold is met as part of the success validation (SC-002)
- [ ] T032-persist [US3] Implement mechanism to **persist and report** accuracy, precision, recall, and AUC-ROC for the **held-out test set separately** from training metrics in `results/classifier_metrics.json`. **Must conform to schema in `contracts/output_schema.yaml`** (SC-002)
- [ ] T033 [US3] Implement prediction function: Given a new divergence score, return predicted outcome and probability
- [ ] T034 [US3] Integrate US3 into `run_diagnostic.py` to output full model metrics and save the trained model artifact

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] (Removed: Logic moved to T004-ext/T005) Memory limit enforcement and downsampling logic are now handled in Foundational phase
- [ ] T036 [P] (Removed: Logic moved to T004-ext/T005) Dynamic downsampling logic is now handled in Foundational phase
- [ ] T037 [P] Generate content hashes for raw data and derived artifacts using SHA. Update `state/projects/PROJ-849-llmxive-follow-up-extending-agent-explor.yaml` under the key `artifact_hashes` with the exact file paths and format: `filename: <sha256_hash>`. Files to hash: `data/raw/*.json`, `data/cached_axpo_results.json`, `results/*.json`. (Constitution Principle V)
- [ ] T038 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T039 Code cleanup and refactoring
- [ ] T040 Run `run_diagnostic.py` validation on a small subset to verify end-to-end flow

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 outputs (divergence scores) and simulation data (T008-impl-cache)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US1 and US2 data (scores + outcomes) and problem type extraction (T005-ext)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Services before CLI integration
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), EXCEPT T008-impl-cache which must run sequentially after T008-exec-axpo or T008-sim-wrapper
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Critical Dependency Chains (Explicit Ordering)

- **T024-verify** MUST run AFTER **T005-ext** and **T017** (Filtering must complete before sample size check).
- **T008-exec-axpo** or **T008-sim-wrapper** MUST run BEFORE **T008-impl-cache** (Ground truth generation before loading). **T008-impl-cache is NOT [P]**.
- **T014** MUST run BEFORE **T015** (Retrieval before Embedding). **T015 is NOT [P]**.
- **T016/T017** MUST run BEFORE **T023** (US1 completion before US2 analysis).
- **T023** MUST run BEFORE **T031** (Data preparation before Model Training).
- **T008-impl-cache** MUST run AFTER **T008-exec-axpo** or **T008-sim-wrapper** and BEFORE **T022** (Simulation data must exist before US2 consumption).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for divergence output schema in tests/contract/test_divergence_schema.py"
Task: "Unit test for zero-retrieval edge case in tests/unit/test_retrieval.py"

# Launch all models/services for User Story 1 together:
Task: "Implement retrieval_service.py"
# Note: T015 depends on T014, so run sequentially or ensure T014 completes first
Task: "Implement divergence_model.py"
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

- [P] tasks = different files, no dependencies (EXCEPT T008-impl-cache which is sequential)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Data Rule**: All data loading tasks MUST fail loudly on real data fetch errors; NO synthetic fallbacks allowed.
- **Compute Rule**: Use CPU-first (DistilBERT) for embeddings; only use GPU if absolutely necessary for the specific model type (not applicable here as per spec).
- **Data Flow Rule**: T008-exec-axpo or T008-sim-wrapper (producer) must precede T008-impl-cache (consumer); T008-impl-cache (producer) must precede T022 (consumer); T005-ext (producer) must precede T030 (consumer); T006 (producer) must precede T014 (consumer).
- **Constraint Rule**: T004-ext implements the hard timeout and memory limit in `src/lib/resource_tracker.py`.
- **Reporting Rule**: T032-persist ensures held-out test metrics are reported separately and conform to `contracts/output_schema.yaml`.
- **Threshold Rule**: T032-verify ensures the 60% accuracy threshold is explicitly checked.
- **Simulation Rule**: T008-exec-axpo or T008-sim-wrapper executes the AXPO agent/simulation to generate ground truth; T008-impl-cache strictly loads this data.
- **Integration Rule**: T004-integration ensures `resource_tracker` is invoked in the main flow to enforce limits.
- **Verification Rule**: T024-verify ensures N >= 30 is checked after all filtering steps (T005-ext, T017).
- **Ordering Rule**: Tasks marked [P] MUST NOT have explicit dependencies on other tasks in the same phase. Dependencies like T015->T014 are removed from [P] tags. T008-impl-cache is NOT [P].