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

- [ ] T001a [P] Create project root directory `projects/PROJ-772-testing-cosmic-ray-arrival-direction-iso/` and subdirectories (`code/`, `data/`, `tests/`, `state/`)
- [ ] T001b [P] Create `.gitignore` file with specific entries: `data/`, `__pycache__/`, `*.pyc`, `.env`, `state/projects/*.yaml` (except.gitkeep)
- [ ] T001c [P] Create `code/` directory structure including `__init__.py`, `ingestion/`, `analysis/`, `stats/`, `utils/`, `models/`
- [ ] T001d [P] Create `data/` directory structure including `raw/`, `processed/` with `.gitkeep` files
- [ ] T001e [P] Create `tests/` directory structure including `unit/`, `integration/`, `contract/`
- [ ] T002 [P] Initialize Python 3.11 project [UNRESOLVED-CLAIM: c_584dc434 — status=not_enough_info] with `requirements.txt` in `code/` containing exact version pins (e.g., `healpy>=1.16.0 [UNRESOLVED-CLAIM: c_664285e7 — status=not_enough_info]`, `numpy>=1.24.0 [UNRESOLVED-CLAIM: c_38f0a1da — status=not_enough_info]`, `pandas>=2.0.0 [UNRESOLVED-CLAIM: c_151b781a — status=not_enough_info]`, `scipy>=1.10.0 [UNRESOLVED-CLAIM: c_2045ae06 — status=not_enough_info]`, `astropy>=5.3.0 [UNRESOLVED-CLAIM: c_4dfa098d — status=not_enough_info]`, `requests>=2.31.0 [UNRESOLVED-CLAIM: c_a277caa4 — status=not_enough_info]`, `tqdm>=4.65.0 [UNRESOLVED-CLAIM: c_e6b161ac — status=not_enough_info]`, `pytest>=7.4.0 [UNRESOLVED-CLAIM: c_a1017f1a — status=not_enough_info]`)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `code/config.yaml` with pinned random seeds, dataset versions (Auger DOI: 10.5281/zenodo.3966535 [UNRESOLVED-CLAIM: c_ed74d550 — status=not_enough_info], TA: 2023-01 [UNRESOLVED-CLAIM: c_fb6304f5 — status=not_enough_info]), and path definitions
- [ ] T005 [P] Implement checksum verification logic in `code/ingestion/checksum.py` using SHA-256; ensure logic writes checksums to `state/projects/PROJ-772-testing-cosmic-ray-arrival-direction-iso.yaml` as required by Constitution Principle III
- [ ] T006 [P] Setup logging infrastructure in `code/utils/logging.py` to record event exclusion counts and pipeline steps
- [ ] T007a [P] Create `code/models/event_catalog.py` with `EventCatalog` class (Energy, RA, Dec, Source)
- [ ] T007b [P] Create `code/models/exposure_map.py` with `ExposureMap` class (HEALPix Nside=64 [UNRESOLVED-CLAIM: c_2e21e941 — status=not_enough_info], exposure values)
- [ ] T007c [P] Create `code/models/power_spectrum.py` with `PowerSpectrum` class (ell values, Cl values, p-value)
- [ ] T008 [P] Implement graceful error handling for missing data repositories in `code/ingestion/download_events.py`
- [ ] T032a [P] Create/Initialize `research.md` in `specs/001-testing-cosmic-ray-arrival-direction-iso/` if missing, with placeholder sections for detector types and calibration methods
- [ ] T034a [P] Create/Initialize `data-model.md` in `specs/001-testing-cosmic-ray-arrival-direction-iso/` if missing, with placeholder sections for statistical test definitions

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Download public UHECR event catalogs from Pierre Auger and Telescope Array, apply energy cut (E > 50 EeV), and convert RA/Dec to HEALPix map (Nside=64) [UNRESOLVED-CLAIM: c_f2feb39c — status=not_enough_info].

**Independent Test**: Execute ingestion script on local/CI; verify existence of valid HEALPix map file with correct event count, no NaN coordinates, and coverage matching detector footprints.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: T009 and T010 are 'Write Test' tasks (file creation). They are [P]. Test *execution* occurs after implementation.

