# Tasks: Solvent Effects on Photo-Fries Rearrangement Kinetics

**Input**: Design documents from `/specs/001-solvent-effects/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
- Paths shown below assume single project structure as defined in `plan.md`

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

- [X] T001 Create project structure per `plan.md` (directories: `code/`, `data/`, `tests/`, `docs/`)
- [X] T002 Initialize a Python project with pinned dependencies in `requirements.txt` (numpy, scipy, pandas, scikit-learn, pyyaml, pymatgen, matplotlib, seaborn, pymc, statsmodels)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`
- [X] T004 [P] Initialize `code/utils/seeds.py` to set global random seeds for reproducibility
- [X] T005 [P] Setup `code/utils/logging.py` to handle structured logging of environmental parameters

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. This phase includes configuration, schema definition, and the safety control loop.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006a [P] **Solvent Schema Definition**: Define `contracts/solvent.schema.yaml` to specify the required fields, data types, and constraints for solvent data (name, dielectric_constant, source_id, citation_url).
- [X] T006b [P] **Solvent Data Population**: Populate `data/chemicals/solvents.yaml` with at least 5 distinct solvents (cyclohexane, methanol, acetonitrile, toluene, water) including real NIST values for dielectric constant. Source: NIST Standard Reference Database.
- [X] T006c [P] **Solvent Schema Validation**: Validate `data/chemicals/solvents.yaml` against `contracts/solvent.schema.yaml` to ensure all required fields and data types are correct.
- [X] T006d [P] **Version Hash Generation & State Update**: Execute SHA-256 hashing on `data/chemicals/solvents.yaml` and record the result in `state/artifact_hashes.yaml` under the key `solvents_yaml_hash`. **Constraint**: This task MUST create the `state/artifact_hashes.yaml` file if it does not exist, ensuring the key `solvents_yaml_hash` is populated with a valid hash. This ensures the hash is always current per Constitution Principle V and guarantees T017a can execute successfully.
- [X] T007 [P] Define `contracts/kinetic_trace.schema.yaml` for data validation of transient-absorption traces.
- [X] T008 [P] Implement `code/data/loaders.py` to fetch real solvent properties from `data/chemicals/solvents.yaml` (no synthetic generation of input properties).
- [X] T009a [P] **Config Paths & CPU Constraints**: Implement `code/config.py` to enforce CPU-only execution constraints and define file paths for `data/raw/`, `data/compute/`, `data/processed/`.
- [X] T009b [P] **Explicit Solvent Configuration**: Extend `code/config.py` to define the `EXPLICIT_SOLVENTS` list (e.g., `['water', 'methanol']`) required by T029b for FR-005 compliance. **Constraint**: This list MUST be populated with at least one solvent if N >= 5 to satisfy the [deferred] explicit model requirement.
- [X] T010 [P] Create `tests/unit/test_loaders.py` to verify solvent property loading against versioned lookup table.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

- [X] T015b [US1] **Real Data Ingestion (Blocking)**: Implement `code/data/ingest.py` to ingest real transient-absorption data from a user-provided file path defined in `code/config.py` (key `REAL_DATA_PATH`). **Constraint**: The file path MUST be read from `code/config.py`. If `USE_REAL_DATA=true` and the file at the configured path is missing, the script MUST print `CRITICAL: Real data file missing at {path}. Aborting.` and exit with code `sys.exit(1)`. **Implementation Step**: The task MUST include a step to create/update `code/config.py` with a default path or handle CLI arguments to override it if the key is missing. No synthetic fallback is permitted in this mode. **Dependency**: This task is the primary data source for the research phase.
- [X] T015c [P] [US1] **CI-Placeholder Data Generation**: Implement `code/data/generate_synthetic.py` to generate deterministic synthetic transient-absorption traces (mocking laser flash photolysis) as the **primary CI Data Source** when `USE_REAL_DATA=false` or hardware is unavailable. **Constraint**: This task MUST produce `data/raw/synthetic_traces.csv` to ensure FR-002 is satisfied in CI. It runs only if T015b is bypassed. **Invocation**: `python code/data/generate_synthetic.py --seed 42 --output data/raw/synthetic_traces.csv`. **Note**: This is a staged CI-only fallback authorized by the spec's Assumptions section.
- [X] T015e [US1] **Instrument Capture Interface**: Implement `code/data/instrument_interface.py` to define the `capture_transient_data()` function required by FR-002. **Constraint**: This function MUST attempt to connect to hardware; if hardware is absent, it MUST raise `NotImplementedError` with a clear message. This task is the primary mechanism for the spec's 'capture' requirement. **Dependency**: T015b and T015c are ingestion paths that feed into the pipeline, but T015e defines the interface.
- [X] T015d [P] **Hardware Integration Gap Documentation**: Create `docs/hardware_integration_status.md` to explicitly document that the 'capture' capability is deferred to future hardware integration, and the current implementation relies on file ingestion or synthetic generation. **Constraint**: This document MUST clarify that T015e exists as an interface but raises `NotImplementedError` in the absence of hardware.

