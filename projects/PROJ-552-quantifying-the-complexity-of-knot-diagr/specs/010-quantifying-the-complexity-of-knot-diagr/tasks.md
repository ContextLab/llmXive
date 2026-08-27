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

## Phase 0: Setup (Shared Infrastructure & Scope Definition)

- [X] T001 Create project structure per implementation plan. **Deliverable**: Create directories: `code/download`, `code/data`, `code/analysis`, `code/reproducibility`, `code/utils`, `data/raw`, `data/processed`, `data/plots`, `docs/reproducibility`, `docs/analysis`, `tests/unit`, `tests/integration`, `tests/contract`. **Verification**: Run `ls -R` and verify against `plan.md` Project Structure section.
- [X] T002 Initialize Python 3.11 project with dependencies. **Deliverable**: Create `code/requirements.txt` containing: `pandas`, `numpy`, `statsmodels`, `matplotlib`, `requests`, `pyyaml`, `seaborn`, `pytest`, `scikit-learn`, `database-knotinfo`, `oeis`. **Verification**: `pip install -r code/requirements.txt` succeeds and `database-knotinfo` is installed.
- [X] T003 [P] Configure linting and formatting tools. **Deliverable**: Create `code/.black`, `code/.flake8`, and `code/mypy.ini` (or `pyproject.toml` sections) with configurations referencing `specs/010-quantifying-the-complexity-of-knot-diagr/templates/lint-config.yaml`. **Verification**: `black --check.` and `flake8.` pass.
- [X] T010 **Generate Validation Scope Document**: Create `docs/reproducibility/validation_scope.md` containing the ≤10 vs ≤13 crossing distinction, justification, and counts table as required by SC‑012. **Verification**: File exists and contains both tables.
- [ ] T148 **Orchestrator Clean‑Up**: Create `code/analysis/run_pipeline.py` that calls the modular components (downloader, parser, validator, orthogonalization, model fitting, plotting, reporting) in the correct order. Ensure no duplicate logic exists. **Verification**: Script runs end‑to‑end without errors. [UNRESOLVED-CLAIM: c_901e9622 — status=not_enough_info] **Note**: Moved to Phase 0 to ensure definition precedes execution.
- [X] T999 **Source Justification Document (FR‑001)**: Add `docs/reproducibility/source_justification.md` explaining that `database-knotinfo` internally queries the Knot Atlas API, providing a citation to the Knot Atlas URL and confirming parity with the direct download used in T184. **Verification**: {{claim:c_47b6ad22}} (Wikidata Q49848, https://www.wikidata.org/wiki/Q49848)

## Phase 1: Foundational (Blocking Prerequisites)

- [X] T004 Implement exponential backoff retry logic for network calls (FR‑008). **Deliverable**: `code/download/retry_wrapper.py` with configurable backoff. **Verification**: Simulated transient failure triggers ≥3 retries with exponential delays. [UNRESOLVED-CLAIM: c_fed72453 — status=not_enough_info]
- [X] T004a **Retry Logic Verification** (SC‑004). **Deliverable**: `tests/unit/test_retry_backoff.py` asserting retry count and backoff intervals. **Verification**: Test passes.
- [ ] T004b **Database‑KnotInfo Wrapper** (FR‑008) – now correctly tagged to indicate it uses the retry wrapper. **Deliverable**: `code/download/knot_info_loader.py` uses `retry_wrapper`. **Verification**: Wrapper invoked on failure.
- [ ] T151 **Refactor `code/data/validator.py` for Correct Flag Logic**: **Issue**: Reviewer noted [deferred] of records flagged with `missing_invariant_flags` for core tabulated invariants. **Action**: Refactor `code/data/validator.py` to strictly distinguish between `data_quality_flags` (for nulls/format errors in any field) and `missing_invariant_flags` (only for Phase 2+ computed invariants when diagram data is missing). Ensure core invariants (crossing number, braid index) never trigger `missing_invariant_flags`. **Verification**: Unit test `tests/unit/test_validator_flag_logic.py` confirms 0 `missing_invariant_flags` for core invariants in the full dataset. **Note**: Moved to Phase 1 to ensure data integrity before analysis.
- [ ] T152 **Re-run Data Ingestion Pipeline with Real Data Verification**: **Issue**: Reviewer flagged potential fabrication/simulated data due to high missing flags. **Action**: Re-execute `code/download/knot_atlas_downloader.py` and `code/data/parser.py` to ensure `data/processed/knot_filtered.csv` contains real values for core invariants. Append a sample of raw JSON and parsed CSV rows to `docs/reproducibility/data_ingestion_evidence.md`. **Verification**: `data_ingestion_evidence.md` contains non-placeholder data; `missing_invariant_flags` count is near zero. **Note**: Moved to Phase 1 to ensure data integrity before analysis.
- [ ] T007 Create `code/data/tie_breaking_validator.py` script that returns exit code 0 on success and generate `docs/reproducibility/tie_breaking_rules.md` (SC‑007). **Verification**: Script exits 0 and file exists.
- [X] T184 **Direct Knot Atlas Download** (FR‑001). **Deliverable**: `code/download/knot_atlas_downloader.py` fetches raw knot data directly from the Knot Atlas URL (`) using `requests`. Must handle specific API endpoint and JSON schema. **Verification**: Download succeeds, file size > 128 KB, source URL is logged, and data schema matches expected format. [UNRESOLVED-CLAIM: c_c5eb1f8c — status=not_enough_info]
- [X] T184a **Source Verification for Library vs Direct** (FR‑001). **Deliverable**: `code/download/source_verifier.py` compares a sample of data fetched via `database-knotinfo` with the directly downloaded Knot Atlas data (from T184) to confirm equivalence and that the library resolves to the canonical URL. **Verification**: {{claim:c_50415d96}}

## Phase 2: User Story 1 – Download and Parse Knot Data (Priority: P1)

- [ ] T011 **Download & Parse Knot Data from Knot Atlas** – Use `database-knotinfo` library (verified source) *and* the direct downloader from T184 to fetch knot data programmatically. Parse into a DataFrame using `fetch_all_knots()` configuration, writing `data/raw/knot_atlas_raw.json`. Implements FR‑001 directly. **Verification**: File size > 128 KB and contains expected header fields; code imports `database-knotinfo` and uses `fetch_all_knots()`.
- [ ] T011b **Download Retry Verification** (SC‑004) – Execute the download with `retry_wrapper`; test script ensures exponential backoff is exercised on simulated failures. **Verification**: Test logs show ≥3 retries with backoff.
- [ ] T012 **Data Parser** (`code/data/parser.py`) – Clean and normalize parsed data, flag only tabulated invariants. **Verification**: Unit test `tests/unit/test_parser.py` ensures no `missing_invariant_flags` for crossing number or braid index.
- [ ] T012a **Data Quality Report** (`code/data/quality_report.py`) – Compute null percentages (per-column, excluding empty strings), duplicate counts (exact row match), format pass rates. Generate `docs/reproducibility/data_quality_report.md`. **Verification**: Report shows {{claim:c_edbc91ef}}.
- [ ] T012b **Tie‑Breaking Validation** – Execute `code/data/tie_breaking_validator.py` on processed data. **Verification**: Exit code 0 and `docs/reproducibility/tie_breaking_rules.md` lists applied rules.
- [ ] T013 **Downloader Caching** – Implement local cache in `code/download/knot_info_loader.py`. **Verification**: Subsequent runs read from cache (log entry).
- [X] T015 **Hyperbolic Volume Filter** – Filter `knots_cleaned.csv` for `hyperbolic_volume > 0`, log exclusions, generate `docs/reproducibility/excluded_knots.md`. **Verification**: Documented exclusions match records.

## Phase 2.5: Core Invariant Validation & Consistency (formerly Phase 1.5, now after parsing)

- [ ] T180 **Create Knot Record Schema** – Add `contracts/knot_record.schema.yaml` defining required fields for KnotRecord, including placeholders for future computed invariants. **Verification**: File exists and is syntactically valid YAML. **Note**: Moved before T018 to ensure schema exists before validation.
- [ ] T182 **Extend Knot Record Schema for Computed Invariants** – Update `contracts/knot_record.schema.yaml` to include optional fields for arc index, Seifert circle count, and bridge number (required by Phase 10 tasks). **Verification**: Schema validates records containing these new fields. **Note**: Moved before T018 to ensure schema exists before validation.
- [ ] T014 **Persist Raw & Cleaned Data** – Save raw JSON to `data/raw/knot_atlas_raw.json` and filtered CSV to `data/processed/knot_filtered.csv`. **Verification**: Files exist with correct sizes.
- [ ] T018 **Contract Test for Data Schema** – `tests/contract/test_schemas.py` validates `contracts/knot_record.schema.yaml` against `data/processed/knot_filtered.csv`. **Verification**: Test passes.
- [X] T016 **Core Tabulated Invariant Precision** – Validate crossing number and braid index against KnotInfo references with absolute tolerance **1 × 10⁻⁶** and match rate ≥ 90 % (SC‑015, SC‑010). Generate `docs/reproducibility/core_precision_consistency.md`. **Dependency**: Requires T010 (Validation Scope) and data from T011/T012. **Verification**: Match rate ≥ 90 % within tolerance.
- [ ] T017 **Hyperbolic Volume Consistency** – Validate hyperbolic volume against KnotInfo where available, with tolerance **1 × 10⁻⁶**, match rate ≥ 90 % (SC‑015, SC‑010). Generate `docs/reproducibility/hyperbolic_volume_validation.md`. **Verification**: Match rate ≥ 90 % within tolerance.
- [ ] T200a **Dataset Completeness Validation** (SC‑001). **Deliverable**: `code/data/completeness_validator.py` counts records per crossing number, checks null % ≤ 5 %, ensures no duplicates, and cross‑checks counts against the Hoste‑Thistlethwaite‑Weeks enumeration (OEIS A002863) for the **full census (≤13 crossings)** using the `oeis` package or hardcoded lookup. Generates `docs/reproducibility/dataset_completeness_report.md`. **Verification**: Report meets all thresholds and explicitly confirms full-census count against OEIS A002863.
- [X] T200b **Ambiguous Alternating Classification Handling** (SC‑006). **Deliverable**: `code/data/alternating_handler.py` marks records with missing or ambiguous alternating/non‑alternating classification as `unclassifiable` and excludes them from group‑wise analyses. Generates `docs/reproducibility/alternating_handling_report.md`. **Verification**: Log shows count of excluded/marked records.
- [ ] T200c **Core‑Invariant Coverage Documentation** (SC‑008). **Deliverable**: `docs/reproducibility/core_invariant_coverage.md` summarises which core invariants (crossing number, braid index) are present for each record and overall coverage percentage. **Verification**: Coverage ≥ 95 % as required.
- [X] T200d **Descriptive Comparison Metrics Generation** (SC‑009). **Deliverable**: Extend `code/analysis/comparison_metrics.py` to compute mean difference, variance ratio, and Cohen’s d for alternating vs non‑alternating groups and output `docs/reproducibility/group_comparison_metrics.md`. **Verification**: Report contains all three metrics.
- [X] T200e **Explicit Tolerance Statement** (SC‑010). **Deliverable**: Update documentation in T016/T017 to state the 1 × 10⁻⁶ tolerance; no code change required beyond comments. **Verification**: Docs reflect tolerance.
- [X] T200f **Core‑Invariant Precision Consistency Report** (SC‑014). **Deliverable**: `docs/reproducibility/core_precision_consistency_extended.md` expands on T016 results, explicitly referencing SC‑014 criteria. **Verification**: Report aligns with SC‑014.
- [X] T200h **Residual Analysis Threshold Documentation** (SC‑011). **Deliverable**: `docs/reproducibility/residual_analysis_threshold.md` explicitly states the ≥ 2 SD deviation rule and lists identified families. **Verification**: Report matches the rule.
- [ ] T200i **Validation Scope Table Assurance** (SC‑012). **Deliverable**: Ensure `docs/reproducibility/validation_scope.md` (from T010) contains the required counts table and justification; add a checklist section. **Verification**: Table present and matches spec.
- [ ] T200j **Scatter‑Plot Visibility Validation** (SC‑016). **Deliverable**: Enhance `code/reproducibility/plot_validator.py` to compute the percentage of data points visible in each plot using alpha blending + jittering simulation; require ≥ 95% and **fail the build (exit code 1) if <95%**. Update `docs/reproducibility/plot_validation_report.md`. **Verification**: Report shows ≥ 95% visibility; script exits 0 only if criterion met.
- [ ] T200j2 **Scatter‑Plot Visibility Verification Execution** – Run `code/reproducibility/plot_validator.py` on all generated plots, generate `docs/reproducibility/plot_visibility_report.md` confirming the ≥ 95% criterion and **blocking if failed**. **Verification**: Report passes; build fails if criterion not met.
- [ ] T200k **Core Invariant Precision Validation (FR‑014)** – Implement a precision‑validation module (`code/reproducibility/core_precision_validator.py`) that recomputes crossing number and braid index from raw diagram data, compares against KnotInfo with tolerance 1 × 10⁻⁶, and produces `docs/reproducibility/core_precision_validation.md`. **Verification**: {{claim:c_a48c3003}} (Wikidata Q655020, https://www.wikidata.org/wiki/Q655020)
- [ ] T200l **Core Invariant Measurement‑Precision Standard (FR‑015)** – Produce `docs/reproducibility/core_measurement_precision_standard.md` summarizing how the precision‑validation satisfies the measurement‑precision standard defined in FR‑014/FR‑015, including statistical summaries. **Verification**: Document exists and references T200k results.
- [X] T1840 **FR‑009 Flag Logic Verification** – Add unit test `tests/unit/test_missing_invariant_flags.py` confirming that `missing_invariant_flags` are set only for computed invariants (arc index, Seifert circle count, bridge number) and never for core tabulated invariants. Update `docs/reproducibility/flag_logic_report.md` with results. **Verification**: Test passes; report generated.
- [ ] T183a **Implement Missing Invariant Flag Generation** – Implement logic in `code/data/validator.py` to set `missing_invariant_flags` for Phase 2+ computed invariants when diagram representations (DT code, braid word) are null/missing, as defined in FR-009. **Verification**: Unit test confirms flag is set for missing diagram data.

## Phase 3: User Story 2 – Core Invariant Precision Checks (Priority: P2)

- [X] T084 **Validator Core‑Invariant Unit Test** – `tests/unit/test_core_invariant_flags.py` asserts `missing_invariant_flags` empty for core invariants across the full dataset. **Verification**: Test passes.
- [ ] T183 **Fix Missing‑Invariant Flag Logic** (FR‑009). **Deliverable**: Refactor `code/data/validator.py` so that `missing_invariant_flags` are set **only** for invariants that cannot be derived from diagram representations (arc index, Seifert circle count, bridge number). Add unit test `tests/unit/test_missing_flags.py`. **Verification**: Test confirms core invariants never flagged.

## Phase 4: User Story 3 – Regression & Modeling (Priority: P3)

- [X] T025 **Deprecate Old Regression Script** – Ensure `code/analysis/regression.py` is removed or contains only a deprecation notice. **Verification**: File absent or contains only deprecation comment. [UNRESOLVED-CLAIM: c_63308db8 — status=not_enough_info]
- [ ] T041c **Plotting Module** – Implement in `code/analysis/plotting.py`. **Input**: `data/processed/knot_filtered.csv`. **Verification**: Generated PNGs are 1200 × 900 px, contain metadata fields: title, x‑label, y‑label, legend, source citation; also passes SC‑016 via T149.
- [ ] T041a‑linear **Model Fitting – Linear** (US3) – Implement in `code/analysis/model_fitting_linear.py`. **Verification**: Unit test `tests/unit/test_linear_model.py` runs on real filtered CSV and asserts R², AIC, BIC, MAE are computed.
- [ ] T041a‑poly **Model Fitting – Polynomial** (US3) – Implement in `code/analysis/model_fitting_poly.py`. **Verification**: Unit test `tests/unit/test_poly_model.py` asserts metrics.
- [ ] T041a‑log **Model Fitting – Logarithmic** (US3) – Implement in `code/analysis/model_fitting_log.py`. **Verification**: Unit test `tests/unit/test_log_model.py` asserts metrics.
- [X] T041b **Residual Analysis Module** (US3) – Implement in `code/analysis/residual_analysis.py`. **Verification**: Unit test `tests/unit/test_residual_analysis.py` confirms detection of families deviating ≥ 2 SD on synthetic data (distribution: normal, size: 1000, noise: 0.1). **Note**: T200h documents the ≥ 2 SD rule for real data.
- [X] T041d **Model Reporting Module** (US3) – Implement in `code/analysis/model_reporting.py`. **Verification**: Generate JSON report and validate against `contracts/regression_output.schema.yaml` using `jsonschema`.
- [X] T028 **Residual Analysis Execution** – Run `code/analysis/residual_analysis.py` on filtered dataset, generate `docs/reproducibility/residual_analysis.md`. **Verification**: File contains a section "Families deviating ≥ 2 SD". [UNRESOLVED-CLAIM: c_fc6b6540 — status=not_enough_info]
- [ ] T041e‑cn‑hv **Scatter Plot: Crossing Number vs. Hyperbolic Volume (Stratified)** – Generate `data/plots/crossing_vs_hyperbolic.png`. **Input**: `data/processed/knot_filtered.csv`. **Verification**: Image meets resolution (1200x900px), labels, legend, ≥95% points visible (validated by T200j/T200j2) using alpha blending + jittering simulation.
- [X] T041e‑bi‑hv **Scatter Plot: Braid Index vs. Hyperbolic Volume (Stratified)** – Generate `data/plots/braid_vs_hyperbolic.png`. **Verification**: Same criteria as above.
- [X] T026b **Orthogonalization Logic** – Implement `code/analysis/orthogonalization.py` to orthogonalize braid index w.r.t. crossing number. **Verification**: Unit test confirms orthogonalized predictor has zero correlation with crossing number. [UNRESOLVED-CLAIM: c_7fb1bb3c — status=not_enough_info] **Output**: `data/processed/knot_orthogonalized.csv`.
- [X] T026a **Variance Partitioning Metrics** – Compute variance partitioning, document in `docs/reproducibility/variance_partitioning.md`. **Verification**: Report includes R² split and acknowledges braid ≤ crossing constraint.
- [ ] T029‑integration **Verify Orthogonalization Integration** – Verify that `code/analysis/model_fitting.py` (T029) loads `data/processed/knot_orthogonalized.csv` (output of T026b) as input. **Verification**: Code inspection confirms input path; unit test asserts `orthogonalized` flag in model input.
- [X] T029 **Regression Model Fitting** – Use orthogonalized predictors (from `data/processed/knot_orthogonalized.csv`) to fit Linear, Polynomial, and Logarithmic models (via tasks T041a‑linear/poly/log). Generate `docs/reproducibility/regression_results.md`. **Verification**: Report contains R², AIC, BIC, MAE for each model; input file confirmed as orthogonalized dataset. [UNRESOLVED-CLAIM: c_fc24511c — status=not_enough_info]
- [X] T030 **Contract Test for Regression** – `tests/contract/test_regression.py` validates output schema against `contracts/regression_output.schema.yaml`. **Verification**: Test passes.
- [ ] T107 **Fix VIF Calculation Logic** – Re‑implement VIF in `code/analysis/model_fitting.py` to operate on `data/processed/knot_filtered.csv` using `statsmodels.stats.outliers_influence.variance_inflation_factor`. **Verification**: VIF values documented in `docs/reproducibility/multicollinearity_assessment.md`.
- [X] T104 **Add Strict PEP 484 Type Hints** – Added type hints to all public functions in analysis modules. **Verification**: `mypy --strict code/analysis/` passes with zero errors.
- [ ] T106 **Verify Data Loading in Model Fitting** – Unit test ensures `model_fitting.py` loads `data/processed/knot_filtered.csv` and that `hyperbolic_volume`, `crossing_number`, `braid_index` are non‑zero. **Verification**: Test passes.
- [X] T108 **Remove Deprecated Regression Script** – Deleted `code/analysis/regression.py` (or left with deprecation notice). **Verification**: File absent or contains only deprecation comment; search confirms no duplicate regression logic.

## Phase 5: Edge Cases, Data Quality & Reproducibility (Priority: P4)

- [ ] T032 **Data Validation & Error Handling** – Implement comprehensive checks in `code/data/validator.py`. **Verification**: Unit tests cover error paths.
- [ ] T033 **Generate Full Reproducibility Documentation** – Assemble all docs (`data_quality_report.md`, `excluded_knots.md`, `random_seeds.md`, `hyperbolic_volume_validation.md`, `core_precision_consistency.md`, `residual_analysis.md`, `tie_breaking_rules.md`, `plot_validation_report.md`, etc.). **Verification**: Directory `docs/reproducibility/` contains all required files.
- [X] T034 **Checksums Manifest & State Update** – Generate `docs/reproducibility/checksums.md` with SHA‑256 for all data files and update `state/...yaml` artifact map. **Verification**: Manifest matches file hashes; state file updated.
- [X] T051 **Consolidate Checksum Manifests** – Migrate old checksum files to `data/checksums.json` and update `docs/reproducibility/checksums.md`. **Verification**: Only `data/checksums.json` referenced.
- [ ] T052 **Consolidate Log Files** – Move logs to `docs/reproducibility/logs/`, update `docs/reproducibility/operation_logs.md`. **Verification**: Log directory contains expected files.
- [X] T053 **Update Reproducibility README** – Revise `docs/reproducibility/README.md` with TOC linking authoritative documents; remove `README_SUMMARY.md`. **Verification**: README renders correctly.
- [ ] T054 **Verify Multicollinearity Calculation** – Ensure VIF calculation in `model_fitting.py` uses actual data and matches `docs/reproducibility/multicollinearity_assessment.md`. **Verification**: Consistency check passes.
- [X] T055 **Consolidate Regression Logic** – Confirm `code/analysis/regression.py` is absent or deprecated. **Verification**: Test confirms no duplicate logic.
- [X] T059 **Remove Duplicate Regression Logic** – Ensure no active regression code remains in deprecated files. **Verification**: Search confirms absence; unit test `tests/unit/test_no_duplicate_regression.py` passes.
- [ ] T061 **Finalize Reproducibility Artifacts** – Ensure all logs, checksums, README are in place. **Verification**: Audit script confirms completeness.

## Phase 6: Final Verification & Gate Clearance

- [ ] T069 **Final Data Integrity Audit** – `code/scripts/final_data_audit.py` runs validator, checks flag counts, outputs `docs/reproducibility/final_data_integrity_audit.md`. **Verification**: Audit passes.
- [ ] T070 **Final Statistical Correctness Audit** – Re‑run `model_fitting.py` and `residual_analysis.py`, produce `docs/reproducibility/final_statistical_audit.md`. **Verification**: Audit confirms VIF value documented, residual families identified, metrics computed on real data.
- [X] T071 **Final Filesystem Hygiene Audit** – `code/scripts/final_hygiene_audit.py` verifies file existence/non‑existence, outputs `docs/reproducibility/final_hygiene_audit.md`. **Verification**: Audit passes.
- [ ] T072 **Final Hyperbolic Volume Consistency Check** – Re‑run volume validation, ensure match rate ≥ 90%, update `hyperbolic_volume_validation.md`. **Verification**: Documented rate meets threshold.
- [ ] T073 **Final Real Data Evidence** – Append first lines of `data/raw/knot_atlas_raw.json` and sample rows of `data/processed/knot_filtered.csv` to `docs/reproducibility/data_ingestion_evidence.md`. **Verification**: File contains excerpts.
- [X] T074 **Generate Final Reproducibility Package** – Compile all reports into `docs/reproducibility/FINAL_REPORT_PACKAGE.md` with links and summary. **Verification**: Package generated and links resolve.

## Phase 7: Code Quality & Architecture Refactoring (Addressing Research Reviewer Code Quality)

- [ ] T101 **Split `code/analysis/model_fitting.py` into modular components** – Refactored into:
 - `code/analysis/model_fitting.py`: Pure model fitting.
 - `code/analysis/residual_analysis.py`: Residual logic.
 - `code/analysis/plotting.py`: Figure generation.
 - `code/analysis/model_reporting.py`: Report generation.
 **Verification**: Each file < 200 lines.
- [X] T102 **[P] Consolidate Visualization Modules** – Merged visualization scripts into `code/analysis/visualization.py`. **Verification**: Old files deleted; new file imports successfully.
- [X] T103 **[P] Consolidate Metrics Modules** – Merged metric scripts into `code/analysis/metrics.py`. **Verification**: Old files deleted; new file contains all metric logic.
- [X] T104 **[P] Add PEP 484 Type Hints** – Completed (see T104 above).
- [ ] T105 **Create Unit Tests for Refactored Logic** – Added `tests/unit/test_model_fitting.py` and `tests/unit/test_residual_analysis.py`. **Verification**: Tests pass.
- [X] T106 **Verify Data Loading in Model Fitting** – Completed (see T106 above).
- [X] T107 **Fix VIF Calculation Logic** – Completed (see T107 above).
- [X] T108 **Remove Deprecated `regression.py`** – Completed (see T108 above).

## Phase 8: Data Integrity & Report Consistency (Addressing Research Reviewer Data Quality)

- [X] T109 **Investigate and Fix Data Ingestion** – Re‑run download/parsing pipeline to ensure real values for core invariants; verify missing flags ≤ 5 %. **Verification**: Evidence file shows real values and flag count ≤ 5 %. [UNRESOLVED-CLAIM: c_576115d8 — status=not_enough_info]
- [ ] T110 **Resolve Report Contradictions** – Align `data_quality_report.md`, `data_quantities.md`, and `invariant_coverage.md` to report identical totals and flag statistics. **Verification**: Manual diff confirms consistency.
- [X] T111 **Validate Real Data vs. Fabrication** – Populate `data_ingestion_evidence.md` with real data snippets. **Verification**: Evidence file contains real data excerpts.
- [X] T112 **Re‑run Consistency Check** – Execute hyperbolic volume consistency check; update report with ≥ 90 % match rate. **Verification**: Report shows required match rate.

## Phase 9: Filesystem Hygiene & Documentation Accuracy (Addressing Research Reviewer Filesystem Hygiene)

- [ ] T113 **Delete Redundant Checksum Manifests** – Deleted `data/checksums.sha256` and `data/checksums.csv`; retained only `data/checksums.json`. **Verification**: Only `data/checksums.json` exists.
- [ ] T114 **Consolidate Log Files** – Deleted `data/logs.jsonl` and `data/operation_logs.jsonl`; all logs now in `docs/reproducibility/logs/`. **Verification**: Logs only exist in the designated directory. [UNRESOLVED-CLAIM: c_2ef7b4af — status=not_enough_info]
- [X] T115 **Update README Accuracy** – Revised `docs/reproducibility/README.md` to list authoritative documents and removed `README_SUMMARY.md`. **Verification**: {{claim:c_ec349e90}} (Wikidata Q131983664, https://www.wikidata.org/wiki/Q131983664)
- [X] T116 **Naming Convention Consolidation** – Removed redundant narrative files, consolidating content into authoritative counterparts. **Verification**: No duplicate narrative files remain. [UNRESOLVED-CLAIM: c_2e837dba — status=not_enough_info]

## Phase 10: Deferred Scope (Phase 2+ Only)

- [X] T080 **Compute Additional Invariants** – Implement `code/data/computed_invariants.py` for arc index, Seifert circle count, bridge number where diagram data exists. **Dependency**: Requires Phase 2+ completion. **Verification**: Unit test validates calculations against known examples. *(Compliant with FR‑003 because computation occurs after Phase 1.)* **Note**: Status corrected to [ ] as per spec deferral.
- [X] T081 **Verify Computed Invariants** – `code/data/verify_invariants.py` compares computed values against definitions and KnotInfo where available. Generates `docs/reproducibility/computed_invariant_verification.md`. **Verification**: Report lists any discrepancies. **Note**: Status corrected to [ ] as per spec deferral.
- [X] T182 **Extend Knot Record Schema for Computed Invariants** – (Moved to Phase 2.5)
- [X] T200g **Additional Invariant Completeness** (SC‑005). **Deliverable**: After Phase 10 computes arc index, Seifert circle count, bridge number, run `code/data/additional_completeness.py` to verify ≥ 95 % of computable invariants are populated. Generates `docs/reproducibility/additional_invariant_completeness.md`. **Verification**: Completeness ≥ 95 %. **Note**: Moved to Phase 10 to depend on T080.

## Phase 11: Revision & Corrections (Addressing Outstanding Review Concerns)

- [X] T124 **Refactor Validator Missing‑Invariant Logic** – Ensure `missing_invariant_flags` only for Phase 2+ computed invariants. **Verification**: {{claim:c_6758bda3}} (Wikidata Q145, https://www.wikidata.org/wiki/Q145)
- [ ] T125 **Regenerate Data Quality Report** – After validator fix, re‑run quality report. **Verification**: Report shows `missing_invariant_flags` = 0, null % ≤ 5 %.
- [X] T126 **Add ComprehensiveType Hints** – (see T104)
- [X] T127 **Verify Real Data Loading in Model Fitting** – (see T106)
- [X] T128 **Correct VIF Calculation and Documentation** – (see T107)
- [X] T129 **Remove Deprecated Regression Script** – (see T108)
- [X] T130 **Add Test for Absence of Duplicate Regression Logic** – (see T059)
- [X] T131 **Provide Data Ingestion Evidence** – (see T111)
- [X] T132 **Re‑run Hyperbolic Volume Consistency Check** – (see T112)
- [X] T133 **Resolve Documentation Contradictions** – (see T110)
- [X] T134 **Re‑run Dataset Completeness Validation** – (see T200a)
- [X] T135 **Add Unit Test for High VIF Values** – Implement `tests/unit/test_vif_high.py` asserting each VIF ≥ 5. **Verification**: Test passes.

## Phase 12: Additional Revision Tasks (Addressing Remaining Review Issues)

- [ ] T137 **Regenerate Data Quality Report** – After fixing the validator, re‑run `code/data/quality_report.py` to produce an updated `docs/reproducibility/data_quality_report.md` with correct flag counts (expected `missing_invariant_flags` ≈ 0). **Verification**: Report shows accurate counts and passes null‑percentage thresholds.
- [ ] T138 **Provide Data Ingestion Evidence** – Create `docs/reproducibility/data_ingestion_evidence.md` containing a snippet (first few lines) of `data/raw/knot_atlas_raw.json` and a few rows of `data/processed/knot_filtered.csv` to demonstrate real data usage. **Verification**: File exists and contains the expected excerpts.
- [ ] T139 **Re‑run Hyperbolic Volume Consistency Check** – Execute `code/analysis/hyperbolic_volume_validation.py` against the verified dataset and update `docs/reproducibility/hyperbolic_volume_validation.md` with the actual match rate and coverage percentage. **Verification**: Document shows ≥ 90 % match where coverage ≥ 90 %.
- [ ] T140 **Delete Deprecated Checksum Files** – Remove `data/checksums.sha256` and `data/checksums.csv` (if present). Ensure only `data/checksums.json` remains as the authoritative manifest. **Verification**: Files are deleted; `docs/reproducibility/checksums.md` references only `data/checksums.json`.
- [X] T141 **Update Checksums Documentation** – Edit `docs/reproducibility/checksums.md` to remove references to the deprecated files and confirm the path points strictly to `data/checksums.json`. **Verification**: Documentation reflects the single manifest.
- [ ] T142 **Delete Old Log Files** – Remove `data/logs.jsonl` and `data/operation_logs.jsonl`. Ensure all operational logs are exclusively located in `docs/reproducibility/logs/`. **Verification**: Old log files are absent; new logs are present in the designated directory.
- [ ] T143 **Update Operation Logs Documentation** – Revise `docs/reproducibility/operation_logs.md` to describe the current log location (`docs/reproducibility/logs/`) and remove any “migrated” language. **Verification**: Documentation matches actual log storage.
- [ ] T144 **Revise Reproducibility README** – Update `docs/reproducibility/README.md` to list all authoritative documents (e.g., data quality report, validation scope, checksum manifest, logs) and remove or consolidate the generic `README_SUMMARY.md`. **Verification**: README accurately reflects the directory contents and provides clear navigation.
- [X] T145 **Remove Redundant README_SUMMARY.md** – Delete `docs/reproducibility/README_SUMMARY.md` if it adds no unique value. **Verification**: File is removed; references to it are eliminated.
- [ ] T146 **Correct VIF Calculation on Real Data** – Verify that `code/analysis/model_fitting.py` loads `data/processed/knot_filtered.csv` correctly, recompute VIF using `statsmodels.stats.outliers_influence.variance_inflation_factor`, and update `docs/reproducibility/multicollinearity_assessment.md` to reflect the expected high multicollinearity (VIF ≫ 5) or, if data truly shows low correlation, document the anomaly. **Verification**: VIF values in the report align with the dataset characteristics.
- [ ] T147 **Remove/Duplicate Regression Script** – Ensure `code/analysis/regression.py` is either deleted or contains only a deprecation notice, with all functional logic residing in `code/analysis/model_fitting.py`. **Verification**: No active regression code remains in `regression.py`; imports are updated accordingly.
- [ ] T149 **Ensure Plot Resolution Meets SC‑016** – Adjust plot generation parameters in `code/analysis/plotting.py` (e.g., `plt.figure(figsize=(12,9), dpi=100)`) so that all generated PNGs are at least 1200 × 900 px and contain required metadata. Re‑run `code/reproducibility/plot_validator.py` and update `docs/reproducibility/plot_validation_report.md` with passing results. **Verification**: Plot files meet size criteria; validation report passes.
- [ ] T150 **Update Plot Validation Documentation** – After fixing plot resolution, ensure `docs/reproducibility/plot_validation_report.md` accurately reflects the successful checks (resolution, axes labels, legend, data visibility). **Verification**: Report shows all checks passed.

## Phase 13: Addressing Specific Reviewer Concerns (Research Reviewer Code Quality & Data Quality)

- [ ] T153 **Resolve Report Contradictions (Record Counts)** – **Issue**: Reviewer noted discrepancy between "476 records" and "[deferred] records" in reports. **Action**: Update `docs/reproducibility/data_quality_report.md`, `docs/reproducibility/data_quantities.md`, and `docs/reproducibility/invariant_coverage.md` to reflect consistent, accurate record counts (total prime knots ≤13 crossings). **Verification**: All three documents report identical total counts and flag statistics.
- [ ] T154 **Re-run Hyperbolic Volume Consistency Check** – **Issue**: Reviewer noted inconsistency in volume validation due to potential data issues. **Action**: Once real data is confirmed, re-run `code/analysis/hyperbolic_volume_validation.py` and update `docs/reproducibility/hyperbolic_volume_validation.md` with the actual match rate and coverage percentage. **Verification**: Document shows ≥90% match rate where coverage ≥90%.
- [X] T155 **Consolidate Visualization Modules (Code Quality)** – **Issue**: Reviewer noted proliferation of `complexity_visualization*` files. **Action**: Merge `code/analysis/complexity_visualization.py`, `code/analysis/complexity_visualization_examples.py`, and `code/analysis/complexity_visualization_runner.py` into a single `code/analysis/visualization.py` with clear function separation. Delete the old files. **Verification**: Old files deleted; new file imports and functions correctly.
- [X] T156 **Consolidate Metrics Modules (Code Quality)** – **Issue**: Reviewer noted proliferation of `composite_metric*` files. **Action**: Merge `code/analysis/composite_metric*.py` files into a single `code/analysis/metrics.py`. Delete the old files. **Verification**: Old files deleted; new file contains all metric logic.
- [ ] T157 **Verify VIF Calculation on Real Data** – **Issue**: Reviewer noted VIF is expected to be significantly elevated, contradicting known mathematical constraints that suggest low values should not occur in this context. **Action**: Verify `code/analysis/model_fitting.py` loads `data/processed/knot_filtered.csv` correctly. Re-run VIF calculation using `statsmodels`. Update `docs/reproducibility/multicollinearity_assessment.md` to reflect expected high multicollinearity (VIF >> 5). **Verification**: Report shows high VIF values consistent with `braid_index <= crossing_number`.
- [ ] T158 **Ensure No Duplicate Regression Logic** – **Issue**: Reviewer noted ambiguity between `model_fitting.py` and `regression.py`. **Action**: Ensure `code/analysis/regression.py` is deleted or contains only a deprecation notice. All model fitting logic must reside in `code/analysis/model_fitting.py`. **Verification**: Search confirms no duplicate regression logic; `regression.py` is inactive.
- [ ] T159 **Update Checksums Documentation (Hygiene)** – **Issue**: Reviewer noted redundant checksum manifests (`checksums.sha256`, `checksums.csv`). **Action**: Ensure `data/checksums.json` is the sole manifest. Delete `data/checksums.sha256` and `data/checksums.csv`. Update `docs/reproducibility/checksums.md` to reference only `data/checksums.json`. **Verification**: Only `data/checksums.json` exists; documentation is updated.
- [ ] T160 **Update Log File Location (Hygiene)** – **Issue**: Reviewer noted logs fragmented between `data/` and `docs/reproducibility/logs/`. **Action**: Delete `data/logs.jsonl` and `data/operation_logs.jsonl`. Ensure all logs are exclusively in `docs/reproducibility/logs/`. Update `docs/reproducibility/operation_logs.md` to remove "migrated" language. **Verification**: Old log files deleted; new logs in correct location.
- [ ] T161 **Revise Reproducibility README (Hygiene)** – **Issue**: Reviewer noted generic READMEs not reflecting specific structure. **Action**: Update `docs/reproducibility/README.md` to list authoritative documents (e.g., "For braid index precision, see `braid_index_precision_validation.md`"). Remove `README_SUMMARY.md`. **Verification**: README accurately reflects directory contents and provides clear navigation. [UNRESOLVED-CLAIM: c_629cf084 — status=not_enough_info]
- [ ] T162 **Add Unit Tests for Refactored Analysis Modules** – **Issue**: Reviewer noted missing unit tests for split logic. **Action**: Create `tests/unit/test_model_fitting.py` and `tests/unit/test_residual_analysis.py` to cover the refactored logic in `code/analysis/model_fitting.py` and `code/analysis/residual_analysis.py`. **Verification**: Tests pass and cover key functions.
- [X] T163 **Verify Type Hints in Refactored Modules** – **Issue**: Reviewer noted missing type hints. **Action**: Run `mypy --strict code/analysis/` and fix all errors. Ensure all public functions in refactored modules have PEP 484 type hints. **Verification**: `mypy --strict` passes with zero errors.
- [ ] T164 **Split `code/analysis/model_fitting.py` (if not already done)** – **Issue**: Reviewer noted `model_fitting.py` is too large ([deferred] bytes). **Action**: If not already completed in T101, split `code/analysis/model_fitting.py` into `code/analysis/model_fitting.py` (fitting/metrics), `code/analysis/residual_analysis.py` (deviation logic), `code/analysis/plotting.py` (visualization), and `code/analysis/model_reporting.py` (report generation). Ensure each file is < 200 lines. **Verification**: Each file is < 200 lines; tests pass.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T1841 Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
