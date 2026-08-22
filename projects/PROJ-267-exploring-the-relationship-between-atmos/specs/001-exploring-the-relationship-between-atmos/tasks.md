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

⚠️ **CRITICAL**: T012 must pass before Phase 1 begins.

- [X] T001 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/` root directory
- [X] T002 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/code/` directory
- [X] T003 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data/raw/` directory
- [X] T004 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/` directory
- [X] T005 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/` directory

- [X] T012 [Sequential] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/state/projects/PROJ-267-exploring-the-relationship-between-atmos.yaml` with project metadata and an **empty** `artifact_hashes` map `{}` per Constitution Principle V. **Note: This task initializes the state file. It MUST be marked complete [X] before Phase 1 begins. The `artifact_hashes` map starts empty to allow subsequent tasks to populate it.**

**Checkpoint**: Foundational artifacts initialized - Phase 1 (Design) can now begin.

---

## Phase 1: Foundational (Design & Contracts)

**Purpose**: Core infrastructure, data models, and schema contracts that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. T010 must strictly precede T013/T014.

**Phase Mapping to FR/SC Coverage (Updated)**:
| Phase | FR Coverage | SC Coverage | Description |
|-------|-------------|-------------|-------------|
| Phase 0: Setup | FR-001, FR-002 (Prep) | SC-001 (Prep) | Directory setup, state init |
| Phase 1: Foundational | FR-003 (Design) | SC-001 (Design) | Data model, schemas, methodology |
| Phase 1.5: Theoretical Frame | FR-003 (Clarification) | SC-001 (Clarification) | Frame of reference definition |
| Phase 2: Data Ingestion | FR-001, FR-002 | SC-001 | Download and merge data |
| Phase 3: Analysis | FR-004, FR-005, FR-008 | SC-002 | Correlation and bootstrap |
| Phase 4: Visualization | FR-006, FR-009, FR-007 | SC-003, SC-004 | Plots and reports |
| Phase 5: Polish | All | All | Final validation |

