---
description: "Task list for Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index"
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
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (verify via `ls -R` against `plan.md` Project Structure section)
- [X] T002 Initialize Python 3.11 project with dependencies: `pandas`, `numpy`, `statsmodels`, `matplotlib`, `requests`, `pyyaml`, `seaborn`, `pytest`, `scikit-learn` (Note: `statsmodels` is primary for regression metrics; `scikit-learn` included for potential preprocessing tools)
- [X] T003 [P] Configure linting and formatting tools (black, flake8, mypy)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Note**: This project uses local file storage only. No database, authentication, or API routing is required or implemented.

- [X] T004 [P] Implement exponential back-off retry logic in `code/download/knot_atlas_loader.py` (FR-008)
- [X] T005 [P] Setup CI/CD pipeline with linting, formatting, and basic build steps.
- [X] T006 [P] Setup initial testing framework with unit tests.
- [X] T007 Create `code/data/tie_breaking_validator.py` script that returns exit code 0 on success and generate `docs/reproducibility/tie_breaking_rules.md` (SC-007)

### Data Pipeline & Invariant Validation (Foundational)

- [X] T056 [US1] **Execute Real Data Ingestion Verification**: Run `code/download/knot_atlas_loader.py` and `code/data/parser.py` in a fresh environment. Capture the first 100 lines of `data/raw/knot_atlas_raw.json` and the first 50 lines of `data/processed/knots_cleaned.csv` into `docs/reproducibility/data_ingestion_evidence.md`. **Must show non-zero, non-placeholder values for crossing_number, braid_index, and hyperbolic_volume.**
- [X] T057 [US1] **Fix Validator Flagging Logic**: Refactor `code/data/validator.py` to strictly enforce FR-009. Add a unit test `tests/unit/test_validator_flags.py` that asserts:
  - `missing_invariant_flags` is empty for core invariants (crossing_number, braid_index) because they are tabulated.
  - `missing_invariant_flags` is populated ONLY for Phase 2+ invariants (if/when computed) when diagram representations are missing.
  - `data_quality_flags` is used for nulls/format errors.
  - **Constraint**: Core tabulated invariants must NEVER trigger `missing_invariant_flags`.

### Analysis Module Splitting (Foundational - Required before Phase 3)

- [X] T041 [US3] **Split `code/analysis/regression.py` into four distinct modules** (see T041a-T041d). **Note**: T041a-T041d are the atomic implementation tasks; this parent task is a summary checkpoint.
  - [X] T041a [US3] **Create `code/analysis/model_fitting.py`**: Split logic from `code/analysis/regression.py`. Implement Linear, Polynomial, Logarithmic, AND Ridge regression models (Ridge as descriptive comparison only). Calculate R², AIC, BIC, MAE. (FR-005)
  - [X] T041b [US3] **Create `code/analysis/residual_analysis.py`**: Split logic from `code/analysis/regression.py`. Implement logic for identifying families deviating ≥ 2 SD (SC-011).
  - [X] T041c [US3] **Create `code/analysis/plotting.py`**: Split logic from `code/analysis/exploratory.py`. Implement all figure generation logic (FR-004, SC-016).
  - [X] T041d [US3] **Create `code/analysis/model_reporting.py`**: Split logic from `code/analysis/regression.py`. Implement logic for generating markdown/JSON reports for these models.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Parse Knot Data from Knot Atlas (Priority: P1) 🎯 MVP

**Goal**: Download knot data from Knot Atlas including crossing numbers, braid indices, hyperbolic volume, and alternating/non-alternating classification for all prime knots with crossing number ≤ 13.

- [X] T011 [US1] Create `code/download/knot_atlas_loader.py` to download data using the retry logic from T004
- [X] T012 [US1] Implement parser in `code/data/parser.py` to clean and normalize data. **CRITICAL**: Validate and flag *only* tabulated invariants (crossing number, braid index) present in the raw data. Do NOT implement logic for Phase 2+ computed invariants (arc index, etc.) here; that logic belongs in Phase 2+ (not implemented yet). Ensure `missing_invariant_flags` are ONLY set for missing *tabulated* values or format errors (FR-009, SC-009).
- [X] T013 [US1] Implement caching in downloader (T011)
- [X] T014 [US1] Save raw data to `data/raw/knot_atlas_raw.json` and cleaned to `data/processed/knots_cleaned.csv`
- [X] T015 [US1] Filter dataset for hyperbolic knots, logging exclusions, and **generate `docs/reproducibility/excluded_knots.md` documenting excluded records** (FR-012, SC-012)
- [X] T016 [US1] **Validate core tabulated invariants (crossing number, braid index) against KnotInfo references** with 1e-6 tolerance. Generate `docs/reproducibility/core_precision_consistency.md` (FR-013, SC-015). **This task covers the full validation scope for core invariants only.**
- [X] T017 [US1] **Validate Hyperbolic Volume consistency** against KnotInfo references. Generate `docs/reproducibility/hyperbolic_volume_validation.md` (SC-014). **This task is distinct from T016.**

