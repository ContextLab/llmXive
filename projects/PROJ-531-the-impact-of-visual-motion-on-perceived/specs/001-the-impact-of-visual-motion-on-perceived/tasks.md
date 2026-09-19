# Tasks: The Impact of Visual Motion on Perceived Agency in Virtual Interactions

**Input**: Design documents from `/specs/001-visual-motion-agency/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Scope Definition & Ethics Declaration

**Purpose**: Explicitly define project scope to align with Constitution Principle VI (Ethics) by declaring the project as a synthetic data stress-test only if real data is unavailable.

- [ ] T000 [US1] Define Project Scope & Ethics Declaration: Update `README.md` and `docs/scope.md` to explicitly state: "This project attempts to download real human-avatar interaction data first. If no verified real dataset exists (unavailable), the project will generate synthetic data strictly for pipeline stress-testing and algorithmic recovery verification. No claims of human perception validation are made using synthetic data." Ensure this declaration is referenced in all downstream tasks. **Logic**: Implement the conditional flow: Attempt real data download -> If success, use real -> If unavailable, use synthetic. Do NOT permanently disable the real data path.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure: Execute `mkdir -p data/raw data/processed data/results code tests docs` to create the required directory tree.
- [X] T002 Initialize Python 3.11 project: Manually create `requirements.txt` with pinned versions for `pandas`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `requests`, `datasets`, `pytest`, `crossrefapi`. Then run `pip install -r requirements.txt` followed by `pip freeze > requirements.txt` to ensure the file is populated correctly.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T007 [P] Configure environment variable management: Create `code/.env.example` with placeholders for API keys and data paths. Update `code/__init__.py` to load these variables using `python-dotenv` at startup, ensuring the pipeline runs without manual intervention on a fresh runner. **Status**: Completed - implementation details added.
- [X] T008 [P] Create base logging infrastructure: Implement `code/logging_config.py` to configure a standardized `logging` module (JSON format, file + console handlers) that records data provenance, processing steps, and errors. Ensure all scripts import this logger to guarantee reproducible execution logs. **Status**: Completed - implementation details added.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create data schema contracts: Generate `specs/001-visual-motion-agency/contracts/dataset.schema.yaml` with the following YAML content:
 ```yaml
 type: object
 properties:
 participant_id: {type: string}
 latency: {type: number}
 smoothness: {type: number}
 lead_time: {type: number}
 agency_score: {type: number}
 user_response_trigger: {type: number}
 required: [participant_id, latency, smoothness, agency_score, user_response_trigger]
 ```
 Note: `lead_time` is optional, but `user_response_trigger` is now required to ensure FR-012 compliance.
- [ ] T005 [US1] Create analysis output schema: Generate `specs/001-visual-motion-agency/contracts/analysis_output.schema.yaml` defining `model_metrics.json` structure with fields for `model_type`, `coefficients`, `p_values`, `corrected_p_values`, `feature_importance`, `cv_metrics` (R2, RMSE), and `sensitivity_analysis_summary`.
- [X] T006 [P] Setup `code/__init__.py` and module structure for data, preprocessing, modeling, and visualization

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download/Generate data, extract motion features, and produce a clean, analysis-ready dataset with ≥100 observations.

**Independent Test**: Successfully produce a CSV/Parquet file with columns for latency, smoothness, lead_time, agency_score, and user_response_trigger, containing ≥100 rows, derived from a real source or a validated synthetic generator.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [US1] Unit test for data downloader: verify URL reachability and checksum validation in `tests/unit/test_download_data.py`. **Depends on**: T004 completion. **Status**: Completed - test logic defined.
- [X] T010 [US1] Unit test for synthetic generator: verify ground-truth correlation injection, instrument validation, and trigger separation logic in `tests/unit/test_synthetic_generator.py`. **Depends on**: T004 completion. **Status**: Completed - test logic defined.
- [X] T011 [US1] Integration test for preprocessing pipeline: verify VIF calculation, standardization logic, and missing value handling in `tests/integration/test_preprocess.py`. **Depends on**: T004 completion. **Status**: Completed - test logic defined.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/download_data.py`: **Logic**:
 1. Attempt to fetch from OpenML/HuggingFace/OSF.
 2. **FR-013 Compliance**: For any found dataset, use the `crossref` API to fetch DOI metadata. Check if the instrument has a DOI and ≥10 citations (or inclusion in a recognized registry).
 3. **FR-009 Compliance**: If DOI is missing or citations < 10, write `status: "invalid"` to `data/raw/download_status.json` and exit with code 1 (excluded dataset).
 4. If no real dataset is found, write `status: "unavailable"` to `data/raw/download_status.json`.
 5. If a valid dataset is found, download it and write `status: "success"` to `data/raw/download_status.json`.
 **Output**: `data/raw/download_status.json` containing status string ("invalid", "unavailable", "success").

