# Tasks: Interdisciplinary Bridging Coefficient Analysis

**Input**: Design documents from `/specs/001-bridging-coefficient-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [X] T001 Create project structure per implementation plan: Execute `mkdir -p src/{models,services,cli,lib} tests/{contract,integration,unit} data/{raw,processed} artifacts/{results,plots}` to create all required directories. <!-- FAILED: unspecified -->
- [ ] T002 {{claim:c_d6eb7e14}} <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `pyproject.toml` with explicit sections `[tool.black]` (line_length=88, target_version=['py311']) and `[tool.ruff]` (select=['E402', 'F401', 'I001'], ignore=[]) defining specific rules.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `src/lib/config.py` for constants, random seeds, and paths (`data/`, `artifacts/`)
- [X] T005 [P] Implement `src/models/node.py` dataclass with fields: `id`, `title`, `citation_count`, `embedding_vector`, `primary_cluster`, `topic_cluster`
- [X] T006 [P] Create `src/models/graph_utils.py` with **stub signatures** and docstrings for `louvain_cluster(G)` and `calc_bridging(G, clusters)` functions; full implementation deferred to T014.
- [ ] T007 Setup `tests/contract/test_schemas.py` to validate against `specs/001-bridging-coefficient-analysis/contracts/` <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [ ] T008 Configure `pytest` with `conftest.py` for temporary data directories and seed pinning <!-- SKIPPED: YAML+regex parse failed (while parsing a block mapping
 in "<unicode string>", line 1, column 7:
 def logging_config():
 ^
expected <block end>, but found '<scalar>'
 in "<unicode string>", line 2, column 13:
 """
 ^) -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Topological Metric Computation (Priority: P1) 🎯 MVP

**Goal**: Download OpenAlex subgraph, assign structural clusters (Louvain), and compute bridging coefficients.

**Independent Test**: Can be fully tested by running the ingestion pipeline on a sampled subgraph and verifying that every node has a valid `bridging_coefficient` (0.0 to 1.0) and `primary_cluster` label, with no memory errors on CPU.

### Tests for User Story 1

- [X] T010 [P] [US1] Contract test for node schema in `tests/contract/test_node_schema.py` with function `test_node_has_required_fields`.
- [ ] T011 [P] [US1] Integration test for ingestion pipeline on sample data in `tests/integration/test_ingest_pipeline.py` with function `test_ingest_creates_subgraph`. <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [X] T012 [US1] Implement `src/services/ingest.py`: Fetch OpenAlex data via `pyalex` with **degree-stratified random sampling** to target subgraph size, explicitly **constructing the `networkx.Graph` object `G`** for downstream consumption (See plan.md Complexity Tracking: Degree-Stratified Sampling). *Note: Spec FR-001 references 'PubGraph', but implementation targets OpenAlex; this is a known spec drift.*
- [~] T013 [US1] Implement `src/services/clustering.py`: Run Louvain community detection on the graph `G` to assign `primary_cluster` IDs (See FR-002).
- [~] T014 [US1] Implement `src/models/graph_utils.py`: **Complete the implementation** of `calc_bridging(G, clusters)` to calculate `bridging_coefficient` for each node (inter-cluster edges / total degree), handling degree-0 nodes gracefully (See T006).
- [~] T015 [US1] Add validation in `src/models/graph_utils.py::calc_bridging`: Add `try/except` block to explicitly **assign a value of 0.0** for degree-0 nodes to prevent division-by-zero and satisfy Edge Cases (See spec.md Edge Cases).
- [~] T016 [US1] Save processed graph with clusters and coefficients to `data/processed/subgraph_with_clusters.parquet`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Outcome Variable Derivation (Citations and Novelty) (Priority: P2)

**Goal**: Extract citation counts and compute novelty scores using text-based clustering (k-means) independent of graph topology, using centroid distance for novelty.

**Independent Test**: Can be tested by processing a batch of nodes, verifying citation counts are non-negative integers, and novelty scores are positive floats, with a check confirming nodes with identical titles have zero novelty distance.

### Tests for User Story 2

- [~] T018 [P] [US2] Contract test for embedding output in `tests/contract/test_embedding_schema.py` with function `test_embedding_dimensions`.
- [~] T019 [P] [US2] Integration test for novelty calculation in `tests/integration/test_novelty_calculation.py` with function `test_novelty_centroid_distance`.

### Implementation for User Story 2

- [~] T023 [US2] Handle edge cases: Modify `src/services/embeddings.py` to **filter out nodes with missing/empty titles for novelty calculation ONLY, but retain them in the dataset for citation analysis**, logging excluded node IDs to `data/logs/excluded_nodes.csv` (See spec.md Edge Cases).
- [~] T020 [US2] Implement `src/services/embeddings.py`: Load `sentence-transformers/all-MiniLM-L6-v2` (CPU mode) and generate embeddings for all valid node titles in **batches** to meet 7GB RAM constraint, ensuring **no individual node latency exceeds a low-latency threshold** (See plan.md Complexity Tracking: Batched Embedding).
- [~] T021 [US2] Implement `src/services/clustering.py`: Perform k-means clustering (k=100) on title embeddings to assign `topic_cluster` IDs (independent of Louvain) (See FR-008).
- [~] T022 [US2] Implement novelty calculation: Compute **cosine distance** between each node's title embedding and the **centroid** of its assigned `topic_cluster` to derive the `novelty_score`, ensuring the predictor (topology) and outcome (novelty) are mathematically independent (See FR-004).
- [~] T024 [US2] Save final dataset with citations, novelty scores, and clusters to `data/processed/final_analysis_dataset.parquet`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Correlation Analysis (Priority: P3)

**Goal**: Perform Spearman correlation, linear regression, binned non-linear analysis, and multiple-comparison correction.

**Independent Test**: Can be tested by running the analysis on the computed dataset, verifying that p-values are returned and corrected, and findings are labeled "associational".

### Tests for User Story 3

- [~] T036 [P] [US3] Contract test for analysis output schema in `tests/contract/test_analysis_output_schema.py` with function `test_report_has_associational_label`.
- [~] T037 [P] [US3] Integration test for full statistical pipeline in `tests/integration/test_statistical_pipeline.py` with function `test_binned_analysis_execution`. <!-- SKIPPED: YAML+regex parse failed (while parsing a block mapping
 in "<unicode string>", line 1, column 1:
 def test_pipeline_integration_wi...
 ^
expected <block end>, but found '<scalar>'
 in "<unicode string>", line 2, column 13:
 """
 ^) -->

### Implementation for User Story 3

- [~] T026 [US3] Implement `src/services/analysis.py`: Calculate Spearman rank correlation between `bridging_coefficient` and `citation_count`/`novelty_score` (See FR-005).
- [~] T027b [US3] Implement `src/services/analysis.py`: Perform **linear regression** between `bridging_coefficient` and `citation_count`/`novelty_score` (See FR-005).
- [~] T027c [US3] Implement `src/services/analysis.py`: Perform **binned non-linear analysis** (to detect inverted-U effects) as an exploratory extension (See plan.md Complexity Tracking: Binned Analysis).
- [~] T028 [US3] Apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) to all p-values, **configurable via a CLI flag** to allow selection of method (See FR-006).
- [~] T029 [US3] Generate final report in `artifacts/results/analysis_report.md` explicitly labeling results as "associational" (See FR-007).
- [~] T030 [US3] Save statistical outputs (coefficients, p-values, plots) to `artifacts/results/statistical_metrics.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T031 [P] Documentation updates in `specs/001-bridging-coefficient-analysis/quickstart.md`: Update the "Prerequisites" and "Run" sections to reflect the final pipeline steps, dependencies, and exact CLI commands.
- [~] T032 [P] Code cleanup and refactoring for memory efficiency (Ingest): Refactor `src/services/ingest.py` to use **generator expressions** for data loading to reduce peak RAM.
- [~] T032b [P] Code cleanup and refactoring for memory efficiency (Embeddings): Refactor `src/services/embeddings.py` to ensure strict batch processing and memory release between batches.
- [~] T033 [P] Verify embedding performance against SC-005: Create `tests/bench/test_embedding_speed.py` to run a benchmark on a representative sample, measure **maximum latency per node**, and assert that the max latency is ≤ 50ms. The test must fail if the threshold is exceeded, providing evidence that SC-005 is met.
- [~] T034 [P] Additional unit tests for edge cases (isolated nodes, single-node clusters) in `tests/unit/test_graph_utils.py`: Implement functions `test_isolated_node` and `test_single_node_cluster`.
- [~] T035 [P] Validate data source reachability: Create `tests/unit/test_data_source.py` to verify the OpenAlex API endpoint is reachable and `pyalex` can fetch a sample record before running the full pipeline.
- [~] T039 [P] Add memory profiling: Integrate `memory_profiler` into `src/services/ingest.py` and `src/services/embeddings.py` to log peak RAM usage per batch, ensuring compliance with a specified data storage limit.
- [~] T038 [P] Run `quickstart.md` validation to ensure full pipeline reproducibility: Execute the pipeline and generate `artifacts/validation_report.md` containing the execution log, exit code, and artifact hashes.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data from US1 and US2

### Within Each User Story

- Tests are mandatory for reproducibility
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
# Launch all tests for User Story 1 together:
Task: "Contract test for node schema in tests/contract/test_node_schema.py"
Task: "Integration test for ingestion pipeline in tests/integration/test_ingest_pipeline.py"

# Launch all models/services for User Story 1 together:
Task: "Implement src/services/ingest.py: Fetch OpenAlex data..."
Task: "Implement src/services/clustering.py: Run Louvain community detection..."
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
 - Developer A: User Story 1 (Ingestion & Topology)
 - Developer B: User Story 2 (Embeddings & Text Clustering)
 - Developer C: User Story 3 (Statistics & Reporting)
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
- **Critical Constraint**: All tasks must run on a multi-core CPU with sufficient memory and a time limit.. No GPU, no low-bit quantization.
- **Data Source**: Use `pyalex` for OpenAlex data; ensure sampling strategy fits memory limits.
- **Spec Drift**: Note that FR-001 in spec.md references "PubGraph" while implementation uses "OpenAlex". This is a known issue to be resolved via formal spec amendment.