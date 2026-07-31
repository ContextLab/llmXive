# Tasks: Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

**Input**: Design documents from `/specs/001-predict-hea-yield-strength/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create directory structure: `code/`, `data/raw`, `data/processed`, `output/`, `tests/`, `output/plots`
- [X] T001b Create `__init__.py` files in all `code/` and `tests/` subdirectories
- [X] T001c Create `requirements.txt` and `README.md` scaffolding

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup deterministic logging and random seed management in `code/utils/logging.py`
- [X] T005 [P] Create base data schemas and validation logic in `code/data/__init__.py`
- [X] T006 Implement unit normalization utility (MPa conversion) in `code/utils/unit_utils.py`. **Scope**: This task creates a reusable function `normalize_to_mpa(value, unit)` available for the entire project. **CRITICAL**: The function MUST explicitly handle: (1) Unit column present: convert GPa to MPa (multiply by 1000), (2) Unit column missing: assume MPa, (3) Invalid unit string: raise `ValueError`. **Depends on T004**.
- [X] T007 Setup environment configuration management for verified dataset URLs in `code/utils/config.py`
- [X] T029a [P] [Cross-Cutting] Implement plot disclaimer injector in `code/utils/plot_utils.py` to append "Associational analysis only; no causal inference" to all generated matplotlib/seaborn figures. **Depends on T004**.
- [X] T029b [P] [Cross-Cutting] Implement report disclaimer injector in `code/utils/report_utils.py` to append the mandatory disclaimer to report markdown text. **Depends on T004**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Descriptor Engineering (Priority: P1) 🎯 MVP

**Goal**: Download HEA data from verified repositories, calculate compositional descriptors (δ, Δχ, VEC, entropy, melting var), and filter to single-phase room-temperature alloys.

**Independent Test**: Execute data pipeline; verify output CSV exists with count of single-phase HEA compositions and complete descriptor values.

### Implementation for User Story 1

- [X] T008 [P] [US1] Implement data downloader in `code/data/download.py` to fetch from `research.verified_datasets['hea_compositions']` in `research.md`. **CRITICAL Logic**:
 1. Attempt to fetch from verified URL in `research.md`.
 2. If verified URL is MISSING or fails, attempt to fetch from open repositories listed in FR-001 in this EXACT order:
 (1) **Materials Project**: `https://materialsproject.org/rest/v2/materials?elements=HEA&properties=yield_strength` (API key required).
 (2) **NIST HEA Database**: ` (scrape or API if available).
 (3) **Zenodo**: ` (or specific DOI from spec).
 3. If ALL sources fail, return status `NO_DATA` (do NOT terminate the process).
 4. If data is found (N > 0), return status `SUCCESS`.
 5. If data is found but N=0 (empty file), return status `NO_DATA`.
 This satisfies FR-001's requirement to attempt open repositories and report N=0. **Depends on T005, T007**.

- [X] T009 [P] [US1] Implement data preprocessor in `code/data/preprocess.py` to filter single-phase, room-temperature, and handle missing yield strength values. **Depends on T008**.

- [X] T010 [US1] Apply unit normalization in `code/data/preprocess.py` using the utility from T006 to convert all yield strength to MPa. **Depends on T009, T006**.

- [X] T011 [P] [US1] Implement elemental property loader in `code/data/descriptors.py` (atomic radii, electronegativity, valence counts, **melting temperature**). **Primary Source**: Load from `contracts/elemental_properties.schema.yaml`. **CRITICAL**: If melting temperature data is missing for any element in the dataset, the task MUST raise a `DataHygieneError` and exclude the composition; it MUST NOT query external APIs or silently omit the descriptor. **Depends on T005**.

- [X] T012 [US1] Implement descriptor calculator in `code/data/descriptors.py` for δ, Δχ, VEC, mixing entropy, and **melting temperature variance**. **CRITICAL**: This task MUST explicitly list 'melting temperature variance' as a required output and fail if the input data (from T011) does not contain melting temperatures. **Depends on T010, T011**.

- [X] T013 [US1] Implement composition filter in `code/data/descriptors.py` to exclude entries with missing elemental properties. **Depends on T012**.

- [X] T014 [US1] Implement pipeline orchestrator in `code/data/pipeline.py` to define the sequence: download -> preprocess (filter) -> normalize -> descriptors -> filter_missing. **CRITICAL**: This task MUST pass the status returned by T008 (`SUCCESS` or `NO_DATA`) to T015. **Depends on T008, T009, T010, T011, T012, T013**.

