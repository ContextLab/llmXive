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

- [X] T002 [P] Initialize Python project with pinned Python dependencies in `requirements.txt` (biopython, scikit-bio, scipy, pandas, numpy, ete3, requests, lxml, matplotlib, seaborn, pytest). **Note**: System binaries `mafft` and `fasttree` are NOT included here; see T002a.

- [X] T002a [P] Install system binaries `mafft` and `fasttree` on the runner via `apt-get install mafft fasttree`. **Constraint**: Must verify binaries are in PATH by running `mafft --version` and `FastTree --version` before proceeding. If `fasttree` is not found, attempt `apt-get install fasttree-mt` or build from source if the package is unavailable.

- [X] T003 [P] Configure linting (ruff/flake) and formatting (black) tools. **Constraint**: Must enforce specific error codes `F401` (unused import) and `ANN001` (missing type hint) via `ruff.toml` or `pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` to manage paths, API keys, random seeds, and data retention thresholds (80%).

- [X] T005 [P] Implement robust logging infrastructure in `code/logging_config.py` (file + console handlers, structured JSON for pipeline steps).

- [X] T006 [P] Create base entity dataclasses in `code/entities.py` (PlantSpecies, PhylogeneticTree, MetaboliteProfile, DistanceMatrix).

- [X] T007 [P] Implement data integrity utilities in `code/utils.py` (checksum verification, streaming file iterators, error handling wrappers).

- [X] T008 [P] Implement environment variable validation in `code/validate_env.py`. **Constraint**: Must raise `ValueError` with specific message if required variables (API keys, paths) are missing; no silent fallbacks to synthetic data.

- [X] T009 [P] [US1] Generate `data/raw/species_list.txt` containing the target list of plant species with valid NCBI Taxonomy IDs and KEGG organism codes. **Source**: Run `scripts/fetch_species_list.py` which queries a verified public source (e.g., a curated list from a published paper or a specific KEGG/NCBI query script) to populate this file. **Constraint**: This file MUST exist before T020a runs. **Format**: One species per line, `NCBI_ID\tKEGG_CODE\tScientificName`. **Threshold**: Target list must support at least 80% retention.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Phylogenetic Signal Detection (Priority: P1) 🎯 MVP

**Goal**: Retrieve multi-locus genomic data and KEGG metabolite profiles, build phylogeny, and run Mantel test.

**Independent Test**: The system executes the full pipeline on a small sample, producing a valid tree, metabolite matrix, and a Mantel r/p-value, while correctly rejecting runs with >20% data loss.

### Implementation for User Story 1

- [X] T020a [US1] Implement `code/main.py`: Orchestration logic. **Constraint**: Must read `data/raw/species_list.txt` (from T009) to calculate 'Total Target'. **Pre-condition**: Must verify `data/raw/species_list.txt` exists before proceeding; if missing, raise `FileNotFoundError`. Must distinguish between 'total data loss' (>20% species missing BOTH sequence AND metabolite data -> HALT) and 'partial exclusion' (species missing KEGG only -> EXCLUDE from matrix, RETAIN in tree, LOG warning). **Formula**: Data Loss = (Species with NO Sequence AND NO Metabolite) / Total Target. **Threshold**: Halt if >20%.

- [X] T013a [P] [US1] Create a stub function `fetch_species_data` in `code/data_loader.py` that raises `NotImplementedError`. **Constraint**: This task establishes the interface for T013b. **Signature**: `def fetch_species_data(species_id: str, loci: list) -> dict`.

- [X] T010 [P] [US1] Contract test for data loader output schema. **Deliverable**: Create `tests/contract/schemas/data_loader.yaml` and `tests/contract/test_data_loader.py` with function `test_data_loader_schema_matches`. Assert output matches schema.

- [X] T011a [P] [US1] Create fixture `data/raw/test_species_10.txt` containing 10 diverse plant species with valid NCBI IDs and KEGG codes for integration testing.

- [X] T013b [US1] Implement `code/data_loader.py`: NCBI Entrez fetcher for ribosomal and plastid marker genes (Full Implementation). **Constraint**: Must raise `ValueError` with species ID and missing locus details if fetch fails; NO synthetic fallback. Log format must include species ID and locus.

- [X] T014 [US1] Implement `code/data_loader.py`: KEGG COMPOUND/BRITE fetcher for secondary metabolite presence/absence. **Constraint**: Must handle species with no KEGG entry by excluding from matrix but flagging in log (do not halt).

