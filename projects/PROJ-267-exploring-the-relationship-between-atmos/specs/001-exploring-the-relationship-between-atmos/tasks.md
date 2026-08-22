# Tasks: Atmospheric River Gravity Correlation

**Input**: Design documents from `/specs/001-atmospheric-river-gravity/`
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

## Phase 0: Setup & Verification (Blocking Prerequisites)

**Purpose**: Project initialization, verification gates, and data hygiene setup. **MUST** complete before Phase 1 (Design).

⚠️ **CRITICAL**: T008 must pass before Phase 1 begins.

- [X] T001 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/` root directory
- [X] T002 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/code/` directory
- [X] T003 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data/raw/` directory
- [X] T004 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/` directory
- [X] T005 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/` directory

- [ ] T008 [P] Create citation verification script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/00_verify_citations.py` that validates both URL reachability AND citation validation (title-token-overlap ≥ 0.7 against primary source) per Constitution Principle II. **Algorithm**: Extract canonical URLs from citation metadata in `spec.md` and `plan.md` (specifically referencing the URLs defined in T015 and T016); perform HTTP HEAD request to verify accessibility; retrieve primary source metadata via that URL; compute title-token-overlap against the primary source's title field. Script must exit with error code if any citation fails. **This script runs immediately in Phase 0** to ensure URLs are reachable before Phase 1 begins. Note: The script extracts URLs directly from the spec/plan files, eliminating circular dependencies. T008 does NOT depend on T037; it verifies the URLs defined in the task descriptions of T015/T016 directly.
- [ ] T012 [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/state/projects/PROJ-267-exploring-the-relationship-between-atmos.yaml` with project metadata and `artifact_hashes` map per Constitution Principle V. **Note: Removed [P] tag to ensure sequential initialization after T001-T005. Depends on T001-T005.**

**Checkpoint**: Verification gates ready - Phase 1 (Design) can now begin.

---

## Phase 1: Foundational (Design & Contracts)

**Purpose**: Core infrastructure, data models, and schema contracts that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. T010 must strictly precede T013/T014. **T008 is a BLOCKING GATE for this phase.**

- [ ] T006 Initialize Python project with dependencies in `projects/PROJ-267-exploring-the-relationship-between-atmos/code/requirements.txt` (pandas, numpy, scipy, statsmodels, requests, matplotlib, seaborn, pyyaml)
- [ ] T007 [P] Configure linting and formatting tools: create `.flake8` and `pyproject.toml` in `projects/PROJ-267-exploring-the-relationship-between-atmos/code/`
- [ ] T009 [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/quickstart.md` covering installation, run commands, data sources, and expected outputs per FR-007 documentation requirements.
- [ ] T010 [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data-model.md` with entity definitions (AR Event, Gravity Anomaly, Correlation Result) per plan.md Phase 1 output. **Must complete before T013/T014.**
- [ ] T013 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/contracts/dataset.schema.yaml` for merged CSV schema validation per US-1. **Depends on T010.**
- [ ] T014 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/contracts/output.schema.yaml` for correlation result schema validation per US-2. **Depends on T010.**

**Checkpoint**: Foundation ready - user story implementation can now begin in priority order

---

## Phase 2: User Story 1 - Data Ingestion & Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve GRACE-FO mascon and NOAA AR catalog data, align to monthly resolution for West Coast NA region (mid-latitude, 35°N-50°N, 120°W-125°W), apply GRACE-FO preprocessing

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying the output contains a merged CSV with ≥ 90% of expected monthly rows and no NaN values in the primary columns

**⚠️ DEPENDENCY**: T015 must complete before T016, T016 must complete before T017. **⚠️ HARD GATE**: Phase 1 (including T013, T014) must complete before T018 can run. **⚠️ DEPENDENCY**: T017 depends on T013 (schema generation).

### Implementation for User Story 1

- [ ] T015 [US1] Create data fetching script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/01_data_ingestion_grace.py` that: (1) fetches GRACE-FO processed mascon solutions from ` (PO.DAAC CMR search API for GRACE-FO L2 Mascon RL06), (2) logs dataset version/release date per Constitution Principle VI, (3) implements region filtering for West Coast NA (35°N-50°N, 120°W-125°W), (4) saves raw downloads to `data/raw/grace-fo/` with checksums per Principle III.
- [ ] T016 [US1] Create data fetching script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/01_data_ingestion_noaa.py` that: (1) fetches NOAA CPC Atmospheric River Catalog data from ` (NOAA ERDDAP endpoint), (2) logs dataset version/release date, (3) implements region filtering for West Coast NA, (4) saves raw downloads to `data/raw/noaa-ar/` with checksums.
- [ ] T017 [US1] Create preprocessing and merge script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/02_preprocessing.py` that: (1) applies GRACE-FO degree-1 coefficient correction, (2) applies GRACE-FO C20 coefficient replacement, (3) applies 300 km Gaussian smoothing at a spatial scale appropriate for the study domain, (4) implements monthly mean aggregation for GRACE-FO mascon values, (5) implements monthly mean aggregation for AR Integrated Water Vapor Transport, (6) handles missing months by logging warnings and skipping per edge cases, (7) excludes months with zero AR events from correlation calculation, (8) validates output against `contracts/dataset.schema.yaml` (generated by T013) and saves merged CSV `projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/merged_monthly.csv`. **Depends on T013.**
- [ ] T018 [US1] Create contract test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_dataset_schema.py` for merged CSV schema validation. **Depends on T013 completion and T017 data generation.**
- [ ] T019 [US1] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_data_pipeline.py` for data ingestion completeness verification.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Statistical Correlation Analysis (Priority: P1)

**Goal**: Compute Pearson correlation between AR intensity and gravity anomalies across lag windows 0-3 months, apply bootstrap resampling (1000 iterations, seed=42), multiple-comparison correction, and control region validation

**Independent Test**: Can be tested by running the analysis module on a mock dataset and verifying the output includes correlation coefficients, p-values, corrected significance flags, bootstrap confidence intervals, and control region comparison results

**⚠️ DEPENDENCY**: T017 must complete before T020 (requires merged_monthly.csv). **⚠️ DEPENDENCY**: T014 must complete before T024.
**⚠️ KNOWN SPEC CONTRADICTION**: Spec contains internal contradiction (SC-002 defines p < 0.05 as success criterion while Constitution Principle VII forbids pre-specified thresholds). Implementation follows power-justified approach (bootstrap CIs, no pre-specified effect size). Flagged for kickback to spec author.

### Implementation for User Story 2

- [ ] T020 [US2] Create correlation computation script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/03_correlation.py` that: (1) computes Pearson correlation between AR intensity and gravity anomalies, (2) implements lag window analysis (lags, 1, 2, 3 months), (3) **Design Choice**: implements autocorrelation correction using AR(1) pre-whitening (statsmodels.tsa.ar_model.AutoReg) and effective sample size calculation to control Type I errors as per plan.md 'Autocorrelation Correction (Methodology Update)' section, (4) does NOT pre-specify effect size threshold as success criteria per Constitution Principle VII; reports bootstrap CIs only. **Note**: p < 0.05 is reported as an informational significance flag per SC-002, not as a pre-specified success criterion.
- [ ] T021 [US2] Create bootstrap correction script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/04_bootstrap_correction.py` that: (1) implements bootstrap resampling (1000 iterations, seed=42) for 95% confidence intervals, (2) applies FDR correction using `statsmodels.stats.multitest.multipletests` for p-values, (3) reports p < 0.05 as a 'significance flag (informational only)' for reporting purposes, NOT as a pre-specified success criteria or effect size threshold, (4) creates Correlation Result output with region_type field (target/control). **Design Choice**: Newey-West standard errors used for robust inference per plan.md 'Autocorrelation Correction (Methodology Update)' section.
- [ ] T022 [US2] Create control validation script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/05_control_validation.py` that: (1) implements control region selection (areas without significant AR activity), (2) implements control vs target region correlation comparison, (3) implements noise-floor calculation from GRACE-FO mascon uncertainty metadata, (4) implements signal magnitude comparison to GRACE-FO measurement noise floor (≥ 3σ threshold) as a MANDATORY verification step per FR-004 (task must assert this condition is met or report failure), (5) handles null results (correlation < 0.1) by reporting with p-value and confidence intervals without forcing positive finding.
- [ ] T023 [US2] Create contract test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_correlation_schema.py` for Correlation Result entity validation. **Depends on T014 completion.**
- [ ] T024 [US2] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_correlation_pipeline.py` for correlation analysis with mock dataset.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Diagnostic Visualization & Sensitivity Reporting (Priority: P2)

**Goal**: Generate time-series overlays, scatter plots with regression lines, spatial anomaly maps, and sensitivity analysis

**Independent Test**: Can be tested by verifying that plot files are generated in the output directory and the sensitivity report contains results for the specified threshold set

**⚠️ DEPENDENCY**: T022 must complete before T025 (requires Correlation Result output)

### Implementation for User Story 3

- [ ] T025 [US3] Create time-series visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/06_visualization_timeseries.py` that generates time-series overlay plot saved as `projects/PROJ-267-exploring-the-relationship-between-atmos/output/timeseries_overlay.png`. **Must include caption: "Note: Gravity anomaly refers to geoid height at satellite altitude (GRACE-FO L2 mascon), not surface gravitational acceleration."**
- [ ] T026 [US3] Create scatter visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/07_visualization_scatter.py` that generates scatter plot with regression line saved as `projects/PROJ-267-exploring-the-relationship-between-atmos/output/scatter_regression.png`. **Must include caption: "Note: Gravity anomaly refers to geoid height at satellite altitude (GRACE-FO L2 mascon), not surface gravitational acceleration."**
- [ ] T027 [US3] Create spatial visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/08_visualization_spatial.py` that generates spatial anomaly map saved as `projects/PROJ-267-exploring-the-relationship-between-atmos/output/spatial_anomaly_map.png`. **Must include caption: "Note: Gravity anomaly refers to geoid height at satellite altitude (GRACE-FO L2 mascon), not surface gravitational acceleration."**
- [ ] T028 [US3] Create sensitivity analysis script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/09_sensitivity_report.py` that: (1) implements threshold sweep across a range of representative values as required by SC-003, (2) implements correlation coefficient stability reporting, (3) implements confidence interval overlap variation reporting, (4) **CRITICAL**: The content generation logic must explicitly frame all statistical findings as associational, avoiding causal language (causes, effect, impact, driven by, leads to, triggers) during the report construction process. (5) validates absence of causal keywords (causes, effect, impact, driven by, leads to, triggers) in all output reports per FR-007 using regex pattern matching as **secondary validation only**, ensuring the primary requirement is met by the generation logic itself. **Note**: The generation logic must avoid causal framing; regex is a secondary check.
- [ ] T029 [US3] Create temporal bias documentation script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/10_temporal_bias_analysis.py` that: (1) implements temporal aggregation bias documentation per FR-009, (2) provides justification for monthly resolution choice versus sub-monthly alternatives, (3) outputs `docs/temporal_bias_analysis.md`.
- [ ] T030 [US3] Create output validation test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_output_schema.py` for report language compliance (causal keyword absence using regex pattern matching). **Depends on T028.**
- [ ] T031 [US3] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_visualization_pipeline.py` for visualization and sensitivity report generation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

**⚠️ DEPENDENCY**: All Phase 2-4 tasks must complete before Phase 5

- [ ] T032 [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/README.md` with required sections: installation, data sources, run commands, expected outputs.
- [ ] T033 Run all contract tests to verify schema compliance.
- [ ] T034 Run all integration tests to verify pipeline end-to-end.
- [ ] T035 Measure aggregate pipeline runtime (full historical dataset from data/processed/merged_monthly.csv) to verify ≤ 6 hours on 2 CPU cores and 7 GB RAM (SC-004) using Python time module with assertion that fails if exceeded.
- [ ] T036 [P] Document checksums for all data files in `projects/PROJ-267-exploring-the-relationship-between-atmos/state/` per Principle III.
- [ ] T037 [P] Verify all dataset URLs are reachable and documented in `projects/PROJ-267-exploring-the-relationship-between-atmos/docs/methodology.md`. **Note: This is a final validation step, not a prerequisite for T008.**
- [ ] T038 [P] Update `projects/PROJ-267-exploring-the-relationship-between-atmos/state/projects/PROJ-267-exploring-the-relationship-between-atmos.yaml` with `updated_at` timestamp and content hashes per Principle V.
- [ ] T039 Run quickstart.md validation to confirm reproducibility: `python code/09_sensitivity_report.py --validate && pytest tests/contract/test_output_schema.py`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 0)**: No dependencies - can start immediately
- **Foundational (Phase 1)**: Depends on Setup completion - BLOCKS all user stories. **T008 is a blocking prerequisite.**
- **User Stories (Phase 2-4)**: Sequential dependencies - MUST complete in order
 - **Phase 2 (US1)**: Must complete before Phase 3
 - **Phase 3 (US2)**: Must complete before Phase 4 (requires merged_monthly.csv from Phase 2)
 - **Phase 4 (US3)**: Must complete after Phase 3 (requires Correlation Result from Phase 3)
- **Polish (Phase 5)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories
- **User Story 2 (P1)**: Requires US1 data output (merged_monthly.csv) - CANNOT start until US1 completes
- **User Story 3 (P2)**: Requires US2 analysis output (Correlation Result) - CANNOT start until US2 completes

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion before preprocessing
- Preprocessing before analysis
- Analysis before visualization
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (except T008 which is sequential)
- All Foundational tasks marked [P] can run in parallel (within Phase 1, respecting T010 -> T013/T014 order)
- Contract tests for different schemas (T018, T023, T030) can run in parallel
- Integration tests for different pipelines (T019, T024, T031) can run in parallel
- Visualization tasks (T025, T026, T027) can run in parallel after T022 completes

---

## Notes

- [P] tasks = different files, no dependencies (within their phase)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: All tasks must be CPU-tractable (no GPU/CUDA, no 8-bit/4-bit quantization, no large LLMs)
- **CRITICAL**: Dataset URLs must be specific and reachable (NO "download from UCI" without HOW)
- **CRITICAL**: Task ordering MUST respect data flow (ingestion → preprocessing → analysis → visualization)
- **SPEC CONTRADICTION FLAG**: Spec.md contains internal contradiction (Principle VII states thresholds MUST NOT be pre-specified, but SC-002 pre-specifies p < 0.05 and Constitution Principle VII mentions Pearson > 0.5 as example). Tasks implement power-justified approach per plan. **Spec requires kickback for resolution.**
- **PLAN ROOT CAUSE**: Constitution Check shows PENDING VERIFICATION for dataset URLs. T008 added for explicit citation verification. **Plan requires update.**
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence