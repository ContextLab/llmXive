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

## Phase 0: Plan-Spec Alignment (CRITICAL GATE)

**Purpose**: Resolve direct contradictions between plan.md and spec.md before implementation begins.

- [ ] T000 [P] **Resolve Plan/Spec Conflict**: Edit `specs/001-knot-complexity-analysis/plan.md` to REMOVE the "Critical Methodological Revision" section that proposes a "c-only" baseline. REPLACE it with a statement confirming adherence to **FR-005** and **SC-002**: the analysis MUST fit joint regression models (linear, polynomial, logarithmic) using BOTH crossing number AND braid index as predictors, and MUST compute VIF for multicollinearity assessment. Verification: `grep -r "c-only baseline"` in plan.md returns 0 matches; `grep -r "joint regression"` returns matches.

---

## Phase 1: Validation Benchmark (SC-015 Gate)

**Purpose**: Establish measurement precision for core invariants on the Phase 1 subset (crossing number ≤ 10) before full analysis proceeds.

- [ ] T026 [US1] **Phase 1 Validation Benchmark**: Validate core invariants (crossing number, braid index) against **KnotInfo reference values** for the **subset of knots with crossing number ≤ 10**; require ≥ 90% coverage (per FR-003/SC-008/SC-015). Document results in `docs/reproducibility/core_invariants_tabulation.md`. Verification: coverage percentage reported for the ≤ 10 subset only.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes critical data-quality logic to ensure SC-001 compliance.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T001 Create all project directories per plan.md Project Structure (code/, tests/, data/, docs/, data/raw/, data/processed/, data/plots/, docs/reproducibility/, tests/contract/, tests/integration/, tests/unit/)
- [X] T002 Initialize Python 3.11 project with dependencies in requirements.txt (pandas, numpy, scipy, statsmodels, matplotlib, seaborn, requests, pyyaml)
- [X] T003 [P] Configure linting and formatting tools (black, flake8) in .pre-commit-config.yaml
- [X] T004 [P] Define data schemas in `specs/001-knot-complexity-analysis/contracts/knot-record.schema.yaml`
- [X] T005 [P] Define regression model schemas in `specs/001-knot-complexity-analysis/contracts/regression-model.schema.yaml`
- [X] T005b [P] Define the dataset schema file `dataset.schema.yaml` in `specs/001-knot-complexity-analysis/contracts/` (per plan.md)
- [X] T006 Setup reproducibility logging framework in `code/reproducibility/logs.py` (timestamp, operation, input_file, output_file, parameters, status, duration_ms fields documented and testable; verification: unit tests in `tests/unit/test_logs.py` confirming all relevant fields present and testable)
- [X] T007 Implement random seed pinning in all `code/` files with stochastic operations (per Constitution Principle I; verification: if stochastic operations exist, all have pinned seeds documented in `docs/reproducibility/random_seeds.md`; if none exist, document N/A in `random_seeds.md`)
- [X] T008 Create `quickstart.md` in `specs/001-knot-complexity-analysis/quickstart.md` documenting end‑to‑end pipeline execution steps (per plan.md)
- [X] T009 [P] Implement unified flagging system in `code/data/validator.py` handling missing invariant flags, data quality flags, and ambiguous classification flags. **Core invariants (crossing number, braid index) are excluded from `missing_invariant_flags` per FR‑009.** Verification: unit tests in `tests/unit/test_validator.py` demonstrating correct flag generation.
- [X] T016a [P] Create the validation pipeline script `code/data/run_validation.py` that orchestrates schema checks, null percentage validation (SC-001), format pass rate, and duplicate checks. Verification: script exits 0 on clean data, 1 on failure.
- [X] T026a [P] Document Constitution Principle VI invariant verification procedure for additional invariants (arc index, Seifert circle count, bridge number) against primary literature (e.g., Birman & Menasco, Ohyama 1993) in `docs/reproducibility/invariant_definitions.md`. Verification: all additional invariants have documented reference and validation notes.
- [X] T026b [P] Implement `code/analysis/invariant_coverage.py` for computing and validating additional invariants (optional for Phase MVP, but required for validation logic). Verification: module runs without error on sample data.
- [X] T030 [P] Document tie‑breaking rules in `docs/reproducibility/tie_breaking_rules.md` (per SC‑007)
- [X] T040b [P] Implement `code/analysis/hyperbolic_volume_validation.py` for cross‑checking hyperbolic volume against KnotInfo (framed as data integrity check, not independent verification). Verification: module runs and logs results.
- [X] T065a [P] Implement `code/reproducibility/citation_validator.py` to run the Reference‑Validator Agent logic, enforcing title‑token overlap ≥ 0.7 for all citations (per Constitution Principle II). Verification: run `python code/reproducibility/citation_validator.py` on all citations; all must meet the threshold.
- [X] T066a [P] Implement `code/reproducibility/hashing.py` to generate and record content hashes for artifacts and update `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml` (per Constitution Principle V). Verification: run `python code/reproducibility/hashing.py` and confirm hash recorded and `updated_at` timestamp updated.
- [X] T013 [US1] Implement downloader for **Knot Atlas** in `code/download/knot_atlas_loader.py` with robust braid_index parsing (per FR‑001) and exponential back‑off retry logic (initial = 1 s, multiplier = 2, max = 32 s) with partial caching (per FR‑008). Verification: successful download of at least one knot record with all required fields, including braid_index.
- [X] T015 [US1] Implement parser in `code/data/parser.py` to extract crossing number, braid index, hyperbolic volume, and alternating classification from Knot Atlas data, applying tie‑breaking rules (braid word > DT code, lexicographic) (per FR‑011). Includes fallback lookup in `code/data/parser.py` to query KnotInfo API for `braid_index` when missing; log fallback usage in `docs/reproducibility/fallback_usage_log.md` (per reviewer action item). Verification: parser outputs correctly typed fields for a sample record.
- [X] T016 [US1] Integrate `code/data/validator.py` (T009) and `code/data/run_validation.py` (T016a) to enforce null‑percentage ≤ 5 % for required fields, format pass rate ≥ 99 %, and duplicate count = 0 (per FR‑002, SC‑001). Verification: unit tests confirm enforcement of these thresholds.

**Checkpoint**: Foundation ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Download and Parse Knot Data from Knot Atlas for all prime knots with crossing number ≤ 13 (Priority: P1) 🎯 MVP

**Goal**: Download knot data from Knot Atlas including crossing numbers, braid indices, hyperbolic volume, and alternating/non‑alternating classification for all prime knots with crossing number ≤ 13 (≈ 9988 knots, OEIS A002863).

- [X] T014 [US1] Implement exponential back‑off retry logic (initial = 1 s, multiplier = 2, max = 32 s) in `code/download/knot_atlas_loader.py`; cache partial results after consecutive failures (per FR‑008). Verification: simulated failures trigger back‑off and cache creation.
- [X] T018 [US1] Save raw data to `data/raw/knot_atlas_raw.json` and cleaned data to `data/processed/knots_cleaned.csv`.
- [X] T017 [US1] Generate dataset size report in `docs/reproducibility/dataset_counts.md` stating the total number of prime knots with crossing number ≤ 13 (≈ 9988) and per‑crossing‑number counts. Verification: run `code/analysis/validate_counts.py` to compare `len(df)` to the expected dataset size.
- [X] T019 [US1] Filter dataset to hyperbolic knots (volume > 0) and log excluded knots in `docs/reproducibility/excluded_knots.md` (per FR‑012). Verification: exclusion count matches log.
- [X] T040 [US1] Validate hyperbolic volume against KnotInfo reference values using `code/analysis/hyperbolic_volume_validation.py` (T040b); require ≥ 90 % record‑wise match within tolerance 1e‑6. If coverage < 90 %, document limitation and skip cross‑check (per FR‑013). Verification: report in `docs/reproducibility/hyperbolic_volume_validation.md` includes coverage percentage and any skip notice.
- [X] T020 [US1] Verify dataset size against OEIS A002863 (9988 prime knots ≤ 13 crossings). Document method and result in `docs/reproducibility/validation_scope.md` (per SC‑001). Verification: size matches OEIS count.

### Tests for User Story 1 (OPTIONAL)

- [X] T011 [P] [US1] Contract test for data schema in `tests/contract/test_schemas.py`
- [X] T012 [P] [US1] Integration test for download pipeline in `tests/integration/test_pipeline.py`

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Establish Measurement Precision for Core Invariants (Priority: P2)

**Goal**: Establish precision thresholds for crossing number and braid index before correlation analysis proceeds so that I can validate measurement accuracy across different classes of prime knots.

- [X] T022 [US2] Implement precision validation module in `code/analysis/precision.py` to validate crossing number and braid index (per FR‑002, FR‑003). Verification: module outputs pass/fail per thresholds.
- [X] T023 [US2] Implement scatter plots of crossing number vs. braid index stratified by alternating/non‑alternating in `code/analysis/exploratory.py` (per FR‑004). Save to `data/plots/crossing_vs_braid.png` (1200 × 900 px).
- [X] T028 [US2] Compute null percentage for required invariant fields and document in `docs/reproducibility/data_quality_report.md` (per FR‑002, SC‑013). Verification: report reflects current dataset.
- [X] T029 [US2] **(Removed – flag logic now handled correctly in T009)**
- [X] T030b [US2] Implement validation script `docs/reproducibility/tie_breaking_validator.py` that checks consistency of tie‑breaking rules; **if no knots with multiple representations are found, log the result as "not applicable" in `docs/reproducibility/validation_status.md`** (per SC‑007). **Depends on T026**. Verification: script runs and returns 0 for current data; status log updated.
- [X] T067 [US2] Add human‑readable complexity interpretation guide in `docs/reproducibility/complexity_interpretation.md` (per reviewer feedback).
- [X] T068 [US2] Generate visualization examples mapping complexity metric to knot diagram features in `data/plots/complexity_visualization_examples.png`.
- [X] T069 [US2] Document concrete data quantities processed (knot counts per crossing number, total records, null percentages) in `docs/reproducibility/data_quantities.md`.
- [X] T070 [US2] Document classification error margins and signal‑to‑noise ratio analysis in `docs/reproducibility/classification_error_analysis.md`.

**Checkpoint**: User Stories 1 and 2 should both work independently.

---

## Phase 5: User Story 3 - Fit Regression Models to Assess Joint Predictive Relationships (Priority: P3)

**Goal**: Fit multiple regression models to test linear vs. non‑linear relationships for associating hyperbolic volume from crossing number and braid index **using BOTH predictors as mandated by FR-005 and SC-002**.

