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
- [X] T002 Initialize Python 3.11 project [UNRESOLVED-CLAIM: c_0f6b5d4b — status=not_enough_info] with dependencies: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `requests`, `pyyaml`, `seaborn`, `pytest`
- [X] T003 [P] Configure linting and formatting tools (black, flake8, mypy)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement exponential back-off retry logic in `code/download/knot_atlas_loader.py` (FR-008)
- [X] T005 [P] Setup CI/CD pipeline with linting, formatting, and basic build steps.
- [X] T006 [P] Setup initial testing framework with unit tests.
- [X] T007 Create `code/data/tie_breaking_validator.py` script that returns exit code 0 on success and generate `docs/reproducibility/tie_breaking_rules.md` (SC-007)
- [ ] T008 [P] Setup database schema and migrations framework (if applicable) <!-- ATOMIZE: requested -->
- [ ] T009 [P] Implement authentication/authorization framework (if applicable)
- [ ] T010 [P] Setup API routing and middleware structure (if applicable)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Parse Knot Data from Knot Atlas (Priority: P1) 🎯 MVP

**Goal**: Download knot data from Knot Atlas including crossing numbers, braid indices, hyperbolic volume, and alternating/non-alternating classification for all prime knots with crossing number ≤ 13.

- [X] T011 [US1] Create `code/download/knot_atlas_loader.py` to download data using the retry logic from T004
- [X] T012 [US1] Implement parser in `code/data/parser.py` to clean and normalize data. **CRITICAL**: Ensure `missing_invariant_flags` are ONLY set for Phase 2+ computed invariants (arc index, Seifert circle count, bridge number) when diagram representations are missing [UNRESOLVED-CLAIM: c_fc9c3d2e — status=not_enough_info]. Core tabulated invariants (crossing number, braid index) must NEVER trigger `missing_invariant_flags` [UNRESOLVED-CLAIM: c_27e2c824 — status=not_enough_info] (FR-009, SC-009).
- [X] T013 [US1] Implement caching in downloader (T011)
- [X] T014 [US1] Save raw data to `data/raw/knot_atlas_raw.json` and cleaned to `data/processed/knots_cleaned.csv`
- [X] T015 [US1] Filter dataset for hyperbolic knots [UNRESOLVED-CLAIM: c_c77efa60 — status=not_enough_info], logging exclusions, and **generate `docs/reproducibility/excluded_knots.md` documenting excluded records** (FR-012, SC-012)
- [X] T016 [US1] **Validate core tabulated invariants (crossing number, braid index) against KnotInfo references** with 1e-6 tolerance. Generate `docs/reproducibility/core_precision_consistency.md` (FR-013, SC-014, SC-015). **Do NOT use `tie_breaking_validator.py` for this task.**
- [X] T017 [US1] **Validate hyperbolic volume consistency against KnotInfo references** with 1e-6 tolerance. Generate `docs/reproducibility/hyperbolic_volume_validation.md`. **This is a distinct validation from T016 and requires its own logic.** (FR-013, SC-014)

### Tests for User Story 1 (OPTIONAL)

- [ ] T018 [P] [US1] Contract test for data schema in `tests/contract/test_schemas.py`
- [ ] T019 [P] [US1] Integration test for download pipeline in `tests/integration/test_pipeline.py`

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Establish Measurement Precision for Core Invariants (Priority: P2)

**Goal**: Validate measurement accuracy of core invariants across different knot classes.

- [X] T020 [US2] Implement precision validation module in `code/analysis/precision.py` to **validate tabulated core invariants (crossing number, braid index) against KnotInfo references** (1e-6 tolerance). **This task validates ground truth data, not algorithmic computation** (FR-003, SC-008).
- [X] T021 [US2] Generate scatter plots in `data/plots/` and generate `docs/reproducibility/plot_validation_report.md` verifying metadata and tags (SC-016)
- [X] T022 [US2] Create automated validation script for plot metadata and generate `docs/reproducibility/plot_validation_report.md` (SC-016)

