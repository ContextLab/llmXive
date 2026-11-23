# Tasks: Predicting Plant Pathogen Virulence from Publicly Available Genomic and Phenotypic Data

**Input**: Design documents from `/specs/001-predict-plant-pathogen-virulence/`
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

- [X] T001 Create directory structure: `src/`, `tests/`, `data/raw`, `data/processed`, `output`, `src/data`, `src/analysis`, `src/viz`, `src/models`, `src/utils`. **Dependencies**: None. **Output**: Empty directories ready for code.
- [X] T002 Create `.gitignore` and `src/utils/config.py` for seed pinning, path management, and environment variables. **Deliverable**: `config.py` must define `SEED` (int), `DATA_ROOT` (str), `API_TIMEOUT` (int), and `LOG_LEVEL` (str) constants.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools. **Deliverable**: Create `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections defining specific rules (e.g., line-length=88, select=["E", "F", "I"]).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented, including Phylogenetic Tree Construction (per Plan Phase 1), Unified Error Handling, Data Hygiene, and Schema Definitions.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes the Tree Construction tasks (T026, T027), Unified Error Handling (T059), Data Hygiene (T051, T055), and Schema Definition (T031c) which are prerequisites for all statistical analysis and data fetching.

- [X] T004 [P] Implement `src/utils/logging.py` with exponential backoff logic for network retries
- [X] T006 [P] Define `src/models/isolate.py`: Class `Isolate` (fields: strain_id, species, genome_path, phenotype_score, metadata). **Note**: Phenotypic score is a field here, not a separate class.
- [X] T007 [P] Define `src/models/genomic_feature.py`: Class `GenomicFeature` (fields: feature_id, type, presence_binary, pwm_count, source)
- [X] T008 [P] Define `src/models/species_aggregate.py`: Class `SpeciesAggregate` (fields: species_name, avg_phenotype, isolate_count, variance). **Dependency**: Must be completed before T020.
- [X] T009 [P] Setup `requirements.txt` with exact pinned versions for reproducibility (FR-010)
- [X] T059 [P] [US1/US2] Implement `src/utils/errors.py` and update `src/data/download.py` / `src/analysis/correlation.py`: **Unified Fail Loudly Error Handling**. **Requirement**: Define a single `DataFetchError` exception class with signature `__init__(self, url, status_code, context)`. Wrap ALL data ingestion (NCBI, PHI-base, hmmsearch) and analysis steps (Tree, PGLS, FDR) in this pattern. If ANY fetch, parsing, schema validation, model convergence, or FDR calculation fails after retries, raise `DataFetchError` with specific URL, HTTP status code, or context. **Constraint**: NO `try/except` block that catches this and returns synthetic/mock data. **Specifics**: Catch `requests.exceptions.*`, `JSONDecodeError`, `SchemaValidationError`, `statsmodels.convergence_error`, `ValueError` (NaN). **Justification**: Constitution Principle III (Data Hygiene) mandates strict failure modes to prevent silent fabrication. **Dependency**: T002. **Note**: This task must be completed before T015/T016 to ensure error handling is present during data fetch.
- [X] T026 [US2] Implement `src/analysis/phylogeny.py`: **Extract** core housekeeping genes (rpoB, gyrB, 16S) from the downloaded genome assemblies (`data/raw/*.fna`) using `biopython` or `prodigal`. **Constraint**: Use ONLY housekeeping genes, EXCLUDING virulence genes to prevent circularity (Constitution Principle VI). **Fallback**: If 16S is insufficient for *Fusarium* (fungi), retrieve reference tree from NCBI Taxonomy or use alternative core genes (e.g., RPB1, RPB2). **Pre-check**: Verify `data/raw/*.fna` exists (produced by T015) before extraction. **Output**: `data/processed/housekeeping_genes.fasta`. **Dependency**: T015, T059.
- [X] T027 [US2] Implement `src/analysis/phylogeny.py`: **Construct** phylogenetic tree using the extracted housekeeping gene sequences via Maximum Likelihood (IQ-TREE or RAxML). **Validation**: Verify `data/processed/tree.newick` and `data/processed/phylo_covariance_matrix.npy` are written, non-empty, and have non-zero branch lengths. **Output**: `data/processed/tree.newick` and `data/processed/phylo_covariance_matrix.npy`. **Dependency**: T026, T059. **Note**: These artifacts are REQUIRED inputs for T028a and T028b.
- [X] T031c [US2] Define the schema, content, and validation criteria for the 'Descriptive Case Study report' to be generated when N < 10. **Output**: `docs/case_study_schema.md`. **Required Sections**: 'Sample Size', 'Limitations', 'Aggregate Statistics', 'No P-Values'. **Required Data Fields**: `species_list` (list of strings), `phenotype_range` (tuple of min, max), `isolate_count` (int), `feature_count` (int). **Dependency**: None. **Note**: This task is moved to Phase 2 to ensure schema availability before any N < 10 logic is triggered.

**Checkpoint**: Foundation ready (including Phylogenetic Tree, Error Handling, Data Hygiene, and Case Study Schema) - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible Data Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Download specific plant pathogen genomes, extract virulence features, retrieve phenotypic scores, and merge into a clean dataset.

**Independent Test**: The pipeline can be run end-to-end on a clean environment; it must produce a single CSV/Parquet file containing aligned genomic feature vectors and phenotypic scores for at least 10 distinct isolates (or species aggregates), with all source URLs logged.

### Tests for User Story 1 ⚠️

- [X] T011 [US1] Unit test for NCBI E-utilities download logic in `tests/unit/test_download.py`. **Function**: `test_ncbi_eutil_retry_logic`. **Setup**: Mock `requests.get` to raise `ConnectionError` three times then succeed. **Assertion**: `assert "Retry attempt 1" in log_output` and `assert "Retry attempt 2" in log_output` and `assert DataFetchError` is NOT raised on 4th success. **Negative Test**: Mock `requests.get` to fail 5 times; `assert DataFetchError` is raised on 5th attempt with message containing "Failed to fetch real data". **Note**: Written to fail before implementation (TDD). Sequential to code existence.
- [X] T012 [US1] Unit test for PHI-base phenotype fetch and fallback logic in `tests/unit/test_download.py`. **Function**: `test_phibase_fetch_and_aggregation`. **Setup**: Mock isolate-level fetch to return 404, then mock species-level aggregation logic. **Assertion**: `assert "Species-level aggregation triggered" in log_output` if isolate linkage < 50%. **Negative Test**: If isolate linkage >= 50%, assert no aggregation log entry. **Note**: Written to fail before implementation (TDD). Sequential to code existence.
- [X] T013 [US1] Integration test for full download-extract-merge flow in `tests/integration/test_pipeline.py`. **Function**: `test_full_pipeline_flow`. **Setup**: Use a small, known subset of real data or mocked successful fetches. **Assertion**: `assert os.path.exists("data/processed/merged_dataset.parquet")` and `assert len(df) >= 10` and `assert "phenotype_score" in df.columns`. **Note**: Written to fail before implementation (TDD). Sequential to code existence.
- [X] T014 [US1] Contract test for output schema (CSV/Parquet) in `tests/contract/test_schemas.py`. **Function**: `test_output_schema_compliance`. **Assertion**: `assert "phenotype_score" in df.columns` and `assert df.dtypes['phenotype_score'] == float` and `assert "strain_id" in df.columns`. **Note**: Written to fail before implementation (TDD). Sequential to code existence.

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement `src/data/download.py`: Fetch *Fusarium graminearum*, *Pseudomonas syringae*, and *Xanthomonas* spp. genomes via `biopython` E-utilities with retry logic (FR-001). **Dependency**: T001, T002, T059.
- [X] T016 [P] [US1] Implement `src/data/download.py`: Retrieve phenotypic disease severity scores from PHI-base or literature tables; implement species-level aggregation fallback (FR-001, FR-009). **Dependency**: T001, T002, T059.
- [X] T017 [P] [US1] Implement `src/data/extract.py`: Run `hmmsearch` against PHI-base/Pfam libraries to generate binary virulence gene presence/absence matrix (FR-002). **Dependency**: T015.
- [X] T018 [P] [US1] Implement `src/data/extract.py`: Count transcription factor binding sites using Position Weight Matrices (PWMs) (FR-002). **Dependency**: T015.
- [X] T020 [US1] Implement `src/data/merge.py`: **Unified Merge and Aggregation Logic**. **Step 1**: Align genomic features with phenotypic scores by isolate/species ID; handle missing phenotypes by dropping rows and logging counts (FR-006). **Step 2**: Detect if `linked_isolate_count / total_isolate_count < 0.5`. **Step 3**: If true, aggregate by species (group by species_name, average phenotype, count isolates) and merge into the final analysis-ready dataset format. **Schema**: The output MUST match the schema of T019 (isolate_id, species, feature_vector, phenotype_score) exactly, replacing isolate_id with species_name if aggregated. **Output**: `data/processed/merged_dataset.parquet`. **Dependency**: T008, T017, T018, T059. **Note**: This single task replaces T020a/b/c to ensure a valid producer for T021 regardless of the aggregation path.
- [X] T021 [US1] Implement `src/data/merge.py`: Output final analysis-ready dataset (CSV/Parquet) to `data/processed/merged_dataset.parquet` and summary report (processed count, missing count) (FR-001, FR-006). **Dependency**: T020.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Association Analysis (Priority: P2)

**Goal**: Compute PGLS (N>=30) or Spearman (N<30) correlations, apply Benjamini-Hochberg FDR, and identify significant genomic-virulence associations.

**Independent Test**: The analysis script runs on the P1 output dataset and produces a ranked list of genomic features with correlation coefficients, p-values, and adjusted p-values, identifying a set of top candidates.

### Tests for User Story 2 ⚠️

- [X] T022 [US2] Unit test for housekeeping gene extraction and tree construction in `tests/unit/test_phylogeny.py`. **Function**: `test_housekeeping_gene_extraction`. **Setup**: Mock `biopython` to return a small FASTA with rpoB, gyrB. **Assertion**: `assert len(genes) > 0` and `assert "rpoB" in genes` and `assert "virulence_gene" not in genes`. **Note**: Written to fail before implementation (TDD). Sequential to code existence.
- [X] T023 [US2] Unit test for PGLS/Spearman calculation and BH FDR in `tests/unit/test_correlation.py`. **Function**: `test_benjamini_hochberg_correction`. **Setup**: Generate a small array of raw p-values (e.g., [0.01, 0.05, 0.03, 0.001]). **Assertion**: `assert adjusted_pvalues[0] <= raw_pvalues[0]` and `assert len(adjusted_pvalues) == len(raw_pvalues)` and `assert all(adjusted_pvalues >= 0)`. **Note**: Written to fail before implementation (TDD). Sequential to code existence.
- [X] T024 [US2] Unit test for FDR sensitivity check in `tests/unit/test_correlation.py`. **Function**: `test_fdr_sensitivity_check`. **Setup**: Run both BH and Permutation FDR on a mock dataset. **Assertion**: `assert "sensitivity_check" in output_columns` and `assert "raw_pvalue" in output_columns`. **Note**: Written to fail before implementation (TDD). Sequential to code existence.
- [X] T025 [US2] Integration test for full analysis pipeline (Tree -> Correlation -> FDR) in `tests/integration/test_pipeline.py`. **Function**: `test_analysis_pipeline_flow`. **Setup**: Use mock data files for tree and dataset. **Assertion**: `assert os.path.exists("data/processed/results.csv")` and `assert "adjusted_pvalue" in df.columns` and `assert "correlation_coefficient" in df.columns`. **Note**: Written to fail before implementation (TDD). Sequential to code existence.

### Implementation for User Story 2

- [X] T031a [US2] Implement `src/analysis/correlation.py`: Check sample size N after aggregation. **Output**: Flag `low_power` if N < 10, `medium_power` if 10 <= N < 30, `high_power` if N >= 30. **Dependency**: T021. **Note**: This task is the GATE for all subsequent statistical tasks.
- [X] T028a [US2] Implement `src/analysis/correlation.py`: **Execution (Spearman)**: Compute Phylogenetic Signal-Adjusted Spearman Rank Correlation between every extracted genomic feature and the phenotypic disease severity score vector (FR-004, Constitution Principle VI). **Input**: `data/processed/merged_dataset.parquet` (from T021) and `data/processed/tree.newick` (from T027). **Output**: Raw correlation coefficients and p-values to `data/processed/raw_correlations.csv`. **Constraint**: Spearman is mandatory for 10 <= N < 30. **Authorization**: For N < 10, this task is SKIPPED per Plan 'Power & Limitation Disclosure' and FR-009 fallback. **Dependency**: T021, T031a, T027, T059. **Orchestrator Note**: Execute ONLY if 10 <= N < 30. If N >= 30, skip to T028b. If N < 10, skip to T031b.
- [X] T028b [US2] Implement `src/analysis/correlation.py`: **Execution (PGLS)**: Compute Phylogenetic Generalized Least Squares (PGLS) correlations between every extracted genomic feature and the phenotypic disease severity score vector (FR-004). **Input**: `data/processed/merged_dataset.parquet` (from T021) and `data/processed/tree.newick` (from T027). **Output**: Raw correlation coefficients and p-values to `data/processed/raw_correlations.csv`. **Constraint**: PGLS is mandatory for N >= 30. **Authorization**: For N < 10, this task is SKIPPED per Plan 'Power & Limitation Disclosure' and FR-009 fallback. **Dependency**: T021, T031a, T027, T059. **Orchestrator Note**: Execute ONLY if N >= 30. If N < 30, skip to T028a or T031b.
- [X] T029a [US2] Implement `src/analysis/correlation.py`: **FDR Correction (N>=10)**: Apply **Benjamini-Hochberg (BH)** as the PRIMARY method (FR-005, Constitution Principle VI) to raw p-values to control the False Discovery Rate (FDR) at < 0.05. **Implementation**: Use standard BH algorithm with `random_state=42`. Implement Permutation-based FDR (1000 permutations, `random_state=42`) as a secondary/sensitivity check only. **Input**: Raw p-values from `data/processed/raw_correlations.csv` (from T028a or T028b). **Output**: Adjusted p-values to `data/processed/adjusted_pvalues.csv`. **Dependency**: T028a (if N<30) OR T028b (if N>=30), T059. **Orchestrator Note**: Ensure `raw_correlations.csv` is populated by T028a or T028b before this task runs. Skip if N < 10.
- [X] T029b [US2] Implement `src/analysis/correlation.py`: **No FDR (N<10)**: Generate a placeholder output file `data/processed/adjusted_pvalues.csv` with a single row indicating 'No FDR applied (N<10)' and `p_value=NaN`. **Justification**: Required by FR-009 and US-2 Edge Cases for graceful degradation. **Dependency**: T031a, T031c, T021. **Note**: T031c must be marked [X] (complete) before T029b can run.
- [X] T030 [US2] Implement `src/analysis/correlation.py`: Filter results for visualization (|ρ| ≥ 0.5) while retaining all significant features (FDR < 0.05) in raw output (FR-007). **Dependency**: T029a (if N>=10). **Orchestrator Note**: Skip if N < 10.
- [X] T031b [US2] Implement `src/analysis/correlation.py`: If N < 10, generate Descriptive Case Study report to `output/case_study_report.md` using the schema from T031c (sanctioned fallback per Plan Power & Limitation Disclosure). **Justification**: Required by FR-009 and US-2 Edge Cases for graceful degradation. This task bypasses FR-004 statistical computation as authorized by the Plan. **Dependency**: T031a, T031c, T021. **Note**: T031c must be marked [X] (complete) before T031b can run.
- [X] T032 [US2] Output ranked table of features with coefficients, p-values, and adjusted p-values to `data/processed/results.csv`. If N < 10, include a 'low_power' flag and descriptive summary in metadata (FR-004, FR-005). **Dependency**: T030 (if N>=10), T031b (if N<10), T021. **Orchestrator Note**: If N < 10, depend on T031b. If N >= 10, depend on T030.
- [X] T033 [US2] Implement metric calculation: Calculate and report **Success Rate (SC-001)** and **Proportion of Significant Features (SC-004)** in the final summary report. (SC-001, SC-004). **Dependency**: T032.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reproducibility Reporting (Priority: P3)

**Goal**: Generate a heatmap of top associations and a self-contained Jupyter notebook documenting the workflow.

**Independent Test**: The pipeline generates a PNG heatmap of the top significant features and a `.ipynb` file that, when opened, renders the analysis steps and plots without requiring additional configuration.

### Tests for User Story 3 ⚠️

- [X] T034 [US3] Unit test for heatmap generation and filtering in `tests/unit/test_viz.py`. **Specific Test**: `test_heatmap_filters_by_correlation_threshold`. **Setup**: Create a DataFrame with correlation coefficients ranging from -1 to 1. **Assertion**: `assert output.shape[0] == filtered_input.shape[0]` and `assert all(output['rho'].abs() >= 0.5)` and `assert output.shape[0] < input.shape[0]` (if input has <0.5 values). **Note**: Written to fail before implementation (TDD). Sequential to code existence.
- [X] T035 [US3] Integration test for notebook execution and numerical equivalence in `tests/integration/test_reproducibility.py`. **Specific Check**: Validate numerical equivalence with tolerance of 1e-5. **Includes**: Simulate clean CPU environment (via Docker or CI job) and execute `output/reproducibility_notebook.ipynb` to verify SC-003. **Deliverable**: CI log showing successful execution on fresh runner. **Assertion**: `assert notebook_execution_status == "success"` and `assert max_error < 1e-5`. **Dependency**: T038, T032.

### Implementation for User Story 3

- [X] T036 [US3] Implement `src/analysis/viz.py`: Generate seaborn heatmap of top significant features (|ρ| ≥ 0.5) against disease severity and save to `output/heatmap_top_features.png`. **Output**: `output/heatmap_top_features.png`. **Dependency**: Requires output from T032 (results.csv). (FR-008).
- [X] T038 [US3] Implement `src/main.py` (orchestrator): Generate Jupyter notebook `output/reproducibility_notebook.ipynb` with code cells, metadata/URLs, and execution logic. **Dependency**: T032.
- [X] T039 [US3] Implement `src/main.py`: Execute notebook cells, compare outputs, and validate numerical equivalence within dynamic tolerance (SC-003). **Deliverable**: Calculate floating-point error bounds for PGLS/Spearman and set `tolerance` to **relative error < 1e-5** comparing the 'correlation_coefficient' column. This threshold is scientifically accepted for iterative methods. **Dependency**: T038.
- [X] T040 [US3] Implement `src/main.py`: Resource monitoring logic (memory, runtime, exit conditions) and output to `output/runtime_metrics.json`. **Dependency**: None.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Update `README.md` with usage examples and dependency list. **Specifics**: Add sections: "Usage" (CLI command: `python src/main.py --input...`), "Dependencies" (list from `requirements.txt`).
- [X] T042 [P] Update `docs/api.md` with function signatures and module descriptions. **Specifics**: Document `src/analysis/correlation.py`, `src/data/download.py`, `src/analysis/phylogeny.py` using Sphinx docstring style.
- [X] T043 [P] Run `quickstart.md` validation using `lychee` tool and ensure all links work. **Exit Code**: 0 on success.
- [X] T044 [P] Run `ruff --fix` and `black` to ensure code style compliance. **Verification**: Run `ruff check --exit-zero` and `black --check` to confirm no changes needed.
- [X] T045 [P] Reduce cyclomatic complexity of `src/analysis/correlation.py` to < 10. **Verification**: Run `radon cc src/analysis/correlation.py` and ensure max score < 10.
- [X] T046 [P] Optimize `src/data/download.py` to use streaming for large downloads to reduce peak RAM. **Specifics**: Use `requests.get(..., stream=True)` and write in chunks of 64KB. **Test**: Run `python -m memory_profiler tests/integration/test_large_file.py` using a 1GB dummy file and assert Peak RAM < 500MB.
- [X] T047 [P] Add memory profiling hooks to `src/main.py` to verify memory limit during execution. **Specifics**: Use `memory_profiler` library and log format `Peak Memory: {value} MB`.
- [X] T048 [P] Add unit tests for specific edge cases: `test_download_handles_404`, `test_extract_handles_empty_genome` in `tests/unit/`. **Logic**: Mock request to return 404, assert `DataFetchError` is raised with message containing "Failed to fetch real data". **Assertion**: `test_download_handles_404`: `assert "Failed to fetch real data" in str(exc_info.value)`. **Assertion**: `test_extract_handles_empty_genome`: `assert "Empty genome" in log_output` or `assert DataFetchError` is raised.
- [X] T049 [P] Add unit tests for missing data handling: `test_merge_handles_missing_phenotype` in `tests/unit/`. **Logic**: Input DataFrame with a substantial proportion of NaN values in the phenotype column, assert rows dropped and log entry created. **Assertion**: `assert len(output_df) < len(input_df)` and `assert "excluded due to missing phenotype" in log_output`.
- [X] T050 [P] Verify `requirements.txt` pins and add comments for external binary dependencies (`hmmsearch`, `IQ-TREE`). **Format**: `# Binary dependency: hmmsearch (requires external installation)`.
- [X] T051 [P] [US1] Add explicit URL validation and "fail loudly" logic to `src/data/download.py` ensuring no synthetic fallbacks are ever triggered (Constitution Data Hygiene). **Specifics**: Check HTTP 200 status before parsing; raise `DataFetchError` with message "Failed to fetch real data from {url}". **Signature**: `DataFetchError(url, status_code, context)`. **Dependency**: T059.
- [X] T052 [P] [US2] Add unit test for `test_correlation_handles_collinear_features` to verify FDR robustness under high collinearity (Plan: Power & Limitation Disclosure). **Logic**: Create two features with correlation > 0.99, assert FDR remains controlled. **Assertion**: `assert len(significant_features) <= expected_max` and `assert "collinearity" in log_output`.
- [X] T053 [P] [US3] Add documentation to `output/reproducibility_notebook.ipynb` explicitly stating the sample size limitation and the "low_power" flag logic if N < 10 (Plan: Power & Limitation Disclosure). **Specifics**: Insert text "Warning: N < 10. Low power to detect small effects." in cell 1.
- [X] T054 [P] [US1] Implement `src/data/download.py` to stream NCBI genome assemblies using `requests` with chunked writing to disk, ensuring No single file exceeds a manageable memory footprint before processing. (Constitution: Large real datasets). **Specifics**: Use `requests.get(..., stream=True)`, chunk size optimized for system throughput.
- [X] T055 [P] [US1] Add a `try/except` block in `src/data/download.py` that raises a `DataFetchError` if NCBI or PHI-base fetch fails, explicitly removing any `except` blocks that fallback to `generate_synthetic_*()` or `mock_*()` functions (Constitution: Fail loudly). **Specifics**: Define `DataFetchError(Exception)` with signature `__init__(self, url, status_code, context)`. **Dependency**: T059.
- [X] T056 [P] [US2] Update `src/analysis/phylogeny.py` to validate that the constructed tree has non-zero branch lengths and is rooted; if not, apply `dendropy` or `ete3` methods to root and scale, logging the correction (FR-003). **Specifics**: Threshold for non-zero: > 1e-10. Method: `tree.root_with_outgroup()`.
- [X] T057 [P] [US2] Add a pre-filtering step in `src/analysis/correlation.py` to remove genomic features present in < 10% of isolates to mitigate p >> n issues before running PGLS/Spearman (Plan: Power & Limitation Disclosure). **Specifics**: Calculate `sum(feature_vector) / len(isolates) < 0.1`. **Note**: Ensure all significant features (FDR < 0.05) are retained in raw output even if pre-filtered by **re-adding them to the final results.csv with p_value=NaN and flag="filtered_rare"**. **Log**: "Filtered {count} rare features." **Implementation**: Filter features for the model, run FDR, then re-insert filtered features into the final CSV with `flag='filtered_rare'` and `p_value=NaN`.
- [X] T058 [P] [US3] Add a "Data Provenance" section to `output/reproducibility_notebook.ipynb` that dynamically lists the exact URLs and accessions used for the current run (FR-001, SC-003). **Specifics**: Code snippet to iterate over `data/processed/metadata.json` and print URLs.

---

## Phase N+1: Data Hygiene & Robustness (Revision Round 2)

**Purpose**: Address specific reviewer concerns regarding data provenance, streaming, and strict failure modes to ensure Constitution compliance. (Consolidated in T059).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories (Includes T026, T027, T059, T031c)
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (dataset) AND T027 (Tree)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (results)

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
- All tests for a user story marked [P] can run in parallel (Note: Tests are sequential to code existence for execution, but can be written in parallel)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

**Note on TDD**: Tasks marked [P] in the test sections (e.g., T011-T014) can be executed in parallel *if* the implementation code exists. However, in a development workflow, these tests should be written to fail before the corresponding implementation tasks (T015-T021) are completed.

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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Statistical Analysis)
 - Developer C: User Story 3 (Visualization/Docs)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, cross-story dependencies that break independence
- **Data Hygiene**: All data loaders MUST fail loudly if real data fetch fails; NO synthetic fallbacks allowed.
- **Streaming**: If datasets are large, implement streaming/chunking to stay within 7GB RAM limits.
- **Phylogeny**: Ensure tree construction uses housekeeping genes (rpoB, gyrB, 16S), NOT virulence genes, to avoid circularity.
- **Constitution Compliance**: **Benjamini-Hochberg FDR** is the mandatory primary FDR method (FR-005, US-2, Constitution Principle VI). **PGLS** is mandatory for N >= 30; **Spearman** is mandatory for 10 <= N < 30. N < 10 triggers a descriptive case study (T031b).
- **Revision Note**: Updated T028b to enforce PGLS for N >= 30. Added T028a for Spearman (N < 30). Updated T029 to prioritize BH FDR. Moved T031c to Phase 2. Updated T039 tolerance to 1e-5. Fixed dependency chains (T031a -> T028a/T028b -> T029). Removed redundant text. Removed T028c (Spearman). Added T057 re-addition logic.