- [X] T083 [US3] Refactor regression logic from `code/analysis/regression.py` into `code/analysis/model_fitting.py` (fits linear, polynomial, logarithmic models **using both crossing number and braid index as predictors** per corrected plan.md from T000) and keep `regression.py` as a thin wrapper importing the new module (preserves plan compatibility). Verification: both scripts produce identical outputs.
- [X] T032 [US3] **(Removed – superseded by T083)**
- [X] T033 [US3] **(Removed – superseded by T083)**
- [X] T034 [US3] Perform residual analysis to identify hyperbolic knot families **pretzel** and **hyperbolic non‑alternating** (per FR‑005, SC‑011). Document families in `docs/reproducibility/residual_analysis.md`.
- [X] T035 [US3] Document residual family analysis in `docs/reproducibility/residual_analysis.md` with specific knot identifiers and explanations.
- [X] T036 [US3] Compute Spearman and Pearson correlation coefficients with effect sizes (Cohen’s d, r); explicitly note that p‑values are **not reported** for census data (per FR‑006 and Constitution Principle VII). Verification: output files contain “p‑value: N/A”.
- [X] T037 [US3] Compute VIF for multicollinearity assessment **on the joint regression model** (per FR‑005). Verification: VIF values recorded in `docs/reproducibility/multicollinearity_assessment.md`.
- [X] T038 [US3] Document multicollinearity assessment in `docs/reproducibility/multicollinearity_assessment.md`, explicitly acknowledging the mathematical constraint **braid index ≤ crossing number** and the resulting VIF values (per FR‑005).
- [X] T039 [US3] Compute descriptive comparison metrics (mean difference, variance ratio, Cohen’s d) for alternating vs. non‑alternating groups in `code/analysis/model_fitting.py` (per FR‑006).

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: User Story 4 - Edge Case Handling, Data Quality, and Reproducibility Documentation (Priority: P4)

**Goal**: Handle edge cases (API unavailability, missing invariants, ambiguous classifications, crossing number ties) with documented fallback behaviors, AND produce complete reproducibility documentation.

### Implementation for User Story 4

- [X] T044 [US4] Generate SHA‑256 checksums for all data files in `code/reproducibility/checksums.py` (per FR‑007). Output MUST be `data/checksums.sha256` (single canonical file).
- [X] T045 [US4] Record checksums in `data/checksums.sha256` and document in `docs/reproducibility/checksums.md`. Verification: `sha256sum -c data/checksums.sha256` passes.
- [X] T046 [US4] Generate derivation notes with formula citations in `docs/reproducibility/derivation_notes.md`. Verification script `code/reproducibility/derivation_validator.py` confirms all required sections are non‑empty.
- [X] T049 [US4] Generate timestamped logs for all operations in `docs/reproducibility/operation_logs.md`.
- [X] T050 [US4] Document random seed values used in `docs/reproducibility/random_seeds.md`.
- [X] T051 [US4] Log uncomputable invariants in `docs/reproducibility/uncomputable_invariants.md` (per FR‑003).
- [X] T052 [US4] Document invariant coverage in `docs/reproducibility/invariant_coverage.md` (per SC‑008).
- [X] T053 [US4] Generate validation status report in `docs/reproducibility/validation_status.md` (per SC‑007).

**Checkpoint**: User Stories 1‑4 should all work independently.

---

## Phase N+3: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T054a [P] Generate invariant algorithms documentation in `docs/reproducibility/invariant_algorithms.md` with reference implementations and mathematical definitions per FR‑003.
- [X] T054 [P] Documentation updates in `docs/reproducibility/` (ensure all FR‑007 required reproducibility documents are present with required content: `data_quality_report.md`, `validation_scope.md`, `excluded_knots.md`, `invariant_coverage.md`, `random_seeds.md`, `tie_breaking_rules.md`, `validation_status.md`, `algorithm_validation.md`, `hyperbolic_volume_validation.md`, `residual_analysis.md`, `multicollinearity_assessment.md`, `uncomputable_invariants.md`, `checksums.md`, `derivation_notes.md`, `operation_logs.md`, `census_interpretation.md`, `mathematical_constraints.md`, `invariant_algorithms.md`, `core_invariants_tabulation.md`, `correlation_metrics.md`, `ambiguous_classification_log.md`).
- [X] T055 Code cleanup and refactoring in `code/` to meet linting standards (black --check passes with no violations). **Note: Linting report generation is handled by T114 in Phase N+5.**
- [X] T056 Run `quickstart.md` validation to ensure end‑to‑end reproducibility and document validation results in `docs/reproducibility/quickstart_validation.md` with end‑to‑end pass/fail status.
- [X] T084a [P] Add PEP 484 type annotations to `code/download/knot_atlas_loader.py`.
- [X] T084b [P] Add PEP 484 type annotations to `code/analysis/precision.py`.
- [X] T084c [P] Add PEP 484 type annotations to `code/analysis/model_fitting.py`.
- [X] T084d [P] Add PEP 484 type annotations to `code/data/validator.py`.
- [X] T086 [P] Add unit tests in `tests/unit/test_regression.py` for regression model fitting and goodness‑of‑fit metric calculation (per Reviewer Action Item Testing).
- [X] T087 [P] Add unit tests in `tests/unit/test_residual_analysis.py` for residual‑family identification logic (per Reviewer Action Item Testing).
- [X] T088 [P] Add unit tests in `tests/unit/test_downloader.py` specifically for exponential back‑off behavior (per Reviewer Action Item Testing).

