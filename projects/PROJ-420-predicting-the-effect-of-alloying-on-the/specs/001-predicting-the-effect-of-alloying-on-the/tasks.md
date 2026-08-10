# Tasks: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

**Input**: Design documents from `/specs/001-predict-poissons-ratio/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

 Tasks MUST be organized by user story so each user story can be independently implemented
 and tested.

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python 3.11 project with dependencies (pandas, numpy, scikit-learn, requests, pyyaml, seaborn, matplotlib, compositional, statsmodels, materialsproject, datasets, periodictable, joblib, pytest, pytest-cov, ruff, black) in `code/requirements.txt`.
- [X] T003 [P] Configure linting (ruff==0.1.6) and formatting (black==23.12.1) tools in `code/` using `pyproject.toml` as the configuration source.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/__init__.py` and basic project scaffolding
- [X] T005 [P] Setup environment configuration management in `code/config.py` (loading `data/`, `models/` paths, random seeds, `VALID_MEASUREMENT_METHODS` regex list).
- [X] T006 [P] Implement logging infrastructure in `code/logging_config.py` (JSON logging, error levels).
- [X] T007 Create data schema definitions in `code/schemas/alloy_record.py` (Pydantic models for AlloyRecord, ModelMetrics). **Requirement**: The `measurement_method` field MUST be **Optional** in the raw schema. If the field is missing in the raw data, the record is excluded immediately in T014 before final schema validation. (satisfies FR-009).
- [X] T008 Implement checksum utility in `code/utils/checksum.py` for verifying raw data integrity.
- [X] T008b [P] Verify data source accessibility and semantic validity: Implement a script in `code/data_verification.py` to verify the accessibility of the target Materials Project and NIST APIs. Check network reachability AND verify that the API returns a valid data structure matching the expected schema (semantic verification). **Schema Check**: The API response MUST include the `measurement_method` field (as float/string) and the composition fields (Cu, Mg, Si, Zn, Mn). If the API is unreachable, returns invalid data, or lacks required fields, raise a `RuntimeError`.
- [X] T008c [P] Validate Normalized Schema: Implement a script to fetch the *normalized* merged data structure and validate it against `contracts/merged_schema.yaml` using the `jsonschema` library. **Validation Target**: Validate the Python dictionary representing the normalized record, not the raw API wrapper. If the schema does not match, raise a `RuntimeError`. **Note**: `contracts/merged_schema.yaml` must be created to reflect the raw/merged state (before cleaning).
- [X] T008d [P] Implement Merge & Deduplicate logic in `code/merge.py`. **Deduplication Logic**: Merge on exact match of normalized atomic fractions (tolerance 1e-6) and Young's Modulus (tolerance 1e-3 GPa). **Conflict Resolution**: If duplicates exist, prefer the record where `measurement_method` string contains 'Ultrasonic' or 'Direct'; if both or neither, prefer the source 'NIST' over 'Materials Project'. (satisfies FR-001).
- [X] T008e [P] Verify raw API schema: Implement a pre-download check in `code/data_verification.py` to verify the *raw* API response structure. **Check**: Verify the JSON path `$.data.properties.poisson_ratio` (float), `$.data.composition.elements` (dict), and `$.data.properties.young_modulus` (float) exist. If the `measurement_method` field is expected in the raw schema, verify its presence. Raise `RuntimeError` if missing.
- [X] T009 [US1] Implement data extraction for Materials Project in `code/_download_logic.py`. **Endpoint**: Use `https://next-gen.materialsproject.org/api/v2/materials/` with query parameters `?elements=Al&property_ids=poisson_ratio&property_ids=young_modulus`. **Authentication**: The script MUST read `MP_API_KEY` from environment variables. **Fallback**: **Attempt MP first**. If MP returns zero entries, **attempt NIST**. If NIST also fails, HALT with error "CRITICAL: No valid data found in MP or NIST." (satisfies FR-001).
- [X] T009b [US1] Implement data extraction for NIST in `code/_download_logic.py`. **Endpoint**: Use `datasets.load_dataset("nist_materials_data", split="train")` or a verified public CSV URL (must be specified in `code/config.py`). **Requirement**: This task implements the plan's dual-source strategy (FR-001). If the fetch fails (network error or dataset not found), log a CRITICAL warning "NIST fetch failed." **HALT** if MP also failed. Do NOT proceed with an empty dataset.
- [X] T010 [US1] Implement data cleaning in `code/data/clean.py` to verify the raw data (from T009a, T009b) contains all required fields (Poisson's ratio, Young's modulus, Cu, Mg, Si, Zn, Mn, **measurement_method**). **Field Mappings**: Map `poisson_ratio` -> `poisson_ratio`, `young_modulus` -> `young_modulus`, `elements` -> `composition` (dict). If any required field is missing or null in the raw data, raise a `ValueError`. **Mapping Logic**: Handle raw field name differences (e.g., `nu` -> `poisson_ratio`) via a configurable map in `code/config.py`.
- [X] T011 [US1] Implement monolithic filtering in `code/data/clean.py`. **Definition**: `alloy_type == 'monolithic'` OR `is_composite == False` OR `composite_fraction == 0.0`. **Priority**: Check `alloy_type` first, then `is_composite`, then `composite_fraction`. If neither field exists, the record is excluded. (satisfies FR-002).
- [X] T012 [US1] Implement unit normalization in `code/data/clean.py`. **Source Units**: `young_modulus` expected in GPa (convert MPa by /1000), `composition` expected in wt% (convert to at% using atomic weights from `periodictable` package). (satisfies FR-003).
- [X] T013 [US1] Implement exclusion logic in `code/data/clean.py` for entries where major element sum < 0.95. **Calculation**: `major_sum = sum(Cu, Mg, Si, Zn, Mn)` in atomic fractions. **Al Balance**: `Al balance = 1.0 - major_sum`. If `major_sum < 0.95`, exclude row with log warning. (satisfies FR-003).
- [X] T014 [US1] Implement independence verification in `code/data/clean.py`. **Requirement**: If `measurement_method` is missing in the raw data, **EXCLUDE the record immediately** (do not infer). Log the exclusion. **Regex**: Use `VALID_MEASUREMENT_METHODS` from `code/config.py` (default `r'(Ultrasonic|Direct|Resonant|Impulse)'`). (satisfies FR-009). **Logging**: Log exact counts of excluded records to `data/logs/exclusion_log.txt` (CSV format: `step,count,reason`).
- [X] T015 [US1] Implement final validation and orchestration in `code/data/clean.py` (run full pipeline -> save `data/processed/alloys_clean.parquet`).
- [X] T016 [US1] Implement exclusion logging in `code/data/clean.py`. **Requirement**: Log exact counts of excluded records at each step (e.g., 'Excluded 12 due to missing Poisson', 'Excluded 5 due to sum < 0.95') to `data/logs/exclusion_log.txt` (CSV format). (satisfies T018b).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 2b: Documentation Update (Pre-CLI)

