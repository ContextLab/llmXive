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

- [ ] T001-Search [Research] [FR-007] [US-1] **Search for candidate data sources**.
 1. Action: Create `research/candidate_sources.json` by performing live API searches against:
 - Zenodo: ` (handle pagination via `page` param)
 - NIST Materials Data Repository: `
 - Materials Project: ` (requires API key in env `MP_API_KEY`)
 - CrossRef DOI search: `
 2. Constraint: Do NOT guess IDs. If a search returns no results, record an empty list `[]` and log the query used.
 3. Deliverable: `research/candidate_sources.json` with keys: `binary_apt_ids`, `ternary_apt_dois`, `calphad_dois`, `dft_dois`.
 **Dependency**: None.

- [ ] T002-Verify [Research] [FR-007] [US-1] Create `code/data/verify_sources.py` to validate candidate IDs/DOIs. **Requirements**:
 1. Validate by sending a GET request to the DOI URL; a successful validation is HTTP 200 **and** the returned JSON field `status` equals `"published"` (or equivalent for Zenodo/NIST).
 2. Record verified IDs/DOIs in `research/data_sources.md`.
 3. If no verified IDs are found, record "No verified source found" with citation to the search query and timestamp.
 4. Do NOT halt the pipeline; set a flag `verified=False` for missing sources.
 **Dependency**: Must run after T001-Search.

- [ ] T003-Record [Research] [FR-007] [US-1] Execute `code/data/verify_sources.py` to verify ALL sources (Binary APT, Ternary APT, CALPHAD, DFT). **Requirements**:
 1. Run `python code/data/verify_sources.py`.
 2. Populate `research/data_sources.md` with sections for each source type.
 3. If a source category is missing, write a placeholder entry with `source_id: "NONE"` and `doi: "DOI_NOT_FOUND"`.
 4. If CALPHAD or DFT are missing, the pipeline proceeds to fallback tasks but MUST NOT proceed to scientific analysis until a formal amendment is created.
 **Dependency**: Must run after T002-Verify and T001-Search.

- [ ] T017b-Config [Research] [FR-002] [Constitution VI] Create the content for `research/spec_amendment_fr002.md`. **Requirements**:
 1. Build a string containing the amendment text.
 2. If `research/data_sources.md` provides a DOI for the DFT dataset, insert it; otherwise insert the literal placeholder `DOI_NOT_FOUND`.
 3. The text must contain verbatim:
 ```
 This project deviates from FR-002 due to CI hardware constraints. Instead of running Quantum ESPRESSO, it loads pre-computed DFT energies from [SOURCE_DOI_PLACEHOLDER]. This deviation is justified by the need for a runnable pipeline on free-tier hardware.
 ```
 **Dependency**: Must run after T003-Record.

- [ ] T017b-VerifySpecAmendment [Research] [FR-002] [Constitution VI] Verify that `spec.md` contains a section referencing `research/spec_amendment_fr002.md`. **Requirements**:
 1. Parse `spec.md` and confirm a line `# Amendment FR-002` exists and includes the path to the amendment file.
 2. If missing, raise an error prompting the author to merge the amendment.
 **Dependency**: Must run after T017b-Exec.

- [ ] T017b-WriteSpecAmendment [Research] [FR-002] [Constitution VI] Create `code/data/write_spec_amendment.py`. **Requirements**:
 1. Script takes the content string from T017b-Config and writes it to `research/spec_amendment_fr002.md`.
 2. Must NOT modify `spec.md` directly.
 **Dependency**: Must run after T017b-Config.

- [ ] T017b-Exec [Research] [FR-002] [Constitution VI] Execute `code/data/write_spec_amendment.py` to create `research/spec_amendment_fr002.md`. **Requirements**:
 1. Run `python code/data/write_spec_amendment.py`.
 2. Verify the file exists and contains the required text.
 **Dependency**: Must run after T017b-WriteSpecAmendment.

- [ ] T017b-UpdateSpec [Research] [FR-002] [Constitution VI] Update `spec.md` to include a reference to the amendment. **Requirements**:
 1. Append a section `## Amendment FR-002` with a link to `research/spec_amendment_fr002.md`.
 2. Commit the change.
 **Dependency**: Must run after T017b-Exec.

