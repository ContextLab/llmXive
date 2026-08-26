# Tasks: Exploring the Correlation Between Solar Flare Characteristics and Geomagnetic Storm Intensities

**Input**: Design documents from `/specs/001-solar-flare-storm-correlation/`
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

- [X] T001 Created project structure per `plan.md` "Project Structure" code block: `projects/PROJ-031-exploring-the-correlation-between-solar-/` containing `code/`, `data/`, `results/`, `contracts/`, `tests/`, `requirements.txt`, `README.md`
- [X] T002 Initialized Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, statsmodels, requests, pyyaml, pytest)
- [X] T003 [P] Configured linting (flake8/pylint) and formatting (black/isort)
- [X] T062 [P] [Foundational] **Orchestrator**: Created `code/main.py` as the orchestrator script to invoke the pipeline steps in the correct order as defined in the plan. **Order**: 1) Verify Sources (T071), 2) Ingest & Stream (T063), 3) Align (T014), 4) Filter Non-Recurrent (T016b), 5) Analyze (T022). **Dependency**: This task defines the flow; all other tasks depend on the logic being present.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] [Foundational] Created `contracts/aligned_event.schema.yaml` defining SolarFlareEvent, CMEEvent, GeomagneticStorm, and AlignedEvent entities with fields: `timestamp`, `flare_flux`, `cme_speed`, `dst_min`, `is_recurrent`. **Verification**: File exists and is valid YAML.
- [X] T005 [P] Created `contracts/metrics.schema.yaml` defining correlation coefficients, p-values, R², VIF, and threshold metrics
- [X] T006 [P] [Foundational] Created `code/versioning.py` for SHA-256 hashing and state file updates (`state/projects/PROJ-031-...yaml`)
- [X] T006b [P] [Foundational] Defined the `code/profiler.py` interface (function signatures) for end-to-end timing and peak RAM measurement. **This task set up the module; profiling execution is deferred to T045.**
- [X] T006c [P] [Foundational] Configured `config/profiler_config.yaml` defining timing thresholds (6h) and RAM thresholds (7GB) for validation.
- [X] T071 [P] [Foundational] **Explicit CDAWeb URL Verification**: Implemented `verify_cdaweb_source()` function in `code/ingest.py` that performs a HEAD request to the specific SOHO/LASCO CME catalog URL before any data download. Implemented logic to raise `DataFetchError` with the exact URL and HTTP status code if the response is not 200. Updated `data/source_manifest.yaml` with the `cme_url_verified` boolean and `verification_timestamp`. **Constraint**: This task is a **blocking gate** for Constitution Principle II (Verified Accuracy); T011 and T012 cannot proceed until T071 passes. **Dependency**: None (Blocking Gate). **Rationale**: Per Plan.md Constitution Check, CME source status is "PENDING" and requires verification before claiming compliance.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Event Alignment (Priority: P1) 🎯 MVP

**Goal**: Download solar eruption data (GOES, LASCO) and geomagnetic indices (Dst, Kp), align them within a ≤3-day window, and produce a unified dataset with missing data flags (no exclusion).

**Independent Test**: Verify the pipeline downloads all available historical events, produces `data/processed/aligned_events.csv` with correct timestamps and flags, and retains events with missing predictors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for `aligned_events.csv` schema validation in `tests/contract/test_aligned_event.py` (Function: `test_aligned_event_schema_valid`, Assert: `schema.validate(data)` using a mock fixture with valid schema-compliant JSON)
- [X] T010 [P] [US1] Integration test for full download-and-align flow in `tests/integration/test_ingest_align.py` (Function: `test_full_ingest_align_flow`, Assert: `os.path.exists(aligned_csv) and len(df) > 0` using a mocked FTP response with a representative set of synthetic but schema-valid data)

### Implementation for User Story 1

