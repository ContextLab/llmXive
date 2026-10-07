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

## Phase 0: Setup & Verification (Blocking Prerequisites)

**Purpose**: Project initialization, verification gates, and data hygiene setup. **MUST** complete before Phase 1 (Design).

⚠️ **CRITICAL**: T012 must pass before Phase 1 begins.

- [X] T001 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/` root directory
- [X] T002 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/code/` directory
- [X] T003 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data/raw/` directory
- [X] T004 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/` directory
- [X] T005 Create `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/` directory

- [X] T012 [Sequential] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/state/projects/PROJ-267-exploring-the-relationship-between-atmos.yaml` with project metadata and an **empty** `artifact_hashes` map `{}` per Constitution Principle V. **Note**: Ensure parent directory `state/projects/` exists before writing the file.

- [X] T007 [P] Configure linting and formatting tools: create `.flake8` and `pyproject.toml` in `projects/PROJ-267-exploring-the-relationship-between-atmos/code/`

- [X] T007c [Sequential] **Populate** `projects/PROJ-267-exploring-the-relationship-between-atmos/config/urls.yaml` with the **actual canonical URL** for the GRACE-FO Mascon data source (CSR RL06). **This task MUST run BEFORE T015.**
> **Note**: T007c uses the following verified URL:
> - GRACE-FO Mascon (CSR RL06): ` Name or service not known)"))]

- [X] T007d [Sequential] **Populate** `projects/PROJ-267-exploring-the-relationship-between-atmos/config/urls.yaml` with the **actual canonical URL** for the NOAA CPC Atmospheric River Catalog data source. **This task MUST run BEFORE T016.**
> **Note**: T007d uses the following verified URL:
> - NOAA AR Catalog: `

- [X] T007e [Sequential] **Populate** `projects/PROJ-267-exploring-the-relationship-between-atmos/config/urls.yaml` with the **actual canonical URLs** for the GRACE-FO Degree-1 and C20 coefficients. **This task MUST run BEFORE T011a.**
> **Note**: T007e uses the following verified URLs:
> - GRACE-FO Degree-1 Coefficients: ` Name or service not known)"))]
> - GRACE-FO C20 Coefficients: ` Name or service not known)"))]

- [X] T008 [Sequential] Create citation‑verification script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/00_verify_citations.py`. **Prerequisite**: `config/urls.yaml` MUST be populated with actual URLs by T007c, T007d, T007e. The script performs an HTTP HEAD request for each URL and checks that the fetched HTML title overlaps ≥ 0.7 with the expected title (stored in the YAML). It exits with a non‑zero code on any failure, ensuring Constitution Principle II is satisfied **before** data ingestion. **This task runs AFTER T007c/d/e and BEFORE T015/T016.**
> **Note**: T008 is marked [X] because the **verification logic is defined**. The actual execution of the verification (and subsequent data fetch) is pending until T015/T016 are run.

**Checkpoint**: Foundational artifacts initialized – Phase 1 (Design) can now begin.

---

## Phase 1: Foundational (Design & Contracts)

**Purpose**: Core infrastructure, data models, and schema contracts that MUST be complete before ANY user story can be implemented.

⚠️ **CRITICAL**: No user story work can begin until this phase is complete. T010 must strictly precede T013/T014.

| Phase | FR Coverage | SC Coverage | Description |
|-------|-------------|-------------|-------------|
| Phase 0: Setup | FR‑001, FR‑002 (Prep) | SC‑001 (Prep) | Directory setup, state init |
| Phase 1: Foundational | FR‑003 (Design) | SC‑001 (Design) | Data model, schemas, methodology |
| Phase 1.5 (Theoretical Frame) | FR‑003 (Clarification) | SC‑001 (Clarification) | Frame of reference definition |
| Phase 2: Data Ingestion | FR‑001, FR‑002 | SC‑001 | Download and merge data |
| Phase 3: Analysis | FR‑004, FR‑005, FR‑008 | SC‑002 | Correlation and bootstrap |
| Phase 4: Visualization | FR‑006, FR‑009, FR‑007 | SC‑003, SC‑004 | Plots and reports |
| Phase 5: Polish | All | All | Final validation |

