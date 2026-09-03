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

**Purpose**: Fetch, verify, and document real scientific data sources (CALPHAD, DFT, APT) to satisfy FR-001, FR-002, FR-007, and SC-003. **Hard Fail**: If a verified source is not found for core data, the pipeline MUST halt with a clear error. No placeholders allowed for core scientific data.

### Sub-Phase 0.1: Source Search & Verification (Research)

- [ ] T001-Search [Research] [FR-007] [US-1] **Search for candidate data sources**. **Requirements**:
 1. **Action**: Create `research/candidate_sources.json` by performing **live API searches** against Zenodo, NIST, Materials Project, and CrossRef.
 2. **Constraint**: Search for binary APT IDs, ternary APT DOIs, CALPHAD DOIs, and DFT DOIs using keywords: "Fe-Cr APT", "Fe-Cr-Mo segregation", "TCFE9 parameters", "DFT segregation energy BCC".
 3. **Constraint**: Do NOT guess IDs. If a search returns no results, record an empty list `[]` and log the query used.
 4. **Constraint**: If specific IDs are unknown, leave them as empty lists; the task is to FIND them via search, not guess them.
 5. **Deliverable**: `research/candidate_sources.json` with keys: `binary_apt_ids`, `ternary_apt_dois`, `calphad_dois`, `dft_dois`.
 **Dependency**: None.

- [ ] T002-Verify [Research] [FR-007] [US-1] Create `code/data/verify_sources.py` to validate candidate IDs/DOIs. **Requirements**:
 1. **Constraint**: Do NOT perform live API searches in the script creation phase. The script MUST be designed to validate a pre-provided list of candidate IDs/DOIs in `research/candidate_sources.json` (output of T001-Search) against Zenodo/NIST/CrossRef APIs.
 2. **Constraint**: If verified IDs/DOIs are found, the script MUST record them in `research/data_sources.md`.
 3. **Constraint**: If NO verified IDs are found, the script MUST record "No verified source found" with a citation to the search query (from T001-Search) and timestamp in `research/data_sources.md`.
 4. **Constraint**: If "No verified source found", the script MUST NOT halt the pipeline; it MUST set a flag to trigger the fallback path (only for non-core data).
 5. **Deliverable**: `code/data/verify_sources.py`.
 **Dependency**: Must run after T001-Search.

- [ ] T003-Record [Research] [FR-007] [US-1] Execute `code/data/verify_sources.py` to verify ALL sources (Binary APT, Ternary APT, CALPHAD, DFT). **Requirements**:
 1. Run `python code/data/verify_sources.py`.
 2. **Constraint**: If verified IDs are found, record them in `research/data_sources.md`.
 3. **Constraint**: If NO verified ID found for a source, record "No verified source found" in `research/data_sources.md`.
 4. **Constraint**: If "No verified source found" for CALPHAD or DFT, the pipeline MUST proceed to fallback tasks (T045e-Gen, T045f-Gen) but MUST NOT proceed to scientific analysis until a source is found or a formal amendment is created.
 5. **Deliverable**: Updated `research/data_sources.md` with all sections.
 **Dependency**: Must run after T002-Verify and T001-Search.

- [ ] T017b-Config [Research] [FR-002] [Constitution VI] Create the content for `research/spec_amendment_fr002.md`. **Requirements**:
 1. Create the content string for the "Spec Amendment" artifact explicitly documenting the deviation from FR-002.
 2. State that for CI execution, FR-002 is amended to "Load pre-computed DFT energies from verified literature sources" instead of "compute using Quantum ESPRESSO".
 3. Justify this amendment based on CI hardware constraints and the need for a runnable pipeline.
 4. **Constraint**: This document serves as the Single Source of Truth for the deviation, aligning Spec and Plan.
 5. **Template**: The content MUST contain the following text verbatim:
 "This project deviates from FR-002 due to CI hardware constraints. Instead of running Quantum ESPRESSO, it loads pre-computed DFT energies from [SOURCE_DOI_PLACEHOLDER]. This deviation is justified by the need for a runnable pipeline on free-tier hardware."
 6. **Constraint**: Replace [SOURCE_DOI_PLACEHOLDER] with the actual DOI from `research/data_sources.md` (output of T003-Record) **after T003-Record has executed**.
 7. **Deliverable**: Content string for `research/spec_amendment_fr002.md`.
 **Dependency**: Must run after T003-Record.

- [ ] T017b-Script [Research] [FR-002] [Constitution VI] Create `code/data/write_spec_amendment.py`. **Requirements**:
 1. Create a script that takes the content string from T017b-Config and writes it to `research/spec_amendment_fr002.md`.
 2. **Constraint**: The script MUST NOT modify the spec.md file directly; it MUST write to the amendment artifact.
 3. **Deliverable**: `code/data/write_spec_amendment.py`.
 **Dependency**: Must run after T017b-Config.

- [ ] T017b-Exec [Research] [FR-002] [Constitution VI] Execute `code/data/write_spec_amendment.py` to create `research/spec_amendment_fr002.md`. **Requirements**:
 1. Run `python code/data/write_spec_amendment.py`.
 2. **Constraint**: Verify that `research/spec_amendment_fr002.md` exists and contains the required text.
 3. **Deliverable**: `research/spec_amendment_fr002.md`.
 **Dependency**: Must run after T017b-Script and T017b-Config.

