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

**Purpose**: Fetch, verify, and document real scientific data sources (CALPHAD, DFT, APT) to satisfy FR-001, FR-002, FR-007, and SC-003. **Hard Fail**: If a verified source is not found, the pipeline MUST halt with a clear error. No placeholders allowed for core scientific data.

### Sub-Phase 0.1: Source Verification & Spec Amendments (Research)

- [ ] T018-Config [Research] [FR-007] [US-1] Create `research/candidate_sources.json` with pre-provided lists of candidate IDs/DOIs. **Requirements**:
 1. **Constraint**: Create the file `research/candidate_sources.json` with a JSON object.
 2. **Constraint**: Include keys: `binary_apt_ids` (list), `ternary_apt_dois` (list), `calphad_dois` (list), `dft_dois` (list).
 3. **Constraint**: If no candidate IDs/DOIs are known, create empty lists `[]` for each key and log a warning.
 4. **Constraint**: Use placeholder values (e.g., "NIST_ID_PLACEHOLDER", "DOI_PLACEHOLDER") if specific IDs are not yet known, to ensure the task is executable.
 5. **Deliverable**: `research/candidate_sources.json` with all required keys.
 **Dependency**: None.

- [ ] T018a-Script [Research] [FR-007] [US-1] Create `code/data/verify_apt_binary.py` to validate candidate IDs. **Requirements**:
 1. **Constraint**: Do NOT perform live API searches in the script creation phase. The script MUST be designed to validate a pre-provided list of candidate IDs in `research/candidate_sources.json` against Zenodo/NIST APIs.
 2. **Constraint**: If verified IDs are found, the script MUST record them in `research/data_sources.md`.
 3. **Constraint**: If NO verified IDs are found, the script MUST record "No verified APT data found" with a citation to the search query and timestamp in `research/data_sources.md`.
 4. **Constraint**: If "No verified APT data found", the script MUST NOT halt the pipeline; it MUST set a flag to trigger the fallback path.
 5. **Deliverable**: `code/data/verify_apt_binary.py`.
 **Dependency**: Must run after T018-Config.

- [ ] T018a-Exec [Research] [FR-007] [US-1] Execute `code/data/verify_apt_binary.py` to verify binary APT sources. **Requirements**:
 1. Run `python code/data/verify_apt_binary.py`.
 2. **Constraint**: If verified IDs are found, record them in `research/data_sources.md`.
 3. **Constraint**: If NO verified IDs are found, record "No verified APT data found" in `research/data_sources.md` and **continue** the pipeline to fallback tasks (T095e).
 4. **Deliverable**: Updated `research/data_sources.md` with "Binary APT Sources" section.
 **Dependency**: Must run after T018a-Script and T018-Config.

- [ ] T018c-Script [Research] [FR-007] [US-1] Create `code/data/verify_apt_ternary.py` to validate candidate DOIs. **Requirements**:
 1. **Constraint**: Do NOT perform live API searches in the script creation phase. The script MUST be designed to validate a pre-provided list of candidate DOIs in `research/candidate_sources.json` against CrossRef API.
 2. **Constraint**: If verified DOIs are found, the script MUST record them in `research/data_sources.md`.
 3. **Constraint**: If NO verified ternary APT data exists, the script MUST explicitly record "No verified ternary APT data found" and document the search scope in `research/data_sources.md`.
 4. **Constraint**: If "No verified ternary APT data found", the script MUST NOT halt the pipeline; it MUST set a flag to trigger the fallback path.
 5. **Deliverable**: `code/data/verify_apt_ternary.py`.
 **Dependency**: Must run after T018-Config.

- [ ] T018c-Exec [Research] [FR-007] [US-1] Execute `code/data/verify_apt_ternary.py` to verify ternary APT sources. **Requirements**:
 1. Run `python code/data/verify_apt_ternary.py`.
 2. **Constraint**: If verified DOIs are found, record them in `research/data_sources.md`.
 3. **Constraint**: If NO verified ternary APT data found, record "No verified ternary APT data found" in `research/data_sources.md` and **continue** the pipeline to fallback tasks (T095e).
 4. **Deliverable**: Updated `research/data_sources.md` with "Ternary APT Sources" section.
 **Dependency**: Must run after T018c-Script and T018-Config.

