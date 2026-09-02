# Tasks: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

**Input**: Design documents from `/specs/001-investigating-md-diffusion-predictive-power/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-424-investigating-the-predictive-power-of-mo/`) by creating the following directories: `code/`, `data/raw/`, `data/processed/`, `data/interim/`, `tests/unit/`, `tests/integration/`.

- [ ] T002 Initialize Python 3.11 project with dependencies: `gromacs`, `mdanalysis`, `numpy`, `pandas`, `scipy`, `matplotlib`, `seaborn`, `scikit-learn`, `pyyaml`, `ruff`, `black` in `projects/PROJ-424-investigating-the-predictive-power-of-mo/requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-424-investigating-the-predictive-power-of-mo/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Initialize `data/raw/.gitkeep` and create `data/raw/manifest.json` to track checksums for curated experimental data. **Replaces redundant directory creation**; ensures data hygiene from the start.
- [X] T006b [P] Implement `code/data/raw/nist_refs.json` creation script or manual population step to generate the curated experimental diffusion coefficients for water, ethanol, and acetone at 298K/300K. **Must include source citations and checksums**. This task implements the "manual curation" path defined in Plan Phase 0.
- [X] T006a [P] Implement `code/utils/data_fetcher.py` to **validate** the existence of `data/raw/nist_refs.json`. If missing, raise a clear, actionable error pointing to T006b. **Do NOT attempt network fetch**; rely on the curated file as the canonical source per Plan.
- [X] T005 [P] Implement `code/config.py` to define parameters: solvents (water, ethanol, acetone), timescales (1ns, 5ns, 10ns), force field (MARTINI), scaling factors, and R² threshold (high). **Note**: Threshold set to 0.95 per Constitution Principle VI; **T008a** tracks the required spec update to align FR-008.
- [X] T007 Implement `code/utils/logging.py` for structured logging and `code/utils/checksums.py` for artifact verification
- [ ] T008a [Spec Kickback (Blocking)] Update `spec.md` FR-008 to change MSD linearity threshold from R² ≥ 0.99 to R² ≥ 0.95, aligning with Constitution Principle VI. **This is an external PR requirement; implementation proceeds with 0.95 per Constitution.** <!-- FAILED: unspecified -->
- [ ] T008b [Spec Kickback (Blocking)] Update `spec.md` SC-005 to replace 'bootstrap difference-of-means test (p ≤ 0.05)' with 'descriptive trend analysis' due to N=3 limitations. **This is an external PR requirement; implementation proceeds with trend analysis.**
- [ ] T008c [Spec Kickback (Blocking)] Update `spec.md` SC-003 to define sensitivity sweep parameters as {low, medium, high percentages} (removing `[deferred]` status). **This is an external PR requirement; implementation proceeds with concrete values.**
- [ ] T009 Create base schemas in `code/data_models/` for `diffusion_results`, `bootstrap_stats`, and `sensitivity_report`
- [ ] T010 Generate `contracts/*.schema.yaml` files for data validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Timescale-Accuracy Curves for Simple Liquids (Priority: P1) 🎯 MVP

**Goal**: Execute MD simulations for water, ethanol, acetone at varying time scales to assess convergence.; extract MSD; calculate diffusion coefficients; compare to NIST benchmarks; generate timescale-accuracy plot.

**Independent Test**: Run the pipeline for water at early, intermediate, and late time steps.; verify MAE calculation against `data/raw/nist_refs.json`; produce a plot of MAE vs. Simulation Duration.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (TDD-First), ensure they FAIL before implementation**

- [X] T011 [P] [TDD-First] [US1] Unit test for MSD extraction logic in `tests/unit/test_msd.py`
- [X] T012 [P] [TDD-First] [US1] Unit test for diffusion coefficient calculation and scaling in `tests/unit/test_msd.py`
- [X] T013 [P] [TDD-First] [US1] Unit test for MAE calculation against NIST refs in `tests/unit/test_analysis.py`

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement `code/simulation/topology.py` to generate MARTINI topology files (.gro,.top) for water, ethanol, and acetone
- [X] T015 [US1] Implement `code/simulation/runner.py` to execute GROMACS/LAMMPS simulations with timeout (h limit), density convergence check (±1% over 200ps), and non-equilibration flagging. **Must generate or load specific.gro,.top, and.mdp files** derived from T014 outputs with explicit NPT/production parameters. **Uses R² ≥ 0.95 threshold** (per Constitution, pending T008a).
- [ ] T016 [US1] Implement `code/analysis/msd.py` to:
 - Extract MSD trajectory from simulation output
 - Perform linear regression (MSD vs. time)
 - Validate linearity (R² ≥ 0.95) citing **Constitution Principle VI** and **T008a** as the authority for this threshold
 - Calculate diffusion coefficient and apply solvent-specific scaling factors
- [X] T017 [US1] Implement `code/reporting/plots.py` to generate timescale-accuracy curves (MAE vs. Duration) with uncertainty bands
- [ ] T018 [US1] Implement `code/main.py` pipeline entry point to orchestrate: topology gen → simulation → MSD extraction → diffusion calc → MAE calculation → plotting

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Methodological Rigor via Sensitivity Analysis (Priority: P2)

**Goal**: Verify robustness of diffusion coefficient estimation by sweeping regression start times ([deferred], [deferred], [deferred] of trajectory length) and confirming variance < 5%.

**Independent Test**: Run sensitivity analysis on a 10ns ethanol trajectory; verify variance in calculated D values across start times; generate sensitivity report.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`
- [X] T020 [P] [US2] Integration test for variance threshold check in `tests/integration/test_sensitivity.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/analysis/sensitivity.py` to:
 - Sweep regression start times at **[deferred], [deferred], and [deferred]** (0.1, 0.2, 0.3) of total trajectory length as defined in Plan and US-2 (pending T008c).
 - Calculate diffusion coefficient for each start time
 - Compute variance and flag if > 5%
 - Output `sensitivity_report` schema
- [ ] T022 [US2] Integrate sensitivity analysis into `code/main.py` (runs after primary analysis for each solvent-timescale)
- [ ] T023 [US2] Add logging for sensitivity results in `code/utils/logging.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Execute Full Batch Analysis with Statistical Confidence Intervals (Priority: P3)

**Goal**: Run full batch (solvents × 3 timescales); perform bootstrap resampling (a sufficient number of iterations, with a fallback to a lower count); generate summary table with confidence intervals; perform descriptive trend analysis.

**Independent Test**: Execute full pipeline; verify `bootstrap_stats.csv` contains mean MAE and 95% CI for all solvent-timescale combinations; verify final report includes trend analysis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for bootstrap resampling logic in `tests/unit/test_bootstrap.py`
- [ ] T025 [P] [US3] Unit test for CI calculation and fallback logic in `tests/unit/test_bootstrap.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/analysis/bootstrap.py` to:
 - Perform bootstrap iterations on MAE distribution
 - Implement fallback to 100 iterations if wall-clock time > 5.5h
 - Calculate confidence intervals (percentile method)
 - Output `bootstrap_stats.csv`
- [ ] T027 [US3] Implement `code/reporting/tables.py` to generate summary table with mean MAE, 95% CI, and **descriptive trend analysis** (1ns vs 10ns improvement). **Output must include**: 'MAE_1ns', 'MAE_10ns', 'Reduction %', 'Trend Direction' (e.g., 'Improving'). Cites **T008b** as the authority for the statistical method. **Depends on T026.**
- [ ] T028 [US3] Integrate full batch execution into `code/main.py` (loop over solvents × timescales)
- [ ] T029 [US3] Update `code/main.py` to handle NIST reference missing values (skip and log warning)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `projects/PROJ-424-investigating-the-predictive-power-of-mo/README.md` and `quickstart.md`
- [ ] T031 Code cleanup and refactoring in `code/`
- [ ] T032 Performance optimization for bootstrap resampling (vectorization)
- [ ] T033 [P] Additional unit tests for edge cases (non-linear MSD, missing refs) in `tests/unit/`
- [ ] T034 Run quickstart.md validation to ensure end-to-end execution
- [ ] T035 Generate final report artifact in `data/processed/final_report.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T008a, T008b, T008c** (Spec Kickbacks) are **Blocking Gates** requiring external PR resolution before the project is fully spec-compliant, but implementation proceeds with Constitution/Plan values.
 - **T006b** (Curated Data) must be completed before **T006a** (Data Validation) to ensure the file exists.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T015 (US1) completion** for MSD extraction logic. T021 cannot run in parallel with T015.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T015 (US1) results (diffusion coefficients)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (TDD-First)
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), **except** T008a/b/c which are blocking gates for implementation.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (TDD-First)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Critical Intra-Phase Dependencies (Phase 5)

- **T026 (Bootstrap)** must complete before **T027 (Summary Table)** can start. T027 consumes the output of T026.
- **T026** is **NOT** parallel-safe with T027.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for MSD extraction logic in tests/unit/test_msd.py"
Task: "Unit test for diffusion coefficient calculation and scaling in tests/unit/test_msd.py"

# Launch all models for User Story 1 together:
Task: "Implement code/simulation/topology.py"
Task: "Implement code/analysis/msd.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - **Ensure T006b (Curated Data) is completed** to provide ground truth.
 - **Ensure T008a/b/c are tracked** as external spec update requirements.
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
- **Critical**: All simulation tasks MUST use MARTINI force field or reduced system size to meet 6h runtime limit (FR-007).
- **Critical**: All data loading MUST use the curated `nist_refs.json` file; T006a validates existence, T006b creates it. NO synthetic fallbacks.
- **Critical**: Bootstrap iterations MUST fallback to 100 if wall-clock time > 5.5h (FR-004).
- **Critical**: T008a, T008b, T008c are mandatory spec kickbacks that must be resolved (via external PR) before the project is fully spec-compliant, but implementation proceeds with Constitution/Plan values.
- **Critical**: T026 (Bootstrap) must strictly precede T027 (Summary Table) within Phase 5.
- **Critical**: T001 explicitly defines directory structure; T004 is now dedicated to data manifest initialization to avoid redundancy.
- **Critical**: T021 uses concrete values {[deferred], [deferred], [deferred]} for sensitivity analysis.
- **Critical**: T027 explicitly defines output format for trend analysis.