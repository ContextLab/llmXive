# Tasks: Assessing the Impact of Network Centrality on Age‑Related Cognitive Decline

**Input**: Design documents from `/specs/001-assessing-network-centrality-feature/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `docs/`) <!-- SKIPPED: YAML+regex parse failed (while scanning a simple key
 in "<unicode string>", line 4, column 1:
 Furthermore, the constraint "Rea...
 ^
could not find expected ':'
 in "<unicode string>", line 6, column 1:
 Since I cannot access the real A...
 ^) -->
- [ ] T002 Initialize Python 3.10 project with `requirements.txt` (nibabel, nilearn, networkx, pandas, scikit-learn, statsmodels, matplotlib, seaborn, reportlab)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup environment configuration management (load ADNI credentials from `.env`, validate presence of required keys)
- [ ] T005 [P] Implement logging infrastructure (machine-readable logs per FR-011 in `logs/pipeline.log`)
- [ ] T006 [P] Create base data models/entities (Participant, ImagingSession, CentralityMetrics, CognitiveScore, RegressionResult) in `code/data_models.py`
- [X] T006b [P] Create `code/config/network_rois.json` containing explicit lists of ROI indices for DMN and FPN networks as per the AAL atlas definition.
- [~] T007 Setup directory structure for `data/raw/`, `data/processed/`, `data/analysis/`, `outputs/` with `.gitignore` rules for large files
- [~] T008 Implement utility functions for CSV reading/writing and checksum validation (FR-001, Data Hygiene)
- [X] T008b [P] Generate `docs/sync_impact_report.md` documenting the Constitution (Bonferroni) vs. Spec (FDR) conflict and the ratified decision to follow the Spec, satisfying Constitution Principle V (Versioning Discipline).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Network Centrality for a Cohort (Priority: P1) 🎯 MVP

**Goal**: Download ADNI rs-fMRI, preprocess (CPU-only), build connectivity matrices, and extract centrality metrics for DMN/FPN.

**Independent Test**: Execute the pipeline on a subset of participants and verify that centrality tables are produced for *all* AAL ROIs, with ≥ 90% of participants having non-missing values for each metric.

### Implementation for User Story 1

- [ ] T009 [US1] Implement ADNI authentication and downloader in `code/download/adni_downloader.py` (FR-001) <!-- FAILED: unspecified -->
 - Fetch rs-fMRI NIfTI files and clinical CSVs for specified participant IDs via the **LONI IDGK portal API** using `--user`/`--pass` flags.
 - **Input**: Read participant IDs from `data/raw/participant_list.csv` or accept `--ids` CLI argument.
 - **Validation**: Explicitly check for the presence of TMT-A and WAIS-R columns in the fetched clinical CSVs; raise error if missing.
 - Handle authentication errors and missing data gracefully. **Note**: If ADNI credentials are unavailable, the pipeline MUST abort for the primary run; mock data is only for unit/integration tests.
- [X] T010 [US1] Implement QC and preprocessing pipeline in `code/preprocess/fMRI_pipeline.py` (FR-002, FR-013)
 - **Production Path**: Use Docker container with FSL/AFNI for motion correction, slice-time correction, MNI normalization (mm resampling), and band-pass filtering (low-frequency cutoff).
 - **CI/Simulation Path**: Generate mock NIfTI files in `data/processed/` for N=5 participants that **simulate the output of the full preprocessing pipeline** (including motion correction logic) to ensure schema compatibility with downstream steps. Do NOT skip motion correction.
 - Implement Framewise Displacement (FD) calculation.
 - Exclude participants with mean FD > 0.5mm or >20% volumes > 0.5mm [UNRESOLVED-CLAIM: c_760ba2fd — status=not_enough_info]; log exclusions to `data/analysis/qc_log.json`.
 - Output preprocessed NIfTI files.
- [ ] T011 [US1] Implement connectivity matrix construction in `code/centrality/connectivity.py` (FR-003)
 - Load AAL atlas (read-only) and extract mean BOLD time series for a set of cortical and subcortical regions of interest.
 - Compute a **standard Pearson correlation** matrix per participant (no percentile threshold).
- [ ] T012 [US1] Implement centrality metric calculation in `code/centrality/metrics.py` (FR-004)
 - Calculate degree, betweenness, and closeness centrality for every ROI using `networkx`.
 - Store raw ROI-level metrics.
- [ ] T013 [US1] Implement main US1 orchestration script `code/main_us1.py`
 - **Dependency**: Waits for completion of T009, T010, T011, and T012.
 - Chain: Download -> QC/Preprocess -> Connectivity -> Centrality.
 - Enforce SC-001 (≥90% complete tables) and SC-002 (valid matrices).
 - Generate `data/analysis/centrality_metrics.csv` (containing raw ROI metrics).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Relate Centrality to Cognitive Scores (Priority: P2)

**Goal**: Merge data, run hierarchical linear regression with covariates, apply FDR correction, and validate assumptions.
**⚠️ Dependency**: This phase strictly follows Phase 3 (US1) completion. US2 cannot run in parallel with US1.

### Implementation for User Story 2

- [ ] T014 [US2] Implement QC Count and Threshold Validation in `code/analysis/qc_validator.py` (FR-014)
 - **Input**: Read `data/analysis/qc_log.json` generated by T010.
 - Calculate the number of **usable participants** (post-QC exclusions).
 - Verify sample size ≥ 85 [UNRESOLVED-CLAIM: c_443986d6 — status=not_enough_info].
 - **Abort** with clear error message if usable count < 85.
 - Output `data/analysis/qc_summary.json` with the usable count.
- [ ] T015 [US2] Implement data merging and cleaning in `code/analysis/data_merger.py` (FR-006, FR-012)
 - **Input**: Merge `data/analysis/centrality_metrics.csv` (from T013) with cognitive scores from `data/raw/clinical_data.csv`.
 - Exclude participants with missing cognitive scores; log omissions.
 - Generate `data/analysis/merged_dataset.csv`.
- [ ] T016 [US2] Implement centrality aggregation and regression engine in `code/analysis/regression.py` (FR-005, FR-007, FR-016)
 - **Dependency**: T006b (network_rois.json).
 - **Mapping**: Explicitly load DMN and FPN ROI lists from `code/config/network_rois.json` to calculate per-network means.
 - Calculate per-network means (DMN, FPN) and global means for each metric.
 - **Output Schema**: **Append** per-network mean columns (e.g., `degree_DMN`, `degree_FPN`) to the existing `data/analysis/centrality_metrics.csv` (or create a derived file if schema separation is preferred, but must preserve raw data).
 - Fit separate linear models for each (Centrality Metric × Cognitive Domain) pair (3×3=9 models) [UNRESOLVED-CLAIM: c_b59e55dd — status=not_enough_info].
 - Control for covariates.
 - Calculate β, SE, p-values, partial-r, and VIF.
 - Compute Pearson correlation matrix among centrality metrics.
- [ ] T017 [US2] Implement statistical diagnostics and FDR correction in `code/analysis/diagnostics.py` (FR-008, FR-009, FR-015)
 - Apply Benjamini-Hochberg FDR correction to the p-values; output q-values.
 - Check assumptions: Linearity, Normality (Shapiro-Wilk), Homoscedasticity (Breusch-Pagan), Independence.
 - Flag VIF > 5 [UNRESOLVED-CLAIM: c_213b933f — status=not_enough_info] and assumption violations (warnings only, do not halt).
- [ ] T018 [US2] Implement main US2 orchestration script `code/main_us2.py`
 - Chain: QC Validation (T014) -> Merge (T015) -> Regression (T016) -> Diagnostics (T017).
 - Generate `data/analysis/regression_results.csv` and `data/analysis/diagnostics.json`.
 - Enforce SC-003 (FDR q-values reported) and SC-006 (diagnostics produced).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (with US2 dependent on US1 output)

---

## Phase 5: User Story 3 - Visualize and Export Findings (Priority: P3)

**Goal**: Generate a concise PDF report with plots, heatmaps, and tables.
**⚠️ Dependency**: This phase strictly follows Phase 4 (US2) completion. US3 cannot start until US2 is done.

### Implementation for User Story 3

- [ ] T019 [US3] Implement visualization helpers in `code/viz/plotting.py`
 - Create scatter plots (Centrality vs. Cognitive Score).
 - **Output**: Save intermediate plots to `outputs/viz/scatter_*.png` and `outputs/viz/heatmap_*.png`.
 - Create table visualization for FDR-adjusted q-values.
- [ ] T020 [US3] Implement report generator in `code/viz/report_generator.py` (FR-010)
 - Assemble plots and tables into a PDF using `reportlab` or `matplotlib` + `PIL`.
 - Include QC summary (exclusions, sample size).
 - Ensure file size ≤ 5 MB [UNRESOLVED-CLAIM: c_be1fedbb — status=not_enough_info] (SC-004).
 - Handle missing backend errors gracefully (FR-010 scenario 2).
- [ ] T021 [US3] Implement main US3 orchestration script `code/main_us3.py`
 - Trigger report generation upon completion of US2.
 - Save final report to `outputs/final_report.pdf`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T022 [P] Write unit tests for centrality calculation logic (`tests/unit/test_centrality.py`)
- [ ] T023 [P] Write unit tests for regression logic and FDR correction (`tests/unit/test_regression.py`)
- [ ] T024 [P] Write integration test for full pipeline flow (mock data) (`tests/integration/test_pipeline.py`)
- [ ] T025a [P] Refactor `code/preprocess/fMRI_pipeline.py` to reduce cyclomatic complexity to < 10.
- [ ] T025b [P] Remove all TODO comments from `code/`.
- [ ] T026a [P] Optimize connectivity matrix calculation to use chunked processing for memory efficiency.
- [ ] T026b [P] Run integration test on N=20 [UNRESOLVED-CLAIM: c_5b10a0e7 — status=not_enough_info] and record runtime in `outputs/perf_metrics.json` to verify < 4 hour constraint.
- [ ] T027 [P] Documentation updates: Add `quickstart.md` and update `README.md` with execution instructions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2)
- **User Story 2 (Phase 4)**: **Strictly depends on Phase 3 (US1) completion**. Cannot run in parallel with US1.
- **User Story 3 (Phase 5)**: **Strictly depends on Phase 4 (US2) completion**. Cannot run in parallel with US2.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Requires output of US1 (`data/analysis/centrality_metrics.csv`) and `data/raw/clinical_data.csv`.
- **User Story 3 (P3)**: Requires output of US2 (`data/analysis/regression_results.csv`).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, **US1 can start**.
- **US2 and US3 cannot start in parallel with US1** due to data dependencies. They must wait for their respective upstream phases.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel **only if** mock data is available and the dependency chain is explicitly managed (not recommended for this project).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify centrality CSV generation)
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
 - Developer B: **Wait** for US1 output to start US2 (or use mock data with explicit synchronization)
 - Developer C: **Wait** for US2 output to start US3
3. Stories complete and integrate independently

---

## Governance Note: Constitution vs. Spec Contradiction

**Issue**: The Constitution (Principle VII) mandates Bonferroni correction, while the Spec (FR-008) and Plan mandate Benjamini-Hochberg FDR correction.
**Status**: This project follows the **Spec (FDR)** as the primary source of truth for the implementation.
**Action Required**: A formal "Sync Impact Report" has been generated in `docs/sync_impact_report.md` (Task T008b) to resolve this contradiction per Constitution Section V. The current implementation documents this conflict here to satisfy the "Verified Accuracy" and "Reproducibility" principles by explicitly acknowledging the deviation from the Constitution's default rule.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All preprocessing tasks must use CPU-only methods (nilearn, downsampling) as no GPU is available on the runner.
- **Data Constraint**: Tasks must use real ADNI data or validated mock data for CI; no synthetic fabrication of cognitive scores.
- **Data Source Constraint**: T009 must explicitly define the URL or API endpoint for ADNI data retrieval; "download from ADNI" is insufficient without a specific mechanism (e.g., `adni_downloader.py` using `requests` to the LONI IDGK portal with `--user`/`--pass` flags).
- **Power Constraint**: T014 must strictly enforce the N ≥ 85 threshold before proceeding to regression; if N < 85, the pipeline must exit with a specific error code (e.g., 2) and a message citing "Insufficient Power for Regression (N < 85)".
- **Preprocessing Constraint**: T010 must generate mock data that mimics the output of the full preprocessing pipeline (including motion correction) to ensure FR-002 compliance in all execution paths.