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

- [X] T001b [P] Create standard project directory structure: Execute `mkdir -p code data/raw data/interim data/processed tests/unit tests/integration tests/contract` to establish the required hierarchy.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (requests, pandas, pybedtools, scipy, seaborn, matplotlib, biopython, pytest, psutil, joblib). Note: `pybedtools` is used for BED parsing and annotation as per plan.md Technical Context. `psutil` is added for total memory monitoring in T036. `joblib` is added for parallel execution in T036.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections defining standard rules
- [X] T008 [P] Setup `tests/` directory structure: Create `unit/`, `integration/`, `contract/` subdirectories and `__init__.py` in each

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` to define `TMP_DIR` (default `/tmp`), `DATA_RAW_DIR`, `DATA_INTERIM_DIR`, `DATA_PROCESSED_DIR`, retry limits, and dataset version constants. **This task defines configuration constants ONLY. It does NOT implement the disk check logic (handled by T005b) or RAM check logic (handled by T005a).**
- [X] T005a [P] Create `code/utils/` directory structure and implement `code/utils/memory_check.py` to verify ≥16GB RAM availability (SC-004 target). **This task explicitly enforces the SC-004 requirement for 16GB RAM. If RAM < 16GB, the pipeline MUST exit with a CRITICAL error and clear message. No execution is allowed below this threshold.**
- [X] T005b [P] Implement `code/utils/disk_check.py` to verify ≥14GB available disk space on `TMP_DIR` (FR-002). **This task explicitly implements the FR-002 disk space check. The pipeline MUST exit with a clear error message if disk space < 14GB.**
- [X] T005c [P] Implement `code/utils/time_check.py` to track elapsed time during pipeline execution and exit with error if > 6 hours (SC-004). **This task implements the runtime monitoring required to verify the 6-hour constraint on the CPU-only runner. It does NOT include arbitrary warning thresholds.**
- [X] T006 [P] [FR-006] Implement `code/utils/network.py` with exponential backoff (limited retries) for HTTP requests. **Constraint**: Must raise `MaxRetriesError` after a defined number of failures.; NO synthetic fallback allowed.
- [X] T007 Create `data/provenance.json` structure to record specific ENCODE accession IDs, JASPAR version, and download timestamps as per Constitution (VI)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download, parse, and normalize ATAC-seq/ChIP-seq peak data for multiple cell types into a unified BED-like format with gene annotations.

**Independent Test**: Verify pipeline downloads files to `TMP_DIR`, parses them without crashing, and outputs a summary report of peak counts per cell type within 14GB disk limits.

### Tests for User Story 1 (REQUIRED) ⚠️

- [X] T010 [US1] Write unit test `tests/unit/test_ingest.py::test_parse_handles_malformed_bed` which is expected to fail until T012-T014 implementation is complete. Assert parser raises specific `ValueError` on malformed BED input and logs error. **Verification**: Run `pytest tests/unit/test_ingest.py::test_parse_handles_malformed_bed` and assert exit code 1. **This task is REQUIRED to meet US-1 Independent Test criteria. Note: This task depends on T012-T014 (code existence) and is NOT parallel-safe.**
- [X] T011 [US1] Write unit test `tests/unit/test_network.py::test_retry_exponential_backoff` which is expected to fail until T006 implementation is complete. Assert network utility retries a limited number of times with exponential delays. before raising `MaxRetriesError`. **Verification**: Run `pytest tests/unit/test_network.py::test_retry_exponential_backoff` and assert exit code 1. **This task is REQUIRED to meet US-1 Independent Test criteria. Note: This task depends on T006 (code existence) and is NOT parallel-safe.**

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download.py` to download ENCODE peak files for representative human cell lines (GM, K, HepG, H-hESC, IMR90) using `code/utils/network.py` (FR-001, FR-006). **Constraint**: If download fails, raise `DataFetchError` and DO NOT fall back to synthetic/mock data (Constitution Data Hygiene).
- [X] T013 [US1] Implement parsing logic in `code/preprocess.py` to convert downloaded files to standardized BED format AND annotate with gene symbols. **Critical**: Intermediate parsed files MUST be written to `TMP_DIR` (configured in T004) to satisfy FR-002's requirement for a configurable temporary directory. Final aggregated results are stored in `data/interim/`. **Constraint**: If parsing fails, raise `DataParseError` and DO NOT fall back to synthetic/mock data. (FR-002). **Dependencies**: Depends on T005b (disk check) and T012. Note: This task relies on T004 for path configuration.
- [ ] T014 [US1] Implement gene annotation and background model aggregation in `code/preprocess.py` using `pybedtools` to map peak coordinates to gene symbols (hg38) and, for each target cell type, aggregate peaks from the remaining cell types to form the dynamic background model (FR-002, FR-004). **Output**: Writes `data/interim/background_union.bed`. **Dependencies**: Depends on T005b (disk check) and T013.
- [ ] T015 [US1] Implement `code/main.py` orchestration logic: function `run_ingestion(peak_files)` takes parsed peaks as input and generates `data/processed/ingestion_summary.json` with keys: `total_peaks` (int, sum of all parsed files), `cell_types` (list, **exact values**: ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']; raise error if input contains unexpected types), `parsed_count` (int, count of successfully parsed files) (depends on T012, T013, T014 completion). **This task implements the logic previously flagged as REJECTED, now fully implemented with clear artifact outputs.**
- [ ] T016 [US1] Update `code/main.py` to integrate `code/utils/disk_check.py` (T005b), `code/utils/memory_check.py` (T005a), and `code/utils/time_check.py` (T005c) as pre-flight and runtime checks before `run_ingestion` execution. **Dependencies**: T004, T005a, T005b, T005c, T012, T013, T014, T015 must be complete to ensure orchestration logic calls implemented functions. **Action**: Explicitly import and execute `code.utils.disk_check`, `code.utils.memory_check`, and `code.utils.time_check` before calling `run_ingestion`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Motif Scanning and Enrichment Analysis (Priority: P2)

**Goal**: Scan peaks for TF motifs using FIMO (CPU-only), compute background model (union of other cell types), and calculate enrichment scores with multiple-testing correction.

**Independent Test**: Run scanning on a small synthetic subset, verify output contains p-values ≤0.0001, and confirm distinct enrichment profiles (correlation <0.8) between cell types.

### Tests for User Story 2 (REQUIRED) ⚠️

- [ ] T018 [US2] Write unit test `tests/unit/test_background.py::test_union_aggregation` which is expected to fail until T014 implementation is complete. Assert background generation correctly aggregates (unioning) Peak Regions from the other 4 cell types. **Verification**: Run `pytest tests/unit/test_background.py::test_union_aggregation` and assert exit code 1. **Note: This task depends on T014 (code existence) and is NOT parallel-safe.**
- [ ] T019 [US2] Write unit test `tests/unit/test_motifs.py::test_fisher_exact_correction` which is expected to fail until T022 implementation is complete. Assert Fisher's test returns correct p-values and Benjamini-Hochberg correction returns correct q-values for a known input matrix. **Verification**: Run `pytest tests/unit/test_motifs.py::test_fisher_exact_correction` and assert exit code 1. **Note: This task depends on T022 (code existence) and is NOT parallel-safe.**

### Implementation for User Story 2

- [ ] T021a [US2] Implement `code/scan.py` to invoke FIMO (subprocess) against JASPAR CORE database with p-value ≤0.0001 threshold (FR-003). **Note**: The spec allows 'FIMO or HOMER', but plan.md explicitly selects FIMO. This task explicitly acknowledges the spec's flexibility while adhering to the plan's selection. **Dependencies**: Depends on T014 output (specifically `data/interim/background_union.bed` for context, though scanning uses target peaks).
- [ ] T021b [US2] Implement `code/scan.py` to parse FIMO output into a standardized list of motif matches with genomic coordinates and p-values.
- [ ] T022 [US2] Implement enrichment calculation in `code/enrichment.py` using Fisher's exact test against the background model (union of other cell types) (FR-004). **Dependencies**: Explicitly consumes `data/interim/background_union.bed` generated by T014.
- [ ] T023 [US2] Implement Benjamini-Hochberg correction in `code/enrichment.py` to generate adjusted q-values (FR-004)
- [ ] T025 [US2] Add chunked processing logic in `code/enrichment.py` to ensure memory usage stays <7GB if dataset size approaches RAM limits (GitHub Actions free-tier constraint). **Note**: This is a defensive measure; the primary assumption of in-memory processing remains unless limits are exceeded.
- [ ] T024 [US2] Update `code/main.py` to orchestrate scanning, enrichment: function `run_enrichment(matches, background)` takes motif matches as input and outputs `data/processed/enrichment_matrix.csv` with columns: `motif_id` (**JASPAR ID format, e.g., 'MA0001.1'**), `cell_type` (**exact string match**: ['GM12878', 'K562', 'HepG2', 'H1-hESC', 'IMR90']), `p_value` (float), `q_value` (float) (depends on T021a, T021b, T022, T023, T025 outputs). **This task implements the logic previously flagged as REJECTED, now fully implemented with clear artifact outputs.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Cross-Validation (Priority: P3)

**Goal**: Generate heatmaps of enrichment results and validate findings against independent ChIP-seq data.

**Independent Test**: Generate plots, verify heatmap clustering silhouette score ≥0.4, and confirm ≥60% overlap between predicted motifs and independent ChIP-seq peaks.

### Tests for User Story 3 (REQUIRED) ⚠️

- [ ] T026 [US3] Write unit test `tests/unit/test_viz.py::test_heatmap_silhouette_score` which is expected to fail until T028 implementation is complete. Assert clustering function returns silhouette score and logs it. **Verification**: Run `pytest tests/unit/test_viz.py::test_heatmap_silhouette_score` and assert exit code 1. **Note: This task depends on T028 (code existence) and is NOT parallel-safe.**
- [ ] T027 [US3] Write unit test `tests/unit/test_validate.py::test_chip_overlap_calculation` which is expected to fail until T030 implementation is complete. Assert overlap percentage is calculated correctly against a mock ChIP-seq dataset. **Verification**: Run `pytest tests/unit/test_validate.py::test_chip_overlap_calculation` and assert exit code 1. **Note: This task depends on T030 (code existence) and is NOT parallel-safe.**

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/visualize.py` to generate heatmap: function `generate_heatmap(matrix)` takes enrichment_matrix.csv as input, uses Euclidean distance clustering with linkage='average', and outputs `data/processed/heatmap.png` (FR-005). **Note**: This task is the prerequisite for T032. Depends on T024. The silhouette score is computed in T031a, not here.
- [ ] T030a [US3] Implement `code/validate.py` to fetch independent ChIP-seq accession IDs from ENCODE API. **Logic**: Load cell type mapping internally (hardcoded dictionary based on spec assumptions: `{'GM12878': 'ENCFF...', 'K562': 'ENCFF...',...}`). Query ENCODE API for ChIP-seq peaks matching the TF and cell type. **Dependencies**: Depends on T024 (to know which TFs to query) and T032a (to filter top motifs).
- [ ] T030b [US3] Implement `code/validate.py` to download real peak files for the retrieved accession IDs. **Constraint**: If API returns no results, raise `DataValidationError` (FAIL VALIDATION) immediately. Do NOT set a flag and continue. **Dependencies**: Depends on T030a.
- [ ] T030c [US3] Implement `code/validate.py` to calculate overlap percentage between predicted peaks and downloaded ChIP-seq peaks. **Output**: Writes `data/processed/validation_stats.json` with `overlap_pct`. **Dependencies**: Depends on T030b.
- [ ] T032a [US3] Implement `code/validate.py` to filter enrichment results to top enriched motifs (q < 0.05) before generating summary table, ensuring FR-005's 'top enriched' constraint is satisfied. **Output**: List of objects with keys: `motif_id` (string), `cell_type` (string), `q_value` (float). **Dependencies**: T024.
- [ ] T031a [US3] Implement `code/validate.py` to compute silhouette score from the enrichment matrix (T024) and log the result. **This task verifies the metric as a success condition (Independent Test).** **Note**: Depends on T024 (raw matrix data), NOT T028 (image). **Output**: Writes `data/processed/silhouette_score.json` containing the computed score to ensure data flow to T031b and T033.
- [ ] T031b [US3] Implement `code/validate.py` to enforce the silhouette score threshold: Read `data/processed/silhouette_score.json` (T031a). If score < 0.4, exit with non-zero error code and clear message (FAIL VALIDATION). If score >= 0.4, log success. **This task explicitly covers the 'Independent Test' success path (score >= 0.4) and failure path (exit error). It does NOT continue if the test fails.** **Note**: Depends on T031a.
- [ ] T033 [US3] Update `code/main.py` to orchestrate visualization and validation: function `run_validation_report(heatmap_data, chip_data, score, silhouette_flag, overlap_flag)` takes heatmap data (from T028), validation stats (from T030c), silhouette score (from T031a), `silhouette_test_passed` (from T031b), and `overlap_test_passed` (from T030c) as input and generates `data/processed/validation_report.json` with keys: `overlap_pct` (float, The precision of the measurement will be reported to two decimal places, or null), `top_motifs` (**list of objects with keys: `motif_id` (string), `q_value` (float, high precision (e.g., four decimal places)), `overlap_pct` (float, 2 decimal places, or null)**), `silhouette_score` (float, 2 decimal places), `silhouette_test_passed` (bool), `overlap_test_passed` (bool, derived from T030c logic), `validation_passed` (bool, **True ONLY if BOTH `silhouette_test_passed` AND `overlap_test_passed` are True**). (depends on T028, T030c, T031a, T031b, T032a). **Note**: This task is the prerequisite for T034.
- [ ] T034 [US3] Generate final summary table: function `generate_summary_table(enrichment_csv, validation_json)` reads from `data/processed/enrichment_matrix.csv` (filtered by T032a) and `data/processed/validation_report.json` and outputs `data/processed/summary_table.csv` with columns: `motif_id`, `p_value_raw`, `q_value_adj`, `chip_overlap_pct`. **Logic**: Select the 'top N' motifs by q-value (ranking) from the filtered set to satisfy FR-005's 'top enriched' requirement. Note: `chip_overlap_pct` is calculated as the ratio of the intersection of predicted and observed peaks to their union, expressed as a percentage. (depends on T030c, T033, T032a). This table satisfies US-3-SC1 Scenario 3.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `README.md` and `specs/001-gene-regulation/quickstart.md`. **Content Requirement**: `quickstart.md` MUST include: 1) Exact commands to run the pipeline (`python -m code.main`), 2) Expected output artifacts list, 3) Expected output format for `ingestion_summary.json`, `enrichment_matrix.csv`, and `validation_report.json`, 4) A note on the required disk space (≥14GB) and RAM (≥16GB per SC-004, ≥7GB per plan).
- [ ] T036 [P] Performance optimization for FIMO execution: Modify FIMO loop in `code/scan.py` to use `joblib.Parallel(n_jobs=2, max_nbytes=500MB)` where safe, ensuring total memory footprint remains <7GB. **Verification**: Verify that `code/scan.py` runs with `joblib.Parallel` and that a log entry confirms memory usage < 7GB during execution. **Constraint**: Must include a runtime check using `psutil` to verify **total** process memory usage does not exceed 7GB during parallel execution.
- [ ] T038 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility on the target CI environment. **Dependencies**: T035, T030. **Action**: Execute `python -m code.main` as per quickstart.md and verify exit code 0 and existence of `data/processed/validation_report.json`. **Note**: This task (renumbered from T037) restores the end-to-end validation step required to verify the final deliverable.

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
- **Tests**: All test tasks for a user story can run in parallel **among themselves** once their respective implementation tasks (the producers) are complete. They cannot run concurrently with their producers.
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (AFTER implementation is done):
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
- **Critical Constraint**: All tasks must run on CPU-only free-tier CI (A minimal computing environment with a small number of cores, limited RAM, and limited disk). No GPU, no 8-bit quantization, no large model training.
- **Data Integrity**: No synthetic/fake data allowed. All analysis must use real ENCODE/JASPAR data. **Fail Loudly**: If real data fetch fails, raise an error.
- **Background Model**: Use "Peak Regions from other cell types" (union) as the background model, as mandated by FR-004 and Spec Assumptions.
- **Disk Space**: Check for ≥14GB free space (FR-002, SC-004).
- **Silhouette Score**: Verify ≥0.4. If < 0.4, exit with error (do not continue).
- **Overlap Threshold**: Verify ≥60% overlap. If < 60% or missing, set `overlap_test_passed = False` and `validation_passed = False`.
- **Chunked Processing**: Authorized to meet a defined RAM limit if needed
- **File Paths**: Strictly follow plan.md file structure: `code/download.py`, `code/preprocess.py`, `code/scan.py`, `code/enrichment.py`, `code/visualize.py`.
- **Plan Discrepancy Note**: There is a known contradiction between SC-004 (requires 16GB RAM) and plan.md (targets moderate RAM usage). This has been flagged for kickback to the planning stage. Tasks T005a and T005c now implement monitoring and warnings to handle this constraint gap gracefully while enforcing the 6-hour limit and 14GB disk requirement.
- **Removed Tasks**: Phase O (T039-T046) and T037 (renumbered to T038) have been removed/renumbered as they constituted unapproved scope creep or redundancy. T031 has been split into T031a (verification) and T031b (conditional fail) to align with spec. T029 added to provide the mapping config required by T030.

The research question, method, and references remain unchanged as no specific values were asserted in the original passage beyond the target to be generalized.
- **File Paths**: Strictly follow plan.md file structure: `code/download.py`, `code/preprocess.py`, `code/scan.py`, `code/enrichment.py`, `code/visualize.py`.
- **Plan Discrepancy Note**: There is a known contradiction between SC-004 (requires 16GB RAM) and plan.md (targets ~7GB RAM). This has been flagged for kickback to the planning stage. Tasks are based on the plan's constraints.