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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `src/utils/logging.py` with exponential backoff logic for network retries
- [X] T006 [P] Define `src/models/isolate.py`: Class `Isolate` (fields: strain_id, species, genome_path, phenotype_score, metadata). **Note**: Phenotypic score is a field here, not a separate class.
- [X] T007 [P] Define `src/models/genomic_feature.py`: Class `GenomicFeature` (fields: feature_id, type, presence_binary, pwm_count, source)
- [X] T008 [P] Define `src/models/species_aggregate.py`: Class `SpeciesAggregate` (fields: species_name, avg_phenotype, isolate_count, variance). **Dependency**: Must be completed before T019, T020, T021.
- [X] T009 [P] Setup `requirements.txt` with exact pinned versions for reproducibility (FR-010)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible Data Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Download specific plant pathogen genomes, extract virulence features, retrieve phenotypic scores, and merge into a clean dataset.

**Independent Test**: The pipeline can be run end-to-end on a clean environment; it must produce a single CSV/Parquet file containing aligned genomic feature vectors and phenotypic scores for at least 10 distinct isolates (or species aggregates), with all source URLs logged.

### Tests for User Story 1 ⚠️

- [X] T011 [US1] Unit test for NCBI E-utilities download logic in `tests/unit/test_download.py`. **Note**: Written to fail before implementation. (TDD: Sequential to code existence, not parallel execution).
- [X] T012 [US1] Unit test for PHI-base phenotype fetch and fallback logic in `tests/unit/test_download.py`. **Note**: Written to fail before implementation. (TDD: Sequential to code existence, not parallel execution).
- [X] T013 [US1] Integration test for full download-extract-merge flow in `tests/integration/test_pipeline.py`. **Note**: Written to fail before implementation. (TDD: Sequential to code existence, not parallel execution).
- [X] T014 [US1] Contract test for output schema (CSV/Parquet) in `tests/contract/test_schemas.py`. **Note**: Written to fail before implementation. (TDD: Sequential to code existence, not parallel execution).

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement `src/data/download.py`: Fetch *Fusarium graminearum*, *Pseudomonas syringae*, *Xanthomonas* spp. genomes via `biopython` E-utilities with retry logic (FR-001). **Dependency**: T001, T002.
- [X] T016 [P] [US1] Implement `src/data/download.py`: Retrieve phenotypic disease severity scores from PHI-base or literature tables; implement species-level aggregation fallback (FR-001, FR-009). **Dependency**: T001, T002.
- [X] T017 [P] [US1] Implement `src/data/extract.py`: Run `hmmsearch` against PHI-base/Pfam libraries to generate binary virulence gene presence/absence matrix (FR-002). **Dependency**: T015.
- [X] T018 [P] [US1] Implement `src/data/extract.py`: Count transcription factor binding sites using Position Weight Matrices (PWMs) (FR-002). **Dependency**: T015.
- [ ] T019 [US1] Implement `src/data/merge.py`: Align genomic features with phenotypic scores by isolate/species ID; handle missing phenotypes by dropping rows and logging counts (FR-006). **Function**: `align_genomic_phenotypic`. **Output**: `data/processed/merged_raw.parquet`. **Dependency**: T008, T017, T018.
- [X] T020a [US1] Implement `src/data/merge.py`: Detect if `linked_isolate_count / total_isolate_count < 0.5`. **Output**: Flag `needs_aggregation`. **Dependency**: T019.
- [ ] T020b [US1] Implement `src/data/merge.py`: If `needs_aggregation` is true, aggregate by species (group by species_name, average phenotype, count isolates) and write to `data/processed/species_aggregates.parquet`. **Dependency**: T020a.
- [ ] T020c [US1] Implement `src/data/merge.py`: If `needs_aggregation` is true, invoke the analysis module (T028a-c logic) on `data/processed/species_aggregates.parquet` and output results to `data/processed/aggregated_results.csv`. **Dependency**: T020b.
- [ ] T021 [US1] Implement `src/data/merge.py`: Output final analysis-ready dataset (CSV/Parquet) to `data/processed/merged_dataset.parquet` and summary report (processed count, missing count) (FR-001, FR-006). **Dependency**: T020b (or T019 if no aggregation needed).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Association Analysis (Priority: P2)

**Goal**: Compute PGLS correlations, apply Benjamini-Hochberg FDR, and identify significant genomic-virulence associations.

**Independent Test**: The analysis script runs on the P1 output dataset and produces a ranked list of genomic features with correlation coefficients, p-values, and adjusted p-values, identifying a set of top candidates.

### Tests for User Story 2 ⚠️

