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

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Setup (Shared Infrastructure & Scope Definition)

- [X] T001 Create project structure per implementation plan. **Deliverable**: Create directories: `code/download`, `code/data`, `code/analysis`, `code/reproducibility`, `code/utils`, `data/raw`, `data/processed`, `data/plots`, `docs/reproducibility`, `docs/analysis`, `tests/unit`, `tests/integration`, `tests/contract`. **Verification**: Run `ls -R` and verify against `plan.md` Project Structure section.
- [X] T002 Initialize Python 3.11 project with dependencies. **Deliverable**: Create `code/requirements.txt` containing: `pandas`, `numpy`, `statsmodels`, `matplotlib`, `requests`, `pyyaml`, `seaborn`, `pytest`, `scikit-learn`, `database-knotinfo`. **Verification**: `pip install -r code/requirements.txt` succeeds and `database-knotinfo` is installed.
- [X] T003 [P] Configure linting and formatting tools. **Deliverable**: Create `code/.black`, `code/.flake8`, and `code/mypy.ini` (or `pyproject.toml` sections) with configurations referencing `specs/010-quantifying-the-complexity-of-knot-diagr/templates/lint-config.yaml`. **Verification**: `black --check.` and `flake8.` pass.
- [X] T005 [P] Setup CI/CD pipeline. **Deliverable**: Create `.github/workflows/ci.yml` containing jobs for `linting`, `formatting check`, and `pytest` execution, triggered on push to main and PRs. **Verification**: CI runs on a commit.
- [X] T006 [P] Setup initial testing framework. **Deliverable**: Create `tests/conftest.py` with fixtures for data paths and `tests/__init__.py`. **Verification**: Run `pytest --collect-only` and verify it returns 0 tests without error.
- [X] T010 **Generate Validation Scope Document**: Create `docs/reproducibility/validation_scope.md` containing the ≤10 vs ≤13 crossing distinction, justification, and counts table (SC-012). **Verification**: File exists and contains both tables.

---

## Phase 1: Foundational (Blocking Prerequisites)

- [X] T004 [P] Implement `database-knotinfo` client wrapper in `code/download/knot_info_loader.py` (FR-008). **Verification**: Script runs without error and fetches sample data.
- [X] T007 Create `code/data/tie_breaking_validator.py` script that returns exit code 0 on success and generate `docs/reproducibility/tie_breaking_rules.md` (SC-007). **Verification**: Script exits 0 and file exists.
- [X] T041a **Model Fitting – Linear/Polynomial/Logarithmic** (US3) – Implement in `code/analysis/model_fitting.py`. **Verification**: Unit test `tests/unit/test_linear_model.py` runs on a synthetic dataset and asserts R², AIC, BIC, MAE are computed. (Note: Ridge regression is excluded per FR-005).
- [X] T041b **Residual Analysis Module** (US3) – Implement in `code/analysis/residual_analysis.py`. **Verification**: Unit test `tests/unit/test_residual_analysis.py` confirms detection of families deviating ≥ 2 SD on synthetic data.
- [X] T041c **Plotting Module** (US3) – Implement in `code/analysis/plotting.py`. **Verification**: Script `code/analysis/plot_validation.py` generates all required PNGs and asserts each image is 1200×900 px (using `backend='Agg'` and `dpi=100`) and contains required metadata.
- [X] T041d **Model Reporting Module** (US3) – Implement in `code/analysis/model_reporting.py`. **Verification**: Generate JSON report and validate against `contracts/regression_output.schema.yaml` using `jsonschema`.

---

## Phase 1.5: Core Invariant Validation & Consistency Checks (New: Addresses SC-015, FR-014, FR-013, SC-014)

