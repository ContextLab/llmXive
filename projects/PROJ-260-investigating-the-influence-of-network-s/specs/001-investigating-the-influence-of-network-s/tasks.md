---
description: "Task list template for feature implementation"
---

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

- [X] T001a [P] Create data directories: `data/raw/`, `data/derived/`, `data/derived/topology/`, `data/derived/vdos/`, `data/derived/reference/`, `data/derived/correlation/`, `data/metadata/`
 - **Implementation**: Create a single script `scripts/setup_dirs.py` that creates all required data directories in one atomic operation.
- [X] T001b [P] Create output directories: `outputs/`, `outputs/figures/`, `outputs/reports/`
 - **Implementation**: Extend `scripts/setup_dirs.py` to create output directories.
- [X] T001c [P] Create `src/__init__.py`, `src/models/__init__.py`, `src/services/__init__.py`, `src/cli/__init__.py`, `src/lib/__init__.py`
- [X] T002 [P] Initialize Python project with `requirements.txt` (numpy>=1.24, scipy>=1.10, pandas>=2.0, scikit-learn>=1.3, ase>=3.22, matplotlib>=3.7, seaborn>=0.12, networkx>=3.1, pytest>=7.4, pytest-cov>=4.1, pytest-randomly>=3.15, statsmodels>=0.14)
 - **Note**: All dependencies must have explicit version constraints to ensure reproducibility (Constitution Principle I).
- [X] T003a [P] Create `ruff.toml` with strict linting rules: select=["E", "F", "I", "W"], ignore=[], line-length=88
 - **Content**: Explicitly set `target-version = "py311"`, `preview = true`
- [X] T003b [P] Create `pyproject.toml` [tool.black] section: line-length=88, target-version=['py311'], include='\.pyi?$'

---

## Phase 2: Foundational (Blocking Prerequisites & Data Acquisition)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented, AND securing real data sources.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. All test infrastructure (T009, T010) must be ready before test-writing tasks in Phase 3.

- [X] T004 [P] Create `src/models/simulation_box.py` (Data class for atomic positions, velocities, and metadata)
- [X] T005 [P] Create `src/models/bond_network.py` (Graph representation: nodes=atoms, edges=bonds, metrics)
- [X] T006 [P] Create `src/models/vibrational_spectrum.py` (Data class for VDOS, participation ratio, frequency bins)
- [X] T007 [P] Create `src/lib/utils.py` (Checksum verification, logging setup, seed management, and file validation enhancements)
- [X] T008 [P] Create `src/lib/config.py` (Configuration management, path constants, seed initialization)
- [X] T009 [P] Create test package `__init__.py` files in `tests/unit/`, `tests/integration/`, and `tests/contract/`
 - **Note**: Atomic task for test infrastructure.
- [X] T010 [P] Configure `pyproject.toml` with pytest plugins (`pytest-randomly`, `pytest-cov`) and coverage thresholds
 - **Note**: This task is a blocking prerequisite for test-writing tasks T012-T037. Must **complete** (config written) before T012-T016 can be **written**.

**Data Acquisition & Reference Generation Tasks (Must precede US Implementation)**

- [X] T055a [Foundational] Generate `data/metadata/dataset_registry.json` with required dataset IDs
 - **Purpose**: Create the registry file required by T056 to fetch data.
 - **Logic**: Populate with IDs for three system sizes (N=1000, 2000, 4000) from verified sources (Materials Cloud/Zenodo).
 - **Output**: `data/metadata/dataset_registry.json`.
- [X] T055b [Foundational] Generate `data/metadata/valid_sources.json` for κ source validation
 - **Purpose**: Create the registry file required by T057 to validate κ source independence.
 - **Logic**: Populate with valid source types (e.g., 'experimental', 'distinct_simulation') and their IDs.
 - **Output**: `data/metadata/valid_sources.json`.
