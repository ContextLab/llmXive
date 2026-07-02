# Tasks: Predicting Avian Song Variation with Climatic and Geographic Factors

**Input**: Design documents from `/specs/001-predicting-avian-song-variation/`
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

- [ ] T001a [P] Create directory structure script file (`scripts/create_dirs.sh` or `code/utils.py` function)
- [ ] T001b [P] Execute directory structure script to create `code/`, `data/raw/`, `data/processed/`, `output/`, `tests/` with specific paths defined in the script

- [ ] T002a [P] Create `requirements.txt` with dependencies: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `scipy`, `geopandas`, `rasterio`, `pytest`
- [ ] T002b Initialize Python 3.11 virtualenv and install dependencies from `requirements.txt` <!-- ATOMIZE: requested -->

- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Create `code/utils.py` with helper functions for logging, random state pinning, and memory monitoring
- [~] T005a [P] Implement data validation schema in `specs/001-predicting-avian-song-variation/contracts/analysis_output.schema.yaml`
- [~] T005b [P] Create `contracts/analysis_output.schema.yaml` defining the expected columns and types for `model_summary.csv`
- [~] T006 [P] Setup logging infrastructure to write to `output/logs/ingestion.log` and `output/logs/modeling.log`
- [~] T007 Create base configuration management to load paths from `plan.md` and environment variables
- [~] T008 Setup `state.yaml` tracking for Constitution Principle V (hashes and timestamps)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Variable Alignment (Priority: P1) 🎯 MVP

**Goal**: Ingest avian acoustic data and merge with climate/geographic variables into a single clean table.

**Independent Test**: The pipeline loads raw CSVs, joins by species/location, and outputs a single CSV with no missing core variables.

### Implementation for User Story 1

- [~] T009 [P] [US1] Implement `code/ingestion.py` to fetch acoustic metadata from Xeno-Canto API (filtered by target species) and save to `data/raw/acoustic_raw.csv`
- [~] T010 [P] [US1] Implement `code/ingestion.py` to fetch climate layers (WorldClim) and elevation (GEBCO) and save to `data/raw/climate_raw.csv` and `data/raw/elevation_raw.csv`
- [ ] T011 [US1] Implement data alignment logic in `code/ingestion.py`: Join acoustic, climate, and elevation data using `location_id` and `species`. Handle temporal mismatches by aggregating climate to recording date.
- [ ] T012 [US1] Implement missing data handling in `code/ingestion.py`: Flag or remove records with missing matches, generate `output/logs/missing_matches.log` (FR-006).
- [ ] T013 [US1] Implement Validation Check in `code/ingestion.py`: Calculate alignment success rate (`aligned_rows / total_raw_rows`). If < 95%, HALT execution, log error, and report failure. Do not proceed to modeling. (SC-001, plan.md Phase 0 Step 4).
- [ ] T015 [US1] Write final aligned dataset to `data/processed/aligned_dataset.csv`
- [ ] T016 [US1] Update `state.yaml` with new artifact hashes and timestamp (Constitution Principle V)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Exploratory Data Analysis and Correlation Matrix (Priority: P2)

**Goal**: Generate correlation matrix and scatterplot matrix; handle multicollinearity automatically.

**Independent Test**: Script produces a PDF report with correlation heatmap and scatterplots; applies PCA/Ridge/Lasso if |r| > 0.8.

### Implementation for User Story 2

- [ ] T017 [P] [US2] Implement `code/eda.py` to load `data/processed/aligned_dataset.csv`
- [ ] T018 [P] [US2] Implement correlation matrix generation (heatmap) in `code/eda.py` using `seaborn`
- [ ] T019 [US2] Implement multicollinearity detection in `code/eda.py`: Identify pairs with |r| > 0.8. If detected, apply PCA if > 2 correlated pairs, else apply Ridge/Lasso Regression; document method in `output/reports/eda_report.pdf` (FR-002).
- [ ] T020 [US2] Implement spatial autocorrelation check in `code/eda.py`: Perform Moran's I test on null model residuals; append statistic and p-value to `output/reports/eda_report.pdf`.
- [ ] T021 [US2] Implement scatterplot matrix generation (song metrics vs. climate variables) in `code/eda.py`
- [ ] T022 [US2] Generate `output/reports/eda_report.pdf` containing all visualizations and the multicollinearity handling documentation
- [ ] T023 [US2] Update `state.yaml` with new artifact hashes and timestamp

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Associational Modeling and Sensitivity Analysis (Priority: P3)

