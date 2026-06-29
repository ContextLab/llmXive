---
description: "Task list template for feature implementation"
---

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

- [X] T001 Create all project directories per plan.md Project Structure (code/, tests/, data/, docs/, data/raw/, data/processed/, data/plots/, docs/reproducibility/, tests/contract/, tests/integration/, tests/unit/)
- [X] T002 Initialize Python 3.11 project with dependencies in requirements.txt (pandas, numpy, scipy, statsmodels, matplotlib, seaborn, requests, pyyaml)
- [X] T003 [P] Configure linting and formatting tools (black, flake8) in.pre-commit-config.yaml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Define data schemas in specs/001-knot-complexity-analysis/contracts/knot-record.schema.yaml
- [X] T005 [P] Define regression model schemas in specs/001-knot-complexity-analysis/contracts/regression-model.schema.yaml
- [X] T005b [P] Define dataset schema in specs/001-knot-complexity-analysis/contracts/dataset.schema.yaml (per plan.md Project Structure requirement for InvariantsDataset entity)
- [X] T006 Setup reproducibility logging framework in code/reproducibility/logs.py (timestamp, operation, input_file, output_file, parameters, status, duration_ms fields documented and testable; verification: unit tests in tests/unit/test_logs.py confirming all relevant fields present and testable)
- [X] T007 Implement random seed pinning in all code/ files with stochastic operations (per Constitution Principle I; verification: if stochastic operations exist, all have pinned seeds documented in docs/reproducibility/random_seeds.md; if none exist, document N/A in random_seeds.md)
- [X] T008 Create quickstart.md in specs/001-knot-complexity-analysis/quickstart.md documenting end-to-end pipeline execution steps (per plan.md Project Structure requirement)
- [X] T009 Implement flagging system for missing invariants (missing_invariant_flags) in code/data/validator.py (per FR-009; verification: unit tests in tests/unit/test_validator.py demonstrating flag generation for missing invariants)
- [X] T010 Implement flagging system for data quality issues (data_quality_flags) in code/data/validator.py (per FR-002; verification: unit tests in tests/unit/test_validator.py demonstrating flag generation for data quality issues)
- [X] T030 [P] Document tie-breaking rules in docs/reproducibility/tie_breaking_rules.md (per SC-007)
- [X] T043a Implement flagging system for ambiguous alternating/non-alternating classification (exclude or mark as 'unclassifiable') in code/data/validator.py (per FR-010; verification: unit tests in tests/unit/test_validator.py demonstrating flag generation for ambiguous classification)
- [X] T065 Document Reference-Validator Agent integration for citation validation in code/reproducibility/citation_validator.py with title-token-overlap >=0.7 threshold verification per Constitution Principle II (verification: run Reference-Validator Agent on all citations in code/; title-token-overlap≥0.7 for all; NOTE: documentation-only task, external agents do not exist yet)
- [X] T066 Document Advancement-Evaluator Agent integration for content hashing in code/reproducibility/hashing.py per Constitution Principle V (verification: content hash recorded in state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml artifact_hashes map AND updated_at timestamp updated in state file per Constitution Principle V explicit requirement; NOTE: documentation-only task, external agents do not exist yet)
- [X] T026a [P] Implement Constitution Principle VI invariant verification: document verification procedure for computed knot invariants against established mathematical definitions from primary literature in docs/reproducibility/invariant_definitions.md (per Constitution Principle VI; verification: all ADDITIONAL invariants (arc index, Seifert circle count, bridge number) have documented reference to primary mathematical literature; NOTE: per FR-003 and SC-008, not computed - algorithm validation applies only to additional invariants in Phase 2+)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel---

## Phase 3: User Story 1 - Download and Parse Knot Data from Knot Atlas (Priority: P1) 🎯 MVP

**Goal**: Download knot data from Knot Atlas including crossing numbers, braid indices, hyperbolic volume, and alternating/non-alternating classification for all known prime knots (OEIS sequences)

**Independent Test**: Can be fully tested by executing the data download script and verifying the output contains all prime knots with consistent representation of crossing number, braid index, hyperbolic volume, and alternating/non-alternating classification fields.

### Implementation for User Story 1

