# Tasks: Quantifying the Impact of Data Artifacts on Planetary Nebula Morphology

**Input**: Design documents from `/specs/001-quantify-artifact-bias/`
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

- [ ] T001a [P] Create project directories: `code/`, `code/synthetic`, `code/metrics`, `code/analysis`, `code/io`, `data/raw`, `data/synthetic`, `data/processed`, `data/validation`, `tests/unit`, `tests/contract`, `tests/integration`, `logs`
- [ ] T001b [P] Create `.gitignore` excluding `data/`, `__pycache__`, `*.pyc`, `logs/`, `*.log`
- [ ] T001c [P] Initialize `README.md` with project overview and quickstart instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (numpy, scikit-image, astropy, scipy, statsmodels, pandas, matplotlib, pytest)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [ ] T004 [P] Create `code/config.py` with pinned random seeds, default paths, and **concrete** artifact parameters: noise levels ranging from low to moderate, saturation range from a baseline to 0.5 in 0.05 increments (derived from spec assumptions on typical instrumental variations) (FR-002, FR-003, SC-003)
- [~] T005 [P] Implement `code/io/loader.py` to validate FITS headers (WCS, exposure, filter), abort on missing metadata, and **log the specific missing fields** for traceability (FR-008, FR-009)
- [~] T006 [P] Create `code/synthetic/generator.py` to generate synthetic planetary nebulae with known ground-truth ellipticity and asymmetry (no GPU, CPU-only) **and save these exact ground-truth values to a JSON metadata file** (e.g., `data/synthetic/gt_metadata.json`) to serve as the Single Source of Truth (Constitution Principle IV)
- [~] T007 [P] Implement `code/io/writer.py` to save generated images and logs with checksums for reproducibility (FR-008)
- [~] T008 [P] Setup `tests/unit/` structure and `pytest` configuration
- [~] T009 [P] **CRITICAL**: Acquire, vet, checksum, and process a small set of real HST images (MAST) for manual validation as required by Constitution Principle VII; store in `data/validation/` and create `data/validation/validation_manifest.json` (Plan: Constitution Check Principle VII)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Evaluate Noise‑Induced Bias on Ellipticity (Priority: P1) 🎯 MVP

**Goal**: Quantify how varying Gaussian noise levels bias ellipticity measurements against a known ground truth.

**Independent Test**: Run pipeline on clean synthetic image, inject specific noise level, compute ellipticity, and verify deviation from ground truth.

**Dependency Note**: Tasks T010-T012 depend on T005 completion. T006 must complete before T005 if T005 validates generated files.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [~] T010 [P] [US1] Contract test for `code/io/loader.py` in `tests/unit/test_loader.py`: **Function `test_loader_raises_on_missing_wcs`** asserting that `loader.load()` raises `ValueError` when WCS metadata is missing (FR-009)
- [~] T011 [P] [US1] Unit test for noise injection logic in `tests/unit/test_artifacts.py`: **Function `test_noise_injection_sigma`** asserting that injected noise matches target sigma within tolerance (FR-002)
- [~] T012 [P] [US1] Unit test for ellipticity calculation in `tests/unit/test_ellipticity.py`: **Function `test_ellipticity_calculation`** asserting that second-order moments yield correct ellipticity for a known synthetic shape (FR-004) <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [~] T013 [P] [US1] Implement `code/metrics/ellipticity.py` using second-order moments (FR-004)
- [~] T014 [US1] Implement `code/synthetic/artifacts.py` noise injection function: **iterate** over sigma levels [0.01, 0.05, 0.10] * median signal, save results to `data/processed/noise_sweep_{sigma}.fits` (FR-002) <!-- FAILED: unspecified -->
- [~] T016 [US1] Implement statistical test logic: **Two-sample t-test** with Bonferroni correction; output p-values to `logs/stats_results.csv` (FR-005)
- [ ] T015 [US1] Create `code/main.py` pipeline step to: load clean image -> inject noise -> measure ellipticity -> **load ground truth from `data/synthetic/gt_metadata.json`** -> compute bias -> log results (FR-001, FR-008)
- [ ] T017 [US1] Add logging for noise parameters, seeds, and bias results to `logs/research.log`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Saturation‑Induced Bias on Asymmetry (Priority: P2)

**Goal**: Determine if pixel-level saturation systematically inflates the asymmetry index.

**Independent Test**: Inject controlled saturation, compute asymmetry, and test against clean baseline.

### Tests for User Story 2 (MANDATORY) ⚠️

