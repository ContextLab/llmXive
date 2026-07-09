# Tasks: Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects

**Input**: Design documents from `/specs/001-cmb-defect-analysis/`
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

- [ ] T001a [P] Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `output/`, `tests/`
- [ ] T001b [P] Create `code/__init__.py` and `tests/__init__.py`
- [ ] T001c [P] Create `requirements.txt` with dependencies: `healpy`, `numpy`, `scipy`, `scikit-learn`, `requests`, `astropy`, `matplotlib`, `pytest`
- [ ] T001d [P] Create `README.md` with project overview and setup instructions
- [ ] T002 [P] Configure linting (flake8/pylint) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/raw/`, `data/processed/`) and logging infrastructure
- [ ] T005 Implement `code/download.py` with exponential backoff retry logic for Planck Legacy Archive access
- [ ] T006 Implement checksum validation logic for downloaded FITS files in `code/download.py`
- [ ] T007 Create base configuration management for paths, seeds, and Planck parameters in `code/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download Planck 2015/2018 SMICA CMB temperature map at Nside=128, validate integrity, apply Galactic mask, and verify pixel counts.

**Independent Test**: Can be fully tested by downloading a single Planck map, applying the Galactic mask, and verifying pixel counts and coverage.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for download retry logic and checksum validation in `tests/test_download.py`
- [ ] T011 [P] [US1] Unit test for mask application and pixel count verification in `tests/test_mask.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/download.py`: Fetch `COM_CMB_ILM-NR1-000_R2.01.fits` (SMICA Nside=128) from Planck Legacy Archive with retry logic
- [ ] T013 [US1] Implement `code/download.py`: Validate file integrity via MD5/SHA checksums against known Planck values
- [ ] T014 [US1] Implement `code/mask.py`: Load a Galactic mask (or equivalent) and apply to CMB map
- [ ] T015 [US1] Implement `code/mask.py`: Apply a pixel buffer zone as PRIMARY method per Spec Edge Cases by setting pixels within N=2 of mask edge to 0. Algorithm: For each pixel, if distance to nearest masked pixel <= 2, set value to 0.
- [ ] T015b [US1] Implement `code/mask.py`: Apply Schmalzing & Gorski (1998) analytical correction as SECONDARY verification step; compare T015 output against analytical expectations and log comparison
- [ ] T016 [US1] Verify masked map has ≥95% sky coverage and ≥2.5M valid pixels (FR-002) using formula: `sky_coverage = valid_pixels / (12 * 128^2)`. Save verification result to `data/processed/coverage_report.json`
- [ ] T017 [US1] Compute basic statistics (mean, std) on masked map to ensure physical plausibility and Save mean/std to `data/processed/map_stats.json`
- [ ] T018 [US1] Save masked map to `data/processed/masked_cmb_n128.fits`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Minkowski Functional Computation (Priority: P2)

**Goal**: Compute all three Minkowski Functionals (area, perimeter, genus) on the masked CMB map at thresholds {±0.5σ, ±1σ, 0σ} with mask-corrected estimators.