- [ ] T018d-Script [Research] [FR-001] [FR-007] [US-1] Create `code/data/verify_calphad.py` to validate candidate DOIs. **Requirements**:
 1. **Constraint**: Do NOT perform live API searches in the script creation phase. The script MUST be designed to validate a pre-provided list of candidate DOIs in `research/candidate_sources.json`.
 2. **Constraint**: Must provide a specific DOI/URL.
 3. **Constraint**: Must verify that the source contains interaction parameters for Fe-Cr-Mo, Fe-Cr-V, Fe-Mo-V, Fe-Cr-W, and Fe-Mo-W. If missing, record "No verified open CALPHAD source with ternary parameters found".
 4. Record the DOI/URL in `research/data_sources.md`.
 5. **Constraint**: If no open source is found, record "No verified open CALPHAD source found" and **continue** the pipeline to fallback tasks (T095e).
 6. **Deliverable**: `code/data/verify_calphad.py`.
 **Dependency**: Must run after T018-Config.

- [ ] T018d-Exec [Research] [FR-001] [FR-007] [US-1] Execute `code/data/verify_calphad.py` to verify CALPHAD sources. **Requirements**:
 1. Run `python code/data/verify_calphad.py`.
 2. **Constraint**: If verified DOI/URL is found, record it in `research/data_sources.md`.
 3. **Constraint**: If no open source is found, record "No verified open CALPHAD source found" in `research/data_sources.md` and **continue** the pipeline to fallback tasks (T095e).
 4. **Deliverable**: Updated `research/data_sources.md` with "CALPHAD Source" section.
 **Dependency**: Must run after T018d-Script and T018-Config.

- [ ] T018e-Script [Research] [FR-002] [FR-007] [US-1] Create `code/data/verify_dft.py` to validate candidate DOIs. **Requirements**:
 1. **Constraint**: Do NOT perform live API searches in the script creation phase. The script MUST be designed to validate a pre-provided list of candidate DOIs in `research/candidate_sources.json`.
 2. **Constraint**: Must provide a specific DOI/URL.
 3. **Constraint**: If no dataset is found, record "No verified DFT source found" and **continue** the pipeline to fallback tasks (T095e).
 4. Record the DOI/URL in `research/data_sources.md`.
 5. **Deliverable**: `code/data/verify_dft.py`.
 **Dependency**: Must run after T018-Config.

- [ ] T018e-Exec [Research] [FR-002] [FR-007] [US-1] Execute `code/data/verify_dft.py` to verify DFT sources. **Requirements**:
 1. Run `python code/data/verify_dft.py`.
 2. **Constraint**: If verified DOI/URL is found, record it in `research/data_sources.md`.
 3. **Constraint**: If no DFT source is found, record "No verified DFT source found" in `research/data_sources.md` and **continue** the pipeline to fallback tasks (T095e).
 4. **Deliverable**: Updated `research/data_sources.md` with "DFT Source" section.
 **Dependency**: Must run after T018e-Script and T018-Config.

- [ ] T017b-Config [Research] [FR-002] [Constitution VI] Create the content for `research/spec_amendment_fr002.md`. **Requirements**:
 1. Create the content string for the "Spec Amendment" artifact explicitly documenting the deviation from FR-002.
 2. State that for CI execution, FR-002 is amended to "Load pre-computed DFT energies from verified literature sources" instead of "compute using Quantum ESPRESSO".
 3. Justify this amendment based on CI hardware constraints and the need for a runnable pipeline.
 4. **Constraint**: This document serves as the Single Source of Truth for the deviation, aligning Spec and Plan.
 5. **Template**: The content MUST contain the following text verbatim:
 "This project deviates from FR-002 due to CI hardware constraints. Instead of running Quantum ESPRESSO, it loads pre-computed DFT energies from [SOURCE_DOI_PLACEHOLDER]. This deviation is justified by the need for a runnable pipeline on free-tier hardware."
 6. **Constraint**: Replace [SOURCE_DOI_PLACEHOLDER] with the actual DOI from `research/data_sources.md` before execution.
 7. **Deliverable**: Content string for `research/spec_amendment_fr002.md`.
 **Dependency**: None.

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