### Plot Generation & Validation (Moved to US1 per SC-016)

- [X] T021 [US1] **Generate Exploratory Plots**: Use `code/analysis/plotting.py` (created in T041c) to generate scatter plots in `data/plots/`. Generate `docs/reproducibility/plot_validation_report.md` verifying metadata and tags (SC-016).
- [X] T022 [US1] **Automated Plot Validation**: Create automated validation script for plot metadata and generate `docs/reproducibility/plot_validation_report.md` (SC-016).

### Tests for User Story 1 (OPTIONAL)

- [X] T018 [P] [US1] Contract test for data schema in `tests/contract/test_schemas.py`
- [X] T019 [P] [US1] Integration test for download pipeline in `tests/integration/test_pipeline.py`

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Establish Measurement Precision for Core Invariants (Priority: P2)

**Goal**: Validate measurement accuracy of core invariants across different knot classes.
*Note: Core invariant validation is now handled in T016/T017. This phase focuses on advanced invariants (Phase 2+ scope) which are currently deferred.*

- [ ] T020 [US2] **Advanced Invariant Computation (DEFERRED)**: This task is **DEFERRED** to Phase 2+ as per FR-003 and Assumptions "Phase 2+ Scope Boundary". Do NOT implement arc index, Seifert circle count, or bridge number computation in Phase 1. This task placeholder remains for future reference. **OUT OF SCOPE FOR PHASE 1.**

### Tests for User Story 2 (OPTIONAL)

- [X] T023 [P] [US2] Contract test for precision validation module in `tests/contract/test_precision.py`
- [X] T024 [P] [US2] Integration test for data quality check in `tests/integration/test_data_quality.py`

**Checkpoint**: User Story 2 should be fully functional and testable independently.

---

## Phase 5: User Story 3 - Fit Regression Models to Assess Joint Predictive Relationships (Priority: P3)

**Goal**: Fit regression models to assess the relationship between hyperbolic volume, crossing number, and braid index.

- [X] T025 [US3] **Refactoring Prerequisite**: Ensure `code/analysis/regression.py` is removed or deprecated as logic has been migrated to `code/analysis/model_fitting.py` (T041a).
- [X] T026 [US3] Implement regression model fitting in `code/analysis/model_fitting.py` for **Linear, Polynomial, Logarithmic, AND Ridge models**. **Note**: Ridge is included as a comparative model per Plan T-021, while Linear/Polynomial/Logarithmic are the primary forms per FR-005.
- [X] T027 [US3] **Implement variance partitioning metrics and descriptive interpretation** acknowledging braid_index <= crossing_number constraint. **Document that coefficients are for descriptive variance partitioning only, not independent predictive value** (FR-005).
- [X] T028 [US3] Perform residual analysis to identify outlier knot families and generate `docs/reproducibility/residual_analysis.md` (SC-011)

### Tests for User Story 3 (OPTIONAL)

- [X] T029 [P] [US3] Contract test for regression model in `tests/contract/test_regression.py`
- [X] T030 [P] [US3] Integration test for residual analysis in `tests/integration/test_residual_analysis.py`

**Checkpoint**: User Story 3 should be fully functional and testable independently.

---

## Phase 6: User Story 4 - Edge Case Handling, Data Quality, and Reproducibility Documentation (Priority: P4)

**Goal**: Implement robust edge case handling and comprehensive reproducibility documentation.

- [X] T031 [US4] Implement data validation and error handling mechanisms
- [X] T032 [US4] **Generate complete reproducibility documentation** including: `docs/reproducibility/data_quality_report.md`, `validation_scope.md`, `excluded_knots.md`, `random_seeds.md`, `hyperbolic_volume_validation.md`, `core_precision_consistency.md`, `residual_analysis.md`, `tie_breaking_rules.md`, `plot_validation_report.md`, and `logs/` (FR-007, SC-003)
- [X] T033 [US4] Generate `docs/reproducibility/checksums.md` with SHA-256 checksums for all data files **AND update `state/...yaml` artifact map with new hashes** (FR-007, SC-003, Constitution Principle V)

### Tests for User Story 4 (OPTIONAL)

- [X] T034 [P] [US4] Unit tests for edge case handling scenarios in `tests/unit/test_edge_cases.py`
- [X] T035 [P] [US4] Integration test for reproducibility documentation generation in `tests/integration/test_reproducibility.py`

