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
- Paths shown below assume single‑project structure — adjust based on plan.md structure

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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes critical data-quality logic to ensure SC-001 compliance.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Define data schemas in `specs/001-knot-complexity-analysis/contracts/knot-record.schema.yaml`
- [X] T005 [P] Define regression model schemas in `specs/001-knot-complexity-analysis/contracts/regression-model.schema.yaml`
- [X] T005b [P] Define the dataset schema file `dataset.schema.yaml` in `specs/001-knot-complexity-analysis/contracts/` (per plan.md)
- [X] T006 Setup reproducibility logging framework in `code/reproducibility/logs.py` (timestamp, operation, input_file, output_file, parameters, status, duration_ms fields documented and testable; verification: unit tests in `tests/unit/test_logs.py` confirming all relevant fields present and testable)
- [X] T007 Implement random seed pinning in all `code/` files with stochastic operations (per Constitution Principle I; verification: if stochastic operations exist, all have pinned seeds documented in `docs/reproducibility/random_seeds.md`; if none exist, document N/A in `random_seeds.md`)
- [X] T008 Create `quickstart.md` in `specs/001-knot-complexity-analysis/quickstart.md` documenting end‑to‑end pipeline execution steps (per plan.md)
- [X] T009 [P] Implement unified flagging system in `code/data/validator.py` handling missing invariant flags, data quality flags, and ambiguous classification flags in a single cohesive module. Verification: unit tests in `tests/unit/test_validator.py` demonstrating flag generation for all three types.
- [X] T016a [P] Create the validation pipeline script `code/data/run_validation.py` that orchestrates schema checks, null percentage validation (SC-001), format pass rate, and duplicate checks. Verification: script exits 0 on clean data, 1 on failure.
- [X] T026a [P] Document Constitution Principle VI invariant verification procedure for additional invariants (arc index, Seifert circle count, bridge number) against primary literature (e.g., Birman & Menasco, Ohyama 1993) in `docs/reproducibility/invariant_definitions.md`. Verification: all additional invariants have documented reference and validation notes.
- [X] T026b [P] Implement `code/analysis/invariant_coverage.py` for computing and validating additional invariants (optional for Phase 1 MVP, but required for validation logic). Verification: module runs without error on sample data.
- [X] T030 [P] Document tie‑breaking rules in `docs/reproducibility/tie_breaking_rules.md` (per SC‑007)
- [X] T040b [P] Implement `code/analysis/hyperbolic_volume_validation.py` for cross-checking hyperbolic volume against KnotInfo (framed as data integrity check, not independent verification). Verification: module runs and logs results.
- [X] T065a [P] Implement `code/reproducibility/citation_validator.py` to run the Reference‑Validator Agent logic, enforcing title‑token overlap ≥ 0.7 for all citations (per Constitution Principle II). Verification: run `python code/reproducibility/citation_validator.py` on all citations; all must meet the threshold.
- [X] T066a [P] Implement `code/reproducibility/hashing.py` to generate and record content hashes for artifacts and update `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml` (per Constitution Principle V). Verification: run `python code/reproducibility/hashing.py` and confirm hash recorded and `updated_at` timestamp updated.
- [X] T013 [US1] Implement downloader for **Knot Atlas** in `code/download/knot_atlas_loader.py` with robust braid_index parsing (per FR‑001) and exponential back‑off retry logic (initial = 1 s, multiplier = 2, max = 32 s) with partial caching (per FR‑008). Verification: successful download of at least one knot record with all required fields, including braid_index.
- [X] T015 [US1] Implement parser in `code/data/parser.py` to extract crossing number, braid index, hyperbolic volume, and alternating classification from Knot Atlas data, applying tie‑breaking rules (braid word > DT code, lexicographic) (per FR‑011). Includes fallback lookup in `code/data/parser.py` to query KnotInfo API for `braid_index` when missing; log fallback usage in `docs/reproducibility/fallback_usage_log.md` (per reviewer action item). Verification: parser outputs correctly typed fields for a sample record.
- [X] T016 [US1] Integrate `code/data/validator.py` (T009) and `code/data/run_validation.py` (T016a) to enforce null‑percentage ≤ 5 % for required fields, format pass rate ≥ 99 %, and duplicate count = 0 (per FR‑002, SC‑001). Verification: unit tests confirm enforcement of these thresholds.

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Download and Parse Knot Data from Knot Atlas for all prime knots with crossing number ≤ 13 (Priority: P1) 🎯 MVP

