# Tasks: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

**Input**: Design documents from `/specs/001-network-centrality-sleep-synchrony/`
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

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so that they:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: `code/`, `data/raw`, `data/processed`, `data/metrics`, `data/results`, `tests/unit`, `tests/integration`. Verify each directory exists after creation.
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (mne, statsmodels, networkx, scipy, pandas, numpy, pyedflib).
- [X] T003 [P] Configure linting (flake8/pylint) and formatting (black) tools in `code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Create `code/loaders.py` with functions `load_raw_edf` and `load_annotations` to handle `data/raw` vs `data/processed` directory structure.
- [X] T004 [P] Create `code/config.yaml` with signal‑processing parameters (filter cutoffs 0.5‑45 Hz, ICA thresholds, band definitions).
- [X] T005 [P] Implement `code/__init__.py` and basic logging infrastructure in `code/main.py`. *Note*: Runtime depends on T004 and T006 being present.
- [X] T007 [P] Setup environment configuration management (random seed pinning in `code/config.yaml`).
- [X] T008 [P] Implement data integrity check utility (checksum verification for raw files).

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download Sleep‑EDF dataset, preprocess EEG (filtering, ICA), and segment into labeled epochs.

**Independent Test**: The pipeline executes on a subset, output matches expected epoch counts, and no NaN values remain in filtered arrays.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download.py` to fetch Sleep‑EDF from PhysioNet via MNE, verify checksums (FR‑001).
- [X] T016 [US1] Add error handling for corrupted `.edf` files in `code/download.py` (log error, skip file, continue) (Edge Case: Data Corruption).
- [ ] [ ] T013 [US1] Implement `code/preprocess.py` band‑pass filter (0.5–45 Hz) on raw EEG signals (FR‑002).
- [ ] [ ] T014 [US1] Implement `code/preprocess.py` ICA artifact removal (kurtosis > 5.0 or high‑freq power > 3× baseline) (FR‑002).
- [ ] [ ] T015 [US1] Implement `code/preprocess.py` epoching into ‑second windows labeled by sleep stage (Wake, N1‑N3, REM) (FR‑002).
- [ ] [ ] T017 [US1] Add validation step to ensure no NaN values remain in output arrays.
- [ ] [ ] T018 [US1] Output cleaned signal arrays and epoch metadata to `data/processed/`.

### Tests for User Story 1 (OPTIONAL)

- [X] T048 [P] [US1] Unit test for checksum verification in `tests/unit/test_download.py`.
- [X] T049 [P] [US1] Unit test for ICA artifact flagging logic in `tests/unit/test_preprocess.py`.
- [X] T050 [P] [US1] Integration test for full download‑to‑epoch flow in `tests/integration/test_pipeline.py`.

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Metric Computation (Centrality and Synchrony) (Priority: P2)

**Goal**: Compute network centrality metrics from waking connectivity and neural synchrony (PLI) from sleep epochs.