- [ ] T017b-Update [Research] [FR-002] [Constitution VI] Update `plan.md` to reflect the amendment. **Requirements**:
 1. Append a note to `plan.md` stating: "FR-002 amended for CI: DFT computation replaced by pre-computed data loading (see research/spec_amendment_fr002.md)."
 2. **Constraint**: This ensures the Single Source of Truth is maintained.
 3. **Deliverable**: Updated `plan.md`.
 **Dependency**: Must run after T017b-Exec.

### Sub-Phase 0.2: Data Fetching (Implementation)

- [ ] T045a-Fetch [Research] [FR-007] Fetch APT datasets for binary systems (Fe-Cr, Fe-Mo, Fe-V, Fe-W) using IDs from T003-Record. **Requirements**:
 1. Implement `code/data/fetch_apt_data.py` to download real APT data for binary systems.
 2. Use specific Accession IDs recorded in `research/data_sources.md` by T003-Record.
 3. **Constraint**: If T003-Record recorded "No verified APT data found", the task MUST NOT raise an exception. It MUST record a status "no_data" in `data/processed/validation_status.json` and **continue** the pipeline.
 4. **Constraint**: If a network error occurs during fetch, the task MUST raise a `FetchError` and halt execution.
 5. **Output**: Save real data to `data/raw/apt_data/<system>_apt.json`. Update `data_manifest.json` with `source_type: 'experimental'`, `source_id: <accession_id>`, `doi: <doi>`, `url: <url>`.
 **Dependency**: Must run after T003-Record.

- [ ] T045c-Fetch [Research] [FR-007] Fetch APT datasets for ternary systems (Fe-Cr-Mo, etc.) using DOIs from T003-Record. **Requirements**:
 1. Extend `code/data/fetch_apt_data.py` to download real APT data for ternary systems.
 2. Use specific DOIs recorded in `research/data_sources.md` by T003-Record.
 3. **Constraint**: If T003-Record recorded "No verified ternary APT data found", the task MUST NOT raise an exception. It MUST record a status "no_data" in `data/processed/validation_status.json` and **continue** the pipeline.
 4. **Constraint**: If fetch fails, the task MUST raise a `FetchError` and halt execution.
 5. **Output**: Save real data to `data/raw/apt_data/` and update `data_manifest.json`.
 **Dependency**: Must run after T003-Record.

- [ ] T045e-Fetch [Research] [FR-001] [FR-007] Fetch Open CALPHAD parameters using DOI from T003-Record. **Requirements**:
 1. Implement `code/data/download_calphad.py` to fetch the file using the specific DOI/URL from T003-Record.
 2. Verify checksum against the provided hash in `research/data_sources.md`.
 3. **Constraint**: If T003-Record recorded "No verified open CALPHAD source found", the task MUST NOT raise an exception. It MUST record a status "no_data" in `data/processed/validation_status.json` and **continue** the pipeline.
 4. **Constraint**: If fetch fails or checksum mismatch, the task MUST raise a `FetchError` and halt execution.
 5. **Output**: Save to `data/raw/calphad_params.json`. Update `data_manifest.json`.
 **Dependency**: Must run after T003-Record.

- [ ] T045f-Fetch [Research] [FR-002] [FR-007] Fetch pre‑computed DFT energies using DOI from T003-Record. **Requirements**:
 1. Implement `code/data/download_dft_energies.py` to fetch the file using the specific DOI/URL from T003-Record.
 2. Verify checksum/DOI.
 3. **Constraint**: If T003-Record recorded "No verified DFT source found", the task MUST trigger T045f-Gen (fallback) and **not** raise an exception to the pipeline.
 4. **Constraint**: If fetch fails or checksum mismatch, the task MUST raise a `FetchError` and halt execution.
 5. **Output**: Save to `data/raw/dft_energies.json`. Update `data_manifest.json`.
 **Dependency**: Must run after T003-Record.

- [ ] T045f-Gen [Research] [FR-002] [FR-007] Generate a minimal `data/raw/dft_energies.json` with a 'MISSING_SOURCE' flag if fetch fails. **Requirements**:
 1. Create `code/data/generate_fallback_dft.py`.
 2. If T045f-Fetch failed or T003-Record found no source, run this script to create a minimal JSON file with `source_type: 'fallback'`, `source_id: 'missing_source'`, and a flag `MISSING_SOURCE: true`.
 3. **Constraint**: This task MUST NOT generate fake physics data; it MUST only create a placeholder to allow the pipeline to proceed to the 'No Data' fallback logic.
 4. **Output**: Save to `data/raw/dft_energies.json`. Update `data_manifest.json`.
 **Dependency**: Must run after T045f-Fetch.

- [ ] T090-Config [Research] [FR-001] Create `research/synthetic_ground_truth.yaml` with injection parameters. **Requirements**:
 1. Create the file `research/synthetic_ground_truth.yaml` with a YAML structure containing `interaction_coefficients` (default: {Cr_Mo: 0.05, Cr_V: 0.05,...}) and `random_seed` (default: 42).
 2. **Constraint**: This file MUST be created before T090-Script runs.
 3. **Deliverable**: `research/synthetic_ground_truth.yaml`.
 **Dependency**: None.