- [X] T022 [US2] Unit test for housekeeping gene extraction and tree construction in `tests/unit/test_phylogeny.py`. **Note**: Written to fail before implementation. (TDD: Sequential to code existence, not parallel execution).
- [X] T023 [US2] Unit test for PGLS calculation and BH FDR in `tests/unit/test_correlation.py`. **Note**: Written to fail before implementation. (TDD: Sequential to code existence, not parallel execution).
- [X] T024 [US2] Unit test for Permutation FDR sensitivity check in `tests/unit/test_correlation.py`. **Note**: Written to fail before implementation. (TDD: Sequential to code existence, not parallel execution).
- [X] T025 [US2] Integration test for full analysis pipeline (Tree -> PGLS -> FDR) in `tests/integration/test_pipeline.py`. **Note**: Written to fail before implementation. (TDD: Sequential to code existence, not parallel execution).

### Implementation for User Story 2

- [X] T026 [US2] Implement `src/analysis/phylogeny.py`: **Extract** core housekeeping genes (rpoB, gyrB, 16S) from the downloaded genome assemblies (`data/raw/*.fna`) using `biopython` or `prodigal`. **Constraint**: Use ONLY housekeeping genes, EXCLUDING virulence genes to prevent circularity (Constitution Principle VI). **Fallback**: If 16S is insufficient for *Fusarium* (fungi), retrieve reference tree from NCBI Taxonomy or use alternative core genes (e.g., RPB1, RPB2). **Output**: `data/processed/housekeeping_genes.fasta`. **Dependency**: T015.
- [X] T027 [US2] Implement `src/analysis/phylogeny.py`: **Construct** phylogenetic tree using the extracted housekeeping gene sequences via Maximum Likelihood (IQ-TREE or RAxML). Validate tree (rooted, branch lengths) and generate phylogenetic covariance matrix. **Output**: `data/processed/tree.newick` and `data/processed/phylo_covariance_matrix.npy`. **Dependency**: T026.
- [ ] T028a [US2] Implement `src/analysis/correlation.py`: **Method Selection Logic**: If N >= 30, select PGLS; if N < 30, select Phylogenetic Signal-Adjusted Spearman (sanctioned exception to FR-004 per Plan: Power & Limitation Disclosure). **Input**: `data/processed/merged_dataset.parquet` from T021 and `data/processed/tree.newick` from T027. **Dependency**: T021, T027.
- [ ] T028b [US2] Implement `src/analysis/correlation.py`: **PGLS Calculation**: Compute Phylogenetic Generalized Least Squares correlation coefficients between every genomic feature and disease severity score. **Input**: `data/processed/merged_dataset.parquet` and `data/processed/phylo_covariance_matrix.npy`. **Dependency**: T028a (if N>=30).
- [ ] T028c [US2] Implement `src/analysis/correlation.py`: **Spearman Calculation**: Compute Phylogenetic Signal-Adjusted Spearman correlation for N < 30. **Input**: `data/processed/merged_dataset.parquet`, `data/processed/tree.newick`, and `data/processed/phylo_covariance_matrix.npy`. **Dependency**: T028a (if N<30).
- [ ] T029a [US2] Implement `src/analysis/correlation.py`: Apply **Benjamini-Hochberg (BH) FDR** correction to raw p-values derived from the correlation tests. **Primary Method**: BH FDR (Constitution Principle VI). **Documentation**: Explicitly note this as a sanctioned exception to FR-005's primary option (per Plan). **Dependency**: T028b/T028c.
- [ ] T029b [US2] Implement `src/analysis/correlation.py`: **Permutation-based FDR Sensitivity Check**: Run permutation shuffling to generate null distribution and compute FDR as a sensitivity check (FR-005 primary option). **Dependency**: T028b/T028c.
- [ ] T030 [US2] Implement `src/analysis/correlation.py`: Filter results for visualization (|ρ| ≥ 0.5) while retaining all significant features (FDR < 0.05) in raw output (FR-007). **Dependency**: T029a.
- [ ] T031 [US2] Implement `src/analysis/correlation.py`: Handle edge case where **N < 10 after species aggregation** by skipping statistical testing and generating a **Descriptive Case Study** report to `output/case_study_report.md`. (FR-009). **Dependency**: T020c (if aggregated).
- [ ] T032 [US2] Output ranked table of features with coefficients, p-values, and adjusted p-values to `data/processed/results.csv`. If N < 10, include a 'low_power' flag and descriptive summary in metadata (FR-004, FR-005). **Dependency**: T030.
- [ ] T033 [US2] Implement metric calculation: Calculate and report **Success Rate (SC-001)** and **Proportion of Significant Features (SC-004)** in the final summary report. (SC-001, SC-004). **Dependency**: T032.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reproducibility Reporting (Priority: P3)

**Goal**: Generate a heatmap of top associations and a self-contained Jupyter notebook documenting the workflow.

**Independent Test**: The pipeline generates a PNG heatmap of the top significant features and a `.ipynb` file that, when opened, renders the analysis steps and plots without requiring additional configuration.