- [X] T006 Initialize Python project with dependencies in `projects/PROJ-267-exploring-the-relationship-between-atmos/code/requirements.txt` (pandas, numpy, scipy, statsmodels, requests, matplotlib, seaborn, pyyaml)
- [X] T007 [P] Configure linting and formatting tools: create `.flake8` and `pyproject.toml` in `projects/PROJ-267-exploring-the-relationship-between-atmos/code/`
- [X] T009 [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/quickstart.md` covering installation, run commands, data sources, and expected outputs per FR-007 documentation requirements.
- [X] T009b [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/docs/methodology.md` with the initial methodology draft, including the 'Frame of Reference and Coordinate System' section placeholder. **Depends on T001-T005.**
- [X] T010 [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data-model.md` with entity definitions (AR Event, Gravity Anomaly, Correlation Result) per plan.md Phase 1 output. **Must complete before T013/T014.**
 **Content to be written:**
 ```markdown
 # Data Model

 ## AR Event
 - **date**: ISO 8601 date string
 - **peak_intensity**: Float (Integrated Water Vapor Transport in kg/m/s)
 - **footprint**: List of [lat, lon] coordinates (bounding box)

 ## Gravity Anomaly
 - **date**: ISO 8601 date string (monthly)
 - **anomaly_value**: Float (Geoid height anomaly at satellite altitude in meters)
 - **uncertainty**: Float (Standard deviation of the anomaly in meters)
 - **region**: String (Study region identifier)

 ## Correlation Result
 - **lag**: Integer (Months)
 - **correlation_coefficient**: Float (Pearson r)
 - **raw_p_value**: Float
 - **corrected_p_value**: Float
 - **confidence_interval_lower**: Float
 - **confidence_interval_upper**: Float
 - **significance_flag**: Boolean (Informational only, p < 0.05 corrected)
 - **region_type**: String ('target' or 'control')
 - **signal_to_noise_ratio**: Float (Correlation coefficient / uncertainty)
 ```
- [X] T013 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/contracts/dataset.schema.yaml` for merged CSV schema validation per US-1. **Depends on T010.**
 **Content to be written:**
 ```yaml
 type: object
 properties:
 date:
 type: string
 format: date
 ar_intensity:
 type: number
 gravity_anomaly:
 type: number
 uncertainty:
 type: number
 required:
 - date
 - ar_intensity
 - gravity_anomaly
 - uncertainty
 ```
- [X] T014 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/contracts/output.schema.yaml` for correlation result schema validation per US-2. **Depends on T010.**
 **Content to be written:**
 ```yaml
 type: object
 properties:
 lag:
 type: integer
 correlation_coefficient:
 type: number
 raw_p_value:
 type: number
 corrected_p_value:
 type: number
 confidence_interval_lower:
 type: number
 confidence_interval_upper:
 type: number
 significance_flag:
 type: boolean
 region_type:
 type: string
 signal_to_noise_ratio:
 type: number
 required:
 - lag
 - correlation_coefficient
 - corrected_p_value
 - region_type
 ```

**Checkpoint**: Foundation ready - user story implementation can now begin in priority order

---

## Phase 1.5: Theoretical Frame & Coordinate Reference Clarification (Priority: P1 - Revision)

**Purpose**: Address the "albert-einstein-simulated" review regarding the definition of the gravitational anomaly frame of reference and the distinction between physical curvature and coordinate artifacts. This phase MUST precede Phase 2 to ensure the data model is correct before preprocessing.

**Independent Test**: Verification that `data-model.md` and `docs/methodology.md` explicitly define the reference frame (satellite altitude potential vs. geoid) and document the covariant nature of the measurement.

- [ ] T032 [US1/US2] Update `projects/PROJ-267-exploring-the-relationship-between-atmos/data-model.md` to explicitly define the "Gravity Anomaly" entity's frame of reference. **Requirement**: Must state that the anomaly represents the perturbation in the gravitational potential at the GRACE-FO satellite altitude (approx. low Earth orbit), not the geoid height at the Earth's surface. Must explicitly note that this is a coordinate-dependent quantity derived from spherical harmonic coefficients and that the analysis assumes a static, non-rotating frame for the duration of the monthly aggregation, acknowledging the coordinate artifact nature of "static" anomalies in a dynamic field. **Depends on T010 (Complete).**
- [ ] T033 [US1/US2] Update `projects/PROJ-267-exploring-the-relationship-between-atmos/docs/methodology.md` to include a "Frame of Reference and Coordinate System" section. **Requirement**: Must explain that GRACE-FO measures changes in the Earth's gravity field by tracking inter-satellite distance variations, which are then converted to spherical harmonic coefficients. The analysis uses the "geoid height at satellite altitude" as the proxy for mass redistribution, explicitly distinguishing this from the "geoid" (equipotential surface at mean sea level). Must reference the 1915 field equations context as a conceptual reminder that gravitational potential is covariant, but the monthly averaging effectively integrates over the orbital perturbations to yield a scalar potential anomaly in the satellite's reference frame. **Depends on T009b.**

**Checkpoint**: Theoretical ambiguity resolved; data model updated before any data processing.

---

## Phase 2: User Story 1 - Data Ingestion & Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve GRACE-FO mascon and NOAA AR catalog data, align to monthly resolution for West Coast NA region (mid-latitude, 35°N-50°N, 120°W-125°W), apply GRACE-FO preprocessing

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying the output contains a merged CSV with ≥ 90% of expected monthly rows and no NaN values in the primary columns

**⚠️ DEPENDENCY**: T015 must complete before T016, T016 must complete before T017. **⚠️ HARD GATE**: Phase 1 (including T013, T014) and Phase 1.5 (T032) must complete before T017a/T017b can run. **⚠️ DEPENDENCY**: T017a/T017b depend on T013 (schema generation) and T032 (data model definition).

### Implementation for User Story 1

- [ ] T015 [US1] Create data fetching script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/01_data_ingestion_grace.py` that: (1) fetches GRACE-FO processed mascon solutions from ` (PO.DAAC CMR search API for GRACE-FO L2 Mascon RL06), (2) logs dataset version/release date per Constitution Principle VI, (3) implements region filtering for West Coast NA (35°N-50°N, 120°W-125°W), (4) saves raw downloads to `data/raw/grace-fo/` with checksums per Principle III.
- [ ] T016 [US1] Create data fetching script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/01_data_ingestion_noaa.py` that: (1) fetches NOAA CPC Atmospheric River Catalog data from `https://coastwatch.pfeg.noaa.gov/erddap/tabledap/ar_catalog.html` (NOAA ERDDAP endpoint), (2) logs dataset version/release date, (3) implements region filtering for West Coast NA, (4) saves raw downloads to `data/raw/noaa-ar/` with checksums.
- [ ] T008 [US1] Create citation verification script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/00_verify_citations.py` that validates both URL reachability AND citation validation (title-token-overlap ≥ 0.7 against primary source) per Constitution Principle II. **Algorithm**: Reads the URLs defined in the task descriptions of T015 and T016 (CMR and ERDDAP endpoints); perform HTTP HEAD request to verify accessibility; retrieve primary source metadata via that URL; compute title-token-overlap against the primary source's title field. Script must exit with error code if any citation fails. **This script runs in Phase 2** to ensure URLs are reachable and verified after they are defined. Note: Internal functions should be modularized (URL extraction from task text, HTTP requests, metadata retrieval, overlap calculation) to manage granularity. **Depends on T015 and T016 completion.**
- [ ] T017a [US1] Create GRACE-FO preprocessing script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/02_preprocessing_grace.py` that: (1) applies GRACE-FO degree-1 coefficient correction, (2) applies GRACE-FO C20 coefficient replacement, (3) applies **Gaussian smoothing** at a spatial scale appropriate for the study domain, (4) implements monthly mean aggregation for GRACE-FO mascon values. **Depends on T015 and T013.** **ATOMIZER FLAG: This task is too coarse for a single LLM pass; atomizer will split if needed.**
- [ ] T017b [US1] Create NOAA aggregation script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/02_preprocessing_noaa.py` that: (1) implements monthly mean aggregation for AR Integrated Water Vapor Transport, (2) handles missing months by logging warnings and skipping per edge cases, (3) excludes months with zero AR events from correlation calculation. **Depends on T016.** **ATOMIZER FLAG: This task is too coarse for a single LLM pass; atomizer will split if needed.**
- [ ] T017c [US1] Create merge and validation script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/02_preprocessing_merge.py` that: (1) merges processed GRACE-FO and NOAA data, (2) validates output against `contracts/dataset.schema.yaml` (generated by T013) and saves merged CSV `projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/merged_monthly.csv`. **Depends on T017a, T017b, and T013.** **ATOMIZER FLAG: This task is too coarse for a single LLM pass; atomizer will split if needed.**
- [ ] T018 [US1] Create contract test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_dataset_schema.py` for merged CSV schema validation. **Depends on T013 completion and T017c data generation.**
- [ ] T019 [US1] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_data_pipeline.py` for data ingestion completeness verification.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Statistical Correlation Analysis (Priority: P1)

**Goal**: Compute Pearson correlation between AR intensity and gravity anomalies across lag windows 0-3 months, apply bootstrap resampling (1000 iterations, seed=42), multiple-comparison correction, and control region validation

**Independent Test**: Can be tested by running the analysis module on a mock dataset and verifying the output includes correlation coefficients, p-values, corrected significance flags, bootstrap confidence intervals, and control region comparison results

**⚠️ DEPENDENCY**: T017c must complete before T020 (requires merged_monthly.csv). **⚠️ DEPENDENCY**: T014 must complete before T023.
**⚠️ KNOWN SPEC CONTRADICTION**: Spec contains internal contradiction (SC-002 defines p < 0.05 as success criterion while Constitution Principle VII forbids pre-specified thresholds). Implementation follows power-justified approach (bootstrap CIs, no pre-specified effect size). Flagged for kickback to spec author.

### Implementation for User Story 2

- [ ] T020 [US2] Create correlation and bootstrap analysis script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/03_correlation_analysis.py` that: (1) computes Pearson correlation between AR intensity and gravity anomalies, () implements lag window analysis (lags, short-term intervals, 2, 3 months), (3) **Design Choice**: implements autocorrelation correction using AR(1) pre-whitening (statsmodels.tsa.ar_model.AutoReg) and effective sample size calculation to control Type I errors as per plan.md 'Autocorrelation Correction (Methodology Update)' section, (4) implements bootstrap resampling (1000 iterations, seed=42) for 95% confidence intervals, (5) applies FDR correction using `statsmodels.stats.multitest.multipletests` for p-values, (6) **CRITICAL**: reports p < 0.05 as a 'significance flag (informational only)' for reporting purposes, NOT as a pre-specified success criteria or effect size threshold. NO branching logic based on p-value thresholds will be implemented. (7) creates Correlation Result output with region_type field (target/control). (8) calculates the signal-to-noise ratio by dividing the correlation coefficient by the 'uncertainty' field from `merged_monthly.csv` and reports this ratio as a continuous metric, explicitly NOT asserting a binary pass/fail or referencing a specific threshold (e.g., 3σ) as a success criterion. **Design Choice**: Newey-West standard errors used for robust inference per plan.md 'Autocorrelation Correction (Methodology Update)' section. **Depends on T017c and T014.**
- [ ] T023 [US2] Create contract test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_correlation_schema.py` for Correlation Result entity validation. **Depends on T014 completion.**
- [ ] T024 [US2] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_correlation_pipeline.py` for correlation analysis with mock dataset.
- [ ] T020b [P] Create performance profiling script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/03_profile_runtime.py` that: (1) profiles the runtime of T020 on a representative sample of the data, (2) outputs `docs/runtime_profile.md` with estimated runtime for the full dataset. **Depends on T020 completion. Output is required input for T040.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Diagnostic Visualization & Sensitivity Reporting (Priority: P2)

**Goal**: Generate time-series overlays, scatter plots with regression lines, spatial anomaly maps, and sensitivity analysis

**Independent Test**: Can be tested by verifying that plot files are generated in the output directory and the sensitivity report contains results for the specified threshold set

**⚠️ DEPENDENCY**: T020 must complete before T025 (requires Correlation Result output)

### Implementation for User Story 3

- [ ] T025 [US3] Create time-series visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/06_visualization_timeseries.py` that generates time-series overlay plot saved as `projects/PROJ-267-exploring-the-relationship-between-atmos/output/timeseries_overlay.png`. **Must include caption: "Note: Gravity anomaly refers to geoid height at satellite altitude (GRACE-FO L2 mascon), not surface gravitational acceleration."**
- [ ] T026 [US3] Create scatter visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/07_visualization_scatter.py` that generates scatter plot with regression line saved as `projects/PROJ-267-exploring-the-relationship-between-atmos/output/scatter_regression.png`. **Must include caption: "Note: Gravity anomaly refers to geoid height at satellite altitude (GRACE-FO L2 mascon), not surface gravitational acceleration."**
- [ ] T027 [US3] Create spatial visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/08_visualization_spatial.py` that generates spatial anomaly map saved as `projects/PROJ-267-exploring-the-relationship-between-atmos/output/spatial_anomaly_map.png`. **Must include caption: "Note: Gravity anomaly refers to geoid height at satellite altitude (GRACE-FO L2 mascon), not surface gravitational acceleration."**
- [ ] T028 [US3] Create sensitivity analysis script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/09_sensitivity_report.py` that: (1) implements threshold sweep across the set {0.4, 0.5, 0.6} as required by SC-003 (correcting the spec's malformed set), explicitly defining the set as a range of moderate values, (2) implements correlation coefficient stability reporting, (3) implements confidence interval overlap variation reporting, (4) **CRITICAL**: The content generation logic must explicitly frame all statistical findings as associational, avoiding causal language (causes, effect, impact, driven by, leads to, triggers) during the report construction process. (5) validates absence of causal keywords (causes, effect, impact, driven by, leads to, triggers) in all output reports per FR-007 using regex pattern matching as a **final safety check only**, ensuring the primary requirement is met by the generation logic itself. **Note**: The generation logic must avoid causal framing; regex is a secondary check. **Depends on T020.**
- [ ] T029 [US3] Create temporal bias documentation script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/10_temporal_bias_analysis.py` that: (1) implements temporal aggregation bias documentation per FR-009, (2) provides justification for monthly resolution choice versus sub-monthly alternatives, (3) outputs `docs/temporal_bias_analysis.md`. **Depends on T028.**
- [ ] T030 [US3] Create output validation test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_output_schema.py` for report language compliance (causal keyword absence using regex pattern matching). **Depends on T028.**
- [ ] T031 [US3] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_visualization_pipeline.py` for visualization and sensitivity report generation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

**⚠️ DEPENDENCY**: All Phase 2-4 tasks must complete before Phase 5

- [ ] T037 [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/README.md` with required sections: installation, data sources, run commands, expected outputs.
- [ ] T038 Run all contract tests to verify schema compliance.
- [ ] T039 Run all integration tests to verify pipeline end-to-end.
- [ ] T040 Measure aggregate pipeline runtime (full historical dataset from data/processed/merged_monthly.csv, GRACE-FO mission launch 2018-03-01 to latest available data point as of 2024-12-31) to verify ≤ 6 hours on 2 CPU cores and 7 GB RAM (SC-004) using Python time module with assertion that fails if exceeded. **Input: `docs/runtime_profile.md` from T020b.**
- [ ] T041 [P] Document checksums for all data files in `projects/PROJ-267-exploring-the-relationship-between-atmos/state/` per Principle III.
- [ ] T042 [P] Verify all dataset URLs are reachable and documented in `projects/PROJ-267-exploring-the-relationship-between-atmos/docs/methodology.md`. **Note: This is a final validation step, not a prerequisite for T008.**
- [ ] T043 [P] Update `projects/PROJ-267-exploring-the-relationship-between-atmos/state/projects/PROJ-267-exploring-the-relationship-between-atmos.yaml` with `updated_at` timestamp and content hashes per Principle V.
- [ ] T044 Run quickstart.md validation to confirm reproducibility: `python code/09_sensitivity_report.py --validate && pytest tests/contract/test_output_schema.py`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 0)**: No dependencies - can start immediately
- **Foundational (Phase 1)**: Depends on Setup completion - BLOCKS all user stories.
- **Theoretical Frame (Phase 1.5)**: Depends on Phase 1 (T010, T009b) - BLOCKS Phase 2.
- **User Stories (Phase 2-4)**: Sequential dependencies - MUST complete in order
 - **Phase 2 (US1)**: Must complete before Phase 3
 - **Phase 3 (US2)**: Must complete before Phase 4 (requires merged_monthly.csv from Phase 2)
 - **Phase 4 (US3)**: Must complete after Phase 3 (requires Correlation Result from Phase 3)
- **Polish (Phase 5)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) and Theoretical Frame (Phase 1.5) - No dependencies on other stories
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

- All Setup tasks marked [P] can run in parallel (except T012 which is sequential)
- All Foundational tasks marked [P] can run in parallel (within Phase 1, respecting T010 -> T013/T014 order)
- Contract tests for different schemas (T018, T023, T030) can run in parallel
- Integration tests for different pipelines (T019, T024, T031) can run in parallel
- Visualization tasks (T025, T026, T027) can run in parallel after T020 completes
- Revision tasks (T032, T033) can run in parallel after T010/T009b completes

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
- **PLAN ROOT CAUSE**: Constitution Check shows PENDING VERIFICATION for dataset URLs. T008 added for explicit citation verification (moved to Phase 2). **Plan requires update.**
- **REVISION NOTE**: Phase 1.5 added to address "albert-einstein-simulated" review regarding the definition of the gravitational anomaly frame of reference and the distinction between physical curvature and coordinate artifacts. Phase 1.5 now precedes Phase 2 to ensure data model correctness.
- **REVISION NOTE**: T008 moved to Phase 2 to resolve circular dependency with URL definitions in T015/T016.
- **REVISION NOTE**: T017 split into T017a, T017b, T017c to reduce granularity.
- **REVISION NOTE**: T020 and T021 merged into T020 to reduce context switching.
- **REVISION NOTE**: T020b added for intermediate performance profiling.
- **REVISION NOTE**: T009b added to create docs/methodology.md.
- **REVISION NOTE**: T012, T010, T013, T014 marked as complete to unblock downstream tasks.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence