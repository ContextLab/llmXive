# Tasks: Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys

**Input**: Design documents from `/specs/001-quantifying-composition-dependent-grain/`
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

## Phase 0: Data Acquisition & Validation (Research)

**Purpose**: Fetch, verify, and document real scientific data sources (CALPHAD, DFT, APT) to satisfy FR-001, FR-002, FR-007, and SC-003. Explicitly handle "No Data" states to prevent pipeline deadlocks.

### Sub-Phase 0.1: Source Verification & Fallback (Research)

- [ ] T045a-Verify [Research] [FR-007] Verify existence of NIST APT accession IDs for binary systems (Fe-Cr, Fe-Mo, Fe-V, Fe-W). **Requirements**:
 1. Query NIST/DOI databases for APT measurements in BCC Fe alloys.
 2. **Constraint**: If verified IDs are found, record them in `research/data_sources.md`.
 3. **Constraint**: If NO verified IDs are found, explicitly record "No verified APT data found" with a citation to the search query and timestamp in `research/data_sources.md`.
 4. **Deliverable**: `research/data_sources.md` with a section "Binary APT Sources" containing specific Accession IDs OR a definitive "No Data" statement.
 **Dependency**: None.

- [ ] T045c-Verify [Research] [FR-007] Verify existence of peer-reviewed literature sources (DOIs) for ternary APT datasets (Fe-Cr-Mo, etc.). **Requirements**:
 1. Search literature for ternary APT measurements.
 2. **Constraint**: If verified DOIs are found, record them in `research/data_sources.md`.
 3. **Constraint**: If NO verified ternary APT data exists, explicitly record "No verified ternary APT data found" and document the search scope in `research/data_sources.md`.
 4. **Deliverable**: `research/data_sources.md` with a section "Ternary APT Sources" containing specific DOIs OR a definitive "No Data" statement.
 **Dependency**: None.