- [X] T021 [P] [US1] Save raw downloads to `data/raw/` with checksums. **Constraint**: Must update `state/projects/PROJ-408-investigating-the-predictive-power-of-pl.yaml` `artifact_hashes.data_raw` map with checksums (primary source of truth); local `checksums.txt` is secondary only. **Path**: `state/projects/PROJ-408-investigating-the-predictive-power-of-pl.yaml`. **Order**: Must execute immediately after T013b and T014.

- [X] T015a [US1] Implement `code/phylo_pipeline.py`: Multi-locus sequence concatenation. **Input**: Individual FASTA files from T013b. **Output**: Single concatenated FASTA per species.

- [X] T015b [US1] Implement `code/phylo_pipeline.py`: Multi-locus sequence alignment using the `mafft` binary (via subprocess). **Input**: Concatenated FASTA from a designated sample. **Output**: Aligned FASTA. **Constraint**: Must use `mafft` binary with `--thread` flags; no alternative aligners.

- [X] T016a [US1] Implement `code/phylo_pipeline.py`: Prepare alignment for FastTree (formatting, trimming if needed). **Input**: Aligned FASTA from T015b.

- [X] T016b [US1] Implement `code/phylo_pipeline.py`: Maximum-likelihood tree construction using FastTree binary. **Input**: Prepared alignment from T016a. **Output**: Newick tree file.

- [X] T017 [US1] Implement `code/phylo_pipeline.py`: Patristic distance matrix calculation. **Constraint**: Must explicitly calculate distance as the sum of branch lengths from the root to the tips for unresolved nodes (polytomies), using `scikit-bio` or `ete3` to replicate `ape` package defaults (average path length). Do not rely on library defaults that might treat polytomies as zero-length.

- [X] T018 [US1] Implement `code/stats_engine.py`: Jaccard dissimilarity matrix calculation from binary metabolite vectors.

- [X] T019 [US1] Implement `code/stats_engine.py`: Mantel test with a sufficient number of permutations to ensure robust statistical inference. **Deliverables**: Output r and p-value to `data/processed/mantel_results.json`. **Constraint**: p-value must be calculated explicitly against the in-memory null distribution. **Edge Case**: Must detect degenerate distributions (zero variance in permutations) and report a specific warning/p-value. **Reproducibility**: Must save the full null distribution to `data/processed/null_distribution.json`. **Dependency**: T020a must pass the data loss check.

- [X] T011b [P] [US1] Integration test for full pipeline run on the 10 species fixture. **Input**: `data/raw/test_species_10.txt`. **Output**: `data/processed/test_tree.newick`. **Assertion**: `assert p-value is a float and 0 <= p-value <= 1`.

- [X] T012 [P] [US1] Negative control test: Verify shuffled metabolite profiles yield negligible correlation. **Threshold**: `|r| < 0.05`. **Input**: Real phylogenetic distances + shuffled metabolite matrix. **Dependency**: T019.

- [X] T020b [US1] Implement `code/main.py`/`code/report.py`: SC-003 Verification. **Logic**: Calculate final retention percentage (species with both data types / total target). Compare against a predefined target threshold. **Deliverable**: Append status "SC-003: Retention X% (PASS/FAIL)" to `output/reports/validation_log.txt`. **Dependency**: Requires T020a to have completed successfully.

- [X] T037 [P] [US1] Run full pipeline on a representative subset to verify runtime compliance (SC-004). **Constraint**: Must capture runtime, log it to `data/processed/runtime_metrics.json` (key: `runtime_seconds`), and assert it is <= 6 hours. **Dependency**: T019.

- [X] T037a [P] [US1] Implement runtime assertion logic for T037. **Constraint**: Must read `data/processed/runtime_metrics.json`, extract `runtime_seconds`, compare against a predefined runtime threshold, and raise `RuntimeError` if exceeded. **Dependency**: T037.

**Checkpoint**: At this point, User Story 1 core data pipeline is ready; T019 (Mantel test) is the critical path for final validation.

---

## Phase 4: User Story 2 - Environmental Control via Partial Mantel Test (Priority: P2)

**Goal**: Integrate USDA climate data to construct a climate distance matrix and run a Partial Mantel test.

**Independent Test**: The system produces a Partial Mantel r and p-value, comparing it against the standard Mantel r, and logs warnings for low-power climate clusters.