- [X] T055 [Foundational] Implement `src/services/registry_validator.py` to verify `data/metadata/dataset_registry.json`
 - **Depends on T001, T008, T055a**: Requires directory structure, path configuration, and registry file.
 - **Schema Validation**: Verify the registry file exists and contains a list of objects with fields: `system_size` (int), `zenodo_id` (string), `realization_count` (int).
 - **HALT Condition**: If the file is missing, invalid JSON, or schema mismatch, **HALT** with a fatal error code 1. Do not proceed to T056.
 - **Output**: Write a validation log to `data/metadata/registry_validation.log`.
- [X] T056 [Foundational] Implement `src/services/data_loader.py` to fetch real amorphous silicon trajectories
 - **Depends on T055**: Requires validated registry file.
 - **Dataset IDs**: **MUST** fetch datasets using IDs listed in `data/metadata/dataset_registry.json`. **Do NOT hardcode IDs**.
 - **API Logic**: Use `requests` to fetch metadata from Zenodo API endpoint. Parse `metadata['keywords']` or `metadata['description']` to identify realizations. Count files in the download directory to verify `realization_count`.
 - **Validation**: **MUST** verify that data exists for **all three** required system sizes (N=1000, 2000, 4000) as listed in the registry. If any size is missing, **HALT** with a fatal error.
 - **Realization Count**: If `realization_count < 30` for any size, **LOG** a "Low Power Warning" and proceed (do NOT halt), as Spec FR-006 only requires 3 distinct sizes.
 - **MUST fail loudly** if download fails or if ID is not found; NO synthetic fallback allowed.
 - **ID Extraction**: **MUST** extract the `trajectory_id` from the fetched metadata and write it to `data/metadata/trajectory_ids.json` for T039/T057 to consume.
 - **Constitution III Compliance**: **MUST** compute and record the SHA256 checksum of all downloaded files in `state/projects/PROJ-260-investigating-the-influence-of-network-s.yaml` before proceeding.
- [X] T039 [Foundational] Implement `src/services/reference_generator.py` to verify trajectory ID independence
 - **Depends on T056**: Requires `trajectory_ids.json` to be present.
 - **Input Schema**: Accepts `trajectory_ids.json` (from T056) and `kappa_source_id` (extracted from the `source_id` column of the CSV produced by T057).
 - **Logic**: Compare `source_id` against `trajectory_source`.
 - **Error Handling**: If `source_id == trajectory_source`, **HALT** with FatalError: "Circular Dependency Detected" (Exit Code 2).
 - **Output**: Write validation result to `data/metadata/independence_check.log`.
- [X] T057 [Foundational] Implement `src/services/kappa_ingester.py` to ingest researcher-provided independent κ values
 - **Depends on T039, T055b, T056**: Requires validated registry, trajectory IDs, independence check logic, and valid sources registry.
 - **Input Mechanism**: Implement a CLI argument `--kappa-file` and a config fallback `data/derived/reference/kappa_values.csv`.
 - **Schema**: The CSV must have columns: `system_size`, `kappa`, `source_id`, `source_type`, `trajectory_id`.
 - **Source Validation**: `source_id` must be a lowercase string matching regex `^[a-z0-9_]+$` and present in `data/metadata/valid_sources.json`. `source_type` must be one of the valid types (e.g., 'experimental', 'distinct_simulation').
 - **Independence Check**: **MUST** call `reference_generator.py` (T039) to verify that the `source_id` in the input file is **NOT** the same as the `trajectory_source` extracted in T056. If `source_id == trajectory_source`, **HALT** with FatalError: "Circular Dependency Detected".
 - **Output**: Write validated κ values to `data/derived/reference/kappa_values.csv`.
 - **Error Handling**: If the file is missing, invalid, or fails independence check, **HALT** with a fatal error (FR-008).