- [ ] T017b-VerifyAmendment [Research] [FR-002] [Constitution VI] Verify that the amendment text in `research/spec_amendment_fr002.md` matches the template and contains a DOI (or `DOI_NOT_FOUND`). **Requirements**:
 1. Simple string check; fail if the placeholder text is missing.
 **Dependency**: Must run after T017b-UpdateSpec.

### Sub-Phase 0.2: Data Fetching (Implementation)

- [ ] T045a-Fetch [Research] [FR-007] Fetch APT datasets for binary systems (Fe-Cr, Fe-Mo, Fe-V, Fe-W) using IDs from T003-Record. **Requirements**:
 1. Implement `code/data/fetch_apt_data.py` to download real APT data.
 2. Construct download URL as `<accession_id>/files/<system>_apt.json?download=1`.
 3. Save to `data/raw/apt_data/<system>_apt.json`.
 4. Update `data_manifest.json` with `source_type: 'experimental'`, `source_id: <accession_id>`, `doi: <doi>`, `url: <constructed URL>`.
 5. If "no_data" flag is present, write `status: "no_data"` to `data/processed/validation_status.json` and continue.
 6. Raise `FetchError` on network failure.
 **Dependency**: Must run after T003-Record.

- [ ] T045c-Fetch [Research] [FR-007] Fetch APT datasets for ternary systems (Fe-Cr-Mo, etc.) using DOIs from T003-Record. **Requirements**:
 1. Extend `code/data/fetch_apt_data.py` to handle ternary DOIs.
 2. Download URL: `https://doi.org/<doi>` (follow redirects).
 3. Save to `data/raw/apt_data/<system>_apt.json`.
 4. Update `data_manifest.json` accordingly.
 5. If "no_data", record status and continue.
 **Dependency**: Must run after T003-Record.

- [ ] T045e-Fetch [Research] [FR-001] [FR-007] Fetch Open CALPHAD parameters using DOI from T003-Record. **Requirements**:
 1. Implement `code/data/download_calphad.py`.
 2. Download URL from DOI (via `https://doi.org/<doi>`).
 3. Verify checksum using **SHA‑256** (hash provided in `research/data_sources.md`).
 4. Save to `data/raw/calphad_params.json`.
 5. If missing, write `status: "no_data"` to `data/processed/validation_status.json` and continue.
 6. Raise `FetchError` on failure.
 **Dependency**: Must run after T003-Record.

- [ ] T045f-Fetch [Research] [FR-002] [FR-007] Fetch pre‑computed DFT energies using DOI from T003-Record. **Requirements**:
 1. Implement `code/data/download_dft_energies.py`.
 2. Download via DOI URL.
 3. Verify checksum (SHA‑256).
 4. Save to `data/raw/dft_energies.json`.
 5. If not found, set a flag `missing=True` (do not raise).
 **Dependency**: Must run after T003-Record.

- [ ] T045f-Gen [Research] [FR-002] [FR-007] Generate a minimal `data/raw/dft_energies.json` with a `MISSING_SOURCE` flag if fetch fails. **Requirements**:
 1. Create `code/data/generate_fallback_dft.py`.
 2. Produce JSON: `{ "source_type": "fallback", "source_id": "missing_source", "MISSING_SOURCE": true }`.
 3. Update `data_manifest.json`.
 **Dependency**: Must run after T045f-Fetch.

- [X] T047b [P] [FR-001] Implement `code/services/thermo_extrapolator.py` to linearly extrapolate missing CALPHAD parameters (500‑900 K) using `scipy.interpolate.interp1d`. **Constraint**: No sklearn regression. **Dependency**: After T050 and T045e-Fetch.

- [ ] T047c [P] Execute and validate `code/services/thermo_extrapolator.py` on a sample set of missing parameters. **Dependency**: Must run after T047b.