**Goal**: Fit linear regression/GLM, perform sensitivity analysis, and validate model stability.

**Independent Test**: Model runs on CPU, produces coefficients, sensitivity loop completes, and stability metrics are reported.

### Implementation for User Story 3

- [ ] T024 [P] [US3] Implement `code/modeling.py` to load `data/processed/aligned_dataset.csv`
- [ ] T025 [US3] Implement data splitting in `code/modeling.py`: Partition into train/hold-out using `train_test_split` with fixed `random_state` and stratification by species if sample sizes allow; otherwise use random split (FR-007).
- [ ] T026 [US3] Implement distributional check in `code/modeling.py`: Run Shapiro-Wilk test on residuals from an initial OLS model. Switch to GLM (Gamma/Poisson) if p < 0.05, and report the selected family in the output (FR-009, SC-008).
- [ ] T027 [US3] Implement model fitting in `code/modeling.py`: Check for presence of phylogenetic data file; if missing, default to geographic coordinates as proxies (FR-008). Fit the selected model (OLS or GLM) and calculate variance explained by confounders vs. climate using partial R-squared comparing full model to confounders-only baseline. Report the variance explained by these confounders (FR-008, SC-007).
- [ ] T028 [US3] Implement predictive stability check in `code/modeling.py`: Evaluate on hold-out set, calculate `r_squared_diff`. Flag if >= 0.10 (SC-006).
- [ ] T029 [US3] Implement sensitivity analysis loop in `code/modeling.py`: Sweep thresholds across the exact set {0.05, 0.1}, re-evaluate predictors, and record model fit metrics for each threshold (FR-004, SC-003). Do NOT calculate Cohen's f².
- [ ] T030 [US3] Implement convergence aggregation in `code/modeling.py`: Calculate convergence rate across species subsets where converged is defined as optimizer status == success, against total species subsets attempted. Append rate and flag status to `output/models/model_summary.csv` and `output/reports/analysis_report.pdf`. Flag if < 90% (SC-002).
- [ ] T031 [US3] Generate `output/models/model_summary.csv` with coefficients, p-values, R², `r_squared_diff`, and confounder_variance_explained. Explicitly include columns for confounder_variance_explained and r_squared_diff. All headers must include "Associational Analysis" (FR-003, SC-006, SC-007).
- [ ] T032 [US3] Generate `output/reports/analysis_report.pdf` compiling all metrics and sensitivity results. Ensure ALL headers in the report include the phrase "Associational Analysis" (FR-003).
- [ ] T033 [US3] Validate `model_summary.csv` against `contracts/analysis_output.schema.yaml` (FR-005).
- [ ] T034 [US3] Update `state.yaml` with final artifact hashes and timestamp (Constitution Principle V).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035a [P] Update `README.md` with usage instructions
- [ ] T035b [P] Update `docs/` with API reference
- [ ] T036a Refactor code based on linting results
- [ ] T036b Refactor code based on performance bottlenecks identified in T037
- [ ] T037 Performance optimization (ensure memory < 5.6 GB ([deferred] of 7 GB limit), runtime < 4.8h)
- [ ] T044 [P] Additional unit tests in `tests/unit/`
- [ ] T045 Run `quickstart.md` validation

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data output and US2 EDA insights

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
# Launch all tasks for User Story 1 together (if parallel capacity exists):
Task: "Fetch acoustic metadata from Xeno-Canto API"
Task: "Fetch climate layers and elevation data"
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