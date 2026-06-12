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

- [X] T001a Create code/ and tests/ directories per plan.md Project Structure
- [ ] T001b Create data/ and docs/ directories per plan.md Project Structure
- [ ] T001c Create data/raw/, data/processed/, data/plots/ subdirectories per plan.md
- [ ] T001d Create docs/reproducibility/ and tests/contract/, tests/integration/, tests/unit/ subdirectories per plan.md
- [ ] T002 Initialize Python 3.11 project with dependencies in requirements.txt (pandas, numpy, scipy, statsmodels, matplotlib, seaborn, requests, pyyaml)
- [ ] T003 [P] Configure linting and formatting tools (black, flake8) in .pre-commit-config.yaml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Define data schemas in specs/001-knot-complexity-analysis/contracts/knot-record.schema.yaml
- [ ] T005 [P] Define regression model schemas in specs/001-knot-complexity-analysis/contracts/regression-model.schema.yaml
- [ ] T006 Setup reproducibility logging framework in code/reproducibility/logs.py (timestamp, operation, input_file, output_file, parameters, status, duration_ms)
- [ ] T007 Implement random seed pinning in code/__init__.py (per Constitution Principle I)
- [ ] T009 [P] Implement flagging system for missing invariants (missing_invariant_flags) in code/data/validator.py (per FR-009)
- [ ] T010 [P] Implement flagging system for data quality issues (data_quality_flags) in code/data/validator.py (per FR-002)
- [ ] T043a [P] Implement flagging system for ambiguous alternating/non-alternating classification (exclude or mark as 'unclassifiable') in code/data/validator.py (per FR-010)
- [ ] T065 [P] Implement citation validation framework in code/reproducibility/citation_validator.py with title-token-overlap >=0.7 threshold verification per Constitution Principle II
- [ ] T066 [P] Implement content hashing for artifacts in code/reproducibility/hashing.py with Advancement-Evaluator Agent integration per Constitution Principle V

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Parse Knot Data from Knot Atlas (Priority: P1) 🎯 MVP

**Goal**: Download knot data from Knot Atlas including crossing numbers, braid indices, hyperbolic volume, and alternating/non-alternating classification for all prime knots with crossing number ≤13

**Independent Test**: Can be fully tested by executing the data download script and verifying the output contains all prime knots with crossing number ≤13 with consistent representation of crossing number, braid index, hyperbolic volume, and alternating/non-alternating classification fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for data schema in tests/contract/test_schemas.py
- [ ] T012 [P] [US1] Integration test for download pipeline in tests/integration/test_pipeline.py

### Implementation for User Story 1