- [X] T057b [P] [US1/US2 Only] Implement `src/services/mock_kappa_generator.py` for US1/US2 testing
 - **Purpose**: Generate mock κ values for US1/US2 testing to avoid blocking on T057 during early development.
 - **Logic**: Generate random κ values based on system size with a fixed seed. Write to `data/derived/reference/mock_kappa_values.csv`.
 - **Usage**: Only used if `--mode=test` is passed to the CLI. Does not affect production runs.
 - **Dependency**: T017/T026 can depend on T057 OR T057b in test mode.

**Checkpoint**: Foundation + Data + Reference ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Network Topology Extraction (Priority: P1) 🎯 MVP

**Goal**: Parse MD trajectories, construct bond networks via RDF minimum, and compute local graph metrics.

**Independent Test**: The system can process a single, small amorphous silicon trajectory file and output a CSV containing atomic IDs, coordination numbers, and local bond angle variance without requiring thermal conductivity data or VDOS calculation.

### Tests for User Story 1 (TDD: Write tests first)

- [X] T012 [P] [US1] Contract test for topology schema in `tests/contract/test_topology_schema.py` (Validates CSV columns: atom_id, coord_num, angle_var, is_valid)
 - **Depends on T009, T010** (Completion required before writing)
 - **Note**: Writing phase parallel; **Execution blocked by T017 completion**. TDD requires tests to be written before implementation, but they cannot run until code exists.
- [X] T013 [P] [US1] Unit test for RDF calculation in `tests/unit/test_rdf.py` (Verifies cutoff detection logic against known synthetic RDF)
 - **Depends on T009, T010** (Completion required before writing)
 - **Note**: Writing phase parallel; **Execution blocked by T017 completion**.
- [X] T014 [P] [US1] Unit test for bond network construction in `tests/unit/test_bond_network.py` (Verifies coordination counts match manual calculation for a small cluster)
 - **Depends on T009, T010** (Completion required before writing)
 - **Note**: Writing phase parallel; **Execution blocked by T017 completion**.
- [X] T015 [US1] Integration test for invalid file handling in `tests/integration/test_topology_errors.py` (Verifies "Invalid File Format" error on corrupted header)
 - **Depends on T009, T010** (Completion required before writing)
 - **Note**: Writing phase parallel; **Execution blocked by T017 completion**.
- [X] T016 [US1] Integration test for physical anomaly flagging in `tests/integration/test_topology_anomalies.py` (Verifies flagging of coordination > 6 without halting)
 - **Depends on T009, T010** (Completion required before writing)
 - **Note**: Writing phase parallel; **Execution blocked by T017 completion**.

### Implementation for User Story 1

- [X] T017 [US1] Implement `src/services/topology_extractor.py` (FR-001, FR-002)
 - Parse LAMMPS/XYZ using `ase`
 - **Dynamic Cutoff**: Determine bond cutoff dynamically by locating the first minimum of the RDF for the specific dataset (Constitution Principle VII). **MUST** implement this logic as a core step.
 - Construct bond network based on cutoff.
 - Compute local metrics (coordination number, bond angle variance).
 - **Anomaly Flagging**: Implement mandatory flagging of any atom with coordination > 6 as a "Physical Anomaly" without halting the process.
 - **Global Validation**: **MUST** calculate the average coordination number. If the absolute difference from the reference value (4.00) is > 0.05, **LOG** a "CRITICAL: Acceptance Test Failed" message and **set return code 3**. **DO NOT** halt the pipeline (to allow anomaly flagging), but the task status must reflect that the Spec's acceptance criterion was not met.
 - Output `data/derived/topology/` CSVs.
 - **TDD Note**: Can be developed using a local mock file. Real data execution depends on T056 success (or halt).
- [X] T018 [P] [US1] Add logging for topology extraction steps and RDF cutoff decisions (US-1 Edge Cases)
 - **Log Levels**: Use `INFO` for steps, `DEBUG` for RDF values.
 - **Format**: `%(asctime)s - %(levelname)s - %(module)s - %(message)s`
 - **Destination**: Both `stdout` and `data/metadata/topology_log.log`.
