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

**Purpose**: Project initialization and basic structure. **Prerequisite**: T012c (Spec Amendment) must be completed before T012.

- [X] T001 Create project structure per implementation plan: Execute `mkdir -p src/{models,services,cli,lib} tests/{contract,integration,unit} data/{raw,processed} artifacts/{results,plots}` to create all required directories.
- [X] T002 Initialize a Python project with a compatible modern version. with `pyproject.toml` at repository root: Define `[build-system]` (requires=["setuptools", "wheel"]), `[project]` (name, version, dependencies list including `networkx`, `scikit-learn`, `sentence-transformers`, `pandas`, `numpy`, `scipy`, `pyalex`, `memory-profiler`, `pytest`, `ruff`, `black`), and `[tool.black]`/`[tool.ruff]` sections. **Verification**: Assert `pyproject.toml` contains section `[project.dependencies]` with all listed packages and run `pip check` to verify no conflicts.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Append `[tool.ruff]` section to existing `pyproject.toml` with `select=['E402', 'F401', 'I001']` and `ignore=[]`. **Verification**: Run `ruff check.` and assert a successful exit code.
- [X] T031a [P] Documentation updates (Prerequisites): Insert the string "pyalex>=1.0" and "sentence-transformers" into the "Prerequisites" section of `specs/001-bridging-coefficient-analysis/quickstart.md`. **Verification**: Assert `quickstart.md` contains string "pyalex>=1.0" and "sentence-transformers" in the Prerequisites section.
- [X] T031b [P] Documentation updates (Run): Insert the command "python -m src.cli.main --sample-size 1000" into the "Run" section of `specs/001-bridging-coefficient-analysis/quickstart.md`. **Verification**: Assert `quickstart.md` contains string "python -m src.cli.main --sample-size 1000" in the Run section.
- [X] T012c [US1] **BLOCKING**: Amend spec.md: Update `specs/001-bridging-coefficient-analysis/spec.md` to replace ALL occurrences of "PubGraph" with "OpenAlex" in FR-001, Assumptions, Edge Cases, User Scenarios, and any other text. **Verification**: Assert `spec.md` no longer contains the string "PubGraph" anywhere in the file. **Prerequisite**: Must be completed before T012.

---

## Phase 2: Foundational (Data Ingestion & Sampling)

**Purpose**: Core infrastructure and data pipeline foundation. **Prerequisite**: T012c must be completed. This phase includes the critical data fetcher and sampling logic required by all User Stories.
**Note**: T012 (Ingest) is the final step of this phase, consuming the logic from T040 and T012a.

**⚠️ CRITICAL**: All data fetcher and sampling tasks must be complete before any User Story implementation (Phase 3) begins.

- [X] T008 Configure `pytest` with `conftest.py` for seed pinning and coverage: Create `tests/conftest.py` with `pytest_configure` hook that calls `random.seed` and `numpy.random.seed` with a fixed integer at module import. Create `pytest.ini` with `[pytest]` section containing `addopts = --cov --cov-report=term-missing --log-cli-level=INFO`. **Verification**: Run `pytest --collect-only` to confirm flags are active.
- [X] T004 [P] Setup `src/lib/config.py` for constants, random seeds, and paths: Create file with variables `SEED=42`, `DATA_PATH='data/'`, `ARTIFACT_PATH='artifacts/'`. **Verification**: Assert `config.py` imports successfully and exports `SEED=42`.
- [X] T005 [P] Implement `src/models/node.py` dataclass: Define fields `id`, `title`, `citation_count`, `embedding_vector`, `primary_cluster`, `topic_cluster`. **Verification**: Assert file exists, contains `@dataclass` decorator, and run `tests/unit/test_node_instantiation.py`.
- [X] T006 [P] Create `src/models/graph_utils.py` with stub signatures: Define `louvain_cluster(G)` and `calc_bridging(G, clusters)` functions. **Verification**: Assert file exists and functions raise `NotImplementedError`.
- [X] T007 [P] Setup `tests/contract/test_schemas.py`: Load `specs/001-bridging-coefficient-analysis/contracts/node.schema.yaml` and `analysis_output.schema.yaml`. Create `test_schema_validation` function. **Verification**: Assert file exists and test passes on valid YAML.
- [ ] T040 [US1] **BLOCKING**: Implement strict data fetcher with NO synthetic fallback and STREAMING support: Refactor `src/services/ingest.py` to use `datasets.load_dataset(..., streaming=True)` for OpenAlex data. The task MUST specify exact query parameters: `fields=['id', 'title', 'cited_by_count', 'publication_date']`, `filters={'type': 'work'}`. The logic MUST consume the stream incrementally, adding nodes/edges to the graph object immediately without buffering the full dataset, enforcing a memory buffer limit. If `pyalex` or `datasets` fails to fetch, the script MUST check for a verified local cache at `data/raw/cache.parquet`. If cache exists, load from cache; if no cache exists, raise a `RuntimeError` with message "Data fetch failed: <error>". **Verification**: Assert `RuntimeError` is raised on failure with message containing "Data fetch failed" and verify memory usage stays < 7GB during stream processing using `memory-profiler` with `pytest` fixture and a mock dataset of 100k nodes.
- [ ] T012a [US1] **BLOCKING**: Implement Snowball Sampling: Create function `sample_subgraph_stream(G_stream, target_size, seed_node_id, max_depth=3)` in `src/services/ingest.py`. **Algorithm**: 1. Select a random seed node from the stream. 2. Perform Breadth-First Search (BFS) up to `max_depth` to collect neighbors. 3. If target size not reached, select a new seed from unvisited nodes and repeat. 4. Filter edges to only include those within the collected node set. This preserves local neighborhood topology. **Verification**: Add unit test `tests/unit/test_ingest.py::test_snowball_sampling_preserves_local_topology` that asserts the local clustering coefficient distribution of the sample matches a Barabási-Albert mock graph (N=1000, m=3, seed=42) with KS p-value > 0.05 AND D < 0.1. **Prerequisite**: T040, T006.
- [ ] T012 [US1] **BLOCKING**: Implement `src/services/ingest.py`: Orchestrate data fetch using `pyalex` with **Snowball Sampling** (T012a) to target subgraph size, integrating with the streaming logic from T040. **Prerequisite**: T012c (Spec Amendment completed), T040 (Strict Fetch + Streaming), T012a (Snowball Sampling Logic). (See plan.md Complexity Tracking: Snowball Sampling).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Topological Metric Computation (Priority: P1) 🎯 MVP