- [ ] T009 [P] [US1] Write unit test file `tests/unit/test_healpix_conversion.py` to verify coordinate transformation accuracy
- [ ] T010 [P] [US1] Write integration test file `tests/integration/test_ingestion.py` to verify end-to-end data ingestion pipeline

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `download_events.py` to fetch Fetch Auger Open Data 2020 (DOI: 10.5281/zenodo.3966535) [UNRESOLVED-CLAIM: c_fe2bcb7e — status=not_enough_info] and TA Public Data 2023-01 [UNRESOLVED-CLAIM: c_f93f827f — status=not_enough_info] and The document references Telescope Array Public Data 2023-01. to `data/raw/`
- [ ] T012 [US1] Implement `preprocess.py` to filter events with E > 50 EeV [UNRESOLVED-CLAIM: c_46caef4f — status=not_enough_info], exclude missing energy/coords, and log exclusion counts
- [ ] T013 [US1] Implement `analysis/healpix_conversion.py` to convert RA/Dec to HEALPix Nside=64 [UNRESOLVED-CLAIM: c_2e21e941 — status=not_enough_info], handling wrap-around and pixel overflow
- [ ] T014 [US1] Fetch pinned exposure maps (Auger from `, TA from ` Name or service not known)"))]) to `data/processed/`
- [ ] T015 [US1] Add validation to ensure combined dataset contains only valid events and output map covers visible sky correctly
- [ ] T016 [US1] Add logging for data ingestion steps, event counts, and exclusion reasons

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Angular Power Spectrum Computation and Exposure Correction (Priority: P2)

**Goal**: Compute angular power spectrum ($C_\ell$) for $\ell=1..5$ from HEALPix map, using detector exposure to generate expected isotropic distribution and analyzing residuals with shot-noise subtraction.

