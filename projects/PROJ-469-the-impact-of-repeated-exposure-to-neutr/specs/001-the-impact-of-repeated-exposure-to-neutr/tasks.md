# Tasks: The Impact of Self‑Reported Political News Exposure on Implicit Political Bias

**Input**: Design documents from `/specs/001-political-news-implicit-bias/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: `mkdir -p code/ data/raw/ data/processed/ results/ logs/`
- [X] T002 Initialize Python 3.11 project: Create `requirements.txt` with pinned versions for `pandas`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `scipy`, `jinja2`, `pyyaml`, `pytest`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes strict data validation and a priori power analysis.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` defining seeds, paths, alpha thresholds (0.01, 0.05, 0.10), and bootstrap count (n=1000)
- [X] T005 [P] Implement `code/data_loader.py` skeleton to load CSV, validate existence of `data/raw/`, and raise `ValueError` if no data found
- [X] T005b [P] Document IAT Protocol: Extract and record the specific IAT stimulus set and software version from the dataset's source metadata into `code/iat_protocol.md` to satisfy Constitution Principle VI for static data analysis. <!-- FAILED: unspecified -->
- [X] T006 Implement `code/preprocessing.py` skeleton: Define function signatures `load_data`, `impute_mice`, `derive_variables` and raise `NotImplementedError` in placeholders
- [ ] T007 Create `contracts/dataset.schema.yaml` defining columns `IAT_D_score`, `political_ideology`, `news_exposure_freq` and validation logic
- [ ] T008 Configure error handling and logging infrastructure in `code/` (logging to `logs/` and console)
- [ ] T009 Setup environment configuration management (`.env` or `config.yaml` for data paths)
- [~] T017a [P] **A Priori Power Analysis**: Create `code/power.py` to calculate the minimum sample size required to detect the interaction effect with power ≥ 0.80 at α = 0.05 using literature-based effect sizes. Output `results/power_design.csv` with `required_n` and `met_target` status. This task MUST complete before US1.
- [ ] T038 [P] **Data Acquisition**: Implement `code/data_fetcher.py` to fetch the "Political IAT" dataset from the Project Implicit canonical source. **If the specific dataset URL is unknown or unavailable, the script MUST halt with a clear `ValueError` stating "Real data source not found." DO NOT use fallback datasets (e.g., NAB) or generate synthetic data.** <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Associational Analysis (Priority: P1) 🎯 MVP

**Goal**: Load Project Implicit data, map variables via codebook, handle missing data (MICE), and fit the primary linear regression model with interaction.

**Independent Test**: Execute the data loading, imputation, and regression pipeline on a subset of data; verify output coefficients, p-values, and imputation diagnostics in `results/diagnostics.csv`.