- [ ] T017a-Script [Research] [FR-002] [Constitution VI] Create `code/data/write_fr002_deviation.py`. **Requirements**:
 1. Create a script that documents the deviation from the spec's "compute segregation energies using Quantum ESPRESSO" requirement.
 2. Justify the use of pre‑computed DFT data (T018e-Verify) and the "Reduced CALPHAD Parameter Set" due to CI constraints (no GPU, 6 h limit).
 3. State that the pipeline logic is validated against literature data, and the "compute" step is deferred to HPC resources in a separate branch.
 4. **Constraint**: This document MUST reference the `research/spec_amendment_fr002.md` artifact as the Single Source of Truth for the deviation.
 5. **Deliverable**: `code/data/write_fr002_deviation.py`.
 **Dependency**: Must run after T017b-Exec.

- [ ] T017a-Exec [Research] [FR-002] [Constitution VI] Execute `code/data/write_fr002_deviation.py` to create `research/fr002_deviation.md`. **Requirements**:
 1. Run `python code/data/write_fr002_deviation.py`.
 2. **Constraint**: Verify that `research/fr002_deviation.md` exists and references `research/spec_amendment_fr002.md`.
 3. **Deliverable**: `research/fr002_deviation.md`.
 **Dependency**: Must run after T017a-Script and T017b-Exec.

### Sub-Phase 0.2: Data Fetching (Implementation)

- [ ] T045a-Fetch [Research] [FR-007] Fetch APT datasets for binary systems (Fe-Cr, Fe-Mo, Fe-V, Fe-W) using IDs from T018a-Exec. **Requirements**:
 1. Implement `code/data/fetch_apt_data.py` to download real APT data for binary systems.
 2. Use specific Accession IDs recorded in `research/data_sources.md` by T018a-Exec.
 3. **Constraint**: If T018a-Exec recorded "No verified APT data found", the task MUST NOT raise an exception. It MUST record a status "no_data" in `data/processed/validation_status.json` and **continue** the pipeline.
 4. **Constraint**: If a network error occurs during fetch, the task MUST raise a `FetchError` and halt execution.
 5. **Output**: Save real data to `data/raw/apt_data/<system>_apt.json`. Update `data_manifest.json` with `source_type: 'experimental'`, `source_id: <accession_id>`, `doi: <doi>`, `url: <url>`.
 **Dependency**: Must run after T018a-Exec.

- [ ] T045c-Fetch [Research] [FR-007] Fetch APT datasets for ternary systems (Fe-Cr-Mo, etc.) using DOIs from T018c-Exec. **Requirements**:
 1. Extend `code/data/fetch_apt_data.py` to download real APT data for ternary systems.
 2. Use specific DOIs recorded in `research/data_sources.md` by T018c-Exec.
 3. **Constraint**: If T018c-Exec recorded "No verified ternary APT data found", the task MUST NOT raise an exception. It MUST record a status "no_data" in `data/processed/validation_status.json` and **continue** the pipeline.
 4. **Constraint**: If fetch fails, the task MUST raise a `FetchError` and halt execution.
 5. **Output**: Save real data to `data/raw/apt_data/` and update `data_manifest.json`.
 **Dependency**: Must run after T018c-Exec.

- [ ] T045e-Fetch [Research] [FR-001] [FR-007] Fetch Open CALPHAD parameters using DOI from T018d-Exec. **Requirements**:
 1. Implement `code/data/download_calphad.py` to fetch the file using the specific DOI/URL from T018d-Exec.
 2. Verify checksum against the provided hash in `research/data_sources.md`.
 3. **Constraint**: If T018d-Exec recorded "No verified open CALPHAD source found", the task MUST NOT raise an exception. It MUST record a status "no_data" in `data/processed/validation_status.json` and **continue** the pipeline.
 4. **Constraint**: If fetch fails or checksum mismatch, the task MUST raise a `FetchError` and halt execution.
 5. **Output**: Save to `data/raw/calphad_params.json`. Update `data_manifest.json`.
 **Dependency**: Must run after T018d-Exec.