- [ ] T045e-Verify [Research] [FR-001, FR-007] Identify a verified open CALPHAD source (e.g., Zenodo record, NIST database) for TCFE9 parameters. **Requirements**:
 1. Locate a specific DOI/URL for an open CALPHAD parameter set compatible with TCFE9 (e.g., `).
 2. Record the DOI/URL in `research/data_sources.md`.
 3. **Constraint**: Must provide a specific DOI/URL, not a generic "TCFE9" reference.
 4. **Constraint**: If no open source is found, record "No verified open CALPHAD source found" and halt further CALPHAD tasks.
 5. **Deliverable**: `research/data_sources.md` with a section "CALPHAD Source" containing the specific DOI/URL or "No Data".
 **Dependency**: None.

- [ ] T045f-Verify [Research] [FR-002, FR-007] Identify a verified literature dataset (e.g., Materials Project ID, Zenodo record) containing DFT segregation energies. **Requirements**:
 1. Locate a specific DOI/URL for a pre-computed DFT dataset for Fe-Cr, Fe-Mo, etc.
 2. Record the DOI/URL in `research/data_sources.md`.
 3. **Constraint**: Must provide a specific DOI/URL.
 4. **Constraint**: If no dataset is found, record "No verified DFT source found" and halt DFT tasks.
 5. **Deliverable**: `research/data_sources.md` with a section "DFT Source" containing the specific DOI/URL or "No Data".
 **Dependency**: None.

### Sub-Phase 0.2: Data Fetching & Placeholder Generation (Implementation)

- [ ] T045a-Fetch [Research] [FR-007] Fetch APT datasets for binary systems using IDs from T045a-Verify. **Requirements**:
 1. Implement `code/data/fetch_apt_data.py` to download real APT data for binary systems.
 2. Use specific Accession IDs recorded in `research/data_sources.md` by T045a-Verify.
 3. **Constraint**: If T045a-Verify recorded "No verified APT data found", create a placeholder file `data/raw/apt_data/<system>_no_data.json` with `status: "no_data"` and `reason: "no_source_found"`. Do NOT raise a hard error.
 4. **Constraint**: If a network error occurs during fetch, create a placeholder `data/raw/apt_data/<system>_no_data.json` with `status: "no_data"` and `reason: "fetch_failed"`.
 5. **Output**: Save real data to `data/raw/apt_data/<system>_apt.json` OR the placeholder. Update `data_manifest.json` with `source_type: 'experimental'`, `source_id: <accession_id or 'N/A'>`, `doi: <doi or 'N/A'>`, `url: <url or 'N/A'>`.
 **Dependency**: Must run after T045a-Verify.

- [ ] T045c-Fetch [Research] [FR-007] Fetch APT datasets for ternary systems using DOIs from T045c-Verify. **Requirements**:
 1. Implement `code/data/fetch_apt_data.py` (extend existing) to download real APT data for ternary systems.
 2. Use specific DOIs recorded in `research/data_sources.md` by T045c-Verify.
 3. **Constraint**: If T045c-Verify recorded "No verified ternary APT data found", create a placeholder `data/raw/apt_data/<system>_no_data.json` with `status: "no_data"`.
 4. **Constraint**: If fetch fails, create a placeholder with `status: "no_data"`.
 5. **Output**: Save real data or placeholder to `data/raw/apt_data/` and update `data_manifest.json`.
 **Dependency**: Must run after T045c-Verify.

- [ ] T045e-Fetch [Research] [FR-001, FR-007] Fetch Open CALPHAD parameters using DOI from T045e-Verify. **Requirements**:
 1. Implement `code/data/download_calphad.py` to fetch the file using the specific DOI/URL from T045e-Verify.
 2. Verify checksum against the provided hash in `research/data_sources.md`.
 3. **Constraint**: If T045e-Verify recorded "No verified open CALPHAD source found", create `data/raw/calphad_params_no_data.json` with `status: "no_data"`.
 4. **Constraint**: If fetch fails or checksum mismatch, raise a hard error. Do NOT fallback to synthetic parameters.
 5. **Output**: Save to `data/raw/calphad_params.json` (if success) or placeholder (if no source) and update `data_manifest.json`.
 **Dependency**: Must run after T045e-Verify.

- [ ] T045f-Fetch [Research] [FR-002, FR-007] Fetch pre-computed DFT energies using DOI from T045f-Verify. **Requirements**:
 1. Implement `code/data/download_dft_energies.py` to fetch the file using the specific DOI/URL from T045f-Verify.
 2. Verify checksum/DOI.
 3. **Constraint**: If T045f-Verify recorded "No verified DFT source found", create `data/raw/dft_energies_no_data.json` with `status: "no_data"`.
 4. **Constraint**: If fetch fails or checksum mismatch, raise a hard error. Do NOT fallback to synthetic data.
 5. **Output**: Save to `data/raw/dft_energies.json` (if success) or placeholder and update `data_manifest.json`.
 **Dependency**: Must run after T045f-Verify.

- [ ] T090 [Research] Create `data/generate_ground_truth.py`. **Requirements**:
 1. Use `pycalphad` to load TCFE9 parameters (or a verified open subset) from `data/raw/calphad_params.json` (T045e-Fetch).
 2. Read injected interaction coefficients from `research/synthetic_ground_truth.yaml` (created by T090-Config).
 3. Simulate DFT segregation energies using the McLean isotherm with injected coefficients and random noise.
 4. **Constraint**: Do NOT simulate "experimental" APT concentrations. This task is for regression engine validation only.
 5. Save output to `data/raw/generated_ground_truth.csv`.
 6. **Constraint**: Must use a fixed random seed for reproducibility.
 7. **Output**: Write a `data_manifest.json` entry for this file with `source_type: 'generated'`, `source_id: 'generate_ground_truth.py'`, and the script hash.
 **Dependency**: Must run after T045e-Fetch and T090-Config.

- [ ] T090-Config [Research] Create `research/synthetic_ground_truth.yaml`. **Requirements**:
 1. Define exact interaction coefficients (e.g., `beta_CrMo: 0.05 eV`) and random seed for reproducibility.
 2. **Constraint**: All values must be explicitly defined in this file; no hard-coded constants in scripts.
 3. **Deliverable**: `research/synthetic_ground_truth.yaml`.
 **Dependency**: None.

- [ ] T091 [Research] Execute `data/generate_ground_truth.py` to create `data/raw/generated_ground_truth.csv`. **Constraint**: Verify checksum of output file. **Dependency**: Must run after T090.

- [ ] T092 [Research] Update `data_manifest.json` to include the generated ground truth dataset with its checksum and generation parameters. **Dependency**: Must run after T091.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create `scripts/setup_project.py` with explicit directory definitions for `projects/PROJ-448-quantifying-composition-dependent-grain-/`, `code/`, `data/`, `tests/`, `research/`, `data/figures/`, and `data/processed/`. The script MUST create these directories if they do not exist.
- [X] T001b Execute `scripts/setup_project.py` to create the full directory tree as defined in T001a.
- [X] T002a Create `requirements.txt` at `projects/PROJ-448-quantifying-composition-dependent-grain-/` with dependencies: `pymatgen`, `ase`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `pycalphad`, `pyyaml`, `requests`, `memory_profiler`, `ruff`, `black`, `quantum-espresso-runner` (mock/placeholder for CI).
- [X] T002b Run `pip install -r requirements.txt` to install dependencies.
- [X] T003 [P] Configure linting (ruff/flake) and formatting (black) tools in `pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008a Create `code/__init__.py` with a minimal logger setup that does NOT depend on `config.py`. **Purpose**: Provide a basic logger for early initialization scripts. **Dependency**: None.
- [X] T004 [P] Create `code/config.py` to define paths, random seeds, and temperature ranges (K to elevated temperatures in increments), and alloy system constants. **Dependency**: Must run after T008a.
- [X] T008b [P] Configure error handling and logging infrastructure in `code/__init__.py` using the constants defined in `code/config.py`. **Dependency**: Must run after T004.
- [X] T049 [P] Implement `code/data/manifest_validator.py` to verify that all data sources in `data_manifest.json` possess valid DOI or URL fields (or `source_id` for generated data) as required by FR-007. If a source lacks these, the validator MUST raise an error.
- [X] T050 [P] Create `code/data/manifest_schema.json` defining the strict schema for `data_manifest.json` including `source_type`, `source_id`, `doi`, `url`, and `checksum` fields.
- [ ] T047b [P] [FR-001] [Edge Cases] Implement `code/services/thermo_extrapolator.py` to handle missing thermodynamic parameters in the CALPHAD database. **Requirement**: Use `scipy.interpolate.interpd` or `numpy.polyfit` for linear extrapolation of missing parameters in the 500-900K range. **Constraint**: Do NOT use `sklearn.linear_model.LinearRegression` for this specific extrapolation task; use dedicated interpolation libraries to avoid conceptual confusion and ensure thermodynamic consistency. **Constraint**: This task is a FALLBACK mechanism for missing parameters, not the primary extraction logic. **Dependency**: Must run after T050 and T045e-Fetch.
- [ ] T047c [P] Execute and validate `code/services/thermo_extrapolator.py` on a sample set of missing parameters. **Requirement**: Verify that extrapolated values are physically plausible and consistent with TCFE9 trends. **Dependency**: Must run after T047b.
- [X] T005 [P] [FR-007] Validate the final `data_manifest.json`. **Requirements**:
 1. Run `manifest_validator.py` (T049) against the combined manifest (created by T045a-Fetch, T045c-Fetch, T045e-Fetch, T045f-Fetch, T092).
 2. Ensure all real data sources have valid DOIs/URLs.
 3. **Constraint**: If validation fails, the process MUST terminate with an error.
 **Dependency**: Must run after T045a-Fetch, T045c-Fetch, T045e-Fetch, T045f-Fetch, T092, T049, T050.
- [X] T007 [P] Define `code/models/` directory structure and base entity schemas for `SegregationProfile`, `AlloySystem`, and `RegressionModel`. **Output**: Create `code/models/schemas.py` with Pydantic models for `SegregationProfile`, `AlloySystem`, and `RegressionModel`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Thermodynamic Segregation Profile Generation (Priority: P1) 🎯 MVP

**Goal**: Compute equilibrium segregation energies and concentrations for BCC alloy systems using pre-computed DFT values (Real Data) and the McLean isotherm model.

**Independent Test**: Run the computation pipeline on Fe-Cr at elevated temperatures and verify the output file contains valid segregation energy (eV) and equilibrium concentration (atomic fraction) derived from the McLean equation using REAL DFT data.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for McLean isotherm calculation in `tests/unit/test_mclean.py`.
- [X] T011 [P] [US1] Integration test for data loading and profile generation in `tests/integration/test_us1_profile.py`.

### Implementation for User Story 1

- [X] T001c [P] [FR-002] Implement `code/services/gb_service.py` to generate symmetric tilt grain boundary supercells using `pymatgen` from MP-13 seed. **Dependency**: Must run after T004.
- [ ] T017 [US1] [FR-002-PLACEHOLDER] **Mock/Stub** Implement `code/services/dft_service.py` to simulate the interface for Quantum ESPRESSO DFT calculations. **Constraint**: **HPC-ONLY**. This task MUST be skipped in the CI environment. **Requirements**:
 1. Define supercell geometry: Σ5 tilt grain boundary, 36.9° misorientation angle.
 2. Input format: PWscf input files (template only).
 3. **Constraint**: If running in CI environment (check `CI` env var), log "SKIPPED: HPC-ONLY" and exit successfully. Do NOT attempt to run DFT.
 4. **Deliverable**: Create `research/templates/fe_cr_gb.pwscf` as a template file and `data/raw/supercell_template.pwscf` as the output.
 5. **Dependency**: Must run after T001c.
- [ ] T017a [Review-Response] [FR-002] Create `research/fr002_deviation.md`. **Requirements**:
 1. Explicitly document the deviation from the spec's "compute segregation energies using Quantum ESPRESSO" requirement.
 2. Justify the use of pre-computed DFT data (T045f-Fetch) and the "Reduced CALPHAD Parameter Set" due to CI constraints (no GPU, 6h limit).
 3. State that the pipeline logic is validated against literature data, and the "compute" step is deferred to HPC resources in a separate branch.
 4. **Constraint**: This document MUST reference the `research/spec_amendment_fr002.md` artifact as the Single Source of Truth for the deviation.
 **Dependency**: Must run after T017b.
- [ ] T017b [Review-Response] [FR-002] Create `research/spec_amendment_fr002.md`. **Requirements**:
 1. Create a formal "Spec Amendment" artifact explicitly documenting the deviation from FR-002.
 2. State that for CI execution, FR-002 is amended to "Load pre-computed DFT energies from verified literature sources" instead of "compute using Quantum ESPRESSO".
 3. Justify this amendment based on CI hardware constraints and the need for a runnable pipeline.
 4. **Constraint**: This document serves as the Single Source of Truth for the deviation, aligning Spec and Plan.
 **Dependency**: None.
- [ ] T013 [US1] [FR-002, FR-007] Implement `code/services/surrogate_service.py` to compute literature-calibrated segregation energies. **Input**: Load REAL DFT energies from `data/raw/dft_energies.json` (fetched by T045f-Fetch) via `code/data/load_dft_energies.py` (T013b). **Constraint**: This task MUST NOT implement or call any real DFT code. It MUST load the pre-computed energies from the REAL dataset (T045f-Fetch). **Constraint**: If `data/raw/dft_energies.json` is missing, the script MUST raise a hard error. Do NOT fallback to synthetic data (T091). **Constraint**: T013 does NOT depend on T017 (HPC-ONLY). **Dependency**: Must run after T045f-Fetch and T013b.
- [X] T055 [US1] Implement validation in `code/services/surrogate_service.py` to ensure surrogate inputs align with the supercell geometry generated by `gb_service.py`. **Dependency**: Must run after T001c and T013.
- [ ] T013b [P] [FR-002] Implement `code/data/load_dft_energies.py` to load pre-computed DFT energies from `data/raw/dft_energies.json`. **Requirements**:
 1. Load the JSON file fetched by T045f-Fetch.
 2. Validate the schema (keys: `system`, `energy_eV`, `temperature`).
 3. Raise an error if the file is missing or malformed.
 **Dependency**: Must run after T045f-Fetch.
- [ ] T014 [US1] [FR-003] Implement `code/models/mclean.py` to calculate equilibrium concentrations from segregation energy and bulk composition. **Requirements**:
 1. Implement the core McLean isotherm equation.
 2. Cap equilibrium concentration at 1.0 and return a "saturation" flag if the calculated value exceeds 1.0.
 3. Add logging using the logger from `code/config.py`. Messages: "Calculated segregation energy: {value} eV", "Applied McLean isotherm", "Equilibrium concentration: {value}", "Saturation flag: {flag}".
 **Dependency**: Must run after T013b.
- [ ] T018 [US1] Generate `data/processed/segregation_profiles.json` containing computed profiles for the ternary systems under investigation. **Dependency**: Must run after T014.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multicomponent Cooperative Effect Analysis (Priority: P2)

**Goal**: Analyze segregation profiles to identify non-linear thresholds and cooperative effects where multiple solutes amplify segregation.

**Independent Test**: Run analysis on the pre-computed ternary dataset and verify the regression model with interaction terms identifies at least one statistically significant interaction coefficient (p<0.05) and demonstrates >10% MSE reduction on a held-out test set compared to a purely additive binary model.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for interaction term generation in `tests/unit/test_regression.py`.
- [ ] T020 [P] [US2] Integration test for cooperative effect detection in `tests/integration/test_us2_cooperative.py`.

### Implementation for User Story 2

- [ ] T021a [US2] [FR-004] Generate interaction terms for regression. **Requirements**:
 1. Use `sklearn.preprocessing.PolynomialFeatures(degree=2, include_bias=False)` to generate interaction terms (e.g., Cr*Mo, Cr*V).
 2. **Constraint**: If `sklearn` is unavailable, manual implementation of interaction terms is permitted provided the mathematical result is identical.
 3. **Deliverable**: Generate `data/processed/interaction_terms.csv` with columns [Cr, Mo, Cr*Mo,...].
 **Dependency**: Must run after T018.
- [ ] T021b [US2] [FR-004] Implement `code/models/regression.py` to fit linear models with interaction terms. **Library**: Use `sklearn.linear_model.LinearRegression`. **Dependency**: Must run after T021a.
- [ ] T022 [US2] [FR-004] Implement logic to compare MSE of interaction model vs. additive binary null hypothesis, requiring >10% MSE reduction to confirm cooperative effects. **Output**: Log "MSE reduction: X% (Threshold: 10%)" and raise warning if threshold not met. **Dependency**: Must run after T021b.
- [ ] T023 [US2] [FR-004] Implement significance testing (p-value < 0.05) for interaction coefficients. **Dependency**: Must run after T021b.
- [ ] T024a [US2] [FR-006] Implement `code/services/plotter.py` to generate heatmaps visualizing segregation energy vs. bulk composition and temperature. **Requirements**:
 1. Input: `data/processed/segregation_profiles.json` (T018).
 2. Output: `data/figures/segregation_heatmap.png` (T024b).
 3. Mapping: x=bulk_concentration, y=temperature, z=segregation_energy.
 4. Style: Use `cmap=viridis` and `norm=Normalize` (symmetric range to handle negative values). Do NOT use `LogNorm`.
 **Dependency**: Must run after T018.
- [ ] T024b [US2] [FR-006] Integrate the plotting logic from T024a to generate `data/figures/segregation_heatmap.png`. **Dependency**: Must run after T024a and T018.
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

- [ ] T029 [P] [US3] [FR-005] Implement `code/models/validation.py` to perform k-fold cross-validation on composition/temperature data points. **Dependency**: Must run after T021b.
- [ ] T030 [US3] [FR-005] Calculate and report R² and MSE for each fold, plus mean and standard deviation. **Output**: Log "Mean R²: X, Std Dev: Y" and flag if Std Dev > 0.05. **Dependency**: Must run after T029.
- [ ] T031 [US3] Perform transferability check: train on Fe-Cr-Mo, test on held-out Fe-Cr-V subset (if applicable). **Dependency**: Must run after T029.
- [ ] T032 [US3] Add overfitting detection logic (high training/low validation score) and flagging. **Dependency**: Must run after T030.
- [ ] T033 [US3] Generate `data/processed/cross_validation_results.json` with full metrics and fold details. **Dependency**: Must run after T030.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Experimental Strategy (Priority: P1 - Research Review)

**Goal**: Address SC-003: Validate computed segregation energies against experimental literature values (APT) and document the experimental plan.

**Independent Test**: A validation document `research/validation_report.md` is generated that explicitly compares model predictions (derived from REAL DFT) against REAL APT data, and details the experimental apparatus (APT) parameters required for final scientific acceptance.

### Implementation for Validation Strategy

- [ ] T095a-Check [Validation] [SC-003] Check for presence of APT data in `data/raw/apt_data/` (from T045a-Fetch, T045c-Fetch). **Requirements**:
 1. Iterate through all expected binary and ternary systems.
 2. **Constraint**: If a system-specific 'no_data' placeholder exists (e.g., `ternary_no_data.json` or `Fe-V_no_data.json`), log "Validation Skipped: No Data for <system>" and record status in `data/processed/validation_status.json`.
 3. **Deliverable**: Create `data/processed/validation_status.json` with entries for each system: `{"system": "Fe-Cr", "status": "data_present"}` or `{"system": "Fe-Cr-Mo", "status": "no_data"}`.
 **Dependency**: Must run after T018 (Real Profiles) and T045a-Fetch, T045c-Fetch.

- [ ] T095a-Compare [Validation] [SC-003] Perform Experimental Validation (SC-003) for available data. **Requirements**:
 1. Read `data/processed/validation_status.json` (T095a-Check).
 2. **Constraint**: If a system has `status: "no_data"`, skip comparison and generate an empty result file for that system.
 3. Compare computed profiles (from T018, derived from REAL DFT T045f-Fetch) against REAL APT data for binary systems (Fe-Cr, Fe-Mo, etc.) where data exists.
 4. Compute deviation (RMSE/MAE) between model predictions and APT measurements.
 5. Write results to `data/processed/sc003_deviation.json`.
 6. **Constraint**: If binary APT data is missing (indicated by a 'no_data' placeholder or missing file), log "Validation Skipped: No Binary APT Data for <system>" and produce an empty result file with `status: "no_data"` for that system. Do NOT crash.
 **Dependency**: Must run after T095a-Check and T018.

- [ ] T095d [Validation] [SC-003] Generate Ternary Validation Skip Report. **Requirements**:
 1. Check `data/processed/validation_status.json` (T095a-Check) for ternary systems with `status: "no_data"`.
 2. If ternary data is missing, generate `data/processed/sc003_ternary_skip_report.json` explicitly stating: "Ternary APT data unavailable for SC-003 validation. Validation limited to binary systems."
 3. Include a reference to the search results in `research/data_sources.md` (T045c-Search) that confirmed the absence of data.
 4. **Constraint**: This task satisfies the "skip and document" path for SC-003 when data is missing. Generating this report is a VALID SUCCESS OUTCOME for SC-003 in the absence of data.
 **Dependency**: Must run after T095a-Check.

- [ ] T095c [Validation] [SC-003] Perform Binary Experimental Validation. **Requirements**:
 1. Explicitly compare computed binary segregation profiles (from T018) against REAL APT literature values (from T045a-Fetch) for Fe-Cr, Fe-Mo, Fe-V, Fe-W.
 2. Check for 'no_data' placeholders for each binary system. If a placeholder exists, log "Skipped: No Data" and record in output.
 3. Calculate RMSE/MAE for each binary system where data exists.
 4. Write results to `data/processed/sc003_binary_validation.json`.
 5. **Constraint**: This task is the primary source of SC-003 validation for the available data.
 **Dependency**: Must run after T095a-Check and T018.

- [ ] T096 [Validation] Write `research/validation_report.md` summarizing the parameter recovery results (T095b), the experimental validation results (T095a-Compare, T095c, T095d), statistical significance, and confirmation of the surrogate model's validity. **Dependency**: Must run after T095a-Compare, T095c, T095d.

- [ ] T095b [Validation] [PIPELINE-VALIDATION] Compare regression coefficients against "injected ground truth" (T091) for pipeline logic verification only. **Constraint**: This task is for **PIPELINE VALIDATION ONLY** and must be clearly labeled as such. It does NOT satisfy SC-003. **Dependency**: Must run after T025 and T091.

- [ ] T100 [Validation] [Review-Response] Create `research/experimental_validation_plan.md` to address the "Direct Measurement" requirement. **Requirements**:
 1. Specify **Atom Probe Tomography (APT)** as the primary apparatus for measuring segregation at the atomic scale.
 2. Define the **minimum detectable concentration** (e.g., 0.1 at.%) and the **detection limit** for trace elements (Cr, Mo, V, W) at grain boundaries.
 3. Estimate the **quantity of material** required (e.g., needle-shaped specimens of ~100nm diameter) and the preparation method (FIB lift-out).
 4. Cite specific literature (DOIs) where APT has successfully measured similar segregation in BCC Fe alloys.
 5. Explicitly state that while the current CI pipeline uses a surrogate, this plan defines the *physical* validation step required for final scientific acceptance.
 **Dependency**: None (can run in parallel with T095a-Check, but must be included in the final report).

**Checkpoint**: Validation strategy is documented, the project acknowledges the redefined success criterion, and the experimental gap identified by the reviewer is explicitly addressed.

---

## Phase 7: Review Response & Documentation (Priority: P1 - Research Review)

**Goal**: Explicitly address the reviewer's concern regarding the "Direct Measurement" of segregation energies and the definition of the experimental apparatus.

### Implementation for Review Response

- [ ] T101 [Review-Response] [FR-007, SC-003] Update `research/data_sources.md` to include a dedicated section "Experimental Validation Apparatus". **Requirements**:
 1. Describe the **Atom Probe Tomography (APT)** setup in detail: laser pulse frequency, wavelength, sample temperature (cryogenic vs. room), and detection efficiency.
 2. Specify the **minimum detectable concentration** for Cr, Mo, V, and W at the grain boundary interface (e.g., 0.1 at.%).
 3. Document the **sample preparation** workflow: FIB lift-out parameters, annular milling steps, and final polishing voltage to ensure grain boundary integrity.
 4. Include a table of **literature DOIs** for APT studies on BCC Fe alloys that successfully resolved similar segregation phenomena.
 5. **Constraint**: This section must not rely on computational data; it must define the *physical* measurement capability.
 **Dependency**: None.

- [ ] T102 [Review-Response] [FR-007] Update `research/experimental_validation_plan.md` to include a "Detection Limit Analysis". **Requirements**:
 1. Calculate the theoretical detection limit for the specified APT setup based on literature sensitivity factors.
 2. Compare this limit against the predicted segregation concentrations from the McLean model (T018).
 3. **Constraint**: If the predicted concentration is below the detection limit, explicitly state "Below Detection Limit" and propose a strategy (e.g., lower temperature, higher bulk concentration) to bring the signal within range.
 4. **Dependency**: Must run after T101 (Apparatus Definition) AND T018 (Predicted Concentrations).
 **Dependency**: Must run after T101 and T018.

- [ ] T103 [Review-Response] [FR-007] Revise `research/validation_report.md` to include a "Gap Analysis" section. **Requirements**:
 1. Compare the current computational results (surrogate) with the proposed experimental plan.
 2. Explicitly state: "This project validates the *methodology* of detecting non-linearity. The *quantitative* validation of segregation energies requires the experimental apparatus defined in T100/T101."
 3. **Constraint**: Do not claim the computational results are "verified" without the experimental data. Use language like "consistent with" or "predicted by".
 4. **Dependency**: Must run after T102 (Detection Limit) AND T096 (Validation Report).
 **Dependency**: Must run after T102 and T096.

**Checkpoint**: The project now explicitly addresses the reviewer's concern about the lack of experimental apparatus definition and provides a clear path to physical validation.

---

## Dependencies & Execution Order

The execution order is strictly enforced as follows:

1. **Foundation Chain**: T001a → T001b → T002a → T002b → T003 → T008a → T004 → T008b → T049 → T050 → T047b → T047c → T005 (Validation) → T007.
2. **Data Acquisition Chain**:
 - T045a-Verify, T045c-Verify, T045e-Verify, T045f-Verify (Research) run in parallel.
 - T045a-Fetch, T045c-Fetch, T045e-Fetch, T045f-Fetch (Fetch) run in parallel after their respective Verify tasks.
 - T090-Config (Config) is independent.
 - T090 (Synthetic Gen) depends on T045e-Fetch and T090-Config.
 - T091 (Synthetic Exec) depends on T090.
 - T092 (Synthetic Manifest) depends on T091.
 - T005 (Manifest Validation) depends on T045a-Fetch, T045c-Fetch, T045e-Fetch, T045f-Fetch, T092.
3. **Core Implementation**:
 - T001c (GB Service) is independent.
 - T017 (DFT Service) depends on T001c (HPC-Only).
 - T017b (Spec Amendment) is independent.
 - T017a (Deviation Doc) depends on T017b.
 - T013b (DFT Loader) depends on T045f-Fetch.
 - T013 (Surrogate Service) depends on T045f-Fetch and T013b. **CRITICAL**: T013 does NOT depend on T001c.
 - T014 (McLean Physics) depends on T013b.
 - T018 (Profiles) depends on T014.
 - T055 (Validation) depends on T001c and T013.
4. **Analysis & Validation**:
 - T021a (Interactions) depends on T018.
 - T021b (Regression) depends on T021a.
 - T022, T023 (Stats) depend on T021b.
 - T024a (Plotting) depends on T018.
 - T024b (Plotting Integration) depends on T024a and T018.
 - T029, T030, T031, T032, T033 (Cross-Validation) depend on T021b.
 - T095a-Check (Check Data) depends on T018 and T045a-Fetch, T045c-Fetch.
 - T095d (Ternary Skip) depends on T095a-Check.
 - T095a-Compare (Compare) depends on T095a-Check and T018.
 - T095c (Binary Validation) depends on T095a-Check and T018.
 - T095b (Synthetic Validation) depends on T025 and T091.
 - T096 (Report) depends on T095a-Compare, T095c, T095d.
 - T100 (Experimental Plan) is independent but must be completed before final project closure.
5. **Review Response Chain**:
 - T101 (Apparatus Definition) depends on None.
 - T102 (Detection Limit) depends on T101 and T018.
 - T103 (Gap Analysis) depends on T102 and T096.