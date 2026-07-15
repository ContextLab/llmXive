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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `results/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with dependencies: `networkx`, `pandas`, `scipy`, `statsmodels`, `requests`, `pyyaml`, `numpy`, `biopython`, `dendropy`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/config.py` to load organism IDs, confidence thresholds, and paths from YAML
- [ ] T005 [P] Implement `code/utils.py` with logging setup, checksumming (SHA256), and exponential backoff helpers
- [ ] T006 [P] Create `code/hash_checker.py` to compute hashes for `data/` and `results/` and update `state/` YAML
- [ ] T007 Create `contracts/correlation_result.schema.yaml`, `contracts/pgls_result.schema.yaml`, `contracts/sensitivity_report.schema.yaml`
- [X] T008 [P] Setup `tests/contract/test_schemas.py` to validate JSON outputs against the schema files
- [ ] T009 [P] Fetch the Newick phylogenetic tree from OpenTree of Life (api.opentree.org) using taxonomic IDs for target organisms; save to `data/phylogeny/tree.newick`; if fetch fails, log a warning and skip the comparative test (PGLS) gracefully (per Spec Assumptions) rather than failing the build

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Cross-Species Correlation Analysis (Priority: P1) 🎯 MVP

**Goal**: Download PPI networks (STRING) and essentiality labels (DEG), map IDs, compute centralities, and calculate Spearman correlations for multiple organisms.