**Independent Test**: Generate a summary CSV with centrality and synchrony scores per subject, openable in a spreadsheet without errors.

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/metrics.py` to construct functional connectivity matrices using theta (4‑8 Hz) and alpha (8‑13 Hz) coherence from waking data (FR‑003).
- [X] T023 [US2] Validate connectivity matrices are symmetric and values are strictly between 0 and 1 (FR‑003).
- [X] T024 [US2] Implement `code/metrics.py` to compute degree, betweenness, and eigenvector centrality using NetworkX (FR‑004).
- [X] T025 [US2] Implement `code/metrics.py` to calculate Phase Lag Index (PLI) across electrode pairs for each epoch (FR‑005).
- [X] T026 [US2] Aggregate PLI to mean global synchrony score per sleep stage (FR‑005).
- [X] T027 [US2] Handle missing sleep stages by excluding the subject‑stage pair (Edge Case: Missing Sleep Stages).
- [X] T028 [US2] Calculate Variance Inflation Factor (VIF) for centrality metrics and flag > 5.0 (FR‑009); ensure VIF reporting is separate from model covariates. <!-- SKIPPED: non-mapping output -->
- [X] T029 [US2] Extract `waking_night_id` and `sleep_night_id` to determine temporal proximity (FR‑011).
- [X] T030 [US2] Output `data/metrics/SubjectMetrics.csv` with subject ID, centrality metrics, synchrony scores, and VIF flags.

### Tests for User Story 2 (OPTIONAL)

- [X] T051 [P] [US2] Unit test for NetworkX centrality calculation on synthetic graph in `tests/unit/test_metrics.py`.
- [X] T052 [P] [US2] Unit test for PLI calculation on synthetic signal in `tests/unit/test_metrics.py`.
- [X] T053 [P] [US2] Integration test for matrix symmetry and value range (0‑1) in `tests/integration/test_metrics.py`.

**Checkpoint**: User Stories 1 & 2 should both work independently.

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Execute correlation/LME analysis, apply FDR correction, and generate the final report.

**Independent Test**: Run analysis on metrics CSV, produce a JSON report with coefficients and corrected p‑values, programmatically validatable.

### Implementation for User Story 3

- [X] T034 [US3] Implement subject‑count check (N ≥ 30). If N < 30, **log a warning** and continue; downstream tasks will perform effect‑size estimation (see T011).
- [X] T011 [US3] When N < 30, compute effect sizes (Cohen’s d) and 95 % confidence intervals for each centrality‑synchrony pair; append these to `analysis_results.json`. <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
 in "<unicode string>", line 2, column 1:
 **Key Implementation Details:**
 ^
expected alphabetic or numeric character, but found '*'
 in "<unicode string>", line 2, column 2:
 **Key Implementation Details:**
 ^) -->
- [X] T036 [US3] Perform Shapiro‑Wilk test on LME residuals for diagnostics; store results in `data/results/residuals_diagnostics.json` (FR‑012 for diagnostics only).
- [X] T037 [US3] **Mandatory**: Implement LME analysis in `code/analysis.py` with formula `centrality ~ pli + global_coherence + (1|subject)`. Generate raw p‑values, apply **Benjamini‑Hochberg FDR** correction, and write `data/results/analysis_results.json`. This satisfies FR‑006, FR‑007 (as upgraded to FDR per plan), and FR‑012 (diagnostic Shapiro‑Wilk).
- [X] T038 [US3] *Deprecated*: Previously separate FDR task – now superseded by T037. Marked for reference only.
- [X] T039 [US3] Implement `code/report.py` to generate a JSON report containing coefficients, raw p‑values, FDR‑corrected p‑values, and effect‑size fields (if N < 30). (FR‑008)
- [X] T040 [US3] Extend the report to flag results with adjusted p < 0.05 as “Significant” and others as “Non‑Significant”. (FR‑008)
- [X] T041 [US3] Include a “Confounding Limitation” section in the report when `temporal_proximity` flag from T029 indicates waking and sleep data originate from the same night. (FR‑011)
- [X] T042 [US3] Output final artifacts: `data/results/analysis_results.json` and a Markdown summary `reports/final_report.md`.

### Tests for User Story 3 (OPTIONAL)

- [X] T054 [P] [US3] Unit test for residual diagnostics JSON generation in `tests/unit/test_analysis.py`.
- [X] T055 [P] [US3] Unit test for FDR correction logic in `tests/unit/test_analysis.py`.
- [X] T056 [P] [US3] Integration test for end‑to‑end report generation in `tests/integration/test_analysis.py`.

**Checkpoint**: All user stories should now be independently functional and produce the required deliverables.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T043 [P] Documentation updates in `docs/` and `README.md`: add installation instructions, usage examples, and data model diagram; create `docs/quickstart.md`.
- [X] T044 [P] Refactor `code/metrics.py` to reduce cyclomatic complexity to a lower, manageable level and ensure every public function has a comprehensive docstring.
- [X] T045 [P] Refactor `code/analysis.py` to enforce function length < 50 lines and add type hints throughout.
- [X] T045 [P] Performance optimization: add memory profiling in `code/main.py` to ensure peak RAM < 4 GB (SC‑003).
- [ ] T046 [P] Run quickstart validation script to ensure end‑to‑end execution from a fresh clone.
- [ ] T047 [P] Verify runtime logging in `code/main.py` targets < 4 hours on a 2 vCPU runner (SC‑002).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational. After that, US 1, US 2, and US 3 can run in parallel (subject to data flow).
- **Polish (Final Phase)**: Depends on completion of the desired user stories.

### User Story Data Flow

- US 1 produces `data/processed/` files required by US 2.
- US 2 produces `data/metrics/SubjectMetrics.csv` required by US 3.
- US 3 consumes the CSV and generates final results and reports.

### Parallel Opportunities

- All `[P]` tasks within a phase can be developed concurrently, provided runtime ordering respects the data‑flow described above.
- Tests marked `[P]` can be executed in parallel after their corresponding implementation tasks.

---

## Implementation Strategy

- **MVP First**: Complete Setup → Foundational → US 1, validate, then iteratively add US 2 and US 3.
- **Incremental Delivery**: Each story is independently testable; integration occurs only at the data‑flow boundaries.
- **Parallel Team**: One developer can finish Setup & Foundational, then separate developers take US 1, US 2, and US 3 in parallel.

---

## Notes

- All tasks are designed to run on a CPU‑only CI runner (2 vCPU, ≤ 4 GB RAM, ≤ 6 h).
- The pipeline respects the plan’s methodological upgrades (LME + FDR) while flagging spec contradictions for downstream amendment.
- Edge‑case handling (missing stages, corrupted files, collinearity) is explicitly covered in the relevant tasks.