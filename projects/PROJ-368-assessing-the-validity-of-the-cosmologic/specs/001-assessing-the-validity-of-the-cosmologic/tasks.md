# Tasks: Assessing the Validity of the Cosmological Principle with Public CMB Data

**Input**: Design documents from `/specs/001-assess-cosmological-principle/`
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

## Phase 0: Spec Alignment & Requirement Updates (CRITICAL PRE-REQUISITE)

**Purpose**: Resolve contradictions between spec.md and plan.md BEFORE implementation begins.

- [ ] T001 [P] Update `spec.md` FR-009: Replace "Benjamini-Hochberg correction" with "Maximum Statistic approach (max of N/S and E/W asymmetries)" to align with plan.md and statistical best practices. <!-- FAILED: unspecified -->
- [ ] T002 [P] Update `spec.md` SC-002: Replace "Benjamini-Hochberg correction applied" with "Maximum Statistic approach applied" to ensure success criteria match implementation.
- [ ] T003 [P] Update `spec.md` US-4 Acceptance Scenario 3: Replace "Benjamini-Hochberg" with "Maximum Statistic" to align test criteria with the implemented method.

**Checkpoint**: Spec artifacts are now consistent with the plan. No implementation tasks may proceed until T001-T003 are complete.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T004 Create project directories: `mkdir -p code tests data/raw data/processed data/simulations data/reports docs`
- [ ] T005 Create `pyproject.toml` in root with a compatible Python version and pinned dependencies: `healpy`, `numpy`, `scipy`, `astropy`, `requests`, `pyyaml`
- [ ] T006 [P] Configure linting (flake/black) and formatting tools in `pyproject.toml`
- [~] T007 Create `code/config.py` defining paths, random seeds, Nside constants, and simulation counts.
- [~] T008 [P] Initialize git repository and add `.gitignore` for `data/`, `__pycache__/`, `*.pyc`
- [~] T009 [P] Create `code/logging_config.py` implementing JSON format logging at INFO level
- [~] T010 Create `tests/test_config.py` to validate configuration constants and paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Acquire and preprocess public Planck CMB data (Priority: P1) 🎯 MVP

**Goal**: Download, validate, mask, and downgrade the Planck SMICA CMB map to fit CI constraints.

**Independent Test**: Verify the downloaded map exists with correct Nside=2048, mask application excludes correct regions, and the Nside=128 downgraded map fits in <100MB RAM and has no NaN/inf values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T011 [P] [US1] Unit test for checksum validation in `tests/test_data_loader.py`
- [~] T012 [P] [US1] Unit test for mask application and pixel exclusion in `tests/test_data_loader.py`
- [~] T013 [P] [US1] Unit test for Nside downgrade memory usage and NaN checks in `tests/test_data_loader.py` <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [ ] T014 [US1] Implement `download_planck_map()` in `code/data_loader.py` to fetch Nside=2048 SMICA map from ESA archive with SHA-256 validation
- [ ] T015 [US1] Implement `apply_galactic_mask()` in `code/data_loader.py` using Commander mask to exclude foregrounds. **Deliverable**: Log mask statistics to `data/processed/mask_stats.json` and raise `ValueError` if unmasked sky retention < 95%. Verify both: (1) ≥95% of masked pixels are excluded, AND (2) remaining unmasked region is ≥95% of the sky.
- [ ] T016 [US1] Implement `downgrade_resolution()` in `code/data_loader.py` to convert masked map to Nside=128 using healpy
- [ ] T017 [US1] Add error handling for URL unavailability and checksum mismatches in `code/data_loader.py`
- [ ] T018 [US1] Add logging for data ingestion steps in `code/data_loader.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Compute spherical harmonic decomposition and angular power spectrum (Priority: P1)

**Goal**: Compute a_lm coefficients and C_l spectra for full sky and hemispherical splits using the MASTER algorithm.

**Independent Test**: Compute C_l from a known isotropic simulation and verify recovery within 1% error; verify hemispherical splits produce valid spectra.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for `map2alm` stability and range [2, 128] in `tests/test_harmonics.py`
- [ ] T020 [P] [US2] Unit test for C_l positivity and length () in `tests/test_harmonics.py`
- [ ] T021 [P] [US2] Integration test for hemispherical split generation in `tests/test_harmonics.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement `compute_alm()` in `code/harmonics.py` using healpy `map2alm` with `iter=3` for l ∈ [low, 128]. **DEPENDS ON T016** (downgraded map must be ready).
- [ ] T023 [US2] Implement `compute_full_sky_cl()` in `code/harmonics.py` to derive C_l from a_lm
- [ ] T024 [US2] Implement `split_hemispheres()` in `code/harmonics.py` to generate North/South and East/West pixel masks
- [ ] T025 [US2] Implement `compute_hemisphere_cl()` in `code/harmonics.py` using pseudo-C_l (MASTER) estimator to correct for mode coupling. **DEPENDS ON T016 AND T024**.
- [ ] T026 [US2] Integrate hemispherical masks and compute per-axis power spectra in `code/harmonics.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Generate Monte Carlo null distribution and perform statistical test (Priority: P2)

**Goal**: Generate isotropic Gaussian simulations, compute hemispherical variance, and derive p-values using the Maximum Statistic approach.

**Independent Test**: Run analysis on simulated isotropic data to verify uniform p-value distribution; inject anisotropy to verify power (>80% detection).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for `synalm` generation speed (<30s per sim) in `tests/test_simulations.py`
- [ ] T028 [P] [US3] Unit test for hemispherical variance calculation in `tests/test_statistics.py`
- [ ] T029 [P] [US3] Unit test for Maximum Statistic p-value computation in `tests/test_statistics.py`
- [ ] T030 [P] [US3] Unit test for power validation logic (injection/recovery) in `tests/test_statistics.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `generate_isotropic_sims()` in `code/simulations.py` using Planck 2018 best-fit ΛCDM power spectrum and fixed seed
- [ ] T032 [US3] Implement `compute_hemispherical_variance()` in `code/statistics.py` for observed and simulated maps
- [ ] T033 [US3] Implement `build_null_distribution()` in `code/statistics.py` aggregating variance stats from N simulations
- [ ] T034 [US3] Implement `calculate_max_stat_pvalue()` in `code/statistics.py` using the maximum of N/S and E/W asymmetries.
- [ ] T035 [US3] Add power validation logic to detect injected anisotropy in `code/statistics.py`
- [ ] T036 [US3] Add logging for simulation progress and p-value results in `code/statistics.py`
- [ ] T037 [US3] Implement `generate_power_validation_report()` in `code/statistics.py`. **Deliverable**: Write power validation report to `data/reports/power_validation.json` with keys: `detection_rate`, `threshold`, `n_trials`. Verify detection rate ≥80% for p < 0.05 using Maximum Statistic.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: User Story 4 - Document reproducibility and sensitivity analysis (Priority: P3)