### Implementation for User Story 2

- [X] T022 [P] [US2] Contract test for climate distance matrix schema. **Deliverable**: Create `tests/contract/schemas/climate_matrix.yaml` and `tests/contract/test_climate_data.py` with function `test_climate_matrix_schema_matches`.

- [X] T024 [US2] Implement `code/data_loader.py`: USDA PLANTS climate zone fetcher (streaming if large, or direct URL fetch). **Constraint**: Must use verified real source; no mock data.

- [X] T025 [US2] Implement `code/stats_engine.py`: Climate distance matrix construction. **Input**: USDA PLANTS climate zone assignments. **Metric**: Euclidean distance on normalized continuous climate vectors derived from USDA PLANTS data (specifically: 'Hardiness Zone', 'Temperature Range', 'Precipitation'). **Justification**: See plan.md Constitution Check Section VII (Continuous vectors used despite "zone" terminology for finer resolution). **Constraint**: Do NOT use binary metrics (Jaccard/Hamming). **Note**: This deviates from Constitution Principle VII's "categories" requirement; justified by Plan.md Section VII for continuous resolution.

- [X] T025b [US2] Implement `code/stats_engine.py`: Stratified subset analysis. **Input**: Full dataset, climate zone categories. **Action**: Calculate Mantel r-values for each climate zone subset (if n >= 20). **Constraint**: If n < 20, log a warning and skip that cluster. **Deliverable**: Write comparison results to `data/processed/stratified_temp.txt` (intermediate file). **Note**: This is a supplementary analysis to T026 (Partial Mantel), not a replacement.

- [X] T026 [US2] Implement `code/stats_engine.py`: Partial Mantel test implementation (controlling for climate matrix). **Dependencies**: T017 (Phylogenetic Distance Matrix), T025 (Climate Distance Matrix). **Note**: Does NOT depend on T019 (Standard Mantel result).

- [X] T028 [US2] Save climate matrix and partial test results to `data/processed/` with derivation logs. **Output**: `data/processed/climate_dist_matrix.csv`, `data/processed/partial_mantel_results.json`.

- [X] T023 [P] [US2] Integration test for Partial Mantel calculation. **Input**: `data/processed/phylo_dist_matrix.csv`, `data/processed/climate_dist_matrix.csv`. **Output**: `data/processed/partial_mantel_results.json`. **Assertion**: `assert isinstance(partial_r, float) and isinstance(p_value, float) and 0 <= p_value <= 1`. **Note**: This test runs after T026/T028 to verify the artifact generation.

- [X] T027 [US2] Implement `code/main.py`: Logic to aggregate results (Standard Mantel r vs. Partial Mantel r) and verify cluster sizes. **Constraint**: If any climate cluster has <20 species, explicitly LOG a warning regarding low power but PROCEED with the full dataset analysis. **Deliverable**: Generate `output/reports/stratified_analysis.txt` containing the specific r-value comparisons (Full vs. Stratified) required by Constitution Principle VII. **Dependency**: T025b (reads `data/processed/stratified_temp.txt`).

**Checkpoint**: At this point, User Stories 1 and 2 have code paths; T019 and T026 are the critical paths for final validation.

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate publication-quality plots and a text summary of results.

**Independent Test**: The system generates `phylo_metabolite_heatmap.png`, `mantel_results.png`, and `analysis_summary.txt` with correct data.

### Implementation for User Story 3

- [X] T030 [US3] Implement `code/viz.py`: Phylogenetic tree heatmap overlay (metabolite clusters) using `ete3` or `matplotlib`/`seaborn`. Save as `output/figures/phylo_metabolite_heatmap.png`.

- [X] T031 [US3] Implement `code/viz.py`: Scatter plot (Phylo Dist vs. Metabolite Dissimilarity) with regression line and permutation distribution histogram. Save as `output/figures/mantel_results.png`.

- [X] T029 [P] [US3] Visual regression test for heatmap output. **Tool**: `pytest-mpl` with baseline image at `tests/contract/baselines/phylo_metabolite_heatmap.png`. **Assertion**: Check file existence, minimum size (> 100KB), and pixel similarity score > 0.95 (tolerance=0.05, style='default'). **Dependency**: T030 (must run after T030 generates the baseline).

