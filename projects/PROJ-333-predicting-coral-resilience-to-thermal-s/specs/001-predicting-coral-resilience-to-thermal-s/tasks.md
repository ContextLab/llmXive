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

- **Single project**: `code/`, `tests/` at repository root (Aligned with Plan.md Project Structure)
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

- [ ] T001a [P] Create project directory structure: `code/`, `tests/`, `data/raw`, `data/processed`, `results/plots`, `specs/001-coral-resilience-prediction/`
- [ ] T001b [P] Create `.gitignore` file excluding `data/raw/*.fastq.gz`, `data/processed/*.rds`, `__pycache__`, `*.pyc`
- [X] T002 Initialize Python project with pinned dependencies (`biopython`, `pysam`, `scipy`, `pandas`, `matplotlib`, `gprofiler-official`, `rpy2`) in `requirements.txt`
- [ ] T003a [P] Create `.flake8` configuration file with `max-line-length=88` and `ignore=E203,W503`
- [ ] T003b [P] Create `pypyproject.toml` configuration for `black` (line length 88) and `isort`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. This phase includes all static external data acquisition and verification.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` defining all project constants: paths (`data/raw`, `data/processed`), NCBI BioProject ID, RAM thresholds (`MAX_RAM_GB = 7`), and `MIN_SAMPLES_FOR_FILTER`.
 - **MUST set `MIN_COUNT_THRESHOLD = 10`** as a provisional value to satisfy Constitution Check VII (Uniform Filtering).
 - **MUST include a code comment** referencing the provisional nature: `# MIN_COUNT_THRESHOLD=10 is provisional per T009b. Research phase may update this value.`
 - **MUST include a code comment** referencing the formal amendment: `# BioProject ID updated via T004b (Spec Amendment). Original PRJNA superseded.`
- [ ] T004b [P] **Formal Spec Amendment Record**: Create `specs/001-coral-resilience-prediction/amendments.md` (or update existing) to document the change from PRJNA292777 to PRJNA321023.
 - **MUST create a formal amendment record** with ID `AMEND-001`, date, and description: "Updated BioProject ID to the current accession number. per Plan.md".
 - **MUST NOT** modify `spec.md` directly in this task; `spec.md` is frozen. The record documents the required change for implementation.
 - **Output**: `specs/001-coral-resilience-prediction/amendments.md`.
 - **Content Structure**: Include "Decision Process", "Impact on Success Criteria", and "Final Value Determination Date" sections.
 - **Example Content**: "Decision Process: Review literature for Acropora millepora expression variance. Impact: Lower threshold may increase false positives; higher may miss weak signals."
- [ ] T004c [P] [DEPENDS: T004b] **Update Configuration**: Update `code/config.py` to set `BIOPROJECT_ID = "PRJNA321023"` explicitly, ensuring the code uses the correct ID referenced in T004b.
- [X] T005 [P] Implement logging infrastructure in `code/utils/logging.py` to track memory usage (RSS) and execution time
- [X] T006 [P] Create base data model schema definition `code/models/expression.py` (ExpressionMatrix class definition only, no instances)
- [X] T007 [P] Create base data model schema definition `code/models/phenotype.py` (PhenotypeRecord class definition only, no instances)
- [X] T008 [P] Create base data model schema definition `code/models/dge.py` (DGEResult class definition only, no instances)
- [X] T009 [P] Create error handling utilities in `code/utils/errors.py` (specifically for NCBI timeout retries and checksum mismatches)
- [ ] T009b [P] Document the **strategy for deferring empirical filtering thresholds** in `data/processed/deferred_thresholds_strategy.md`.
 - **MUST use exact file path**: `data/processed/deferred_thresholds_strategy.md`.
 - **MUST include sections**: "Decision Process" (how thresholds are chosen), "Impact on Success Criteria" (SC-002, SC-003), "Final Value Determination Date".
 - **MUST state** that the final numeric values will be determined during the research phase and recorded in `config.py` before T020 runs.
 - **MUST align the "Final Value Determination Date"** with the metric generation phase in Task T028c.
 - **MUST include example content structure**: e.g., "Decision Process: Review literature for Acropora millepora expression variance. Impact: Lower threshold may increase false positives; higher may miss weak signals."
- [ ] T011 [P] Create integration test scaffolding in `tests/integration/` using mock small FASTQ files to verify pipeline flow without downloading real data.
 - **MUST generate mock FASTQ files** (e.g., `mock_sample_1.fastq.gz`, `mock_sample_2.fastq.gz`) with realistic headers and random sequences as part of this task's deliverable.
 - **Output**: `tests/integration/data/mock_fastq/` containing mock files.
