# Tasks: Exploring the Mechanisms of Gene Regulation Across Different Cell Types

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are REQUIRED as they implement critical verification steps mandated by the spec's 'Independent Test' sections.

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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project root directory: `projects/PROJ-019-exploring-the-mechanisms-of-gene-regulat/`
- [X] T001b [P] Create `code/` directory inside project root
- [X] T001c [P] Create `data/` directory inside project root
- [X] T001d [P] Create `data/raw/` directory inside project root
- [X] T001e [P] Create `data/interim/` directory inside project root
- [X] T001f [P] Create `data/processed/` directory inside project root
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (requests, pandas, pybedtools, scipy, seaborn, matplotlib, biopython, pytest). Note: `pybedtools` is used for BED parsing and annotation as per plan.md Technical Context.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections defining standard rules
- [X] T008 [P] Setup `tests/` directory structure: Create `unit/`, `integration/`, `contract/` subdirectories and `__init__.py` in each

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` to define `TMP_DIR`, `DATA_RAW_DIR`, `DATA_INTERIM_DIR`, `DATA_PROCESSED_DIR`, retry limits, and dataset version constants
- [X] T005 [P] Create `code/utils/disk_check.py` to verify ≥14GB free space in `TMP_DIR` before execution (FR-002, Edge Cases) and exit with clear error if insufficient
- [X] T006 [P] Create `code/utils/network.py` implementing exponential backoff with a maximum of 3 retries for HTTP requests (FR-006)
- [X] T007 Create `data/provenance.json` structure to record specific ENCODE accession IDs, JASPAR version, and download timestamps as per Constitution (VI)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download, parse, and normalize ATAC-seq/ChIP-seq peak data for 5 cell types into a unified BED-like format with gene annotations.

**Independent Test**: Verify pipeline downloads files to `TMP_DIR`, parses them without crashing, and outputs a summary report of peak counts per cell type within 14GB disk limits.

### Tests for User Story 1 (REQUIRED) ⚠️

- [ ] T010 [P] [US1] Write unit test `tests/unit/test_ingest.py::test_parse_handles_malformed_bed` which is expected to fail until T012-T014 implementation is complete. Assert parser raises specific `ValueError` on malformed BED input and logs error. **This task is REQUIRED to meet US-1 Independent Test criteria.**
- [ ] T011 [P] [US1] Write unit test `tests/unit/test_network.py::test_retry_exponential_backoff` which is expected to fail until T006 implementation is complete. Assert network utility retries a limited number of times with exponential delays. before raising `MaxRetriesError`. **This task is REQUIRED to meet US-1 Independent Test criteria.**

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download.py` to download ENCODE peak files for GM12878, K562, HepG2, H1-hESC, IMR90 using `code/utils/network.py` (FR-001, FR-006)
- [X] T013 [US1] Implement parsing logic in `code/preprocess.py` to convert downloaded files to standardized BED format AND annotate with gene symbols, storing results in `data/interim/` (FR-002). Note: This task relies on T013b for path configuration.
- [X] T013b [US1] Implement `code/config.py` logic to configure and validate `TMP_DIR` usage for intermediate storage, ensuring FR-002's configurable directory requirement is met. This includes setting default paths, validating write permissions, and explicitly distinguishing `TMP_DIR` (intermediate) from `data/interim/` (final output) to ensure the 'configurable directory' requirement is satisfied.
- [X] T014 [US1] Implement gene annotation and background model aggregation in `code/preprocess.py` using `pybedtools` to map peak coordinates to gene symbols (hg38) and, for each target cell type, aggregate peaks from the remaining cell types to form the dynamic background model (FR-002, FR-004)
- [ ] T015 [US1] Implement `code/main.py` orchestration logic: function `run_ingestion(peak_files)` takes parsed peaks as input and generates `data/processed/ingestion_summary.json` with keys: `total_peaks` (int, sum of all parsed files), `cell_types` (list, **exact values**: ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']; raise error if input contains unexpected types), `parsed_count` (int, count of successfully parsed files) (depends on T012, T013, T013b, T014 completion)
- [ ] T016 [US1] Update `code/main.py` to integrate `code/utils/disk_check.py` as a pre-flight check before `run_ingestion` execution. **Dependencies**: T012, T013, T014 must be complete to ensure orchestration logic calls implemented functions.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Motif Scanning and Enrichment Analysis (Priority: P2)

**Goal**: Scan peaks for TF motifs using FIMO (CPU-only), compute background model (union of other cell types), and calculate enrichment scores with multiple-testing correction.

**Independent Test**: Run scanning on a small synthetic subset, verify output contains p-values ≤0.0001, and confirm distinct enrichment profiles (correlation <0.8) between cell types.

### Tests for User Story 2 (REQUIRED) ⚠️

- [ ] T018 [P] [US2] Write unit test `tests/unit/test_background.py::test_union_aggregation` which is expected to fail until T014 implementation is complete. Assert background generation correctly aggregates (unioning) Peak Regions from the other 4 cell types.
- [ ] T019 [P] [US2] Write unit test `tests/unit/test_motifs.py::test_fisher_exact_correction` which is expected to fail until T022 implementation is complete. Assert Fisher's test returns correct p-values and Benjamini-Hochberg correction returns correct q-values for a known input matrix.

### Implementation for User Story 2

- [X] T021a [US2] Implement `code/scan.py` to invoke FIMO (subprocess) against JASPAR CORE database with p-value ≤0.0001 threshold (FR-003). Depends on T014 output (background model and parsed peaks).
- [X] T021b [US2] Implement `code/scan.py` to parse FIMO output into a standardized list of motif matches with genomic coordinates and p-values.
- [X] T022 [US2] Implement enrichment calculation in `code/enrichment.py` using Fisher's exact test against the background model (union of other cell types) (FR-004)
- [X] T023 [US2] Implement Benjamini-Hochberg correction in `code/enrichment.py` to generate adjusted q-values (FR-004)
- [X] T025 [US2] Add chunked processing logic in `code/enrichment.py` to ensure memory usage stays <7GB if dataset size approaches RAM limits (GitHub Actions free-tier constraint). **Note**: This is a defensive measure; the primary assumption of in-memory processing remains unless limits are exceeded.
- [ ] T024 [US2] Update `code/main.py` to orchestrate scanning, enrichment: function `run_enrichment(matches, background)` takes motif matches as input and outputs `data/processed/enrichment_matrix.csv` with columns: `motif_id` (**JASPAR ID format, e.g., 'MA0001.1'**), `cell_type` (**exact string match**: ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']), `p_value` (float), `q_value` (float) (depends on T021a, T021b, T022, T023, T025 outputs)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Cross-Validation (Priority: P3)

**Goal**: Generate heatmaps of enrichment results and validate findings against independent ChIP-seq data.

**Independent Test**: Generate plots, verify heatmap clustering silhouette score ≥0.4 (as a verification metric), and confirm ≥60% overlap between predicted motifs and independent ChIP-seq peaks.

### Tests for User Story 3 (REQUIRED) ⚠️

- [ ] T026 [P] [US3] Write unit test `tests/unit/test_viz.py::test_heatmap_silhouette_score` which is expected to fail until T028 implementation is complete. Assert clustering function returns silhouette score and logs it.
- [ ] T027 [P] [US3] Write unit test `tests/unit/test_validate.py::test_chip_overlap_calculation` which is expected to fail until T030 implementation is complete. Assert overlap percentage is calculated correctly against a mock ChIP-seq dataset.

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `code/visualize.py` to generate heatmap: function `generate_heatmap(matrix)` takes enrichment_matrix.csv as input, uses Euclidean distance clustering with linkage='average', checks silhouette score, and outputs `data/processed/heatmap.png` (FR-005). **Note**: This task is the prerequisite for T032. Depends on T024.
- [ ] T032a [US3] Implement `code/validate.py` to filter enrichment results to top enriched motifs (q < 0.05) before generating summary table, ensuring FR-005's 'top enriched' constraint is satisfied. **Output**: List of motif IDs and their q-values for downstream tasks.
- [ ] T030 [US3] Implement `code/validate.py` to fetch independent ChIP-seq peaks for the top enriched motifs (q < 0.05) from ENCODE. This task must include logic to: 1) **Filter enrichment results to motifs with q < 0.05 (input from T032a)**, 2) Identify corresponding TFs and cell types, 3) **Map motif_id to TF name and then to specific ENCODE accession IDs** using a hardcoded mapping table for top 5 motifs per cell type (e.g., `{'MA0001.1': 'ENCSR000XXX',...}`), 4) **Retrieve ChIP-seq peak files from ENCODE using specific accession IDs and URLs** (e.g., `), 5) Calculate overlap percentage (FR-005). **Dependencies**: T032a, T028.
- [ ] T031 [US3] Implement `code/validate.py` to compute silhouette score from the heatmap data (generated by T028) and log the result. **If score < 0.4, log a warning but do NOT exit with error code 1**, as the spec requires generating visualizations regardless of clustering quality. **Note**: Depends on T028 completion.
- [ ] T032 [US3] Update `code/main.py` to orchestrate visualization and validation: function `run_validation_report(heatmap_data, chip_data)` takes heatmap data (from T028) and validation stats (from T030) as input and generates `data/processed/validation_report.json` with keys: `overlap_pct` (float, 2 decimal places), `top_motifs` (**list of objects with keys: `motif_id` (string), `q_value` (float, 4 decimal places), `overlap_pct` (float, 2 decimal places)**), `silhouette_score` (float, 2 decimal places) (depends on T028, T030, T032a). **Note**: This task is the prerequisite for T033.
- [ ] T033 [US3] Generate final summary table: function `generate_summary_table(enrichment_csv, validation_json)` reads from `data/processed/enrichment_matrix.csv` (filtered by T032a) and `data/processed/validation_report.json` and outputs `data/processed/summary_table.csv` with columns: `motif_id`, `p_value_raw`, `q_value_adj`, `chip_overlap_pct`. Note: `chip_overlap_pct` is calculated as the ratio of the intersection of predicted and observed peaks to their union, expressed as a percentage. (depends on T030, T032, T032a). This table satisfies US-3-SC1 Scenario 3.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `README.md` and `specs/001-gene-regulation/quickstart.md`
- [ ] T036 [P] Performance optimization for FIMO execution: Modify FIMO loop in `code/scan.py` to use `joblib.Parallel(n_jobs=2, max_nbytes=500MB)` where safe, ensuring total memory footprint remains <7GB.
- [ ] T037 [P] Additional unit tests in `tests/unit/`: Add contract tests `test_ingestion_summary_schema()` validating `total_peaks` (int) and `cell_types` (list), and `test_enrichment_matrix_schema()` validating `motif_id` (str) and `q_value` (float) in `tests/contract/` for schema validation.
- [ ] T038 Run `quickstart.md` validation to ensure end-to-end reproducibility on the target CI environment.

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
# Launch all tests for User Story 1 together:
Task: "Write unit test for tests/unit/test_ingest.py::test_parse_handles_malformed_bed"
Task: "Write unit test for tests/unit/test_network.py::test_retry_exponential_backoff"

# Launch all models for User Story 1 together:
Task: "Implement code/download.py to download ENCODE peak files"
Task: "Implement parsing logic in code/preprocess.py"
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
- **Critical Constraint**: All tasks must run on CPU-only free-tier CI (A minimal computing environment with a small number of cores, limited RAM (~GB), and limited disk.). No GPU, no 8-bit quantization, no large model training.
- **Data Integrity**: No synthetic/fake data allowed. All analysis must use real ENCODE/JASPAR data.
- **Background Model**: Use "Peak Regions from other cell types" (union) as the background model, as mandated by FR-004 and Spec Assumptions.
- **Disk Space**: Check for ≥14GB free space (FR-002, SC-004).
- **Silhouette Score**: Verify ≥0.4 and log warning if lower (do NOT exit with error code 1).
- **Chunked Processing**: Authorized to meet a defined RAM limit if needed

The research question, method, and references remain unchanged as no specific values were asserted in the original passage beyond the target to be generalized..
- **File Paths**: Strictly follow plan.md file structure: `code/download.py`, `code/preprocess.py`, `code/scan.py`, `code/enrichment.py`, `code/visualize.py`.
- **Plan Discrepancy Note**: There is a known contradiction between SC-004 (requires 16GB RAM) and plan.md (targets ~7GB RAM). This has been flagged for kickback to the planning stage. Tasks are based on the plan's constraints.