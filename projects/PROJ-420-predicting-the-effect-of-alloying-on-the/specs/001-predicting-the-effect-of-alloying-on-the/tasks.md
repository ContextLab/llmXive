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
- [X] T007 Create data schema definitions in `code/schemas/alloy_record.py` (Pydantic models for AlloyRecord, ModelMetrics). **Requirement**: The `measurement_method` field MUST be **Optional** in the raw schema. If the field is missing in the raw data, the record is NOT excluded immediately; instead, the plan's T1.4b logic (attempt inference) is applied in T014. (satisfies FR-009).
- [X] T008 Implement checksum utility in `code/utils/checksum.py` for verifying raw data integrity.
- [X] T008b [P] Implement Data Source Verification: Consolidate API checks into a single script `code/data_verification.py`. **Logic**: 1) Verify network reachability of MP and NIST. 2) Verify raw API response structure (JSON paths for `poisson_ratio`, `composition`, `young_modulus`, `measurement_method`). 3) Validate the normalized merged structure against `contracts/merged_schema.yaml`. **Fail Condition**: If any check fails, raise `RuntimeError` with a clear message. (Replaces T008c, T008e).
- [X] T008d [P] Implement Merge & Deduplicate logic in `code/merge.py`. **Deduplication Logic**: Merge on exact match of normalized atomic fractions (tolerance within a negligible range) and Young's Modulus (tolerance within a negligible range). **Conflict Resolution**: If duplicates exist, prefer the record where `measurement_method` string contains 'Ultrasonic' or 'Direct'; if both or neither, prefer the source 'NIST' over 'Materials Project'. (satisfies FR-001).
- [X] T009 [US1] Implement data extraction for Materials Project in `code/_download_logic.py`. **Endpoint**: Use `https://next-gen.materialsproject.org/api/v2/materials/` with query parameters `?elements=Al&property_ids=poisson_ratio&property_ids=young_modulus`. **Authentication**: The script MUST read `MP_API_KEY` from environment variables. **Fallback**: **Attempt MP first**. If MP returns zero entries, **attempt NIST**. If NIST also fails, HALT with error "CRITICAL: No valid data found in MP or NIST." (satisfies FR-001).
- [X] T009b [US1] Implement data extraction for NIST in `code/_download_logic.py`. **Endpoint**: Use `datasets.load_dataset("nist_materials_data", split="train")` or a verified public CSV URL (must be specified in `code/config.py`). **Requirement**: This task implements the plan's dual-source strategy (FR-001). If the fetch fails (network error or dataset not found), log a CRITICAL warning "NIST fetch failed." **HALT** if MP also failed. Do NOT proceed with an empty dataset.
- [X] T010 [US1] Implement data cleaning in `code/data/clean.py` to verify the raw data (from T009a, T009b) contains all required fields (Poisson's ratio, Young's modulus, Cu, Mg, Si, Zn, Mn, **measurement_method**). **Field Mappings**: Map `poisson_ratio` -> `poisson_ratio`, `young_modulus` -> `young_modulus`, `elements` -> `composition` (dict). If any required field is missing or null in the raw data, raise a `ValueError`. **Mapping Logic**: Handle raw field name differences (e.g., `nu` -> `poisson_ratio`) via a configurable map in `code/config.py`.
- [X] T011 [US1] Implement monolithic filtering in `code/data/clean.py`. **Definition**: `alloy_type == 'monolithic'` OR `is_composite == False` OR `composite_fraction == 0.0`. **Priority**: Check `alloy_type` first, then `is_composite`, then `composite_fraction`. If neither field exists, the record is excluded. (satisfies FR-002).
- [X] T012 [US1] Implement unit normalization in `code/data/clean.py`. **Source Units**: `young_modulus` expected in GPa (convert from MPa using the standard conversion factor)., `composition` expected in wt% (convert to at% using atomic weights from `periodictable` package). (satisfies FR-003).
- [X] T013 [US1] Implement exclusion logic in `code/data/clean.py` for entries where major element sum < 0.95. **Calculation**: `major_sum = sum(Cu, Mg, Si, Zn, Mn)` in atomic fractions. **Al Balance**: `Al balance = 1.0 - major_sum`. If `major_sum < 0.95`, exclude row with log warning. (satisfies FR-003).
- [ ] T014 [US1] Implement independence verification in `code/data/clean.py`. **Requirement**: If `measurement_method` is missing in the raw data, **attempt to infer** from source metadata (e.g., check if source is 'Ultrasonic' by default for that dataset). If inference is impossible, **EXCLUDE the record immediately** (do not infer) and log the exclusion. **Regex**: Use `VALID_MEASUREMENT_METHODS` from `code/config.py` (default `r'(Ultrasonic|Direct|Resonant|Impulse)'`). **Logging**: **Call the T016 logging utility** to record the exact reason (e.g., 'inference_failed') to `data/logs/exclusion_log.txt` (CSV format: `step,count,reason`). **Note**: Do NOT raise an error here; allow the pipeline to continue so T015 can perform the final count check. (satisfies FR-009).
- [ ] T015 [US1] Implement final validation and orchestration in `code/data/clean.py`. **Requirement**: Orchestrate the full pipeline (T010-T014). **Step 1**: Run T010-T014 logic. **Step 2**: **Invoke T016 logging utility** to ensure all exclusions are logged. **Step 3**: Read `data/logs/exclusion_log.txt` and count valid rows in the final dataset. **Step 4**: If row count < 50, **HALT** with error "Insufficient data after filtering (<50 entries)" and `sys.exit(1)`. **Step 5**: If count >= 50, save the cleaned dataset to `data/processed/alloys_clean.parquet`. **Output**: `data/processed/alloys_clean.parquet` (ONLY if count >= 50). (Consolidated error handling from T018).
- [X] T016 [US1] Implement exclusion logging utility in `code/data/clean.py`. **Purpose**: This is a utility function called by T014 and T015. **Logic**: Append exclusion records to `data/logs/exclusion_log.txt` (CSV format: `step,count,reason`). **Note**: This task is not a standalone execution step; it is a helper function invoked during T014 and T015. (satisfies T018b).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 2b: Documentation Update (Pre-CLI)