**Checkpoint**: User Story 4 should be fully functional and testable independently.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Documentation updates in docs/
- [X] T037 [P] **Generate `docs/reproducibility/methodology.md`** explaining the rationale for using descriptive statistics (effect sizes) instead of inferential statistics (p-values) in a census analysis context (FR-006, Constitution Principle VII)
- [X] T038 [P] Code cleanup and refactoring
- [X] T039 [P] Additional unit tests (if requested) in tests/unit/
- [X] T040 [P] Security hardening

---

## Phase N+1: Code Quality & Data Integrity Remediation (Review-Driven)

**Purpose**: Address critical reviewer concerns regarding file modularity, data flagging logic, and filesystem hygiene.

### Refactoring: Analysis Module Splitting (Addressing Code Quality Review)

- [X] T041 [US3] **Split `code/analysis/regression.py` into four distinct modules** (see T041a-T041d). **Note**: T041a-T041d are the atomic implementation tasks; this parent task is a summary checkpoint.

### Data Integrity: Fix Flagging Logic (Addressing Data Quality Review)

- [X] T046 [US1] **Verify Flagging Logic in `code/data/validator.py`**: Ensure `missing_invariant_flags` are **only** set for Phase 2+ computed invariants (arc index, Seifert circle count, bridge number) when diagram representations are missing.
 - **Constraint**: Core tabulated invariants (crossing number, braid index) must **never** trigger `missing_invariant_flags`.
 - **Validation**: Ensure `data_quality_flags` is used for null values, format errors, and duplicates.
 - **Note**: This task verifies the logic implemented in T057.

- [X] T047 [US1] **Re-run Data Pipeline**: Re-execute the download and parsing pipeline to regenerate `data/processed/knots_cleaned.csv` with correct flagging. Verify that `missing_invariant_flags` count is near zero for core fields.

- [X] T048 [US1] **Resolve Report Contradictions**: Update `docs/reproducibility/data_quality_report.md`, `docs/reproducibility/data_quantities.md`, and `docs/reproducibility/invariant_coverage.md` to reflect consistent record counts (reconcile "476" vs "") and correct flag statuses.

- [X] T049 [US1] **Validate Real Data**: Run `code/download/knot_atlas_loader.py` and `code/data/parser.py`. Append the first 10 lines of `data/raw/knot_atlas_raw.json` and the first 5 lines of `data/processed/knots_cleaned.csv` to `docs/reproducibility/data_ingestion_evidence.md`. **Must show non-zero, non-placeholder values for crossing_number, braid_index, and hyperbolic_volume.**

- [X] T050 [US1] **Re-run Consistency Check**: Re-run the hyperbolic volume consistency check against KnotInfo and update `docs/reproducibility/hyperbolic_volume_validation.md` with actual match rate and coverage percentage.

### Filesystem Hygiene: Clean Up Artifacts (Addressing Filesystem Hygiene Review)

- [X] T051 [US4] **Consolidate Checksum Manifests**:
 - [ ] Check if `data/checksums.sha256` or `data/checksums.csv` exist.
 - [ ] If they exist, **migrate** their content to `data/checksums.json` and log the action. If they do not exist, log "Not found (expected)" and pass.
 - [ ] Ensure `data/checksums.json` is the **sole** authoritative manifest.
 - [ ] Update `docs/reproducibility/checksums.md` to remove references to deprecated files.

- [X] T052 [US4] **Consolidate Log Files**:
 - [ ] Check if `data/logs.jsonl` or `data/operation_logs.jsonl` exist.
 - [ ] If they exist, **migrate** their content to `docs/reproducibility/logs/` and log the action. If they do not exist, log "Not found (expected)" and pass.
 - [ ] Ensure all operational logs are exclusively located in `docs/reproducibility/logs/`.
 - [ ] Update `docs/reproducibility/operation_logs.md` to remove "migrated" language and confirm current clean state.

- [X] T053 [US4] **Update READMEs**:
 - [ ] Update `docs/reproducibility/README.md` to list **authoritative** documents for each category (e.g., point to `braid_index_precision_validation.md` as the final report).
 - [ ] Consolidate or remove `docs/reproducibility/README_SUMMARY.md` if it adds no value.
 - [ ] Remove or rename files with non-standard naming (e.g., `combined_invariant_intuition_narrative_story_extra.md`) to adhere to disciplined naming conventions.

- [X] T054 [US3] **Verify Multicollinearity Calculation**: Re-implement VIF calculation in `code/analysis/model_fitting.py` to ensure it operates on actual loaded data. Verify that reported VIF values reflect the expected high multicollinearity (VIF >> 5) due to the `braid_index <= crossing_number` constraint. Document the corrected VIF in `docs/reproducibility/multicollinearity_assessment.md`.