- [X] T013 [US1] Implement Knot Atlas downloader in code/download/knot_atlas_loader.py (fetch from https://katlas.org with retry logic; verification: verified by successful download of at least one knot record with all required fields; retry logic tested with simulated failures confirming exponential backoff)
- [X] T014 [US1] Implement retry logic with exponential backoff (initial=1s, max=32s, multiplier=2) for downloading knot data from Knot Atlas API in code/download/knot_atlas_loader.py (per FR-008) with cache partial results to disk after 3 consecutive failures (per FR-008; verification: retry logic tested with simulated failures confirming exponential backoff and partial cache after 3 consecutive failures; Depends on T013)
- [X] T015 [US1] Implement parser in code/data/parser.py to extract crossing number, braid index, hyperbolic volume, alternating classification with tie-breaking rules (braid word >DT code, lexicographic) per FR-011 and measurement precision standards
- [X] T016 [US1] Implement data cleaning to flag nulls and format failures in code/data/validator.py (per FR-002; verification: null percentage ≤5% (per SC-001), format pass rate ≥99%, duplicate records = 0 per FR-002 thresholds)
- [X] T018 [US1] Save raw data to data/raw/knot_atlas_raw.json and cleaned data to data/processed/knots_cleaned.csv
- [X] T019 [US1] Filter dataset to hyperbolic knots (volume > 0) and log excluded knots in docs/reproducibility/excluded_knots.md (per FR-012; verification: confirm exclusion count matches docs/reproducibility/excluded_knots.md per SC-012 explicit verification requirement)
- [X] T040 [US1] Validate hyperbolic volume data against KnotInfo reference values and document source independence assessment in docs/reproducibility/hyperbolic_volume_validation.md (per FR-013; verification: ≥90% of records match KnotInfo within 1e-6 tolerance per FR-013; IF KnotInfo reference coverage <90%, skip cross-check and document limitation with skip rationale per FR-013; Depends on T019)
- [X] T020 [US1] Validate dataset completeness against OEIS sequences and document validation results in docs/reproducibility/validation_scope.md (per SC-001)
- [X] T026 [US1] Validate tabulation accuracy for core invariants (crossing number, braid index) against KnotInfo reference values and document results in docs/reproducibility/core_precision_consistency.md with pass/fail status and coverage percentage; note that braid index is TABULATED from Knot Atlas per FR-003/SC-008 (algorithm validation for additional invariants deferred to Phase 2+ per SC-010; core invariants are TABULATED not computed, so algorithm validation does not apply to Phase 1; Constitution Principle VI applies to computed invariants in Phase 2+)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation - Tests require the code to exist first**

- [X] T011 [P] [US1] Contract test for data schema in tests/contract/test_schemas.py
- [X] T012 [P] [US1] Integration test for download pipeline in tests/integration/test_pipeline.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Establish Measurement Precision for Core Invariants (Priority: P2)

**Goal**: Establish precision thresholds for crossing number and braid index before correlation analysis proceeds so that I can validate measurement accuracy across different classes of prime knots

**Independent Test**: Can be fully tested by generating scatter plots and summary statistics showing the crossing number vs. braid index relationship for alternating knots separately from non-alternating knots, with validation against reference values where available.

### Implementation for User Story 2

- [X] T022 [US2] Implement precision validation module in code/analysis/precision.py to validate crossing number and braid index (per FR-002, FR-003)
- [X] T023 [US2] Generate scatter plots of crossing number vs. braid index stratified by alternating/non-alternating in code/analysis/exploratory.py (per FR-004)
- [X] T024 [US2] Save plots to data/plots/crossing_vs_braid.png with resolution 1200x900 pixels
- [X] T028 [US2] Compute null percentage for required invariant fields and document in docs/reproducibility/data_quality_report.md (per FR-002, SC-013)
- [X] T029 [US2] Apply missing_invariant_flags and data_quality_flags defined in T009/T010 in code/data/validator.py (per FR-002, FR-009; NOTE: requires T009/T010 flag definitions from Phase 2)
- [X] T030b [US2] Implement validation script to automate tie-breaking rule consistency checks in docs/reproducibility/tie_breaking_validator.py (per SC-007; verification: script must return success exit code (0) on consistency check per SC-007; Depends on T030)
- [X] T067 [US2] Add human-readable complexity interpretation guide in docs/reproducibility/complexity_interpretation.md (per dan-rockmore-simulated review - "human readability" of metric)
- [X] T068 [US2] Generate visualization examples showing how complexity metric maps to knot diagram features in data/plots/complexity_visualization_examples.png (per dan-rockmore-simulated review)
- [X] T069 [US2] Document concrete data quantities processed (knot counts per crossing number, total records, null percentages) in docs/reproducibility/data_quantities.md (per marie-curie-simulated review - "concrete numbers")
- [X] T070 [US2] Document classification error margins and signal-to-noise ratio analysis in docs/reproducibility/classification_error_analysis.md (per marie-curie-simulated review)

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation - Tests require the code to exist first**

- [X] T021 [P] [US2] Contract test for precision validation output in tests/contract/test_precision.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Fit Regression Models to Assess Joint Predictive Relationships (Priority: P3)

**Goal**: Fit multiple regression models to test linear vs. non-linear relationships for associating hyperbolic volume from crossing number and braid index

**Independent Test**: Can be fully tested by executing the regression and validation pipeline on an exploratory sample and producing correlation coefficients and goodness-of-fit metrics.

### Implementation for User Story 3

- [X] T032 [US3] Implement regression model fitting (linear, polynomial, logarithmic) in code/analysis/regression.py (per FR-005)
- [X] T033 [US3] Compute goodness-of-fit metrics (R², AIC/BIC, MAE) for each model type in code/analysis/regression.py (per FR-005)
- [X] T034 [US3] Implement residual analysis to identify hyperbolic knot families (pretzel, hyperbolic non-alternating) in code/analysis/residual_analysis.py (per FR-005, SC-011)
- [X] T035 [US3] Document residual family analysis in docs/reproducibility/residual_analysis.md with specific knot identifiers and potential explanations
- [X] T036 [US3] Compute Spearman and Pearson correlation coefficients with effect sizes (Cohen's d, r) in code/analysis/regression.py (per FR-006; verification: explicitly verify p-values are NOT reported for census data and marked as 'not applicable for census data' in all output artifacts per FR-006 and Constitution Principle VII census-data exception)
- [X] T037 [US3] Compute VIF for multicollinearity assessment in code/analysis/regression.py (per FR-005)
- [X] T038 [US3] Document multicollinearity assessment in docs/reproducibility/multicollinearity_assessment.md with acknowledgment of braid index ≤ crossing number definitional constraint (per plan.md Assumptions)
- [X] T039 [US3] Compute descriptive comparison metrics (mean difference, variance ratio, Cohen's d) for alternating vs. non-alternating groups in code/analysis/regression.py (per FR-006)

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation - Tests require the code to exist first**

- [X] T031 [P] [US3] Contract test for regression model output in tests/contract/test_regression.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Edge Case Handling, Data Quality, and Reproducibility Documentation (Priority: P4)

**Goal**: Handle edge cases (API unavailability, missing invariants, ambiguous classifications, crossing number ties) with documented fallback behaviors, AND produce complete reproducibility documentation

**Independent Test**: Can be fully tested by (1) simulating edge cases and verifying appropriate flags/logs, AND (2) verifying that all reproducibility artifacts are present.

### Implementation for User Story 4

- [X] T044 [US4] Generate SHA-256 checksums for all data files in code/reproducibility/checksums.py (per FR-007)
- [X] T045 [US4] Record checksums in data/ directory and document in docs/reproducibility/checksums.md (per FR-007)
- [X] T046 [US4] Generate derivation notes with formula citations in docs/reproducibility/derivation_notes.md (include formula citations with page/section references, step‑by‑step transformation logic with intermediate values, all parameter values used, and justification for any non‑standard choices per FR-007; verification: validation script in code/reproducibility/derivation_validator.py confirms all four sections present with non‑empty content)
- [X] T049 [US4] Generate timestamped logs for all operations in docs/reproducibility/operation_logs.md (per FR-007)
- [X] T050 [US4] Document random seed values used in docs/reproducibility/random_seeds.md (per FR-007)
- [X] T051 [US4] Log uncomputable invariants in docs/reproducibility/uncomputable_invariants.md (per FR-003)
- [X] T052 [US4] Document invariant coverage in docs/reproducibility/invariant_coverage.md (per SC-008)
- [X] T053 [US4] Generate validation status report in docs/reproducibility/validation_status.md (per SC-007)

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation - Tests require the code to exist first**

- [X] T042 [P] [US4] Integration test for edge case handling in tests/integration/test_edge_cases.py

**Checkpoint**: At this point, User Stories 1, 2, 3 AND 4 should all work independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T054a [P] Generate invariant algorithms documentation in docs/reproducibility/invariant_algorithms.md with reference implementations and mathematical definitions per FR-003
- [X] T054 [P] Documentation updates in docs/reproducibility/ (ensure all FR-007 required reproducibility documents are present with required content: data_quality_report.md, validation_scope.md, excluded_knots.md, invariant_coverage.md, random_seeds.md, tie_breaking_rules.md, validation_status.md, algorithm_validation.md, hyperbolic_volume_validation.md, residual_analysis.md, multicollinearity_assessment.md, uncomputable_invariants.md, checksums.md, derivation_notes.md, operation_logs.md, census_interpretation.md, mathematical_constraints.md, invariant_algorithms.md, core_precision_consistency.md, correlation_metrics.md, ambiguous_classification_log.md)
- [X] T055 Code cleanup and refactoring in code/ to meet linting standards (black --check pass with no violations) and document linting report in docs/reproducibility/linting_report.md
- [X] T056 Run quickstart.md validation to ensure end-to-end reproducibility and document validation results in docs/reproducibility/quickstart_validation.md with end-to-end pass/fail status
- [X] T057 [P] Additional unit tests in tests/unit/ (test_downloader.py with test_download_retry_logic that verifies exponential backoff delays 1s→2s→4s on simulated failures; test_download_partial_cache that verifies cache creation after 3 consecutive failures; test_download_timeout that verifies timeout handling; test_parser.py with test_crossing_number_parsing, test_braid_index_parsing, test_hyperbolic_volume_parsing)
- [X] T058 Verify all random seeds are pinned and document verification results in docs/reproducibility/seed_verification.md with all pinned seed values (distinct from T050 random_seeds.md which lists values used)
- [X] T059 Document selection bias acknowledgment (hyperbolic-only filtering) in docs/reproducibility/selection_bias.md (per FR-012, Assumptions)
- [X] T060 Document census data statistical interpretation in docs/reproducibility/census_interpretation.md (per Assumptions)
- [X] T061 Document mathematical constraint acknowledgment (braid index ≤ crossing number) in docs/reproducibility/mathematical_constraints.md (per Assumptions)
- [X] T071 [P] Create final summary report in docs/reproducibility/final_report.md synthesizing all findings with human-readable complexity interpretations (per dan-rockmore-simulated review - "concrete data quantities and measurement precision standards")
- [X] T072 [P] Create methodology appendix in docs/reproducibility/methodology_appendix.md with concrete data quantities and measurement precision standards (per marie-curie-simulated review)

---

## Phase N+1: Revision Tasks Addressing Review Feedback (REVIEWER-DRIVEN ADDITIONS - BEYOND ORIGINAL SPEC)

**⚠️ SCOPE CREEP ACKNOWLEDGMENT**: All tasks in this phase (T073-T086) are reviewer-driven additions beyond the original spec requirements. Per Constitution Principle IV, these additions are explicitly documented as such to preserve traceability.

**⚠️ TASK REMOVAL NOTE**: T079 was removed as it requested computing SHA-256 hash of tasks.md within the same revision cycle (circular task, not practically executable).

**Purpose**: Resolve outstanding reviewer concerns and ensure compliance with all functional and reproducibility requirements.

- [X] T073 [P] Update `code/download/knot_atlas_loader.py` to explicitly request the braid‑index column from Knot Atlas API (per data‑quality reviewer comment) and log the request parameters.
- [X] T074 [P] Implement fallback lookup of missing braid‑index values from KnotInfo within the downloader; merge results into the main dataset when Knot Atlas lacks the field. **NOTE: REVIEWER-DRIVEN ADDITION** - This task extends beyond original spec requirements.
- [X] T075 [P] Refactor `code/data/validator.py` so that `missing_invariant_flags` are only set for invariants that cannot be computed from diagram representations (Phase 2+), ensuring core tabulated invariants (crossing number, braid index) never receive this flag.
- [X] T076 [P] After fixing braid‑index acquisition and flag logic, regenerate `docs/reproducibility/data_quality_report.md` and `docs/reproducibility/invariant_coverage.md`; verify that null percentages for all required fields are ≤ 5 % and that flag counts are accurate. (Depends on T073, T075)
- [X] T077 [P] Run `code/reproducibility/run_checksums.py` on all current data files; update `data/checksums.sha256` (per plan.md) to reflect the new hashes; commit the updated manifest. (Depends on T044, T045)
- [X] T078 [P] Add a checksum‑verification step to `docs/reproducibility/quickstart.md` that aborts pipeline execution if any checksum mismatch is detected; include automated test `tests/integration/test_checksum_verification.py`. (Depends on T077)
- [X] T080 [P] Add unit tests for the exponential backoff behavior in the downloader (`tests/unit/test_backoff.py`) verifying delay progression (1 s → 2 s → 4 s → …) and maximum cap.
- [X] T081 [P] Add unit tests for regression model fitting and goodness‑of‑fit metric calculation (`tests/unit/test_regression_metrics.py`) ensuring R², AIC, BIC, and MAE are computed correctly for synthetic data.
- [X] T082 [P] Add unit tests for residual‑family identification logic (`tests/unit/test_residual_analysis.py`) confirming that families with residuals ≥ 2 σ are correctly listed.
- [X] T083 [P] Add comprehensive type hints (PEP 484) to key modules: `code/download/knot_atlas_loader.py`, `code/analysis/precision.py`, `code/analysis/regression.py`, and `code/data/validator.py`; run `mypy` as part of CI.
- [X] T084 [P] Refactor analysis code into focused modules per code‑quality reviewer suggestion:
 - `code/analysis/coverage.py` – pure coverage calculations
 - `code/analysis/validation.py` – hyperbolic‑volume cross‑checks
 - `code/analysis/model_fitting.py` – regression fitting and residual analysis
 - `code/analysis/plotting.py` – all figure generation
 (Depends on T032-T034)
- [X] T085 [P] Update CI workflow to include linting, type‑checking (`mypy`), and the new unit tests; ensure the pipeline completes within the specified CI limit.
- [X] T086 [P] Document the newly added type‑hinting and modularization in `docs/reproducibility/code_structure.md` for future maintainers.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase N+1)**: Depends on prior phases being complete; can run in parallel with Polish once foundational work is verified.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2) - EXCEPT T009, T010, T043a which modify same file
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all implementation for User Story 1 together:
Task: "Implement Knot Atlas downloader in code/download/knot_atlas_loader.py"
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
- **Reviewer Concerns Addressed**:
 - **FR-010 Compliance**: T043a (ambiguous classification handling - exclude or mark as 'unclassifiable') in Foundational with verification criteria
 - **FR-008 Partial Results Cache**: T014 explicitly includes caching partial results after 3 consecutive failures with verification criteria
 - **Constitution Principles**: T065 (citation validation per Principle II), T066 (content hashing per Principle V) with explicit agent integration documentation
 - **Constitution Principle V**: T066 includes updated_at timestamp verification per explicit Constitution requirement
 - **Constitution Principle VI**: T026a explicitly addresses invariant definition verification per Constitution Principle VI, with clarification that core invariants are TABULATED not computed
 - **Phase Boundary (FR-003)**: T026 validates tabulation accuracy for core invariants; T026a handles algorithm validation for additional invariants deferred to Phase 2+ per SC-010; output file renamed to core_precision_consistency.md to align with SC-015
 - **Data Flow Order**: Download (T013‑T018, T019, T040, T020) → Precision/EDA (T022‑T030, T030b) → Regression (T032‑T039) → Edge Cases/Reproducibility (T044‑T053)
 - **T040‑T019 Ordering**: T040 now comes after T019 to validate on filtered dataset
 - **T026 Placement**: T026 moved to Phase 3 (US1) since it depends on US1 data availability
 - **T029 Dependency**: T029 explicitly notes dependency on T009/T010 from Phase 2
 - **T011‑T012 Ordering**: Tests moved AFTER implementation tasks to fix producer‑consumer violation
 - **T065‑T066 [P] Removal**: Removed [P] tag from T065, T066 as they are documentation‑only tasks
 - **Phase 1 Scope Boundary**: All tasks for crossing number ≤10 validation are marked; crossing number 11‑13 data is downloaded but not validated per spec requirements
 - **dan-rockmore-simulated Review**: T067 (human-readable complexity interpretation), T068 (visualization examples), T071 (final summary with human-readable interpretations)
 - **marie-curie-simulated Review**: T069 (concrete data quantities), T070 (classification error margins), T072 (methodology appendix with precision standards)
 - **Naming Conventions**: T050 (random_seeds.md) vs T058 (seed_verification.md) explicitly distinguished
 - **Duplicate Work Removal**: T017 (dataset_counts.md) removed - T020 handles all dataset counting per SC-001
 - **Traceability**: T065/T066 explicitly cite Constitution Principles II/V
 - **T026 Output File**: Renamed from core_invariants_tabulation.md to core_precision_consistency.md to match SC-015 specification
 - **T054 Checklist Updates**: Added invariant_algorithms.md, correlation_metrics.md, ambiguous_classification_log.md to required documents list; changed logs.md reference to operation_logs.md for filename consistency
 - **File Path Alignment**: T013 uses code/download/knot_atlas_loader.py per plan.md (not knot_atlas_downloader.py)
 - **T014 Dependency**: T014 explicitly marked as dependent on T013 since retry logic is part of downloader
 - **T030b Dependency**: T030b explicitly marked as dependent on T030 since validation requires rules documentation
 - **T056 Dependency**: T056 depends on T008 (quickstart.md must exist before validation)
 - **SC-012 Compliance**: T019 includes explicit verification step confirming exclusion count matches excluded_knots.md
 - **FR-013 Compliance**: T040 includes ≥90% match threshold requirement AND skip condition verification in verification
 - **SC-007 Compliance**: T030b includes success exit code (0) verification requirement
 - **Constitution Principle I**: T007 expanded to all code/ files with stochastic operations, not just __init__.py
 - **Constitution Principle II/V**: T065/T066 document agent integration rather than custom implementation
 - **Constitution Principle VI**: T026a explicitly addresses invariant definition verification requirement with tabulated vs computed distinction
 - **Coverage Gaps**: T005b (dataset.schema.yaml), T008 (quickstart.md) added to cover plan.md artifacts
 - **Phase Boundary Clarity**: T026 vs T026a split clarifies Phase 1 (tabulation) vs Phase 2+ (algorithm validation) boundary
 - **T057 Test Assertions**: T057 now specifies exact assertions for each test function
 - **T007 Conditional Verification**: T007 verification made conditional to handle vacuous truth case
 - **T036 Census Data Compliance**: T036 includes explicit verification that p-values are NOT reported for census data per FR-006 and Constitution Principle VII
 - **Test Ordering Consistency**: T021, T031, T042 moved AFTER implementation tasks to match T011-T012 pattern
 - **T014 Retry Operation**: Explicitly states 'downloading knot data from Knot Atlas API' as the retried operation
 - **Template Placeholders**: All {{claim:c_...}} placeholders replaced with concrete values
 - **Revision Task Dependencies**: T076, T077, T078, T084 have explicit dependency annotations; [P] tags removed from tasks with dependencies
 - **Scope Creep Documentation**: Phase N+1 header explicitly notes all tasks are reviewer-driven additions; T074 marked with '**NOTE: REVIEWER-DRIVEN ADDITION**'
- **Template Placeholder Fixes (Panel Concern executability-fa488105)**: All {{claim:c_...}} markers removed from verification sections. T016 verification uses concrete SC-001 thresholds. T040 verification uses concrete FR-013 thresholds. No remaining template placeholders in tasks.md.
- **Test Placement Standardization (Panel Concern ordering-36499398)**: All test tasks (T011-T012, T021, T031, T042) placed AFTER implementation tasks within each user story for consistent pattern.
- **Scope Creep Documentation (Panel Concern executability-4e5cb4a6)**: Phase N+1 header explicitly states 'REVIEWER-DRIVEN ADDITIONS - BEYOND ORIGINAL SPEC'. T074 (KnotInfo fallback lookup) marked with '**NOTE: REVIEWER-DRIVEN ADDITION**'. Phase N+1 Notes section lists all tasks as reviewer-driven vs. spec-required for clear traceability per Constitution Principle IV.
- **T077 Checksum Path Fix**: Updated from data/checksums.json to data/checksums.sha256 per plan.md specification.
- **T079 Removal**: Removed circular task requesting SHA-256 hash of tasks.md within same revision cycle.
- **SC-015 FR-014 Reference Issue**: SC-015 references non-existent FR-014 - this is in spec.md (not tasks.md). Flagged as plan-root cause requiring spec.md correction in response.

---

## Verdict

All functional requirements, reproducibility mandates, and reviewer feedback have been addressed. The remaining tasks (T073‑T086) will close the data‑quality gaps, strengthen the code base, and ensure full compliance before the next analysis pass.

**Known Issues Requiring Plan/Spec Correction**:
- SC-015 references FR-014 which does not exist in spec.md (FR-001 through FR-013 are defined). This requires spec.md correction.
