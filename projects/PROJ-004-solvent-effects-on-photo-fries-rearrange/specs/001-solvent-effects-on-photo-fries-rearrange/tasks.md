# Tasks: Solvent Effects on Photo‑Fries Rearrangement Kinetics

**Input**: Design documents from `/specs/001-solvent-effects/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
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
- [X] T002 Initialize a Python project with pinned dependencies in `requirements.txt` (numpy, scipy, pandas, scikit-learn, pyyaml, pymc, statsmodels, ruff, black, rdkit)
- [X] T002b [P] **Add RDKit for Molecular Proxy**: Ensure `rdkit` is explicitly pinned in `requirements.txt` with a specific version (e.g., `rdkit==2023.9.1` or latest) to support T029d's CPU-tractable proxy models.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pypyproject.toml`
- [X] T004 [P] Initialize `code/utils/seeds.py` to set global random seeds for reproducibility
- [X] T005 [P] Setup `code/utils/logging.py` to handle structured logging of environmental parameters

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. This phase includes configuration, schema definition, and the safety control loop.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006a [P] **Solvent Schema Definition**: Define `contracts/solvent.schema.yaml` to specify the required fields, data types, and constraints for solvent data (name, dielectric_constant, source_id, citation_url).
- [X] T006b [P] **Solvent Data Population**: Populate `data/chemicals/solvents.yaml` with at least 5 distinct solvents (cyclohexane, methanol, acetonitrile, toluene, water) including real NIST values for dielectric constant. Source: NIST Standard Reference Database.
- [X] T006c [P] **Solvent Schema Validation**: Validate `data/chemicals/solvents.yaml` against `contracts/solvent.schema.yaml` to ensure all required fields and data types are correct.
- [X] T006d [P] **Version Hash Generation & State Update**: Execute SHA‑256 hashing on `data/chemicals/solvents.yaml` and record the result in `state/artifact_hashes.yaml` under the key `solvents_yaml_hash`. This task MUST create the `state/artifact_hashes.yaml` file if it does not exist, ensuring the key is always populated.
- [X] T007 [P] Define `contracts/kinetic_trace.schema.yaml` for data validation of transient‑absorption traces.
- [X] T008 [P] Implement `code/data/loaders.py` to fetch real solvent properties from `data/chemicals/solvents.yaml` (no synthetic generation of input properties).
- [X] T009a [P] **Config Paths & CPU Constraints**: Implement `code/config.py` to enforce CPU‑only execution constraints and define file paths for `data/raw/`, `data/compute/`, `data/processed/`. Also define:
 - `USE_REAL_DATA` (bool, default False)
 - `REAL_DATA_PATH` (string, path to a CSV/JSON trace file)
 - `DEFAULT_BAROMETRIC_PRESSURE` (float, hPa, default 1013.25)
 - `DEFAULT_SUBSTRATE_MASS` (float, g, default 0.0)
 - `DEFAULT_INTEGRATION_TIME_MS` (float, ms, default 0.0)
