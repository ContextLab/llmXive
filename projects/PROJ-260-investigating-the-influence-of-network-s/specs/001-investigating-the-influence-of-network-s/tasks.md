# Tasks: Investigating the Influence of Network Structure on Heat Conduction in Amorphous Solids

**Input**: Design documents from `/specs/001-investigate-network-heat-conduction/`
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

- [ ] T001a [P] Create project directory structure: `src/`, `tests/`, `data/raw/`, `data/derived/`, `outputs/`, `data/metadata/`, `data/derived/topology/`, `data/derived/vdos/`, `data/derived/reference/`, `data/derived/correlation/`, `outputs/figures/`, `outputs/reports/`
- [ ] T001b [P] Create `src/__init__.py`, `src/models/__init__.py`, `src/services/__init__.py`, `src/cli/__init__.py`, `src/lib/__init__.py`
- [X] T001c [P] Create `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`, `tests/contract/__init__.py`
- [X] T002 Initialize Python project with `requirements.txt` (numpy, scipy, pandas, scikit-learn, ase, matplotlib, seaborn, networkx, pytest, pytest-cov, pytest-randomly)
- [ ] T003a [P] Create `ruff.toml` with strict linting rules: select=["E", "F", "I", "W"], ignore=[], line-length=88
 - **Content**: Explicitly set `target-version = "py311"`, `preview = true`
- [X] T003b [P] Create `pyproject.toml` [tool.black] section: line-length=88, target-version=['py311'], include='\.pyi?$'

---

## Phase 2: Foundational (Blocking Prerequisites & Data Acquisition)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented, AND securing real data sources.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. All test infrastructure (T012, T013) must be ready before test-writing tasks in Phase 3.

- [X] T004 [P] Create `src/models/simulation_box.py` (Data class for atomic positions, velocities, metadata, thermal conductivity)
- [X] T005 [P] Create `src/models/bond_network.py` (Graph representation: nodes=atoms, edges=bonds, metrics)
- [X] T006 [P] Create `src/models/vibrational_spectrum.py` (Data class for VDOS, participation ratio, frequency bins)
- [ ] T007 [P] Create `src/lib/utils.py` (Checksum verification, logging setup, seed management, and file validation enhancements)
- [X] T008 [P] Create `src/lib/config.py` (Configuration management, path constants, seed initialization)
- [ ] T009 [P] Create directory structure `tests/unit/`, `tests/integration/`, `tests/contract/`
 - **Note**: This task is a blocking prerequisite for test-writing tasks T012-T037. Must **complete** (files created) before T012-T016 can be **written**.
- [X] T010 [P] Configure `pyproject.toml` with pytest plugins (`pytest-randomly`, `pytest-cov`) and coverage thresholds
 - **Note**: This task is a blocking prerequisite for test-writing tasks T012-T037. Must **complete** (config written) before T012-T016 can be **written**.

**Data Acquisition & Reference Generation Tasks (Must precede US Implementation)**

- [ ] T056 [US1] Implement `src/services/data_loader.py` to fetch real amorphous silicon trajectories
 - Fetch datasets using IDs defined in `research.md` Verified Datasets block (e.g., specific Zenodo/Materials Cloud IDs) for **all available** system sizes (N=1000, 2000, 4000).
 - **MUST fail loudly** if download fails or if ID is not found in `research.md`; NO synthetic fallback allowed
 - If specific datasets are missing, write a detailed error report to `data/raw/missing_datasets.log` and exit with code 1. Do not proceed to downstream tasks.
 - Verify checksums against provided manifest
 - Output raw files to `data/raw/` with metadata logs
 - **Do not hardcode IDs**; use the verified list from `research.md`
 - **Scope**: Fetch **all available** realizations for the 3 system sizes. If < 30 realizations exist per size, proceed but flag "Limited Sample" later.
- [ ] T039 [US3] Implement `src/services/independent_source_fetcher.py` (FR-008, US-3)
 - **Depends on T056**: Requires access to simulation box metadata and system sizes.
 - **Fetch Independent κ**: Attempt to download thermal conductivity ($\kappa$) values from **independent sources** (experimental measurements or distinct MD runs) listed in `research.md`.
 - **Strict Independence**: **MUST NOT** generate synthetic values. If no independent source is found for a specific system size, the system MUST raise a `FatalError` and halt the pipeline.
 - Output `data/derived/reference/κ_values.csv` with columns: `system_size`, `temperature`, `kappa_value`, `source_type` (experimental/simulation), `source_id`, `trajectory_id`.
 - Verify independence of source trajectory vs topology source (log to `data/metadata/independence_log.json`).
 - **FR-008 Compliance**: If the source is not independent (same trajectory ID), raise `FatalError`.

**Checkpoint**: Foundation + Data + Reference ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Network Topology Extraction (Priority: P1) 🎯 MVP

**Goal**: Parse MD trajectories, construct bond networks via RDF minimum, and compute local graph metrics.

**Independent Test**: The system can process a single, small amorphous silicon trajectory file and output a CSV containing atomic IDs, coordination numbers, and local bond angle variance without requiring thermal conductivity data or VDOS calculation.

### Tests for User Story 1 (TDD: Write tests first)

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. T012 and T013 MUST precede T017.
> **Execution Note**: These tests are written first (TDD) but can only be *executed* after T017 is implemented.
> **[P] Note**: [P] indicates parallel **writing** capability. Execution is blocked by T017 implementation completion. T009/T010 must complete before T012-T016 can be written.

- [ ] T012 [P] [US1] Contract test for topology schema in `tests/contract/test_topology_schema.py` (Validates CSV columns: atom_id, coord_num, angle_var, is_valid)
 - **Depends on T009, T010** (Completion required before writing)
 - **Note**: Writing phase parallel; execution blocked by T017.
- [ ] T013 [P] [US1] Unit test for RDF calculation in `tests/unit/test_rdf.py` (Verifies cutoff detection logic against known synthetic RDF)
 - **Depends on T009, T010** (Completion required before writing)
 - **Note**: Writing phase parallel; execution blocked by T017.
- [ ] T014 [P] [US1] Unit test for bond network construction in `tests/unit/test_bond_network.py` (Verifies coordination counts match manual calculation for a small cluster)
 - **Depends on T009, T010** (Completion required before writing)
 - **Note**: Writing phase parallel; execution blocked by T017.
- [ ] T015 [US1] Integration test for invalid file handling in `tests/integration/test_topology_errors.py` (Verifies "Invalid File Format" error on corrupted header)
 - **Depends on T009, T010** (Completion required before writing)
- [ ] T016 [US1] Integration test for physical anomaly flagging in `tests/integration/test_topology_anomalies.py` (Verifies flagging of coordination > 6 without halting)
 - **Depends on T009, T010** (Completion required before writing)

### Implementation for User Story 1

- [ ] T017 [US1] Implement `src/services/topology_extractor.py` (FR-001, FR-002)
 - Parse LAMMPS/XYZ using `ase`
 - **Dynamic Cutoff**: Determine bond cutoff dynamically by locating the first minimum of the RDF for the specific dataset (Constitution Principle VII). **MUST** implement this logic as a core step.
 - Construct bond network based on cutoff.
 - Compute local metrics (coordination number, bond angle variance).
 - **Anomaly Flagging**: Implement mandatory flagging of any atom with coordination > 6 as a "Physical Anomaly" without halting the process.
 - Validate average coordination against reference value (4.00 ± 0.05) [UNRESOLVED-CLAIM: c_0a4bbbb1 — status=not_enough_info] and flag result.
 - Output `data/derived/topology/` CSVs.
 - **TDD Note**: Can be developed using a local mock file before T056 succeeds.
- [ ] T018 [US1] Add logging for topology extraction steps and RDF cutoff decisions (US-1 Edge Cases)
 - **Log Levels**: Use `INFO` for steps, `DEBUG` for RDF values.
 - **Format**: `%(asctime)s - %(levelname)s - %(module)s - %(message)s`
 - **Destination**: Both `stdout` and `data/metadata/topology_log.log`.