- [ ] T045f-Fetch [Research] [FR-002] [FR-007] Fetch pre‑computed DFT energies using DOI from T018e-Exec. **Requirements**:
 1. Implement `code/data/download_dft_energies.py` to fetch the file using the specific DOI/URL from T018e-Exec.
 2. Verify checksum/DOI.
 3. **Constraint**: If T018e-Exec recorded "No verified DFT source found", the task MUST catch the `DataNotFoundError` internally and trigger T045f-Gen (fallback). Do NOT raise the exception to the pipeline.
 4. **Constraint**: If fetch fails or checksum mismatch, the task MUST raise a `FetchError` and halt execution.
 5. **Output**: Save to `data/raw/dft_energies.json`. Update `data_manifest.json`.
 **Dependency**: Must run after T018e-Exec.

- [ ] T045f-Gen [Research] [FR-002] [FR-007] Generate a minimal `data/raw/dft_energies.json` with a 'MISSING_SOURCE' flag if fetch fails. **Requirements**:
 1. Create `code/data/generate_fallback_dft.py`.
 2. If T045f-Fetch failed, run this script to create a minimal JSON file with `source_type: 'fallback'`, `source_id: 'missing_source'`, and a flag `MISSING_SOURCE: true`.
 3. **Constraint**: This task MUST NOT generate fake physics data; it MUST only create a placeholder to allow the pipeline to proceed to the 'No Data' fallback logic.
 4. **Output**: Save to `data/raw/dft_energies.json`. Update `data_manifest.json`.
 **Dependency**: Must run after T045f-Fetch.

- [ ] T090-Config [Research] [FR-001] Create `research/synthetic_ground_truth.yaml` with injection parameters. **Requirements**:
 1. Create the file `research/synthetic_ground_truth.yaml` with a YAML structure containing `interaction_coefficients` (default: {Cr_Mo: 0.05, Cr_V: 0.05, ...}) and `random_seed` (default: 42).
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
- [X] T005 [P] [FR-007] Validate the final `data_manifest.json`. **Requirements**:
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
- [ ] T013 [US1] [FR-002, FR-007] Implement `code/services/surrogate_service.py` to compute literature‑calibrated segregation energies. **Input**: Load REAL DFT segregation energies for binaries from `data/raw/dft_energies.json` via `code/data/load_dft_energies.py` (T013b). **Constraint**: This task MUST NOT implement or call any real DFT code. It MUST load the pre‑computed energies from the REAL dataset (T045f-Fetch) or the fallback placeholder (T045f-Gen). **Constraint**: If `data/raw/dft_energies.json` is missing, raise a hard error. **Dependency**: Must run after T045f-Fetch/T045f-Gen, T013b, T017b-Exec, T017a-Exec, and T049b-Lookup.
- [ ] T013-Exec [US1] [FR-002, FR-007] Execute `code/services/surrogate_service.py` to generate `data/processed/surrogate_energies.json`. **Requirements**:
 1. Run `python code/services/surrogate_service.py`.
 2. **Constraint**: If `data/raw/dft_energies.json` is missing entirely (no file), raise a hard error.
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
- [X] T055 [US1] Implement validation in `code/services/surrogate_service.py` to ensure surrogate inputs align with the supercell geometry generated by `gb_service.py`. **Dependency**: Must run after T001c and T013.
- [ ] T014 [US1] [FR-003] Implement `code/models/mclean.py` to calculate equilibrium concentrations from segregation energy and bulk composition. **Requirements**:
 1. Implement the core McLean isotherm equation.
 2. Cap equilibrium concentration at 1.0 and return a "saturation" flag if the calculated value exceeds 1.0.
 3. Add logging using the logger from `code/config.py`. Messages: "Calculated segregation energy: {value} eV", "Applied McLean isotherm", "Equilibrium concentration: {value}", "Saturation flag: {flag}".
 **Dependency**: Must run after T013b.
- [ ] T018 [US1] [FR-003] Generate `data/processed/segregation_profiles.json` containing computed profiles for the ternary systems under investigation. **Requirements**:
 1. Load equilibrium compositions from `data/processed/equilibrium_compositions.csv` (T048-Exec).
 2. Load DFT energies from `data/processed/surrogate_energies.json` (T013-Exec).
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