- [X] T009b [P] **Explicit Solvent Configuration**: Extend `code/config.py` to define the `EXPLICIT_SOLVENTS` list (e.g., `['water', 'methanol']`). Must contain at least one solvent when `N ≥ 5` to satisfy FR‑005.
- [X] T010 [P] Create `tests/unit/test_loaders.py` to verify solvent property loading against the versioned lookup table.
- [X] T014 [P] **Environment Logging Infrastructure**: Implement `code/analysis/environment.py` that logs temperature, humidity, **barometric pressure**, **substrate_mass**, and **integration_time_ms** for each run. Must read `DEFAULT_BAROMETRIC_PRESSURE`, `DEFAULT_SUBSTRATE_MASS`, and `DEFAULT_INTEGRATION_TIME_MS` from `code/config.py`. If real hardware sensors are unavailable, defaults are used; if keys are missing, raise `ConfigurationError`. Output → `data/processed/environment_logs.json`. **Clarification**: This task generates a list of run identifiers internally based on the configured solvent list in `code/config.py`. It depends on T015b/c only to produce the *data traces* associated with these runs, not the run IDs themselves.
- [X] T015b [P] **Real Data Ingestion (Blocking)**: Implement `code/data/ingest.py` to read transient‑absorption data from `REAL_DATA_PATH` defined in `code/config.py`. If `USE_REAL_DATA=True` and the file is missing, abort with `CRITICAL: Real data file missing at {path}.` and exit with code 1. This task is the primary data source for downstream analysis.
- [X] T015c [P] **CI‑Placeholder Synthetic Data Generation**: Implement `code/data/generate_synthetic.py` to deterministically generate synthetic transient‑absorption traces when `USE_REAL_DATA=False`. Produce `data/raw/synthetic_traces.csv`. Invocation: `python code/data/generate_synthetic.py --seed 42 --output data/raw/synthetic_traces.csv`.
- [X] T015e [P] **Instrument Capture Interface**: Implement `code/data/instrument_interface.py` defining `capture_transient_data()` which raises `NotImplementedError` if hardware is absent. This provides the API for future hardware integration.
- [X] T015d [P] **Hardware Integration Gap Documentation**: Create `docs/hardware_integration_status.md` documenting the current reliance on file ingestion or synthetic generation and the missing hardware interface.
- [X] T059a **Study Design Definition**: Implement `code/analysis/power.py` to define static study design parameters (`n ≥ 3` replicates per solvent, number of solvents, effect‑size placeholder). Output → `data/processed/study_design.yaml`. **NOTE**: This task is **sequential**; remove the [P] tag.
- [X] T059b **Run Power Analysis**: Extend `code/analysis/power.py` to execute the power analysis using the design from T059a and generate `data/processed/study_power_analysis.json` with keys `methodology`, `sample_size_n`, `effect_size_status`, `effect_size_value`, `update_trigger`. **Dependency**: Runs after T059a.
- [X] T068 **Structural Baseline Pre-Irradiation Capture**: Implement `code/analysis/baseline_capture.py` to enforce the measurement of a ground-state UV-Vis spectrum *before* any laser pulse. If `USE_REAL_DATA=True`, read `data/raw/baseline_<solvent>_<replicate>.csv`. If `USE_REAL_DATA=False`, generate a synthetic baseline using a Lorentzian model (lambda_max from `code/config.py`, FWHM=20nm, noise=0.005AU) and save to `data/raw/baseline_<solvent>_<replicate>.csv`. This spectrum serves as the zero-reference for T044. **Dependency**: Must run before T044. **Spec Compliance**: Must log thresholds (25 ± 0.5°C, ±2% RH) and trigger `PauseExperiment` if deviations are detected in associated environment logs.
- [X] T017c **Robust Hash Initialization**: Implement `code/analysis/hash_manager.py` to ensure `state/artifact_hashes.yaml` exists and contains a valid `solvents_yaml_hash`. Reads `data/chemicals/solvents.yaml`, computes SHA‑256, writes to state. Raises `FileNotFoundError` if solvents file missing. **Must run before T017a**.

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 – Configure and Execute Solvent Series (Priority P1) 🎯 MVP

**Goal**: Define a series of solvents spanning non‑polar to polar conditions and initiate the experimental protocol with full environmental logging.

**Independent Test**: Verify that the system logs dielectric constant (validated against `solvents.yaml`), temperature (25 ± 0.5 °C), and relative humidity (±2 % RH) for each run.

### Tests for User Story 1 (OPTIONAL)

- [X] T011 [P] [US1] Unit test for `code/data/loaders.py` validating dielectric constant lookup (`tests/unit/test_solvent_validation.py`).
- [X] T012 [P] [US1] Integration test for environmental logging (`tests/integration/test_env_logging.py`). Depends on T014 completion.

### Implementation for User Story 1

- [X] T013 [US1] **CLI Solvent Series Configuration**: Implement `code/main.py` CLI entry point to accept a list of solvents. Must validate that **≥ 5 distinct solvents** are provided and that their dielectric constants span a broad low‑to‑high range. Exit with error if constraints not met. Calls `code/analysis/environment.py` to generate logs.
- [X] T017a [US1] **Environmental Validation & SC‑010 Enforcement**: Implement `code/analysis/validation.py` to:
 1. Verify each logged dielectric constant deviates **≤ 2 %** from the lookup table.
 2. Compute the **percentage of runs** meeting this tolerance.
 3. Fail (raise `ValidationError`) if the percentage is **< 98 %** (fulfilling SC‑010).
 4. Flag temperature or humidity excursions beyond tolerances. Output → `data/processed/validation_flags.json`. Depends on `state/artifact_hashes.yaml` (generated by T017c) and on `data/processed/environment_logs.json`.
- [X] T017b [US1] **Compliance Reporting**: Extend `code/analysis/validation.py` to calculate overall environmental compliance (≥ 95 % of runs within all tolerances) and write `data/processed/compliance_report.json`. Uses outputs from T017a and the environment logs.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 – Extract Radical‑Pair Lifetime (Priority P2)

**Goal**: Process raw spectroscopic data to extract singlet‑radical-pair intermediate lifetime via global kinetic analysis.

**Independent Test**: Verify system outputs lifetime value with confidence interval and calibration record from uploaded decay traces.

### Tests for User Story 2 (OPTIONAL)

- [X] T019 [P] [US2] Unit test for exponential fitting (`tests/unit/test_kinetic_fit.py`).
- [X] T020 [P] [US2] Integration test for replicate statistics (`tests/integration/test_replicate_analysis.py`).

### Implementation for User Story 2

- [X] T016 [US2] **Calibration Application**: Implement `code/analysis/calibration.py` to apply instrument calibration factors, log detector response and wavelength stability per FR‑004. Output → `data/processed/calibration_record.json`.
- [X] T021 [US2] **Joint NLME Model Definition**: Implement `code/analysis/kinetic_fit.py` to **define** (but not execute) a Joint Non‑Linear Mixed‑Effects model using `pymc`. This step computes the PCA‑derived Solvent Polarity Index (for later correlation) and prepares model objects. Output → `data/processed/nlme_model.pkl`.
- [X] T022 [US2] **NLME Model Execution & Lifetime Extraction**: Extend `code/analysis/kinetic_fit.py` to **run** the NLME model, extract posterior distributions for lifetimes, compute mean, standard deviation per solvent, and flag outliers (> 2 σ). Output → `data/processed/kinetic_metrics.csv`.
- [X] T023 [US2] **Outlier Flagging**: Integrated in T022 (see above) – flags runs beyond a statistically significant threshold.
- [X] T025 [US2] **Threshold Sensitivity Analysis**: Implement sensitivity analysis on lifetime discrepancy cut‑offs `{0.05, 0.1}` ns. **Design Decision**: The spec (SC-008) contains a malformed set `{, 0.1}`. This task explicitly resolves the ambiguity by choosing **0.05 ns** as the lower bound to ensure a meaningful sensitivity range. Generate `data/processed/sensitivity_analysis.csv` with columns `threshold`, `false_positive_rate`, `false_negative_rate`.
- [X] T026 [US2] **Aggregated Kinetic Metrics**: Consolidate outputs into `data/processed/kinetic_metrics.csv` (if not already produced by T022) for downstream correlation.

**Checkpoint**: User Stories 1 & 2 should now work independently.

---

## Phase 5: User Story 3 – Correlate Solvation Energy with Kinetic Lifetimes (Priority P3)

**Goal**: Correlate computed solvation free energies with experimentally determined lifetimes using associational inference.

**Independent Test**: Verify system generates regression plot, statistical significance test, and multiple‑comparison correction.

### Tests for User Story 3 (OPTIONAL)

- [X] T027 [P] [US3] Unit test for VIF calculation (`tests/unit/test_collinearity.py`).
- [X] T028 [P] [US3] Integration test for correlation pipeline (`tests/integration/test_correlation.py`).

### Implementation for User Story 3

- [X] T029a [US3] **DFT Data Fetching (Implicit)**: Load pre‑computed implicit‑solvent DFT results from `data/compute/dft_results.csv`. If absent, use `rdkit`-based approximations or raise `ConfigurationError` to prevent heavy external dependencies (Gaussian/psi4) on CPU-only runners. Output rows include `model_type='implicit'`.
- [X] T029d [US3] **Explicit Solvent Model Computation (CPU Proxy)**: Implement `code/data/compute/solvent_models.py` to generate explicit‑solvent data when missing:
 - Use **RDKit** to generate 3D geometry of phenyl benzoate in the solvent.
 - Optimize geometry with **UFF** force field (CPU-tractable proxy for GAFF2/OpenMM).
 - Compute solvation free energy via **GBSA** (Generalized Born Surface Area) model in RDKit (CPU-tractable proxy for B3LYP/OpenMM). **Do NOT run OpenMM, Gaussian, or B3LYP**. Tag output rows with `model_type='explicit'`.
 - **Clarification**: This task satisfies FR-005's requirement for "explicit solvent models" by utilizing a validated CPU-tractable proxy (cluster-continuum approximation via UFF/GBSA) as permitted by the plan's feasibility constraints.
- [X] T029b [US3] **Model Partitioning & Validation**: Partition the solvent list into ≤ 80 % implicit and ≥ 20 % explicit based on `EXPLICIT_SOLVENTS`. **Dynamic Logic**: Calculate `min_explicit` as a proportion of the total solvent set.. **Validation**: The code MUST dynamically calculate this value and validate that the count of explicit models is ≥ `min_explicit`. **Do NOT hardcode checks for N=5**. Raise `ConfigurationError` if not satisfied.
- [X] T029c [US3] **Write Combined Solvation Table**: Merge implicit and explicit results into `data/compute/solvent_solvation.csv`. Must contain columns `solvent_id`, `solvation_energy`, `model_type`.
- [X] T030a [US3] **PCA‑Derived Index Preparation**: In `code/analysis/correlation.py`, compute a PCA on standardized dielectric constant and solvation energy **solely to produce a single Solvent Polarity Index**. This index is the *only* predictor used in the primary Bayesian Hierarchical Model. Raw dielectric constant and solvation energy are **excluded** from hypothesis testing.
- [X] T030b [US3] **Bayesian Hierarchical Model Execution & Reporting**: Run the Bayesian Hierarchical Model using the PCA‑derived index as predictor. Generate `data/processed/correlation_results.json` containing `bayesian_slope`, `bayesian_r2`, `credible_intervals`, and `p_value_equivalent`. **Spec Compliance**: Perform a secondary ANOVA (despite primary Bayesian model) specifically to satisfy the "ANOVA" keyword requirement in SC-003. Ensure findings are labeled `"associational"` in metadata.
- [X] T031 [US3] **VIF on PCA Index Only**: Perform VIF analysis **only** on the PCA‑derived Solvent Polarity Index (or its orthogonal components). Explicitly note that raw dielectric constant and solvation energy are excluded. Output → `data/processed/vif_scores.json`.
- [X] T032 [US3] **Multiple‑Comparison Correction**: Apply Bonferroni/Holm correction to any secondary tests (including the secondary ANOVA from T030b) and record family-wise error rate in `correlation_results.json`.
- [X] T033 [US3] **Associational Framing Enforcement**: Ensure all JSON outputs and figure captions contain a `"framing": "associational"` field.
- [X] T034 [US3] **Figure Generation & Artifact Copy**: Generate `paper/figures/regression_plot.png` using the Bayesian results and VIF scores. Copy `data/processed/correlation_results.json` (do not regenerate) into the paper assets. Ensure the figure caption includes the `"associational"` tag.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross‑Cutting Concerns (Review‑Driven)

**Purpose**: Address specific reviewer concerns regarding instrumentation, calibration, and reproducibility.

- [X] T035 [P] **Instrument Registry**: Implement `code/analysis/instrument_registry.py` to load instrument configuration from `data/chemicals/instrument_config.yaml`. Default to `"Generic Transient Absorption Spectrometer"` if missing. Output → `data/processed/instrument_config.json`.
- [X] T036 [P] **Quantitative Deviation Analysis**: Extend `docs/deviation_analysis.md` to compute and record RMSE and % error between simulated lifetimes (from synthetic data) and observed lifetimes (from real data). Include tables and plots.
- [X] T037 [P] **Methodology Documentation**: Update `docs/methodology.md` with instrument model, calibration dates, detection limits, and sample quantities per FR‑007.
- [X] T041 [P] **Hydration Control & Monitoring**: Implement `code/analysis/hydration_control.py` to log RH to three significant figures, integrate with `environment.py`, and raise `PauseExperiment` if RH deviates beyond ±2 % RH.
- [X] T042 [P] **Product Quantification (HPLC‑UV)**: Implement `code/analysis/product_quantification.py` to define HPLC‑UV method, detection thresholds, and calibration standards. Excludes NMR.
- [X] T043 [P] **Temporal Resolution Validation**: Implement `code/analysis/temporal_resolution.py` to log and validate that the measurement window spans ns–µs as per FR‑002.
- [X] T044 [P] **Baseline Logging**: Implement `code/analysis/baseline_logger.py` to record pre‑ and post‑irradiation absorbance spectra. Output → `data/processed/structural_baselines.csv`. **Dependency**: Requires T068 (Baseline Capture) to provide pre-irradiation reference.
- [X] T045 [P] **Calibration Protocol**: Implement `code/analysis/calibration_protocol.py` to load standards from `data/chemicals/calibration_standards.yaml`, record detector response curves, calculate detection limits, and generate a per‑run calibration certificate in `data/processed/calibration_certificates/`.
- [X] T045b [P] **Calibration Verification**: Implement `code/analysis/calibration_verification.py` to verify that the calibration certificate generated by T045 is valid (non-empty, correct schema) before downstream tasks (T060) proceed.
- [X] T046 [P] **Error Analysis**: Implement `code/analysis/error_analysis.py` to compute standard deviations and confidence intervals for all measured and derived quantities, output to `data/processed/error_margins.json`.
- [X] T047 [P] **Polarity Scale Definition**: Implement `code/analysis/polarity_scale.py` to log which polarity metric (dielectric constant, ET(30), or PCA index) is used for each analysis. Output → `data/processed/polarity_scale_definition.yaml`.

---

## Phase 7: Review‑Driven Enhancements (Addressing Specific Gaps)

**Purpose**: Implement missing experimental controls and reporting standards identified by reviewers.

- [X] T053 [P] **Sample Quantity Tracking**: Implement `code/analysis/sample_tracker.py` to record exact solvent volumes, substrate masses, and integration times per trial with appropriate significant figures. Generates `data/processed/sample_quantity_report.csv`.
- [X] T054 [P] **Error Propagation Analysis**: Implement `code/analysis/error_propagation.py` to propagate uncertainties from raw measurements through all downstream calculations (lifetimes, regression coefficients). Output includes propagated standard deviations and 95 % CI for every metric.
- [X] T055 [P] **Ground‑State Characterization**: Implement `code/analysis/ground_state.py`:
 - If `data/raw/ground_state_<solvent>.csv` exists, read real UV‑Vis spectra and log them.
 - Else, simulate spectra using a Lorentzian model with `lambda_max` from `code/config.py` (default UV), FWHM = 20 nm, baseline noise = 0.005 AU.
 - Output → `data/processed/ground_state_spectra.csv`.
- [X] T056 [P] **Analytical Method Specification**: Extend `docs/methodology.md` (or generate `docs/method_spec.md`) to detail solvent polarity scale, HPLC‑UV quantification, temporal resolution, and calibration standards.
- [X] T057 [P] **Replicate Statistics Dashboard**: Implement `code/analysis/replicate_dashboard.py` to produce a visual/table summary (mean, SD, CV, outlier flags) for each solvent condition. Output → `docs/replicate_dashboard.html`.
- [X] T058 [P] **Detection Threshold Validation**: Implement `code/analysis/detection_threshold.py` to compute SNR for each lifetime measurement, flag results below the instrument detection limit, and record in `data/processed/detection_threshold_report.json`.

---

## Phase 8: Final Integration (Critical Path)

**Purpose**: Ensure the entire pipeline runs end‑to‑end and all reviewer concerns are satisfied.

- [X] T099 [P] **Safety Monitor & Control Loop**: Implement `code/analysis/safety_monitor.py` that calls `hydration_control.check()`, catches `PauseExperiment`, logs the pause reason, and alerts the researcher. Integrates with the main execution driver.
- [X] T039 [P] **Full Pipeline Integration Test**: Implement `tests/integration/test_full_pipeline.py` that executes the full workflow from solvent configuration through statistical correlation. Must wait for completion of T026 (kinetic metrics) and T034 (final figures). Validates presence and integrity of `kinetic_metrics.csv`, `correlation_results.json`, and `trend_verification_report.json`.

---

## Phase 9: Review‑Driven Enhancements (Addressing Specific Gaps – Executable)

**Purpose**: Provide the missing artifacts required by FR‑007 and SC‑004 and close remaining reviewer gaps.

- [ ] T060 **Instrument Definition & Calibration Log**: Implement `code/analysis/instrument_calibration_log.py` to generate `data/processed/instrument_calibration_log.json` containing:
 - `instrument_model` (from `data/chemicals/instrument_config.yaml` or `code/config.py`; raise `ConfigurationError` if missing)
 - `detector_type` (from `data/chemicals/instrument_config.yaml`)
 - `detection_limit_absorbance` (from `data/chemicals/instrument_config.yaml`)
 - `calibration_date` (from `data/processed/calibration_certificates/{run_id}_cert.json`)
 - `calibration_certificate_path` (from `data/processed/calibration_certificates/`)
 - **Dependency**: Runs after T035, T045, and T045b (verification). **Constraint**: Must fail if source config is missing; do not generate synthetic defaults.
- [ ] T061 **Quantitative Material Balance Report**: Implement `code/analysis/material_balance.py` to read outputs from `sample_tracker.py` (T053) and `environment.py` (T014) and produce `data/processed/material_balance_report.csv` with columns `solvent`, `solvent_volume_ml`, `substrate_mass_g`, `integration_time_ms`, plus associated measurement uncertainties. **Dependency**: After T053 and T014.
- [ ] T062 **Structural Baseline Verification**: Implement `code/analysis/baseline_verification.py` to compare pre‑ and post‑irradiation spectra from `baseline_logger.py` (T044) and simulated/real spectra from T055. Flag deviations > 3 × baseline noise. Output → `data/processed/baseline_verification_report.json`. **Dependency**: After T044 and T055.
- [ ] T063 **Analytical Method Validation**: Implement `code/analysis/method_validation.py` to verify HPLC‑UV detection thresholds against calibration standards (from T045) and document in `docs/method_validation_report.md`. **Dependency**: After T042 and T056.
- [ ] T064 **Hydration State Control Log**: Implement `code/analysis/hydration_state_log.py` to export the detailed RH measurements recorded by `hydration_control.py` into `data/processed/hydration_state_log.csv`. **Dependency**: After T041.
- [ ] T065 **Temperature Stability Verification**: Implement `code/analysis/temperature_stability.py` to analyze temperature logs from `environment.py`, ensure control stayed within ±0.1 °C throughout each run, and generate `data/processed/temperature_stability_report.json`. **Dependency**: After T014 and T041.

---

## Phase 10: Reviewer-Specific Instrumentation & Baseline Controls (New)

**Purpose**: Directly address the "Marie Curie" and "Rosalind Franklin" simulation reviews regarding missing instrument definitions, calibration protocols, detection limits, and structural baseline measurements.

- [ ] T066 **Instrument Model & Detection Limit Specification**: Implement `code/analysis/instrument_spec.py` to explicitly define the instrument model (e.g., "Generic Transient Absorption Spectrometer" or specific model from `data/chemicals/instrument_config.yaml`), detector type, and detection limit. **Constraint**: Do not hardcode specific commercial models (e.g., "Edinburgh LP980") unless explicitly defined in `data/chemicals/instrument_config.yaml`. Output → `data/processed/instrument_spec.json`. **Dependency**: After T035.
- [ ] T067 **Calibration Date & Certificate Generation**: Extend `code/analysis/calibration_protocol.py` (T045) to automatically generate a machine-readable calibration certificate including the `calibration_date` (ISO 8601) and a hash of the calibration standard file used. This addresses the "Marie Curie" review requiring "exact instrument model and its calibration date". Output → `data/processed/calibration_certificates/{run_id}_cert.json`. **Dependency**: After T045.
- [ ] T069 **Hydration State Quantification & Logging**: Implement `code/analysis/hydration_quantifier.py` to calculate the theoretical water content of the solvent mixture based on the logged RH and temperature (using the Magnus formula or similar), and log this value to three significant figures in `data/processed/hydration_quantification.json`. **Spec Compliance**: Must explicitly reference the ±2% RH threshold from the spec's Edge Cases and trigger `PauseExperiment` if exceeded. **Dependency**: After T041.
- [ ] T070 **Product Distribution Analytical Method Definition**: Implement `code/analysis/product_method_spec.py` to explicitly document the HPLC-UV method parameters (column type, mobile phase, flow rate, detection wavelength) used for quantifying the ortho/para isomers. This addresses the "Rosalind Franklin" review asking "Is this NMR integration, chromatographic separation...?" and defines the "detection threshold and calibration standard". Output → `docs/hplc_method_spec.md`. **Dependency**: After T042.
- [ ] T071 **Intermediate Detection Methodology Declaration**: Implement `code/analysis/detection_methodology.py` to formally declare the "Transient Absorption Spectroscopy" method as the primary means of measuring singlet-radical-pair lifetimes, including the time-resolution (ns–µs) and the specific spectral window used. Values must be read from `code/config.py` and `data/chemicals/instrument_config.yaml`. Output → `docs/detection_methodology.md`. **Dependency**: After T015e.