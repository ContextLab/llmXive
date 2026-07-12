# Tasks: Systematic Assessment of Non-Coding Variant Effects on Transcription Factor Binding Affinities

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `data/raw/`, `data/derived/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with dependencies (`pandas`, `numpy`, `biopython`, `scikit-learn`, `pybedtools`, `pyfaidx`, `requests`, `pytest`) in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`
- [ ] T004 [P] Create `.gitignore` excluding `data/raw/*` (except checksums), `data/derived/*`, `__pycache__`, and `.env`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create `code/config.py` defining paths, random seeds, MAF threshold (a low-frequency cutoff), and `DEFAULT_WINDOW` (optional fallback for error cases). **CRITICAL**: The scoring engine MUST derive the window size dynamically from the loaded PWM length for each TF, NOT from this config constant. This config key is for documentation/fallback only.
- [ ] T005b [P] [US1] Add validation logic in `code/config.py` to assert that the scoring module correctly reads the PWM length to determine window size, ensuring spec compliance with dynamic windowing (FR-002). Do NOT assert a fixed value; assert that the scoring module's `get_window_size(tf_id)` function returns `len(pwm)` for the given TF.
- [ ] T006 [P] Implement `code/utils.py` with genome coordinate helpers, FASTA memory-mapped I/O wrappers, and checksum verification functions
- [ ] T007 [P] Create `code/__init__.py` and module structure for `data_ingestion`, `scoring`, and `statistics`
- [ ] T008 Setup `tests/unit/`, `tests/integration/`, and `tests/contract/` directories with `__init__.py` files
- [ ] T009 [P] Create `data/checksums.json` template and `code/data_ingestion.py` skeleton for downloading and verifying raw data

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Regulatory Context Filtering (Priority: P1) 🎯 MVP

**Goal**: Download common human SNPs from dbSNP (primary) and 1000 Genomes (fallback) and filter them to those located within annotated regulatory regions using ENCODE/Roadmap BED files.

