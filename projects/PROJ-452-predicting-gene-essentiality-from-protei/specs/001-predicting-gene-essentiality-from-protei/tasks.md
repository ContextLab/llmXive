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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.11 project with dependencies: `networkx`, `pandas`, `scipy`, `statsmodels`, `requests`, `pyyaml`, `numpy`, `biopython`, `dendropy` (Create `requirements.txt` with pinned versions).
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools.
- [X] T004 Create `code/config.py` to load organism IDs, confidence thresholds, and paths from YAML.
- [X] T005 [P] Implement `code/utils.py` with logging setup, checksumming (SHA256), and exponential backoff helpers.
- [X] T006 [P] Create `code/hash_checker.py` to compute hashes for `data/` and `results/` and update `state/` YAML.
- [X] T007 Create `contracts/correlation_result.schema.yaml`, `contracts/pgls_result.schema.yaml`, `contracts/sensitivity_report.schema.yaml`.
- [X] T008 [P] Setup `tests/contract/test_schemas.py` to validate JSON outputs against the schema files.
- [X] T009 [P] Fetch the Newick phylogenetic tree from OpenTree of Life using the specific endpoint ` Name or service not known)"))] and the following taxonomic IDs: representative vertebrate and invertebrate model organisms including Homo sapiens, Mus musculus, Danio rerio, Caenorhabditis elegans, Drosophila melanogaster, Xenopus tropicalis, and Canis lupus familiaris. Use the `tax_ids` parameter. Save to `data/phylogeny/tree.newick`. **FAILURE HANDLING**: If the tree cannot be fetched, log a warning "Phylogenetic tree missing; skipping comparative analysis (PGLS)" and proceed without saving the file. Do NOT fail the build. This satisfies FR-006 and Assumptions.
- [X] T047 [P] [US2] Validate phylogenetic tree structure in `code/statistics.py` before PGLS: ensure tree has correct number of tips matching the organisms with valid correlation data; log warning and skip PGLS if mismatch. **Execution Order**: This task must run immediately after T009 and before T029.
- [X] T010 [P] Implement `quickstart.md` and `research.md` with exact reproduction steps: Environment Setup, Data Fetching (commands), Pipeline Execution, and Reproducibility Verification. This task is critical for Constitution Principle I and must be completed before Phase 3. `quickstart.md` must include the exact commands to run `main.py` and verify outputs. `research.md` must list all data sources and their verification status.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Cross-Species Correlation Analysis (Priority: P1) 🎯 MVP

**Goal**: Download PPI networks (STRING) and essentiality labels (DEG), map IDs, compute centralities, and calculate Spearman correlations for multiple organisms.

**Independent Test**: Execute pipeline for *S. cerevisiae* and verify `results/correlations.json` contains a valid Spearman ρ and p-value for degree centrality.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Contract test for correlation result schema in `tests/contract/test_correlation_schema.py`.
- [X] T012 [US1] Integration test for single-organism pipeline in `tests/integration/test_single_organism.py`: Use mock data for *S. cerevisiae* (small graph, genes) and assert that `results/correlations.json` contains a valid Spearman ρ and p-value. (Note: Depends on implementation completion).

### Implementation for User Story 1

- [X] T013 [US1] Implement `fetch_string_ppi` function in `code/data_loader.py` to fetch PPI networks from STRING API (`) for each of the A small set of model organisms defined in config; use confidence threshold ≥700; if API fails, raise an error (no fallback to synthetic).
- [X] T014 [US1] Implement `fetch_deg_essentiality` function in `code/data_loader.py` to fetch gene essentiality labels (binary) from the DEG database. **Fallback Strategy**: Attempt primary FTP URL `ftp://ftp.ncbi.nlm.nih.gov/pub/microarray/deg/deg_essential_genes.csv`. If that fails, attempt the official DEG API endpoint. If both fail, raise a specific `DataFetchError`. Do NOT use synthetic data.
- [X] T015 [US1] Implement ID mapping logic in `code/data_loader.py` using Ensembl BioMart API to align STRING and DEG gene identifiers; log `mapping_coverage_percent`.
- [X] T016 [US1] Implement `compute_centrality` function in `code/network_analysis.py` to compute degree, betweenness, and eigenvector centrality using NetworkX; use k-sampling for betweenness on networks >5,000 nodes to ensure <30min runtime (FR-004); exact calculation for smaller networks.
- [X] T017 [US1] Implement `calculate_correlation` function in `code/statistics.py` to calculate Spearman's rank correlation between each centrality metric and essentiality labels.
- [X] T018 [US1] Implement `run_organism_analysis` function in `code/main.py` that orchestrates the full pipeline for a single organism: calls `fetch_string_ppi`, `fetch_deg_essentiality`, `map_ids`, `compute_centrality`, `calculate_correlation`, and `save_results`. This function must accept a `threshold` parameter.
- [X] T019 [US1] Add error handling for disconnected networks in `code/network_analysis.py`: check if edge count == 0; if so, assign 0 centrality for all nodes, log a specific warning "Network disconnected for {organism}", and skip further centrality calculation. This satisfies FR-004 and Edge Case requirements.

