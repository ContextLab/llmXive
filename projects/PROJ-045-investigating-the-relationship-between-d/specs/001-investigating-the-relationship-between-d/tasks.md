# Tasks: Defect Chemistry and Ionic Conductivity Analysis

**Input**: Design documents from `/specs/001-defect-chemistry-conductivity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create `data/raw/` and `data/processed/` directories in `projects/PROJ-045-investigating-the-relationship-between-d/`
- [X] T002 Create `code/` and `tests/` directories in `projects/PROJ-045-investigating-the-relationship-between-d/`
- [X] T003 Initialize Python 3.11 project with `pymatgen`, `ase`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pydantic`, `statsmodels` in `requirements.txt`
- [X] T004 [P] Configure linting (flake8) and formatting (black) tools in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T005 Setup data directory structure (`data/raw/`, `data/processed/`) and `checksums.txt` in `projects/PROJ-045-investigating-the-relationship-between-d/`
- [X] T006 [P] Implement logging infrastructure with timestamped, level-based output in `code/utils.py`
- [X] T007 [P] Setup environment configuration management (loading `config.yaml` or env vars) in `code/utils.py`
- [X] T008 Create base Pydantic models for `ElectrolyteComposition`, `DefectConfiguration`, `MigrationBarrier`, `AnalysisResult` in `code/models.py`
- [X] T009 Implement SHA-256 checksumming utility for raw data verification in `code/utils.py`
- [X] T010 Setup GitHub Actions workflow template for CPU-only execution with a limited core count and 7GB RAM with 6h timeout in `.github/workflows/ci.yml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline and Validation (Priority: P1) 🎯 MVP

**Goal**: Download crystal structures and experimental ionic conductivity data from OBELiX and Materials Project, then validate dataset completeness.

**Independent Test**: Can be fully tested by running the data download and validation script and producing a dataset completeness report without executing any DFT calculations.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for data download success rate (≥93%) in `tests/test_download.py`
- [X] T012 [P] [US1] Integration test for completeness report generation in `tests/test_validate.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement logic to handle missing OBELiX defect data (log specific message and proceed with DFT-computed values) in `code/validate.py`
- [X] T014 [P] [US1] Implement `download.py` to fetch crystal structures from OBELiX and Materials Project using static MP-ID list in `code/download.py`
- [X] T015 [P] [US1] Implement `validate.py` to check for required variables (vacancy, interstitial, antisite, migration barrier, conductivity) in `code/validate.py`
- [X] T016 [US1] Implement logic to generate `completeness_report.json` listing availability status per composition in `code/validate.py`
- [X] T017 [US1] Add error handling for failed downloads with retry logic (limited attempts, exponential backoff) in `code/download.py`
- [X] T018 [US1] Add logging for missing variables with specific dataset and variable names in `code/validate.py`
- [X] T019a [US1] **REVISE**: Update `spec.md` FR-002 to explicitly include Bond-Valence Sum (BVS) validation (>10% deviation threshold) and crystallographic constraint checks (Li-O distance within the typical coordination range observed in lithium-oxygen complexes, consistent with established structural models [DOI/arXiv/author-year].) as mandatory validation steps. **MUST be completed before T019/T020.**
- [X] T019 [US1] **REVISE**: Implement Bond-Valence Sum (BVS) validation in `code/validate.py` to filter out structures where calculated BVS deviates >10% from ideal oxidation states (as authorized by T019a update to spec.md). **MUST run before any DFT task.**
- [X] T020 [US1] **REVISE**: Implement crystallographic constraint check in `code/validate.py` to verify Li-O distances fall within 1.95-2.15 Å range for transition metal oxides (as authorized by T019a update to spec.md) and log violations.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Defect Energy and Barrier Calculations (Priority: P2)

**Goal**: Compute defect formation energies and estimate migration barriers using a hybrid DFT/Semi-empirical strategy within CPU-only constraints.

**Independent Test**: Can be fully tested by running the calculation module on 2-3 pre-selected test systems and verifying output energy values match expected ranges from literature (within 0.5 eV tolerance for defect energies).