**Goal**: Document code versions, perform threshold sensitivity sweep, and report adjusted p-values.

**Independent Test**: Run pipeline with thresholds {2.5σ, 3.0σ, 3.5σ} and verify documented variation in rejection rates.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T038 [P] [US4] Unit test for sensitivity sweep execution in `tests/test_sensitivity.py`

### Implementation for User Story 4

- [ ] T039 [US4] Implement `run_sensitivity_sweep()` in `code/sensitivity.py` to test thresholds across a range of standard deviations.
- [ ] T040 [US4] Generate `requirements.txt` with pinned versions (healpy, numpy, scipy, astropy) in `code/`
- [ ] T041 [US4] Create `README.md` with sections: Installation, Usage, Data Provenance, and pinned versions of healpy/numpy/scipy.
- [ ] T042 [US4] Implement reporting of uncorrected and Maximum Statistic p-values in `code/main.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Spec Alignment & Polish

**Purpose**: Resolve spec contradictions and perform cross-cutting improvements

- [ ] T043 [P] Code cleanup and refactoring of `code/` scripts
- [ ] T044 [P] Performance optimization for Monte Carlo loop in `code/simulations.py` (Target: Reduce Monte Carlo loop runtime relative to baseline)
- [ ] T045 [P] Refactor `code/harmonics.py` T025 to use vectorized operations
- [ ] T046 [P] Additional unit tests in `tests/` if requested
- [ ] T047 Run `quickstart.md` validation to ensure end-to-end pipeline execution

**Checkpoint**: Project ready for research review

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Spec Alignment)**: No dependencies - MUST complete first.
- **Setup (Phase 1)**: Depends on Phase 0 completion.
- **User Story 1 (Phase 2)**: Depends on Setup completion.
- **User Story 2 (Phase 3)**: Depends on US1 (data) and Setup.
- **User Story 3 (Phase 4)**: Depends on US2 (C_l) and Setup.
- **User Story 4 (Phase 5)**: Depends on US3 (results) and Setup.
- **Spec Alignment (Phase 6)**: Depends on all user stories complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup - No dependencies on other stories.
- **User Story 2 (P1)**: Can start after Setup - Depends on data from US1 (masked/downgraded map).
- **User Story 3 (P2)**: Can start after Setup - Depends on C_l from US2.
- **User Story 4 (P3)**: Can start after Setup - Depends on results from US3.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 1)
- Once Setup phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for checksum validation in tests/test_data_loader.py"
Task: "Unit test for mask application in tests/test_data_loader.py"

# Launch implementation tasks for User Story 1:
Task: "Implement download_planck_map() in code/data_loader.py"
Task: "Implement apply_galactic_mask() in code/data_loader.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Spec Alignment
2. Complete Phase 1: Setup
3. Complete Phase 2: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (data ingestion)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 → Spec aligned
2. Complete Setup → Foundation ready
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Add User Story 4 → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 and Setup together
2. Once Setup is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Harmonics)
 - Developer C: User Story 3 (Statistics)
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
- **Critical Constraint**: All tasks must run on CPU-only CI (a limited number of cores, limited RAM, no GPU). No 8-bit/4-bit quantization or large model loading.
- **Data Integrity**: No fake data generation. All inputs must come from real Planck 2018 SMICA source.
- **Spec Alignment**: Phase 0 tasks (T001-T003) are mandatory prerequisites to ensure spec consistency before implementation.