**Purpose**: Update documentation after CLI interface is defined

- [X] T032 [P] Update `docs/quickstart.md` with CLI flags for extraction and modeling steps. **Format**: Include exact command lines: '1. Install requirements', '2. Set MP_API_KEY', '3. Run `python code/cli/download_cli.py`', '4. Run `python code/cli/clean_cli.py`', '5. Run `python code/cli/model_cli.py`'. **Note**: This task runs *after* T045/T046 define the interface.

---

## Phase 2c: CLI Orchestration (Enabling Independent Testing)

**Purpose**: Enable independent testing of User Story 1 and 2

- [X] T045 [US1] Implement CLI entry point for data extraction: Create the script `code/cli/download_cli.py` that orchestrates the data extraction steps. **Flags**: `--input`, `--output`, `--log-level`. Use `argparse`. **Output**: JSON summary of download counts.
- [X] T046 [US1] Implement CLI entry point for data cleaning: Create the script `code/cli/clean_cli.py` that orchestrates the data cleaning steps. **Flags**: `--input`, `--output`, `--log-level`. Use `argparse`. **Output**: Parquet file `data/processed/alloys_clean.parquet`.

**Checkpoint**: CLI access to US1 is now available.

---

## Phase 3: User Story 2 - Regression Model Training and Validation (Priority: P2)

- [X] T019 [US2] Implement ILR transformation in `code/data/clean.py` using the `compositional.ilr` function for Cu, Mg, Si, Zn, Mn atomic fractions. **Order**: Fixed order `['Cu', 'Mg', 'Si', 'Zn', 'Mn']` to ensure reproducibility.
- [X] T021 [US2] Implement Stratified Train/Test Split: Implement a script in `code/modeling.py` to perform an 80/20 split on the **ILR-transformed data**. **Fallback**: If bins < 2 due to small dataset, reduce to 2 bins. If bins < 2 after reduction, use `train_test_split(..., shuffle=True, random_state=42)`.
- [X] T022 [US2] Implement Random Forest training with k-fold cross-validation in `code/modeling.py`. **Hyperparameters**: `n_estimators=100`, `max_depth=None`, `random_state=42`.
- [X] T023 [US2] Implement test set evaluation in `code/modeling.py` (compute and log test-set MAE).
- [X] T023b [US2] Implement results logging and flagging in `code/modeling.py`. **Threshold**: Flag 'methodological_concern' if `cv_mae > 0.5 * std(target)`. **Output**: Write explanation to `results/final_report.md` (must include the flag text).
- [X] T024 [US2] Implement model serialization in `code/modeling.py` (save trained model to `models/rf_model.pkl` using `joblib.dump(model, ..., compress=3, protocol=3)`).
- [X] T025b [US2] Implement results logging in `code/modeling.py`. **Schema**: `{'cv_mae': float, 'test_mae': float, 'std_dev': float}`.

**Checkpoint**: User Story 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Feature Importance and Associational Interpretation (Priority: P3)