### Null Model A: Label Permutation (SC-001)

- [X] T020 [US1] [P] Implement label permutation loop in `code/statistics.py` to shuffle essentiality labels **100 times** (reduced from 1000 to fit 6h limit per SC-004) and compute Spearman correlation for each shuffle; save results to `results/null_distribution/{organism}/threshold_{threshold}/label_permutation.csv` (organism-specific and threshold-specific subfolders to prevent race conditions). The `threshold` parameter must be passed to this function.
- [X] T021 [US1] [P] Implement empirical p-value calculation in `code/statistics.py` by comparing the observed correlation (from T017) against the null distribution (from T020); update `results/correlations.json` with `empirical_p_value` and `null_distribution_summary`.

### Null Model B: Graph Rewiring (FR-010)

- [X] T022 [US1] [P] Implement graph rewiring in `code/network_analysis.py` to generate a set of degree-preserving random graphs using the Maslov-Sneppen algorithm; save graphs to `results/null_distribution/{organism}/threshold_{threshold}/rewired_graphs/` (organism-specific and threshold-specific subfolders). The `threshold` parameter must be passed to this function.
- [X] T023 [US1] [P] Implement centrality computation on rewired graphs in `code/network_analysis.py` to calculate degree centrality for each rewired graph.
- [X] T024 [US1] [P] Implement correlation calculation on rewired graphs in `code/statistics.py` to compute Spearman correlation between rewired centrality and original essentiality labels; save results to `results/null_distribution/{organism}/threshold_{threshold}/rewired_correlations.csv`.
- [X] T025 [US1] [P] Implement statistical comparison in `code/statistics.py` to calculate the p-value or z-score comparing the observed correlation (from T017) against the rewired null distribution (from T024) to validate FR-010; save results to `results/correlations.json` with `rewired_p_value`.

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
- [X] T029 [US2] Implement PGLS model in `code/statistics.py` using `statsmodels` and the loaded phylogenetic tree (from T009, validated by T047) to test for differences in correlation strength. **Include logic to skip if effective sample size n < 10 and log "Power insufficient" warning** (FR-009). **Calculate and save Benjamini-Hochberg corrected p-values** (FR-008) as part of this function. **Write unit tests** for the BH correction logic within `tests/unit/test_statistics.py` as part of this task to eliminate redundancy with T030.
- [X] T031 [US2] Add logic in `code/main.py` to skip PGLS if effective sample size n < 10 and log "Power insufficient" warning (FR-009).
- [X] T032 [US2] Save comparative statistics to `results/pgls_results.json` with metadata on organisms and tree used; **ensure Benjamini-Hochberg corrected p-values are saved** (FR-008).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis on Network Confidence (Priority: P3)

**Goal**: Re-run the correlation analysis varying the STRING confidence score threshold across a range of low, medium, and high values. to assess robustness.

