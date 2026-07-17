# Tasks: Cosmic Ray Anisotropy Solar‑Cycle Modulation

**Input**: Design documents from `/specs/121-cosmic-ray-anisotropy-solar-cycle/`
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-121-investigating-the-relationship-between-c/`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (no CUDA/GPU libs)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup directory structure: `data/raw`, `data/processed`, `data/results`, `reports`, `code/src`
- [X] T005 [P] Implement `src/data_loader.py` for downloading IceCube and Auger data with SHA-256 checksum verification
- [X] T006 [P] Implement `src/solar_proxies.py` to fetch NOAA NGDC indices (sunspot, solar wind, IMF) with retry logic, specifically implementing **exponential backoff** strategy and a hard limit of **3 attempts** per request as required by FR-002
- [ ] T007 Create base data entities: `EventDataset` and `SolarProxySeries` in `src/entities.py`
- [ ] T008 Configure `src/config.py` for environment variables and default bin size (27 days)
- [ ] T009 Setup `src/utils.py` for logging, error handling, and UTC Julian date conversion

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End‑to‑end Data Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download IceCube/Auger/NOAA data, bin events, generate HEALPix maps, and output dipole time-series CSV.

**Independent Test**: Execute `run_all.sh` on a fresh runner; verify data download, HEALPix map generation (Nside 64), and CSV output with ≥ 95% expected rows.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for data download integrity in `tests/contract/test_data_download.py`
- [ ] T012 [P] [US1] Integration test for full pipeline flow in `tests/integration/test_pipeline_flow.py` <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `src/binning.py` to convert timestamps to UTC Julian dates and bin events into configurable intervals (FR-010)
- [ ] T013 [P] [US1] Implement `src/anisotropy.py` to generate HEALPix maps at an appropriate resolution and fit spherical harmonic coefficients (ℓ≤2) <!-- ATOMIZE: requested -->
- [ ] T014 [US1] Implement `src/pipeline.py` to orchestrate download, binning, and map generation per interval <!-- ATOMIZE: requested -->
- [ ] T015 [US1] Implement `run_pipeline.sh` wrapper script that calls `src/pipeline.py` with `--bin-size` argument
- [ ] T016 [US1] Add logic to handle partial intervals (last bin) and explicitly **set the `partial_interval` boolean flag to `true` in the output CSV** if the final interval is shorter than the bin size, as required by FR-003
- [ ] T017 [US1] Implement `run_all.sh` orchestrator that calls `run_pipeline.sh`, logs "Data acquisition completed", and **handles missing sources by logging a warning and proceeding with available data** (e.g., Auger-only) to ensure the output CSV contains ≥90% of expected rows, satisfying US-1 Acceptance Scenario 2
- [ ] T018 [US1] Create `data/results/dipole_timeseries.csv` with columns: `interval_start, dipole_amp, dipole_phase, quad_amp, partial_interval`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation & Significance (Priority: P2)

**Goal**: Perform Lomb-Scargle, block-bootstrap, and Monte-Carlo shuffle to quantify correlation significance.

**Independent Test**: Run `analyze_correlation.py` on the CSV from US1; verify periodogram plots, correlation coefficients with p-values, and FAP calculation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for statistical methods in `tests/contract/test_stats.py`
- [X] T020 [P] [US2] Integration test for correlation analysis in `tests/integration/test_correlation.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `src/stats.py` with Lomb-Scargle periodogram function (using `astropy.timeseries`)
- [ ] T022 [US2] Implement block-bootstrap resampling in `src/stats.py` with **conditional logic**: if the number of independent blocks is < 30, reduce block length to **1 × bin_size**; otherwise use **2 × bin_size**, ensuring compliance with FR-005
- [ ] T023 [US2] Implement Monte-Carlo shuffle test (sufficient permutations) shuffling solar proxy series relative to anisotropy, **and ensure the block-bootstrap logic in T022 is fully integrated here** with the conditional fallback (if blocks < 30, use 1x bin_size) to satisfy FR-005
- [ ] T024 [US2] Implement Bonferroni correction logic (α=0.0017) and "positive result" flagging in `src/stats.py`
- [~] T025 [US2] Create `analyze_correlation.py` entry point to run all statistical tests per detector (IceCube, Auger)
- [~] T026 [US2] Generate PDF output with periodogram plots, correlation heatmaps, and FAP reports
- [ ] T027 [US2] **Generate synthetic dataset with injected known correlation signal**: Implement `src/validation.py` to create a simulated dataset with a known ground truth correlation (specific amplitude and phase) between anisotropy and solar proxy, **saving the output to `data/synthetic/validation_input.csv`**, serving as the input for the blind validation step (FR-011)
- [ ] T028 [US2] Implement blind validation in `src/validation.py` using the synthetic dataset generated in T027; **write metrics (fp_rate, power) to `data/results/validation_metrics.json`** to verify FR-011 requirements. The JSON must contain keys `fp_rate` (float) and `power` (float).
- [X] T029 [US2] **Add an assertion in `tests/unit/test_validation.py` that raises an error if `fp_rate > 0.05` or `power < 0.8`** using the metrics from T028, ensuring the system fails the build if thresholds are not met. This task enforces the verification step required by FR-011 and SC-008.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproducible Reporting & Packaging (Priority: P3)

