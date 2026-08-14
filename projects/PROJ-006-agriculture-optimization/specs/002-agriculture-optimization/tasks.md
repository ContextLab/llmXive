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
- [ ] T002 {{claim:c_372956d9}} <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [ ] T003 [P] Configure linting and formatting tools (black, flake8, isort) and `.gitignore`
- [X] T004 Create `src/config/constants.py` with random seeds, paths, and cloud cover thresholds {0.6, 0.7, 0.8}
- [X] T005 Create `src/config/schemas.py` for internal contract definitions
- [X] T006 [P] Setup logging infrastructure in `src/utils/io_helpers.py`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create `contracts/dataset.schema.yaml` defining expected columns (household_id, CSA_Index, Stability_Score, HFIAS, etc.)
- [ ] T008 Create `contracts/output.schema.yaml` defining regression output structure
- [X] T009 Implement `src/utils/io_helpers.py` with strict CSV/Parquet I/O and checksum verification
- [ ] T010 [P] Create `src/data/generators/synthetic_generator.py` for CI validation ONLY; MUST raise `FatalError` if real data is missing AND `--synthetic` flag is NOT set, preventing silent fallback to mock data in production.
- [ ] T011 Setup `data/raw/`, `data/processed/`, `data/logs/` directory structure
- [X] T012 Create `src/cli/validate.py` to enforce schema contracts on ingestion

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ingest and Harmonize Multimodal Data (Priority: P1) 🎯 MVP

**Goal**: Download LSMS-ISA and Sentinel-2 data, perform spatial join, and construct the analysis-ready dataset.

**Independent Test**: Verify that `data/processed/analysis_dataset.csv` exists, contains non-null values for CSA Index and Stability Score, and passes `contracts/dataset.schema.yaml` validation.

### Implementation for User Story 1

- [X] T013 [P] [US1] Write contract test skeleton for dataset schema in `tests/contract/test_dataset_schema.py` (TDD: write test first).
- [X] T014 [P] [US1] Write integration test skeleton for ingestion pipeline in `tests/integration/test_ingestion.py` (validates implementation of T015-T018).
- [X] T015 [US1] Implement `src/data/collectors/survey_collector.py` to fetch LSMS-ISA (Malawi/Tanzania) with explicit URL handling and error logging. <!-- FAILED: unspecified -->
- [X] T015a [US1] Implement region selection logic in `src/data/collectors/survey_collector.py` to resolve the specific country (Malawi or Tanzania) and generate the canonical download URL (e.g., World Bank microdata portal pattern) and file format (.dta/.csv).
- [X] T015b [US1] Implement caching mechanism in `src/data/collectors/survey_collector.py` to check local storage, verify checksums against a cache manifest, and only download if missing or checksum mismatch.
- [X] T016 [US1] Implement `src/data/collectors/remote_sensing_collector.py` to fetch Sentinel-2 L2A imagery from the Copernicus Data Space Ecosystem API with streaming support and explicit caching (checksum verification). <!-- FAILED: unspecified -->
- [ ] T017 [US1] Implement `src/data/processing/spatial_join.py` to link household coordinates to satellite pixels using a Buffer intersection algorithm (fuzzing logic).
- [ ] T018 [US1] Implement `src/data/processing/feature_engineering.py` to construct CSA_Index and Stability_Score.
- [ ] T018a [US1] Implement temporal window mapping logic in `src/data/processing/feature_engineering.py` to map `survey_year` + `country` to specific growing season months (e.g., Malawi: March-May; Tanzania: March-May/Nov-Dec) for NDVI aggregation.
- [ ] T018b [US1] Implement NDVI time-series aggregation logic in `src/data/processing/feature_engineering.py` to calculate the Coefficient of Variation (CV) over the specific growing season (mapped in T018a) for each household's plot.
- [ ] T018c [US1] Implement Stability_Score calculation (1/CV) and CSA Index construction (sum of binary indicators + extension frequency) in `src/data/processing/feature_engineering.py`, including validation of the index against the survey data schema.
- [ ] T019 [US1] Implement `src/cli/run_pipeline.py` to orchestrate ingestion, joining, and feature engineering, ensuring it is parameterized for sensitivity analysis sweeps.
- [ ] T010a [US1] Implement integration wiring in `src/cli/run_pipeline.py` to enforce T010's 'fail loudly' behavior: check for `--synthetic` flag before calling collectors; if missing and real data absent, raise `FatalError` immediately.
- [ ] T020 [US1] Add error handling for missing coordinates and log exclusions to `data/logs/ingestion_errors.log`.
- [ ] T021 [US1] Implement village-level aggregation fallback in `src/data/processing/feature_engineering.py` with explicit conditional logic: Attempt household join -> Count N -> If N < 300, aggregate to village level using 'village_id' as key and 'mean' as function for CSA_Index and Stability_Score.
- [ ] T021a [US1] Implement verification step in `src/data/processing/feature_engineering.py` to confirm that the aggregated dataset meets statistical power requirements: verify effective sample size >= 300 OR variance reduction > 10% compared to household-level noise before proceeding.
- [ ] T022 [US1] Generate `data/processed/analysis_dataset.csv` and validate against schema.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Statistical Analysis and Diagnostics (Priority: P2)

**Goal**: Run multivariate regression models with robust standard errors and perform collinearity diagnostics.

**Independent Test**: Execution of `src/analysis/run_regression.py` produces a summary file containing regression coefficients, p-values, and VIF scores for both Yield Stability and Food Security models, completing within 60 minutes on CPU.

### Implementation for User Story 2

