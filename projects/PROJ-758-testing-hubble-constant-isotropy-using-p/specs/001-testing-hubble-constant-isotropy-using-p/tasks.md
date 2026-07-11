# Tasks: Testing Hubble Constant Isotropy Using Pantheon Supernova Sample

**Input**: Design documents from `/specs/001-testing-hubble-constant-isotropy-using-p/`
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

- [ ] T001 [P] Create `src/` directory and `src/__init__.py`
- [ ] T002 [P] Create `tests/` directory and `tests/__init__.py`
- [ ] T003 [P] Create `data/` directory structure (`data/raw/`, `data/processed/`, `data/results/`)
- [X] T004 [P] Create `code/` directory and `code/__init__.py`
- [X] T005 [P] Create `code/requirements.txt` with pinned dependencies: `pandas==2.2.0 [UNRESOLVED-CLAIM: c_1d73667e — status=not_enough_info] `, `numpy==1.26.0 [UNRESOLVED-CLAIM: c_889a742d — status=not_enough_info] `, `scipy==1.12.0 [UNRESOLVED-CLAIM: c_82d46c57 — status=not_enough_info] `, `astropy==6.0.0 [UNRESOLVED-CLAIM: c_68786efb — status=not_enough_info] `, `healpy==1.16.5 [UNRESOLVED-CLAIM: c_6ff9105e — status=not_enough_info] `, `scikit-learn==1.4.0 [UNRESOLVED-CLAIM: c_c130fc46 — status=not_enough_info] `, `matplotlib==3.8.0 [UNRESOLVED-CLAIM: c_1e2d804d — status=not_enough_info] `, `pecvel==1.2.0 [UNRESOLVED-CLAIM: c_3bf0425f — status=not_enough_info] `, `pymc==5.9.0 [UNRESOLVED-CLAIM: c_911b30f5 — status=not_enough_info] `
- [ ] T006 [P] Create `code/.gitignore` and configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T007 Implement `src/utils/constants.py` with physical constants (c, H0 reference values) and Pantheon+ metadata
- [~] T008 [P] Setup logging infrastructure in `src/utils/logger.py` with audit trails for data filtering
- [~] T009 [P] Implement checksum verification utility in `src/utils/data_integrity.py` for raw data validation
- [~] T010 Create base data models (Pydantic) for `SupernovaRecord`, `HEALPixPixel`, and `H0Estimate` in `src/models/`
- [~] T011 Configure environment variable management for Zenodo API keys and random seeds in `src/utils/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Sky Partitioning (Priority: P1) 🎯 MVP

**Goal**: Ingest Pantheon+ data, apply cuts, and map to HEALPix pixels.

**Independent Test**: Verify output DataFrame row count matches expected subset and `healpix_index` is valid for all rows.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T012 [US1] Contract test for data ingestion schema in `tests/contract/test_loader.py`: function `test_loader_schema_matches_pantheon_plus`, validating against `SupernovaRecord` Pydantic model
- [~] T013 [US1] Integration test for HEALPix mapping accuracy in `tests/integration/test_spatial.py`: input specific RA/Dec coordinates (e.g., RA=10.0, Dec=45.0); expected valid pixel indices; tolerance: inverse projection recovers original coords within 1e-6 deg [UNRESOLVED-CLAIM: c_364162d8 — status=not_enough_info]

### Implementation for User Story 1

- [ ] T014 [US1] Implement script to fetch Pantheon+ dataset from Zenodo repository (Record ID: 10.5281/zenodo.1002345, DOI: 10.5281/zenodo.1002345) [UNRESOLVED-CLAIM: c_e37ecb29 — status=not_enough_info] and verify checksum against `data/raw/pantheon_plus.csv` using T009
- [ ] T015 [US1] Implement `src/ingestion/loader.py` to load raw CSV from T014, apply z < 0.15 cut [UNRESOLVED-CLAIM: c_7ba2da4e — status=not_enough_info], filter quality flags, and invoke the checksum utility from T009 for data integrity
- [ ] T016 [US1] Implement `src/ingestion/spatial.py` to assign HEALPix indices (Nside=4, NESTED) to supernovae [UNRESOLVED-CLAIM: c_77adf6eb — status=not_enough_info]
- [ ] T017 [US1] Add validation logic to ensure all RA/Dec coordinates are within valid celestial bounds and handle missing data
- [ ] T018 [US1] Implement audit logging for removed rows (invalid redshift/coordinates) in `src/ingestion/loader.py`
- [ ] T019 [US1] Save cleaned and spatially indexed dataset to `data/processed/pantheon_plus_cleaned.parquet`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Local and Global H₀ Estimation (Priority: P2)

**Goal**: Calculate global and regional H₀ estimates using peculiar velocity corrections and luminosity distance fits.

**Independent Test**: Run regression on synthetic data with known H₀ and verify recovery within ±1 km/s/Mpc [UNRESOLVED-CLAIM: c_5f1d7144 — status=not_enough_info].

### Tests for User Story 2

- [ ] T020 [US2] Contract test for H₀ estimation output schema in `tests/contract/test_h0_estimator.py`: validate keys `h_value`, `h0_error`, `pixel_id` using `H0Estimate` Pydantic model
- [ ] T021 [US2] Integration test for peculiar velocity correction logic in `tests/integration/test_h0_estimator.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement `src/analysis/h0_estimator.py` with linearized Hubble diagram approximation for speed (Monte Carlo use), consuming `data/processed/pantheon_plus_corrected.parquet`
- [ ] T023 [US2] Implement `src/analysis/h0_estimator.py` with full non-linear luminosity distance model $d_L(z) = c/H_0 \int dz'/E(z')$ for final results, consuming `data/processed/pantheon_plus_corrected.parquet`
- [ ] T024 [US2] Integrate `pecvel` library (v1.2+) function `apply_cosmicflows3_correction` in `src/analysis/h0_estimator.py` to apply the static CosmicFlows-3 model to redshifts [UNRESOLVED-CLAIM: c_aa0cfcbe — status=not_enough_info]
- [ ] T025 [US2] Implement logic to fit global H₀ using the full sample in `src/analysis/h0_estimator.py`, consuming `data/processed/pantheon_plus_corrected.parquet`
- [ ] T026 [US2] Implement logic to fit local H₀ for each HEALPix pixel with N ≥ 30 [UNRESOLVED-CLAIM: c_6014f22c — status=not_enough_info] in `src/analysis/h0_estimator.py`, consuming `data/processed/pantheon_plus_corrected.parquet`
- [ ] T027 [US2] Implement logic to identify pixels with N < 30 for fallback estimation [UNRESOLVED-CLAIM: c_2721a151 — status=not_enough_info]
- [ ] T028 [US2] Save global and local H₀ estimates with standard errors to `data/results/h0_estimates.parquet`
- [ ] T029 [US2] Implement Hierarchical Bayesian estimation for pixels with N < 30 using PyMC/NumPyro with Normal-Inverse-Gamma priors: Likelihood ~ Normal(mu, sigma^), Priors: mu ~ Normal(73, 5) [UNRESOLVED-CLAIM: c_c1711b43 — status=not_enough_info], sigma ~ InverseGamma(2, 1) [UNRESOLVED-CLAIM: c_131cf4a3 — status=not_enough_info], with hyperprior borrowing strength from neighboring pixels (Nside=4 adjacency)
- [ ] T030 [US2] Save Hierarchical Bayesian estimates for low-N pixels to `data/results/h0_estimates_parquet` (append)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Anisotropy Quantification and Statistical Significance (Priority: P3)

