---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Gene Essentiality from Protein Interaction Network Topology

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [X] T001 Run `scripts/init_project_structure.sh` to create directories: `code/`, `data/raw/`, `data/processed/`, `data/phylogeny/`, `results/`, `tests/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.11 project with dependencies: `networkx`, `pandas`, `scipy`, `statsmodels`, `requests`, `pyyaml`, `numpy`, `biopython`, `dendropy` (Create `requirements.txt` with pinned versions).
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools.
- [X] T004 [P] Configure `code/config.py` to load organism IDs, confidence thresholds, and paths from YAML. **Note**: This task now loads the specific organism IDs defined in T004a.
- [X] T004a [P] **Create `code/config.py` with hardcoded organism list**: Define a Python constant `ORGANISM_IDS = ['9606', '559292', '83333', '10090', '7227']` (Human, S. cerevisiae, E. coli, Mouse, D. melanogaster) and `CONFIDENCE_THRESHOLDS = [500, 700, 900]`. This list MUST contain 5-8 specific organism IDs as required by FR-001. This file is the single source of truth for T013.
- [X] T005 [P] Implement `code/utils.py` with logging setup, checksumming (SHA256), and exponential backoff helpers.
- [X] T006 [P] Create `code/hash_checker.py` to compute hashes for `data/` and `results/` and update `state/` YAML.
- [X] T007 Create `contracts/correlation_result.schema.yaml`, `contracts/pgls_result.schema.yaml`, `contracts/sensitivity_report.schema.yaml`.
- [X] T008 [P] Setup `tests/contract/test_schemas.py` to validate JSON outputs against the schema files.
- [X] T010 [P] Implement `quickstart.md` and `research.md` with exact reproduction steps: Environment Setup, Data Fetching (commands), Pipeline Execution, and Reproducibility Verification. This task is critical for Constitution Principle I and must be completed before Phase 3. `quickstart.md` must include the exact commands to run `main.py` and verify outputs. `research.md` must list all data sources and their verification status.
- [X] T019b [US1] **Determine permutation count N**: Set `N = 1000` in `code/config.py` based on standard statistical practice for empirical null distributions. This value **replaces** the '[deferred]' placeholder in SC-001 and is the **final, hardcoded value** for the project scope. Document the justification in `docs/permutation_justification.md`. **Dependency**: This task must complete before T020.
- [X] T009a [US2] **Fetch Phylogenetic Tree**: Implement `fetch_phylogenetic_tree` in `code/data_loader.py` to fetch the Newick tree from OpenTree of Life dynamically. **Logic**: 1) Read organism names from `code/config.py`. 2) Use OpenTree API to resolve names to tax_ids. 3) Use OpenTree API to fetch the tree. 4) Save to `data/phylogeny/tree.newick`. **FAILURE HANDLING**: If the tree cannot be fetched or IDs are missing, **log a warning "Phylogenetic tree missing; halting pipeline for PGLS"** and **DO NOT save the file**. Do NOT construct a synthetic tree. This satisfies FR-006 and Assumptions.
- [X] T009b [US2] **Validate Phylogenetic Tree**: Implement a check in `code/main.py` to verify `data/phylogeny/tree.newick` exists after T009a. If missing, set `pgls_enabled=False` and log "PGLS disabled: tree missing". This task gates T047 and T029a.
- [X] T047 [US2] Validate phylogenetic tree structure in `code/statistics.py` before PGLS: ensure tree has correct number of tips matching the organisms with valid correlation data; log warning and skip PGLS if mismatch. **Execution Order**: This task must run immediately after T009b and before T029a.
- [X] T072 [P] **Set Reproducibility Seed**: Implement `set_seed(seed)` in `code/utils.py` using `random.seed`, `numpy.random.seed`, and `os.environ['PYTHONHASHSEED']`. **CRITICAL ORDERING**: This function must be called at the **very start** of `main.py`, **before** any library import that might rely on randomness (e.g., `import networkx`, `import pandas`). Update `code/config.py` to load `random_seed = 42`. This task is in Phase 2 to ensure it runs before all other tasks.

---

## Phase 3: User Story 1 - Cross-Species Correlation Analysis (Priority: P1) 🎯 MVP

**Goal**: Download PPI networks (STRING) and essentiality labels (DEG), map IDs, compute centralities, and calculate Spearman correlations for multiple organisms.

**Independent Test**: Execute pipeline for *S. cerevisiae* and verify `results/correlations.json` contains a valid Spearman ρ and p-value for degree centrality.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Contract test for correlation result schema in `tests/contract/test_correlation_schema.py`.
- [X] T012 [US1] Integration test for single-organism pipeline in `tests/integration/test_single_organism.py`: Use mock data for *S. cerevisiae* (small graph, genes) and assert that `results/correlations.json` contains a valid Spearman ρ and p-value. (Note: Depends on implementation completion).

### Implementation for User Story 1

- [X] T013 [US1] Implement `fetch_string_ppi` function in `code/data_loader.py` to fetch PPI networks from STRING API for each organism ID in `code/config.py` (from T004a). Use confidence threshold ≥700; if API fails for a specific organism, log a warning and skip that organism (do not crash the entire pipeline).
- [X] T014 [US1] Implement `fetch_deg_essentiality` function in `code/data_loader.py` to fetch gene essentiality labels (binary) from the DEG database. **Fallback Strategy**: Attempt primary FTP URL `ftp://ftp.ncbi.nlm.nih.gov/pub/microarray/deg/`. If that fails, attempt the official DEG API endpoint. If both fail, log a warning and skip the organism. Do NOT use synthetic data.
- [X] T015 [US1] Implement ID mapping logic in `code/data_loader.py` using Ensembl BioMart API to align STRING and DEG gene identifiers; log `mapping_coverage_percent`.
- [X] T016 [US1] Implement `compute_centrality` function in `code/network_analysis.py` to compute degree, betweenness, and eigenvector centrality using NetworkX; use k-sampling for betweenness on networks >5,000 nodes to ensure <30min runtime (FR-004); exact calculation for smaller networks.
- [X] T017 [US1] Implement `calculate_correlation` function in `code/statistics.py` to calculate Spearman's rank correlation between each centrality metric and essentiality labels.
- [X] T018 [US1] Implement `run_organism_analysis` function in `code/main.py` that orchestrates the full pipeline for a single organism: calls `fetch_string_ppi`, `fetch_deg_essentiality`, `map_ids`, `compute_centrality`, `calculate_correlation`, **calls the null model functions (T020, T022)**, and `save_results`. This function must accept a `threshold` parameter.
- [X] T019 [US1] Add error handling for disconnected networks in `code/network_analysis.py`: check if edge count == 0; if so, assign 0 centrality for all nodes, log a specific warning "Network disconnected for {organism}", and skip further centrality calculation. This satisfies FR-004 and Edge Case requirements.
- [X] T045 [P] [US1] **Implement Streaming Data Loader**: Refactor `code/data_loader.py` to handle large datasets using `urllib.request` or `requests` with chunked reading for the specific FTP/API sources defined in the plan (e.g., DEG). Ensure memory usage stays < 7GB. Explicitly state sample size if full stream is truncated by time limits. Do NOT use the `datasets` library.
- [X] T046 [P] [US1] Add explicit exclusion logging in `code/data_loader.py` for genes missing from the PPI network (Edge Case): count and log excluded genes per organism in `results/mapping_coverage.json`.
- [X] T048 [P] [US1] Add unit tests in `tests/unit/test_data_loader.py` to verify that `fetch_string_ppi` and `fetch_deg_essentiality` raise specific exceptions on network timeout or 404 errors, ensuring no silent fallback to synthetic data.
- [X] T050 [P] [US1] Implement robust error handling in `code/data_loader.py` for Ensembl BioMart API failures: if the primary BioMart endpoint fails, attempt a fallback to a secondary mirror (e.g., use ` Name or service not known)"))] if ` Name or service not known)"))] fails) before raising a `DataFetchError`. This addresses the risk of single-point API failure for ID mapping (FR-003).
- [X] T051 [P] [US1] Add a `--dry-run` flag to `code/main.py` that executes the data fetching and mapping steps for a single organism without computing centralities or correlations, to validate data sources and mapping coverage before a full run. This addresses the risk of long-running failures due to data issues (Risks & Mitigations).
- [X] T054 [P] [US1] Implement a specific test case in `tests/unit/test_data_loader.py` to verify that the ID mapping function correctly handles genes with multiple aliases and selects the most appropriate Ensembl ID based on the organism context.
- [X] T055 [P] [US1] Add a logging statement in `code/network_analysis.py` to report the exact number of nodes and edges used for centrality calculation after any sampling or filtering, to ensure transparency in the computational process (Constitution Principle I).
- [X] T058 [P] [US1] DEFERRED: Add a retry mechanism with exponential backoff (limited attempts, base 2s) to `code/data_loader.py` specifically for the Ensembl BioMart API calls in T015 to mitigate transient network errors without falling back to synthetic data.
- [X] T059 [P] [US1] DEFERRED: Implement a dedicated unit test in `tests/unit/test_data_loader.py` that mocks a persistent 500 error from the Ensembl BioMart API to verify that the retry logic eventually raises the correct `DataFetchError` after the maximum attempts.
- [X] T062 [P] [US1] DEFERRED: Add a specific task to `code/utils.py` to implement a deterministic random seed setter that is called at the start of every data loading and analysis step to ensure full reproducibility of the streaming and sampling processes across runs. (Note: This is now covered by T072).
- [X] T063 [P] [US1] DEFERRED: Create a contract test in `tests/contract/test_mapping_schema.py` to validate the structure of `results/mapping_coverage.json` (from T046), ensuring it contains the required fields: `organism_id`, `total_genes`, `mapped_genes`, and `coverage_percent`.
- [X] T066 [P] [US1] DEFERRED: Implement a check in `code/network_analysis.py` to verify that the graph is connected before computing betweenness centrality; if the graph is disconnected, log a warning and compute centrality only on the largest connected component, saving the component size in the results.
- [X] T068 [US1] **Address Review: Data Source Verification**: Implement a pre-flight check in `code/main.py` that validates the existence and accessibility of the primary STRING (`) and DEG (`ftp://ftp.ncbi.nlm.nih.gov/pub/microarray/deg/`) URLs defined in `research.md` before any data fetching begins. If a primary source is unreachable for a specific organism, skip that organism and log a warning, but DO NOT exit the entire pipeline. This addresses the risk of "API Rate Limiting" and "Data Fetching" failures by failing fast for the specific organism.
- [X] T069 [US3] **Address Review: Streaming Implementation**: Refactor `code/data_loader.py` to use `urllib.request` or `requests` with chunked reading for the DEG dataset if the FTP download fails or is too large for RAM. Ensure the code explicitly logs the `chunked=True` mode and the chunk size used. If chunked reading is used, the task must save a log entry in `results/mapping_coverage.json` stating `data_source_mode: "chunked"`. This addresses the "Large real datasets" rule.
- [X] T073 [US1] **Address Review: Data Fetching Robustness**: Implement a strict `try/except` block in `code/data_loader.py` for the primary STRING API call that raises a custom `DataFetchError` with the specific organism ID and error code if the fetch fails. Ensure this error is caught in `main.py` to skip the organism gracefully, but **never** falls back to synthetic data or a mock network. This enforces the "Fail Loudly" rule for real data sources.
- [X] T074 [US1] **Address Review: ID Mapping Fallback**: Refactor `code/data_loader.py` (T015) to implement a secondary mapping strategy using Gene Symbols if Ensembl BioMart fails or returns low coverage (<10%). This secondary strategy must use a strict, case-sensitive string match against the DEG database and must log the specific number of genes matched via this fallback. If the fallback also fails, raise `DataFetchError`.

### Null Model A: Label Permutation (SC-001)

- [X] T020 [US1] [P] Implement label permutation loop in `code/statistics.py` to shuffle essentiality labels **N times** (where N is the value **read from `code/config.py` (set by T019b)**) and compute Spearman correlation for each shuffle; save results to `results/null_distribution/{organism}/threshold_{threshold}/label_permutation.csv` (organism-specific and threshold-specific subfolders to prevent race conditions). The `threshold` parameter must be passed to this function. **Dependency**: This task requires T019b to be complete.
- [X] T021 [US1] [P] Implement empirical p-value calculation in `code/statistics.py` by comparing the observed correlation (from T017) against the null distribution (from T020); update `results/correlations.json` with `empirical_p_value` and `null_distribution_summary`. **Dependency**: T021 requires both T017 and T020 to be complete.

### Null Model B: Graph Rewiring (FR-010)

- [X] T022 [US1] [P] Implement graph rewiring in `code/network_analysis.py` to generate a set of degree-preserving random graphs using the Maslov-Sneppen algorithm; save graphs to `results/null_distribution/{organism}/threshold_{threshold}/rewired_graphs/` (organism-specific and threshold-specific subfolders). The `threshold` parameter must be passed to this function.
- [X] T023 [US1] [P] Implement centrality computation on rewired graphs in `code/network_analysis.py` to calculate degree centrality for each rewired graph.
- [X] T024 [US1] [P] Implement correlation calculation on rewired graphs in `code/statistics.py` to compute Spearman correlation between rewired centrality and original essentiality labels; save results to `results/null_distribution/{organism}/threshold_{threshold}/rewired_correlations.csv`.
- [X] T025 [US1] [P] Implement statistical comparison in `code/statistics.py` to calculate the p-value for FR-010: aggregate rewired correlations (from T024) into a distribution, compare the observed correlation (from T017) against it by calculating `count(rewired_corr >= observed_corr) / total_rewired`, and save results to `results/correlations.json` with `rewired_p_value`. **Dependency**: T025 requires T017 and T024 to be complete.
- [X] T026 [US1] [P] **Verify Scale-Free Topology**: Implement `verify_scale_free_topology` in `code/network_analysis.py` to compare the power-law exponent (gamma) of the original network vs. the rewired networks. **Output**: Generate `results/topology_validation.json` containing the exponents, the comparison result, and a **pass/fail flag** confirming the original network is scale-free and the rewired network is not. This task explicitly addresses the "why" of FR-010.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comparative Statistical Testing (Priority: P2)

**Goal**: Compare correlation coefficients across organisms using Phylogenetic Generalized Least Squares (PGLS) with Fisher's z-transformation.

**Independent Test**: Run analysis on at least two distinct organisms with a provided tree; verify `results/pgls_results.json` contains a PGLS statistic and p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US2] Contract test for PGLS result schema in `tests/contract/test_pgls_schema.py`.
- [X] T027 [P] [US2] Integration test for cross-species comparison in `tests/integration/test_cross_species.py`: Use mock correlation data for multiple organisms and a mock tree; assert that `results/pgls_results.json` contains a valid PGLS statistic and p-value.