- [ ] T023 [P] [US2] Write contract test skeleton for regression output in `tests/contract/test_regression_output.py` (TDD).
- [ ] T024 [P] [US2] Write integration test skeleton for model execution in `tests/integration/test_regression.py` (validates T025).
- [ ] T025 [US2] Implement `src/analysis/run_regression.py` to fit Model 1 (Stability_Score) and Model 2 (HFIAS) using statsmodels with Robust standard errors (Huber-White) for heteroskedasticity, and output initial results to `data/processed/regression_results.json`.
- [ ] T025a [US2] Implement VIF calculation and flagging logic within `src/analysis/run_regression.py` to report VIF > 5 and annotate model summary.
- [ ] T025b [US2] Implement Bonferroni correction logic in `src/analysis/run_regression.py`: apply alpha=0.0167 (Wikipedia: Holm–Bonferroni method, https://en.wikipedia.org/wiki/Holm–Bonferroni_method) threshold, assert adjusted p-values are present in output JSON, and log the adjusted threshold explicitly.
- [ ] T026 [US2] Generate regression summary tables including coefficients, p-values, and VIF scores in `data/processed/regression_results.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Sensitivity Analysis and Final Report (Priority: P3)

**Goal**: Perform sensitivity analysis on cloud cover thresholds and generate the final associational report.

**Independent Test**: Execution of `src/analysis/sensitivity_check.py` produces a plot and table showing coefficient stability across threshold sweeps, and the final report includes the observational framing disclaimer.

### Implementation for User Story 3

- [ ] T028 [P] [US3] Write contract test skeleton for sensitivity output in `tests/contract/test_sensitivity.py` (TDD).
- [ ] T029 [P] [US3] Write integration test skeleton for report generation in `tests/integration/test_report.py` (validates T030-T035).
- [ ] T030 [US3] Implement `src/analysis/sensitivity_check.py` to sweep cloud cover thresholds over a representative set of values, re-run ingestion parameters, and output results to `data/processed/sensitivity_results.csv` and `reports/sensitivity_plot.png`.
- [ ] T031 [US3] Generate sensitivity plots showing variation in `CSA_Index` coefficient magnitude.
- [ ] T032 [US3] Implement report generator in `src/services/report_generator.py` to output to `reports/final_report.pdf` using matplotlib/reportlab.
- [ ] T033 [US3] Ensure final report explicitly states "associational" nature, Bonferroni adjustment, and the specific numerical threshold alpha=0.0167.
- [ ] T034 [US3] Include limitations section (observational design, spatial fuzzing, sample size).
- [ ] T035 [US3] Generate final PDF report with all tables, plots, and disclaimers.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` and `README.md`
- [ ] T037 Code cleanup and refactoring for type hints and modularity
- [ ] T038 [P] Additional unit tests in `tests/unit/` for helper functions
- [ ] T039 Security hardening (PII scan on commits, data privacy checks)
- [ ] T040 Run `quickstart.md` validation and fix any broken links

---

## Phase N+1: Research & Reproducibility (Addressing Reviewer Concerns)

**Purpose**: Address critical gaps identified in prior research-stage reviews regarding implementation completeness, data artifacts, and reproducibility.

**Goal**: Ensure actual code, data, and results exist to validate the pipeline, resolving the "Implementation Gap" and "No Data Artifacts" findings.

- [ ] T045 [US1] Execute the full data ingestion pipeline (T015-T022) locally to generate `data/processed/analysis_dataset.csv` for validation; DO NOT commit raw data to repository.
- [ ] T045a [US1] Verify `data/processed/analysis_dataset.csv` exists, has >300 records, and passes `contracts/dataset.schema.yaml` validation.
- [ ] T046 [US2] Execute the regression pipeline (T025-T027) locally to generate `regression_results.json` with valid coefficients and p-values; DO NOT commit raw results.
- [ ] T047 [US3] Execute the sensitivity and reporting pipeline (T030-T035) locally to generate `sensitivity_results.csv` and `final_report.pdf`; DO NOT commit raw reports.
- [ ] T041a [P] Run the Reference-Validator Agent on `research.md` to verify all citations; fail if any citation is unreachable or mismatch.
- [ ] T041b [P] Handle Reference-Validator failure: update `research.md` or remove invalid citations until verification passes.
- [ ] T041c [P] Update `quickstart.md` to document the Reference-Validator Agent as an automated gate for citation accuracy.
- [ ] T042 [P] Create `data-model.md` documenting entity relationships, variable definitions, and provenance sources.
- [ ] T043 [P] Create `quickstart.md` with executable instructions for reproducing the full pipeline from a clean checkout.
- [ ] T044 [P] Implement `Dockerfile` and `docker-compose.yml` for environment reproducibility.
- [ ] T048 [P] Add `README.md` to project root with project summary, installation steps, and link to final report.
- [ ] T055 [P] Resolve all `_TODO:` markers in `spec.md` (action) and Verify `spec.md` contains no `_TODO:` markers (check).
- [ ] T050 [P] Verify all test files (`tests/contract/`, `tests/integration/`) are present and pass against the generated artifacts.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Research & Reproducibility (Phase N+1)**: Depends on successful execution of US1, US2, US3 pipelines to generate artifacts locally

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
- Research & Reproducibility tasks (T041-T055) can run in parallel once artifacts are generated locally

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
- **Compute Feasibility**: All tasks must run on CPU-only free tier with limited RAM and disk resources. Use streaming for large datasets.
- **Reproducibility**: All artifacts (data, results, reports) must be generated by the pipeline, not hand-crafted.
- **Research Quality**: Spec must contain a falsifiable hypothesis and specific research gap; no TODOs allowed in final spec.