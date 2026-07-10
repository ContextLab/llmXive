# Tasks: Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data

**Input**: Design documents from `/specs/001-testing-the-isotropy-of-cosmic-expansion/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure explicitly including directories: `data/raw`, `data/processed`, `code`, `tests/unit`, `tests/integration`, `tests/contract`, `docs`, `reports`
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt`. **MUST create `requirements.txt` containing specific version-pinned packages (e.g., `astropy>=6.0,<7.0`, `healpy>=1.16.0,<2.0.0`). If the plan's Technical Context lists packages without specific versions, the task MUST run `pip-compile` to resolve compatible versions and pin them.**
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/utils.py` with helper functions for cosmological calculations and file I/O
- [ ] T006 [P] Setup `pytest` configuration and directory structure (`tests/unit/`, `tests/integration/`, `tests/contract/`)
- [ ] T007 Create base data models (dataclasses) in `code/models.py` for `SupernovaRecord`, `HealpixPixel`, `HarmonicCoefficient`
- [~] T008 Configure environment variable loading for `code/main.py` and simulation seeds
- [~] T009 Implement logging infrastructure in `code/utils.py` to track excluded entries and processing steps

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Data Ingestion and Residual Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest Pantheon+ data, calculate residuals against flat ΛCDM, apply redshift cuts, and map to sky coordinates.

**Independent Test**: Verify output CSV row count matches Pantheon+ 'full' sample (within redshift cuts) and residuals match manual calculation for a known subset.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Contract test for `data/processed/residuals.csv` schema in `tests/contract/test_residuals.py`
- [~] T011 [P] [US1] Integration test verifying row count and coordinate validity in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [~] T012 [US1] Implement `code/ingest.py` to download Pantheon+ v1.0 from official repository (handling checksum verification)
- [~] T012a [Rev] Update `plan.md` Summary and Technical Context to explicitly state that residuals are calculated using the **flat ΛCDM model** via numerical integration, removing the contradictory "model-independent spline fit" reference. **Dependencies: T012**
- [ ] T013 [US1] Implement filtering logic in `code/ingest.py` to exclude entries with missing RA, Dec, redshift, or distance modulus
- [ ] T005 [US1] Implement `code/utils.py` function to **automatically extract cosmological parameters ($H_, \Omega_m$) from the Pantheon+ dataset metadata (JSON format, keys: `cosmology.H0`, `cosmology.Omega_m`)** with fallback to the release paper values if missing, and record dataset version and checksums. **Dependencies: T012**
- [ ] T014 [US1] Implement `code/ingest.py` function to calculate theoretical distance modulus $\mu_{th}$ via **numerical integration using `scipy.integrate.quad` with `rtol=1e-8`** of the inverse Hubble parameter $1/E(z)$, **extracting $H_0, \Omega_m$ from Pantheon+ metadata** (with fallback to release paper values) as mandated by FR-002. **Dependencies: T005**
- [ ] T015 [US1] Implement `code/ingest.py` function to compute observed residuals $\mu_{obs} - \mu_{th}$
- [ ] T016 [US1] Write filtered and processed data to `data/processed/residuals.csv` with columns: ID, RA, Dec, z, $\mu_{obs}$, $\sigma_{\mu}$, $\mu_{th}$, residual
- [ ] T017 [US1] Add logging in `code/ingest.py` to record the count of excluded supernovae and reasons

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Spherical Harmonic Decomposition and Dipole/Quadrupole Extraction (Priority: P2)

**Goal**: Project residuals onto HEALPix grid and extract dipole/quadrupole amplitudes via the Spec-mandated pseudo-C_l method with MASTER correction.

**Independent Test**: Verify extracted amplitudes match a synthetic dataset with an injected dipole signal within statistical error.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US2] Contract test for `data/processed/pseudo_cl_results.json` schema in `tests/contract/test_pseudo_cl_results.py`

### Implementation for User Story 2 - Method: Spec-Mandated pseudo-C_l (FR-003, FR-004)

- [ ] T026a [US2] Implement `code/spherical_harmonics.py` function to project `data/processed/residuals.csv` onto HEALPix grid (**Nside=32**) by converting RA/Dec to pixel indices. **Dependencies: T016**
- [ ] T026b [US2] Implement `code/spherical_harmonics.py` function to **bin residuals per pixel** (aggregate mean residual for each pixel). **Dependencies: Ta**
- [ ] T026a [Rev] Update `plan.md` Summary and Technical Context to explicitly state **HEALPix resolution Nside=32**, removing the contradictory "Nside=16" reference. **Dependencies: T026b**
- [ ] T027 [US2] Implement `code/spherical_harmonics.py` function `compute_pseudo_cl` to calculate harmonic coefficients $a_{\ell m}$ for **low-order multipoles** using the pseudo-C_l method with MASTER correction to account for the survey mask. **Dependencies: T026b**
- [ ] T028 [US2] Extract scalar amplitudes for dipole ($\ell=1$) and quadrupole ($\ell=2$) from pseudo-C_l coefficients and write to `data/processed/pseudo_cl_results.json`. **Dependencies: T027**
- [ ] T021 [Rev] Update `data/metadata.json` to include a `measurement_protocol` section with keys: `method: pseudo-C_l`, `correction: MASTER`, `resolution: Nside=32`. **Dependencies: T028**
- [ ] T029 [US2] Implement visualization helper in `code/utils.py` to generate a sky map (**Nside=16**) of residuals for `reports/sky_map.png` by **re-projecting the Nside=32 data** from T026b to a lower resolution for visualization. **Dependencies: T026b**

### Reproducibility Validation (SC-002)

- [ ] T032 [US2] Implement test in `tests/integration/test_reproducibility.py` to generate a synthetic HEALPix map with a known injected dipole, run the pseudo-C_l + MASTER pipeline, and verify the recovered amplitude matches the injected value within 1e-3 mag. **Dependencies: T028**

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently

---

## Phase 5: User Story 3 - Null Distribution Simulation and Significance Assessment (Priority: P3)

**Goal**: Generate isotropic mock catalogs via Spec-mandated Rotation Matrices (FR-005), compute null distribution, and derive p-values.

**Independent Test**: {{claim:c_3120b814}} (95% confidence).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Contract test for `data/processed/null_distribution.csv` schema in `tests/contract/test_null_dist.py`
- [ ] T034 [P] [US3] Integration test verifying p-value > 0.05 for isotropic input in `tests/integration/test_significance.py`

### Implementation for User Story 3

- [ ] T035 [US3] Implement `code/simulations.py` to generate random rotation matrices for coordinate transformation. **Dependencies: None**
- [ ] T036 [US3] Implement `code/simulations.py` to derive a binary survey mask from Pantheon+ RA/Dec density: pixels with >0 supernovae are set to 1 (non-empty), others to 0. **MUST use Nside=32 resolution to match analysis.** **Dependencies: T013**
- [ ] T037a [US3] Implement `code/simulations.py` function to **define rotation logic** for applying random 3D rotation matrices to celestial coordinates (RA, Dec). **Dependencies: T035, T036**
- [ ] T037b [US3] Implement the **rotation simulation loop**: apply T037a to generate N=10,000 iterations of rotated catalogs, compute dipole/quadrupole amplitudes for each, and stream results to `data/processed/null_distribution.csv` with schema **`run_id, dipole_amp, quadrupole_amp, converged`**. **Include logic to programmatically measure the running mean change (absolute difference in mag) over the last 1,000 simulations and set a 'converged' flag if change < 0.001 mag. Do NOT halt the loop; continue to N=10,000 or until runtime limit is reached.** **Dependencies: T037a**
- [ ] T040 [US3] Implement `code/main.py` logic to compare observed amplitudes (from T028) against the null distribution (T037b), **calculate p-values, compare against the significance threshold, and output the 'significant' flag** as mandated by FR-006. **Dependencies: T028, T037b**
- [ ] T041 [US3] Implement `code/main.py` logic to flag result as "statistically significant anisotropy" if p-value < 0.05. **Dependencies: T040**
- [ ] T042 [US3] Generate final report in `reports/analysis_report.md` summarizing **p-values, amplitudes, significance status, and runtime**. **Must include sections: 'Observed Amplitudes', 'Null Distribution Statistics', 'P-Value Calculation', 'Significance Flag', and 'Systematic Error Discussion' (qualitative, based on literature).** **Dependencies: T041**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Review Revision - Documentation, Systematics & Protocol (Priority: P3)

**Goal**: Address specific reviewer concerns regarding measurement protocol, redshift ranges, systematic error handling, and cross-calibration details (Marie Curie Review).

### Implementation for Revision Concerns (Marie Curie Review)

- [ ] T043 [Rev] Update `code/ingest.py` to explicitly document and log the photometric systems used (SDSS, SNLS, etc.) and the light-curve fitter (SALT2) parameters applied, ensuring traceability to the Pantheon+ release paper. **Dependencies: T012**
- [ ] T045 [Rev] Update `data/metadata.json` to include a `cross_calibration` section detailing the method for harmonizing photometric systems across different surveys (e.g., color corrections). **Dependencies: T016**
- [ ] T046 [Rev] Update `reports/analysis_report.md` template to include a dedicated section for "Systematic Error Analysis" and "Measurement Protocol" as requested by the reviewer. **Dependencies: T042**
- [ ] T047 [Rev] Update `README.md` and `docs/quickstart.md` to document the pseudo-C_l method, the specific redshift range (filtering only for missing values per Spec Assumptions), and the resolution of the spec/plan conflict regarding systematics. **Dependencies: T042**
- [ ] T054 [Rev] Implement `code/systematics.py` to calculate and log quantitative estimates for extinction (using E(B-V) maps if available in metadata), selection bias (via completeness functions), and calibration drift, as required by the reviewer's request for systematic error quantification. **CRITICAL: These estimates are logged for informational purposes ONLY and MUST NOT be applied to the null distribution generation to preserve the strict isotropic mock catalog definition per Spec Assumptions.** **Dependencies: T016**
- [ ] T055 [Rev] Update `code/main.py` to integrate systematic error estimates (T054) into the final `reports/analysis_report.md`, explicitly stating how these factors influence the confidence in the isotropy test result. **Dependencies: T042, T054**

**Checkpoint**: Review concerns addressed; system now explicitly handles measurement protocol, systematics, and cross-calibration.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Documentation updates in `README.md` and `docs/quickstart.md`
- [ ] T049 Code cleanup and refactoring for readability
- [ ] T050 Performance optimization for simulation loop (ensure < 6h runtime on CPU)
- [ ] T051 [P] Additional unit tests for numerical accuracy in `tests/unit/`
- [ ] T052 Security hardening (ensure no hardcoded credentials)
- [ ] T053 Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **Strict Sequential Order**: User Story 1 (P1) -> User Story 2 (P2) -> User Story 3 (P3).
 - **Note**: US2 depends on US1 output (residuals.csv). US3 depends on US2 output (amplitudes).
 - **Parallelism**: Only tasks marked [P] within the same phase can run in parallel. Tasks across phases MUST run sequentially.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: **Strictly depends** on US1 data output (T016). Cannot start until US1 completes.
- **User Story 3 (P3)**: **Strictly depends** on US2 observed amplitudes (T028). Cannot start until US2 completes.
- **Revision (Phase 6)**: Can be implemented in parallel with US1/US2/US3 but must be merged before final release.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- **Note**: Different user stories CANNOT be worked on in parallel if they have strict dependencies (US1 -> US2 -> US3).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for residuals.csv schema in tests/contract/test_residuals.py"
Task: "Integration test verifying row count and coordinate validity in tests/integration/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Create SupernovaRecord dataclass in code/models.py"
Task: "Create HealpixPixel dataclass in code/models.py"
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

### Sequential Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Must complete before Developer B starts)
 - Developer B: User Story 2 (Starts only after US1 is complete)
 - Developer C: User Story 3 (Starts only after US2 is complete)
3. Stories complete and integrate sequentially.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Revision Note**: Phase 6 tasks (T043-T047, T021, T054, T055) specifically address the "Marie Curie" reviewer concerns regarding measurement protocol, redshift ranges, systematic error quantification, and cross-calibration details. **Systematics are documented and quantified (T054) but NOT applied to the null distribution generation to preserve the strict isotropic mock catalog definition.**
- **Spec vs Plan Conflict**: Tasks T026a-T029 implement the Spec requirements (pseudo-C_l, Nside=32) exclusively. MLE and GRF methods have been removed to align with the singular approved methodology. **Plan.md has been updated (T012a, T026a) to reflect these Spec requirements.**
- **Execution Order**: Strict sequential execution is required for US1 -> US2 -> US3 due to data dependencies.
- **Deleted Tasks**: T019 (arbitrary redshift cut) and T044 (systematics correction module) were removed to strictly comply with Spec Assumptions and FR-005.