### Tests for User Story 1 (OPTIONAL) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for data loading: Implement `test_load_raises_valueerror_on_missing_columns` in `tests/unit/test_data_loader.py`
- [X] T011 [P] [US1] Unit test for MICE imputation logic (missingness < 50% check) in `tests/unit/test_preprocessing.py`
- [X] T012 [P] [US1] Unit test for regression model fitting and interaction term extraction in `tests/unit/test_models.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data_loader.py` to map raw columns to `IAT_D_score`, `political_ideology`, `news_exposure_freq` using codebook; raise `ValueError` on failure
- [~] T014 [US1] Implement `code/preprocessing.py` MICE imputation (5 imputations) with missingness rate check (>50% halts); implement logging of warning message if missingness > 50%; output imputed data to `data/processed/imputed_data.csv`
- [X] T015 [US1] Implement `code/models.py` to fit primary linear regression: `IAT_D ~ news_exposure_z * political_ideology` (continuous)
- [X] T016 [US1] Implement derived variable creation in `code/preprocessing.py`: `news_exposure_z` (z-scored) and `ideology_binary` (median split for later use)
- [ ] T017b [US1] **Retrospective Power Analysis**: Calculate `observed_power` using fitted model effect size; output to `results/power_analysis.csv` with columns: `observed_power`, `required_n`, `effect_size`, `met_target`. (Distinct from T017a).
- [X] T018 [US1] Integrate pipeline in `code/main.py` (Load -> Impute -> Model) and save initial results <!-- SKIPPED: YAML+regex parse failed (while scanning a simple key
 in "<unicode string>", line 9, column 1:
 Additionally, the supporting fil...
 ^
could not find expected ':'
 in "<unicode string>", line 11, column 1:
 **Note**: Running `python code/m...
 ^) -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Robustness & Sensitivity Checks (Priority: P2)

**Goal**: Validate stability via bootstrap, test alpha sensitivity, and verify robustness against model specification changes.

**Independent Test**: Run bootstrap, alpha sweep, and covariate model; verify confidence intervals, significance status changes, and coefficient magnitude changes are reported.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T019 [P] [US2] Unit test for bootstrap resampling loop (1000 iterations) and Monte Carlo SE calculation in `tests/unit/test_robustness.py`
- [X] T020 [P] [US2] Unit test for alpha sweep logic (0.01, 0.05, 0.10) in `tests/unit/test_robustness.py`

### Implementation for User Story 2

- [ ] T024b [US2] **Binary Model Fit**: Re-fit linear regression using `ideology_binary` (from T016) instead of continuous ideology; report results (coefficient/significance) and save to `results/binary_model.csv`. **Must complete before T021-T023.**
- [X] T021 [US2] Implement `code/robustness.py` bootstrap procedure (1000 resamples); calculate Monte Carlo SE and confidence interval for interaction term; ensure resamples complete without partial state logic
- [~] T022 [US2] Implement alpha sweep in `code/robustness.py` to re-evaluate significance at thresholds **{0.01, 0.05, 0.10}**; report variation in significance status; save results to `results/alpha_sweep.csv`
- [X] T023 [US2] Implement covariate adjustment model in `code/models.py`: Re-fit model from scratch using imputed data and added covariates (`age`, `gender`, `education`); compare interaction coefficient magnitude/significance to primary model
- [X] T025 [US2] Integrate robustness checks into `code/main.py` pipeline after primary model
- [ ] T026 [US2] Save robustness metrics (bootstrap CI, alpha sweep results, covariate comparison, binary model results) to `results/robustness_metrics.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reporting & Artifact Generation (Priority: P3)

**Goal**: Generate consolidated PDF report and CSV summary tables containing all model summaries, effect sizes, power analysis, and plots.

**Independent Test**: Inspect `results/` directory for `report.pdf` (≤ 5 MB) and `model_summary.csv` after pipeline completion.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T027 [P] [US3] Integration test for report generation (file existence and size check) in `tests/integration/test_reporting.py`

### Implementation for User Story 3

- [ ] T028 [US3] Create `code/reporting.py`: Create `templates/report.j2` with sections: Methods, Primary Model, Robustness, Power Analysis, Plots; generate PDF report using `jinja2`
- [ ] T029 [US3] Generate CSV summary tables (`model_summary.csv`, `diagnostics.csv`) aggregating coefficients, p-values, and imputation stats
- [ ] T030 [US3] Implement plotting functions (interaction plot, bootstrap distribution) using `seaborn`/`matplotlib` and embed in report
- [ ] T031 [US3] Integrate reporting step into `code/main.py` as the final pipeline stage
- [ ] T032 [US3] Ensure all artifacts are written to `results/` directory with correct filenames and constraints (PDF ≤ 5 MB)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T033 [P] Add unit tests for edge cases (missing columns, >50% missingness, bootstrap timeout) in `tests/unit/`
- [ ] T034 Code cleanup and refactoring to ensure CPU-only compliance (no GPU imports, memory-efficient loops)
- [ ] T035 Refactor `code/robustness.py` to use multiprocessing or chunking to ensure runtime < 6h on 2-core CPU; verify by local benchmark
- [ ] T036 [P] Update `docs/README.md` with execution instructions and data requirements
- [ ] T037 Run `quickstart.md` validation and final end-to-end test on sample data

---

## Phase 7: Data Acquisition & Validation (Critical Path for Real Results)

**Goal**: Address the "Real Data" constraint by implementing a robust, verified data fetch mechanism to prevent fabrication and ensure reproducibility.

**Independent Test**: Verify that `code/data_fetcher.py` successfully downloads a sample subset of the Project Implicit data (or halts with a clear error) and validates it against the schema without raising a `ValueError` for missing columns.

### Implementation for Data Acquisition

- [ ] T038 [P] [US1] **Data Fetch**: Implement `code/data_fetcher.py` to fetch the "Political IAT" dataset from the Project Implicit canonical source. **If the specific dataset URL is unknown or unavailable, the script MUST halt with a clear `ValueError` stating "Real data source not found." DO NOT use fallback datasets (e.g., NAB) or generate synthetic data.**
- [ ] T039 [US1] Implement `code/data_loader.py` logic to verify the downloaded file against `contracts/dataset.schema.yaml` immediately after fetch; raise `ValueError` with specific missing columns if validation fails.
- [ ] T040 [US1] Create `data/raw/.gitkeep` and `data/raw/README.md` documenting the exact source URL used and the date of download to ensure provenance.
- [ ] T041 [US1] Implement a "dry-run" data fetch in `code/main.py` that downloads the first 100 rows to `data/processed/sample_data.csv` for local testing of the pipeline without requiring the full dataset.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes T038 (Data Fetch) and T017a (A Priori Power).**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (Phase 3)**: Depends on T038 (Data Fetch) and T017a (A Priori Power) completion.
 - **US2 (Phase 4)**: Depends on US1 completion.
 - **US3 (Phase 5)**: Depends on US1 and US2 completion.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) and Data Acquisition (Phase 7) - No dependencies on other stories. **Produces the core data and model.**