### Tests for User Story 2 (OPTIONAL)

- [ ] T023 [P] [US2] Contract test for precision validation module in `tests/contract/test_precision.py`
- [ ] T024 [P] [US2] Integration test for data quality check in `tests/integration/test_data_quality.py`

**Checkpoint**: User Story 2 should be fully functional and testable independently.

---

## Phase 5: User Story 3 - Fit Regression Models to Assess Joint Predictive Relationships (Priority: P3)

**Goal**: Fit regression models to assess the relationship between hyperbolic volume, crossing number, and braid index.

- [X] T025 [US3] **Create `code/analysis/model_fitting.py` and `code/analysis/residual_analysis.py`** to implement model fitting and residual analysis logic. This task establishes the file structure required for downstream refactoring.
- [X] T026 [US3] Implement regression model fitting in `code/analysis/model_fitting.py` for **Linear, Polynomial, and Logarithmic models only**. **Explicitly exclude Ridge regression** per FR-005 census data constraints.
- [X] T027 [US3] **Implement variance partitioning metrics and descriptive interpretation** acknowledging braid_index <= crossing_number constraint. **Document that coefficients are for descriptive variance partitioning only, not independent predictive value** (FR-005).
- [X] T028 [US3] Perform residual analysis to identify outlier knot families and generate `docs/reproducibility/residual_analysis.md` (SC-011)

### Tests for User Story 3 (OPTIONAL)

- [ ] T029 [P] [US3] Contract test for regression model in `tests/contract/test_regression.py`
- [ ] T030 [P] [US3] Integration test for residual analysis in `tests/integration/test_residual_analysis.py`

**Checkpoint**: User Story 3 should be fully functional and testable independently.

---

## Phase 6: User Story 4 - Edge Case Handling, Data Quality, and Reproducibility Documentation (Priority: P4)

**Goal**: Implement robust edge case handling and comprehensive reproducibility documentation.

- [X] T031 [US4] Implement data validation and error handling mechanisms
- [X] T032 [US4] **Generate complete reproducibility documentation** including: `docs/reproducibility/data_quality_report.md`, `validation_scope.md`, `excluded_knots.md`, `random_seeds.md`, `hyperbolic_volume_validation.md`, `core_precision_consistency.md`, `residual_analysis.md`, `tie_breaking_rules.md`, `plot_validation_report.md`, and `logs/` (FR-007, SC-003)
- [X] T033 [US4] Generate `docs/reproducibility/checksums.md` with SHA-256 checksums for all data files **AND update `state/...yaml` artifact map with new hashes** (FR-007, SC-003, Constitution Principle V)

### Tests for User Story 4 (OPTIONAL)

- [ ] T034 [P] [US4] Unit tests for edge case handling scenarios in `tests/unit/test_edge_cases.py`
- [ ] T035 [P] [US4] Integration test for reproducibility documentation generation in `tests/integration/test_reproducibility.py`

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

- [ ] T041 [US3] **Split `code/analysis/model_fitting.py`** into three distinct modules, each under 200 lines:
 - [ ] Create `code/analysis/model_fitting.py`: Pure model fitting (Linear, Polynomial, Logarithmic) and metric calculation (R², AIC, BIC, MAE).
 - [ ] Create `code/analysis/residual_analysis.py`: Logic for identifying families deviating ≥ 2 SD [UNRESOLVED-CLAIM: c_6f098e8c — status=not_enough_info] (SC-011).
 - [ ] Create `code/analysis/plotting.py`: All figure generation logic (FR-004, SC-016).
 - [ ] Create `code/analysis/model_reporting.py`: Logic for generating markdown/JSON reports for these models.

- [ ] T042 [US3] **Consolidate Visualization Modules**: Merge `code/analysis/complexity_visualization.py`, `code/analysis/complexity_visualization_examples.py`, and `code/analysis/complexity_visualization_runner.py` into a single `code/analysis/visualization.py` with clear function separation.

- [ ] T043 [US3] **Consolidate Metrics Modules**: Merge `code/analysis/composite_metric*.py` files into a single `code/analysis/metrics.py`.