**Goal**: Download OpenAlex subgraph, assign structural clusters (Louvain), and compute bridging coefficients.
**Independent Test**: Can be fully tested by running the ingestion pipeline on a sampled subgraph and verifying that every node has a valid `bridging_coefficient` (0.0 to 1.0) and `primary_cluster` label, with no memory errors on CPU.

### Tests for User Story 1

- [X] T010 [P] [US1] Contract test for node schema in `tests/contract/test_node_schema.py` with function `test_node_has_required_fields`.
- [X] T011 [P] [US1] Integration test for ingestion pipeline on sample data in `tests/integration/test_ingest_pipeline.py` with function `test_ingest_creates_subgraph`.

### Implementation for User Story 1

- [ ] T012b [US1] Validate subgraph representativeness (Local Topology): Create function `validate_sampled_graph(G_sampled)` in `src/services/ingest.py` that computes and compares the **local clustering coefficient distribution** of `G_sampled` against a theoretical scale-free distribution. **Pass Criteria**: Kolmogorov-Smirnov test p-value > 0.05 AND KS statistic D < 0.1. **Output**: Write report to `artifacts/results/sampling_validation.json`. **Verification**: Assert `artifacts/results/sampling_validation.json` exists and contains keys `['sampled_local_clustering_dist', 'ks_statistic', 'p_value']`. **Prerequisite**: T012a, T012.
- [X] T013 [US1] Implement `src/services/clustering.py`: Run Louvain community detection on the graph `G` to assign `primary_cluster` IDs (See FR-002).
- [X] T014 [US1] Implement `src/models/graph_utils.py`: **Complete the implementation** of `calc_bridging(G, clusters)` to calculate `bridging_coefficient` for each node (inter-cluster edges / total degree). **Edge Case Handling**: Explicitly handle degree-0 nodes by assigning `bridging_coefficient=0.0` to prevent division-by-zero (See spec.md Edge Cases).
- [ ] T016 [US1] Save processed graph with clusters and coefficients to `data/processed/subgraph_with_clusters.parquet`: Write the graph data to Parquet format using `pandas.to_parquet`. **Prerequisite**: T012, T013, T014.
- [ ] T016a [US1] Verify saved graph artifact: Create function `verify_parquet()` in `tests/unit/test_graph_utils.py` that asserts `data/processed/subgraph_with_clusters.parquet` exists and contains columns `[id, title, citation_count, primary_cluster, bridging_coefficient]`. **Logic**: Assert `primary_cluster` has no nulls for nodes with degree > 0. Assert `bridging_coefficient` is 0.0 for nodes with degree == 0 and non-null for nodes with degree > 0. **Prerequisite**: T016.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Outcome Variable Derivation (Citations and Novelty) (Priority: P2)

**Goal**: Extract citation counts and compute novelty scores using text-based clustering (k-means) independent of graph topology, using centroid distance for novelty.