- [ ] T048-Script [Research] [FR-001] Create `code/services/thermo_extractor.py`. **Requirements**:
 1. Load `data/raw/calphad_params.json`.
 2. Compute equilibrium bulk compositions for the five ternary systems across a range of elevated temperatures and a range of bulk Cr concentrations spanning from trace levels up to 0.1..
 3. Call `code/services/thermo_extrapolator.py` for any missing parameters.
 4. Save to `data/processed/equilibrium_compositions.csv`.
 5. Update `data_manifest.json` (`source_type: 'derived'`).
 **Dependency**: After T045e-Fetch and T047c.

- [ ] T048-Orchestrate [Research] [FR-001] Create `code/services/thermo_orchestrator.py` to run extraction for **each** ternary system individually. **Requirements**:
 1. Loop over system list `["Fe-Cr-Mo","Fe-Cr-V","Fe-Mo-V","Fe-Cr-W","Fe-Mo-W"]`.
 2. For each, invoke `thermo_extractor.py` with a system argument.
 3. Ensure `code/services/thermo_extrapolator.py` has been executed (depend on T047c).
 **Dependency**: After T048-Script and T047c.

- [ ] T048-FeCrMo [Research] [FR-001] Execute extraction for Fe‑Cr‑Mo. **Dependency**: T048-Orchestrate.

- [ ] T048-FeCrV [Research] [FR-001] Execute extraction for Fe‑Cr‑V. **Dependency**: T048-Orchestrate.

- [ ] T048-FeMoV [Research] [FR-001] Execute extraction for Fe‑Mo‑V. **Dependency**: T048-Orchestrate.

- [ ] T048-FeCrW [Research] [FR-001] Execute extraction for Fe‑Cr‑W. **Dependency**: T048-Orchestrate.

- [ ] T048-FeMoW [Research] [FR-001] Execute extraction for Fe‑Mo‑W. **Dependency**: T048-Orchestrate.

- [ ] T048-Exec [Research] [FR-001] Run `code/services/thermo_orchestrator.py` to generate `data/processed/equilibrium_compositions.csv`. **Dependency**: After all five per‑system tasks above.

- [ ] T049b-Lookup [Research] [FR-002] Create `code/services/supercell_lookup.py`. **Requirements**:
 1. Map supercell identifiers (e.g., `sigma5_fe_cr.cif`) to entries in `data/raw/dft_energies.json`.
 2. Raise informative `KeyError` if no match.
 **Dependency**: After T001c and T045f-Fetch/T045f-Gen.

- [ ] T090-Config [Research] [FR-001] Create `research/synthetic_ground_truth.yaml` with `interaction_coefficients` (default `{Cr_Mo: 0.05, Cr_V: 0.05, Mo_V: 0.05, Cr_W: 0.05, Mo_W: 0.05, V_W: 0.05}`) and `random_seed: 42`. **Dependency**: None.

- [ ] T090-CreateScript [Research] [FR-001] Create `data/generate_ground_truth.py`. **Requirements**:
 1. Load CALPHAD params from `data/raw/calphad_params.json`.
 2. Read interaction coefficients from `research/synthetic_ground_truth.yaml`.
 3. Simulate DFT segregation energies using McLean with injected coefficients and Gaussian noise (seeded).
 4. Output `data/raw/generated_ground_truth.csv`.
 **Dependency**: After T045e-Fetch and T090-Config.

- [ ] T091-Exec [Research] Execute `data/generate_ground_truth.py` to create `data/raw/generated_ground_truth.csv`. **Dependency**: After T090-CreateScript.

- [ ] T092-ManifestUpdate [Research] [FR-007] Update `data_manifest.json` with entry for `generated_ground_truth.csv`. **Dependency**: After T091-Exec.

- [ ] T013-CheckPlaceholder [Research] [FR-002] Verify that `data/raw/dft_energies.json` does **not** contain `MISSING_SOURCE: true`. If it does, abort the scientific pipeline with a clear error message. **Dependency**: After T045f-Fetch and before T013.

- [ ] T013b [Research] [FR-002] Implement `code/data/load_dft_energies.py` to load `data/raw/dft_energies.json`. **Requirements**:
 1. Validate against schema `{system:str, element:str, energy_eV:float, temperature_K:int}`.
 2. Raise error on malformed file.
 **Dependency**: After T045f-Fetch/T045f-Gen.

