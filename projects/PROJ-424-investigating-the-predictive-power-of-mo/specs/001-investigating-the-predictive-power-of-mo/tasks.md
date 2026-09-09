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

- [ ] T001a [P] Create `code/` directory and subdirectories (`simulation/`, `analysis/`, `reporting/`, `utils/`) at `projects/PROJ-424-investigating-the-predictive-power-of-mo/`. **Verify**: `ls -R code/`.
- [ ] T001b [P] Create `data/` directory and subdirectories (`raw/`, `processed/`, `interim/`) at `projects/PROJ-424-investigating-the-predictive-power-of-mo/`. **Verify**: `ls -R data/`.
- [ ] T001c [P] Create `tests/` directory and subdirectories (`unit/`, `integration/`) at `projects/PROJ-424-investigating-the-predictive-power-of-mo/`. **Verify**: `ls -R tests/`.
- [ ] T002 [P] Initialize Python project with dependencies: `gromacs>=2023.0`, `mdanalysis>=2.0`, `numpy>=1.24`, `pandas>=2.0`, `scipy>=1.10`, `matplotlib>=3.7`, `seaborn>=0.12`, `scikit-learn>=1.2`, `pyyaml>=6.0`, `ruff>=0.1.0`, `black>=23.0` in `projects/PROJ-424-investigating-the-predictive-power-of-mo/requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-424-investigating-the-predictive-power-of-mo/`. **Deliverables**: `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections, and `.ruff.toml` with specific rules (e.g., `E4`, `E7`, `E9`, `F`).

---

## Phase 2.1: Foundational Implementation (Blocking Prerequisites for User Stories)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007a [P] Implement `code/utils/logging.py` for structured logging. **Deliverable**: A `setup_logger` function that configures a standard Python logger with JSON formatting and file output to `logs/`.
- [X] T007b [P] Implement `code/utils/checksums.py` for artifact verification. **Deliverable**: A `calculate_sha256(file_path)` function that returns the SHA256 hash of a file.
- [X] T005 [P] Implement `code/config.py` to define parameters: solvents (water, ethanol, acetone), timescales (1ns, 5ns, 10ns), force field (MARTINI), scaling factors, and R² threshold (0.95). **Note**: Threshold set to 0.95 per Constitution Principle VI and spec.md FR-008.
- [X] T006b [P] Create `data/raw/nist_refs.json` with **hardcoded** experimental diffusion coefficients for water, ethanol, and acetone at 298K/300K. **Action**: Manually populate the JSON with the following values (or verified literature equivalents) and calculate the SHA256 checksum:
 - Water: D = 2.30e-9 m²/s (Source: NIST) [UNRESOLVED-CLAIM: c_f5f54b7e — status=not_enough_info]
 - Ethanol: D = 1.24e-9 m²/s (Source: NIST) [UNRESOLVED-CLAIM: c_baa9ca3e — status=not_enough_info]
 - Acetone: D = 4.50e-9 m²/s (Source: NIST) [UNRESOLVED-CLAIM: c_8191b2b0 — status=not_enough_info]
 **Output**: `data/raw/nist_refs.json` and `data/raw/manifest.json` with checksum.
- [X] T006c [P] Implement `code/utils/data_fetcher.py` to **validate** the existence and checksum of `data/raw/nist_refs.json`. If missing or checksum mismatch, raise a clear, actionable error pointing to T006b. **Do NOT attempt network fetch**; rely on the curated file as the canonical source per Plan and spec.md FR-001.
- [X] T009a [P] Create base schema for `diffusion_results` in `code/data_models/diffusion_results.yaml`.
- [X] T009b [P] Create base schema for `bootstrap_stats` in `code/data_models/bootstrap_stats.yaml`.
- [X] T009c [P] Create base schema for `sensitivity_report` in `code/data_models/sensitivity_report.yaml`.
- [ ] T010 [P] Generate `contracts/*.schema.yaml` files for data validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Timescale-Accuracy Curves for Simple Liquids (Priority: P1) 🎯 MVP

**Goal**: Execute MD simulations for water, ethanol, acetone at varying time scales to assess convergence.; extract MSD; calculate diffusion coefficients; compare to NIST benchmarks; generate timescale-accuracy plot.

**Independent Test**: Run the pipeline for water at early, intermediate, and late time steps.; verify MAE calculation against `data/raw/nist_refs.json`; produce a plot of MAE vs. Simulation Duration.

### Tests for User Story 1 (TDD-First - Write BEFORE implementation) ⚠️

- [X] T011 [US1] Unit test for MSD extraction logic in `tests/unit/test_msd.py`. **Must fail before T016**.
- [X] T012 [US1] Unit test for diffusion coefficient calculation and scaling in `tests/unit/test_msd.py`. **Must fail before T016**.
- [X] T013 [US1] Unit test for MAE calculation against NIST refs in `tests/unit/test_analysis.py`. **Must fail before T018**.

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement `code/simulation/topology.py` to generate MARTINI topology files (.gro,.top) for water, ethanol, and acetone. **Deliverable**: Files saved to `data/raw/topologies/`.
- [X] T015 [US1] Implement `code/simulation/runner.py` to execute GROMACS/LAMMPS simulations with timeout (6h limit), density convergence check (±1% over 200ps), and non-equilibration flagging. **Must load specific.gro,.top, and.mdp files** from `data/raw/topologies/` generated by T014. **Uses R² ≥ 0.95 threshold** (per Constitution, T005, spec.md FR-008).
- [X] T016 [US1] Implement `code/analysis/msd.py` to:
 - Extract MSD trajectory from simulation output
 - Perform linear regression (MSD vs. time)
 - Validate linearity (R² ≥ 0.95) citing **Constitution Principle VI** and **spec.md FR-008** as the authority for this threshold
 - Calculate diffusion coefficient and apply solvent-specific scaling factors
- [X] T017 [US1] Implement `code/reporting/plots.py` to generate timescale-accuracy curves (MAE vs. Duration) with uncertainty bands
- [X] T018 [US1] Implement `code/main.py` pipeline entry point to orchestrate: topology gen → simulation → MSD extraction → diffusion calc → MAE calculation → plotting

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Methodological Rigor via Sensitivity Analysis (Priority: P2)

**Goal**: Verify robustness of diffusion coefficient estimation by sweeping regression start times (early fractions of trajectory length) and confirming variance < 5%.

**Independent Test**: Run sensitivity analysis on a 10ns ethanol trajectory; verify variance in calculated D values across start times; generate sensitivity report.

### Tests for User Story 2 (TDD-First - Write BEFORE implementation) ⚠️

- [X] T019 [US2] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`. **Must fail before T021**.
- [X] T020 [US2] Integration test for variance threshold check in `tests/integration/test_sensitivity.py`. **Must fail before T021**.

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/analysis/sensitivity.py` to:
 - Sweep regression start times at **0.1, 0.2, and 0.3** of total trajectory length as defined in Plan, spec.md SC-003, and US-2.
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

### Tests for User Story 3 (TDD-First - Write BEFORE implementation) ⚠️

- [ ] T024 [US3] Unit test for bootstrap resampling logic in `tests/unit/test_bootstrap.py`. **Must fail before T026**.
- [ ] T025 [US3] Unit test for CI calculation and fallback logic in `tests/unit/test_bootstrap.py`. **Must fail before T026**.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/analysis/bootstrap.py` to:
 - Perform bootstrap iterations on MAE distribution
 - Implement fallback to 100 iterations if wall-clock time > 5.5h (use `time.time()` at start of loop and check delta before each iteration)
 - Calculate confidence intervals (percentile method)
 - Output `bootstrap_stats.csv`
- [ ] T027 [US3] Implement `code/reporting/tables.py` to generate summary table with mean MAE, 95% CI, and **descriptive trend analysis** (1ns vs 10ns improvement). **Output must include**: 'MAE_1ns', 'MAE_10ns', 'Reduction %', 'Trend Direction' (e.g., 'Improving'). **Cite spec.md SC-005** as the authority for the statistical method (N=3 limitation). **Depends on T026.**
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
- **Foundational (Phase 2.1)**: Depends on Setup completion - BLOCKS all user stories
 - **T006b** (Curated Data) must be completed before **T006c** (Data Validation) to ensure the file exists.
 - **T007a/b** (Utils) must be completed before **T005** (Config) and **T006c** (Validation) as they provide logging and checksum functions.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2.1) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2.1) - **Depends on T015 (US1) completion** for MSD extraction logic. T021 cannot run in parallel with T015.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2.1) - Depends on T015 (US1) results (diffusion coefficients)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (TDD-First)
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2.1), **except** T006b/T006c dependency and T007a/b dependency.
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
# Launch all tests for User Story 1 together (TDD-First):
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
2. Complete Phase 2.1: Foundational (CRITICAL - blocks all stories)
 - **Ensure T006b (Curated Data) is completed** to provide ground truth.
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
- **Critical**: All data loading MUST use the curated `nist_refs.json` file; T006c validates existence, T006b creates it. NO synthetic fallbacks.
- **Critical**: Bootstrap iterations MUST fallback to 100 if wall-clock time > 5.5h (FR-004).
- **Critical**: T026 (Bootstrap) must strictly precede T027 (Summary Table) within Phase 5.
- **Critical**: T001 is split into T001a, T001b, T001c for executability.
- **Critical**: T021 uses concrete values 0.1, 0.2, 0.3 for sensitivity analysis.
- **Critical**: T027 explicitly defines output format for trend analysis and cites spec.md SC-005.
- **Critical**: T016 cites Constitution Principle VI and spec.md FR-008 for R² ≥ 0.95.
- **Critical**: T006b includes checksum verification to ensure reproducibility.
- **Critical**: T014 (Topology) must precede T015 (Simulation) due to file dependency.
- **Critical**: T007a/b (Utils) must precede T005 (Config) and T006c (Validation) due to function dependency.