- [X] T026 [P] [US3] Implement feature importance extraction from Random Forest in `code/analysis.py` using `sklearn.inspection.permutation_importance` with `n_repeats=10`, `random_state=42`.
- [X] T027a [US3] Implement Permutation Importance on ILR features in `code/analysis.py`. Save to `results/feature_importance.json` (single source of truth). **Content**: ILR-space Permutation Importance scores.
- [X] T027b [US3] Implement Perturbation-Based Sensitivity Analysis in `code/analysis.py`. **Parameter**: `sigma=0.01` ([deferred] of the **training set's observed range** for the specific element). **Justification**: Perturb composition slightly without pushing outside simplex. **Output**: Log sigma value in report.
- [X] T028 [US3] Implement VIF calculation in `code/analysis.py`. **Threshold**: Flag if VIF > 5.0. **Log**: 'WARNING: High collinearity detected for <element> (VIF=<value>)'. **Method**: `statsmodels.stats.outliers_influence.variance_inflation_factor`. **Output**: `data/processed/collinearity_diagnostic.json` (list of `{'element': str, 'vif': float}`).
- [X] T029 [US3] Implement result ranking and comparison logic in `code/analysis.py`. **Output**: JSON `results/feature_importance_summary.json` with `top_element`, `second_element`, `ratio`, `comparison_statement`. **Report**: Include sentence 'The top element ({X}) has a relative importance of {ratio:.2f} compared to {Y}'.
- [X] T030a [US3] Implement final report generation in `code/main.py`. **Requirement**: Include explicit associational language in **all result statements** and the **Limitations** section. **Note**: Section 7 (Computational Irreducibility) is omitted due to scope constraints.
- [X] T030b [US3] Implement report validation in `code/main.py`. **Check**: Regex `r'(associat|correlat)[^\n]*not causal'` must match in the **entire document**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Verification & Testing

**Purpose**: Ensure compliance with spec and plan. **Note**: No unapproved scope-creep tasks (e.g., hypergraph rewriting) are present in this phase.

- [X] T040 [P] Run `pytest --cov=code` and verify coverage report shows **[deferred] line coverage and [deferred] branch coverage** using `pytest-cov`.
- [X] T041 [US2] Unit tests for modeling logic. **Cases**: 1) `train_test_split` preserves target distribution within 5% error. 2) `RandomForestRegressor` with fixed seed produces identical `feature_importances_` on re-run. 3) `cross_val_score` returns array of length 5. **Expected Output**: Pass/Fail boolean.
- [X] T042 [US1] Contract tests for data schemas. **Schemas**: `alloy_record.schema.yaml` vs `data/processed/alloys_clean.parquet`, `model_metrics.schema.yaml` vs `data/processed/model_metrics.json`. **Method**: `jsonschema.validate` + `pytest` assertion. **Pass/Fail**: True if valid, False otherwise.
- [X] T043 [US3] Unit tests for analysis logic. **Cases**: 1) VIF calculation returns correct values for known matrix. 2) Permutation importance returns non-negative values. **Expected Output**: Pass/Fail boolean.
- [X] T044 [P] Run `pytest` on all CLI scripts and verify CLI flags work. **Command**: `python -m code.cli.download_cli --help` (run from project root with virtualenv activated).
- [X] T018 [US1] Final Validation: Ensure `data/processed/alloys_clean.parquet` is created and contains **>= 50 rows**. **Failure Condition**: If valid entries < 50, **HALT** with error "Insufficient data after filtering (<50 entries)". **Do NOT create `data/processed/alloys_clean.parquet` if the dataset size is < 50**.
- [X] T018b [US1] Implement exclusion logging in `code/data/clean.py`. **Requirement**: Log exact counts of excluded records at each step (e.g., 'Excluded 12 due to missing Poisson', 'Excluded 5 due to sum < 0.95') to `data/logs/exclusion_log.txt` (CSV format: `step,count,reason`). **Order**: Log **before** the HALT check in T018.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T033 [P] Update `docs/data-model.md` with new schema fields for measurement provenance. **Format**: Markdown table.
- [X] T034 [P] Update `docs/README.md` with updated execution steps and dependencies. **Steps**: '1. Install requirements', '2. Set MP_API_KEY', '3. Run `python code/cli/download_cli.py`', '4. Run `python code/cli/clean_cli.py`', '5. Run `python code/cli/model_cli.py`'. **Format**: Numbered list.
- [X] T035 [P] Run `ruff==0.1.6 check --fix code/` (config: `pyproject.toml`).
- [X] T036 [P] Run `black==23.12.1 code/` (config: `pyproject.toml`).
- [X] T038 [P] Implement caching in `code/_download_logic.py` using `joblib.Memory` with `location='data/cache'`, `verbose=0`. **Policy**: Clean cache if size > 1GB or if `data/raw/` checksums change or > 24h old.
- [X] T039 [P] Implement parallelization in `code/modeling.py` using `joblib.Parallel` with `n_jobs=2`, `backend='loky'`, `verbose=0`.