- [ ] T090-Script [Research] [FR-001] Create `data/generate_ground_truth.py`. **Requirements**:
 1. Create the script file `data/generate_ground_truth.py`.
 2. Use `pycalphad` to load TCFE9 parameters (or verified open subset) from `data/raw/calphad_params.json` (T045e‑Fetch).
 3. Read injected interaction coefficients from `research/synthetic_ground_truth.yaml` **after T090-Config has executed**.
 4. Simulate DFT segregation energies using the McLean isotherm with injected coefficients and random noise.
 5. **Constraint**: Do NOT simulate "experimental" APT concentrations. This task is for regression engine validation only.
 6. **Constraint**: Must use a fixed random seed for reproducibility.
 7. **Output**: Write a `data_manifest.json` entry for this file with `source_type: 'generated'`, `source_id: 'generate_ground_truth.py'`, and the script hash.
 **Dependency**: Must run after T045e‑Fetch and T090‑Config.

- [ ] T091-Exec [Research] Execute `data/generate_ground_truth.py` to create `data/raw/generated_ground_truth.csv`. **Requirements**:
 1. Run `python data/generate_ground_truth.py`.
 2. Verify checksum of output file matches the value in `research/synthetic_ground_truth.yaml`.
 3. **Constraint**: If checksum mismatch, re-run with debug logging.
 **Dependency**: Must run after T090-Script and T090-Config.

- [ ] T092-ManifestUpdate [Research] [FR-007] Update `data_manifest.json` to include the generated ground truth dataset. **Requirements**:
 1. Add an entry for `data/raw/generated_ground_truth.csv` with `source_type: 'generated'`, `source_id: 'generate_ground_truth.py'`, and the checksum.
 2. **Constraint**: This update must be atomic and verified.
 **Dependency**: Must run after T091-Exec.

- [ ] T048-Script [Research] [FR-001] [US-1] Create `code/services/thermo_extractor.py`. **Requirements**:
 1. Create the script file `code/services/thermo_extractor.py`.
 2. Use `pycalphad` to load `data/raw/calphad_params.json` (output of T045e‑Fetch).
 3. Compute equilibrium bulk compositions for Fe‑Cr‑Mo, Fe‑Cr‑V, Fe‑Mo‑V, Fe‑Cr‑W, Fe‑Mo‑W across a representative range of temperatures and bulk Cr concentrations spanning low to moderate values.
 4. Handle missing parameters via `code/services/thermo_extrapolator.py` (T047b) with warnings.
 5. Save results to `data/processed/equilibrium_compositions.csv`.
 6. Update `data_manifest.json` with entry `source_type: 'derived'`, `source_id: 'equilibrium_compositions'`.
 **Dependency**: Must run after T045e‑Fetch (and after T047b if extrapolation needed).

- [ ] T048-Orchestrate [Research] [FR-001] [US-1] Create `code/services/thermo_orchestrator.py` to run the extraction and extrapolation loop for ALL required ternary systems. **Requirements**:
 1. Create the script file `code/services/thermo_orchestrator.py`.
 2. This script MUST iterate through all required ternary systems (Fe-Cr-Mo, Fe-Cr-V, Fe-Mo-V, Fe-Cr-W, Fe-Mo-W) and invoke T047b (extrapolator) for every missing parameter instance before committing data.
 3. **Constraint**: This task ensures T047b is run for *every* missing parameter instance before T048 runs, preventing incomplete data.
 4. **Deliverable**: `code/services/thermo_orchestrator.py`.
 **Dependency**: Must run after T048-Script and T047b.

- [ ] T048-Exec [Research] [FR-001] [US-1] Execute `code/services/thermo_orchestrator.py` to generate `data/processed/equilibrium_compositions.csv`. **Requirements**:
 1. Run `python code/services/thermo_orchestrator.py`.
 2. Verify that `data/processed/equilibrium_compositions.csv` is generated and non-empty.
 **Dependency**: Must run after T048-Orchestrate and T045e‑Fetch.

- [ ] T049b-Lookup [Research] [FR-002] [US-1] Create `code/services/supercell_lookup.py`. **Requirements**:
 1. Create the script file `code/services/supercell_lookup.py`.
 2. Implement a lookup function that maps supercell identifiers (e.g., `sigma5_fe_cr.cif`) to corresponding entries in `data/raw/dft_energies.json`.
 3. Raise an informative `KeyError` if no matching DFT entry exists.
 **Dependency**: Must run after T001c and T045f-Fetch/T045f-Gen.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001a Create `scripts/setup_project.py` with explicit directory definitions for `projects/PROJ-448-quantifying-composition-dependent-grain-/`, `code/`, `data/`, `tests/`, `research/`, `data/figures/`, and `data/processed/`. The script MUST create these directories if they do not exist.
