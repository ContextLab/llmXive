# Tasks: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Input**: Design documents from `/specs/001-knot-complexity-analysis/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan in projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/
- [ ] T002 Initialize Python 3.11 project with dependencies in pyproject.toml (pandas, numpy, scipy, statsmodels, matplotlib, seaborn, requests, pyyaml)
- [ ] T003 [P] Configure linting and formatting tools (black, flake8) in.pre-commit-config.yaml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Define data schemas in specs/001-knot-complexity-analysis/contracts/knot-record.schema.yaml
- [ ] T005 [P] Define regression model schemas in specs/001-knot-complexity-analysis/contracts/regression-model.schema.yaml
- [ ] T006 Setup reproducibility logging framework in code/reproducibility/logs.py (timestamp, operation, input_file, output_file, parameters, status, duration_ms)
- [ ] T007 Implement random seed pinning in code/__init__.py (per Constitution Principle I)
- [ ] T008 Create base directory structure (data/raw, data/processed, data/plots, docs/reproducibility)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Parse Knot Data from Knot Atlas (Priority: P1) 🎯 MVP

**Goal**: Download knot data from Knot Atlas including crossing numbers, braid indices, hyperbolic volume, and alternating/non-alternating classification for all prime knots with crossing number ≤13

**Independent Test**: Can be fully tested by executing the data download script and verifying the output contains all prime knots with crossing number ≤13 with consistent representation of crossing number, braid index, hyperbolic volume, and alternating/non-alternating classification fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for data schema in tests/contract/test_schemas.py
- [ ] T010 [P] [US1] Integration test for download pipeline in tests/integration/test_pipeline.py

### Implementation for User Story 1

