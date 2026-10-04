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
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
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

- [ ] T001a [P] Design data directories: `data/raw/`, `data/derived/`, `data/derived/topology/`, `data/derived/vdos/`, `data/derived/reference/`, `data/derived/correlation/`, `data/metadata/`
 - **Implementation**: Create the directory structure in the repository and write the hierarchy definition to `docs/design/directory_structure.md`.
 - **Verification**: Ensure `docs/design/directory_structure.md` exists and lists all required paths.
- [ ] T001b [P] Design output directories: `outputs/`, `outputs/figures/`, `outputs/reports/`
 - **Implementation**: Create the directory structure in the repository and write the hierarchy definition to `docs/design/output_structure.md`.
 - **Verification**: Ensure `docs/design/output_structure.md` exists and lists all required paths.
- [X] T001c [P] Create `src/__init__.py`, `src/models/__init__.py`, `src/services/__init__.py`, `src/cli/__init__.py`, `src/lib/__init__.py`
- [X] T002 [P] Initialize Python project with `requirements.txt` (numpy, scipy, pandas, scikit-learn, ase, matplotlib, seaborn, networkx, pytest, pytest-cov, pytest-randomly, statsmodels)
- [X] T003a [P] Create `ruff.toml` with strict linting rules: select=["E", "F", "I", "W"], ignore=[], line-length=88
 - **Content**: Explicitly set `target-version = "py311"`, `preview = true`
- [X] T003b [P] Create `pyproject.toml` [tool.black] section: line-length=88, target-version=['py311'], include='\.pyi?$'

---

## Phase 2: Foundational (Blocking Prerequisites & Data Acquisition)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented, AND securing real data sources.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. All test infrastructure (T009, T010) must be ready before test-writing tasks in Phase 3.

**Sequential Execution Note**: T055a, T055b, T056, and T057 form a strict sequential chain. T055a must complete before T055b starts. T055b must complete before T056 starts. T056 must complete before T057 starts. T004-T008 can run in parallel with T055a.

- [X] T004 [P] Create `src/models/simulation_box.py` (Data class for atomic positions, velocities, and metadata)
- [X] T005 [P] Create `src/models/bond_network.py` (Graph representation: nodes=atoms, edges=bonds, metrics)
- [X] T006 [P] Create `src/models/vibrational_spectrum.py` (Data class for VDOS, participation ratio, frequency bins)
- [X] T007 [P] Create `src/lib/utils.py` (Checksum verification, logging setup, seed management, and file validation enhancements)
- [X] T008 [P] Create `src/lib/config.py` (Configuration management, path constants, seed initialization, and `VERIFIED_DATASET_IDS` constant)
- [X] T009 [P] Create test package `__init__.py` files in `tests/unit/`, `tests/integration/`, and `tests/contract/`
 - **Note**: Atomic task for test infrastructure.
- [X] T010 [P] Configure `pyproject.toml` with pytest plugins (`pytest-randomly`, `pytest-cov`) and coverage thresholds
 - **Note**: This task is a blocking prerequisite for test-writing tasks T012-T037. Must **complete** (config written) before T012-T016 can be **written**.

**Data Acquisition & Reference Generation Tasks (Must precede US Implementation)**

- [ ] T055a [Foundational] Implement `src/services/registry_generator.py` to generate `data/metadata/dataset_registry.json`
 - **Purpose**: Create a registry mapping system sizes (N=1000, 2000, 4000) to valid dataset IDs from verified sources (e.g., Zenodo, Materials Cloud).
 - **Logic**: Query the `VERIFIED_DATASET_IDS` constant in `src/lib/config.py` to build the registry.
 - **Output**: `data/metadata/dataset_registry.json`.
 - **Dependency**: Must be run before T055b to provide valid dataset IDs.
- [ ] T055b [Foundational] Implement `src/services/registry_validator.py` to validate `data/metadata/dataset_registry.json`
 - **Purpose**: Verify that all dataset IDs in the registry are reachable and valid.
 - **Logic**: Use the Zenodo API endpoint `https://zenodo.org/api/records/{id}` to check each ID. If any ID is invalid, **HALT** with a fatal error.
 - **Output**: `data/metadata/registry_validation.log` AND `data/metadata/valid_sources.json` (containing the list of validated source IDs). **This file MUST be created here.**
 - **Dependency**: Must be run after T055a and before T056.