---

## Phase N+1: Reviewer‑Driven Additions (Adjusted for Spec Compliance)

- [ ] T073 [US1] **Implement braid_index acquisition logic**: Implement the logic in `code/data/validator.py` to handle missing `braid_index` by flagging with `missing_invariant_flags` and logging to `docs/reproducibility/missing_braid_index.log`. **Do NOT exclude the knot from the primary analysis** (per FR‑001; FR‑009). This maintains strict data lineage.
- [ ] T074 [US1] **Log missing braid_index**: When `braid_index` is absent in a Knot Atlas record, ensure the record is flagged with `missing_invariant_flags` (per T073) and log the incident in `docs/reproducibility/missing_braid_index.log`. **Do NOT exclude the knot from the primary analysis** (per FR‑001; FR‑009). This maintains strict data lineage. **Depends on T073**.
- [ ] T075 [US1] Refactor `code/data/validator.py` so that `missing_invariant_flags` are only set for **computed** invariants (arc index, Seifert circle count, bridge number) when diagram representations are missing. **Tabulated** invariants (crossing number, braid index) fetched from the source must NEVER trigger this flag; if a tabulated invariant is missing from the source, use the logic in T074 to flag it separately. (per FR‑001, FR‑003).
- [ ] T076 [US1] After fixing braid‑index acquisition and flag logic, regenerate `docs/reproducibility/data_quality_report.md` and `docs/reproducibility/invariant_coverage.md`; verify that null percentages for all required fields are ≤ 5 % and that flag counts are accurate. (Depends on T073, T075)
- [X] T077 [US4] Run `code/reproducibility/run_checksums.py` on all current data files; update `data/checksums.sha256` (per plan.md) to reflect the new hashes; commit the updated manifest. (Depends on T044, T045)
- [X] T078 [US4] Add a checksum‑verification step to `docs/reproducibility/quickstart.md` that aborts pipeline execution if any checksum mismatch is detected; include automated test `tests/integration/test_checksum_verification.py`. (Depends on T077)
- [X] T080 [US1] Add unit tests for the exponential backoff behavior in the downloader (`tests/unit/test_backoff.py`) verifying delay progression (1 s → 2 s → 4 s → …) and maximum cap.
- [X] T081 [US3] Add unit tests for regression model fitting and goodness‑of‑fit metric calculation (`tests/unit/test_regression_metrics.py`) ensuring R², AIC, BIC, and MAE are computed correctly for synthetic data.
- [X] T082 [US3] Add unit tests for residual‑family identification logic (`tests/unit/test_residual_analysis.py`) confirming that families with residuals ≥ 2 σ are correctly listed.
- [X] T083 [US1] Add comprehensive type hints (PEP 484) to key modules: `code/download/knot_atlas_loader.py`, `code/analysis/precision.py`, `code/analysis/regression.py`, and `code/data/validator.py`; run `mypy` as part of CI.
- [X] T084 [US1] Refactor analysis code into focused modules per code‑quality reviewer suggestion:
 - `code/analysis/coverage.py` – pure coverage calculations
 - `code/analysis/validation.py` – hyperbolic‑volume cross‑checks
 - `code/analysis/model_fitting.py` – regression fitting and residual analysis
 - `code/analysis/plotting.py` – all figure generation
 (Depends on T032‑T034)
