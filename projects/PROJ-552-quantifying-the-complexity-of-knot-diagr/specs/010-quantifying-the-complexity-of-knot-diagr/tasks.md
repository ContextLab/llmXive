---
description: "Task list for Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index"
---

# Tasks: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Input**: Design documents from `/specs/010-quantifying-the-complexity-of-knot-diagr/`
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
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan. **Deliverable**: Create directories: `code/download`, `code/data`, `code/analysis`, `code/reproducibility`, `code/utils`, `data/raw`, `data/processed`, `data/plots`, `docs/reproducibility`, `docs/analysis`, `tests/unit`, `tests/integration`, `tests/contract`. **Verification**: Run `ls -R` and verify against `plan.md` Project Structure section.
- [X] T002 Initialize Python 3.11 project with dependencies. **Deliverable**: Create `code/requirements.txt` containing: `pandas`, `numpy`, `statsmodels`, `matplotlib`, `requests`, `pyyaml`, `seaborn`, `pytest`, `scikit-learn`, `database-knotinfo`.
- [X] T003 [P] Configure linting and formatting tools. **Deliverable**: Create `code/.black`, `code/.flake8`, and `code/mypy.ini` (or `pyproject.toml` sections) with configurations referencing `specs/010-quantifying-the-complexity-of-knot-diagr/templates/lint-config.yaml`.
- [X] T005 [P] Setup CI/CD pipeline. **Deliverable**: Create `.github/workflows/ci.yml` containing jobs for `linting`, `formatting check`, and `pytest` execution, triggered on push to main and PRs.
- [X] T006 [P] Setup initial testing framework. **Deliverable**: Create `tests/conftest.py` with fixtures for data paths and `tests/__init__.py`. **Verification**: Run `pytest --collect-only` and verify it returns 0 tests without error.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Note**: This project uses local file storage only. No database, authentication, or API routing is required or implemented.

- [X] T004 [P] Implement `database-knotinfo` client wrapper in `code/download/knot_info_loader.py` (FR-008). **Deliverable**: Create script that fetches data using `database-knotinfo` library, implements exponential back-off retry logic, and handles network errors. **Verification**: Script runs without error and fetches sample data.
- [X] T007 Create `code/data/tie_breaking_validator.py` script that returns exit code 0 on success and generate `docs/reproducibility/tie_breaking_rules.md` (SC-007). **Note**: This script implements the logic; execution is handled in Phase 3 (T012b).

### Analysis Module Prerequisites (Moved from Phase N+1 to Phase 2)

*Note: T041 and sub-tasks are moved here to ensure modules exist before T029 (Regression) in Phase 5.*

- [X] T041 [US3] **Split `code/analysis/model_fitting.py` into four distinct modules** (see T041a-T041d). **Note**: T041a-T041d are the atomic implementation tasks; this parent task is a summary checkpoint.
  - [X] T041a [US3] **Create `code/analysis/model_fitting.py`**: Split logic from `code/analysis/regression.py`. Implement Linear, Polynomial, Logarithmic, AND Ridge regression models (Ridge as descriptive comparison only). Calculate R², AIC, BIC, MAE. (FR-005).
  - [X] T041b [US3] **Create `code/analysis/residual_analysis.py`**: Split logic from `code/analysis/regression.py`. Implement logic for identifying families deviating ≥ 2 SD (SC-011).
  - [X] T041c [US3] **Create `code/analysis/plotting.py`**: Split logic from `code/analysis/exploratory.py`. Implement all figure generation logic (FR-004, SC-016).
  - [X] T041d [US3] **Create `code/analysis/model_reporting.py`**: Split logic from `code/analysis/regression.py`. Implement logic for generating markdown/JSON reports for these models.

### Data Pipeline & Invariant Validation (Foundational - Moved to Phase 3 for dependency order)

*Note: T056 and T057 have been moved to Phase 3 to ensure they execute after data production tasks.*

---

## Phase 3: User Story 1 - Download and Parse Knot Data from Knot Atlas (Priority: P1) 🎯 MVP

**Goal**: Download knot data from Knot Atlas including crossing numbers, braid indices, hyperbolic volume, and alternating/non-alternating classification for all prime knots with crossing number ≤ 13.

