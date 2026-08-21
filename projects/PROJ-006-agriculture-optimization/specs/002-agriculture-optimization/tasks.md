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

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `contracts/`, `data/`). **Verification**: Run `ls -R` to confirm all directories exist and are empty.
- [ ] T002 Create `src/utils/state_manager.py` to handle artifact hashing and update `state/projects/PROJ-006-agriculture-optimization.yaml` with content hashes for `data/raw/*` and `data/processed/*`. **Verification**: Run a dry-run hash calculation on a dummy file to confirm the update mechanism works.
- [ ] T003 [P] Configure linting and formatting tools (black, flake8, isort) and `.gitignore`
- [X] T004 Create `src/config/constants.py` with random seeds, paths, and cloud cover thresholds {0.6, 0.7, 0.8}
- [X] T005 Create `src/config/schemas.py` for internal contract definitions
- [X] T006 [P] Setup logging infrastructure in `src/utils/io_helpers.py`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create `contracts/dataset.schema.yaml` defining expected columns (household_id, CSA_Index, Stability_Score, HFIAS, etc.). **Verification**: Write a small Python script to load this YAML and validate it against `pydantic` or `jsonschema` to ensure it is syntactically valid and loadable.
- [ ] T008 Create `contracts/output.schema.yaml` defining regression output structure. **Verification**: Write a small Python script to load this YAML and validate it against `pydantic` or `jsonschema` to ensure it is syntactically valid and loadable.
- [X] T009 Implement `src/utils/io_helpers.py` with strict CSV/Parquet I/O and checksum verification
- [ ] T010 Implement `src/data/generators/synthetic_generator.py` as a **utility only**. **Logic**: This script MUST NOT be called automatically by the pipeline. It exists solely for manual data generation if a user explicitly runs it. The pipeline must NOT invoke this to bypass real data requirements. **Requirements**: Use Multivariate Normal distributions for continuous variables (land_size, education) and Bernoulli for binary variables (finance_access, practice_*), with a fixed random seed (e.g., 42) to ensure deterministic generation. Correlations between variables must mimic real survey data (e.g., positive correlation between education and finance access).
- [ ] T010a Implement integration wiring in `src/cli/run_pipeline.py` to enforce "Fail Loudly" behavior (prerequisite: T010). **Logic**: Check for `--synthetic` flag (default: False). If real data is missing and `--synthetic` is NOT provided, raise a `FatalError` immediately with the message: "Real data missing. Use --synthetic flag for CI validation or provide real data in data/raw/". Do NOT call the synthetic generator automatically.
- [ ] T010b Configure the CI workflow (`.github/workflows/ci.yml`) to invoke the pipeline with `--synthetic` flag when real data is missing, ensuring automated reproducibility. **Verification**: Run a dry-run CI job to confirm the flag is passed and the synthetic generator is invoked.
- [ ] T011 Setup `data/raw/`, `data/processed/`, `data/logs/` directory structure. **Verification**: Run `ls -R data/` to confirm directory tree exists.
- [X] T012 Create `src/cli/validate.py` to enforce schema contracts on ingestion
- [X] T012a [P] Implement integration wiring in `src/cli/run_pipeline.py` to enforce "Fail Loudly" behavior (prerequisite: T010). **Logic**: Check for `--synthetic` flag (default: False). If real data is missing and `--synthetic` is NOT provided, raise a `FatalError` immediately with the message: "Real data missing. Use --synthetic flag for CI validation or provide real data in data/raw/". Do NOT call the synthetic generator automatically. (Note: This task is a duplicate of T010a; T010a is the authoritative version. T012a is removed in the final list.)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ingest and Harmonize Multimodal Data (Priority: P1) 🎯 MVP

**Goal**: Download LSMS-ISA and Sentinel-2 data, perform spatial join, and construct the analysis-ready dataset.

**Independent Test**: Verify that `data/processed/analysis_dataset.csv` exists, contains non-null values for CSA Index and Stability Score, and passes `contracts/dataset.schema.yaml` validation.

### Implementation for User Story 1