- [X] T019 [P] [US1] Create `tests/integration/test_full_topology.py` to verify end-to-end extraction on a small reference file
- [X] T020 [P] [US1] Implement CLI override mechanism for RDF cutoff (US-1 Edge Cases)
 - Add `--rdf-cutoff-override` argument to CLI.
 - **Default Behavior**: If override is not used, default to the first local minimum of the RDF.
 - Log the decision (override vs. detected minimum vs. ambiguous default) in the execution log.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Vibrational Mode Analysis and Bottleneck Identification (Priority: P2)

**Goal**: Calculate VDOS via VACF, compute participation ratio, and identify topological bottlenecks.

**Independent Test**: The system can take the output of User Story 1 (network topology) and a velocity dump, compute the VDOS, and output a scalar value representing the "density of localized modes" for that specific simulation box.

### Tests for User Story 2

- [X] T021 [P] [US2] Contract test for VDOS schema in `tests/contract/test_vdos_schema.py` (Validates columns: frequency, vdos, participation_ratio)
 - **Depends on T009, T010**
 - **Note**: Writing phase parallel; **Execution blocked by T026 completion**.
- [X] T022 [P] [US2] Unit test for VACF calculation in `tests/unit/test_vacf.py` (Verifies decay behavior on synthetic velocity data)
 - **Depends on T009, T010**
 - **Note**: Writing phase parallel; **Execution blocked by T026 completion**.
- [X] T023 [P] [US2] Unit test for participation ratio calculation in `tests/unit/test_participation_ratio.py`
 - **Depends on T009, T010**
 - **Note**: Writing phase parallel; **Execution blocked by T026 completion**.
- [X] T024 [P] [US2] Integration test for missing velocity data handling in `tests/integration/test_vdos_errors.py` (Verifies graceful failure of VDOS step, allowing topology to proceed)
 - **Depends on T009, T010**
 - **Note**: Writing phase parallel; **Execution blocked by T026 completion**.
- [X] T025 [P] [US2] Integration test for sensitivity analysis in `tests/integration/test_sensitivity.py` (Verifies bottleneck density stability with threshold sweep ±0.5)
 - **Depends on T009, T010**
 - **Note**: Writing phase parallel; **Execution blocked by T026 completion**.

### Implementation for User Story 2

- [X] T026 [US2] Implement `src/services/vdos_calculator.py` (FR-003, FR-004)
 - Compute Velocity Autocorrelation Function (VACF)
 - Calculate VDOS via Fourier Transform.
 - **Precision**: **MUST** cast all numerical arrays to `numpy.float64` explicitly to satisfy Constitution Principle VI.
 - Compute Participation Ratio.
 - Identify localized modes (high PR, low frequency).
 - Document numerical tolerance thresholds in code comments and `data/derived/vdos/tolerance_report.txt` (Constitution Principle VI).
 - Output `data/derived/vdos/` CSVs.
 - **Performance**: Implement vectorized FFT and parallel processing for VACF to meet SC-005 runtime thresholds.
- [X] T027 [P] [US2] Implement `src/services/sensitivity_analyzer.py` (US-2)
 - Sweep under-coordination threshold (±0.5)
 - Calculate bottleneck density (coordination < 3)
 - Report coefficient of variation
 - Output sensitivity report
- [X] T028 [P] [US2] Implement validation for acoustic modes and high-freq peak (US-2 Acceptance 1 & 3)
 - **Algorithm**: Find local maximum in the terahertz frequency range. Flag as "Spectral Anomaly" **only if** (peak height < 5% of global maximum) AND (system is NOT perfectly coordinated).
 - **Scenario 3 Logic**: If the system is perfectly coordinated (coordination ~4.0 for all atoms), log "Valid Physical State: Perfectly Coordinated" and **DO NOT** flag as anomaly, even if the high-freq peak is absent.
 - **Action**: If the high-frequency peak is absent in a non-perfectly-coordinated system, log a warning indicating "Spectral Anomaly: Missing high-freq peak" and flag the result as 'Spectral Anomaly'. **DO NOT halt** the pipeline.
 - **Note**: Only halt if velocity data is missing (graceful failure), not for specific spectral shapes.
