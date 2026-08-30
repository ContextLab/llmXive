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

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `outputs/`)
- [X] T002 Initialize Python project with `requirements.txt` (numpy, scipy, pandas, scikit-learn, ase, matplotlib, seaborn, networkx, pytest, pytest-cov, pytest-randomly)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites & Data Acquisition)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented, AND securing real data sources.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. All test infrastructure (T009, T010) must be ready before test-writing tasks in Phase 3.

- [ ] T004 [P] Create `src/models/simulation_box.py` (Data class for atomic positions, velocities, metadata, thermal conductivity)
- [ ] T005 [P] Create `src/models/bond_network.py` (Graph representation: nodes=atoms, edges=bonds, metrics)
- [ ] T006 [P] Create `src/models/vibrational_spectrum.py` (Data class for VDOS, participation ratio, frequency bins)
- [ ] T007 [P] Create `src/lib/utils.py` (Checksum verification, logging setup, seed management, and file validation enhancements)
- [ ] T008 [P] Create `src/lib/config.py` (Configuration management, path constants, seed initialization)
- [ ] T009 Setup `tests/` directory structure (`unit/`, `integration/`, `contract/`)
 - **Note**: This task is a prerequisite for T012-T037. Do not mark as parallel-safe if it implies concurrent execution with test-writing tasks.
- [ ] T010 Configure `pytest` with `pytest-randomly` and coverage thresholds in `pyproject.toml`
 - **Note**: This task is a prerequisite for T012-T037. Do not mark as parallel-safe if it implies concurrent execution with test-writing tasks.

**Data Acquisition Tasks (Must precede US Implementation)**

- [ ] T056 [US1] Implement `src/services/data_loader.py` to fetch real amorphous silicon trajectories
 - Fetch datasets using IDs defined in `research.md` Verified Datasets block (e.g., specific Zenodo/Materials Cloud IDs)
 - **MUST fail loudly** if download fails or if ID is not found in `research.md`; NO synthetic fallback allowed
 - If specific datasets are missing, the project MUST halt and log the missing IDs for manual acquisition
 - Verify checksums against provided manifest
 - Output raw files to `data/raw/` with metadata logs
 - **Do not hardcode IDs**; use the verified list from `research.md`
- [ ] T057 [US1] Implement streaming logic for large datasets (if >7GB) using `datasets.load_dataset(..., streaming=True)`
 - Process chunks to compute RDF/Topology without loading full dataset into RAM
 - Log streaming progress and chunk counts
 - **Defensive Measure**: If the 3 system sizes (N=1000, 2000, 4000) with required realizations exceed memory, explicitly downsample *real* data (as per Spec Assumptions) rather than failing or using synthetic data.
 - **Note**: Optional if strict downsampling is enforced per Spec Assumptions, but retained for robustness.
- [ ] T058 [US3] Implement `src/services/external_data_verifier.py` to validate thermal conductivity sources
 - Check that κ values come from independent sources (experimental or distinct MD runs)
 - Cross-reference with `data/metadata/independence_log.json` (schema defined in `data-model.md`)
 - Halt pipeline if independence cannot be verified

**Checkpoint**: Foundation + Data ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Network Topology Extraction (Priority: P1) 🎯 MVP

**Goal**: Parse MD trajectories, construct bond networks via RDF minimum, and compute local graph metrics.

**Independent Test**: The system can process a single, small amorphous silicon trajectory file and output a CSV containing atomic IDs, coordination numbers, and local bond angle variance without requiring thermal conductivity data or VDOS calculation.

### Tests for User Story 1 (TDD: Write tests first)

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. T012 and T013 MUST precede T017.
> **Execution Note**: These tests are written first (TDD) but can only be *executed* after T017 is implemented.

- [ ] T012 [P] [US1] Contract test for topology schema in `tests/contract/test_topology_schema.py` (Validates CSV columns: atom_id, coord_num, angle_var, is_valid)
- [ ] T013 [P] [US1] Unit test for RDF calculation in `tests/unit/test_rdf.py` (Verifies cutoff detection logic against known synthetic RDF)
- [ ] T014 [P] [US1] Unit test for bond network construction in `tests/unit/test_bond_network.py` (Verifies coordination counts match manual calculation for a small cluster)
- [ ] T015 [US1] Integration test for invalid file handling in `tests/integration/test_topology_errors.py` (Verifies "Invalid File Format" error on corrupted header)
- [ ] T016 [US1] Integration test for physical anomaly flagging in `tests/integration/test_topology_anomalies.py` (Verifies flagging of coordination > 6 without halting)

### Implementation for User Story 1