- [X] T001b Execute `scripts/setup_project.py` to create the full directory tree as defined in T001a.
- [X] T002a Create `requirements.txt` at `projects/PROJ-448-quantifying-composition-dependent-grain-/` with dependencies: `pymatgen`, `ase`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `pycalphad`, `pyyaml`, `requests`, `memory_profiler`, `ruff`, `black`, `quantum-espresso-runner` (mock/placeholder for CI).
- [X] T002b Run `pip install -r requirements.txt` to install dependencies.
- [X] T003 [P] Configure linting (ruff/flake) and formatting (black) tools in `pyproject.toml`.

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T008a Create `code/__init__.py` with a minimal logger setup that does NOT depend on `config.py`. **Purpose**: Provide a basic logger for early initialization scripts. **Dependency**: None.
- [X] T004 [P] Create `code/config.py` to define paths, random seeds, and temperature ranges (K to elevated temperatures in increments), and alloy system constants. **Dependency**: Must run after T008a.
- [X] T008b [P] Configure error handling and logging infrastructure in `code/__init__.py` using the constants defined in `code/config.py`. **Dependency**: Must run after T004.
- [X] T049 [P] Implement `code/data/manifest_validator.py` to verify that all data sources in `data_manifest.json` possess valid DOI or URL fields (or `source_id` for generated data) as required by FR-007. If a source lacks these, the validator MUST raise an error.
- [X] T050 [P] Create `code/data/manifest_schema.json` defining the strict schema for `data_manifest.json` including `source_type`, `source_id`, `doi`, `url`, and `checksum` fields.
- [X] T047b [P] [FR-001] [Edge Cases] Implement `code/services/thermo_extrapolator.py` to handle missing thermodynamic parameters in the CALPHAD database. **Requirement**: Use `scipy.interpolate.interp1d` or `numpy.polyfit` for linear extrapolation of missing parameters in the 500‑900 K range. **Constraint**: Do NOT use `sklearn.linear_model.LinearRegression` for this specific extrapolation task; use dedicated interpolation libraries to avoid conceptual confusion and ensure thermodynamic consistency. **Constraint**: This task is a FALLBACK mechanism for missing parameters, not the primary extraction logic. **Additional Requirement**: Verify that any extrapolated values remain consistent with TCFE9 trends (thermodynamic consistency check). **Dependency**: Must run after T050 and T045e‑Fetch.
- [X] T047c [P] Execute and validate `code/services/thermo_extrapolator.py` on a sample set of missing parameters. **Requirement**: Verify that extrapolated values are physically plausible and consistent with TCFE9 trends. **Dependency**: Must run after T047b.
- [X] T050-ManifestFinal [P] [FR-007] Finalize `data_manifest.json`. **Requirements**:
 1. Run `manifest_validator.py` (T049) against the combined manifest (created by T045a‑Fetch, T045c‑Fetch, T045e‑Fetch, T045f‑Fetch/T045f-Gen, T092-ManifestUpdate, T048-Exec, T091-Exec, T049b-Lookup).
 2. Ensure all real data sources have valid DOIs/URLs.
 3. **Constraint**: If validation fails, the process MUST terminate with an error.
 **Dependency**: Must run after T045a‑Fetch, T045c‑Fetch, T045e‑Fetch, T045f‑Fetch/T045f-Gen, T092-ManifestUpdate, T049, T050, T048-Exec, T091-Exec, T049b-Lookup.
- [X] T007 [P] Define `code/models/` directory structure and base entity schemas for `SegregationProfile`, `AlloySystem`, and `RegressionModel`. **Output**: Create `code/models/schemas.py` with Pydantic models for `SegregationProfile`, `AlloySystem`, and `RegressionModel`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

## Phase 3: User Story 1 - Thermodynamic Segregation Profile Generation (Priority: P1) 🎯 MVP

**Goal**: Compute equilibrium segregation energies and concentrations for BCC alloy systems using pre‑computed DFT values (Real Data) and the McLean isotherm model.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for McLean isotherm calculation in `tests/unit/test_mclean.py`.
- [X] T011 [P] [US1] Integration test for data loading and profile generation in `tests/integration/test_us1_profile.py`.

### Implementation for User Story 1

- [X] T001c [P] [FR-002] Implement `code/services/gb_service.py` to generate symmetric tilt grain boundary supercells using `pymatgen` from MP‑13 seed. **Dependency**: Must run after T004.
- [X] T017 [P] [FR-002] [Review‑Response] Implement `code/services/dft_service.py`. **Constraint**: **HPC‑ONLY**. This task MUST be skipped in the CI environment. **Requirements**:
 1. Create a stub file `code/services/dft_service.py`.
 2. Define supercell geometry: Σ tilt grain boundary, specific misorientation angle.
 3. Input format: PWscf input files (template only).
 4. **Constraint**: If running in CI environment (check `CI` env var), log "SKIPPED: HPC‑ONLY" and exit successfully. Do NOT attempt to run DFT.
 5. **Deliverable**: Create `research/templates/fe_cr_gb.pwscf` as a template file and `data/raw/supercell_template.pwscf` as the output.
 6. **Reference**: Must cite spec‑amendment T017b for the deviation from original FR‑002.
 **Dependency**: Must run after T017b-Exec and T017a-Exec.
- [X] T013b [P] [FR-002] Implement `code/data/load_dft_energies.py` to load pre‑computed DFT energies from `data/raw/dft_energies.json`. **Requirements**:
 1. Load the JSON file fetched by T045f‑Fetch or generated by T045f-Gen.
 2. Validate the schema (keys: `system`, `energy_eV`, `temperature`).
 3. Raise an error if the file is missing or malformed.
 **Dependency**: Must run after T045f-Fetch/T045f-Gen.