- [X] T085 [US1] Update CI workflow to include linting, type‑checking (`mypy`), and the new unit tests; ensure the pipeline completes within the specified CI limit.
- [X] T086 [US1] Document the newly added type‑hinting and modularization in `docs/reproducibility/code_structure.md` for future maintainers.

---

## Phase N+3: Critical Data Integrity & Filesystem Hygiene Fixes (Re‑ordered and Clarified)

**CRITICAL**: Must be completed before any further analysis or reporting.

- [ ] T098 [US4] **Fix Flagging Logic in Validator**: Refactor `code/data/validator.py` to ensure `missing_invariant_flags` are **only** set for Phase 2+ computed invariants (arc index, etc.) when diagram representations are missing. Core tabulated invariants (crossing number, braid index) must never trigger this flag. (Addresses `c331e6ba9675`, `54f11db3305b`)
- [ ] T099 [US3] **Implement VIF Calculation**: Add VIF computation to `code/analysis/model_fitting.py` (uses `statsmodels.stats.outliers_influence.variance_inflation_factor`) **for the joint regression model** (per T000 corrected plan). Output the VIF table to `docs/reproducibility/multicollinearity_assessment.md`. Verify that VIF values are reported (expected high due to braid index ≤ crossing number) and that the file exists.
- [ ] T100 [US3] **Consolidate Regression Logic**: Remove deprecated `code/analysis/regression.py` after migration to `model_fitting.py`. Ensure no duplicate logic remains.
- [ ] T091a [US4] **Create Data Fabrication Audit Script**: Create `code/analysis/audit_data_fabrication.py` that generates `docs/reproducibility/data_fabrication_audit.md` containing: 1. A side-by-side sample of the first 10 raw JSON rows vs. the corresponding 10 parsed CSV rows. 2. A summary table stating that `missing_invariant_flags` for core fields (crossing number, braid index) are 0 for the first 100 rows. 3. **Pass/Fail Criteria**: The script exits 0 on PASS, 1 on FAIL. (Does not require data yet; creates the script only).
- [ ] T091b [US4] **Run Data Fabrication Audit**: **Re-run the download/parser pipeline logic (T013/T015) after T098 fixes**, then execute `code/analysis/audit_data_fabrication.py` to generate `docs/reproducibility/data_fabrication_audit.md`. Verification: Script exits 0 and the audit file exists with correct content.
- [ ] T102 [US4] **Migrate Logs to Reproducibility Directory**: Move all existing log files (`data/logs.jsonl`, `data/operation_logs.jsonl`) to `docs/reproducibility/logs/`. Verify that each moved file is present in the new location before proceeding. Update any code references accordingly.
- [ ] T103 [US4] **Validate Migrated Logs**: Verify that all logs in `docs/reproducibility/logs/` are valid JSON lines and complete. Update `docs/reproducibility/operation_logs.md` to confirm the new location and remove any "migrated" language.
- [ ] T093 [US4] **Update Data Quality Documentation**: **Depends on T091b**. Run a script to extract the exact record count from `data/processed/knots_cleaned.csv` and update `docs/reproducibility/data_quality_report.md`, `docs/reproducibility/data_quantities.md`, and `docs/reproducibility/invariant_coverage.md` with the accurate count and flag statuses. Verification: All three files contain the correct count.
- [ ] T094 [US4] **Re‑run Hyperbolic Volume Consistency Check & Source Independence**: After data regeneration (T091b), execute `code/analysis/hyperbolic_volume_validation.py` and update `docs/reproducibility/hyperbolic_volume_validation.md` with the actual match rate and coverage percentage. **Include a Source Independence Assessment** (determining if Knot Atlas and KnotInfo share data sources) as required by SC‑014 and FR‑013.
- [ ] T095 [US4] **Create JSON Checksum Manifest (Preserve SHA256)**: **Depends on T091b and T044/T045**. Generate `data/checksums.json` containing a JSON mapping of file paths to their SHA‑256 hashes **in addition to** retaining the existing `data/checksums.sha256`. Verify both files exist and hashes match.
- [ ] T096 [US4] **Delete Legacy Log Files After Migration**: After successful execution of T102 and verification via T103, delete `data/logs.jsonl` and `data/operation_logs.jsonl`. This task must run **after** T102 and must verify that the migrated logs are intact (T103 passed) before deletion.

**Dependencies & Execution Order**

- T098 → T099 → T091a → T091b → T094 (linearized)
- T102 → T103 → T096 (migration before deletion)
- T095 runs after T091b (data regeneration) and T044/T045 (checksum generation).
- T093 runs after T091b.
- All verification tasks (T093) run after T091b regeneration.

---

## Phase N+5: Code Quality Refactoring (Addressing Research Reviewer Code Quality Concerns)

**Purpose**: Address specific code quality issues identified by `research_reviewer_code_quality_research` regarding file size, modularity, and type safety.

- [ ] T099a [P] **Split `code/analysis/model_fitting.py`**: Split `code/analysis/model_fitting.py` (currently >14KB) into three distinct modules, each <200 lines:
 1. `code/analysis/model_fitting.py`: Pure model fitting (Linear, Polynomial, Logarithmic) **using joint predictors** and metric calculation (R², AIC, BIC, MAE).
 2. `code/analysis/residual_analysis.py`: Logic for identifying families deviating ≥ 2 SD (T034, SC-011).
 3. `code/analysis/plotting.py`: All figure generation logic (T023, T033).
 Verification: Run `wc -l` on each file; all must be < 200 lines. Unit tests must pass for each module.
- [ ] T107 [P] **Verify Split**: Verify the split performed in T099a. Run `wc -l` on each file; all must be < 200 lines. Unit tests must pass for each module. (Depends on T099a).
- [ ] T110 [P] **Add Strict Type Hints**: Add PEP 484 type hints to all public functions in the refactored modules (`model_fitting.py`, `residual_analysis.py`, `plotting.py`, `visualization.py`, `metrics.py`).
 Verification: Run `mypy --strict code/analysis/` and ensure zero errors.
- [ ] T111 [P] **Create Unit Tests for Refactored Modules**: Create `tests/unit/test_model_fitting.py` and `tests/unit/test_residual_analysis.py` to cover the split logic with ≥90% coverage.
 Verification: `pytest --cov=code/analysis` shows ≥90% coverage for the new modules.
- [ ] T112 [P] **Verify VIF Calculation on Real Data**: Ensure `code/analysis/model_fitting.py` loads `data/processed/knots_cleaned.csv` directly and computes VIF on the actual dataset **using the joint model**.
 Verification: `docs/reproducibility/multicollinearity_assessment.md` reports VIF >> 5 (expected high correlation) or explicitly documents the data source if low.
- [ ] T113 [P] **Remove Redundant Regression Logic**: Ensure `code/analysis/regression.py` is removed or strictly serves as an orchestration wrapper if its logic has been fully migrated to `model_fitting.py`.
 Verification: No duplicate regression logic exists; `grep -r "fit_model"` in `code/analysis/` returns results only in the designated core module.
- [ ] T114 [P] **Generate Linting Report**: Run `mypy --strict` on all refactored analysis modules and **generate `docs/reproducibility/linting_report.md`** with the full output (per FR-007). Verification: `linting_report.md` exists and contains the mypy output.

---

## Phase N+4: Final Review & Release

- Run full CI pipeline including linting, type‑checking, unit tests, and integration tests.
- Ensure all documentation files referenced in the Constitution are present and up‑to‑date.
- Tag release after successful pipeline.