- [X] T015 [US1] Generate `data/processed/hea_descriptors.csv` and write `output/data_status.json` at the exact relative path `output/data_status.json`. The JSON schema MUST be: `{ "count": int, "count_warning": bool (true if count < 500), "power_status": bool (true if count < 50), "timestamp": str }`. **CRITICAL**:
 1. If status from T014 is `NO_DATA`: Set `count` = 0, `count_warning` = false, `power_status` = false. Log "DATA_LIMITATION_WARNING: No data found. Exiting with code 0." and exit with code 0.
 2. If status is `SUCCESS` and count < 500: Set `count_warning` = true and log "DATA_LIMITATION_WARNING: Only N entries found. Statistical power may be reduced."
 3. If status is `SUCCESS` and count < 50: Set `power_status` = true.
 This task MUST explicitly implement the "flagging" action required by FR-001 and ensure the JSON artifact is written before any exit. **Depends on T014**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Predictive Performance Evaluation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting models (5-fold CV, hyperparameter tuning ≤50 trees, depth ≤10), evaluate on hold-out test set, and compare against Linear Regression baseline.

**Independent Test**: Execute training script; verify `output/metrics.json` contains R², MAE, RMSE for all models; confirm runtime ≤ 3 hours on CPU.

### Implementation for User Story 2

- [X] T016 [P] [US2] Implement data splitter in `code/models/train.py` to create a **strictly held-out** test set using **Stratified by Elemental Ratios** (as per Plan feasibility decision).
 **Algorithm**:
 1. Compute elemental ratios for each alloy.
 2. Bin alloys into strata based on these ratios.
 3. Split 80/20 stratified by these bins, ensuring seed=42.
 4. **Validation**: Assert that no elemental combination appears in both sets (approximate disjointness).
 **CRITICAL**: This task replaces the previous "disjoint elemental sets" requirement with the feasible "Stratified" approach. **Depends on T015**.

- [X] T017 [P] [US2] Implement Linear Regression baseline trainer in `code/models/train.py`. **Depends on T016**.

- [X] T018 [P] [US2] Implement Random Forest trainer with 5-fold CV and grid search (trees: 10 to 50, depth ≤ 10) in `code/models/train.py`. **CRITICAL**: Grid search MUST cover the range 10 to 50 trees and max_depth <= 10, strictly adhering to FR-004's ≤50 trees constraint. **Depends on T016**.

- [X] T019 [P] [US2] Implement Gradient Boosting trainer with 5-fold CV and grid search (trees: 10 to 50, depth ≤ 10) in `code/models/train.py`. **CRITICAL**: Grid search MUST cover the range 10 to 50 trees and max_depth <= 10, strictly adhering to FR-004's ≤50 trees constraint. **Depends on T016**.

- [X] T020 [US2] Implement evaluation runner in `code/models/evaluate.py` to compute R², MAE, RMSE on held-out test set AND generate plots. **Must use T029a for all generated plots**. **Depends on T017, T018, T019, T029a**.

- [X] T021 [US2] Create `output/metrics.json` writer to record metrics for all models and select the best model. The JSON schema MUST be: `{ "rf": { "R2": float, "MAE": float, "RMSE": float }, "gb": { "R2": float, "MAE": float, "RMSE": float }, "linear": { "R2": float, "MAE": float, "RMSE": float }, "best_model": "rf|gb|linear" }`. **Depends on T020**.

- [X] T022 [US2] Add total pipeline runtime tracker in `code/main.py` (or `code/utils/runtime.py`) to measure the end-to-end duration (data acquisition + descriptors + training + validation). **CRITICAL**: This task MUST depend on T014, T030, T026, T018, T019, T021 to capture the FULL runtime. It MUST write `output/pipeline_runtime.json` with schema `{ "total_runtime_seconds": float, "limit_seconds": 21600, "status": "pass|fail" }`. **If `total_runtime_seconds` > 21600, raise an AssertionError**. **Depends on T014, T030, T026, T018, T019, T021**.

---

## Phase 5: User Story 3 - Statistical Validation and Significance Reporting (Priority: P3)

**Goal**: Perform permutation testing, bootstrap resampling, multiple‑comparison correction, sensitivity analysis on α, and VIF diagnostics.

**Independent Test**: Execute validation script; verify report contains p‑values, confidence intervals, corrected significance levels, and VIF flags.

### Implementation for User Story 3

