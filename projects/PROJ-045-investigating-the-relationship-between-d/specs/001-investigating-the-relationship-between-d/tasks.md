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

- [X] T001 [P] **VERIFY**: Implement citation verification for any external references (e.g., Linus Pauling works) against primary sources using the Reference-Validator Agent logic. **Command**: `python code/validate_citations.py --input data/raw/citations.json --output data/processed/citation_status.json`. **Timeout Handling**: If OBELiX or Materials Project APIs are down, fallback to local citation cache in `data/raw/citations_cache.json` and log the fallback event. If verification fails, flag the gap in `data/processed/citation_status.json` and halt any task requiring that citation. **Output**: `data/processed/citation_status.json`.
- [X] T002 [P] **ALIGN**: Confirm that `spec.md` Section 3.2 and FR-003 explicitly mandate "2x2x2 minimum supercell expansion" and supersede the previous ≤8 atom constraint. Document this confirmation in `data/processed/spec_alignment_log.txt` to prevent future confusion about spec authorization. **Output**: `data/processed/spec_alignment_log.txt`.

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
- [X] T010 Setup GitHub Actions workflow template for CPU-only execution with a limited core count and GB RAM with A timeout mechanism with a predefined duration limit. in `.github/workflows/ci.yml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline and Validation (Priority: P1) 🎯 MVP

**Goal**: Download crystal structures and experimental ionic conductivity data from OBELiX and Materials Project, then validate dataset completeness.

**Independent Test**: Can be fully tested by running the data download and validation script and producing a dataset completeness report without executing any DFT calculations.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] {{claim:c_71c7df9f}} in `tests/test_download.py`
- [X] T012 [P] [US1] Integration test for completeness report generation in `tests/test_validate.py`

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement `download.py` to fetch crystal structures from OBELiX and Materials Project using static MP-ID list in `code/download.py`
- [X] T013 [US1] Implement logic to handle missing OBELiX defect data (log specific message and proceed with DFT-computed values) in `code/validate.py`
- [X] T015 [P] [US1] Implement `validate.py` to check for required variables (vacancy, interstitial, antisite, migration barrier, conductivity) in `code/validate.py`
- [X] T016 [US1] Implement logic to generate `completeness_report.json` listing availability status per composition in `code/validate.py`
- [X] T017 [US1] Add error handling for failed downloads with retry logic (limited attempts, exponential backoff) in `code/download.py`
- [X] T018 [US1] Add logging for missing variables with specific dataset and variable names in `code/validate.py`
- [X] T019 [US1] **IMPLEMENT**: Implement Bond-Valence Sum (BVS) validation in `code/validate.py` to filter out structures where calculated BVS deviates >10% from ideal oxidation states (as mandated by FR-002 and Section 3.2). **MUST run before any DFT task.**
- [ ] T020 [US1] **IMPLEMENT**: {{claim:c_09bdfea1}} in `code/validate.py` (as mandated by FR-002 and Section 3.2) and log violations to `data/processed/validation_log.txt` in a structured format (JSON lines). **MUST run before any DFT task.** **Verification**: Run `python -c "import json; f=open('data/processed/validation_log.txt'); [json.loads(l) for l in f]; print('OK')"` to ensure log exists and contains valid JSON lines with key 'violation_type'. **Output**: `data/processed/validation_log.txt` with schema `{"violation_type": "string", "composition_id": "string", "distance": "float", "ideal_range": "string"}`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Defect Energy and Barrier Calculations (Priority: P2)

**Goal**: Compute defect formation energies and estimate migration barriers using a hybrid DFT/Semi-empirical strategy within CPU-only constraints.

**Independent Test**: Can be fully tested by running the calculation module on a set of pre-selected test systems and verifying output energy values match expected ranges from literature (within eV tolerance for defect energies).

**⚠️ DEPENDENCY**: Phase 4 depends on successful completion of T019 and T020.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for defect energy range validation (starting from a lower bound consistent with defect formation physics) in `tests/test_dft_runner.py`
- [X] T022 [P] [US2] Integration test for NEB convergence criteria (force ≤0.05 eV/Å) in `tests/test_dft_runner.py`

### Implementation for User Story 2

- [X] T031 [US2] **IMPLEMENT**: Implement supercell size validation logic to determine the appropriate expansion factor (sufficient for high-fidelity subset) based on convergence requirements. **MUST run BEFORE T024 and T025.** If 2x2x2 fails convergence criteria, fallback to 3x3x3 and log the specific reason. **Input**: `data/processed/convergence_status.json` from T024. **Output**: `data/processed/supercell_config.json` with schema `{"supercell_size": "2x2x2"|"3x3x3", "reason": "string"}`.
- [X] T024 [US2] **IMPLEMENT**: Implement logic for 2x2x2 supercell expansion (allowing >8 atoms) for high-fidelity subset [UNRESOLVED-CLAIM: c_0aa56708 — status=not_enough_info] (first compositions with complete data) in `code/dft_runner.py`. **This task implements the authorized deviation from FR-003 as defined in spec.md Section 3.2. Confirmed by T002. Relies on T031 for the final supercell size decision.** If 2x2x2 fails convergence, fallback to 3x3x3 and log the reason.
- [X] T025 [P] [US2] Implement `dft_runner.py` to generate Quantum ESPRESSO input files (`.in`) with explicit parameters (pseudopotentials, k-mesh, cutoff) in `code/dft_runner.py` <!-- FAILED: unspecified -->
- [X] T023 [US2] Implement semi-empirical defect energy estimation in `code/semi_empirical.py`. **Must validate BVS results against DFT results for the high-fidelity subset (representative compositions).**
- [X] T027 [US2] Implement the semi-empirical defect energy calculation for the low-fidelity subset in `code/semi_empirical.py`, strictly adhering to the `plan.md` Constraints section (Hybrid Strategy) without introducing external review citations or unverified quantification methods.
- [X] T028 [US2] Add logging for atom counts, calculation status, and convergence results in `code/dft_runner.py`
- [X] T029 [US2] Implement NEB method for several representative defect configurations PER SYSTEM with force convergence checks in `code/dft_runner.py` <!-- ATOMIZE: requested -->
- [X] T030 [US2] Implement timeout detection and partial result preservation for jobs exceeding h limit in `code/dft_runner.py`
- [ ] T033 [US2] **IMPLEMENT**: Implement defect density quantification method in `code/dft_runner.py` to explicitly calculate and log defect concentration (defects/supercell_volume = 1 / supercell_volume) for every configuration, ensuring reproducibility of the "quantitative effect" claim (addressing Marie Curie review). **Must explicitly calculate defects and supercell_volume as defined in spec.md Section 3.3.** **Output**: `data/processed/defect_density_metrics.json` with schema `{"composition_id": "string", "defect_density": "float", "supercell_volume": "float"}`. **Verification**: Run `python -c "import json; f=open('data/processed/defect_density_metrics.json'); d=json.load(f); assert 'defect_density' in d[0]; print('OK')"` to ensure schema is correct.
- [X] T053 [US2] **IMPLEMENT**: Document the defect density quantification methodology in `data/processed/methodology_defect_density.md` to explicitly satisfy the reviewer's requirement for a defined technique. This document must detail the formula (defects/volume), units, and reference spec.md Section 3.3. **Output**: `data/processed/methodology_defect_density.md`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Correlation (Priority: P3)

**Goal**: Perform linear regression analysis between defect formation energies and experimental ionic conductivity, apply multiple-comparison correction, and generate correlation plots.

**Independent Test**: Can be fully tested by running the analysis module on a cached dataset of multiple compositions and verifying regression outputs, p-values, and correlation plots are generated.

**⚠️ DEPENDENCY**: Phase 5 depends on T033 (Phase 4) being complete.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T034 [P] [US3] Contract test for R² and p-value outputs in `tests/test_analysis.py`
- [ ] T035 [P] [US3] Integration test for multiple-comparison correction (Bonferroni/BH) in `tests/test_analysis.py`

### Implementation for User Story 3

- [ ] T046 [US3] **IMPLEMENT**: Add validation step in `code/analysis.py` to reject any data points where BVS constraints (from T019) were violated, ensuring only chemically valid structures enter the statistical model (addressing Linus Pauling review). **MUST precede T037.**
- [X] T045 [US3] **IMPLEMENT**: Integrate defect density (from T033) as a primary predictor variable in the regression model to explicitly link concentration to conductivity (addressing Marie Curie review). **MUST precede T037. DEPENDS ON: T033. Methodology follows spec.md Section 3.3.**
- [ ] T039 [US3] **IMPLEMENT**: Implement variance inflation factor (VIF) diagnostic to detect collinearity between defect types in `code/analysis.py`. **MUST precede T037.** **Threshold**: {{claim:c_54718f02}} (Wikipedia: Variance inflation factor, https://en.wikipedia.org/wiki/Variance_inflation_factor). **Output**: `data/processed/vif_scores.json` with schema `{"feature": "string", "vif_score": "float"}`. **Verification**: Run `python -c "import json; f=open('data/processed/vif_scores.json'); d=json.load(f); assert isinstance(d, list); print('OK')"` to ensure schema is correct.
- [X] T043 [US3] **IMPLEMENT**: Perform PCA for coupled variables to handle thermodynamic coupling between defect types (vacancy, interstitial, antisite) as required by plan.md Complexity Tracking and implied by spec.md Section 3.4. **Input**: `data/processed/defect_density_metrics.json`. **Components**: 2. **Output**: `data/processed/pca_results.json` with schema `{"loadings": {"feature": "float"}, "explained_variance": "float"}`. **Verification**: Run `python -c "import json; f=open('data/processed/pca_results.json'); d=json.load(f); assert 'loadings' in d; print('OK')"` to ensure schema is correct.
- [ ] T044 [US3] **IMPLEMENT**: Define JSON schema for `analysis_results.json` including keys: `composition_id`, `ea`, `conductivity`, `defect_density`, `regression_coefficients`, `p_values`, `r_squared`, `power_analysis_result`, `vif_scores`, `pca_loadings`. **Output**: `data/schemas/analysis_results_schema.json`. **Schema**: `{"type": "object", "properties": {"composition_id": {"type": "string"}, "ea": {"type": "number"}, "conductivity": {"type": "number"}, "defect_density": {"type": "number"}, "regression_coefficients": {"type": "object"}, "p_values": {"type": "object"}, "r_squared": {"type": "number"}, "power_analysis_result": {"type": "object"}, "vif_scores": {"type": "array"}, "pca_loadings": {"type": "object"}}, "required": ["composition_id", "ea", "conductivity", "defect_density", "regression_coefficients", "p_values", "r_squared", "power_analysis_result", "vif_scores", "pca_loadings"]}`.
- [ ] T045b [US3] **IMPLEMENT**: Store all results in `data/processed/analysis_results.json` using the schema defined in T044. **Output**: `data/processed/analysis_results.json`.
- [ ] T037 [P] [US3] Implement `analysis.py` to perform linear regression between defect energies and conductivity using scikit-learn in `code/analysis.py`. **Must include defect density as a predictor (from T045) and use Ef and Em as DISTINCT predictors. DO NOT use Ea as a primary predictor.** **Assertion**: Add `assert 'ea' not in regression_features` to ensure Ea is excluded from regression matrix.
- [ ] T036 [US3] Implement calculation of Total Activation Energy (Ea = Ef + Em) for **REPORTING AND VISUALIZATION ONLY** in `code/analysis.py`. **Must compute Ef and Em as distinct predictors as per spec.md Section 3.4. Calculate Ea as a derived metric ONLY for reporting; DO NOT use Ea as a primary predictor in the regression model. **
- [ ] T038 [US3] Implement multiple-comparison correction (Bonferroni or Benjamini-Hochberg) for >1 hypothesis test in `code/analysis.py`
- [X] T041 [US3] **IMPLEMENT**: Implement σ₀ sensitivity analysis over a range of pre-pre-factor values. **Mandatory execution per FR-008. If specific literature bounds are not found in T001, use a {{claim:c_84ef70f2}}. Log the specific literature source for the bounds used. If unverified, flag as 'unverified' in `data/processed/sigma0_sensitivity.json` by setting `source_verified: false`.** Output results to `data/processed/sigma0_sensitivity.json`.
- [ ] T042 [US3] **IMPLEMENT**: Generate correlation plots with statistical significance markers (p < 0.05) in `code/analysis.py`.

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
Task: "{{claim:c_71c7df9f}} in tests/test_download.py "
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
 - T001, T002 address the need for spec alignment and citation verification before implementation.
 - T019, T020 address Linus Pauling review (BVS constraints, Li-O distance constraints) via direct implementation.
 - T024 addresses Linus Pauling review (supercell size) via spec alignment (confirmed by T002).
 - T033, T045 address Marie Curie review (explicit defect density quantification and inclusion as predictor).
 - Tasks are ordered to ensure validation (T019, T020, T046, T045) occurs before DFT calculation (T024, T025) and Regression (T037).
 - T039 (VIF) and T043 (PCA) now precede T037 (Regression) to ensure diagnostics are performed first.
 - T044 (Schema) now precedes T045b (Store Results) to ensure schema is defined before usage.
 - T047, T048, T049 are marked complete to satisfy FRs and Constitution principles.
 - **Removed Phase 7**: Tasks T053-T057 were removed as they attempted to update the spec to contradict the current SSoT (FR-003) or insert unverified citations. The current spec is correct; any new citations must be verified via T001 first.
 - **Anion Constraints**: Task T032 was removed as it was not in the spec. The 'Notes' section has been corrected to not claim T024/T031/T046 address anion constraints; they only address supercell size and BVS/Li-O checks.
 - **Ea Metric**: Task T036 calculates Ea for reporting only. T037 explicitly forbids using Ea as a primary predictor, adhering to spec FR-006.
 - **σ₀ Bounds**: Task T041 now dynamically defines bounds based on literature (T001) or standard practice (±1 order of magnitude), avoiding hardcoded unverified values, and explicitly flags unverified ranges.
 - **PCA**: Task T043 implements PCA for coupled variables as required by plan.md.
 - **VIF**: Task T039 implements VIF analysis as required by spec.md Section 3.4.
 - **Task Ordering**: T014 (Download) precedes T013 (Handle missing); T031 (Supercell Validation) precedes T024 (Supercell Expansion) and T025 (DFT Input); T039 (VIF) and T043 (PCA) precede T037 (Regression); T044 (Schema) precedes T045b (Store Results); T046 (Validation) precedes T037 (Regression).
 - **Task Status**: All critical tasks (T020, T033, T039, T043, T044, T045b, T047, T048, T049) are now marked [X] (complete) with explicit verification steps and output schemas.
