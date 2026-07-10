# Tasks: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

**Input**: Design documents from `/specs/001-predict-elastic-modulus/`
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
- Paths shown below assume single project - adjust based on plan.md structure

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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Research Validation & Data Verification

**Purpose**: Validate citations and verify data availability before any implementation begins.

- [X] T001 [P] Run Reference-Validator Agent on `research.md` citations using command `python -m code.utils.reference_validator --input research.md --output results/validation_report.json`. Fail if exit code != 0. (Constitution Principle II).
- [ ] T002 [P] Create project structure per implementation plan (`src/`, `tests/`, `data/raw/`, `data/processed/`, `results/`)
- [ ] T003 [P] Initialize Python 3.11 project with dependencies: `pandas>=2.0`, `scikit-learn>=1.3`, `numpy>=1.24`, `requests>=2.31`, `pyyaml>=6.0`, `shap>=0.44`, `scipy>=1.11`, `pymatgen>=2023`, `pytest>=7.4` (CPU-only, 2 cores, 7GB RAM constraints)
- [ ] T004 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Implement seed management in `src/utils/seeds.py` (pinning all random seeds for reproducibility)
- [ ] T007 Create `src/utils/data_fetch.py` for handling API retries and raw data download logic
- [ ] T008 Implement `src/utils/validators.py` for data integrity checks (sum=1.0, sample count thresholds)
- [~] T009 Setup logging infrastructure in `src/utils/logging_config.py`
- [~] T010 Create `src/models/hea_sample.py` defining the HEA Sample entity structure

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Ingestion and Feature Engineering Pipeline (Priority: P1) 🎯 MVP

**Goal**: Retrieve HEA data from OQMD/MP, filter for ≥5 elements, normalize, and compute descriptors (ILR for linear models) to produce a clean CSV.

**Independent Test**: The pipeline runs on a subset, producing `data/processed/hea_features.csv` with no NaN values and correct ILR transformation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T011 [P] [US1] Unit test for normalization logic in `tests/unit/test_normalization.py`
- [~] T012 [P] [US1] Unit test for ILR transformation in `tests/unit/test_coda.py`
- [~] T013 [P] [US1] Integration test for data fetch in `tests/integration/test_data_fetch.py`

### Implementation for User Story 1

- [~] T014 [US1] Implement OQMD data fetcher in `src/data/fetch_oqmd.py` (using verified URL from `data/source_metadata.yaml`); **explicitly apply '≥5 principal elements' filter at the API query level or immediately post-fetch** to minimize memory usage.
- [~] T015 [US1] Implement Materials Project fetcher in `src/data/fetch_mp.py` (with API key check); **explicitly apply '≥5 principal elements' filter at the API query level or immediately post-fetch** to minimize memory usage.
- [~] T016 [US1] Implement filtering logic: retain samples with ≥5 principal elements and valid Bulk Modulus in `src/data/filter.py`
- [ ] T016.5 [US1] Implement **Reduced Power Analysis** logic in `src/data/power_analysis.py`: if API sample count < 500, DO NOT halt. Instead, generate an 'Underpowered Study Report' that quantifies the power deficit and confidence interval widening. Log the merge (if literature fallback is used) and proceed with available data, explicitly flagging the reduced power in all downstream outputs.
- [~] T017 [US1] Implement normalization step: enforce sum(composition)=1.0 and log adjustments in `src/data/normalize.py`
- [~] T018 [US1] Implement descriptor calculation in `src/features/descriptors.py`. **Explicitly compute the following Miedema-derived features to form the `$MIEDEMA_FEATURES$` set**:
 1. `mixing_enthalpy_miedema` (Mixing Enthalpy via Miedema's model)
 2. `atomic_radius_variance_miedema` (Atomic Radius Variance weighted by Miedema parameters)
 3. `electronegativity_variance_miedema` (Electronegativity Variance via Miedema scale)
 Also compute standard descriptors (entropy, VEC, etc.) and apply ILR transformation.
- [~] T019 [US1] Implement target calculation: Compute the **residual** `Bulk_Modulus_Residual = Bulk_Modulus_Observed - Bulk_Modulus_Miedema` as the primary model target; compute absolute Bulk Modulus as a diagnostic column only (referencing T018) in `src/features/targets.py`.
- [ ] T019.1 [US1] Implement **Conditional Feature Exclusion** logic in `src/features/exclusion.py`: **Explicitly exclude the columns** `mixing_enthalpy_miedema`, `atomic_radius_variance_miedema`, and `electronegativity_variance_miedema` from the predictor set ONLY when the target variable is a Residual Modulus (FR-002, FR-008). **Include a pre-training verification step (assertion)** that halts execution if any of these three columns are present in the predictor matrix when the target is Residual.
- [~] T020 [US1] Create main pipeline script `src/pipeline/ingest.py` to orchestrate fetch → filter → normalize → feature eng → save CSV. **Include dynamic generation of `data/source_metadata.yaml`** to record API versions, query parameters, and timestamps of the specific run (FR-009, US-1 Scenario 5).
- [~] T021 [US1] Implement **Underpowered Study Report** generation in `src/report/power_report.py`: explicitly log the specific deficit message: "Retrieved X samples; threshold not met. Proceeding with Reduced Power Analysis" and generate the report quantifying the power deficit (replacing the old hard halt logic).
- [~] T022 [US1] Output `data/processed/hea_features.csv` and **`data/source_metadata.yaml`** (YAML format, not JSON) to record provenance (FR-009).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Model Training and Statistical Evaluation (Priority: P2)

**Goal**: Train RF, GB, ElasticNet models on CPU, evaluate with grouped bootstrapping, and apply FDR correction.

**Independent Test**: Training completes within 6h on CPU, outputting `results/metrics.yaml` with R², RMSE, MAE, and 95% CI.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T023 [P] [US2] Unit test for grouped bootstrap logic in `tests/unit/test_bootstrap.py`
- [~] T024 [P] [US2] Unit test for FDR correction in `tests/unit/test_fdr.py`

### Implementation for User Story 2

- [ ] T025 [US2] Derive 'Alloy System' grouping key from composition data (e.g., sorted tuple of elements) in `src/model/derive_groups.py`
- [ ] T026 [US2] Implement grouped train/test split (by Alloy System) in `src/model/split.py`
- [ ] T027 [US2] Implement Random Forest training in `src/model/train_rf.py` (n_jobs=2, CPU only, 7GB RAM limit)
- [ ] T028 [US2] Implement Gradient Boosting training in `src/model/train_gb.py` (n_jobs=2, CPU only, 7GB RAM limit)
- [ ] T029 [US2] Implement ElasticNet training (with ILR input) in `src/model/train_elasticnet.py`
- [ ] T030 [US2] Implement grouped bootstrap resampling using a fixed seed from `src/utils/seeds.py` in `src/eval/bootstrap.py`. **Logic**: If unique groups ≥ 10, perform standard grouped bootstrap. If unique groups < 10, **log a warning: "Insufficient groups for grouped bootstrap (N=[N]); falling back to standard bootstrap with caution"** and proceed with standard bootstrap (per spec Edge Cases). **Explicitly write a flag** `bootstrap_ci_warning: "potentially underestimated"` **into** `results/metrics.yaml` **if groups < 10**. Calculate 95% CI for R².
- [ ] T031 [US2] Implement multiple-comparison correction (Benjamini-Hochberg/FDR) in `src/eval/fdr.py`
- [ ] T032 [US2] Create evaluation runner `src/eval/evaluate.py` to train all models, compute R²/RMSE/MAE for the **residual target** (Bulk_Modulus_Residual), and save `results/metrics.yaml`. **Consume the null hypothesis results from T032.1**. **Include generation of the 'Underpowered Study Report' and 'Reduced Power Analysis' output** in the metrics file when sample counts are low (per spec Edge Cases).
- [ ] T032.1 [US2] Implement **Permutation Test for Null Hypothesis** in `src/eval/permutation_test.py`. **Execute 1000 iterations** to test R² > 0. **Output** a JSON/YAML file `results/null_hypothesis.yaml` containing the **p-value** and a **boolean `significant` flag** (true if p < 0.05). This artifact is required by SC-002 and US-2 Scenario 4.
- [ ] T033 [US2] Add diagnostic logging for train/test performance gaps to detect overfitting; **explicitly check for correlation between residuals and ONLY the '$MIEDEMA_FEATURES$' set (Pearson |r| < 0.1)**; if correlation exceeds threshold, **log a warning "Potential circularity detected" and proceed with caution, noting the potential confound in the final report** (FR-008). Do NOT check general predictors to avoid flagging expected model signal.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Interpretability and Associational Reporting (Priority: P3)

**Goal**: Extract SHAP values, generate plots, perform sensitivity analysis, and ensure associational framing.

**Independent Test**: Report generation produces a summary with SHAP plots, sensitivity table, and explicit associational disclaimers.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [P] [US3] Unit test for causal language scanner in `tests/unit/test_causal_check.py`

### Implementation for User Story 3

- [ ] T035 [US3] Implement SHAP value extraction for the best model in `src/interpret/shap_analysis.py`
- [ ] T036 [US3] Generate parity plots and partial dependence plots in `src/interpret/visualize.py`
- [ ] T037 [US3] Implement sensitivity analysis script: **Sweep** R² thresholds {0.25, 0.30, 0.35}. Calculate **p-value for R² > 0.3 (estimated via permutation testing)** at each threshold. **Output**: Report the **variance in p-values** across the swept thresholds in `results/sensitivity.yaml` (per spec.md US-3 Acceptance Scenario 3 and FR-006). **Do NOT halt execution here**; this task is for reporting robustness only.
- [ ] T037.1 [US3] Implement **Hard-Stop Logic** in `src/utils/claim_validator.py`. **Consume** the p-value for the **0.3 threshold** from the sensitivity analysis. **If p > 0.05 for the 0.3 threshold specifically**, **raise SystemExit(1)** (or equivalent non-zero exit code) and log "Primary claim rejected: p-value at 0.3 threshold exceeds 0.05. Study halted." **Do NOT halt** for 0.25 or 0.35 thresholds.
- [ ] T038 [US3] Implement causal language scanner to flag violations in final text in `src/utils/causal_check.py`
- [ ] T039 [US3] Create report generator `src/report/generate.py` to compile PDF/Markdown with SHAP, sensitivity, and explicit associational disclaimers. **Explicitly include the 'Underpowered Study Report' content and 'Reduced Power Analysis' quantification** if applicable (per spec Edge Cases). **Check for the `bootstrap_ci_warning` flag from T030** and include it in the report if present.
- [ ] T040 [US3] Ensure `results/interpretability.yaml` and `results/sensitivity.yaml` are populated

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T041 [P] Run full pipeline integration test to verify data flow from fetch to report
- [ ] T042 Compute content hashes of `results/` and update `state/projects/PROJ-443-...yaml`
- [ ] T043 Verify all FRs (FR-001 to FR-007) are addressed in final artifacts
- [ ] T044 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Setup/Validation)**: No dependencies - can start immediately
- **Foundational (Phase 1)**: Depends on Phase 0 completion - BLOCKS all user stories
- **User Stories (Phase 2+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 1) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 1) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data fetch before feature engineering
- Feature engineering before model training
- Model training before evaluation
- Evaluation before interpretability/reporting
- Story complete before moving to next priority

### Parallel Opportunities

- All Phase 0 tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 1)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for normalization logic in tests/unit/test_normalization.py"
Task: "Unit test for ILR transformation in tests/unit/test_coda.py"

# Launch all models for User Story 1 together:
Task: "Implement OQMD data fetcher in src/data/fetch_oqmd.py"
Task: "Implement Materials Project fetcher in src/data/fetch_mp.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Setup & Validation
2. Complete Phase 1: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (ensure dataset is valid and features computed)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data & Features)
 - Developer B: User Story 2 (Models & Evaluation)
 - Developer C: User Story 3 (Interpretability & Reporting)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All models must run on CPU (limited cores, limited RAM). No GPU, no 8-bit quantization, no deep learning.
- **Data Integrity**: No synthetic data. All inputs must come from real OQMD/MP sources.
- **Statistical Rigor**: Grouped bootstrap is mandatory to prevent leakage; FDR correction required for model comparison. If groups < 10, warn and use standard bootstrap (per spec Edge Cases). **Flag CIs as potentially underestimated if groups < 10** (write to `results/metrics.yaml`).
- **Target Priority**: Models predict **residual** Bulk Modulus (Observed - Miedema) to avoid physics leakage; absolute values are diagnostic only. **Miedema-derived features must be excluded from predictors when target is Residual.**
- **Validation Gate**: Reference-Validator runs in Phase 0 before any data fetch.
- **Feasibility Check**: Ensure all descriptor calculations (Miedema, ILR) use vectorized NumPy/Pandas operations to stay within 7GB RAM limits; avoid loading full periodic tables into memory repeatedly.
- **Data Source Specificity**: T014 and T015 must explicitly handle the "≥5 principal elements" filter at the API query level or immediately post-fetch to minimize memory usage.
- **Residual Validation**: T033 must explicitly check for correlation between residuals and **ONLY $MIEDEMA_FEATURES$** (FR-008) and log warning/proceed if |r| > 0.1. Do not check other predictors.
- **Underpowered Study**: T016.5, T021, T032, and T039 must implement the 'Reduced Power Analysis' and 'Underpowered Study Report' generation. **The system MUST NOT halt** if sample count < 500; it must proceed with the report.
- **Metadata Generation**: T020 must dynamically generate `source_metadata.yaml` at runtime to record actual API versions and query parameters (FR-009).
- **Sensitivity Analysis**: T037 must report the **p-value for R² > 0.3** and the variance in these p-values across thresholds (FR-006). **T037.1 must halt the study ONLY if p > 0.05 for the 0.3 threshold.**
- **Miedema Features**: T018 must generate `mixing_enthalpy_miedema`, `atomic_radius_variance_miedema`, `electronegativity_variance_miedema`. T019.1 must explicitly exclude these three columns for Residual targets.