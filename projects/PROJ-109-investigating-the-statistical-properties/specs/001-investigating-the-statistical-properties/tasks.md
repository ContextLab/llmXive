# Tasks: Investigating Statistical Properties of Simulated Dark Matter Halos

**Input**: Design documents from `/specs/001-dark-matter-halo-statistics/`
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

- [ ] T001 Create project structure per implementation plan: `mkdir -p code/data code/analysis data/raw data/processed results tests/unit tests/integration docs`
- [ ] T002 Initialize Python 3.11 project with dependencies: Install pip, setuptools, wheel; then install pandas, numpy, scipy; then run `pip freeze` to generate `requirements.txt` with exact versions (pin to exact versions, generate via `pip freeze`)
- [ ] T003 [P] Configure linting (flake8/pylint) and formatting (black) tools in `pyproject.toml` (black --line-length 88, flake8 max-line-length=100)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `code/config.py` with pinned random seeds, file paths, simulation box size (suitable for capturing large-scale structure), and critical density constants
- [ ] T005A [P] Pre-register significance thresholds (α=0.05) and correction method (Benjamini-Hochberg) in `code/config.py` as mandated by Constitution VII (FR-009, SC-003); these values MUST be hard-coded and immutable during the run; this task is for configuration only, not implementation of the test logic (See T033)
- [ ] T005B [P] Create `code/contracts/halo.schema.yaml` and `code/contracts/results.schema.yaml` for data validation
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging.py` (format: `%(asctime)s - %(levelname)s - %(message)s`, level: INFO, output: `logs/pipeline.log`)
- [ ] T007A [P] Create `code/data/streaming.py` class `ChunkedHDF5Reader` with `__init__(path, chunk_size)` and `__iter__` methods
- [ ] T007B [P] Create `code/data/streaming.py` function `stream_halos(chunk_size=10000)` returning generator of halo dictionaries
- [ ] T007C [P] Create `code/data/streaming.py` function `subsample_particles(n=500, seed=42)` implementing the 'Subsampled Plummer-Softened Potential' logic (See Plan Phase 1, Complexity Tracking)
- [ ] T008 [P] [US1] Implement synthetic data generator with controlled deviations in `code/data/synthetic_generator.py` as conditional fallback (triggered ONLY if API fails); output schema: HDF5, deviation: offset NFW concentration by a small magnitude, use a fixed random seed, path: `data/raw/synthetic_halos.h5`; note: synthetic generator is primary execution path for this stage as per Plan mandate

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Download and filter public cosmological simulation catalogs (IllustrisTNG TNG100-1 and Millennium) to produce a validated halo dataset ready for structural analysis. If real data is unavailable, generate synthetic data with controlled deviations.

**Independent Test**: Can be fully tested by successfully downloading both catalogs (including particle data) or generating synthetic data, filtering for halos with ≥300 particles, and producing a consolidated dataset file that contains all required columns (mass, position, velocity, particle counts).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009A [P] [US1] Unit test `test_filter_halos_300_particles` in `tests/unit/test_preprocess.py`
- [ ] T009B [P] [US1] Unit test `test_stream_halos_chunk_size` in `tests/unit/test_streaming.py`
- [ ] T010A [P] [US1] Unit test `test_synthetic_data_deviation_injection` in `tests/unit/test_synthetic.py`
- [ ] T010B [P] [US1] Unit test `test_synthetic_schema_validation` in `tests/unit/test_synthetic.py`
- [ ] T011 [P] [US1] Integration test `test_full_data_pipeline` in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [X] T012 Implement `code/data/download.py` to fetch IllustrisTNG TNG100-1 and Millennium catalogs via API; check API status; trigger synthetic fallback ONLY on failure (FR-001)
- [X] T013 [US1] Implement halo filtering logic in `code/data/preprocess.py` to retain only halos with ≥300 particles and log filtered count (FR-002)
- [X] T014 [US1] Implement chunked streaming writer in `code/data/preprocess.py` to save filtered data as `data/processed/filtered_halos_{timestamp}.parquet` (chunk_size=10k, compression=snappy)
- [~] T015 [US1] Add validation against `code/contracts/halo.schema.yaml` after filtering in `code/data/preprocess.py`
- [X] T016 [US1] Add logging for data gap detection in `code/data/download.py` (message: 'DATA_GAP: Real data unavailable, switching to synthetic'; trigger: HTTP 403/Timeout)
- [X] T017 [US1] Implement local overdensity calculation in `code/data/compute_metrics.py` using cKDTree with periodic boundary wrapping, spherical top-hat of a characteristic radius, using simulation box size from T004; explicitly use Memory-Mapped Sparse Particle Stream and Subsampled strategy (% random sample) as defined in Plan Phase 1, Complexity Tracking; process on synthetic/filtered particle stream after filtering; document how the 5 Mpc radius calculation remains statistically valid on a subsample (FR-003)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Structural Metric Computation (Priority: P2)

**Goal**: Compute shape (s=c/a), spin parameter (λ), and concentration index (c) for each halo using validated physical formulas.

**Independent Test**: Can be fully tested by running the metric computation on a a sample of halos and verifying that output distributions match expected physical ranges (shape s ∈ [0,1], spin λ ∈ [0,1], concentration c > 0).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test `test_inertia_tensor_shape` in `tests/unit/test_metrics.py`
- [X] T019 [P] [US2] Unit test `test_spin_parameter_subsample` in `tests/unit/test_spin.py`
- [X] T020 [P] [US2] Unit test `test_nfw_convergence` in `tests/unit/test_concentration.py`
- [X] T021 [P] [US2] Integration test `test_full_metric_pipeline` in `tests/integration/test_metrics.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement shape parameter s=c/a calculation from inertia tensor of particle positions in `code/data/compute_metrics.py` (FR-004)
- [ ] T023 [US2] {{claim:c_dbac5b85}} in `code/data/compute_metrics.py` using Subsampled Plummer-Softened Potential (N=500 particles) via T007C; this is the ONLY valid implementation due to memory constraints (See Plan Phase 1, Complexity Tracking); document deviation from 'direct summation' in code comments and log in Data Gap Report (FR-005)
- [ ] T023B [US2] Document deviation from 'direct summation' to 'Subsampled Plummer-Softened Potential' and validate that the subsampled approach satisfies the scientific intent of FR-005 in `docs/data_gap_report.md`
- [ ] T024 [US2] Implement NFW profile fitting via scipy.optimize.curve_fit with convergence logging and exclusion logic in `code/data/compute_metrics.py` (FR-006)
- [ ] T025 [US2] Add validation checks for metric ranges in `code/data/compute_metrics.py` (if not (0 <= s <= 1): raise ValueError; message: 'Shape out of range')
- [ ] T026 [US2] Log convergence rates and failed fit counts in `code/data/compute_metrics.py` (message: 'CONVERGENCE: X% success, Y failed fits'; aggregate to `results/convergence_stats.json`)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Hypothesis Testing (Priority: P3)

