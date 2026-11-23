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

- [X] T072 [P] **Set Reproducibility Seed**: Implement `set_seed(seed)` in `code/utils.py` using `random.seed`, `numpy.random.seed`, and `os.environ['PYTHONHASHSEED']`. **CRITICAL ORDERING**: This is the FIRST task in Phase 2. It must be implemented before any other code that might import random/numpy. Update `code/config.py` to load `random_seed = 42`. **ADDITION**: Add a runtime check in `code/main.py` that verifies the running seed matches the configured seed before execution. This ensures no library imports occur before the seed is set in the main execution flow. **Dependency**: None (First in phase). **RUNTIME CHECK**: Add a check in `main.py` to verify that the running seed matches the configured seed before execution.
- [ ] T019c_static [P] **Set Permutation Count N**: Define `PERMUTATION_COUNT = 10000` in `code/config.py`. This value is fixed for reproducibility and meets SC-001 requirements without an undefined power analysis. **Dependency**: T072.
- [X] T004a [P] **Create `code/config.py` with hardcoded organism list**: Define a Python constant `ORGANISM_IDS = ['9606', '559292', '83333', '10090', '7227']` (Human, S. cerevisiae, E. coli, Mouse, D. melanogaster) and `CONFIDENCE_THRESHOLDS = [500, 700, 900]`. This list MUST contain 5-8 specific organism IDs as required by FR-001. This file is the single source of truth for T004. **Dependency**: T019c_static.
- [X] T004 [P] Configure `code/config.py` to load organism IDs, confidence thresholds, and paths from YAML. **Note**: This task now loads the specific organism IDs defined in T004a and the N value from T019c_static. **Dependency**: T004a, T019c_static.
- [X] T002 Initialize Python 3.11 project [UNRESOLVED-CLAIM: c_da51748c — status=not_enough_info] with dependencies: `networkx`, `pandas`, `scipy`, `statsmodels`, `requests`, `pyyaml`, `numpy`, `biopython`, `dendropy`. **Note**: `pymer4` removed as `statsmodels` is used for PGLS.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools.
- [X] T005 Implement `code/utils.py` with logging setup, checksumming (SHA256), and exponential backoff helpers. **Note**: This module must NOT import `random` or `numpy` at the top level; imports must occur inside functions to avoid seed conflicts with T072. **Dependency**: T072.
- [X] T006 [P] Create `code/hash_checker.py` to compute hashes for `data/` and `results/` and update `state/` YAML.
- [X] T007 Create `contracts/correlation_result.schema.yaml`, `contracts/pgls_result.schema.yaml`, `contracts/sensitivity_report.schema.yaml`.
- [X] T008 [P] Setup `tests/contract/test_schemas.py` to validate JSON outputs against the schema files.
- [ ] T010 [P] Implement `quickstart.md` and `research.md` with exact reproduction steps: Environment Setup, Data Fetching (commands), Pipeline Execution, and Reproducibility Verification. This task is critical for Constitution Principle I and must be completed before Phase 3. `quickstart.md` must include the exact commands to run `main.py` and verify outputs. `research.md` must list all data sources and their verification status. <!-- FAILED: unspecified -->
- [ ] T009a [US2] **Fetch Phylogenetic Tree**: Implement `fetch_phylogenetic_tree` in `code/data_loader.py` to fetch the Newick tree from OpenTree of Life dynamically. **Logic**: 1) Read organism names from `code/config.py`. 2) Use OpenTree API to resolve names to tax_ids. 3) Use OpenTree API to fetch the tree. 4) Save to `data/phylogeny/tree.newick`. **FAILURE HANDLING**: If the tree cannot be fetched or IDs are missing, **log a warning "Phylogenetic tree missing; skipping PGLS"** and **set `pgls_enabled=False`**. Do NOT construct a synthetic tree. Do NOT halt the entire pipeline. This satisfies FR-006 and Assumptions. **Dependency**: T072.
- [ ] T009b [US2] **Validate Phylogenetic Tree**: Implement a check in `code/main.py` to verify `data/phylogeny/tree.newick` exists after T009a. If missing, set `pgls_enabled=False` and log "PGLS disabled: tree missing". **Dependency**: T009a.
- [ ] T004c [P] **Validate Organism Count**: Implement a check in `code/config.py` (or `main.py`) that verifies the final `ORGANISM_IDS` list contains between 5 and 8 organisms after all validation steps (T090, T092) are complete. If count < 5, log a CRITICAL error and halt. **Dependency**: T090, T092 (to be run in Phase 10, but logic defined here).