- [ ] T013 [US1] [FR-002, FR-007] Implement `code/services/load_dft_surrogate.py` to load literature‑calibrated segregation energies. **Input**: Load REAL DFT segregation energies for binaries from `data/raw/dft_energies.json` via `code/data/load_dft_energies.py` (T013b). **Constraint**: This task MUST NOT implement or call any real DFT code. It MUST load the pre‑computed energies from the REAL dataset (T045f-Fetch) or the fallback placeholder (T045f-Gen). **Constraint**: If `data/raw/dft_energies.json` is missing, trigger the fallback path (T045f-Gen) or log a warning and proceed with a minimal output if the fallback was already generated. **Constraint**: This task implements the **amended** requirement per T017b; it does NOT satisfy the original FR-002 "compute" requirement. **Dependency**: Must run after T045f-Fetch/T045f-Gen, T013b, T017b-Exec, T017a-Exec, and T049b-Lookup. <!-- ATOMIZE: requested -->
- [ ] T013-Exec [US1] [FR-002, FR-007] Execute `code/services/load_dft_surrogate.py` to generate `data/processed/surrogate_energies.json`. **Requirements**:
 1. Run `python code/services/load_dft_surrogate.py`.
 2. **Constraint**: If `data/raw/dft_energies.json` is missing entirely (no file), trigger T045f-Gen (fallback) and proceed with the generated placeholder. Do NOT raise a hard error.
 3. **Constraint**: If `data/raw/dft_energies.json` contains a 'MISSING_SOURCE' flag (from T045f-Gen), the task MUST log "Data missing: using fallback" and generate a minimal output file with `source_type: 'fallback'` instead of raising a hard error.
 4. **Output**: Save to `data/processed/surrogate_energies.json`.
 **Dependency**: Must run after T013 and T045f-Fetch/T045f-Gen.
- [X] T017c [P] [FR-002] [Constitution VI] Implement `code/services/thermo_consistency_check.py` to verify that loaded surrogate DFT energies align with TCFE9 parameters. **Requirements**:
 1. Load `data/raw/dft_energies.json` (T045f-Fetch/T045f-Gen) and `data/raw/calphad_params.json` (T045e-Fetch).
 2. Compare segregation energies against thermodynamic predictions from CALPHAD for binary systems.
 3. **Constraint**: If energies deviate by > 0.1 eV from CALPHAD trends, log a warning and flag the data for review.
 4. **Constraint**: If no CALPHAD data is available, skip the check and log "Thermodynamic consistency check skipped: no CALPHAD data".
 5. **Deliverable**: Write `data/processed/thermo_consistency_report.json` with pass/fail status and deviation metrics.
 **Dependency**: Must run after T045e-Fetch and T013-Exec (to ensure surrogate data is loaded).
- [X] T055 [US1] Implement validation in `code/services/load_dft_surrogate.py` to ensure surrogate inputs align with the supercell geometry generated by `gb_service.py`. **Dependency**: Must run after T001c and T013.
- [X] T014 [US1] [FR-003] Implement `code/models/mclean.py` to calculate equilibrium concentrations from segregation energy and bulk composition. **Requirements**:
 1. Implement the core McLean isotherm equation.
 2. Cap equilibrium concentration at 1.0 and return a "saturation" flag if the calculated value exceeds 1.0.
 3. Add logging using the logger from `code/config.py`. Messages: "Calculated segregation energy: {value} eV", "Applied McLean isotherm", "Equilibrium concentration: {value}", "Saturation flag: {flag}".
 **Dependency**: Must run after T013b.
- [ ] T018 [US1] [FR-003] Generate `data/processed/segregation_profiles.json` containing computed profiles for the ternary systems under investigation. **Requirements**: <!-- ATOMIZE: requested -->
 1. Load equilibrium compositions from `data/processed/equilibrium_compositions.csv` (T048-Exec).
 2. Load DFT energies from `data/processed/surrogate_energies.json` (T013-Exec). **Note**: This task loads SURROGATE or FALLBACK energies, NOT computed DFT energies. FR-002 is satisfied via the amendment T017b.
 3. Apply McLean model (T014) to compute GB concentrations.
 4. Save results to `data/processed/segregation_profiles.json`.
 **Dependency**: Must run after T048-Exec, T014, T013-Exec, T045f-Fetch/T045f-Gen.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

## Phase 4: User Story 2 - Multicomponent Cooperative Effect Analysis (Priority: P2)

**Goal**: Analyze segregation profiles to identify non‑linear thresholds and cooperative effects where multiple solutes amplify segregation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for interaction term generation in `tests/unit/test_regression.py`.
- [X] T020 [P] [US2] Integration test for cooperative effect detection in `tests/integration/test_us2_cooperative.py`.

### Implementation for User Story 2

- [ ] T021a-Gen-Synth [US2] [FR-004] Generate interaction terms for regression on SYNTHETIC data. **Requirements**:
 1. Use `sklearn.preprocessing.PolynomialFeatures(degree=2, include_bias=False)` to generate interaction terms (e.g., Cr*Mo, Cr*V).
 2. **Constraint**: Input file: `data/raw/generated_ground_truth.csv` (from T091-Exec).
 3. **Constraint**: Use exact column naming convention: `Cr_Mo`, `Cr_V`, `Mo_V`, `Cr_W`, `Mo_W`, `V_W` (underscores for interactions).
 4. **Deliverable**: Generate `data/processed/interaction_terms_synth.csv` with columns [Cr, Mo, Cr_Mo,...] using comma delimiter. **Output Path**: `data/processed/interaction_terms_synth.csv`.
 **Dependency**: Must run after T091-Exec.
- [ ] T021a-Gen-Sci [US2] [FR-004] Generate interaction terms for regression on SCIENTIFIC data. **Requirements**:
 1. Use `sklearn.preprocessing.PolynomialFeatures(degree=2, include_bias=False)` to generate interaction terms.
 2. **Constraint**: Input file: `data/processed/segregation_profiles.json` (from T018).
 3. **Constraint**: Use exact column naming convention.
 4. **Deliverable**: Generate `data/processed/interaction_terms_sci.csv` with columns [Cr, Mo, Cr_Mo,...]. **Output Path**: `data/processed/interaction_terms_sci.csv`.
 **Dependency**: Must run after T018.