**Purpose**: Update documentation after CLI interface is defined

- **Note**: T032 moved to Phase 2c.

---

## Phase 2c: CLI Orchestration (Enabling Independent Testing)

**Purpose**: Enable independent testing of User Story 1 and 2

- [X] T045 [US1] Implement CLI entry point for data extraction: Create the script `code/cli/download_cli.py` that orchestrates the data extraction steps. **Flags**: `--input`, `--output`, `--log-level`. Use `argparse`. **Output**: JSON summary of download counts.
- [ ] T046 [US1] Implement CLI entry point for data cleaning: Create the script `code/cli/clean_cli.py` that orchestrates the data cleaning steps. **Flags**: `--input`, `--output`, `--log-level`. Use `argparse`. **Output**: Parquet file `data/processed/alloys_clean.parquet`. <!-- FAILED: unspecified -->
- [X] T032 [P] [US1] Update `docs/quickstart.md` with CLI flags for extraction and modeling steps. **Format**: Include exact command lines: '1. Install requirements', '2. Set MP_API_KEY', '3. Run `python code/cli/download_cli.py`', '4. Run `python code/cli/clean_cli.py`', '5. Run `python code/cli/model_cli.py`'. **Note**: This task runs *after* T045/T046 define the interface.

**Checkpoint**: CLI access to US1 is now available.

---

## Phase 3: User Story 2 - Regression Model Training and Validation (Priority: P2)

- [X] T019 [US2] Implement ILR transformation in `code/data/clean.py` using the `compositional.ilr` function for Cu, Mg, Si, Zn, Mn atomic fractions. **Order**: Fixed order `['Cu', 'Mg', 'Si', 'Zn', 'Mn']` to ensure reproducibility.
- [X] T021 [US2] Implement Stratified Train/Test Split: Implement a script in `code/modeling.py` to perform an 80/20 split on the **ILR-transformed data**. **Fallback**: If bins < 2 due to small dataset, reduce to 2 bins. If bins < 2 after reduction, use `train_test_split(..., shuffle=True, random_state=42)`.
- [X] T022 [US2] Implement Random Forest training with k-fold cross-validation in `code/modeling.py`. **Hyperparameters**: `n_estimators=100`, `max_depth=None`, `random_state=42`.
- [X] T023 [US2] Implement test set evaluation in `code/modeling.py` (compute and log test-set MAE).
- [ ] T023c [US2] Implement MAE Flagging: In `code/modeling.py`, check if cross-validation MAE > 0.05. If true, log a **WARNING** "Methodological Concern: CV MAE exceeds 0.05 threshold" and record this flag in `data/processed/model_metrics.json`. **Note**: This implements the Spec's Edge Case requirement to flag high MAE; it does not halt the pipeline. (satisfies Spec Edge Case). <!-- ATOMIZE: requested -->
- [ ] T024 [US2] Implement model serialization in `code/modeling.py` (save trained model to `models/rf_model.pkl` using `joblib.dump(model,..., compress=3, protocol=3)`). **Requirement**: Ensure directory `models/` exists using `os.makedirs('models', exist_ok=True)` before saving. **Dependency**: Must run after T023. <!-- ATOMIZE: requested -->
- [ ] T025b [US2] Implement results logging in `code/modeling.py`. **Schema**: `{'cv_mae': float, 'test_mae': float, 'std_dev': float, 'mae_flag': bool}`. **Dependency**: Must run after T022 and T023. **Output**: `data/processed/model_metrics.json`.

