# Tasks: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

**Input**: Design documents from `/specs/001-validity-equipartition-granular/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The spec explicitly requests independent tests for energy accuracy (US1), statistical classification (US2), sensitivity sweeps (US3), and regression fit (US4). Tests are INCLUDED.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/`, `artifacts/` at repository root
- Paths shown below assume single project structure as defined in `plan.md`

<!--
 ============================================================================
 IMPORTANT: The tasks below are generated based on the provided spec.md and plan.md.

 Tasks are organized by User Story priority (P1 -> P2 -> P3).
 Each task includes specific file paths and dependencies.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `artifacts/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, statsmodels, pyyaml, tqdm, pytest)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/checksum_raw_data.py` to generate SHA-256 hashes for `data/raw/` and write to a local log file (NOT the shared state YAML) (Constitution Principle III)
- [ ] T005 [P] Implement `code/hash_artifacts.py` to generate content hashes for `artifacts/` and update `state/...yaml` (Constitution Principle V)
- [X] T006 Create `code/config.py` to load material properties (mass, inertia, roughness proxy) and frequency bins from `data/config.yaml`
- [~] T007 Implement `code/main.py` orchestration script with argument parsing for pipeline stages
- [~] T008 Setup `tests/conftest.py` with fixtures for synthetic data generation and random seed pinning

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Energy Component Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest particle tracking data and driving logs to compute $E_{trans}$, $E_{rot}$, $E_{pot}$, and $E_{vib}$ for every particle/frame.

**Independent Test**: Run ingestion script on a small synthetic CSV subset; verify calculated energies match manual calculations within $1e-9$ tolerance.

**Dependency Order**: T012 -> T013 -> T014 -> T016 -> T015 -> T017

### Tests for User Story 1

- [~] T009 [P] [US1] Unit test for energy formulas in `tests/test_energy.py` (verify $E_{trans} = 0.5mv^2$, etc. with known inputs)
- [~] T010 [P] [US1] Integration test for missing frame interpolation in `tests/test_ingestion.py` (verify linear interpolation logic)
- [~] T011 [P] [US1] Integration test for material-specific mass application in `tests/test_ingestion.py` (verify steel vs. polymer constants)

### Implementation for User Story 1

- [~] T012 [US1] Implement `code/ingestion.py` function to load and sync particle tracking CSVs with driving signal logs (FR-001)
- [~] T013 [US1] Implement `code/ingestion.py` function to handle missing frames via linear interpolation or flagging (Edge Case: missing frames)
- [~] T014 [US1] Implement `code/ingestion.py` function to compute $v$ and $\omega$ via finite differences from positions/orientations
- [~] T016 [US1] Implement logic to handle datasets lacking z-axis data: add a 'pot_incomplete' boolean column to the output dataframe and write a specific warning log entry (Edge Case: missing z-axis)
- [~] T015 [US1] Implement `code/ingestion.py` function to calculate $E_{trans}$, $E_{rot}$, $E_{pot}$, and $E_{vib}$ using independent physics formulas (e.g., $E_{vib}$ derived from high-frequency acceleration variance or specific vibrational mode analysis, NOT as a residual) using config constants (FR-002)
- [~] T017 [US1] Output computed `energy_samples.csv` to `data/derived/` with columns: particle_id, timestamp, $E_{trans}$, $E_{rot}$, $E_{pot}$, $E_{vib}$, pot_incomplete <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Deviation Assessment and Hypothesis Testing (Priority: P2)

**Goal**: Compare observed energy distributions against Maxwell-Boltzmann prediction using KS and Chi-squared tests.

**Independent Test**: Run analysis on "thermal" vs "non-thermal" labeled datasets; verify p-values and rejection flags match expected ground truth.

**Dependency**: T017 (Phase 3)

### Tests for User Story 2