**Independent Test**: Can be tested by processing a batch of nodes, verifying citation counts are non-negative integers, and novelty scores are positive floats, with a check confirming nodes with identical titles have zero novelty distance.

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for embedding output in `tests/contract/test_embedding_schema.py` with function `test_embedding_dimensions`.
- [X] T019 [P] [US2] Integration test for novelty calculation in `tests/integration/test_novelty_calculation.py` with function `test_novelty_centroid_distance`.

### Implementation for User Story 2

- [X] T020 [US2] Implement `src/services/embeddings.py`: Load `sentence-transformers/all-MiniLM-L6-v2` (CPU mode) and generate embeddings for all **valid** node titles. **Logic**: Filter out nodes with empty or null titles (log excluded IDs to stdout/stderr with reason "empty_title" or "null_title") and retain them in the dataframe with null novelty scores. Generate embeddings in **batches of 64**. **Prerequisite**: None (filtering logic integrated). **Function**: `generate_embeddings_batch(texts)`. **Verification**: Assert max latency per node <= 50ms in unit test `tests/bench/test_embedding_speed.py` (See plan.md Complexity Tracking: Batched Embedding).
- [X] T021 [US2] Implement `src/services/clustering.py`: Perform k-means clustering (k=100) on title embeddings to assign `topic_cluster` IDs (independent of Louvain) (See FR-008). **Prerequisite**: T020.
- [X] T022 [US2] Implement novelty calculation: Compute **minimum cosine distance** between each node's title embedding and the centroid of **any OTHER topic_cluster** (not its own) to derive the `novelty_score`, ensuring the predictor (topology) and outcome (novelty) are mathematically independent. **Edge Case Handling**: If a node is the *only* member of its cluster (singleton), calculate the distance to the centroid of the **nearest other cluster** (not 0.0). **Output**: Add `novelty_score` column to the dataframe. **Verification**: Link to test `test_novelty_centroid_distance` in T019. **Prerequisite**: T020, T021.
- [ ] T024 [US2] Save final dataset with citations, novelty scores, and clusters to `data/processed/final_analysis_dataset.parquet`. **Prerequisite**: T020, T021, T022, T016.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Correlation Analysis (Priority: P3)

**Goal**: Perform Spearman correlation, linear regression, binned non-linear analysis, and multiple-comparison correction.

**Independent Test**: Can be tested by running the analysis on the computed dataset, verifying that p-values are returned and corrected, and findings are labeled "associational".

### Tests for User Story 3

- [X] T036 [P] [US3] Contract test for analysis output schema in `tests/contract/test_analysis_output_schema.py` with function `test_report_has_associational_label`.
- [ ] T037 [P] [US3] Integration test for full statistical pipeline in `tests/integration/test_statistical_pipeline.py` with function `test_binned_analysis_execution`. **Input**: `data/processed/final_analysis_dataset.parquet`. **Assertions**: Verify p-values are present, corrected, and the report contains the "associational" label.

### Implementation for User Story 3