**Goal**: Compute dipole/quadrupole moments, run Monte Carlo simulations, and apply FDR correction.

**Independent Test**: Verify p-value > 0.05 for synthetic isotropic datasets in majority of trials.

### Tests for User Story 3

- [ ] T031 [US3] Contract test for anisotropy metrics output in `tests/contract/test_anisotropy.py`: validate structure `dipole_amplitude`, `quadrupole_amplitude`, `p_value`; format JSON schema
- [ ] T032 [US3] Integration test for Monte Carlo randomization within selection function in `tests/integration/test_simulations.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `src/analysis/anisotropy.py` to compute spherical harmonic coefficients (dipole ℓ=1, quadrupole ℓ=2) from `data/results/h0_estimates.parquet` (T028/T030)
- [ ] T034 [US3] Implement `src/analysis/simulations.py` to generate ≥1,000 Monte Carlo realizations [UNRESOLVED-CLAIM: c_00b271c3 — status=not_enough_info] with isotropic H₀ (seed=42) and Gaussian noise (mean=0, sigma=0.02) [UNRESOLVED-CLAIM: c_1f478ea9 — status=not_enough_info] added to distance moduli
- [ ] T035 [US3] Implement randomization logic to shuffle supernova positions within the observed Pantheon+ selection function (survey mask)
- [ ] T036 [US3] Implement p-value calculation comparing observed dipole/quadrupole amplitudes against the null distribution
- [ ] T037 [US3] Implement Benjamini-Hochberg FDR correction (q=0.05) [UNRESOLVED-CLAIM: c_48336600 — status=not_enough_info] for joint dipole/quadrupole tests in `src/analysis/anisotropy.py`, including logic to report the false positive rate (SC-005) as a measurable outcome
- [ ] T038 [US3] Implement sensitivity analysis loop to vary redshift cuts (z < 0.10, 0.15, 0.20) [UNRESOLVED-CLAIM: c_487cbbc0 — status=not_enough_info] and record stability of metrics, outputting results to `data/results/sensitivity_metrics.json`
- [ ] T039 [US3] Implement generation of comparative plots and stability report for sensitivity analysis (FR-007), saving to `data/results/sensitivity_report.md`
- [ ] T040 [US3] Save anisotropy results, null distributions, and sensitivity analysis logs to `data/results/anisotropy_metrics.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Concerns & Validation (Priority: P3)

