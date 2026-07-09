# Tasks: Evolutionary Pressure on Alternative Splicing in Primates

**Input**: Design documents from `/specs/PROJ-002-001-evolutionary-pressure/`
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

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 and R 4.3 project with dependencies [UNRESOLVED-CLAIM: c_b0a1dfb9 — status=not_enough_info] (pandas, numpy, pyyaml, biopython, requests, tqdm, pybedtools, pyBigWig, scikit-learn, loguru, phylolm, ape, data.table, ggplot2)
- [ ] T003 [P] Configure linting (flake8, black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup configuration management for genome assemblies (GRCh, panTro6, rheMac10, calJac4) in `config/genomes.yaml`
- [ ] T005 [P] Implement logging infrastructure (`src/utils/logger.py`) with timestamped, multi-level logging and error code tracking
- [ ] T006 [P] Setup artifact hashing utilities (`src/utils/hash.py`) to generate SHA-256 checksums for all intermediate and final files
- [ ] T007 Create base data models for `RNASeqSample`, `SplicingEvent`, `EnrichmentResult`, and `PhylogeneticTree` in `src/data_models/`
- [ ] T008 Setup environment configuration management for CI (Sampled) vs Full (HPC) modes
- [ ] T009 [P] Implement lifecycle management retention hooks (`src/pipeline/lifecycle.py`) for configurable retention logic. (metadata recording, file age checking)
- [ ] T055 [P] Implement cron-triggered `lifecycle_manager` script (`src/pipeline/lifecycle_manager.py`) to compress FASTQs, deposit to Zenodo, record DOI in `metadata.json`, and delete local copies after a defined retention period.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Quantify lineage‑specific splicing events (Priority: P1) 🎯 MVP

**Goal**: Download RNA-seq data, align reads, compute PSI values, and identify lineage-specific splicing events with strict sample size enforcement and audit trails.

**Independent Test**: Execute the pipeline on a single sample per species (simulated for CI) and verify that a PSI table is produced, a `pipeline.log` is generated with timestamps, and that at least one splice junction is reported. The test must verify that the pipeline aborts with an error code if the input list contains an insufficient number of replicates for any species.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data download and replicate validation in `tests/contract/test_download_replicates.py`: Verify pipeline aborts with error 101 if <3 replicates and error 102 if >5 replicates [UNRESOLVED-CLAIM: c_f0b1e31e — status=not_enough_info], including informative error messages as specified in US-1 acceptance scenarios.
- [ ] T011 [P] [US1] Integration test for full alignment and PSI quantification flow in `tests/integration/test_psi_pipeline.py`: Verify PSI table is produced, `pipeline.log` contains timestamps, and at least one splice junction is reported.
- [ ] T012 [P] [US1] Unit test for alignment duration validation script (`validate_alignment_time.py`) in `tests/unit/test_align_time.py`: Verify script correctly parses duration from `pipeline.log` and asserts ≤2 hours.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement SRA download script (`src/pipeline/download.py`) to fetch FASTQs for Human (SRP010775), Chimp (SRP009050), Macaque (SRP009051), Marmoset (SRP009052)
- [ ] T014 [US1] Implement replicate count validation in `src/pipeline/download.py` to abort with error code 101 (<3 replicates) or error code 102 (>5 replicates) and log to `pipeline.log`
- [ ] T015 [P] [US1] Implement STAR alignment wrapper (`src/pipeline/align.py`) with default parameters and wall-time logging
- [ ] T016 [P] [US1] Implement SUPPA2 quantification script (`src/pipeline/quantify.py`) to generate unified PSI TSV
- [ ] T017 [US1] Implement lineage-specific event detection (`src/pipeline/detect_events.py`) applying |ΔPSI| > 0.1 and FDR < 0.05 thresholds
- [ ] T018 [US1] Implement placeholder flagging logic in `detect_events.py` to mark synthetic data results as "PLACEHOLDER" per FR-016
- [ ] T019 [P] [US1] Implement artifact hashing and manifest generation (`src/pipeline/hash_manifest.py`) and integrate into main pipeline loop to write SHA-256 hashes for all BAMs, PSI tables, TSVs, `pipeline.log`, `metadata.json`, `lifecycle_manifest.json`, and `primate_tree.nwk` directly to `pipeline.log` at every step
- [ ] T020 [P] [US1] Create validation script `validate_alignment_time.py` to benchmark alignment duration on a multi-core reference node
- [ ] T021 [P] [US1] Implement lifecycle manifest generation (`lifecycle_manifest.json`) with download timestamps and checksums

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Annotate regulatory regions surrounding splicing events (Priority: P2)

**Goal**: Extract ±500 bp flanking intronic sequences and annotate them with real phyloP conservation scores and accelerated-evolution flags.

**Independent Test**: Run the annotation module on a pre‑filtered list of splicing events and confirm that a BED file with sequence coordinates and a CSV file with actual phyloP scores and acceleration flags are generated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Contract test for flanking sequence extraction in `tests/contract/test_flank_extraction.py`
- [ ] T023 [P] [US2] Integration test for phyloP score retrieval and acceleration flagging in `tests/integration/test_phylop_annotation.py`

### Implementation for User Story 2

- [ ] T024 [P] [US2] Implement flanking sequence extraction (`src/pipeline/extract_flanks.py`) using `bedtools getfasta` for ±500 bp regions
- [ ] T025 [P] [US2] Implement phyloP score retrieval (`src/pipeline/annotate_phyloP.py`) using `pyBigWig` to query UCSC 100-way Vertebrate Conservation track
- [ ] T026 [US2] Implement logic to calculate average phyloP score (ignoring Ns) and record `NA` for assembly gaps
- [ ] T027 [US2] Implement accelerated-evolution flagging logic (TRUE if phyloP indicates significant conservation loss) in `annotate_phyloP.py`
- [ ] T028 [P] [US2] Implement sensitivity analysis script (`src/pipeline/sensitivity_analysis.py`) to sweep acceleration threshold (±0.5)
- [ ] T029 [P] [US2] Ensure exclusion of events with `NA` phyloP scores from downstream enrichment tests

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Test enrichment of splicing events in accelerated regulatory regions (Priority: P3)

**Goal**: Statistically assess enrichment of LSEs in accelerated regions using phylogenetic logistic regression, permutation testing, and FDR correction.

**Independent Test**: Run the statistical module on the annotated event table and verify that a phylogenetic logistic regression (using `phylolm::phyloglm`) is executed with `primate_tree.nwk` as the tree input, producing an enrichment p-value and odds ratio.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Contract test for phylogenetic logistic regression output schema in `tests/contract/test_enrichment_schema.py`
- [ ] T031 [P] [US3] Integration test for permutation-based null model and FDR correction in `tests/integration/test_enrichment_stats.py`
- [ ] T032 [P] [US3] Unit test for Manhattan plot validation (`validate_plot.py`) in `tests/unit/test_plot_validation.py`

### Implementation for User Story 3

- [ ] T033 [P] [US3] Implement control region generation (`src/pipeline/generate_controls.py`) to create matched non-LSE intronic regions
- [ ] T034 [US3] Implement cohort assembly (`src/pipeline/assemble_cohort.py`) merging LSEs and Controls into `regression_cohort.tsv`
- [ ] T035 [P] [US3] Implement R statistical script (`src/pipeline/stats.R`) using `phylolm::phyloglm` with LSE status as response and **mean_phyloP (continuous)** as predictor; binary `accelerated_flag` used only for descriptive statistics and sensitivity analysis
- [ ] T036 [US3] Implement permutation test (≥1,000 iterations) in `stats.R` shuffling LSE status across combined LSE+Control cohort **while preserving genomic distance (using phylogenetic independent contrasts permutation)** to avoid breaking the phylogenetic signal
- [ ] T037 [US3] Implement Benjamini-Hochberg FDR correction across the 4 lineage tests in `stats.R`
- [ ] T038 [P] [US3] Implement Manhattan plot generation (`src/pipeline/plot.py`) outputting PNG (≥1200×800 px) with chromosome labels and significance threshold line
- [ ] T039 [US3] Implement validation script `validate_plot.py` to check PNG dimensions, axis labels, and threshold line presence
- [ ] T040 [P] [US3] Implement logic to output empty result set with clear warning if no events pass FDR threshold (no silent failure)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Power Analysis & Validation (Priority: P1)

**Goal**: Validate sample size requirements and ensure pipeline logic handles edge cases correctly.

- [ ] T041 [P] Execute `power_analysis.R` to validate the minimum 3 replicates requirement for detecting |ΔPSI| ≥ 0.1
- [ ] T042 [P] Implement synthetic data generation for CI logic validation (ensuring no scientific findings are derived from synthetic data); **Note**: `validate_alignment_time.py` is a benchmark for the 8-core reference node and is NOT run on free-tier CI; CI verification uses synthetic data with relaxed timing constraints
- [ ] T043 [P] Implement integration test `test_full_pipeline.py` to verify end-to-end flow with synthetic data
- [ ] T044 [P] Verify that `primate_tree.nwk` is loaded correctly and aborts with specific error if missing or malformed

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045 [P] Documentation updates in `docs/` and `README.md`
- [ ] T046 Code cleanup and refactoring of `src/pipeline/` modules
- [ ] T047 Performance optimization for STAR alignment and SUPPA2 quantification in CI mode
- [ ] T048 [P] Additional unit tests for edge cases (assembly gaps, missing phyloP scores, empty enrichment results) in `tests/unit/`
- [ ] T049 Run quickstart.md validation to ensure all steps are executable

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Power Analysis (Phase 6)**: Depends on Foundational - can run in parallel with US1 implementation
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (LSE list)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US1 (LSE list) and US2 (Annotated regions)

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
- Power Analysis (Phase 6) can run in parallel with US1/US2 implementation

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data download and replicate validation in tests/contract/test_download_replicates.py"
Task: "Integration test for full alignment and PSI quantification flow in tests/integration/test_psi_pipeline.py"
Task: "Unit test for alignment duration validation script in tests/unit/test_align_time.py"

# Launch all models for User Story 1 together:
Task: "Implement SRA download script in src/pipeline/download.py"
Task: "Implement replicate count validation in src/pipeline/download.py"
Task: "Implement STAR alignment wrapper in src/pipeline/align.py"
Task: "Implement SUPPA2 quantification script in src/pipeline/quantify.py"
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
 - Developer B: User Story 2 (Annotation)
 - Developer C: User Story 3 (Statistics)
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
- **Critical Constraint**: All tasks must be feasible on free-tier CPU-only CI (a limited number of cores, constrained RAM, constrained disk, no GPU).. Use sampled data or pre-aligned BAMs for CI; full data for HPC.
- **Data Integrity**: Never fabricate data. Use real SRA accessions or clearly flagged synthetic data for CI logic only.
- **Reproducibility**: Every artifact must have a SHA-256 hash recorded in `pipeline.log` or `artifacts_manifest.json`.