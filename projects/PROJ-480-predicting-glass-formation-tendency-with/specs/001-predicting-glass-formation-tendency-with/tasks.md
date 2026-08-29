# Tasks: Predicting Glass Formation Tendency with Machine Learning on Public Data

**Input**: Design documents from `/specs/001-predicting-glass-formation-tendency-with/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: `mkdir -p src/data src/models src/reports src/cli src/lib tests/contract tests/unit tests/integration data/raw data/processed state/ reports/`
- [X] T002 Initialize Python 3.11 project with dependencies: Create `pyproject.toml` with [dependencies] section containing `xgboost`, `pymatgen`, `scikit-learn`, `pandas`, `numpy`, `statsmodels`, `pyyaml`, `pytest`.
- [ ] T003 [P] Configure linting (flake8/ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `src/lib/constants.py` with fixed random seed (42), file paths (`data/`, `state/`, `src/`), and EXPLICIT validation thresholds: `MIN_SAMPLES=30`, `TARGET_SAMPLES=500`, `CIRCULARITY_THRESHOLD=0.99`, `VIF_RIDGE_THRESHOLD=10`, `VIF_PCA_THRESHOLD=30`.
- [X] T004b [P] Implement `src/lib/exceptions.py` with base error classes (`DataValidationError`, `CircularDataError`) and `src/lib/utils.py` with SHA-256 checksum calculation and logging helpers.
- [ ] T005 [P] Create `tests/contract/` directory and schema files (`dataset.schema.yaml`, `descriptor_set.schema.yaml`, `model_artifact.schema.yaml`) aligning with data-model.md
- [X] T006 Configure environment variable management: Create `.env.example` with keys and implement `src/lib/config.py` to load from `os.environ`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Aggregation, Target Detection, and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Automatically download metallic glass data from verified Zenodo source, detect target type, compute atomic descriptors, and produce a validated, checksummed dataset.

**Independent Test**: Running `src/data/download.py` and `src/data/descriptors.py` on a small subset produces a valid CSV with no nulls in predictors and a matching SHA-256 checksum in `state/`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T007 [P] [US1] Unit test for `src/data/descriptors.py` descriptor calculation logic in `tests/unit/test_descriptors.py`
- [X] T008 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`

### Implementation for User Story 1

- [X] T009 [US1] Implement `src/data/download.py`: Fetch data from **Zenodo DOI: 10.5281/zenodo.5778205** (experimental $D_c$). **MUST raise** on total failure; do NOT fall back to manual files or synthetic data. If network fails, the pipeline must halt with a clear error message to ensure reproducibility.
- [ ] T010 [US1] Implement `src/data/descriptors.py`: Compute Atomic Size Mismatch ($\delta$), Mixing Enthalpy ($\Delta H_{mix}$), and Electronegativity Difference ($\Delta \chi$) using `pymatgen`. Handle unknown elements by logging and excluding rows.
- [ ] T011 [US1] Implement `src/data/validation.py` (Complete): A single, comprehensive script implementing:
 1. Target detection (regression vs classification).
 2. Data hygiene (drop missing, log counts, validate chemical balance).
 3. Minimum sample count check (raise `DataValidationError` if < 30).
 4. **Lightweight linear circularity pre-check** (R² check only).
 5. **Provenance check**: Verify binary labels are empirically observed (explicit 'label' column) or derived from $D_c$ using a physical threshold (e.g., 1mm), not arbitrary statistical splits.
 6. **Do not** rely on stubs; this task implements the full logic for these specific checks.
- [ ] T012 [US1] Implement `src/data/pipeline.py`: Orchestrate download -> descriptor computation -> validation. Compute SHA-256 checksum of final dataset and update `state/projects/PROJ-480-...yaml` `artifact_hashes` map. **DO NOT** save to flat text file.
- [ ] T013 [US1] Add logging for all exclusion reasons (unknown element, missing target, unbalanced composition).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (produces `data/processed/clean_dataset.csv`).

---

## Phase 4: User Story 2 - CPU-Constrained Model Training, Validation, and Power Analysis (Priority: P2)

**Goal**: Train XGBoost (or Ridge if collinear) with 5-fold Cluster-Aware CV, ensure CPU feasibility, and perform post-hoc power analysis/MDES.

