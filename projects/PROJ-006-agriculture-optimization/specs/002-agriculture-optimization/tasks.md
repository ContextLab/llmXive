# Tasks: Correlational Analysis of Climate‑Smart Agricultural Practices and Yield Stability Independent of Financial Access

**Input**: Design documents from `/specs/001-climate-smart-eval/`
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

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `contracts/`, `data/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pinned: pandas, numpy, scikit-learn, statsmodels, geopandas, rasterio, requests, pyyaml)
- [ ] T003 [P] Configure linting and formatting tools (black, flake8, isort) and `.gitignore`
- [ ] T004 Create `src/config/constants.py` with random seeds, paths, and cloud cover thresholds {, 0.7, 0.8}
- [ ] T005 Create `src/config/schemas.py` for internal contract definitions
- [ ] T006 [P] Setup logging infrastructure in `src/utils/io_helpers.py`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create `contracts/dataset.schema.yaml` defining expected columns (household_id, CSA_Index, Stability_Score, HFIAS, etc.)
- [ ] T008 Create `contracts/output.schema.yaml` defining regression output structure
- [ ] T009 Implement `src/utils/io_helpers.py` with strict CSV/Parquet I/O and checksum verification
- [ ] T010 Create `src/data/generators/synthetic_generator.py` for CI validation ONLY; MUST fail loudly (raise fatal error) if real data is missing and synthetic flag is not set, preventing silent fallback to mock data.
- [ ] T011 Setup `data/raw/`, `data/processed/`, `data/logs/` directory structure
- [ ] T012 Create `src/cli/validate.py` to enforce schema contracts on ingestion

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ingest and Harmonize Multimodal Data (Priority: P1) 🎯 MVP

**Goal**: Download LSMS-ISA and Sentinel-2 data, perform spatial join, and construct the analysis-ready dataset.

**Independent Test**: Verify that `data/processed/analysis_dataset.csv` exists, contains non-null values for CSA Index and Stability Score, and passes `contracts/dataset.schema.yaml` validation.

### Implementation for User Story 1

- [ ] T015 [US1] Implement `src/data/collectors/survey_collector.py` to fetch LSMS-ISA (Malawi/Tanzania) with explicit URL handling and error logging
- [ ] T015a [US1] Implement region selection logic in `src/data/collectors/survey_collector.py` to resolve the specific country (Malawi or Tanzania) and generate the canonical download URL (e.g., World Bank microdata portal pattern) and file format (.dta/.csv).
- [ ] T015b [US1] Implement caching mechanism in `src/data/collectors/survey_collector.py` to check local storage, verify checksums against a cache manifest, and only download if missing or checksum mismatch.
- [ ] T016 [US1] Implement `src/data/collectors/remote_sensing_collector.py` to fetch Sentinel-2 L2A imagery from the Copernicus Data Space Ecosystem API with streaming support and explicit caching (checksum verification).
- [ ] T017 [US1] Implement `src/data/processing/spatial_join.py` to link household coordinates to satellite pixels using a Buffer intersection algorithm

The research question investigates how spatial proximity influences intersection patterns, employing a buffer-based intersection method to analyze spatial relationships. References: [Citation to be inserted]. (fuzzing logic).
- [ ] T018 [US1] Implement `src/data/processing/feature_engineering.py` to construct CSA_Index and Stability_Score.
- [ ] T018a [US1] Implement NDVI time-series aggregation logic in `src/data/processing/feature_engineering.py` to calculate the Coefficient of Variation (CV) over the specific growing season (months -5) for each household's plot.
- [ ] T018b [US1] Implement Stability_Score calculation (1/CV) and CSA Index construction (sum of binary indicators + extension frequency) in `src/data/processing/feature_engineering.py`, including validation of the index against the survey data schema.
- [ ] T019 [US1] Implement `src/cli/run_pipeline.py` to orchestrate ingestion, joining, and feature engineering, ensuring it is parameterized for sensitivity analysis sweeps.
- [ ] T020 [US1] Add error handling for missing coordinates and log exclusions to `data/logs/ingestion_errors.log`.
- [ ] T021 [US1] Implement village-level aggregation fallback in `src/data/processing/feature_engineering.py` with explicit conditional logic: Attempt household join -> Count N -> If N < 300, aggregate to village level using 'village_id' as key and 'mean' as function for CSA_Index and Stability_Score.
- [ ] T022 [US1] Generate `data/processed/analysis_dataset.csv` and validate against schema.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: T014 (Integration Test) requires T019 (Pipeline) to be implemented before execution.

- [ ] T013 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py`
- [ ] T014 [P] [US1] Integration test for ingestion pipeline in `tests/integration/test_ingestion.py`; requires T019 to be implemented first to execute.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Statistical Analysis and Diagnostics (Priority: P2)