- **User Story 2 (P2)**: Depends on US1 completion (needs primary model and data) to perform robustness checks.
- **User Story 3 (P3)**: Depends on US1 and US2 completion (needs all results) to generate the final report.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Loaders before Robustness/Reporting
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **Data Acquisition (Phase 7) tasks (T038) MUST complete before Phase 3 (US1) begins.**
- Once Foundational and Data Acquisition are done, US1 can start immediately; US2 and US3 must wait for US1 data/model
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data loading in tests/unit/test_data_loader.py"
Task: "Unit test for MICE imputation in tests/unit/test_preprocessing.py"

# Launch all models for User Story 1 together:
Task: "Implement data_loader.py in code/data_loader.py"
Task: "Implement preprocessing.py skeleton in code/preprocessing.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 7: Data Acquisition (Ensure real data source is defined and fetchable)
4. Complete Phase 3: User Story 1 (Load, Impute, Primary Model)
5. **STOP and VALIDATE**: Test User Story 1 independently on real data
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational + Data Acquisition → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Core Analysis)
 - Developer B: User Story 2 (Robustness - can start once US1 data is ready)
 - Developer C: User Story 3 (Reporting - can start once US1/US2 are ready)
 - Developer D: Data Acquisition (Phase 7) - Critical path for all
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
- **Critical Constraint**: All tasks must run on CPU-only CI with limited computational resources. Do not use GPU libraries or large models.
- **Data Constraint**: Tasks must use real data from user-provided path or verified source. **NO FAKE DATA GENERATION.** If a real source cannot be verified, the task must halt with a clear error, not generate synthetic data.
- **Feasibility Check**: T021 (Bootstrap) and T035 (Multiprocessing) are critical to ensure the 6-hour limit is met on 2 cores.
- **Power Analysis**: T017a (A Priori) must run before T013-T018. T017b (Retrospective) runs after model fitting.