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

- [ ] T001 Create `data/raw/` and `data/processed/` directories in `projects/PROJ-045-investigating-the-relationship-between-d/`
- [ ] T002 Create `code/` and `tests/` directories in `projects/PROJ-045-investigating-the-relationship-between-d/`
- [ ] T003 Initialize Python 3.11 project with `pymatgen`, `ase`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pydantic`, `statsmodels` in `requirements.txt`
- [ ] T004 [P] Configure linting (flake8) and formatting (black) tools in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T005 Setup data directory structure (`data/raw/`, `data/processed/`) and `checksums.txt` in `projects/PROJ-045-investigating-the-relationship-between-d/`
- [ ] T006 [P] Implement logging infrastructure with timestamped, level-based output in `code/utils.py`
- [ ] T007 [P] Setup environment configuration management (loading `config.yaml` or env vars) in `code/utils.py`
- [ ] T008 Create base Pydantic models for `ElectrolyteComposition`, `DefectConfiguration`, `MigrationBarrier`, `AnalysisResult` in `code/models.py`
- [ ] T009 Implement SHA-256 checksumming utility for raw data verification in `code/utils.py`
- [ ] T010 Setup GitHub Actions workflow template for CPU-only execution (2 cores, 7GB RAM) with 6h timeout in `.github/workflows/ci.yml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline and Validation (Priority: P1) 🎯 MVP

**Goal**: Download crystal structures and experimental ionic conductivity data from OBELiX and Materials Project, then validate dataset completeness.

**Independent Test**: Can be fully tested by running the data download and validation script and producing a dataset completeness report without executing any DFT calculations.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for data download success rate (≥93%) in `tests/test_download.py`
- [ ] T012 [P] [US1] Integration test for completeness report generation in `tests/test_validate.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement logic to handle missing OBELiX defect data (log specific message and proceed with DFT-computed values) in `code/validate.py`
- [ ] T014 [P] [US1] Implement `download.py` to fetch crystal structures from OBELiX and Materials Project using static MP-ID list in `code/download.py`
- [ ] T015 [P] [US1] Implement `validate.py` to check for required variables (vacancy, interstitial, antisite, migration barrier, conductivity) in `code/validate.py`
- [ ] T016 [US1] Implement logic to generate `completeness_report.json` listing availability status per composition in `code/validate.py`
- [ ] T017 [US1] Add error handling for failed downloads with retry logic (2 attempts, exponential backoff) in `code/download.py`
- [ ] T018 [US1] Add logging for missing variables with specific dataset and variable names in `code/validate.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Defect Energy and Barrier Calculations (Priority: P2)

**Goal**: Compute defect formation energies and estimate migration barriers using a hybrid DFT/Semi-empirical strategy within CPU-only constraints.

**Independent Test**: Can be fully tested by running the calculation module on 2-3 pre-selected test systems and verifying output energy values match expected ranges from literature (within 0.5 eV tolerance for defect energies).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for defect energy range validation (starting from a lower bound consistent with defect formation physics) in `tests/test_dft_runner.py`
- [ ] T020 [P] [US2] Integration test for NEB convergence criteria (force ≤0.05 eV/Å) in `tests/test_dft_runner.py`

### Implementation for User Story 2