**Independent Test**: Execute pipeline for *S. cerevisiae* and verify `results/correlations.json` contains a valid Spearman ρ and p-value for degree centrality.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for correlation result schema in `tests/contract/test_correlation_schema.py`
- [ ] T011 [US1] Integration test for single-organism pipeline in `tests/integration/test_single_organism.py` (Note: Depends on implementation completion) <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data_loader.py` to fetch PPI networks from STRING API (default threshold ≥700) for several model organisms; use specific endpoint (e.g., `) and fallback to local `data/raw/` files if API is unreachable; define organism list in config
- [X] T013 [US1] Implement `code/data_loader.py` to fetch gene essentiality labels (binary) from DEG database (e.g., ` or direct CSV fetch) for the same organisms; fallback to local `data/raw/` if API fails; define organism list in config
- [X] T014 [US1] Implement ID mapping logic in `code/data_loader.py` using Ensembl BioMart API to align STRING and DEG gene identifiers; log `mapping_coverage_percent`
- [X] T015 [US1] Implement `code/network_analysis.py` to compute degree, betweenness, and eigenvector centrality using NetworkX; use k-sampling for betweenness on networks >5,000 nodes to ensure <30min runtime (FR-004); exact calculation for smaller networks
- [ ] T016 [US1] Implement `code/statistics.py` to calculate Spearman's rank correlation between each centrality metric and essentiality labels
- [ ] T017 [US1] Implement `code/main.py` orchestration loop: download → map → centrality → correlation → save to `results/correlations.json`
- [ ] T020 [US1] Add error handling for disconnected networks (assign 0 centrality) and missing gene overlaps (skip with warning)

### Null Model A: Label Permutation (SC-001)

- [ ] T018a [US1] [P] Implement label permutation loop in `code/statistics.py` to shuffle essentiality labels [deferred] times and compute Spearman correlation for each shuffle; save results to `results/null_distribution/label_permutation.csv`
- [ ] T018b [US1] [P] Implement empirical p-value calculation in `code/statistics.py` by comparing the observed correlation (from T016) against the null distribution (from T018a); update `results/correlations.json` with `empirical_p_value` and `null_distribution_summary`

### Null Model B: Graph Rewiring (FR-010)

- [ ] T019a [US1] [P] Implement graph rewiring in `code/network_analysis.py` to generate a set of degree-preserving random graphs using the Maslov-Sneppen algorithm; save graphs to `results/null_distribution/rewired_graphs/`
- [ ] T019b [US1] [P] Implement centrality computation on rewired graphs in `code/network_analysis.py` to calculate degree centrality for each rewired graph
- [ ] T019c [US1] [P] Implement correlation calculation on rewired graphs in `code/statistics.py` to compute Spearman correlation between rewired centrality and original essentiality labels; save results to `results/null_distribution/rewired_correlations.csv`; compare observed correlation against this null distribution to validate FR-010

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comparative Statistical Testing (Priority: P2)

**Goal**: Compare correlation coefficients across organisms using Phylogenetic Generalized Least Squares (PGLS) with Fisher's z-transformation.

**Independent Test**: Run analysis on at least two distinct organisms with a provided tree; verify `results/pgls_results.json` contains a PGLS statistic and p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for PGLS result schema in `tests/contract/test_pgls_schema.py`
- [ ] T022 [P] [US2] Integration test for cross-species comparison in `tests/integration/test_cross_species.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement Fisher's z-transformation in `code/statistics.py` to normalize correlation coefficients for comparison
- [ ] T024 [US2] Implement PGLS model in `code/statistics.py` using `statsmodels` and the loaded phylogenetic tree (from T009) to test for differences in correlation strength
- [ ] T025 [P] [US2] Implement Benjamini-Hochberg correction in `code/statistics.py` for multiple-comparison adjustment of PGLS p-values (FR-008) and apply in output generation
- [ ] T026 [US2] Add logic in `code/main.py` to skip PGLS if effective sample size n < 10 and log "Power insufficient" warning (FR-009)
- [ ] T027 [US2] Save comparative statistics to `results/pgls_results.json` with metadata on organisms and tree used

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis on Network Confidence (Priority: P3)

**Goal**: Re-run the correlation analysis varying the STRING confidence score threshold across a range of low, medium, and high values. to assess robustness.

**Independent Test**: Run pipeline with thresholds [500, 700] for one organism; verify output contains separate results for each threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_schema.py`
- [ ] T029 [P] [US3] Integration test for multi-threshold run in `tests/integration/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T030 [US3] Refactor `code/main.py` to accept a list of confidence thresholds (default: [500, 700, 900]); for each threshold, re-fetch data, re-map IDs, re-compute centralities, and re-calculate correlations; save results to `results/correlations.json` with key naming convention `threshold_<value>` (e.g., `threshold_500`, `threshold_700`) containing nested objects with correlation metrics and sample sizes
- [ ] T031 [P] [US3] Implement logging for network sparsity (flag if edges < 500) while allowing NaN/0 returns for centrality metrics (Edge Case)
- [ ] T032 [US3] Generate `results/sensitivity_report.md` summarizing correlation coefficients and stability (|Δρ|) across thresholds; MUST include a table of |Δρ| values for each threshold pair and a pass/fail flag for SC-002 (stability ≤ 0.1)
- [ ] T033 [US3] Verify SC-002: Calculate absolute difference in correlation coefficients across thresholds and flag if > 0.1; log pass/fail status for SC-002 in `results/sensitivity_report.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `quickstart.md` and `research.md`
- [ ] T035 Code cleanup and refactoring of `code/` modules
- [ ] T036 Performance optimization: ensure total runtime < 6 hours on GitHub Actions (2 CPU, 7GB RAM)
- [ ] T037 [P] Additional unit tests in `tests/unit/` for centrality algorithms and statistical functions
- [ ] T038 Run `hash_checker.py` and verify `state/` artifact hashes are updated
- [ ] T039 Run quickstart.md validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 results (correlations) and phylogenetic tree (T009)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Reuses US1 logic with different parameters

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loading and mapping before centrality computation
- Centrality computation before correlation calculation
- Null distribution generation (T018a, T019a) must precede comparison (T018b, T019c)
- Core implementation (T017) must precede sensitivity analysis (T030)
- Story complete before moving to next priority

### Explicit Prerequisites

- **T017** is a prerequisite for **T030** (orchestration loop must exist before refactoring for thresholds)
- **T018a** is a prerequisite for **T018b** (null distribution must be generated before p-value calculation)
- **T019a** is a prerequisite for **T019b**, which is a prerequisite for **T019c** (graph generation → centrality → correlation)
- **T009** is a prerequisite for **T024** (phylogenetic tree must be fetched before PGLS)

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
# Note: Integration test T011 cannot run in parallel with implementation

# Launch all data loading models for User Story 1 together:
Task: "Implement data_loader.py to fetch PPI networks"
Task: "Implement data_loader.py to fetch essentiality labels"
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
- **Data Integrity**: All tasks use real data from STRING/DEG/OpenTree APIs or local fallbacks; no synthetic/fake data generation tasks.
- **Ordering**: T018a/T019a must precede T018b/T019c. T017 must precede T030. T009 must precede T024.