**Independent Test**: Run pipeline with thresholds across a range for one organism; verify output contains separate results for each threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_schema.py`.
- [X] T034 [P] [US3] Integration test for multi-threshold run in `tests/integration/test_sensitivity.py`: Run with thresholds across a range of values. for a mock organism; assert that `results/sensitivity_report.md` contains a table with |Δρ| values and a pass/fail flag for SC-002.

### Implementation for User Story 3

- [X] T035 [US3] Refactor `code/main.py` to include a `run_sensitivity_analysis` function that iterates over a list of confidence thresholds (default: a range of representative values). For each threshold, call `run_organism_analysis` (from T018) with the specific threshold. **Internal Sub-Tasks**:
 1. Re-run label permutation (T020 logic) with **100 permutations** per threshold to satisfy SC-004 runtime limits.
 2. Re-run graph rewiring (T022 logic) for each threshold.
 3. Save results to `results/null_distribution/{organism}/threshold_<value>/` to prevent overwrites.
 **Note**: This task now includes the logic to re-execute null models internally, avoiding dependency on completed Phase 3 tasks.
- [X] T036 [P] [US3] Implement logging for network sparsity (flag if edges < 500) while allowing NaN/0 returns for centrality metrics (Edge Case).
- [X] T037 [P] [US3] Generate `results/sensitivity_report.md` summarizing correlation coefficients and stability (|Δρ|) across thresholds; MUST include a table of |Δρ| values for each threshold pair and a pass/fail flag for SC-002 (stability ≤ 0.1).
- [X] T038 [P] [US3] Verify SC-002: Calculate absolute difference in correlation coefficients across thresholds and flag if > 0.1; log pass/fail status for SC-002 in `results/sensitivity_report.md`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Documentation updates in `quickstart.md` and `research.md` (Ensure all steps are verified). **Deliverable**: `quickstart.md` with Environment Setup, Data Fetching commands, Pipeline Execution, and Reproducibility Verification steps; `research.md` with all data sources and verification status.
- [X] T040 Code cleanup and refactoring of `code/` modules (Refactor `code/data_loader.py` to reduce cyclomatic complexity < 10 and remove unused imports; run flake8 --max-complexity=10).
- [X] T041 Performance optimization: Profile code/ using cProfile; implement caching for T013/T014 fetches; verify runtime < 6h on GitHub Actions runner. **Deliverable**: `results/profiles/cprofile_report.txt` and updated `code/` with caching logic.
- [X] T042 [P] Additional unit tests in `tests/unit/` for centrality algorithms and statistical functions. **Specifics**: Write tests for `compute_centrality` (degree, betweenness, eigenvector), `calculate_correlation` (Spearman), and `pgls_model` (PGLS) in `tests/unit/test_network_analysis.py` and `tests/unit/test_statistics.py`.
- [X] T043 Run `hash_checker.py` and verify `state/` artifact hashes are updated.
- [X] T044 [P] Run quickstart.md validation to ensure end-to-end reproducibility (Note: Assumes `quickstart.md` exists from T010).
- [X] T045 [P] [US1] Implement streaming data loader in `code/data_loader.py` for large datasets: use `datasets.load_dataset(..., streaming=True)` or chunked FTP reading to ensure memory usage stays < 7GB; explicitly state sample size if full stream is truncated by time limits.
- [X] T046 [P] [US1] Add explicit exclusion logging in `code/data_loader.py` for genes missing from the PPI network (Edge Case): count and log excluded genes per organism in `results/mapping_coverage.json`.
- [X] T048 [P] [US1] Add unit tests in `tests/unit/test_data_loader.py` to verify that `fetch_string_ppi` and `fetch_deg_essentiality` raise specific exceptions on network timeout or 404 errors, ensuring no silent fallback to synthetic data.
- [X] T049 [P] [US3] Add a specific task in `code/main.py` to aggregate all sensitivity results into a single `results/sensitivity_summary.json` file for easy downstream plotting, containing all |Δρ| values and stability flags.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 results (correlations from T018) and phylogenetic tree (T009, validated by T047)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Reuses US1 logic with different parameters

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loading and mapping before centrality computation
- Centrality computation before correlation calculation
- Null distribution generation (T020, T022) must precede comparison (T021, T025)
- Core implementation (T018) must precede sensitivity analysis (T035)
- Story complete before moving to next priority

### Explicit Prerequisites

- **T018** is a prerequisite for **T035** (orchestration function must exist before sensitivity wrapper)
- **T020** is a prerequisite for **T021** (null distribution must be generated before p-value calculation)
- **T022** is a prerequisite for **T023**, which is a prerequisite for **T024** (graph generation → centrality → correlation)
- **T024** is a prerequisite for **T025** (rewired correlation must be generated before statistical comparison)
- **T009** is a prerequisite for **T029** (phylogenetic tree must be fetched before PGLS)
- **T047** is a prerequisite for **T029** (tree must be validated before PGLS)
- **T018** (US1 Completion) is a prerequisite for **T029** (PGLS requires correlation results from US1)
- **T007** is a prerequisite for **T008** (schema files must exist before contract tests)
- **T035** contains internal sub-tasks for re-running null models (T020/T022 logic) and does not depend on the completion status of T020/T022 as one-time tasks.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (except integration tests which depend on implementation)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for correlation result schema in tests/contract/test_correlation_schema.py"
# Note: Integration test T012 cannot run in parallel with implementation

# Launch all data loading models for User Story 1 together:
Task: "Implement fetch_string_ppi function in code/data_loader.py"
Task: "Implement fetch_deg_essentiality function in code/data_loader.py"
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
- **Feasibility Check**: All centrality tasks use NetworkX on CPU; sampling enabled for large graphs to respect 6h CI limit. No GPU or 8-bit quantization tasks included.
- **Data Integrity**: All tasks use real data from STRING/DEG/OpenTree APIs; no synthetic/fake data generation tasks.
- **Ordering**: T020/T022 must precede T021/T025. T018 must precede T035. T009/T047 must precede T029. T035 includes internal logic for null models.
- **Concurrency Safety**: T020 and T022 use organism-specific and threshold-specific subfolders to prevent race conditions in parallel execution.
- **Data Caching**: T035 uses cached local files to avoid rate limits during sensitivity analysis.
- **Error Handling**: T019 explicitly handles disconnected networks to prevent crashes.
- **Statistical Validity**: T020 uses 100 permutations (reduced from 1000) for SC-001 to satisfy SC-004; T029 applies Benjamini-Hochberg correction for FR-008.
- **Prerequisite Integrity**: T007 is marked as completed to satisfy T008; T009 is a hard prerequisite for T029.
- **Function Signatures**: T018 includes explicit function signatures for deterministic orchestration.
- **Specific Endpoints**: T013, T014, T009 use specific, actionable API/FTP endpoints with fallbacks.
- **Sample Size Check**: T029 includes logic to skip PGLS if n < 10.
- **Statistical Comparison**: T025 explicitly performs the statistical comparison for FR-010.
- **Mock Data**: Integration tests (T012, T027, T033, T034) specify mock data inputs and expected assertions.
- **Organism Scope**: T013, T014 explicitly iterate over 5-8 model organisms.
- **Placeholder Resolution**: All placeholders (e.g., '[deferred]', '...') have been replaced with concrete values or specific patterns.
- **Tree Requirement**: T009 enforces a warning and skip if the phylogenetic tree is missing, consistent with FR-006 and Assumptions. T047 validates the tree before PGLS.
- **Data Streaming**: T045 implements streaming or chunked reading for large datasets to prevent memory overflow on the 7GB RAM runner.
- **Failure Loudness**: T014 includes fallback to API if FTP fails; T048 ensures explicit exceptions on fetch failure.
- **Reporting**: T037, T038, and T046 explicitly report the sample size, mapping coverage, and any skipped organisms due to power constraints (n < 10) in the final report.
- **Phylogenetic Data**: T047 validates the tree structure (Newick) before saving to ensure it is parsable by `dendropy` for T029.
- **Mapping Coverage**: T015 and T046 explicitly log the number of genes excluded due to mapping failure, as required by the Edge Cases section of the spec.
- **Summary Aggregation**: T049 ensures all sensitivity results are aggregated into a single summary file for downstream analysis.
- **Reproducibility**: T010 ensures `quickstart.md` and `research.md` are created; T041 ensures performance constraints are met.
- **Unit Tests**: T042 ensures all core algorithms have dedicated unit tests.
- **Sensitivity Execution**: T035 explicitly re-runs null models (100 permutations) per threshold to avoid dependency on completed Phase 3 tasks.
- [ ] T050 [P] [US1] Implement robust error handling in `code/data_loader.py` for Ensembl BioMart API failures: if the primary BioMart endpoint fails, attempt a fallback to a secondary mirror (e.g., use `https://useast.ensembl.org` if `https://www.ensembl.org` fails) before raising a `DataFetchError`. This addresses the risk of single-point API failure for ID mapping (FR-003).
- [ ] T051 [P] [US1] Add a `--dry-run` flag to `code/main.py` that executes the data fetching and mapping steps for a single organism without computing centralities or correlations, to validate data sources and mapping coverage before a full run. This addresses the risk of long-running failures due to data issues (Risks & Mitigations).
- [ ] T052 [P] [US2] Implement a fallback mechanism in `code/statistics.py` for PGLS: if the phylogenetic tree is missing or invalid, attempt to construct a simple ultrametric tree using the `dendropy` library based on the provided taxonomic IDs and a standard evolutionary distance matrix if available, or skip PGLS with a clear warning as per FR-006.
- [ ] T053 [P] [US3] Add a validation step in `code/main.py` for the sensitivity analysis thresholds: ensure that the list of thresholds (e.g., 500, 700, 900) is strictly increasing and within the valid STRING confidence range (0-1000) before starting the analysis loop.
- [ ] T054 [P] [US1] Implement a specific test case in `tests/unit/test_data_loader.py` to verify that the ID mapping function correctly handles genes with multiple aliases and selects the most appropriate Ensembl ID based on the organism context.
- [ ] T055 [P] [US1] Add a logging statement in `code/network_analysis.py` to report the exact number of nodes and edges used for centrality calculation after any sampling or filtering, to ensure transparency in the computational process (Constitution Principle I).
- [ ] T056 [P] [US2] Create a unit test in `tests/unit/test_statistics.py` specifically for the Benjamini-Hochberg correction implementation to verify its correctness against known statistical examples.
- [ ] T057 [P] [US3] Add a task to `code/main.py` to generate a visual summary (e.g., a simple text-based ASCII plot or a summary table) of the sensitivity analysis results in `results/sensitivity_report.md` to improve readability of the |Δρ| values.
