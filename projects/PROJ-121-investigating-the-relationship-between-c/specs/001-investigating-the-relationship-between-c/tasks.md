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

- [ ] T001 Create project structure per implementation plan (`src/`, `data/`, `tests/`, `output/`)
- [ ] T002 Initialize Python 3.11 project with dependencies: `astropy`, `healpy`, `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `requests`, `lxml`, `jinja2`, `pyyaml`, `statsmodels`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools
- [ ] T004 [P] Create `requirements.txt` with pinned versions ensuring CPU-only execution (no CUDA)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement `src/utils/checksum.py` for SHA-256 verification of downloaded files
- [ ] T006 Implement `src/utils/logging.py` for structured logging with timestamps and log levels
- [ ] T007 Create `src/data/models/event_dataset.py` and `src/data/models/solar_proxy_series.py` entities
- [ ] T008 Implement `src/data/models/anisotropy_interval.py` entity with schema validation
- [ ] T009 Create `src/utils/config.py` to handle `--bin-size` argument (7-60 days, A default value will be established for the parameter, pending empirical determination during the implementation phase.) and validate constraints
- [ ] T010 Setup `data/raw/`, `data/processed/`, `data/results/`, and `output/` directory structure
- [ ] T019 [P] [US1] Implement `src/data/preprocess.py` sampling logic: if dataset > 7GB RAM, apply energy threshold (>10 TeV) or random sampling to fit memory limits (Prerequisite for T015/T016)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End‑to‑end Data Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download IceCube/Auger/NOAA data, bin events, generate HEALPix maps, and output dipole time-series CSV.

**Independent Test**: Execute `run_all.sh` on a fresh runner; verify data download, HEALPix map generation (Nside 64), and CSV output with ≥ 95% expected rows.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for data download integrity in `tests/contract/test_data_download.py`
- [ ] T012 [P] [US1] Integration test for full pipeline flow in `tests/integration/test_pipeline_flow.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `src/data/download.py` with retry logic (multiple retries, exponential back-off) for IceCube (HuggingFace), Auger (fallback if unavailable), and NOAA NGDC; **explicitly invoke SHA-256 checksum verification for all downloaded files** as per FR-001, logging success or failure for each source
- [ ] T014 [P] [US1] Implement `src/data/solar_proxy.py` to fetch and align daily sunspot, solar wind, and IMF indices; **explicitly invoke SHA-256 checksum verification** for any cached or downloaded proxy data files as per FR-002
- [ ] T018 [US1] Implement `src/cli/run_all.sh` to orchestrate download, preprocess, and reporting; **accept `--bin-size` argument** and pass it to the preprocess module; exit 0 on success
- [ ] T015 [US1] Implement `src/data/preprocess.py` to convert timestamps to UTC Julian dates, **accept `bin_size` parameter from orchestrator**, and bin events into non-overlapping intervals
- [ ] T015b [US1] Implement `src/data/preprocess.py` to generate HEALPix sky maps with a resolution parameter suitable for the study scale for each interval; **verify Nside 64 map exists in `data/processed/`** before proceeding
- [ ] T016 [US1] Implement `src/data/preprocess.py` logic to fit spherical harmonics (ℓ=2) and extract dipole amplitude/phase; **write coefficients to `data/processed/spherical_harmonics.json` and update CSV**
- [ ] T017 [US1] Implement `src/data/preprocess.py` to write `data/results/dipole_timeseries.csv` with headers `interval_start, dipole_amp, dipole_phase, quad_amp`
- [ ] T020 [US1] Add error handling for missing IceCube/Auger data to proceed with available data and log warnings

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation & Significance (Priority: P2)

**Goal**: Perform Lomb-Scargle, block-bootstrap, and Monte-Carlo shuffle to quantify correlation significance.

