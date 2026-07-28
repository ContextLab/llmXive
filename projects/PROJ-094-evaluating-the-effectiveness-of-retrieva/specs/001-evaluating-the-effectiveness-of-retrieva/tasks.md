# Tasks: Evaluating the Effectiveness of Retrieval‑Augmented Generation for Code Search

**Input**: Design documents from `/specs/001-evaluating-rag-code-search/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)
**Tests**: Included per spec requirements (US1, US2, US3 independent tests)
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `specs/`)
- [X] T002 Create `requirements.txt` pinning exact versions for: `ir-datasets==1.2.10`, `sentence-transformers==2.7.0`, `faiss-cpu==1.8.0`, `rank_bm25==0.2.2`, `scikit-learn==1.5.0`, `pandas==2.2.0`, `numpy==1.26.0`, `psutil==6.0.0`, `transformers==4.42.0`, `torch==2.3.0`, `accelerate==0.31.0`. Do not use version ranges.
- [ ] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `src/lib/utils.py` with `set_seed()` for deterministic runs, `truncate_tokens()` for 256-token limit, and `strip_non_ascii()`
- [ ] T005 [P] Implement `src/data/checksum.py` for verifying raw data integrity via SHA-256 hashes
- [ ] T006 [P] Implement `src/data/download.py` using `ir_datasets.load("codesearchnet")` to fetch Python/Java subsets; **FAIL LOUDLY** if download fails (no synthetic fallback); cache to `data/raw/`
- [ ] T007 Implement `src/data/preprocess.py` to load raw data, strip non-ASCII, truncate to ≤256 tokens, and extract `doc_id`, `func_name`, `language`, `path`, `repo`, `code`, `docstring` (query)
- [ ] T008 Implement `src/lib/metrics_utils.py` for calculating Precision@10, Recall@10, nDCG@10, and handling zero-match cases (assign 0.0 scores)
- [ ] T009 Implement `src/lib/stat_utils.py` for Spearman's rho, Pearson's r, Wilcoxon signed-rank test, and normality checks
- [ ] T010 [P] Setup `tests/unit/test_metrics.py` with unit tests for metric calculations (Precision, Recall, nDCG)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible RAG vs. Baseline Evaluation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Run a complete, end-to-end comparison of RAG, BM25, and Dual-Encoder on A series of queries will be conducted to address the research question, utilizing the established method as outlined in the literature (citation)., outputting a CSV with nDCG@k scores.

**Independent Test**: {{claim:c_c1d4f68e}}

### Tests for User Story 1 ⚠️

- [ ] T011 [P] [US1] Integration test `tests/integration/test_pipeline_ee.py` verifying end-to-end execution on 50 queries produces valid CSV output with correct columns
- [ ] T012 [P] [US1] Contract test `tests/contract/test_schema_validation.py` validating CSV output schema matches spec (Query ID, Method, Metric Name, Metric Value, Descriptors)

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `src/models/retriever_bm25.py` using `rank_bm25` on pre-processed code snippets; handle zero matches gracefully; **must accept `masked_snippets` input parameter for control experiment**.
- [ ] T014 [P] [US1] Implement `src/models/retriever_neural.py` using `sentence-transformers/all-MiniLM-L6-v2` for dual-encoder retrieval; load on CPU; **must accept `masked_snippets` input parameter for control experiment**.
- [ ] T015 [US1] Implement `src/models/retriever_rag.py`:
 - **Retrieval**: Use `sentence-transformers/all-MiniLM-L6-v2` to index and retrieve top snippets (prevents circular validation with CodeBERT-based descriptors per FR-008).
 - **Interface**: Return top-k snippets and their embeddings; **must accept `masked_snippets` input parameter for control experiment**.
 - Output ranked list of snippets.
- [ ] T016 [US1] Implement `src/models/rag_generator.py`:
 - Load `Salesforce/codegen-350M-mono` with `device="cpu"` (CPU-only mode, no bitsandbytes if unsupported).
 - Implement RAG prompt template: `"Question: {query}\nContext: {snippet}\nAnswer:"`
 - Concatenate top retrieved snippets within -token limit.
 - Generate response with temperature=0.0.
 - **Interface**: Accept `masked_context` input parameter for control experiment.
- [ ] T017 [US1] Implement `src/analysis/evaluation.py` to orchestrate the three pipelines (BM25, DE, RAG) on test queries, compute metrics (nDCG@10, Precision@10) per FR-004, and output `data/results/retrieval_metrics.csv`.
- [ ] T018 [P] [US1] Implement `src/cli/main.py` entry point with `--seed` argument for reproducibility (FR-003)
- [ ] T019 [US1] Add logging in `src/models/rag_pipeline.py` and `src/models/retriever_*.py` to track execution time and memory usage (psutil)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Semantic Descriptor Correlation Analysis (Priority: P2)

**Goal**: Correlate code-level semantic properties (API density, doc density, naming consistency) with performance deltas (RAG vs. Baseline) for the 50 test queries.

**Independent Test**: The system outputs a JSON report containing Spearman correlation coefficients and p-values for each descriptor against the performance delta, flagging p < 0.05 as significant.

### Tests for User Story 2 ⚠️

- [ ] T020 [P] [US2] Unit test `tests/unit/test_descriptors.py` verifying API density, doc density, and naming consistency calculations on sample snippets
- [ ] T021 [P] [US2] Integration test `tests/integration/test_correlation_analysis.py` verifying correlation output format and statistical significance flags for a representative set of test queries

### Implementation for User Story 2

- [ ] T022 [US2] Implement `src/data/descriptor_calc.py`:
 - **Scope**: Compute descriptors for **a representative set of test queries and their associated ground-truth snippets** (matching the evaluation set per Plan Feasibility Strategy).
 - Calculate API density (ratio of API calls to total tokens). [UNRESOLVED-CLAIM: c_15f0d1de — status=not_enough_info]
 - Calculate Documentation density (ratio of comment tokens). [UNRESOLVED-CLAIM: c_cb6e65db — status=not_enough_info]
 - Calculate Naming-consistency score using `microsoft/codebert-base` embeddings (average pairwise cosine similarity of identifiers) per FR-002, FR-008.
- [ ] T023 [US2] Implement `src/analysis/correlation.py`:
 - Compute performance deltas (RAG nDCG - Baseline nDCG) per query. [UNRESOLVED-CLAIM: c_cf5f9b3a — status=not_enough_info]
 - Calculate Spearman's rho and Pearson's r between descriptors and deltas.
 - Perform normality check; switch to Wilcoxon signed-rank test if non-normal (FR-005).
 - Output `data/results/correlation_report.json` with coefficients, p-values, and significance flags.
- [ ] T024 [US2] Implement `src/analysis/control_experiment.py`:
 - **Step 1**: Mask API and documentation tokens in the **50 test queries and their ground-truth snippets**.
 - **Step 2**: **Re-run all three retrieval pipelines (BM25, Dual-Encoder, RAG)** on the **masked snippets** (masking both index and query) to generate NEW performance deltas (required by FR-009).
 - **Step 3**: **Re-execute the RAG generation step ONLY** (using the **masked retrieved snippets** as context) to produce valid generation metrics for the control comparison.
 - **Step 4**: Compute new descriptors for the **masked 50 test queries and their ground-truth snippets**.
 - **Step 5**: Re-run correlation analysis on the new deltas and descriptors.
 - Output `data/results/control_experiment_report.json`.
- [ ] T025 [P] [US2] Implement `src/analysis/label_noise.py` for manual spot-check logic; output `data/results/label_noise_estimate.json` (FR-010)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Resource Constraint Degradation Study (Priority: P3)

**Goal**: Understand how strict resource limits (1GB RAM, Layered model

The research question is [RESEARCH QUESTION]. The method is [METHOD] (Citation).) degrade RAG advantage.

**Independent Test**: The pipeline runs with "strict resource" flags, {{claim:c_035ff90b}} (2412.01555, https://arxiv.org/abs/2412.01555), model is reduced, and a degradation report is generated.

### Tests for User Story 3 ⚠️

- [ ] T026 [P] [US3] Integration test `tests/integration/test_resource_constraints.py` verifying memory cap enforcement and model reduction

### Implementation for User Story 3

- [ ] T027 [US3] Implement `src/models/rag_pipeline_constrained.py`:
 - **Self-contained implementation**: Re-implement the retrieval and generation logic with constrained resources to ensure US3 is independently shippable (does not modify T015's `retriever_rag.py`).
 - **Model**: Load `Salesforce/codegen-350M-mono` with `config.num_hidden_layers = 2`.
 - **Memory Enforcement**: {{claim:c_09098f9a}}
 - **Runtime Monitoring**: Measure peak process RSS via `psutil` during execution to verify the ≤1.05GB limit (FR-006).
- [ ] T028 [US3] Implement `src/analysis/resource_study.py`:
 - **Driver Script**: Run the pipeline from T027 with resource-constrained flags.
 - **Configuration**: Configure FAISS `IndexFlatIP` with memory limit ≤1.05GB (monitor via `psutil`).
 - **Enforcement Loop**: Implement a runtime enforcement loop: estimate size, construct index, measure peak RSS via `psutil`; if >1.05GB, perform a random subsample of vectors and retry; if limit still exceeded after subsampling, **fail loudly** with an explicit error message.
 - Compare results to standard run; output `data/results/degradation_report.json` with absolute percentage point drops (FR-006).
- [ ] T029 [US3] Extend `src/cli/main.py` with `--resource-constrained` flag to trigger strict mode (requires T027 implementation)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` and `README.md` with usage examples
- [ ] T031 Code cleanup and refactoring; ensure all tasks are idempotent
- [ ] T032 Performance optimization: ensure throughput ≥ 33 queries/hour (SC-004)
- [ ] T033 [P] Additional unit tests for edge cases (token truncation, zero matches, NaN handling) in `tests/unit/`
- [ ] T034 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T035 Verify all CSV outputs handle "NaN" string for missing descriptors per FR-007

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 metrics (deltas) for correlation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 pipeline for constrained run

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
Task: "Integration test for end-to-end pipeline in tests/integration/test_pipeline_e2e.py"
Task: "Contract test for schema validation in tests/contract/test_schema_validation.py"