- [ ] T018 [US1] **Download and Verify Reference Transcriptome**: Download *Acropora millepora* reference transcriptome (NCBI RefSeq) to `data/raw/reference/`.
 - **MUST fetch the official SHA256 checksum** from the NCBI RefSeq FTP manifest for assembly GCF_ using the URL: ` (or use a pre-validated hash from `research.md` if available).
 - **MUST verify that assembly GCF_000163615.2 belongs to BioProject PRJNA** before proceeding.
 - **MUST verify** the downloaded file against the checksum.
 - **MUST fail immediately** if the checksum does not match (external verification).
 - **MUST index** the verified reference for Salmon using `salmon index`.
 - **Output**: `data/raw/reference/index/` and `data/raw/reference/checksum.json`.
 - **Note**: T018 is resource-intensive; it MUST run AFTER T015 to prevent resource contention on the runner.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - RNA-seq Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download raw FASTQ reads from NCBI BioProject PRJNA321023 (per T004b/T004c), map to reference transcriptome, and quantify gene expression while ensuring peak memory < 7 GB.

**Independent Test**: Can be fully tested by running the download and quantification script on a local machine or CI runner and verifying that peak memory usage (RSS) remains < 7 GB and that the output expression matrix contains only samples with valid treatment metadata.

### Tests for User Story 1 (TDD Workflow - MUST BE WRITTEN FIRST) ⚠️

> **NOTE**: These tasks MUST be completed and the tests must FAIL before T015-T021 implementation begins (TDD workflow).

- [X] T012 [P] [US1] Unit test: Add `tests/unit/test_ingest.py::test_sha256_verification_passes_on_valid_file` and `test_sha256_verification_fails_on_corrupted_file` [DEPENDS: T004]
- [X] T013 [P] [US1] Unit test: Add `tests/unit/test_ingest.py::test_metadata_parsing_excludes_missing_treatment` and verifies warning log [DEPENDS: T004]
- [ ] T014 [P] [US1] Integration test: Add `tests/integration/test_memory.py::test_quantification_memory_stays_under_7GB` on a small sample subset [DEPENDS: T011]
 - **MUST use mock data generated by T011** to ensure the test is self-contained.

### Implementation for User Story 1

- [ ] T015 [US1] Implement `code/ingest.py`: Download FASTQ files from NCBI SRA using `fasterq-dump` (SRA Toolkit) for project **PRJNA321023** (per T004c) with `--split-files --gzip` and exponential backoff retry logic with a bounded maximum number of retries; save to `data/raw/PRJNA321023/*.fastq.gz` and log status to `data/raw/download_log.json`
- [ ] T016 [US1] [DEPENDS: T015] Implement `code/ingest.py`: Generate SHA256 checksums for downloaded files, fetch the **canonical reference hash** from the NCBI manifest (as per T018 logic), and compare against it; **fail immediately** if mismatch to prevent T017 execution.
 - **MUST NOT** just verify self-consistency; must verify against external source.
 - **Output**: `data/raw/checksums.json` (with reference hash and computed hash).
- [ ] T017 [US1] [DEPENDS: T016] Implement `code/ingest.py`: Parse phenotype metadata, map sample IDs to treatment conditions (Heat vs. Control), and exclude samples with missing treatment status (logging warnings); only process files verified in T016
- [ ] T019 [US1] [DEPENDS: T016, T018] Implement `code/quant.py`: Stream FASTQ files against reference index (from T018) using Salmon (CPU mode) with command `salmon quant -i <index_path> -l A -r <fastq_path> -o <output_dir> --validateMappings --memGb <allocated_memory>`; generate individual `quant.sf` files to `data/processed/quant/<sample_id>/`; enforce memory-mapped processing to stay within available system RAM limits.
- [ ] T019b [US1] [DEPENDS: T019] Implement `code/quant.py`: Aggregate individual `quant.sf` files into a single count matrix (`data/processed/count_matrix.csv`) required for downstream filtering and DGE analysis
- [ ] T020 [US1] [DEPENDS: T019b] Implement `code/quant.py`: Filter expression matrix using `config.MIN_COUNT_THRESHOLD` (provisional value 10 from T004) in >= `config.MIN_SAMPLES_FOR_FILTER` samples.
 - **MUST use the provisional config value** defined in T004.
 - Document the applied filter in `data/processed/filter_log.md`.
- [ ] T021 [US1] Add validation step to verify output expression matrix contains only valid samples and log total file size

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (valid count matrix generated within memory limits)

---

## Phase 4: User Story 2 - Differential Gene Expression Analysis (Priority: P2)

**Goal**: Run differential gene expression (DGE) analysis using native R DESeq2 to identify genes significantly upregulated/downregulated under thermal stress, ensuring results are associational and FDR-corrected.

**Independent Test**: Can be fully tested by executing the DESeq2 pipeline with the quantified data and verifying that a results table is generated containing log2-fold changes and adjusted p-values for all tested genes.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Unit test: Add `tests/unit/test_dge.py::test_fdr_calculation_benjamini_hochberg`
- [ ] T023 [P] [US2] Integration test: Add `tests/integration/test_dge.py::test_output_format_contains_log2fc_pvalue_fdr`

### Implementation for User Story 2

- [ ] T023b [US2] [DEPENDS: T019b] **Batch Effect Detection & Design Logic**: Implement `code/batch_detection.R` to:
 - Load count matrix from `data/processed/count_matrix.csv` (T019b).
 - Perform **internal VST** (variance stabilizing transformation) on the count matrix to determine design.
 - Perform `prcomp` on the variance-stabilized data.
 - Check if the first principal component (PC1) correlates strongly (r > 0.7) with sequencing lane or date (if inferable).
 - If batch metadata exists: Set design formula `~ batch + condition`.
 - If no batch metadata but PC1 correlates with a hidden factor: Set design `~ condition` and log "Potential Batch Confounding".
 - If no batch metadata and no correlation: Set design `~ condition`.
 - **Output**: A JSON file `data/processed/dge_design_config.json` containing the selected formula and the batch detection rationale.
 - **MUST save** the selected formula to be consumed by T024.
 - **MUST log** the specific rationale and correlation value (r) in `data/processed/batch_detection_log.md`.
- [ ] T024 [US2] [DEPENDS: T023b] Implement `code/dge_analysis.R`: Load count matrix (`data/processed/count_matrix.csv`), phenotype data, and the dynamic design formula from `data/processed/dge_design_config.json` (T023b). Construct the DESeq2 design using the formula determined by T023b.
- [ ] T025 [US2] Implement `code/dge_analysis.R`: Run native R DESeq2 Differential Expression analysis with empirical Bayes dispersion shrinkage. Save the `dds` object to `data/processed/dds.rds`.
- [ ] T026 [US2] Implement `code/dge_analysis.R`: Apply Benjamini-Hochberg correction to p-values to generate FDR column. Save results to `data/processed/dge_results.csv`.
- [ ] T027 [US2] Implement `code/dge_analysis.R`: Annotate output results table with metadata header stating "Associational Study - No Causal Claims". **Ensure this label is propagated to the final `results/report.md` and `enrichment_report.md`**.
- [ ] T028a [US2] [DEPENDS: T025] **Calculate Null Expectation**: Load `dds` object from T025. Use DESeq2's `results(dds, independentFiltering=TRUE)` to obtain the summary of the null model. Calculate the theoretical expected count of significant genes under the null hypothesis: `expected_count = total_genes * significance_threshold`. Save this value to `data/processed/null_expectation.json` (single float value).
- [ ] T028b [US2] [DEPENDS: T026, T028a, T028c] **Validate Statistical Rigor**: Read observed significant count from `dge_results.csv` (T026) and expected count from `null_expectation.json` (T028a). **Read the specific metric values from `sc002_metrics.json` (T028c)**.
 - **MUST check** if `observed > expected` AND `p < 0.05` (for the comparison test).
 - Generate histogram of raw p-values saved to `data/processed/pvalue_distribution.png`.
 - **MUST append the specific 'observed' and 'expected' values** and the validation status (PASS/FAIL based on observed > expected AND p < 0.05) to `data/processed/validation_report.md`.
- [ ] T028c [US2] [DEPENDS: T026, T028a] **Record Success Criteria Metrics**: Generate `data/processed/sc002_metrics.json` containing:
 - `observed_significant_count` (float)
 - `expected_significant_count` (float)
 - `comparison_result` (string: "PASS" or "FAIL")
 - **MUST output** these specific values as evidence for SC-002.
- [ ] T028d [US2] [DEPENDS: T026] **Assert FDR Threshold**: Calculate the final False Discovery Rate (FDR) of the reported significant hits (FDR <= 0.05).
 - **MUST assert** that the proportion of genes with FDR > 0.05 is within acceptable limits.
 - **MUST generate** `data/processed/fdr_assertion.json` containing the calculated FDR rate and a "PASS" or "FAIL" status against the 0.05 threshold.
 - **MUST fail** the pipeline if FDR > 0.05 (SC-005).
- [ ] T029 [US2] Save final DGE results to `data/processed/dge_results.csv` ensuring all genes have log2FC, p-value, FDR, and the theoretical comparison result from T028b

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (valid DGE results generated with correct statistical corrections)

---

## Phase 5: User Story 3 - Pathway Enrichment and Visualization (Priority: P3)

**Goal**: Visualize differentially expressed genes via volcano plot and perform pathway enrichment analysis (g:Profiler) to identify heat-shock or oxidative stress pathways.

**Independent Test**: Can be fully tested by running the enrichment script on the top significant genes and verifying that a volcano plot image and an enrichment report (listing pathways) are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test: Add `tests/unit/test_viz.py::test_volcano_plot_generation_saves_png`
- [ ] T031 [P] [US3] Unit test: Add `tests/unit/test_enrich.py::test_enrichment_report_parsing_hsp_oxidative`

### Implementation for User Story 3

- [ ] T032 [US3] [DEPENDS: T029] Implement `code/viz.py`: Generate Volcano Plot (log2FC vs -log10 p-value) for genes with FDR < 0.05 (from T029); save as `data/processed/volcano_plot.png`
- [ ] T033 [US3] [DEPENDS: T029] **Gene ID Mapping**: Implement `code/gene_mapping.py` to convert gene IDs from `dge_results.csv` (T029) to the format required by g:Profiler (e.g., Ensembl IDs or Gene Symbols) using `biomaRt` or a local mapping file. Save the mapped list to `data/processed/mapped_gene_ids.txt`.
- [ ] T034 [US3] [DEPENDS: T033] Implement `code/enrichment.py`: Query g:Profiler API (`https://biit.cs.ut.ee/gprofiler/gost`) using the mapped gene IDs from T033 and the predefined list [HSP, Oxidative Stress] as `sources`. Save raw results to `data/processed/enrichment_raw.json`.
 - **MUST use** the specific query parameters: `query`, `organism=ammi` (or appropriate code), `sources=["GO:BP", "KEGG", "Reactome"]`.
- [ ] T035 [US3] [DEPENDS: T034] Implement `code/enrichment.py`: Generate `data/processed/enrichment_report.md` using g:Profiler results (T034).
 - **MUST include** the list of pathways, p-values, and FDR.
 - **MUST include** a "Statistical Significance Summary" section stating whether enrichment for HSP or Oxidative Stress pathways is statistically significant (FDR < 0.05) based on the results.
 - **MUST state** "No enrichment found for predefined pathways" if the query returned no matches.
 - **MUST ensure** the "Statistical Significance Summary" section is present even if no pathways are found (to allow T036 to parse it).
 - **MUST inherit the "Associational Study" disclaimer** from T027 and T035c.
- [ ] T035c [US3] [DEPENDS: T035, T027] **Generate Final Report**: Create `results/report.md` (if it exists, update; otherwise create).
 - **MUST inherit** the "Associational Study" disclaimer from T027 (dge_results.csv) and T035 (enrichment_report.md).
 - **MUST include** a summary of the DGE results, Enrichment findings, and the final validation status.
 - **MUST explicitly state** "Observational Study - No Causal Claims" in the header.
- [ ] T036 [US3] [DEPENDS: T035] **Validate Biological Plausibility**: Parse `enrichment_report.md` (T035).
 - **MUST first verify that the Statistical Significance Summary section exists** before parsing.
 - If specific p-values/FDRs for HSP or Oxidative Stress pathways are present, compare against FDR < 0.1 threshold (SC-003).
 - **Success Criterion**: PASS if **at least one** pathway from [HSP, Oxidative] has FDR < 0.1.
 - **Failure Verdict Format**: If neither pathway is enriched, append the string `"Biological Plausibility: FAIL (No predefined pathways enriched at FDR < 0.1)"` to the report.
 - Record FDR=1.0 for missing pathways.
 - Append the "Biological Plausibility" verdict to `data/processed/enrichment_report.md`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates: Update `README.md` with execution instructions and data source citations
- [ ] T038 Code cleanup and refactoring (remove unused imports, optimize memory usage in `code/quant.py`)
- [ ] T039 Performance optimization: Verify streaming logic in `code/quant.py` prevents memory spikes on full dataset
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
- All Foundational tasks marked [P] (T005, T009, T011, T018) can run in parallel (with caution on T018 resource usage)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together (T006, T007, T008 from Phase 2):
Task: "Create base data model schema definition code/models/expression.py (T006)"
Task: "Create base data model schema definition code/models/phenotype.py (T007)"
Task: "Create base data model schema definition code/models/dge.py (T008)"

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
- **Critical Constraint**: All tasks must respect the constrained RAM limit and runtime on CPU-only runners. No GPU or 8-bit quantization allowed.
- **Data Integrity**: All tasks must use real data from the specified NCBI BioProject (PRJNA321023, per T004b/T004c). No synthetic data generation is permitted.
- **Deferral of Empirics**: Thresholds (counts, samples) are deferred to the research phase and must not be hardcoded as final values in implementation tasks, but a provisional value (10) is used for execution (T004).