- [ ] T011 [US1] Implement Knot Atlas downloader in code/download/knot_atlas_downloader.py (fetch from https://katlas.org with retry logic)
- [ ] T012 [US1] Implement retry logic with exponential backoff (initial=1s, max=32s, multiplier=2) in code/download/knot_atlas_downloader.py (per FR-008)
- [ ] T013 [US1] Implement parser in code/data/parser.py to extract crossing number, braid index, hyperbolic volume, alternating classification (per FR-002)
- [ ] T014 [US1] Implement data cleaning to flag nulls and format failures in code/data/validator.py (per FR-002)
- [ ] T015 [US1] Generate dataset size report in docs/reproducibility/dataset_counts.md with concrete prime knot counts per crossing number (per Marie Curie review - standard of evidence)
- [ ] T016 [US1] Save raw data to data/raw/knot_atlas_raw.json and cleaned data to data/processed/knots_cleaned.csv
- [ ] T017 [US1] Filter dataset to hyperbolic knots (volume > 0) and log excluded knots in docs/reproducibility/excluded_knots.md (per FR-012)
- [ ] T018 [US1] Validate dataset completeness against OEIS A002863 and KnotInfo for crossing number ≤10 (per SC-001)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Establish Measurement Precision for Core Invariants (Priority: P2)

**Goal**: Establish precision thresholds for crossing number and braid index before correlation analysis proceeds so that I can validate measurement accuracy across different classes of prime knots

**Independent Test**: Can be fully tested by generating scatter plots and summary statistics showing the crossing number vs. braid index relationship for alternating knots separately from non-alternating knots, with validation against reference values where available.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for precision validation output in tests/contract/test_precision.py

### Implementation for User Story 2

- [ ] T020 [US2] Implement precision validation module in code/analysis/precision.py to validate crossing number and braid index (per FR-002, FR-003)
- [ ] T021 [US2] Generate scatter plots of crossing number vs. braid index stratified by alternating/non-alternating in code/analysis/exploratory.py (per FR-004)
- [ ] T022 [US2] Save plots to data/plots/crossing_vs_braid.png with resolution 1200x900 pixels
- [ ] T023 [US2] Document measurement precision standards and error margins in docs/reproducibility/measurement_precision.md (per Marie Curie review - standard of evidence)
- [ ] T024 [US2] Validate algorithm implementation against KnotInfo reference values where available (per FR-003)
- [ ] T025 [US2] Log validation results in docs/reproducibility/algorithm_validation.md with pass/fail status and coverage percentage
- [ ] T026 [US2] Compute null percentage for required invariant fields and document in docs/reproducibility/data_quality_report.md (per FR-002, SC-013)
- [ ] T027 [US2] Flag records with missing_invariant_flags and data_quality_flags in code/data/validator.py (per FR-002, FR-009)
- [ ] T028 [US2] Document tie-breaking rules in docs/reproducibility/tie_breaking_rules.md and implement validation script (per FR-011, SC-007)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Fit Regression Models to Assess Joint Predictive Relationships (Priority: P3)

**Goal**: Fit multiple regression models to test linear vs. non-linear relationships for associating hyperbolic volume from crossing number and braid index

**Independent Test**: Can be fully tested by executing the regression and validation pipeline on an exploratory sample and producing correlation coefficients and goodness-of-fit metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Contract test for regression model output in tests/contract/test_regression.py

### Implementation for User Story 3

- [ ] T030 [US3] Implement regression model fitting (linear, polynomial, logarithmic) in code/analysis/regression.py (per FR-005)
- [ ] T031 [US3] Compute goodness-of-fit metrics (R², AIC/BIC, MAE) for each model type in code/analysis/regression.py (per FR-005)
- [ ] T032 [US3] Implement residual analysis to identify hyperbolic knot families deviating ≥2 standard deviations in code/analysis/residual_analysis.py (per FR-005, SC-011)
- [ ] T033 [US3] Document residual family analysis in docs/reproducibility/residual_analysis.md with specific knot identifiers and potential explanations
- [ ] T034 [US3] Compute Spearman and Pearson correlation coefficients with effect sizes (Cohen's d, r) in code/analysis/regression.py (per FR-006)
- [ ] T035 [US3] Compute VIF for multicollinearity assessment in code/analysis/regression.py (per FR-005)
- [ ] T036 [US3] Document multicollinearity assessment in docs/reproducibility/multicollinearity_assessment.md with acknowledgment of braid index ≤ crossing number constraint
- [ ] T037 [US3] Compute descriptive comparison metrics (mean difference, variance ratio, Cohen's d) for alternating vs. non-alternating groups in code/analysis/regression.py (per FR-006)
- [ ] T038 [US3] Create combined complexity metric visualization for human readability in code/analysis/visualization.py (per Dan Rockmore review - human readability)
- [ ] T039 [US3] Document interpretation of combined metric in docs/reproducibility/interpretation.md (per Dan Rockmore review - shared understanding)
- [ ] T040 [US3] Validate hyperbolic volume data against KnotInfo reference values in docs/reproducibility/hyperbolic_volume_validation.md (per FR-013)
- [ ] T041 [US3] Document source independence assessment between Knot Atlas and KnotInfo in docs/reproducibility/hyperbolic_volume_validation.md (per FR-013)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Edge Case Handling, Data Quality, and Reproducibility Documentation (Priority: P4)

**Goal**: Handle edge cases (API unavailability, missing invariants, ambiguous classifications, crossing number ties) with documented fallback behaviors, AND produce complete reproducibility documentation

**Independent Test**: Can be fully tested by (1) simulating edge cases and verifying appropriate flags/logs, AND (2) verifying that all reproducibility artifacts are present.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T042 [P] [US4] Integration test for edge case handling in tests/integration/test_edge_cases.py

### Implementation for User Story 4

- [ ] T043 [US4] Implement flagging system for missing invariants (missing_invariant_flags) in code/data/validator.py (per FR-009)
- [ ] T044 [US4] Implement flagging system for data quality issues (data_quality_flags) in code/data/validator.py (per FR-002)
- [ ] T045 [US4] Implement tie-breaking rules (braid word > DT code, lexicographic) in code/data/parser.py (per FR-011)
- [ ] T046 [US4] Document tie-breaking rules in docs/reproducibility/tie_breaking_rules.md (per SC-007)
- [ ] T047 [US4] Generate SHA-256 checksums for all data files in code/reproducibility/checksums.py (per FR-007)
- [ ] T048 [US4] Record checksums in data/ directory and document in docs/reproducibility/checksums.md (per FR-007)
- [ ] T049 [US4] Generate derivation notes with formula citations in docs/reproducibility/derivation_notes.md (per FR-007)
- [ ] T050 [US4] Log excluded knots (torus/satellite) in docs/reproducibility/excluded_knots.md (per FR-012)
- [ ] T051 [US4] Document validation scope (≤10 vs ≤13) in docs/reproducibility/validation_scope.md (per SC-001)
- [ ] T052 [US4] Generate timestamped logs for all operations in docs/reproducibility/logs.md (per FR-007)
- [ ] T053 [US4] Document random seed values used in docs/reproducibility/random_seeds.md (per FR-007)
- [ ] T054 [US4] Log uncomputable invariants in docs/reproducibility/uncomputable_invariants.md (per FR-003)
- [ ] T055 [US4] Document invariant coverage in docs/reproducibility/invariant_coverage.md (per SC-008)
- [ ] T056 [US4] Generate validation status report in docs/reproducibility/validation_status.md (per SC-007)

**Checkpoint**: At this point, User Stories 1, 2, 3 AND 4 should all work independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T057 [P] Documentation updates in docs/reproducibility/ (ensure all 11+ files present)
- [ ] T058 Code cleanup and refactoring in code/
- [ ] T059 Run quickstart.md validation to ensure end-to-end reproducibility
- [ ] T060 [P] Additional unit tests in tests/unit/ (test_downloader.py, test_parser.py)
- [ ] T061 Verify all random seeds are pinned and documented in docs/reproducibility/random_seeds.md
- [ ] T062 Document selection bias acknowledgment (hyperbolic-only filtering) in final reports (per FR-012, Assumptions)
- [ ] T063 Document census data statistical interpretation in final reports (per Assumptions)
- [ ] T064 Document mathematical constraint acknowledgment (braid index ≤ crossing number) in final reports (per Assumptions)

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
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - May integrate with US1/US2/US3 but should be independently testable

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
Task: "Contract test for data schema in tests/contract/test_schemas.py"
Task: "Integration test for download pipeline in tests/integration/test_pipeline.py"

# Launch all implementation for User Story 1 together:
Task: "Implement Knot Atlas downloader in code/download/knot_atlas_downloader.py"
Task: "Implement parser in code/data/parser.py"
Task: "Implement data cleaning in code/data/validator.py"
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
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Download/Parse)
 - Developer B: User Story 2 (Precision/EDA)
 - Developer C: User Story 3 (Regression)
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
- **Reviewer Concerns Addressed**:
 - **Dan Rockmore**: T038, T039 (Combined metric visualization & interpretation for human readability and shared understanding)
 - **Marie Curie**: T015, T023, T026 (Dataset counts with concrete numbers, measurement precision standards, null percentage validation for standard of evidence)
- **Data Flow Order**: Download (T011-T018) → Precision/EDA (T020-T028) → Regression (T030-T041) → Edge Cases/Reproducibility (T043-T056)
- **Phase 1 Scope Boundary**: All tasks for crossing number ≤10 validation are marked; crossing number 11-13 data is downloaded but not validated per spec requirements
