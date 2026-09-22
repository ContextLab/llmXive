# Tasks: Interdisciplinary Bridging Coefficient Analysis

**Input**: Design documents from `/specs/001-bridging-coefficient-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- **[GLOBAL]**: Project-wide tasks (e.g., spec amendments)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure. **Prerequisite**: T012c (Spec Amendment) must be completed before T012, T040, T012a.

- [X] T001 Create project structure per implementation plan: Execute `mkdir -p src/{models,services,cli,utils} tests/{contract,integration,unit} data/{raw,processed} artifacts/{results,plots}` to create all required directories.
- [X] T002 Initialize a Python project with a compatible modern version. with `pyproject.toml` at repository root: Define `[build-system]` (requires=["setuptools", "wheel"]), `[project]` (name, version, dependencies list including `networkx`, `scikit-learn`, `sentence-transformers`, `pandas`, `numpy`, `scipy`, `pyarrow`, `datasets`, `memory-profiler`, `pytest`, `ruff`, `black`), and `[tool.black]`/`[tool.ruff]` sections. **Verification**: Assert `pyproject.toml` contains string "networkx" in `[project.dependencies]` and run `pip check` to verify no conflicts.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Append `[tool.ruff]` section to existing `pyproject.toml` with `select=['E402', 'F401', 'I001']` and `ignore=[]`. **Verification**: Run `ruff check.` and assert a successful exit code.
- [X] T031a [P] Documentation updates (Prerequisites): Insert the string "pyarrow" and "datasets" into the "Prerequisites" section of `specs/001-bridging-coefficient-analysis/quickstart.md`. **Verification**: Assert `quickstart.md` contains string "pyarrow" and "datasets" in the Prerequisites section.
- [X] T031b [P] Documentation updates (Run): Insert the command "python -m src.cli.main --sample-size [REDACTED]" into the "Run" section of `specs/001-bridging-coefficient-analysis/quickstart.md`. **Verification**: Assert `quickstart.md` contains a sample size configuration in the Run section.
- [ ] T012c [GLOBAL] **BLOCKING**: Amend spec.md and plan.md: Update `specs/001-bridging-coefficient-analysis/spec.md` AND `specs/001-bridging-coefficient-analysis/plan.md` to replace ALL occurrences of "PubGraph" with "OpenAlex-derived Subgraph" or "OpenAlex". **Specific Edits**:
  1. **FR-001**: Replace "PubGraph dataset" with "OpenAlex-derived Subgraph".
  2. **Assumptions**: Replace "PubGraph" with "OpenAlex".
  3. **Edge Cases**: Replace "PubGraph" with "OpenAlex".
  4. **User Scenarios**: Replace "PubGraph" with "OpenAlex".
  5. **Plan.md**: Replace "PubGraph" with "OpenAlex" in all sections.
  **Verification**: Assert `spec.md` and `plan.md` no longer contain the string "PubGraph" anywhere in the files. **Prerequisite**: None. **Note**: This task MUST be completed before T040, T012a, and T012. This task amends the definition of FR-001 and User Story 1 to align the spec with the plan's data source.

---

## Phase 2: Foundational (Data Ingestion & Sampling)

**Purpose**: Core infrastructure and data pipeline foundation. **Prerequisite**: T012c must be completed. This phase includes the critical data fetcher and sampling logic required by all User Stories.
**Note**: T012 (Ingest) is the final step of this phase, consuming the logic from T040 and T012a.

**⚠️ CRITICAL**: All data fetcher and sampling tasks must be complete before any User Story implementation (Phase 3) begins.

- [X] T008 Configure `pytest` with `conftest.py` for seed pinning and coverage: Create `tests/conftest.py` with `pytest_configure` hook that calls `random.seed` and `numpy.random.seed` with a fixed integer at module import. Create `pytest.ini` with `[pytest]` section containing `addopts = --cov --cov-report=term-missing --log-cli-level=INFO`. **Verification**: Run `pytest --collect-only` to confirm flags are active.
- [X] T004 [P] Setup `src/models/config.py` for constants, random seeds, and paths: Create file with variables `SEED=42`, `DATA_PATH='data/'`, `ARTIFACT_PATH='artifacts/'`, `MAX_BUFFER_ROWS=10000`, and `MAX_RAM_GB=7.0`. **Verification**: Assert `config.py` imports successfully and exports `SEED=42`, `MAX_BUFFER_ROWS=10000`, and `MAX_RAM_GB=7.0`.
- [X] T005 [P] Implement `src/models/node.py` dataclass: Define fields `id`, `title`, `citation_count`, `embedding_vector`, `primary_cluster`, `topic_cluster`. **Verification**: Assert file exists, contains `@dataclass` decorator, and run `tests/unit/test_node_instantiation.py`.
- [X] T006 [P] Create `src/models/graph_utils.py` with stub signatures: Define `louvain_cluster(G)` and `calc_bridging(G, clusters)` functions. **Verification**: Assert file exists and functions raise `NotImplementedError`.
- [X] T007 [P] Setup `tests/contract/test_schemas.py`: Load `specs/001-bridging-coefficient-analysis/contracts/node.schema.yaml` and `analysis_output.schema.yaml`. Create `test_schema_validation` function. **Verification**: Assert file exists and test passes on valid YAML.
- [X] T040 [US1] **BLOCKING**: Implement strict data fetcher with NO synthetic fallback and STREAMING support: Refactor `src/services/ingest.py` to use `datasets.load_dataset("openalex/works", streaming=True)` for the OpenAlex-derived subgraph. The task MUST specify exact query parameters: `fields=['id', 'title', 'cited_by_count', 'publication_date']`, `filters={'type': 'work'}`. The logic MUST consume the stream incrementally, adding nodes/edges to the graph object immediately without buffering the full dataset, enforcing a memory buffer limit of `MAX_BUFFER_ROWS` (a sufficiently large row count) using `itertools.islice`. If `datasets` fails to fetch, the script MUST check for a verified local cache at `data/raw/cache.parquet`. If cache exists, load from cache; if no cache exists, raise a `RuntimeError` with message "Data fetch failed: <error>". If the stream exceeds `MAX_BUFFER_ROWS`, the script MUST raise a `RuntimeError` with message "Buffer limit exceeded: <current_count> > <MAX_BUFFER_ROWS>". **Verification**: Assert `RuntimeError` is raised on failure with message containing "Data fetch failed" or "Buffer limit exceeded" and verify memory usage stays < 7GB during stream processing using `memory-profiler` with `pytest` fixture and a mock dataset of large-scale nodes. **Prerequisite**: T012c, T040 must ensure data source definition precedes fetching. **Note**: This task verifies real data ingestion capability; mock data is only for memory profiling, not for functional verification of the fetcher.
- [X] T012a [US1] **BLOCKING**: Implement Snowball Sampling: Create function `sample_subgraph_stream(G_stream, target_size, seed_node_id, max_depth=3)` in `src/services/ingest.py`. **Algorithm**: 1. Select a random seed node from the stream. 2. Perform Breadth-First Search (BFS) up to `max_depth` to collect neighbors. 3. If target size not reached, select a **new seed randomly from unvisited nodes** and repeat. **Limit**: Max **5 attempts** to find a new seed before failing. 4. Filter edges to only include those within the collected node set. This preserves local neighborhood topology. **Verification**: Add unit test `tests/unit/test_ingest.py::test_snowball_sampling_preserves_local_topology` that asserts the local clustering coefficient distribution of the sample matches a Barabási-Albert mock graph (n=1000, m=3, seed=42) with KS p-value > 0.05 AND D < 0.1. **Reference Distribution Logic**: If `data/raw/reference_degree_dist.json` exists, use it for the KS test; otherwise, use theoretical power-law with alpha=2.1 and min_k=1. **Prerequisite**: T012c, T040, T006.
- [ ] T012 [US1] **BLOCKING**: Implement `src/services/ingest.py`: Orchestrate data fetch using `datasets.load_dataset("openalex/works", streaming=True)` for the OpenAlex-derived subgraph with **Snowball Sampling** (T012a) to target subgraph size, integrating with the streaming logic from T040. **Function Signature**: `def run_ingestion_pipeline(target_size: int, seed_node_id: str) -> nx.Graph`. **Error Handling**: Must handle fetch failures and buffer limits as defined in T040. **Prerequisite**: T012c (Spec Amendment completed), T040 (Strict Fetch + Streaming), T012a (Snowball Sampling Logic), T005 (Node dataclass), T006 (Graph utils stubs). (See plan.md Complexity Tracking: Snowball Sampling).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Topological Metric Computation (Priority: P1) 🎯 MVP

**Goal**: Download OpenAlex subgraph, assign structural clusters (Louvain), and compute bridging coefficients.
**Independent Test**: Can be fully tested by running the ingestion pipeline on a sampled subgraph and verifying that every node has a valid `bridging_coefficient` (0.0 to 1.0) and `primary_cluster` label, with no memory errors on CPU.

### Tests for User Story 1

- [X] T010 [P] [US1] Contract test for node schema in `tests/contract/test_node_schema.py` with function `test_node_has_required_fields`.
- [X] T011 [P] [US1] Integration test for ingestion pipeline on sample data in `tests/integration/test_ingest_pipeline.py` with function `test_ingest_creates_subgraph`.

### Implementation for User Story 1

- [X] T013 [US1] Implement `src/services/clustering.py`: Run Louvain community detection on the graph `G` to assign `primary_cluster` IDs (See FR-002).
- [X] T014 [US1] Implement `src/models/graph_utils.py`: **Complete the implementation** of `calc_bridging(G, clusters)` to calculate `bridging_coefficient` for each node (inter-cluster edges / total degree). **Edge Case Handling**: Explicitly handle degree-0 nodes by assigning `bridging_coefficient=0.0` to prevent division-by-zero (See spec.md Edge Cases).
- [ ] T012b [US1] Validate subgraph representativeness (Schema Check & Topology Equivalence): **Implement** function `validate_sampled_graph(G_sampled)` in `src/services/ingest.py` that verifies every node in `G_sampled` has a non-null `primary_cluster` and `bridging_coefficient` (defaulting to 0.0 for isolated nodes). **Representativeness Check**: Compute degree distribution and cluster size distribution. Perform Kolmogorov-Smirnov (KS) test against OpenAlex reference distribution (or theoretical power-law if reference unavailable) and assert KS p-value > 0.05 AND D < 0.1. **Reference Logic**: If `data/raw/reference_degree_dist.json` exists, use it; otherwise, use theoretical power-law with alpha=2.1 and min_k=1. **Pass Criteria**: No nulls in critical fields; all coefficients in range [0.0, 1.0]; KS test passes. **Output**: Write report to `artifacts/results/sampling_validation.json` AND `artifacts/results/topology_equivalence.json`. **Verification**: Assert `artifacts/results/sampling_validation.json` and `artifacts/results/topology_equivalence.json` exist and contain keys `['sampled_node_count', 'valid_bridging_count', 'valid_cluster_count', 'ks_p_value', 'ks_D_statistic', 'representativeness_passed']`. **Prerequisite**: T012a, T040, T013, T014.
- [ ] T016 [US1] Save processed graph with clusters and coefficients to `data/processed/subgraph_with_clusters.parquet`: Write the graph data to Parquet format using `pandas.to_parquet`. **Verification**: Assert file exists, contains columns `['id', 'primary_cluster', 'bridging_coefficient']`, and generate `sha256sum` of the file, writing the hash to `state/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l.yaml` under `artifact_hashes`. **Note**: Artifact integrity will be verified by the global hash mechanism in Phase 5. **Prerequisite**: T012, T013, T014, T012b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Outcome Variable Derivation (Citations and Novelty) (Priority: P2)

**Goal**: Extract citation counts and compute novelty scores using text-based clustering (k-means) independent of graph topology, using centroid distance for novelty.

**Independent Test**: Can be tested by processing a batch of nodes, verifying citation counts are non-negative integers, and novelty scores are positive floats (with 0.0 allowed for singletons), with a check confirming nodes with identical titles have zero novelty distance.

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for embedding output in `tests/contract/test_embedding_schema.py` with function `test_embedding_dimensions`.
- [X] T019 [P] [US2] Integration test for novelty calculation in `tests/integration/test_novelty_calculation.py` with function `test_novelty_centroid_distance`. **Prerequisite**: T024 (dataset must exist).

### Implementation for User Story 2

- [X] T020 [US2] Implement `src/services/embeddings.py`: Load `sentence-transformers/all-MiniLM-L6-v2` (CPU mode) and generate embeddings for all **valid** node titles. **Logic**: Filter out nodes with empty or null titles (log excluded IDs to stdout/stderr with reason "empty_title" or "null_title") and retain them in the dataframe with null novelty scores. Generate embeddings in **batches**. **Prerequisite**: None (filtering logic integrated). **Function**: `generate_embeddings_batch(texts)`. **Verification**: Assert max latency per node <= 50ms in unit test `tests/bench/test_embedding_speed.py` (See plan.md Complexity Tracking: Batched Embedding).
- [X] T021 [US2] Implement `src/services/clustering.py`: Perform k-means clustering (k=100) on title embeddings to assign `topic_cluster` IDs (independent of Louvain) (See FR-008). **Prerequisite**: T020.
- [ ] T022 [US2] Implement novelty calculation: Compute **cosine distance between each node's title embedding and the centroid of its OWN topic_cluster** to derive the `novelty_score`, ensuring the predictor (topology) and outcome (novelty) are mathematically independent. **Logic**: For each node, calculate cosine distance to its own cluster centroid. **Edge Case Handling**: If a node is the *only* member of its cluster (singleton), assign `novelty_score=0.0`. For non-singleton nodes, novelty scores must be positive floats. **Output**: Add `novelty_score` column to the dataframe. **Verification**: Link to test `test_novelty_centroid_distance` in T019. **Note**: While the spec's independent test mentions "positive floats", 0.0 is a valid edge case for singletons/perfect matches. **Prerequisite**: T020, T021.
- [ ] T024 [US2] Save final dataset with citations, novelty scores, and clusters to `data/processed/final_analysis_dataset.parquet`. **Verification**: Assert file exists, contains columns `['id', 'citation_count', 'novelty_score', 'primary_cluster', 'topic_cluster']`, and passes schema validation against `specs/001-bridging-coefficient-analysis/contracts/final_dataset_schema.schema.yaml`. **Prerequisite**: T020, T021, T022, T016.
- [ ] T025 [US2] Validate final dataset schema: Implement function `validate_final_dataset_schema(df)` in `src/services/ingest.py` to validate the final dataset against `specs/001-bridging-coefficient-analysis/contracts/final_dataset_schema.schema.yaml` before analysis. **Verification**: Assert test passes and logs validation status. **Prerequisite**: T024.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Correlation Analysis (Priority: P3)

**Goal**: Perform Spearman correlation, linear regression, and multiple-comparison correction.

**Independent Test**: Can be tested by running the analysis on the computed dataset, verifying that p-values are returned and corrected, and findings are labeled "associational".

### Tests for User Story 3

- [X] T036 [P] [US3] Contract test for analysis output schema in `tests/contract/test_analysis_output_schema.py` with function `test_report_has_associational_label`.
- [ ] T037 [P] [US3] Integration test for full statistical pipeline in `tests/integration/test_statistical_pipeline.py` with function `test_binned_analysis_execution`. **Input**: `data/processed/final_analysis_dataset.parquet`. **Assertions**: Verify p-values are present, corrected, and the report contains the "associational" label. **Verification**: Assert `artifacts/results/analysis_report.md` exists and contains "associational", and `artifacts/results/corrected_pvalues.json` exists. **Note**: This test will fail if the input dataset is missing or invalid. **Prerequisite**: T025, T029.

### Implementation for User Story 3

- [X] T026 [US3] Implement `src/services/analysis.py`: Calculate Spearman rank correlation between `bridging_coefficient` and `citation_count`/`novelty_score` (See FR-005).
- [X] T027 [US3] Perform Linear Regression: Implement `linear_regression` function in `src/services/analysis.py` to model the relationship between bridging coefficient and outcomes. **Mandatory**: This task must include **covariates** (`publication_year`, `primary_cluster_size`) to control for confounds. **Prerequisite**: T026.
- [X] T028 [US3] Apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) to all p-values (from T026, T027), **configurable via a CLI flag** to allow selection of method (See FR-006). **Output**: Write corrected p-values to `artifacts/results/corrected_pvalues.json`. **Verification**: Assert `artifacts/results/corrected_pvalues.json` contains keys `['method', 'raw_pvalues', 'corrected_pvalues', 'significant_count']`.
- [X] T030 [US3] Save statistical outputs (coefficients, p-values, plots) to `artifacts/results/statistical_metrics.json`. **Prerequisite**: T026, T027, T028.
- [X] T030b [US3] Generate binned analysis plots: Implement `generate_binned_plots(df)` in `src/services/analysis.py` to create binned analysis plots (e.g., bridging coefficient vs citation count bins) and save to `artifacts/results/`. **Verification**: Assert plot files exist in `artifacts/results/`. **Prerequisite**: T026, T027.
- [ ] T029 [US3] Generate final report in `artifacts/results/analysis_report.md` explicitly labeling results as "associational" (See FR-007). **Format**: Markdown with sections: '## Methodology', '## Correlation Results', '## Regression Results', '## Conclusion'. **Verification**: Assert report contains "associational" and NOT "causal". **Mandatory**: This task MUST ingest the corrected p-values from `artifacts/results/corrected_pvalues.json` (output of T028) for all reported statistics. **Prerequisite**: T026, T027, T028, T030, T030b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Code cleanup and refactoring for memory efficiency (Ingest): Refactor data loading functions in `src/services/ingest.py` to use **generator expressions** for row iteration to reduce peak RAM. **Specifics**: Replace `pandas.read_parquet` with `pyarrow.parquet.ParquetFile` streaming reader for large files. **Verification**: Run memory test T039b.
- [X] T032b [P] Code cleanup and refactoring for memory efficiency (Embeddings): Modify `src/services/embeddings.py` to use a **generator for yielding batches** to ensure strict batch processing. **Verification**: Run test T032c.
- [X] T032c [P] Memory test (Embeddings): Add test `tests/unit/test_embeddings.py::test_batch_memory_release` that asserts memory drops between batches.
- [X] T033 [P] Verify embedding performance against SC-005: Create `tests/bench/test_embedding_speed.py` to run a benchmark on a representative sample, measure **maximum latency per node**, and assert that the max latency is ≤ 50ms. The test must fail if the threshold is exceeded, providing evidence that SC-005 is met.
- [X] T034 [P] Additional unit tests for edge cases (isolated nodes, single-node clusters) in `tests/unit/test_graph_utils.py`: Implement functions `test_isolated_node` and `test_single_node_cluster`. **Logic**: Ensure isolated nodes get bridging=0.0 and single-node clusters handle centroid distance=0.0 correctly.
- [X] T035 [P] Validate data source reachability: Create `tests/unit/test_data_source.py` to verify the OpenAlex API endpoint is reachable and `datasets` can fetch a sample record before running the full pipeline.
- [X] T039 [P] Add memory profiling: Integrate `memory_profiler` into `src/services/ingest.py` and `src/services/embeddings.py` to log peak RAM usage per batch. **Output**: Generate `artifacts/results/memory_profile.log`. **Verification**: Assert `artifacts/results/memory_profile.log` exists and contains a line matching regex `Peak RAM: [-9.]+ GB <= <MAX_RAM_GB>` where `<MAX_RAM_GB>` is the value read from `src/models/config.py`.
- [X] T039b [P] Enforce memory constraint: Create `tests/unit/test_memory_constraint.py` that runs the pipeline with a mock dataset and asserts peak RAM usage remains within acceptable system limits (<= `src/models/config.py`'s `MAX_RAM_GB`), failing the build if exceeded. **Prerequisite**: Completion of T032, T032b.
- [X] T038 [P] Run `quickstart.md` validation: Execute command `python -m src.cli.main --run-validation` and generate `artifacts/validation_report.md`. **Content Requirements**: Must contain exit code 0, artifact hashes, and runtime duration. **Verification**: Assert `artifacts/validation_report.md` exists and contains strings `['Exit Code: 0', 'Artifact Hashes:', 'Runtime Duration:']`.
- [X] T042 [US1] Add data validation task: Create `tests/unit/test_ingest.py::test_real_data_integrity` that asserts the fetched data contains no nulls in critical fields (`id`, `title`, `cited_by_count`). **Verification**: Assert test passes.
- [X] T043 [US2] Implement embedding batch validation: Add a check in `src/services/embeddings.py` to verify that every batch of embeddings has the correct dimension (consistent with the model architecture for `all-MiniLM-L6-v2`) and no NaN values. **Verification**: Assert `ValueError` is raised if check fails.
- [X] T045 [US3] Implement reproducibility audit trail: Create a script `scripts/audit_reproducibility.py` that re-runs the entire pipeline on a fresh dataset and compares the output hashes of `artifacts/results/*` using `sha256`. **Logic**: Compare sha256 of all files; exit code 0 if match, 1 if mismatch. **Prerequisite**: All prior analysis tasks. **Verification**: Assert script runs and exits correctly.
- [X] T046 [US1] **Data Integrity Review**: Implement `tests/unit/test_ingest.py::test_streaming_data_integrity` to verify that the streaming ingestion logic correctly handles partial reads and does not drop nodes at stream boundaries. **Verification**: Assert that the node count in the processed graph matches the expected count from the stream metadata.
- [X] T047 [US2] **Novelty Baseline Check**: Add a unit test `tests/unit/test_metrics.py::test_novelty_baseline` that verifies the novelty score calculation returns 0.0 for a node whose title is identical to the centroid of its cluster (simulating a perfect match) OR the distance to the nearest other cluster if the node is a singleton. **Verification**: Assert the test passes with a sufficiently tight tolerance.
- [X] T048 [US3] **Correlation Robustness**: Implement `tests/unit/test_analysis.py::test_correlation_robustness` to verify that the Spearman correlation results are stable across different random seeds when applied to the same dataset. **Verification**: Assert that the correlation coefficient exhibits negligible variation across multiple runs with different seeds.
- [X] T049 [US1] **Streaming Buffer Edge Case**: Add a unit test `tests/unit/test_ingest.py::test_stream_buffer_boundary` that specifically injects a mock stream where the `MAX_BUFFER_ROWS` limit is hit exactly at a record boundary and verifies the `RuntimeError` is raised with the correct count and no partial records are included. **Prerequisite**: T040.
- [X] T050 [US2] **Singleton Cluster Novelty**: Add a unit test `tests/unit/test_metrics.py::test_singleton_novelty_calculation` that constructs a synthetic dataset where exactly one node forms a cluster of size 1, and verifies the novelty score calculation handles the "distance to own cluster centroid" logic without crashing or returning NaN. **Prerequisite**: T022.
- [X] T051 [US3] **Covariate Collinearity Check**: Implement a check in `src/services/analysis.py` (within the linear regression task) to detect and warn if the covariates (publication year, cluster size) exhibit high variance inflation factors (VIF > 5) before running the regression, logging a warning to `artifacts/results/regression_warnings.log`. **Verification**: Create a synthetic test dataset with known collinearity (e.g., `publication_year` and `cluster_size` perfectly correlated) and assert the log file is created and contains the warning message. **Prerequisite**: T027.
- [X] T052 [US3] **Report Formatting Validation**: Add an integration test `tests/integration/test_report_generation.py` that parses the generated `artifacts/results/analysis_report.md` and asserts it contains the exact phrase "associational" and does NOT contain the phrase "causal" or "causes". **Verification**: Assert the test passes. **Prerequisite**: T029.
- [X] T054 [US3] **Runtime Validation**: Implement `scripts/measure_runtime.py` to measure total pipeline runtime and write to `artifacts/results/runtime_report.json`. **Verification**: Assert file exists and contains `total_runtime_seconds` <= 21600 (6 hours). **Prerequisite**: T012, T013, T014, T020, T021, T022, T026, T027, T028, T029, T030, T030b.
- [X] T055 [US3] **Memory Profiling**: Implement `scripts/profile_memory.py` to run the pipeline with memory profiling enabled and write `artifacts/results/memory_report.json` with peak RAM usage. **Verification**: Assert file exists and contains `peak_ram_gb` <= 7.0. **Prerequisite**: T032, T032b, T039.
- [X] T056 [US3] **Embedding Latency Check**: Implement `scripts/check_embedding_latency.py` to measure embedding inference time per node and write `artifacts/results/latency_report.json`. **Verification**: Assert file exists and contains `max_latency_ms` <= 50. **Prerequisite**: T020, T033.
- [X] T057 [US1] **Streaming Chunking Strategy**: Implement `src/services/ingest.py` logic to explicitly define and log the chunk size used during streaming ingestion (e.g., `chunksize=10000`) to ensure deterministic memory behavior. **Verification**: Assert `artifacts/results/streaming_config.log` contains the defined chunk size and that the pipeline does not exceed `MAX_RAM_GB` when processing a mock stream of a large-scale row count. **Prerequisite**: T040.
- [X] T058 [US2] **Embedding Model Version Pinning**: Update `pyproject.toml` and `src/services/embeddings.py` to explicitly pin the `sentence-transformers` model version (e.g., `all-MiniLM-L6-v2@2.2.2`) and verify the loaded model matches this version at runtime. **Verification**: Assert `artifacts/results/model_versions.json` contains the exact version string and that the test fails if the version mismatches. **Prerequisite**: T020.
- [X] T053 [US3] **Verify Hash Integrity**: Implement `scripts/verify_hashes.py` to calculate `sha256sum` of all files in `data/` and `artifacts/` and compare against `state/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l.yaml` under the `artifact_hashes` key. **Verification**: Assert script exits with code 0 if hashes match, 1 if mismatch. **Prerequisite**: T016, T024, T025, T028, T029, T030, T030b, T054, T055, T056.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately (except T012c blocks T012, T040, T012a).
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
- [GLOBAL] label maps task to project-wide scope (e.g., spec amendments)
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on a multi-core CPU with sufficient memory and a time limit. No GPU, no low-bit quantization.
- **Data Source**: Use `datasets.load_dataset` for OpenAlex data; ensure sampling strategy fits memory limits.
- **Spec Drift**: Resolved by T012c (Formal amendment of spec.md and plan.md).
- **Non-Circular Validation**: Ensured by T034 (Edge case tests) and strict separation of T021 (Text Clustering) and T013 (Topological Clustering).
- **Temporal Validity**: Temporal validation tasks (T025, T028a) removed as they were scope creep not traceable to spec.
- **Data Integrity**: New tasks T046, T047, T048 added to address specific review concerns regarding streaming robustness, novelty baseline correctness, and correlation stability.
- **Novelty Definition**: Novelty is defined as cosine distance to the node's OWN topic_cluster centroid, measuring deviation from the topic mean. Singleton clusters are assigned 0.0.
- **Edge Case Coverage**: New tasks T049, T050, T051, T052 added to rigorously test buffer boundaries, singleton cluster handling, covariate collinearity, and report phrasing constraints.
- **Validation Steps**: New tasks T053-T056 added to explicitly implement and verify hash integrity, runtime, memory, and latency constraints as required by the plan.
- **Streaming Robustness**: New tasks T057 added to ensure deterministic memory behavior.
- **Model Reproducibility**: New task T058 added to pin model versions.
- **Statistical Rigor**: Removed T059 (Statistical Power Analysis) as it was identified as scope creep.
- **Removed Tasks**: T059, T060, T061 removed due to lack of traceability to spec.md.