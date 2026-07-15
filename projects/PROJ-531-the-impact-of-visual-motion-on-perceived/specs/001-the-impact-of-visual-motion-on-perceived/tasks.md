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

**Purpose**: Explicitly define project scope to align with Constitution Principle VI (Ethics) by declaring the project as a synthetic data stress-test only.

- [X] T000 [US1] Define Project Scope & Ethics Declaration: Update `README.md` and `docs/scope.md` to explicitly state: "This project is strictly a synthetic data stress-test. No human participants are involved. No claims of human perception validation are made. Real data path is disabled due to unavailability." Ensure this declaration is referenced in all downstream tasks.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure: Execute `mkdir -p data/raw data/processed code tests docs` to create the required directory tree.
- [X] T002 Initialize Python 3.11 project: Manually create `requirements.txt` with pinned versions for `pandas`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `requests`, `datasets`, `pytest`. Then run `pip install -r requirements.txt` followed by `pip freeze > requirements.txt` to ensure the file is populated correctly.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

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
 required: [participant_id, latency, smoothness, agency_score]
 ```
 Note: `lead_time` is intentionally excluded from the `required` list to allow for missing telemetry data.
- [X] T005 Create analysis output schema: Generate `specs/001-visual-motion-agency/contracts/analysis_output.schema.yaml` defining `model_metrics.json` structure.
- [ ] T006 [P] Setup `code/__init__.py` and module structure for data, preprocessing, modeling, and visualization
- [ ] T007 [P] Configure environment variable management for API keys (if needed) and data paths
- [ ] T008 Create base logging infrastructure to record data provenance and processing steps

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download/Generate data, extract motion features, and produce a clean, analysis-ready dataset with ≥100 observations.

**Independent Test**: Successfully produce a CSV/Parquet file with columns for latency, smoothness, lead_time, and agency_score, containing ≥100 rows, derived from a real source or a validated synthetic generator.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [US1] Unit test for data downloader: verify URL reachability and checksum validation in `tests/unit/test_download_data.py`. **Depends on**: T012 completion. <!-- FAILED: unspecified -->
- [ ] T010 [US1] Unit test for synthetic generator: verify ground-truth correlation injection and instrument validation logic in `tests/unit/test_synthetic_generator.py`. **Depends on**: T013 completion.
- [ ] T011 [US1] Integration test for preprocessing pipeline: verify VIF calculation and missing value handling in `tests/integration/test_preprocess.py`. **Depends on**: T014 completion.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/download_data.py`: Attempt to fetch from OpenML/HuggingFace/OSF; verify instrument validity (DOI/citations) per FR-013. **Output**: `data/raw/download_status.json`. **Error Handling**: Exit with code 1 if no valid dataset found.
- [ ] T013 [US1] Implement `code/generate_synthetic_data.py`: **Runs in parallel with T012**. Generate synthetic human-avatar interaction data with known ground-truth motion-agency relationships (FR-011) ONLY if T012 returns status "unavailable" OR "invalid". Ensure `user response trigger` is distinct from agency score (FR-012).
- [ ] T014 [US1] Implement `code/preprocess.py`: Extract motion features (latency, smoothness/jerk, lead_time) and aggregate agency scores (FR-002, FR-003).
- [ ] T015 [US1] Implement VIF diagnostic logic in `code/preprocess.py`: Flag and exclude features with VIF ≥5 (FR-006); log collinearity issues.
- [ ] T017 [US1] Output `data/processed/cleaned_data.csv` with documented scoring method and standardization (0–1 range if needed) (Edge Case).
- [ ] T016 [US1] Implement power analysis and sample size check: Read `data/processed/cleaned_data.csv` from T017. Calculate N. **Logic**: If N < 80, set `abort_flag` to true in config. If 80 <= N < 100, set `max_depth` to 3. **Output**: `data/processed/modeling_config.json` containing `n_samples`, `max_depth`, `abort_flag`. **Note**: This task calculates and writes the config; it does NOT abort the process.
- [~] T016b [US1] **Enforce N>=80 Gate**: Read `data/processed/modeling_config.json` from T016. If `abort_flag` is true, raise `SystemExit(1)` with error "Analysis aborted: Insufficient sample size (N < 80)".
- [~] T018 [US1] Add validation logic to exclude trait/personality measures from primary regression; allow only as covariates in secondary checks (Assumption: Post-task ratings).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Hypothesis Testing (Priority: P2)

**Goal**: Fit Multiple Linear Regression (OLS) and Random Forest models, apply corrections, and compute sensitivity analysis.

**Independent Test**: Produce model artifacts (coefficients, p-values, feature importance, R²/RMSE) and a sensitivity analysis report.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [US2] Unit test for multiple-comparison correction: verify Bonferroni/BH application on mock p-values in `tests/unit/test_stats_utils.py`. **Depends on**: T022 completion.
- [X] T020 [US2] Integration test for model fitting: verify k-fold CV and max_depth constraints for small N in `tests/integration/test_model_fitting.py`. **Depends on**: T022, T022b completion.

### Implementation for User Story 2