- [ ] T021a-Gen [US2] [FR-004] Generate interaction terms for regression. **Requirements**:
 1. Use `sklearn.preprocessing.PolynomialFeatures(degree=2, include_bias=False)` to generate interaction terms (e.g., Cr*Mo, Cr*V).
 2. **Constraint**: If `sklearn` is unavailable, manual implementation of interaction terms is permitted provided the mathematical result is identical.
 3. **Constraint**: Use exact column naming convention: `Cr_Mo`, `Cr_V`, `Mo_V`, `Cr_W`, `Mo_W`, `V_W` (underscores for interactions).
 4. **Constraint**: Input file: `data/processed/segregation_profiles.json` (from T018).
 5. **Deliverable**: Generate `data/processed/interaction_terms_temp.csv` with columns [Cr, Mo, Cr_Mo,...] using comma delimiter. **Output Path**: `data/processed/interaction_terms_temp.csv`.
 **Dependency**: Must run after T018.
- [ ] T021a-Persist [US2] [FR-004] Persist interaction terms to `data/processed/interaction_terms.csv`. **Requirements**:
 1. Read `data/processed/interaction_terms_temp.csv` (from T021a-Gen).
 2. Validate the schema and column names.
 3. Save to `data/processed/interaction_terms.csv`.
 **Dependency**: Must run after T021a-Gen.
- [X] T021b [US2] [FR-004] Implement `code/models/regression.py` to fit linear models with interaction terms. **Library**: Use `sklearn.linear_model.LinearRegression`. **Dependency**: Must run after T021a-Persist.
- [ ] T022 [US2] [FR-004] Implement logic to compare MSE of interaction model vs. additive binary null hypothesis, requiring >10% MSE reduction to confirm cooperative effects. **Output**: Log "MSE reduction: X% (Threshold: 10%)" and raise warning if threshold not met. **Dependency**: Must run after T021b.
- [ ] T022-Exec [US2] [FR-004] Execute the MSE comparison logic and generate the null hypothesis model data. **Requirements**:
 1. Run `python code/services/mse_comparison.py` (created by T022).
 2. **Constraint**: If T022 logic was not run, this task MUST generate the null hypothesis data and perform the comparison.
 3. **Output**: Write `data/processed/mse_comparison.json`.
 **Dependency**: Must run after T022 and T021b.
- [ ] T023 [US2] [FR-004] Implement significance testing (p-value < 0.05) for interaction coefficients. **Dependency**: Must run after T021b.
- [ ] T023-Exec [US2] [FR-004] Execute the significance testing logic. **Requirements**:
 1. Run `python code/services/significance_test.py` (created by T023).
 2. **Constraint**: Ensure p-values are calculated and stored.
 3. **Output**: Write `data/processed/significance_results.json`.
 **Dependency**: Must run after T023 and T021b.
- [X] T024a [US2] [FR-006] Implement `code/services/plotter.py` to generate heatmaps visualizing segregation energy vs. bulk composition and temperature. **Requirements**:
 1. Input: `data/processed/segregation_profiles.json` (T018).
 2. Output: `data/figures/segregation_heatmap.png` (T024b).
 3. Mapping: x=bulk_concentration, y=temperature, z=segregation_energy.
 4. Style: Use `cmap=viridis` and `norm=Normalize` (symmetric range to handle negative values). Do NOT use `LogNorm`.
 **Dependency**: Must run after T018.
- [ ] T024b [US2] [FR-006] Integrate the plotting logic from T024a to generate `data/figures/segregation_heatmap.png`. **Dependency**: Must run after T024a and T018.
- [X] T021c [US2] [FR-004] [Constitution VII] Implement `code/services/statistical_validation.py` to orchestrate joint verification of interaction term significance AND k-fold stability. **Requirements**:
 1. Input: Regression coefficients from T021b, p-values from T023-Exec, CV results from T029/T030.
 2. **Constraint**: Check if ANY interaction term has p < 0.05 AND |coefficient| > 0.01 eV.
 3. **Constraint**: Check if CV R² standard deviation <= 0.05.
 4. **Constraint**: If BOTH conditions are met, mark "Cooperative Effects Detected". If either fails, mark "No Significant Cooperative Effects".
 5. **Output**: Write `data/processed/statistical_validation_report.json` with unified pass/fail status.
 **Dependency**: Must run after T023-Exec and T030.
