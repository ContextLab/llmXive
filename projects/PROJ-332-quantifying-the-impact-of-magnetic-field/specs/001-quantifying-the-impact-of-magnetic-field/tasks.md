# Tasks: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

**Input**: Design documents from `/specs/001-quantify-topology-confinement/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per `plan.md`)
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

- [ ] T001 Create project structure per `plan.md` (directories: `code/`, `data/raw/`, `data/processed/`, `artifacts/`, `tests/`)
- [X] T002 Initialize Python project with `requirements.txt` (pinning `scipy`, `numpy`, `matplotlib`, `pandas`, `pytest`, `requests`, `pyyaml`; **NO** `mdsplus` library)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/data/__init__.py` and `code/analysis/__init__.py`
- [X] T005 [P] Create `code/main.py` entry point with argument parsing for discharge list
- [ ] T006 [P] [FR-007] Implement global timeout wrapper and memory guard in `code/utils/limits.py`, wire this wrapper to `code/main.py`, AND explicitly configure the timeout in the GitHub Actions workflow file at `.github/workflows/ci.yml` to ensure immediate pipeline abort on violation at the CI level.
- [ ] T007 Create base schema definitions in `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`
- [X] T008 Implement logging infrastructure in `code/utils/logger.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Retrieval and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically retrieve up to 10 specific DIII-D discharge datasets from the public MDSplus archive and parse them into a unified analysis-ready format containing `island_width` (pre-calculated or derived) and `tau_e`.

**Independent Test**: The pipeline can be tested by running the retrieval script against the public MDSplus archive and verifying that a single CSV file is produced containing a small number of rows (discharges) with columns for `discharge_id`, `island_width`, `tau_e`, `te_profile`, `ne_profile`, and `confinement_mode`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for MDSplus connection retry logic in `tests/unit/test_retrieval.py` <!-- FAILED: unspecified -->
- [X] T010 [P] [US1] Integration test for exclusion of discharges with missing data in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement MDSplus client connection with retry logic (multiple attempts, fixed time intervals) in `code/data/retrieval.py`
- [X] T012 [US1] Implement logic to fetch EFIT, `islands`, `taue`, AND `h98y2` fields from the MDSplus `taue` or `h98y2` tree for a given discharge ID in `code/data/retrieval.py`. **MUST** include `h98y2` retrieval to support confinement mode classification as per `spec.md:FR-003`.
- [ ] T013 [US1] Implement logic to retrieve pre-calculated `island_width` from MDSplus; if missing, **derive** it using the Rutherford equation approximation with inputs: `local magnetic shear`, `q`, and `Bt` from EFIT as per `spec.md:FR-002`. If derivation inputs are also missing, log warning and exclude discharge. **Do not** strictly exclude if pre-calculated is missing; use derivation as the primary fallback.
- [X] T014a [US1] Implement parsing logic to convert MDSplus time-series data into a raw structured DataFrame in `code/data/preprocessing.py`
- [ ] T014b [US1] [FR-009] Implement schema validation logic to validate input/output against `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` **before** any parsing or analysis begins in `code/data/validator.py`.
- [X] T015 [US1] Implement validation: ensure at least 5 valid discharges remain; fail pipeline if fewer [FR-001] in `code/main.py`
- [ ] T016 [US1] Save unified dataset to `data/processed/unified_analysis.csv` with checksum generation. **Must include** `tau_e` AND the derived `confinement_mode` (L-mode vs H-mode) based on the H98y2 factor (H-mode if H98y2 >= 0.85) as per `spec.md:FR-003` in `code/data/preprocessing.py`. <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Topological Metric Calculation (Priority: P2)

**Goal**: Calculate topological metrics (resonant surface density) and validate edge cases.

**Independent Test**: The calculation module can be tested by feeding it a provided reference CSV file containing known values for a set of test discharges and verifying that the output matches the expected values within a reasonable tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for resonant surface density calculation against reference values in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement q-profile extraction from EFIT data in `code/analysis/metrics.py`
- [X] T019 [US2] Implement outlier detection: flag and exclude discharges where `island_width` > minor radius in `code/analysis/metrics.py`
- [X] T020a [US2] Handle edge case: if no integer q-values cross minor radius, assign default "zero" density in `code/analysis/metrics.py`
- [ ] T020b [US2] **NEW**: Calculate `resonant_surface_density` by counting rational surfaces (q=m/n) per unit normalized minor radius (rho_tor) using the EFIT q-profile. A surface is rational if |q - m/n| < 0.01, **implementing a loop where m and n range from a lower bound to an upper bound inclusive** as per `spec.md:FR-002`. If q-profile exists but has no integer crossings, density is 0. Output to `data/processed/metrics.csv`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Visualization (Priority: P3)

**Goal**: Compute Spearman rank correlation between topological metrics and energy confinement time, generate a scatter plot, and output the p-value.

**Independent Test**: The analysis module can be tested by running it on a small synthetic dataset with a known negative correlation and verifying that the system correctly reports the calculated p-value and flags the significance status.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for Spearman correlation and bootstrap resampling logic in `tests/unit/test_correlation.py`
- [ ] T024 [P] [US3] Integration test for "Hypothesis Not Supported" flag logic in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement Spearman rank correlation calculation between `island_width`/`resonant_surface_density` and `tau_e`. **MUST include**:
 1. **Stratification Logic**: Check N per mode (L/H). If N >= 3 for both, calculate separate correlations and **output separate correlation coefficients and p-values for each mode** as per `spec.md:FR-010`. If N < 3 for either, skip stratification, calculate global correlation, and append warning: "Stratification skipped: insufficient samples per mode (N < 3)".
 2. **Multicollinearity Check**: Check correlation between `q_max - q_min` and `resonant_surface_density`. If > 0.95, flag as collinear, exclude `resonant_surface_density` from multivariate analysis, and report only univariate correlation as per `spec.md:FR-011`.
 3. **Bootstrap Resampling**: Perform bootstrap with a **fixed random seed** to ensure reproducibility as per `spec.md:FR-005` and Constitution I.
 4. Calculate confidence intervals.
- [ ] T027 [US3] Implement hypothesis logic: `directional_effect` (r < -0.5) and `statistical_significance` (p < 0.05) in `code/analysis/correlation.py`
- [ ] T028 [US3] **NEW**: Implement power analysis calculation to determine statistical power for the observed effect size given sample size N. If power < 20% to detect |r|=0.5, flag result as "Inconclusive due to low power" as per `spec.md:FR-008`.
- [ ] T029 [US3] Generate diagnostic scatter plot (`topology_vs_confinement.png`) with regression line and CI bands in `code/viz/plot.py`
- [ ] T030 [US3] Generate final summary report artifact consuming outputs from T025, T027, T028, and T029. **Must unconditionally report** the effect size magnitude (|r|) for ALL valid datasets regardless of statistical significance, and include the power analysis result and "Inconclusive" flag if applicable, in `code/main.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Update `quickstart.md` with execution commands and environment setup
- [ ] T032 Run full pipeline integration test with a known set of DIII-D discharge IDs
- [ ] T033 Verify memory footprint < 7 GB and execution time < 6 hours in CI environment
- [ ] T034 [P] Add docstrings to all modules in `code/`

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
- **User Story 2 (P2)**: Depends on US1 completion (requires parsed data) - **Cannot run until T016 is done**
- **User Story 3 (P3)**: Depends on US2 completion (requires calculated metrics) - **Cannot run until T020b is done**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows) - **Note: In this specific pipeline, data flow (US1->US2->US3) enforces sequential execution, but code structure can be developed in parallel.**
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for MDSplus connection retry logic in tests/unit/test_retrieval.py"
Task: "Integration test for exclusion of discharges with missing data in tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement MDSplus client connection with retry logic in code/data/retrieval.py"
Task: "Implement parsing logic to convert MDSplus time-series data in code/data/preprocessing.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify 5-10 valid rows in CSV)
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
 - Developer A: User Story 1 (Data Retrieval)
 - Developer B: User Story 2 (Metrics - can start coding logic, but needs US1 data for full integration)
 - Developer C: User Story 3 (Analysis - can start coding logic, but needs US2 data for full integration)
3. Stories complete and integrate sequentially due to data flow dependencies.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Do NOT use synthetic data fallbacks. If MDSplus fetch fails, the job MUST fail (FR-001, Constitution VI).
- **CRITICAL**: If pre-calculated island width is missing, the Rutherford equation derivation MUST be attempted before exclusion (FR-002).
- **CRITICAL**: Stratification by mode is mandatory if N>=3 per mode; otherwise, global correlation with warning (FR-010).
- **CRITICAL**: Fixed random seed is mandatory for all stochastic processes (FR-005, Constitution I).
- **CRITICAL**: Power analysis is mandatory and must flag "Inconclusive" if power < 20% (FR-008).