- [X] T030 [US3] Implement power analysis checker in `code/models/evaluate.py` to read `output/data_status.json` (from T015) and write `output/power_analysis.json` at the exact relative path `output/power_analysis.json`. **Schema**: `{ "n": int, "status": "sufficient" | "low_power", "action": "proceed" }`. **CRITICAL**: If N < 50, set status to `low_power` and action to `proceed`. Do NOT skip statistical tests. This artifact is the single source of truth for whether statistical tests should run (they always run, but with a warning). **Depends on T015**.

- [X] T023 [US3] Implement VIF calculator in `code/models/evaluate.py` for the **Linear Regression baseline model ONLY** (`model_linear`). Calculate VIF for all descriptors in the linear model and flag any VIF > 10. **CRITICAL**: FR‑009 specifies VIF "within the full multiple regression model". Random Forest and Gradient Boosting are non‑linear ensemble methods that do not utilize a design matrix suitable for standard VIF calculation; therefore, VIF is **not** calculated for RF or GB. Write results to `output/vif_results.json` with schema `{ "vif_values": { "descriptor": float }, "max_vif": float, "needs_remediation": bool }`. **Depends on T017**.

- [X] T023b [US3] Implement VIF remediation in `code/models/evaluate.py`. **CRITICAL**: This task MUST read `output/vif_results.json`. If `needs_remediation` is true, apply PCA or L1‑regularization **only** to the linear baseline model (`model_linear`) and re‑train. Save the corrected model as `model_linear_corrected` and write `output/remediation_results.json` confirming the method used (PCA/L1). **Depends on T023**.

- [X] T044 [P] Enforce a sufficient number of permutations for permutation‑importance testing, regardless of dataset size. Implements a hard‑coded loop of a fixed number of permutations and logs a warning if N is very small. **Depends on T018, T019**.

- [X] T024 [US3] Implement permutation importance tester in `code/models/evaluate.py` (using a sufficiently large number of permutations) to calculate p‑values for all descriptors. **CRITICAL**: This task runs a sufficient number of permutations to ensure statistical robustness. (as enforced by T044) and does **not** skip for low N. Writes results to `output/permutation_results.json`. **Depends on T018, T019, T044**.

- [X] T025 [US3] Implement multiple‑comparison correction (Bonferroni/Benjamini-Hochberg) in `code/models/evaluate.py`. **Depends on T024**.

- [X] T026 [US3] Implement bootstrap resampling in `code/models/evaluate.py` (a sufficient number of resamples) for **BOTH** the Linear Regression baseline model (`model_linear` or `model_linear_corrected` if remediation applied) **and** the best performing tree‑based model (selected after tuning) to calculate a confidence interval for R². **CRITICAL**: Uses the corrected linear model when applicable. Writes `output/bootstrap_results.json`. **Depends on T017, T018, T019, T023, T030**.

- [X] T027 [US3] Implement sensitivity analysis runner in `code/models/evaluate.py` to sweep α over the discrete set **{0.01, 0.05, 0.1}**. Calculate the count of significant descriptors and R² values for each threshold. **CRITICAL**: This task MUST explicitly record the **absolute headline R²** values for the best model and the linear baseline for each α threshold in `output/sensitivity_results.json`. **Schema**: `{ "thresholds": [ { "alpha": float, "absolute_R2_best": float, "absolute_R2_linear": float, "significant_count": int } ] }`. **Depends on T024, T025**.

- [X] T028 [US3] Create statistical report generator in `output/report.md` including all p‑values, CIs, VIF flags, and integrating DISCLAIMERS from T029a/T029b. The report MUST follow this template:
 1. Overview
 2. Model Performance (from T021)
 3. Statistical Validation (VIF, Permutation, Bootstrap)
 4. Sensitivity Analysis (from T027)
 5. Conclusion (with disclaimer). **CRITICAL**: This task MUST include an explicit verification step: "Assert mandatory disclaimer string 'Associational analysis only; no causal inference' exists in the generated output/report.md". **CRITICAL**: If `data_status['count_warning']` is true, the report MUST include a dedicated section titled "Data Limitation Warning" re‑emitting the warning message from T015. **Depends on T015, T021, T023, T023b, T024, T025, T026, T027, T029a, T029b**.

---

## Phase 5a: Data Hygiene, Provenance, and Versioning (Cross‑Cutting)

**Purpose**: Ensure constitutional compliance for data integrity, traceability, and artifact versioning.

- [X] T060 Compute SHA256 checksum for the raw dataset file generated by T008 (e.g., `data/raw/hea_raw.parquet`) and record it in `state/projects/PROJ-418-predicting-the-yield-strength-of-high-en.yaml` under key `"artifact_hashes"`. **CRITICAL**: If T008 returns `NO_DATA`, write `null` for the checksum. **Depends on T008**.

