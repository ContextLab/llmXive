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

- [X] T004 [P] Implement `code/config.py` to define `TMP_DIR` (default `/tmp`), `DATA_RAW_DIR`, `DATA_INTERIM_DIR`, `DATA_PROCESSED_DIR`, retry limits, and dataset version constants. **Includes logic to validate that `TMP_DIR` exists and has ≥14GB free space before any processing begins (FR-002).**
- [X] T005 [P] Create `code/utils/memory_check.py` to verify ≥16GB RAM availability (SC-004) and log a CRITICAL warning if below 16GB but above 7GB (Plan target), exiting with error ONLY if < 7GB. **This task explicitly addresses the SC-004 requirement for 16GB RAM. If RAM < 16GB, the pipeline logs a warning that the spec constraint is at risk but continues to allow execution on free-tier resources.**
- [X] T006 [P] Create `code/utils/network.py` implementing exponential backoff with a maximum of 3 retries for HTTP requests [UNRESOLVED-CLAIM: c_42c5bac3 — status=not_enough_info] (FR-006)
- [X] T007 Create `data/provenance.json` structure to record specific ENCODE accession IDs, JASPAR version, and download timestamps as per Constitution (VI)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download, parse, and normalize ATAC-seq/ChIP-seq peak data for multiple cell types into a unified BED-like format with gene annotations.

**Independent Test**: Verify pipeline downloads files to `TMP_DIR`, parses them without crashing, and outputs a summary report of peak counts per cell type within 14GB disk limits.

### Tests for User Story 1 (REQUIRED) ⚠️