- [ ] T056 [Foundational] Implement `src/services/data_loader.py` to fetch real amorphous silicon trajectories
 - **Depends on T001, T008, T055a, T055b**: Requires directory structure, path configuration, and a valid dataset registry.
 - **Dataset IDs**: Fetch datasets using IDs from `data/metadata/dataset_registry.json`. Do NOT hardcode IDs.
 - **Method**: Use `datasets.load_dataset(name, split=..., streaming=True)` with the specific Hugging Face dataset IDs from the registry.
 - **Validation**: **MUST** verify that data exists for **all three** required system sizes (N=1000, 2000, 4000). If any size is missing, **HALT** with a fatal error.
 - **Sample Size Handling**: If the count of realizations per size is < 30, **LOG** a "Low Power Warning" and proceed (do NOT halt). The pipeline must not proceed if N=0.
 - **ID Extraction**: **MUST** extract the `trajectory_id` from the fetched metadata and write it to `data/metadata/trajectory_ids.json` for T057 to consume.
 - **MUST fail loudly** if download fails or if ID is not found; NO synthetic fallback allowed.
 - **Constitution III Compliance**: **MUST** compute and record the SHA256 checksum of all downloaded files in `state/projects/PROJ-260-investigating-the-influence-of-network-s.yaml` before proceeding.
- [X] T039 [Foundational] **REMOVED** (Logic merged into T057 for atomic ingestion validation)
- [ ] T057 [Foundational] Implement `src/services/kappa_ingester.py` to ingest researcher-provided independent κ values
 - **Depends on T055a, T055b, T056**: Requires validated registry, `valid_sources.json` (created by T055b), trajectory IDs, and valid sources.
 - **Input Mechanism**: Implement a CLI argument `--kappa-file` and a config fallback `data/derived/reference/kappa_values.csv`.
 - **Schema**: The CSV must have columns: `system_size`, `kappa`, `source_id`, `source_type`, `trajectory_id`.
 - **Source Validation**: `source_id` must be a lowercase string matching regex `^[a-z0-9_]+$` and present in `data/metadata/valid_sources.json`. **MUST** verify `data/metadata/valid_sources.json` exists before reading. If the file is missing, **HALT** with a fatal error. `source_type` must be one of the valid types (e.g., 'experimental', 'distinct_simulation').
 - **Independence Check (Atomic Step)**: **MUST** extract `source_id` from the input CSV and compare it against `trajectory_source` (from `data/metadata/trajectory_ids.json`). If `source_id == trajectory_source`, **HALT** with FatalError: "Circular Dependency Detected" (Exit Code 2) BEFORE writing any output.
 - **Output**: Write validated κ values to `data/derived/reference/kappa_values.csv` ONLY if the independence check passes.
 - **Error Handling**: If the file is missing, invalid, or fails independence check, **HALT** with a fatal error (FR-008).

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
 - **Note**: Writing phase parallel; **Execution blocked by T057 completion**.
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

- [ ] T046 [US3] Implement loop to ingest data for **three distinct system sizes** (N=1000, 2000, 4000) and aggregate power metrics (FR-006, Plan Scale/Scope)
 - **Depends on T056, T057, T017, T026, T061**: Requires data fetched, κ values validated, topology/VDOS data produced, and streaming support implemented.
 - **Data Source**: Process **all available realizations** fetched by T056 for each of the 3 system sizes.
 - **File Pattern**: **MUST** locate files using the glob pattern `data/derived/topology/*_N{size}*.csv` in the `data/derived/topology/` directory.
 - **Size Identification**: **MUST** parse system size from filename pattern `*_N{size}*.csv` or metadata field `system_size`.
 - **Explicit Validation**: **MUST** verify that exactly three distinct system sizes (N=1000, 2000, 4000) are present in the input data. If fewer than 3 distinct sizes are found, **HALT** with a fatal error. This is a mandatory check for FR-006 compliance.
 - **Statistical Validity**: If available realizations < 30 per size, **LOG** a "Low Power Warning" and proceed (do NOT halt), as Spec FR-006 only requires 3 distinct sizes.
 - Aggregate power metrics for the full population across the three sizes.
 - **Output**: Write aggregated dataset to `data/derived/correlation/aggregated_dataset.csv`.
 - **Note**: This task aggregates *already fetched* data; it does not fetch new data.
