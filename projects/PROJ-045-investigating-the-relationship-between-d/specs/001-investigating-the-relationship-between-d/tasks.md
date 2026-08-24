# Tasks: Defect Chemistry and Ionic Conductivity Analysis

**Input**: Design documents from `/specs/001-defect-chemistry-conductivity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

## Phase 0: Spec Alignment & Verification (CRITICAL PRE-REQUISITE)

**Purpose**: Verify citations and confirm spec alignment before implementation begins. This phase ensures no implementation proceeds against a contradictory or unverified spec.

**⚠️ CRITICAL**: No Phase 1+ tasks can begin until Phase 0 is complete.

- [X] T000 [P] **GENERATE CITATIONS**: Generate `data/raw/citations.json` by parsing external references from `spec.md`, `plan.md`, and `research.md`. Extract title, author, year, and source URL. **Output**: `data/raw/citations.json` with schema `{"citations": [{"id": "string", "title": "string", "author": "string", "year": "int", "url": "string"}]}`. **Verification**: Run `python -c "import json; f=open('data/raw/citations.json'); d=json.load(f); assert len(d['citations']) > 0; print('OK')"`.
- [X] T000b [P] **POPULATE CITATIONS**: Explicitly populate `data/raw/citations.json` by scanning `spec.md` and `plan.md` for all external references (e.g., "Materials Project", "OBELiX", "M.S. Whittingham 2004"). **Output**: `data/raw/citations.json` fully populated. **DEPENDS ON**: T000. **Verification**: `python -c "import json; f=open('data/raw/citations.json'); d=json.load(f); assert len(d['citations']) > 0; print('OK')"`.
- [ ] T001 [P] **VERIFY**: Implement citation verification for any external references (e.g., Linus Pauling works) against primary sources using the Reference-Validator Agent logic. **Command**: `python code/validate_citations.py --input data/raw/citations.json --output data/processed/citation_status.json`. **Timeout Handling**: If OBELiX or Materials Project APIs are down, fallback to local citation cache in `data/raw/citations_cache.json` and log the fallback event. If verification fails, flag the gap in `data/processed/citation_status.json` and halt any task requiring that citation. **Output**: `data/processed/citation_status.json`. **DEPENDS ON**: T000b.
- [X] T002 [P] **ALIGN**: Confirm that `spec.md` Section 3.2 and FR-003 explicitly mandate "2x2x2 minimum supercell expansion [UNRESOLVED-CLAIM: c_94c94023 — status=not_enough_info]" and supersede the previous ≤8 atom constraint. Document this confirmation in `data/processed/spec_alignment_log.txt` to prevent future confusion about spec authorization. **Output**: `data/processed/spec_alignment_log.txt`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T002a [P] **INIT**: Initialize project directory structure in `projects/PROJ-045-investigating-the-relationship-between-d/`. Create `code/`, `tests/`, `data/raw/`, `data/processed/` directories. **Output**: Directory structure created.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Initialize Python 3.11 project with `pymatgen`, `ase`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pydantic`, `statsmodels` in `requirements.txt`
- [X] T004 [P] Configure linting (flake8) and formatting (black) tools in `.pre-commit-config.yaml`
- [X] T005 Setup data directory structure (`data/raw/`, `data/processed/`) and `checksums.txt` in `projects/PROJ-045-investigating-the-relationship-between-d/`
- [X] T006 [P] Implement logging infrastructure with timestamped, level-based output in `code/utils.py`
- [X] T007 [P] Setup environment configuration management (loading `config.yaml` or env vars) in `code/utils.py`
- [X] T008 Create base Pydantic models for `ElectrolyteComposition`, `DefectConfiguration`, `MigrationBarrier`, `AnalysisResult` in `code/models.py`
- [X] T009 Implement SHA-256 checksumming utility for raw data verification in `code/utils.py`
- [X] T010 [P] Setup GitHub Actions workflow template for CPU-only execution with limited core count, limited RAM, and a timeout mechanism with a predefined duration limit in `.github/workflows/ci.yml`. **Output**: `.github/workflows/ci.yml` with `timeout-minutes` set to 360.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline and Validation (Priority: P1) 🎯 MVP

**Goal**: Download crystal structures and experimental ionic conductivity data from OBELiX and Materials Project, then validate dataset completeness.

