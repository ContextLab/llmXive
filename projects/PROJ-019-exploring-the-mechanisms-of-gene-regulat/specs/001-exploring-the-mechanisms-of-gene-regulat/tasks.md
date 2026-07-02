# Tasks: Exploring the Mechanisms of Gene Regulation Across Different Cell Types

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

- [ ] T001a [P] Create project directory structure: `projects/PROJ-019-exploring-the-mechanisms-of-gene-regulat/`, `code/`, `data/`, `tests/`
- [ ] T001b [P] Create `__init__.py` files in `code/` and `tests/` directories
- [ ] T001c [P] Create `.gitkeep` files in `data/raw/`, `data/processed/`, `data/results/`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (requests, pandas, pybedtools, scipy, seaborn, matplotlib, biopython, gffutils, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` to define `TMP_DIR`, `DATA_RAW_DIR`, `DATA_PROCESSED_DIR`, `DATA_RESULTS_DIR`, retry limits, and dataset version constants
- [ ] T005 [P] Create `code/utils/disk_check.py` to verify ≥1GB free space in `TMP_DIR` before execution (FR-002, Edge Cases) and exit with clear error if insufficient
- [ ] T006 [P] Create `code/utils/network.py` implementing exponential backoff with a maximum of 3 retries for HTTP requests (FR-006)
- [ ] T007 Create `data/provenance.yaml` structure to record ENCODE accession IDs, JASPAR version, and download timestamps
- [ ] T008 Setup `tests/` directory structure (`unit`, `integration`, `contract`)
- [ ] T099 [P] Update `spec.md` to align with Plan Corrections: 
  - FR-002: Change disk space requirement from "≥14GB" to "≥1GB free" to match runner constraints.
  - FR-004: Change background model from "Peak Regions from other cell types" to "GC-matched random genomic regions".
  - US-3-SC1: Change acceptance criteria from "ensuring silhouette score ≥0.4" to "verifying silhouette score ≥0.4 or failing with diagnostic log".
  - SC-004: Explicitly authorize "chunked processing" to meet 7GB RAM limit.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download, parse, and normalize ATAC-seq/ChIP-seq peak data for 5 cell types into a unified BED-like format with gene annotations.

**Independent Test**: Verify pipeline downloads files to `TMP_DIR`, parses them without crashing, and outputs a summary report of peak counts per cell type within 1GB free disk limits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Unit test `tests/unit/test_ingest.py::test_parse_handles_malformed_bed` to assert parser raises specific `ValueError` on malformed BED input and logs error.
- [ ] T011 [P] [US1] Unit test `tests/unit/test_network.py::test_retry_exponential_backoff` to assert network utility retries exactly 3 times with exponential delays before raising `MaxRetriesError`.

### Implementation for User Story 1

- [ ] T016 [US1] Implement `code/main.py` pre-flight check to verify ≥1GB free space in `TMP_DIR` (referencing spec Edge Cases and FR-002 as updated in T099) before download starts.
- [ ] T012 [US1] Implement `code/ingest.py` to download ENCODE peak files for GM, K, HepG2, H1-hESC, IMR90 using `code/utils/network.py` (FR-001, FR-006)
- [ ] T013 [US1] Implement parsing logic in `code/ingest.py` to convert downloaded files to standardized BED format and store in `data/processed/` (FR-002)
- [ ] T014 [US1] Implement gene annotation logic in `code/ingest.py` using `gffutils` to map peak coordinates to gene symbols (hg38) (FR-002)
- [ ] T015 [US1] Implement `code/main.py` orchestration logic to run ingestion and generate `data/results/ingestion_summary.json` with peak counts per cell type (integrating T016 check)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Motif Scanning and Enrichment Analysis (Priority: P2)

**Goal**: Scan peaks for TF motifs using FIMO (CPU-only), compute GC-matched background, and calculate enrichment scores with multiple-testing correction.

**Independent Test**: Run scanning on a small synthetic subset, verify output contains p-values ≤0.0001, and confirm distinct enrichment profiles (correlation <0.8) between cell types.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test `tests/unit/test_background.py::test_gc_matching_tolerance` to assert generated background regions have GC-content within 5% of input peaks.
- [ ] T019 [P] [US2] Unit test `tests/unit/test_motifs.py::test_fisher_exact_correction` to assert Fisher's test returns correct p-values and Benjamini-Hochberg correction returns correct q-values for a known input matrix.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/background.py` to generate GC-matched random genomic regions restricted to open chromatin as the background model (Plan Correction per T099). Algorithm: 1) Generate random regions using `pybedtools randomize`, 2) Filter regions where GC-content is within 5% of input peaks, 3) Repeat until N regions are found.
- [ ] T021 [US2] Implement `code/motifs.py` to invoke FIMO (subprocess) against JASPAR CORE database with p-value ≤0.0001 threshold (FR-003)
- [ ] T022 [US2] Implement enrichment calculation in `code/motifs.py` using Fisher's exact test against the GC-matched background model (FR-004)
- [ ] T023 [US2] Implement Benjamini-Hochberg correction in `code/motifs.py` to generate adjusted q-values (FR-004)
- [ ] T025 [US2] Add chunked processing logic in `code/motifs.py` to ensure memory usage stays <7GB (Plan Correction per T099 update)
- [ ] T024 [US2] Update `code/main.py` to orchestrate background generation, scanning, and enrichment, outputting `data/results/enrichment_matrix.csv` (depends on T025)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Cross-Validation (Priority: P3)

