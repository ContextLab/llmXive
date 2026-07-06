# Tasks: Exploring the Statistical Significance of Fine‑Structure Constant Variations

**Input**: Design documents from `/specs/001-fine-structure-constant-variations/`
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

- [ ] T001 Create project structure per implementation plan (code/, tests/, data/, specs/)
- [ ] T002 Initialize Python project with pinned requirements (pymc>=5.0.0, arviz, astropy, specutils, numpy, scipy, pandas, requests, fsspec) in requirements.txt
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` with paths, random seeds, and verified NIST constants (Fe II, Mg II, Si IV, C IV, Al III) as hardcoded values
- [ ] T005 Create `code/data_model.py` defining `Absorber` and `Line` entities with required attributes (redshift, wavelengths, q_coefficients, S/N)
- [ ] T006 [P] Setup directory structure for `data/raw/`, `data/processed/`, and `data/simulated/` with `.gitkeep`
- [ ] T007 Implement `code/utils.py` for logging, error handling, and FITS header parsing utilities
- [ ] T008 Configure pytest environment with `pytest-cov` and seed enforcement in `tests/conftest.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download/publicly access quasar spectra (simulated for MVP, ESO-ready logic) and extract metal-absorption line lists with measured wavelengths.

**Independent Test**: Run pipeline on a small subset of simulated spectra; verify output CSV contains correctly identified lines with wavelengths within sub-angstrom precision of ground truth.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for line extraction output schema in `tests/contract/test_line_extraction.py`
- [ ] T010 [P] [US1] Integration test for end-to-end data ingestion on simulated subset in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `code/data_ingestion.py` to generate/download simulated UVES-like spectra (mocking ESO logic) and save to `data/raw/`
- [ ] T012 [P] [US1] Implement `code/line_extraction.py` using `specutils` to identify Fe II, Mg II, Si IV, C IV, Al III lines and extract wavelengths
- [ ] T013 [US1] Implement logic in `code/line_extraction.py` to assign `q_coeff` from NIST constants and flag lines with S/N < 5
- [ ] T014 [US1] Implement error handling in `code/data_ingestion.py` to skip corrupted files and log errors without crashing
- [ ] T015 [US1] Depends on: T011, T012, T013, T014. Implement logic to save `data/processed/absorber_catalog.csv` containing extracted lines, redshifts, and quality flags. Validate output against `absorber.schema.yaml` ensuring columns `absorber_id`, `redshift`, `line_species`, `wavelength`, `q_coeff`, `snr` are present and typed correctly.
- [ ] T016 [US1] Add validation in `code/line_extraction.py` to ensure at least 2 lines with non-zero `q_coeff` per absorber for identifiability

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hierarchical Bayesian Inference for Δα/α Estimation (Priority: P2)

**Goal**: Run a hierarchical Bayesian model (PyMC v5) to estimate Δα/α per absorber, accounting for systematic errors as nuisance parameters.

**Independent Test**: Run model on simulated data with known Δα/α; verify 95% CI contains true value in ≥95% of 10+ independent seeds (Multiple chains, warmup, draws).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Contract test for model output schema (posterior summaries, R-hat) in `tests/contract/test_model_output.py`
- [ ] T018 [P] [US2] Integration test for coverage accuracy (10+ seeds) in `tests/integration/test_bayesian_coverage.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/model.py` defining Level 1 (absorber-specific Δα/α) and Level 2 (global trend/systematics) PyMC hierarchical structure
- [ ] T020 [US2] Implement nuisance parameter modeling in `code/model.py` for wavelength calibration drift (Half-Cauchy prior scale=0.1 Å if no ThAr data)
- [ ] T021 [US2] Implement `code/inference.py` to run NUTS sampling with 4 chains, 2000 warmup, 4000 draws, and `arviz.rhat` convergence checks for the primary 'with-systematics' model.
- [ ] T021b [US2] Implement `code/inference.py` to run a separate 'without-systematics' model instance (using same data but fixed systematics to zero) and save posterior samples to `data/processed/posteriors_no_sys.json`. This task is required for SC-004 verification.
- [ ] T022 [US2] Depends on: T021, T021b. Measure systematic error propagation per SC-004: Calculate variance of Δα/α from the 'with-systematics' model (T021) and the 'without-systematics' model (T021b). Write the ratio and individual variances to `data/processed/metrics.json`. If the 'with-systematics' variance is lower than the 'without-systematics' variance, log a warning indicating potential regularization effects but DO NOT halt execution. This output serves as the verification record for SC-004.
- [ ] T023 [US2] Generate posterior summary tables (mean, std, 95% CI) for each absorber and save to `data/processed/posteriors.json`
- [ ] T024 [US2] Implement fallback logic to raise an error if R-hat > 1.01 for any parameter, halting execution

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Comparison and Spatial/Temporal Trend Validation (Priority: P3)