- [X] T055 [US3] **Consolidate Regression Logic**: Check if `code/analysis/regression.py` exists.
 - [ ] If it exists and logic has been migrated to `model_fitting.py` per T041, remove or deprecate `regression.py`.
 - [ ] If it does not exist, log "Not found (expected)" and pass.
 - [ ] Ensure no duplicate regression logic exists between files.

---

## Phase N+2: Data Pipeline Verification & Statistical Correctness (Critical Review Response)

**Purpose**: Directly address the critical "Fabrication/Simulation" and "Statistical Methodology" failures identified in the latest research reviews. These tasks are blocking and must be completed before any further analysis.

*Note: T056 and T057 have been moved to Phase 2 (Foundational) to ensure data is produced before Phase 3 consumption. This section now focuses on verification of the fixed pipeline.*

- [X] T056 [US1] **Execute Real Data Ingestion Verification**: (Moved to Phase 2)
- [X] T057 [US1] **Fix Validator Flagging Logic**: (Moved to Phase 2)
- [X] T058 [US3] **Correct VIF Calculation**: Update `code/analysis/model_fitting.py` to load `data/processed/knots_cleaned.csv` directly. Re-calculate VIF for crossing_number and braid_index. **Expected Result**: VIF >> 5 (high multicollinearity) due to the mathematical constraint. If VIF ~, the data loading or calculation is incorrect and must be debugged. Document the corrected VIF in `docs/reproducibility/multicollinearity_assessment.md`.
- [X] T059 [US3] **Remove Duplicate Regression Logic**: Audit `code/analysis/`. Ensure `code/analysis/regression.py` is removed or deprecated if `code/analysis/model_fitting.py` contains the logic. Verify no duplicate model fitting code exists.
- [X] T060 [US4] **Regenerate Data Quality Report**: Re-run the data quality pipeline with the fixed validator (T057). Generate an updated `docs/reproducibility/data_quality_report.md` showing `missing_invariant_flags` count near zero for core fields and consistent record counts (no "small vs large" contradiction).
- [X] T061 [US4] **Finalize Reproducibility Artifacts**: Ensure all logs are in `docs/reproducibility/logs/`, all checksums are in `data/checksums.json`, and `docs/reproducibility/README.md` correctly points to the authoritative reports (T053, T051, T052).

---

## Phase N+3: Advanced Code Quality & Type Safety (Addressing Code Quality Review)

**Purpose**: Address specific code quality issues regarding file size, modularity, and type safety identified in `research_reviewer_code_quality_research__2026-07-01__research.md`.

- [ ] T062 [US3] **Split `code/analysis/model_fitting.py`**: Refactor `code/analysis/model_fitting.py` (currently of substantial size) into three distinct modules, each under 200 lines:
  - `code/analysis/model_fitting.py`: Pure model fitting (Linear, Polynomial, Logarithmic) and metric calculation (R², AIC, BIC, MAE).
  - `code/analysis/residual_analysis.py`: Logic for identifying families deviating ≥ 2 SD.
  - `code/analysis/plotting.py`: All figure generation logic.
  - `code/analysis/model_reporting.py`: Logic for generating markdown/JSON reports.
  - **Note**: This task splits the monolithic file created in T041a.

- [ ] T063 [US3] **Consolidate Visualization Modules**: Merge `code/analysis/complexity_visualization.py`, `code/analysis/complexity_visualization_examples.py`, and `code/analysis/complexity_visualization_runner.py` into a single `code/analysis/visualization.py` with clear function separation.

- [ ] T064 [US3] **Consolidate Metrics Modules**: Merge `code/analysis/composite_metric*.py` files into a single `code/analysis/metrics.py`.

- [ ] T065 [US3] **Enforce Type Hints**: Add PEP 484 type hints to all functions in the refactored analysis modules (`model_fitting.py`, `residual_analysis.py`, `plotting.py`, `visualization.py`, `metrics.py`). Verify with `mypy --strict code/analysis/` and fix all errors.

- [ ] T066 [US3] **Create Unit Tests for Refactored Modules**: Create `tests/unit/test_model_fitting.py` and `tests/unit/test_residual_analysis.py` to cover the split logic and ensure comprehensive coverage of the refactored functions.

- [ ] T067 [US3] **Verify File Size Constraints**: Run a script to verify that all files in `code/analysis/` are under lines (or 10KB) and report any violations.

- [ ] T068 [US3] **Update Documentation for Refactoring**: Update `docs/reproducibility/methodology.md` and `docs/reproducibility/README.md` to reflect the new module structure and entry points.