- [X] T026 [US3] Implement `src/services/analysis.py`: Calculate Spearman rank correlation between `bridging_coefficient` and `citation_count`/`novelty_score` (See FR-005).
- [X] T027 [US3] Perform Linear Regression: Implement `linear_regression` function in `src/services/analysis.py` to model the relationship between bridging coefficient and outcomes. **Mandatory**: This task must include **covariates** (publication year, cluster size) to control for confounds. **Prerequisite**: T026.
- [ ] T027_binned_analysis [US3] Perform Binned Non-Linear Analysis: Implement `create_binned_data` and `calculate_bin_statistics` functions in `src/services/analysis.py`. **Strategy**: Use **quantile bins, k=10** for `bridging_coefficient`. **Covariate Handling**: Stratify bins by publication year (e.g., decades) or cluster size quartiles to ensure the analysis controls for these covariates as per Plan Phase 3.2. **Output**: Write results to `artifacts/results/binned_analysis.json` with keys `['bin_edges', 'mean_bridging', 'mean_citations', 'stratification_key']`. **Prerequisite**: T027.
- [X] T028 [US3] Apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) to all p-values (from T026, T027, T027_binned_analysis), **configurable via a CLI flag** to allow selection of method (See FR-006). **Output**: Write corrected p-values to `artifacts/results/corrected_pvalues.json`. **Verification**: Assert `artifacts/results/corrected_pvalues.json` contains keys `['method', 'raw_pvalues', 'corrected_pvalues', 'significant_count']`.
- [X] T029 [US3] Generate final report in `artifacts/results/analysis_report.md` explicitly labeling results as "associational" (See FR-007). **Prerequisite**: T026, T027, T027_binned_analysis, T028, T030.
- [X] T030 [US3] Save statistical outputs (coefficients, p-values, plots) to `artifacts/results/statistical_metrics.json`. **Prerequisite**: T026, T027, T027_binned_analysis, T028.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Code cleanup and refactoring for memory efficiency (Ingest): Refactor data loading functions in `src/services/ingest.py` to use **generator expressions** for row iteration to reduce peak RAM. **Specifics**: Replace `pandas.read_parquet` with `pyarrow.parquet.ParquetFile` streaming reader for large files. **Verification**: Run memory test T039b.
- [ ] T032b [P] Code cleanup and refactoring for memory efficiency (Embeddings): Modify `src/services/embeddings.py` to use a **generator for yielding batches** to ensure strict batch processing. **Verification**: Run test T032c.
- [ ] T032c [P] Memory test (Embeddings): Add test `tests/unit/test_embeddings.py::test_batch_memory_release` that asserts memory drops between batches.
- [X] T033 [P] Verify embedding performance against SC-005: Create `tests/bench/test_embedding_speed.py` to run a benchmark on a representative sample, measure **maximum latency per node**, and assert that the max latency is ≤ 50ms. The test must fail if the threshold is exceeded, providing evidence that SC-005 is met.
- [X] T034 [P] Additional unit tests for edge cases (isolated nodes, single-node clusters) in `tests/unit/test_graph_utils.py`: Implement functions `test_isolated_node` and `test_single_node_cluster`. **Logic**: Ensure isolated nodes get bridging=0.0 and single-node clusters handle centroid distance=0.0 correctly.
- [X] T035 [P] Validate data source reachability: Create `tests/unit/test_data_source.py` to verify the OpenAlex API endpoint is reachable and `pyalex` can fetch a sample record before running the full pipeline.
- [ ] T039 [P] Add memory profiling: Integrate `memory_profiler` into `src/services/ingest.py` and `src/services/embeddings.py` to log peak RAM usage per batch. **Output**: Generate `artifacts/results/memory_profile.log`. **Verification**: Assert `artifacts/results/memory_profile.log` exists and contains a line matching regex `Peak RAM: [0-9.]+ GB <= 7.0 GB`.
- [X] T039b [P] Enforce memory constraint: Create `tests/unit/test_memory_constraint.py` that runs the pipeline with a mock dataset and asserts peak RAM usage remains within acceptable system limits, failing the build if exceeded. **Prerequisite**: Completion of T032, T032b.
- [X] T038 [P] Run `quickstart.md` validation: Execute command `python -m src.cli.main --run-validation` and generate `artifacts/validation_report.md`. **Content Requirements**: Must contain exit code 0, artifact hashes, and runtime duration. **Verification**: Assert `artifacts/validation_report.md` exists and contains strings `['Exit Code: 0', 'Artifact Hashes:', 'Runtime Duration:']`.
- [ ] T042 [US1] Add data validation task: Create `tests/unit/test_ingest.py::test_real_data_integrity` that asserts the fetched data contains no nulls in critical fields (`id`, `title`, `cited_by_count`) and that the number of rows matches the requested sample size exactly (within a small tolerance of **5%**). **Verification**: Assert test passes with a small tolerance.
- [ ] T043 [US2] Implement embedding batch validation: Add a check in `src/services/embeddings.py` to verify that every batch of embeddings has the correct dimension (consistent with the model architecture for `all-MiniLM-L6-v2`) and no NaN values. **Verification**: Assert `ValueError` is raised if check fails.
- [X] T045 [US3] Implement reproducibility audit trail: Create a script `scripts/audit_reproducibility.py` that re-runs the entire pipeline on a fresh dataset and compares the output hashes of `artifacts/results/*` using `sha256`. **Logic**: Compare sha256 of all files; exit code 0 if match, 1 if mismatch. **Prerequisite**: All prior analysis tasks. **Verification**: Assert script runs and exits correctly.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately (except T012c blocks T012).
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Prerequisites**: T012c, T040, T012a must be complete. T012 is the final step of Phase 2.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user, stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data from US1 and US2.

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

1. Complete Phase 1: Setup (including T012c)
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
- **Critical Constraint**: All tasks must run on a multi-core CPU with sufficient memory and a time limit. No GPU, no low-bit quantization.
- **Data Source**: Use `pyalex` for OpenAlex data; ensure sampling strategy fits memory limits.
- **Spec Drift**: Resolved by T012c (Formal amendment of spec.md).
- **Exploratory Analysis**: Binned non-linear analysis (T027_binned_analysis) is now mandatory to satisfy plan's Complexity Tracking.
- **Non-Circular Validation**: Ensured by T034 (Edge case tests) and strict separation of T021 (Text Clustering) and T013 (Topological Clustering).
- **Temporal Validity**: Temporal validation tasks (T025, T028a) removed as they were scope creep not traceable to spec.