- [X] T010 [US1] Write unit test `tests/unit/test_ingest.py::test_parse_handles_malformed_bed` which is expected to fail until T012-T014 implementation is complete. Assert parser raises specific `ValueError` on malformed BED input and logs error. **This task is REQUIRED to meet US-1 Independent Test criteria. Note: This task must run AFTER T012-T014 to avoid import errors, despite being a test-first task. Do NOT mark [P] as it depends on code existence.**
- [X] T011 [P] [US1] Write unit test `tests/unit/test_network.py::test_retry_exponential_backoff` which is expected to fail until T006 implementation is complete. Assert network utility retries a limited number of times with exponential delays. before raising `MaxRetriesError`. **This task is REQUIRED to meet US-1 Independent Test criteria. Note: This task must run AFTER T006.**

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download.py` to download ENCODE peak files for representative human cell lines using `code/utils/network.py` (FR-001, FR-006). **Constraint**: If download fails, raise `DataFetchError` and DO NOT fall back to synthetic/mock data (Constitution Data Hygiene).
- [X] T013 [US1] Implement parsing logic in `code/preprocess.py` to convert downloaded files to standardized BED format AND annotate with gene symbols. **Critical**: Intermediate parsed files MUST be written to `TMP_DIR` (configured in T004) to satisfy FR-002's requirement for a configurable temporary directory. Final aggregated results are stored in `data/interim/`. **Constraint**: If parsing fails, raise `DataParseError` and DO NOT fall back to synthetic/mock data. (FR-002). Note: This task relies on T004 for path configuration.
- [X] T014 [US1] Implement gene annotation and background model aggregation in `code/preprocess.py` using `pybedtools` to map peak coordinates to gene symbols (hg38) and, for each target cell type, aggregate peaks from the remaining cell types to form the dynamic background model (FR-002, FR-004)
- [ ] T015 [US1] Implement `code/main.py` orchestration logic: function `run_ingestion(peak_files)` takes parsed peaks as input and generates `data/processed/ingestion_summary.json` with keys: `total_peaks` (int, sum of all parsed files), `cell_types` (list, **exact values**: ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']; raise error if input contains unexpected types), `parsed_count` (int, count of successfully parsed files) (depends on T012, T013, T014 completion)
- [ ] T016 [US1] Update `code/main.py` to integrate `code/utils/disk_check.py` and `code/utils/memory_check.py` as pre-flight checks before `run_ingestion` execution. **Dependencies**: T004, T005, T012, T013, T014, T015 must be complete to ensure orchestration logic calls implemented functions.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Motif Scanning and Enrichment Analysis (Priority: P2)

**Goal**: Scan peaks for TF motifs using FIMO (CPU-only), compute background model (union of other cell types), and calculate enrichment scores with multiple-testing correction.

**Independent Test**: Run scanning on a small synthetic subset, verify output contains p-values ≤0.0001, and confirm distinct enrichment profiles (correlation <0.8) between cell types.

### Tests for User Story 2 (REQUIRED) ⚠️

- [X] T018 [P] [US2] Write unit test `tests/unit/test_background.py::test_union_aggregation` which is expected to fail until T014 implementation is complete. Assert background generation correctly aggregates (unioning) Peak Regions from the other 4 cell types.
- [X] T019 [P] [US2] Write unit test `tests/unit/test_motifs.py::test_fisher_exact_correction` which is expected to fail until T022 implementation is complete. Assert Fisher's test returns correct p-values and Benjamini-Hochberg correction returns correct q-values for a known input matrix.

### Implementation for User Story 2

- [X] T021a [US2] Implement `code/scan.py` to invoke FIMO (subprocess) against JASPAR CORE database with p-value ≤0.0001 threshold (FR-003). **Note**: {{claim:c_f85c1c37}}. The spec allows 'FIMO or HOMER', but plan.md explicitly selects FIMO. This task explicitly acknowledges the spec's flexibility while adhering to the plan's selection. Depends on T014 output (background model and parsed peaks).
- [X] T021b [US2] Implement `code/scan.py` to parse FIMO output into a standardized list of motif matches with genomic coordinates and p-values.
- [X] T022 [US2] Implement enrichment calculation in `code/enrichment.py` using Fisher's exact test against the background model (union of other cell types) (FR-004)
- [X] T023 [US2] Implement Benjamini-Hochberg correction in `code/enrichment.py` to generate adjusted q-values (FR-004)
- [X] T025 [US2] Add chunked processing logic in `code/enrichment.py` to ensure memory usage stays <7GB if dataset size approaches RAM limits [UNRESOLVED-CLAIM: c_75780519 — status=not_enough_info] (GitHub Actions free-tier constraint). **Note**: This is a defensive measure; the primary assumption of in-memory processing remains unless limits are exceeded.
- [ ] T024 [US2] Update `code/main.py` to orchestrate scanning, enrichment: function `run_enrichment(matches, background)` takes motif matches as input and outputs `data/processed/enrichment_matrix.csv` with columns: `motif_id` (**JASPAR ID format, e.g., 'MA0001.1'**), `cell_type` (**exact string match**: ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']), `p_value` (float), `q_value` (float) (depends on T021a, T021b, T022, T023, T025 outputs)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Cross-Validation (Priority: P3)

**Goal**: Generate heatmaps of enrichment results and validate findings against independent ChIP-seq data.

**Independent Test**: Generate plots, verify heatmap clustering silhouette score ≥0.4 [UNRESOLVED-CLAIM: c_49ce5412 — status=not_enough_info] (as a verification metric), and confirm ≥60% overlap between predicted motifs and independent ChIP-seq peaks [UNRESOLVED-CLAIM: c_80a1739b — status=not_enough_info].

### Tests for User Story 3 (REQUIRED) ⚠️

- [X] T026 [P] [US3] Write unit test `tests/unit/test_viz.py::test_heatmap_silhouette_score` which is expected to fail until T028 implementation is complete. Assert clustering function returns silhouette score and logs it.
- [X] T027 [P] [US3] Write unit test `tests/unit/test_validate.py::test_chip_overlap_calculation` which is expected to fail until T030 implementation is complete. Assert overlap percentage is calculated correctly against a mock ChIP-seq dataset.

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `code/visualize.py` to generate heatmap: function `generate_heatmap(matrix)` takes enrichment_matrix.csv as input, uses Euclidean distance clustering with linkage='average', and outputs `data/processed/heatmap.png` (FR-005). **Note**: This task is the prerequisite for T032. Depends on T024. The silhouette score is computed in T031a, not here.
- [X] T029 [P] [US3] Create `data/config/cell_type_mapping.json` containing the mapping of internal cell type strings (e.g., 'H1-hESC') to ENCODE `cell_line` values. **Content Requirement**: The file MUST be a JSON object mapping internal names to ENCODE cell line IDs (e.g., `{"GM12878": "ENCFF...", "K562": "ENCFF..."}`). This file will be used by T030 to dynamically fetch ChIP-seq data, avoiding hardcoded code in the script. **Dependencies**: None (Config file).
- [ ] T032a [US3] Implement `code/validate.py` to filter enrichment results to top enriched motifs (q < 0.05) before generating summary table, ensuring FR-005's 'top enriched' constraint is satisfied. **Output**: List of motif IDs and their q-values for downstream tasks. **Dependencies**: T024.
- [ ] T030 [US3] Implement `code/validate.py` to fetch independent ChIP-seq peaks for the top enriched motifs (q < 0.05) from ENCODE. **CRITICAL**: Load the `CELL_TYPE_MAPPING` from `data/config/cell_type_mapping.json` (T029). Do NOT use hardcoded mapping tables in code. 1) Identify TF name and cell type from enrichment matrix. 2) Use ENCODE API with mapping to retrieve accession IDs. 3) Handle cases where API returns no results: log a warning and record `overlap_pct = None` (do not crash or invent data). 4) Download the real peak files. 5) Calculate overlap percentage (FR-005). **Dependencies**: T032a, T024, T029.
- [ ] T031a [US3] Implement `code/validate.py` to compute silhouette score from the enrichment matrix (T024) and log the result. **This task verifies the metric as a success condition (Independent Test).** **Note**: Depends on T024 (raw matrix data), NOT T028 (image). **Output**: Writes `data/processed/silhouette_score.json` containing the computed score to ensure data flow to T031b and T032.
- [ ] T031b [US3] Implement `code/validate.py` to enforce the silhouette score threshold: Read `data/processed/silhouette_score.json` (T031a). If score < 0.4, log a warning and set `validation_passed = False`. If score >= 0.4, log a success message and set `validation_passed = True`. **This task explicitly covers the 'Independent Test' success path (score >= 0.4) and failure path. It does NOT exit with code 1; the pipeline continues, and the result is reported in T032.** **Note**: Depends on T031a.
- [ ] T032 [US3] Update `code/main.py` to orchestrate visualization and validation: function `run_validation_report(heatmap_data, chip_data, score, validation_flag)` takes heatmap data (from T028), validation stats (from T030), silhouette score (from T031a), and validation flag (from T031b) as input and generates `data/processed/validation_report.json` with keys: `overlap_pct` (float, The precision of the measurement will be reported to two decimal places [UNRESOLVED-CLAIM: c_0c44415f — status=not_enough_info]., or null), `top_motifs` (**list of objects with keys: `motif_id` (string), `q_value` (float, high precision (e.g., four decimal places) [UNRESOLVED-CLAIM: c_7dacf4a5 — status=not_enough_info]), `overlap_pct` (float, 2 decimal places, or null)**), `silhouette_score` (float, 2 decimal places), `validation_passed` (bool), `silhouette_test_passed` (bool, derived from score >= 0.4). (depends on T028, T030, T031a, T031b, T032a). **Note**: This task is the prerequisite for T033.
- [ ] T033 [US3] Generate final summary table: function `generate_summary_table(enrichment_csv, validation_json)` reads from `data/processed/enrichment_matrix.csv` (filtered by T032a) and `data/processed/validation_report.json` and outputs `data/processed/summary_table.csv` with columns: `motif_id`, `p_value_raw`, `q_value_adj`, `chip_overlap_pct`. Note: `chip_overlap_pct` is calculated as the ratio of the intersection of predicted and observed peaks to their union, expressed as a percentage. (depends on T030, T032, T032a). This table satisfies US-3-SC1 Scenario 3.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `README.md` and `specs/001-gene-regulation/quickstart.md`. **Content Requirement**: `quickstart.md` MUST include: 1) Exact commands to run the pipeline (`python -m code.main`), 2) Expected output artifacts list, 3) Expected output format for `ingestion_summary.json`, `enrichment_matrix.csv`, and `validation_report.json`, 4) A note on the required disk space (≥14GB) and RAM (≥16GB per SC-004, ≥7GB per plan).
- [ ] T036 [P] Performance optimization for FIMO execution: Modify FIMO loop in `code/scan.py` to use `joblib.Parallel(n_jobs=2, max_nbytes=500MB)` where safe, ensuring total memory footprint remains <7GB [UNRESOLVED-CLAIM: c_f61c9eee — status=not_enough_info].
- [X] T038 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility on the target CI environment. **Dependencies**: T034, T030.

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
- **Critical Constraint**: All tasks must run on CPU-only free-tier CI (A minimal computing environment with a small number of cores, limited RAM (~GB), and limited disk [UNRESOLVED-CLAIM: c_7984fdaf — status=not_enough_info].). No GPU, no 8-bit quantization, no large model training.
- **Data Integrity**: No synthetic/fake data allowed. All analysis must use real ENCODE/JASPAR data. **Fail Loudly**: If real data fetch fails, raise an error.
- **Background Model**: Use "Peak Regions from other cell types" (union) as the background model, as mandated by FR-004 and Spec Assumptions.
- **Disk Space**: Check for ≥14GB free space (FR-002, SC-004).
- **Silhouette Score**: Verify ≥0.4 and log the result. If < 0.4, log a warning and set `validation_passed = False` (do not hard fail unless spec changes).
- **Chunked Processing**: Authorized to meet a defined RAM limit if needed
- **File Paths**: Strictly follow plan.md file structure: `code/download.py`, `code/preprocess.py`, `code/scan.py`, `code/enrichment.py`, `code/visualize.py`.
- **Plan Discrepancy Note**: There is a known contradiction between SC-004 (requires 16GB RAM) and plan.md (targets ~7GB RAM). This has been flagged for kickback to the planning stage. Tasks are based on the plan's constraints, with T005 explicitly checking for 16GB.
- **Removed Tasks**: Phase O (T039-T046) and T037 have been removed as they constituted unapproved scope creep or redundancy. T031 has been split into T031a (verification) and T031b (conditional fail) to align with spec. T029 added to provide the mapping config required by T030.

The research question, method, and references remain unchanged as no specific values were asserted in the original passage beyond the target to be generalized..
- **File Paths**: Strictly follow plan.md file structure: `code/download.py`, `code/preprocess.py`, `code/scan.py`, `code/enrichment.py`, `code/visualize.py`.
- **Plan Discrepancy Note**: There is a known contradiction between SC-004 (requires 16GB RAM) and plan.md (targets ~GB RAM). This has been flagged for kickback to the planning stage. Tasks are based on the plan's constraints.