- [ ] T018 [P] [US2] Unit test for saturation clipping logic in `tests/unit/test_artifacts.py`: **Function `test_saturation_clipping`** asserting that the correct fraction of brightest pixels are clipped (FR-003)
- [ ] T019 [P] [US2] Unit test for asymmetry calculation in `tests/unit/test_asymmetry.py`: **Function `test_asymmetry_conselice`** asserting that the A-statistic matches the Conselice (2003) definition (FR-004)

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/metrics/asymmetry.py` using Conselice (2003) definition with robust centering (FR-004)
- [ ] T023 [US2] Implement statistical test logic to compare saturated vs. clean asymmetry with Bonferroni correction (FR-005)
- [ ] T021 [US2] Implement `code/synthetic/artifacts.py` saturation clipping function: **implement sweep logic** across **0.0 to 0.5 in 0.05 increments** (FR-003)
- [ ] T022 [US2] Create `code/main.py` pipeline step to: load clean image -> inject saturation -> measure asymmetry -> **load ground truth from `data/synthetic/gt_metadata.json`** -> compute bias -> log results (FR-001, FR-008)
- [ ] T024 [US2] Implement sensitivity analysis sweep: **range to 0.5, step 0.05**; output CSV `data/processed/saturation_sweep.csv` with columns [saturation_fraction, asymmetry_mean, asymmetry_std]; **generate statistical summary** to verify p < 0.05 and monotonic trends (SC-003)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Derive Calibration Functions to Correct Bias (Priority: P3)

**Goal**: Fit regression models linking artifact intensity to bias and derive correction functions.

**Independent Test**: Apply derived correction to synthetic data and verify residual bias is non-significant.

**Dependency Note**: US3 depends on data aggregation from US1 and US2, and specifically on the completion of T027 (regression model) and T028 (validation logic).

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T025 [P] [US3] Contract test for regression model output schema in `tests/contract/test_regression.py`
- [ ] T026 [P] [US3] Unit test for correction application logic in `tests/unit/test_validation.py`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/analysis/regression.py` to fit linear/polynomial models (artifact intensity -> bias) (FR-005)
- [ ] T028 [US3] Implement `code/analysis/validation.py` to apply inverse correction and compute residual bias; **generate statistical report** (p-values, confidence intervals) for residual bias as mandated by FR-007
- [ ] T029 [US3] Create `code/main.py` pipeline step to: aggregate results from US1/US2 -> fit models -> apply corrections -> validate (FR-006, FR-007)
- [ ] T030 [US3] Implement power analysis script to verify n=50 achieves ≥80% power for effect size 0.05; **must be run AFTER US1/US2 to use observed effect size**; **output explicit limitation documentation** if power < 80% (SC-004)
- [ ] T031 [US3] Generate final calibration function outputs: save to `data/processed/calibration_functions.json` with schema `{ "ellipticity_model": {...}, "asymmetry_model": {...} }` and validation report linking to underlying files (SC-002)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032a [P] Update `quickstart.md`: Add sections on data generation, artifact injection, and metric calculation with code snippets
- [ ] T032b [P] Update `research.md`: Add sections on results, bias trends, and calibration function performance
- [ ] T033 Code cleanup and refactoring of `code/main.py` into modular CLI entry points
- [ ] T034 Performance optimization: Ensure full sensitivity sweep runs < 4 hours on 2 CPU cores
- [ ] T035 [P] Integration test for full pipeline (Synth -> Inject -> Measure -> Correct -> Validate) in `tests/integration/test_pipeline.py`
- [ ] T036 Run `quickstart.md` validation to ensure all artifacts are reproducible

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Note**: T006 (Generation) produces files that T005 (Loader) validates; T006 is a prerequisite for T005 if T005 validates generated files.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data aggregation from US1 and US2 **and completion of T027 (regression) and T028 (validation)**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Metrics before services/pipeline steps
- Core implementation before integration
- Story complete before moving to next priority
- **Statistical Logic (T016, T023) must be implemented before Pipeline Steps (T015, T022) that consume their output.**

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US2 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (US1/US2 parallel, US3 after)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for loader in tests/unit/test_loader.py (test_loader_raises_on_missing_wcs)"
Task: "Unit test for noise injection in tests/unit/test_artifacts.py (test_noise_injection_sigma)"
Task: "Unit test for ellipticity in tests/unit/test_ellipticity.py (test_ellipticity_calculation)"

# Launch models/metrics for User Story 1 together:
Task: "Implement code/metrics/ellipticity.py"
Task: "Implement code/synthetic/artifacts.py (noise)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Clean vs. Noise)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo (Calibration)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Noise/Ellipticity)
 - Developer B: User Story 2 (Saturation/Asymmetry)
3. Developer C: User Story 3 (Calibration/Regression) - starts after US1/US2 data available
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All tasks must run on CPU-only CI with a limited number of cores and memory. No GPU, no 8-bit quantization, no deep learning.
- **Data**: Synthetic data generation must be deterministic and checksummed. No fake data for final metrics; use synthetic ground truth for validation.
- **Ground Truth**: All ground-truth values MUST be saved to machine-readable artifacts (JSON/CSV) as per Constitution Principle IV.
- **Saturation Range**: Concrete values (0.0 to 0.5, step 0.05) are defined in T004 and used in T021/T024.

---

## Phase X: Revision & Gap Resolution (Addressing Plan/Spec Ambiguities)

**Purpose**: Resolve specific gaps identified in the plan/spec regarding undefined saturation ranges and ensure data flow integrity.

- [ ] T039 [US2] Add a validation check in `code/synthetic/artifacts.py` to ensure that the saturation clipping logic does not inadvertently clip the entire image (resulting in 0 signal) unless explicitly configured for edge-case testing.
- [ ] T040 [US1] Verify that the noise injection logic in `code/synthetic/artifacts.py` uses `numpy.random.Generator` with the seed from `config.py` to guarantee exact reproducibility across runs, as required by FR-008.
- [ ] T041 [US3] Ensure the regression model in `code/analysis/regression.py` handles the case where artifact intensity is zero (baseline) by forcing the intercept to match the ground-truth bias (which should be zero) or explicitly modeling the residual offset.