- [ ] T019 [US1] Create `tests/integration/test_full_topology.py` to verify end-to-end extraction on a small reference file
- [ ] T020 [US1] Implement CLI override mechanism for RDF cutoff (US-1 Edge Cases)
 - Add `--rdf-cutoff-override` argument to CLI.
 - **Default Behavior**: If override is not used, default to the first local minimum of the RDF.
 - Log the decision (override vs. detected minimum vs. ambiguous default) in the execution log.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Vibrational Mode Analysis and Bottleneck Identification (Priority: P2)

**Goal**: Calculate VDOS via VACF, compute participation ratio, and identify topological bottlenecks.

**Independent Test**: The system can take the output of User Story 1 (network topology) and a velocity dump, compute the VDOS, and output a scalar value representing the "density of localized modes" for that specific simulation box.

### Tests for User Story 2

- [ ] T021 [P] [US2] Contract test for VDOS schema in `tests/contract/test_vdos_schema.py` (Validates columns: frequency, vdos, participation_ratio)
 - **Depends on T009, T010**
- [ ] T022 [P] [US2] Unit test for VACF calculation in `tests/unit/test_vacf.py` (Verifies decay behavior on synthetic velocity data)
 - **Depends on T009, T010**
- [ ] T023 [P] [US2] Unit test for participation ratio calculation in `tests/unit/test_participation_ratio.py`
 - **Depends on T009, T010**
- [ ] T024 [US2] Integration test for missing velocity data handling in `tests/integration/test_vdos_errors.py` (Verifies graceful failure of VDOS step, allowing topology to proceed)
 - **Depends on T009, T010**
- [ ] T025 [US2] Integration test for sensitivity analysis in `tests/integration/test_sensitivity.py` (Verifies bottleneck density stability with threshold sweep ±0.5)
 - **Depends on T009, T010**

### Implementation for User Story 2

- [ ] T026 [US2] Implement `src/services/vdos_calculator.py` (FR-003, FR-004)
 - Compute Velocity Autocorrelation Function (VACF)
 - Calculate VDOS via Fourier Transform.
 - **Precision**: **MUST** cast all numerical arrays to `numpy.float64` explicitly to satisfy Constitution Principle VI.
 - Compute Participation Ratio.
 - Identify localized modes (high PR, low frequency).
 - Document numerical tolerance thresholds in code comments and `data/derived/vdos/tolerance_report.txt` (Constitution Principle VI).
 - Output `data/derived/vdos/` CSVs.
- [ ] T027 [US2] Implement `src/services/sensitivity_analyzer.py` (US-2)
 - Sweep under-coordination threshold (±0.5)
 - Calculate bottleneck density (coordination < 3)
 - Report coefficient of variation
 - Output sensitivity report
- [ ] T028 [US2] Add validation for acoustic modes (non-zero low-freq) and high-freq peak (10.0–15.0 THz) in `src/services/vdos_calculator.py` (US-2 Acceptance 1)
 - **Thresholds**: {{claim:c_ae658279}} High-freq peak range: –15.0 THz (positive values) [UNRESOLVED-CLAIM: c_c0d5a1f5 — status=not_enough_info].
 - **Action**: Log warning if acoustic modes are near zero or high-freq peak is missing.
- [ ] T029 [US2] Create `tests/integration/test_full_vdos.py` to verify end-to-end VDOS calculation on a reference box
- [ ] T030 [US2] Document numerical tolerance thresholds in code comments and `data/derived/vdos/tolerance_report.txt` (Constitution Principle VI)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Robustness Validation (Priority: P3)

**Goal**: Aggregate metrics with independent thermal conductivity data, perform correlation analysis with Bootstrap, and validate robustness across three distinct system sizes.

**Independent Test**: The system can ingest three datasets with distinct system sizes (N=1000, 2000, 4000) and pre-computed topology, run the correlation analysis, and output a summary table showing the correlation coefficient, p-value, and 95% confidence interval for each dataset.