---

## Phase 3: User Story 1 - Cross-Species Correlation Analysis (Priority: P1) 🎯 MVP

**Goal**: Download PPI networks (STRING) and essentiality labels (DEG), map ID, compute centralities, and calculate Spearman correlations for multiple organisms.

**Independent Test**: Execute pipeline for *S. cerevisiae* and verify `results/correlations.json` contains a valid Spearman ρ and p-value for degree centrality.

### Null Model A: Label Permutation (SC-001)

- [ ] T020 [US1] [P] Implement label permutation loop in `code/statistics.py` to shuffle essentiality labels **N times** (where N is the value **read from `code/config.py` (set by T019c_static)**) and compute Spearman correlation for each shuffle; save results to `results/null_distribution/{organism}/threshold_{threshold}/label_permutation.csv` (organism-specific and threshold-specific subfolders). The `threshold` parameter must be passed to this function. **Dependency**: T019c_static.
- [X] T017 [US1] Implement `calculate_correlation` function in `code/statistics.py` to calculate Spearman's rank correlation between each centrality metric and essentiality labels. **Dependency**: T016.
- [X] T021 [US1] [P] Implement empirical p-value calculation in `code/statistics.py` by comparing the observed correlation (from T017) against the null distribution (from T020); update `results/correlations.json` with `empirical_p_value` and `null_distribution_summary`. **Dependency**: T017, T020.
- [X] T021b [US1] **Validate SC-001 Proportion Criterion**: Implement logic in `code/statistics.py` to aggregate results across all organisms, calculate the proportion of organisms where the correlation is statistically significant (p < 0.05), and compare this proportion against the high percentile (e.g., 95th) of the null distribution generated by shuffling labels across organisms. Save the result (pass/fail) and the specific comparison statistics to `results/correlations.json` under `sc001_validation`. **Dependency**: T020, T021.

### Null Model B: Graph Rewiring (FR-010)

