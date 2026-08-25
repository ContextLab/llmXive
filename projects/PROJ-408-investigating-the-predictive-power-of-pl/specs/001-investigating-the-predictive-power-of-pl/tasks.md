# Tasks: Investigating the Predictive Power of Plant Phylogeny on Secondary Metabolite Profiles

**Input**: Design documents from `/specs/001-phylogeny-metabolite-prediction/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per plan.md structure)
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `scripts/setup_project.py` to programmatically generate all required directories (`code/`, `data/raw/`, `data/processed/`, `output/figures/`, `output/reports/`, `tests/`, `tests/contract/schemas/`).

- [X] T001b [P] Execute `scripts/setup_project.py` to initialize the repository structure.

- [X] T002 [P] Initialize Python project with pinned Python dependencies in `requirements.txt` (biopython, scikit-bio, scipy, pandas, numpy, ete3, requests, lxml, matplotlib, seaborn, pytest). **Note**: System binaries `mafft` and `fasttree` are NOT included here; see Ta.

- [ ] T002a [P] Install system binaries `mafft` and `fasttree` on the runner via `apt-get install mafft fasttree` (or equivalent for the runner OS). **Constraint**: Must verify binaries are in PATH before proceeding.

- [ ] T003 [P] Configure linting (ruff/flake) and formatting (black) tools. **Constraint**: Must enforce specific error codes for unused imports and missing type hints.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` to manage paths, API keys, random seeds, and data retention thresholds (a high proportion).

- [X] T005 [P] Implement robust logging infrastructure in `code/logging_config.py` (file + console handlers, structured JSON for pipeline steps).

- [X] T006 [P] Create base entity dataclasses in `code/entities.py` (PlantSpecies, PhylogeneticTree, MetaboliteProfile, DistanceMatrix).

- [X] T007 [P] Implement data integrity utilities in `code/utils.py` (checksum verification, streaming file iterators, error handling wrappers).

- [ ] T008 [P] Implement environment variable validation in `code/validate_env.py`. **Constraint**: Must raise `ValueError` with specific message if required variables (API keys, paths) are missing; no silent fallbacks to synthetic data.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Phylogenetic Signal Detection (Priority: P1) 🎯 MVP

**Goal**: Retrieve multi-locus genomic data and KEGG metabolite profiles, build phylogeny, and run Mantel test.

**Independent Test**: The system executes the full pipeline on a small sample, producing a valid tree, metabolite matrix, and a Mantel r/p-value, while correctly rejecting runs with >20% data loss.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests AFTER the skeleton implementation exists but BEFORE the full implementation.
> **Clarification**: The correct execution order for Test-Driven Development (TDD) in this context is:
> 1. **T013 (Skeleton)**: Create empty or minimal stubs for `code/data_loader.py` and `code/phylo_pipeline.py`.
> 2. **T010-T012 (Tests)**: Implement the test cases which will fail against the stubs.
> 3. **T013 (Full Implementation)**: Implement the full logic in `code/data_loader.py` and `code/phylo_pipeline.py` to make the tests pass.
> Do not attempt to run T010-T012 before T013 (skeleton) exists.

- [X] T010 [P] [US1] Contract test for data loader output schema. **Deliverable**: Create `tests/contract/schemas/data_loader.yaml` and `tests/contract/test_data_loader.py` with function `test_data_loader_schema_matches`. Assert output matches schema.

- [ ] T011 [P] [US1] Integration test for full pipeline run on a diverse set of species. **Input**: `data/raw/test_species_10.txt`. **Output**: `data/processed/test_tree.newick`. **Assertion**: `assert p-value < 0.05` (or < 0.1 for small sample).