# Launch all models for User Story 1 together:
Task: "Implement BM25 retriever in src/models/retriever_bm25.py"
Task: "Implement Dual-Encoder retriever in src/models/retriever_neural.py"
Task: "Implement RAG retrieval in src/models/retriever_rag.py"
Task: "Implement RAG generator in src/models/rag_generator.py"
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
- **Critical Constraint**: All data loading MUST use `ir-datasets` and fail loudly if real data is unavailable (no synthetic fallback).
- **Critical Constraint**: All model inference MUST run on CPU for standard runs; no GPU offloading permitted per Plan.
- **Critical Constraint**: Semantic descriptors MUST be computed for the **test queries and their ground-truth snippets** (matching evaluation set), not the full dataset, to meet CPU time limits.
- **Critical Constraint**: RAG retrieval MUST use `all-MiniLM-L6-v2` and generation MUST use `codegen-350M-mono` to prevent circular validation.
- **Critical Constraint**: Control experiment (T024) MUST re-run retrieval pipelines on masked data and re-execute generation only for RAG.
- **Critical Constraint**: Resource study (T027) MUST use `config.num_hidden_layers = 2` and monitor peak RSS via `psutil`.
- **Critical Constraint**: US3 (T027) MUST implement a self-contained pipeline to ensure independence from US1.