**Independent Test**: Verify the output of the filtering script is a list of SNPs with genomic coordinates that overlap at least one regulatory region BED interval, with no SNPs outside these regions included.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/data_ingestion.py` to download common human SNPs (MAF > 1%) from **dbSNP** (primary source) using `bcftools` or FTP. **URL**: `ftp://ftp.ncbi.nih.gov/snp/organisms/human_9606_b155_GRCh38p13/VCF/`. **Constraint**: If dbSNP is unavailable, switch to fallback (T010a) and log source lineage to `data/raw/source_log.txt`.
- [ ] T010a [US1] Implement `code/data_ingestion.py` to download Genomes Phase 3 VCF (common SNPs) as a fallback source. **URL**: `ftp://ftp.1000genomes.ebi.ac.uk/ebi/ftp/1000_Genomes/release/20130502/ALL.chr*.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz`.
- [ ] T010b [US1] Implement `code/data_ingestion.py` to download JASPAR PWMs (CORE collection) for human TFs. **URL**: `. Save to `data/raw/jaspar_pwm.txt`.
- [ ] T010c [US1] Implement selection logic in `code/data_ingestion.py` to prioritize dbSNP (T010) and fallback to 1000 Genomes (T010a) if dbSNP unavailable; log source lineage to `data/raw/source_log.txt`.
- [ ] T011 [US1] Implement `code/data_ingestion.py` to download ENCODE/Roadmap promoter and enhancer BED files. **URL**: ` (Promoter) and ` (Enhancer) or specific `wgEnRegTss...bed.gz` patterns from ENCODE portal.
- [ ] T012 [US1] Implement filtering logic in `code/data_ingestion.py` to exclude SNPs with MAF < 1% and non-ACGT alleles (handle N/indels).
- [ ] T013 [US1] Implement overlap logic in `code/data_ingestion.py` using `pybedtools` to intersect SNPs with regulatory regions (≥1bp overlap). **Dependency**: Requires T010 (or T010a) producing `data/raw/snps_raw.vcf` AND T011 producing `data/raw/regulatory_regions.bed`.
- [ ] T013b [US1] Implement `code/data_ingestion.py` to generate a GC-matched non-regulatory control set. Logic: Select random genomic regions, match GC content within ±2% of the filtered regulatory SNPs, and ensure no overlap with regulatory regions. Save to `data/derived/gc_matched_controls.parquet`.
- [ ] T014 [US1] Save filtered SNPs to `data/derived/filtered_snps.parquet`; **Run pydantic/JSONSchema validator against `specs/001-gene-regulation/contracts/snp_schema.schema.yaml` before saving**.
- [ ] T015 [US1] Implement `tests/unit/test_data_ingestion.py` to verify MAF filtering and non-ACGT exclusion logic
- [ ] T016 [US1] Implement `tests/integration/test_ingestion_pipeline.py` to verify overlap logic against a small synthetic BED/SNP set

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Allele-Specific Binding Affinity Scoring (Priority: P2)

**Goal**: Calculate the difference in binding affinity ($\Delta Score$) between reference and alternate alleles for every SNP-TF pair within a **dynamic context window** where the window size equals the PWM length (per FR-002).

**Independent Test**: Run the scorer on a small, manually verified subset of SNPs and compare the calculated $\Delta Score$ against a manual calculation to ensure mathematical correctness.

### Implementation for User Story 2

- [ ] T017 [US2] Implement `code/scoring.py` to load JASPAR PWMs (from T010b output `data/raw/jaspar_pwm.txt`) and convert them to scoring matrices. **Dependency**: Requires T010b completion.
- [ ] T018 [US2] Implement `code/scoring.py` to extract genomic sequences from a reference FASTA (using `pyfaidx` memory-mapped access) based on SNP coordinates and **dynamic window size equal to the PWM length** for the specific TF being scored. **Dependency**: Requires T014 (filtered SNPs) and T017 (PWMs). **Validation**: Assert that the window size used matches the `len(pwm)` for the current TF.
- [ ] T019 [US2] Implement `code/scoring.py` to calculate log-odds scores for both reference and alternate allele sequences
- [ ] T020 [US2] Implement `code/scoring.py` to compute $\Delta Score = Score_{alt} - Score_{ref}$ for all valid SNP-TF pairs
- [ ] T020b [US2] Implement `code/scoring.py` to calculate and output a boolean flag `is_large_magnitude` where true if the absolute $\Delta Score$ is ≥ 2 bits. This flag is for reporting purposes only and MUST NOT be used to filter the input data for statistical tests (per FR-003).
- [ ] T021 [US2] Save scoring results to `data/derived/scores.parquet` with columns: `snp_id`, `tf_id`, `ref_score`, `alt_score`, `delta_score`, `window_size`, `is_large_magnitude`
- [ ] T022 [US2] Implement `tests/unit/test_scoring.py` to verify log-odds calculation and $\Delta Score$ logic on known sequences
- [ ] T023 [US2] Implement `tests/integration/test_scoring_pipeline.py` to verify end-to-end sequence extraction and scoring flow

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Enrichment and GWAS Overlap Analysis (Priority: P3)

**Goal**: Aggregate $\Delta Score$ distributions, perform permutation tests, and cross-reference high-impact SNPs with GWAS Catalog loci.

**Independent Test**: Run the analysis on a synthetic dataset where enrichment status is known and verify the permutation test correctly identifies enrichment with p-value < 0.05.

### Implementation for User Story 3

- [ ] T024 [P] [US3] Implement `code/statistics.py` to perform stratified label permutation test (n=100) shuffling SNP positions **within the same LD block ID (stratum)** to generate null distributions; use random seed from `config.py`. This preserves local sequence context and GC content (per FR-004).
- [ ] T025 [US3] Implement `code/statistics.py` to calculate p-values for each TF's observed $\Delta Score$ distribution against its null distribution, **apply multiple testing correction**, and **verify/flag TFs where adjusted p-value < 0.05** (per SC-002).
- [ ] T025a [US3] Implement `code/statistics.py` to perform a **Kolmogorov-Smirnov (KS) test** on the **FULL unfiltered distribution** of scores for SNPs *inside* GWAS loci against the distribution of scores for SNPs *outside* GWAS loci (or the matched control set), as required by FR-005 and FR-007.
- [ ] T026 [US3] Implement `code/statistics.py` to identify high-impact SNPs (top configurable % by $|\Delta Score|$)
- [ ] T027 [US3] Implement `code/statistics.py` to download/load **GWAS Catalog lead SNPs** (BED format) from `ftp://ftp.ebi.ac.uk/pub/databases/gwas/latest/` (filtering specifically for 'lead' variants) and calculate overlap enrichment ratios. **Note**: Ensure the data source is filtered for lead SNPs, not generic summary statistics. Use the file with the most recent modification timestamp available at runtime.
- [ ] T028 [US3] Implement `code/statistics.py` to apply **West-Stephens max-T permutation FDR** method to the p-values generated from the permutation tests across all TFs. This method MUST preserve the joint distribution of scores across correlated TF motifs by permuting the GWAS status labels across the entire dataset simultaneously for each permutation iteration (per FR-006).
- [ ] T029 [US3] Save final results to `data/derived/enrichment_results.parquet` including p-values, FDR, enrichment ratios, and high-impact SNP lists
- [ ] T030 [US3] Implement `tests/unit/test_statistics.py` to verify permutation logic and FDR calculation
- [ ] T031 [US3] Implement `tests/integration/test_enrichment_pipeline.py` to verify end-to-end statistical analysis on synthetic data

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Create `code/main.py` orchestration script to run the full pipeline (Ingestion → Scoring → Statistics)
- [ ] T032b [P] Implement logic to generate **synthetic data** (SNPs, BEDs, PWMs) for CI Validation Mode
- [ ] T032c [P] Implement mode switch logic in `code/main.py` to toggle between 'Research' (Real Data) and 'Validation' (Synthetic Data) modes
- [ ] T033 [P] Generate `data/checksums.json` for all files in `data/raw/` and `data/derived/`
- [ ] T034 Update `README.md` with execution instructions and data source citations
- [ ] T035 [P] Add performance monitoring to `code/main.py` to log RAM usage and execution time per phase
- [ ] T036 Run `pytest` to ensure all tests pass and generate coverage report

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (filtered SNPs) for sequence extraction
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (scores) for statistical analysis
- **Data Flow**: T010/T011 (Data Fetch) → T014 (Filtered SNPs) → T018 (Sequence Extraction) → T020 (Scoring) → T024 (Permutation) → T027 (GWAS Overlap)

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for data ingestion in tests/contract/test_ingestion.py"
Task: "Integration test for filtering pipeline in tests/integration/test_ingestion_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Create data_ingestion.py in code/data_ingestion.py"
Task: "Create utils.py in code/utils.py"
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