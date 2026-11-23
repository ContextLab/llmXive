# Tasks: Testing Cosmic Ray Arrival Direction Isotropy with Public Ultra‑High‑Energy Data

**Input**: Design documents from `/specs/001-testing-cosmic-ray-arrival-direction-iso/`
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

- [ ] T001 [P] Initialize project directory structure: Create `projects/PROJ-772-testing-cosmic-ray-arrival-direction-iso/` and subdirectories `code/`, `data/`, `tests/`, `state/`. Create `.gitignore` (excluding `data/`, `__pycache__/`, `*.pyc`, `.env`, `state/projects/*.yaml` except.gitkeep). Initialize `requirements.txt` in `code/` with exact pins: `healpy>=1.16.0`, `numpy>=1.24.0`, `pandas>=2.0.0`, `scipy>=1.10.0`, `astropy>=5.3.0`, `requests>=2.31.0`, `tqdm>=4.65.0`, `pytest>=7.4.0`, `pydantic>=2.0.0`. Setup linting (flake8/black) in `code/.pre-commit-config.yaml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Create `code/config.yaml` with pinned random seeds, dataset versions (Auger DOI: 10.5281/zenodo.3966535, TA: 2023-01), and path definitions.
- [X] T003 [P] Initialize `state/projects/PROJ-772-testing-cosmic-ray-arrival-direction-iso.yaml` with the following exact schema:
 ```yaml
 project_id: PROJ-772-testing-cosmic-ray-arrival-direction-iso
 artifact_hashes: {}
 updated_at: # ISO 8601 timestamp
 ```
 **Note**: This task defines the schema required for T004 to write checksums, satisfying Constitution Principle III.
- [ ] T004 [P] Implement `code/ingestion/checksum.py` to automatically compute SHA-256 hashes for all files in `data/` (raw and processed) and write them to `state/projects/PROJ-772-testing-cosmic-ray-arrival-direction-iso.yaml`. **Success Criterion**: The script must update the `artifact_hashes` map with no manual intervention.
- [ ] T005 [P] Setup logging infrastructure in `code/utils/logging.py` to record event exclusion counts and pipeline steps.
- [ ] T006a [P] Create `code/models/event_catalog.py` with `EventCatalog` class using Pydantic v2: `class EventCatalog(BaseModel): energy: float64 (ge=0), ra: float64 (ge=-180, le=180), dec: float64 (ge=-90, le=90), source: str`.
- [ ] T006b [P] Create `code/models/exposure_map.py` with `ExposureMap` class using Pydantic v2: `class ExposureMap(BaseModel): nside: int, pixel_data: np.ndarray (shape=(12*nside**2,), dtype=float64), detector: str`.
- [ ] T006c [P] Create `code/models/power_spectrum.py` with `PowerSpectrum` class using Pydantic v2: `class PowerSpectrum(BaseModel): ell: List[int], cl: List[float64], p_value: float64 (ge=0, le=1)`.
- [ ] T007 [P] Implement graceful error handling for missing data repositories in `code/ingestion/download_events.py` (raise explicit HTTPError with message "Data repository unavailable: {url}. Aborting pipeline per Constitution Principle I.", NO synthetic fallback). **Success Criterion**: The script must exit with code 1 and print a clear error message if the fetch fails, satisfying the spec's "fail gracefully" edge case.
- [ ] T008a [P] Create/Initialize `research.md` in `specs/001-testing-cosmic-ray-arrival-direction-iso/` if missing, with **specific required sections**:
 1. "Detector Types & Calibration Methods" (must detail laser-based timing, muon tracks, standard candles)
 2. "Integrated Exposure Estimates" (must detail km²·sr·yr values)
 3. "Statistical Test Definitions" (must define Angular Power Spectrum, alpha=0.05)
- [ ] T008b [P] Create/Initialize `data-model.md` in `specs/001-testing-cosmic-ray-arrival-direction-iso/` if missing, with **specific required sections**:
 1. "EventCatalog Schema"
 2. "ExposureMap Schema"
 3. "PowerSpectrum Schema"
 4. "Statistical Test Definitions" (must explicitly define the global max-C_l test)

**Dependencies**:
- T004 depends on T003 completion (schema must exist before writing)
- T004 depends on T001 completion (state/ directory must exist)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Download public UHECR event catalogs from Pierre Auger and Telescope Array, apply energy cut (E > 50 EeV), and convert RA/Dec to HEALPix map (Nside=64).

**Independent Test**: Execute ingestion script on local/CI; verify existence of valid HEALPix map file with correct event count, no NaN coordinates, and coverage matching detector footprints.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: T009 and T010 are 'Write Test' tasks (file creation). They are [P]. Test *execution* occurs after implementation.

- [ ] T009 [P] [US1] Write unit test file `tests/unit/test_healpix_conversion.py` with specific tests: `test_ra_dec_to_pixel_roundtrip` (verify RA/Dec -> pixel -> RA/Dec is exact), `test_pixel_bounds` (verify no overflow for valid RA/Dec), and `test_nan_handling` (verify NaN coordinates are excluded).
- [ ] T010 [P] [US1] Write integration test file `tests/integration/test_ingestion.py` with specific tests: `test_ingestion_filters_E_gt_50_EeV` (verify event count after filtering), `test_combined_dataset_validity` (verify no NaN in final dataset), and `test_file_existence` (verify `data/processed/healpix_map.fits` exists).

### Implementation for User Story 1

- [ ] T011 [US1] Implement `download_events.py` to fetch Auger Open Data 2020 (DOI: 10.5281/zenodo.3966535) and TA Public Data 2023-01 to `data/raw/`. **Dependency**: Requires T007 (graceful failure logic) to be implemented first.
- [ ] T012 [US1] Implement `preprocess.py` to filter events with E > 50 EeV, exclude missing energy/coords, and log exclusion counts.
- [ ] T013 [US1] Implement `analysis/healpix_conversion.py` to convert RA/Dec to HEALPix Nside=64, handling wrap-around and pixel overflow.
- [ ] T014 [US1] Fetch pinned exposure maps (Auger and TA) to `data/processed/` using **official exposure maps from the same release versions as the event catalogs** (DOI: 10.5281/zenodo.3966535 for Auger, TA 2023-01 release). **Note**: If official exposure maps are not found in the specified release, the task MUST halt with a clear error (per T007 logic), not guess a URL.
- [ ] T015 [US1] Implement `analysis/combine_exposure.py` to merge Auger and TA exposure maps into a single `data/processed/combined_exposure_map.fits` using weighted averaging based on detector area or simple union as per standard practice. **Dependency**: Requires T014 completion.
- [ ] T016 [US1] Add validation to ensure combined dataset contains only valid events and output map covers visible sky correctly.
- [ ] T017 [US1] Add logging for data ingestion steps, event counts, and exclusion reasons.

**Dependencies**:
- All US1 tasks depend on Phase 2 completion
- T011 depends on T007

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Angular Power Spectrum Computation and Exposure Correction (Priority: P2)

**Goal**: Compute angular power spectrum ($C_\ell$) for $\ell=1..5$ from HEALPix map, using detector exposure to generate expected isotropic distribution and analyzing residuals with shot-noise subtraction.

**Independent Test**: Run computation on synthetic dataset with injected dipole; verify $C_\ell$ recovery within RMS error bounds and correct shot-noise subtraction.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Write contract test file `tests/contract/test_power_spectrum.py` to validate `PowerSpectrum` model (check `ell` and `cl` types, `p_value` range) and `ExposureMap` model (check `nside` and `pixel_data` shape).
- [ ] T019 [P] [US2] Write integration test file `tests/integration/test_exposure_correction.py` to verify `exposure_correction.py` input (HEALPix map, exposure map) and output (intensity map) properties, and verify numerical tolerance (e.g., `np.allclose` within 1e-6).

### Implementation for User Story 2

- [ ] T020a [US2] Implement `analysis/exposure_correction.py` to generate exposure-corrected intensity map ($I = N_{obs}/N_{exp}$) using pinned exposure maps. **Dependency**: Requires T015 (combined exposure map) and T013 (HEALPix map) completion.
- [ ] T020b [US2] Implement `analysis/residuals.py` to compute raw residuals ($N_{obs} - N_{exp}$) as required by spec US-2, storing output in `data/processed/raw_residuals.fits`. **Dependency**: Requires T015 and T013 completion.
- [ ] T021 [US2] Implement `analysis/power_spectrum.py` to compute spherical-harmonic coefficients $a_{\ell m}$ from the exposure-corrected intensity map with shot-noise subtraction ($1/N_{tot}$).
- [ ] T022 [US2] Implement shot-noise subtraction logic in `analysis/power_spectrum.py` to isolate anisotropy signal.
- [ ] T023 [US2] Implement calculation of $C_\ell$ for low-order $\ell$ with numerical stability checks for low-exposure regions.
- [ ] T024 [US2] Add validation to ensure $C_\ell$ values are computed without division-by-zero errors.

**Dependencies**:
- T020a depends on T013 and T015 completion
- T020b depends on T013 and T015 completion
- T021, T022, T023, T024 depend on T020a completion

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance Testing and Multiple-Comparison Correction (Priority: P3)

**Goal**: Generate a large set of isotropic Monte Carlo simulations (weighted by exposure), compute max $C_\ell$ distribution, and derive global p-value to test isotropy at $\alpha=0.05$.

**Independent Test**: Run pipeline on purely random isotropic dataset; verify global p-value > 0.05 in [deferred] of trials (false positive rate control).

**⚠️ PLAN ALIGNMENT WARNING**: FR-004 explicitly requires 10,000 Monte Carlo simulations. The plan.md Summary and Complexity Tracking sections currently authorize a scalable number of simulations sufficient for robust statistical analysis. due to runtime constraints. This creates a direct contradiction. **Execution of T026/T027 requires an explicit plan.md update authorizing 10,000 simulations or a formal risk acceptance.**

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Write unit test file `tests/unit/test_monte_carlo.py` with specific tests: `test_seed_reproducibility_generates_identical_arrays` (verify same seed produces identical event sets), `test_distribution_properties` (verify generated events follow isotropic distribution within statistical bounds).
- [ ] T026 [P] [US3] Write integration test file `tests/integration/test_significance_test.py` with specific tests: `test_isotropic_dataset_p_value_gt_0.05` (verify p-value > 0.05 for [deferred] of trials on isotropic data), `test_max_cl_extraction` (verify max $C_\ell$ is correctly extracted from each simulation).

### Implementation for User Story 3

- [ ] T027 [US3] Implement benchmarking and batching logic in `analysis/monte_carlo.py` to validate throughput before full run. **Success Criteria**:
 1. Measure time per simulation batch on the target runner.
 2. Extrapolate to 10,000 simulations.
 3. If projected total time > 5.5 hours, the task MUST halt and output "FEASIBILITY FAILED: 10k simulations exceed 6h limit. Plan update required." (Do NOT proceed to 1k).
 4. If projected time <= 5.5 hours, proceed to full run.
 **Note**: This task resolves the contradiction between Spec (10k) and Plan (1k/feasibility) by enforcing a strict feasibility gate that halts on failure.
- [ ] T028 [US3] Implement `analysis/monte_carlo.py` to generate [deferred] isotropic event sets weighted by exact exposure map (per FR-004). **Logic**:
 - Only execute if T027 feasibility check passes.
 - If T027 fails, the pipeline halts with a clear error.
 - **No fallback to 1,000 simulations**.
 **Dependency**: Requires T027 completion.
- [ ] T029 [US3] Implement `stats/significance_test.py` to compute max $C_\ell$ for each of the 10,000 simulations and build null distribution. **Dependency**: Requires T028 completion.
- [ ] T030 [US3] Implement global empirical p-value calculation by comparing observed max $C_\ell$ to null distribution of the 10,000 simulations.
- [ ] T031 [US3] Persist the null distribution (list of max $C_\ell$ values) to `data/processed/null_distribution.json` for verification of SC-002 and SC-003.
- [ ] T032 [US3] Implement binary decision logic: reject isotropy if $p \le \alpha$, else fail to reject.
- [ ] T033 [US3] Add convergence checks to flag degenerate distributions (e.g., all $C_\ell$ identical) as critical failures and **explicitly call `sys.exit(1)`** to halt the pipeline as required by spec Edge Cases.

**Dependencies**:
- T027 must complete before T028
- T028 must complete before T029, T030, T031, T032, T033

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Research Review Resolution (Addressing Marie Curie Review)

**Goal**: Address reviewer concerns regarding instrumental calibration details, integrated exposure estimates, and statistical test specifications.

**Independent Test**: Verify `research.md` and `data-model.md` contain explicit calibration methods, exposure estimates, and statistical test definitions.

### Implementation for Research Review Resolution

- [ ] T034 [Review] Update `research.md` to document detector types; Telescope Array Surface & Fluorescence), and calibration methods (laser-based timing systems, atmospheric muon tracks for angular resolution, and standard candles for energy scale). **Dependency**:Requires T008a completion (file must exist with required sections).
- [ ] T035 [Review] Update `research.md` to extract and document total integrated exposure (km²·sr·yr) and expected event count (E > 50 EeV) for Auger/TA combined based on official exposure maps (from T015). **Dependency**: Requires T008a completion.
- [ ] T036 [Review] Update `data-model.md` to explicitly define statistical test (Angular Power Spectrum / Harmonic Analysis) and confidence level ($\alpha=0.05$) for rejecting isotropy. **Dependency**: Requires T008b completion.
- [ ] T037 [Review] Update `code/config.yaml` to include references to calibration procedures and exposure estimates used in the analysis.
- [ ] T038 [Review] Add validation task to ensure research documentation matches implementation parameters:
 1. Compare `config.yaml` parameters with `main.py` usage.
 2. Compare `research.md` exposure estimates with `data/processed/combined_exposure_map.fits` metadata.
 3. Compare `data-model.md` test definitions with `stats/significance_test.py` logic.

**Dependencies**:
- T034, T035 depend on T008a completion
- T036 depends on T008b completion

**Checkpoint**: Research documentation fully addresses reviewer concerns

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` including quickstart.md and API docs
- [ ] T040 [P] Optimize `map2alm` calls in `analysis/power_spectrum.py` using Nside=64 caching and implement parallel execution strategy in `analysis/monte_carlo.py` to ensure simulations complete within time limits
- [ ] T041 [P] Additional unit tests for edge cases (empty data, missing coords) in `tests/unit/`
- [ ] T042 Security hardening for external data fetching (checksum verification, timeout handling)
- [ ] T043 Run quickstart.md validation to ensure end-to-end pipeline execution on CI

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Research Review (Phase 6)**: Depends on Foundational completion (specifically T008a/T008b) and User Story completion; can run in parallel with US1-3 if artifacts exist
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T004 which depends on T003 and T001**
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Write unit test file tests/unit/test_healpix_conversion.py"
Task: "Write integration test file tests/integration/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Create base data models/entities in code/models/"
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
 - Developer D: Research Review Resolution (Phase 6)
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
- **Critical Constraint**: All Monte Carlo simulations must complete within 6 hours on 2-CPU CPU-only runner; optimize `map2alm` calls via T040 and batching (T027). **NOTE**: T027 implements a strict feasibility gate; if 10k simulations are infeasible, the pipeline halts. **Plan.md must be updated** if 10k proves infeasible.
- **Critical Constraint**: No synthetic data for primary scientific results; use real Auger/TA data only.
- **Plan Discrepancy Note**: Spec FR-004 requires 10,000 simulations. Plan.md currently states [deferred]. Tasks enforce Spec requirement (10k) via T027/T028 strict enforcement, but **plan.md must be updated** if 10k proves infeasible.
- **Review Resolution**: Phase 6 tasks (T034-T038) specifically address Marie Curie's request for calibration details (laser/muon tracks), exposure estimates (km²·sr·yr), and statistical test definitions (Harmonic Analysis, $\alpha=0.05$).
- **Constitution Compliance**: Task T003 and T004 ensure Data Hygiene (schema definition, automated checksums in state file) and Verified Accuracy (null distribution artifact) as per Constitution Principles III and II.
- **Exposure Map Source Warning**: Task T014 mandates using official exposure maps from the same release versions as event catalogs. If not found, the task halts.