- [X] T032 [US3] Implement `code/main.py`/`code/report.py`: Text summary generator. **Dependencies**: T019 (Mantel stats), T017 (Distance Matrix), T026 (Partial Mantel results). **Logic**: Read `data/processed/mantel_results.json` and `data/processed/partial_mantel_results.json`, extract r/p-values, calculate ratio (partial r / standard r), and write to `output/reports/analysis_summary.txt`. **Deliverables**: Must include headline r, p-value, partial r, and the comparative ratio to assess robustness per SC-002.

- [X] T033 [US3] Ensure all figures meet high-resolution standards (DPI ≥ 300). **Constraint**: Must save as PNG with `dpi=300` parameter.

**Checkpoint**: All user stories have code paths; final validation pending T019/T026 completion.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034a [P] Generate `docs/README.md` with project overview, installation instructions, and usage examples.

- [X] T034b [P] Generate `docs/quickstart.md` with step-by-step guide to run the full pipeline.

- [X] T036 [P] Performance optimization: Ensure streaming logic handles large species lists within 7GB RAM limit.

- [X] T038 [P] Verify all `data/raw/` files have corresponding checksums in `state/projects/...yaml` and `data/processed/` files have derivation logs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **MVP Validation**: T037/T037a are now part of Phase 3 (US1) to ensure runtime compliance is an MVP requirement, not a polish item.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data loader patterns established in US1, but statistically independent. **Note**: T026 (Partial Mantel) requires T017 (Phylo Dist) and T025 (Climate Dist), NOT T019.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on output from US1 and US2 (results and matrices). **Note**: T032 requires T019, T017, AND T026 outputs.

### Within Each User Story

- **Tests (if included) MUST be written AFTER skeleton code exists but BEFORE full implementation**: T013a (skeleton) -> T010-T012 (tests) -> T013b (full implementation).
- **Data loading and validation (T013b, T014) MUST precede alignment (T015a, T015b)**
- **Alignment (T015b) MUST precede tree building (T016b)** (via T015a -> T015b -> T016a -> T016b flow)
- **Tree building (T016b) MUST precede distance calculation (T017)**
- **Distance calculations MUST precede statistical tests (T019, T026)**
- **Statistical tests MUST precede visualization (T030, T031)**
- **Orchestration (T020a) MUST precede statistical tests (T019)** to ensure data validity.
- **Data Hygiene (T021) MUST follow data loading (T013b, T014) immediately**.
- **Species List (T009) MUST precede Orchestration (T020a)**.

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

---

## Phase N+1: Revision & Hardening (Addressing Review Concerns)

**Purpose**: Address specific gaps identified in the analysis phase regarding data provenance, edge case handling, and verification robustness.

- [ ] T039 [P] [US1] Implement explicit species ID mapping validation in `code/data_loader.py`. **Rationale**: To prevent silent mismatches between NCBI Taxonomy IDs and KEGG organism codes which can lead to data loss. **Constraint**: Must verify 1:1 mapping for every species in `data/raw/species_list.txt` before initiating fetches; halt if any ID is ambiguous or missing in either source.

- [X] T040 [P] [US1] Add a "degenerate distribution" detection unit test in `tests/unit/test_stats_engine.py`. **Rationale**: To ensure T019 correctly handles the edge case where all permutations yield the same statistic. **Input**: Synthetic matrix with zero variance. **Assertion**: `assert warning_raised` and `p_value == 1.0` (or specific sentinel).

- [X] T041 [P] [US2] Implement a "low-power cluster" simulation test in `tests/unit/test_stats_engine.py`. **Rationale**: To verify T025b and T027 correctly log warnings and skip clusters with <20 species without crashing. **Input**: Mock climate data with one cluster of 5 species. **Assertion**: `assert warning_logged` and `result_skipped == True`.

- [ ] T042 [US1] Implement a "data retention audit" script in `scripts/audit_data.py`. **Rationale**: To provide an independent verification of SC-003 ([deferred] retention) by parsing `data/processed/` logs and comparing against `data/raw/species_list.txt`. **Output**: `output/reports/retention_audit.txt` with a PASS/FAIL status independent of the main pipeline run.

- [X] T043 [P] [US3] Implement a "figure metadata" validator in `tests/contract/test_viz.py`. **Rationale**: To ensure T033 (DPI) and T030/T031 outputs contain required EXIF/PNG metadata (e.g., DPI tag, creation timestamp) for publication readiness. **Assertion**: `assert image.info['dpi'] >= 300`.