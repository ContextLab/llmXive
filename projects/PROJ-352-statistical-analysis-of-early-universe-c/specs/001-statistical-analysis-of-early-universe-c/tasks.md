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

- [X] T001a [P] Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `output/`, `tests/`
- [X] T001b [P] Create `code/__init__.py` and `tests/__init__.py`
- [X] T001c [P] Create `requirements.txt` with dependencies: `healpy`, `numpy`, `scipy`, `scikit-learn`, `requests`, `astropy`, `matplotlib`, `pytest`
- [X] T001d [P] Create `README.md` with project overview and setup instructions
- [ ] T002a [P] Create `.flake8` configuration file for linting.
- [ ] T002b [P] Create `.pylintrc` configuration file for linting.
- [ ] T004a [P] Create `data/raw/`, `data/processed/`, and `output/` directories.
- [ ] T004b [P] Implement basic logging configuration in `code/config.py` with format `%(asctime)s - %(levelname)s - %(message)s` and level `INFO`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement `code/download.py` with exponential backoff retry logic for Planck Legacy Archive access
- [X] T007 Implement checksum validation logic for downloaded FITS files in `code/download.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download Planck 2015/2018 SMICA CMB temperature map at Nside=128, validate integrity, apply Galactic mask, and verify pixel counts.

**Independent Test**: Can be fully tested by downloading a single Planck map, applying the Galactic mask, and verifying pixel counts and coverage.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for download retry logic and checksum validation in `tests/test_download.py`
- [X] T011 [P] [US1] Unit test for mask application and pixel count verification in `tests/test_mask.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download.py`: Fetch `COM_CMB_ILM-NR1-000_R2.01.fits` (SMICA Nside=128) from Planck Legacy Archive with retry logic
- [X] T013 [US1] Implement `code/download.py`: Validate file integrity via MD5/SHA checksums against known Planck Legacy Archive values for `COM_CMB_ILM-NR1-000_R2.01.fits` and save validation result to `data/raw/checksum_report.json`.
- [ ] T015 [US1] Implement `code/mask.py`: Apply the Schmalzing & Gorski analytical correction as the PRIMARY and SOLE method for mask correction, strictly adhering to plan.md Phase 1 Step 1.4 which mandates using the mask's own Minkowski Functionals to correct observed MFs analytically. DO NOT use buffer zones as the primary correction method.
- [ ] T015b [US1] Implement `code/mask.py`: Apply a 2-pixel buffer zone as a SECONDARY verification step ONLY; compare T015 output against analytical expectations and log comparison to `data/processed/mask_verification.log`.
- [ ] T018 [US1] Save masked map to `data/processed/masked_cmb_n128.fits`
- [ ] T016a [US1] {{claim:c_2e64795e}} (input: `data/processed/masked_cmb_n128.fits`) and save verification result to `data/processed/coverage_report.json` with schema {"sky_coverage": float, "valid_pixels": int, "total_pixels": int}.
- [ ] T017 [US1] Compute basic statistics (mean, std) on masked map (input: `data/processed/masked_cmb_n128.fits`) and save mean/std to `data/processed/map_stats.json` with schema {"mean": float, "std": float}.

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
- [ ] T023 [US2] Compute functionals at thresholds {±0.5σ, ±1σ, 0σ} [UNRESOLVED-CLAIM: c_cfa7e974 — status=not_enough_info] and store results in a dictionary with keys corresponding to threshold values.
- [ ] T024a [US2] Generate theoretical genus curve for Gaussian Random Field as a STATIC REFERENCE derived analytically from the Planck power spectrum and save to `data/processed/theoretical_genus_curve.json`.
- [ ] T024c [US2] Compute RMS deviation between observed MFs (from T025) and theoretical genus curve (from T024a) to verify computation accuracy.
- [ ] T025 [US2] Save MF results to `data/processed/minkowski_functionals_observed.json`
- [ ] T024 [US2] Verify numerical precision (≥6 decimal places) and reproducibility (±0.001% tolerance) [UNRESOLVED-CLAIM: c_2155ed38 — status=not_enough_info] and save report to `data/processed/precision_report.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Gaussian Simulation and Statistical Comparison (Priority: P3)

**Goal**: Generate Gaussian random field realizations matching Planck beam/noise, compute their MFs, and perform multivariate statistical comparison (Likelihood Ratio Test) against the Gaussian null hypothesis and a theoretical Cosmic String template model.

**Independent Test**: Can be tested by generating N=1,000 Gaussian simulations to verify the pipeline method within 6h runtime.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for power spectrum matching in simulations in `tests/test_simulate.py`
- [ ] T027 [P] [US3] Unit test for shrinkage covariance estimation in `tests/test_statistics.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/simulate.py`: Load theoretical LCDM power spectrum (Planck TT, TE, EE)
- [ ] T029 [US3] Implement `code/simulate.py`: Load Planck beam transfer function and SMICA noise covariance maps
- [ ] T030 [US3] Implement `code/simulate.py`: Generate N=1,000 Gaussian random field realizations with beam smoothing (FWHM=5.0 arcmin) and noise (σ²=1.1 μK²) [UNRESOLVED-CLAIM: c_d97322f6 — status=not_enough_info] using streaming/batch processing to ensure runtime ≤6h (FR-007). Process simulations in batches (Generate -> Compute MF -> Discard Map) to stay under available RAM constraints.
- [ ] T031 [US3] (Deprecated - merged into T030)
- [ ] T032 [US3] Compute Minkowski Functionals for each simulation using `code/minkowski.py`
- [ ] T036a [US3] (Deprecated - alternative hypothesis handled via theoretical model)
- [ ] T036 [US3] (Deprecated - alternative hypothesis handled via theoretical model)
- [ ] T033 [US3] Implement `code/statistics.py`: Compute sample covariance matrix of MFs across N=1,000 simulations using Ledoit-Wolf shrinkage estimator
- [ ] T034 [US3] Implement `code/statistics.py`: Perform PCA on MF curves to reduce dimensionality for stable multivariate testing
- [ ] T035 [US3] Implement `code/statistics.py`: Perform Likelihood Ratio Test (Lambda = -2 * log(L_H0 / L_H1)) comparing observed MF vector against Gaussian null hypothesis ($H_0$) and a theoretical Cosmic String template model ($H_1$) as defined in FR-005, using the sample covariance matrix from T033 to account for correlation between functionals.
- [ ] T030b [US3] (Deprecated - merged into T030)
- [ ] T037 [US3] Output final results to `output/results.json` with ≥6 decimal precision (p-value, Gμ upper bounds, and deviation status)
- [ ] T038 [US3] Generate summary plots (Genus curve comparison) for `quickstart.md`

**Checkpoint**: All user stories should now be independently functional (Gaussian Null Hypothesis and Theoretical String Alternative Hypothesis Analysis Complete)

---