- [X] T013 [P] [US1] Write contract test skeleton for dataset schema in `tests/contract/test_dataset_schema.py` (TDD: write test first).
- [X] T014 [P] [US1] Write integration test skeleton for ingestion pipeline in `tests/integration/test_ingestion.py` (validates implementation of T015-T022).
- [X] T015 [US1] [FR-001] Implement `src/data/collectors/survey_collector.py`. Specifics: Construct canonical World Bank microdata URL (Malawi/Tanzania), handle authentication, extract fields (`household_id`, `latitude`, `longitude`, `practice_*`, `extension_visits`, `finance_access`, `hlias`, `land_size`, `education`). **Include Region Selection Logic**: Resolve specific country and generate URL. **Include Caching Logic**: Check local storage, verify checksums against cache manifest, download only if missing/mismatch. Log download errors.
- [X] T016 [US1] Implement `src/data/collectors/remote_sensing_collector.py` to fetch Sentinel-2 L2A (S2MSI2A) imagery from the Copernicus Data Space Ecosystem API. Specifics: Use `requests` with OAuth2, filter by `cloud_cover < 0.8`, download granules covering survey coordinates.
- [ ] T017 [US1] [FR-002] Implement `src/data/processing/spatial_join.py` to link household coordinates to satellite pixels. Specifics: Apply a **spatial buffer** (fuzzing logic) around household coordinates to handle LSMS-ISA privacy fuzzing. Use `geopandas.sjoin` or `rasterio` to extract mean NDVI for the buffer area. **Parameters**: Use a geodesic buffer radius of a moderate spatial scale. **Verification**: Ensure the join logic is deterministic and logs the number of matches.
- [ ] T017a [US1] Implement verification step in `src/data/processing/spatial_join.py` to calculate and log the percentage of households successfully joined. **Logic**: Calculate linkage percentage = (matched households / total valid households). Log the result in `data/logs/ingestion_errors.log` in JSON format with level ERROR if linkage < 95% or N < 300. Log `MISSING_SATELLITE_DATA` for excluded regions.
- [ ] T017c [US1] Implement explicit validation step in `src/data/processing/spatial_join.py` to verify the 95% linkage threshold (SC-001). **Logic**: If linkage < 95% OR N < 300, trigger the aggregation routine defined in T021. If linkage >= 95% and N >= 300, log success and produce `data/logs/linkage_validation.json` with the calculated percentage and total valid households.
- [ ] T017b [US1] Implement documentation generation in `src/data/processing/spatial_join.py` to record the specific geospatial fuzzing radius (1km) and temporal window (growing season months) used for NDVI aggregation. **Output**: Update `data-model.md` or create `data/processed/spatial_alignment_doc.json` with these parameters to satisfy Constitution Principle VII.
- [ ] T018 [US1] [FR-003] Implement `src/data/processing/feature_engineering.py` to construct CSA_Index and Stability_Score. **Logic**: Map `survey_year` + `country` to growing season months (e.g., Malawi: Oct-Mar, Tanzania: Mar-May); calculate NDVI time-series CV; compute Stability_Score (1/CV); sum binary practice indicators for CSA Index. **Ensure** `village_id` is derived or retained in the output dataset for clustering. **Validate** CSA Index construction against the "survey data schema definition" documented in `data-model.md` (not just the derived contract) and `contracts/dataset.schema.yaml`. **Verification**: Run a validation check to ensure all required fields exist and match the schema.
- [ ] T021 [US1] Implement village-level aggregation fallback in `src/data/processing/feature_engineering.py` with explicit conditional logic: If triggered by T017a, aggregate to village level using 'village_id' as key and 'mean' as function for CSA_Index and Stability_Score. **Verification**: Ensure the aggregated dataset retains the `village_id` column and has N >= 300.
- [ ] T021a [US1] Implement verification step in `src/data/processing/feature_engineering.py` to confirm that the aggregated dataset meets statistical power requirements: verify effective sample size >= 300. If N < 300 after aggregation, raise a `FatalError` with a detailed log of the missing sample size.
- [ ] T019 [US1] Implement `src/cli/run_pipeline.py` to orchestrate ingestion, joining, and feature engineering, ensuring it is parameterized for sensitivity analysis sweeps.
- [ ] T020 [US1] Add error handling for missing coordinates and log exclusions to `data/logs/ingestion_errors.log`.
- [ ] T022 [US1] Generate `data/processed/analysis_dataset.csv` and validate against schema.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Statistical Analysis and Diagnostics (Priority: P2)