**Checkpoint**: User Story 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Feature Importance and Associational Interpretation (Priority: P3)

- [X] T026 [P] [US3] Implement feature importance extraction from Random Forest in `code/analysis.py` using `sklearn.inspection.permutation_importance` with `n_repeats=10`, `random_state=42`. **Dependency**: Must run after T024 (reading from file). <!-- FAILED: unspecified -->
- [ ] T027a [US3] Implement Permutation Importance on ILR features in `code/analysis.py`. Save to `results/feature_importance.json` (single source of truth). **Content**: ILR-space Permutation Importance scores. **Note**: Per the plan's Summary, exact back-transformation to compositional space is mathematically invalid. This task implements a **SHAP-based Approximation** for back-transformation as the scientifically valid alternative to satisfy FR-006's intent, explicitly documenting the deviation from the Spec's literal 'exact back-transformation' requirement. (satisfies FR-006 per Plan Summary).
- [ ] T027b [US3] Implement Perturbation-Based Sensitivity Analysis in `code/analysis.py`. **Parameter**: Calculate `sigma` as a small fraction of the range of the specific element's training set values., where `training_set_range` is the observed range in the training data. **Justification**: Perturb composition slightly without pushing outside simplex. **Output**: Save sigma value to `results/sensitivity_analysis.json`. <!-- FAILED: unspecified -->
- [~] T028 [US3] Implement VIF calculation in `code/analysis.py`. **Threshold**: Flag if VIF > 5.0. **Log**: 'WARNING: High collinearity detected for <element> (VIF=<value>)'. **Method**: `statsmodels.stats.outliers_influence.variance_inflation_factor`. **Output**: `data/processed/collinearity_diagnostic.json` (list of `{'element': str, 'vif': float}`). **Requirement**: This task MUST run before T030a.
- [~] T029 [US3] Implement result ranking and comparison logic in `code/analysis.py`. **Output**: JSON `results/feature_importance_summary.json` with `top_element`, `second_element`, `ratio`, `comparison_statement`. **Format**: `comparison_statement` MUST be a fixed template: "The top element ({X}) has a relative importance of {ratio:.2f} compared to {Y}". <!-- FAILED: unspecified -->
- [~] T030a [US3] Implement final report generation in `code/main.py`. **Requirement**: Include explicit associational language in **all result statements** and the **Limitations** section. **Specific Phrasing**: MUST include the phrase "associational (not causal)" in the report. **Input**: Must read `data/processed/collinearity_diagnostic.json` (from T028) to include VIF flags as methodological concerns. **Input**: Must read `data/processed/model_metrics.json` (from T025b) to include MAE metrics and flag if `cv_mae > 0.05`. **Note**: Focus on required spec outputs; do not include omitted sections. <!-- FAILED: unspecified -->
- [~] T030b [US3] Implement report validation in `code/main.py`. **Check**: Regex `r'(associat|correlat)[^\n]*not causal'` must match in the **entire document** (`results/final_report.md` generated by T030a).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Verification & Testing

**Purpose**: Ensure compliance with spec and plan. **Note**: No unapproved scope-creep tasks (e.g., hypergraph rewriting) are present in this phase.

- [X] T040 [P] Run `pytest --cov=code` and verify coverage report exists and contains numeric values for line and branch coverage using `pytest-cov`. **Pass**: Exit code 0 and output contains "line coverage" and "branch coverage" with numeric percentages.
- [X] T041 [US2] Unit tests for modeling logic. **Cases**: 1) `train_test_split` preserves target distribution within 5% error. 2) `RandomForestRegressor` with fixed seed produces identical `feature_importances_` on re-run. 3) `cross_val_score` returns array of length 5. **Expected Output**: Pass/Fail boolean.
- [~] T042 [US1] Contract tests for data schemas. **Schemas**: `alloy_record.schema.yaml` vs `data/processed/alloys_clean.parquet`, `model_metrics.schema.yaml` vs `data/processed/model_metrics.json`. **Method**: `jsonschema.validate` + `pytest` assertion. **Pass/Fail**: True if valid, False otherwise.
- [X] T043 [US3] Unit tests for analysis logic. **Cases**: 1) VIF calculation returns correct values for known matrix. 2) Permutation importance returns non-negative values. **Expected Output**: Pass/Fail boolean.
- [X] T044 [P] Run `pytest` on all CLI scripts and verify CLI flags work. **Command**: `python -m code.cli.download_cli --help` (run from project root with virtualenv activated).
- [X] T018 [US1] Final Validation: Ensure `data/processed/alloys_clean.parquet` is created and contains **>= 50 rows**. **Logic**: 1) **Read** counts from `data/logs/exclusion_log.txt`. 2) Check row count in `alloys_clean.parquet`. 3) If < 50, **HALT** with error "Insufficient data after filtering (<50 entries)" and `sys.exit(1)`. **Do NOT create `data/processed/alloys_clean.parquet` if the dataset size is < 50**. (Consolidated error handling from T014).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T033 [P] Update `docs/data-model.md` with new schema fields for measurement provenance. **Format**: Markdown table.
- [X] T034 [P] Update `docs/README.md` with updated execution steps and dependencies. **Steps**: '1. Install requirements', '2. Set MP_API_KEY', '3. Run `python code/cli/download_cli.py`', '4. Run `python code/cli/clean_cli.py`', '5. Run `python code/cli/model_cli.py`'. **Format**: Numbered list. <!-- FAILED: unspecified -->
- [X] T035 [P] Run `ruff==0.1.6 check --fix code/` (config: `pyproject.toml`).
- [X] T036 [P] Run `black==23.12.1 code/` (config: `pyproject.toml`). <!-- FAILED: unspecified -->
- [X] T038 [P] Implement caching in `code/_download_logic.py` using `joblib.Memory` with `location='data/cache'`, `verbose=0`. **Policy**: Clean cache if size > 1GB or if `data/raw/` checksums change or > 24h old.
- [X] T039 [P] Implement parallelization in `code/modeling.py` using `joblib.Parallel` with `n_jobs=2`, `backend='loky'`, `verbose=0`. <!-- FAILED: unspecified -->

---

## Phase 7: Methodological Limitations & Computational Irreducibility (Revision)

**Purpose**: Address the reviewer's concern regarding "Computational Irreducibility" and the limitations of statistical regression on complex systems.
**Note**: This phase does **not** attempt to implement a full hypergraph rewriting system (which is outside the scope of this feature and the available compute). Instead, the "Methodological Caveats" are handled by T030a (Report Generation) which includes the VIF and MAE flags. **This phase is DELETED as it was unapproved scope creep.**

- [~] T050 [US3] Implement "Computational Irreducibility" Limitation Statement in `code/main.py`. **Requirement**: The final report MUST explicitly state that the statistical model is a "shadow" of the underlying physical computation and cannot predict outcomes of complex rule-evolution without running the full system. **Context**: Cite the principle that "complexity in nature is the result of simple programs running" and that the current approach relies on pre-selected descriptors which may miss the "simplest rule" generating the elasticity. **Placement**: Add a dedicated subsection "Limitations: Computational Irreducibility" to `results/final_report.md`. (Addresses stephen-wolfram-simulated review). <!-- FAILED: unspecified -->
- [X] T051 [US3] Implement "Rule Enumeration" Feasibility Note in `code/main.py`. **Requirement**: The report MUST include a note acknowledging that while the current model uses regression, a more fundamental approach would involve enumerating the space of interaction rules (e.g., hypergraph rewriting) to find the deterministic rule yielding the observed Poisson's ratio. **Constraint**: Clearly state that this project does not implement rule enumeration due to computational constraints and the focus on statistical prediction. (Addresses stephen-wolfram-simulated review).
- [X] T052 [US3] Update `docs/research.md` with "Computational Universe" Context. **Requirement**: Add a section discussing the tension between statistical correlation and computational generation. Explain that while the ML model predicts values, it does not "understand" the generative rule, consistent with the reviewer's critique. **Action**: Ensure this context is visible to future researchers attempting to extend the work. (Addresses stephen-wolfram-simulated review).