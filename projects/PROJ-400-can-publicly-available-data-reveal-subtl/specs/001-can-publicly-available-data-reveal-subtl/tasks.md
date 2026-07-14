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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-400-can-publicly-available-data-reveal-subtl/`)
- [ ] T002 Initialize Python 3.11 project with dependencies (`requests`, `pandas`, `scipy`, `pyyaml`, `numpy`, `pytest`) in `requirements.txt`
- [ ] T003 [P] Configure linting (flake8/ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement data schema definitions in `specs/001-t-violation-beta-decay/contracts/` (d_measurement.schema.yaml, meta_analysis_result.schema.yaml)
- [ ] T005 [P] Create directory structure for `data/raw/` and `data/processed/` with `.gitkeep` and checksum placeholder logic
- [ ] T006 [P] Implement base configuration loader in `code/config.py` to handle random seed pinning and environment vars
- [ ] T007 [Depends on T004] Create base entity classes `Nucleus` and `DMeasurement` in `code/models.py` matching `data-model.md`
- [ ] T008 [P] Create `code/utils/` directory and implement robust error handling and logging infrastructure in `code/utils/logger.py` (handling retries, 404s, and range parsing)
- [ ] T009 [P] Setup environment configuration management by creating `config.yaml` for configurable target nuclei list (e.g., 6He, 19Ne)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Archival Data Retrieval and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Retrieve published T-violation D-coefficients and uncertainties from NNDC ENSDF and harmonize them into a single CSV.

**Independent Test**: Can be fully tested by executing the data extraction script against the ENSDF API/website and verifying the output CSV contains rows with D-coefficient values and uncertainties for a target nucleus.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [Depends on T004] [US1] Contract test for data retrieval schema validation in `tests/contract/test_retrieval_schema.py`
- [ ] T011 [P] [US1] Unit test for range-to-uncertainty conversion logic in `tests/unit/test_harmonization.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `retrieval.py` in `code/retrieval.py` to fetch D-coefficients from NNDC ENSDF API (https://www.nndc.bnl.gov/ensdf/getrefs.jsp) with exponential backoff retry logic and parse ENSDF XML/JSON response
- [ ] T013 [P] [US1] Implement `harmonization.py` in `code/harmonization.py` to align data by nuclear state and handle range/point-estimate edge cases
- [ ] T014 [US1] Implement the main data pipeline orchestrator in `code/main.py` (US1 section) to save harmonized data to `data/processed/harmonized_d_coefficients.csv`, ensuring the output CSV is validated by running a schema check to assert columns `value`, `uncertainty`, and `source_id` exist and are non-null before saving, satisfying the Independent Test criteria
- [ ] T015 [US1] Add validation logic to flag nuclei with "insufficient data" and write to a missing_nuclei list in the output CSV or separate log file
- [ ] T016 [US1] Add logging for data retrieval success rates to `logs/retrieval.log` with specific failure reasons (404, timeout, missing D-coeff)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Meta-Analysis and Upper Bound Calculation (Priority: P2)

**Goal**: Perform inverse-variance weighted meta-analysis to calculate combined D-coefficient and 95% confidence interval upper bound.

**Independent Test**: Can be fully tested by running the statistical analysis module on a mock dataset with known injected D-coefficients.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for inverse-variance weighting accuracy against mock data in `tests/unit/test_meta_analysis.py`
- [ ] T019 [P] [US2] Integration test for Z-test against zero hypothesis in `tests/integration/test_hypothesis_test.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `meta_analysis.py` in `code/meta_analysis.py` to calculate weighted average and combined uncertainty
- [ ] T021 [US2] Implement the 95% confidence interval upper bound calculation logic in `code/meta_analysis.py` to explicitly calculate and output the 95% CI upper bound as a distinct numerical value, saving the result as the field `d_upper_bound_95ci` in `data/processed/meta_analysis_results.json`, handling cases where the mean is indistinguishable from zero
- [ ] T022 [US2] Implement the Z-test logic in `code/meta_analysis.py` to test the combined mean against the Standard Model prediction (D=0) as the primary hypothesis test, including verification logic to compare the Z-score against the null hypothesis and calculate the p-value, replacing any permutation-based approach
- [ ] T023 [US2] Integrate with User Story 1 components: Read the artifact `data/processed/harmonized_d_coefficients.csv` produced by T014 in `code/main.py` to consume the harmonized data for analysis
- [ ] T024 [US2] Save `MetaAnalysisResult` to `data/processed/meta_analysis_results.json` with schema validation

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Consistency Testing and Sensitivity Validation (Priority: P3)

**Goal**: Perform Cochran's Q consistency test, calculate sensitivity limits, and cross-reference with PDG constraints.

**Independent Test**: Can be fully tested by running the validation module on the processed data and verifying the generation of a heterogeneity p-value and PDG comparison table.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for Cochran's Q statistic calculation in `tests/unit/test_consistency.py`
- [ ] T027 [P] [US3] Unit test for sensitivity limit calculation (inverse-variance weighted average of uncertainties) in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `consistency.py` in `code/consistency.py` to calculate Cochran's Q statistic and p-value (use permutation engine for fallback if n < 5, but NOT for primary test)
- [ ] T029 [US3] Implement sensitivity limit calculation in `code/consistency.py` as the inverse-variance weighted average of individual uncertainties and verify it matches the weighted average of uncertainties per SC-003
- [ ] T030 [US3] Implement `validation.py` in `code/validation.py` to dynamically fetch the current PDG Review limits by invoking the Reference-Validator Agent to verify the source URL and extract the current limits, cross-referencing derived bounds, ensuring no hardcoded values are used
- [ ] T031 [US3] Add logic to flag results that are looser than the current world average
- [ ] T031a [US3] Implement explicit p-value threshold check in `code/consistency.py` to compare Cochran's Q p-value against 0.05 and flag consistency status
- [ ] T032 [US3] Generate final validation report in `data/processed/validation_report.json`

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