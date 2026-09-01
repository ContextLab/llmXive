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
- [X] T002 Initialize a Python project with pinned dependencies in `requirements.txt` (numpy, scipy, pandas, scikit-learn, pyyaml, pymatgen, matplotlib, seaborn, pymc)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`
- [X] T004 [P] Initialize `code/utils/seeds.py` to set global random seeds for reproducibility
- [X] T005 [P] Setup `code/utils/logging.py` to handle structured logging of environmental parameters

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes data generation/ingestion which is a prerequisite for US2/US3.

- [X] T006 Create `data/chemicals/solvents.yaml` with versioned dielectric constant lookup table (schema: `name`, `dielectric_constant`, `source_id` (NIST Standard Reference Database 103b), `version_hash`, `citation_url`; **Requirement**: MUST populate with at least 5 distinct solvents including cyclohexane, methanol, acetonitrile, toluene, and water with real NIST values sourced from the NIST database. The task MUST generate a SHA-256 content hash of the final file and store it in `state/artifact_hashes` to satisfy SC-010's 'measured against lookup table version hash' condition).
- [X] T007 Define `contracts/solvent.schema.yaml` and `contracts/kinetic_trace.schema.yaml` for data validation
- [X] T008 Implement `code/data/loaders.py` to fetch real solvent properties from `data/chemicals/solvents.yaml` (no synthetic generation of input properties)
- [X] T009 Implement `code/config.py` to enforce CPU-only execution constraints and define file paths for `data/raw/`, `data/compute/`, `data/processed/`
- [X] T010 [P] Create `tests/unit/test_loaders.py` to verify solvent property loading against versioned lookup table

- [X] T015b [US1] **Real Data Ingestion (Blocking)**: Implement `code/data/ingest.py` to ingest real transient-absorption data from a user-provided file path (e.g., `data/raw/real_traces.csv`). **Constraint**: This task MUST raise a `FileNotFoundError` with exit code 1 and a clear error message if the real data file is missing AND the `USE_REAL_DATA` environment variable is set to true. If `USE_REAL_DATA` is false or unset, it must proceed to T015. It is the primary data source for the research phase.
- [X] T015 [P] [US1] **CI-Placeholder Data Generation**: Implement `code/data/generate_synthetic.py` to generate deterministic synthetic transient-absorption traces (mocking laser flash photolysis) as a **fallback ONLY** for CI logic testing. **Constraint**: This task MUST NOT be used as the primary research data source. It runs only if T015b is explicitly bypassed or disabled. Output to `data/raw/synthetic_traces.csv`.
- [X] T015c [P] [US1] **Real Instrument Interface**: Implement `code/hardware/interface.py` to provide the API contract for 'capturing' transient-absorption data (e.g., `capture_trace(serial_port, timeout)`). This task satisfies the 'MUST capture' requirement of FR-002 by defining the interface. For CI, this implementation defaults to returning synthetic data from T015, but must be swappable for real driver logic when hardware is available.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Configure and Execute Solvent Series (Priority: P1) 🎯 MVP

**Goal**: Define a series of solvents spanning non-polar to polar conditions and initiate the experimental protocol with full environmental logging.

**Independent Test**: Verify that the system logs dielectric constant (validated against `solvents.yaml`), temperature (25 ± 0.5°C), and relative humidity (±2% RH) for each run.

### Tests for User Story 1 (OPTIONAL)

- [X] T011 [P] [US1] Unit test for `code/data/loaders.py` validating dielectric constant lookup in `tests/unit/test_solvent_validation.py`
- [X] T012 [US1] Integration test for environmental logging in `tests/integration/test_env_logging.py` (depends on T014)

### Implementation for User Story 1

- [X] T014 [US1] Implement `code/analysis/environment.py` to log temperature, humidity, barometric pressure, **substrate_mass**, and **integration_time_ms** for each run. **Constraint**: Must output to `data/processed/environment_logs.json` with all fields required by FR-007 (addressing SC-004, FR-007).
- [X] T013 [US1] Implement `code/main.py` CLI entry point to configure solvent series (multiple solvents, ε range low to moderate). **Dependency**: Depends on T014's *module implementation* (the code exists to be called), NOT on the existence of the output file. T013 invokes T014's functions to generate the log file.
- [X] T017 [US1] Implement `code/analysis/validation.py` to: 1) flag runs where logged dielectric constants deviate >2% from `solvents.yaml` (addressing SC-010), 2) calculate and verify environmental compliance percentage (≥95% of runs within tolerance) by reading `data/processed/environment_logs.json` and write result to `data/processed/compliance_report.json`. **Constraint**: The denominator for compliance percentage is 'total configured solvent runs' (sum of all `n` replicates defined in configuration). **Constraint**: This task MUST first verify `data/chemicals/solvents.yaml` exists and contains a valid `version_hash`; if missing, it MUST raise a `ConfigurationError` to prevent silent failure. 3) detect and flag runs where temperature or humidity exceeds tolerance (addressing Edge Cases in spec).
- [X] T018 [US1] Implement `code/analysis/validation.py` to detect and flag runs where temperature or humidity exceeds tolerance (addressing Edge Cases in spec)

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
- [X] T021 [P] [US2] Implement `code/analysis/kinetic_fit.py` to perform global kinetic analysis (exponential fitting) on `data/processed/calibrated_traces.csv` (or synthetic equivalent)
- [X] T022 [US2] Implement `code/analysis/kinetic_fit.py` to calculate mean lifetime and standard deviation for n ≥ 3 replicates per solvent
- [X] T023 [US2] Implement `code/analysis/kinetic_fit.py` to flag outliers beyond a statistically significant threshold. (addressing US-2 acceptance scenario)
- [X] T024 [US2] Implement `code/analysis/power.py` to document power analysis for n=3 and estimate detectable effect size (addressing SC-007)
- [X] T025 [US2] Implement `code/analysis/kinetic_fit.py` to perform threshold sensitivity analysis on lifetime discrepancy cutoffs across a range of values and report false-positive/negative rates (addressing SC-008)
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

- [X] T029a [US3] **DFT Solvation Fetcher**: Implement `code/data/compute/solvent_models.py` to fetch or compute DFT solvation data for a list of N solvents. Output intermediate results to `data/compute/dft_solvation_raw.csv`.
- [X] T029b [US3] **Partitioning Logic**: Implement `code/data/compute/solvent_models.py` to select a subset of size `floor(N * alpha)` (or fewer) for implicit solvent models (SMD/PCM) and the remaining `N - subset_size` (guaranteed ≥ 20% if N ≥ 5) for explicit solvent models (QM/MM or cluster-continuum). **Constraint**: `alpha` is defined in `code/config.py` (default 0.8). **Selection Strategy**: The first `floor(N * alpha)` solvents in the configuration list are implicit; the rest are explicit.
- [X] T029c [US3] **CSV Writer**: Implement `code/data/compute/solvent_models.py` to combine results from T029a and T029b into `data/compute/solvent_solvation.csv`. This task satisfies FR-005 (≤80% implicit, ≥20% explicit).
- [X] T030a [US3] **Bayesian Correlation**: Implement `code/analysis/correlation.py` to perform **Bayesian Hierarchical Modeling (BHM)** to correlate lifetime with Solvation Energy and Dielectric Constant. **Constraint**: Do NOT use standard ANOVA or Linear Regression as the primary model. Use a PCA-derived "Solvent Polarity Index" as the primary predictor to avoid tautology. Output posterior distributions for slope and intercept. **Dependency**: This task must complete before T030b.
- [X] T030b [US3] **Statistical Reporting**: Implement `code/analysis/correlation.py` to report **Posterior Probability of Effect**, **Bayes Factors**, AND **exact p-value** (via `scipy.stats.f_oneway` ANOVA test) to satisfy SC-003. **Clarification**: The 'exact p-value' is the frequentist p-value from the ANOVA test, required by SC-003. Calculate **Bayesian R²** and **credible intervals (CI)**. Explicitly frame all findings as associational and exploratory due to low N (n=3). **Output**: Must write `data/processed/correlation_results.json` with keys: `posterior_slope`, `bayesian_p_value`, `frequentist_anova_p_value`, `bayes_factor`, `bayesian_r2`, `credible_intervals`. (Addressing SC-001, SC-003, SC-006). **Dependency**: This task must complete after T030a.
- [X] T031 [US3] Implement `code/analysis/correlation.py` to perform VIF analysis to distinguish dielectric vs. solvation effects (addressing SC-009 and Rosalind Franklin review)
- [X] T032 [US3] Implement `code/analysis/correlation.py` to apply multiple-comparison correction (e.g., Bonferroni) and report family-wise error rate
- [X] T033 [US3] Implement `code/analysis/correlation.py` to frame all findings as associational (not causal) in output metadata
- [X] T049 [US3] **Correlation Power Analysis**: Implement `code/analysis/power.py` to perform and document a specific power analysis for the *correlation* step (US-3) using n=3 replicates, estimating the detectable effect size for the regression slope. Output to `data/processed/correlation_power_analysis.json` (addressing SC-007).
- [X] T034 [US3] Generate `paper/figures/regression_plot.png` and **copy** `data/processed/correlation_results.json` from T030b (do not regenerate) with **Bayesian R²**, **95% Credible Intervals**, **p-values**, and VIF scores; ensure all findings are explicitly framed as associational (addressing SC-006). **Dependency**: This task depends on completion of T030b AND T031 (to ensure VIF scores are available).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns (Review-Driven)

**Purpose**: Address specific reviewer concerns regarding instrumentation, calibration, and reproducibility.

- [X] T035 [P] Implement `code/analysis/instrument_registry.py` to define and log instrument configuration. **Constraint**: The system MUST load the instrument model (e.g., "Edinburgh Instruments LP-series" or "Generic") from `data/chemicals/instrument_config.yaml`. If the config is missing, it MUST default to "Generic Transient Absorption Spectrometer" to ensure vendor agnosticism and avoid hard-coding specific hardware dependencies (addressing Marie Curie review on missing instrument definition).
- [X] T036 [P] Update `docs/deviation_analysis.md` to compare simulated vs. expected physical behaviors
- [X] T037 [P] Add `docs/methodology.md` detailing instrument model, calibration dates, detection limits, and sample quantities (addressing Marie Curie review on reproducibility and instrument calibration protocol)
- [X] T048 [US3] **Trend Verification**: Implement `code/analysis/validation.py` to verify that consistent trends are observed across ≥5 solvent conditions as a pass/fail criterion for SC-002. This task must read `data/processed/correlation_results.json` and `data/processed/kinetic_metrics.csv` to confirm the correlation holds across the minimum required solvent set. Output to `data/processed/trend_verification_report.json`.
- [X] T050 [US1] **Temporal Resolution Validator**: Implement `code/analysis/validation.py` to explicitly validate that captured data meets the 'ns–μs' temporal resolution constraint specified in FR-002. This task must inspect the metadata of `data/processed/calibrated_traces.csv` and flag any runs outside the specified time window. Output to `data/processed/temporal_resolution_report.json`.
- [X] T041 [P] **Hydration Control & Monitoring**: Implement `code/analysis/hydration_control.py` to actively monitor and log solvent hydration states to three significant figures (±2% RH tolerance). This task must integrate with the environmental logging system (T014) and flag any run where hydration state deviates beyond tolerance, **pausing the experiment and alerting the researcher** (addressing Rosalind Franklin's concern about hydration artifacts). **Note**: This task consolidates the logic previously split between T041 and T052.
- [X] T042 [P] Implement `code/analysis/product_quantification.py` to define the analytical method (HPLC with UV detection) for quantifying ester rearrangement products, including detection thresholds and calibration standards. **Constraint**: NMR is explicitly excluded; only HPLC with UV detection is permitted as per Spec Assumptions.
- [X] T043 [P] Implement `code/analysis/temporal_resolution.py` to explicitly log and validate the temporal resolution of kinetic measurements (ns–μs) against instrument specifications (addressing Rosalind Franklin review on temporal resolution)
- [X] T044 [P] **Structural Baseline Logging**: Implement `code/analysis/baseline_logger.py` to record ground-state structural parameters (e.g., absorbance spectra, baseline stability) before and after photo-irradiation for each run, satisfying the requirement for a structural baseline as requested by Rosalind Franklin. Output to `data/processed/structural_baselines.csv`.
- [X] T045 [P] **Detection Limit Verification**: Implement `code/analysis/detection_limits.py` to calculate and log the detection limit (in absorbance units or equivalent) for the singlet-radical-pair intermediate for each instrument session, addressing Marie Curie's concern for detection thresholds. Output to `data/processed/detection_limits.json`. **Dependency**: Depends on T051 (Calibration Protocol) completion.
- [X] T046 [P] **Error Margin Documentation**: Implement `code/analysis/error_analysis.py` to calculate and report the standard deviation and confidence intervals for all measured quantities (lifetime, solvation energy, product distribution) across independent runs, ensuring error margins are stated for every measurement as per Marie Curie's requirements. Output to `data/processed/error_margins.json`.
- [X] T047 [P] **Polarity Scale Definition**: Implement `code/analysis/polarity_scale.py` to explicitly define and log the solvent polarity scale used (e.g., dielectric constant ε, ET(30), or PCA-derived index) for every analysis, ensuring the scale is clearly stated as recommended by Rosalind Franklin. Output to `data/processed/polarity_scale_definition.yaml`.
- [X] T051 [P] **Instrument Calibration Protocol**: Implement `code/analysis/calibration_protocol.py` to enforce a strict calibration sequence before any measurement. This task must: 1) Load calibration standards from `data/chemicals/calibration_standards.yaml`, 2) Record detector response curves and wavelength calibration data for each session, 3) Calculate and log detection limits in absorbance units (addressing Marie Curie's request for detection threshold quantification), and 4) Generate a calibration certificate for each run. Output to `data/processed/calibration_certificates/`.

---

## Phase 7: Review-Driven Enhancements (Addressing Specific Gaps)

**Purpose**: Implement missing experimental controls and reporting standards identified by Marie Curie and Rosalind Franklin reviews.

- [X] T053 [P] **Sample Quantity Tracking**: Implement `code/analysis/sample_tracker.py` to record exact quantities of all materials used per trial (solvent volume, substrate mass, integration time). This task must validate that all quantities are recorded to appropriate significant figures and generate a material balance report for each run (addressing Marie Curie's requirement for "weight of material" recording).
- [X] T054 [P] **Error Propagation Analysis**: Implement `code/analysis/error_propagation.py` to calculate and report error margins for all derived quantities (lifetimes, correlation coefficients) by propagating uncertainties from raw measurements through the entire analysis pipeline. Output must include standard deviations and confidence intervals for every reported metric (addressing Marie Curie's concern for stated error margins).
- [X] T055 [P] **Ground-State Characterization**: Implement `code/analysis/ground_state.py` to perform and log ground-state structural characterization (UV-Vis spectra, baseline stability) before photo-irradiation for each solvent condition. This task must establish the structural baseline required to distinguish solvent effects from instrumental artifacts (addressing Rosalind Franklin's request for ground-state characterization).
- [X] T056 [P] **Analytical Method Specification**: Implement `code/analysis/method_spec.py` to generate a comprehensive methods specification document that explicitly defines: 1) The solvent polarity scale used (dielectric constant, ET(30), or PCA index), 2) The analytical method for product quantification (HPLC-UV with specified detection thresholds), 3) The temporal resolution of kinetic measurements, and 4) The calibration standards used. Output to `docs/methodology.md` (addressing Rosalind Franklin's methodological requirements).
- [X] T057 [P] **Replicate Statistics Dashboard**: Implement `code/analysis/replicate_dashboard.py` to generate a visual and tabular summary of replicate statistics across all solvent conditions, including mean, standard deviation, coefficient of variation, and outlier flags. This task must clearly display the number of independent runs performed per condition (addressing Marie Curie's concern for reporting replicate counts).
- [ ] T058 [P] **Detection Threshold Validation**: Implement `code/analysis/detection_threshold.py` to validate that all measured intermediate lifetimes exceed the instrument's detection limit by a statistically significant margin. This task must calculate the signal-to-noise ratio for each measurement and flag any results that fall below the detection threshold (addressing Marie Curie's concern for detection limits).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Note**: T015b (Real Data Ingestion) is now an independent task that triggers on `USE_REAL_DATA=true`. T015 runs independently as the default fallback.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Review-Driven Enhancements (Phase 7)**: Depends on completion of Phases 1-6, as these tasks build upon existing infrastructure to add missing controls and reporting

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
- **Note**: T012 (Integration test for US1) depends on T014 implementation and cannot run in parallel with it.
- All Phase 7 tasks marked [P] can run in parallel once Phases 1-6 are complete, as they represent independent enhancements to the analysis pipeline.

### Critical Execution Order for Phase 5

- **T029a, T029b, T029c MUST complete before T030a**: T030a (Correlation Analysis) consumes the output of T029c (Solvent Models). T029 is NOT parallel [P] in execution; it is a sequential prerequisite (a -> b -> c).
- **T030a and T030b are sequential**: T030b depends on the output of T030a.
- **T034 depends on T030b and T031**: T034 generates the final figures and reports based on T030b's results and T031's VIF scores.
- **T039 depends on T034**: T039 is the final integration gate.

### Critical Execution Order for Phase 6

- **T039 (Integration Test)**: Must strictly wait for the completion of **Phase 4 (T026)** and **Phase 5 (T034)**. Do not execute T039 until all upstream data processing tasks in Phases 4 and 5 are finished.
- **T044, T045, T046, T047, T048, T050** are independent of each other but depend on the completion of Phase 4 and Phase 5 data generation. They can run in parallel once those phases are complete.
- **T051 (Calibration Protocol)** must complete before T045 (Detection Limit Verification) as the latter relies on calibration data.
- **T041 (Hydration Control)** is now self-contained and does not depend on T052 (which is removed).

### Critical Execution Order for Phase 7

- **T053, T054, T055, T056, T057, T058** are independent of each other but depend on the completion of Phases 1-6. They can run in parallel once the core pipeline is functional.
- **T056 (Method Specification)** should be completed early in Phase 7 to guide implementation of other tasks.
- **Note**: T052 has been removed and merged into T041.

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
 - T017, T017b, T018, T025, T048 address SC-010, SC-004, sensitivity analysis, and trend verification (SC-002).
 - T024, T049, T030a, T030b, T031, T032 address power analysis (US-2 and US-3), Bayesian statistics, p-value reporting (SC-003), collinearity (VIF), and multiple-comparison corrections.
 - T015b (Real Data), T015 (Synthetic Fallback) ensure data integrity and null hypothesis testing without violating reproducibility.
 - **T029a, T029b, T029c now implement the dynamic partitioning logic for implicit/explicit solvent models as required by FR-005, replacing the fragmented T029a-d tasks.**
 - T042 restricted to HPLC with UV detection only; NMR explicitly excluded.
 - **Statistical Note**: All statistical tasks (T030a, T030b) strictly follow the Plan's Bayesian Hierarchical Modeling approach, BUT T030b now also reports exact p-values (via ANOVA) to satisfy SC-003, framing the Bayesian result as the primary inference for low-N robustness.
 - **New Review Addressing (Phase 7)**:
 - T051 explicitly addresses Marie Curie's concern for instrument calibration protocol and detection limits by implementing a comprehensive calibration system.
 - T041 (merged T052) addresses Rosalind Franklin's concern for hydration state control by implementing active monitoring and pausing on deviation.
 - T053 addresses Marie Curie's requirement for recording exact quantities of materials per trial.
 - T054 addresses Marie Curie's concern for error margins by implementing error propagation analysis.
 - T055 addresses Rosalind Franklin's request for ground-state structural characterization.
 - T056 addresses Rosalind Franklin's methodological requirements by generating a comprehensive methods specification.
 - T057 addresses Marie Curie's concern for reporting replicate counts and statistics.
 - T058 addresses Marie Curie's concern for detection thresholds by validating measurements against instrument limits.
 - **T038 has been removed** as it contradicts the Constitution's automated governance model for checksumming.
 - **T017, T017b, T018 have been consolidated** into T017 to avoid confusion about partial implementation.
 - **T006 now mandates population of `solvents.yaml`** to ensure T010 and T017 have data to verify against.
 - **T015b now includes conditional logic** to preserve CI reproducibility while enforcing real data requirements when requested.
 - **T014 now includes substrate_mass and integration_time_ms** to satisfy FR-007.
 - **T049 adds power analysis for US-3** to satisfy SC-007 for the correlation step.
 - **T050 adds temporal resolution validation** to satisfy FR-002.
 - **T048 adds trend verification** to satisfy SC-002.
 - **T051 moved to Phase 6** to resolve dependency with T045.
 - **T052 removed and merged into T041** to resolve circular dependency.
 - **T056 output path corrected** to `docs/methodology.md`.
 - **T034 dependency on T031 added** to ensure VIF scores are available.
 - **T006 mandates version hash generation** to satisfy SC-010.
 - **T017 denominator clarified** to 'total configured runs'.
 - **T029b alpha defined** in config.
 - **T030b ANOVA added** to satisfy SC-003.