- [X] T022 [US1] [P] Implement graph rewiring in `code/network_analysis.py` to generate a set of degree-preserving random graphs using the Maslov-Sneppen algorithm; save graphs to `results/null_distribution/{organism}/threshold_{threshold}/rewired_graphs/` (organism-specific and threshold-specific subfolders). The `threshold` parameter must be passed to this function. **Dependency**: T016.
- [X] T023 [US1] [P] Implement centrality computation on rewired graphs in `code/network_analysis.py` to calculate degree centrality for each rewired graph.
- [X] T024 [US1] [P] Implement correlation calculation on rewired graphs in `code/statistics.py` to compute Spearman correlation between rewired centrality and original essentiality labels; save results to `results/null_distribution/{organism}/threshold_{threshold}/rewired_correlations.csv`.
- [X] T025 [US1] [P] Implement statistical comparison in `code/statistics.py` to calculate the p-value for FR-010: aggregate rewired correlations (from T024) into a distribution, compare the observed correlation (from T017) against it by calculating `count(rewired_corr >= observed_corr) / total_rewired`, and save results to `results/correlations.json` with `rewired_p_value`. **Dependency**: T017, T024.
- [X] T086 [US1] **Address Review: Null Model Validation**: Implement a check in `code/statistics.py` to verify that the null distribution generated by label permutation (T020) has a mean correlation close to zero (|mean| < 0.05). If the mean deviates significantly, log a warning "Null distribution biased" and flag the result as potentially invalid. **Rationale**: Ensures the null model is functioning correctly.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `fetch_string_ppi` function in `code/data_loader.py` to fetch PPI networks from STRING API for each organism ID in `code/config.py` (from T004a). Use confidence threshold ≥700; if API fails for a specific organism, log a warning and skip that organism (do not crash the entire pipeline).
- [X] T014 [US1] Implement `fetch_deg_essentiality` function in `code/data_loader.py` to fetch gene essentiality labels (binary) from the DEG database. **Fallback Strategy**: Attempt primary FTP URL `ftp://ftp.ncbi.nlm.nih.gov/pub/microarray/deg/`. If that fails, attempt the official DEG API endpoint. If both fail, log a warning and skip the organism. Do NOT use synthetic data.
- [X] T015 [US1] Implement ID mapping logic in `code/data_loader.py` using Ensembl BioMart API to align STRING and DEG gene identifiers; log `mapping_coverage_percent`.
- [X] T016 [US1] Implement `compute_centrality` function in `code/network_analysis.py` to compute degree, betweenness, and eigenvector centrality using NetworkX. **Algorithm**: For networks >5,000 nodes, use `k`-sampling for betweenness. **Time-Budgeting**: If exact calculation on networks of moderate to large scale exceeds **25 minutes**, automatically switch to k-sampling with **k=100** to guarantee completion within the 30-minute FR-004 limit. Log the switch and sampling parameters. **Dependency**: T013, T014, T015.
- [ ] T018 [US1] Implement `run_organism_analysis` function in `code/main.py` that orchestrates the full pipeline for a single organism: calls `fetch_string_ppi`, `fetch_deg_essentiality`, `map_ids`, `compute_centrality`, `calculate_correlation`, **calls the null model functions (T020, T022)**, and `save_results`. This function must accept a `threshold` parameter. **Dependency**: T013, T014, T015, T016, T017, T020, T022.
- [X] T019 [US1] Add error handling for disconnected networks in `code/network_analysis.py`: check if edge count == 0; if so, assign 0 centrality for all nodes, log a specific warning "Network disconnected for {organism}", and skip further centrality calculation. This satisfies FR-004 and Edge Case requirements.
- [X] T046 [US1] Add explicit exclusion logging in `code/data_loader.py` for genes missing from the PPI network (Edge Case): count and log excluded genes per organism in `results/mapping_coverage.json` with the **specific JSON key `excluded_count`**. This ensures structured reporting for SC-005.
- [X] T048 [P] [US1] Add unit tests in `tests/unit/test_data_loader.py` to verify that `fetch_string_ppi` and `fetch_deg_essentiality` raise specific exceptions on network timeout or 404 errors, ensuring no silent fallback to synthetic data.
- [ ] T050 [P] [US1] Add a `--dry-run` flag to `code/main.py` that executes the data fetching and mapping steps for a single organism without computing centralities or correlations, to validate data sources and mapping coverage before a full run.
- [X] T051 [P] [US1] Add a logging statement in `code/network_analysis.py` to report the exact number of nodes and edges used for centrality calculation after any sampling or filtering, to ensure transparency in the computational process (Constitution Principle I).
- [X] T054 [P] [US1] Add a unit test in `tests/unit/test_data_loader.py` to verify that the ID mapping function correctly handles genes with multiple aliases and selects the most appropriate Ensembl ID based on the organism context.
- [X] T058 [P] [US1] DEFERRED: Add a retry mechanism with exponential backoff (limited attempts, base initial delay) to `code/data_loader.py` specifically for the Ensembl BioMart API calls in T015 to mitigate transient network errors without falling back to synthetic data.
- [X] T059 [P] [US1] DEFERRED: Implement a dedicated unit test in `tests/unit/test_data_loader.py` that mocks a persistent 500 error from the Ensembl BioMart API to verify that the retry logic eventually raises the correct `DataFetchError` after the maximum attempts.
- [X] T063 [P] [US1] DEFERRED: Create a contract test in `tests/contract/test_mapping_schema.py** to validate the structure of `results/mapping_coverage.json` (from T046), ensuring it contains the required fields: `organism_id`, `total_genes`, `mapped_genes`, and `coverage_percent`.
- [X] T066 [P] [US1] DEFERRED: Implement a check in `code/network_analysis.py` to verify that the graph is connected before computing betweenness centrality; if the graph is disconnected, log a warning and compute centrality only on the largest connected component, saving the component size in the results.
- [ ] T068 [US1] **Address Review: Data Source Verification**: Implement a pre-flight check in `code/main.py` that validates the existence and accessibility of the primary STRING (`) and DEG (`ftp://ftp.ncbi.nlm.nih.gov/pub/microarray/deg/`) URLs before any data fetching begins. If a primary source is unreachable for a specific organism, skip that organism and log a warning, but DO NOT exit the entire pipeline.
- [X] T069 [US3] **Address Review: Streaming Implementation**: Refactor `code/data_loader.py` to use `urllib.request` or `requests** with chunked reading for the DEG dataset if the FTP download fails or is too large for RAM. **Specifics**: Explicitly define `chunk_size = 1024 * 1024` (1MB) and trigger chunked mode if the estimated file size exceeds a substantial portion of available RAM. Ensure the code explicitly logs the `chunked=True` mode and the chunk size used. If chunked reading is used, the task must save a log entry in `results/mapping_coverage.json` stating `data_source_mode: "chunked"` and specifying `chunk_size = 1024 * 1024` (1MB). **Dependency**: T091 (Verification).
- [ ] T073 [US1] **Address Review: Data Fetching Robustness**: Implement a strict `try/except` block in `code/data_loader.py` for the primary STRING API call that raises a custom `DataFetchError` with the specific organism ID and error code if the fetch fails. Ensure this error is caught in `main.py` to skip the organism gracefully, but **never** falls back to synthetic data.
- [X] T074 [US1] **Address Review: ID Mapping Fallback**: Refactor `code/data_loader.py` to implement a secondary mapping strategy using Gene Symbols if Ensembl BioMart fails or returns low coverage (<10%). This secondary strategy must use a strict, case-sensitive string match against the DEG database and must log the specific number of genes matched via this fallback. If the fallback also fails, raise `DataFetchError`.
- [ ] T075 [P] [US3] Add a specific task in `code/main.py` to aggregate all sensitivity results into a single `results/sensitivity_summary.json` file for easy downstream plotting, containing all |Δρ| values and stability flags. **Dependency**: T035.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US2] Contract test for PGLS result schema in `tests/contract/test_pgls_schema.py`.
- [X] T028 [P] [US2] Integration test for cross-species comparison in `tests/integration/test_cross_species.py`: Use mock correlation data for multiple organisms and a mock tree; assert that `results/pgls_results.json` contains a valid PGLS statistic and p-value.

### Implementation for User Story 2

- [X] T028 [US2] Implement Fisher's z-transformation in `code/statistics.py` to normalize correlation coefficients for comparison.
- [X] T029a [US2] Implement PGLS model in `code/statistics.py` using `statsmodels` and the loaded phylogenetic tree (from T009a, validated by T009b) to test for differences in correlation strength. **Include logic to skip if effective sample size n < 10 and log "Power insufficient" warning** (FR-009). **Calculate and save Benjamini-Hochberg corrected p-values** (FR-008) as part of this function. **Dependency**: T009a, T009b, T028.
- [X] T029b [US2] [P] Write unit tests for the Benjamini-Hochberg correction logic within `tests/unit/test_statistics.py` to ensure correctness against known examples.
- [ ] T031 [US2] Add logic in `code/main.py` to skip PGLS if effective sample size n < 10 and log "Power insufficient" warning (FR-009).
- [X] T032 [US2] Save comparative statistics to `results/pgls_results.json` with metadata on organisms and tree used; **ensure Benjamini-Hochberg corrected p-values are saved** (FR-008).
- [X] T052 [P] [US2] **Remove Synthetic Tree Fallback**: Ensure `code/statistics.py` (T029a) does NOT attempt to construct a tree. If the tree is missing (T009b set `pgls_enabled=False`), skip PGLS with a clear warning as per FR-006.
- [X] T060 [P] [US2] DEFERRED: Add a validation check in `code/statistics.py` for the PGLS input data: ensure that the correlation coefficients and sample sizes passed to the model are strictly positive and that the sample size meets the minimum threshold (n >= 10) before model fitting, logging a clear error if violated.
- [X] T065 [P] [US2] DEFERRED: Add a unit test in `tests/unit/test_statistics.py` to verify the Fisher's z-transformation and inverse transformation functions, ensuring numerical stability and correctness for correlation coefficients near the boundaries (-1 and 1).
- [X] T066b [P] [US2] **Address Review: Phylogenetic Tree Validation**: Implement a check in `code/statistics.py` to verify that the phylogenetic tree (from T009a) contains all organism IDs used in the correlation analysis. If any are missing, log a warning "Tree mismatch" and exclude those organisms from the PGLS analysis.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Sensitivity Analysis on Network Confidence (Priority: P3)

**Goal**: Re-run the correlation analysis varying the STRING confidence score threshold across a range of low, medium, and high values. to assess robustness.

**Independent Test**: Run pipeline with thresholds across a range for one organism; verify output contains separate results for each threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_schema.py`.
- [X] T034 [P] [US3] Integration test for multi-threshold run in `tests/integration/test_sensitivity.py`: Run with a range of thresholds for a mock organism.; assert that `results/sensitivity_report.md` contains a table with |Δρ| values and a pass/fail flag for SC-002.