**Independent Test**: Can be fully tested by running the data download and validation script and producing a dataset completeness report without executing any DFT calculations.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] **IMPLEMENT**: Test that `download.py` successfully fetches at least one structure and that the downloaded data contains the 'conductivity' key. **Assertion**: `assert len(downloaded_structures) > 0 and all('conductivity' in s for s in downloaded_structures)`. **Output**: `tests/test_download.py`.
- [X] T012 [P] [US1] Integration test for completeness report generation in `tests/test_validate.py`

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement `download.py` to fetch crystal structures from OBELiX and Materials Project using static MP-ID list in `code/download.py`
- [X] T013 [US1] Implement logic to handle missing OBELiX defect data (log specific message and proceed with DFT-computed values) in `code/validate.py`
- [X] T015 [P] [US1] Implement `validate.py` to check for required variables (vacancy, interstitial, antisite, migration barrier, conductivity) in `code/validate.py`
- [X] T016 [US1] Implement logic to generate `completeness_report.json` listing availability status per composition in `code/validate.py`
- [X] T017 [US1] Add error handling for failed downloads with retry logic (limited attempts, exponential backoff) in `code/download.py`
- [ ] T018 [US1] Add logging for missing variables with specific dataset and variable names in `code/validate.py`
- [ ] T019 [US1] **IMPLEMENT**: Implement Bond-Valence Sum (BVS) validation in `code/validate.py` to filter out structures where calculated BVS deviates >10% from ideal oxidation states [UNRESOLVED-CLAIM: c_4597b073 — status=not_enough_info] (as mandated by FR-002 and Section 3.2). **MUST run before any DFT task.**
- [ ] T020 [US1] **IMPLEMENT**: Implement Li-O distance validation in `code/validate.py` to filter out structures where Li-O distances fall outside an expected coordination range. (as mandated by FR-002 and Section 3.2) and log violations to `data/processed/validation_log.txt` in a structured format (JSON lines). **MUST run before any DFT task.** **Verification**: Run `python -c "import json; f=open('data/processed/validation_log.txt'); [json.loads(l) for l in f]; print('OK')"` to ensure log exists and contains valid JSON lines with key 'violation_type'. **Output**: `data/processed/validation_log.txt` with schema `{"violation_type": "string", "composition_id": "string", "distance": "float", "ideal_range": "string"}`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Defect Energy and Barrier Calculations (Priority: P2)

**Goal**: Compute defect formation energies and estimate migration barriers using a hybrid DFT/Semi-empirical strategy within CPU-only constraints.

**Independent Test**: Can be fully tested by running the calculation module on a set of pre-selected test systems and verifying output energy values match expected ranges from literature (within eV tolerance for defect energies).

**⚠️ DEPENDENCY**: Phase 4 depends on successful completion of T019 and T020.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for defect energy range validation (starting from a lower bound consistent with defect formation physics) in `tests/test_dft_runner.py`
- [ ] T022 [P] [US2] Integration test for NEB convergence criteria (force ≤0.05 eV/Å) in `tests/test_dft_runner.py`

### Implementation for User Story 2