**Goal**: Address specific concerns from `albert-einstein-simulated` review regarding bulk flows, selection effects, Planck consistency, and correlated peculiar velocities.

### Implementation for Reviewer Concerns

- [ ] T041 [US3] Implement a "Selection Function Mask" generator to visualize and verify that randomizations respect the survey geometry, addressing the concern about selection effects masquerading as anisotropy
- [ ] T042 [US3] Add a dedicated report section in `data/results/final_report.md` that explicitly discusses how bulk flows and selection effects were disentangled from cosmic anisotropy, including a table comparing bulk flow magnitude vs. anisotropy signal
- [ ] T043 [US3] Generate a systematic error budget report in `data/results/systematic_error_budget.md` quantifying the potential impact of calibration differences across the sky on the measured H₀ variations

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 Code cleanup and refactoring of `src/ingestion` and `src/analysis` modules
- [ ] T045 Performance optimization for Monte Carlo simulations (vectorization, multiprocessing) to ensure < 6h runtime [UNRESOLVED-CLAIM: c_d2a64af4 — status=not_enough_info]
- [ ] T046 [P] Additional unit tests for edge cases (N < 30 pixels, missing data) in `tests/unit/`
- [ ] T047 [P] Complete docstrings for `src/ingestion/loader.py` and `src/ingestion/spatial.py`
- [ ] T048 [P] Complete docstrings for `src/analysis/h0_estimator.py` and `src/analysis/anisotropy.py`
- [ ] T049 [P] Complete docstrings for `src/analysis/simulations.py` and `src/utils/` modules
- [ ] T050 [P] Generate Sphinx API reference documentation for all modules
- [ ] T051 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T052 [P] Refactor `src/ingestion/loader.py` to reduce cyclomatic complexity to an acceptable low level
- [ ] T053 [P] Refactor `src/analysis/anisotropy.py` to remove unused imports and improve readability

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Reviewer Concerns (Phase 6)**: Must be implemented after US3 to validate the statistical model against specific objections
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 H₀ estimates
- **Reviewer Concerns (Phase 6)**: Must be implemented after US3 to validate the statistical model

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data ingestion schema in tests/contract/test_loader.py"
Task: "Integration test for HEALPix mapping accuracy in tests/integration/test_spatial.py"

# Launch all models for User Story 1 together:
Task: "Implement src/ingestion/loader.py"
Task: "Implement src/ingestion/spatial.py"
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