- [ ] T013 [Research] [FR-002‑Amend] Implement `code/services/load_dft_surrogate.py` to load pre‑computed DFT energies **only if** `T013-CheckPlaceholder` passed. **Dependency**: After T013b and T013-CheckPlaceholder.

- [ ] T013-Exec [Research] Execute `code/services/load_dft_surrogate.py` to generate `data/processed/surrogate_energies.json`. **Dependency**: After T013.

- [ ] T014 [US1] [FR-003] Implement `code/models/mclean.py` (McLean isotherm). **Dependency**: After T013b.

- [ ] T018-FeCrMo [US1] Generate segregation profile for Fe‑Cr‑Mo. **Requirements**:
 1. Load equilibrium compositions from `data/processed/equilibrium_compositions.csv` (filter Fe‑Cr‑Mo rows).
 2. Load surrogate energies from `data/processed/surrogate_energies.json`.
 3. Apply McLean (T014).
 4. Save to `data/processed/segregation_FeCrMo.json`.
 **Dependency**: After T048-Exec, T014, T013-Exec.

- [ ] T018-FeCrV [US1] Same as above for Fe‑Cr‑V → `segregation_FeCrV.json`. **Dependency**: Same.

- [ ] T018-FeMoV [US1] Same as above for Fe‑Mo‑V → `segregation_FeMoV.json`. **Dependency**: Same.

- [ ] T018-FeCrW [US1] Same as above for Fe‑Cr‑W → `segregation_FeCrW.json`. **Dependency**: Same.

- [ ] T018-FeMoW [US1] Same as above for Fe‑Mo‑W → `segregation_FeMoW.json`. **Dependency**: Same.

- [ ] T018-Aggregate [US1] Combine the five JSON files into a single `data/processed/segregation_profiles.json`. **Dependency**: After all five system‑specific tasks.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001a Create `scripts/setup_project.py` … (unchanged)
- [X] T001b Execute `scripts/setup_project.py` … (unchanged)
- [X] T002a Create `requirements.txt` … (unchanged)
- [X] T002b Run `pip install -r requirements.txt` … (unchanged)
- [X] T003 [P] Configure linting … (unchanged)

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T008a Create `code/__init__.py` … (unchanged)
- [X] T004 [P] Create `code/config.py` … (unchanged)
- [X] T008b [P] Configure error handling … (unchanged)
- [X] T049 [P] Implement `code/data/manifest_validator.py` … (unchanged)
- [X] T050 [P] Create `code/data/manifest_schema.json` … (unchanged)
- [X] T047b … (already defined above)
- [X] T047c [P] Execute and validate extrapolator … (already defined above)
- [X] T050-ManifestFinal [P] Finalize `data_manifest.json` … (unchanged)
- [X] T007 [P] Define `code/models/` directory and schemas … (unchanged)

## Phase 3: User Story 1 - Thermodynamic Segregation Profile Generation (Priority: P1) 🎯 MVP

### Tests for User Story 1 (OPTIONAL)

- [X] T010 [P] [US1] Unit test for McLean … (unchanged)
- [X] T011 [P] [US1] Integration test … (unchanged)

### Implementation for User Story 1

- [X] T001c [P] [FR-002] Implement `code/services/gb_service.py` … (unchanged)
- [X] T017 [P] [FR-002] Implement stub `code/services/dft_service.py` (HPC‑ONLY) … (unchanged)
- [X] T013b … (unchanged)
- [ ] T013 [US1] [FR-002‑Amend] Implement surrogate loader … (description updated above)
- [ ] T013-Exec … (description updated above)
- [X] T017c [FR-002] Implement `code/services/thermo_consistency_check.py` … (unchanged)
- [X] T055 [US1] Validation in surrogate loader … (unchanged)
- [X] T014 … (unchanged)
- [ ] T018-FeCrMo … (new per‑system tasks added)
- [ ] T018-FeCrV … (new)
- [ ] T018-FeMoV … (new)
- [ ] T018-FeCrW … (new)
- [ ] T018-FeMoW … (new)
- [ ] T018-Aggregate … (new)