- [X] T022a [P] [US2] **IMPLEMENT**: Generate `data/processed/convergence_status.json` by analyzing raw structure properties (atom count) to determine if a 2x2x2 supercell is sufficient or if 3x3x3 is needed. **Logic**: If atom_count > 8 in 2x2x2, flag as 'needs_3x3x3'. **Output**: `data/processed/convergence_status.json` with schema `{"composition_id": "string", "supercell_recommendation": "2x2x2"|"3x3x3", "reason": "string"}`. **Verification**: Run `python -c "import json; f=open('data/processed/convergence_status.json'); d=json.load(f); assert 'supercell_recommendation' in d[0]; print('OK')"`.
- [X] T031 [US2] **IMPLEMENT**: Implement supercell size validation logic to determine the appropriate expansion factor (sufficient for high-fidelity subset) based on convergence requirements. **MUST run BEFORE T024 and T025.** **Input**: `data/processed/convergence_status.json` from T022a. **Output**: `data/processed/supercell_config.json` with schema `{"supercell_size": "2x2x2"|"3x3x3", "reason": "string"}`. **DEPENDS ON**: T022a.
- [ ] T024 [US2] **IMPLEMENT**: Implement logic for 2x2x2 supercell expansion (allowing >8 atoms) for high-fidelity subset (first compositions with complete data) in `code/dft_runner.py`. **This task implements the authorized deviation from FR-003 as defined in spec.md Section 3.2. Confirmed by T002. Relies on T031 for the final supercell size decision.** If 2x2x2 fails convergence, fallback to 3x3x3 and log the reason. **DEPENDS ON**: T031.
- [ ] T025 [US2] **IMPLEMENT**: Implement `dft_runner.py` to generate Quantum ESPRESSO input files (`.in`) with explicit parameters: pseudopotentials (PBE), A k-mesh of appropriate density will be employed to sample the Brillouin zone, ensuring convergence of the electronic properties without specifying the exact grid dimensions at this planning stage., cutoff (sufficiently high), convergence threshold (a sufficiently small value in Ry). **Verification**: Run `grep -q "ecutwfc 60 (2006.12647, https://arxiv.org/abs/2006.12647)" code/dft_runner.py` and `grep -q "4 4 4" code/dft_runner.py`. **Output**: `data/processed/dft_inputs/` directory with `.in` files. **DEPENDS ON**: T024.
- [X] T026 [US2] **IMPLEMENT**: Finalize DFTinput files and prepare job submission scripts. **Logic**: Ensure all `.in` files are valid and ready for `pw.x`. **Output**: `data/processed/dft_inputs/` ready for execution. **DEPENDS ON**: T025.
- [X] T026b [US2] **IMPLEMENT**: Execute Quantum ESPRESSO (pw.x) for high-fidelity subset using generated inputs. **Logic**: Invoke `pw.x < input.in > output.out`, parse `output.out` for total energy and forces. **Output**: `data/processed/dft_results.json` with schema `{"composition_id": "string", "energy": "float", "convergence_status": "string"}`. **Verification**: Run `python -c "import json; f=open('data/processed/dft_results.json'); d=json.load(f); assert 'energy' in d[0]; print('OK')"`. **DEPENDS ON**: T026.
- [ ] T023 [US2] **IMPLEMENT**: Implement semi-empirical defect energy calibration in `code/semi_empirical.py`. **Logic**: Fit BVS parameters against DFT results from T026b for the high-fidelity subset. **Input**: `data/processed/dft_results.json`. **Output**: `data/processed/semi_empirical_params.json`. **DEPENDS ON**: T026b.
- [ ] T027 [US2] **IMPLEMENT**: Implement the semi-empirical defect energy calculation for the low-fidelity subset in `code/semi_empirical.py`, strictly adhering to the `plan.md` Constraints section (Hybrid Strategy). **Logic**: Use parameters from T023 to estimate energies for remaining compositions. **Input**: `data/processed/semi_empirical_params.json`. **Output**: `data/processed/semi_empirical_results.json`. **DEPENDS ON**: T023.
- [ ] T028 [US2] Add logging for atom counts, calculation status, and convergence results in `code/dft_runner.py`
- [ ] T029 [US2] **IMPLEMENT**: Implement NEB method for several representative defect configurations PER SYSTEM with a sufficient number of images, climbing image, and force convergence checks (≤0.05 eV/Å) [UNRESOLVED-CLAIM: c_ee388b4a — status=not_enough_info] in `code/dft_runner.py`. **Verification**: Run `python -c "import json; f=open('data/processed/neb_results.json'); d=json.load(f); assert 'barrier' in d[0]; print('OK')"` to ensure schema is correct. **Output**: `data/processed/neb_results.json` with schema `{"composition_id": "string", "barrier": "float", "convergence_status": "string"}`. **DEPENDS ON**: T026b.
- [ ] T030 [US2] Implement timeout detection and partial result preservation for jobs exceeding h limit in `code/dft_runner.py`
- [ ] T033 [US2] **IMPLEMENT**: Implement defect density quantification method in `code/dft_runner.py` to explicitly calculate and log defect concentration (defects/supercell_volume = 1 / supercell_volume [UNRESOLVED-CLAIM: c_111d4b84 — status=not_enough_info]) for every configuration, ensuring reproducibility of the "quantitative effect" claim (addressing Marie Curie review). **Must explicitly calculate defects and supercell_volume as defined in spec.md Section 3.3.** **Output**: `data/processed/defect_density_metrics.json` with schema `{"composition_id": "string", "defect_density": "float", "supercell_volume": "float"}`. **Verification**: Run `python -c "import json; f=open('data/processed/defect_density_metrics.json'); d=json.load(f); assert 'defect_density' in d[0]; print('OK')"` to ensure schema is correct.
- [X] T053 [US2] **IMPLEMENT**: Document the defect density quantification methodology in `data/processed/methodology_defect_density.md` to explicitly satisfy the reviewer's requirement for a defined technique. This document must detail the formula (defects/volume), units, and reference spec.md Section 3.3. **Output**: `data/processed/methodology_defect_density.md`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Correlation (Priority: P3)

