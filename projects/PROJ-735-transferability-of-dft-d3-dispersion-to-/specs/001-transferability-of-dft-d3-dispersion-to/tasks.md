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

- [X] T000 [P] Generate synthetic local fallback data: `data/IL-Benchmark-local.zip` (20 ion pairs with XYZ coords and CCSD(T)/CBS references) and `data/experimental_bulk_properties.csv` (density/viscosity for 20 pairs). **Algorithm**: Use fixed seed 42. Generate a set of random XYZ coordinates within a 5-10 Å box. Assign reference energies from a deterministic pseudo-random distribution (mean in the typical range for such systems, std within a representative magnitude for such systems). **Note**: This dataset size (20) is required by Plan CI limits but contradicts Spec Assumption (≥100). The generated data must be deterministic. **Deviation from Spec**: This task explicitly acknowledges the deviation from Spec FR-001 (Zenodo) and FR-008 (NIST) due to CI constraints, as documented in the Plan. **Requirement**: The generation script must log a CRITICAL warning that the Spec-mandated URLs were empty/invalid before generating this synthetic fallback.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create directory `data/raw/` and `data/derived/`
- [X] T001b [P] Create directory `code/` and `tests/`
- [X] T001c [P] Create file `code/__init__.py` and `tests/__init__.py`
- [X] T002 [P] Initialize a Python project with `requirements.txt` dependencies (psi4, pandas, numpy, scipy, scikit-learn, requests, pyyaml)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/load_data.py` to load and validate local fallback dataset `data/IL-Benchmark-local.zip` and `data/experimental_bulk_properties.csv`. **Verification Step**: The script MUST first attempt to fetch from the Spec-mandated URLs (FR-001, FR-008). If they fail (empty/invalid), it MUST log a CRITICAL warning and proceed with the local fallback. This establishes the synthetic data as a documented fallback, not an unverified primary source.
- [X] T005 [P] Implement checksum validation script for raw data in `code/load_data.py` (T001a creates dirs, this validates content)
- [X] T006 [P] Implement `code/utils.py` for common statistical functions (bootstrap resampling, error metrics)
- [X] T007 [P] Create base `CalculationResult` and `IonPair` data classes in `code/models.py`
- [X] T008 [P] Configure error handling and logging infrastructure in `code/logger.py`
- [X] T009 [P] Setup environment configuration management: Create `code/config.yaml` with keys `seed`, `data_path`, `output_path`. **Verification**: Verify `code/config.yaml` exists and contains all required keys with valid types.

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
- [X] T018 [US1] Implement bootstrap resampling (**1,000 replicates**) in `code/analyze_energies.py` to compute 95% CI for raw MAE (FR-014). **Verification**: Generate `raw_energies.csv` and a `power_analysis_note.txt` explicitly stating the limitation of 20 pairs vs. Spec requirement of ≥100. **Requirement**: The final `benchmark_report.md` MUST include a "Statistical Power Warning" stating that the 20-pair dataset is underpowered for the Spec's intended statistical significance and that CIs are for descriptive purposes only.
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
- [X] T023 [US2] Implement bootstrap resampling (**1,000 replicates**) in `code/derive_scaling.py` to generate confidence intervals for scaling factor `s` and hypothesis test. **Verification**: Generate `scaling_factor.txt` and a `power_analysis_note.txt` explicitly stating the limitation of 20 pairs vs. Spec requirement of ≥100. **Requirement**: The final `benchmark_report.md` MUST include a "Statistical Power Warning" stating that the 20-pair dataset is underpowered for the Spec's intended statistical significance and that CIs are for descriptive purposes only.
- [X] T024 [US2] Implement hypothesis test in `code/derive_scaling.py` to check if the confidence interval for `s` excludes 1.0
- [ ] T025 [US2] Read the optimal scaling factor `s` and its CI from the output of T022/T023 and write to `data/derived/scaling_factor.txt`. **Dependency**: T022, T023, T024. **Format**: Write a human-readable text file containing the value and CI (format not strictly mandated by Spec, but must be parsable). <!-- FAILED: unspecified -->
- [X] T026 [US2] Update `code/analyze_energies.py` to recompute error metrics using the scaled D3 term. **Dependency**: T025 (must read the written file).
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

- [X] T030 [P] [US3] Implement `code/correlate_bulk.py` to merge energy results with experimental density/viscosity data. **Verification**: Verify `correlation_data.csv` contains merged columns `pair_id`, `d3_term`, `density`, `viscosity`.
- [X] T031 [US3] Implement `code/correlate_bulk.py` to compute Pearson and Spearman correlations between Raw D3 Term and Density. **Verification**: Verify output includes R, R², p-value, and 95% CI.
- [X] T032 [US3] Implement `code/correlate_bulk.py` to compute Pearson and Spearman correlations between Scaled D3 Term and Density. **Verification**: Verify output includes R, R², p-value, and 95% CI.
- [X] T033 [US3] Implement `code/correlate_bulk.py` to compute Pearson and Spearman correlations between **Dispersion-Only Error** (Scaled D3 - Reference D3) and Viscosity. **Note**: This task implements the Plan's scientific methodology which excludes "Total Interaction-Energy Error" correlations as invalid. **Verification**: Verify output includes R, R², p-value, and 95% CI for this specific correlation.
- [X] T034 [US3] Implement bootstrap resampling (**1,000 replicates**) in `code/correlate_bulk.py` for confidence intervals of all correlation coefficients. **Verification**: Generate `power_analysis_note.txt` explicitly stating the limitation of 20 pairs vs. Spec requirement of ≥100. **Requirement**: The final `correlation_report.md` MUST include a "Statistical Power Warning" stating that the 20-pair dataset is underpowered for the Spec's intended statistical significance and that CIs are for descriptive purposes only.
- [X] T035 [US3] Implement Bonferroni correction for the family of correlation tests in `code/correlate_bulk.py`
- [X] T036 [US3] Update `code/generate_reports.py` to generate `correlation_report.md` with coefficients, R², p-values, CIs, and adjusted p-values
- [X] T037 [US3] Add handling for missing bulk property data (log warning, skip entry) in `code/correlate_bulk.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T060 [P] [Revision] Run `flake8` and `black` on `code/` and `tests/`; fix all reported linting/formatting issues
- [ ] T061 [P] Profile `code/run_psi4.py` and `code/analyze_energies.py` using `cProfile`; optimize the top 3 bottlenecks; generate `profile_report.md`
- [ ] T062 [P] Write unit tests for `code/utils.py` functions `bootstrap_resample` and `calculate_metrics`. **Specifics**: Implement `tests/unit/test_utils.py::test_bootstrap_resample` (asserts 1000 resampled datasets) and `tests/unit/test_utils.py::test_calculate_metrics` (asserts MAE/RMSE calculations). **Verification**: Ensure [deferred] coverage for these functions.
- [ ] T063 [P] Implement input validation in `code/load_data.py` for XYZ file format and CSV column presence. **Specifics**: Reject XYZ files with non-numeric coordinates. **Tests**: Write `tests/unit/test_load_data.py::test_load_data_invalid_xyz` (asserts ValueError).
- [ ] T064 [P] Update `docs/benchmark_report.md` to include the raw energy metrics, MAE CI, and scaling factor results. **Verification**: Verify file contains all required sections.
- [ ] T065 [P] Update `docs/benchmark_report.md` to **explicitly state the calibration procedure** (or lack thereof) for DFT-D3 parameters against ionic liquid data, as required by the Marie Curie review. **Verification**: Verify section "Calibration Procedure" exists and states "No calibration was performed against IL data."
- [ ] T066 [P] Update `docs/correlation_report.md` to include the correlation results and Bonferroni corrections. **Verification**: Verify file contains all required sections.
- [ ] T067 [P] Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data Gen)**: No dependencies - can start immediately
- **Setup (Phase 1)**: Depends on Phase 0 completion (data must exist)
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - US1, US2, US3 can proceed in parallel (if staffed) or sequentially (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on completion of all user stories

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (`raw_energies.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 output
- **Polish (Final Phase)**: Depends on completion of all user stories

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
5. Add Polish (Final Phase) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D: Polish
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint Note**: The Plan restricts the dataset to a manageable number of pairs due to CI limits (limited CPU resources and time). This contradicts the Spec's Assumption of ≥100 pairs for statistical power (FR-007, FR-010, FR-014). Tasks T018, T023, T034 execute with 20 pairs but explicitly require a "Statistical Power Warning" in the output to acknowledge this limitation.
- **Scientific Constraint**: Task T033 implements the "Dispersion-Only Error" correlation as per the Plan's scientific methodology, which explicitly excludes "Total Interaction-Energy Error" correlations as invalid. This resolves the conflict between Spec FR-009(c) and Plan Methodology.
- **Data Source Note**: The project relies on the local fallback `data/IL-Benchmark-local.zip` as the Primary Source of Truth due to empty/invalid URLs in the Spec's FR-001 and FR-008. Task T004 ensures this is a documented fallback after attempting the Spec-mandated sources.
- **Phase 6 Removal**: Phase 6 (Revision) has been removed entirely as its tasks (T038-T045) were not authorized by the Spec or Plan, creating scope creep.