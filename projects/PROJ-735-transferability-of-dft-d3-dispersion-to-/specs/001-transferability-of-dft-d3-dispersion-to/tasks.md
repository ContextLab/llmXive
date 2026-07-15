# Tasks: Transferability of DFT‑D3 Dispersion to Ionic Liquids

**Input**: Design documents from `/specs/PROJ-735-transferability-of-dft-d3-dispersion-to-/`
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

## Phase 0: Data Generation (Setup)

**Purpose**: Generate the required synthetic local fallback data to ensure executability, given CI constraints.

- [ ] T000 [P] Generate synthetic local fallback data: `data/IL-Benchmark-local.zip` (20 ion pairs with XYZ coords and CCSD(T)/CBS references) and `data/experimental_bulk_properties.csv` (density/viscosity for 20 pairs). **Note**: This dataset size (20) is required by Plan CI limits but contradicts Spec Assumption (≥100). The generated data must be deterministic (fixed seed).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create directory `data/raw/` and `data/derived/`
- [ ] T001b Create directory `code/` and `tests/`
- [ ] T001c Create file `code/__init__.py` and `tests/__init__.py`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` dependencies (psi4, pandas, numpy, scipy, scikit-learn, requests, pyyaml)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T001a Create directory `data/raw/` and `data/derived/`
- [X] T005 [P] Implement checksum validation script for raw data in `code/load_data.py` (T001a creates dirs, this validates content)
- [~] T004 [P] Implement `code/load_data.py` to load and validate local fallback dataset `data/IL-Benchmark-local.zip` and `data/experimental_bulk_properties.csv` (Primary Source due to CI constraints)
- [X] T006 [P] Implement `code/utils.py` for common statistical functions (bootstrap resampling, error metrics)
- [X] T007 Create base `CalculationResult` and `IonPair` data classes in `code/models.py`
- [X] T008 Configure error handling and logging infrastructure in `code/logger.py`
- [~] T009 Setup environment configuration management for dataset paths and random seeds

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Benchmark DFT-D3 Interaction Energies (Priority: P1) 🎯 MVP

**Goal**: Compute DFT-D interaction energies for a set of ionic-liquid ion-pair complexes and compare them to high-level CCSD(T)/CBS reference values.

**Independent Test**: The pipeline can be executed on a fresh GitHub Actions runner and will produce a CSV of raw dispersion-corrected DFT energies, reference energies, and error metrics without any scaling or correlation steps.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for energy parsing logic in `tests/unit/test_parse_psi4.py`
- [X] T011 [P] [US1] Unit test for error metric calculation (MAE, RMSE, MSE) in `tests/unit/test_metrics.py`
- [X] T012 [P] [US1] Integration test for full pipeline on a subset of 2 ion pairs in `tests/integration/test_pipeline_us1.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/run_psi4.py` to execute B3LYP/def2-TZVP + D3 (Becke-Johnson damping) + **Counterpoise correction** (using `bsse_type='cp'`) single-point calculations on CPU only
- [X] T014 [US1] Implement retry logic (up to 3 attempts) for failed Psi4 jobs within `code/run_psi4.py`
- [X] T015 [US1] Implement `code/analyze_energies.py` to extract total energy and D3 dispersion contribution from Psi4 output
- [X] T016 [US1] Implement `code/analyze_energies.py` to compute MAE, RMSE, and Mean Signed Error (MSE) against CCSD(T)/CBS references
- [X] T017 [US1] Implement `code/analyze_energies.py` to generate `raw_energies.csv` with columns: pair_id, reference_energy, dft_total_energy, d3_dispersion_energy, signed_error
- [X] T018 [US1] Implement bootstrap resampling (**1,000 replicates**) in `code/analyze_energies.py` to compute 95% CI for raw MAE (FR-014). **Note**: Dataset limited to 20 pairs by Plan/CI; Spec requires ≥100 for statistical power. <!-- FAILED: unspecified -->
- [X] T019 [US1] Update `code/generate_reports.py` to include raw energy metrics and MAE CI in `benchmark_report.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Derive a Simple Scaling Correction (Priority: P2)

**Goal**: Obtain a single scalar that, when applied to the D3 dispersion term, reduces systematic bias across the benchmark set.