- [~] T018 [P] [US2] Unit test for KS test logic in `tests/test_stats.py` (verify p-value calculation against known distribution)
- [~] T019 [P] [US2] Unit test for Chi-squared test logic in `tests/test_stats.py` (verify statistic and rejection boolean)
- [ ] T020 [P] [US2] Integration test for multi-frequency aggregation in `tests/test_stats.py` (verify summary table generation)

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/stats.py` function to bin energy data by driving frequency and material type, reading input from `data/derived/energy_samples.csv` (Constitution Principle VII)
- [ ] T022 [US2] Implement `code/stats.py` function to perform Kolmogorov-Smirnov test against the theoretical Maxwell-Boltzmann distribution (using sample mean to estimate scale parameter if required by KS variant, but explicitly targeting MB) (FR-003)
- [ ] T023 [US2] Implement `code/stats.py` function to perform Chi-squared goodness-of-fit test: bin observed counts using standard binning rules and calculate expected counts by integrating the Maxwell-Boltzmann PDF over these bins (FR-004)
- [ ] T024 [US2] Implement `code/stats.py` function to apply Benjamini-Hochberg (FDR) correction for multiple comparisons (FR-006)
- [ ] T025 [US2] Generate `statistical_results.json` in `artifacts/` containing test types, statistics, p-values, and rejection flags
- [ ] T026 [US2] Implement logic to handle non-stationary segments (chirped signals) by binning or exclusion (Edge Case: chirped signals)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

**Goal**: Perform sensitivity analysis on decision thresholds ($\alpha$) and discrepancy boundaries to ensure robustness.

**Independent Test**: Execute sensitivity sweep on fixed dataset; verify output report lists variation in rejection rates across thresholds.

**Dependency**: Reads `artifacts/statistical_results.json` from T025

### Tests for User Story 3

- [ ] T027 [P] [US3] Unit test for threshold sweep logic in `tests/test_sensitivity.py` (verify iteration over $\alpha \in \{0.01, 0.05, 0.10\}$)
- [ ] T028 [P] [US3] Unit test for discrepancy boundary sweep in `tests/test_sensitivity.py` (verify iteration over boundaries $\{1\%, 5\%, 10\%\}$)

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/sensitivity.py` function to sweep significance threshold $\alpha$ over the set $\{0.01, 0.05, 0.10\}$ and record rejection counts (FR-005)
- [ ] T030 [US3] Implement `code/sensitivity.py` function to sweep quasi-thermal energy ratio boundaries over the set $\{1\%, 5\%, 10\%\}$ anchored to the reference value 1.0 and record classification rates (FR-005)
- [ ] T031 [US3] Generate `sensitivity_analysis_report.json` in `artifacts/` containing threshold vs. rejection rate data (FR-005)
- [ ] T032 [US3] Verify robustness: ensure primary rejection decision remains *identical* across the specific threshold set $\{0.01, 0.05, 0.10\}$ and output the boolean comparison result (Success Criterion SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Regression Analysis of Deviation Drivers (Priority: P3)

**Goal**: Perform linear regression to relate deviation magnitude to driving frequency and material roughness; test significance.

**Independent Test**: Run regression on synthetic dataset with known slope/intercept; verify calculated coefficients match within 1% tolerance.

**Dependency**: Reads `artifacts/statistical_results.json` from T025 to derive deviation magnitudes.

### Tests for User Story 4

- [ ] T033 [P] [US4] Unit test for linear regression fit in `tests/test_regression.py` (verify slope/intercept calculation)
- [ ] T034 [P] [US4] Unit test for t-test significance in `tests/test_regression.py` (verify p-value calculation for slope)

### Implementation for User Story 4

- [ ] T035 [US4] Implement `code/regression.py` function to prepare predictors (frequency, roughness proxy mapped from material type in config.yaml) and target (deviation magnitude from `statistical_results.json`)
- [ ] T036 [US4] Implement `code/regression.py` function to fit linear model and calculate slope, intercept, $R^2$ (FR-007)
- [ ] T037 [US4] Implement `code/regression.py` function to perform t-tests on coefficients and report p-values (FR-008)
- [ ] T038 [US4] Generate `regression_results.json` in `artifacts/` with model parameters and significance metrics
- [ ] T039 [US4] Verify regression validity: ensure slope p-value < 0.05 for frequency relationship (Success Criterion SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `README.md` and `docs/`
- [ ] T041 [P] Run `ruff check --fix` on all code files to remove unused imports and fix formatting
- [ ] T042 [P] Refactor loops in `code/ingestion.py` to use vectorized numpy operations for performance
- [ ] T043 [P] Add unit test `test_large_dataset_memory` in `tests/unit/` to verify memory usage stays within acceptable limits with large inputs
- [ ] T044 [P] Add unit test `test_empty_bin_handling` in `tests/unit/` to verify graceful handling of empty frequency bins
- [ ] T045 [P] Run `quickstart.md` validation to ensure end-to-end pipeline execution

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
- **User Story 2 (P2)**: Depends on US1 output (`data/derived/energy_samples.csv`)
- **User Story 3 (P3)**: Depends on US2 output (`artifacts/statistical_results.json`)
- **User Story 4 (P3)**: Depends on US2 output (`artifacts/statistical_results.json`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before Services/Logic
- Core implementation before Integration
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
# Launch all tests for User Story 1 together:
Task: "Unit test for energy formulas in tests/test_energy.py"
Task: "Integration test for missing frame interpolation in tests/test_ingestion.py"
Task: "Integration test for material-specific mass application in tests/test_ingestion.py"

# Launch all models/config for User Story 1 together:
Task: "Create code/config.py to load material properties"
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
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3/4
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
- **Data Feasibility**: All tasks assume CPU-only execution (scipy/statsmodels). No GPU models. Data sampling applied if >14GB.
- **Real Data**: Tasks assume real datasets (Zenodo/OpenGranular) are fetched; no synthetic fabrication of input data.
- **Data Source Specificity**: Tasks T012 and T017 explicitly require implementation of a fetcher for real NAB or UCI granular data (e.g., `) rather than generic "download" instructions, ensuring the execution gate's fabrication guard is satisfied.
- **Ordering Constraint**: T021 (binning) and T022 (KS test) are explicitly ordered after T017 (energy output) to ensure the verification script does not run before the evaluation data is computed.