**Goal**: Download knot data from Knot Atlas including crossing numbers, braid indices, hyperbolic volume, and alternating/non‑alternating classification for all prime knots with crossing number ≤ 13 (≈ 9988 knots, OEIS A002863).

### Implementation for User Story 1

- [X] T014 [US1] Implement exponential back‑off retry logic (initial = 1 s, multiplier = 2, max = 32 s) in `code/download/knot_atlas_loader.py`; cache partial results after consecutive failures (per FR‑008). Verification: simulated failures trigger back‑off and cache creation.
- [X] T018 [US1] Save raw data to `data/raw/knot_atlas_raw.json` and cleaned data to `data/processed/knots_cleaned.csv`.
- [X] T017 [US1] Generate dataset size report in `docs/reproducibility/dataset_counts.md` stating the total number of prime knots with crossing number ≤ 13 (≈ 9988, OEIS A002863) and per‑crossing‑number counts. Verification: run `python code/analysis/validate_counts.py` to compare `len(df)` to the expected dataset size.
- [X] T019 [US1] Filter dataset to hyperbolic knots (volume > 0) and log excluded knots in `docs/reproducibility/excluded_knots.md` (per FR‑012). Verification: exclusion count matches log.
- [X] T040 [US1] Validate hyperbolic volume against KnotInfo reference values using `code/analysis/hyperbolic_volume_validation.py` (T040b); require ≥ 90 % record‑wise match within tolerance 1e‑6. If coverage < 90 %, document limitation and skip cross‑check (per FR‑013). Verification: report in `docs/reproducibility/hyperbolic_volume_validation.md` includes coverage percentage and any skip notice.
- [X] T020 [US1] Verify dataset size against OEIS A002863 (9988 prime knots ≤ 13 crossings). Document method and result in `docs/reproducibility/validation_scope.md` (per SC‑001). Verification: size matches OEIS count.
- [X] T026 [US1] Validate tabulation accuracy for core invariants (crossing number, braid index) against KnotInfo reference values; require ≥ 90 % coverage (per FR‑003/SC‑008). Document results in `docs/reproducibility/core_invariants_tabulation.md`. Verification: coverage percentage reported.

### Tests for User Story 1 (OPTIONAL)

- [X] T011 [P] [US1] Contract test for data schema in `tests/contract/test_schemas.py`
- [X] T012 [P] [US1] Integration test for download pipeline in `tests/integration/test_pipeline.py`

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Establish Measurement Precision for Core Invariants (Priority: P2)

**Goal**: Establish precision thresholds for crossing number and braid index before correlation analysis proceeds so that I can validate measurement accuracy across different classes of prime knots.

### Implementation for User Story 2

- [X] T022 [US2] Implement precision validation module in `code/analysis/precision.py` to validate crossing number and braid index (per FR‑002, FR‑003). Verification: module outputs pass/fail per thresholds.
- [X] T023 [US2] Generate scatter plots of crossing number vs. braid index stratified by alternating/non‑alternating in `code/analysis/exploratory.py` (per FR‑004). Save to `data/plots/crossing_vs_braid.png` (1200 × 900 px).
- [X] T028 [US2] Compute null percentage for required invariant fields and document in `docs/reproducibility/data_quality_report.md` (per FR‑002, SC‑013). Verification: report reflects current dataset.
- [X] T029 [US2] Apply `missing_invariant_flags` and `data_quality_flags` defined in T009 (per FR‑002, FR‑009). Verification: flags appear in validation outputs.
- [X] T030b [US2] Implement validation script `docs/reproducibility/tie_breaking_validator.py` that checks consistency of tie‑breaking rules; script must exit 0 on success (per SC‑007). Verification: script runs and returns 0 for current data.
- [X] T067 [US2] Add human‑readable complexity interpretation guide in `docs/reproducibility/complexity_interpretation.md` (per reviewer feedback).
- [X] T068 [US2] Generate visualization examples mapping complexity metric to knot diagram features in `data/plots/complexity_visualization_examples.png`.
- [X] T069 [US2] Document concrete data quantities processed (knot counts per crossing number, total records, null percentages) in `docs/reproducibility/data_quantities.md`.
- [X] T070 [US2] Document classification error margins and signal‑to‑noise ratio analysis in `docs/reproducibility/classification_error_analysis.md`.

**Checkpoint**: User Stories 1 and 2 should both work independently.

---

## Phase 5: User Story 3 - Fit Regression Models to Assess Joint Predictive Relationships (Priority: P3)

**Goal**: Fit multiple regression models to test linear vs. non‑linear relationships for associating hyperbolic volume from crossing number and braid index.

### Implementation for User Story 3

- [X] T032 [US3] Implement regression model fitting (linear, polynomial degree 2, logarithmic) in `code/analysis/regression.py` (per FR‑005).
- [X] T033 [US3] Compute goodness‑of‑fit metrics (R², AIC/BIC, MAE) for each model (per FR‑005).
- [X] T034 [US3] Perform residual analysis to identify hyperbolic knot families **pretzel** and **hyperbolic non‑alternating** (per FR‑005, SC‑011). Document families in `docs/reproducibility/residual_analysis.md`.
- [X] T035 [US3] Document residual family analysis in `docs/reproducibility/residual_analysis.md` with specific knot identifiers and explanations.
- [X] T036 [US3] Compute Spearman and Pearson correlation coefficients with effect sizes (Cohen’s d, r); explicitly note that p‑values are **not reported** for census data (per FR‑006 and Constitution Principle VII). Verification: output files contain “p‑value: N/A”.
- [X] T037 [US3] Compute VIF for multicollinearity assessment (per FR‑005). Verification: VIF values recorded in `docs/reproducibility/multicollinearity_assessment.md`.
- [X] T038 [US3] Document multicollinearity assessment in `docs/reproducibility/multicollinearity_assessment.md`, explicitly acknowledging the mathematical constraint **braid index ≤ crossing number** (per FR‑005).
- [X] T039 [US3] Compute descriptive comparison metrics (mean difference, variance ratio, Cohen’s d) for alternating vs. non‑alternating groups in `code/analysis/regression.py` (per FR‑006).

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: User Story 4 - Edge Case Handling, Data Quality, and Reproducibility Documentation (Priority: P4)

**Goal**: Handle edge cases (API unavailability, missing invariants, ambiguous classifications, crossing number ties) with documented fallback behaviors, AND produce complete reproducibility documentation.

### Implementation for User Story 4

- [X] T044 [US4] Generate SHA‑256 checksums for all data files in `code/reproducibility/checksums.py` (per FR‑007).
- [X] T045 [US4] Record checksums in `data/checksums.sha256` and document in `docs/reproducibility/checksums.md`.
- [X] T046 [US4] Generate derivation notes with formula citations in `docs/reproducibility/derivation_notes.md`. Verification script `code/reproducibility/derivation_validator.py` confirms all required sections are non‑empty.
- [X] T049 [US4] Generate timestamped logs for all operations in `docs/reproducibility/operation_logs.md`.
- [X] T050 [US4] Document random seed values used in `docs/reproducibility/random_seeds.md`.
- [X] T051 [US4] Log uncomputable invariants in `docs/reproducibility/uncomputable_invariants.md` (per FR‑003).
- [X] T052 [US4] Document invariant coverage in `docs/reproducibility/invariant_coverage.md` (per SC‑008).
- [X] T053 [US4] Generate validation status report in `docs/reproducibility/validation_status.md` (per SC‑007).