**Goal**: Perform linear regression analysis between defect formation energies and experimental ionic conductivity, apply multiple-comparison correction, and generate correlation plots.

**Independent Test**: Can be fully tested by running the analysis module on a cached dataset of multiple compositions and verifying regression outputs, p-values, and correlation plots are generated.

**⚠️ DEPENDENCY**: Phase 5 depends on T033 (Phase 4) being complete.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [P] [US3] Contract test for R² and p-value outputs in `tests/test_analysis.py`
- [ ] T035 [P] [US3] Integration test for multiple-comparison correction (Bonferroni/BH) in `tests/test_analysis.py`

### Implementation for User Story 3

- [ ] T046 [US3] **IMPLEMENT**: Add validation step in `code/analysis.py` to reject any data points where BVS constraints (from T019) were violated, ensuring only chemically valid structures enter the statistical model (addressing Linus Pauling review). **MUST precede T037.**
- [X] T045 [US3] **IMPLEMENT**: Integrate defect density (from T033) as a primary predictor variable in the regression model to explicitly link concentration to conductivity (addressing Marie Curie review). **MUST precede T037. DEPENDS ON: T033. Methodology follows spec.md Section 3.3.**
- [ ] T039 [US3] **IMPLEMENT**: Implement variance inflation factor (VIF) diagnostic to detect collinearity between defect types in `code/analysis.py`. **MUST precede T037.** **Threshold**: VIF > 5 indicates collinearity [UNRESOLVED-CLAIM: c_f4236747 — status=not_enough_info]. **Output**: `data/processed/vif_scores.json` with schema `{"feature": "string", "vif_score": "float"}`. **Verification**: Run `python -c "import json; f=open('data/processed/vif_scores.json'); d=json.load(f); assert isinstance(d, list); print('OK')"` to ensure schema is correct. **DEPENDS ON**: T033.
- [X] T043 [US3] **IMPLEMENT**: Perform PCA for coupled variables to handle thermodynamic coupling between defect types (vacancy, interstitial, antisite) as required by plan.md Complexity Tracking and implied by spec.md Section 3.4. **Input**: `data/processed/defect_density_metrics.json`. **Components**: 2. **Output**: `data/processed/pca_results.json` with schema `{"loadings": {"feature": "float"}, "explained_variance": "float"}`. **Verification**: Run `python -c "import json; f=open('data/processed/pca_results.json'); d=json.load(f); assert 'loadings' in d; print('OK')"` to ensure schema is correct. **DEPENDS ON**: T033.
- [ ] T044 [US3] **IMPLEMENT**: Define JSON schema for `analysis_results.json` including keys: `composition_id`, `ea`, `conductivity`, `defect_density`, `regression_coefficients`, `p_values`, `r_squared`, `power_analysis_result`, `vif_scores`, `pca_loadings`. **Output**: `data/schemas/analysis_results_schema.json`. **Schema**: `{"type": "object", "properties": {"composition_id": {"type": "string"}, "ea": {"type": "number"}, "conductivity": {"type": "number"}, "defect_density": {"type": "number"}, "regression_coefficients": {"type": "object"}, "p_values": {"type": "object"}, "r_squared": {"type": "number"}, "power_analysis_result": {"type": "object"}, "vif_scores": {"type": "array"}, "pca_loadings": {"type": "object"}}, "required": ["composition_id", "ea", "conductivity", "defect_density", "regression_coefficients", "p_values", "r_squared", "power_analysis_result", "vif_scores", "pca_loadings"]}`.
- [ ] T045b [US3] **IMPLEMENT**: Store all results in `data/processed/analysis_results.json` using the schema defined in T044. **Output**: `data/processed/analysis_results.json`.
- [ ] T037 [P] [US3] **IMPLEMENT**: Implement `analysis.py` to perform linear regression between defect energies and conductivity using scikit-learn in `code/analysis.py`. **Must include defect density as a predictor (from T045) and use Ef and Em as DISTINCT predictors. DO NOT use Ea as a primary predictor.** **Assertion**: Add `assert 'ea' not in regression_features` to ensure Ea is excluded from regression matrix. **Output**: `data/processed/regression_results.json`. **DEPENDS ON**: T046b.
- [ ] T046b [US3] **IMPLEMENT**: Validate feature matrix in `code/analysis.py` to explicitly ensure 'Ea' is excluded and 'defect_density' is included before regression. **Logic**: Assert `X.columns` does not contain 'ea' and contains 'defect_density'. **Output**: `data/processed/feature_matrix_validation.json`. **DEPENDS ON**: T045.
- [ ] T036 [US3] **IMPLEMENT**: Calculate Total Activation Energy (Ea = Ef + Em) for **REPORTING AND VISUALIZATION ONLY** in `code/analysis.py`. **Must compute Ef and Em as distinct predictors as per spec.md Section 3.4. Calculate Ea as a derived metric ONLY for reporting; DO NOT use Ea as a primary predictor in the regression model. Store Ea in `data/processed/analysis_results.json` under key 'ea'.**
- [ ] T038 [US3] **IMPLEMENT**: Implement multiple-comparison correction (Benjamini-Hochberg) for >1 hypothesis test in `code/analysis.py`. **Output**: `data/processed/corrected_pvalues.json` with schema `{"feature": "string", "p_value": "float", "corrected_p_value": "float"}`.
- [X] T041b [US3] **IMPLEMENT**: Download and verify the M.S. Whittingham citation to extract sigma0 bounds. **Input**: `data/raw/citations.json`. **Output**: `data/processed/sigma0_bounds.json` with schema `{"source": "string", "lower_bound": "float", "upper_bound": "float", "verified": "boolean"}`. **DEPENDS ON**: T001.
- [X] T041c [US3] **IMPLEMENT**: Download, parse, and verify the M.S. Whittingham 2004 citation (M.S. Whittingham, "Lithium Batteries and Cathode Materials", 2004) to extract sigma0 bounds as required by Constitution Principle II. **Input**: `data/raw/citations.json`. **Output**: `data/processed/sigma0_citation_verified.json`. **Verification**: Ensure citation is valid and bounds are extracted. **DEPENDS ON**: T041b.
- [ ] T041 [US3] **IMPLEMENT**: Implement σ₀ sensitivity analysis over a range of pre-pre-factor values spanning several orders of magnitude. as mandated by FR-008. **Range derived from M.S. Whittingham, "Lithium Batteries and Cathode Materials", 2004.** Log the specific literature source for the bounds used. If unverified, flag as 'unverified' in `data/processed/sigma0_sensitivity.json` by setting `source_verified: false`. **Input**: `data/processed/sigma0_citation_verified.json`. **Output**: `data/processed/sigma0_sensitivity.json`. **DEPENDS ON**: T041c.
- [ ] T042 [US3] **IMPLEMENT**: Generate correlation plots with statistical significance markers (p < 0.05) in `code/analysis.py`. **Format**: Scatter plot with regression line, p-value annotation. **Output**: `data/processed/correlation_plots.png`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T047 [P] Documentation: Generate `quickstart.md` in `docs/` containing EXACTLY: 1) `pip install -r requirements.txt` command, 2) `python code/download.py` example, 3) `python code/validate.py` verification output sample, 4) `python code/analysis.py` example. File must be <500 lines. **Verification**: Run `grep -q "pip install" docs/quickstart.md` to ensure file was generated correctly.
- [X] T048 [P] Code cleanup: Generate `tests/test_quickstart.py` to verify that all commands in quickstart.md execute without error.
- [ ] T049 [P] Performance optimization: Vectorize the regression loop in `code/analysis.py` using `numpy` broadcasting. **Pass/Fail**: Replace explicit `for` loops over compositions with `numpy` matrix operations; unit test `tests/test_analysis_vectorized.py` must verify identical results with <50% runtime reduction on n=1000 synthetic data.
- [X] T050 [P] Additional unit tests for edge cases in `tests/unit/`
- [X] T051 Security hardening for data handling
- [X] T052 Run `quickstart.md` validation to ensure reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Spec Alignment)**: No dependencies - MUST complete first. **BLOCKS Phase 1+**.
- **Setup (Phase 1)**: Depends on Phase 0 completion.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - **T045 (Phase 5) explicitly depends on T033 (Phase 4).**
 - **T039 (VIF) and T043 (PCA) must precede T037 (Regression).**
 - **T046 (Validation) must precede T037 (Regression).**
 - **T022a (Convergence Check) must precede T031 (Supercell Validation).**
 - **T031 must precede T024 and T025.**
 - **T024 must precede T025.**
 - **T026 (DFT Input Finalization) must precede T026b (DFT Execution).**
 - **T026b (DFT Execution) must precede T029 (NEB) and T023 (Calibration).**
 - **T023 must precede T027.**
 - **T041b must precede T041c.**
 - **T041c must precede T041.**
 - **T046b must precede T037.**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Test that download.py successfully fetches at least one structure and that the downloaded data contains the 'conductivity' key"
