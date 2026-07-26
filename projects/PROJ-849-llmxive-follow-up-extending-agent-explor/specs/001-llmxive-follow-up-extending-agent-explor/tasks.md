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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-849-llmxive-follow-up-extending-agent-explor/code/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (transformers, rank_bm25, scikit-learn, pandas, datasets, pyyaml)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `src/lib/config.py` with constants, seeds, paths, and memory/time limits (FR-007, FR-010)
- [ ] T004-ext [P] Implement 5-hour hard timeout logic in `src/lib/config.py` or `src/cli/run_diagnostic.py` using `signal` module or `timeout` decorators to enforce FR-007 abort behavior (FR-007)
- [ ] T005 [P] Create `src/lib/data_loader.py` with strict real-data fetch logic: HEAD request pre-check, `ERR_DATASET_UNREACHABLE` halt on failure, NO synthetic fallback (FR-001, Constitution Principle II)
- [ ] T005-ext [P] Extend `src/lib/data_loader.py` to explicitly extract, parse, and validate the 'problem_type' attribute from the raw dataset fields (e.g., `dataset["problem_type"]`) and raise `ValueError` if null for stratification use (US-3, FR-010)
- [ ] T006 [P] Create `src/lib/tool_mapper.py` to load `data/tool_mappings/mathvista_tool_map.json`, extract the 'tool_descriptions' list for each problem, and raise `ERR_TOOL_MAPPING_MISSING` if absent (FR-002, FR-009)
- [ ] T007 [P] Implement `src/lib/metrics.py` with cosine similarity and zero-vector handling logic (FR-003, FR-004)
- [ ] T008 [P] Setup `tests/unit/` and `tests/contract/` directory structure with schema validation utilities
- [ ] T008-impl-schema [P] Define the data schema for `simulated_failure_rate` (e.g., `{'problem_id': str, 'simulated_failure': bool, 'failure_reason': str}`) in `src/lib/simulation_runner.py` or a dedicated schema file, ensuring it generates ground-truth outcomes for US2/US3 (FR-008, US-2, US-3)
- [ ] T008-impl-axpo [P] Implement `src/services/axpo_simulator.py` to execute the original AXPO agent (or load cached simulation) on the problem subset; explicitly implement the `run()` method to generate ground-truth outcomes and store them as `simulated_failure_rate` (FR-008, US-2, US-3)

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

- [ ] T014 [US1] Implement `src/services/retrieval_service.py`: Build BM25 index from tool descriptions **using the loaded data from T006 (`src/lib/tool_mapper.py`)**, retrieve top-ranked, handle empty results (FR-002, FR-009)
- [ ] T015 [US1] Implement `src/models/divergence_model.py`: Load DistilBERT, encode thinking prefix, calculate cosine similarity (FR-003, FR-004) <!-- FAILED: unspecified -->
- [ ] T015-compute-centroid [US1] Implement logic to embed the retrieved tool descriptions (from T014) and compute the centroid vector using the SAME encoder as the thinking prefix; consume `retrieved_tool_descriptions` from T014 (FR-003)
- [ ] T016-limit [US1] Implement logic in `src/lib/data_loader.py` or `src/cli/run_diagnostic.py` to limit the dataset to 500 records if the source contains more, as required by FR-001 (FR-001)
- [ ] T016 [US1] Implement `src/cli/run_diagnostic.py` entry point: Orchestrate loading, retrieval, and scoring for the full dataset (FR-001)
- [ ] T017-n-check [US1] Add error handling for missing "thinking" prefix (skip record, log error code `ERR_MISSING_THINKING`) and enforce N ≥ 30 check with specific error message "Insufficient Sample Size for Power Analysis" raising a specific exception to halt execution (FR-010)
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

- [ ] T022 [P] [US2] Extend `src/lib/simulation_runner.py` (referencing **T008-impl-axpo**) to generate or load `simulated_failure_rate` for the subset by calling `axpo_simulator.run()` or loading from `results/cached_simulations.json` using the **defined schema from T008-impl-schema** (FR-008, US-2) <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [ ] T023 [US2] Implement `src/services/analysis_service.py`: Merge divergence scores with failure rates, perform Pearson correlation test (FR-005)
- [ ] T024 [US2] Add logic to check sample size N ≥ 30 before correlation; raise "Statistical Power Insufficient" if N < 30 (FR-010)
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

- [ ] T030 [P] [US3] Extend `src/services/analysis_service.py` to split data (stratified by **problem_type extracted in T005-ext**) into train/test sets (FR-006, US-3)
- [ ] T031 [US3] Implement Logistic Regression training using `scikit-learn` on divergence scores to predict binary failure (FR-006)
- [ ] T032 [US3] Add evaluation logic: Calculate accuracy, precision, recall, and AUC-ROC on the test set (SC-002, SC-003)
- [ ] T032-verify [US3] Add logic to verify/assert that the accuracy > 60% threshold is met as part of the success validation (SC-002)
- [ ] T032-persist [US3] Implement mechanism to **persist and report** accuracy, precision, recall, and AUC-ROC for the **held-out test set separately** from training metrics in `results/classifier_metrics.json` (SC-002)
- [ ] T033 [US3] Implement prediction function: Given a new divergence score, return predicted outcome and probability
- [ ] T034 [US3] Integrate US3 into `run_diagnostic.py` to output full model metrics and save the trained model artifact

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Enforce memory limit (≤ 7 GB) in `run_diagnostic.py` with graceful abort (FR-007)
- [ ] T036 [P] Add dataset downsampling logic: if N > 500 or memory > 7GB, automatically downsample the dataset to 300 records (FR-007)
- [ ] T037 [P] Generate content hashes for raw data and derived artifacts, updating `state/projects/PROJ-849-llmxive-follow-up-extending-agent-explor.yaml` (Constitution Principle V)
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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 outputs (divergence scores) and simulation data (T008-impl-axpo)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US1 and US2 data (scores + outcomes) and problem type extraction (T005-ext)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Services before CLI integration
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
Task: "Contract test for divergence output schema in tests/contract/test_divergence_schema.py"
Task: "Unit test for zero-retrieval edge case in tests/unit/test_retrieval.py"

# Launch all models/services for User Story 1 together:
Task: "Implement retrieval_service.py"
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

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Data Rule**: All data loading tasks MUST fail loudly on real data fetch errors; NO synthetic fallbacks allowed.
- **Compute Rule**: Use CPU-first (DistilBERT) for embeddings; only use GPU if absolutely necessary for the specific model type (not applicable here as per spec).
- **Data Flow Rule**: T008-impl-axpo (producer) must precede T022 (consumer); T005-ext (producer) must precede T030 (consumer); T006 (producer) must precede T014 (consumer).
- **Constraint Rule**: T004-ext implements the hard timeout for FR-007 in Foundational phase.
- **Reporting Rule**: T032-persist ensures held-out test metrics are reported separately.
- **Threshold Rule**: T032-verify ensures the 60% accuracy threshold is explicitly checked.