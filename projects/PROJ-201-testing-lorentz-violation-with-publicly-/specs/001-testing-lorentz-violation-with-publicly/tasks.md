# Tasks: Testing Lorentz Violation with Publicly Available CMB Data

**Input**: Design documents from `/specs/001-testing-lorentz-violation/`
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

- [ ] T001 [P] Create project directory structure: `mkdir -p code/data code/analysis code/utils data/raw data/processed data/simulations data/results tests`
- [ ] T002 [P] Initialize Python 3.11 project: Run `python -m venv venv` and create `pyproject.toml` with `[build-system]` section
- [ ] T003 [P] Configure linting: Create `.flake8` file and add `[tool.black]` section to `pyproject.toml`
- [ ] T004 [P] Create `config.yaml` template with keys: `paths` (raw, processed, results), `seeds` (random, numpy), `constants` (sme_coefficient, l_max)
- [ ] T005 [P] Create `.gitignore` to exclude `venv/`, `data/raw/`, `data/processed/`, `*.pyc`, `__pycache__/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 [P] Implement `code/config.py` function `load_config()`: Parse `config.yaml`, validate keys, return dict
- [ ] T007 [P] Implement `code/config.py` function `enforce_seeds()`: Set `random.seed`, `numpy.random.seed` from config
- [ ] T008 [P] Implement `code/utils/logging.py`: Create `setup_logger()` function returning a configured `logging.Logger`
- [ ] T009 [P] Create `requirements.txt` with pinned versions: `healpy==1.16.2`, `numpy==1.24.0`, `scipy==1.10.0`, `emcee==3.1.3`, `requests==2.31.0`, `astropy==5.2.0`, `pyyaml==6.0.1`
- [ ] T010 [P] Setup `tests/__init__.py` and `pytest.ini` configuration
- [ ] T011 [P] Create `code/__init__.py` to expose public API
- [ ] T012 [P] Create `data/raw/.gitkeep` and `data/processed/.gitkeep`
- [ ] T013 [P] Create `code/data/simulation.py` skeleton with `inject_sme_coefficient()` function signature (Plan Task 1.2)
- [ ] T014 [P] Create `code/analysis/anisotropy.py` skeleton with `calculate_biposh()` function signature
- [ ] T015 [P] Create `code/analysis/inference.py` skeleton with `run_mcmc()` function signature
- [ ] T016 [P] Create `code/main.py` skeleton: Entry point that loads config, enforces seeds, and logs start
- [ ] T017 [P] Define Forward Model Algorithm: Write docstring and comments in `code/data/simulation.py` detailing the injection logic: `a_lm_new = a_lm_iso + k * alpha_lm` **BEFORE** convolution with beam functions (Plan Task 1.2)
- [ ] T018 [US2] Implement `inject_sme_coefficient()` in `code/data/simulation.py` to produce 200 FITS files in `data/simulations/` with **Nside=256** (sub-sampled for RAM), injecting specific k values (Plan Task 1.3)
- [ ] T019 [US2] Implement `generate_isotropic_null()` in `code/data/simulation.py` to produce 200 FITS files in `data/simulations/` with **Nside=256** and realistic noise (using config-defined noise models) (Plan Task 1.3)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download Planck PR3 SMICA, EE, TE maps and masks, verify integrity, apply masks, and deconvolve beams to produce analysis-ready datasets.

**Independent Test**: Execute `code/data/downloader.py` and `code/data/processor.py`; verify output files exist in `data/processed/`, have Nside=2048, contain no NaNs in unmasked regions, and match expected file sizes.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T020 [P] [US1] Unit test `tests/test_data.py::test_download_retry_logic`: Verify exponential backoff and retry count
- [ ] T021 [P] [US1] Unit test `tests/test_data.py::test_checksum_verification`: Verify `assert file_hash == expected_hash`
- [ ] T022 [P] [US1] Unit test `tests/test_data.py::test_mask_application`: Verify masked pixels are zeroed
- [ ] T023 [P] [US1] Integration test `tests/test_data.py::test_end_to_end_pipeline`: Verify `data/processed/` contains valid FITS files

### Implementation for User Story 1

- [ ] T024 [US1] Implement `code/data/downloader.py`: Fetch SMICA, EE, TE maps and masks from ESA Legacy Archive (FITS) with retry logic
- [ ] T025 [US1] Implement checksum verification in `code/data/downloader.py`: Verify file integrity against ESA records, raise error on mismatch
- [ ] T026 [US1] Implement `code/data/processor.py`: Load raw maps, apply confidence masks, and deconvolve beam/pixel window functions
- [ ] T027 [US1] Implement validation in `code/data/processor.py`: Check for NaNs and correct Nside=2048 resolution in output
- [ ] T028 [US1] Implement error handling in `code/data/downloader.py`: Raise `ERROR_DATA_UNAVAILABLE` on persistent failure
- [ ] T029 [US1] Update `code/main.py`: Add trigger for data acquisition pipeline (calls `downloader.py` and `processor.py`)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Anisotropy Diagnostics and Power Spectrum Estimation (Priority: P2)

**Goal**: Compute angular power spectra (TT, EE, TE) for ℓ < 200, perform dipole modulation analysis, calculate BipoSH coefficients (L=2,3), and implement Minkowski functional checks for non-Gaussianity.

**Independent Test**: Run diagnostics on generated isotropic simulations; verify p-value > 0.05 for null hypothesis and correct recovery of injected signal in anisotropic simulations. Ensure execution completes within 6 hours on 2 CPU cores.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US2] Unit test `tests/test_analysis.py::test_power_spectrum_calculation`: Verify `healpy.anafast` output against reference
- [ ] T031 [P] [US2] Unit test `tests/test_analysis.py::test_dipole_modulation`: Verify Hanson & Lewis estimator output
- [ ] T032 [P] [US2] Unit test `tests/test_analysis.py::test_biposh_calculation`: Verify L=2,3 BipoSH coefficients
- [ ] T033 [P] [US2] Unit test `tests/test_analysis.py::test_minkowski_functionals`: Verify V0, V1, V2 calculation

### Implementation for User Story 2

- [ ] T034 [P] [US2] Implement `code/analysis/power_spectra.py`: Compute TT, EE, TE spectra for ℓ < 200 using `healpy.anafast`
- [ ] T035 [US2] Implement `code/analysis/anisotropy.py`: Calculate dipole modulation amplitude and phase (Hanson & Lewis estimator)
- [ ] T036 [US2] Implement `code/analysis/anisotropy.py`: Calculate BipoSH coefficients for L=2 (Quadrupole) and L=3 (Octupole) modes
- [ ] T037 [US2] Implement `code/analysis/minkowski.py`: Calculate Minkowski functionals (V, V1, V2) to flag non-Gaussian artifacts
- [ ] T038 [US2] Implement logic in `code/analysis/minkowski.py`: If Minkowski flag is set, **log the flag and save diagnostic trace for review** (do NOT halt or downgrade) (Edge Case handling)
- [ ] T039 [US2] Integrate diagnostic analysis in `code/main.py` (simulation generation is handled in Phase 2)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Comparison and Statistical Inference (Priority: P3)

**Goal**: Perform likelihood-ratio test comparing isotropic vs. anisotropic models, run MCMC sampling to constrain SME coefficient \(k_{(V)00}^{(5)}\), and apply multiple-comparison correction (Benjamini-Hochberg FDR).

**Independent Test**: Run MCMC on synthetic zero-SME data; verify posterior centers at zero with correct credible interval. Verify FDR correction is applied to p-values from BipoSH modes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T040 [P] [US3] Unit test `tests/test_inference.py::test_likelihood_function`: Verify likelihood calculation
- [ ] T041 [P] [US3] Unit test `tests/test_inference.py::test_mcmc_convergence`: Verify ESS calculation and warning trigger
- [ ] T042 [P] [US3] Unit test `tests/test_inference.py::test_fdr_correction`: Verify Benjamini-Hochberg implementation
- [ ] T043 [P] [US3] Integration test `tests/test_inference.py::test_full_inference_pipeline`: End-to-end test on synthetic data

### Implementation for User Story 3

- [ ] T045 [US3] Implement `code/analysis/inference.py`: Construct likelihood function comparing observed vs. simulated BipoSH coefficients
- [ ] T046 [US3] Implement `code/analysis/inference.py`: Run MCMC sampling (100 walkers, 2000 burn-in, **8000 samples total**) using `emcee` to derive posterior for \(k_{(V)00}^{(5)}\)
- [ ] T047 [US3] Implement convergence monitoring in `code/analysis/inference.py`: Check ESS; if < 200, issue warning and save trace plot
- [ ] T048 [US3] Implement `code/analysis/inference.py`: Apply Benjamini-Hochberg FDR correction to p-values from BipoSH modes (L=2,3)
- [ ] T049 [US3] Implement result classification logic: "consistent with isotropy" vs "anomalous" based on corrected p-value < 0.05
- [ ] T050 [US3] Implement output generation in `code/analysis/inference.py`: Save posterior distributions, likelihood-ratio statistics, and SME constraints to `data/results/`
- [ ] T051 [US3] Update `code/main.py`: Execute full inference pipeline and generate final report

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T052 [P] Documentation updates: Add docstrings to all modules and update `quickstart.md`
- [ ] T053 Code cleanup and refactoring for performance optimization
- [ ] T054 [P] Add unit tests for edge cases (corrupted files, MCMC non-convergence)
- [ ] T055 Update `state/projects/PROJ-201-testing-lorentz-violation-with-publicly-.yaml` with data file hashes
- [ ] T056 Verify end-to-end runtime is within acceptable limits and RAM usage is within acceptable bounds.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for input data (for noise modeling if needed, but simulations use config models)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for diagnostic results

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
Task: "Unit test for download retry logic and checksum verification in tests/test_data.py"
Task: "Unit test for mask application and beam deconvolution in tests/test_data.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/downloader.py"
Task: "Implement code/data/processor.py"
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