- [X] T010 [US1] **Generate Validation Scope Document**: Create `docs/reproducibility/validation_scope.md` containing the ≤10 vs ≤13 crossing distinction, justification, and counts table (SC-012, Plan Phase 1 Step 1.3). **Note**: This must be generated BEFORE filtering and analysis.
- [X] T011 [US1] Create `code/download/knot_info_loader.py` to download data using the `database-knotinfo` library and retry logic from T004.
- [X] T012 [US1] Implement parser in `code/data/parser.py` to clean and normalize data. **CRITICAL**: Validate and flag *only* tabulated invariants (crossing number, braid index) present in the raw data. Do NOT implement logic for Phase 2+ computed invariants (arc index, etc.) here; that logic belongs in Phase 2+ (not implemented yet). Ensure `missing_invariant_flags` are ONLY set for missing *tabulated* values or format errors (FR-009, SC-009).
- [X] T012a [US1] **Implement Data Quality Report Logic**: Create `code/data/quality_report.py` to calculate null percentages, format pass rates, and duplicate counts across the *entire* dataset. Generate `docs/reproducibility/data_quality_report.md` (FR-002, SC-013).
- [X] T012b [US1] **Execute Tie-Breaking Validator**: Run `code/data/tie_breaking_validator.py` (created in T007) on the processed data. Verify exit code 0 and generate `docs/reproducibility/tie_breaking_rules.md` confirming rule application (SC-007).
- [X] T013 [US1] Implement caching in downloader (T011).
- [X] T014 [US1] Save raw data to `data/raw/knot_atlas_raw.json` and cleaned to `data/processed/knots_cleaned.csv`.
- [X] T015 [US1] **Implement Hyperbolic Filter**: Filter dataset for hyperbolic knots (`volume > 0`) in `code/data/parser.py` or a dedicated filter script. Log exclusions and **generate `docs/reproducibility/excluded_knots.md` documenting excluded records** (FR-012, SC-012). **This task implements the filter logic, not just logging.**
- [X] T028 [US3] **Perform Residual Analysis**: Implement residual analysis in `code/analysis/residual_analysis.py` using **Median Absolute Deviation (MAD)** scaled to standard deviation (* MAD) for outlier detection (≥ 2 sigma threshold) to ensure robustness (SC-011, Plan Phase 3 Step 3.2). Generate `docs/reproducibility/residual_analysis.md`.

### Data Ingestion Verification (Moved from Phase 2 to Phase 3)

- [X] T056 [US1] **Execute Real Data Ingestion Verification**: Create `code/scripts/ingest_evidence.py` that runs the pipeline, validates the **entire census** (9,988 knots) for nulls and format errors, and writes the full validation report to `docs/reproducibility/data_ingestion_evidence.md`. **Must show non-zero, non-placeholder values for crossing_number, braid_index, and hyperbolic_volume across the full dataset.**
- [X] T057 [US1] **Fix Validator Flagging Logic**: Refactor `code/data/validator.py` function `validate_invariants` to: 1. Check if invariant is in `[crossing_number, braid_index]`; if so, skip `missing_invariant_flags`. 2. For other invariants, check diagram representation availability. 3. Add unit test `tests/unit/test_validator_flags.py` asserting that `missing_invariant_flags` is empty for core invariants and populated only for Phase 2+ invariants when diagram representations are missing. **Constraint**: Core tabulated invariants must NEVER trigger `missing_invariant_flags`.

### Plot Generation & Validation (Moved to US1 per SC-016)

- [X] T021 [US1] **Generate Exploratory Plots**: Use `code/analysis/plotting.py` (created in T041c) to generate scatter plots in `data/plots/`. Generate `docs/reproducibility/plot_validation_report.md` verifying metadata and tags (SC-016).
- [X] T022 [US1] **Automated Plot Validation**: Create automated validation script for plot metadata and generate `docs/reproducibility/plot_validation_report.md` (SC-016).

### Tests for User Story 1 (OPTIONAL)

- [X] T018 [P] [US1] Contract test for data schema in `tests/contract/test_schemas.py`.
- [X] T019 [P] [US1] Integration test for download pipeline in `tests/integration/test_pipeline.py`.

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Establish Measurement Precision for Core Invariants (Priority: P2)

**Goal**: Validate measurement accuracy of core invariants across different knot classes.
*Note: Core invariant validation is now handled in T016/T017. This phase focuses on advanced invariants (Phase 2+ scope) which are currently deferred.*

- [ ] T020 [US2] **Advanced Invariant Computation (DEFERRED)**: This task is **DEFERRED** to Phase 2+ as per FR-003 and Assumptions "Phase 2+ Scope Boundary". Do NOT implement arc index, Seifert circle count, or bridge number computation in Phase 1. **Activation Gate**: This task becomes active ONLY when a "Phase 2+ Trigger" is validated (e.g., `state/phases/phase2_trigger.md` exists and confirms Phase 1 completion). **OUT OF SCOPE FOR PHASE 1.**