**Goal**: Perform Kolmogorov-Smirnov tests and Spearman correlations to assess deviations from NFW/ΛCDM predictions across mass and environment bins.

**Independent Test**: Can be fully tested by running the full statistical pipeline on the processed dataset and producing a results summary with p-values, effect sizes, and visualizations saved as PNG/PDF.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027A [P] [US3] Unit test `test_mass_binning_ranges` in `tests/unit/test_binning.py`
- [ ] T027B [P] [US3] Unit test `test_environment_binning_threshold` in `tests/unit/test_binning.py`
- [ ] T028A [P] [US3] Unit test `test_ks_test_pvalue` in `tests/unit/test_stats.py`
- [ ] T028B [P] [US3] Unit test `test_benjamini_hochberg_correction` in `tests/unit/test_stats.py`
- [ ] T029A [P] [US3] Unit test `test_spearman_correlation` in `tests/unit/test_correlations.py`
- [ ] T029B [P] [US3] Unit test `test_bullock_comparison` in `tests/unit/test_correlations.py`
- [ ] T030 [P] [US3] Integration test `test_full_analysis_pipeline` in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement mass binning spanning multiple orders of magnitude in solar mass units and environment binning (Δ < 200 vs ≥ 200) in `code/analysis/stats.py` (FR-007)
- [ ] T032 [P] [US3] Implement two-sample KS tests between low/high environmental bins for shape, spin, and concentration in `code/analysis/stats.py` (FR-008)
- [ ] T033 [P] [US3] Implement Benjamini-Hochberg correction for multiple hypothesis testing across ≥9 KS tests [UNRESOLVED-CLAIM: c_decadb70 — status=not_enough_info] in `code/analysis/stats.py` (FR-009); use threshold from `code/config.py`
- [ ] T034 [P] [US3] Implement Spearman's ρ correlation between halo mass and each structural metric in `code/analysis/stats.py` (FR-010)
- [ ] T035 [P] [US3] {{claim:c_0940b987}} (astro-ph/0402210, https://arxiv.org/abs/astro-ph/0402210) in `code/analysis/stats.py` (FR-011); include fallback behavior if citation validation fails: default to standard Bullock et al. 2001 parameters (c_200 = 10, alpha = -0.1) and log the fallback event
- [ ] T035B [US3] Implement the actual Bullock comparison logic (deviation statistics calculation) in `code/analysis/stats.py` (FR-011)
- [ ] T036 [US3] Implement Bullock et al. (2001) analytic fit using the standard form c(M) = c_200 * (M/M_200)^alpha with c_200=10 and alpha is set to a negative value.; validate these hardcoded parameters against the spec's intent; if the spec's citation year is ambiguous, use these default values and log the resolution; do NOT attempt to fetch external sources (FR-011)
- [ ] T037 [US3] Implement visualization generation (scatter plots, KDE curves, heatmaps) using matplotlib/seaborn in `code/analysis/visualize.py` (FR-012)
- [ ] T038 [US3] Save all results (p-values, effect sizes, convergence rates) to `results/statistics.json`
- [ ] T039 [US3] Save visualizations as PNG/PDF in `results/figures/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040A [P] Documentation updates in `docs/data_gap_report.md` including Data Source, Fallback Reason, Synthetic Parameters (FR-001, Plan Phase 0)
- [ ] T040B [P] Code cleanup: Remove unused imports and optimize memory usage in `code/data/compute_metrics.py`
- [ ] T041A [P] Performance optimization: Implement memory-mapped array access for particle stream in `code/data/compute_metrics.py` (target: reduce I/O by at least 50% or achieve high throughput)
- [ ] T042A [P] Unit test `test_halo_300_particles_boundary` in `tests/unit/test_edge_cases.py`
- [ ] T042B [P] Unit test `test_nfw_fit_failure_handling` in `tests/unit/test_edge_cases.py`
- [ ] T042C [P] Unit test `test_empty_bin_handling` in `tests/unit/test_edge_cases.py`
- [ ] T043 [US3] Run quickstart.md validation and verify pipeline execution within 6 hours on GitHub Actions free-tier runner (command: `python code/main.py --run-all`; output: `results/timing.json`)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Unit test for data filtering logic in tests/unit/test_preprocess.py"
Task: "Unit test for synthetic data generation and deviation injection in tests/unit/test_synthetic.py"

# Launch all models for User Story 1 together:
Task: "Implement halo filtering logic in code/data/preprocess.py"
Task: "Implement chunked streaming writer in code/data/preprocess.py"
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