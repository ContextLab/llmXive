# Tasks: Predicting the Ductility of Additively Manufactured Nickel-Based Superalloys

**Input**: Design documents from `/specs/224-ductility-prediction/`
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
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create `code/` directory structure
- [X] T002 [P] Create `data/`, `artifacts/`, `tests/` directories
- [X] T003 [P] Create `code/data/`, `code/models/`, `code/analysis/` subdirectories

**Checkpoint**: Setup complete

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Initialize Python 3.11 virtual environment
- [X] T006 [P] Create `requirements.txt` with pinned versions: pandas, numpy, scikit-learn, statsmodels, xgboost, requests, lxml, pyyaml
- [X] T007 [P] Configure linting (ruff) and formatting (black) tools
- [X] T008 [P] Create `pytest.ini` and basic test harness

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Curated Dataset Acquisition (Priority: P1) 🎯 MVP

**Goal**: Construct a unified, cleaned dataset from literature tables and HuggingFace sources, ensuring all units are SI and records are valid.

**Independent Test**: Execute `code/data/acquisition.py` and `code/data/cleaning.py` and verify `data/curated_builds.csv` exists with ≥50 rows (or critical warning logged) and all required columns (laser_power, scan_speed, hatch_spacing, layer_thickness, ductility, alloy_family, energy_density).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Unit test for unit conversion logic in `code/tests/test_data_cleaning.py`
- [X] T014 [P] [US1] Unit test for missing value exclusion logic in `code/tests/test_data_cleaning.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement data acquisition in `code/data/acquisition.py`:
 - **Primary Source**: Parse supplementary tables from the four cited papers (using `lxml` or manual CSV ingestion) as the primary source per `plan.md`.
 - **Secondary Source**: Attempt to query the HuggingFace "additive-manufacturing-superalloy" collection.
 - **Merge**: Combine all successful sources.
 - **Error Handling**: If HuggingFace is unreachable or returns empty, log a CRITICAL warning but **DO NOT** fail. Proceed with the data from the primary source (papers).
 - **Output**: A unified DataFrame.
- [ ] T016 [US1] Implement Materials Project descriptor fetch in `code/data/acquisition.py`: <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
 - Query the Materials Project API **only** for alloy crystallographic descriptors (lattice parameters, space group) for the alloys present in the dataset.
 - Merge these descriptors into the unified DataFrame.
 - Log any API failures but proceed with available data.
- [X] T017 [US1] Implement data cleaning in `code/data/cleaning.py`:
 - Convert all raw units to SI (W, mm/s, µm, %).
 - Filter out records with missing ductility or incomplete process specs (log reasons).
 - Map alloy composition to binary flags for specific elements: Cr, Al, Ti, Co, Mo, W.
 - Output `data/curated_builds.csv`.
- [X] T018 [US1] Implement feature engineering in `code/data/preprocessing.py`:
 - Calculate volumetric energy density: `E_v = P / (v * h * t)`.
 - Add `E_v` to the dataset.
 - Verify column integrity.
- [X] T019 [US1] Add validation check in `code/data/cleaning.py`:
 - If row count < 50, log critical warning but proceed.
 - Log total excluded records and reasons.
- [ ] T020 [US1] Version the `data/curated_builds.csv` artifact: <!-- ATOMIZE: requested -->
 - Compute SHA-256 hash of the CSV file.
 - **MANDATORY**: Record the hash in `state/projects/PROJ-224-predicting-the-ductility-of-additively-m.yaml` under the `artifact_hashes` key.
 - Do not store hashes in alternative locations (e.g., `data/.checksums` or `state/` root).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Parameter Influence via Mixed-Effects Modeling (Priority: P2)

**Goal**: Fit a linear mixed-effects model to determine parameter influence, handling multicollinearity via VIF and performing sensitivity analysis.

**Independent Test**: Run `code/models/lme_model.py` on `data/curated_builds.csv` and verify output contains standardized coefficients, 95% CIs, p-values, partial R², and that the model converges.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for VIF calculation logic in `code/tests/test_models.py`
- [ ] T022 [P] [US2] Unit test for mixed-effects convergence check in `code/tests/test_models.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement VIF analysis and feature filtering in `code/data/preprocessing.py`:
 - Calculate VIF for all fixed-effect predictors (Power, Speed, Hatch, Thickness, Energy Density).
 - **Logic**: IF Energy Density VIF > 5 THEN:
 - Drop the individual constituent predictors (Power, Speed, Hatch, Thickness).
 - Retain ONLY Energy Density as the representative for that group.
 - **Verification**: Re-calculate VIF on the reduced set to confirm max VIF ≤ 5.
 - Log the final set of predictors used.
 - Output the filtered dataset.
- [~] T024 [US2] Implement Linear Mixed-Effects model in `code/models/lme_model.py`:
 - Fit model with fixed effects (selected predictors from T023) and random intercept for `alloy_family`.
 - Ensure model uses CPU-only execution.
 - Extract standardized coefficients, 95% CIs, and p-values.
 - **Random Effects**: Extract and store the random intercept estimates for each alloy family.
 - **Convergence Check**: If the model fails to converge, log an ERROR, set a `convergence_failed` flag in the output artifact, and DO NOT proceed with coefficient interpretation.