- [X] T011 [US1] Implemented `code/ingest.py` to download GOES X-ray flare lists, SOHO/LASCO CME data, and Dst indices from NOAA SWPC/CDAWeb. **Constraint**: Explicitly enforced a download window spanning **2010-01-01 to 2023-12-31**. If the current date is after 2023, truncated the download at 2023-12-31. **Pre-flight validation**: Explicitly checked for and rejected any imports of `datasets` (HuggingFace) or `huggingface_hub`. If found, raised an `ImportError` with a message citing the Assumptions section. **Depends on T071**.
- [X] T011b [US1] **Date Range Validation**: Added a validation step in `code/ingest.py` to verify the downloaded data covers **2010-01-01 to 2023-12-31**. Verification logic: `min(date) >= 2010-01-01 AND max(date) >= 2023-12-31`. If incomplete (missing >1 day of data at either end), raised `DataInsufficiencyError`. If missing <=1 day, logged a "Data Insufficiency" warning, set `data_limitation` flag in `results/metrics.json` to `true`, and continued. **Graceful Failure**: If the window is slightly off (e.g., missing <=1 day), logged a warning and set `data_limitation` flag. **Dependency**: T011.
- [X] T012 [US1] Implemented `code/ingest.py` to retrieve CME catalog data (speed, width, direction) from CDAWeb SOHO/LASCO. **Depends on T071**.
- [X] T013 [US1] Implemented `code/ingest.py` to download Dst indices from NOAA SWPC using the explicit URL ` and write to `data/raw/dst_indices.csv`. **Verification**: Assert file exists and contains >0 rows. **Note**: Did NOT validate against `aligned_event.schema.yaml` here; deferred validation to alignment step. **Dependency**: T011.
- [X] T014 [US1] Implemented `code/align.py` to identify Dst minima (storms) independently, then match preceding solar events within ≤3-day window
- [X] T015 [US1] Implemented `code/align.py` logic to flag missing solar predictors as null (do NOT exclude events) and handle "no match found" cases
- [X] T016 [US1] Implemented logic to flag recurrent activity periods in the primary dataset with a `is_recurrent` flag.
- [X] T016b [US1] Implemented logic to filter non-recurrent storms from the primary dataset to create a derived `data/processed/analysis_subset.csv`. **Filtering Rule**: Only include distinct minima separated by ≥24 hours of recovery, where "recovery" is defined as Dst returning to > -20 nT. **Depends on T016.**
- [X] T017 [US1] Implemented blocking validation gate in `code/validate.py` to check `aligned_events.csv` against `contracts/aligned_event.schema.yaml`. **Failure Behavior**: If validation fails, raised a `ValidationError` exception and exit immediately with code 1; logged "Validation Failed: [schema_error_details]". **Dependency**: T004.
- [X] T018 [US1] Wrote `data/processed/aligned_events.csv` and updated `data/source_manifest.yaml` with checksums (only if T017 passes). **Verification**: Assert file exists and checksum matches source_manifest.yaml. **Dependency**: T017.
- [X] T019 [US1] Added logging for data quality metrics (counts of missing CME speeds, flares, etc.)
- [X] T025a [US1] Applied multiple comparison correction (Bonferroni (Wikidata Q87892954, https://www.wikidata.org/wiki/Q87892954)) to all hypothesis tests and recorded the method name in `results/metrics.json`.
- [X] T063 [US1] **Streaming Implementation**: Refactored `code/ingest.py` to use `requests` with `stream=True` and chunked processing for all large file downloads. **Constraint**: The implementation never loaded the entire raw file into memory at once. It processed data in chunks of manageable size and wrote directly to the final CSV or an intermediate chunked format, ensuring peak RAM usage remained well below a substantial threshold even for multi-year datasets. **Dependency**: T011, T012, T013.
- [X] T064 [US1] **Fail-Loud Verification**: Added a dedicated pre-execution check in `code/main.py` that attempts to fetch a single "heartbeat" record from each configured data source (NOAA SWPC, CDAWeb) before starting the full download. If any heartbeat failed, the script raised `DataFetchError` and terminated immediately with a clear error message indicating the failed source. **Dependency**: T011, T012, T013.
- [X] T066 [US1] **Manifest Consistency**: Updated `data/source_manifest.yaml` to include a `last_verified_at` timestamp and a `status` field for every source URL. The ingestion script updates this file atomically after a successful full download and validation. If the file is missing or corrupted, the pipeline fails.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Compute Spearman correlations, perform linear regression with VIF checks, and execute post-hoc power analysis.

**Independent Test**: Verify correlation coefficients, p-values, R², VIF, and power analysis warnings are computed and output correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for `metrics.json` schema validation in `tests/contract/test_metrics.py`
- [X] T021 [P] [US2] Unit test for Spearman correlation and VIF calculation logic in `tests/unit/test_analysis.py`

### Implementation for User Story 2

- [X] T022 [US2] Implemented `code/analysis.py` to compute Spearman rank correlation (log-transformed flare flux→Dst and CME speed→Dst) with p-values. **Input: Consumed `data/processed/analysis_subset.csv` (created by T016b).** **Depends on T016b**. **Output**: Wrote `spearman_flare_dst`, `spearman_cme_dst`, and `p_values` to `results/metrics.json`. **Multiple-Comparison**: Applied Bonferroni correction to p-values.
- [X] T023 [US2] Implemented linear regression modeling using the model selected in T024. Calculated R² for the selected model. Output the R² value to `results/metrics.json`. **Input**: Used the `selected_model_type` from T024.
- [X] T024 [US2] Implemented Variance Inflation Factor (VIF) calculation. If VIF > 5: Computed separate univariate models. Selected the univariate model with the higher absolute correlation coefficient as the primary report. Recorded the selected model type in `results/metrics.json`. **Input**: Used `df_analysis_subset`.
- [X] T025 [US2] Performed post-hoc power analysis using a pre-specified effect size r=0.30; logged warning if N < 30.
- [X] T026 [US2] Implemented non-linear (piecewise) model testing using `scipy.optimize.curve_fit` with a custom piecewise linear function.
- [X] T027 [US2] Ensured all findings are framed as associational in output documentation.
- [X] T028 [US2] Validated output against `contracts/metrics.schema.yaml`
- [X] T067 [US2] **Power Analysis Clarity**: In `code/analysis.py`, ensured the post-hoc power analysis explicitly calculated the "Minimum Detectable Effect Size" (MDES) using `statsmodels.stats.power.tt_solve_power`. If N < 30, appended a specific "Power Limitation" section to `results/metrics.json` explaining that definitive threshold claims cannot be made.
- [X] T070 [US2] Updated `contracts/metrics.schema.yaml` to include new keys for performance metrics and data limitations.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Identification and Sensitivity Analysis (Priority: P3)

**Goal**: Identify predictive thresholds using a time-series hold-out set (recent years) and perform sensitivity analysis.

**Independent Test**: Verify threshold identification, hold-out validation, and sensitivity sweep are executed correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Contract test for threshold sensitivity results in `tests/contract/test_thresholds.py`
- [X] T031 [P] [US3] Integration test for time-series split validation in `tests/integration/test_threshold_validation.py`

### Implementation for User Story 3

- [X] T032a [US3] Verified the dataset contains events spanning 2010-01-01 to 2023-12-31 and logged a warning if incomplete.
- [X] T032c [US3] Implemented a unit test in `tests/unit/test_thresholds.py` to verify the strict time-series split logic (Train: 2010-2020, Test: 2021-2023) and ensure no data leakage occurs.
- [X] T033 [US3] Implemented threshold identification for severe storms (Dst ≤ significant negative threshold) by filtering for severe storm events and analyzing CME speeds.
- [X] T034b [US3] Implemented sensitivity analysis sweeping cutoffs over a range of high-velocity thresholds with a step size.
- [X] T035 [US3] Computed and reported True Positive Rate (detection rate) variation across the specified cutoffs on the hold-out set.
- [X] T036 [US3] If no significant threshold is found, explicitly reported this with justification.
- [X] T037 [US3] Updated `results/metrics.json` with threshold candidates, sensitivity results, and citation.
- [X] T038 [US3] Validated final metrics against `contracts/metrics.schema.yaml`
- [X] T068 [US3] Implemented the strict time-series split logic in `code/analysis.py` to isolate Train (2010-2020) and Test (2021-2023) sets. Implemented the verification test in `tests/integration/test_threshold_validation.py` to ensure the hold-out set is strictly used for validation only.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Updated `README.md` to frame findings as associational and include data provenance
- [X] T040 [P] Refactored `code/align.py` to reduce cyclomatic complexity to <10. **Target**: Extracted `match_events` logic into a separate function.
- [X] T041 Performance optimization (ensure execution ≤6h, RAM ≤7GB)
- [X] T042 [P] Additional unit tests in `tests/unit/` targeting coverage. **Specifics**: Added tests for edge cases in `align.py` (e.g., missing data, recurrent events).
- [X] T043 Ran `quickstart.md` validation
- [X] T044 [US1-US3] Implemented `code/plotting.py` to generate plots.
- [X] T045 [US1-US3] Ran full pipeline profiling and output performance metrics.
- [X] T045b [US1-US3] Implemented performance metrics writing to `results/metrics.json` including`execution_time` and `peak_ram_gb` as required by FR-012.
- [X] T076 [US3] **Threshold Justification**: Implemented strict citation logic in `code/analysis.py` for the NOAA SWPC definition document. (Wikidata Q24576, https://www.wikidata.org/wiki/Q24576)
- [X] T078 [US1-US3] Verified all data sources in `data/source_manifest.yaml` and updated `last_verified_at` timestamps.
- [X] T079 [US2] Implemented piecewise regression logic in `code/analysis.py`as a fallback for low R², ensuring `scipy.optimize.curve_fit` is used and results are reported.

---

## Revision Tasks (Addressing Analysis Findings)

**Purpose**: New tasks added to resolve specific gaps identified in the analysis phase.

- [X] T080 [US1] **Explicit NOAA Dst URL Implementation**: In `code/ingest.py`, replace any generic "NOAA SWPC" references with the explicit URL ` and implement a robust parser for the JSON response. **Parser Logic**: Extract 'dst' field from 'data' array. **Error Handling**: Raise `DataFetchError` if JSON is malformed or 'dst' is missing. **Rationale**: Spec FR-003 requires a real, reachable URL; generic references are insufficient for the "Fail-Loud" check.
- [X] T081 [US1] **CME Data Parser Robustness**: In `code/ingest.py`, implement a dedicated parser for the CDAWeb SOHO/LASCO CME catalog (typically a text-based or ASCII table format) that handles missing speed values gracefully by setting `cme_speed` to `NaN` and flagging them with `cme_speed_missing: true`, rather than skipping the row. **Rationale**: Spec US-1 requires retaining events with missing predictors; current logic may be dropping them.
- [X] T082 [US1] **Recurrent Storm Logic Verification**: In `code/align.py`, explicitly implement the "≥24 hours of recovery" rule for identifying distinct minima. Add a unit test in `tests/unit/test_align.py` to verify that two storms occurring 12h apart are correctly flagged as recurrent (`is_recurrent == True`). **Rationale**: Assumption in spec states non-recurrent storms must be used; this logic needs explicit implementation and verification.
- [X] T083 [US2] **VIF Calculation on Correct Subset**: Ensure `code/analysis.py` calculates the VIF on the `df_analysis_subset` (non-recurrent storms) as required, not the full `df_aligned`. **Rationale**: VIF on the full dataset including recurrent events may yield misleading collinearity metrics.
- [X] T084 [US3] **Threshold Sensitivity Sweep Range**: In `code/analysis.py`, ensure the sensitivity analysis sweeps CME speed cutoffs specifically at 900, 1000, and 1100 km/s with a step size of 100 km/s. **Output**: Report True Positive Rate for each of these specific points in `results/metrics.json`. **Rationale**: Spec FR-008 mandates specific step sizes; generic sweeps may miss these critical points.
- [X] T085 [US3] **Hold-Out Set Verification**: Add a validation step in `code/analysis.py` to assert that the `train_set` contains ONLY events from 2010-2020 and `test_set` contains ONLY events from 2021-2023, raising an error if any leakage is detected. **Assertion Logic**: `assert train_set['year'].max() <= 2020 and test_set['year'].min() >= 2021`. **Error Message**: "Data Leakage Detected: Train/Test split violated." **Rationale**: FR-011 requires a strict time-series split; this needs explicit enforcement.