### Implementation for User Story 2

- [X] T028 [US2] Implement Fisher's z-transformation in `code/statistics.py` to normalize correlation coefficients for comparison.
- [X] T029a [US2] Implement PGLS model in `code/statistics.py` using `statsmodels` and the loaded phylogenetic tree (from T009a, validated by T009b and T047) to test for differences in correlation strength. **Include logic to skip if effective sample size n < 10 and log "Power insufficient" warning** (FR-009). **Calculate and save Benjamini-Hochberg corrected p-values** (FR-008) as part of this function.
- [X] T029b [US2] [P] Write unit tests for the Benjamini-Hochberg correction logic within `tests/unit/test_statistics.py` to ensure correctness against known examples.
- [X] T031 [US2] Add logic in `code/main.py` to skip PGLS if effective sample size n < 10 and log "Power insufficient" warning (FR-009).
- [X] T032 [US2] Save comparative statistics to `results/pgls_results.json` with metadata on organisms and tree used; **ensure Benjamini-Hochberg corrected p-values are saved** (FR-008).
- [X] T052 [P] [US2] **Remove Synthetic Tree Fallback**: Ensure `code/statistics.py` (T029a) does NOT attempt to construct a tree. If the tree is missing (T009b set `pgls_enabled=False`), skip PGLS with a clear warning as per FR-006.
- [X] T060 [P] [US2] DEFERRED: Add a validation check in `code/statistics.py` for the PGLS input data: ensure that the correlation coefficients and sample sizes passed to the model are strictly positive and that the sample size meets the minimum threshold (n >= 10) before model fitting, logging a clear error if violated.
- [X] T065 [P] [US2] DEFERRED: Add a unit test in `tests/unit/test_statistics.py` to verify the Fisher's z-transformation and inverse transformation functions, ensuring numerical stability and correctness for correlation coefficients near the boundaries (-1 and 1).
- [X] T076 [US2] **Address Review: PGLS Error Handling**: Implement a `try/except` block in `code/statistics.py` (T029a) around the PGLS model fitting. If `statsmodels` raises a convergence error or a singular matrix error (common with small sample sizes), catch the exception, log "PGLS model failed to converge for {organism_list}", and record the failure in `results/pgls_results.json` without crashing the pipeline.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis on Network Confidence (Priority: P3)