**Independent Test**: Executing `src/models/train.py` in a CPU-limited Docker container completes < 6 hours, outputs `state/model.pkl`, and generates `state/power_analysis.json`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T014 [P] [US2] Unit test for `src/models/train.py` 5-fold CV logic in `tests/unit/test_logo_cv.py`
- [ ] T015 [P] [US2] Integration test for end-to-end training with small subset in `tests/integration/test_training.py`

### Implementation for User Story 2

- [ ] T016 [US2] Implement `src/models/train.py` (Complete):
 1. Chemical Family derivation (majority element or "Multi-Component").
 2. **Primary Method**: **5-fold Cluster-Aware Cross-Validation** (stratified by chemical family) as required by FR-003.
 3. **Fallback**: If chemical families are too sparse for 5-fold (e.g., < 5 samples in a group), use Adaptive Leave-One-Group-Out (LOGO).
 4. Model selection logic: **Default to XGBoost** (regressor or classifier). **If VIF > 10, switch to Ridge Regression**. **If VIF > 30, switch to PCA + Ridge**.
 5. **Training Constraint**: If training exceeds 6 hours, first attempt to simplify the model (e.g., reduce `max_depth`, `n_estimators`). If still exceeded, raise `DataValidationError`. Log timing metrics.
 6. Save final trained model to `state/model.pkl`.
- [ ] T017 [US2] Implement `src/models/evaluate.py` (Complete): A single, comprehensive script implementing:
 1. **Post-hoc Power Analysis**: Calculate MDES and achieved power using `statsmodels.stats.power.FTestPower` (per FR-010). Save to `state/power_analysis.json`.
 2. Performance metrics (R²/AUC) calculation against baseline.
 3. Collinearity diagnostics (VIF calculation) and write scores to `state/model_artifact.json` with a 'comment' field.
 4. **Primary Circularity Check**: Perform **Linear Circularity Check (R² > 0.99)** as mandated by FR-013.
 5. **Secondary Robustness Check**: Perform permutation test (**1000 iterations**) to verify $P_{shuffled} < 0.95 \times P_{real}$.
 6. **Selection Bias measurement**: K-S statistic against Inoue's Rules synthetic distribution.
 7. Save all diagnostic results (VIF, Circularity status, Bias status) to `state/model_artifact.json` with comments.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Model trained, metrics saved).

---

## Phase 5: User Story 3 - Interpretability and Descriptor Ranking (Priority: P3)

**Goal**: Extract feature importances, perform collinearity diagnostics, and visualize top descriptor pairs.

**Independent Test**: Running `src/models/interpret.py` produces a ranked list of descriptors, VIF scores, and a PNG plot.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US3] Unit test for feature importance extraction in `tests/unit/test_interpret.py`

### Implementation for User Story 3

- [ ] T019 [US3] Implement `src/models/interpret.py` (Part 1): Feature importance extraction and ranking from the trained model.
- [ ] T020 [US3] Implement `src/models/interpret.py` (Part 2): Generate 2D visualization (Decision Boundary for classification, Partial Dependence for regression) for top 2 descriptors.
- [ ] T021 [US3] Implement `src/models/interpret.py` (Part 3): Permutation test (1000 iterations) to validate monotonic trend significance (p < 0.05) or AUC > 0.6 for top features. **Permute the feature values** (not the target) 1000 times and re-calculate **Spearman correlation** to determine the p-value.
- [ ] T022 [US3] Generate summary report identifying top 3 predictors and relative contribution percentages. **Calculate and report Recall and Precision variation**.

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all be independently functional.

---

## Phase 6: Verification of Diagnostics (Priority: P3)

**Goal**: Verify that the diagnostics (VIF, Circularity, Bias) implemented in US1 and US2 have been executed and results are recorded.

**Note**: The core logic for these diagnostics is implemented in **T011** (Validation) and **T017** (Evaluate). This phase focuses on ensuring these tasks are executed and results are aggregated.

### Tests for User Story 6 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US6] Unit test for circularity permutation test in `tests/unit/test_circularity.py`

### Verification for User Story 6

- [ ] T024 [US6] **Verify execution** of T011 (Provenance/Pre-check) and T017 (Robust Circularity/Bias). Ensure `state/model_artifact.json` contains the 'comment' fields for VIF and bias status as required by FR-008 and FR-015. This task confirms the artifacts exist and are valid.

