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

- [ ] T001A Create project directory structure: `mkdir -p code/data code/analysis data/raw data/processed results tests/unit tests/integration docs`
- [ ] T001B Create `__init__.py` files in all new directories to ensure Python package recognition.
- [ ] T002A Install Python dependencies: `pip install pandas numpy scipy scikit-learn matplotlib seaborn requests h5py astropy numba pytest`
- [ ] T002B Generate `requirements.txt` with exact versions using `pip freeze`.
- [X] T003 [P] Configure linting (flake8/pylint) and formatting (black) tools in `pyproject.toml` (black --line-length 88, flake8 max-line-length=100)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `code/config.py` with pinned random seeds, file paths, simulation box size (h⁻¹ Mpc for Millennium, appropriate domain size for TNG100-1), and critical density constants.
- [ ] T004D [P] [US1] Define Bullock et al. (2001) analytic fit parameters as numerical constants in `code/config.py` (variables: `BULLOCK_C200`, `BULLOCK_ALPHA`). **Specific Requirement**: Must include the exact numerical values for c_200 and alpha as per the paper. (See T036A).
- [ ] T004E [P] [US3] Add docstring and citation block for Bullock et al. (2001) parameters in `code/config.py` (See T004D). **Dependency**: Must complete after T004D.
- [ ] T005A [P] Configure Benjamini-Hochberg correction method in `code/config.py` as parameters for the analysis logic (See T033 for implementation). Do NOT mark as immutable constants; these are configuration inputs for the statistical tests.
- [ ] T005B [P] Create `code/contracts/halo.schema.yaml` and `code/contracts/results.schema.yaml` for data validation (Full schema for US2/US3).
- [ ] T005C [P] [US1] Create `code/contracts/raw_halo.schema.yaml` containing ONLY raw columns: `mass`, `position`, `velocity`, `particle_count`. This schema is for US1 validation only.
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging.py` (format: `%(asctime)s - %(levelname)s - %(message)s`, level: INFO, output: `logs/pipeline.log`)
- [ ] T007A [P] [US1] Implement streaming infrastructure in `code/data/streaming.py`:
 1. Class `ChunkedHDF5Reader` with `__init__(path, chunk_size)` and `__iter__` methods
 2. Function `stream_halos(chunk_size=10000)` returning generator of halo dictionaries
- [ ] T007B [P] [US1] Implement synthetic data generator with controlled deviations in `code/data/synthetic_generator.py`. **Role**: Fallback Utility. **Execution Logic**: This task MUST NOT run unconditionally. It generates synthetic data ONLY if explicitly called by T012 after T012 detects an API failure (HTTP 403/Timeout). **Output**: HDF5 file at `data/raw/synthetic_halos.h5` with controlled deviations (offset NFW concentration). **Reproducibility**: Must record the generated file's checksum in `state/projects/PROJ-109-investigating-the-statistical-properties.yaml` (Constitution Principle III) and record generation parameters (deviation magnitude, seed, NFW offset) in `state/projects/PROJ-109-investigating-the-statistical-properties.yaml` and `code/config_synthetic.yaml` (Constitution Principle VI). **Dependency**: Must be available for T012 to call on failure.
- [ ] T007D [P] [US1] Record synthetic generation parameters (specific deviation magnitude, seed, NFW offset values) in `state/projects/PROJ-109-investigating-the-statistical-properties.yaml` and `code/config_synthetic.yaml` to satisfy Constitution Principle VI (Reproducibility). **Dependency**: Must complete after T007B.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Download and filter public cosmological simulation catalogs (IllustrisTNG TNG100-1 and Millennium) to produce a validated halo dataset ready for structural analysis. If real data is unavailable, generate synthetic data with controlled deviations.

**Independent Test**: Can be fully tested by successfully downloading both catalogs (including particle data) or generating synthetic data, and producing a consolidated dataset file that contains all required columns (mass, position, velocity, particle counts).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T009A [P] [US1] Unit test `test_filter_halos_300_particles` in `tests/unit/test_preprocess.py`
- [ ] T009B [P] [US1] Unit test `test_stream_halos_chunk_size` in `tests/unit/test_streaming.py`
- [ ] T010A [P] [US1] Unit test `test_synthetic_data_deviation_injection` in `tests/unit/test_synthetic.py`
- [ ] T010B [P] [US1] Unit test `test_synthetic_schema_validation` in `tests/unit/test_synthetic.py`
- [X] T011 [P] [US1] Integration test `test_full_data_pipeline` in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data/download.py` to fetch IllustrisTNG TNG100-1 and Millennium catalogs via API. **Execution Flow**: Attempt real download -> If HTTP 403/Timeout/404, log 'DATA_GAP: Real data unavailable, switching to synthetic' -> **Call T007B** to generate synthetic fallback. (FR-001) <!-- FAILED: unspecified -->
- [X] T013 [US1] Implement halo filtering logic in `code/data/preprocess.py` to retain only halos with ≥300 particles. **Verification**: Assert output dataset contains only rows where `particle_count >= 300`. Log the exact count of filtered vs total halos. (FR-002)
- [X] T014 [US1] Implement chunked streaming writer in `code/data/preprocess.py` to save filtered data as `data/processed/filtered_halos_{timestamp}.parquet`. **Schema**: Output must contain columns [mass, position, velocity, particle_count] ONLY. **Note**: Derived metrics (overdensity, shape, spin, concentration) are NOT included in this US1 output. (chunk_size=10k, compression=snappy)
- [ ] T015 [US1] Add validation against `code/contracts/raw_halo.schema.yaml` after filtering in `code/data/preprocess.py`. **Requirement**: Must load `raw_halo.schema.yaml` and call `jsonschema.validate` on the data. (FR-002)
- [X] T016 [US1] Add logging for data gap detection in `code/data/download.py` (message: 'DATA_GAP: Real data unavailable, switching to synthetic'; trigger: HTTP 403/Timeout)
- [ ] T017B [US1] Implement local overdensity calculation in `code/data/compute_metrics.py` using cKDTree with periodic boundary wrapping. **Specification**: Use a spherical top-hat of **5 Mpc h⁻¹ radius** (constant `R_TOP_HAT = 5.0`). **Method**: Create a `numpy.memmap` view of the source HDF5 file (generated by T012 or T007B) to access particle positions directly. **Periodic Wrapping**: Explicitly wrap coordinates using the simulation box size defined in `code/config.BOX_SIZE` before neighbor counting. Compute overdensity as Δ = ρ_local / ρ_critical (using ρ_critical from T004). (FR-003) **Dependency**: Must complete after T012/T007B (Data availability).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Structural Metric Computation (Priority: P2)