- [ ] T013 [US1] Implement Knot Atlas downloader in code/download/knot_atlas_downloader.py (fetch from https://katlas.org with retry logic)
- [ ] T014 [US1] Implement retry logic with exponential backoff (initial=1s, max=32s, multiplier=2) in code/download/knot_atlas_downloader.py (per FR-008) with cache partial results to disk after 3 consecutive failures (per FR-008)
- [ ] T015 [US1] Implement parser in code/data/parser.py to extract crossing number, braid index, hyperbolic volume, alternating classification with tie-breaking rules (braid word > DT code, lexicographic) per FR-011 and measurement precision standards
- [ ] T016 [US1] Implement data cleaning to flag nulls and format failures in code/data/validator.py (per FR-002)
- [ ] T018 [US1] Save raw data to data/raw/knot_atlas_raw.json and cleaned data to data/processed/knots_cleaned.csv
- [ ] T017 [US1] Generate dataset size report in docs/reproducibility/dataset_counts.md with concrete prime knot counts per crossing number (per US1 dataset enumeration requirement)
- [ ] T019 [US1] Filter dataset to hyperbolic knots (volume > 0) and log excluded knots in docs/reproducibility/excluded_knots.md (per FR-012)
- [ ] T020 [US1] Validate dataset completeness against OEIS A002863 and KnotInfo for crossing number ≤10 and document validation results in docs/reproducibility/validation_scope.md (per SC-001)
- [ ] T040 [US1] Validate hyperbolic volume data against KnotInfo reference values and document source independence assessment in docs/reproducibility/hyperbolic_volume_validation.md (per FR-013)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Establish Measurement Precision for Core Invariants (Priority: P2)

**Goal**: Establish precision thresholds for crossing number and braid index before correlation analysis proceeds so that I can validate measurement accuracy across different classes of prime knots

**Independent Test**: Can be fully tested by generating scatter plots and summary statistics showing the crossing number vs. braid index relationship for alternating knots separately from non-alternating knots, with validation against reference values where available.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for precision validation output in tests/contract/test_precision.py

### Implementation for User Story 2

- [ ] T022 [US2] Implement precision validation module in code/analysis/precision.py to validate crossing number and braid index (per FR-002, FR-003)
- [ ] T023 [US2] Generate scatter plots of crossing number vs. braid index stratified by alternating/non-alternating in code/analysis/exploratory.py (per FR-004)
- [ ] T024 [US2] Save plots to data/plots/crossing_vs_braid.png with resolution 1200x900 pixels
- [ ] T025 [US2] Document measurement precision standards and error margins in docs/reproducibility/measurement_precision.md (include precision thresholds, error margins per FR-004)
- [ ] T026 [US2] Validate tabulation accuracy for core invariants (crossing number, braid index) against KnotInfo reference values and document results in docs/reproducibility/algorithm_validation.md with pass/fail status and coverage percentage; note that braid index is TABULATED from Knot Atlas per FR-003/SC-008 (algorithm validation for additional invariants deferred to Phase 2+)
- [ ] T028 [US2] Compute null percentage for required invariant fields and document in docs/reproducibility/data_quality_report.md (per FR-002, SC-013)
- [ ] T029 [US2] Apply missing_invariant_flags and data_quality_flags defined in T009 in code/data/validator.py (per FR-002, FR-009)
- [ ] T030 [US2] Document tie-breaking rules in docs/reproducibility/tie_breaking_rules.md (per SC-007)
- [ ] T030b [US2] Implement validation script to automate tie-breaking rule consistency checks in code/analysis/tie_breaking_validator.py (per SC-007)
- [ ] T067 [US2] Add human-readable complexity interpretation guide in docs/reproducibility/complexity_interpretation.md (per dan-rockmore-simulated review - "human readability" of metric)
- [ ] T068 [US2] Generate visualization examples showing how complexity metric maps to knot diagram features in data/plots/complexity_visualization_examples.png (per dan-rockmore-simulated review)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Fit Regression Models to Assess Joint Predictive Relationships (Priority: P3)

**Goal**: Fit multiple regression models to test linear vs. non-linear relationships for associating hyperbolic volume from crossing number and braid index

**Independent Test**: Can be fully tested by executing the regression and validation pipeline on an exploratory sample and producing correlation coefficients and goodness-of-fit metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Contract test for regression model output in tests/contract/test_regression.py

### Implementation for User Story 3

- [ ] T032 [US3] Implement regression model fitting (linear, polynomial, logarithmic) in code/analysis/regression.py (per FR-005)
- [ ] T033 [US3] Compute goodness-of-fit metrics (R², AIC/BIC, MAE) for each model type in code/analysis/regression.py (per FR-005)
- [ ] T034 [US3] Implement residual analysis to identify hyperbolic knot families deviating ≥2 standard deviations in code/analysis/residual_analysis.py (per FR-005, SC-011)
- [ ] T035 [US3] Document residual family analysis in docs/reproducibility/residual_analysis.md with specific knot identifiers and potential explanations
- [ ] T036 [US3] Compute Spearman and Pearson correlation coefficients with effect sizes (Cohen's d, r) in code/analysis/regression.py (per FR-006)
- [ ] T037 [US3] Compute VIF for multicollinearity assessment in code/analysis/regression.py (per FR-005)
- [ ] T038 [US3] Document multicollinearity assessment in docs/reproducibility/multicollinearity_assessment.md with acknowledgment of braid index ≤ crossing number constraint
- [ ] T039 [US3] Compute descriptive comparison metrics (mean difference, variance ratio, Cohen's d) for alternating vs. non-alternating groups in code/analysis/regression.py (per FR-006)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Edge Case Handling, Data Quality, and Reproducibility Documentation (Priority: P4)

**Goal**: Handle edge cases (API unavailability, missing invariants, ambiguous classifications, crossing number ties) with documented fallback behaviors, AND produce complete reproducibility documentation

**Independent Test**: Can be fully tested by (1) simulating edge cases and verifying appropriate flags/logs, AND (2) verifying that all reproducibility artifacts are present.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T042 [P] [US4] Integration test for edge case handling in tests/integration/test_edge_cases.py

### Implementation for User Story 4

- [ ] T044 [US4] Generate SHA-256 checksums for all data files in code/reproducibility/checksums.py (per FR-007)
- [ ] T045 [US4] Record checksums in data/ directory and document in docs/reproducibility/checksums.md (per FR-007)
- [ ] T046 [US4] Generate derivation notes with formula citations in docs/reproducibility/derivation_notes.md (include formula citations with page/section references, step-by-step transformation logic with intermediate values, all parameter values used, and justification for any non-standard choices per FR-007)
- [ ] T047 [US4] Log excluded knots (torus/satellite) in docs/reproducibility/excluded_knots.md (per FR-012)
- [ ] T048 [US4] Document validation scope (≤10 vs ≤13) in docs/reproducibility/validation_scope.md (per SC-001)
- [ ] T049 [US4] Generate timestamped logs for all operations in docs/reproducibility/operation_logs.md (per FR-007)
- [ ] T050 [US4] Document random seed values used in docs/reproducibility/random_seeds.md (per FR-007)
- [ ] T051 [US4] Log uncomputable invariants in docs/reproducibility/uncomputable_invariants.md (per FR-003)
- [ ] T052 [US4] Document invariant coverage in docs/reproducibility/invariant_coverage.md (per SC-008)
- [ ] T053 [US4] Generate validation status report in docs/reproducibility/validation_status.md (per SC-007)
- [ ] T069 [US4] Document concrete data quantities processed (knot counts per crossing number, total records, null percentages) in docs/reproducibility/data_quantities.md (per marie-curie-simulated review - "concrete numbers")
- [ ] T070 [US4] Document classification error margins and signal-to-noise ratio analysis in docs/reproducibility/classification_error_analysis.md (per marie-curie-simulated review)

**Checkpoint**: At this point, User Stories 1, 2, 3 AND 4 should all work independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T054 [P] Documentation updates in docs/reproducibility/ (ensure all FR-007 required reproducibility documents are present with required content: data_quality_report.md, validation_scope.md, excluded_knots.md, invariant_coverage.md, random_seeds.md, tie_breaking_rules.md, validation_status.md, algorithm_validation.md, hyperbolic_volume_validation.md, residual_analysis.md, multicollinearity_assessment.md, uncomputable_invariants.md, checksums.md, derivation_notes.md, operation_logs.md, census_interpretation.md, mathematical_constraints.md, invariant_algorithms.md)
- [ ] T054a [P] Generate invariant algorithms documentation in docs/reproducibility/invariant_algorithms.md with reference implementations and mathematical definitions per FR-003
- [ ] T055 Code cleanup and refactoring in code/ to meet linting standards (black --check pass with 0 violations) and document linting report in docs/reproducibility/linting_report.md
- [ ] T056 Run quickstart.md validation to ensure end-to-end reproducibility and document validation results in docs/reproducibility/quickstart_validation.md with end-to-end pass/fail status
- [ ] T057 [P] Additional unit tests in tests/unit/ (test_downloader.py with test_download_retry_logic, test_download_partial_cache, test_download_timeout; test_parser.py with test_crossing_number_parsing, test_braid_index_parsing, test_hyperbolic_volume_parsing)
- [ ] T058 Verify all random seeds are pinned and document verification results in docs/reproducibility/seed_verification.md with all pinned seed values (distinct from T050 random_seeds.md which lists values used)
- [ ] T059 Document selection bias acknowledgment (hyperbolic-only filtering) in docs/reproducibility/selection_bias.md (per FR-012, Assumptions)
- [ ] T060 Document census data statistical interpretation in docs/reproducibility/census_interpretation.md (per Assumptions)
- [ ] T061 Document mathematical constraint acknowledgment (braid index ≤ crossing number) in docs/reproducibility/mathematical_constraints.md (per Assumptions)
- [ ] T071 [P] Create final summary report in docs/reproducibility/final_report.md synthesizing all findings with human-readable complexity interpretations (per dan-rockmore-simulated review - "concrete data quantities and measurement precision standards")
- [ ] T072 [P] Create methodology appendix in docs/reproducibility/methodology_appendix.md with concrete data quantities and measurement precision standards (per marie-curie-simulated review)

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
  - **FR-010 Compliance**: T043a (ambiguous classification handling - exclude or mark as 'unclassifiable') moved to Foundational
  - **FR-008 Partial Results Cache**: T014 explicitly includes caching partial results after 3 consecutive failures
  - **Constitution Principles**: T065 (citation validation per Principle II), T066 (content hashing per Principle V)
  - **Phase Boundary (FR-003)**: T026 validates tabulation accuracy for core invariants - algorithm validation for additional invariants deferred to Phase 2+
  - **Data Flow Order**: Download (T013-T020, T040) → Precision/EDA (T022-T030, T030b) → Regression (T032-T039) → Edge Cases/Reproducibility (T044-T053)
  - **Phase 1 Scope Boundary**: All tasks for crossing number ≤10 validation are marked; crossing number 11-13 data is downloaded but not validated per spec requirements
  - **dan-rockmore-simulated Review**: T067 (human-readable complexity interpretation), T068 (visualization examples), T071 (final summary with human-readable interpretations)
  - **marie-curie-simulated Review**: T069 (concrete data quantities), T070 (classification error margins), T072 (methodology appendix with precision standards)
  - **Naming Conventions**: T050 (random_seeds.md) vs T058 (seed_verification.md) explicitly distinguished
  - **Duplicate Work Removal**: T008 removed as redundant to T001c/T001d
  - **Traceability**: T065/T066 explicitly cite Constitution Principles
  - **Plan Alignment**: T002 uses requirements.txt per plan.md
  - **FR-003 Compliance**: T054a generates invariant_algorithms.md per FR-003 requirement
  - **Constitution Principle Citations**: T065/T066 include explicit Constitution Principle II/V citations for audit traceability
  - **T067-T072 Scope**: These reviewer-driven tasks are documented as addressing incorporated reviewer feedback (dan-rockmore-simulated, marie-curie-simulated)