- [X] T059a [P] **Define Study Design**: Implement `code/analysis/power.py` to define the static study design parameters (n ≥ 3 replicates per solvent, number of solvents) and document the methodology for power analysis. **Constraint**: Output must be a partial artifact `data/processed/study_design.yaml` containing `methodology`, `sample_size_n`, and a `deferred_effect_size` placeholder with a clear `update_trigger` description (e.g., 'Update when pilot study effect size is determined'). **Input**: Read default effect size from `code/config.py` (key `EFFECT_SIZE_COHEN_D`, default 0.8) if available, otherwise use 0.8 to denote a standard medium effect size for planning purposes. **Dependency**: **MUST run BEFORE T021 and T026** to define the required sample size (n≥3) before data generation or fitting begins.
- [X] T059b [P] **Run Power Analysis**: Implement `code/analysis/power.py` to execute the power analysis using the design from T059a and generate `data/processed/study_power_analysis.json`. **Constraint**: The JSON MUST include keys: `methodology`, `sample_size_n`, `effect_size_status` (e.g., 'pending', 'estimated'), `effect_size_value` (null if pending), and `update_trigger`. **Dependency**: Depends on T059a.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Configure and Execute Solvent Series (Priority: P1) 🎯 MVP

**Goal**: Define a series of solvents spanning non-polar to polar conditions and initiate the experimental protocol with full environmental logging.

**Independent Test**: Verify that the system logs dielectric constant (validated against `solvents.yaml`), temperature (25 ± 0.5°C), and relative humidity (±2% RH) for each run.

### Tests for User Story 1 (OPTIONAL)

- [X] T011 [P] [US1] Unit test for `code/data/loaders.py` validating dielectric constant lookup in `tests/unit/test_solvent_validation.py`
- [X] T012 [US1] Integration test for environmental logging in `tests/integration/test_env_logging.py` (depends on T014 completion)

### Implementation for User Story 1

- [X] T014 [US1] Implement `code/analysis/environment.py` to log temperature, humidity, **barometric pressure**, **substrate_mass**, and **integration_time_ms** for each run. **Constraint**: Must output to `data/processed/environment_logs.json` with all fields required by FR-007 (addressing SC-004, FR-007). **Explicitly mandate**: The script MUST capture `barometric_pressure` (hPa) and `substrate_mass` (g) from `code/config.py` (keys `DEFAULT_BAROMETRIC_PRESSURE` and `DEFAULT_SUBSTRATE_MASS`). If hardware sensors are absent, use the default values from config (e.g., 1013.25 hPa, 0.0 g). If missing in config, raise a `ConfigurationError`. **Dependency**: Depends on T009 (Config) and T008 (Solvent Loader). Does NOT depend on T015b/c.
- [X] T013 [US1] Implement `code/main.py` CLI entry point to configure solvent series (multiple solvents, ε range low to moderate). **Constraint**: The CLI MUST explicitly validate that at least 5 distinct solvent conditions are provided and that the dielectric constants span a broad range from low values to high magnitudes. If constraints are not met, the CLI MUST exit with an error before proceeding. **Dependency**: Depends on T014's *module implementation* (the code exists to be called), NOT on the existence of the output file. T013 invokes T014's functions to generate the log file.
- [X] T017a [US1] **Environmental Validation**: Implement `code/analysis/validation.py` to: 1) flag runs where logged dielectric constants deviate >2% from `solvents.yaml` (addressing SC-010), 2) detect and flag runs where temperature or humidity exceeds tolerance (addressing Edge Cases in spec). Output list of flagged runs to `data/processed/validation_flags.json`. **Constraint**: This task MUST first verify `data/chemicals/solvents.yaml` exists and contains a valid `version_hash` by **reading `state/artifact_hashes.yaml`**. **Robustness**: If `state/artifact_hashes.yaml` is missing, the task MUST check if `data/chemicals/solvents.yaml` exists; if so, it MUST run the hash generation logic (as per T006d) to create the state file, OR raise a clear `ConfigurationError` instructing the user to run T006d. It MUST NOT crash with a generic traceback. **Dependency**: Depends on T006d.
- [X] T017b [US1] **Compliance Reporting**: Implement `code/analysis/validation.py` to calculate the environmental compliance percentage (≥95% of runs within tolerance) by reading `data/processed/environment_logs.json` and `data/processed/validation_flags.json`, then write the result to `data/processed/compliance_report.json`. **Constraint**: The denominator for compliance percentage is 'total configured solvent runs' (sum of all `n` replicates defined in configuration). **Logic**: Count 'valid' flags from `validation_flags.json`, divide by total configured runs, assert ≥98% threshold for SC-010.
- [X] T017c [US1] **Robust Hash Initialization**: Implement `code/analysis/hash_manager.py` to ensure `state/artifact_hashes.yaml` exists and contains a valid `solvents_yaml_hash`. **Constraint**: This task MUST read `data/chemicals/solvents.yaml`, compute its SHA-256 hash, and write it to `state/artifact_hashes.yaml`. If `solvents.yaml` is missing, it MUST raise a `FileNotFoundError`. **Dependency**: This task MUST run before T017a to guarantee a valid hash exists.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Extract Radical-Pair Lifetime (Priority: P2)

**Goal**: Process raw spectroscopic data to extract singlet-radical-pair intermediate lifetime via global kinetic analysis.

**Independent Test**: Verify system outputs lifetime value with confidence interval and calibration record from uploaded decay traces.

### Tests for User Story 2 (OPTIONAL)

- [X] T019 [P] [US2] Unit test for exponential fitting in `tests/unit/test_kinetic_fit.py`
- [X] T020 [P] [US2] Integration test for replicate statistics in `tests/integration/test_replicate_analysis.py`

### Implementation for User Story 2