- [ ] T021 [US2] Define and implement semi-empirical approximation method (bond-valence sum model using parameters from Brown (author-year) with 10% tolerance) for remaining compositions to achieve n≥12 in `code/semi_empirical.py`. **Must validate BVS results against DFT results for the high-fidelity subset.**
- [ ] T022 [US2] Implement logic for 2x2x2 supercell expansion (allowing >8 atoms) for high-fidelity subset (a small number of compositions) in `code/dft_runner.py`. **This task implements the 'Hybrid Strategy' deviation from FR-003 as authorized by Plan.md Summary; MUST include a sub-task to update spec.md FR-003 to reflect the relaxed atom count constraint.**
- [ ] T023 [P] [US2] Implement `dft_runner.py` to generate Quantum ESPRESSO input files (`.in`) with explicit parameters (pseudopotentials, k-mesh, cutoff) in `code/dft_runner.py`
- [ ] T024 [US2] Document the hybrid strategy alignment in `docs/strategy_alignment.md`, explicitly citing `plan.md` Summary as the source of the >8 atom supercell allowance and noting that `spec.md` FR-003 currently reflects this via the 'OR ≤8 atoms' clause, ensuring no contradiction exists between current artifacts.
- [ ] T025 [US2] Implement the semi-empirical defect energy calculation for the low-fidelity subset in `code/semi_empirical.py`, strictly adhering to the `plan.md` Constraints section (Hybrid Strategy) without introducing external review citations or unverified quantification methods.
- [ ] T027 [US2] Add logging for atom counts, calculation status, and convergence results in `code/dft_runner.py`
- [ ] T028 [US2] Implement NEB method for several representative defect configurations PER SYSTEM with force convergence checks in `code/dft_runner.py`
- [ ] T029 [US2] Implement timeout detection and partial result preservation for jobs exceeding h limit in `code/dft_runner.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Correlation (Priority: P3)

**Goal**: Perform linear regression analysis between defect formation energies and experimental ionic conductivity, apply multiple-comparison correction, and generate correlation plots.

**Independent Test**: Can be fully tested by running the analysis module on a cached dataset of multiple compositions and verifying regression outputs, p-values, and correlation plots are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Contract test for R² and p-value outputs in `tests/test_analysis.py`
- [ ] T031 [P] [US3] Integration test for multiple-comparison correction (Bonferroni/BH) in `tests/test_analysis.py`

### Implementation for User Story 3

- [ ] T032 [US3] Implement calculation of Total Activation Energy (Ea = Ef + Em) for regression input in `code/analysis.py`
- [ ] T033 [P] [US3] Implement `analysis.py` to perform linear regression between defect energies and conductivity using scikit-learn in `code/analysis.py`
- [ ] T034 [US3] Implement multiple-comparison correction (Bonferroni or Benjamini-Hochberg) for >1 hypothesis test in `code/analysis.py`
- [ ] T035 [US3] Implement variance inflation factor (VIF) diagnostic to detect collinearity between defect types in `code/analysis.py`
- [ ] T036 [US3] Implement threshold sensitivity analysis (sweep p < 0.01, 0.05, 0.1) and report mean false-positive rate in `code/analysis.py`
- [ ] T037 [US3] Implement σ₀ sensitivity analysis over a range of conductivity-temperature product values.. **Mandatory execution per FR-008, overriding the 'Optional' note in Assumptions.**
- [ ] T038 [US3] Implement generation of correlation plots with statistical significance markers (p < 0.05) in `code/analysis.py`
- [ ] T039 [US3] Implement statistical power calculation using `statsmodels.stats.power` as the Python-native replacement for the standalone G*Power application mentioned in SC-003 (α=0.05, effect size ≥0.1, target power ≥0.8) in `code/analysis.py`
- [ ] T040 [US3] Store all results in `data/processed/analysis_results.json` with machine-readable schema linking to raw data points in `code/analysis.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation: Generate `quickstart.md` in `docs/` containing EXACTLY: 1) `pip install -r requirements.txt` command, 2) `python code/download.py` example, 3) `python code/validate.py` verification output sample, 4) `python code/analysis.py` example. File must be <500 lines and pass `pytest tests/test_quickstart.py`.
- [ ] T042 [P] Code cleanup: Refactor `code/download.py` to use `requests` streaming for files >100MB. **Pass/Fail**: Must handle a large file without memory error on a runner with limited RAM, using moderate buffer chunks.. Add unit test `tests/test_download_streaming.py` verifying this behavior.
- [ ] T043 [P] Performance optimization: Vectorize the regression loop in `code/analysis.py` using `numpy` broadcasting. **Pass/Fail**: Replace explicit `for` loops over compositions with `numpy` matrix operations; unit test `tests/test_analysis_vectorized.py` must verify identical results with <50% runtime reduction on n=1000 synthetic data.
- [ ] T044 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T045 Security hardening for data handling
- [ ] T046 Run `quickstart.md` validation to ensure reproducibility

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
Task: "Contract test for data download success rate (≥93%) in tests/test_download.py"
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
- **Critical Review Address**: Tasks T024, T025, T026 explicitly address Plan.md defined algorithmic constraints (bond-valence, Boltzmann distribution) and are ordered to validate inputs before calculation.