**Goal**: Run multivariate regression models with robust standard errors and perform collinearity diagnostics.

**Independent Test**: Execution of `src/analysis/run_regression.py` produces a summary file containing regression coefficients, p-values, and VIF scores for both Yield Stability and Food Security models, completing within 60 minutes on CPU.

### Implementation for User Story 2

- [ ] T025 [US2] Implement `src/analysis/run_regression.py` to fit Model 1 (Stability_Score) and Model 2 (HFIAS) using statsmodels with Robust standard errors (Huber-White) for heteroskedasticity, calculate VIF scores, apply Bonferroni correction by adjusting the significance threshold to alpha is set to a small significance threshold consistent with standard statistical practice., and output results to `data/processed/regression_results.json`.
- [ ] T026 [US2] Implement VIF calculation and flagging logic within `src/analysis/run_regression.py` (if not fully covered in T025) to report VIF > 5 and annotate model summary.
- [ ] T027 [US2] Generate regression summary tables including coefficients, p-values, and VIF scores in `data/processed/regression_results.json`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US2] Contract test for regression output in `tests/contract/test_regression_output.py`
- [ ] T029 [P] [US2] Integration test for model execution in `tests/integration/test_regression.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Sensitivity Analysis and Final Report (Priority: P3)

**Goal**: Perform sensitivity analysis on cloud cover thresholds and generate the final associational report.

**Independent Test**: Execution of `src/analysis/sensitivity_check.py` produces a plot and table showing coefficient stability across threshold sweeps, and the final report includes the observational framing disclaimer.

### Implementation for User Story 3

- [ ] T030 [US3] Implement `src/analysis/sensitivity_check.py` to sweep cloud cover thresholds over the specific set {0.6, 0.7, 0.8}, re-run ingestion parameters, and output results to `data/processed/sensitivity_results.csv` and `reports/sensitivity_plot.png`.
- [ ] T031 [US3] Generate sensitivity plots showing variation in `CSA_Index` coefficient magnitude.
- [ ] T032 [US3] Implement report generator in `src/services/report_generator.py` to output to `reports/final_report.pdf` using matplotlib/reportlab.
- [ ] T033 [US3] Ensure final report explicitly states "associational" nature, Bonferroni adjustment, and the specific numerical threshold alpha is set to a small positive value..
- [ ] T034 [US3] Include limitations section (observational design, spatial fuzzing, sample size).
- [ ] T035 [US3] Generate final PDF report with all tables, plots, and disclaimers.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T036 [P] [US3] Contract test for sensitivity output in `tests/contract/test_sensitivity.py`
- [ ] T037 [P] [US3] Integration test for report generation in `tests/integration/test_report.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` and `README.md`
- [ ] T039 Code cleanup and refactoring for type hints and modularity
- [ ] T040 [P] Additional unit tests in `tests/unit/` for helper functions
- [ ] T041 Security hardening (PII scan on commits, data privacy checks)
- [ ] T042 Run `quickstart.md` validation and fix any broken links

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 results

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Collectors before processors
- Processors before analysis
- Analysis before reporting
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
# Launch all collectors for User Story 1 together:
Task: "Implement src/data/collectors/survey_collector.py (Region Selection)"
Task: "Implement src/data/collectors/survey_collector.py (Caching/Download)"
Task: "Implement src/data/collectors/remote_sensing_collector.py"
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
   - Developer B: User Story 2 (Statistical Analysis)
   - Developer C: User Story 3 (Sensitivity & Reporting)
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
- **Data Integrity**: Never use synthetic data unless real data is unavailable AND the script fails loudly (no silent fallbacks).
- **Compute Feasibility**: All tasks must run on CPU-only free tier (GB RAM, 14GB disk). Use streaming for large datasets.