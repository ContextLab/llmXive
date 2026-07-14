# Tasks: GraphCompass: Topological Predictors of Semantic Coherence in CPU-Constrained RAG

**Input**: Design documents from `/specs/001-graph-compass-topology/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-911-llmxive-follow-up-extending-mcompassrag/`)
- [ ] T002 Initialize Python 3.11 project with pinned `requirements.txt` (networkx, scikit-learn, bertopic, datasets, pandas, numpy, pytest)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` to define hyperparameters (window=10), random seeds, and path constants
- [ ] T005 [P] Create `code/utils/hash_artifacts.py` to calculate SHA-256 hashes for `data/` and update `state/projects/PROJ-911-llmxive-follow-up-extending-mcompassrag.yaml`
- [ ] T006 Setup `data/raw/`, `data/processed/`, and `data/results/` directory structure
- [ ] T007 Implement `code/data_loader.py` to fetch HotpotQA (`fullwiki`) and Wikipedia 20231001.en via `datasets.load_dataset` with deterministic sampling (N ≤ 360)
- [ ] T008 Implement sampling logic in `code/data_loader.py` to ensure the sample size N is strictly ≤ 360 before execution, enforcing the ‑hour time budget constraint (FR‑007). The loader should truncate or randomly sample the dataset to N ≤ 360; it must **not raise an exception** if the raw dataset exceeds this limit.
- [ ] T009 Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` for artifact validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Graph Construction and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Process academic abstracts to extract deterministic topological features (modularity, centrality) from lexical co-occurrence graphs on CPU.

**Independent Test**: Run the graph construction pipeline on a sample subset (up to 360 docs) and verify numerical feature vectors are generated for every document within 60s/doc.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Unit test for graph edge case (low term diversity < 5) in `tests/unit/test_graph_builder.py`
- [ ] T011 [P] [US1] Integration test for full graph pipeline on sample data in `tests/integration/test_graph_pipeline.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement TF‑IDF filtering with fixed reference vocabulary and **save the resulting vocabulary to `data/processed/fixed_vocab.json`** (FR‑001) for versioning (Plan Data Traceability). The versioning script will hash this file.
- [ ] T013 [US1] Implement sliding window lexical co-occurrence graph construction in `code/graph_builder.py` (FR‑001). The window size will be sufficiently large to capture relevant lexical relationships. **Dependency**: Requires filtered terms from T012.
- [ ] T014 [US1] Implement topological metric calculation (modularity, avg path length, degree/betweenness centrality) in `code/topology_extractor.py` (FR‑002)
- [ ] T015 [US1] Add error handling for low‑diversity documents (assign default zeros or log warning) in `code/topology_extractor.py`
- [ ] T016 [US1] Write graph artifacts and feature vectors to `data/processed/graphs.json` and `data/processed/features.csv`
- [ ] T017 [US1] Add logging for document processing time to verify <60s constraint per doc

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Neural Baseline Generation and Retrieval Simulation (Priority: P2)

**Goal**: Generate comparative baseline using BERTopic (CPU) and simulate retrieval performance for both methods against ground‑truth queries.

**Independent Test**: Run BERTopic (CPU) and retrieval simulation on a disjoint test set, verifying Recall@k scores are generated.

**Methodology Note**: Per plan.md "Critical Methodological Clarification", retrieval ranking uses **TF‑IDF Cosine Similarity** only. Topological signatures are extracted *after* ranking for correlation analysis.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for Recall@k output schema in `tests/contract/test_recall_schema.py`
- [ ] T019 [P] [US2] Integration test for disjoint train/test split validation in `tests/integration/test_data_split.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement BERTopic (CPU‑only mode, no CUDA) for topic embeddings in `code/neural_baseline.py` (FR‑)
- [ ] T021 [US2] Implement fallback mechanism for BERTopic memory pressure (reduce corpus/window size) in `code/neural_baseline.py`
- [ ] T022 [US2] Implement TF‑IDF Cosine Similarity ranking for query‑document matching in `code/retrieval_sim.py` (FR‑004). **Output**: `data/results/retrieval_scores.csv` (ranked lists)
- [ ] T023 [US2] Implement extraction of topological signatures **ONLY from the set of documents returned by the TF‑IDF ranking**; ensure no topology data is used to generate the ranking scores. **Output**: `data/results/retrieved_features.csv`
- [ ] T024 [US2] Implement Recall@K calculation against HotpotQA ground‑truth in `code/evaluator.py` (FR‑004). 

The research question is: Can we improve multi-hop reasoning performance by incorporating knowledge graph embeddings into a transformer-based architecture?

The method is: We will evaluate the performance of our model on the HotpotQA dataset, using Recall@K as a key metric.

(FR‑004) **Output**: `data/results/retrieval_scores.csv`
- [ ] T025 [US2] Ensure strict disjointness between training corpus and query set to prevent data leakage in `code/data_loader.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Latency Benchmarking (Priority: P3)

**Goal**: Quantify relationship between graph topology and retrieval precision, and measure computational efficiency gain.

**Independent Test**: Analyze correlation coefficients and latency logs to confirm hypothesis evaluation and latency reduction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for Spearman correlation calculation in `tests/unit/test_evaluator.py`
- [ ] T027 [P] [US3] Integration test for end‑to‑end statistical validation in `tests/integration/test_statistical_validation.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement Spearman rank correlation between topological features (per query, from T016) and Recall@10 (from T024) in `code/evaluator.py` (FR‑005). **Note**: This task depends on T016 and T024 completion.
- [ ] T029 [US3] Implement paired t‑test for precision metrics **and calculate the ratio of Graph Recall@10 to Neural Recall@10**, logging whether the ratio meets the ≥ 0.70 threshold in `metrics.json` (FR‑006).
- [ ] T030 [US3] Calculate wall‑clock time and percentage reduction in metadata generation latency in `code/evaluator.py` (FR‑006)
- [ ] T031 [US3] Write final metrics (r, p‑value, Recall@k, latency) to `data/results/metrics.json` and `data/results/correlation.csv`
- [ ] T032 [US3] Validate results against Success Criteria (SC‑001 to SC‑005) by logging the correlation coefficient r, p‑value and a status field indicating whether the hypothesis was supported (r > 0.6). **Do NOT raise an exception on low r; only log status.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Update `docs/` with quickstart.md and architecture diagrams
- [ ] T034 Code cleanup and refactoring of `code/` scripts
- [ ] T035 Performance optimization for graph construction loop (vectorization where possible)
- [ ] T036 [P] Add comprehensive unit tests for `code/utils/hash_artifacts.py`
- [ ] T037 Run `quickstart.md` validation to ensure full pipeline reproducibility
- [ ] T038 Verify all artifacts are checksummed and state file is updated

---

## Phase 7: Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational (Phase 2) completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires `data/processed/` from US1 for comparison logic
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires outputs from US1 (features) and US2 (Recall scores)

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
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU‑only CI (limited cores, constrained RAM, time limit). No GPU, no 8‑bit quantization, no large model loading.
- **Data Integrity**: All datasets must be real (HotpotQA, Wikipedia) via `datasets` library. No synthetic data generation.
- **Methodology**: Topological signatures are extracted from *retrieved* documents only; they are NOT used for ranking. Ranking is performed via TF‑IDF Cosine Similarity.

