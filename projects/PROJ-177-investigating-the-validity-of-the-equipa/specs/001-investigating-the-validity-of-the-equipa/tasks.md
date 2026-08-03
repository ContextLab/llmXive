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

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `artifacts/`, `tests/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, statsmodels, pyyaml, tqdm, pytest)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/checksum_raw_data.py` to generate SHA-256 hashes for `data/raw/` and write the checksums to the project's `state/...yaml` map (Constitution Principle III)
- [X] T005 [P] Implement `code/hash_artifacts.py` to generate content hashes for `artifacts/` and update `state/...yaml` (Constitution Principle V)
- [X] T006 Create `code/config.py` to load material properties (mass, inertia, roughness proxy) and frequency bins from `data/config.yaml`
- [X] T007 Implement `code/main.py` orchestration script with argument parsing for pipeline stages
- [X] T008 Setup `tests/conftest.py` with fixtures for synthetic data generation and random seed pinning
- [X] T009 [P] [Foundational] Implement `code/ingestion.py` function `load_and_sample` to accept a generic `--data-source` CLI argument (local path or generic dataset ID) and implement the random sampling strategy required by Spec Assumption 5 (e.g., `itertools.islice` first N rows or fixed-seed random sample) if the dataset exceeds runner constraints. This task MUST fail loudly if the real fetch fails, with no synthetic fallback (FR-001, Assumption 5). **CRITICAL**: This task MUST record the specific random seed and sample indices used in `artifacts/sampling_metadata.json` to ensure reproducibility (Constitution Principle I).
- [X] T010 [P] [Foundational] Implement `code/ingestion.py` function `validate_metadata` to validate required metadata fields (mass, radius, material type) in the dataset header; if missing, raise a `ValueError` with a specific message indicating which field is missing (Addressing "Assumptions" regarding material properties). This task is scoped to `validate_metadata` to ensure parallel safety with T009.
- [X] T011 [P] [Foundational] Implement `code/ingestion.py` function to handle missing z-axis data by adding a 'pot_incomplete' boolean column to the output dataframe and writing a specific warning log entry (Edge Case: missing z-axis)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Energy Component Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest particle tracking data and driving logs to compute $E_{trans}$, $E_{rot}$, $E_{pot}$, and $E_{vib}$ for every particle/frame.

**Independent Test**: Run ingestion script on a small synthetic CSV subset; verify calculated energies match manual calculations within a high-precision tolerance.

**Dependency Order**: T015 -> T016 -> T017 -> T018 -> T019. (T020 is independent test data generation).

### Tests for User Story 1