### Tests for User Story 3

- [ ] T031 [P] [US3] Contract test for correlation schema in `tests/contract/test_correlation_schema.py` (Validates output: r, p_value, ci, power, corrected_p)
 - **Depends on T009, T010**
- [ ] T032 [P] [US3] Unit test for Bootstrap resampling in `tests/unit/test_bootstrap.py` (Verifies multiple iterations and CI calculation accuracy vs manual calculation with |output - manual| < 1e-6)
 - **Note**: The "manual calculation" oracle must be a deterministic, script-based calculation defined here to serve as the reference for T041.
 - **Depends on T009, T010**
- [ ] T033 [P] [US3] Unit test for multiple-comparison correction in `tests/unit/test_corrections.py` (Bonferroni/FDR)
 - **Depends on T009, T010**
- [ ] T034 [US3] Integration test for independence check in `tests/integration/test_independence_check.py` (Verifies halting if κ source is not independent)
 - **Depends on T009, T010**
- [ ] T035 [US3] Integration test for randomization control in `tests/integration/test_randomization_control.py` (Verifies r≈0, p>0.5 on randomized metrics)
 - **Depends on T009, T010**
- [ ] T036 [US3] Integration test for runtime threshold in `tests/integration/test_runtime_threshold.py` (Verifies ≤30 mins on 4000-atom system)
 - **Depends on T009, T010**
- [ ] T037 [US3] Integration test for Low Power warning in `tests/integration/test_low_power_warning.py` (Verifies warning triggers when power < 0.8)
 - **Depends on T009, T010**

### Implementation for User Story 3

- [ ] T046 [US3] Implement loop to ingest data for **three distinct system sizes (N=1000, 2000, 4000)** and aggregate power metrics (FR-006, Plan Scale/Scope)
 - **Data Source**: Process **all available realizations** fetched by T056 for each of the 3 system sizes.
 - **Statistical Validity**: If available realizations < 30 per size, flag "Low Statistical Power / Limited Sample" in report. Do not fabricate data.
 - Pass sample size count to power calculator.
 - Aggregate power metrics for the full population across the three sizes.
- [ ] T041 [US3] Implement `src/services/statistical_analyzer.py` (FR-005, FR-006, FR-007)
 - **Depends on T046**: Aggregates data produced by T046.
 - Perform Spearman and Pearson correlation.
 - Execute Bootstrap Resampling for confidence interval (sufficient iterations).
 - Apply multiple-comparison correction (Bonferroni/FDR) with unit of testing: **per metric per system-size comparison**.
 - **Power Analysis**: Read effect size from `config.yaml` (fixed value 0.3).
 - **Reference Oracle**: Use the deterministic reference calculation defined in T032 to verify accuracy (|output - manual| < 1e-6).
 - **Limitation Reporting**: If available realizations < 30, flag "Low Statistical Power / Limited Sample" in the final report.
 - Output `data/derived/correlation/` results and summary tables.
- [ ] T042 [US3] Implement finite-size effect validation (compare correlation consistency across sizes) (US-3 Acceptance 1)
 - **Explicitly output the variance value** of correlation coefficients across the three system sizes.
- [ ] T043 [US3] Add "Low Power" warning logic if power < 0.8 (SC-002)
- [ ] T047 [US3] Implement explicit reporting of statistical power value (SC-002)
 - **Effect Size Source**: Read effect size (0.3) from `config.yaml` (created by T048).
 - **Documentation**: The effect size 0.3 is a fixed assumption based on literature review (document source in `outputs/reports/assumptions.md`).
 - Ensure the calculated statistical power is reported in the final summary table and report.
 - Flag "Low Power" if < 0.8.
- [ ] T044 [US3] Create `tests/integration/test_full_correlation.py` to verify end-to-end statistical pipeline
- [ ] T045 [US3] Create `src/cli/main.py` to orchestrate the full pipeline (Topology → VDOS → Reference → Correlation)
 - **Depends on T017, T026, T039, T041** (Not parallel-safe)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final reporting

