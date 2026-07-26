# Tasks: Semantic Divergence Diagnostic for Agentic Reasoning

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-agent-explor/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-849-llmxive-follow-up-extending-agent-explor/code/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (transformers, rank_bm25, scikit-learn, pandas, datasets, pyyaml)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `src/lib/config.py` with constants, seeds, paths, and memory/timeout limits (FR-007)
- [ ] T005 [P] Create `src/lib/data_loader.py` to load HuggingFace datasets (MathVista/ScienceQA) with streaming support and strict error handling (FR-001, Constitution Principle II)
- [ ] T006 [P] Create `src/lib/tool_loader.py` to load `data/tool_mappings/mathvista_tool_map.json`. **Must verify the loaded mapping is valid and contains at least one entry; halt with "Tool Mapping Missing" error if file is missing or empty** (FR-002)
- [ ] T006b [P] Implement dataset size validation logic in `src/cli/run_diagnostic.py` or a dedicated validator. **Must check the final loaded dataset size N >= 30 (FR-010) after data loading and before correlation/classification. Halt with "Insufficient Sample Size for Power Analysis" if N < 30** (FR-010)
- [ ] T007 [P] Implement `src/lib/axpo_simulator.py` to execute cached AXPO agent simulations for ground-truth failure rates (FR-008)
- [ ] T008 [P] Setup `tests/unit/` and `tests/contract/` directory structure
- [ ] T017 [P] Create `src/cli/run_diagnostic.py` entry point structure. **Must include pre-flight check to verify dataset URL reachability before execution (Constitution Principle II)** (FR-001)
- [ ] T018 [US1] Implement memory monitoring logic for the model to enforce ≤ 7 GB RAM, auto-downsample to a manageable subset of records if exceeded. **Note: Global timeout and hard abort logic is handled in T034a** (FR-007)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Semantic Divergence Metrics (Priority: P1) 🎯 MVP

**Goal**: Implement the core diagnostic to extract thinking traces, retrieve tool distributions via BM25, and calculate the Semantic Divergence Score.

**Independent Test**: The system can be tested by processing a small, fixed set of problems and verifying that the output JSON contains a calculated divergence score for each, derived from the specific embeddings of the thinking prefix and the tool descriptions, without requiring any RL training loops.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for `src/models/divergence_model.py` output schema in `tests/contract/test_schemas.py`
- [ ] T012 [P] [US1] Unit test for BM25 retrieval edge case (zero results) in `tests/unit/test_retrieval.py`
- [X] T013 [P] [US1] Unit test for cosine similarity calculation (orthogonal vectors) in `tests/unit/test_divergence_model.py`

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `src/services/retrieval_service.py` to build BM25 index from tool mappings and retrieve a set of top-ranked descriptions (FR-002, FR-009)
- [ ] T015 [US1] Implement `src/models/divergence_model.py` to encode thinking prefixes and tool centroids using DistilBERT (CPU-only) (FR-003) <!-- FAILED: unspecified -->
- [ ] T016 [US1] Implement logic in `src/models/divergence_model.py` to calculate cosine similarity and `semantic_divergence_score` (1 - similarity) (FR-004)
- [ ] T017 [US1] Implement error handling in `src/models/divergence_model.py` for missing thinking prefixes (skip record) and zero-retrieval (zero vector centroid) (Edge Cases)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlate Divergence with Simulated RL Failure Rates (Priority: P2)

**Goal**: Validate the hypothesis by correlating the computed divergence scores with simulated RL failure rates.

**Independent Test**: The system can be tested by feeding it a synthetic dataset where divergence scores are perfectly negatively correlated with success rates, verifying that the output correlation coefficient demonstrates a strong negative relationship.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for correlation output schema in `tests/contract/test_schemas.py`
- [X] T020 [P] [US2] Integration test for correlation pipeline with synthetic data in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [ ] T021 [US2] Integrate `src/lib/axpo_simulator.py` output (simulated failure rates) with the divergence scores from T015 (US1). **Must execute the simulator and merge the results. [DEPENDS: T015, T007]** (FR-008)
- [ ] T022 [US2] Implement `src/services/analysis_service.py` to perform Pearson correlation test between divergence scores and failure rates (FR-005)
- [ ] T023 [US2] Add statistical power check in `src/services/analysis_service.py` to halt if N < 30 (FR-010, Edge Cases) **[Note: Early check moved to T006b]**
- [ ] T024 [US2] Calculate the Pearson correlation coefficient and p-value. **Determine if the result is statistically significant (p < 0.05)** (SC-001) **[DEPENDS: T022]**
- [ ] T025 [US2] Implement logic to flag "Significant Negative Correlation" based on p-value < 0.05 and append this flag (`significance_flag`: boolean) and `p_value` to the JSON report. **[DEPENDS: T024]** (SC-001)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predict Failure via Logistic Regression (Priority: P3)

**Goal**: Operationalize the diagnostic by training a classifier to predict agent failure from the divergence metric.

**Independent Test**: The system can be tested by running the Logistic Regression on a training subset and verifying that the model achieves an accuracy > 60% on a held-out test set, and that the AUC-ROC is > 0.65.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for classifier output schema in `tests/contract/test_schemas.py`
- [ ] T027 [P] [US3] Unit test for Logistic Regression training on stratified split in `tests/unit/test_analysis_service.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement data splitting logic in `src/services/analysis_service.py` (**stratified train/test split by `problem_type` if available; if `problem_type` is missing, use a random split**). **[DEPENDS: T021]** (FR-006)
- [ ] T029 [US3] Train Logistic Regression classifier using divergence scores to predict binary success/failure (FR-006)
- [ ] T030 [US3] Implement evaluation metrics (Accuracy, Precision, Recall, AUC-ROC) on the held-out test set (SC-002, SC-003)
- [ ] T031 [US3] Generate final report including model metrics and validation status (AUC ≥ 0.65 check) for the held-out test set.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `docs/` and `quickstart.md`. **Ensure `quickstart.md` references T037a for versioning compliance** (Constitution Principle V)
- [ ] T033 Code cleanup and refactoring across `src/`
- [ ] T034a [P] Implement global timeout wrapper in `src/cli/run_diagnostic.py` that enforces a hard time limit and aborts the job with "Timeout Exceeded" error if exceeded (FR-007, SC-004)
- [ ] T035 [P] Additional unit tests for edge cases (empty thinking prefix, missing tool mapping) in `tests/unit/`
- [ ] T036 Security hardening for data loading (URL verification)
- [ ] T037a [P] Implement versioning mechanism to compute content hashes and write them to `state/projects/PROJ-849-llmxive-follow-up-extending-agent-explor.yaml` and trigger `updated_at` timestamp updates (Constitution Principle V)
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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (divergence scores) and AXPO simulation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 output (divergence scores) and US2 data (failure rates)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for output schema in tests/contract/test_schemas.py"
Task: "Unit test for BM25 retrieval edge case in tests/unit/test_retrieval.py"

# Launch all models/services for User Story 1 together:
Task: "Implement retrieval_service.py in src/services/retrieval_service.py"
Task: "Implement divergence_model.py in src/models/divergence_model.py"
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
- **Data Integrity**: Do NOT use synthetic fallbacks for data loading; if real data fetch fails, the system must halt (Constitution Principle II).
- **Compute Feasibility**: All embedding tasks must run on CPU (DistilBERT); if GPU is required for any reason, the task must explicitly state the scaled-down GPU form and rely on the execution stage's auto-offload, but this plan prioritizes CPU-only execution.
- **Dependency Enforcement**: T006b depends on T005. T021 depends on T015 and T007. T028 depends on T021. T034a is a global wrapper.