**Checkpoint**: User Stories 1‑4 should all work independently.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T054a [P] Generate invariant algorithms documentation in `docs/reproducibility/invariant_algorithms.md` with reference implementations and mathematical definitions per FR‑003.
- [X] T054 [P] Documentation updates in `docs/reproducibility/` (ensure all FR‑007 required reproducibility documents are present with required content: `data_quality_report.md`, `validation_scope.md`, `excluded_knots.md`, `invariant_coverage.md`, `random_seeds.md`, `tie_breaking_rules.md`, `validation_status.md`, `algorithm_validation.md`, `hyperbolic_volume_validation.md`, `residual_analysis.md`, `multicollinearity_assessment.md`, `uncomputable_invariants.md`, `checksums.md`, `derivation_notes.md`, `operation_logs.md`, `census_interpretation.md`, `mathematical_constraints.md`, `invariant_algorithms.md`, `core_invariants_tabulation.md`, `correlation_metrics.md`, `ambiguous_classification_log.md`).
- [X] T055 Code cleanup and refactoring in `code/` to meet linting standards (black --check passes with no violations) and document linting report in `docs/reproducibility/linting_report.md`.
- [X] T056 Run `quickstart.md` validation to ensure end‑to‑end reproducibility and document validation results in `docs/reproducibility/quickstart_validation.md` with end‑to‑end pass/fail status.
- [X] T057 [P] Additional unit tests in `tests/unit/`:
 - `test_downloader.py` with tests for exponential back‑off, partial cache creation, and timeout handling.
 - `test_parser.py` with tests for crossing number parsing, braid index parsing, hyperbolic volume parsing.
- [X] T058 Verify all random seeds are pinned and document verification results in `docs/reproducibility/seed_verification.md` (distinct from `random_seeds.md` which lists values used).
- [X] T059 Document selection bias acknowledgment (hyperbolic‑only filtering) in `docs/reproducibility/selection_bias.md` (per FR‑012, Assumptions).
- [X] T060 Document census data statistical interpretation in `docs/reproducibility/census_interpretation.md` (per Assumptions).
- [X] T061 Document mathematical constraint acknowledgment (**braid index ≤ crossing number**) in `docs/reproducibility/mathematical_constraints.md` (per Assumptions).
- [X] T071 [P] Create final summary report in `docs/reproducibility/final_report.md` synthesizing all findings with human‑readable complexity interpretations and concrete data quantities (per reviewer feedback).
- [X] T072 [P] Create methodology appendix in `docs/reproducibility/methodology_appendix.md` with concrete data quantities and measurement precision standards (per reviewer feedback).

---

## Phase N+2: Code Quality & Modularity Refactoring (Addressing Research Reviewer Code Quality Concerns)

**Purpose**: Address modularity, type hinting, and test coverage gaps identified in `research_reviewer_code_quality_research__2026-06-18__research.md`.

- [X] T081 [US3] Refactor `code/analysis/invariant_coverage.py` (created in T026b) into focused modules: `code/analysis/coverage.py` (pure calculations) and `code/analysis/coverage_reporting.py` (report generation) (per Reviewer Action Item Modularity & Readability).
- [X] T082 [US3] Refactor `code/analysis/hyperbolic_volume_validation.py` (created in T040b) into `code/analysis/validation.py` (cross‑check logic) and `code/analysis/validation_reporting.py` (report generation) (per Reviewer Action Item Modularity & Readability).
- [ ] T083 [US3] Refactor `code/analysis/regression.py` into `code/analysis/model_fitting.py` (regression fitting, residuals, metrics) and `code/analysis/plotting.py` (figure generation) (per Reviewer Action Item Modularity & Readability).
- [ ] T084 [US1] Add PEP 484 type annotations to `code/download/knot_atlas_loader.py` (per Reviewer Action Item Type Hints).
- [ ] T085 [US2] Add PEP 484 type annotations to `code/analysis/precision.py` (per Reviewer Action Item Type Hints).
- [ ] T086 [US3] Add unit tests in `tests/unit/test_regression.py` for regression model fitting and goodness‑of‑fit metric calculation (per Reviewer Action Item Testing).
- [ ] T087 [US3] Add unit tests in `tests/unit/test_residual_analysis.py` for residual‑family identification logic (per Reviewer Action Item Testing).
- [ ] T088 [US1] Add unit tests in `tests/unit/test_downloader.py` specifically for exponential back‑off behavior (per Reviewer Action Item Testing).

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