- [X] T016 [US2] Implement `code/analysis/calibration.py` to apply instrument calibration factors and log detector response/wavelength stability per `FR-004`
- [X] T021 [US2] **Joint Non-Linear Mixed-Effects (NLME) Modeling**: Implement `code/analysis/kinetic_fit.py` to define and fit a **Joint Non-Linear Mixed-Effects (NLME)** model for global kinetic analysis. **Constraint**: Use `pymc` or `statsmodels` to define fixed effects (decay rates) and random effects (inter-replicate and inter-solvent variance). Do NOT use standard `scipy.optimize.curve_fit` for the primary analysis. The model must propagate uncertainty from the kinetic fit into the final lifetime estimate. Output must include the posterior distribution of the lifetime parameter.
- [X] T022 [US2] Implement `code/analysis/kinetic_fit.py` to calculate mean lifetime and standard deviation for n ≥ 3 replicates per solvent
- [X] T023 [US2] Implement `code/analysis/kinetic_fit.py` to flag outliers beyond a statistically significant threshold. (addressing US-2 acceptance scenario)
- [X] T025 [US2] Implement `code/analysis/kinetic_fit.py` to perform threshold sensitivity analysis on lifetime discrepancy cutoffs across a range of values and report false-positive/negative rates (addressing SC-008). **Constraint**: **Define a list of significance thresholds in `code/analysis/kinetic_fit.py`.** (correcting the spec's malformed syntax `{, 0.05, 0.1}` to the valid set `{0.05, 0.1}`). **Output**: Generate `data/processed/sensitivity_analysis.csv` with columns `threshold`, `false_positive_rate`, `false_negative_rate`. **Note**: SC-008 syntax error is acknowledged; T025 uses valid values from config or defaults.
- [X] T026 [US2] Create `data/processed/kinetic_metrics.csv` containing extracted lifetimes, CIs, and replicate statistics

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlate Solvation Energy with Kinetic Lifetimes (Priority: P3)

**Goal**: Correlate computed solvation free energies with experimentally determined lifetimes using associational inference.

**Independent Test**: Verify system generates regression plot, statistical significance test, and multiple-comparison correction.

### Tests for User Story 3 (OPTIONAL)

- [X] T027 [P] [US3] Unit test for VIF calculation in `tests/unit/test_collinearity.py`
- [X] T028 [P] [US3] Integration test for correlation pipeline in `tests/integration/test_correlation.py`

### Implementation for User Story 3

- [X] T029a [US3] **DFT Data Fetching**: Implement `code/data/compute/solvent_models.py` to fetch or compute DFT solvation data for a list of N solvents. **Constraint**: This task must complete before T029b. **Input**: Load pre-computed DFT data from `data/compute/dft_results.csv` or run Gaussian script if file missing. **Output**: The output CSV MUST include a `model_type` column (values: 'implicit', 'explicit') to distinguish model types.
- [X] T029b [US3] **Solvent Model Partitioning & Validation**: Implement `code/data/compute/solvent_models.py` to: 1) partition the list of N solvents into ≤80% implicit (SMD/PCM) and ≥20% explicit (QM/MM or cluster-continuum) models based on `EXPLICIT_SOLVENTS` list in `code/config.py` and the `model_type` column, and 2) validate the split. **Constraint**: This task MUST validate that the total number of solvents (N) is sufficient to satisfy the 80/20 split constraint (e.g., if N=5, at least 1 must be explicit) BEFORE executing any partitioning logic. If N is too small to satisfy the constraint mathematically, it MUST raise a `ConfigurationError` citing FR-005 and suggesting an increase in N. **Dependency**: This task must complete after T029a and T029d.
- [X] T029c [US3] **Write Solvent Models**: Implement `code/data/compute/solvent_models.py` to write the combined results to `data/compute/solvent_solvation.csv`. **Constraint**: This task must complete after T029b.
- [X] T029d [US3] **Explicit Solvent Computation**: Implement `code/data/compute/solvent_models.py` to generate or fetch explicit solvent model data (QM/MM or cluster-continuum) for the solvents designated in `EXPLICIT_SOLVENTS`. **Constraint**: This task MUST produce data compatible with the `model_type='explicit'` requirement in T029b. If pre-computed data is unavailable, it MUST implement a simplified QM/MM cluster model (e.g., using `rdkit` and `openmm` for a small cluster) or fetch from a verified repository. **Dependency**: This task must complete before T029b.
- [X] T030a [US3] **Bayesian Correlation**: Implement `code/analysis/correlation.py` to perform **Bayesian Hierarchical Modeling (BHM)** to correlate lifetime with Solvation Energy and Dielectric Constant. **Constraint**: Do NOT use standard ANOVA or Linear Regression as the *only* model. Use a PCA-derived "Solvent Polarity Index" as the primary predictor to avoid tautology. Output posterior distributions for slope and intercept. **Dependency**: This task must complete before T030b and T031.
- [X] T030b [US3] **Statistical Reporting**: Implement `code/analysis/correlation.py` to perform **Bayesian Hierarchical Modeling (BHM)** as the **PRIMARY** method to satisfy **FR-006** and **SC-003**. **Constraint**: Standard ANOVA is **NOT FORBIDDEN** but is a **secondary diagnostic** to satisfy FR-006. Explicitly frame all findings as associational and exploratory due to low N (n=3). **Output**: Must write `data/processed/correlation_results.json` with keys: `bayesian_slope`, `bayesian_r2`, `credible_intervals`, `p_value_equivalent` (posterior prob). **(Note: Bayesian methods are now the primary method for SC-003 compliance, with ANOVA as a secondary diagnostic, resolving the conflict with the Plan).** (Addressing SC-001, SC-003, SC-006). **Dependency**: This task must complete after T030a.
- [X] T031 [US3] Implement `code/analysis/correlation.py` to perform VIF analysis to distinguish dielectric vs. solvation effects (addressing SC-009 and Rosalind Franklin review). **Constraint**: **Do NOT calculate VIF on raw variables** (dielectric constant and solvation energy) as this violates the Plan's tautology constraint. Calculate VIF **only on the PCA-derived Solvent Polarity Index** or its orthogonal components for diagnostic purposes. Explicitly state in the output that raw VIF is forbidden for hypothesis testing. **Output**: Write `data/processed/vif_scores.json`. **Dependency**: Depends on T030a (PCA Index).
- [X] T032 [US3] Implement `code/analysis/correlation.py` to apply multiple-comparison correction (e.g., Bonferroni) and report family-wise error rate
- [X] T033 [US3] Implement `code/analysis/correlation.py` to frame all findings as associational (not causal) in output metadata. **Constraint**: The script MUST inject the string `"associational"` into the `framing` metadata field of the JSON output and the figure caption text automatically. This ensures verifiable compliance with SC-006.
- [X] T034 [US3] Generate `paper/figures/regression_plot.png` and **copy** `data/processed/correlation_results.json` from Tb (do not regenerate) with **Bayesian R²**, **95% Credible Intervals**, **p-values**, and VIF scores; ensure all findings are explicitly framed as associational (addressing SC-006). **Constraint**: **Automated Framing**: The script MUST inject the string `"associational"` into the `framing` metadata field of the JSON output and the figure caption text. **Source**: VIF scores MUST be read from `data/processed/vif_scores.json`. **Dependency**: This task depends on completion of T030b AND T031 (to ensure VIF scores are available). **Dependency**: T031 must complete before T034.
- [X] T048 [US3] **Trend Verification**: Implement `code/analysis/validation.py` to verify that consistent trends are observed across ≥5 solvent conditions as a pass/fail criterion for SC-002. **Constraint**: This task MUST read `data/processed/correlation_results.json` and `data/processed/kinetic_metrics.csv`, aggregate lifetimes by solvent, compute the trend direction (increasing/decreasing), and verify that the trend is consistent (monotonic or non-monotonic but significant) across all 5+ conditions. Output to `data/processed/trend_verification_report.json` with a `pass/fail` status and a summary of the observed trend. **Dependency**: Depends on T034 completion. **(Note: T048 is now implemented and fully functional).** **Constraint**: This task is a **blocking gate** for US3 completion.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns (Review-Driven)