**Goal**: Run multivariate regression models with robust standard errors and perform collinearity diagnostics.

**Independent Test**: Execution of `src/analysis/run_regression.py` produces a summary file containing regression coefficients, p-values, and VIF scores for both Yield Stability and Food Security models, completing within 60 minutes on CPU.

### Implementation for User Story 2

- [ ] T023 [P] [US2] Write contract test skeleton for regression output in `tests/contract/test_regression_output.py` (TDD).
- [ ] T024 [P] [US2] Write integration test skeleton for model execution in `tests/integration/test_regression.py` (validates T025).
- [ ] T025 [US2] Implement `src/analysis/run_regression.py` to fit Model 1 (Stability_Score) and Model 2 (HFIAS) using statsmodels. **Requirements**: Use Cluster-Robust Standard Errors (clustered by `village_id`) for heteroskedasticity and spatial autocorrelation. Calculate VIF scores for all predictors using `statsmodels.stats.outliers_influence.variance_inflation_factor` on the design matrix. Apply Bonferroni correction (alpha=0.0167). **Output**: Write initial results to `data/processed/regression_results.json` including fields: `adjusted_alpha`, `bonferroni_corrected_p_values`, `coefficients`, `vif_scores`.
- [ ] T026 [US2] Generate regression summary tables including coefficients, p-values, and VIF scores in `data/processed/regression_results.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Sensitivity Analysis and Final Report (Priority: P3)

**Goal**: Perform sensitivity analysis on cloud cover thresholds and generate the final associational report.

**Independent Test**: Execution of `src/analysis/sensitivity_check.py` produces a plot and table showing coefficient stability across threshold sweeps, and the final report includes the observational framing disclaimer.

### Implementation for User Story 3

- [ ] T028 [P] [US3] Write contract test skeleton for sensitivity output in `tests/contract/test_sensitivity.py` (TDD).
- [ ] T029 [P] [US3] Write integration test skeleton for report generation in `tests/integration/test_report.py` (validates T030-T035).
- [ ] T030 [US3] Implement `src/analysis/sensitivity_check.py` to sweep cloud cover thresholds across a representative set of values. **Logic**: Filter the *existing* NDVI time-series aggregation (from T018) based on the new cloud cover threshold; re-calculate Stability_Score and CSA_Index if the filter changes the dataset composition; re-run regression logic on the filtered subset. **Output**: Write variation in `CSA_Index` coefficient magnitude to `data/processed/sensitivity_results.csv` and generate `reports/sensitivity_plot.png`.
- [ ] T032a [US3] Implement sensitivity plot generation in `src/analysis/sensitivity_check.py` showing variation in `CSA_Index` coefficient magnitude across thresholds.
- [ ] T035a [US3] Implement explicit interpretation logic in `src/analysis/sensitivity_check.py` to analyze the `sensitivity_results.csv` and calculate 'max_delta_coefficient' and 'std_coefficient'. Write these metrics to `data/processed/sensitivity_metrics.json` and generate a summary paragraph for the final report. **Verification**: Ensure the JSON file contains the calculated metrics.
- [ ] T032 [US3] Implement `src/services/report_generator.py` to generate `reports/final_report.pdf` using matplotlib/reportlab. **Mandatory**: Programmatically inject the "associational" nature disclaimer, the Bonferroni adjustment method, the specific numerical threshold alpha=0.0167, and the summary paragraph from T035a into the report header/footer. This task replaces the manual check in T033.
- [ ] T034 [US3] Include limitations section (observational design, spatial fuzzing, sample size) in the report generator logic.
- [ ] T035 [US3] Generate final PDF report with all tables, plots, and disclaimers by calling the generator in T032.

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

**Purpose**: Address critical gaps identified in prior research-stage reviews regarding implementation completeness, data artifacts, and reproducibility. Specifically resolves the "Implementation Gap", "No Data Artifacts", "Missing Source Files", "Spec TODOs", and "Filesystem Hygiene" findings.

**Goal**: Ensure actual code, data, and results exist to validate the pipeline, resolving the "Implementation Gap", "No Data Artifacts", and "Spec TODOs" findings.

- [ ] T045 [P] **Create Missing Source Files**: Implement all missing source files listed in `plan.md` structure (e.g., `src/models/`, `src/services/`, `src/cli/run_pipeline.py`) to match the claimed task completion status. **Note**: Ensure file paths align with actual implementations in T025/T030 (e.g., `src/analysis/run_regression.py`).
- [ ] T041a [US1] **Re-run Pipeline for Reproducibility**: Run `src/cli/run_pipeline.py` locally (using the synthetic generator via `--synthetic` flag as configured in T010b, or a specific documented real data file if available) to generate `data/processed/analysis_dataset.csv`.
- [ ] T041b [US1] **Verify Data Artifacts**: Confirm `data/processed/analysis_dataset.csv` exists, has >300 records, and passes `contracts/dataset.schema.yaml` validation.
- [ ] T042a [US2] **Execute Analysis Pipeline**: Run `src/analysis/run_regression.py` locally to generate `data/processed/regression_results.json` with valid coefficients and p-values.
- [ ] T043a [US3] **Execute Reporting Pipeline**: Run `src/analysis/sensitivity_check.py` and `src/services/report_generator.py` locally to generate `reports/sensitivity_results.csv`, `reports/sensitivity_metrics.json`, and `reports/final_report.pdf`.
- [ ] T046 [P] **Create Test Infrastructure**: Generate all test files (`tests/contract/`, `tests/integration/`, `tests/unit/`) referenced in US1-US3 tasks to ensure TDD compliance.
- [ ] T047 [P] **Create Dependency Manifest**: Generate `requirements.txt` with pinned dependency versions (pandas, numpy, statsmodels, geopandas, rasterio, etc.).
- [ ] T048 [P] **Create Reproducibility Artifacts**: Generate `Dockerfile`, `docker-compose.yml`, and `README.md` with installation and reproduction steps.
- [X] T050 [P] **Create and Validate Research Document**: Generate `research.md` (Phase 0 output) with literature review and citations, then immediately run the Reference-Validator Agent on `research.md` to verify all citations; update or remove invalid citations until verification passes. This task unblocks any downstream dependencies on `research.md`.
- [ ] T051 [P] **Filesystem Hygiene Check**: Verify all files are in correct locations per `plan.md` (e.g., `specs/001-climate-smart-eval/` for specs, `src/` for code, `contracts/` for schemas).
- [ ] T052 [P] **Data Provenance Documentation**: Create `data/raw/.provenance.yaml` documenting source URLs, download timestamps, API versions, and license/attribution for all raw data.
- [ ] T053a [P] **Create Data Model Document**: Generate `data-model.md` with variable definitions and schema details.
- [ ] T053b [P] **Sample Size Justification**: Add power analysis or sample-size justification in `data-model.md` for the target N > 1000 (or village aggregation logic). **Logic**: Use a standard power analysis approximation (e.g., G*Power or rule-of-thumb N > 1000 for multivariate regression) to justify the sample size. Document the calculation and assumptions.
- [ ] T054 [P] **Missing Data Strategy**: Document missing value imputation and outlier detection strategies in `data-model.md` and implement in `src/data/processing/`.
- [ ] T055 [P] **Final Verification**: Re-run all integration tests against the newly generated artifacts to confirm the pipeline is reproducible from a clean checkout.

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
Task: "Implement src/data/collectors/survey_collector.py (Region Selection & Caching)"
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
- **Data Integrity**: Never use synthetic data unless real data is unavailable AND the script fails loudly (no silent fallbacks). Manual injection is required for CI.
- **Compute Feasibility**: All tasks must run on CPU-only free tier with limited RAM and disk resources. Use streaming for large datasets.
- **Reproducibility**: All artifacts (data, results, reports) must be generated by the pipeline, not hand-crafted.
- **Research Quality**: Spec must contain a falsifiable hypothesis and specific research gap; no TODOs allowed in final spec.
- **Reviewer Compliance**: Phase N+1 tasks (T041-T055) are mandatory to address the "Full Revision Required" verdicts from prior reviews regarding missing code, data artifacts, and unresolved spec TODOs.