**Goal**: Generate LaTeX report, figures, and bundle environment specs.

**Independent Test**: Invoke `make_report.sh`; confirm `report.pdf` compiles, figures are saved, and `requirements.txt` is present.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Contract test for report generation in `tests/contract/test_report.py`
- [X] T031 [P] [US3] Integration test for full report build in `tests/integration/test_report_build.py`

### Implementation for User Story 3

- [X] T032 [P] [US3] Create LaTeX template `reports/report_template.tex` with sections for methods, results, and figures
- [~] T033 [US3] Implement `make_report.sh` to compile `report.pdf` using `pdflatex` and copy figures
- [X] T034 [US3] Add script to generate `requirements.txt` with exact versions of all Python packages
- [~] T035 [US3] Implement figure generation scripts for time-series, heatmaps, and periodograms
- [X] T036 [US3] Add error handling for missing `requirements.txt` with clear abort message
- [~] T037 [US3] Ensure report includes statement on hypothesis support based on Bonferroni-corrected p-values

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Configurable Temporal Binning (Priority: P2)

**Goal**: Enable experimentation with different bin sizes (14, 27, 54 days).

**Independent Test**: Run `run_all.sh --bin-size 14` and `--bin-size 54`; verify CSV row counts and log messages.

### Implementation for User Story 4

- [ ] T042 [US4] Verify `src/data/preprocess.py` correctly bins events into non-overlapping intervals of specified length (via T018 argument)
- [ ] T043 [US4] Add logging in `src/data/preprocess.py` to record "Using bin size: X days" and validate bin size constraints (a lower-bound duration to 60 days)

**Checkpoint**: Bin-size sensitivity analysis is fully supported

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T047 [P] Update `docs/quickstart.md` with new pipeline steps and bin-size options
- [ ] T048 [P] Update `README.md` with installation and usage instructions
- [ ] T049 [P] Refactor `src/data/download.py` and `src/analysis/significance.py` to reduce cyclomatic complexity to < 10
- [ ] T050 [P] Optimize `src/data/preprocess.py` to ensure memory usage < 6GB during full -year dataset processing
- [ ] T051 [P] Additional unit tests for edge cases (missing data, leap seconds) in `tests/unit/`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (CSV)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 outputs
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 and US2

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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data download integrity in tests/contract/test_data_download.py"
Task: "Integration test for full pipeline flow in tests/integration/test_pipeline_flow.py"

# Launch all models for User Story 1 together:
Task: "Create event_dataset model in src/data/models/event_dataset.py"
Task: "Create solar_proxy_series model in src/data/models/solar_proxy_series.py"
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
 - Developer B: User Story 2 (Statistics)
 - Developer C: User Story 3 (Reporting)
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
- **Data Feasibility**: All tasks must run on CPU-only CI with limited computational resources.. No GPU/CUDA.
- **Real Data**: All tasks must use real data sources (IceCube HuggingFace, NOAA NGDC). No fabrication.
- **Ordering**: Data download tasks (T013-T014) MUST precede preprocessing (T015-T017). Analysis (T023-T031) MUST follow pipeline completion.
- **Spec vs. Plan**: Tasks strictly follow Spec (FR-005) for block length (2 × bin_size). Plan's "Stationary Bootstrap" is noted as optional.
- **Fallback**: T026/T026b ensures FR-005 safety valve is implemented.