**Goal**: Compute shape (s=c/a), spin parameter (λ), and concentration index (c) for each halo using validated physical formulas.

**Independent Test**: Can be fully tested by running the metric computation on a sample of halos and verifying that output distributions match expected physical ranges (shape s ∈ [0,1], spin λ ∈ [0,1], concentration c > 0).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test `test_inertia_tensor_shape` in `tests/unit/test_metrics.py`
- [X] T019 [P] [US2] Unit test `test_spin_parameter_subsample` in `tests/unit/test_spin.py`
- [X] T020 [P] [US2] Unit test `test_nfw_convergence` in `tests/unit/test_concentration.py`
- [X] T021 [P] [US2] Integration test `test_full_metric_pipeline` in `tests/integration/test_metrics.py`

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement shape parameter s=c/a calculation from inertia tensor of particle positions in `code/data/compute_metrics.py`. **Input**: Requires halo dataset with columns: `particle_positions` (Nx3), `particle_masses` (Nx1). (FR-004)
- [X] T023 [US2] Implement spin parameter λ calculation in `code/data/compute_metrics.py`. **Scientific Goal**: Compute total energy E via direct summation approximation of potential energy (FR-005). **DEVIATION & JUSTIFICATION**: Due to O(N²) computational complexity of full direct summation being infeasible on CPU-only CI, this task implements a **Subsampled Plummer-Softened Potential** using N=500 random particles per halo. This is a documented approximation that preserves the physical intent of FR-005 while satisfying CPU feasibility constraints. **Algorithm**:
 1. Randomly select N=500 particles from the halo's particle set (or all if <500).
 2. Calculate potential energy E_pot using the Plummer-softened formula: E_pot = -G * Σ_i Σ_j (m_i * m_j) / sqrt(r_ij² + ε²), where ε = 0.01 * halo_radius (halo radius defined as the radius containing [deferred] of the halo mass).
 3. Calculate total energy E = E_kin + E_pot.
 4. Compute spin parameter λ = J * |E|^(1/2) / (G * M^(5/2)).
 **Dependency**: Requires `code/data/compute_metrics.py` utilities. **Mandatory Dependency**: Must complete after T023B (Waiver Documentation) to ensure the spec deviation is formally acknowledged. **Fallback**: Raise error if subsample < 500 particles. (FR-005, SC-004)
- [ ] T023B [US2] Document the 'Subsampled Plummer-Softened Potential' approach as a 'Complexity Constraint' (not a Data Gap) in `docs/architecture_constraints.md`. **Content**: Explain that the subsampled approach preserves the physical intent of FR-005 while satisfying CPU feasibility. **Dependency**: Must complete before T023.
- [X] T024 [US2] Implement NFW profile fitting via scipy.optimize.curve_fit with convergence logging and exclusion logic in `code/data/compute_metrics.py` (FR-006) <!-- FAILED: unspecified -->
- [X] T025 [US2] Add validation checks for metric ranges in `code/data/compute_metrics.py` (if not (0 <= s <= 1): raise ValueError; message: 'Shape out of range')
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
- [X] T030 [P] [US3] Integration test `test_full_analysis_pipeline` in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement mass binning with specific boundaries across multiple orders of magnitude in stellar mass and environment binning (Δ < 200 vs ≥ 200) in `code/analysis/stats.py`. **Requirement**: Explicitly use `ρ_critical` from `code/config.py` (defined in T004) for overdensity normalization. (FR-007)
- [X] T032 [P] [US3] Implement two-sample KS tests between low/high environmental bins for shape, spin, and concentration in `code/analysis/stats.py` (FR-008)
- [ ] T033 [P] [US3] Implement Benjamini-Hochberg correction for multiple hypothesis testing across multiple KS tests (multiple metrics x multiple bins) in `code/analysis/stats.py` (FR-009); use threshold from `code/config.py`. <!-- FAILED: unspecified -->
- [ ] T034 [P] [US3] Implement Spearman's ρ correlation between halo mass and each structural metric in `code/analysis/stats.py` (FR-010)
- [ ] T036A [US3] Load Bullock et al. (2001) parameters from `code/config.py` (variables `BULLOCK_C200`, `BULLOCK_ALPHA` defined in T004D). **Verification**: Assert values match the expected constants by checking `config.BULLOCK_C200` and `config.BULLOCK_ALPHA` are not None and are numeric. (FR-011)
- [ ] T036B [US3] Implement the Bullock et al. (2001) analytic fit function in `code/analysis/stats.py` using the parameters from T036A.
- [ ] T035 [US3] Implement comparison against Bullock et al. (2001) analytic fit in `code/analysis/stats.py`. **Dependency**: Requires parameters verified in T036A and fit function from T036B. (FR-011)
- [ ] T035A [US3] Calculate and report deviation statistics (RMSE, mean difference) between measured mass-concentration relation and the Bullock et al. (2001) fit curve. **Dependency**: Must complete after T035. (SC-005, FR-011)
- [ ] T037 [US3] Implement visualization generation (scatter plots, KDE curves, heatmaps) using matplotlib/seaborn in `code/analysis/visualize.py` (FR-012)
- [ ] T038 [US3] Save all results (p-values, effect sizes, convergence rates) to `results/statistics.json`
- [ ] T039 [US3] Save visualizations as PNG/PDF in `results/figures/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040A [P] Documentation updates in `docs/architecture_constraints.md` including Data Source, Fallback Reason, Synthetic Parameters, and Complexity Constraints (FR-001, Plan Phase 0)
- [ ] T040B [P] Code cleanup: Remove unused imports and optimize memory usage in `code/data/compute_metrics.py`
- [ ] T041A [P] Performance optimization: Implement memory-mapped array access for particle stream in `code/data/compute_metrics.py` (target: reduce I/O by at least 50% or achieve high throughput)
- [ ] T042A [P] Unit test `test_halo_300_particles_boundary` in `tests/unit/test_edge_cases.py`
- [ ] T042B [P] Unit test `test_nfw_fit_failure_handling` in `tests/unit/test_edge_cases.py`
- [ ] T042C [P] Unit test `test_empty_bin_handling` in `tests/unit/test_edge_cases.py`
- [ ] T043 [US3] Run quickstart.md validation and verify pipeline execution within 6 hours on GitHub Actions free-tier runner (limited cores, 7GB RAM) using the stratified sample size defined in `code/config.py`. **Requirement**: **Mechanism**: Wrap `python code/main.py` execution in a Python timer script to capture start/stop time. **Assertion**: Assert duration < 21600s based on the generated `results/timing.json`. Log the justification for the sample size and timing results in `results/timing.json`. (command: `python code/main.py --run-all`; output: `results/timing.json`)

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