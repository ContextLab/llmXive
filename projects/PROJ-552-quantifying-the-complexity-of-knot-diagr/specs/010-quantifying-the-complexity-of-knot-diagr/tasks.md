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
- [X] T003 [P] Configure linting and formatting tools (black, flake8) in .pre-commit-config.yaml

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
- [X] T009 [P] Implement unified flagging system in `code/data/validator.py` handling missing invariant flags, data quality flags, and ambiguous classification flags. **Core invariants (crossing number, braid index) are excluded from `missing_invariant_flags` per FR‑009.** Verification: unit tests in `tests/unit/test_validator.py` demonstrating correct flag generation.
- [X] T016a [P] Create the validation pipeline script `code/data/run_validation.py` that orchestrates schema checks, null percentage validation (SC-001), format pass rate, and duplicate checks. Verification: script exits 0 on clean data, 1 on failure.
- [X] T026a [P] Document invariant verification procedure for additional invariants (arc index, Seifert circle count, bridge number) against primary literature (e.g., Birman & Menasco, Ohyama 1993) in `docs/reproducibility/invariant_definitions.md`. **(Phase 2+ only)** Verification: existence of documentation.
- [X] T026b [P] Implement `code/analysis/invariant_coverage.py` for computing and validating additional invariants. **(Phase 2+ only, optional for MVP)** Verification: module runs without error on sample data.
- [X] T030 [P] Document tie‑breaking rules in `docs/reproducibility/tie_breaking_rules.md` (per SC‑007)
- [X] T040b [P] Implement `code/analysis/hyperbolic_volume_validation.py` for cross‑check of hyperbolic volume against KnotInfo (framed as data integrity check, not independent verification). Verification: module runs and logs results.
- [X] T065a [P] Implement `code/reproducibility/citation_validator.py` to enforce title‑token overlap ≥ 0.7 for all citations (per Constitution Principle II). Verification: script runs and reports all citations meeting threshold.
- [X] T066a [P] Implement `code/reproducibility/hashing.py` to generate and record SHA‑256 hashes for artifacts and update `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml` (per Constitution Principle V). Verification: script runs, hash recorded, `updated_at` timestamp updated.
- [X] T013 [US1] Implement downloader for **Knot Atlas** in `code/download/knot_atlas_loader.py` with robust braid_index parsing (per FR‑001) and exponential back‑off retry logic (initial = 1 s, multiplier = 2, max = 32 s) with partial caching after 3 failures (FR‑008). Verification: successful download of at least one knot record with all required fields, including braid_index.
- [X] T015 [US1] Implement parser in `code/data/parser.py` to extract crossing number, braid index, hyperbolic volume, and alternating classification from Knot Atlas data, applying tie‑breaking rules (braid word > DT code, lexicographic). No external fallback for braid index. Verification: parser outputs correctly typed fields for a sample record.
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
- [X] T026 [US1] Validate tabulation accuracy for core invariants (crossing number, braid index) against KnotInfo reference values; require ≥ 90 % coverage (per FR‑003/SC‑008). Document results in `docs/reproducibility/core_invariants_tabulation.md`. Verification: coverage percentage reported.

### Tests for User Story 1 (OPTIONAL)

- [X] T011 [P] [US1] Contract test for data schema in `tests/contract/test_schemas.py`
- [X] T012 [P] [US1] Integration test for download pipeline in `tests/integration/test_pipeline.py`

**Checkpoint**: User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Establish Measurement Precision for Core Invariants (Priority: P2)

**Goal**: Establish precision thresholds for crossing number and braid index before correlation analysis proceeds so that I can validate measurement accuracy across different classes of prime knots.

- [X] T022 [US2] Implement precision validation module in `code/analysis/precision.py` to validate crossing number and braid index (per FR‑002, FR‑003). Verification: module outputs pass/fail per thresholds.
- [X] T023 [US2] Generate scatter plots of crossing number vs. braid index stratified by alternating/non‑alternating in `code/analysis/exploratory.py` (per FR‑004). Save to `data/plots/crossing_vs_braid.png` (1200 × 900 px).
- [X] T028 [US2] Compute null percentage for required invariant fields and document in `docs/reproducibility/data_quality_report.md` (per FR‑002, SC‑013). Verification: report reflects current dataset.
- [X] T029 [US2] **(Removed – flag logic now handled correctly in T009)**
- [X] T030b [US2] Implement validation script `docs/reproducibility/tie_breaking_validator.py` that checks consistency of tie‑breaking rules; script must exit 0 on success (per SC‑007). Verification: script runs and returns 0 for current data.
- [X] T067 [US2] Add human‑readable complexity interpretation guide in `docs/reproducibility/complexity_interpretation.md` (per reviewer feedback).
- [X] T068 [US2] Generate visualization examples mapping complexity metric to knot diagram features in `data/plots/complexity_visualization_examples.png`.
- [X] T069 [US2] Document concrete data quantities processed (knot counts per crossing number, total records, null percentages) in `docs/reproducibility/data_quantities.md`.
- [X] T070 [US2] Document classification error margins and signal‑to‑noise ratio analysis in `docs/reproducibility/classification_error_analysis.md`.

**Checkpoint**: User Stories 1 and 2 should both work independently.

---

## Phase 5: User Story 3 - Fit Regression Models to Assess Joint Predictive Relationships (Priority: P3)

**Goal**: Fit multiple regression models to test linear vs. non‑linear relationships for associating hyperbolic volume from crossing number and braid index.

- [X] T083 [US3] Refactor regression logic from `code/analysis/regression.py` into `code/analysis/model_fitting.py` (fits linear, polynomial, logarithmic models) and keep `regression.py` as a thin wrapper importing the new module (preserves plan compatibility). Verification: both scripts produce identical outputs.
- [X] T032 [US3] **(Removed – superseded by T083)**
- [X] T033 [US3] **(Removed – superseded by T083)**
- [X] T034 [US3] Perform residual analysis to identify hyperbolic knot families **pretzel** and **hyperbolic non‑alternating** (per FR‑005, SC‑011). Document families in `docs/reproducibility/residual_analysis.md`.
- [X] T035 [US3] Document residual family analysis in `docs/reproducibility/residual_analysis.md` with specific knot identifiers and explanations.
- [X] T036 [US3] Compute Spearman and Pearson correlation coefficients with effect sizes (Cohen’s d, r); explicitly note that p‑values are **not reported** for census data (per FR‑006 and Constitution Principle VII). Verification: output files contain “p‑value: N/A”.
- [X] T037 [US3] Compute VIF for multicollinearity assessment (per FR‑005). Verification: VIF values recorded in `docs/reproducibility/multicollinearity_assessment.md`.
- [X] T038 [US3] Document multicollinearity assessment in `docs/reproducibility/multicollinearity_assessment.md`, explicitly acknowledging the mathematical constraint **braid index ≤ crossing number** (per FR‑005).
- [X] T039 [US3] Compute descriptive comparison metrics (mean difference, variance ratio, Cohen’s d) for alternating vs. non‑alternating groups in `code/analysis/model_fitting.py` (per FR‑006).

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: User Story 4 - Edge Case Handling, Data Quality, and Reproducibility Documentation (Priority: P4)

**Goal**: Handle edge cases (API unavailability, missing invariants, ambiguous classifications, crossing number ties) with documented fallback behaviors, AND produce complete reproducibility documentation.

