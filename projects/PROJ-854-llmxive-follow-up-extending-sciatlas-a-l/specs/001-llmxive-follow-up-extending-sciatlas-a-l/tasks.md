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
- [X] T002 Initialize Python 3.11 project with `pyproject.toml` at repository root: Define `[build-system]` (requires=["setuptools", "wheel"]), `[project]` (name, version, dependencies list including `networkx`, `scikit-learn`, `sentence-transformers`, `pandas`, `numpy`, `scipy`, `pyalex`, `memory-profiler`, `pytest`, `ruff`, `black`), and `[tool.black]`/`[tool.ruff]` sections. **Verification**: Assert `pyproject.toml` contains section `[project.dependencies]` with all listed packages and run `pip check` to verify no conflicts.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Append `[tool.ruff]` section to existing `pyproject.toml` with `select=['E402', 'F401', 'I001']` and `ignore=[]`. **Verification**: Run `ruff check.` and assert exit code 0.
- [X] T012c [US1] **BLOCKING**: Amend spec.md: Update `specs/001-bridging-coefficient-analysis/spec.md` to replace all references to "PubGraph" with "OpenAlex" and update FR-001 to mandate "OpenAlex" dataset. Document the justification for this data source change in the Assumptions section. **Verification**: Confirm `spec.md` no longer mentions "PubGraph", FR-001 explicitly mentions "OpenAlex", and includes a "Data Source Justification" note. **Prerequisite**: Must be completed before T012.
- [X] T031a [P] Documentation updates (Prerequisites): Insert the string "pyalex>=1.0" and "sentence-transformers" into the "Prerequisites" section of `specs/001-bridging-coefficient-analysis/quickstart.md`. **Verification**: Assert `quickstart.md` contains string "pyalex>=1.0" and "sentence-transformers" in the Prerequisites section.
- [X] T031b [P] Documentation updates (Run): Insert the command "python -m src.cli.main --sample-size 1000" into the "Run" section of `specs/001-bridging-coefficient-analysis/quickstart.md`. **Verification**: Assert `quickstart.md` contains string "python -m src.cli.main --sample-size 1000" in the Run section.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Prerequisite**: T040 and T041 must be completed before T012.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Configure `pytest` with `conftest.py` for seed pinning and coverage: Create `tests/conftest.py` with `pytest_configure` hook that calls `random.seed(42)` and `numpy.random.seed(42)` at module import. Create `pytest.ini` with `[pytest]` section containing `addopts = --cov --cov-report=term-missing --log-cli-level=INFO`. **Verification**: Run `pytest --collect-only` to confirm flags are active.
- [X] T004 [P] Setup `src/lib/config.py` for constants, random seeds, and paths: Create file with variables `SEED=42`, `DATA_PATH='data/'`, `ARTIFACT_PATH='artifacts/'`. **Verification**: Assert `config.py` imports successfully and exports `SEED=42`.
- [X] T005 [P] Implement `src/models/node.py` dataclass: Define fields `id`, `title`, `citation_count`, `embedding_vector`, `primary_cluster`, `topic_cluster`. **Verification**: Assert file exists, contains `@dataclass` decorator, and run `tests/unit/test_node_instantiation.py`.
- [X] T006 [P] Create `src/models/graph_utils.py` with stub signatures: Define `louvain_cluster(G)` and `calc_bridging(G, clusters)` functions. **Verification**: Assert file exists and functions raise `NotImplementedError`.
- [X] T007 [P] Setup `tests/contract/test_schemas.py`: Load `specs/001-bridging-coefficient-analysis/contracts/node.schema.yaml` and `analysis_output.schema.yaml`. Create `test_schema_validation` function. **Verification**: Assert file exists and test passes on valid YAML.
- [X] T040 [US1] **BLOCKING**: Implement strict data fetcher with NO synthetic fallback: Refactor `src/services/ingest.py` to remove any `try/except` blocks that catch download errors and substitute synthetic data. If `pyalex` fails to fetch data, the script MUST raise a `RuntimeError` with message "Data fetch failed: <error>". **Verification**: Assert `RuntimeError` is raised on failure with message containing "Data fetch failed".
- [ ] T041 [US1] **BLOCKING**: Implement explicit streaming logic: Modify `src/services/ingest.py` to use `pyalex` streaming iterator with `chunk_size=1000` to process OpenAlex data in batches, accumulating results to `data/raw/openalex_stream.parquet` without loading the entire subgraph into RAM. **Verification**: Assert data is written in chunks and peak RAM < 7GB on sample data.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Topological Metric Computation (Priority: P1) 🎯 MVP

**Goal**: Download OpenAlex subgraph, assign structural clusters (Louvain), and compute bridging coefficients.
**Independent Test**: Can be fully tested by running the ingestion pipeline on a sampled subgraph and verifying that every node has a valid `bridging_coefficient` (0.0 to 1.0) and `primary_cluster` label, with no memory errors on CPU.

### Tests for User Story 1

- [X] T010 [P] [US1] Contract test for node schema in `tests/contract/test_node_schema.py` with function `test_node_has_required_fields`.
- [X] T011 [P] [US1] Integration test for ingestion pipeline on sample data in `tests/integration/test_ingest_pipeline.py` with function `test_ingest_creates_subgraph`.

### Implementation for User Story 1

- [X] T012 [US1] Implement `src/services/ingest.py`: Fetch OpenAlex data via `pyalex` with **degree-stratified random sampling** to target subgraph size. **Prerequisite**: T012c (Spec Amendment completed), T040 (Strict Fetch), T041 (Streaming). (See plan.md Complexity Tracking: Degree-Stratified Sampling).
- [ ] T012a [US1] Implement degree-stratified random sampling: Create function `sample_subgraph(G, target_size)` in `src/services/ingest.py` that groups nodes by degree percentile (low, medium, high) and samples proportionally. **Verification**: Add unit test `tests/unit/test_ingest.py::test_sample_subgraph_preserves_degree_distribution` that asserts the sampled degree histogram matches the full graph within tolerance **0.05** (5% KS statistic).
- [ ] T012b [US1] Validate subgraph representativeness: Create function `validate_sampled_graph(G_full, G_sampled)` in `src/services/ingest.py` that computes and asserts the degree distribution of `G_sampled` matches `G_full` within a specified tolerance. **Output**: Write report to `artifacts/results/sampling_validation.json`. **Verification**: Assert `artifacts/results/sampling_validation.json` exists and contains keys `['full_degree_dist', 'sampled_degree_dist', 'ks_statistic', 'p_value']`.
- [X] T013 [US1] Implement `src/services/clustering.py`: Run Louvain community detection on the graph `G` to assign `primary_cluster` IDs (See FR-002).
- [X] T014 [US1] Implement `src/models/graph_utils.py`: **Complete the implementation** of `calc_bridging(G, clusters)` to calculate `bridging_coefficient` for each node (inter-cluster edges / total degree). **Edge Case Handling**: Explicitly handle degree-0 nodes by assigning `bridging_coefficient=0.0` to prevent division-by-zero (See spec.md Edge Cases).
- [ ] T016 [US1] Save processed graph with clusters and coefficients to `data/processed/subgraph_with_clusters.parquet`: Write the graph data to Parquet format using `pandas.to_parquet`.
- [ ] T016a [US1] Verify saved graph artifact: Create function `verify_parquet()` in `tests/unit/test_graph_utils.py` that asserts `data/processed/subgraph_with_clusters.parquet` exists and contains columns `[id, title, citation_count, primary_cluster, bridging_coefficient]` with **no null values** in `primary_cluster` or `bridging_coefficient`. <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Outcome Variable Derivation (Citations and Novelty) (Priority: P2)

**Goal**: Extract citation counts and compute novelty scores using text-based clustering (k-means) independent of graph topology, using centroid distance for novelty.

**Independent Test**: Can be tested by processing a batch of nodes, verifying citation counts are non-negative integers, and novelty scores are positive floats, with a check confirming nodes with identical titles have zero novelty distance.

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for embedding output in `tests/contract/test_embedding_schema.py` with function `test_embedding_dimensions`.
- [X] T019 [P] [US2] Integration test for novelty calculation in `tests/integration/test_novelty_calculation.py` with function `test_novelty_centroid_distance`.

### Implementation for User Story 2

- [ ] T023a [US2] Implement filtering logic (Empty Titles): Modify `src/services/embeddings.py` to filter out nodes with **empty string** titles **before** novelty calculation. **Logic**: Exclude from centroid calculation but **RETAIN** in the final dataset with `novelty_score` set to `null`. Log excluded node IDs to `data/logs/excluded_nodes.csv` with reason "empty_title". **Verification**: Assert `data/logs/excluded_nodes.csv` exists with columns `['node_id', 'reason']` and contains at least one row if empty titles exist in test data.
- [ ] T023b [US2] Implement filtering logic (Null Titles): Modify `src/services/embeddings.py` to filter out nodes with **null/missing** (None) titles **before** novelty calculation. **Logic**: Exclude from centroid calculation but **RETAIN** in the final dataset with `novelty_score` set to `null`. Append to `data/logs/excluded_nodes.csv` with reason "null_title". **Verification**: Assert `data/logs/excluded_nodes.csv` contains rows for null titles with reason "null_title".
- [ ] T023c [US2] Verify edge case handling: Create test `tests/unit/test_embeddings.py::test_empty_title_handling` that asserts nodes with empty or null titles are retained in the dataframe but have `null` novelty scores.
- [ ] T020 [US2] Implement `src/services/embeddings.py`: Load `sentence-transformers/all-MiniLM-L6-v2` (CPU mode) and generate embeddings for all **valid** node titles (filtered by T023a/T023b) in **batches of 64**. **Prerequisite**: T023a, T023b. **Function**: `generate_embeddings_batch(texts)`. **Verification**: Assert max latency per node <= 50ms in unit test `tests/bench/test_embedding_speed.py` (See plan.md Complexity Tracking: Batched Embedding).
- [X] T021 [US2] Implement `src/services/clustering.py`: Perform k-means clustering (k=100) on title embeddings to assign `topic_cluster` IDs (independent of Louvain) (See FR-008). **Prerequisite**: T020.
- [X] T022 [US2] Implement novelty calculation: Compute **cosine distance** between each node's title embedding and the **centroid** of its assigned `topic_cluster` to derive the `novelty_score`, ensuring the predictor (topology) and outcome (novelty) are mathematically independent. **Output**: Add `novelty_score` column to the dataframe. **Verification**: Link to test `test_novelty_centroid_distance` in T019. **Prerequisite**: T021.
- [ ] T025 [US2] Calculate temporal lag variables: Implement function `calc_temporal_lags(df)` in `src/services/ingest.py` to compute `years_since_publication` and `citation_window` based on metadata. **Output**: Add `years_since_publication` and `citation_window` columns to the dataframe. **Verification**: Assert dataframe contains columns `['years_since_publication', 'citation_window']`.
- [ ] T024 [US2] Save final dataset with citations, novelty scores, and clusters to `data/processed/final_analysis_dataset.parquet`.

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
- [X] T027 [US3] Perform Linear Regression: Implement `linear_regression` function in `src/services/analysis.py` to model the relationship between bridging coefficient and outcomes. **Mandatory**: This task must be completed to satisfy FR-005.
- [X] T027c [US3] Perform Binned Non-Linear Analysis: Implement `binned_analysis` function in `src/services/analysis.py` to detect non-monotonic relationships. **Strategy**: Use **quantile bins, k=10**. **Output**: Write results to `artifacts/results/binned_analysis.json` with keys `['bin_edges', 'mean_bridging', 'mean_citations']`. **Prerequisite**: T027.
- [X] T028a [US3] Validate temporal lag significance: Perform statistical test on `years_since_publication` (from T025) to ensure it significantly correlates with citation count, validating the "future impact" claim (See Spec Assumptions). **Output**: Write results to `artifacts/results/temporal_validation.json`. **Prerequisite**: T025.
- [X] T028 [US3] Apply multiple-comparison correction (Bonferroni or Benjamini-Hochberg) to all p-values (from T026, T027, T027c, T028a), **configurable via a CLI flag** to allow selection of method (See FR-006). **Output**: Write corrected p-values to `artifacts/results/corrected_pvalues.json`. **Verification**: Assert `artifacts/results/corrected_pvalues.json` contains keys `['method', 'raw_pvalues', 'corrected_pvalues', 'significant_count']`.
- [X] T029 [US3] Generate final report in `artifacts/results/analysis_report.md` explicitly labeling results as "associational" (See FR-007).
- [X] T030 [US3] Save statistical outputs (coefficients, p-values, plots) to `artifacts/results/statistical_metrics.json`.
- [X] T044 [US3] Implement statistical power analysis: Implement function `calculate_power` in `src/services/analysis.py` using `statsmodels.stats.power.tt_solve_power` to calculate power given sample size and effect size. **Output**: Append power analysis results to `artifacts/results/analysis_report.md` with keys `['power', 'effect_size', 'n_obs']`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Code cleanup and refactoring for memory efficiency (Ingest): Refactor data loading functions in `src/services/ingest.py` to use **generator expressions** for row iteration to reduce peak RAM. **Verification**: Run memory test T039b.
- [ ] T032b [P] Code cleanup and refactoring for memory efficiency (Embeddings): Modify `src/services/embeddings.py` to use a **generator for yielding batches** to ensure strict batch processing. **Verification**: Run test T032c.
- [ ] T032c [P] Memory test (Embeddings): Add test `tests/unit/test_embeddings.py::test_batch_memory_release` that asserts memory drops between batches.
- [X] T033 [P] Verify embedding performance against SC-005: Create `tests/bench/test_embedding_speed.py` to run a benchmark on a representative sample, measure **maximum latency per node**, and assert that the max latency is ≤ 50ms. The test must fail if the threshold is exceeded, providing evidence that SC-005 is met.
- [X] T034 [P] Additional unit tests for edge cases (isolated nodes, single-node clusters) in `tests/unit/test_graph_utils.py`: Implement functions `test_isolated_node` and `test_single_node_cluster`. **Logic**: Ensure isolated nodes get bridging=0.0 and single-node clusters handle centroid distance=0.0 correctly.
- [X] T035 [P] Validate data source reachability: Create `tests/unit/test_data_source.py` to verify the OpenAlex API endpoint is reachable and `pyalex` can fetch a sample record before running the full pipeline.
- [ ] T039 [P] Add memory profiling: Integrate `memory_profiler` into `src/services/ingest.py` and `src/services/embeddings.py` to log peak RAM usage per batch. **Output**: Generate `artifacts/results/memory_profile.log`. **Verification**: Assert `artifacts/results/memory_profile.log` exists and contains a line matching regex `Peak RAM: [0-9.]+ GB <= 7.0 GB`.
- [X] T039b [P] Enforce memory constraint: Create `tests/unit/test_memory_constraint.py` that runs the pipeline with a mock dataset and asserts peak RAM usage remains within acceptable system limits, failing the build if exceeded. **Prerequisite**: Completion of T032, T032b.
- [X] T038 [P] Run `quickstart.md` validation: Execute command `python -m src.cli.main --run-validation` and generate `artifacts/validation_report.md`. **Content Requirements**: Must contain exit code 0, artifact hashes, and runtime duration. **Verification**: Assert `artifacts/validation_report.md` exists and contains strings `['Exit Code: 0', 'Artifact Hashes:', 'Runtime Duration:']`.
- [ ] T042 [US1] Add data validation task: Create `tests/unit/test_ingest.py::test_real_data_integrity` that asserts the fetched data contains no nulls in critical fields (`id`, `title`, `cited_by_count`) and that the number of rows matches the requested sample size exactly (within a small tolerance of **5%**). **Verification**: Assert test passes with 5% tolerance.
- [ ] T043 [US2] Implement embedding batch validation: Add a check in `src/services/embeddings.py` to verify that every batch of embeddings has the correct dimension (consistent with the model architecture for `all-MiniLM-L6-v2`) and no NaN values. **Verification**: Assert `ValueError` is raised if check fails.
- [X] T045 [US3] Implement reproducibility audit trail: Create a script `scripts/audit_reproducibility.py` that re-runs the entire pipeline on a fresh dataset and compares the output hashes of `artifacts/results/*` using `sha256`. **Logic**: Compare sha256 of all files; exit code 0 if match, 1 if mismatch. **Verification**: Assert script runs and exits correctly.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately (except T012c blocks T012).
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Prerequisites**: T040, T041 must be complete.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

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
- **Exploratory Analysis**: Binned non-linear analysis (T027c) is now mandatory to satisfy plan's Complexity Tracking.
- **Non-Circular Validation**: Ensured by T034 (Edge case tests) and strict separation of T021 (Text Clustering) and T013 (Topological Clustering).
- **Temporal Validity**: Ensured by T025 and T028a (Temporal lag validation).