**Independent Test**: Run computation on synthetic dataset with injected dipole; verify $C_\ell$ recovery within RMS error bounds and correct shot-noise subtraction.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Write contract test file `tests/contract/test_power_spectrum.py`
- [ ] T018 [P] [US2] Write integration test file `tests/integration/test_exposure_correction.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `analysis/power_spectrum.py` to compute spherical-harmonic coefficients $a_{\ell m}$ from the exposure-corrected intensity map with shot-noise subtraction ($1/N_{tot}$) [UNRESOLVED-CLAIM: c_9597aced — status=not_enough_info]
- [ ] T020 [US2] Implement `analysis/exposure_correction.py` to generate exposure-corrected intensity map ($I = N_{obs}/N_{exp}$) using pinned exposure maps (depends on T013 output)
- [ ] T021 [US2] Implement shot-noise subtraction logic in `analysis/power_spectrum.py` to isolate anisotropy signal
- [ ] T022 [US2] Implement calculation of $C_\ell$ for low-order $\ell$ with numerical stability checks for low-exposure regions
- [ ] T024 [US2] Add validation to ensure $C_\ell$ values are computed without division-by-zero errors

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance Testing and Multiple-Comparison Correction (Priority: P3)

**Goal**: Generate a large set of isotropic Monte Carlo simulations (weighted by exposure), compute max $C_\ell$ distribution, and derive global p-value to test isotropy at $\{{claim:c_ec7f39ef}} (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value)$.

**Independent Test**: Run pipeline on purely random isotropic dataset; verify global p-value > 0.05 in [deferred] of trials [UNRESOLVED-CLAIM: c_e2259470 — status=not_enough_info] (false positive rate control).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Write unit test file `tests/unit/test_monte_carlo.py` for random seed reproducibility
- [ ] T026 [P] [US3] Write integration test file `tests/integration/test_significance_test.py`

### Implementation for User Story 3

- [ ] T027 [US3] Implement `analysis/monte_carlo.py` to generate [deferred] isotropic event sets weighted by exact exposure map (per FR-004). Note: Must utilize optimization strategies from T027b and T038.
- [ ] T027b [US3] Implement benchmarking and batching logic in `analysis/monte_carlo.py` to parallelize The Monte Carlo simulation plan requires 10,000 simulations. [UNRESOLVED-CLAIM: c_4f6b2d66 — status=not_enough_info] across 2 CPUs within 6-hour runtime limit. This task must validate throughput and define the batching strategy before full run.
- [ ] T028 [US3] Implement `stats/significance_test.py` to compute max $C_\ell$ for each of the simulations and build null distribution (depends on T027/T027b completion)
- [ ] T029 [US3] Implement global empirical p-value calculation by comparing observed max $C_\ell$ to null distribution of The Monte Carlo simulation plan requires 10,000 simulations. [UNRESOLVED-CLAIM: c_4f6b2d66 — status=not_enough_info]
- [ ] T029b [US3] Persist the null distribution (list of max $C_\ell$ values from [deferred] sims) to `data/processed/null_distribution.json` for verification of SC-002 and SC-003
- [ ] T030 [US3] Implement binary decision logic: reject isotropy if $p \le \alpha$ [UNRESOLVED-CLAIM: c_6f3395e9 — status=not_enough_info], else fail to reject
- [ ] T031 [US3] Add convergence checks to flag degenerate distributions (e.g., all $C_\ell$ identical) as critical failures

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Research Review Resolution (Addressing Marie Curie Review)

**Goal**: Address reviewer concerns regarding instrumental calibration details, integrated exposure estimates, and statistical test specifications.

**Independent Test**: Verify `research.md` and `data-model.md` contain explicit calibration methods, exposure estimates, and statistical test definitions.

### Implementation for Research Review Resolution

- [ ] T032 [Review] Update `research.md` to document detector types , TA Fluorescence/Surface) [UNRESOLVED-CLAIM: c_77338459 — status=verified] and {{claim:c_cda8bf62}} (1507.04182, https://arxiv.org/abs/1507.04182)
- [ ] T033 [Review] Update `research.md` to calculate and document total integrated exposure (km²·sr·yr) and expected event count (E > 50 EeV) for Auger/TA combined [UNRESOLVED-CLAIM: c_d43ff569 — status=not_enough_info]
- [ ] T034 [Review] Update `data-model.md` to explicitly define statistical test (Angular Power Spectrum / Harmonic Analysis) and confidence level ($\{{claim:c_ec7f39ef}}$)
- [ ] T035 [Review] Update `code/config.yaml` to include references to calibration procedures and exposure estimates
- [ ] T036 [Review] Add validation task to ensure research documentation matches implementation parameters in `main.py`

**Checkpoint**: Research documentation fully addresses reviewer concerns

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` including quickstart.md and API docs
- [ ] T038 [P] Optimize `map2alm` calls in `analysis/power_spectrum.py` using Nside=64 caching [UNRESOLVED-CLAIM: c_b07a7318 — status=not_enough_info] and implement parallel execution strategy in `analysis/monte_carlo.py` to ensure The Monte Carlo simulation plan requires 10,000 simulations. [UNRESOLVED-CLAIM: c_4f6b2d66 — status=not_enough_info] complete within 6 hours
- [ ] T039 [P] Additional unit tests for edge cases (empty data, missing coords) in `tests/unit/`
- [ ] T040 Security hardening for external data fetching (checksum verification, timeout handling)
- [ ] T041 Run quickstart.md validation to ensure end-to-end pipeline execution on CI

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Research Review (Phase 6)**: Depends on Foundational completion (specifically T032a/T034a) and User Story completion; can run in parallel with US1-3 if artifacts exist
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
- **Critical Constraint**: All Monte Carlo simulations (N=10,000) must complete within 6 hours on 2-CPU CPU-only runner [UNRESOLVED-CLAIM: c_5011bb0b — status=not_enough_info]; optimize `map2alm` calls via T038 and batching (T027b).
- **Critical Constraint**: No synthetic data for primary scientific results; use real Auger/TA data only.
- **Plan Discrepancy Note**: Spec FR-004 requires The Monte Carlo simulation plan requires 10,000 simulations. [UNRESOLVED-CLAIM: c_4f6b2d66 — status=not_enough_info]. Plan.md currently states [deferred]. Tasks enforce Spec requirement ([deferred]) and add optimization tasks (T027b, T038) to ensure feasibility. Plan.md must be updated to reflect The Monte Carlo simulation plan requires 10,000 simulations. [UNRESOLVED-CLAIM: c_4f6b2d66 — status=not_enough_info] and the optimization strategy.
- **Review Resolution**: Phase 6 tasks (T032-T036) specifically address Marie Curie's request for calibration details, exposure estimates, and statistical test definitions.
- **Constitution Compliance**: Task T005 and T029b ensure Data Hygiene (checksums in state file) and Verified Accuracy (null distribution artifact) as per Constitution Principles III and II.