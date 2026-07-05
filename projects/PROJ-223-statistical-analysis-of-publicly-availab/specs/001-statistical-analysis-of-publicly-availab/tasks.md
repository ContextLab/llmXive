# Tasks: Statistical Analysis of Publicly Available Traffic Accident Data

**Input**: Design documents from `/specs/001-statistical-analysis-of-publicly-available-traffic-accident-data/`
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

- [ ] T001 Create project structure per implementation plan. Create directories: `code/`, `data/raw/`, `data/processed/`, `output/`, `tests/`, `docs/`, `state/`.
- [ ] T002 Initialize Python 3.11 project with `requirements.txt`. Create `requirements.txt` with pinned versions: `pandas==2.1.0`, `numpy==1.26.0`, `scikit-learn==1.3.0`, `statsmodels==0.14.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `requests==2.31.0`, `pyyaml==6.0.1`, `scipy==1.11.0`.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools. Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections in `code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 [P] Setup environment configuration management. Create `code/config.py` to load FARS/NOAA URLs from `research.md` and expose them as constants. <!-- FAILED: unspecified -->
- [ ] T005 [P] Implement schema validation helpers for raw and merged datasets
- [ ] T006 [P] Setup logging infrastructure to record data drop counts and model convergence status
- [~] T007 [P] Create base data processing utilities. Create `code/utils.py` with functions: `load_csv_chunked(path, chunk_size=10000)`, `optimize_memory(df)`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Merging (Priority: P1) 🎯 MVP

**Goal**: Download, clean, and merge FARS and NOAA datasets, filtering for valid records.

**Independent Test**: Verify output CSV contains only rows with non-null severity/weather data, row count ≤ min(input counts), and log reports dropped records.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T008 [P] [US1] Unit test for data download and checksum verification in `tests/test_data_ingestion.py`
- [~] T009 [P] [US1] Integration test for merge logic and null filtering in `tests/test_data_ingestion.py`

### Implementation for User Story 1

- [~] T010 [US1] Implement `code/01_data_ingestion.py` to download FARS (NHTSA) and NOAA GHCN-Daily data using verified URLs. Download to `data/raw/`, compute SHA-256, save to `state/checksums.json`.
- [~] T011 [US1] Implement schema validation in `code/01_data_ingestion.py` to ensure required columns exist.
- [~] T012 [US1] Implement merge logic in `code/01_data_ingestion.py` on timestamp/location. **Drop rows ONLY if structural keys (ID, Lat/Lon) are missing**. **Do NOT drop rows with missing weather data yet**; retain them for imputation in T019.
- [~] T013 [US1] Add robust clipping/winsorization in `code/01_data_ingestion.py`. Apply winsorization at the extreme lower and upper percentiles to temperature and precipitation columns.
- [~] T014 [US1] Log dropped record counts (structural only) and save interim merged dataset to `data/processed/merged_data_interim.csv`.
- [~] T015 [US1] Verify output row count and schema completeness in `code/01_data_ingestion.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Ordinal Logistic Regression Modeling (Priority: P2)

**Goal**: Fit Ordinal Logistic Regression (or fallback) to quantify weather impact on severity.

**Independent Test**: Model converges (or falls back) on CPU, returns coefficients, and produces odds ratios without GPU usage.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for ordinal encoding and model convergence in `tests/test_model_fitting.py`
- [ ] T017 [P] [US2] Integration test for fallback logic (Ordinal → Multinomial) in `tests/test_model_fitting.py`

### Implementation for User Story 2

- [ ] T018 [US2] [Preprocessing] Implement severity encoding (0=Property, 1=Injury, 2=Fatality) in `code/02_preprocessing.py`.
- [ ] T019 [US2] [Preprocessing] Implement Multiple Imputation (MICE) for missing **non-critical** weather data in `code/02_preprocessing.py`. **Execute this AFTER T012**. After imputation, **drop any remaining rows with missing weather data** to ensure the final dataset is complete.
- [ ] T020 [US2] [Modeling] Implement `code/03_model_fitting.py` to fit Ordinal Logistic Regression using `statsmodels`.
- [ ] T021 [US2] [Modeling] Implement proportional odds assumption check (Brant test/LRT) in `code/03_model_fitting.py`.
- [ ] T022 [US2] [Modeling] Implement fallback to Multinomial Logistic Regression if assumption violated in `code/03_model_fitting.py`.
- [ ] T023 [US2] [Modeling] Calculate and report odds ratios (or relative risk ratios) with confidence intervals in `code/03_model_fitting.py`.
- [ ] T024 [US2] [Modeling] Add a timeout wrapper in `code/03_model_fitting.py` that raises `TimeoutError` if execution exceeds **6 hours**, and log the duration.
- [ ] T025 [US2] [Diagnostics] **Check Multicollinearity**. Calculate VIF scores for all predictors in `code/03_model_fitting.py`. Flag if VIF > 5.
- [ ] T026 [US2] [Modeling] **Apply Regularization if Needed**. If VIF > 5 (from T025):
 1. Attempt to re-fit the model using `statsmodels` `OrderedModel` with `fit_regularized` (L2 penalty) if available.
 2. If that fails, switch to `statsmodels` `GLM` with `family=Binomial` (Binary Logistic) as a fallback for the ordinal outcome, OR
 3. Switch to `statsmodels` `GLM` with `family=Binomial` and `cov_type='HC3'` (Robust estimator) if Ridge is unsuitable.
 **Report the regularized/robust coefficients** to `output/reports/regularized_coefficients.json`.
- [ ] T027 [US2] [Diagnostics] **Sensitivity Analysis (MDE)**. Calculate the **Minimum Detectable Effect (MDE)** for OR=1.5 using `statsmodels.stats.power` on the final model (after switch and Ridge/Robust). Write result (MDE value, sample size) to `output/reports/sensitivity_analysis.json`. Verify **MDE < 1.5** (sufficient).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Diagnostics and Visualization (Priority: P3)

**Goal**: Perform diagnostics (VIF, LRT) and generate visualizations.

**Independent Test**: VIF scores calculated, Ridge applied if VIF>5, plots generated as image files.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for VIF calculation and Ridge fallback in `tests/test_diagnostics.py`
- [ ] T029 [P] [US3] Integration test for plot generation and file output in `tests/test_diagnostics.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement Likelihood Ratio Test and McFadden's Pseudo R-squared calculation in `code/04_diagnostics.py`.
- [ ] T031 [US3] Implement Cluster-Robust Standard Errors (CRSE) calculation if needed in `code/04_diagnostics.py`.
- [ ] T032 [US3] Generate coefficient plot and odds ratio table. Generate `coefficient_plot.png` and **`odds_ratio_table.png`** (visual artifact) and `odds_ratio_table.csv` (data artifact) in `code/05_visualization.py`.
- [ ] T033 [US3] Save visualizations to `output/plots/` and statistical summaries to `output/reports/`.
- [ ] T034 [US3] Verify all required outputs exist and are non-empty in `code/05_visualization.py`. Ensure `odds_ratio_table.csv` is machine-readable.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` and `README.md`
- [ ] T036 Code cleanup and refactoring across `code/`
- [ ] T037 Performance optimization (memory usage) across all scripts
- [ ] T038 [P] Additional unit tests for edge cases (empty data, extreme outliers) in `tests/`
- [ ] T039 [P] Execute the command defined in `quickstart.md` (e.g., `python code/01_data_ingestion.py && python code/03_model_fitting.py`) and verify exit code 0.

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
- **Data Flow**: T010 (Ingestion) → T012 (Structural Drop) → T019 (MICE + Final Drop) → T018 (Preprocessing) → T020 (Modeling) → T025 (VIF) → T026 (Ridge/Robust) → T027 (MDE) → T030 (Diagnostics) → T032 (Visualization)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (Preprocessing before Modeling)
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
Task: "Unit test for data download and checksum verification in tests/test_data_ingestion.py"
Task: "Integration test for merge logic and null filtering in tests/test_data_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement schema validation in code/01_data_ingestion.py"
Task: "Implement robust clipping for outliers in code/01_data_ingestion.py"
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
- **Constraint**: All tasks must run on CPU-only CI with limited core count, constrained RAM, and limited disk. No GPU/CUDA.
- **Data Integrity**: Use only real datasets from verified URLs (NHTSA, NOAA). No synthetic data fabrication.