**⚠️ DEPENDENCY**: Phase 4 depends on successful completion of T019a, T019, and T020.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for defect energy range validation (starting from a lower bound consistent with defect formation physics) in `tests/test_dft_runner.py`
- [X] T022 [P] [US2] Integration test for NEB convergence criteria (force ≤0.05 eV/Å) in `tests/test_dft_runner.py`

### Implementation for User Story 2

- [X] T023a [US2] **REVISE**: Update `spec.md` to explicitly define the selection logic for the high-fidelity (DFT) vs low-fidelity (semi-empirical) subset (e.g., "Select a subset of compositions with complete data for DFT; remaining for semi-empirical"). **MUST be completed before T023.**
- [X] T024a [US2] **REVISE**: Update `spec.md` FR-003 to explicitly authorize a "2x2x2 minimum supercell expansion" (allowing >8 atoms) for the high-fidelity subset, resolving the contradiction with the original ≤8 atom constraint. **MUST be completed before T024.**
- [X] T024 [US2] Implement logic for 2x2x2 supercell expansion (allowing >8 atoms) for high-fidelity subset (first 3 compositions with complete data) in `code/dft_runner.py`. **This task implements the authorized deviation from FR-003 as updated in T024a.**
- [X] T025 [P] [US2] Implement `dft_runner.py` to generate Quantum ESPRESSO input files (`.in`) withexplicit parameters (pseudopotentials, k-mesh, cutoff) in `code/dft_runner.py`
- [X] T023 [US2] Define and implement semi-empirical approximation method (bond-valence sum model using parameters from Brown (Wikidata Q42867277, https://www.wikidata.org/wiki/Q42867277)) for remaining compositions to achieve n≥12 in `code/semi_empirical.py`. **Must validate BVS results against DFT results for the high-fidelity subset (first 3 compositions).**
- [X] T027 [US2] Implement the semi-empirical defect energy calculation for the low-fidelity subset in `code/semi_empirical.py`, strictly adhering to the `plan.md` Constraints section (Hybrid Strategy) without introducing external review citations or unverified quantification methods.
- [X] T028 [US2] Add logging for atom counts, calculation status, and convergence results in `code/dft_runner.py`
- [X] T029 [US2] Implement NEB method for several representative defect configurations PER SYSTEM with force convergence checks in `code/dft_runner.py`
- [X] T030 [US2] Implement timeout detection and partial result preservation for jobs exceeding h limit in `code/dft_runner.py`
- [X] T031 [US2] **REVISE**: Implement supercell size validation in `code/dft_runner.py` to ensure minimum 2x2x2 conventional cells are used for the high-fidelity subset (as authorized by T024a). If 2x2x2 fails convergence, fallback to 3x3x3 and log the reason. (Addressing Linus Pauling review on spurious interactions).
- [X] T032 [US2] **REVISE**: Implement oxygen-anion position constraint logic in `code/dft_runner.py` to optionally constrain O-anion positions within 0.05 Å of crystallographic positions during relaxation (addressing Linus Pauling review).
- [X] T033 [US2] **REVISE**: Implement defect density quantification method in `code/dft_runner.py` to explicitly calculate and log defect concentration (defects/volume = 1 / supercell_volume) for every configuration, ensuring reproducibility of the "quantitative effect" claim (addressing Marie Curie review).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Correlation (Priority: P3)

**Goal**: Perform linear regression analysis between defect formation energies and experimental ionic conductivity, apply multiple-comparison correction, and generate correlation plots.

**Independent Test**: Can be fully tested by running the analysis module on a cached dataset of multiple compositions and verifying regression outputs, p-values, and correlation plots are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T034 [P] [US3] Contract test for R² and p-value outputs in `tests/test_analysis.py`
- [X] T035 [P] [US3] Integration test for multiple-comparison correction (Bonferroni/BH) in `tests/test_analysis.py`

### Implementation for User Story 3

- [ ] T045 [US3] **REVISE**: Integrate defect density (from T033) as a primary predictor variable in the regression model to explicitly link concentration to conductivity (addressing Marie Curie review). **MUST precede T037.**
- [X] T036 [US3] Implement calculation of Total Activation Energy (Ea = Ef + Em) for regression input in `code/analysis.py`
- [X] T037 [P] [US3] Implement `analysis.py` to perform linear regression between defect energies and conductivity using scikit-learn in `code/analysis.py`. **Must include defect density as a predictor (from T045).**
- [ ] T038 [US3] Implement multiple-comparison correction (Bonferroni or Benjamini-Hochberg) for >1 hypothesis test in `code/analysis.py`
- [ ] T039 [US3] Implement variance inflation factor (VIF) diagnostic to detect collinearity between defect types in `code/analysis.py`
- [ ] T040 [US3] Implement threshold sensitivity analysis (sweep p < 0.01, 0.05, 0.1) and report mean false-positive rate in `code/analysis.py`
- [ ] T041 [US3] Implement σ₀ sensitivity analysis over a range of conductivity-temperature product values.. **Mandatory execution per FR-008, overriding the 'Optional' note in Assumptions.**
- [ ] T042 [US3] Implement generation of correlation plots with statistical significance markers (p < 0.05) in `code/analysis.py`
- [ ] T043 [US3] Implement statistical power calculation using `statsmodels.stats.power` as the Python-native replacement for the standalone G*Power application mentioned in SC-003 (α=0.05, effect size ≥0.1, target power ≥0.8) in `code/analysis.py`
- [ ] T044 [US3] Store all results in `data/processed/analysis_results.json` with machine-readable schema linking to raw data points in `code/analysis.py`
- [ ] T046 [US3] **REVISE**: Add validation step in `code/analysis.py` to reject any data points where BVS constraints (from T019) were violated, ensuring only chemically valid structures enter the statistical model (addressing Linus Pauling review).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T047 [P] Documentation: Generate `quickstart.md` in `docs/` containing EXACTLY: 1) `pip install -r requirements.txt` command, 2) `python code/download.py` example, 3) `python code/validate.py` verification output sample, 4) `python code/analysis.py` example. File must be <500 lines. **Create `tests/test_quickstart.py` to verify that all commands in quickstart.md execute without error.**
- [ ] T048 [P] Code cleanup: Refactor `code/download.py` to use `requests` streaming for files >100MB. **Pass/Fail**: Must handle a large file without memory error on a runner with a constrained RAM limit, using moderate buffer chunks. Add unit test `tests/test_download_streaming.py` verifying this behavior with a 150MB mock file.
- [ ] T049 [P] Performance optimization: Vectorize the regression loop in `code/analysis.py` using `numpy` broadcasting. **Pass/Fail**: Replace explicit `for` loops over compositions with `numpy` matrix operations; unit test `tests/test_analysis_vectorized.py` must verify identical results with <50% runtime reduction on n=1000 synthetic data.
- [ ] T050 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T051 Security hardening for data handling
- [ ] T052 Run `quickstart.md` validation to ensure reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for data download success rate (≥93%) in tests/test_download.py "
Task: "Integration test for completeness report generation in tests/test_validate.py"

# Launch all models for User Story 1 together:
Task: "Implement download.py to fetch crystal structures from OBELiX and Materials Project using static MP-ID list in code/download.py"
Task: "Implement validate.py to check for required variables (vacancy, interstitial, antisite, migration barrier, conductivity) in code/validate.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
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
 - T019a, T019, T020 address Linus Pauling review (BVS constraints, crystallographic constraints) via spec update T019a.
 - T024a, T024, T031, T032, T046 address Linus Pauling review (supercell size, anion constraints) via spec update T024a.
 - T033, T045 address Marie Curie review (explicit defect density quantification and inclusion as predictor).
 - Tasks are ordered to ensure validation (T019a, T019, T020) occurs before DFT calculation (T024, T025).
 - T024a and T023a ensure spec deviations are authorized before implementation.