**Independent Test**: Run `analyze_correlation.py` on the CSV from US1; verify periodogram plots, correlation coefficients with p-values, and FAP calculation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for statistical calculations in `tests/contract/test_statistics.py`
- [ ] T022 [P] [US2] Integration test for correlation analysis in `tests/integration/test_correlation_analysis.py`

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement `src/analysis/stats_utils.py` for autocorrelation estimation (optional for future enhancement)
- [ ] T024 [P] [US2] Implement `src/analysis/correlation.py` for Lomb-Scargle periodogram analysis on dipole amplitude series
- [ ] T025 [US2] Implement `src/analysis/correlation.py` for Pearson/Spearman cross-correlation with solar proxies
- [ ] T026 [US2] Implement `src/analysis/significance.py` for block-bootstrap (a large number of resamples) with **block length = 2 × bin_size** (per FR-005); **calculate number of bootstrap blocks and trigger T026b if blocks < 10**
- [ ] T026b [US2] Implement `src/analysis/significance.py` fallback to Fourier-based surrogate generation (phase randomization) **if T026 reports blocks < 10**, ensuring statistical validity
- [ ] T027 [US2] Implement `src/analysis/significance.py` for Monte-Carlo shuffle (a large number of permutations) where **the solar proxy time-series is shuffled relative to the anisotropy series** (per FR-005/SC-005); note: Plan suggests both series, but Spec requires proxy-only
- [ ] T028 [US2] Implement `src/analysis/significance.py` to apply Bonferroni correction (α = 0.0017) and flag positive results (|r| ≥ 0.4 AND p ≤ 0.0017)
- [ ] T029 [US2] Add logic to report frequency resolution limits (Δf ≈ a low magnitude in cycles/year) and flag inability to resolve 11-year cycle explicitly
- [ ] T030 [US2] Implement `src/analysis/correlation.py` to generate PDF output with periodogram; **calculate noise level as median power in a low-frequency band and report peak power relative to this noise level**
- [ ] T030a [US2] **Specific Implementation for SC-003**: Implement logic to explicitly identify the peak at the approximately decadal frequency (if present) and report the calculated noise level and the peak power relative to it (e.g., "3.2σ above median noise") in the output metrics
- [ ] T030b [US2] Implement `src/analysis/correlation.py` to **identify and report peak at approximately decadal frequency** (if found) or flag null result, ensuring SC-003 compliance

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproducible Reporting & Packaging (Priority: P3)

**Goal**: Generate LaTeX report, figures, and bundle environment specs.

**Independent Test**: Invoke `make_report.sh`; confirm `report.pdf` compiles, figures are saved, and `requirements.txt` is present.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Contract test for report generation in `tests/contract/test_report.py`
- [ ] T033 [P] [US3] Integration test for full report build in `tests/integration/test_report_build.py`

### Implementation for User Story 3

- [ ] T034 [P] [US3] Implement `src/report/generate_plots.py` to create time-series, heat-maps, and periodogram plots (PNG/SVG)
- [ ] T035 [US3] Implement `src/report/latex_report.py` using Jinja2 to render `report.pdf` with methods, results, and hypothesis statement
- [ ] T036 [US3] Implement logic in `src/report/latex_report.py` to **programmatically generate hypothesis support statement**: check if p ≤ 0.00135 (3σ) AND |r| ≥ 0.4, AND check if Bonferroni-corrected p-value ≤ 0.0017; generate "Supported" only if BOTH conditions are met, otherwise "Not Supported" (per SC-006)
- [ ] T037 [US3] Create `src/cli/make_report.sh` to orchestrate plot generation and LaTeX compilation; abort if `requirements.txt` missing
- [ ] T038 [US3] Ensure `report.pdf` is ≤ 25 pages and includes all required visualizations and quantitative results
- [ ] T039 [US3] Verify `requirements.txt` contains exact versions and CPU-only constraints

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
- **Data Feasibility**: All tasks must run on CPU-only CI with limited computational resources.. No GPU/CUDA.
- **Real Data**: All tasks must use real data sources (IceCube HuggingFace, NOAA NGDC). No fabrication.
- **Ordering**: Data download tasks (T013-T014) MUST precede preprocessing (T015-T017). Analysis (T023-T031) MUST follow pipeline completion.
- **Spec vs. Plan**: Tasks strictly follow Spec (FR-005) for block length (2 × bin_size). Plan's "Stationary Bootstrap" is noted as optional.
- **Fallback**: T026/T026b ensures FR-005 safety valve is implemented.