- [ ] T017 [US1] Implement `src/services/topology_extractor.py` (FR-001, FR-002)
 - Parse LAMMPS/XYZ using `ase`
 - Calculate RDF and identify first minimum (dynamic cutoff)
 - Construct bond network based on cutoff
 - Compute local metrics (coordination number, bond angle variance)
 - **Flag "Physical Anomaly" for any atom with coordination > 6** (do not halt)
 - Validate average coordination against reference value (4.00 ± 0.05) [UNRESOLVED-CLAIM: c_a0633ebf — status=not_enough_info] and flag result
 - Output `data/derived/topology/` CSVs
- [ ] T018 [US1] Add logging for topology extraction steps and RDF cutoff decisions (US-1 Edge Cases)
- [ ] T019 [US1] Create `tests/integration/test_full_topology.py` to verify end-to-end extraction on a small reference file
- [ ] T020 [US1] Implement CLI override mechanism for RDF cutoff (US-1 Edge Cases)
 - Add `--rdf-cutoff-override` argument to CLI
 - Implement logic to log decision when override is used vs. detected minimum vs. ambiguous default
 - Default to first local minimum if RDF is ambiguous and log this decision

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Vibrational Mode Analysis and Bottleneck Identification (Priority: P2)

**Goal**: Calculate VDOS via VACF, compute participation ratio, and identify topological bottlenecks.

**Independent Test**: The system can take the output of User Story 1 (network topology) and a velocity dump, compute the VDOS, and output a scalar value representing the "density of localized modes" for that specific simulation box.

### Tests for User Story 2

- [ ] T021 [P] [US2] Contract test for VDOS schema in `tests/contract/test_vdos_schema.py` (Validates columns: frequency, vdos, participation_ratio)
- [ ] T022 [P] [US2] Unit test for VACF calculation in `tests/unit/test_vacf.py` (Verifies decay behavior on synthetic velocity data)
- [ ] T023 [P] [US2] Unit test for participation ratio calculation in `tests/unit/test_participation_ratio.py`
- [ ] T024 [US2] Integration test for missing velocity data handling in `tests/integration/test_vdos_errors.py` (Verifies graceful failure of VDOS step, allowing topology to proceed)
- [ ] T025 [US2] Integration test for sensitivity analysis in `tests/integration/test_sensitivity.py` (Verifies bottleneck density stability with threshold sweep ±0.5)

### Implementation for User Story 2

- [ ] T026 [US2] Implement `src/services/vdos_calculator.py` (FR-003, FR-004)
 - Compute Velocity Autocorrelation Function (VACF)
 - Calculate VDOS via Fourier Transform
 - Compute Participation Ratio
 - Identify localized modes (high PR, low frequency) [UNRESOLVED-CLAIM: c_ecb89d6d — status=not_enough_info]
 - Output `data/derived/vdos/` CSVs
- [ ] T027 [US2] Implement `src/services/sensitivity_analyzer.py` (US-2)
 - Sweep under-coordination threshold (±0.5)
 - Calculate bottleneck density (coordination < 3) [UNRESOLVED-CLAIM: c_ed49b6d0 — status=not_enough_info]
 - Report coefficient of variation
 - Output sensitivity report
- [ ] T028 [US2] Add validation for acoustic modes (non-zero low-freq) and high-freq peak (-15 THz) in `src/services/vdos_calculator.py` (US-2 Acceptance 1)
- [ ] T029 [US2] Create `tests/integration/test_full_vdos.py` to verify end-to-end VDOS calculation on a reference box
- [ ] T030 [US2] Document numerical tolerance thresholds in code comments and `data/derived/vdos/tolerance_report.txt` (Constitution Principle VI)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Robustness Validation (Priority: P3)

**Goal**: Aggregate metrics with independent thermal conductivity data, perform correlation analysis with Bootstrap, and validate robustness across three distinct system sizes.

**Independent Test**: The system can ingest three datasets with distinct system sizes (N=1000, 2000, 4000) and pre-computed topology, run the correlation analysis, and output a summary table showing the correlation coefficient, p-value, and 95% confidence interval for each dataset.

### Tests for User Story 3

- [ ] T031 [P] [US3] Contract test for correlation schema in `tests/contract/test_correlation_schema.py` (Validates output: r, p_value, ci, power, corrected_p)
- [ ] T032 [P] [US3] Unit test for Bootstrap resampling in `tests/unit/test_bootstrap.py` (Verifies multiple iterations and CI calculation accuracy vs manual calculation with |output - manual| < 1e-6)
 - **Note**: The "manual calculation" oracle must be a deterministic, script-based calculation defined here to serve as the reference for T041.
- [ ] T033 [P] [US3] Unit test for multiple-comparison correction in `tests/unit/test_corrections.py` (Bonferroni/FDR)
- [ ] T034 [US3] Integration test for independence check in `tests/integration/test_independence_check.py` (Verifies halting if κ source is not independent)
- [ ] T035 [US3] Integration test for randomization control in `tests/integration/test_randomization_control.py` (Verifies r≈0, p>0.5 on randomized metrics)
- [ ] T036 [US3] Integration test for runtime threshold in `tests/integration/test_runtime_threshold.py` (Verifies ≤30 mins on 4000-atom system)
- [ ] T037 [US3] Integration test for Low Power warning in `tests/integration/test_low_power_warning.py` (Verifies warning triggers when power < 0.8)