**Goal**: Re-run the correlation analysis varying the STRING confidence score threshold across a range of low, medium, and high values. to assess robustness.

**Independent Test**: Run pipeline with thresholds across a range for one organism; verify output contains separate results for each threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_schema.py`.
- [X] T034 [P] [US3] Integration test for multi-threshold run in `tests/integration/test_sensitivity.py`: Run with a range of thresholds for a mock organism.; assert that `results/sensitivity_report.md` contains a table with |Δρ| values and a pass/fail flag for SC-002.

### Implementation for User Story 3

- [X] T035 [US3] Refactor `code/main.py` to include a `run_sensitivity_analysis` function that iterates over the list of confidence thresholds `[500, 700, 900]` defined in `code/config.py`. For each threshold, call `run_organism_analysis` (from T018) with the specific threshold. **Critical**: Re-use the generic functions from T020 (label permutation) and T022 (graph rewiring); do NOT re-implement logic. Implement caching of intermediate results (e.g., centrality metrics) to avoid redundant computation across thresholds. **Dependencies**: This task depends on T018, T020, and T022 being complete.
- [X] T036 [P] [US3] Implement logging for network sparsity (flag if edges < 500) while allowing NaN/0 returns for centrality metrics (Edge Case).
- [X] T037 [US3] **Generate Sensitivity Report**: Generate `results/sensitivity_report.md` summarizing correlation coefficients and stability (|Δρ|) across thresholds; MUST include a table of |Δρ| values for each threshold pair and a pass/fail flag for SC-002 (stability ≤ 0.1). **Logic**: Calculate the MAXIMUM absolute difference in correlation coefficients across the entire set of thresholds (500, 700, 900) and compare that single max value to 0.1. **CRITICAL**: This task MUST also generate `results/sensitivity_summary.json` containing all |Δρ| values and stability flags. **Dependency**: This task depends on T035 completing successfully. **Note**: This task is the sole owner of generating `results/sensitivity_report.md`.
- [X] T038 [P] [US3] Verify SC-002: Calculate absolute difference in correlation coefficients across thresholds and flag if > 0.1; log pass/fail status for SC-002 in `results/sensitivity_report.md`.
- [X] T049 [P] [US3] Add a specific task in `code/main.py` to aggregate all sensitivity results into a single `results/sensitivity_summary.json` file for easy downstream plotting, containing all |Δρ| values and stability flags. **Dependency**: This task depends on T035 completing successfully.
- [X] T053 [P] [US3] Add a validation step in `code/main.py` for the sensitivity analysis thresholds: ensure that the list of thresholds is strictly increasing and within the valid STRING confidence range before starting the analysis loop.
- [X] T057 [US3] Add a task to `code/main.py` to generate a visual summary (e.g., a simple text-based ASCII plot or a summary table) of the sensitivity analysis results in `results/sensitivity_report.md` to improve readability of the |Δρ| values. **Note**: This logic is now integrated into T037.
- [X] T061 [US3] **Consolidated into T070**: Handle sparse networks (<500 edges) by setting metrics to NaN/0. This logic is now part of T070.
- [X] T064 [P] [US3] DEFERRED: Refactor `code/main.py` to ensure that the `run_sensitivity_analysis` function (T035) properly propagates exceptions from the inner `run_organism_analysis` calls (T018) so that a failure in one threshold does not silently skip the entire sensitivity loop.
- [X] T070 [US3] **Address Review: Threshold Edge Case Handling**: Modify `code/network_analysis.py` to handle the specific case where a high confidence threshold (e.g., 900) results in a network with < 500 edges. Instead of just logging, the code must explicitly set `centrality_metrics` to `NaN` or `0` for that organism/threshold combination and record `reason: "network_too_sparse"` in the output JSON. This ensures the downstream statistical tests (T017) can correctly handle these inputs without crashing. **Note**: This task does NOT generate the report; it ensures the data is valid for T037 to generate the report.
- [X] T071 [US2] **Address Review: PGLS Sample Size Logic**: Refine the logic in `code/statistics.py` (T029a) to explicitly calculate the "effective sample size" as the count of organisms with valid correlation data *and* a corresponding tip in the phylogenetic tree. If this count < 10, the function must omit the PGLS result from the output JSON and log "Power insufficient: n={count}" (FR-009). This ensures the PGLS test is only run when statistically valid.
- [X] T075 [US3] **Address Review: Sensitivity Loop Integrity**: Add a validation check in `code/main.py` (T035) to ensure that the sensitivity analysis loop does not silently skip thresholds due to data fetch errors. If a specific threshold fails for an organism, the result must be recorded as `null` or `skipped` in `results/sensitivity_summary.json` with a specific error reason, rather than omitting the entry entirely.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Documentation updates in `quickstart.md` and `research.md` (Ensure all steps are verified). **Deliverable**: `quickstart.md` with Environment Setup, Data Fetching commands, Pipeline Execution, and Reproducibility Verification steps; `research.md` with all data sources and verification status.
- [X] T040 Code cleanup and refactoring of `code/` modules (Refactor `code/data_loader.py` to reduce cyclomatic complexity < 10 and remove unused imports; run flake8 --max-complexity=10).
- [X] T041a [P] [US1] Run profiling: Execute `code/main.py` with `cProfile` on a representative organism to identify bottlenecks. **Dependency**: This task must run after T016 has been executed to generate profiling data. **Deliverable**: `results/profiles/cprofile_report.txt`.
- [X] T041b [P] [US1] Implement optimizations: Refactor `code/network_analysis.py` based on T041a results to optimize centrality algorithms (T016) to meet the 30-minute runtime requirement for 25k nodes. **Focus**: Optimize centrality algorithms, not data fetches. If profiling shows T016 is the bottleneck, T041b replaces the implementation of T016.
- [X] T042 [P] Additional unit tests in `tests/unit/` for centrality algorithms and statistical functions. **Specifics**: Write tests for `compute_centrality` (degree, betweenness, eigenvector), `calculate_correlation` (Spearman), and `pgls_model` (PGLS) in `tests/unit/test_network_analysis.py` and `tests/unit/test_statistics.py`.
- [X] T043 Run `hash_checker.py` and verify `state/` artifact hashes are updated.
- [X] T044 [P] Run quickstart.md validation to ensure end-to-end reproducibility (Note: Assumes `quickstart.md` exists from T010).

---

## Phase 7: Final Validation & Execution Readiness

**Purpose**: Ensure the pipeline is robust, reproducible, and ready for the execution gate.

- [X] T077 [P] **Address Review: End-to-End Smoke Test**: Create a new integration test `tests/integration/test_smoke_run.py` that runs the full pipeline on a single, small organism (e.g., *S. cerevisiae*) with a mock phylogenetic tree and mock data files. This test must verify that all output files (`correlations.json`, `pgls_results.json`, `sensitivity_summary.json`) are generated with the correct schema and non-null values where expected.
- [ ] T078 [P] **Address Review: Documentation Completeness**: Update `quickstart.md` to include a "Troubleshooting" section that explicitly lists the error codes and log messages generated by T073, T074, T075, and T076, and provides the exact steps a user should take to resolve them (e.g., "Check network connectivity", "Verify organism ID in config").
- [X] T079 [P] **Address Review: Artifact Hashing**: Verify that `code/hash_checker.py` (T006) is executed as the final step of `main.py` and that it updates the `state/projects/PROJ-452-...yaml` file with the SHA256 hashes of all generated JSON and Markdown files in `results/`. Ensure the hash of `research.md` is also included to verify citation integrity.