## Phase 4: User Story 2 - Multicomponent Cooperative Effect Analysis (Priority: P2)

### Tests for User Story 2 (OPTIONAL)

- [X] T019 [P] Unit test for interaction term generation … (unchanged)
- [X] T020 [P] Integration test … (unchanged)

### Implementation for User Story 2

- [ ] T021a-CreateScript [US2] Create a single script `code/services/generate_interaction_terms.py` that can be parameterized with an input CSV path and output path. **Requirements**:
 1. Use `PolynomialFeatures(degree=2, include_bias=False)`.
 2. Input columns must include the base solute columns (`Cr`, `Mo`, `V`, `W`) as defined in the schema from T091-Exec.
 3. Output interaction columns exactly: `Cr_Mo`, `Cr_V`, `Mo_V`, `Cr_W`, `Mo_W`, `V_W`.
 **Dependency**: After T091-Exec (synthetic) and T018-Aggregate (scientific).

- [ ] T021a-Exec-Synth [US2] Execute the script on `data/raw/generated_ground_truth.csv` → `data/processed/interaction_terms_synth.csv`. **Dependency**: After T021a-CreateScript.

- [ ] T021a-Exec-Sci [US2] Execute the script on `data/processed/segregation_profiles.json` (converted to CSV via a helper) → `data/processed/interaction_terms_sci.csv`. **Dependency**: After T021a-CreateScript and T018-Aggregate.

- [X] T021b [US2] Implement `code/models/regression.py` (LinearRegression with interaction terms). **Dependency**: After both interaction‑term files exist.

- [ ] T022-Exec-Synth [US2] Run `code/services/mse_comparison.py` on synthetic dataset, output `data/processed/mse_comparison_synth.json`. **Dependency**: After T021b and T021a-Exec-Synth.

- [ ] T022-Exec-Sci [US2] Run `code/services/mse_comparison.py` on scientific dataset, output `data/processed/mse_comparison_sci.json`. **Dependency**: After T021b and T021a-Exec-Sci.

- [ ] T023-Exec-Synth [US2] Run `code/services/significance_test.py` on synthetic regression output, write `data/processed/significance_results_synth.json`. **Dependency**: After T021b and T021a-Exec-Synth.

- [ ] T023-Exec-Sci [US2] Run `code/services/significance_test.py` on scientific regression output, write `data/processed/significance_results_sci.json`. **Dependency**: After T021b and T021a-Exec-Sci.

- [X] T024a [US2] [FR-006] Implement `code/services/plotter.py` to generate heatmaps from `data/processed/segregation_profiles.json`. **Dependency**: After T018-Aggregate.

- [ ] T024b [US2] Generate `data/figures/segregation_heatmap.png`. **Dependency**: After T024a.

- [X] T021c [US2] [FR-004] Implement `code/services/statistical_validation.py` to combine MSE reduction and significance checks (requires outputs from T022‑Exec‑* and T023‑Exec‑*). **Dependency**: After T022‑Exec‑* and T023‑Exec‑*.

- [X] T025 [US2] Write `data/processed/cooperative_effects_analysis.json` with coefficients, p‑values, MSE reduction. **Dependency**: After T021c.

- [ ] T026 [US2] Flag systems with no significant cooperative effects. **Dependency**: After T025.

## Phase 5: User Story 3 - Model Generalizability and Cross‑Validation (Priority: P3)

### Tests for User Story 3 (OPTIONAL)

- [X] T027 [P] Unit test for k‑fold splitting … (unchanged)
- [X] T028 [P] Integration test for CV metrics … (unchanged)

### Implementation for User Story 3