- [ ] T021a-Persist-Synth [US2] [FR-004] Persist synthetic interaction terms to `data/processed/interaction_terms_synth_final.csv`. **Requirements**:
 1. Read `data/processed/interaction_terms_synth.csv` (from T021a-Gen-Synth).
 2. Validate the schema and column names.
 3. Save to `data/processed/interaction_terms_synth_final.csv`.
 **Dependency**: Must run after T021a-Gen-Synth.
- [ ] T021a-Persist-Sci [US2] [FR-004] Persist scientific interaction terms to `data/processed/interaction_terms_sci_final.csv`. **Requirements**:
 1. Read `data/processed/interaction_terms_sci.csv` (from T021a-Gen-Sci).
 2. Validate the schema and column names.
 3. Save to `data/processed/interaction_terms_sci_final.csv`.
 **Dependency**: Must run after T021a-Gen-Sci.
- [X] T021b [US2] [FR-004] Implement `code/models/regression.py` to fit linear models with interaction terms. **Library**: Use `sklearn.linear_model.LinearRegression`. **Dependency**: Must run after T021a-Persist-Synth and T021a-Persist-Sci.
- [ ] T022-Synth [US2] [FR-004] Implement logic to compare MSE of interaction model vs. additive binary null hypothesis on SYNTHETIC data. **Output**: Log "MSE reduction: X% (Threshold: 10%)" and raise warning if threshold not met. **Dependency**: Must run after T021b and T021a-Persist-Synth.
- [ ] T022-Sci [US2] [FR-004] Implement logic to compare MSE of interaction model vs. additive binary null hypothesis on SCIENTIFIC data. **Output**: Log "MSE reduction: X% (Threshold: 10%)" and raise warning if threshold not met. **Dependency**: Must run after T021b and T021a-Persist-Sci.
- [ ] T022-Exec-Synth [US2] [FR-004] Execute the MSE comparison logic on SYNTHETIC data and generate the null hypothesis model data. **Requirements**:
 1. Run `python code/services/mse_comparison.py` (created by T022-Synth).
 2. **Constraint**: Ensure T022-Synth logic was run.
 3. **Output**: Write `data/processed/mse_comparison_synth.json`.
 **Dependency**: Must run after T022-Synth and T021b.
- [ ] T022-Exec-Sci [US2] [FR-004] Execute the MSE comparison logic on SCIENTIFIC data and generate the null hypothesis model data. **Requirements**:
 1. Run `python code/services/mse_comparison.py` (created by T022-Sci).
 2. **Constraint**: Ensure T022-Sci logic was run.
 3. **Output**: Write `data/processed/mse_comparison_sci.json`.
 **Dependency**: Must run after T022-Sci and T021b.
- [ ] T023-Synth [US2] [FR-004] Implement significance testing (p-value < 0.05) for interaction coefficients on SYNTHETIC data. **Dependency**: Must run after T021b and T021a-Persist-Synth.
- [ ] T023-Sci [US2] [FR-004] Implement significance testing (p-value < 0.05) for interaction coefficients on SCIENTIFIC data. **Dependency**: Must run after T021b and T021a-Persist-Sci.
- [ ] T023-Exec-Synth [US2] [FR-004] Execute the significance testing logic on SYNTHETIC data. **Requirements**:
 1. Run `python code/services/significance_test.py` (created by T023-Synth).
 2. **Constraint**: Ensure p-values are calculated and stored.
 3. **Output**: Write `data/processed/significance_results_synth.json`.
 **Dependency**: Must run after T023-Synth and T021b.
- [ ] T023-Exec-Sci [US2] [FR-004] Execute the significance testing logic on SCIENTIFIC data. **Requirements**:
 1. Run `python code/services/significance_test.py` (created by T023-Sci).
 2. **Constraint**: Ensure p-values are calculated and stored.
 3. **Output**: Write `data/processed/significance_results_sci.json`.
 **Dependency**: Must run after T023-Sci and T021b.
- [X] T024a [US2] [FR-006] Implement `code/services/plotter.py` to generate heatmaps visualizing segregation energy vs. bulk composition and temperature. **Requirements**:
 1. Input: `data/processed/segregation_profiles.json` (T018).
 2. Output: `data/figures/segregation_heatmap.png` (T024b).
 3. Mapping: x=bulk_concentration, y=temperature, z=segregation_energy.
 4. Style: Use `cmap=viridis` and `norm=Normalize` (symmetric range to handle negative values). Do NOT use `LogNorm`.
 **Dependency**: Must run after T018.
- [ ] T024b [US2] [FR-006] Integrate the plotting logic from T024a to generate `data/figures/segregation_heatmap.png`. **Dependency**: Must run after T024a and T018.
- [X] T021c [US2] [FR-004] [Constitution VII] Implement `code/services/statistical_validation.py` to orchestrate joint verification of interaction term significance AND k-fold stability. **Requirements**:
 1. Input: Regression coefficients from T021b, p-values from T023-Exec-Synth/T023-Exec-Sci, CV results from T029/T030.
 2. **Constraint**: Check if ANY interaction term has p < 0.05 AND |coefficient| > 0.01 eV.
 3. **Constraint**: Check if CV R² standard deviation <= 0.05.
 4. **Constraint**: If BOTH conditions are met, mark "Cooperative Effects Detected". If either fails, mark "No Significant Cooperative Effects".
 5. **Output**: Write `data/processed/statistical_validation_report.json` with unified pass/fail status.
 **Dependency**: Must run after T023-Exec-Synth, T023-Exec-Sci, and T030.
