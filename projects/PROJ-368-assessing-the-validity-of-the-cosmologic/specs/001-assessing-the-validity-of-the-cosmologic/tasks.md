---
description: "Task list template for feature implementation"
---

# Tasks: Assessing the Validity of the Cosmological Principle with Public CMB Data

**Input**: Design documents from `/specs/001-assessing-the-validity-of-the-cosmologic/`
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

## Phase 0: Spec Alignment Verification (Blocking Gate)

**Purpose**: Verify that `spec.md` and `plan.md` are consistent regarding the statistical method (Maximum Statistic) before implementation begins.

**CRITICAL**: This phase MUST be completed and verified BEFORE any other task (including T004) is executed.

- [ ] T001 [P] Verify `spec.md` US3 and Statistical Method sections explicitly state "Maximum Statistic approach" and "Benjamini-Hochberg correction is NOT used". Compare with `plan.md` implementation.
 **Logic**:
 1. Read `spec.md` text for US3 and Statistical Method. Confirm "Benjamini-Hochberg correction is NOT used" is present.
 2. Read `plan.md` Summary and Technical Context. Confirm the plan implements "Maximum Statistic".
 3. Read `plan.md` "Note on Spec Conflict". Check if it claims the spec *mandates* BH.
 4. **Resolution**: Since the Spec explicitly forbids BH and the Plan implements Maximum Statistic, the Spec and Plan are ALIGNED on the method.
 5. **Documentation Error Check**: If the Plan's "Note on Spec Conflict" claims a contradiction exists (e.g., "Spec mandates BH"), this is a documentation error in the Plan.
 6. Generate `data/reports/spec_alignment_log.txt` with: "Spec Alignment Verified: Spec and Plan both mandate Maximum Statistic. Plan's 'Note on Spec Conflict' is flagged as a documentation error (incorrectly claims Spec mandates BH)."
 7. If `spec.md` says BH IS used (contradicting the current plan's method), HALT and output error "Spec/Plan Mismatch: Statistical Method Conflict".
 **Deliverable**: `data/reports/spec_alignment_log.txt` (on success or warning) or HALT (on failure).

**Checkpoint**: Spec artifacts are consistent with the plan (or the plan's error is flagged). Implementation tasks may now proceed.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T004 [P] Create all project directories: `mkdir -p data/raw data/processed data/simulations data/reports code tests`. **Verification**: Run `ls -R data code tests` to confirm the exact tree structure exists.
- [X] T005 [P] Create `code/pyproject.toml` with a compatible Python version (>=3.9), build system configuration (e.g., setuptools), and pinned dependencies: `healpy`, `numpy`, `scipy`, `astropy`, `requests`, `pyyaml`. **Requirement**: Explicitly pin versions using a `pip-tools` or `poetry` lockfile strategy (e.g., `pip-tools compile` to generate a `requirements.txt` with exact versions, or `poetry lock`), or by specifying exact version numbers (e.g., `healpy==1.16.2`, `numpy==1.26.0`) to ensure exact reproducibility as per Constitution Principle I. The task must ensure the final dependency list contains specific version numbers.
- [X] T007 Create `code/config.py` defining paths, random seeds, Nside constants, simulation counts, and **filename constants** for all data artifacts (e.g., `PROCESSED_MAP_FILENAME`, `MASK_STATS_FILENAME`, `MASK_VALIDATION_FILENAME`).
- [ ] T008 [Depends on T004] Initialize git repository: `git init`. **Verification**: Create `.gitignore` with `data/`, `__pycache__/`, `*.pyc`, `*.log`. Run `git add.` and `git commit -m "Initial project structure"`.
- [X] T009 [P] Create `code/logging_config.py` implementing JSON format logging at INFO level.
- [X] T010 Create `tests/test_config.py` to validate configuration constants and paths.

**Checkpoint**: Foundation ready - user story implementation can now begin. Note: US1 must complete before US2; US2 before US3.

---

## Phase 2: User Story 1 - Acquire and preprocess public Planck CMB data (Priority: P1) 🎯 MVP

**Goal**: Download, validate, mask, and downgrade the Planck SMICA CMB map to fit CI constraints.

**Independent Test**: Verify the downloaded map exists with correct Nside=2048, mask application excludes correct regions, and the Nside=128 downgraded map fits in <100MB RAM and has no NaN/inf values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Unit test for checksum validation in `tests/test_data_loader.py`.
- [X] T012 [P] [US1] Unit test for mask application and pixel exclusion in `tests/test_data_loader.py`.
- [X] T013 [P] [US1] Unit test for Nside downgrade memory usage and NaN checks in `tests/test_data_loader.py`.

### Implementation for User Story 1

- [X] T014 [US1] Implement `download_planck_map()` in `code/data_loader.py` to fetch Nside=2048 SMICA map from ESA archive with SHA-256 validation.
- [X] T015 [Depends on T014] [US1] Implement `apply_galactic_mask()` in `code/data_loader.py` using Commander mask. **Requirement**: <!-- FAILED: unspecified -->
 1. **Fetch**: Use `healpy` or `astropy` standard loaders to fetch the Commander mask (e.g., `COM_Mask_R3.011_CMB.fits`) from the Planck archive. Do NOT hardcode specific URLs unless verified by the loader's internal resolution.
 2. **Pre-validate**: Calculate the unmasked sky fraction of the fetched mask *before* applying it to the data.
 3. **Constraint Check**: If retention < 95%, raise `ValueError` with a message detailing the actual retention %. **DO NOT** fallback to U81 or any other mask. The spec requires the Commander mask specifically. If the fetch fails or the mask is missing, raise an error immediately.
 4. If retention >= 95%, apply the mask.
 5. Save masked map to `data/processed/masked_n2048.fits`.
 6. Save mask statistics (retention %, mask filename) to `data/processed/mask_stats.json`.
 7. Save pre-validation report to `data/processed/mask_validation_report.json`.
 **Verification**: Verify `mask_validation_report.json` confirms retention >= 95% and `mask_stats.json` contains valid data.
- [ ] T016 [Depends on T015] [US1] Implement `downgrade_resolution()` in `code/data_loader.py` to convert masked map (from `data/processed/masked_n2048.fits`) to Nside=128 using healpy. <!-- FAILED: unspecified -->
- [X] T017 [P] [US1] Add error handling for URL unavailability and checksum mismatches in `code/data_loader.py`.
- [X] T018 [P] [US1] Add logging for data ingestion steps in `code/data_loader.py`.
- [X] T019 [P] [US1] Implement `save_processed_map()` in `code/data_loader.py` to write the final Nside=128 map to `data/processed/{config.PROCESSED_MAP_FILENAME}` with FITS header metadata including provenance and checksum. **Verification**: Verify file exists, size < 150MB, and FITS header contains `provenance` and `checksum` keys.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. **US2 cannot start until T019 is complete.**

---

## Phase 3: User Story 2 - Compute spherical harmonic decomposition and angular power spectrum (Priority: P1)

**Goal**: Compute a_lm coefficients and C_l spectra for full sky and hemispherical splits using the MASTER algorithm.

**Independent Test**: Compute C_l from a known isotropic simulation and verify recovery within 1% error; verify hemispherical splits produce valid spectra.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for `map2alm` stability and range [2, 128] in `tests/test_harmonics.py`.
- [X] T021 [P] [US2] Unit test for C_l positivity and length (l_max - l_min + 1) in `tests/test_harmonics.py`.
- [X] T022 [P] [US2] Integration test for hemispherical split generation in `tests/test_harmonics.py`.

### Implementation for User Story 2

- [X] T023 [US2] Implement `compute_alm()` in `code/harmonics.py` using healpy `map2alm` with `iter=3` for l ∈ [small, 128]. **DEPENDS ON T019** (processed map file must exist).
- [ ] T024 [Depends on T019, T023] [US2] Implement `compute_full_sky_cl()` in `code/harmonics.py` to derive C_l from a_lm. **Deliverable**: Save to `data/reports/full_sky_cl.npy`.
- [ ] T025 [US2] Implement `split_hemispheres()` in `code/harmonics.py` to generate North/South and East/West pixel masks. **Verification**: Verify mask pixel counts match expected hemispherical fractions.
- [ ] T026 [Depends on T019, T025] [US2] Implement `compute_hemisphere_cl()` in `code/harmonics.py` using pseudo-C_l (MASTER) estimator to correct for mode coupling. **Deliverable**: Save N/S and E/W spectra to `data/reports/hemisphere_cl.npy`.
- [ ] T027 [P] [US2] Integrate hemispherical masks and compute per-axis power spectra in `code/harmonics.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. **US3 cannot start until T024 is complete.**

---

## Phase 4: User Story 3 - Generate Monte Carlo null distribution and perform statistical test (Priority: P2)

**Goal**: Generate isotropic Gaussian simulations, compute hemispherical variance, and derive p-values using the Maximum Statistic approach.

**Independent Test**: Run analysis on simulated isotropic data to verify uniform p-value distribution; inject anisotropy to verify power.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for `synalm` generation speed (<30s per sim) in `tests/test_simulations.py`.
- [ ] T029 [P] [US3] Unit test for hemispherical variance calculation in `tests/test_statistics.py`.
- [ ] T030 [P] [US3] Unit test for Maximum Statistic p-value computation in `tests/test_statistics.py`.

### Implementation for User Story 3

- [ ] T032 [Depends on T024, T019] [US3] Implement `generate_isotropic_sims` in `code/simulations.py` using Planck best-fit ΛCDM power spectrum (from T024) and fixed seed. **Constraint**: Generate N=1000 simulations as defined in the Plan's 'Technical Context'. **Justification**: N=1000 is the constant defined in the Plan to ensure reproducibility and sufficient sampling for the Maximum Statistic test. **Deliverable**: Save simulations to `data/simulations/` (or stream if memory constrained).
- [ ] T033 [Depends on T032, T019] [US3] Implement `compute_hemispherical_variance()` in `code/statistics.py` for observed and simulated maps. **Requirement**: Compute variance of power in the l=2..128 range for each hemisphere.
- [ ] T034 [Depends on T033] [US3] Implement `build_null_distribution()` in `code/statistics.py` aggregating variance stats from N simulations. **Deliverable**: Save distribution to `data/reports/null_distribution.npy`.
- [ ] T035 [Depends on T034, T033] [US3] Implement `calculate_max_stat_pvalue()` in `code/statistics.py` using the maximum of N/S and E/W asymmetries. **Logic**: T_obs = max(A_NS_obs, A_EW_obs); p = (count(T_sim >= T_obs) + k) / (N_sims + k), where k is a small integer constant for continuity correction..
- [ ] T037 [P] [US3] Add logging for simulation progress and p-value results in `code/statistics.py`.
- [ ] T038 [Depends on T035] [US3] Implement `generate_power_validation_report()` in `code/statistics.py`. **Deliverable**: Write power validation report to `data/reports/power_validation.json` with keys: `detection_rate`, `threshold`, `n_trials`. Document the observed detection rate.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 5: User Story 4 - Document reproducibility and sensitivity analysis (Priority: P3)

**Goal**: Document code versions, perform threshold sensitivity sweep, and report adjusted p-values.

**Independent Test**: Run pipeline with a range of significance thresholds. and verify documented variation in rejection rates.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T039 [P] [US4] Unit test for sensitivity sweep execution in `tests/test_sensitivity.py`.

### Implementation for User Story 4

- [ ] T040 [Depends on T038] [US4] Implement `run_sensitivity_sweep()` in `code/sensitivity.py` to test thresholds across values defined in `config.py`. **Requirement**: Read threshold values (e.g., sigma levels or p-value cutoffs) from `config.py` (default to a reasonable range if not specified) and record p-values for each. The task must not hardcode specific sigma values; it must use the range defined in the configuration.
- [ ] T041 [P] [US4] Create `README.md` with sections: Installation, Usage, Data Provenance, and pinned versions of healpy/numpy/scipy.
- [ ] T042 [P] [US4] Implement reporting of uncorrected and Maximum Statistic p-values in `code/main.py`. **Deliverable**: Final report printed to stdout and saved to `data/reports/final_results.json`.
- [ ] T043 [Depends on T040] [US4] Implement `generate_sensitivity_report()` in `code/sensitivity.py`. **Deliverable**: Save to `data/reports/sensitivity_report.json` containing the sweep results.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Spec Alignment & Polish

**Purpose**: Resolve spec contradictions and perform cross-cutting improvements

- [ ] T044 [P] Code cleanup and refactoring of `code/` scripts.
- [ ] T045 [P] Additional unit tests in `tests/` if requested.
- [ ] T046 Run `quickstart.md` validation to ensure end-to-end pipeline execution.

**Checkpoint**: Project ready for research review

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Spec Alignment)**: No dependencies - MUST complete first.
- **Setup (Phase 1)**: Depends on Phase 0 completion.
- **User Story 1 (Phase 2)**: Depends on Setup completion.
- **User Story 2 (Phase 3)**: Depends on US1 (data) and Setup. **Cannot run in parallel with US1**.
- **User Story 3 (Phase 4)**: Depends on US2 (C_l) and Setup. **Cannot run in parallel with US2**.
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

- All Setup tasks marked [P] can run in parallel (except T008 which depends on T004).
- All Foundational tasks marked [P] can run in parallel (within Phase 1).
- **User Stories are SERIAL**: US1 must complete before US2; US2 must complete before US3. They cannot run in parallel due to data flow dependencies.
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for checksum validation in tests/test_data_loader.py"
Task: "Unit test for mask application in tests/test_data_loader.py"

# Launch implementation tasks for User Story 1:
Task: "Implement download_planck_map() in code/data_loader.py"
Task: "Implement apply_galactic_mask() in code/data_loader.py" (Depends on T014)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Spec Alignment Check
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
 - Developer B: User Story 2 (Harmonics) - **Wait for US1 completion**
 - Developer C: User Story 3 (Statistics) - **Wait for US2 completion**
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except explicit overrides)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only CI (a limited number of cores, limited RAM, no GPU). No 8-bit/4-bit quantization or large model loading.
- **Data Integrity**: No fake data generation. All inputs must come from real Planck SMICA source.
- **Spec Alignment**: Phase 0 task (T001) is a mandatory verification step to ensure spec consistency before implementation. It now correctly validates that the Spec and Plan agree on Maximum Statistic, while flagging the Plan's "Note on Spec Conflict" as a documentation error.
- **Dependencies**: US2 strictly depends on US1; US3 strictly depends on US2. Parallel execution between stories is NOT supported.
- **Data Streaming**: If the full Nside=2048 map download fails or exceeds memory during processing, the loader must fail loudly (raise an error) rather than falling back to synthetic data. The execution stage will handle retrying with verified real data sources.
- **Performance Optimization**: Removed T006 and T036 as they were not traceable to spec requirements. Focus on functional correctness first.
- **Mask Validation**: Task T015 now strictly enforces the Commander mask requirement and fails loudly if retention <95%, removing unauthorized fallbacks.
- **Statistical Power**: Task T032 explicitly defines N=1000 as per the Plan's Technical Context, removing unverified power analysis claims.
- **Sensitivity Sweep**: Task T040 now reads thresholds from `config.py`, removing hardcoded values and allowing researcher discretion.
- **Parallel Tags**: All tasks with explicit dependencies (e.g., T015, T016, T024, T026, T032, T033, T034, T035, T040) have had their [P] tags removed to prevent incorrect parallel execution.