### Implementation for User Story 3

- [ ] T039 [US3] Implement `src/services/reference_generator.py` (FR-008)
 - Generate independent κ values (Cahill-Pohl or disjoint trajectory Green-Kubo)
 - **Independence Constraint**: If using the Cahill-Pohl model, it MUST be parameterized using *only* system size and temperature metadata, NOT the specific atomic trajectory of the predictor variable.
 - If the model requires trajectory-specific inputs, fetch a **distinct** trajectory from a separate source.
 - Verify independence of source trajectory vs topology source.
 - Output `data/derived/reference/` CSVs
- [ ] T041 [US3] Implement `src/services/statistical_analyzer.py` (FR-005, FR-006, FR-007)
 - Aggregate topology, VDOS, and κ data across **three distinct system sizes: N=1000, N=2000, N=4000** (per Spec FR-006)
 - **Note**: The Plan's requirement for "N≥30 realizations" is flagged as a potential scope creep/memory conflict. This task implements the Spec requirement (3 sizes) while logging the Plan's N≥30 target as a future scalability goal.
 - Perform Spearman and Pearson correlation
 - Execute Bootstrap Resampling for confidence interval (sufficient iterations)
 - Apply multiple-comparison correction (Bonferroni/FDR) with unit of testing: **per metric per system-size comparison**
 - Perform Power Analysis (SC-002) using `statsmodels.stats.power` with explicit effect size assumptions
 - **Reference Oracle**: Use the deterministic reference calculation defined in T032 to verify accuracy (|output - manual| < 1e-6).
 - Output `data/derived/correlation/` results and summary tables
- [ ] T042 [US3] Implement finite-size effect validation (compare correlation consistency across sizes) (US-3 Acceptance 1)
 - **Explicitly output the variance value** of correlation coefficients across the three system sizes
- [ ] T043 [US3] Add "Low Power" warning logic if power < 0.8 (SC-002)
- [ ] T047 [US3] Implement explicit reporting of statistical power value (SC-002)
 - Ensure the calculated statistical power is reported in the final summary table and report [UNRESOLVED-CLAIM: c_079fd510 — status=not_enough_info]
 - Flag "Low Power" if < 0.8
- [ ] T044 [US3] Create `tests/integration/test_full_correlation.py` to verify end-to-end statistical pipeline
- [ ] T045 [US3] Create `src/cli/main.py` to orchestrate the full pipeline (Topology → VDOS → Reference → Correlation)
 - **Depends on T017, T026, T039, T041** (Not parallel-safe)
- [ ] T046 [US3] Implement loop to ingest data for **three distinct system sizes (N=1000, 2000, 4000)** and aggregate power metrics (FR-006, Plan Scale/Scope)
 - Pass sample size count to power calculator
 - Aggregate power metrics for the full population across the three sizes

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final reporting

- [ ] T048 [P] Implement `scripts/update_state_hashes.py` (Phase 6) to compute SHA256 of all artifacts and update state YAML
- [ ] T049 [P] Generate final report in `outputs/reports/` (PDF/HTML) including all correlation tables, figures, and sensitivity analysis
- [ ] T050 [P] Create `outputs/figures/` (RDF plots, VDOS spectra, Correlation scatter plots with CI bands)
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
- **Data Acquisition (T056, T057, T058) can run in parallel with Foundational tasks (T004-T008)**
- Once Foundational + Data Acquisition complete, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
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
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories) + **Data Acquisition (T056-T058)**
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
2. Developer D: **Data Acquisition (Phase 2)** - Secure real datasets
3. Once Foundational + Data Acquisition done:
 - Developer A: User Story 1 (Tests T012-T016, then Implementation T017-T020)
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Data Source**: All trajectory data MUST be fetched from real sources (Materials Cloud/Zenodo) via `ase` or `datasets.load_dataset`. **NO synthetic fallbacks allowed.** T056 must fail loudly if fetch fails.
- **Compute**: {{claim:c_4dbb3776}}. Use streaming/chunking (T057) if datasets exceed memory.
- **Independence**: Thermal conductivity values MUST be verified as independent (T058) before correlation analysis (T041).
- **Statistical Power**: Ensure data for **three distinct system sizes (1000, 2000, 4000)** is processed to satisfy FR-006 and SC-002.
- **Plan vs Spec Discrepancy**: The Plan's "N≥30 realizations" is flagged as a potential scope creep. This implementation strictly follows Spec FR-006 (3 system sizes) while logging the Plan's target as a future goal.