- [ ] T012 [P] [US1] Negative control test: Verify shuffled metabolite profiles yield negligible correlation. **Threshold**: `|r| < 0.05`. **Input**: Real phylogenetic distances + shuffled metabolite matrix.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data_loader.py`: NCBI Entrez fetcher for ribosomal and plastid marker genes. **Constraint**: Must raise `ValueError` with species ID and missing locus details if fetch fails; NO synthetic fallback. Log format must include species ID and locus. **Note**: Implement skeleton first, then full implementation after T010-T012.

- [X] T014 [US1] Implement `code/data_loader.py`: KEGG COMPOUND/BRITE fetcher for secondary metabolite presence/absence. **Constraint**: Must handle species with no KEGG entry by excluding from matrix but flagging in log (do not halt).

- [X] T015a [US1] Implement `code/phylo_pipeline.py`: Multi-locus sequence concatenation. **Input**: Individual FASTA files from T013. **Output**: Single concatenated FASTA per species.

- [X] T015b [US1] Implement `code/phylo_pipeline.py`: Multi-locus sequence alignment using the `mafft` binary (via subprocess). **Input**: Concatenated FASTA from a designated sample. **Output**: Aligned FASTA. **Constraint**: Must use `mafft` binary with `--thread` flags; no alternative aligners.

- [X] T016a [US1] Implement `code/phylo_pipeline.py`: Prepare alignment for FastTree (formatting, trimming if needed). **Input**: Aligned FASTA from T015b.

- [X] T016b [US1] Implement `code/phylo_pipeline.py`: Maximum-likelihood tree construction using FastTree binary. **Input**: Prepared alignment from T016a. **Output**: Newick tree file.

- [X] T017 [US1] Implement `code/phylo_pipeline.py`: Patristic distance matrix calculation. **Constraint**: Must treat unresolved nodes (polytomies) as average path length (sum of branch lengths), consistent with `ape` package defaults.

- [X] T018 [US1] Implement `code/stats_engine.py`: Jaccard dissimilarity matrix calculation from binary metabolite vectors.

- [ ] T019 [US1] Implement `code/stats_engine.py`: Mantel test with a sufficient number of permutations for statistical robustness. **Deliverables**: Output r and p-value, save the null distribution histogram data to `data/processed/null_distribution.json`, AND generate a validation log entry in `output/reports/validation_log.txt` explicitly stating "SC-001: p < 0.05 (PASS)" or "SC-001: p > 0.05 (FAIL)". **Constraint**: p-value must be calculated explicitly against the saved null distribution.

- [X] T020a [US1] Implement `code/main.py`: Orchestration logic. **Constraint**: Must distinguish between 'total data loss' (>20% species missing BOTH sequence and metabolite data -> HALT) and 'partial exclusion' (species missing KEGG only -> EXCLUDE from matrix, RETAIN in tree, LOG warning).

- [ ] T020b [US1] Implement `code/main.py`/`code/report.py`: SC-003 Verification. **Logic**: Calculate final retention percentage (species with both data types / total target). Compare against the target threshold. **Deliverable**: Append status "SC-003: Retention X% (PASS/FAIL)" to `output/reports/validation_log.txt`.

- [ ] T021 [US1] Save raw downloads to `data/raw/` with checksums. **Constraint**: Must update `state/projects/PROJ-408...yaml` `artifact_hashes` map with checksums (primary source of truth); local `checksums.txt` is secondary only.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Environmental Control via Partial Mantel Test (Priority: P2)

**Goal**: Integrate USDA climate data to construct a climate distance matrix and run a Partial Mantel test.

**Independent Test**: The system produces a Partial Mantel r and p-value, comparing it against the standard Mantel r, and logs warnings for low-power climate clusters.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US2] Contract test for climate distance matrix schema. **Deliverable**: Create `tests/contract/schemas/climate_matrix.yaml` and `tests/contract/test_climate_data.py` with function `test_climate_matrix_schema_matches`.

- [ ] T023 [P] [US2] Integration test for Partial Mantel calculation. **Input**: `data/processed/phylo_dist_matrix.csv`, `data/processed/climate_dist_matrix.csv`. **Output**: `data/processed/partial_mantel_results.json`. **Assertion**: `assert partial_r` is calculated and differs from `standard_r` by > 0.0 (if signal exists).

### Implementation for User Story 2

- [X] T024 [US2] Implement `code/data_loader.py`: USDA PLANTS climate zone fetcher (streaming if large, or direct URL fetch). **Constraint**: Must use verified real source; no mock data.

- [ ] T025 [US2] Implement `code/stats_engine.py`: Climate distance matrix construction. **Input**: USDA PLANTS climate zone assignments. **Metric**: Euclidean distance on normalized continuous climate vectors derived from USDA PLANTS data. **Justification**: See plan.md Constitution Check Section VII (Continuous vectors used despite "zone" terminology for finer resolution). **Constraint**: Do NOT use binary metrics (Jaccard/Hamming).

- [ ] T026 [US2] Implement `code/stats_engine.py`: Partial Mantel test implementation (controlling for climate matrix). **Dependencies**: T017 (Phylogenetic Distance Matrix), T025 (Climate Distance Matrix). **Note**: Does NOT depend on T019 (Standard Mantel result).

- [ ] T027 [US2] Implement `code/main.py`: Logic to aggregate results (Standard Mantel r vs. Partial Mantel r) and verify cluster sizes. **Constraint**: If any climate cluster has <20 species, explicitly LOG a warning regarding low power but PROCEED with the full dataset analysis. Do NOT fail or mark as invalid.

- [ ] T028 [US2] Save climate matrix and partial test results to `data/processed/` with derivation logs.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate publication-quality plots and a text summary of results.

**Independent Test**: The system generates `phylo_metabolite_heatmap.png`, `mantel_results.png`, and `analysis_summary.txt` with correct data.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Visual regression test for heatmap output. **Tool**: `pytest-mpl` with baseline image at `tests/contract/baselines/phylo_metabolite_heatmap.png`. **Assertion**: Check file existence, minimum size (> 100KB), and pixel similarity score > 0.95.

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/viz.py`: Phylogenetic tree heatmap overlay (metabolite clusters) using `ete3` or `matplotlib`/`seaborn`. Save as `output/figures/phylo_metabolite_heatmap.png`.