**Independent Test**: Can be tested by computing Minkowski Functionals on a single masked map and verifying the three functional values are returned with physically consistent ranges.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for Minkowski Functional computation on synthetic Gaussian map in `tests/test_minkowski.py`
- [ ] T020 [P] [US2] Integration test for mask-corrected MF computation in `tests/test_minkowski_integration.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/minkowski.py`: Compute Area, Perimeter, and Genus functionals using `healpy` and `numpy`
- [ ] T022 [US2] Implement `code/minkowski.py`: Apply Schmalzing & Gorski mask correction to MF results
- [ ] T023 [US2] Compute functionals at thresholds {±0.5σ, ±1σ, 0σ}
- [ ] T024a [US2] Generate theoretical genus curve for Gaussian Random Field using analytic formula (e.g., Schmalzing & Barreiro) based on input power spectrum and save to `data/processed/theoretical_genus_curve.json`
- [ ] T024 [US2] Verify numerical precision (≥6 decimal places) and reproducibility (±0.001% tolerance) using synthetic Gaussian map (seed=42). Assertion logic: `assert abs(val1 - val2) / val1 < 0.00001` in `tests/test_minkowski.py::test_precision_tolerance`
- [ ] T024c [US2] Compute RMS deviation between observed MFs (from T025) and theoretical genus curve (from T024a). This measures physics deviation (signal vs null hypothesis). Target: ≤1% (SC-002). Save report to `data/processed/computation_accuracy_report.json`
- [ ] T025 [US2] Save MF results to `data/processed/minkowski_functionals_observed.json`
- [ ] T025d [US2] Validate computation accuracy: Generate synthetic Gaussian map (seed=42), compute MFs, calculate RMS deviation against analytic genus curve (from T024a); verify target ≤1% (SC-002). Save report to `data/processed/computation_accuracy_report.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Gaussian Simulation and Statistical Comparison (Priority: P3)

**Goal**: Generate Gaussian random field realizations matching Planck beam/noise, compute their MFs, generate Cosmic String template realizations, and perform multivariate statistical comparison (Likelihood Ratio Test) against both Gaussian ($H_0$) and String ($H_1$) hypotheses.

**Independent Test**: Can be tested by generating N=1,000 total simulations (500 Gaussian + 500 String) to verify the pipeline method within 6h runtime.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for power spectrum matching in simulations in `tests/test_simulate.py`
- [ ] T027 [P] [US3] Unit test for shrinkage covariance estimation in `tests/test_statistics.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/simulate.py`: Load theoretical LCDM power spectrum (Planck 2018 TT, TE, EE)
- [ ] T029 [US3] Implement `code/simulate.py`: Load Planck beam transfer function and SMICA noise covariance maps
- [ ] T030 [US3] Implement `code/simulate.py`: Generate N=500 Gaussian random field realizations with beam smoothing (FWHM=5.0 arcmin) and noise (σ²=1.1 μK²)
- [ ] T030b [US3] Implement `code/simulate.py`: Verify total runtime for N=1000 (500 Gaussian + 500 String) < 6h on GitHub Actions free-tier. Abort if exceeded.
- [ ] T031 [US3] Implement `code/simulate.py`: Process simulations in batches (Generate -> Compute MF -> Discard Map) to stay under available RAM constraints.
- [ ] T032 [US3] Compute Minkowski Functionals for each simulation using `code/minkowski.py`
- [ ] T036 [US3] Implement `code/simulate.py`: Generate N=500 Cosmic String template realizations at varying Gμ values (range [1e-7, 1e-6], 5 steps) and compute their MFs to build the H1 distribution
- [ ] T033 [US3] Implement `code/statistics.py`: Compute sample covariance matrix of MFs across N=1,000 simulations using Ledoit-Wolf shrinkage estimator
- [ ] T034 [US3] Implement `code/statistics.py`: Perform PCA on MF curves to reduce dimensionality for stable multivariate testing
- [ ] T035 [US3] Implement `code/statistics.py`: Perform Likelihood Ratio Test (Lambda = -2 * log(L_H0 / L_H1)) comparing observed MF vector against Gaussian null hypothesis ($H_0$) and Cosmic String alternative hypothesis ($H_1$) distributions. Use Chi-squared distribution with k degrees of freedom. Use Ledoit-Wolf covariance matrix from T033.
- [ ] T037 [US3] Output final results to `output/results.json` with ≥6 decimal precision (p-value, Gμ upper bounds, and deviation status)
- [ ] T038 [US3] Generate summary plots (Genus curve comparison) for `quickstart.md`

**Checkpoint**: All user stories should now be independently functional (Gaussian Null Hypothesis and String Alternative Hypothesis Analysis Complete)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044a [P] Update `docs/quickstart.md` with pipeline usage instructions and example outputs
- [ ] T044b [P] Update `docs/data-model.md` with data schema for `results.json` and `coverage_report.json`
- [ ] T045a [P] Run linter (flake8/pylint) on `code/` and fix all errors/warnings
- [ ] T045b [P] Refactor code to remove duplication (>20% similarity) and improve readability
- [ ] T046a [P] Profile memory usage of simulation loop and optimize to ensure < 6.5GB peak (Strategy: Implement streaming generator, delete maps after MF computation)
- [ ] T046b [P] Profile runtime of full pipeline and optimize hotspots to ensure < 6h total (Strategy: Profile with cProfile, optimize hotspots in minkowski.py)
- [ ] T047a [P] Add unit tests for `code/download.py` (coverage > 80%)
- [ ] T047b [P] Add unit tests for `code/mask.py` (coverage > 80%)
- [ ] T047c [P] Add unit tests for `code/minkowski.py` (coverage > 80%)
- [ ] T048a [P] Run `docs/quickstart.md` validation script and verify all output artifacts match spec
- [ ] T049a [P] Execute download pipeline stress-test loop (N=10) to empirically measure success rate. Success = (HTTP 200 AND checksum match). Metric: success_count / total_attempts * 100. Output schema: `{"total_attempts": N, "successes": M, "rate": M/N}` to `data/processed/reliability_report.json`
- [ ] T049b [P] Execute download pipeline stress-test loop (N=100) to calculate reliability metric for SC-001

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Phase N (Polish)**: Depends on US1, US2, US3 completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data (masked map)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 logic
- **Phase N (Polish)**: Depends on US1, US2, US3 completion

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
Task: "Unit test for download retry logic and checksum validation in tests/test_download.py"
Task: "Unit test for mask application and pixel count verification in tests/test_mask.py"

# Launch all models for User Story 1 together:
Task: "Implement code/download.py: Fetch SMICA map"
Task: "Implement code/download.py: Validate checksums"
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
- **Critical Constraint**: All tasks must run on GitHub Actions free-tier (limited CPU, limited RAM, no GPU). No 8-bit quantization or CUDA operations allowed.
- **Data Integrity**: No fake data generation. All inputs must be from real Planck archives or real theoretical spectra.
- **Simulation Count**: Total simulations = N=1,000 (500 Gaussian + 500 Cosmic String) to strictly adhere to FR-007 and SC-004 (≤6h runtime).
- **Mask Correction**: The 2-pixel buffer zone is the PRIMARY method for edge handling as mandated by Spec Edge Cases. Schmalzing & Gorski analytical correction is used as secondary verification only.
- **Scope**: Observer Invariance (Phase 5b) has been removed as it was unapproved scope creep. The analysis focuses strictly on the Spec's FR-001 to FR-007.
- **Plan vs Spec Conflict**: The Plan.md Phase 1.4 description of Schmalzing & Gorski as "primary" contradicts the Spec.md Edge Cases. The tasks follow the Spec.md (Buffer Primary). The Plan.md requires correction.