### Implementation for User Story 3

- [ ] T035b [US3] **Implement Configurable Threshold Loading**: Implement logic in `code/config.py` to dynamically load and validate the `CONFIDENCE_THRESHOLDS` list from the YAML configuration file. Add validation to ensure the list is non-empty, strictly increasing, and within the valid STRING confidence range (0-1000). This task ensures FR-007's "configurable" requirement is met.
- [ ] T035 [US3] Refactor `code/main.py` to include a `run_sensitivity_analysis` function that iterates over the list of confidence thresholds loaded from `code/config.py` (via T035b). For each threshold, call `run_organism_analysis` (from T018) with the specific threshold. **Critical**: Re-use the generic functions from T020 (label permutation) and T022 (graph rewiring); do NOT re-implement logic. Implement caching of intermediate results (e.g., centrality metrics) to avoid redundant computation across thresholds. **Dependencies**: This task depends on T018, T020, T022, and T035b being complete.
- [X] T036 [P] [US3] Implement logging for network sparsity (flag if edges < 500) while allowing NaN/0 returns for centrality metrics (Edge Case).
- [X] T037 [US3] **Generate Sensitivity Report**: Generate `results/sensitivity_report.md` summarizing correlation coefficients and stability (|Δρ|) across thresholds; MUST include a table of |Δρ| values for each threshold pair and a pass/fail flag for SC-002 (stability ≤ 0.1). **Logic**: Calculate the maximum absolute difference in correlation coefficients across the entire set of thresholds and compare that single max value to the **specific threshold of 0.1**. **CRITICAL**: This task MUST also generate `results/sensitivity_summary.json` containing all |Δρ| values and stability flags. **Dependency**: This task depends on T035 completing successfully.
- [X] T038 [P] [US3] Verify SC-002: Calculate absolute difference in correlation coefficients across thresholds and flag if > 0.1; log pass/fail status for SC-002 in `results/sensitivity_report.md`.
- [ ] T053 [P] [US3] Add a validation step in `code/main.py` to ensure the `CONFIDENCE_THRESHOLDS` list is strictly increasing and within the valid STRING range before starting the sensitivity loop.
- [ ] T057 [US3] Add a task to `code/main.py` to generate a visual summary (e.g., a simple text-based ASCII plot or a summary table) of the sensitivity analysis results in `results/sensitivity_report.md` to improve readability of the |Δρ| values.
- [X] T061 [US3] **Address Review: Threshold Edge Case Handling**: Modify `code/network_analysis.py` to handle the specific case where a high confidence threshold (e.g., 900) results in a network with < 500 edges. Instead of just logging, the code must explicitly set `centrality_metrics` to `NaN` or `0` for that organism/threshold combination and record `reason: "network_too_sparse"` in the output JSON.
- [ ] T064 [P] [US3] DEFERRED: Refactor `code/main.py` to ensure that the `run_sensitivity_analysis` function (T035) properly propagates exceptions from the inner `run_organism_analysis` calls (T018) so that a failure in one threshold does not silently skip the entire sensitivity loop.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Documentation updates in `quickstart.md` and `research.md` (Ensure all steps are verified). **Deliverable**: `quickstart.md` with Environment Setup, Data Fetching commands, Pipeline Execution, and Reproducibility Verification steps; `research.md` must list all data sources and their verification status.
- [X] T040 Code cleanup and refactoring of `code/` modules (Refactor `code/data_loader.py` to reduce cyclomatic complexity < 10 and remove unused imports; run flake8 --max-complexity=10).
- [ ] T041c [P] **Define Execution Time Limit**: Implement `EXECUTION_TIME_LIMIT_HOURS = 6` in `code/config.py`. Add logic in `code/main.py` to measure total runtime and log a warning if it exceeds a high threshold of this limit, and an error if it exceeds 100%. This task satisfies SC-004 by defining and enforcing the limit.
- [ ] T041a [P] Run profiling: Execute `code/main.py` with `cProfile` on a representative organism to identify bottlenecks. **Dependency**: This task must run after T016 has been executed to generate profiling data. **Deliverable**: `results/profiles/cprofile_report.txt`.
- [X] T041b [P] Implement optimizations: Refactor `code/network_analysis.py` based on T041a results to optimize centrality algorithms (T016) to meet the 30-minute runtime requirement for 25k nodes. **Focus**: Optimize centrality algorithms, not data fetches. If profiling shows T016 is the bottleneck, T041b replaces the implementation of T016. **Dependency**: T041c, T041a.
- [X] T042 [P] Additional unit tests in `tests/unit/` for centrality algorithms and statistical functions. **Specifics**: Write tests for `compute_centrality` (degree, betweenness, eigenvector), `calculate_correlation` (Spearman), and `pgls_model` (PGLS) in `tests/unit/test_network_analysis.py` and `tests/unit/test_statistics.py`.
- [X] T043 Run `hash_checker.py` and verify `state/` artifact hashes are updated.
- [ ] T044 [P] Implement `quickstart.md` and `research.md` with exact reproduction steps: Environment Setup, Data Fetching (commands), Pipeline Execution, and Reproducibility Verification. This task is critical for Constitution Principle I and must be completed before Phase 3. `quickstart.md` must include the exact commands to run `main.py` and verify outputs. `research.md` must list all data sources and their verification status.

