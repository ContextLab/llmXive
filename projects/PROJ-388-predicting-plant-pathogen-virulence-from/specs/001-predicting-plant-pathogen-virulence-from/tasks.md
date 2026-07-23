# Tasks: Predicting Plant Pathogen Virulence from Publicly Available Genomic and Phenotypic Data

**Input**: Design documents from `/specs/001-predict-plant-pathogen-virulence/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create directory structure: `src/`, `tests/`, `data/raw`, `data/processed`, `output`, `src/data`, `src/analysis`, `src/viz`, `src/models`, `src/utils`
- [ ] T002 Create `.gitignore` and `src/utils/config.py` for seed pinning, path management, and environment variables
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `src/utils/logging.py` with exponential backoff logic for network retries
- [X] T006 [P] Define `src/models/isolate.py`: Class `Isolate` (fields: strain_id, species, genome_path, phenotype_score, metadata). **Note**: Phenotypic score is a field here, not a separate class.
- [X] T007 [P] Define `src/models/genomic_feature.py`: Class `GenomicFeature` (fields: feature_id, type, presence_binary, pwm_count, source)
- [ ] T008 [P] Define `src/models/species_aggregate.py`: Class `SpeciesAggregate` (fields: species_name, avg_phenotype, isolate_count, variance)
- [X] T009 [P] Setup `requirements.txt` with exact pinned versions for reproducibility (FR-010)
- [ ] T010 [P] Configure directory structure: `data/raw`, `data/processed`, `output`, `src/data`, `src/analysis`, `src/viz`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible Data Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Download specific plant pathogen genomes, extract virulence features, retrieve phenotypic scores, and merge into a clean dataset.

**Independent Test**: The pipeline can be run end-to-end on a clean environment; it must produce a single CSV/Parquet file containing aligned genomic feature vectors and phenotypic scores for at least 10 distinct isolates (or species aggregates), with all source URLs logged.

### Tests for User Story 1 ⚠️

- [X] T011 [P] [US1] Unit test for NCBI E-utilities download logic in `tests/unit/test_download.py`
- [X] T012 [P] [US1] Unit test for PHI-base phenotype fetch and fallback logic in `tests/unit/test_download.py`
- [X] T013 [P] [US1] Integration test for full download-extract-merge flow in `tests/integration/test_pipeline.py`
- [X] T014 [P] [US1] Contract test for output schema (CSV/Parquet) in `tests/contract/test_schemas.py`

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement `src/data/download.py`: Fetch *Fusarium graminearum*, *Pseudomonas syringae*, *Xanthomonas* spp. genomes via `biopython` E-utilities with retry logic (FR-001)
- [X] T016 [P] [US1] Implement `src/data/download.py`: Retrieve phenotypic disease severity scores from PHI-base or literature tables; implement species-level aggregation fallback (FR-001, FR-009)
- [ ] T017 [P] [US1] Implement `src/data/extract.py`: Run `hmmsearch` against PHI-base/Pfam libraries to generate binary virulence gene presence/absence matrix (FR-002)
- [ ] T018 [P] [US1] Implement `src/data/extract.py`: Count transcription factor binding sites using Position Weight Matrices (PWMs) (FR-002)
- [ ] T019 [US1] Implement `src/data/merge.py`: Align genomic features with phenotypic scores by isolate/species ID; handle missing phenotypes by dropping rows and logging counts (FR-006)
- [ ] T020 [US1] Implement fallback logic in `src/data/merge.py`: If <50% isolate linkage, aggregate by species and flag analysis type (FR-009)
- [ ] T021 [US1] Implement `src/data/merge.py`: Output final analysis-ready dataset (CSV/Parquet) to `data/processed/merged_dataset.parquet` and summary report (processed count, missing count) (FR-001, FR-006)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Association Analysis (Priority: P2)

**Goal**: Compute PGLS correlations, apply Permutation-based FDR, and identify significant genomic-virulence associations.

**Independent Test**: The analysis script runs on the P1 output dataset and produces a ranked list of genomic features with correlation coefficients, p-values, and adjusted p-values, identifying a set of top candidates.

### Tests for User Story 2 ⚠️

- [X] T022 [P] [US2] Unit test for housekeeping gene extraction and tree construction in `tests/unit/test_phylogeny.py`
- [X] T023 [P] [US2] Unit test for PGLS calculation and Permutation FDR in `tests/unit/test_correlation.py`
- [X] T024 [P] [US2] Unit test for Benjamini-Yekutieli sensitivity check in `tests/unit/test_correlation.py`
- [X] T025 [P] [US2] Integration test for full analysis pipeline (Tree -> PGLS -> FDR) in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [ ] T026 [US2] Implement `src/analysis/phylogeny.py`: **Extract** core housekeeping genes (rpoB, gyrB, 16S) from the downloaded genome assemblies (`data/raw/*.fna`) using `biopython` or `prodigal` (if annotation needed). **Input**: `data/raw/*.fna` from T015. (FR-003)
- [ ] T027 [US2] Implement `src/analysis/phylogeny.py`: **Construct** phylogenetic tree using the extracted housekeeping gene sequences via Maximum Likelihood (IQ-TREE or RAxML). Validate tree (rooted, branch lengths) and generate phylogenetic covariance matrix. **Output**: `data/processed/tree.newick` and `data/processed/phylo_covariance_matrix.npy`. (FR-003)
- [ ] T028 [US2] Implement `src/analysis/correlation.py`: Compute **Phylogenetic Generalized Least Squares (PGLS)** correlation coefficients between every genomic feature and disease severity score. **Primary Method**: PGLS (FR-004). **Input**: `data/processed/merged_dataset.parquet` from T021 and `data/processed/tree.newick` from T027.
- [ ] T029 [US2] Implement `src/analysis/correlation.py`: Apply **Permutation-based FDR** correction to raw p-values derived from the PGLS tests. **Primary Method**: Permutation-based FDR (FR-005). Perform Benjamini-Yekutieli (BY) as a sensitivity check only.
- [ ] T030 [US2] Implement `src/analysis/correlation.py`: Filter results for visualization (|ρ| ≥ 0.5) while retaining all significant features (FDR < 0.05) in raw output (FR-007)
- [ ] T031 [US2] Implement `src/analysis/correlation.py`: Handle edge case N < 10 by **skipping statistical testing** and generating a **Descriptive Case Study** report (no p-values) as mandated by FR-009. Do not run PGLS if N < 10. (FR-009)
- [ ] T032 [US2] Output ranked table of features with coefficients, p-values, and adjusted p-values to `data/processed/results.csv`. If N < 10, include a 'low_power' flag and descriptive summary in metadata (FR-004, FR-005).
- [ ] T033 [US2] Implement metric calculation: Calculate and report **Success Rate (SC-001)** and **Proportion of Significant Features (SC-004)** in the final summary report. (SC-001, SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reproducibility Reporting (Priority: P3)

**Goal**: Generate a heatmap of top associations and a self-contained Jupyter notebook documenting the workflow.

**Independent Test**: The pipeline generates a PNG heatmap of the top significant features and a `.ipynb` file that, when opened, renders the analysis steps and plots without requiring additional configuration.

### Tests for User Story 3 ⚠️

- [ ] T034 [P] [US3] Unit test for heatmap generation and filtering in `tests/unit/test_viz.py`
- [ ] T035 [P] [US3] Integration test for notebook execution and numerical equivalence in `tests/integration/test_reproducibility.py`

### Implementation for User Story 3

- [ ] T036 [US3] Implement `src/analysis/viz.py`: Generate seaborn heatmap of top significant features (|ρ| ≥ 0.5) against disease severity. **Dependency**: Requires output from T032 (results.csv). (FR-008)
- [ ] T037 [US3] Implement `src/analysis/viz.py`: Save static heatmap PNG to `output/` (FR-008)
- [ ] T038 [US3] Implement `src/main.py` (orchestrator): Compile Jupyter notebook `output/reproducibility_notebook.ipynb` containing all code, data URLs, and parameters (FR-008)
- [ ] T039 [US3] Implement `src/main.py`: Ensure notebook cells execute successfully on a clean CPU environment with numerical equivalence (tolerance=1e-6) (SC-003)
- [ ] T040 [US3] Add runtime monitoring logic to log peak memory usage and total runtime. **Enforcement**: Must raise a `RuntimeError` if memory > 7GB or runtime > 6h (SC-005).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Update `README.md` with usage examples and dependency list
- [ ] T042 [P] Update `docs/api.md` with function signatures and module descriptions
- [ ] T043 [P] Run `quickstart.md` validation and ensure all links work
- [ ] T044 [P] Run `ruff --fix` and `black` to ensure code style compliance
- [ ] T045 [P] Reduce cyclomatic complexity of `src/analysis/correlation.py` to < 10
- [ ] T046 [P] Optimize `src/data/download.py` to use streaming for large downloads to reduce peak RAM
- [ ] T047 [P] Add memory profiling hooks to `src/main.py` to verify 7GB limit during execution
- [ ] T048 [P] Add unit tests for specific edge cases: `test_download_handles_404`, `test_extract_handles_empty_genome` in `tests/unit/`
- [ ] T049 [P] Add unit tests for missing data handling: `test_merge_handles_missing_phenotype` in `tests/unit/`
- [ ] T050 [P] Verify `requirements.txt` pins and add comments for external binary dependencies (`hmmsearch`)
- [ ] T051 [P] [US1] Add explicit URL validation and "fail loudly" logic to `src/data/download.py` ensuring no synthetic fallbacks are ever triggered (Constitution Data Hygiene)
- [ ] T052 [P] [US2] Add unit test for `test_correlation_handles_collinear_features` to verify FDR robustness under high collinearity (Plan: Power & Limitation Disclosure)
- [ ] T053 [P] [US3] Add documentation to `output/reproducibility_notebook.ipynb` explicitly stating the sample size limitation and the "low_power" flag logic if N < 10 (Plan: Power & Limitation Disclosure)

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
- **Constitution Compliance**: **PGLS** is the mandatory primary statistical method (FR-004). **Permutation-based FDR** is the mandatory primary correction method (FR-005). PGLS and Permutation FDR must be implemented as primary; BY and sensitivity checks are secondary.
- **Revision Note**: Updated T026-T033 to enforce PGLS and Permutation FDR as primary methods per FR-004/FR-005. Updated T031 to enforce non-statistical fallback for N<10 per FR-009. Split T006 into T006-T008 for granularity. Added T033 for metric reporting (SC-001, SC-004).