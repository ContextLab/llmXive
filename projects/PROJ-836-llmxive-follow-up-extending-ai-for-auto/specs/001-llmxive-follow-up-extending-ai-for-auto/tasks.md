# Tasks: llmXive follow-up: extending "AI for Auto-Research: Roadmap & User Guide"

**Input**: Design documents from `/specs/001-llmxive-followup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001a [P] Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `tests/unit/`, `tests/integration/`, `config/`, `output/`
- [X] T001b [P] Initialize `code/requirements.txt` with dependencies: `networkx`, `scikit-learn`, `spacy`, `sentence-transformers`, `pandas`, `numpy`, `scipy`, `pytest`, `requests`, `pydantic`
- [X] T001c [P] Initialize `tests/conftest.py` with base fixtures for pytest

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/data_ingestion.py` to download the "AI for Auto-Research" benchmark dataset from the source specified in `config/dataset_source.json`, perform SHA-256 checksum validation against `data/checksums.json`, and run PII scan via `repo-hygiene scan --pii` command. **FAIL LOUDLY** if download fails; do not use synthetic fallback.
- [X] T004a [P] Implement `code/config/dataset_source.json` population logic: Create a script to populate `config/dataset_source.json` with the verified dataset ID and URL after Phase 0 research verification. Implement `code/data_ingestion.py` to read this config.
- [ ] T004b [P] Implement `code/data_ingestion.py` logic to fetch and validate the external experimental outcome metadata (e.g., `labels.json` or `metadata.csv` containing ground-truth failure labels) from the verified real source. Validate that the metadata schema includes 'label' and 'source_type' fields. **FAIL LOUDLY** if metadata is missing or invalid.
- [ ] T005 [P] Implement `code/versioning_manager.py` to compute content hashes for all artifacts and update `state/` YAML file after each pipeline phase.
- [ ] T006 [P] [P] Setup `tests/unit/` and `tests/integration/` directory structures and base `pytest` configuration.
- [ ] T006a [P] Implement `code/config/permutation_config.json` to store the calculated permutation budget (minimum threshold based on statistical sufficiency, maximum based on 6h runtime). Include a script to calculate this based on dataset size (constant `avg_time` = 1.0s per permutation for initial calculation).
- [ ] T007a [P] Implement function `extract_triplets(text: str) -> List[Triplet]` in `code/graph_construction.py` that returns an empty list for empty input.
- [ ] T007b [P] Implement function `build_graph(triplets: List[Triplet]) -> nx.DiGraph` in `code/graph_construction.py` that merges duplicate nodes.
- [ ] T007c [P] Implement function `validate_triplets(triplets: List[Triplet], source_text: str) -> List[Triplet]` in `code/graph_construction.py` using fuzzy matching to confirm "citation isolation" reflects genuine lack of grounding (Constitution Principle VI).
- [ ] T008 [P] Implement `code/metric_engine.py` skeleton with stub functions for cycle density, isolation ratio, and semantic distance, including logging for default values (0.0) on empty graphs.
- [ ] T009 [P] Implement `code/model_training.py` skeleton with Logistic Regression and Random Forest class wrappers, ensuring CPU-only execution flags.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Graph Construction and Metric Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest benchmark logs, parse literature reviews, extract entity-relation triplets, construct directed graphs, and compute topological metrics (cycle density, citation isolation, semantic distance).

**Independent Test**: Run extraction on a known subset of benchmark data; verify output CSV contains correct columns, non-null values, and values within mathematical bounds.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for graph construction on empty/short text in `tests/unit/test_graph_construction.py` (verify default 0.0 metrics and warning logs).
- [ ] T011 [P] [US1] Unit test for cycle density calculation in `tests/unit/test_metric_engine.py` (verify float range 0.0–1.0).
- [ ] T012 [P] [US1] Unit test for citation isolation logic in `tests/unit/test_metric_engine.py` (verify nodes with zero external incoming edges are scored).
- [ ] T013 [US1] Integration test for full graph construction pipeline on sample data in `tests/integration/test_us1_pipeline.py`. (Note: Depends on code implementation (T014-T020), not unit test artifacts. Can run in parallel with unit tests if code is ready).

### Implementation for User Story 1

- [ ] T014 [US1] Implement full triplet extraction logic in `code/graph_construction.py` using spaCy.
- [ ] T014a [US1] Implement fuzzy-matching validation step in `code/graph_construction.py` to cross-reference extracted triplets against source text, confirming "citation isolation" reflects genuine lack of grounding (Constitution Principle VI).
- [ ] T015 [US1] Implement `code/graph_construction.py` directed graph construction logic (nodes: concepts, edges: claims) from extracted triplets.
- [ ] T016 [US1] Implement cycle density calculation in `code/metric_engine.py` (ratio of actual cycles to max possible).
- [ ] T017 [US1] Implement citation isolation metric in `code/metric_engine.py` (degree centrality of nodes with no external incoming edges).
- [ ] T018 [US1] Implement semantic distance calculation in `code/metric_engine.py` using `all-MiniLM-L6-v2` (mean pairwise cosine distance within component).
- [ ] T019 [US1] Add error handling in `code/metric_engine.py` to assign default 0.0 values and log warnings for empty/short inputs (FR-008).
- [ ] T020 [US1] Create `code/main.py` orchestration step to run data ingestion, graph construction, and metric extraction, outputting `data/processed/feature_matrix.csv`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Model Training and Evaluation (Priority: P2)

**Goal**: Train an interpretable classifier (Logistic Regression) using topological metrics, evaluate via 5-fold cross-validation, and report AUC and coefficients.

