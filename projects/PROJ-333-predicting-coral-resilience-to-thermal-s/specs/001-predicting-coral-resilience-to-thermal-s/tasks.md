# Tasks: Predicting Coral Resilience to Thermal Stress Using Publicly Available Genomic Data

**Input**: Design documents from `/specs/001-coral-resilience-prediction/`
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

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/raw`, `data/processed`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies (`biopython`, `pysam`, `scipy`, `pandas`, `matplotlib`, `gprofiler-official`, `pydeseq2`, `gseapy`) in `requirements.txt`
- [ ] T003 [P] Configure linting (flake8/pylint) and formatting (black/isort) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `src/config.py` defining all project constants: paths (`data/raw`, `data/processed`), NCBI BioProject ID (PRJNA292777), RAM thresholds (sufficient memory capacity), and `MIN_SAMPLES_FOR_FILTER = 3`
- [ ] T005 [P] Implement logging infrastructure in `src/utils/logging.py` to track memory usage (RSS) and execution time
- [ ] T006 [P] Create base data model schema definition `src/models/expression.py` (ExpressionMatrix class definition only, no instances)
- [ ] T007 [P] Create base data model schema definition `src/models/phenotype.py` (PhenotypeRecord class definition only, no instances)
- [ ] T008 [P] Create base data model schema definition `src/models/dge.py` (DGEResult class definition only, no instances)
- [ ] T009 [P] Create error handling utilities in `src/utils/errors.py` (specifically for NCBI timeout retries and checksum mismatches)
- [ ] T009b [P] Document justification for filtering thresholds (`counts > 10`, `MIN_SAMPLES_FOR_FILTER = 3`) in `data/processed/data-model.md` to satisfy Constitution Principle VII (deviation documentation)
- [ ] T011 [P] Create integration test scaffolding in `tests/integration/` using mock small FASTQ files to verify pipeline flow without downloading real data

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - RNA-seq Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download raw FASTQ reads from NCBI BioProject [Accession Number], map to reference transcriptome, and quantify gene expression while ensuring peak memory < 7 GB.

**Independent Test**: Can be fully tested by running the download and quantification script on a local machine or CI runner and verifying that peak memory usage (RSS) remains < 7 GB and that the output expression matrix contains only samples with valid treatment metadata.

### Tests for User Story 1 (TDD Workflow - MUST BE WRITTEN FIRST) ⚠️

> **NOTE**: These tasks MUST be completed and the tests must FAIL before T015-T021 implementation begins (TDD workflow).

- [ ] T012 [US1] Unit test: Add `tests/unit/test_ingest.py::test_sha256_verification_passes_on_valid_file` and `test_sha256_verification_fails_on_corrupted_file`
- [ ] T013 [US1] Unit test: Add `tests/unit/test_ingest.py::test_metadata_parsing_excludes_missing_treatment` and verifies warning log
- [ ] T014 [US1] Integration test: Add `tests/integration/test_memory.py::test_quantification_memory_stays_under_7GB` on a small sample subset

### Implementation for User Story 1

- [ ] T015 [US1] [DEPENDS: T014] Implement `src/ingest.py`: Download FASTQ files from NCBI SRA/ENA for project PRJNA292777 with exponential backoff retry logic (max 3 retries); save to `data/raw/PRJNA292777/*.fastq.gz` and log status to `data/raw/download_log.json`
- [ ] T016 [US1] [DEPENDS: T015] Implement `src/ingest.py`: Generate SHA256 checksums for downloaded files, store in `data/raw/checksums.json`, and verify integrity; **fail immediately** if mismatch to prevent T017 execution
- [ ] T017 [US1] [DEPENDS: T016] Implement `src/ingest.py`: Parse phenotype metadata, map sample IDs to treatment conditions (Heat vs. Control), and exclude samples with missing treatment status (logging warnings); only process files verified in T016
- [ ] T018 [US1] Implement `src/reference.py`: Download and index *Acropora millepora* reference transcriptome (NCBI RefSeq GCF_000163615.2)
- [ ] T019 [US1] [DEPENDS: T018] Implement `src/quant.py`: Stream FASTQ files against reference index using Salmon (CPU mode) with command `salmon quant -i <index_path> -l A -r <fastq_path> -o <output_dir> --validateMappings`; generate count matrix to `data/processed/quant.sf`; enforce memory-mapped processing to stay under 7 GB RAM
- [ ] T020 [US1] [DEPENDS: T019, T009b] Implement `src/quant.py`: Filter expression matrix (counts > 10 in >= `config.MIN_SAMPLES_FOR_FILTER` samples) as documented in `data-model.md` (T009b) to ensure dataset size fits CI constraints (FR-002)
- [ ] T021 [US1] Add validation step to verify output expression matrix contains only valid samples and log total file size

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (valid count matrix generated within memory limits)

---

## Phase 4: User Story 2 - Differential Gene Expression Analysis (Priority: P2)

**Goal**: Run differential gene expression (DGE) analysis using `pydeseq2` to identify genes significantly upregulated/downregulated under thermal stress, ensuring results are associational and FDR-corrected.

**Independent Test**: Can be fully tested by executing the DESeq2 pipeline with the quantified data and verifying that a results table is generated containing log2-fold changes and adjusted p-values for all tested genes.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Unit test: Add `tests/unit/test_dge.py::test_fdr_calculation_benjamini_hochberg`
- [ ] T023 [P] [US2] Integration test: Add `tests/integration/test_dge.py::test_output_format_contains_log2fc_pvalue_fdr`

### Implementation for User Story 2

- [ ] T024 [US2] Implement `src/dge.py`: Load count matrix and phenotype data; construct design formula `~ treatment`
- [ ] T025 [US2] Implement `src/dge.py`: Run `pydeseq2` Differential Expression analysis with empirical Bayes dispersion shrinkage
- [ ] T026 [US2] Implement `src/dge.py`: Apply Benjamini-Hochberg correction to p-values to generate FDR column
- [ ] T027 [US2] Implement `src/dge.py`: Annotate output results table with metadata header stating "Associational Study - No Causal Claims"
- [ ] T028a [US2] [DEPENDS: T027] Calculate 'expected count under the null' via 1000 permutations (random seed 42) and compare to observed count of significant genes (FDR < 0.05) to satisfy SC-002; append result to `data/processed/validation_report.md`
- [ ] T028 [US2] [DEPENDS: T028a] Validate FDR distribution: Generate histogram of FDR values saved to `data/processed/fdr_distribution.png` and append status to `data/processed/validation_report.md` against threshold FDR <= 0.05
- [ ] T029 [US2] Save DGE results to `data/processed/dge_results.csv` ensuring all genes have log2FC, p-value, FDR, and the permutation comparison result from T028a

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (valid DGE results generated with correct statistical corrections)

---

## Phase 5: User Story 3 - Pathway Enrichment and Visualization (Priority: P3)

**Goal**: Visualize differentially expressed genes via volcano plot and perform pathway enrichment analysis (g:Profiler/gseapy) to identify heat-shock or oxidative stress pathways.

**Independent Test**: Can be fully tested by running the enrichment script on the top significant genes and verifying that a volcano plot image and an enrichment report (listing pathways) are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test: Add `tests/unit/test_viz.py::test_volcano_plot_generation_saves_png`
- [ ] T031 [P] [US3] Unit test: Add `tests/unit/test_enrich.py::test_enrichment_report_parsing_hsp_oxidative`

### Implementation for User Story 3

- [ ] T032 [US3] [DEPENDS: T029] Implement `src/viz.py`: Generate Volcano Plot (log2FC vs -log10 p-value) for genes with FDR < 0.05 (from T029); save as `data/processed/volcano_plot.png`
- [ ] T033 [US3] [DEPENDS: T029] Implement `src/enrichment.py`: Rank genes by statistic and run Gene Set Enrichment Analysis (GSEA) using `gseapy` against curated gene sets (HSP, Oxidative Stress); note: this is complementary to the primary ORA/API requirement
- [ ] T034 [US3] [DEPENDS: T029] Implement `src/enrichment.py`: Query g:Profiler API for pathway enrichment of top significant genes (FDR < 0.05) from T029
- [ ] T034b [US3] [DEPENDS: T034] Verify the g:Profiler query result contains 'HSP' or 'Oxidative Stress' gene sets; if absent, log a fallback to broader 'stress_response' categories and record the specific gene sets used for SC-003 validation
- [ ] T035 [US3] [DEPENDS: T034b] Implement `src/enrichment.py`: Generate `data/processed/enrichment_report.md` using g:Profiler results (T034/T034b) as the primary source for the pathway enrichment report (FR-005), listing pathways, p-values, and FDR
- [ ] T036 [US3] [DEPENDS: T035] Validate biological plausibility: Append a "Biological Plausibility" section to `data/processed/enrichment_report.md` containing the specific p-value/FDR for HSP/Oxidative pathways (from T034b) and a "PASS/FAIL" verdict against the FDR < 0.1 threshold (SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates: Update `README.md` with execution instructions and data source citations
- [ ] T038 Code cleanup and refactoring (remove unused imports, optimize memory usage in `quant.py`)
- [ ] T039 Performance optimization: Verify streaming logic in `quant.py` prevents memory spikes on full dataset
- [ ] T040 [P] Add unit tests for configuration loading and path resolution in `tests/unit/test_config.py`
- [ ] T041 Run `quickstart.md` validation to ensure full pipeline execution time is < 6 hours on free-tier runner
- [ ] T042 Verify all artifacts (plots, reports) are deterministic by re-running with fixed random seeds

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (count matrix from T021)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US2 (DGE results from T029)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (TDD)
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T005, T009, T011) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together (T006, T007, T008 from Phase 2):
Task: "Create base data model schema definition src/models/expression.py (T006)"
Task: "Create base data model schema definition src/models/phenotype.py (T007)"
Task: "Create base data model schema definition src/models/dge.py (T008)"

# Note: These models define the schema, but the data instances are produced by US1 tasks (T015-T021).
# US2 (DGE) cannot process data until US1 (T021) completes production.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ingest & Quantify)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify memory < 7GB, valid matrix generated)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (DGE results)
4. Add User Story 3 → Test independently → Deploy/Demo (Visuals & Enrichment)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data Ingest/Quant)
   - Developer B: User Story 2 (DGE Analysis) - *Note: Can start code structure, but data dependency means US1 must finish first for full run*
   - Developer C: User Story 3 (Viz/Enrich) - *Note: Requires US2 output*
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
- **Critical Constraint**: All tasks must respect the constrained RAM limit and runtime on CPU-only runners.. No GPU or 8-bit quantization allowed.