- [ ] T044 [US3] **Add Strict Type Hints**: Add PEP 484 type hints to all functions in the refactored analysis modules (`model_fitting.py`, `residual_analysis.py`, `plotting.py`, `visualization.py`, `metrics.py`) and verify correctness with `mypy --strict`.

- [ ] T045 [US3] **Create Unit Tests for Refactored Logic**:
 - [ ] Create `tests/unit/test_model_fitting.py` to cover the split fitting logic.
 - [ ] Create `tests/unit/test_residual_analysis.py` to cover the deviation logic.

### Data Integrity: Fix Flagging Logic (Addressing Data Quality Review)

- [ ] T046 [US1] **Verify Flagging Logic in `code/data/validator.py`**: Ensure `missing_invariant_flags` are **only** set for Phase 2+ computed invariants (arc index, Seifert circle count, bridge number) when diagram representations are missing.
 - **Constraint**: Core tabulated invariants (crossing number, braid index) must **never** trigger `missing_invariant_flags`.
 - **Validation**: Ensure `data_quality_flags` are used for null values, format errors, and duplicates.

- [ ] T047 [US1] **Re-run Data Pipeline**: Re-execute the download and parsing pipeline to regenerate `data/processed/knots_cleaned.csv` with correct flagging. Verify that `missing_invariant_flags` count is near zero for core fields.

- [ ] T048 [US1] **Resolve Report Contradictions**: Update `docs/reproducibility/data_quality_report.md`, `docs/reproducibility/data_quantities.md`, and `docs/reproducibility/invariant_coverage.md` to reflect consistent record counts (reconcile "476" vs "9,988") and correct flag statuses.

- [ ] T049 [US1] **Validate Real Data**: Generate evidence (sample of raw JSON from `data/raw/knot_atlas_raw.json` and corresponding CSV rows) to prove data is real and not fabricated/simulated.

- [ ] T050 [US1] **Re-run Consistency Check**: Re-run the hyperbolic volume consistency check against KnotInfo and update `docs/reproducibility/hyperbolic_volume_validation.md` with actual match rate and coverage percentage.

### Filesystem Hygiene: Clean Up Artifacts (Addressing Filesystem Hygiene Review)

- [ ] T051 [US4] **Consolidate Checksum Manifests**:
 - [ ] Delete `data/checksums.sha256` and `data/checksums.csv` **if they exist**.
 - [ ] Ensure `data/checksums.json` is the **sole** authoritative manifest.
 - [ ] Update `docs/reproducibility/checksums.md` to remove references to deprecated files.

- [ ] T052 [US4] **Consolidate Log Files**:
 - [ ] Delete `data/logs.jsonl` and `data/operation_logs.jsonl` **if they exist**.
 - [ ] Ensure all operational logs are exclusively located in `docs/reproducibility/logs/`.
 - [ ] Update `docs/reproducibility/operation_logs.md` to remove "migrated" language and confirm current clean state.

- [ ] T053 [US4] **Update READMEs**:
 - [ ] Update `docs/reproducibility/README.md` to list **authoritative** documents for each category (e.g., point to `braid_index_precision_validation.md` as the final report).
 - [ ] Consolidate or remove `docs/reproducibility/README_SUMMARY.md` if it adds no value.
 - [ ] Remove or rename files with non-standard naming (e.g., `combined_invariant_intuition_narrative_story_extra.md`) to adhere to disciplined naming conventions.

- [ ] T054 [US3] **Verify Multicollinearity Calculation**: Re-implement VIF calculation in `code/analysis/model_fitting.py` to ensure it operates on actual loaded data. Verify that reported VIF values reflect the expected high multicollinearity (VIF >> 5) due to the `braid_index <= crossing_number` constraint, or explicitly document the data source failure if not.

- [ ] T055 [US3] **Consolidate Regression Logic**: Remove or deprecate `code/analysis/regression.py` if its logic has been migrated to `model_fitting.py` per T041. Ensure no duplicate regression logic exists between files.