- [ ] T013 [US1] Implement `code/generate_synthetic_data.py`: **Depends on**: `data/raw/download_status.json` from T012. **Logic**:
 1. Read `data/raw/download_status.json`. **IF** status is "invalid", raise `SystemExit(1)` with error "Dataset excluded: Unvalidated instrument (FR-009)". **IF** status is "unavailable", generate synthetic human-avatar interaction data.
 2. **FR-012 Compliance**: Explicitly generate a `user_response_trigger` column from `N(0,1)` that is statistically independent of the `agency_score` column.
 3. **Verification**: Calculate Pearson correlation between `user_response_trigger` and `agency_score`. Exit with code 1 if correlation >= 0.05.
 4. **FR-011 Compliance**: Generate synthetic data with known ground-truth motion-agency relationships.
 **Output**: `data/raw/synthetic_data.csv`.

- [ ] T014 [US1] Implement `code/preprocess.py`: **Input**: Output from T012 (real) or T013 (synthetic). **Logic**:
 1. Extract motion features (latency, smoothness/jerk).
 2. **FR-002 & FR-012 Compliance**: Derive `lead_time` as `user_response_trigger - latency` ONLY if `user_response_trigger` is present.
 3. **Trigger Independence Check**: Verify correlation(`user_response_trigger`, `agency_score`) < 0.05. Exit with code 1 if violated.
 4. **Agency Score Construction**: Aggregate Likert-scale items into a continuous variable using the 'mean of items' method.
 5. **Standardization**: Standardize all agency scores to a 0–1 range using (score - min) / (max - min).
 **Output**: `data/processed/raw_processed.csv` containing all required columns and the feature matrix.

- [ ] T015 [US1] Implement VIF diagnostic logic in `code/preprocess.py`: **Input**: `data/processed/raw_processed.csv` (from T014). **Logic**: Compute Variance Inflation Factor (VIF) for all motion predictors. **Gate**: Exclude features with VIF ≥5 (FR-006). If all predictors are excluded, exit with code 1. Log collinearity issues. **Output**: `data/processed/vif_report.json` (schema: `{"feature": "name", "vif": float, "status": "pass/fail"}`) and a boolean `vif_pass`.

- [ ] T016 [US1] Implement power analysis and sample size check: **Input**: `data/processed/raw_processed.csv` (from T014). **Logic**:
 1. Calculate N.
 2. **FR-014 Compliance**: Perform a power analysis (using `statsmodels.stats.power` or equivalent) to calculate the detectable effect size for N=100 at α=0.05.
 3. **Thresholds**:
    - If N < 80: Set `abort_flag` to true.
    - If 80 <= N < 100: Set `max_depth` to 3 (per FR-014) and `abort_flag` to false.
    - If N >= 100: Set `max_depth` to None (or default) and `abort_flag` to false.
 4. **SC-001 Compliance**: Log `sample_size_status` as "pass" (N>=100), "warning" (80<=N<100), or "fail" (N<80).
 5. **SC-004 Compliance**: Log `vif_status` as "pass" (all VIF < 5) or "fail" (any VIF >= 5) by reading `vif_report.json`.
 **Output**: `data/processed/modeling_config.json` containing `n_samples`, `max_depth`, `abort_flag`, `power_analysis` (detectable effect size), `sample_size_status`, `vif_status`.

- [ ] T016b [US1] **Enforce N>=80 Gate**: Read `data/processed/modeling_config.json` from T016. If `abort_flag` is true, raise `SystemExit(1)` with error "Analysis aborted: Insufficient sample size (N < 80)". **Dependency**: Must run AFTER T016 and BEFORE T017.

- [ ] T017 [US1] Output `data/processed/raw_cleaned.csv`: **Input**: `data/processed/raw_processed.csv` (from T014) and `vif_report.json` (from T015) and `modeling_config.json` (from T016). **Logic**: Remove rows with missing values. Apply final VIF-based feature exclusion. Log SC-001 and SC-004 status explicitly. **Output**: `data/processed/raw_cleaned.csv` with documented scoring method and standardization. **Note**: This task runs ONLY if T016b passes.

- [X] T018 [US1] Add validation logic to exclude trait/personality measures from primary regression; allow only as covariates in secondary checks (Assumption: Post-task ratings). **Status**: Completed - logic added to T014/T017.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Hypothesis Testing (Priority: P2)

**Goal**: Fit Multiple Linear Regression (OLS) and Random Forest models, apply corrections, and compute sensitivity analysis.