- [X] T016 **Core Tabulated Invariant Precision** – Validate crossing number and braid index against KnotInfo references, tolerance ≤ 1e‑6. Generate `docs/reproducibility/core_precision_consistency.md`. **Dependency**: Requires T010 (Validation Scope) to be defined. **Verification**: Match rate ≥ 99%.
- [X] T017 **Hyperbolic Volume Consistency** – Validate hyperbolic volume against KnotInfo where available, generate `docs/reproducibility/hyperbolic_volume_validation.md`. **Verification**: Match rate ≥ 90%.
- [X] T018 **Contract Test for Data Schema** – `tests/contract/test_schemas.py` validates `contracts/knot_record.schema.yaml` against `data/processed/knots_cleaned.csv`. **Verification**: Test passes.

---

## Phase 2: User Story 1 – Download and Parse Knot Data (Priority: P1)

- [X] T011 **Download & Parse Primary Data**: Extend `code/download/knot_info_loader.py` to fetch full census data via `database-knotinfo` and parse into a DataFrame, writing `data/raw/knot_atlas_raw.json`. **Dependency**: Requires T010 (Validation Scope) to define download boundaries (≤10 vs ≤13). **Verification**: File size > 128KB (2408.02911, https://arxiv.org/abs/2408.02911) and contains expected header fields. [UNRESOLVED-CLAIM: c_9789b9e2 — status=not_enough_info]
- [X] T012 **Data Parser** (`code/data/parser.py`) – Clean and normalize parsed data, flag only tabulated invariants. **Verification**: Unit test `tests/unit/test_parser.py` ensures no `missing_invariant_flags` for crossing number or braid index.
- [X] T012a **Data Quality Report** (`code/data/quality_report.py`) – Compute null percentages, duplicate counts, format pass rates. Generate `docs/reproducibility/data_quality_report.md`. **Verification**: Report shows null % ≤ 5 % and duplicate count = 0 [UNRESOLVED-CLAIM: c_93f3cdde — status=not_enough_info].
- [X] T012b **Tie‑Breaking Validation** – Execute `code/data/tie_breaking_validator.py` on processed data. **Verification**: Exit code 0 and `docs/reproducibility/tie_breaking_rules.md` lists applied rules.
- [X] T013 **Downloader Caching** – Implement local cache in `code/download/knot_info_loader.py`. **Verification**: Subsequent runs read from cache (log entry).
- [X] T015 **Hyperbolic Volume Filter** – Filter `knots_cleaned.csv` for `hyperbolic_volume > 0`, log exclusions, generate `docs/reproducibility/excluded_knots.md`. **Verification**: {{claim:c_17ad1e09}} (Wikidata Q19358049, https://www.wikidata.org/wiki/Q19358049) and documented.
- [X] T014 **Persist Raw & Cleaned Data** – Save raw JSON to `data/raw/knot_atlas_raw.json` and filtered CSV to `data/processed/knots_filtered.csv`. **Verification**: Files exist with correct sizes.
- [X] T028 **Residual Analysis Execution** – Run `code/analysis/residual_analysis.py` on filtered dataset, generate `docs/reproducibility/residual_analysis.md`. **Verification**: File contains a section "Families deviating ≥ 2 SD". (Moved from Phase 2 to Phase 4 in execution order, but logic implemented here).
- [X] T056 **Real Data Ingestion Verification** – Execute `code/scripts/ingest_evidence.py` to validate the full census (the complete set of knots) for nulls and format errors, output `docs/reproducibility/data_ingestion_evidence.md`. **Verification**: Evidence file contains non-zero values for crossing number, braid index, hyperbolic volume.
- [X] T057 **Validator Refactor & FR‑009 Compliance** – Refactor `code/data/validator.py` to set `missing_invariant_flags` only for non‑core invariants, reference FR-009. Add unit test `tests/unit/test_validator_flags.py`. **Verification**: Test asserts core invariants never produce missing flags.
- [X] T076 **Regenerate Data Quality Report** – Re‑run `code/data/quality_report.py` after validator fix. **Verification**: Updated `data_quality_report.md` shows null % ≤ 0.05 (Wikipedia: Null hypothesis, https://en.wikipedia.org/wiki/Null_hypothesis) % and missing flag counts near zero.
- [X] T093 **Dataset Completeness Validation (SC‑001)** – Create `code/scripts/dataset_completeness.py` that counts records per crossing number, checks null % ≤ 5 %, duplicate = 0, and cross-checks against hardcoded {{claim:c_9b977137}} (Wikipedia: Knot theory, https://en.wikipedia.org/wiki/Knot_theory) enumeration values for crossing numbers ≤ 13. Output `docs/reproducibility/dataset_completeness_report.md`. **Verification**: Report passes all checks.
- [X] T094 **Core‑Invariant Coverage Report (SC‑008)** – Generate `docs/reproducibility/invariant_coverage.md` summarising available vs. missing counts for crossing number and braid index. **Verification**: {{claim:c_46405e3e}} (Wikipedia: Universal health care by country, https://en.wikipedia.org/wiki/Universal_health_care_by_country)
- [X] T095 **Ambiguous Alternating Classification Handling (SC‑006, FR-010)** – Implement logic in `code/data/parser.py` to exclude or mark records with ambiguous `alternating` field, generate `docs/reproducibility/alternating_handling_report.md`. **Verification**: Report lists number of excluded/marked records and confirms compliance.
- [X] T019 **Integration Test for Download Pipeline** – `tests/integration/test_pipeline.py` runs full download‑parse‑filter pipeline and asserts final CSV row count matches expected hyperbolic subset. **Verification**: Test passes.
- [X] T035 **Generate Random Seeds Document** – Create `docs/reproducibility/random_seeds.md` containing all pinned random seed values used in the codebase (FR-007, SC-003). **Verification**: File exists and lists all seeds used.

---

## Phase 2.5: Computed Invariant Verification (Addresses Constitution Principle VI)

- [X] T080 **Compute Additional Invariants** – Implement `code/data/computed_invariants.py` for arc index, Seifert circle count, bridge number where diagram data exists. **Verification**: Unit test validates calculations against known examples.
- [ ] T081 **Verify Computed Invariants** – Implement `code/data/verify_invariants.py` to compare computed values against definitions and KnotInfo where available. Generate `docs/reproducibility/computed_invariant_verification.md`. **Verification**: Report lists any discrepancies.
- [ ] T082 **Update Data Schema** – Extend `contracts/knot_record.schema.yaml` with fields for computed invariants, modify `code/data/parser.py` to accept them. **Verification**: Schema validation test passes.

---

## Phase 3: User Story 2 – Core Invariant Precision Checks (Priority: P2)

- [X] T084 **Validator Core‑Invariant Unit Test** – `tests/unit/test_core_invariant_flags.py` asserts `missing_invariant_flags` empty for core invariants across the full dataset. **Verification**: Test passes.

---

## Phase 4: User Story 3 – Regression & Modeling (Priority: P3)

- [X] T025 **Deprecate Old Regression Script** – Ensure `code/analysis/regression.py` is removed or empty. **Verification**: File absent or contains only a deprecation notice.
- [X] T058 **VIF Calculation & Reporting** – Create `code/scripts/verify_vif.py` to compute VIF for crossing number and braid index, document VIF value and acknowledge multicollinearity, write `docs/reproducibility/multicollinearity_assessment.md`. **Verification**: Report shows VIF value and acknowledges high multicollinearity (no threshold assertion).
- [X] T026b **Orthogonalization Logic** – Implement `code/analysis/orthogonalization.py` to orthogonalize braid index w.r.t. crossing number. **Verification**: Unit test confirms orthogonalized predictor has zero correlation with crossing number.
- [X] T026a **Variance Partitioning Metrics** – Compute variance partitioning, document in `docs/reproducibility/variance_partitioning.md`. **Verification**: Report includes R² split and acknowledges braid ≤ crossing constraint.
- [X] T026c **Descriptive Comparison Metrics** – Implement `code/analysis/comparison_metrics.py` for mean diff, variance ratio, Cohen’s d between alternating vs. non‑alternating groups. Generate `docs/reproducibility/group_comparison_metrics.md`. **Verification**: Metrics computed and documented.
- [X] T029 **Regression Model Fitting** – Use `code/analysis/model_fitting.py` (with orthogonalization) to fit Linear, Polynomial, and Logarithmic models. Generate `docs/reproducibility/regression_results.md`. **Verification**: Report contains R², AIC, BIC, MAE for each model.
- [X] T030 **Contract Test for Regression** – `tests/contract/test_regression.py` validates output schema against `contracts/regression_output.schema.yaml`. **Verification**: Test passes.
- [X] T031 **Integration Test for Residual Analysis** – `tests/integration/test_residual_analysis.py` runs residual module on a subset and checks output file exists. **Verification**: Test passes.

---

## Phase 5: User Story 4 – Edge Cases, Data Quality & Reproducibility (Priority: P4)

- [X] T032 **Data Validation & Error Handling** – Implement comprehensive checks in `code/data/validator.py`. **Verification**: Unit tests cover error paths.
- [X] T033 **Generate Full Reproducibility Documentation** – Assemble all docs (`data_quality_report.md`, `excluded_knots.md`, `random_seeds.md`, `hyperbolic_volume_validation.md`, `core_precision_consistency.md`, `residual_analysis.md`, `tie_breaking_rules.md`, `plot_validation_report.md`, etc.). **Verification**: Directory `docs/reproducibility/` contains all required files.
- [X] T034 **Checksums Manifest & State Update** – Generate `docs/reproducibility/checksums.md` with SHA‑256 for all data files and update `state/...yaml` artifact map. **Verification**: Manifest matches file hashes; state file updated.
- [X] T051 **Consolidate Checksum Manifests** – Migrate old checksum files to `data/checksums.json` and update `docs/reproducibility/checksums.md`. **Verification**: Only `checksums.json` referenced.
- [X] T052 **Consolidate Log Files** – Move logs to `docs/reproducibility/logs/`, update `docs/reproducibility/operation_logs.md`. **Verification**: Log directory contains expected files.
- [X] T053 **Update Reproducibility README** – Revise `docs/reproducibility/README.md` with TOC linking authoritative documents; remove `README_SUMMARY.md`. **Verification**: README renders correctly.
- [X] T054 **Verify Multicollinearity Calculation** – Ensure VIF calculation in `model_fitting.py` uses actual data and matches `docs/reproducibility/multicollinearity_assessment.md`. **Verification**: Consistency check passes.
- [X] T055 **Consolidate Regression Logic** – Confirm `code/analysis/regression.py` is absent or deprecated. **Verification**: Test confirms no duplicate logic.
- [X] T059 **Remove Duplicate Regression Logic** – Ensure no active regression code remains in deprecated files. **Verification**: Search confirms absence; unit test `tests/unit/test_no_duplicate_regression.py` passes.
- [X] T061 **Finalize Reproducibility Artifacts** – Ensure all logs, checksums, README are in place. **Verification**: Audit script confirms completeness.

---

## Phase 6: Final Verification & Gate Clearance

- [X] T069 **Final Data Integrity Audit** – `code/scripts/final_data_audit.py` runs validator, checks flag counts, outputs `docs/reproducibility/final_data_integrity_audit.md`. **Verification**: Audit passes.
- [X] T070 **Final Statistical Correctness Audit** – Re‑run `model_fitting.py` and `residual_analysis.py`, produce `docs/reproducibility/final_statistical_audit.md`. **Verification**: Audit confirms VIF value documented, residual families identified, metrics computed on real data.
- [X] T071 **Final Filesystem Hygiene Audit** – `code/scripts/final_hygiene_audit.py` verifies file existence/non‑existence, outputs `docs/reproducibility/final_hygiene_audit.md`. **Verification**: Audit passes.
- [X] T072 **Final Hyperbolic Volume Consistency Check** – Re‑run volume validation, ensure match rate ≥ 90%, update `hyperbolic_volume_validation.md`. **Verification**: Documented rate meets threshold.
- [X] T073 **Final Real Data Evidence** – Append first lines of `data/raw/knot_atlas_raw.json` and sample rows of `data/processed/knots_filtered.csv` to `docs/reproducibility/data_ingestion_evidence.md`. **Verification**: File contains excerpts.
- [X] T074 **Generate Final Reproducibility Package** – Compile all reports into `docs/reproducibility/FINAL_REPORT_PACKAGE.md` with links and summary. **Verification**: Package generated and links resolve.

---

## Phase 7: Code Quality & Architecture Refactoring (Addressing Research Reviewer Code Quality)

**Goal**: Resolve code quality issues regarding file size, modularity, and type safety identified in `research_reviewer_code_quality_research__2026-07-01__research.md`.

- [X] T101 **Split `code/analysis/model_fitting.py` into modular components** – Refactor the [deferred]-byte `model_fitting.py` into:
 - `code/analysis/model_fitting.py`: Pure model fitting (Linear, Polynomial, Logarithmic) and metric calculation (R², AIC, BIC, MAE).
 - `code/analysis/residual_analysis.py`: Logic for identifying families deviating ≥ 2 SD (T028).
 - `code/analysis/plotting.py`: All figure generation logic (T041c).
 - `code/analysis/model_reporting.py`: Logic for generating the markdown/JSON reports for these models.
 **Constraint**: Each resulting file must be concise. **Verification**: `wc -l` on each file < 200.

- [X] T102 **[P] Consolidate Visualization Modules** – Merge `code/analysis/complexity_visualization.py`, `code/analysis/complexity_visualization_examples.py`, and `code/analysis/complexity_visualization_runner.py` into a single cohesive module `code/analysis/visualization.py` with clear function separation. **Verification**: Old files deleted; new file imports successfully.

- [X] T103 **[P] Consolidate Metrics Modules** – Merge `code/analysis/composite_metric*.py` files into a single `code/analysis/metrics.py` to eliminate fragmentation. **Verification**: Old files deleted; new file contains all metric logic.

- [ ] T104 **[P] Add PEP 484 Type Hints** – Add strict type hints to all public functions in the refactored analysis modules (`model_fitting.py`, `residual_analysis.py`, `plotting.py`, `visualization.py`, `metrics.py`). **Verification**: `mypy --strict code/analysis/` passes with zero errors.

- [ ] T105 **Create Unit Tests for Refactored Logic** – Create `tests/unit/test_model_fitting.py` and `tests/unit/test_residual_analysis.py` to cover the split logic from T101. **Verification**: Both test files exist and pass.

- [ ] T106 **Verify Data Loading in Model Fitting** – Explicitly verify that `code/analysis/model_fitting.py` loads `data/processed/knots_filtered.csv` and not synthetic data. **Verification**: Unit test asserts that input data contains non-zero real values for hyperbolic volume and crossing number.

- [ ] T107 **Fix VIF Calculation Logic** – Re-implement VIF calculation in `code/analysis/model_fitting.py` to ensure it operates on the actual loaded data and reflects the expected high multicollinearity. Document VIF value in `docs/reproducibility/multicollinearity_assessment.md`. **Verification**: `docs/reproducibility/multicollinearity_assessment.md` updated with documented VIF value.

- [ ] T108 **Remove Deprecated `regression.py`** – Ensure `code/analysis/regression.py` is removed or contains only a deprecation notice, consolidating all logic into `model_fitting.py` and `metrics.py`. **Verification**: File absent or empty; no duplicate logic found.

---

## Phase 8: Data Integrity & Report Consistency (Addressing Research Reviewer Data Quality)

**Goal**: Resolve data integrity contradictions and fabrication risks identified in `research_reviewer_data_quality_research__2026-07-01__research.md`.

- [ ] T109 **Investigate and Fix Data Ingestion Pipeline** – Re-run `code/download/knot_info_loader.py` and `code/data/parser.py` to ensure `data/processed/knots_filtered.csv` contains actual values for `crossing_number`, `braid_index`, and `hyperbolic_volume`. **Verification**: {{claim:c_16dc2f31}}

- [ ] T110 **Resolve Report Contradictions** – Update `docs/reproducibility/data_quality_report.md`, `docs/reproducibility/data_quantities.md`, and `docs/reproducibility/invariant_coverage.md` to reflect consistent record counts and flag statuses (near-zero `missing_invariant_flags` for core invariants). **Verification**: Reports are internally consistent and match actual file counts.

- [ ] T111 **Validate Real Data vs. Fabrication** – Generate `docs/reproducibility/data_ingestion_evidence.md` containing a sample of raw JSON from `data/raw/knot_atlas_raw.json` and corresponding parsed CSV rows to prove data authenticity. **Verification**: Evidence file contains real data excerpts, not synthetic placeholders.

- [ ] T112 **Re-run Consistency Check** – Once real data is confirmed, re-run the hyperbolic volume consistency check against KnotInfo (`code/analysis/hyperbolic_volume_validation.py`) and update `docs/reproducibility/hyperbolic_volume_validation.md` with the actual match rate and coverage percentage. **Verification**: Report shows ≥ 90% match rate on real data.

---

## Phase 9: Filesystem Hygiene & Documentation Accuracy (Addressing Research Reviewer Filesystem Hygiene)

**Goal**: Resolve redundant artifacts and documentation inconsistencies identified in `research_reviewer_filesystem_hygiene__2026-07-01__research.md`.

- [ ] T113 **Delete Redundant Checksum Manifests** – Delete `data/checksums.sha256` and `data/checksums.csv`. Ensure `data/checksums.json` is the sole manifest. Update `docs/reproducibility/checksums.md` to remove references to deprecated files. **Verification**: Only `data/checksums.json` exists in `data/`.

- [ ] T114 **Consolidate Log Files** – Delete `data/logs.jsonl` and `data/operation_logs.jsonl`. Ensure all operational logs are exclusively located in `docs/reproducibility/logs/`. Update `docs/reproducibility/operation_logs.md` to remove "migrated" language. **Verification**: Logs only exist in `docs/reproducibility/logs/`.

- [ ] T115 **Update Reproducibility README** – Revise `docs/reproducibility/README.md` to list the *authoritative* documents for each category (e.g., "For braid index precision, see `braid_index_precision_validation.md`") and explicitly note that other files are drafts. Remove `README_SUMMARY.md`. **Verification**: README accurately reflects the directory structure and authoritative sources.

- [ ] T116 **Consolidate Naming Conventions** – Identify and remove/consolidate redundant files (e.g., `combined_invariant_intuition_narrative_story_extra.md`, `braid_index_precision_standards_addendum.md`) into their authoritative counterparts. **Verification**: No duplicate or "extra" narrative files remain in `docs/reproducibility/`.

---

## Phase 10: Deferred Scope (Phase 2+ Only)

**Note**: These tasks are explicitly excluded from Phase 1 implementation per FR-003 and SC-005. They are reserved for exploratory extension after primary results are established.

- [ ] T080 **Compute Additional Invariants** – Implement `code/data/computed_invariants.py` for arc index, Seifert circle count, bridge number where diagram data exists. **Verification**: Unit test validates calculations against known examples.
- [ ] T081 **Verify Computed Invariants** – Implement `code/data/verify_invariants.py` to compare computed values against definitions and KnotInfo where available. Generate `docs/reproducibility/computed_invariant_verification.md`. **Verification**: Report lists any discrepancies.
- [ ] T082 **Update Data Schema** – Extend `contracts/knot_record.schema.yaml` with fields for computed invariants, modify `code/data/parser.py` to accept them. **Verification**: Schema validation test passes.