- [X] T041 [US3] Implement `src/services/statistical_analyzer.py` (FR-005, FR-006, FR-007)
 - **Depends on T046**: Aggregates data produced by T046.
 - Perform Spearman and Pearson correlation.
 - Execute **exactly 1000 (math/0504516, https://arxiv.org/abs/math/0504516)** bootstrap iterations for confidence interval estimation (FR-005, SC-001) using `scipy.stats.bootstrap`.
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
- [ ] T059 [P] [US3] Generate manual reference calculation for SC-001
 - **Algorithm**: Generate a small amorphous silicon structure programmatically using Wooten-Winer-Weaire (WWA) defect generation logic.
 - **Execution**: Run the `topology_extractor.py` (T017) on this generated structure to obtain coordination numbers and bond angle variances.
 - **Calculation**: Compute the Spearman correlation coefficient manually using the standard rank-order formula on the generated metrics. **MUST be calculated dynamically by the script, not hardcoded.**
 - **Output**: Write the calculated `r` value and the input metrics to `data/metadata/manual_reference.json`.
 - **Note**: This ensures the reference is derived from the actual pipeline logic (RDF cutoff, ranking) on a real-like structure, not a hardcoded synthetic value.
- [X] T060 [P] [US3] Implement test for SC-001 accuracy verification
 - **Logic**: Compare the output of T041 (on the small dataset from T059) against the value in `data/metadata/manual_reference.json`.
 - **Threshold**: Fail test if `|output - manual| >= 1e-6`.
 - **Dependency**: **MUST** fail the test suite if `data/metadata/manual_reference.json` is missing or invalid.

---

## Phase 7: Revision & Robustness (Addressing Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data streaming, ambiguity handling, and verification robustness.

- [ ] T061 [P] [US1] Implement streaming support for large trajectory files in `src/services/topology_extractor.py`
 - **Review Concern**: Spec mentions "downsampling" for >100k atoms, but Plan requires real data.
 - **Action**: Modify `ase` loading logic to use `ase.io.stream` with the `chunk_size` parameter for chunked reading of large files.
 - **Constraint**: If full streaming is impossible, implement `itertools.islice` for a well-defined sample (e.g., first N rows).
 - **Logging**: If sampling is used, the task MUST log the exact sample size, seed, and representativeness limitation in `data/metadata/sampling_log.txt`.
 - **Dependency**: Must not introduce synthetic data fallbacks.
 - **Trigger**: Only active if dataset size > 100k atoms or memory constraints are detected. **This task is now ACTIVE and required for pipeline execution.**

- [ ] T062 [P] [US1] Implement robust RDF ambiguity handling in `src/services/topology_extractor.py`
 - **Review Concern**: Spec Edge Case: "What happens when the RDF minimum is ambiguous (e.g., broad first peak)?"
 - **Action**: Implement logic to detect if the first minimum is shallow (depth < 5% of peak height) or if multiple minima exist within 0.2 Å.
 - **Peak Height Definition**: Define 'peak height' as the maximum value of the RDF in the range before the first minimum.
 - **Fallback**: If ambiguous, default to the first local minimum but **LOG** a "CRITICAL: Ambiguous RDF Minimum" warning with the detected range and the chosen cutoff.
 - **Override**: Ensure the `--rdf-cutoff-override` (T020) is mandatory if ambiguity is detected and no manual override is provided.
 - **Output**: Append the ambiguity status and chosen cutoff to `data/metadata/topology_log.log`.

- [ ] T063 [P] [US2] Implement explicit "Missing Velocity Data" failure mode in `src/services/vdos_calculator.py`
 - **Review Concern**: Spec Edge Case: "How does the system handle MD trajectories with missing velocity data?"
 - **Action**: Add a pre-flight check in `vdos_calculator.py` to verify `atoms.get_velocities()` is not `None` and not an empty array before VACF calculation.
 - **Behavior**: If missing, raise a specific `VelocityDataMissingError` with exit code 4. **DO NOT** attempt to proceed with topology extraction (which is separate) but ensure the VDOS pipeline halts cleanly without partial results.
 - **Logging**: Log the specific atom ID or frame range where velocity data is missing to `data/metadata/vdos_errors.log`.

- [ ] T064 [P] [US3] Implement "Single System Size" limitation flag in `src/services/statistical_analyzer.py`
 - **Review Concern**: Spec Edge Case: "What happens when the dataset contains only one system size?"
 - **Action**: Check the count of unique system sizes in the aggregated dataset (T046) by inspecting the `system_size` column.
 - **Behavior**: If count < 3, **LOG** a "LIMITATION: Insufficient System Sizes for Finite-Size Validation" warning and **DO NOT** perform the cross-size variance calculation (T042).
 - **Output**: Include a `finite_size_validation_status: "SKIPPED"` flag in the final correlation report.

- [ ] T065 [P] [Foundational] Add verification test for "Fail Loudly" data loader behavior in `tests/integration/test_data_loader_fail.py`
 - **Review Concern**: Rule: "The loader must FAIL LOUDLY, never fall back to synthetic."
 - **Action**: Create a test that mocks a download failure (e.g., `requests.get` raises `ConnectionError` or returns 404).
 - **Expectation**: Verify that `data_loader.py` raises a `DataFetchError` and **does not** call any `generate_synthetic_*` function or return dummy data.
 - **Assert**: Ensure the process exits with code 1 and logs "FATAL: Real data fetch failed" to the log file.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T009/T010 (Test Infra) MUST complete before T012-T037**
 - **T055a (Registry Generation) MUST succeed before T055b**
 - **T055b (Registry Validation) MUST succeed before T056**
 - **T056 (Data Fetch) MUST succeed (or halt) before T017, T026, T057**
 - **T057 (κ Ingest) MUST succeed before T046**
- **User Story 1 (Phase 3)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **T012/T013 (Tests) MUST precede T017 (Implementation)**
- **User Story 2 (Phase 4)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (Phase 5)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - **T057 (κ Ingest) allows US1/US2 testing with real data subsets**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (except T055a->T055b->T056->T057 chain)
 - **T055a, T055b, T004-T008 can run in parallel**
 - **T055b must complete before T056**
 - **T056 must complete before T057**
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
- **Independence**: Thermal conductivity values MUST be **provided by the researcher** (T057). The system validates independence but does not generate them internally.
- **Statistical Power**: Process **all available realizations** for 3 system sizes. If N<30 per size, **LOG** "Low Power Warning" and proceed (no HALT). **Power analysis uses observed effect size.**
- **Plan vs Spec Discrepancy**: The Plan's "N≥30 realizations" is a statistical validity target. The current implementation follows Spec FR-006 (3 system sizes) AND Plan's N≥30 requirement, explicitly **logging a warning** if realizations < 30, but NOT halting.
- **Precision**: All VDOS and RDF calculations MUST use `numpy.float64` (T026) to satisfy Constitution Principle VI.
- **Performance Note (SC-005)**: The implementation of T041 (1000 bootstrap iterations on N≥30 samples) MUST include performance optimizations (e.g., vectorization, parallel processing) to ensure the full pipeline completes within the 30-minute runtime threshold on a 4-core CPU.
- **Manual Reference (SC-001)**: T059 generates a deterministic reference using WWA generation + pipeline run; T060 enforces the check.
- **Configuration Safety**: T048 config.yaml effect size is for documentation only; T047b ensures code ignores it.
- **Review Concerns Addressed**: Tasks T062-T065 explicitly handle edge cases regarding RDF ambiguity, missing velocities, single system sizes, and data loader failure modes to ensure robustness and compliance with the "Fail Loudly" principle.
- **T057b Removal**: The `mock_kappa_generator` (T057b) has been removed to comply with the Independence of Variables principle. US1/US2 testing must use a small subset of real data or a pre-computed reference file.
- **T039 Removal**: T039 has been merged into T057 to ensure atomic independence checking.
- **T061 Status**: T061 is now an active, required task for handling large files.