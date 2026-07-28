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

- [ ] T001a [P] Create project directory structure: `mkdir -p src/data src/models src/analysis src/cli src/lib data/raw data/processed results tests/unit tests/integration tests/contract`
- [X] T001b [P] Initialize Python 3.11 project with `requirements.txt` pinning `ir-datasets`, `sentence-transformers`, `faiss-cpu`, `rank_bm25`, `scikit-learn`, `pandas`, `numpy`, `psutil`, `transformers`, `torch`, `accelerate`, `pytest`
- [X] T001c [P] Create `.gitignore` and `setup.cfg` for project configuration
- [ ] T002 [P] Configure linting (`ruff`) and formatting (`black`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Implement `src/lib/utils.py` with functions for: fixed random seed setting, tokenization logic (256-token truncation), ASCII stripping, and logging setup
- [ ] T004 [P] Implement `src/data/checksum.py` for raw data hash verification and state file management
- [ ] T005 Create `src/data/models.py` defining `CodeSnippet`, `QueryResult`, and `PerformanceDelta` dataclasses with exact schema alignment to spec
- [ ] T006 Implement `src/data/download.py` using `ir_datasets.load("codesearchnet")` to fetch Python/Java subsets; MUST raise on failure, NO synthetic fallback
- [ ] T007 Implement `src/data/preprocess.py` to load raw data, strip non-ASCII, truncate to 256 tokens, and save processed JSONL/CSV to `data/processed/`
- [ ] T008 [P] Configure `pytest` environment with `conftest.py` for shared fixtures (mocked data paths, temp directories)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible RAG vs. Baseline Evaluation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Build the end-to-end pipeline that downloads CodeSearchNet, runs BM, Dual-Encoder, and RAG retrieval on a set of queries, and outputs nDCG@k/Precision@k metrics in a CSV.

**Independent Test**: The system can be tested by executing the pipeline on a subset of CodeSearchNet queries and verifying that it outputs a CSV file containing three distinct rows (one per method) with valid nDCG@K scores, without requiring any external API calls or GPU resources.

### Implementation for User Story 1

- [ ] T009 [P] [US1] Implement `src/models/retriever_bm25.py` using `rank_bm25` on preprocessed data
- [ ] T010 [P] [US1] Implement `src/models/retriever_neural.py` using `sentence-transformers/all-MiniLM-L6-v2` for dual-encoder retrieval
- [ ] T011 [US1] Implement `src/models/rag_pipeline.py` using `Salesforce/codegen-350M-mono` (CPU mode) with fixed prompt template, temp=0.0, top-k retrieval. MUST include fallback logic to `microsoft/phi-1.5` if the primary model fails to load within 7GB RAM, using 4-bit quantization and `device_map="cpu"` for the fallback to ensure deterministic behavior.
- [ ] T012 [US1] Implement `src/models/metrics.py` to calculate Precision@K, Recall@K, and nDCG@K against ground truth labels
- [ ] T013 [US1] Implement `src/cli/main.py` to orchestrate the multiple methods on 50 queries, handle edge cases (zero matches, truncation warnings), and output `results.csv`
- [ ] T014 [US1] Add deterministic seed enforcement and reproducibility checks in `src/cli/main.py`
- [ ] T015 [US1] Implement memory monitoring in `src/models/rag_pipeline.py` using `psutil` to ensure <7GB RAM usage

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation to verify the pipeline**

- [ ] T016 [P] [US1] Contract test for CSV output schema in `tests/contract/test_output_schema.py`
- [ ] T017 [P] [US1] Integration test for full pipeline execution on 50 queries in `tests/integration/test_pipeline_e2e.py`
- [ ] T018 [P] [US1] Unit test for nDCG calculation logic

The research question is to evaluate the ranking effectiveness of the proposed algorithm. The method involves computing the normalized discounted cumulative gain at a standard cutoff depth. This approach aligns with established retrieval evaluation protocols [DOI:10.1145/1321440.1321442]. in `tests/unit/test_metrics.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Semantic Descriptor Correlation Analysis (Priority: P2)

**Goal**: Compute semantic descriptors (API density, doc density, naming consistency) for test set queries and ground truth snippets and correlate them with performance deltas using Spearman/Pearson tests.

**Independent Test**: The system can be tested by feeding it a pre-computed CSV of performance deltas and code descriptors, verifying that it outputs a JSON report containing Spearman correlation coefficients and p-values for each descriptor against the performance delta.

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `src/data/descriptors.py` to calculate API density, doc density, and Naming-consistency score (using `CodeBERT-base` embeddings) ONLY for test set queries and their ground truth snippets (as defined by T013). MUST NOT compute for retrieved snippets to avoid circularity and ensure CPU feasibility.
- [ ] T020 [US2] Implement `src/analysis/correlation.py` to compute Spearman's rho and Pearson's r. MUST perform a normality test (Shapiro-Wilk) to select between paired t-test and Wilcoxon signed-rank test. MUST format the final `correlation_results.json` and `results.csv` to explicitly flag correlations with p < 0.05 as "statistically significant" and others as "non-significant".
- [ ] T021 [US2] Implement `src/data/masking.py` to implement token masking logic (regex/token-level replacement) for API and documentation tokens as required by FR-009. Explicitly reference FR-009 in the docstring.
- [ ] T022 [US2] Implement `src/analysis/control_experiment.py` to consume masked data generated by `src/data/masking.py`, re-run correlation analysis, and compare results against the unmasked baseline (output of T020) to verify correlations are not artifacts (FR-009). Explicitly reference FR-009 in the docstring.
- [ ] T023 [US2] Implement `src/data/report_generator.py` to generate a CSV report of random samples for HUMAN manual review of ground truth labels (FR-010).
- [ ] T023a [US2] **HUMAN TASK**: Perform Manual Spot-Check. A human must review the CSV generated by T023, estimate the label noise rate, and save the result to `results/manual_noise_input.json` with the format `{"noise_estimate": <estimated_value>}`.
- [ ] T023b [US2] Implement `src/analysis/noise_recorder.py` to load the human-estimated noise rate from `results/manual_noise_input.json` (produced by T023a) and record it in `results/label_noise_estimate.json` (FR-010).
- [ ] T025 [US2] Update `src/cli/main.py` to trigger descriptor calculation and correlation analysis after retrieval, outputting `correlation_results.json`.
- [ ] T026 [US2] Ensure `src/data/descriptors.py` handles `NaN` gracefully and excludes invalid points from correlation while retaining them for retrieval metrics

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Resource Constraint Degradation Study (Priority: P3)

**Goal**: Run the pipeline with strict resource limits (1GB FAISS index, 2-layer model) and generate a degradation report comparing results to the standard run.

**Independent Test**: The system can be tested by running the pipeline with the "strict resource" flags enabled, verifying that the FAISS index size stays below 1GB and the model parameter count is reduced, while still producing valid (though potentially lower) nDCG scores.

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `src/analysis/resource_study.py` to configure FAISS with `IndexFlatIP` and memory cap (limited capacity) via `psutil` monitoring
- [ ] T028 [US3] Implement logic in `src/models/rag_pipeline.py` to load a specific multi-layer transformer variant (e.g., `google/flan-t5-small` or equivalent verified a large-scale parameter model

The research question, method, and references remain unchanged as no specific values or citations were present in the original text to alter.) when `--strict-resources` flag is set. MUST include a programmatic check to verify the loaded model has approximately 150M parameters (±20%) before proceeding.
- [ ] T029 [US3] Implement logic to enforce GB RAM limit by subsampling dataset or using a quantized index type if memory cap is approached (PREREQUISITE for T030). MUST depend on T006/T007 for dataset loading logic.
- [ ] T030 [US3] Update `src/cli/main.py` to support `--strict-resources` mode, run both standard and constrained pipelines, and output `degradation_report.json` with absolute percentage point drops

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Implement `src/analysis/throughput_monitor.py` to measure and log throughput (queries/hour) to `results/throughput_report.json` to verify SC-004
- [ ] T033a [P] Implement batched inference in `src/models/retriever_neural.py` and `src/models/rag_pipeline.py` to meet ≥33 queries/hour throughput target.
- [ ] T033b [P] Implement streaming logic in `src/data/download.py` and `src/data/preprocess.py` to process large datasets in chunks, verifying throughput targets with benchmarks.
- [ ] T034a [P] Update `docs/quickstart.md` with specific instructions on running the pipeline, expected outputs, and resource constraints
- [ ] T034b [P] Update `docs/data-model.md` with specific entity definitions and data flow diagrams
- [ ] T035 Code cleanup and refactoring to ensure modularity
- [ ] T036 [P] Additional unit tests for edge cases (zero matches, truncation, NaN handling) in `tests/unit/`
- [ ] T037 Security hardening: ensure no external API calls and fixed seeds are enforced globally
- [ ] T038 Run `quickstart.md` validation to ensure end-to-end reproducibility

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

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement src/models/retriever_bm25.py using rank_bm25 on preprocessed data"
Task: "Implement src/models/retriever_neural.py using sentence-transformers/all-MiniLM-L6-v2 for dual-encoder retrieval"
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
- **Descriptor Scope**: `src/data/descriptors.py` MUST compute descriptors ONLY for test set queries and ground truth snippets, NOT for retrieved snippets, to prevent circularity and ensure CPU feasibility.
- **Human Task**: Task T023a is a required human intervention step; the pipeline must wait for `results/manual_noise_input.json` to be present before proceeding to T023b.