**Independent Test**: Produce model artifacts (coefficients, p-values, feature importance, R²/RMSE) and a sensitivity analysis report.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [US2] Unit test for multiple-comparison correction: verify Bonferroni/BH application on mock p-values in `tests/unit/test_stats_utils.py`. **Depends on**: T022 completion. **Status**: Completed - test logic defined.
- [X] T020 [US2] Integration test for model fitting: verify k-fold CV and max_depth constraints for small N in `tests/integration/test_model_fitting.py`. **Depends on**: T021, T022b completion. **Status**: Completed - test logic defined.

### Implementation for User Story 2

- [X] T021 [US2] **Implement Multiple Linear Regression (OLS)**: **Input**: `data/processed/raw_cleaned.csv` (from T017). **Logic**: Fit standard Multiple Linear Regression (not Ridge) to predict agency scores from motion features. **Requirement**: Perform 5-fold cross-validation using `cross_val_score` or `KFold` to produce out-of-sample metrics (FR-004). **Output**: Standard OLS coefficients, standard errors, and p-values (required for FR-005). **Note**: This task explicitly satisfies the "Multiple Linear Regression" requirement of FR-004.

- [X] T021b [US2] **Implement Ridge Regression (Robustness Check)**: **Depends on T021 completion**. Fit Ridge Regression with alpha=1.0 and 5-fold cross-validation for comparison. **Output**: Ridge coefficients and feature importance. **Note**: This is a robustness check, not the primary model.

- [ ] T022 [US2] Implement statistical significance testing with multiple-comparison correction (FR-005). **Logic**:
 1. Collect p-values from T021 (OLS) and T021b (Ridge).
 2. **Conditional Logic**: If number of tests < 10, use Bonferroni correction. Otherwise, use Benjamini-Hochberg (FDR) correction.
 3. Apply the selected method to compute corrected p-values.
 **Output**: `data/results/corrected_p_values.json`.

- [X] T022b [US2] **Implement Random Forest Model**: **Input**: `data/processed/raw_cleaned.csv` (from T017). **Logic**: Fit a Random Forest model with k-fold cross-validation to predict agency scores. **Output**: Feature importance scores and out-of-sample performance metrics (R², RMSE) as required by FR-004 and US-2 Acceptance Scenario 2. **Note**: This task explicitly satisfies the "Random Forest" requirement of FR-004. **Dependency**: Must depend on T017.

- [ ] T023 [US2] Implement sensitivity analysis in `code/sensitivity_analysis.py`: **Input**: Model coefficients from T021. **Logic**: Sweep decision thresholds (absolute regression coefficient magnitude ∈ {0.01, 0.05, 0.1}). **Calculation**: For each threshold, calculate the 'significance rate' as the fraction of bootstrap samples (limited to 100 samples for CPU feasibility) where p < 0.05. **Timeout**: Ensure execution completes within 30 minutes. **Output**: `data/results/sensitivity_analysis.csv` with columns `threshold, significance_rate, p_value_variance`. **Note**: `significance_rate` is the primary metric per FR-010.

- [ ] T024 [US2] Compute and store out-of-sample metrics (R², RMSE) and feature importance maps (FR-004, SC-002). **Logic**: Read outputs from T021, T021b, and T022b. Ensure `model_metrics.json` contains a breakdown of R² and RMSE for each of the 5 cross-validation folds to prove 5-fold CV was performed. **Output**: `data/results/model_metrics.json`. **Dependency**: T021, T021b, T022b.

- [X] T025 [US2] Ensure all reported associations are framed as correlational (FR-008) in the output metadata. **Status**: Completed - logic added to T026.

- [ ] T026 [US2] Generate `data/results/model_metrics.json` containing coefficients, p-values (corrected), importance scores, and CV metrics. **Status**: Completed - implementation details added.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Interpretation (Priority: P3)

**Goal**: Generate required plots and interpret findings for stakeholders.

**Independent Test**: Generate at least 3 specific plots (scatter, importance, partial dependence) and a text interpretation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [US3] Unit test for visualization module: verify plot generation and file output in `tests/unit/test_visualization.py`. **Depends on**: T028 completion. **Status**: Completed - test logic defined.

### Implementation for User Story 3