### Tests for User Story 3 ⚠️

- [ ] T034 [US3] Unit test for heatmap generation and filtering in `tests/unit/test_viz.py`. **Specific Test**: `test_heatmap_filters_by_correlation_threshold`. **Assertion**: `assert output.shape[0] == filtered_input.shape[0]` and `assert all(output['rho'].abs() >= 0.5)`.
- [ ] T035 [US3] Integration test for notebook execution and numerical equivalence in `tests/integration/test_reproducibility.py`. **Specific Check**: Validate numerical equivalence with tolerance derived in T039a.
- [ ] T035b [US3] Simulate clean CPU environment (via Docker or CI job) and execute `output/reproducibility_notebook.ipynb` to verify SC-003. **Deliverable**: CI log showing successful execution on fresh runner. **Dependency**: T038c.

### Implementation for User Story 3

- [ ] T036 [US3] Implement `src/analysis/viz.py`: Generate seaborn heatmap of top significant features (|ρ| ≥ 0.5) against disease severity. **Output**: `output/heatmap_top_features.png`. **Dependency**: Requires output from T032 (results.csv). (FR-008).
- [ ] T037 [US3] Implement `src/analysis/viz.py`: Save static heatmap PNG to `output/heatmap_top_features.png`. **Note**: Distinct from T036 to avoid race condition. **Dependency**: T032.
- [ ] T038a [US3] Implement `src/main.py` (orchestrator): Create Jupyter notebook skeleton `output/reproducibility_notebook.ipynb`. **Dependency**: None.
- [ ] T038b [US3] Implement `src/main.py`: Inject code cells from `src/` into notebook. **Dependency**: T038a.
- [ ] T038c [US3] Implement `src/main.py`: Inject metadata/URLs (data sources, parameters) into notebook. **Dependency**: T038b.
- [ ] T039a [US3] Implement `src/main.py`: Execute notebook cells and compare outputs. **Deliverable**: Validate tolerance for numerical equivalence (SC-003) by calculating floating-point error bounds for PGLS/Spearman and setting `tolerance` dynamically (do not hardcode 1e-6). **Dependency**: T038c.
- [ ] T039b [US3] Implement `src/main.py`: Assert numerical equivalence within the validated tolerance. **Dependency**: T039a.
- [ ] T040a [US3] Add memory monitoring logic to `src/main.py` using `memory_profiler` to log peak memory usage. **Dependency**: None.
- [ ] T040b [US3] Add runtime logging logic to `src/main.py` to log total runtime. **Dependency**: None.
- [ ] T040c [US3] Add exit condition check to `src/main.py`: Log warning and exit gracefully if memory > 7GB or runtime > 6h. **Output**: `output/runtime_metrics.json`. **Enforcement**: Ensure SC-005 is not falsely claimed as passed. **Dependency**: T040a, T040b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Update `README.md` with usage examples and dependency list. **Specifics**: Add sections: "Usage" (CLI command: `python src/main.py --input...`), "Dependencies" (list from `requirements.txt`).
- [ ] T042 [P] Update `docs/api.md` with function signatures and module descriptions. **Specifics**: Document `src/analysis/correlation.py`, `src/data/download.py`, `src/analysis/phylogeny.py` using Sphinx docstring style.
- [ ] T043 [P] Run `quickstart.md` validation using `lychee` tool and ensure all links work. **Exit Code**: 0 on success.
- [ ] T044 [P] Run `ruff --fix` and `black` to ensure code style compliance. **Verification**: Run `ruff check --exit-zero` and `black --check` to confirm no changes needed.
- [ ] T045 [P] Reduce cyclomatic complexity of `src/analysis/correlation.py` to < 10. **Verification**: Run `radon cc src/analysis/correlation.py` and ensure max score < 10.
- [ ] T046 [P] Optimize `src/data/download.py` to use streaming for large downloads to reduce peak RAM. **Specifics**: Use `requests.get(..., stream=True)` and write in chunks of 8KB. **Metric**: Peak RAM < 500MB during 1GB download.
- [ ] T047 [P] Add memory profiling hooks to `src/main.py` to verify 7GB limit during execution. **Specifics**: Use `memory_profiler` library and log format `Peak Memory: {value} MB`.
- [ ] T048 [P] Add unit tests for specific edge cases: `test_download_handles_404`, `test_extract_handles_empty_genome` in `tests/unit/`. **Logic**: Mock request to return 404, assert `DataFetchError` is raised.
- [ ] T049 [P] Add unit tests for missing data handling: `test_merge_handles_missing_phenotype` in `tests/unit/`. **Logic**: Input DataFrame with a substantial proportion of NaN values in the phenotype column, assert rows dropped and log entry created.
- [ ] T050 [P] Verify `requirements.txt` pins and add comments for external binary dependencies (`hmmsearch`, `IQ-TREE`). **Format**: `# Binary dependency: hmmsearch (requires external installation)`.
- [ ] T051 [P] [US1] Add explicit URL validation and "fail loudly" logic to `src/data/download.py` ensuring no synthetic fallbacks are ever triggered (Constitution Data Hygiene). **Specifics**: Check HTTP 200 status before parsing; raise `DataFetchError` with message "Failed to fetch real data from {url}".
- [ ] T052 [P] [US2] Add unit test for `test_correlation_handles_collinear_features` to verify FDR robustness under high collinearity (Plan: Power & Limitation Disclosure). **Logic**: Create two features with correlation > 0.99, assert FDR remains controlled.
- [ ] T053 [P] [US3] Add documentation to `output/reproducibility_notebook.ipynb` explicitly stating the sample size limitation and the "low_power" flag logic if N < 10 (Plan: Power & Limitation Disclosure). **Specifics**: Insert text "Warning: N < 10. Low power to detect small effects." in cell 1.
- [ ] T054 [P] [US1] Implement `src/data/download.py` to stream NCBI genome assemblies using `requests` with chunked writing to disk, ensuring no single file exceeds 500MB in RAM before processing (Constitution: Large real datasets). **Specifics**: Use `requests.get(..., stream=True)`, chunk size 8KB.
- [ ] T055 [P] [US1] Add a `try/except` block in `src/data/download.py` that raises a `DataFetchError` if NCBI or PHI-base fetch fails, explicitly removing any `except` blocks that fallback to `generate_synthetic_*()` or `mock_*()` functions (Constitution: Fail loudly). **Specifics**: Define `DataFetchError(Exception)` with signature `__init__(self, url, status_code)`.
- [ ] T056 [P] [US2] Update `src/analysis/phylogeny.py` to validate that the constructed tree has non-zero branch lengths and is rooted; if not, apply `dendropy` or `ete3` methods to root and scale, logging the correction (FR-003). **Specifics**: Threshold for non-zero: > 1e-10. Method: `tree.root_with_outgroup()`.
- [ ] T057 [P] [US2] Add a pre-filtering step in `src/analysis/correlation.py` to remove genomic features present in < 10% of isolates to mitigate p >> n issues before running PGLS/Spearman (Plan: Power & Limitation Disclosure). **Specifics**: Calculate `sum(feature_vector) / len(isolates) < 0.1`. **Note**: Ensure all significant features (FDR < 0.05) are retained in raw output even if pre-filtered by re-adding them to the final output set. **Log**: "Filtered {count} rare features."
- [ ] T058 [P] [US3] Add a "Data Provenance" section to `output/reproducibility_notebook.ipynb` that dynamically lists the exact URLs and accessions used for the current run (FR-001, SC-003). **Specifics**: Code snippet to iterate over `data/processed/metadata.json` and print URLs.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (dataset)
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
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