- [X] T044 [US4] Generate SHA‑256 checksums for all data files using `code/reproducibility/checksum_generator.py`; record in `data/checksums.sha256`. (Matches plan and Constitution Principle III)
- [X] T045 [US4] Record checksums in `data/checksums.sha256` and also produce optional `data/checksums.json` for tooling convenience. Documentation in `docs/reproducibility/checksums.md`.
- [X] T046a [US4] Create `docs/reproducibility/derivation_notes.md` with required sections: (1) Formula citations (author, year, title, DOI/URL); (2) Step‑by‑step transformation logic; (3) References to code locations. Verification script checks for presence of these headings.
- [X] T049a [US4] Generate timestamped operation logs in `data/operation_logs.jsonl` (machine‑readable) and a human‑readable summary `docs/reproducibility/operation_logs.md` containing columns: timestamp, module, action, status, duration_ms. Verification script validates column presence.
- [X] T050a [US4] Document random seed values used in `docs/reproducibility/random_seeds.md` as a markdown table with columns: seed_name, value, purpose, location_in_code. Verification ensures table is non‑empty.
- [X] T051 [US4] Log uncomputable invariants in `docs/reproducibility/uncomputable_invariants.md` (per FR‑003). Verification: file exists and lists any missing invariants.
- [X] T052 [US4] Document invariant coverage in `docs/reproducibility/invariant_coverage.md` (per SC‑008). Verification: coverage percentages reported.
- [X] T053 [US4] Generate validation status report in `docs/reproducibility/validation_status.md` (per SC‑007). Verification: report reflects results of `code/data/run_validation.py`.
- [X] T056 [US4] Run `quickstart.md` validation to ensure end‑to‑end reproducibility and document results in `docs/reproducibility/quickstart_validation.md` with pass/fail status.
- [X] T057 [P] Additional unit tests in `tests/unit/`:
   - `test_downloader.py` with tests for exponential back‑off, partial cache creation, and timeout handling.
   - `test_parser.py` with tests for crossing number parsing, braid index parsing, hyperbolic volume parsing.
- [X] T058 Verify all random seeds are pinned and document verification results in `docs/reproducibility/seed_verification.md` (distinct from `random_seeds.md` which lists values).
- [X] T059 Document selection bias acknowledgment (hyperbolic‑only filtering) in `docs/reproducibility/selection_bias.md` (per FR‑012, Assumptions).
- [X] T060 Document census data statistical interpretation in `docs/reproducibility/census_interpretation.md` (per Assumptions).
- [X] T061 Document mathematical constraint acknowledgment (**braid index ≤ crossing number**) in `docs/reproducibility/mathematical_constraints.md` (per Assumptions).

---

## Phase N+3: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T054a [P] Generate invariant algorithms documentation in `docs/reproducibility/invariant_algorithms.md` with reference implementations and mathematical definitions per FR‑003.
- [X] T054 [P] Documentation updates in `docs/reproducibility/` (ensure all FR‑007 required reproducibility documents are present with required content: `data_quality_report.md`, `validation_scope.md`, `excluded_knots.md`, `invariant_coverage.md`, `random_seeds.md`, `tie_breaking_rules.md`, `validation_status.md`, `algorithm_validation.md`, `hyperbolic_volume_validation.md`, `residual_analysis.md`, `multicollinearity_assessment.md`, `uncomputable_invariants.md`, `checksums.md`, `derivation_notes.md`, `operation_logs.md`, `census_interpretation.md`, `mathematical_constraints.md`, `invariant_algorithms.md`, `core_invariants_tabulation.md`, `correlation_metrics.md`, `ambiguous_classification_log.md`).
- [X] T055 Code cleanup and refactoring in `code/` to meet linting standards (black --check passes with no violations) and document linting report in `docs/reproducibility/linting_report.md`.
- [X] T056 Run `quickstart.md` validation to ensure end‑to‑end reproducibility and document validation results in `docs/reproducibility/quickstart_validation.md` with end‑to‑end pass/fail status.
- [X] T084a [P] Add PEP 484 type annotations to `code/download/knot_atlas_loader.py`.
- [X] T084b [P] Add PEP 484 type annotations to `code/analysis/precision.py`.
- [X] T084c [P] Add PEP 484 type annotations to `code/analysis/model_fitting.py`.
- [X] T084d [P] Add PEP 484 type annotations to `code/data/validator.py`.
- [X] T086 [P] Add unit tests in `tests/unit/test_regression.py` for regression model fitting and goodness‑of‑fit metric calculation (per Reviewer Action Item Testing).
- [X] T087 [P] Add unit tests in `tests/unit/test_residual_analysis.py` for residual‑family identification logic (per Reviewer Action Item Testing).
- [X] T088 [P] Add unit tests in `tests/unit/test_downloader.py` specifically for exponential back‑off behavior (per Reviewer Action Item Testing).