- [X] T025 [US2] Write results to `data/processed/cooperative_effects_analysis.json` including coefficients, p-values, and MSE reduction stats. **Dependency**: Must run after T021c and T022-Exec-Sci.
- [ ] T026 [US2] Add logic to flag systems where no significant cooperative effects are detected within statistical power. **Dependency**: Must run after T025.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

## Phase 5: User Story 3 - Model Generalizability and Cross-Validation (Priority: P3)

**Goal**: Perform k‑fold cross‑validation on empirical composition-segregation functions to assess robustness.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for k‑fold splitting logic in `tests/unit/test_validation.py`.
- [X] T028 [P] [US3] Integration test for cross‑validation metrics in `tests/integration/test_us3_validation.py`.

### Implementation for User Story 3

- [X] T029 [P] [US3] [FR-005] Implement `code/models/validation.py` to perform k‑fold cross‑validation on composition/temperature data points. **Dependency**: Must run after T021b.
- [ ] T029-Exec [US3] [FR-005] Execute the cross-validation routine. **Requirements**:
 1. Run `python code/models/validation.py`.
 2. **Constraint**: Ensure the CV logic is executed and results are stored in memory or a temporary file.
 **Dependency**: Must run after T029.
- [ ] T030 [US3] [FR-005] Calculate and report R² and MSE for each fold, plus mean and standard deviation. **Output**: Log "Mean R²: X, Std Dev: Y" and flag if Std Dev > 0.05. **Dependency**: Must run after T029-Exec.
- [ ] T030-Exec [US3] [FR-005] Execute the reporting logic for cross-validation metrics. **Requirements**:
 1. Run `python code/services/cv_reporter.py` (created by T030).
 2. **Constraint**: Ensure the metrics are written to `data/processed/cv_metrics.json`.
 **Dependency**: Must run after T030.
- [ ] T031 [US3] Perform transferability check: train on Fe‑Cr‑Mo, test on held‑out Fe‑Cr‑V subset (if applicable). **Dependency**: Must run after T029-Exec.
- [ ] T032 [US3] Add overfitting detection logic (high training/low validation score) and flagging. **Dependency**: Must run after T030-Exec.
- [X] T033 [US3] Generate `data/processed/cross_validation_results.json` with full metrics and fold details. **Dependency**: Must run after T030-Exec.

**Checkpoint**: All user stories should now be independently functional

## Phase 6: Validation & Experimental Strategy (Priority: P1 - Research Review)

**Goal**: Address SC‑003: Validate computed segregation energies against experimental literature values to validate the DFT workflow, and document the experimental plan.

### Implementation for Validation Strategy

- [ ] T095a-Check [Validation] [SC-003] Check for presence of APT data in `data/raw/apt_data/` (from T045a‑Fetch, T045c‑Fetch). **Requirements**:
 1. Iterate through all expected binary and ternary systems.
 2. **Constraint**: If a system‑specific 'no_data' placeholder exists (e.g., `ternary_no_data.json` or `Fe-V_no_data.json`), log "Validation Skipped: No Data for <system>" and record status in `data/processed/validation_status.json`.
 3. **Deliverable**: Create `data/processed/validation_status.json` with entries for each system: `{"system": "Fe-Cr", "status": "data_present"}` or `{"system": "Fe-Cr-Mo", "status": "no_data"}`.
 **Dependency**: Must run after T018 (Real Profiles) and T045a‑Fetch, T045c‑Fetch.

- [ ] T095c-Exec [Validation] [SC-003] Perform Binary Experimental Validation. **Requirements**:
 1. Read `data/processed/validation_status.json` (T095a-Check).
 2. **Constraint**: If `status: "no_data"` for a binary system, **immediately trigger T095e-Exec** (Failure Documentation) and exit with code 1. Do NOT bypass SC-003.
 3. **Constraint**: If binary APT data exists, compare computed profiles (from T018) against REAL APT data for binary systems.
 4. **Constraint**: If binary APT data exists, compute RMSE and MAE between model predictions and APT measurements.
 5. **Constraint**: If T018 (segregation_profiles.json) is missing or empty, create an empty `sc003_binary_validation.json` with `status: "no_profiles"` and trigger T095e-Exec.
 6. Write results to `data/processed/sc003_binary_validation.json` (JSON array of objects per system).
 7. **Constraint**: If binary APT data is missing for ALL systems, write `data/processed/sc003_binary_validation.json` as an empty JSON array `[]` AND trigger T095e-Exec.
 8. **Constraint**: If binary APT data is missing for ALL systems, the build MUST FAIL (exit code 1) as SC-003 is a mandatory success criterion.
 **Dependency**: Must run after T095a-Check and T018.

- [ ] T095e-Exec [Validation] [SC-003] SC-003 Fallback Strategy (Failure Documentation). **Requirements**:
 1. If T095c-Exec finds no binary APT data, generate `research/sc003_fallback_report.md`.
 2. Explicitly state: "SC-003 (Experimental Validation) FAILED: No verified APT data found for binary systems. Validation limited to surrogate consistency checks."
 3. **Constraint**: This task documents the failure; it does NOT bypass the criterion.
 4. **Constraint**: This task is triggered ONLY if T095c-Exec fails the build.
 **Dependency**: Must run after T095c-Exec if no data found.