**Independent Test**: Running the "scaling" stage on the CSV from US-1 produces a single numeric factor and a re-computed error summary.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for linear scaling optimization in `tests/unit/test_scaling.py`
- [X] T021 [P] [US2] Unit test for hypothesis testing (s=1.0) logic in `tests/unit/test_hypothesis.py`

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement `code/derive_scaling.py` to fit a scalar `s > 0` minimizing MAE of corrected energies (E_corrected = E_base + s * E_D3)
- [X] T023 [US2] Implement bootstrap resampling (**1,000 replicates**) in `code/derive_scaling.py` to generate confidence intervals for scaling factor `s` and hypothesis test. **Note**: Dataset limited to 20 pairs by Plan/CI; Spec requires ≥100 for statistical power.
- [X] T024 [US2] Implement hypothesis test in `code/derive_scaling.py` to check if the confidence interval for `s` excludes 1.0
- [~] T025 [US2] Write `scaling_factor.txt` containing the optimal `s` and its CI
- [X] T026 [US2] Update `code/analyze_energies.py` to recompute error metrics using the scaled D3 term <!-- FAILED: unspecified -->
- [X] T027 [US2] Update `code/generate_reports.py` to include scaling factor, CI, and hypothesis test result in `benchmark_report.md`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlate Dispersion Terms with Bulk Properties (Priority: P3)

**Goal**: Test whether the magnitude of the (raw or scaled) D3 dispersion contribution is associated with experimentally measured bulk properties (density and viscosity).

**Independent Test**: Executing the correlation stage on the corrected CSV produces Pearson and Spearman coefficients, bootstrap confidence intervals, and Bonferroni-adjusted p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for correlation calculation (Pearson/Spearman) in `tests/unit/test_correlation.py`
- [X] T029 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_bonferroni.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `code/correlate_bulk.py` to merge energy results with experimental density/viscosity data <!-- FAILED: unspecified -->
- [ ] T031 [US3] Implement `code/correlate_bulk.py` to compute Pearson and Spearman correlations between Raw D3 Term and Density
- [ ] T032 [US3] Implement `code/correlate_bulk.py` to compute Pearson and Spearman correlations between Scaled D3 Term and Density
- [ ] T033 [US3] Implement `code/correlate_bulk.py` to compute Pearson and Spearman correlations between **Dispersion-Only Error** (E_D3_term - s*E_D3_ref) and Viscosity. **Note**: Plan explicitly excludes Total Interaction-Energy Error correlation as scientifically invalid.
- [ ] T034 [US3] Implement bootstrap resampling (**1,000 replicates**) in `code/correlate_bulk.py` for confidence intervals of all correlation coefficients. **Note**: Dataset limited to 20 pairs by Plan/CI; Spec requires ≥100 for statistical power.
- [ ] T035 [US3] Implement Bonferroni correction for the family of correlation tests in `code/correlate_bulk.py`
- [ ] T036 [US3] Update `code/generate_reports.py` to generate `correlation_report.md` with coefficients, R², p-values, CIs, and adjusted p-values
- [ ] T037 [US3] Add handling for missing bulk property data (log warning, skip entry) in `code/correlate_bulk.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T060 [P] Documentation updates in `docs/` including `benchmark_report.md`, `correlation_report.md`, and `review_response.md`
- [ ] T061 Run `flake8` and `black` on `code/` and `tests/`; fix all reported linting/formatting issues
- [ ] T062 Profile `code/run_psi4.py` and `code/analyze_energies.py` using `cProfile`; optimize the top 3 bottlenecks; generate `profile_report.md`
- [ ] T063 Write unit tests for `code/utils.py` functions `bootstrap_resample` and `calculate_metrics`; ensure [deferred] coverage
- [ ] T064 Implement input validation in `code/load_data.py` for XYZ file format and CSV column presence; write tests for validation logic
- [ ] T065 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data Gen)**: No dependencies - can start immediately
- **Setup (Phase 1)**: Depends on Phase 0 completion (data must exist)
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - US1, US2, US3 can proceed in parallel (if staffed) or sequentially (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories and revisions being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (`raw_energies.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 output
- **Polish (Final Phase)**: Depends on completion of all user stories and revisions

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Once Foundational phase completes, US1, US2, US3 can start in parallel
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for energy parsing logic in tests/unit/test_parse_psi4.py"
Task: "Unit test for error metric calculation in tests/unit/test_metrics.py"

# Launch all models for User Story 1 together:
Task: "Implement code/run_psi4.py"
Task: "Implement code/analyze_energies.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Data Generation
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
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
- **Constraint Note**: The Plan restricts the dataset to 20 pairs due to CI limits (2 CPU, 6h). This contradicts the Spec's Assumption of ≥100 pairs for statistical power (FR-007, FR-010, FR-014). Tasks T018, T023, T034 execute with 20 pairs but explicitly note this limitation.
- **Scientific Constraint**: T033 uses 'Dispersion-Only Error' as per Plan Methodology, not 'Total Error' as per Spec FR-009(c), because the Plan explicitly excludes the latter as scientifically invalid.