- [ ] T021 [US2] **Implement Multiple Linear Regression (OLS)**: Read `data/processed/modeling_config.json` from T016. Fit standard Multiple Linear Regression (not Ridge) to predict agency scores from motion features. **Output**: Standard OLS coefficients and p-values (required for FR-005).
- [~] T021b [US2] **Implement Ridge Regression (Robustness Check)**: **Depends on T021 completion**. Fit Ridge Regression with k-fold cross-validation for comparison. Output: Ridge coefficients and feature importance.
- [~] T022 [US2] Implement statistical significance testing with Bonferroni or Benjamini-Hochberg correction for ≥3 features (FR-005).
- [~] T022b [US2] **Implement Random Forest Model**: Fit a Random Forest model with k-fold cross-validation to predict agency scores. **Output**: Feature importance scores and out-of-sample performance metrics (R², RMSE) as required by FR-004 and US-2 Acceptance Scenario 2.
- [ ] T023 [US2] Implement sensitivity analysis in `code/sensitivity_analysis.py`: **Sweep decision thresholds** (absolute regression coefficient magnitude ∈ {0.01, 0.05, 0.1}). **Logic**: For each threshold, calculate the 'significance rate' (fraction of bootstrap samples where p < 0.05). **Output**: `data/results/sensitivity_analysis.csv` with columns `threshold, significance_rate, p_value_variance`.
- [~] T024 [US2] Compute and store out-of-sample metrics (R², RMSE) and feature importance maps (FR-004, SC-002).
- [~] T025 [US2] Ensure all reported associations are framed as correlational (FR-008) in the output metadata.
- [ ] T026 [US2] Generate `data/results/model_metrics.json` containing coefficients, p-values (corrected), importance scores, and CV metrics.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Interpretation (Priority: P3)

**Goal**: Generate required plots and interpret findings for stakeholders.

**Independent Test**: Generate at least 3 specific plots (scatter, importance, partial dependence) and a text interpretation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [US3] Unit test for visualization module: verify plot generation and file output in `tests/unit/test_visualization.py`. **Depends on**: T028 completion.

### Implementation for User Story 3

- [X] T028 [US3] Implement `code/visualization.py`: Generate scatter plots of each motion feature vs. agency scores (FR-007).
- [~] T029 [US3] Implement feature importance bar chart generation (FR-007).
- [~] T030 [US3] Implement partial dependence plot for the top predictor (FR-007).
- [~] T031 [US3] Implement interpretation logic: Describe direction/magnitude of predictors or frame null results as evidence for other factors (US-3 Scenario 3).
- [ ] T032 [US3] Save all plots to `data/results/plots/` and generate a summary interpretation in `data/results/interpretation.md`.
- [X] T033 [US3] **Generate Human Review Protocol**: Create `docs/human_review_protocol.md` including: (1) Survey template for independent reviewers, (2) Recruitment script for finding reviewers, (3) Aggregation logic (Python script) for calculating % rating ≥4/5. **Ethics Note**: Since this project uses synthetic data, explicit IRB approval is not required; however, the protocol MUST include a "Human Subject Ethics Declaration" stating that no real human data is involved and reviewers are assessing code artifacts only. **Note**: CI verifies the protocol exists; actual human ratings are a manual step outside CI.
- [ ] T033b [US3] **Manual Review Execution Plan**: Document the step-by-step procedure for recruiting multiple independent reviewers, distributing the survey from T033, collecting ratings, and running the aggregation script to verify SC-005 (≥80% rating ≥4/5).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates: Update `README.md` with data sources, synthetic data limitations, and execution instructions.
- [ ] T035 Code cleanup and refactoring of `code/` scripts.
- [ ] T036 [P] Run `pytest` to ensure all unit and integration tests pass.
- [ ] T037 Verify `data/processed/cleaned_data.csv` meets SC-001 (≥100 observations) and SC-004 (VIF <5).
- [ ] T038 Run quickstart.md validation if generated.

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
- **User Story 2 (P2)**: Depends on US1 completion (requires `data/processed/cleaned_data.csv` and `data/processed/modeling_config.json`).
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
# T012 and T013 run in parallel. T013 conditionally writes output if T012 fails.
# T017 (produce data) runs before T016 (calc N).
# T016 writes config, T016b enforces gate.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Scope Definition (T000)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1 (Data Acquisition & Preprocessing)
5. **STOP and VALIDATE**: Verify `data/processed/cleaned_data.csv` exists with ≥100 rows and valid columns.
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
- **CRITICAL**: Ensure `code/preprocess.py` runs VIF checks (FR-006) before modeling to prevent collinearity issues in US2.
- **CRITICAL**: Ensure `code/model_fitting.py` applies multiple-comparison correction (FR-005) to all p-values.
- **CRITICAL**: Ensure `code/sensitivity_analysis.py` runs the threshold sweep (FR-010) to validate robustness.
- **CRITICAL**: T013 runs in parallel with T012 but conditionally outputs data if T012 fails.
- **CRITICAL**: T021b (Ridge) runs ONLY after T021 (OLS) completes.
- **CRITICAL**: T017 (produce data) runs before T016 (calc N), which runs before T016b (enforce gate).
- **CRITICAL**: T022b implements the Random Forest model required by FR-004.