**Independent Test**: Train model on processed dataset; verify cross-validation AUC is reported, model coefficients are non-zero (or null result reported), and no dimension mismatch errors occur.

### Tests for User Story 2

- [ ] T021 [P] [US2] Unit test for Logistic Regression training on sample matrix in `tests/unit/test_model_training.py` (verify convergence and coefficient output).
- [ ] T022 [P] [US2] Unit test for 5-fold cross-validation logic in `tests/unit/test_model_training.py` (verify AUC calculation and standard deviation).
- [ ] T023 [P] [US2] Integration test for model training and evaluation pipeline in `tests/integration/test_us2_pipeline.py`.

### Implementation for User Story 2

- [ ] T024a [US2] Implement programmatic verification of ground-truth label derivation in `code/model_training.py` to ensure labels are derived from external experimental outcomes (e.g., wet-lab results) by checking the 'source_type' field in the metadata validated by T004b.
- [ ] T024b [US2] Implement data mapping logic in `code/model_training.py` to join feature matrix with verified ground-truth binary failure labels, excluding entries with missing labels (FR-007).
- [ ] T025 [US2] Implement Logistic Regression training in `code/model_training.py` with CPU-only configuration; implement Random Forest fallback if LR fails to converge (FR-004).
- [ ] T026 [US2] Implement 5-fold cross-validation in `code/model_training.py` and calculate Area Under the Curve (AUC) score (FR-005).
- [ ] T027 [US2] Implement feature importance extraction: report LR coefficients or RF SHAP values for all topological metrics (FR-004).
- [ ] T028 [US2] Implement reporting logic in `code/model_training.py` to compare observed AUC against baseline 0.5 (SC-001) and reference the results of T024a for label derivation verification (FR-009).
- [ ] T029 [US2] Implement reporting logic in `code/model_training.py` to check if the 'hallucination' label column exists in the validated metadata (from T004b). If missing, generate the limitation statement regarding "citation isolation" as a hallucination proxy; otherwise, omit it (FR-010).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance Verification (Priority: P3)

**Goal**: Perform a permutation test to verify that the observed correlation between graph metrics and failure labels is not due to chance.

**Independent Test**: Run permutation test; verify p-value is calculated, null hypothesis distribution is generated, and significance is reported.

### Tests for User Story 3

- [ ] T030 [P] [US3] Unit test for permutation test logic in `tests/unit/test_model_training.py` (verify label shuffling and null distribution generation).
- [ ] T031 [P] [US3] Integration test for statistical significance verification in `tests/integration/test_us3_pipeline.py`.

### Implementation for User Story 3

- [ ] T031a [US3] Implement logic in `code/model_training.py` to determine the number of permutations: `permutations = max(minimum_threshold, min(calculated_budget, max_allowed))`. Use `avg_time` = 1.0s (constant) for the initial calculation, or use the value from T006a if available.
- [ ] T032 [US3] Implement permutation test in `code/model_training.py` using the iteration count calculated in T031a to generate the null distribution of AUC scores (FR-006).
- [ ] T033 [US3] Implement p-value calculation logic comparing observed AUC against the null distribution (SC-002).
- [ ] T034 [US3] Update final report generation to explicitly compare p-value and observed AUC, stating statistical significance (FR-006, SC-002).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Run full pipeline end-to-end on the full benchmark dataset to verify CPU feasibility within 6 hours (SC-003).
- [ ] T036 [P] Verify data completeness: ensure all graphs have valid metric values (no NaNs) and are mapped to labels, explicitly preserving the count of graphs with default 0.0 values in the completeness metric (SC-005).
- [ ] T037 [P] Update `quickstart.md` with instructions for running the full pipeline and interpreting results. Run validation to ensure all metadata schema checks (T004a/T004b) pass.
- [ ] T038 [P] Run quickstart.md validation and ensure all citations in `research.md` pass the Metadata Schema Validator check (replacing Reference-Validator Agent check).
- [ ] T039 [P] Final code cleanup, refactoring, and documentation updates.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T004a must complete before T004 (data ingestion) to provide the dataset source config.
 - T004b must complete before T024a (Phase 4) to provide the verified external label source.
 - T006a must complete before T031a (Phase 5) to provide the permutation budget.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (feature matrix) and T004b (label verification)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (model results) and T006a (budget calculation)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion and graph construction before metric calculation
- Metric calculation before model training
- Model training before statistical verification
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004a, T004b, T006a, T007a, T007b, T007c, T006) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for graph construction on empty/short text in tests/unit/test_graph_construction.py"
Task: "Unit test for cycle density calculation in tests/unit/test_metric_engine.py"

# Launch all models for User Story 1 together:
Task: "Implement triplet extraction logic in code/graph_construction.py"
Task: "Implement directed graph construction logic in code/graph_construction.py"
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
- **Data Hygiene**: All data loaders must FAIL LOUDLY on real fetch errors; no synthetic fallbacks allowed.
- **CPU Feasibility**: Ensure all models and datasets are scaled to fit CPU-only runner constraints (≤7 GB RAM, ≤6 h). [UNRESOLVED-CLAIM: c_24549edb — status=not_enough_info]
- **Constitution Compliance**: T004a ensures Metadata Schema Validation; T014a ensures triplet validation; T024a ensures label source verification; T031a ensures dynamic budgeting with a hard floor.
- **Statistical Integrity**: Permutation tests must enforce a minimum of 1000 iterations to ensure statistical power (SC-002).
- **Conditional Reporting**: Limitation statements must be generated only when ground-truth data is missing (T029).