- [X] T012 [P] [US1] Unit test for energy formulas in `tests/test_energy.py` (verify $E_{trans} = 0.5mv^2$, etc. with known inputs)
- [X] T013 [P] [US1] Integration test for missing frame interpolation in `tests/test_ingestion.py` (verify linear interpolation logic)
- [X] T014 [P] [US1] Integration test for material-specific mass application in `tests/test_ingestion.py` (verify steel vs. polymer constants)

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/ingestion.py` function to load and sync particle tracking CSVs with driving signal logs (FR-001)
- [X] T016 [US1] Implement `code/ingestion.py` function to handle missing frames via linear interpolation or flagging (Edge Case: missing frames). If frames are missing, interpolate linearly; if a gap is too large, flag the time window and log a warning.
- [X] T017 [US1] Implement `code/ingestion.py` function to compute $v$ and $\omega$ via finite differences from positions/orientations. See Spec FR-002.
- [X] T018 [US1] Implement `code/ingestion.py` function to calculate $E_{trans}$, $E_{rot}$, $E_{pot}$, and $E_{vib}$ using independent physics formulas. **Operational Definition**: For $E_{vib}$, compute the variance of acceleration over a sliding window of N=5 frames. This specific formula is a project-specific assumption required to satisfy FR-002's mandate to "compute vibrational energy" where the spec does not provide a formula. See `data-model.md` for definition. Use config constants (FR-002).
- [X] T020 [US1] [Independent Test Data] Generate 'thermal' vs 'non-thermal' labeled test datasets in `data/derived/` with known ground truth labels for verification of SC-002. **Method**: Use a Maxwell-Boltzmann PDF generator with known parameters for "thermal" and a heavy-tailed Pareto distribution for "non-thermal" to create synthetic CSVs with known labels. **Scope**: These datasets are used for Unit Tests (T012) AND the Integration Test for US2 (T021/T022) to verify the pipeline's ability to classify thermal vs non-thermal behavior. They are not used as primary scientific input.
- [X] T019 [US1] Output computed `energy_samples.csv` to `data/derived/` with columns: particle_id (int), timestamp (float), $E_{trans}$ (float), $E_{rot}$ (float), $E_{pot}$ (float), $E_{vib}$ (float), pot_incomplete (bool). Ensure 'pot_incomplete' column is set to True if z-axis is missing, with warning log: "WARNING: Missing z-axis data for particle {id}". **Verification**: Generate SHA-256 hash of output file, record in `artifacts/energy_samples.hash`, and verify schema matches expected column list and types.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Deviation Assessment and Hypothesis Testing (Priority: P2)

**Goal**: Compare observed energy distributions against Maxwell-Boltzmann prediction using KS and Chi-squared tests.

**Independent Test**: Run analysis on "thermal" vs "non-thermal" labeled datasets; verify p-values and rejection flags match expected ground truth.

**Dependency**: T019 (Phase 3)

### Tests for User Story 2

- [X] T021 [P] [US2] Unit test for KS test logic in `tests/test_stats.py` (verify p-value calculation against known distribution)
- [X] T022 [P] [US2] Unit test for Chi-squared test logic in `tests/test_stats.py` (verify statistic and rejection boolean)
- [X] T023 [P] [US2] Integration test for multi-frequency aggregation in `tests/test_stats.py` (verify summary table generation)

### Implementation for User Story 2

- [X] T024 [US2] Implement `code/stats.py` function to bin energy data by driving frequency and material type, reading input from `data/derived/energy_samples.csv` (Constitution Principle VII). **Error Handling**: If `energy_samples.csv` is missing or invalid, raise `FileNotFoundError` with message "Input file data/derived/energy_samples.csv not found or invalid. Ensure T019 completed successfully."
- [X] T025 [US2] Implement `code/stats.py` function to perform Kolmogorov-Smirnov test against the theoretical Maxwell-Boltzmann distribution (using sample mean to estimate scale parameter if required by KS variant, but explicitly targeting MB) (FR-003)
- [X] T026 [US2] Implement `code/stats.py` function to perform Chi-squared goodness-of-fit test: bin observed counts using standard binning rules and calculate expected counts by integrating the Maxwell-Boltzmann PDF over these bins (FR-004)
- [X] T027 [US2] Implement `code/stats.py` function to apply Benjamini-Hochberg (FDR) correction for multiple comparisons (FR-006)
- [X] T028 [US2] Generate `statistical_results.json` in `artifacts/` containing test types, statistics, p-values, rejection flags, and sample counts per bin (Addressing SC-002)
- [X] T029 [US2] Implement logic to handle non-stationary segments (chirped signals) by binning or exclusion (Edge Case: chirped signals)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

**Goal**: Perform sensitivity analysis on decision thresholds ($\alpha$) and discrepancy boundaries to ensure robustness.

**Independent Test**: Execute sensitivity sweep on fixed dataset; verify output report lists variation in rejection rates across thresholds.

**Dependency**: Reads `artifacts/statistical_results.json` from T028

### Tests for User Story 3

- [X] T030 [P] [US3] Unit test for threshold sweep logic in `tests/test_sensitivity.py` (verify iteration over $\alpha \in \{, 0.05, 0.10\}$)
- [X] T031 [P] [US3] Unit test for discrepancy boundary sweep in `tests/test_sensitivity.py` (verify iteration over boundaries $\{\%, 5\%, 10\%\}$)

### Implementation for User Story 3

- [X] T032 [US3] Implement `code/sensitivity.py` function to sweep significance threshold $\alpha$ over a range of conventional levels and record rejection counts (FR-005)
- [X] T033 [US3] Implement `code/sensitivity.py` function to sweep quasi-thermal energy ratio boundaries over the set $\{\%, 5\%, 10\%\}$ anchored to the reference value 1.0 and record classification rates (FR-005)
- [X] T034 [US3] Generate `sensitivity_analysis_report.json` in `artifacts/` containing threshold vs. rejection rate data (FR-005)
- [X] T035 [US3] Verify robustness: ensure primary rejection decision remains *identical* across the specific threshold set $\{0.01, 0.05, 0.10\}$ and output the boolean comparison result (Success Criterion SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Regression Analysis of Deviation Drivers (Priority: P3)

**Goal**: Perform linear regression to relate deviation magnitude to driving frequency and material roughness; test significance.

**Independent Test**: Run regression on synthetic dataset with known slope/intercept; verify calculated coefficients match within 1% tolerance.

**Dependency**: Reads `artifacts/statistical_results.json` from T028 to derive deviation magnitudes.

### Tests for User Story 4

- [X] T036 [P] [US4] Unit test for linear regression fit in `tests/test_regression.py` (verify slope/intercept calculation)
- [X] T037 [P] [US4] Unit test for t-test significance in `tests/test_regression.py` (verify p-value calculation for slope)

### Implementation for User Story 4

- [X] T038 [US4] Implement `code/regression.py` function to prepare predictors (frequency, roughness proxy mapped from material type in config.yaml) and target (deviation magnitude from `statistical_results.json`)
- [X] T039 [US4] Implement `code/regression.py` function to fit linear model and calculate slope, intercept, $R^2$ (FR-007)
- [X] T040 [US4] Implement `code/regression.py` function to perform t-tests on coefficients and report p-values (FR-008)
- [X] T041 [US4] Generate `regression_results.json` in `artifacts/` with model parameters and significance metrics
- [X] T042 [US4] Verify regression validity: verify the code correctly calculates and reports the p-value for the slope coefficient relating deviation to driving frequency, comparing against a conventional significance threshold in the report (Addressing SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T043 [P] Documentation updates in `README.md` and `docs/`
- [X] T044 [P] Run `ruff check --fix` on all code files to remove unused imports and fix formatting
- [X] T045 [P] Refactor loops in `code/ingestion.py` to use vectorized numpy operations for performance
- [X] T046 [P] Add unit test `test_large_dataset_memory` in `tests/unit/` to verify memory usage stays within acceptable limits with large inputs
- [X] T047 [P] Add unit test `test_empty_bin_handling` in `tests/unit/` to verify graceful handling of empty frequency bins
- [X] T048 [P] Run `quickstart.md` validation to ensure end-to-end pipeline execution
- [X] T049a [P] [Polish] Implement `code/ingestion.py` CLI flag `--local-only` to enforce local-only mode. If `--data-source` is a remote ID and `--local-only` is set, raise an error. If `--local-only` is NOT set, allow remote fetching but enforce sampling if dataset size > 14GB (aligning with Spec Assumption 5).
- [X] T049b [P] [Polish] Add unit test `test_external_fetch_fails` in `tests/unit/` to assert that attempting to fetch a remote dataset without sampling enabled (when size > 14GB) raises a clear error, and that sampling works correctly when enabled.

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
- **Data Source Specificity**: Task T009 explicitly requires implementation of a fetcher for real data (generic `--data-source`) rather than generic "download" instructions, ensuring the execution gate's fabrication guard is satisfied.
- **Ordering Constraint**: T024 (binning) and T025 (KS test) are explicitly ordered after T019 (energy output) to ensure the verification script does not run before the evaluation data is computed.
- **Streaming Requirement**: Task T009 mandates streaming/sampling the full real dataset to respect memory constraints without resorting to synthetic data.
- **Fail Loudly**: Task T009 ensures that any failure in fetching real data raises an error, preventing silent fallback to synthetic data.
- **Sampling Transparency**: Task T009 requires explicit documentation of any sampling strategy used.
- **Verified Data Injection**: Tasks T010 and T018 ensure that metadata is validated and labeled datasets are generated to prevent assumptions or fabrication.
- **Vibrational Energy Definition**: Task T018 explicitly defines $E_{vib}$ as variance of acceleration over a sliding window of N=5 frames, linking to FR-002 (project-specific operational definition).
- **Z-Axis Handling**: Task T011 and T019 explicitly handle missing z-axis data by flagging, not failing, while T010 ensures required fields are present.
- **Labeled Test Datasets**: Task T020 explicitly generates 'thermal' vs 'non-thermal' datasets for SC-002 verification using synthetic distributions with known parameters for testing only.
- **Scientific Integrity**: Task T039 and T042 verify code logic and reporting, not specific scientific outcomes (p < 0.05).
- **External Fetch Prohibition**: Task T049a/T049b explicitly enforce local-only mode OR sampling for remote sources, ensuring compliance with Spec Assumption 5 and US-1.
- **Reproducibility**: Task T009 mandates recording sampling seed and indices in `artifacts/sampling_metadata.json`.
- **Error Handling**: Task T024 includes explicit error handling for missing input files.