**Goal**: Compute Bayes factors (Null vs. Dipole/Temporal) and fit spatial dipole models to validate trends.

**Independent Test**: Run model comparison on synthetic data with known ground truth; verify Bayes factors favor true model in >90% of trials.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Contract test for Bayes factor output schema in `tests/contract/test_model_comparison.py`
- [ ] T026 [P] [US3] Integration test for dipole fit accuracy in `tests/integration/test_dipole_validation.py`

### Implementation for User Story 3

- [ ] T027a [US3] Validate Bridge Sampling stability on a small synthetic subset. Criteria: Effective Sample Size (ESS) > 100 and variance < 1.0. If criteria fail, log critical error and halt pipeline. This task must pass before T027.
- [ ] T027 [US3] Depends on: T023, T027a. Implement `code/analysis.py` to compute Bayes factors using bridge sampling between Null and Alternative models. Input: posterior samples from T023. If bridge sampling fails stability criteria (per T027a), log "Bayes Factor computation failed: unstable" and record NaN/NA in `data/processed/model_comparison_results.json` instead of halting, ensuring the pipeline completes and reports the failure state. Do NOT fall back to WAIC/LOO.
- [ ] T028 [US3] Depends on: T023. Implement spatial dipole fitting in `code/analysis.py` (Δα/α = A cos(θ) + B) using celestial coordinates (RA, Dec) and posterior estimates from T023.
- [ ] T029 [US3] Implement Bonferroni correction logic in `code/analysis.py` for multiple sightline groups. Apply correction if the number of sightline groups (defined as clusters within 10° or Δz < 0.1) is greater than 5. (Note: Threshold value '5' is an implementation assumption pending spec refinement).
- [ ] T030 [US3] Generate corner plots and summary tables using `arviz` for Δα/α, trend slope, and dipole amplitude in `code/plots.py`
- [ ] T031 [US3] Implement sensitivity analysis script to vary prior widths (±20%) and verify conclusion stability (SC-005)
- [ ] T032 [US3] Save final model comparison results and dipole parameters to `data/processed/model_comparison_results.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `quickstart.md` and `research.md`
- [ ] T034 Code cleanup and refactoring in `code/`
- [ ] T035a [P] Depends on: T021. Profile the inference pipeline (A multi-absorber benchmark) to identify bottlenecks in memory usage and compute time. Document specific optimization targets based on SC-003 (A duration of several hours for absorbers.).
- [ ] T035b [P] Refactor code (e.g., `code/inference.py`, `code/model.py`) to optimize memory usage and compute time. Verify that the 20-absorber run completes < 4 hours and the 30-absorber run < 6 hours on GitHub Actions free-tier (SC-003).
- [ ] T036 [P] Additional unit tests in `tests/unit/` for `q_coeff` assignment and prior logic
- [ ] T037 Run `quickstart.md` validation to ensure end-to-end pipeline executes successfully

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 and US2 can start in parallel after Foundational.
  - US3 must wait for US2 completion (specifically T023).
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for input data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for posterior estimates (T023)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US2 can start in parallel (if team capacity allows)
- US3 must wait for US2 completion
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (US1/US2 only)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for line extraction output schema in tests/contract/test_line_extraction.py"
Task: "Integration test for end-to-end data ingestion on simulated subset in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_ingestion.py to generate/download simulated UVES-like spectra"
Task: "Implement code/line_extraction.py using specutils to identify metal lines"
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
   - Developer C: User Story 3 (must wait for US2 completion)
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
- **CPU Constraint**: All NUTS sampling tasks must respect the CPU / GB RAM limit; use subset sizes (20 absorbers) for benchmark runs.
- **Data Constraint**: No fake data generation; use simulated ground truth for validation, but real ESO access logic must be implemented for production readiness.
- **Bridge Sampling**: FR-005 mandates Bridge Sampling. Stability must be validated (T027a) before use. If unstable, the pipeline logs an error and records NA, but does not use WAIC/LOO.
- **Performance**: SC-003 targets (4h/6h) are hard constraints verified in T035a/T035b.