- **Setup (Phase 1)**: No dependencies – can start immediately.
- **Foundational (Phase 2)**: Depends on Setup – BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational; can run in parallel once Phase 2 is complete.
- **Polish (Final Phase)**: Depends on all desired user stories being complete.
- **Code Quality Refactoring (Phase N+2)**: Can run in parallel with Phase N+1 but depends on Phase 3 completion.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational.
- **User Story 2 (P2)**: Starts after Foundational; may integrate with US1 but independent.
- **User Story 3 (P3)**: Starts after Foundational; may integrate with US1/US2 but independent.
- **User Story 4 (P4)**: Starts after Foundational; may integrate with US1‑US3 but independent.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked **[P]** can run in parallel.
- All Foundational tasks marked **[P]** can run in parallel (except T009 which is a single file).
- Once Foundational completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked **[P]** can run in parallel.
- Models within a story marked **[P]** can run in parallel.
- Different user stories can be worked on in parallel by different team members.
- Phase N+2 (Code Quality) can run in parallel with other phases if capacity allows.

### Task Dependencies (Non‑Parallel)

- T013 → T014: T014 depends on T013 (retry logic part of downloader) – now ordered correctly.
- T019 → T040: T040 depends on T019 (validation on filtered dataset).
- T030 → T030b: T030b depends on T030 (validation script requires rules documentation).
- T009 → T029: T029 depends on T009 (flag definitions from Phase 2).
- T008 → T056: T056 depends on T008 (quickstart.md must exist before validation).
- T081, T082, T083: must complete before T084‑T088 (type hints/tests on refactored modules).
- T026b, T040b: must complete before T081, T082 (refactoring targets).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (including critical remediation logic integrated into T009, T013, T015, T016a).
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: Test User Story 1 independently.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready.
2. Add User Story 1 → Test → Deploy/Demo (MVP!).
3. Add User Story 2 → Test → Deploy/Demo.
4. Add User Story 3 → Test → Deploy/Demo.
5. Add User Story 4 → Test → Deploy/Demo.
6. Each story adds value without breaking previous stories.

### Parallel Team Strategy

- **Team A**: Setup + Foundational (including T009, T013, T015, T016a).
- **Team B**: User Story 1 (Download/Parse).
- **Team C**: User Story 2 (Precision/EDA).
- **Team D**: User Story 3 (Regression).
- **Team E**: User Story 4 (Edge‑case handling & reproducibility).

---

## Notes

- **[P]** tasks = different files, no dependencies.
- **[Story]** label maps task to specific user story for traceability.
- Verify tests fail before implementing.
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.
- Avoid vague tasks, same‑file conflicts, cross‑story dependencies that break independence.
- **Data Quality Remediation**: Logic for braid index parsing, flagging, and validation pipeline (previously T073-T077, T078-T080) has been integrated directly into Phase 2 tasks (T009, T013, T015, T016a) to ensure SC-001 compliance is a prerequisite. Phase N+1 has been removed.
- **Code Quality Refactoring**: T081-T083 now target files created in Phase 2 (T026b, T040b) to resolve phantom file references.
- **Agent Integration**: T065a and T066a implement the actual agent logic scripts.
- **Unified Flagging**: T009 consolidates all flagging systems into a single cohesive module.
- **Execution Paths**: T017, T065a, T066a now specify exact script paths for deterministic execution.