- [ ] T048 [P] Create `config.yaml` with fixed effect size assumption
 - **Content**: `effect_size: 0.3`, `bootstrap_iterations: a sufficient number of iterations to ensure convergence`, `The random seed will be set to a fixed value to ensure reproducibility.`
 - **Documentation**: Add comment in file: "Effect size 0.3 is a fixed assumption for MVP based on literature review (see outputs/reports/assumptions.md)."
- [ ] T049 [P] Implement `scripts/update_state_hashes.py` to compute SHA256 of all artifacts and update state YAML
- [ ] T050 [P] Generate final report in `outputs/reports/` (PDF/HTML) including all correlation tables, figures, and sensitivity analysis
- [ ] T051 [P] Create `outputs/figures/` (RDF plots, VDOS spectra, Correlation scatter plots with CI bands)
- [ ] T052 [P] Update `README.md` with CLI usage examples
- [ ] T053 [P] Generate API documentation for `src/services/`
- [ ] T054 Run `quickstart.md` validation (if applicable)
- [ ] T055 Verify all acceptance criteria from spec.md are met via automated test suite

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T009/T010 (Test Infra) MUST complete before T012-T037**
 - **T056 (Data Fetch) MUST succeed before T017, T026, T039**
 - **T039 (Independent Source Fetch) MUST complete before T041**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion AND Data Acquisition
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **T012/T013 (Tests) MUST precede T017 (Implementation)**
 - **T056 (Data Fetch) MUST precede T017**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004-T008) can run in parallel
- **Data Acquisition (T056, T039) can run in parallel with Foundational tasks (T004-T008)**
- Once Foundational + Data Acquisition complete, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (writing)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for topology schema in tests/contract/test_topology_schema.py" (T012)
Task: "Unit test for RDF calculation in tests/unit/test_rdf.py" (T013)
Task: "Unit test for bond network construction in tests/unit/test_bond_network.py" (T014)

# Launch all models for User Story 1 together:
Task: "Create src/models/simulation_box.py" (T004)
Task: "Create src/models/bond_network.py" (T005)

# Launch Data Acquisition in parallel with Setup/Foundational:
Task: "Implement data loader for Materials Cloud (T056)"
Task: "Implement independent source fetcher (T039)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories) + **Data Acquisition (T056, T039)**
3. Complete Phase 3: User Story 1 (Tests T012-T016 first, then Implementation T017-T020)
4. **STOP and VALIDATE**: Test User Story 1 independently with real data
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Complete Data Acquisition (Phase 2) → Real data secured
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Developer D: **Data Acquisition (Phase 2)** - Secure real datasets (T056, T039)
3. Once Foundational + Data Acquisition done:
 - Developer A: User Story 1 (Tests T012-T016, then Implementation T017-T020)
 - Developer B: User Story 2
 - Developer C: User Story 3
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (writing phase)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Source**: All trajectory data MUST be fetched from real sources (Materials Cloud/Zenodo) via `ase` or `datasets.load_dataset`. **NO synthetic fallbacks allowed.** T056 must fail loudly if fetch fails (exit code 1, log to `data/raw/missing_datasets.log`).
- **Compute**: CPU-first. Use streaming/chunking if datasets exceed memory (though Spec assumes downsampling for >100k atoms).
- **Independence**: Thermal conductivity values MUST be fetched from **independent sources** (T039). If no independent source is found, the pipeline halts.
- **Statistical Power**: Process **all available realizations** for 3 system sizes. If N<30 per size, report limitation. Effect size is fixed at 0.3 (config.yaml) for MVP.
- **Plan vs Spec Discrepancy**: The Plan's "N≥30 realizations" is a statistical validity target. The current implementation follows Spec FR-006 (3 system sizes) AND Plan's N≥30 requirement, explicitly reporting the limitation if realizations < 30.
- **Precision**: All VDOS and RDF calculations MUST use `numpy.float64` (T026) to satisfy Constitution Principle VI.