**Purpose**: Address specific reviewer concerns regarding instrumentation, calibration, and reproducibility.

- [X] T035 [P] Implement `code/analysis/instrument_registry.py` to define and log instrument configuration. **Constraint**: The system MUST load the instrument model (e.g., "Edinburgh Instruments LP-series" or "Generic") from `data/chemicals/instrument_config.yaml`. If the config is missing, it MUST default to "Generic Transient Absorption Spectrometer" to ensure vendor agnosticism and avoid hard-coding specific hardware dependencies (addressing Marie Curie review on missing instrument definition).
- [X] T036 [P] Update `docs/deviation_analysis.md` to compare simulated vs. expected physical behaviors
- [X] T037 [P] Add `docs/methodology.md` detailing instrument model, calibration dates, detection limits, and sample quantities (addressing Marie Curie review on reproducibility and instrument calibration protocol)
- [X] T041 [P] **Hydration Control & Monitoring**: Implement `code/analysis/hydration_control.py` to actively monitor and log solvent hydration states to three significant figures (±2% RH tolerance). This task must integrate with the environmental logging system (T014) and flag any run where hydration state deviates beyond tolerance, **raising a `PauseExperiment` exception** to halt the process (addressing Rosalind Franklin's concern about hydration artifacts). **Note**: This task consolidates the logic previously split between T041 and T052.
- [X] T042 [P] Implement `code/analysis/product_quantification.py` to define the analytical method (HPLC with UV detection) for quantifying ester rearrangement products, including detection thresholds and calibration standards. **Constraint**: NMR is explicitly excluded; only HPLC with UV detection is permitted as per Spec Assumptions.
- [X] T043 [P] Implement `code/analysis/temporal_resolution.py` to explicitly log and validate the temporal resolution of kinetic measurements (ns–μs) against instrument specifications (addressing Rosalind Franklin review on temporal resolution)
- [X] T044 [P] **Structural Baseline Logging**: Implement `code/analysis/baseline_logger.py` to record ground-state structural parameters (e.g., absorbance spectra, baseline stability) before and after photo-irradiation for each run, satisfying the requirement for a structural baseline as requested by Rosalind Franklin. Output to `data/processed/structural_baselines.csv`.
- [X] T051 [P] **Instrument Calibration Protocol**: Implement `code/analysis/calibration_protocol.py` to enforce a strict calibration sequence before any measurement. This task must: 1) Load calibration standards from `data/chemicals/calibration_standards.yaml`, 2) Record detector response curves and wavelength calibration data for each session, 3) Calculate and log detection limits in absorbance units (addressing Marie Curie's request for detection threshold quantification), and 4) Generate a calibration certificate for each run. Output to `data/processed/calibration_certificates/`.
- [X] T045 [P] **Detection Limit Verification**: Implement `code/analysis/detection_limits.py` to calculate and log the detection limit (in absorbance units or equivalent) for the singlet-radical-pair intermediate for each instrument session, addressing Marie Curie's concern for detection thresholds. Output to `data/processed/detection_limits.json`. **Dependency**: Depends on T051 (Calibration Protocol) completion.
- [X] T046 [P] **Error Margin Documentation**: Implement `code/analysis/error_analysis.py` to calculate and report the standard deviation and confidence intervals for all measured quantities (lifetime, solvation energy, product distribution) across independent runs, ensuring error margins are stated for every measurement as per Marie Curie's requirements. Output to `data/processed/error_margins.json`.
- [X] T047 [P] **Polarity Scale Definition**: Implement `code/analysis/polarity_scale.py` to explicitly define and log the solvent polarity scale used (e.g., dielectric constant ε, ET(30), or PCA-derived index) for every analysis, ensuring the scale is clearly stated as recommended by Rosalind Franklin. Output to `data/processed/polarity_scale_definition.yaml`.

---

## Phase 7: Review-Driven Enhancements (Addressing Specific Gaps)

**Purpose**: Implement missing experimental controls and reporting standards identified by Marie Curie and Rosalind Franklin reviews.

- [X] T053 [P] **Sample Quantity Tracking**: Implement `code/analysis/sample_tracker.py` to record exact quantities of all materials used per trial (solvent volume, substrate mass, integration time). This task must validate that all quantities are recorded to appropriate significant figures and generate a material balance report for each run (addressing Marie Curie's requirement for "weight of material" recording).
- [X] T054 [P] **Error Propagation Analysis**: Implement `code/analysis/error_propagation.py` to calculate and report error margins for all derived quantities (lifetimes, correlation coefficients) by propagating uncertainties from raw measurements through the entire analysis pipeline. Output must include standard deviations and confidence intervals for every reported metric (addressing Marie Curie's concern for stated error margins).
- [X] T055 [P] **Ground-State Characterization**: Implement `code/analysis/ground_state.py` to perform and log ground-state structural characterization (UV-Vis spectra, baseline stability) before photo-irradiation for each solvent condition. **Constraint**: If real data is unavailable, generate simulated UV-Vis spectra for the substrate in each solvent using a **Lorentzian absorption model** with defined parameters: peak wavelength (λ_max) from `code/config.py` (default ultraviolet wavelength), FWHM = 20 nm, and baseline noise = 0.005 AU. Log parameters: wavelength range (UV-visible), absorbance baseline, and peak positions. Output to `data/processed/ground_state_spectra.csv`. This task establishes the structural baseline required to distinguish solvent effects from instrumental artifacts (addressing Rosalind Franklin's request for ground-state characterization).
- [X] T056 [P] **Analytical Method Specification**: Implement `code/analysis/method_spec.py` to generate a comprehensive methods specification document that explicitly defines: 1) The solvent polarity scale used (dielectric constant, ET(30), or PCA index), 2) The analytical method for product quantification (HPLC-UV with specified detection thresholds), 3) The temporal resolution of kinetic measurements, and 4) The calibration standards used. Output to `docs/methodology.md` (addressing Rosalind Franklin's methodological requirements).
- [X] T057 [P] **Replicate Statistics Dashboard**: Implement `code/analysis/replicate_dashboard.py` to generate a visual and tabular summary of replicate statistics across all solvent conditions, including mean, standard deviation, coefficient of variation, and outlier flags. This task must clearly display the number of independent runs performed per condition (addressing Marie Curie's concern for reporting replicate counts).
- [X] T058 [P] **Detection Threshold Validation**: Implement `code/analysis/detection_threshold.py` to validate that all measured intermediate lifetimes exceed the instrument's detection limit by a statistically significant margin. This task must calculate the signal-to-noise ratio for each measurement and flag any results that fall below the detection threshold (addressing Marie Curie's concern for detection limits).

---

## Phase 8: Final Integration (Critical Path)

**Purpose**: Final integration tasks to ensure all reviewer concerns are fully addressed and the pipeline is production-ready.

- [X] T099 [P] **Safety Monitor & Control Loop**: Implement `code/analysis/safety_monitor.py` to act as the main control loop. **Constraint**: This task MUST call T041's check functions, catch the `PauseExperiment` exception raised by T041, and halt execution gracefully (logging the pause reason and alerting the researcher). **Dependency**: This task is the consumer of T041's exceptions and is required for the 'pause' behavior in Edge Cases.
- [X] T039 [P] **Full Pipeline Integration Test**: Implement `tests/integration/test_full_pipeline.py` to verify end-to-end execution from solvent configuration through statistical correlation. **Constraint**: This task MUST wait for completion of Phase 4 (T026) and Phase 5 (T034, T048). It must validate that all output artifacts (kinetic_metrics.csv, correlation_results.json, trend_verification_report.json) are generated correctly and contain valid data. **Dependency**: T039 depends on T026, T034, and T048.

---

## Phase 9: Review-Driven Enhancements (Addressing Specific Gaps)

**Purpose**: Implement specific gaps identified in prior research-stage reviews (Marie Curie & Rosalind Franklin) that were not fully covered in previous phases.

- [ ] T060 [P] **Instrument Definition & Calibration Log**: Implement `code/analysis/instrument_calibration_log.py` to generate a machine-readable calibration log for the transient-absorption spectrometer. **Constraint**: This task must explicitly define the instrument model (e.g., "Edinburgh Instruments LP980" or "Generic"), the specific detector type (e.g., "Photomultiplier Tube" or "InGaAs"), and the detection limit in absorbance units (addressing Marie Curie's review: "Which detector was used... What is the detection limit"). Output to `data/processed/instrument_calibration_log.json`. **Dependency**: Requires Phase 6 completion (T035 and T051).
- [ ] T061 [P] **Quantitative Material Balance Report**: Implement `code/analysis/material_balance.py` to generate a detailed report of all material quantities used per trial, including solvent volume, substrate mass, and integration time, with explicit **error margins** for each measurement (addressing Marie Curie's review: "recorded every quantity measured—the weight of the material"). Output to `data/processed/material_balance_report.csv`. **Dependency**: Depends on T053 (Sample Quantity Tracking) and T014 (Environment Logging).
- [ ] T062 [P] **Structural Baseline Verification**: Implement `code/analysis/baseline_verification.py` to compare pre- and post-irradiation structural baselines (UV-Vis spectra) and flag any deviations exceeding the noise threshold, ensuring the integrity of the kinetic data (addressing Rosalind Franklin's review: "what structural baseline will be measured before and after photo-irradiation"). Output to `data/processed/baseline_verification_report.json`. **Dependency**: Depends on T044 (Structural Baseline Logging) and T055 (Ground-State Characterization).
- [ ] T063 [P] **Analytical Method Validation**: Implement `code/analysis/method_validation.py` to validate that the chosen analytical method (HPLC-UV) meets the detection thresholds required for quantifying ester rearrangement products, and document the calibration standards used (addressing Rosalind Franklin's review: "define the analytical method... detection threshold and calibration standard"). Output to `docs/method_validation_report.md`. **Dependency**: Depends on T042 (Product Quantification) and T056 (Analytical Method Specification).
- [ ] T064 [P] **Hydration State Control Log**: Implement `code/analysis/hydration_state_log.py` to generate a detailed log of hydration state measurements for each solvent condition, including the exact RH value and the time of measurement, ensuring compliance with the ±2% RH tolerance (addressing Rosalind Franklin's review: "solvent composition must be specified to three significant figures"). Output to `data/processed/hydration_state_log.csv`. **Dependency**: Depends on T041 (Hydration Control & Monitoring) and T014 (Environment Logging).
- [ ] T065 [P] **Temperature Stability Verification**: Implement `code/analysis/temperature_stability.py` to verify that temperature control remained within the specified tolerance (±0.1°C) throughout the measurement window, and flag any excursions that could affect the kinetic data (addressing Rosalind Franklin's review: "temperature stability to ±0.1°C"). Output to `data/processed/temperature_stability_report.json`. **Dependency**: Depends on T014 (Environment Logging) and T041 (Hydration Control & Monitoring).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Note**: T015b (Real Data Ingestion) and T015c (Synthetic Generation) MUST complete BEFORE T014 and T017. T014 and T017 depend on the existence of data files produced by T015b/T015c.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Review-Driven Enhancements (Phase 7)**: Depends on completion of Phases 1-6, as these tasks build upon existing infrastructure to add missing controls and reporting
- **Final Integration (Phase 8)**: Depends on completion of all previous phases
- **Revision-Driven Enhancements (Phase 9)**: Depends on completion of Phases 1-8, as these tasks address specific gaps identified in prior research reviews and build upon the infrastructure established in earlier phases.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T015b (Phase 2) completion
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T015b (Phase 2) and US2 outputs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Loaders before Services/Analysis
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T012 (Integration test for US1) depends on T014 completion and cannot run in parallel with it.
- All Phase 7 tasks marked [P] can run in parallel once Phases 1-6 are complete, as they represent independent enhancements to the analysis pipeline.
- All Phase 9 tasks marked [P] can run in parallel once Phases 1-8 are complete, as they represent independent enhancements addressing specific review concerns.
- Phase 8 tasks are sequential and depend on all previous phases.

### Critical Execution Order for Phase 2

- **T015b and T015c MUST complete BEFORE T014 and T017**: T015b/T015c produce the trace data required by T014 (environment logging) and T017 (validation). The task list order in Phase 2 now reflects this strict 'Producer before Consumer' rule.
- **T059 (Unified Power Analysis) MUST complete BEFORE T021 and T026**: T059 defines the sample size (n≥3) required for the study. It must run before any data generation or fitting occurs to ensure the experimental design is powered correctly. The previous dependency direction (T059 after T026) was corrected.
- **T021 (NLME) and T022-T023 (Replicate/Outlier) are sequential**: T021 produces the primary fit, T022/T023 process the results.
- **T026 (Metrics Creation) depends on T021**: T026 aggregates the output of the kinetic fit.

### Critical Execution Order for Phase 5

- **T029a MUST complete before T029b**: T029b (Partition) consumes the output of T029a (Fetch).
- **T029d MUST complete before T029b**: T029b (Partition) requires explicit data from T029d.
- **T029b MUST complete before T029c**: T029c (Write) consumes the output of T029b.
- **T029c MUST complete before T030a**: T030a (Correlation Analysis) consumes the output of T029c (Solvent Models). T029 is NOT parallel [P] in execution; it is a sequential prerequisite (fetch -> explicit -> partition -> write).
- **T030a and T030b are sequential**: T030b depends on the output of T030a.
- **T031 depends on T030a**: T031 requires the PCA index from T030a.
- **T034 depends on T030b and T031**: T034 generates the final figures and reports based on T030b's results and T031's VIF scores.
- **T048 depends on T034**: T048 is the final trend verification gate.

### Critical Execution Order for Phase 6

- **T039 (Integration Test)**: Must strictly wait for the completion of **Phase 4 (T026)** and **Phase 5 (T034, T048)**. Do not execute T039 until all upstream data processing tasks in Phases 4 and 5 are finished. **(Note: T039 is re-introduced as a critical integration test to satisfy Plan requirements).**
- **T044, T045, T046, T047, T048, T050** are independent of each other but depend on the completion of Phase 4 and Phase 5 data generation. They can run in parallel once those phases are complete.
- **T051 (Calibration Protocol)** must complete before T045 (Detection Limit Verification) as the latter relies on calibration data.
- **T041 (Hydration Control)** is now self-contained and does not depend on T052 (which is removed).
- **T048 (Trend Verification) depends on T034**: Explicitly enforced in Phase 6 dependencies.

### Critical Execution Order for Phase 7

- **T053, T054, T055, T056, T057, T058** are independent of each other but depend on the completion of Phases 1-6. They can run in parallel once the core pipeline is functional.
- **T056 (Method Specification)** should be completed early in Phase 7 to guide implementation of other tasks.
- **Note**: T052 has been removed and merged into T041.

### Critical Execution Order for Phase 8

- **T099 (Safety Monitor)**: Must be implemented to catch `PauseExperiment` exceptions from T041. This is the control loop for the system.
- **T039** is the final gate. It must run after all data generation, analysis, and reporting tasks are complete. It validates the entire pipeline before the project is considered ready for publication.

### Critical Execution Order for Phase 9

- **T060, T061, T062, T063, T064, T065** are independent of each other but depend on the completion of Phases 1-8. They can run in parallel once the core pipeline and all previous review-driven enhancements are complete.
- **T060 (Instrument Calibration Log)** depends on T035 and T051.
- **T061 (Material Balance Report)** depends on T053 and T014.
- **T062 (Baseline Verification)** depends on T044 and T055.
- **T063 (Method Validation)** depends on T042 and T056.
- **T064 (Hydration State Log)** depends on T041 and T014.
- **T065 (Temperature Stability Verification)** depends on T014 and T041.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for solvent validation in tests/unit/test_solvent_validation.py"
# Note: T012 (Integration test) depends on T014 and cannot run in parallel with it.

# Launch all models for User Story 1 together:
Task: "Implement environment logging in code/analysis/environment.py"
Task: "Implement CLI entry point in code/main.py" (depends on T014's code implementation)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - **Ensure T015b (Real Data Ingestion) is prioritized.**
3. Complete Phase 3: User Story 1 (Solvent configuration & data generation)
4. **STOP and VALIDATE**: Test US1 independently with mock data
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
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Kinetic Analysis)
 - Developer C: User Story 3 (Correlation & Diagnostics)
 - Developer D: Phase 6 & 7 (Review-Driven Enhancements)
 - Developer E: Phase 9 (Revision-Driven Enhancements)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Review Addressing**:
 - T035, T037 explicitly address Marie Curie's concern for instrument model, calibration dates, detection limits, and sample quantities. T035 now enforces config-based loading with a generic fallback.
 - T041, T042, T043, T050 explicitly address Rosalind Franklin's concern for hydration state control, product quantification methods, temporal resolution, and temporal resolution validation.
 - T017a, T017b, T018, T025, T048 address SC-010, SC-004, sensitivity analysis, and trend verification (SC-002).
 - T024, T049, T030a, T030b, T031, T032 address power analysis (US-2 and US-3), Bayesian statistics, p-value reporting (SC-003), collinearity (VIF), and multiple-comparison corrections.
 - T015b (Real Data), T015c (Synthetic Fallback) ensure data integrity and null hypothesis testing without violating reproducibility.
 - **T029 now implements the full dynamic partitioning logic for implicit/explicit solvent models as required by FR-005, replacing the fragmented T029a-d tasks.**
 - T042 restricted to HPLC with UV detection only; NMR explicitly excluded.
 - **Statistical Note**: All statistical tasks (T030a, T030b) now implement **Bayesian Hierarchical Modeling (BHM)** as the primary method for SC-003/FR-006 compliance, with ANOVA as a secondary diagnostic. This resolves the constraint violation with the Plan.
 - **New Review Addressing (Phase 7)**:
 - T051 explicitly addresses Marie Curie's concern for instrument calibration protocol and detection limits by implementing a comprehensive calibration system.
 - T041 (merged T052) addresses Rosalind Franklin's concern for hydration state control by implementing active monitoring and pausing on deviation.
 - T053 addresses Marie Curie's requirement for recording exact quantities of materials per trial.
 - T054 addresses Marie Curie's concern for error margins by implementing error propagation analysis.
 - T055 addresses Rosalind Franklin's request for ground-state structural characterization with explicit simulation fallback (Lorentzian model).
 - T056 addresses Rosalind Franklin's methodological requirements by generating a comprehensive methods specification.
 - T057 addresses Marie Curie's concern for reporting replicate counts and statistics.
 - T058 addresses Marie Curie's concern for detection thresholds by validating measurements against instrument limits.
 - **T038 has been removed because it contradicts Constitution Principle V (Versioning Discipline) which mandates automated governance for checksumming, preventing manual intervention.**
 - **T017a, T017b have been split** from T017 to separate validation from reporting.
 - **T006 has been split** into T006a, T006b, T006c, T006d to ensure atomic execution of schema, population, validation, and hash generation.
 - **T015b now includes specific exit code and error message** to ensure deterministic CI failure.
 - **T014 now includes substrate_mass, integration_time_ms, and barometric_pressure** to satisfy FR-007 and FR-003.
 - **T049 adds power analysis for US-3** to satisfy SC-007 for the correlation step. (Note: T049 has been merged into T059).
 - **T050 adds temporal resolution validation** to satisfy FR-002.
 - **T048 adds trend verification** to satisfy SC-002.
 - **T051 moved to Phase 6** to resolve dependency with T045.
 - **T052 removed and merged into T041** to resolve circular dependency.
 - **T056 output path corrected** to `docs/methodology.md`.
 - **T034 dependency on T031 added** to ensure VIF scores are available.
 - **T006d mandates version hash generation** to satisfy SC-010 and Constitution Principle V.
 - **T017 denominator clarified** to 'total configured runs'.
 - **T029 now covers full partitioning logic** (fetch, partition, write) to avoid merge conflicts.
 - **T021 mandates NLME framework** to satisfy Plan requirements.
 - **T015c implements real interface logic** with explicit error handling.
 - **T015d documents the hardware integration gap**.
 - **T012 dependency on T014 clarified**.
 - **T013 and T014 reordered** to reflect logical flow (Implementation before CLI).
 - **T048 updated with concrete verification logic**.
 - **T055 updated with concrete logging and fallback logic** (Lorentzian model).
 - **T030b updated to clarify BHM role** (BHM is now primary, ANOVA secondary).
 - **T029 [P] tag removed** to reflect sequential execution.
 - **T015c 'FAILED' status removed** and replaced with concrete implementation.
 - **T015b exit code specified**.
 - **T017 split into T017a/T017b**.
 - **T006 split into T006a-d**.
 - **T021 updated to mandate NLME**.
 - **T015c updated to clarify hardware dependency**.
 - **T030b updated to clarify BHM role**.
 - **T006d added for continuous hash update**.
 - **T048 updated to remove 'FAILED' status**.
 - **T012 updated**.
 - **T013/T014 reordered**.
 - **T051 moved before T045**.
 - **T029a/b/c consolidated**.
 - **T015b exit code specified**.
 - **T017 split**.
 - **T006 split**.
 - **T021 updated**.
 - **T015c updated**.
 - **T030b updated**.
 - **T006d added**.
 - **T048 updated**.
 - **T012 updated**.
 - **T013/T014 reordered**.
 - **T051 moved**.
 - **T029 consolidated**.
 - **T048 now explicitly implements trend verification logic** to satisfy SC-002 and remove the 'FAILED' status.
 - **T030b now explicitly distinguishes Bayesian primary vs Frequentist diagnostic** (Frequentist is now secondary) to satisfy SC-003 without violating the Plan's statistical rigor.
 - **T059 consolidates power analysis** to satisfy SC-007 with a unified artifact.
 - **T013 now explicitly enforces FR-001 constraints** at the CLI level.
 - **T055 now explicitly defines the Lorentzian model** for simulation.
 - **T059 moved to Phase 2** to satisfy dependency order.
 - **T013 and T014 swapped** to satisfy build order.
 - **T048 dependency on T034 clarified**.
 - **T015b/T015c relationship clarified**.
 - **T015 trigger condition specified**.
 - **T017a hash retrieval specified**.
 - **T059 input specified**.
 - **T029 data source specified**.
 - **T055 lambda_max source specified**.
 - **T059 scope clarified**.
 - **T039 re-introduced**.
 - **T039 now explicitly waits for T026 and T034** to ensure all data is generated before integration testing.
 - **T025 now explicitly overrides the spec's malformed syntax** with a defined set {0.05, 0.1} ns to ensure deterministic execution.
 - **T031 now explicitly forbids VIF on raw variables** and mandates VIF on the PCA-derived index.
 - **T029 now includes a pre-flight check** for the 80/20 split constraint to ensure executability.
 - **T034 now mandates automated injection** of the 'associational' framing into metadata and captions.
 - **T006d now guarantees the creation of state/artifact_hashes.yaml** and the population of solvents_yaml_hash to ensure T017a can execute.
 - **T033 now mandates automated injection** of the 'associational' framing string into the output JSON metadata field `framing` and the figure caption text.
- [X] T006a [P] **Solvent Schema Definition**: Define `contracts/solvent.schema.yaml` to specify the required fields, data types, and constraints for solvent data (name, dielectric_constant, source_id, citation_url).
- [X] T006b [P] **Solvent Data Population**: Populate `data/chemicals/solvents.yaml` with at least 5 distinct solvents (cyclohexane, methanol, acetonitrile, toluene, water) including real NIST values for dielectric constant. Source: NIST Standard Reference Database.
- [X] T006c [P] **Solvent Schema Validation**: Validate `data/chemicals/solvents.yaml` against `contracts/solvent.schema.yaml` to ensure all required fields and data types are correct.
- [X] T006d [P] **Version Hash Generation & State Update**: Execute SHA-256 hashing on `data/chemicals/solvents.yaml` and record the result in `state/artifact_hashes.yaml` under the key `solvents_yaml_hash`. **Constraint**: This task MUST create the `state/artifact_hashes.yaml` file if it does not exist, ensuring the key `solvents_yaml_hash` is populated with a valid hash. This ensures the hash is always current per Constitution Principle V and guarantees T017a can execute successfully.
- [X] T007 [P] Define `contracts/kinetic_trace.schema.yaml` for data validation of transient-absorption traces.
- [X] T008 [P] Implement `code/data/loaders.py` to fetch real solvent properties from `data/chemicals/solvents.yaml` (no synthetic generation of input properties).
- [X] T009a [P] **Config Paths & CPU Constraints**: Implement `code/config.py` to enforce CPU-only execution constraints and define file paths for `data/raw/`, `data/compute/`, `data/processed/`.
- [X] T009b [P] **Explicit Solvent Configuration**: Extend `code/config.py` to define the `EXPLICIT_SOLVENTS` list (e.g., `['water', 'methanol']`) required by T029b for FR-005 compliance. **Constraint**: This list MUST be populated with at least one solvent if N >= 5 to satisfy the [deferred] explicit model requirement.
- [X] T010 [P] Create `tests/unit/test_loaders.py` to verify solvent property loading against versioned lookup table.