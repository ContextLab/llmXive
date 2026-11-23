# Tasks: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

**Input**: Design documents from `/specs/001-t-violation-beta-decay/`
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

- [ ] T001a Create directory structure for `code/`, `data/`, `tests/`, `docs/`
- [ ] T001b Create `requirements.txt` with initial dependencies
- [ ] T001c Initialize Git repository and add `.gitignore`

- [ ] T002 Initialize Python 3.11 project with dependencies (`requests`, `pandas`, `scipy`, `pyyaml`, `numpy`, `pytest`) in `requirements.txt`
- [ ] T003 [P] Configure linting (flake8/ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004a Implement `d_measurement.schema.yaml` in `specs/001-t-violation-beta-decay/contracts/`
- [ ] T004b Implement `meta_analysis_result.schema.yaml` in `specs/001-t-violation-beta-decay/contracts/`
- [ ] T004c Implement `fusion_result.schema.yaml` in `specs/001-t-violation-beta-decay/contracts/`
- [ ] T005 [P] Create directory structure for `data/raw/` and `data/processed/` with `.gitkeep` and checksum placeholder logic
- [ ] T006 [P] Implement base configuration loader in `code/config.py` to handle random seed pinning and environment vars
- [ ] T007 [Depends on T004] Create base entity classes `Nucleus` and `DMeasurement` in `code/models.py` matching `data-model.md`
- [ ] T008 [P] Create `code/utils/` directory and implement robust error handling and logging infrastructure in `code/utils/logger.py` (handling retries, 404s, and range parsing)
- [ ] T009 [P] Setup environment configuration management by creating `config.yaml` for configurable target nuclei list (e.g., 6He, 19Ne)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Archival Raw Data Retrieval and Validation (Priority: P1) 🎯 MVP

**Goal**: Retrieve raw or semi-raw momentum spectra and polarization asymmetry coefficients for specific nuclei (e.g., 6He, 19Ne) from the NNDC ENSDF database and validate that the data format supports cross-modal covariance analysis.

**Independent Test**: Can be fully tested by executing the data extraction script against the ENSDF API/website and verifying the output contains raw/semi-raw spectra or asymmetry coefficients (not just pre-calculated D-coefficients) for a target nucleus.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [Depends on T004] [US1] Contract test for data retrieval schema validation in `tests/contract/test_retrieval_schema.py`
- [ ] T011 [P] [US1] Unit test for range-to-uncertainty conversion logic in `tests/unit/test_harmonization.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `retrieval.py` in `code/retrieval.py` to fetch raw or semi-raw momentum spectra and polarization asymmetry coefficients from NNDC ENSDF using specific data retrieval endpoints (e.g., 'getdata' for specific evaluations) with exponential backoff retry logic. Parse ENSDF XML/JSON response to extract energy/momentum bins, asymmetry values, and uncertainties. Validate that the retrieved data contains the necessary modalities (momentum AND polarization) for fusion.
- [ ] T013 [P] [US1] Implement `harmonization.py` in `code/harmonization.py` to align data by nuclear state and handle range/point-estimate edge cases. Convert range estimates to point estimates with propagated uncertainty.
- [ ] T014 [US1] Implement the main data pipeline orchestrator in `code/main.py` (US1 section) to save harmonized raw observables to `data/processed/harmonized_raw_observables.csv`, ensuring the output CSV is validated by running a schema check to assert columns `nucleus`, `modality_type`, `value`, `uncertainty`, `source_id` exist and are non-null before saving, satisfying the Independent Test criteria.
- [ ] T015 [US1] Add validation logic to flag nuclei as "fusion impossible" if only pre-calculated D-coefficients are available (no raw spectra or asymmetry data) and write this flag to a separate log file or metadata field in the output CSV.
- [ ] T016 [US1] Add logging for data retrieval success rates to `logs/retrieval.log` with specific failure reasons (404, timeout, missing raw data, missing asymmetry data).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Cross-Modal Data Fusion and Permutation Testing (Priority: P2)

**Goal**: Perform a cross-modal data fusion by computing the covariance matrix between momentum distribution and polarization coefficients for each nucleus, and use permutation testing (minimum 10,000 shuffles) to establish the null distribution and calculate a 95% confidence interval upper bound on the D-coefficient.

**Independent Test**: Can be fully tested by running the statistical analysis module on a mock dataset with known injected correlations, verifying the permutation p-value is stable (variance < 0.01) when the number of shuffles is doubled.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for cross-modal covariance calculation accuracy against mock data in `tests/unit/test_fusion.py`
- [ ] T019 [P] [US2] Integration test for permutation test stability in `tests/integration/test_permutation_stability.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `fusion.py` in `code/fusion.py` to compute the cross-modal covariance matrix between the retrieved momentum distributions and polarization coefficients for each nucleus. Derive the D-coefficient estimate from the covariance matrix. Add validation to flag if the data structure (independent runs) makes the covariance calculation physically invalid (i.e., if the data does not represent simultaneous measurements).
- [ ] T021 [US2] Implement the 95% confidence interval upper bound calculation logic in `code/fusion.py` to explicitly calculate and output the 95% CI upper bound as a distinct numerical value, saving the result as the field `d_upper_bound_95ci` in `data/processed/fusion_results.json`, handling cases where the mean is indistinguishable from zero.
- [ ] T022 [US2] Implement the permutation testing logic in `code/fusion.py` to perform a minimum of 10,000 shuffles of the polarization values relative to momentum bins. Generate the null distribution for the D-coefficient and calculate the p-value. Clamp p-values to [1e-10, 1-1e-10] to avoid floating-point precision issues.
- [ ] T023 [US2] Integrate with User Story 1 components: Read the artifact `data/processed/harmonized_raw_observables.csv` produced by T014 in `code/main.py` to consume the harmonized data for analysis.
- [ ] T024 [US2] Save `FusionResult` to `data/processed/fusion_results.json` with schema validation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Validation and PDG Comparison (Priority: P3)

**Goal**: Calculate the sensitivity limit of the derived bound for each nucleus and compare it against the best single-experiment sensitivity and the Particle Data Group (PDG) review limits to validate the results.

**Independent Test**: Can be fully tested by running the validation module on the processed data and verifying the generation of a sensitivity limit (per nucleus) and a comparison table against the 2024 PDG Review.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for sensitivity limit calculation (standard error of weighted mean) in `tests/unit/test_sensitivity.py`
- [ ] T027 [P] [US3] Unit test for PDG comparison logic in `tests/unit/test_pdg_comparison.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `consistency.py` in `code/consistency.py` to calculate Cochran's Q statistic and p-value for heterogeneity. Use permutation engine for fallback if n < 5, but ensure the primary significance testing for the D-coefficient (as required by FR-003/Constitution VII) remains permutation-based.
- [ ] T029 [US3] Implement sensitivity limit calculation in `code/consistency.py` as the standard error of the weighted mean of measurements for that specific nucleus and verify it matches the weighted average of uncertainties per SC-003.
- [ ] T030a [US3] Implement `pdg_fetcher.py` in `code/data/pdg_fetcher.py` to explicitly retrieve and parse the 2024 PDG Review limits for the target nuclei from the PDG website or a defined CSV source. Store the parsed limits in `data/processed/pdg_limits.json` and validate the citation source.
- [ ] T030 [US3] Implement `validation.py` in `code/validation.py` to cross-reference derived bounds with the PDG limits stored in `data/processed/pdg_limits.json`, ensuring no hardcoded values are used.
- [ ] T031 [US3] Add logic to flag results that are looser than the current world average.
- [ ] T031a [US3] Implement explicit p-value threshold check in `code/consistency.py` to compare Cochran's Q p-value against a predetermined significance threshold and flag consistency status.
- [ ] T032 [US3] Generate final validation report in `data/processed/validation_report.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `docs/` (create `docs/api.md`, `docs/usage.md`) and `quickstart.md`
- [ ] T034 Code cleanup and refactoring of `code/main.py` orchestrator (reduce cyclomatic complexity to < 10)
- [ ] T035 Performance optimization for data retrieval (implement `requests-cache` but set `DISABLE_CACHE=true` in the CI environment to ensure no local cache state persists on fresh runners, ensuring reproducibility)
- [ ] T036 [P] Additional unit tests for edge cases (single measurement, p-value clamping) in `tests/unit/`
- [ ] T037 Security hardening (Add regex validation for nuclei names in `code/retrieval.py`)
- [ ] T038 Run quickstart.md validation (Execute quickstart.md and verify exit code 0)
- [ ] T039 [US2] Implement stability check for permutation test p-value variance < 0.01 by running the test with doubled shuffles and comparing results, as required by SC-004.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data output from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data output from US2

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
Task: "Contract test for data retrieval schema validation in tests/contract/test_retrieval_schema.py"
Task: "Unit test for range-to-uncertainty conversion logic in tests/unit/test_harmonization.py"

# Launch all models for User Story 1 together:
Task: "Create base entity classes in code/models.py"
Task: "Implement data schema definitions in specs/001-t-violation-beta-decay/contracts/"
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