- [ ] T095f [Validation] [SC-003] Experimental Gap Report. **Requirements**:
 1. Generate `research/experimental_gap_report.md` summarizing the lack of experimental data for ternary systems.
 2. Reference the search results in `research/data_sources.md` (T003-Record) that confirmed the absence of data.
 3. **Constraint**: This task is mandatory regardless of binary data availability to document the ternary gap.
 **Dependency**: Must run after T095a-Check.

- [ ] T055b [SC-003] Compute RMSE/MAE for binary validation. **Requirements**:
 1. Load `data/processed/sc003_binary_validation.json`.
 2. Calculate overall RMSE and MAE across all binaries with data.
 3. Write summary to `data/processed/sc003_binary_metrics.json` with keys `overall_rmse`, `overall_mae`.
 **Dependency**: Must run after T095c-Exec.

- [ ] T095b [Validation] [PIPELINE-VALIDATION] Compare regression coefficients against "injected ground truth" (T091) for pipeline logic verification only. **Constraint**: This task is for **PIPELINE VALIDATION ONLY** and does not satisfy SC-003. **Dependency**: Must run after T025 and T091-Exec.

- [ ] T096 [Validation] Write `research/validation_report.md` summarizing the parameter recovery results (T095b), the experimental validation results (T095c-Exec, T095e-Exec, T095f), statistical significance, and confirmation of the surrogate model's validity. **Dependency**: Must run after T095c-Exec, T095e-Exec, T095f.

- [ ] T100 [Review-Response] Create `research/experimental_validation_plan.md` to address the "Direct Measurement" requirement. **Requirements**:
 1. Specify **Atom Probe Tomography (APT)** as the primary apparatus for measuring segregation at the atomic scale.
 2. Define the **minimum detectable concentration** (e.g., 0.1 at.%) and the **detection limit** for trace elements (Cr, Mo, V, W) at grain boundaries.
 3. Estimate the **quantity of material** required (e.g., needle‑shaped specimens of ~100 nm diameter) and the preparation method (FIB lift‑out).
 4. Cite specific literature (DOI 10.1016/j.actamat.2020.01.015) where APT has successfully measured similar segregation in BCC Fe alloys.
 5. Explicitly state that while the current CI pipeline uses a surrogate, this plan defines the *physical* validation step required for final scientific acceptance.
 6. **Constraint**: Generate this file as a required output artifact for the CI build, even if no data exists.
 **Dependency**: None (can run in parallel with T095a-Check, but must be included in the final report).

**Checkpoint**: Validation strategy is documented, the project acknowledges the redefined success criterion, and the experimental gap identified by the reviewer is explicitly addressed.

## Phase 7: Review Response & Documentation (Priority: P1 - Research Review)

**Goal**: Explicitly address the reviewer's concern regarding the "Direct Measurement" of segregation energies and the definition of the experimental apparatus.

### Implementation for Review Response

- [ ] T101 [Review-Response] [FR-007, SC-003] Update `research/data_sources.md` to include a dedicated section "Experimental Validation Apparatus". **Requirements**:
 1. Describe the **Atom Probe Tomography (APT)** setup in detail: laser pulse frequency, wavelength, sample temperature (cryogenic vs. room), and detection efficiency.
 2. Specify the **minimum detectable concentration** for the elements (e.g., 0.1 at.%).
 3. Document the **sample preparation** workflow: FIB lift‑out parameters, annular milling steps, and final polishing voltage to ensure grain boundary integrity.
 4. Include a table of **literature DOIs** for APT studies on BCC Fe alloys that successfully resolved similar segregation phenomena.
 5. **Constraint**: This section must not rely on computational data; it must define the *physical* measurement capability.
 **Dependency**: None.

- [ ] T102 [Review-Response] [FR-007] Update `research/experimental_validation_plan.md` to include a "Detection Limit Analysis". **Requirements**:
 1. Calculate the theoretical detection limit for the specified APT setup based on literature sensitivity factors (use DOI 10.1016/j.actamat.2020.01.015, Equation (3) from the paper).
 2. Compare this limit against the predicted segregation concentrations from the McLean model (T018).
 3. **Constraint**: If the predicted concentration is below the detection limit, explicitly state "Below Detection Limit" and propose a strategy (e.g., lower temperature, higher bulk concentration) to bring the signal within range.
 4. **Constraint**: Ensure this file is generated as a required output artifact for the CI build.
 **Dependency**: Must run after T101 (Apparatus Definition) AND T018.

- [ ] T103 [Review-Response] [FR-007] Revise `research/validation_report.md` to include a "Gap Analysis" section. **Requirements**:
 1. Compare the current computational results (surrogate) with the proposed experimental plan.
 2. Explicitly state: "This project validates the *methodology* of detecting non‑linearity. The *quantitative* validation of segregation energies requires the experimental apparatus defined in T100/T101."
 3. **Constraint**: Do not claim the computational results are "verified" without the experimental data. Use language like "consistent with" or "predicted by".
 4. **Constraint**: Ensure this file is generated as a required output artifact for the CI build.
 **Dependency**: Must run after T102 (Detection Limit) AND T096 (Validation Report).

**Checkpoint**: The project now explicitly addresses the reviewer's concern about the lack of experimental apparatus definition and provides a clear path to physical validation.

## Phase 8: Finalization & Clean‑up

- [ ] T200 Review all tasks for consistency, ensure every FR/SC is covered, and that all placeholder handling references spec‑amendment T017b (for FR-002) and hard-fail logic (for FR-001/002 data sources).
- [ ] T201 Run full pipeline on CI to verify no hard errors, placeholders only appear where permitted (none for core data), and all validation reports generate successfully.