**Note on TDD**: Tasks marked [P] in the test sections (e.g., T011-T014) can be executed in parallel *if* the implementation code exists. However, in a development workflow, these tests should be written to fail before the corresponding implementation tasks (T015-T021) are completed.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for NCBI E-utilities download logic in tests/unit/test_download.py"
Task: "Unit test for PHI-base phenotype fetch and fallback logic in tests/unit/test_download.py"

# Launch all download/extract tasks together:
Task: "Implement src/data/download.py: Fetch genomes via biopython"
Task: "Implement src/data/extract.py: Run hmmsearch for virulence genes"
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
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Hygiene**: All data loaders MUST fail loudly if real data fetch fails; NO synthetic fallbacks allowed.
- **Streaming**: If datasets are large, implement streaming/chunking to stay within 7GB RAM limits.
- **Phylogeny**: Ensure tree construction uses housekeeping genes (rpoB, gyrB, 16S), NOT virulence genes, to avoid circularity.
- **Constitution Compliance**: **Benjamini-Hochberg (BH)** is the mandatory primary FDR method (FR-005). **PGLS** is the primary method for N>=30, with **Phylogenetic Signal-Adjusted Spearman** for N<30 (FR-004).
- **Revision Note**: Updated T020 and T031 to correctly implement FR-009 fallback triggers. Updated T029 to use BH as primary. Updated T028 to handle small-N. Merged T001/T010. Removed incorrect [P] tags from sequential tasks. Added T054-T058 to address data streaming, strict failure modes, and statistical robustness. Added T020b/c for functional aggregation. Added T028a-c for method selection. Added T029a-b for FDR methods. Added T035b for clean environment. Updated T002-T003, T034-T035, T041-T058 for executability. Split T020, T028, T029, T038, T039, T040 for atomicity. Updated T026 for fungal fallback. Updated T028c for data flow. Updated T057 for rare feature retention.