- [ ] T025 [US2] Write results to `data/processed/cooperative_effects_analysis.json` including coefficients, p-values, and MSE reduction stats. **Dependency**: Must run after T021c and T022-Exec.
- [ ] T026 [US2] Add logic to flag systems where no significant cooperative effects are detected within statistical power. **Dependency**: Must run after T025.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

## Phase 5: User Story 3 - Model Generalizability and Cross-Validation (Priority: P3)

**Goal**: Perform k‑fold cross‑validation on empirical composition-segregation functions to assess robustness.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for k‑fold splitting logic in `tests/unit/test_validation.py`.
- [ ] T028 [P] [US3] Integration test for cross‑validation metrics in `tests/integration/test_us3_validation.py`.

### Implementation for User Story 3

- [ ] T029 [P] [US3] [FR-005] Implement `code/models/validation.py` to perform k‑fold cross‑validation on composition/temperature data points. **Dependency**: Must run after T021b.
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
- [ ] T033 [US3] Generate `data/processed/cross_validation_results.json` with full metrics and fold details. **Dependency**: Must run after T030-Exec.

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
 2. **Constraint**: If `status: "no_data"` for a binary system, skip comparison and produce an empty result entry: `{"system": "<name>", "status": "no_data", "rmse": null, "mae": null}`.
 3. **Constraint**: If binary APT data exists, compare computed profiles (from T018) against REAL APT data for binary systems.
 4. **Constraint**: If binary APT data exists, compute RMSE and MAE between model predictions and APT measurements.
 5. **Constraint**: If T018 (segregation_profiles.json) is missing or empty, create an empty `sc003_binary_validation.json` with `status: "no_profiles"`.
 6. Write results to `data/processed/sc003_binary_validation.json` (JSON array of objects per system).
 7. **Constraint**: If binary APT data is missing for ALL systems, write `data/processed/sc003_binary_validation.json` as an empty JSON array `[]` AND trigger T095e.
 8. **Constraint**: If binary APT data is missing for ALL systems, route to T095e (SC-003 Fallback Strategy).
 **Dependency**: Must run after T095a-Check and T018.

- [ ] T095e-Status [Validation] [SC-003] SC-003 Fallback Strategy. **Requirements**:
 1. If T095c-Exec finds no binary APT data, generate `research/sc003_fallback_report.md`.
 2. Explicitly state: "SC-003 (Experimental Validation) cannot be satisfied: No verified APT data found for binary systems. Validation limited to surrogate consistency checks."
 3. Downgrade SC-003 status to "Not Applicable" in the final report.
 4. **Constraint**: This task satisfies the "fail and document" path for SC-003 when data is missing, preventing a silent constraint violation.
 **Dependency**: Must run after T095c-Exec if no data found.

- [ ] T095f [Validation] [SC-003] Experimental Gap Report. **Requirements**:
 1. Generate `research/experimental_gap_report.md` summarizing the lack of experimental data for ternary systems.
 2. Reference the search results in `research/data_sources.md` (T018c-Exec) that confirmed the absence of data.
 3. **Constraint**: This task is mandatory regardless of binary data availability to document the ternary gap.
 **Dependency**: Must run after T095a-Check.

- [ ] T055b [SC-003] Compute RMSE/MAE for binary validation. **Requirements**:
 1. Load `data/processed/sc003_binary_validation.json`.
 2. Calculate overall RMSE and MAE across all binaries with data.
 3. Write summary to `data/processed/sc003_binary_metrics.json` with keys `overall_rmse`, `overall_mae`.
 **Dependency**: Must run after T095c-Exec.

- [ ] T095b [Validation] [PIPELINE-VALIDATION] Compare regression coefficients against "injected ground truth" (T091) for pipeline logic verification only. **Constraint**: This task is for **PIPELINE VALIDATION ONLY** and does not satisfy SC-003. **Dependency**: Must run after T025 and T091-Exec.

- [ ] T096 [Validation] Write `research/validation_report.md` summarizing the parameter recovery results (T095b), the experimental validation results (T095c-Exec, T095e-Status, T095f), statistical significance, and confirmation of the surrogate model's validity. **Dependency**: Must run after T095c-Exec, T095e-Status, T095f.

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