- [ ] T031 [US3] Implement `code/viz.py`: Scatter plot (Phylo Dist vs. Metabolite Dissimilarity) with regression line and permutation distribution histogram. Save as `output/figures/mantel_results.png`.

- [ ] T032 [US3] Implement `code/main.py`/`code/report.py`: Text summary generator. **Dependencies**: T019 (Mantel stats), T017 (Distance Matrix), T026 (Partial Mantel results). **Deliverables**: Must include headline r, p-value, partial r, and the comparative ratio (partial r / standard r) to assess robustness per SC-002. Save as `output/reports/analysis_summary.txt`.

- [ ] T033 [US3] Ensure all figures meet high-resolution standards (DPI ≥ 300) for publication readiness.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034a [P] Generate `docs/README.md` with project overview, installation instructions, and usage examples.

- [ ] T034b [P] Generate `docs/quickstart.md` with step-by-step guide to run the full pipeline.

- [ ] T036 [P] Performance optimization: Ensure streaming logic handles large species lists within 7GB RAM limit.

- [ ] T037 [P] Run full pipeline on a representative subset to verify runtime compliance. (SC-004)

- [ ] T038 [P] Verify all `data/raw/` files have corresponding checksums in `state/projects/...yaml` and `data/processed/` files have derivation logs

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data loader patterns established in US1, but statistically independent. **Note**: T026 (Partial Mantel) requires T017 (Phylo Dist) and T025 (Climate Dist), NOT T019.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on output from US1 and US2 (results and matrices). **Note**: T032 requires T019, T017, AND T026 outputs.

### Within Each User Story

- **Tests (if included) MUST be written AFTER skeleton code exists but BEFORE full implementation**: T013 (skeleton) -> T010-T012 (tests) -> T013 (full implementation).
- **Data loading and validation (T013, T014) MUST precede alignment (T015a, T015b)**
- **Alignment (T015b) MUST precede tree building (T016b)** (via T015a -> T015b -> T016a -> T016b flow)
- **Tree building (T016b) MUST precede distance calculation (T017)**
- **Distance calculations MUST precede statistical tests (T019, T026)**
- **Statistical tests MUST precede visualization (T030, T031)**

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Visualization tasks (T030, T031) can run in parallel once data is ready

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data loader output schema in tests/contract/test_data_loader.py"
Task: "Integration test for full pipeline run on 10 species in tests/integration/test_mantel_pipeline.py"

# Launch data fetching tasks (if multiple loci can be fetched in parallel):
Task: "Implement NCBI Entrez fetcher for 18S"
Task: "Implement NCBI Entrez fetcher for rbcL"
Task: "Implement NCBI Entrez fetcher for matK"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Core Phylogenetic Signal)
4. **STOP and VALIDATE**: Test User Story 1 independently. Ensure data loss < 20% and Mantel test runs.
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Environmental Control)
4. Add User Story 3 → Test independently → Deploy/Demo (Visualization)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data + Phylo + Stats)
 - Developer B: User Story 2 (Climate + Partial Stats)
 - Developer C: User Story 3 (Viz + Reporting)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- **CRITICAL**: Never use synthetic data. If real data fetch fails, the task must fail loudly (raise ValueError).
- **CRITICAL**: Ensure streaming logic is implemented for large datasets to respect 7GB RAM limit.
- **CRITICAL**: System binaries (mafft, fasttree) must be installed via system package manager (T002a), not pip.
- **CRITICAL**: Checksums must be recorded in `state/projects/...yaml` (T021).
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence