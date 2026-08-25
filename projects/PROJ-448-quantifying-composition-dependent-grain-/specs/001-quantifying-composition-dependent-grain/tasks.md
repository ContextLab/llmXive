# Tasks: Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys

**Input**: Design documents from `/specs/001-quantifying-grain-boundary-segregation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, Validation, Cross-Cutting)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create `scripts/setup_project.py` with explicit directory definitions for `projects/PROJ-448-quantifying-composition-dependent-grain-/`, `code/`, `data/`, `tests/`, `research/`, `data/figures/`, and `data/processed/`. The script MUST create these directories if they do not exist.
- [X] T001b Execute `scripts/setup_project.py` to create the full directory tree as defined in T001a.
- [X] T002a Create `requirements.txt` at `projects/PROJ-448-quantifying-composition-dependent-grain-/` with dependencies: `pymatgen`, `ase`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `pycalphad`, `pyyaml`, `requests`, `memory_profiler`, `ruff`, `black`.
- [X] T002b Run `pip install -r requirements.txt` to install dependencies.
- [X] T003 [P] Configure linting (ruff/flake) and formatting (black) tools in `pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008a [P] Create `code/__init__.py` with a minimal logger setup that does NOT depend on `config.py`. **Purpose**: Provide a basic logger for early initialization scripts. **Dependency**: None.
- [X] T004 [P] Create `code/config.py` to define paths, random seeds, and temperature ranges (K to elevated temperatures in increments), and alloy system constants. **Dependency**: Must run after T008a.
- [X] T008b [P] Configure error handling and logging infrastructure in `code/__init__.py` using the constants defined in `code/config.py`. **Dependency**: Must run after T004.
- [X] T049 [P] Implement `code/data/manifest_validator.py` to verify that all data sources in `data_manifest.json` possess valid DOI or URL fields as required by FR-007. If a source lacks these, the validator MUST raise an error.
- [X] T050 [P] Create `code/data/manifest_schema.json` defining the strict schema for `data_manifest.json` including `source_type`, `source_id`, `doi`, `url`, and `checksum` fields.
- [ ] T006a [P] Research: Query the Open Thermodynamic Proxy (e.g., pycalphad open databases) for equilibrium phase compositions for Fe-Cr, Fe-Mo, Fe-V, Fe-W systems at elevated temperatures. **Output**: Write findings to `research/data_sources.md` as a JSON object with keys: `source_id`, `doi`, `url`, `status`. **Dependency**: None.
- [ ] T045a [P] Research: Query the NIST APT database for specific accession IDs for Fe-Cr, Fe-Mo, Fe-V, Fe-W systems. **Output**: Write findings to `research/data_sources.md` as a JSON list of accession IDs. **Dependency**: Must run after T006a.
- [ ] T045c [P] Research: Search Zenodo/DOI for peer-reviewed literature sources containing ternary APT data (Fe-Cr-Mo, Fe-Cr-V, etc.). **Output**: Write findings to `research/data_sources.md` as a JSON list of DOIs. **Dependency**: Must run after T006a.
- [ ] T045d [P] Fetch: Download the real ternary APT literature data from Zenodo using the specific DOIs identified in T045c. **Mechanism**: Use `requests.get()`. **Constraint**: If the fetch fails, raise a fatal error and terminate the pipeline immediately. Do NOT proceed with SC-003 or any validation tasks. The task MUST NOT generate synthetic data or proceed with missing data. **Dependency**: Must run after T045c.
- [ ] T005 [P] Implement `code/data/manifest.py` to generate and validate `data_manifest.json` using the schema from T050 and validator from T049, checking for missing data flags from T045d. **Dependency**: Must run after T049, T050, T006a, T045a, T045c, and T045d.
- [ ] T007 [P] Define `code/models/` directory structure and base entity schemas for `SegregationProfile`, `AlloySystem`, and `RegressionModel`. **Output**: Create `code/models/schemas.py` with Pydantic models for `SegregationProfile`, `AlloySystem`, and `RegressionModel`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Thermodynamic Segregation Profile Generation (Priority: P1) 🎯 MVP

**Goal**: Compute equilibrium segregation energies and concentrations for BCC alloy systems using surrogate DFT energies and the McLean isotherm model.

**Independent Test**: Run the computation pipeline on Fe-Cr at elevated temperatures and verify the output file contains valid segregation energy (eV) and equilibrium concentration (atomic fraction) derived from the McLean equation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for McLean isotherm calculation in `tests/unit/test_mclean.py`.
- [X] T011 [P] [US1] Integration test for data loading and profile generation in `tests/integration/test_us1_profile.py`.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/services/gb_service.py` to generate symmetric tilt grain boundary supercells using `pymatgen` from MP-13 seed.
- [ ] T047a [P] [US1] [FR-001] Validate the presence of binary interaction parameters in the open thermodynamic proxy. **Behavior**: If binary parameters are missing, perform linear extrapolation with a warning and flag the gap. **Dependency**: Must run after T006a.
- [ ] T047b [P] [US1] [FR-001] Handle missing ternary interaction parameters in the open proxy. **Behavior**: If ternary parameters are missing, perform linear interpolation between binary endpoints using `sklearn.linear_model.LinearRegression`. **Constraint**: MUST raise a specific warning and set a "NO_TERNARY_DATA" flag in the output manifest. Do NOT silently interpolate without flagging the gap. **Dependency**: Must run after T047a.
- [ ] T047c [P] [US1] [FR-001] Implement `code/services/thermo_service.py` to extract equilibrium phase compositions for the specified ternary systems (Fe-Cr-Mo, etc.) at elevated temperatures using the open proxy. **Dependency**: Must run after T047b.
- [ ] T013 [US1] [FR-002] Implement `code/services/surrogate_service.py` to compute literature-calibrated segregation energies. **Constraint**: This task MUST NOT implement or call any real DFT code (Quantum ESPRESSO) or DFT retry logic, as per the plan's 'Critical Deviation Note'. **Failure Handling**: The surrogate model is deterministic; if the calculation fails (returns NaN or raises error) or if calibration parameters are missing, raise an immediate exception. Do NOT retry. **Dependency**: Must run after T047c, T012.
- [X] T055 [US1] Implement validation in `code/services/surrogate_service.py` to ensure surrogate inputs align with the supercell geometry generated by `gb_service.py`. **Dependency**: Must run after T012 and T013.
- [ ] T014 [US1] Implement `code/models/mclean.py` to calculate equilibrium concentrations from segregation energy and bulk composition. **Requirements**:
 1. Cap equilibrium concentration at a predefined threshold. and log a "saturation" flag if the calculated value exceeds 1.0.
 2. Add logging statements using the logger from `code/config.py` with messages: "Calculated segregation energy: {value} eV", "Applied McLean isotherm", "Equilibrium concentration: {value}".
 **Dependency**: Must run after T055.
- [X] T018 [US1] Generate `data/processed/segregation_profiles.json` containing computed profiles for the ternary systems under investigation.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multicomponent Cooperative Effect Analysis (Priority: P2)

**Goal**: Analyze segregation profiles to identify non-linear thresholds and cooperative effects where multiple solutes amplify segregation.

**Independent Test**: Run analysis on the pre-computed ternary dataset and verify the regression model with interaction terms identifies at least one statistically significant interaction coefficient (p<0.05) and demonstrates >10% MSE reduction on a held-out test set compared to a purely additive binary model.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for interaction term generation in `tests/unit/test_regression.py`.
- [ ] T020 [P] [US2] Integration test for cooperative effect detection in `tests/integration/test_us2_cooperative.py`.

### Implementation for User Story 2

- [ ] T021 [US2] [FR-004] Implement `code/models/regression.py` to fit linear models with interaction terms (e.g., Cr*Mo, Cr*V). **Library**: Use `sklearn.linear_model.LinearRegression` and `sklearn.preprocessing.PolynomialFeatures(degree=2)` to generate interaction terms. **Dependency**: Must run after T018.
- [ ] T022 [US2] [FR-004] Implement logic to compare MSE of interaction model vs. additive binary null hypothesis, requiring >10% MSE reduction to confirm cooperative effects. **Output**: Log "MSE reduction: X% (Threshold: 10%)" and raise warning if threshold not met. **Dependency**: Must run after T021.
- [ ] T023 [US2] [FR-004] Implement significance testing (p-value < 0.05) for interaction coefficients. **Dependency**: Must run after T021.
- [ ] T024 [US2] [FR-006] Generate heatmaps visualizing segregation energy vs. bulk composition and temperature in `data/figures/segregation_heatmap.png`. **Requirements**: Must cover **all successfully computed alloy systems** (Fe-Cr-Mo, Fe-Cr-V, Fe-Mo-V, Fe-Cr-W, Fe-Mo-W). If the surrogate model fails for a specific system (as noted in T013), log a warning excluding that system and generate the plot for the remaining valid systems only. **Mapping**: x=bulk_concentration, y=temperature, z=segregation_energy. **Style**: Use `cmap=viridis` and `norm=LogNorm`. **Dependency**: Must run after T018.
- [ ] T025 [US2] Write results to `data/processed/cooperative_effects_analysis.json` including coefficients, p-values, and MSE reduction stats. **Dependency**: Must run after T022 and T023.
- [ ] T026 [US2] Add logic to flag systems where no significant cooperative effects are detected within statistical power. **Dependency**: Must run after T025.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Generalizability and Cross-Validation (Priority: P3)

**Goal**: Perform k-fold cross-validation on empirical composition-segregation functions to assess robustness.

**Independent Test**: Execute cross-validation on the combined dataset and verify mean R² is stable across folds with standard deviation ≤ 0.05.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for k-fold splitting logic in `tests/unit/test_validation.py`.
- [ ] T028 [P] [US3] Integration test for cross-validation metrics in `tests/integration/test_us3_validation.py`.

### Implementation for User Story 3

- [ ] T029 [P] [US3] [FR-005] Implement `code/models/validation.py` to perform k-fold cross-validation on composition/temperature data points. **Dependency**: Must run after T021.
- [ ] T030 [US3] [FR-005] Calculate and report R² and MSE for each fold, plus mean and standard deviation. **Output**: Log "Mean R²: X, Std Dev: Y" and flag if Std Dev > 0.05. **Dependency**: Must run after T029.
- [ ] T031 [US3] Perform transferability check: train on Fe-Cr-Mo, test on held-out Fe-Cr-V subset (if applicable). **Dependency**: Must run after T029.
- [ ] T032 [US3] Add overfitting detection logic (high training/low validation score) and flagging. **Dependency**: Must run after T030.
- [ ] T033 [US3] Generate `data/processed/cross_validation_results.json` with full metrics and fold details. **Dependency**: Must run after T030.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Experimental Strategy (Priority: P1 - Research Review)

**Goal**: Address Marie Curie's review concern regarding experimental verification, detection limits, and material requirements for validating computed segregation energies.

**Independent Test**: A review document `research/experimental_verification_plan.md` is generated that explicitly states the instrument model, minimum detectable concentration, and material mass required to validate SC-003.

### Implementation for Validation Strategy

- [ ] T061 [Validation] Define detection limits for APT and SIMS for Fe-Cr, Fe-Mo, Fe-V, Fe-W systems. **Source**: Query NIST APT database using accession IDs from `research/data_sources.md` (generated by T045a). Cite specific source (e.g., 'NIST Technical Note 1234' or 'Smith et al., 2020'). Write to `research/detection_limits.md`. **Dependency**: Must run after T045a.
- [ ] T062 [Validation] Define sample preparation protocols for APT/SIMS analysis of grain boundaries. Write to `research/sample_prep.md`.
- [ ] T063 [Validation] Perform feasibility analysis: compare computed segregation signals (from T018) to detection limits (from T061). Write to `research/feasibility_analysis.md`.
- [ ] T064 [Validation] Document material requirements (purity, grain size) for experimental validation. Write to `research/material_requirements.md`.
- [ ] T060 [Validation] [SC-003] Perform Experimental Validation (SC-003): Fetch real ternary APT data (from T045d), compute the deviation of computed segregation energy from experimental literature values, and write results to `data/processed/sc003_deviation.json`. Include the feasibility analysis (from T063) and detection limits (from T061). **Constraint**: This task is ONLY executable if T045d succeeded. If T045d failed, the pipeline halts before this task. **Dependency**: Must run after T018, T045d, T061, T062, T063, T064.

**Checkpoint**: Validation strategy is documented, and the project acknowledges the gap between computation and experimental proof.

---

## Phase 7: Experimental Feasibility & Instrumentation Review (Priority: P1 - Response to Reviewer)

**Goal**: Directly address the Marie Curie review by specifying the exact experimental apparatus, quantities, and sensitivity required to measure the predicted segregation, ensuring the project moves from "calculation" to "discovery" potential.

**Independent Test**: A review document `research/experimental_verification_plan.md` is generated that explicitly states the instrument model, minimum detectable concentration, and material mass required to validate SC-003.

### Implementation for Experimental Verification

- [ ] T070 [Validation] Research and document the specific Atom Probe Tomography (APT) instrument models (e.g., CAMECA LEAP) capable of resolving Fe-Cr-Mo segregation at grain boundaries. Write to `research/instrument_spec.md`.
- [ ] T071 [Validation] Calculate the minimum sample mass (mg) and number of grain boundaries required to achieve statistical significance (p<0.05) for the predicted segregation concentrations from T018. **Effect Size**: Use computed segregation signals from T018. **Variance**: Use detection limits from T072. **Library**: Use `statsmodels.stats.power.TTestIndPower`. **Conversion**: Convert sample size (N) to mass using `mass_mg = N * (avg_atomic_weight / density) * 1000`, where `avg_atomic_weight` is the weighted average of the alloy and `density = 7.87 g/cm3` for Fe-Cr-Mo. **Constraint**: This task requires real data from T045d to be available. **Dependency**: Must run after T018, T072, T045d.
- [ ] T072 [Validation] Define the specific detection limit (at. ppm) for trace solutes (Mo, V, W) at grain boundaries for the identified APT/SIMS instruments. Update `research/detection_limits.md` with instrument-specific values. **Dependency**: Must run after T061.
- [ ] T073 [Validation] Draft a protocol for correlating the computed segregation energy (eV) to the measurable atomic fraction in the APT dataset, including error propagation analysis. Write to `research/correlation_protocol.md`.
- [ ] T074 [Validation] Synthesize all experimental findings into a single `research/experimental_verification_plan.md` that explicitly answers: "What apparatus?", "How much material?", and "What is the detection limit?". **Required Inputs**: T070, T071, T072, T073, and **T060 (deviation results)** to define detection limits based on computed signals. **Constraint**: This task is ONLY executable if T045d succeeded. **Dependency**: Must run after T070, T071, T072, T073, and T060.

**Checkpoint**: The project now possesses a concrete, instrument-level plan for experimental validation, satisfying the requirement for direct measurement evidence.

---

## Dependencies & Execution Order

The execution order is strictly enforced as follows:

1.  **Foundation Chain**: T001a → T001b → T002a → T002b → T003 → T008a → T004 → T008b → T049 → T050 → T007.
2.  **Data Research & Fetch Chain**:
    -   T006a starts the data research.
    -   From T006a, two parallel branches emerge:
        -   Branch A: T045a (NIST APT IDs)
        -   Branch B: T045c (Zenodo DOIs)
    -   Both Branch A (T045a) and Branch B (T045c) must complete before T005 (Manifest) can run.
    -   T045d (Fetch Real Data) depends strictly on T045c. If T045d fails, the pipeline halts.
    -   T005 depends on T049, T050, T006a, T045a, T045c, and T045d.
3.  **Core Implementation**:
    -   T047a, T047b, T047c (Thermo) depend on T006a/T047a chain.
    -   T012 (GB Service) is independent of T047 chain but must complete before T013.
    -   T013 (Surrogate) depends on T047c and T012.
    -   T014 (McLean) depends on T055 and T013.
    -   T018 (Profiles) depends on T014.
4.  **Analysis & Validation**:
    -   T021, T022, T023 (Regression) depend on T018.
    -   T024 (Heatmaps) depends on T018.
    -   T029, T030, T031, T032, T033 (Cross-Validation) depend on T021.
    -   T061, T062, T063, T064 (Validation Prep) depend on T045a/T045d chain.
    -   T060 (SC-003 Validation) depends on T018, T045d (success), T061, T062, T063, T064.
    -   T070, T072, T073, T074 depend on T061/T060 chain.
    -   T071 (Sample Mass) depends on T018, T072, and T045d (success).