- [X] T029 [P] [US2] Create `tests/integration/test_full_vdos.py` to verify end-to-end VDOS calculation on a reference box
- [X] T030 [P] [US2] Document numerical tolerance thresholds in code comments *and* `config.yaml` (Constitution Principle VI)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Robustness Validation (Priority: P3)

**Goal**: Aggregate metrics with independent thermal conductivity data, perform correlation analysis with Bootstrap, and validate robustness across three distinct system sizes.

**Independent Test**: The system can ingest three datasets with distinct system sizes and pre-computed topology, run the correlation analysis, and output a summary table showing the correlation coefficient, p-value, and 95% confidence interval for each dataset.

### Tests for User Story 3

- [X] T031 [P] [US3] Contract test for correlation schema in `tests/contract/test_correlation_schema.py` (Validates output: r, p_value, ci, power, corrected_p)
 - **Depends on T009, T010**
 - **Note**: Writing phase parallel; **Execution blocked by T041 completion**.
- [X] T032 [P] [US3] Unit test for Bootstrap resampling in `tests/unit/test_bootstrap.py` (Verifies multiple iterations and CI calculation accuracy vs manual calculation with |output - manual| < 1e-6)
 - **Depends on T009, T010**
 - **Note**: Writing phase parallel; **Execution blocked by T041 completion**.
- [X] T033 [P] [US3] Unit test for multiple-comparison correction in `tests/unit/test_corrections.py` (Bonferroni/FDR)
 - **Depends on T009, T010**
 - **Note**: Writing phase parallel; **Execution blocked by T041 completion**.
- [X] T034 [P] [US3] Integration test for independence check in `tests/integration/test_independence_check.py` (Verifies halting if κ source is not independent)
 - **Depends on T009, T010**
 - **Note**: Writing phase parallel; **Execution blocked by T039/T057 completion**.
- [X] T035 [P] [US3] Integration test for randomization control in `tests/integration/test_randomization_control.py` (Verifies r≈0, p>0.5 on randomized metrics)
 - **Depends on T009, T010**
 - **Note**: Writing phase parallel; **Execution blocked by T041 completion**.
- [X] T036 [P] [US3] Integration test for runtime threshold in `tests/integration/test_runtime_threshold.py` (Verifies ≤30 mins on 4000-atom system)
 - **Depends on T009, T010**
 - **Note**: Writing phase parallel; **Execution blocked by T045 completion**.
- [X] T037 [P] [US3] Integration test for Low Power warning in `tests/integration/test_low_power_warning.py` (Verifies warning triggers when power < 0.8)
 - **Depends on T009, T010**
 - **Note**: Writing phase parallel; **Execution blocked by T041 completion**.

### Implementation for User Story 3

- [X] T046 [US3] Implement loop to ingest data for **three distinct system sizes** (N=1000, 2000, 4000) and aggregate power metrics (FR-006, Plan Scale/Scope)
 - **Depends on T056, T057, T058, T017, T026**: Requires data fetched, κ values validated, and topology/VDOS data produced.
 - **Data Source**: Process **all available realizations** fetched by T056 for each of the 3 system sizes.
 - **Size Identification**: **MUST** parse system size from filename pattern `*_N{size}*.xyz` or metadata field `system_size`.
 - **Statistical Validity**: If available realizations < 30 per size, **LOG** a "Low Power Warning" and proceed (do NOT halt), as Spec FR-006 only requires 3 distinct sizes.
 - Aggregate power metrics for the full population across the three sizes.
 - **Note**: This task aggregates *already fetched* data; it does not fetch new data.