**Checkpoint**: All diagnostics complete and recorded.

---

## Phase 7: User Story 4 - Threshold Sensitivity Analysis (Priority: P3)

**Goal**: Perform sensitivity analysis on classification threshold to find optimal operating point.

**Independent Test**: Running `src/reports/sensitivity.py` on a classifier produces a table of FPR/FNR rates and identifies the max F1 threshold.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US4] Unit test for threshold sweep logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 4

- [ ] T026 [US4] Implement `src/reports/sensitivity.py` (Part 1): Threshold sweep logic. **Skip if target_type != binary**. Sweep probability from **0.0 to 1.0 (inclusive)** in steps of 0.05 (**exactly 21 points**). Validate count == 21.
- [ ] T027 [US4] Implement `src/reports/sensitivity.py` (Part 2): Calculate False Positive Rate, False Negative Rate, **Recall, and Precision** for each threshold.
- [ ] T028 [US4] Implement `src/reports/sensitivity.py` (Part 3): Identify and report the threshold that maximizes F1-score. **Calculate and report Recall and Precision variation**.
- [ ] T029 [US4] Save sensitivity analysis results to `state/sensitivity_analysis.json`.

**Checkpoint**: At this point, User Stories 1-4 and 6 are complete.

---

## Phase 8: User Story 5 - Report Generation and Causal Framing (Priority: P3)

**Goal**: Generate final report framing findings as associational with explicit limitations.

**Independent Test**: Running `src/reports/generate.py` produces a report with no causal verbs in results and a "Limitations" section.

### Tests for User Story 5 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US5] Unit test for causal verb scanner in `tests/unit/test_report_generation.py`

### Implementation for User Story 5

- [ ] T031 [US5] Implement `src/reports/generate.py` (Part 1): Aggregate results from training, interpretability, and sensitivity analysis.
- [ ] T032 [US5] Implement `src/reports/generate.py` (Part 2): Enforce "Associational" framing. Scan generated text for causal verbs (causes, determines, leads to) and raise error or auto-correct if found.
- [ ] T033 [US5] Implement `src/reports/generate.py` (Part 3): Generate "Limitations" section explicitly stating observational nature, missing cooling rate data, and power constraints.
- [ ] T034 [US5] Check for selection bias (Inoue's Rules) using K-S statistic against synthetic reference distribution and include in report.
- [ ] T035 [US5] Output final report to `reports/final_report.md`.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates: Update `quickstart.md` with pipeline execution steps and data source instructions.
- [ ] T037 Code cleanup and refactoring (ensure no dead code from fallback logic).
- [ ] T038 Performance optimization: Verify memory usage stays < 7GB on full dataset.
- [ ] T039 [P] Run `pytest` full suite and ensure a perfect pass rate.
- [ ] T040 Run `quickstart.md` validation to ensure end-to-end reproducibility.

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output
- **User Story 6 (P3)**: Can start after Foundational (Phase 2) - Can run in parallel with US2/US3, but results feed into US5. **Must precede US5**.
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output (if binary). **Must precede US5**.
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Depends on US2, US3, US4, US6 outputs. **Must be last**.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Downloaders before Services/Validators
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for descriptor calculation logic in tests/unit/test_descriptors.py"
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/download.py"
Task: "Implement src/data/descriptors.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Data ingestion and descriptor computation)
5. Deploy/demo if ready (Data pipeline ready)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (Data Pipeline MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Model Training MVP!)
4. Add User Story 3, 4, 6 → Test independently → Deploy/Demo (Analysis MVP!)
5. Add User Story 5 → Test independently → Deploy/Demo (Report MVP!)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 6 (Diagnostics - can run early)
3. Stories complete and integrate independently into US3/US4/US5.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Integrity**: Never synthesize data. If download fails, raise error.
- **CPU Constraints**: Ensure all models run within 2-core, 7GB RAM limits. **Use XGBoost by default, but switch to Ridge/PCA if VIF thresholds are met**.
- **Scientific Rigor**: All findings must be framed as associational. Explicitly state limitations.
- **Versioning**: Artifact hashes MUST be recorded in the YAML state file, not flat text files.