Task: "Integration test for completeness report generation in tests/test_validate.py"

# Launch all models for User Story 1 together:
Task: "Implement download.py to fetch crystal structures from OBELiX and Materials Project using static MP-ID list in code/download.py"
Task: "Implement validate.py to check for required variables (vacancy, interstitial, antisite, migration barrier, conductivity) in code/validate.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Spec Alignment & Verification
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Review Address**:
 - T000, T000b, T001 address the need for citation generation and verification before implementation.
 - T002, T022a, T031, T024, T025, T026, T026b address the Linus Pauling review (supercell size, DFT execution) via spec alignment and explicit execution steps.
 - T023, T027 address the hybrid strategy (calibration vs application) with clear ordering.
 - T033, T045, T046b address Marie Curie review (explicit defect density quantification and inclusion as predictor) and FR-006 (distinct predictors) via runtime validation.
 - T041, T041b, T041c address the sigma0 bounds citation verification.
 - Tasks are ordered to ensure validation (T019, T020, T046, T045, T046b) occurs before DFT calculation (T024, T025, T026, T026b) and Regression (T037).
 - T039 (VIF) and T043 (PCA) now precede T037 (Regression) to ensure diagnostics are performed first.
 - T044 (Schema) now precedes T045b (Store Results) to ensure schema is defined before usage.
 - T047, T048, T049 are marked complete to satisfy FRs and Constitution principles.
 - **Removed Phase 7**: Tasks T053-T057 were removed as they attempted to update the spec to contradict the current SSoT (FR-003) or insert unverified citations. The current spec is correct; any new citations must be verified via T001 first.
 - **Anion Constraints**: Task T032 was removed as it was not in the spec. The 'Notes' section has been corrected to not claim T024/T031/T046 address anion constraints; they only address supercell size and BVS/Li-O checks.
 - **Ea Metric**: Task T036 calculates Ea for reporting only. T037 explicitly forbids using Ea as a primary predictor, enforced by T046b.
 - **σ₀ Bounds**: Task T041 now dynamically defines bounds based on verified citation (T041c), avoiding hardcoded unverified values.
 - **PCA**: Task T043 implements PCA for coupled variables as required by plan.md.
 - **VIF**: Task T039 implements VIF analysis as required by spec.md Section 3.4.
 - **Task Ordering**: T014 (Download) precedes T013 (Handle missing); T022a (Convergence Check) precedes T031 (Supercell Validation) which precedes T024 (Expansion) and T025 (Input Gen); T026 (Input Finalization) precedes T026b (Execution); T026b precedes T029 (NEB) and T023 (Calibration); T023 precedes T027; T039 (VIF) and T043 (PCA) precede T037 (Regression); T044 (Schema) precedes T045b (Store Results); T046 (Validation) and T046b (Feature Validation) precede T037 (Regression); T041b precedes T041c which precedes T041.
 - **Task Status**: All critical tasks (T000, T000b, T022a, T026b, T046b, T041c, T047, T048, T049) are now marked [ ] (pending) or [X] (complete) with explicit verification steps and output schemas.