**Goal**: Generate heatmaps/Manhattan plots of enrichment results and validate findings against independent ChIP-seq data.

**Independent Test**: Generate plots, verify heatmap clustering silhouette score ≥0.4, and confirm ≥60% overlap between predicted motifs and independent ChIP-seq peaks.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test `tests/unit/test_viz.py::test_heatmap_silhouette_score` to assert clustering function returns silhouette score ≥0.4 or raises `ValueError` with diagnostic.
- [ ] T027 [P] [US3] Unit test `tests/unit/test_validate.py::test_chip_overlap_calculation` to assert overlap percentage is calculated correctly against a mock ChIP-seq dataset.

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `code/viz.py` to generate heatmap of q-values with Euclidean distance clustering in `data/results/heatmap.png` (FR-005)
- [ ] T029 [P] [US3] Implement `code/viz.py` to generate Manhattan plots of motif enrichment in `data/results/manhattan.png` (Plan Requirement)
- [ ] T030 [US3] Implement `code/validate.py` to fetch independent ChIP-seq peaks for top motifs and calculate overlap percentage (FR-005)
- [ ] T031 [US3] Implement `code/validate.py` to generate `data/results/heatmap.png` and verify silhouette score ≥0.4 (US-3-SC1). If score <0.4, log warning and exit with error code 1.
- [ ] T032 [US3] Update `code/main.py` to orchestrate visualization and validation, generating `data/results/validation_report.json` with overlap stats (depends on T030)
- [ ] T033 [US3] Generate final summary table in `data/results/summary_table.csv` with columns: `motif_id`, `p_value_raw`, `q_value_adj`, `chip_overlap_pct` (depends on T030, T032)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `README.md` and `specs/001-gene-regulation/quickstart.md`
- [ ] T035 Code cleanup and refactoring
- [ ] T036 Performance optimization for FIMO execution (parallelization if safe)
- [ ] T037 [P] Additional unit tests in `tests/unit/`
- [ ] T038 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 results output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints/main orchestration
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for tests/unit/test_ingest.py::test_parse_handles_malformed_bed"
Task: "Unit test for tests/unit/test_network.py::test_retry_exponential_backoff"

# Launch all models for User Story 1 together:
Task: "Implement code/ingest.py to download ENCODE peak files"
Task: "Implement parsing logic in code/ingest.py"
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
   - Developer A: User Story 1 (Data Ingestion)
   - Developer B: User Story 2 (Motif Scanning) - *Note: Requires US1 data*
   - Developer C: User Story 3 (Visualization) - *Note: Requires US2 data*
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
- **Critical Constraint**: All tasks must run on CPU-only free-tier CI (A minimal computing environment with a small number of cores, limited RAM, and limited disk.). No GPU, no 8-bit quantization, no large model training.
- **Data Integrity**: No synthetic/fake data allowed. All analysis must use real ENCODE/JASPAR data.
- **Background Model**: Use GC-matched random genomic regions, NOT peaks from other cell types (Plan Correction per T099).
- **Disk Space**: Check for ≥1GB free space (Plan Correction per T099).
- **Silhouette Score**: Verify ≥0.4 or fail with exit code 1 (Plan Correction per T099).
- **Chunked Processing**: Authorized to meet 7GB RAM limit (Plan Correction per T099).