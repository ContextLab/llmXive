# Tasks: The Use of Climate-Smart Agricultural Practices in Rural Areas to Improve Food Security and Livelihoods

**Input**: Design documents from `/specs/001-csa-food-security/`
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

- [X] T001a [P] Create project directories: `code/`, `data/`, `tests/`, `specs/`
- [X] T001b [P] Create `__init__.py` files in all `code/` sub-packages (`data/`, `analysis/`, `viz/`, `utils/`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, numpy, scikit-learn, statsmodels, geopandas, matplotlib, seaborn, requests, pyyaml)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup directory structure for `data/raw/`, `data/processed/`, and `state/` for checksums
- [X] T005 [P] Implement `code/utils/logging.py` for provenance logging (mapping derived variables to raw IDs)
- [X] T006 [P] Create `code/utils/config.py` to manage environment variables (target countries, years, RAM limits)
- [X] T007 Create base data schema definitions in `specs/001-csa-food-security/contracts/dataset.schema.yaml`
- [X] T008 [P] Implement `code/data/download.py` with function stubs: `download_lsms(country, year)`, `download_nasa_power(lat, lon, start, end)`, `download_faostat(indicator)`
- [X] T009 Setup pytest environment in `tests/` with configuration for CPU-only execution

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download, clean, merge, and sample LSMS, FAOSTAT, and NASA POWER data into a single analysis-ready dataset.

**Independent Test**: Execute `code/data/pipeline.py` and verify `data/processed/merged_sample.parquet` contains ≥ 95% valid records, no missing values in key predictors after imputation, and matches the schema.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_dataset_schema.py`
- [ ] T011 [P] [US1] Integration test for download and merge pipeline in `tests/integration/test_data_pipeline.py` <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement LSMS downloader in `code/data/download.py` targeting Kenya, India, Vietnam (-2023) with error handling for missing years
- [~] T013 [P] [US1] Implement NASA POWER climate downloader in `code/data/download.py` using `requests` and nearest-neighbor spatial interpolation for gaps ≤ 3 months
- [~] T014 [P] [US1] Implement FAOSTAT agricultural indicator downloader in `code/data/download.py`
- [~] T015 [US1] Implement data cleaning and merging logic in `code/data/clean.py`:
 - Merge using country code + year
 - Match climate data to survey coordinates within a **local radius** (growing season avg: a period of several months prior to harvest)
 - Flag unmatched rows and log warnings
- [~] T016 [US1] Implement imputation strategy in `code/data/clean.py` for missing predictor values
- [~] T017 [US1] Implement stratified sampling with **design weights** in `code/data/clean.py` to ensure ≤ 7GB RAM and target N ≥ 5000 households per country; **calculate and apply survey design weights** to preserve design effects for the Mixed-Effects Model
- [~] T018 [US1] Implement provenance logger in `code/utils/logging.py` to log a JSON mapping every component variable (e.g., conservation_tillage_score) to its source LSMS question ID and response ID
- [~] T019 [US1] Create `code/main.py` entry point to orchestrate the full data pipeline (Download → Clean → Save) **(Must run after T012-T018)**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean, merged, sampled dataset ready)

---

## Phase 4: User Story 2 - Statistical Modeling and Analysis (Priority: P2)

**Goal**: Fit Mixed-Effects Regression models to quantify associational relationships between CSA adoption and food security, including interaction terms and mediation analysis.

**Independent Test**: Run `code/analysis/model.py` on a sample subset and verify output includes standardized coefficients, p-values, VIF scores, and random effect estimates without runtime errors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`
- [~] T021 [P] [US2] Unit test for VIF calculation and collinearity flagging in `tests/unit/test_diagnostics.py`

### Implementation for User Story 2

- [~] T022 [US2] Implement CSA Index construction in `code/data/features.py`:
 - Weighted composite score (conservation tillage, crop diversification, irrigation efficiency)
 - **Exclude** digital-technology access and finance access variables from the index calculation to maintain independence from moderation terms (as per Plan Technical Context)
 - Normalize to a unit scale.
- [~] T024 [US2] Implement collinearity diagnostics in `code/analysis/diagnostics.py`:
 - Calculate VIF for all predictors
 - Flag predictors exceeding VIF > 5.0 (log warning, do not auto-exclude mediators)
- [~] T023 [US2] Implement Mixed-Effects Regression model in `code/analysis/model.py`: <!-- FAILED: unspecified -->
 - Include interaction terms for digital and finance access (moderation)
 - Include mediation analysis for digital/finance access (indirect effects) per Constitution Principle VII
 - Apply stratified sampling weights
 - Frame all findings as associational (no causal language)
- [~] T025 [US2] Implement multiple hypothesis correction in `code/analysis/model.py`:
 - Apply **Benjamini-Hochberg FDR correction** (replacing Bonferroni) for > 5 hypotheses to control false discovery rate in hierarchical data
- [~] T025b [US2] Verify Benjamini-Hochberg FDR correction implementation against Plan requirements in `tests/unit/test_model_correction.py`
- [~] T026 [US2] Implement robustness check logic in `code/analysis/model.py`:
 - Alternative variable specifications
 - Sensitivity analysis on CSA adoption threshold (sweep moderate to strict cutoffs) and **report variance in significance rates** as per FR-007
- [~] T027 [US2] Implement timeout handling in `code/analysis/model.py` to log state and **attempt a reduced-batch retry** if > 6 hours
- [~] T028 [US2] Implement timeout verification and performance benchmarking in `tests/integration/test_model_timeout.py` to measure convergence time against GitHub Actions free-tier limit (SC-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (model fitted, diagnostics run, results outputted)

---

## Phase 5: User Story 3 - Visualization and Robustness Reporting (Priority: P3)

**Goal**: Generate scatter plots, coefficient plots, regional maps, and perform robustness checks (leave-one-region-out, bootstrap resampling).

**Independent Test**: Execute `code/viz/plots.py` and verify that multiple distinct plot types are saved to `output/` and robustness logs are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T029 [P] [US3] Contract test for plot output files in `tests/contract/test_plot_outputs.py`
- [~] T030 [P] [US3] Integration test for robustness check execution in `tests/integration/test_robustness.py`

### Implementation for User Story 3

- [~] T031 [US3] Implement scatter plot generation in `code/viz/plots.py` (CSA Index vs. Food Security) **(Must run after T023)**
- [~] T032 [US3] Implement coefficient plot generation in `code/viz/plots.py` (standardized coefficients with confidence intervals)
- [~] T033 [US3] Implement regional map generation in `code/viz/plots.py` using `geopandas` to visualize spatial distribution of CSA adoption and outcomes
- [~] T034 [US3] Implement distribution plot generation in `code/viz/plots.py`
- [~] T035 [US3] Implement leave-one-region-out cross-validation in `code/analysis/robustness.py` **(Must run after T023)**
- [~] T036 [US3] Implement bootstrap resampling with a sufficient number of iterations. in `code/analysis/robustness.py` to validate model stability and report variance estimates
- [~] T037 [US3] Create `code/main.py` entry point extension to orchestrate the full analysis and viz pipeline (Model → Diagnostics → Robustness → Plots)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T038 [P] Documentation updates in `specs/001-csa-food-security/quickstart.md`
- [~] T039 Code cleanup and refactoring in `code/`
- [~] T040 Performance optimization for model fitting (batching, efficient memory usage)
- [~] T041 [P] Additional unit tests for edge cases (missing years, climate gaps, VIF > 5.0) in `tests/unit/`
- [ ] T042 Run quickstart.md validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model results from US2

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
- **Note**: Within User Story 2, tasks T022, T024, T023, T025 form a strict linear chain (Index -> Diagnostics -> Model -> Correction) and **cannot** run in parallel.
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_dataset_schema.py"
Task: "Integration test for download and merge pipeline in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement LSMS downloader in code/data/download.py"
Task: "Implement NASA POWER climate downloader in code/data/download.py"
Task: "Implement FAOSTAT agricultural indicator downloader in code/data/download.py"
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
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Statistical Modeling)
 - Developer C: User Story 3 (Visualization & Robustness)
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
- **Constraint Check**: All tasks must run on CPU-only CI with a limited number of cores and approximately 7GB RAM, with no GPU.. No 8-bit/4-bit quantization, no CUDA, no large LLMs.
- **Data Integrity**: Use real data sources (LSMS, FAOSTAT, NASA POWER) only. No synthetic data fabrication.