- [X] T029 [P] [FR-005] Implement `code/models/validation.py` (5 (2604.10702, https://arxiv.org/abs/2604.10702)‑fold CV). **Dependency**: After T021b.

- [ ] T029-Exec [US3] Execute CV routine, store intermediate results in memory. **Dependency**: After T029.

- [ ] T030 [US3] Calculate R² & MSE per fold, compute mean & std‑dev, log “Mean R²: X, Std Dev: Y”. **Dependency**: After T029-Exec.

- [ ] T030-Exec [US3] Run `code/services/cv_reporter.py` to write `data/processed/cv_metrics.json`. **Dependency**: After T030.

- [ ] T031 [US3] Perform transferability check (train on Fe‑Cr‑Mo, test on Fe‑Cr‑V). **Dependency**: After T029-Exec.

- [ ] T032 [US3] Add overfitting detection logic (high training vs low validation). **Dependency**: After T030-Exec.

- [X] T033 [US3] Generate `data/processed/cross_validation_results.json`. **Dependency**: After T030-Exec.

## Phase 6: Validation & Experimental Strategy (Priority: P1 - Research Review)

### Experimental Validation Tasks

- [ ] T095a-Check [Validation] Check for presence of APT data in `data/raw/apt_data/`. **Dependency**: After T018-Aggregate and T045a‑Fetch/T045c‑Fetch.

- [ ] T095c-ReportNoData [Validation] Generate `data/processed/sc003_binary_validation.json` with status `"N/A"` and a brief rationale when binary APT data is missing. **Dependency**: After T095a-Check.

- [ ] T095c-Exec [Validation] If binary APT data is present, compute RMSE & MAE between computed GB concentrations and experimental APT concentrations:
 1. Align temperature grids via linear interpolation of APT data onto the computed temperature points.
 2. Use formulas `RMSE = sqrt(mean((pred - exp)^2))` and `MAE = mean(|pred - exp|)`.
 3. Write results to `data/processed/sc003_binary_validation.json`.
 **Dependency**: After T095a-Check; falls back to T095c-ReportNoData when no data.

- [ ] T095e-Exec [Validation] If **all** binary systems lack data, generate `research/sc003_fallback_report.md` stating the failure and that only surrogate consistency checks are possible. **Dependency**: After T095c-ReportNoData detects complete absence.

- [ ] T095f [Validation] Generate `research/experimental_gap_report.md` summarizing lack of ternary APT data, referencing `research/data_sources.md`. **Dependency**: After T095a-Check.

- [ ] T055b [SC‑003] Compute overall RMSE/MAE across binaries with data, write `data/processed/sc003_binary_metrics.json`. **Dependency**: After T095c-Exec (only when data present).

- [ ] T095b [Validation] PIPELINE‑ONLY: Compare regression coefficients against synthetic ground truth (for pipeline validation). **Dependency**: After T025 and T091-Exec.

- [ ] T096 [Validation] Write `research/validation_report.md` summarizing pipeline validation (T095b), experimental validation (T095c‑Exec / T095c‑ReportNoData), statistical validation, and note that experimental measurement is pending. **Dependency**: After T095c‑Exec / T095c‑ReportNoData, T095f, T095e‑Exec.

- [ ] T100 [Review‑Response] Create `research/experimental_validation_plan.md` describing Atom Probe Tomography apparatus, detection limits, specimen preparation, and cite DOI 10.1016/j.actamat.2020.01.015. **Dependency**: None (can run in parallel).

## Phase 7: Review Response & Documentation (Priority: P1 - Research Review)

- [ ] T101 [Review‑Response] Update `research/data_sources.md` with "Experimental Validation Apparatus" section describing APT setup, detection limits, sample prep, and literature table. **Dependency**: None.

- [ ] T102 [Review‑Response] Extend `research/experimental_validation_plan.md` with "Detection Limit Analysis": compute theoretical detection limit using Equation (3) from DOI 10.1016/j.actamat.2020.01.015 and compare to predicted GB concentrations (from T018‑Aggregate). Flag “Below Detection Limit” where appropriate. **Dependency**: After T101 and T018‑Aggregate.

- [ ] T103 [Review‑Response] Revise `research/validation_report.md` to include a "Gap Analysis" section linking computational results with the experimental plan, explicitly stating that quantitative validation requires the APT apparatus defined in T100/T101. **Dependency**: After T102 and T096.

## Phase 8: Finalization & Clean‑up

- [ ] T200 Review all tasks for consistency, ensure every FR/SC is covered, placeholders only where permitted, and amendment workflow is complete.
- [ ] T201 Run full pipeline on CI to verify no hard errors; ensure graceful handling of missing core data results in clear reporting rather than abrupt termination.