---

## Phase N+3: Data Integrity & Filesystem Hygiene Remediation (Addressing Critical Reviewer Findings)

**Purpose**: Address critical data integrity failures, filesystem hygiene violations, and statistical correctness issues.

- [X] T089 [P] Generate `docs/reproducibility/data_integrity_evidence.md` by running a script that extracts 5 random records from `data/raw/knot_atlas_raw.json` and the corresponding rows from `data/processed/knots_cleaned.csv`, then writes them side‑by‑side in a markdown table. Verification: script exits 0 and the markdown file exists.
- [X] T090 [P] Refactor `code/data/validator.py` to ensure `missing_invariant_flags` are only set for Phase 2+ computed invariants (arc index, etc.) as per FR‑009. Verification: unit tests confirm core invariants never receive this flag.
- [X] T091 [P] Update `docs/reproducibility/data_quantities.md` with the exact record count derived from `data/processed/knots_cleaned.csv`; commit the change. Verification: test asserts the count in the doc matches `len(df)`.
- [X] T092 [P] Create `docs/reproducibility/data_integrity_evidence.md` (as in T089) containing concrete JSON snippets of 5 raw records and their matching CSV rows to prove data is real. (Redundant task removed; T089 now fulfills this requirement.)
- [X] T093 [P] Re‑run `code/analysis/hyperbolic_volume_validation.py` on the corrected dataset; update `docs/reproducibility/hyperbolic_volume_validation.md` with actual match rate and coverage percentage.
- [X] T094a [P] Verify that `data/checksums.sha256` exists, matches recorded hashes, and that optional `data/checksums.json` (if present) is consistent. No deletion performed.
- [X] T095a [P] Verify that raw operation logs (`data/operation_logs.jsonl`) exist for pipeline reproducibility and that a human‑readable summary `docs/reproducibility/operation_logs.md` is up‑to‑date. No deletion performed.
- [X] T096 [P] Update `docs/reproducibility/README.md` to list authoritative documents for each category and note that other files are drafts/intermediate. Remove redundant `README_SUMMARY.md` if present.
- [X] T097 [P] Verify VIF calculation in `code/analysis/model_fitting.py` operates on actual loaded data; update `docs/reproducibility/multicollinearity_assessment.md` with correct values or explanation.
- [X] T098 [P] Ensure `code/analysis/regression.py` remains as a thin wrapper importing from `model_fitting.py`; no deletion.
- [X] T099a [P] Split `code/analysis/model_fitting.py` into `code/analysis/model_fitting_core.py` (fitting logic), `code/analysis/model_fitting_residuals.py` (residual analysis), and `code/analysis/model_fitting_metrics.py` (metrics computation). Each file must be <200 lines.
- [X] T099b [P] Split `code/analysis/visualization.py` (formerly multiple files) into a single unified module `code/analysis/visualization.py` containing all plot functions. Verification: module runs without error.
- [X] T099c [P] Consolidate metric utilities into `code/analysis/metrics.py`. Verification: module provides required functions.
- [X] T102 [P] Run `mypy --strict` on all refactored analysis modules and fix all errors.
- [X] T103 [P] Add `tests/unit/test_model_fitting.py` and `tests/unit/test_residual_analysis.py` to achieve ≥90 % coverage of the newly split modules.

**Dependencies & Execution Order**

- All Setup and Foundational tasks must complete before any User Story tasks.
- Data‑integrity remediation (Phase N+3) runs after User Story 1 produces the raw/processed data.
- Refactoring tasks (T099a‑c, T102, T103) run after regression refactor (T083) is stable.
- Verification/cleanup tasks (T094a, T095a) run after checksum and log generation tasks (T044, T045, T049a).