---

## Phase 8: Final Validation & Execution Readiness (New)

**Purpose**: Ensure the pipeline is robust, reproducible, and ready for the execution gate.

- [X] T077 [P] **Address Review: End-to-End Smoke Test**: Create a new integration test `tests/integration/test_smoke_run.py` that runs the full pipeline on a single, small organism (e.g., *S. cerevisiae*) with a mock phylogenetic tree and mock data files. This test must verify that all output files (`correlations.json`, `pgls_results.json`, `sensitivity_report.json`) are generated with the correct schema and non-null values where expected.
- [ ] T078 [P] **Address Review: Documentation Completeness**: Update `quickstart.md` to include a "Troubleshooting" section that explicitly lists the error codes and log messages generated by T073, T074, T075, and T076, and provides the exact steps a user should take to resolve them (e.g., "Check network connectivity", "Verify organism ID in config"). **Note**: This section MUST NOT suggest workarounds that bypass data validation gates (e., "use synthetic data"); it should only guide users to fix the root cause or re-run the pipeline.
- [ ] T079 [P] **Address Review: Artifact Hashing**: Verify that `code/hash_checker.py` is executed as the final step of `main.py` and that it updates the `state/projects/PROJ-452-...yaml` file with the SHA256 hashes of all generated JSON and Markdown files in `results/`. Ensure the hash of `research.md` is also included to verify citation integrity.