- [X] T061 Compute SHA256 checksum for the processed descriptor file `data/processed/hea_descriptors.csv` and record it in `state/projects/PROJ-418-predicting-the-yield-strength-of-high-en.yaml` under key `"artifact_hashes"`. **Depends on T015**.

- [X] T062 Generate provenance metadata linking every figure in `output/plots/`, every metric in `output/metrics.json`, and the final report to their originating data rows and code modules. Store as `output/provenance.json`. **Depends on T028**.

- [X] T063 Compute content‑hashes (e.g., SHA256) for all major artifacts (code files, data files, JSON reports, plots) and update the project's state file `state/projects/PROJ-418-predicting-the-yield-strength-of-high-en.yaml` under the `artifact_hashes` map. **Depends on T060, T061, T062**.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031a [P] Update `README.md` with installation steps, usage instructions, and data source requirements. **Implementation**: Generate a comprehensive README.md file based on the spec's FR‑012 requirements, including environment setup, data source details, and usage examples.
- [X] T031b [P] Update `quickstart.md` with a step‑by‑step walkthrough of the pipeline execution. **Implementation**: Generate a quickstart.md file based on FR‑013, providing a clear, numbered guide to running the pipeline from start to finish.
- [X] T032a Run `ruff check` and fix all linting errors in `code/`
- [X] T032b Run `black` and format all Python files in `code/`
- [X] T034 [P] Unit tests for descriptor math in `tests/unit/test_descriptors.py`
- [X] T035 [P] Integration tests for full pipeline in `tests/integration/test_pipeline.py`
- [X] T036 Run quickstart.md validation. **Implementation**: Execute the steps in `quickstart.md` in a clean environment. Capture the output and generate `output/quickstart_validation_report.json` containing: `{ "status": "success|failure", "steps_executed": int, "errors": [], "timestamp": str }`. This satisfies SC‑007.

---

## Phase 7: Execution & Verification (Critical Path)

**Purpose**: Ensure the pipeline executes correctly with real data and produces verified results.

- [X] T037 [US1] Verify data acquisition: Execute `code/data/download.py` and confirm it returns `SUCCESS` or `NO_DATA` status without crashing. **Deliverable**: Log output showing status code and any attempted URLs. **Depends on T008**.
- [X] T038 [US1] Verify data processing: Execute `code/data/pipeline.py` and confirm `output/data_status.json` exists with valid schema (count, count_warning, power_status). **Deliverable**: `output/data_status.json` file. **Depends on T037**.
- [X] T039 [US2] Verify model training: Execute `code/models/train.py` and confirm `output/metrics.json` exists with R², MAE, RMSE for all models and `best_model` key. **Deliverable**: `output/metrics.json` file. **Depends on T038**.
- [X] T040 [US3] Verify statistical validation: Execute `code/models/evaluate.py` and confirm `output/vif_results.json`, `output/permutation_results.json`, `output/bootstrap_results.json`, and `output/sensitivity_results.json` exist with valid schemas. **Deliverable**: All four JSON files. **Depends on T039**.
- [ ] T041 [Cross‑Cutting] Verify final report: Execute report generation and confirm `output/report.md` exists, contains the mandatory disclaimer string, and includes the "Data Limitation Warning" section if `count_warning` is true. **Deliverable**: `output/report.md` file. **Depends on T040**.

---

## Phase 8: Documentation & Specification Alignment

**Purpose**: Resolve the mismatches identified between `spec.md` and `plan.md`.

- [ ] T048 [P] Update `spec.md` (User Story 2 and FR-005) to replace the "disjoint elemental sets" requirement with "Stratified by Elemental Ratios" to match the Plan's feasibility decision. **Deliverable**: Updated `spec.md`.
- [ ] T049 [P] Update `plan.md` to remove the adaptive permutation‑count logic and state that **a large number of permutations** must be performed for all permutation‑importance tests, as required by FR-006.
- [ ] T050 [P] Add a brief note to `spec.md` (in the "Assumptions" section) clarifying that the adaptive permutation count is **not** permitted; the implementation must always run 1000 permutations. This keeps the spec truthful while documenting the agreed‑upon change.

---

## Phase 9: Additional Housekeeping

- Ensure all tasks marked with [P] can be parallelized where file independence permits.
- All JSON/YAML artifacts must conform to the schemas defined in `contracts/`.
- All scripts must pin random seeds (`numpy`, `random`, `torch` if used) for reproducibility.