- [X] T041 [US3] Implement `src/services/statistical_analyzer.py` (FR-005, FR-006, FR-007)
 - **Depends on T046**: Aggregates data produced by T046.
 - Perform Spearman and Pearson correlation.
 - Execute **exactly 1000** bootstrap iterations for confidence interval estimation (FR-005, SC-001) using `scipy.stats.bootstrap`.
 - Apply multiple-comparison correction (Bonferroni/FDR) with unit of testing: **per metric per system-size comparison**.
 - **Power Analysis**: Calculate statistical power using `statsmodels.stats.power.FTestPower` (for ANOVA) or `scipy.stats.pearsonr` with `r_to_z` transformation for correlation power analysis, using the **observed effect size** (Cohen's d for mean differences, Pearson r for correlations) from the data (SC-002). **MUST NOT** use the fixed effect size from `config.yaml`. Document the observed effect size and the calculated power.
 - **Output**: Output `data/derived/correlation/` results and summary tables. **MUST** include `corrected_p_value` as a distinct field in the output artifact.
 - **Performance Note**: To meet SC-005 (≤30 mins), the implementation MUST use vectorized operations (numpy/scipy) and parallel processing for independent bootstrap iterations where feasible.
- [X] T042 [P] [US3] Implement finite-size effect validation (compare correlation consistency across sizes) (US-3 Acceptance 1)
 - **Explicitly output the variance value** of correlation coefficients across the three system sizes.
- [X] T043 [P] [US3] Add "Low Power" warning logic if power < 0.8 (SC-002)
 - **Note**: This is a warning log, not a halt, as the calculation is valid but underpowered.
- [X] T047 [P] [US3] Implement explicit reporting of statistical power value (SC-002)
 - **Effect Size Source**: Use the **observed effect size** calculated from the data for the power analysis. The fixed assumption (0.3) may be documented for context but must **NOT** be used for the calculation.
 - **Documentation**: Document the observed effect size calculation in `outputs/reports/assumptions.md`.
 - Ensure the calculated statistical power is reported in the final summary table and report.
 - Flag "Low Power" if < 0.8.
 - **Constraint**: Code must explicitly ignore `config.yaml` effect size for power calculation.
- [X] T047b [P] [US3] Test to verify power analysis ignores config.yaml effect size
 - **Logic**: Unit test that mocks `config.yaml` with a fixed effect size and verifies the power analysis function calculates power using the **observed** effect size from the data, not the config value.
 - **Fail Condition**: Test fails if the code reads the config value for power calculation.
- [X] T044 [P] [US3] Create `tests/integration/test_full_correlation.py` to verify end-to-end statistical pipeline

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Orchestration & Polish

**Purpose**: Global pipeline orchestration and final reporting

- [X] T045 [P] [Orchestration] Create `src/cli/main.py` to orchestrate the full pipeline (Topology → VDOS → Reference → Correlation)
 - **Depends on T017, T026, T057, T041, T046**: Must execute after all service implementations.
 - **Note**: This task consumes artifacts from multiple services and must be executed after them.
- [X] T048 [P] Create `config.yaml` with fixed effect size assumption (Documentation Only)
 - **Content**: `effect_size:` (for documentation/context only), `bootstrap_iterations: 1000`, `The random seed will be set to a fixed value to ensure reproducibility.`
 - **Documentation**: Add comment in file: "Effect size is a fixed assumption for documentation (see outputs/reports/assumptions.md). **Power analysis uses observed effect size.** The fixed value MUST be ignored by the power analysis logic."
 - **Note**: The fixed value is for documentation only and must be ignored by the power analysis logic to prevent confusion.
- [X] T049 [P] Implement `scripts/update_state_hashes.py` to compute SHA256 of all artifacts and update state YAML
- [X] T050 [P] Generate final report in `outputs/reports/` (PDF/HTML) including all correlation tables, figures, and sensitivity analysis
- [X] T051 [P] Create `outputs/figures/` (RDF plots, VDOS spectra, Correlation scatter plots with CI bands)
- [X] T052 [P] Update `README.md` with CLI usage examples
- [X] T053 [P] Generate API documentation for `src/services/`
- [X] T054 [P] Run `quickstart.md` validation (if applicable)
- [X] T055 [P] Verify all acceptance criteria from spec.md are met via automated test suite
- [X] T059 [P] [US3] Generate manual reference calculation for SC-001
 - **Dataset**: Use a small, known 10-atom cluster with hardcoded coordinates and known correlation r=0.854321.
 - **Logic**: Implement a deterministic script to calculate Spearman correlation on this specific dataset.
 - **Output**: Write the expected value to `data/metadata/manual_reference.json`.
 - **Note**: This file is required for T060 to verify SC-001.
- [X] T060 [P] [US3] Implement test for SC-001 accuracy verification
 - **Logic**: Compare the output of T041 (on the small dataset from T059) against the value in `data/metadata/manual_reference.json`.
 - **Threshold**: Fail test if `|output - manual| >= 1e-6`.
 - **Dependency**: **MUST** fail the test suite if `data/metadata/manual_reference.json` is missing or invalid.

---

## Phase 7: Revision & Robustness (Addressing Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data streaming, ambiguity handling, and verification robustness.

- [ ] T061 [P] [US1] Implement streaming support for large trajectory files in `src/services/topology_extractor.py`
 - **Review Concern**: Spec mentions "downsampling" for >100k atoms, but Plan requires real data.
 - **Action**: Modify `ase` loading logic to support `streaming=True` or chunked reading where feasible, or implement `itertools.islice` for a well-defined sample if full streaming is impossible.
 - **Constraint**: If sampling is used, the task MUST log the exact sample size, seed, and representativeness limitation in `data/metadata/sampling_log.txt`.
 - **Dependency**: Must not introduce synthetic data fallbacks.
 - **Trigger**: Only active if dataset size > 100k atoms or memory constraints are detected.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T009/T010 (Test Infra) MUST complete before T012-T037**
 - **T055a (Registry Generation) MUST succeed before T055**
 - **T055 (Registry Validation) MUST succeed before T056**
 - **T056 (Data Fetch) MUST succeed (or halt) before T017, T026, T039, T057, T058**
 - **T039 (Independence Check) / T057 (κ Ingest) MUST succeed before T046**
- **User Story 1 (Phase 3)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **T012/T013 (Tests) MUST precede T017 (Implementation)**
- **User Story 2 (Phase 4)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (Phase 5)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - **T057b (Mock Kappa) allows US1/US2 testing without T057**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (except T055a->T055->T056->T039/T057 chain)
 - **T055a, T055b, T004-T008 can run in parallel**
 - **T055 must complete before T056**
 - **T056 must complete before T039/T057**
- Once Foundational + Data Acquisition complete, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (writing)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

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
- **Independence**: Thermal conductivity values MUST be **provided by the researcher** (T057). The system validates independence but does not generate them internally. T058 was removed due to undefined API.
- **Statistical Power**: Process **all available realizations** for 3 system sizes. If N<30 per size, **LOG** "Low Power Warning" and proceed (no HALT). **Power analysis uses observed effect size.**
- **Plan vs Spec Discrepancy**: The Plan's "N≥30 realizations" is a statistical validity target. The current implementation follows Spec FR-006 (3 system sizes) AND Plan's N≥30 requirement, explicitly **logging a warning** if realizations < 30, but NOT halting.
- **Precision**: All VDOS and RDF calculations MUST use `numpy.float64` (T026) to satisfy Constitution Principle VI.
- **Performance Note (SC-005)**: The implementation of T041 (1000 bootstrap iterations on N≥30 samples) MUST include performance optimizations (e.g., vectorization, parallel processing) to ensure the full pipeline completes within the 30-minute runtime threshold on a 4-core CPU.
- **Manual Reference (SC-001)**: T059 generates a deterministic reference; T060 enforces the check.
- **Configuration Safety**: T048 config.yaml effect size is for documentation only; T047b ensures code ignores it.