---

## Phase 9: Analysis-Driven Revision & Gap Resolution

**Purpose**: Address specific issues raised by `/speckit.analyze` regarding data source reliability, statistical power, and result interpretation.

**Independent Test**: Re-run `/speckit.analyze` after implementing these tasks and verify the report contains zero "Critical" or "High" severity issues related to data fabrication or missing logic.

### Implementation for Revision Concerns

- [X] T083 [US1] **Address Review: Missing Real Data Source for E. coli**: Implement `fetch_string_ppi` for organism ID '83333' (E. coli) using the explicit URL pattern ` and verify the response contains at least 500 edges. If the API returns 404 or empty data, raise `DataFetchError` immediately. **Rationale**: The current plan assumes E. coli data exists; this task validates the real source availability before execution.
- [X] T084 [US1] **Address Review: Degraded Network for High Thresholds**: Implement a pre-calculation check in `code/network_analysis.py` that counts edges for each threshold before centrality computation. If edges < 500, log "Threshold {t} too sparse for {organism}" and skip centrality calculation for that organism/threshold pair, recording the skip reason in `results/sensitivity_summary.json`. **Rationale**: Ensures the pipeline does not attempt to compute metrics on invalid graphs.
- [X] T085 [US2] **Address Review: PGLS Power Insufficiency**: Implement a dynamic check in `code/statistics.py` that calculates the effective sample size (organisms with valid correlations AND tree tips). If n < 10, skip the PGLS model fitting, log "Power insufficient: n={n}" and record a `skipped` status in `results/pgls_results.json` with the reason. **Rationale**: Prevents statistical errors when sample size is too small for the model.
- [ ] T087 [US3] **Address Review: Sensitivity Threshold Validation**: Implement a check in `code/main.py` to verify that the sensitivity analysis loop does not silently skip thresholds due to data fetch errors. If a specific threshold fails for an organism, the result must be recorded as `null` or `skipped` in `results/sensitivity_summary.json` with a specific error reason. **Rationale**: Ensures the sensitivity analysis results are complete and transparent.

**Checkpoint**: At this point, all analysis-driven revision concerns should be addressed, and the pipeline should be robust against common failure modes.

---

## Phase 10: Final Execution Readiness & Data Source Verification

**Purpose**: Final verification of real data sources and execution readiness before the execution gate.

- [ ] T090 [P] [US1] **Verify E. coli STRING Data Availability**: Execute a one-time check in `code/data_loader.py` to fetch PPI data for E. coli (ID 83333) from STRING with threshold 700. If the API returns fewer than 500 edges or fails, log a CRITICAL warning "E. coli data unavailable; removing from organism list" and update `code/config.py` to exclude '83333' from `ORGANISM_IDS`. **Rationale**: Ensures the pipeline does not fail during execution due to missing real data for a specific organism.
- [X] T091 [P] [US1] **Verify DEG Data Streaming Capability**: Execute a one-time check in `code/data_loader.py` to stream the first 10MB of the DEG FTP dataset. If the stream fails or returns fewer than 1000 lines, log a CRITICAL warning "DEG data stream failed; verify FTP access" and halt execution. **Rationale**: Ensures the streaming implementation (T069) is functional before full execution. **Dependency**: T090.
- [ ] T092 [P] [US2] **Verify Phylogenetic Tree Completeness**: Execute a one-time check in `code/statistics.py` to verify that the fetched phylogenetic tree (from T009a) contains all organism IDs currently in `code/config.py` (after T090). If any are missing, log a CRITICAL warning "Phylogenetic tree incomplete; removing missing organisms from PGLS" and update `code/config.py` to exclude those organisms. **Rationale**: Ensures the PGLS analysis has sufficient data points.
- [X] T093 [P] **Final Pre-Execution Smoke Test**: Run the full pipeline on a single organism (S. cerevisiae) with all validation checks enabled. Verify that all output files are generated, all schema validations pass, and no "CRITICAL" warnings were logged. **Deliverable**: `results/pre_execution_report.md` containing the summary of checks passed/failed. **Rationale**: Final verification before execution gate.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 9)**: Depends on completion of `/speckit.analyze` and identification of specific issues
- **Final Execution Readiness (Phase 10)**: Depends on completion of Phase 9 and all previous phases

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **Revision (Phase 9)**: Can start after `/speckit.analyze` has been run and issues identified
- **Final Execution Readiness (Phase 10)**: Can start after all previous phases are complete

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
- Different user stories can be worked on in parallel by different team members
- Revision tasks (Phase 9) can be worked on in parallel by different team members, as they address specific, independent issues
- Final Execution Readiness tasks (Phase 10) can be worked on in parallel, as they are independent verification checks

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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

### Revision Strategy

After `/speckit.analyze` runs:

1. Review the analysis report and identify specific issues
2. Assign revision tasks (Phase 9) to team members based on expertise
3. Implement revision tasks in parallel
4. Re-run `/speckit.analyze` to verify issues are resolved
5. If issues remain, escalate to `human_input_needed`

### Final Execution Readiness Strategy

After Phase 9 is complete:

1. Execute Phase 10 tasks to verify real data sources
2. Update configuration files based on verification results
3. Run final smoke test (T093)
4. Proceed to execution gate only if all checks pass

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Rule**: Never fall back to synthetic data. If a real data source fails, raise an error and skip the organism, but do not fabricate data.
- **Critical Rule**: Always state the exact streaming/sampling rule used for large datasets.
- **Critical Rule**: Always verify the null model is functioning correctly (mean correlation close to zero).
- **Critical Rule**: Always validate the phylogenetic tree before PGLS analysis.
- **Critical Rule**: Always check for sufficient sample size before PGLS analysis.
- **Critical Rule**: Always check for sufficient mapping coverage before analysis.
- **Critical Rule**: Always check for sufficient network connectivity before centrality calculation.
- **Critical Rule**: Always check for statistical significance before including results in cross-species comparison.
- **Critical Rule**: Always report sensitivity analysis results clearly and transparently.
- **Critical Rule**: Always ensure the pipeline is robust against common failure modes (API errors, data fetch failures, model convergence errors).
- **Critical Rule**: Always ensure the pipeline is reproducible (fixed seeds, pinned dependencies, checksummed data).
- **Critical Rule**: Always ensure the pipeline is traceable (one row, one block, one statistic).
- **Critical Rule**: Always ensure the pipeline is valid (correct statistical methods, correct data sources, correct logic).
- **Critical Rule**: Always verify real data sources before execution (Phase 10).

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T094 Reconcile run-book vs implementation for `code/data/download_string.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/data/download_string.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T095 Reconcile run-book vs implementation for `code/data/download_deg.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/data/download_deg.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T096 Reconcile run-book vs implementation for `code/data/download_depmap.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/data/download_depmap.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