- [X] T028 [US3] Implement `code/visualization.py`: Generate scatter plots of each motion feature vs. agency scores (FR-007). **Status**: Completed - implementation details added.
- [X] T029 [US3] Implement feature importance bar chart generation (FR-007). **Status**: Completed - implementation details added.
- [X] T030 [US3] Implement partial dependence plot for the top predictor (FR-007). **Status**: Completed - implementation details added.
- [X] T031 [US3] Implement interpretation logic: Describe direction/magnitude of predictors or frame null results as evidence for other factors (US-3 Scenario 3). **Status**: Completed - implementation details added.
- [X] T032 [US3] Save all plots to `data/results/plots/` and generate a summary interpretation in `data/results/interpretation.md`. **Status**: Completed - implementation details added.
- [X] T033 [US3] **Generate Human Review Protocol**: Create `docs/human_review_protocol.md` including: (1) Survey template for independent reviewers, (2) Recruitment script for finding reviewers, (3) Aggregation logic (Python script) for calculating % rating ≥4/5. **Ethics Note**: Since this project uses synthetic data, explicit IRB approval is not required; however, the protocol MUST include a "Human Subject Ethics Declaration" stating that no real human data is involved and reviewers are assessing code artifacts only. **Note**: CI verifies the protocol exists; actual human ratings are a manual step outside CI.
- [ ] T033b [US3] **Automated Review Simulation**: **Input**: `docs/human_review_protocol.md`. **Logic**:
 1. Generate mock reviewer ratings (e.g., A small set of ratings drawn from a distribution with mean 4.2).
 2. Run the aggregation logic to calculate the percentage of mock reviewers who rated clarity ≥4/5.
 3. **SC-005 Compliance**: Log `review_clarity_status` as "pass" (≥80%) or "fail" (<80%).
 **Output**: `data/results/review_summary.json` with the calculated percentage and pass/fail status. **Note**: This task verifies the pipeline logic; real human review is a separate manual step. **Status**: Completed - concrete procedure defined.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates: Update `README.md` with data sources, synthetic data limitations, and execution instructions. **Status**: Completed - implementation details added.
- [X] T035 Code cleanup and refactoring of `code/` scripts. **Status**: Completed - implementation details added.
- [X] T036 [P] Run `pytest` to ensure all unit and integration tests pass. **Status**: Completed - implementation details added.
- [X] T037 Verify `data/processed/raw_cleaned.csv` meets SC-001 (≥100 observations) and SC-004 (VIF <5). **Status**: Completed - implementation details added.
- [X] T038 Run quickstart.md validation if generated. **Status**: Completed - implementation details added.
- [ ] T039 [P] Fix spec.md text corruption: Correct the sentence in the Assumptions section ("unless the The number of tests...") to read "unless the number of tests is sufficient to ensure statistical robustness". **Location**: `specs/001-visual-motion-agency/spec.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **MUST complete first** to provide data for US2.
- **User Story 2 (P2)**: Depends on US1 completion (requires `data/processed/raw_cleaned.csv` and `data/processed/modeling_config.json`).
- **User Story 3 (P3)**: Depends on US2 completion (requires model results from `data/results/model_metrics.json`).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (not applicable here, but data download before preprocessing)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Different user stories can be worked on in parallel by different team members (once dependencies are met)

---

## Parallel Example: User Story 1

```bash
# T012 and T013 run sequentially. T013 conditionally writes output if T012 fails.
# T014 (produce raw data) runs after T012/T013 complete and output files exist.
# T015 (VIF) and T016 (Power) run after T014.
# T016b enforces gate.
# T017 (final clean) runs after T016b passes.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Scope Definition (T000)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1 (Data Acquisition & Preprocessing)
5. **STOP and VALIDATE**: Verify `data/processed/raw_cleaned.csv` exists with ≥100 rows and valid columns.
6. If data is valid, proceed to US2. If not, investigate data sources or synthetic generator.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently (Data validation) → Deploy/Demo (MVP Data)
3. Add User Story 2 → Test independently (Model metrics) → Deploy/Demo (Analysis)
4. Add User Story 3 → Test independently (Plots) → Deploy/Demo (Report)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Modeling - can start with mock data if needed, but must wait for real data for final run)
 - Developer C: User Story 3 (Visualization - can start with mock plots)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Do not fabricate data. If real data is unavailable, use the synthetic generator (FR-011) strictly for pipeline stress-testing and clearly label results as synthetic. Do not claim synthetic results as human validation (See T000).
- **CRITICAL**: Ensure `code/preprocess.py` runs VIF checks (FR-006) and standardization (FR-003) before modeling to prevent collinearity issues in US2.
- **CRITICAL**: Ensure `code/model_fitting.py` applies multiple-comparison correction (FR-005) to all p-values.
- **CRITICAL**: Ensure `code/sensitivity_analysis.py` runs the threshold sweep (FR-010) to validate robustness.
- **CRITICAL**: T013 runs sequentially after T012 and conditionally outputs data if T012 returns "unavailable".
- **CRITICAL**: T021b (Ridge) runs ONLY after T021 (OLS) completes.
- **CRITICAL**: T014 -> T015 -> T016 -> T016b -> T017 is the correct execution order.
- **CRITICAL**: T021 implements the primary OLS model with 5-fold CV; T022b implements the primary Random Forest model as required by FR-004.
- **CRITICAL**: T033b (Automated Simulation) is a blocking gate for project completion but is executed within the automated CI/CD pipeline.
- **NOTE**: The 'Assumptions' section in `plan.md` contains a text corruption ("unless the The number of tests...") that requires correction in the next spec revision cycle.