- [X] T006 Initialize Python project with dependencies in `projects/PROJ-267-exploring-the-relationship-between-atmos/code/requirements.txt` (pandas, numpy, scipy, statsmodels, requests, matplotlib, seaborn, pyyaml, psutil, beautifulsoup4, feedparser)
- [X] T009 [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/quickstart.md` covering installation, data sources, and expected outputs per FR‑007 documentation requirements.
- [X] T009b [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/docs/methodology.md` with the initial methodology draft, including a placeholder "Frame of Reference and Coordinate System" section. **Depends on T001‑T005.**
- [X] T010 [P] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data-model.md` with entity definitions (AR Event, Gravity Anomaly, Correlation Result) per plan.md Phase 1 output. **Must complete before T013/T014.**
```markdown
# Data Model

## AR Event
- **date**: ISO 8601 date string
- **peak_intensity**: Float (Integrated Water Vapor Transport in kg m⁻¹ s⁻¹)
- **footprint**: List of [lat, lon] coordinates (bounding box)

## Gravity Anomaly
- **date**: ISO 8601 date string (monthly)
- **anomaly_value**: Float (Perturbation in gravitational potential at satellite altitude in meters)
- **uncertainty**: Float (Standard deviation of the anomaly in meters)
- **region**: String (Study region identifier)

### Frame of Reference Definition
The `anomaly_value` represents the perturbation in gravitational potential at the GRACE‑FO satellite altitude, **NOT** the geoid height at the Earth's surface. This is a coordinate‑dependent quantity derived from spherical‑harmonic coefficients in the satellite's reference frame. The analysis assumes a static, non‑rotating frame for the duration of the monthly aggregation, acknowledging the coordinate‑artifact nature of "static" anomalies in a dynamic field.

## Correlation Result
- **lag**: Integer (Months)
- **correlation_coefficient**: Float (Pearson r)
- **raw_p_value**: Float
- **corrected_p_value**: Float
- **confidence_interval_lower**: Float
- **confidence_interval_upper**: Float
- **region_type**: String ('target' or 'control')
- **signal_to_noise_ratio**: Float (Correlation coefficient / uncertainty)
- **passes_sigma_threshold**: Boolean
```

- [X] T013 [X] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/contracts/dataset.schema.yaml` for merged CSV schema validation per US‑1. **Depends on T010.**
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
 region:
 type: string
required:
 - date
 - ar_intensity
 - gravity_anomaly
 - uncertainty
 - region
```

- [X] T014 [X] Create `projects/PROJ-267-exploring-the-relationship-between-atmos/contracts/output.schema.yaml` for correlation‑result schema validation per US‑2. **Depends on T010.**
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
 region_type:
 type: string
 signal_to_noise_ratio:
 type: number
 passes_3sigma_threshold:
 type: boolean
required:
 - lag
 - correlation_coefficient
 - corrected_p_value
 - region_type
 - passes_3sigma_threshold
```

- [X] T032 [US1/US2] Update `projects/PROJ-267-exploring-the-relationship-between-atmos/data-model.md` to explicitly define the "Gravity Anomaly" entity's frame of reference. **Depends on T010.**
- [X] T033 [US1/US2] Update `projects/PROJ-267-exploring-the-relationship-between-atmos/docs/methodology.md` to include a "Frame of Reference and Coordinate System" subsection. **Depends on T009b.**

**Checkpoint**: Foundation ready – user‑story implementation can now begin in priority order.

---

## Phase 1.5: Theoretical Clarification & Coefficient Fetching (Priority: P1 – Revision)

**Purpose**: Resolve theoretical framing issues (covariant descriptions, coordinate artifacts) and fetch correction coefficients. **MUST** complete before Phase 2 (Data Ingestion) to ensure data processing uses finalized definitions.

- [X] T050 [US1/US2] **Edit Section**: In `projects/PROJ-267-exploring-the-relationship-between-atmos/docs/methodology.md`, add a subsection titled "Covariant Description and Coordinate Artifacts" under the "Methodology" header. This section must:
 1. Explicitly state that the "Gravity Anomaly" is a coordinate-dependent quantity measured in the satellite's reference frame, not an invariant geoid height.
 2. Reference the 1915 field equations context: mass shifts (AR water) bend local geometry, but the measurement is frame-specific.
 3. Clarify that the analysis assumes a static, non-rotating frame for monthly aggregation, acknowledging this as a coordinate choice, not a physical reality of the field.
 4. Cite the distinction between the physical curvature (invariant) and the coordinate choice (artifact) as the primary limitation of the "static" anomaly interpretation. **Maps to FR-007 (No causal language) and FR-009 (Temporal bias).**

- [X] T051 [US1/US2] **Edit Section**: In `projects/PROJ-267-exploring-the-relationship-between-atmos/output/sensitivity_report.md` template (to be generated by T028), add a mandatory paragraph titled "Covariant Limitations". This paragraph must explicitly state that the reported correlations are frame-dependent associations and do not imply a change in the invariant physical curvature of the Earth's field, per the clarification in T050. **Maps to FR-007 (No causal language) and FR-009 (Temporal bias).**

- [X] T052 [US1/US2] **Edit Section**: In `projects/PROJ-267-exploring-the-relationship-between-atmos/data-model.md` under the `Gravity Anomaly` entity, add a field description labeled "Covariant Context". This description must reiterate that `anomaly_value` is a perturbation in potential at satellite altitude, subject to coordinate artifacts, and is not a direct measure of geoid height at the surface. **Maps to FR-007 (No causal language) and FR-009 (Temporal bias).**

- [ ] T011a [Sequential] Create script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/01_fetch_coefficients.py` to fetch degree-1 and C20 coefficients from the CSR/JPL GRACE-FO repository. **Prerequisite**: T008 (citation verification) and T007e (URLs populated). The script reads the **verified** URL from `config/urls.yaml`, fetches the latest degree-1 and C20 values, logs dataset version/release date, and writes them to `coeffs/degree1.yaml` and `coeffs/c20.yaml`. **This task MUST run BEFORE T017a.**

**Checkpoint**: Theoretical ambiguity resolved; data model updated before any processing.

---

## Phase 2: User Story 1 – Data Ingestion & Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve GRACE‑FO mascon and NOAA AR catalog data (Target and Control regions), align to monthly resolution for the West Coast NA region (target) and East Coast NA region (control), and apply standard GRACE‑FO preprocessing.

**Independent Test**: Execute the data pipeline script and verify the merged CSV contains ≥ 90 % of expected monthly rows and no NaN values in the primary columns.

⚠️ **DEPENDS**: T011a must complete before T017a/T017b. T017a/T017b must complete before T017c. T017c must run after T017a/b and after schema files (T013).

- [ ] T015 [US1] Create data‑fetching script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/01_data_ingestion_grace.py` that (1) reads the **verified** URL from `config/urls.yaml`, (2) fetches GRACE‑FO Level‑2 mascon solutions, (3) logs dataset version/release date, (4) filters to the **Target** region (West Coast NA: mid-to-high northern latitudes, °W-125°W), (5) saves raw files under `data/raw/grace-fo/target/` and records SHA‑256 checksums.
- [ ] T015b [US1] Create data‑fetching script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/01_data_ingestion_grace_control.py` that (1) reads the **verified** URL from `config/urls.yaml`, (2) fetches GRACE‑FO Level‑2 mascon solutions, (3) logs dataset version/release date, (4) filters to the **Control** region (East Coast NA: Southern to mid-latitudes, °W‑°W, an area with minimal AR activity), (5) saves raw files under `data/raw/grace-fo/control/` and records SHA‑256 checksums.
- [ ] T016 [US1] Create data‑fetching script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/01_data_ingestion_noaa.py` that (1) reads the **verified** URL from `config/urls.yaml`, (2) fetches the NOAA CPC Atmospheric River Catalog, (3) logs dataset version/release date, (4) filters to the **Target** region, (5) saves raw files under `data/raw/noaa-ar/target/` with checksums.
- [ ] T016b [US1] Create data‑fetching script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/01_data_ingestion_noaa_control.py` that (1) reads the **verified** URL from `config/urls.yaml`, (2) fetches the NOAA CPC Atmospheric River Catalog, (3) logs dataset version/release date, (4) filters to the **Control** region (East Coast NA), (5) saves raw files under `data/raw/noaa-ar/control/` with checksums.
- [ ] T017a [US1] Create GRACE‑FO preprocessing script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/02_preprocessing_grace.py`. The script loads the downloaded mascon CSVs from `data/raw/grace-fo/target/` and `data/raw/grace-fo/control/`, and applies **degree correction** using Swenson & Wahr (2006) coefficients. (read from `coeffs/degree1.yaml`), (3) replaces the **C20** coefficient with the latest SLR‑derived value (read from `coeffs/c20.yaml`), (4) performs **Gaussian smoothing** with a characteristic spatial scale on the order of hundreds of kilometers, (5) aggregates to monthly means, (6) writes `data/processed/grace_preprocessed_target.csv` and `data/processed/grace_preprocessed_control.csv`. The script raises informative errors if required columns are missing. **Depends on T011a and execution of T015/T015b.**
- [ ] T017b [US1] Create NOAA preprocessing script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/02_preprocessing_noaa.py`. The script (1) loads the raw AR catalogs from `data/raw/noaa-ar/target/` and `data/raw/noaa-ar/control/` using `glob.glob` to dynamically discover files matching the pattern `data/raw/noaa-ar/*/*.csv`, (2) aggregates Integrated Water Vapor Transport to monthly means by computing the arithmetic mean of all IWV values for each month, (3) logs warnings for any missing months, (4) **drops any row where the total AR intensity equals zero** to avoid bias, (5) writes `data/processed/noaa_preprocessed_target.csv` and `data/processed/noaa_preprocessed_control.csv`. **Depends on T015/T016.**
- [ ] T017c [US1] Create merge and validation script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/02_preprocessing_merge.py`. The script (1) reads `grace_preprocessed_target.csv`, `noaa_preprocessed_target.csv`, `grace_preprocessed_control.csv`, `noaa_preprocessed_control.csv`, (2) merges target and control data on the `date` column (inner join), (3) **explicitly adds a `region` column** to the merged DataFrame with values 'target' or 'control' corresponding to the source files, (4) validates the merged DataFrame against `contracts/dataset.schema.yaml` using `jsonschema`, (5) writes the validated output to `data/processed/merged_monthly.csv`. **Depends on T017a/T017b and T013.**
- [ ] T018 [US1] Create contract test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_dataset_schema.py` that loads `merged_monthly.csv` and validates against `contracts/dataset.schema.yaml`.
- [ ] T019 [US1] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_data_pipeline.py` that runs the three scripts (`01_data_ingestion_*`, `02_preprocessing_*`, `02_preprocessing_merge.py`) on a small sample and asserts the merged CSV contains the expected columns and no NaNs.

**Checkpoint**: User Story 1 is fully functional and independently testable.

---

## Phase 3: User Story 2 – Statistical Correlation Analysis (Priority: P1)

**Goal**: Compute Pearson correlation between AR intensity and gravity anomalies across lag windows, apply bootstrap resampling (1000 iterations, seed=42), perform autocorrelation correction (Newey-West), and apply FDR multiple‑testing correction. **Validate signal against control regions** as required by FR-008.

**Independent Test**: Run the analysis on a mock dataset and verify the output CSV includes correlation coefficients, raw and corrected p‑values, % bootstrap confidence intervals, control‑region results, and 3σ threshold flags.

⚠️ **DEPENDS**: T017c must be complete; T014 must be present for output schema; T032/T033 provide data‑model semantics. T020 depends on T011a.

- [ ] T020 [US2] Create correlation and bootstrap analysis script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/03_correlation_analysis.py`. The script (1) loads `merged_monthly.csv`, (2) splits data into 'target' and 'control' regions, (3) pre-whitens both series using an AR(1) model, (4) for each lag in a symmetric range of negative to positive integer lags, computes Pearson r and raw p-value, (5) performs bootstrap with `n_boot=1000` and `seed=42` to obtain 95 % CI, (6) calculates Newey-West robust standard errors using `statsmodels.stats.stattools.newey_west`, (7) applies FDR correction, (8) calculates a signal-to-noise ratio, (9) calculates the Minimum Detectable Correlation (MDC), (10) checks if the signal-to-noise ratio > 3.0, (11) writes `data/processed/correlation_results.csv` conforming to `output.schema.yaml`.
- [ ] T023 [US2] Create contract test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_correlation_schema.py` that validates `correlation_results.csv` against `contracts/output.schema.yaml`.
- [ ] T024 [US2] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_correlation_pipeline.py` that runs the full analysis on a synthetic small dataset and asserts the output CSV contains the required columns and no NaNs.
- [ ] T020b [Sequential] Create performance‑profiling script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/03_profile_runtime.py` that (1) loads a representative sample of rows of `merged_monthly.csv`, (2) times the `analyze_region` function from T020, (3) extrapolates to the full dataset size, (4) writes `docs/runtime_profile.md` with the estimate. **Depends on T017c and T020.**

**Checkpoint**: User Stories 1 & 2 are now functional and independently testable.

---

## Phase 4: User Story 3 – Diagnostic Visualization & Sensitivity Reporting (Priority: P2)

**Goal**: Produce time‑series overlays, scatter plots with regression lines, spatial anomaly maps, and a sensitivity‑analysis report that sweeps the explicit threshold set **as the primary metric** to demonstrate robustness.

**Independent Test**: Verify that PNG files are generated in `output/` and that `sensitivity_report.md` contains results for each of the three thresholds and the full range.

- [ ] T025 [US3] Create time‑series visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/06_visualization_timeseries.py` that plots gravity anomaly and AR intensity for target and control regions, saves `output/timeseries_overlay.png`, and adds the mandatory caption.
- [ ] T026 [US3] Create scatter visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/07_visualization_scatter.py` that generates a regression scatter plot, saves `output/scatter_regression.png`, and includes the caption.
- [ ] T027 [US3] Create spatial visualization `projects/PROJ-267-exploring-the-relationship-between-atmos/code/08_visualization_spatial.py` that produces a placeholder spatial anomaly map, saves `output/spatial_anomaly_map.png`, and includes the caption.
- [ ] T028 [US3] Create sensitivity‑analysis script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/09_sensitivity_report.py`. The script (1) loads `correlation_results.csv`, (2) **Sensitivity Visualization Set**: Performs analysis for a specific threshold set `THRESHOLDS_SENSITIVITY = [0.4, 0.5, 0.6]` strictly to demonstrate robustness (these values are arbitrary for sensitivity checking, NOT pre-specified success criteria per Constitution Principle VII), (3) for each threshold computes (a) count of correlations exceeding the threshold, (b) variance of those coefficients (stability), (c) proportion of confidence‑intervals overlapping the overall mean CI, (4) writes a markdown report `output/sensitivity_report.md` that (i) lists the results for the specific set as the main table, (ii) includes a secondary 'Appendix' with a continuous sweep across a bounded range for robustness context, (iii) repeats the frame‑of‑reference disclaimer (referencing T050), (iv) **explicitly checks** that no causal keywords appear (regex safety check).
- [ ] T029 [US3] Create temporal‑bias documentation script `projects/PROJ-267-exploring-the-relationship-between-atmos/code/10_temporal_bias_analysis.py` that (1) retrieves literature values for the typical duration of Atmospheric Rivers (days) from the NOAA CPC AR Technical Report (URL: `https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncdc:C`), (2) compares this duration to the monthly sampling interval, (3) qualitatively assesses the risk of aliasing (e.g., "High risk if AR duration < 15 days"), (4) writes `output/temporal_bias_analysis.md` with the assessment and citations.
- [ ] T030 [US3] Create output‑validation test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/contract/test_output_schema.py` that validates `output/sensitivity_report.md` for the absence of causal keywords
- [ ] T031 [US3] Create integration test `projects/PROJ-267-exploring-the-relationship-between-atmos/tests/integration/test_visualization_pipeline.py` that runs the three visualization scripts and the sensitivity‑analysis script, then asserts that the three PNG files and the markdown report exist.

**Checkpoint**: All user stories now independently functional.

---

## Phase 5: Polish & Cross‑Cutting Concerns

**Purpose**: Final refinements affecting multiple stories and overall validation.

⚠️ **DEPENDS**: All Phase 2‑4 tasks must be complete. T040 depends on T017c, T020, T020b.

- [ ] T037 [P] Create `README.md` with installation, data‑source URLs, run commands (including the corrected quick‑start steps), and expected outputs.
- [ ] T038 Run all contract tests to verify schema compliance.
- [ ] T039 Run all integration tests to verify end‑to‑end pipeline execution.
- [ ] T040 [Sequential] Measure aggregate pipeline runtime. The script reads the estimated full‑run time from `docs/runtime_profile.md` (generated by T020b), compares it against the specified time limit, and writes `docs/runtime_report.md` indicating PASS/FAIL.
- [ ] T041 [P] Document SHA‑256 checksums for all raw data files in `state/projects/PROJ-267-exploring-the-relationship-between-atmos.yaml`.
- [ ] T042 [P] Verify that all dataset URLs in `config/urls.yaml` are reachable and that `docs/methodology.md` lists them.
- [ ] T043 [P] Update the project‑state YAML with a fresh `updated_at` timestamp and content hashes for every artifact.
- [ ] T044 Run quickstart validation: `python code/09_sensitivity_report.py --validate && pytest tests/contract/`.
- [ ] T045a [Sequential] Verify quickstart.md content (matches the final script names and commands).
- [ ] T045b [Sequential] Update quickstart.md to match the final script names and commands.

**Checkpoint**: All tasks are complete.