### Consistency Checks (Moved from Phase 3 to Phase 4 per Plan)

- [X] T016 [US2] **Validate core tabulated invariants (crossing number, braid index) against KnotInfo references** with The tolerance threshold is set to a sufficiently small value to ensure numerical stability.. Generate `docs/reproducibility/core_precision_consistency.md` (FR-013, SC-015). **This task covers the full validation scope for core invariants only.**
- [X] T017 [US2] **Validate Hyperbolic Volume consistency** against KnotInfo references. Generate `docs/reproducibility/hyperbolic_volume_validation.md` (SC-014). **This task is distinct from T016.**

### Tests for User Story 2 (OPTIONAL)

- [X] T023 [P] [US2] Contract test for precision validation module in `tests/contract/test_precision.py`.
- [X] T024 [P] [US2] Integration test for data quality check in `tests/integration/test_data_quality.py`.

**Checkpoint**: User Story 2 should be fully functional and testable independently.

---

## Phase 2.5: Computed Invariant Verification (NEW: Addresses Constitution Principle VI)

**Goal**: Compute and verify additional invariants (arc index, Seifert circle count, bridge number) for the subset where diagram representations allow, as required by Plan.md Phase 2.5.

- [X] T080 [US2] **Implement Computed Invariant Algorithms**: Create `code/data/computed_invariants.py` to compute arc index, Seifert circle count, and bridge number from diagram representations where available. **Note**: These are computed, not tabulated. (Constitution Principle VI).
- [X] T081 [US2] **Verify Computed Invariants**: Implement verification logic in `code/data/verify_invariants.py` to compare computed values against established mathematical definitions and KnotInfo (where available). Document discrepancies in `data/`.
- [X] T082 [US2] **Generate Computed Invariant Report**: Generate `docs/reproducibility/computed_invariant_verification.md` documenting the methodology, results, and any discrepancies found.
- [X] T083 [US2] **Update Data Schema**: Ensure `contracts/knot_record.schema.yaml` includes fields for these computed invariants and update `code/data/parser.py` to handle them if present in source (though they are primarily computed).

**Checkpoint**: Phase 2.5 ensures computed invariants are verified before any analysis that might use them.

---

## Phase 5: User Story 3 - Fit Regression Models to Assess Joint Predictive Relationships (Priority: P3)

**Goal**: Fit regression models to assess the relationship between hyperbolic volume, crossing number, and braid index.

- [X] T025 [US3] **Refactoring Prerequisite**: Ensure `code/analysis/regression.py` is removed or deprecated as logic has been migrated to `code/analysis/model_fitting.py` (T041a).
- [X] T026b [US3] **Implement Orthogonalization Logic**: Create `code/analysis/orthogonalization.py` to orthogonalize the braid index predictor with respect to crossing number (Plan Phase 3 Step 3.1). **Note**: This is a prerequisite for T029 (Regression).
- [X] T026a [US3] **Implement Variance Partitioning Metrics**: Implement logic to calculate variance partitioning metrics and descriptive interpretation acknowledging `braid_index <= crossing_number` constraint. **Document that coefficients are for descriptive variance partitioning only, not independent predictive value** (FR-005).
- [X] T026c [US3] **Implement Descriptive Comparison Metrics**: Create `code/analysis/comparison_metrics.py` to calculate mean differences, variance ratios, and Cohen's d for alternating vs. non-alternating knot groups. Generate `docs/reproducibility/group_comparison_metrics.md` (FR-006, SC-009). **Note**: This task is distinct from regression models and specifically addresses group comparison analysis.
- [X] T029 [US3] **Perform regression model fitting** in `code/analysis/model_fitting.py` for **Linear, Polynomial, Logarithmic, AND Ridge models**. **Note**: Ridge is included as a comparative model per Plan T-021, while Linear/Polynomial/Logarithmic are the primary forms per FR-005. **Depends on T026b (Orthogonalization).**

### VIF Calculation & Verification (Moved to Phase 5)

- [X] T058 [US3] **Correct VIF Calculation**: Create `code/scripts/verify_vif.py` that loads `data/processed/knots_cleaned.csv`, calculates VIF for crossing_number and braid_index, asserts `VIF > 5` (high multicollinearity), and writes the result to `docs/reproducibility/multicollinearity_assessment.md`. **Note**: This task runs before T029 to ensure data correctness.

### Tests for User Story 3 (OPTIONAL)

- [X] T030 [P] [US3] Contract test for regression model in `tests/contract/test_regression.py`.
- [X] T031 [P] [US3] Integration test for residual analysis in `tests/integration/test_residual_analysis.py`.

**Checkpoint**: User Story 3 should be fully functional and testable independently.

---

## Phase 6: User Story 4 - Edge Case Handling, Data Quality, and Reproducibility Documentation (Priority: P4)

**Goal**: Implement robust edge case handling and comprehensive reproducibility documentation.

- [X] T032 [US4] Implement data validation and error handling mechanisms.
- [X] T033 [US4] **Generate complete reproducibility documentation** including: `docs/reproducibility/data_quality_report.md`, `excluded_knots.md`, `random_seeds.md`, `hyperbolic_volume_validation.md`, `core_precision_consistency.md`, `residual_analysis.md`, `tie_breaking_rules.md`, `plot_validation_report.md`, and `logs/` (FR-007, SC-003). **Note**: `validation_scope.md` is generated in Phase 1 (T010), not here.
- [X] T034 [US4] Generate `docs/reproducibility/checksums.md` with SHA-256 checksums for all data files **AND update `state/...yaml` artifact map with new hashes** (FR-007, SC-003, Constitution Principle V).

### Tests for User Story 4 (OPTIONAL)

- [X] T035 [P] [US4] Unit tests for edge case handling scenarios in `tests/unit/test_edge_cases.py`.
- [X] T036 [P] [US4] Integration test for reproducibility documentation generation in `tests/integration/test_reproducibility.py`.

**Checkpoint**: User Story 4 should be fully functional and testable independently.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in docs/.
- [X] T038 [P] **Generate `docs/reproducibility/methodology.md`** explaining the rationale for using descriptive statistics (effect sizes) instead of inferential statistics (p-values) in a census analysis context (FR-006, Constitution Principle VII).
- [X] T039 [P] Code cleanup and refactoring.
- [X] T040 [P] Additional unit tests (if requested) in tests/unit/.
- [X] T041 [P] Security hardening.

---

## Phase N+1: Code Quality & Data Integrity Remediation (Review-Driven)

**Purpose**: Address critical reviewer concerns regarding file modularity, data flagging logic, and filesystem hygiene.

### Data Integrity: Fix Flagging Logic (Addressing Data Quality Review)

*Note: T046 and T047 have been removed as they were redundant and contradictory to T012/T057. Verification is covered by T056.*

### Filesystem Hygiene: Clean Up Artifacts (Addressing Filesystem Hygiene Review)

- [X] T051 [US4] **Consolidate Checksum Manifests**: Create `code/scripts/consolidate_checksums.py` to migrate `data/checksums.sha256`/`.csv` to `data/checksums.json` and update `docs/reproducibility/checksums.md`.
- [X] T052 [US4] **Consolidate Log Files**: Create `code/scripts/consolidate_logs.py` to migrate `data/logs.jsonl` to `docs/reproducibility/logs/` and update `docs/reproducibility/operation_logs.md`.
- [X] T053 [US4] **Update READMEs**: Create `docs/reproducibility/README.md` with a table of contents linking to [list of specific files] and delete `docs/reproducibility/README_SUMMARY.md`. Remove or rename files with non-standard naming (e.g., `combined_invariant_intuition_narrative_story_extra.md`) to adhere to disciplined naming conventions.

- [X] T054 [US3] **Verify Multicollinearity Calculation**: Re-implement VIF calculation in `code/analysis/model_fitting.py` to ensure it operates on actual loaded data. Verify that reported VIF values reflect the expected high multicollinearity (VIF >> 5) due to the `braid_index <= crossing_number` constraint. Document the corrected VIF in `docs/reproducibility/multicollinearity_assessment.md`.

- [X] T055 [US3] **Consolidate Regression Logic**: Check if `code/analysis/regression.py` exists.
 - [ ] If it exists and logic has been migrated to `model_fitting.py` per T041, remove or deprecate `regression.py`.
 - [ ] If it does not exist, log "Not found (expected)" and pass.
 - [ ] Ensure no duplicate regression logic exists between files.

---

## Phase N+2: Data Pipeline Verification & Statistical Correctness (Critical Review Response)

**Purpose**: Directly address the critical "Fabrication/Simulation" and "Statistical Methodology" failures identified in the latest research reviews. These tasks are blocking and must be completed before any further analysis.

*Note: T056 and T057 have been moved to Phase 3. This section now focuses on verification of the fixed pipeline.*

- [X] T059 [US3] **Remove Duplicate Regression Logic**: Audit `code/analysis/`. Ensure `code/analysis/regression.py` is removed or deprecated if `code/analysis/model_fitting.py` contains the logic. Verify no duplicate model fitting code exists.
- [X] T060 [US4] **Regenerate Data Quality Report**: Re-run the data quality pipeline with the fixed validator (T057). Generate an updated `docs/reproducibility/data_quality_report.md` showing `missing_invariant_flags` count near zero for core fields and consistent record counts (no "small vs large" contradiction).
- [X] T061 [US4] **Finalize Reproducibility Artifacts**: Ensure all logs are in `docs/reproducibility/logs/`, all checksums are in `data/checksums.json`, and `docs/reproducibility/README.md` correctly points to the authoritative reports (T053, T051, T052).

---

## Phase N+3: Advanced Code Quality & Type Safety (Addressing Code Quality Review)

**Purpose**: Address specific code quality issues regarding file size, modularity, and type safety identified in `research_reviewer_code_quality_research__2026-07-01__research.md`.

*Note: T062 has been removed as it contradicts T041a-d. The modularity is already established.*

- [X] T063 [US3] **Consolidate Visualization Modules**: Merge `code/analysis/complexity_visualization.py`, `code/analysis/complexity_visualization_examples.py`, and `code/analysis/complexity_visualization_runner.py` into a single `code/analysis/visualization.py` with clear function separation.
- [X] T064 [US3] **Consolidate Metrics Modules**: Merge `code/analysis/composite_metric*.py` files into a single `code/analysis/metrics.py`.
- [X] T065 [US3] **Enforce Type Hints**: Add PEP 484 type hints to all functions in the refactored analysis modules (`model_fitting.py`, `residual_analysis.py`, `plotting.py`, `visualization.py`, `metrics.py`). Verify with `mypy --strict code/analysis/` and fix all errors.
- [X] T066 [US3] **Create Unit Tests for Refactored Modules**: Create `tests/unit/test_model_fitting.py` and `tests/unit/test_residual_analysis.py` to cover the split logic and ensure comprehensive coverage of the refactored functions.
- [X] T067 [US3] **Verify File Size Constraints**: Create `code/scripts/check_file_sizes.py` to verify all files in `code/analysis/` are < 200 lines AND < 10KB, outputting a report to `docs/reproducibility/file_size_audit.md`.
- [X] T068 [US3] **Update Documentation for Refactoring**: Update `docs/reproducibility/methodology.md` and `docs/reproducibility/README.md` to reflect the new module structure and entry points.

---

## Phase N+4: Final Verification & Gate Clearance

**Purpose**: Execute final verification steps to ensure all reviewer concerns from `research_reviewer_data_quality_research__2026-07-01__research.md` and `research_reviewer_filesystem_hygiene__2026-07-01__research.md` are fully resolved before proceeding to the next stage gate.

- [X] T069 [US4] **Final Data Integrity Audit**: Create `code/scripts/final_data_audit.py` to run `validator.py`, check flag counts, verify record counts, and output `docs/reproducibility/final_data_integrity_audit.md`.
- [X] T070 [US3] **Final Statistical Correctness Audit**: Re-run `code/analysis/model_fitting.py` and `code/analysis/residual_analysis.py`. Confirm:
  - VIF values are >> 5 (high multicollinearity) as expected.
  - Residual analysis identifies specific families with deviations ≥ 2 SD.
  - All metrics (R², AIC, BIC, MAE) are calculated on real data.
  - Output a summary to `docs/reproducibility/final_statistical_audit.md`.
- [X] T071 [US4] **Final Filesystem Hygiene Audit**: Create `code/scripts/final_hygiene_audit.py` to verify file existence/non-existence of specific paths and output `docs/reproducibility/final_hygiene_audit.md`.
- [X] T072 [US4] **Final Consistency Check**: Re-run the hyperbolic volume consistency check against KnotInfo. Confirm match rate ≥ 90% (if coverage ≥ 90%) and document in `docs/reproducibility/hyperbolic_volume_validation.md`.
- [X] T073 [US1] **Final Real Data Evidence**: Append the first lines of `data/raw/knot_atlas_raw.json` and the a subset of lines from `data/processed/knots_cleaned.csv` to `docs/reproducibility/data_ingestion_evidence.md` to provide final proof of real data ingestion.
- [X] T074 [US4] **Generate Final Reproducibility Package**: Compile all final reports into a single `docs/reproducibility/FINAL_REPORT_PACKAGE.md` that links to all authoritative documents and summarizes the audit results from T069-T073.

**Checkpoint**: All reviewer concerns addressed; project ready for next stage gate.