- [~] T025 [US2] Implement model diagnostics in `code/analysis/sensitivity.py`:
 - Compute partial R².
 - If partial R² < 0.50, log warning (do not abort).
 - **Likelihood-Ratio Test**: Construct a null intercept-only model and perform a likelihood-ratio test against the full model at α=0.05. Record the test statistic and p-value.
- [~] T026 [US2] Implement sensitivity analysis in `code/analysis/sensitivity.py`:
 - Repeat LME fit for α ∈ {0.05, 0.10} and other representative significance levels..
 - Report variation in coefficients and partial R².
- [~] T027 [US2] Save `MixedEffectsResult` artifact (JSON/CSV) with all metrics, convergence status, and random effect estimates.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Deploy a Predictive Ductility Model (Priority: P3)

**Goal**: Train an XGBoost regressor for prediction, evaluate performance, and compute feature importance.

**Independent Test**: Train XGBoost in `code/models/xgboost_model.py` within 600s, evaluate on hold-out set, and verify R², MAE, RMSE are recorded and permutation importance is computed.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T028 [P] [US3] Unit test for train/val/test split logic in `code/tests/test_models.py`
- [~] T029 [P] [US3] Integration test for model training time budget in `code/tests/test_models.py`

### Implementation for User Story 3

- [~] T030 [US3] Implement data splitting in `code/data/preprocessing.py`:
 - **Logic**:
 - If N < 100: Use **Leave-One-Alloy-Family-Out (LOAFO)** as the stratification strategy within a 5-fold cross-validation loop. In each fold, the left-out alloy family serves as the "held-out test set" for that iteration.
 - If N ≥ 100: Use standard stratified train/val/test split by `alloy_family`.
 - Ensure the test set (left-out fold or held-out split) is used only for final evaluation.
 - Output split data artifacts.
- [~] T031 [US3] Implement XGBoost training in `code/models/xgboost_model.py`:
 - Train with `tree_method="hist"` (CPU-optimized).
 - Perform 5-fold **stratified** CV for hyperparameter tuning (max_depth, learning_rate, n_estimators) within a fixed time budget.
 - Save best model to `artifacts/xgboost_model.pkl`.
- [~] T032 [US3] Implement model evaluation in `code/models/xgboost_model.py`:
 - Evaluate on held-out test set (or LOAFO aggregated metrics).
 - Record R², MAE, RMSE.
 - If R² < 0.60, log result but do not abort.
- [~] T033 [US3] Implement feature importance in `code/models/xgboost_model.py`:
 - Compute permutation feature importance.
 - Load `MixedEffectsResult` artifact from T027.
 - **Comparison**: Compare the top 3 features from XGBoost with the top 3 coefficients from the LME model.
 - **Conditional Logic**: If FR-005 logic (in T023) resulted in a reduced feature set (e.g., only Energy Density), compare the importance/coefficient of the shared feature(s). If the feature sets are disjoint, log a warning and compare only the intersection of features.
- [~] T034 [US3] Save `PredictiveModelArtifact` with metrics and hyperparameters.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final reporting and validation

- [~] T035 [US2/US3] Generate final report in `code/analysis/reporting.py`:
 - Include table of standardized coefficients (US2).
 - Include partial dependence plots for top 3 parameters (US3).
 - Include predictive model metrics (R², MAE, RMSE).
 - Include VIF and sensitivity analysis results.
- [~] T036 [P] Validate final report renders as PDF/Markdown within 30s on CI.
- [~] T037 [P] Update `research.md` with final findings and limitations.
- [~] T038 [P] Run full pipeline integration test (`main.py`) to ensure end-to-end execution ≤ 600s.
- [~] T039 [P] Run quickstart.md validation.

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data output; compares results with US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for unit conversion logic in code/tests/test_data_cleaning.py"
Task: "Unit test for missing value exclusion logic in code/tests/test_data_cleaning.py"

# Launch all models for User Story 1 together:
Task: "Implement data acquisition in code/data/acquisition.py"
Task: "Implement data cleaning in code/data/cleaning.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Data Feasibility**: All tasks are designed for CPU-only execution (Multiple cores, standard RAM capacity). and small datasets (<250 rows). No GPU or heavy deep learning models are used.
- **VIF Logic**: Strict adherence to FR-005: If Energy Density VIF > 5, drop components. This prevents tautological modeling.
- **Data Source Fallback**: T015 explicitly handles the missing HuggingFace dataset by proceeding with a warning and using paper tables as the primary source, ensuring the pipeline does not halt.
- **Edge Case Handling**: T024 and T030 explicitly handle convergence failures and small dataset sizes (N < 100) via LOAFO as per Plan and Spec requirements.
- **LOAFO Definition**: For N < 100, the "held-out test set" is the left-out alloy family in the LOAFO loop.