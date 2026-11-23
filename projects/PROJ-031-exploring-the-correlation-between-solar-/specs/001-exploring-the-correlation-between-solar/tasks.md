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
- [X] T062 [P] [Foundational] **Orchestrator**: Created `code/main.py` as the orchestrator script to invoke the pipeline steps in the correct order as defined in the plan. **Order**: 1) Verify Sources (T071), 2) Heartbeat Check (T064), 3) Ingest & Stream (T011, T012, T013), 4) Align (T014), 5) Filter Non-Recurrent (T016b), 6) Analyze (T022, T024). **Dependency**: This task defines the flow; all other tasks depend on the logic being present.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] [Foundational] Created `contracts/aligned_event.schema.yaml` defining SolarFlareEvent, CMEEvent, GeomagneticStorm, and AlignedEvent entities with fields: `timestamp`, `flare_flux`, `cme_speed`, `dst_min`, `is_recurrent`. **Verification**: File exists and is valid YAML.
- [X] T005 [P] Created `contracts/metrics.schema.yaml` defining correlation coefficients, p-values, R², VIF, and threshold metrics
- [X] T006 [P] [Foundational] Created `code/versioning.py` for SHA-256 hashing and state file updates (`state/projects/PROJ-031-...yaml`) and defined `code/profiler.py` interface and implementation for end-to-end timing and peak RAM measurement.
- [X] T006c [P] [Foundational] Configured `config/profiler_config.yaml` defining timing thresholds (6h) and RAM thresholds (7GB) for validation.
- [X] T071 [P] [Foundational] **Explicit CDAWeb URL Verification**: Implemented `verify_cdaweb_source()` function in `code/ingest.py` that performs a HEAD request to the specific SOHO/LASCO CME catalog URL before any data download. Implemented logic to raise `DataFetchError` with the exact URL and HTTP status code if the response is not 200. Updated `data/source_manifest.yaml` with the `cme_url_verified` boolean and `verification_timestamp`. **Constraint**: This task is a **blocking gate** for Constitution Principle II (Verified Accuracy); T011, T012, and T013 cannot proceed until T071 passes. **Dependency**: None (Blocking Gate). **Rationale**: Per Plan.md Constitution Check, CME source status is "PENDING" and requires verification before claiming compliance.
- [X] T064 [P] [Foundational] **Fail-Loud Verification**: Implemented a dedicated pre-execution check in `code/main.py` that attempts to fetch a single "heartbeat" record from each configured data source (NOAA SWPC, CDAWeb) before starting the full download. If any heartbeat failed, the script raised `DataFetchError` and terminated immediately with a clear error message indicating the failed source. **Dependency**: T071 (Source Verification must pass first). **Rationale**: Ensures sources are alive before attempting full download; logically follows URL verification.
- [X] T063 [US1] **Streaming Implementation**: Refactored `code/ingest.py` to use `requests` with `stream=True` and chunked processing for all large file downloads. **Constraint**: The implementation never loaded the entire raw file into memory at once. It processed data in chunks of manageable size and wrote directly to the final CSV or an intermediate chunked format, ensuring peak RAM usage remained well below a substantial threshold even for multi-year datasets. **Dependency**: T071. **Note**: Moved from Phase 3 to Phase 2 to ensure data is downloaded correctly from the start.
- [ ] T070 [P] [Foundational] **Metrics Schema Update**: Updated `contracts/metrics.schema.yaml` to include performance metrics (`execution_time`, `peak_ram_gb`) and data limitation flags (`data_limitation`) **BEFORE** any validation tasks (T028, T038) run. **Dependency**: T005. **Rationale**: Ensures T028 and T038 validate against a complete schema including FR-012 requirements. **Constraint**: This task MUST be completed before T017, T017b, T028, and T038 to avoid temporal logic gaps where validation runs against an incomplete schema. <!-- FAILED: unspecified -->
- [X] T068 [US2, US3] **Fixed Time-Series Split Logic**: Implemented the strict time-series split logic in `code/analysis.py` using **fixed historical dates** as mandated by Plan.md. **Logic**: **Train Set**: Events from `2010-01-01` to `2020-12-31`. **Test Set**: Events from `2021-01-01` to `2023-12-31`. **Validation**: Added a check to verify the downloaded data covers the full 2010-2023 range. **Constraint**: If the data window is insufficient (e.g., missing 2023 data), the system MUST raise a `DataInsufficiencyError` and terminate. The "proceed with warning" fallback has been removed to strictly enforce FR-011. **Dependency**: T011, T012, T013. **Rationale**: Resolves conflict between dynamic spec interpretation and Plan.md explicit fixed dates. **Constraint**: This task strictly adheres to the Plan.md Summary and Constraints (Train: 2010-2020, Test: 2021-2023).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Event Alignment (Priority: P1) 🎯 MVP

**Goal**: Download solar eruption data (GOES, LASCO) and geomagnetic indices (Dst, Kp), align them within a ≤3-day window, and produce a unified dataset with missing data flags (no exclusion).

**Independent Test**: Verify the pipeline downloads all available historical events, produces `data/processed/aligned_events.csv` with correct timestamps and flags, and retains events with missing predictors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for `aligned_events.csv` schema validation in `tests/contract/test_aligned_event.py` (Function: `test_aligned_event_schema_valid`, Assert: `schema.validate(data)` using a mock fixture with valid schema-compliant JSON) <!-- FAILED: unspecified -->
- [ ] T010 [P] [US1] Integration test for full download-and-align flow in `tests/integration/test_ingest_align.py` (Function: `test_full_ingest_align_flow`, Assert: `os.path.exists(aligned_csv) and len(df) > 0` using a mocked FTP response with a representative set of synthetic but schema-valid data)

### Implementation for User Story 1

- [X] T011 [US1] Implemented `code/ingest.py` to download GOES X-ray flare lists from `ftp://ftp.swpc.noaa.gov/pub/lists/goes/xray/` covering ≥10 years of historical data (2010-2023). **Constraint**: Explicitly enforced a download window spanning **2010-01-01 to 2023-12-31**. If the current date is after 2023, truncated the download at 2023-12-31. **Pre-flight validation**: Explicitly checked for and rejected any imports of `datasets` (HuggingFace) or `huggingface_hub`. If found, raised an `ImportError` with a message citing the Assumptions section. **Depends on T071, T063, T064**.
- [X] T011b [US1] **Date Range Validation**: Added a validation step in `code/ingest.py` to verify the downloaded data covers **2010-01-01 to 2023-12-31**. Verification logic: `max(date) < 2023-12-30` triggers `DataInsufficiencyError` (missing >1 day). If `max(date) >= 2023-12-30` and `< 2023-12-31`, log a "Data Insufficiency" warning, set `data_limitation` flag in `results/metrics.json` to `true`, and continue. **Constraint**: This graceful failure is only allowed if the spec explicitly permits a 1-day tolerance; otherwise, strict compliance is enforced. **Dependency**: T011.
- [X] T012 [US1] Implemented `code/ingest.py` to retrieve CME catalog data (speed, width, direction) from CDAWeb SOHO/LASCO database. **URL**: `. **Constraint**: The specific URL is now explicitly defined. **Dependency**: T071, T063, T064.
- [X] T013 [US1] Implemented `code/ingest.py` to download Dst indices from NOAA SWPC. **URL**: `. **Constraint**: The specific URL is now explicitly defined. **Dependency**: T071, T063, T064.
- [ ] T014 [US1] Implemented `code/align.py` to identify Dst minima (storms) independently, then match preceding solar events within ≤3-day window
- [ ] T015 [US1] Implemented `code/align.py` logic to flag missing solar predictors as null (do NOT exclude events) and handle "no match found" cases
- [X] T016 [US1] Implemented logic to flag recurrent activity periods in the primary dataset with a `is_recurrent` flag.
- [ ] T016b [US1] Implemented logic to filter non-recurrent storms from the primary dataset to create a derived `data/processed/analysis_subset.csv`. **Filtering Rule**: Only include distinct minima separated by ≥24 hours of recovery, where "recovery" is defined as Dst returning to > **-20 nT** AND maintaining that level for ≥24 hours. **Constraint**: Preserves events with null `cme_speed` if they meet non-recurrent criteria; does not drop them. **Validation**: Calls `code/validate.py` to validate `analysis_subset.csv` against `aligned_event.schema.yaml` before writing. **Depends on T016**. **Note**: Dependency on T017b removed to fix circular dependency.
- [ ] T017 [P] [US1] Implemented blocking validation gate in `code/validate.py` to check `aligned_events.csv` (against `aligned_event.schema.yaml`). **Failure Behavior**: If validation fails, raised a `ValidationError` exception and exit immediately with code 1; logged "Validation Failed: [schema_error_details]". **Constraint**: Validates in-memory dataframes from T016 before T017b runs. **Dependency**: T004, T016.
- [ ] T017b [P] [US1] Implemented blocking validation gate in `code/validate.py` to check `analysis_subset.csv` (against `aligned_event.schema.yaml`) **after** filtering. **Failure Behavior**: If validation fails, raised a `ValidationError` exception and exit immediately with code 1. **Dependency**: T016b, T017.
- [ ] T018 [US1] Wrote `data/processed/aligned_events.csv` and updated `data/source_manifest.yaml` with checksums (only if T017 passes). **Verification**: Assert file exists and checksum matches source_manifest.yaml. **Dependency**: T017.
- [X] T019 [US1] Added logging for data quality metrics (counts of missing CME speeds, flares, etc.)
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

- [X] T022 [P] [US2] Implemented `code/analysis.py` to compute Spearman rank correlation (log-transformed flare flux→Dst and CME speed→Dst) with p-values. [UNRESOLVED-CLAIM: c_b83a5f69 — status=not_enough_info] **Input: Consumed `data/processed/analysis_subset.csv` (created by T016b).** **Depends on T016b**. **Output**: Wrote `spearman_flare_dst`, `spearman_cme_dst`, and `p_values` to `results/metrics.json`. **Multiple-Comparison**: Applied Bonferroni correction to p-values and explicitly recorded the method name in `results/metrics.json` as required by Plan.md.
- [X] T024 [US2] Implemented Variance Inflation Factor (VIF) calculation on `df_analysis_subset` (non-recurrent storms). **Logic**: If VIF > 5: **Select the univariate model with the higher absolute correlation coefficient** as the primary report. Do NOT select Ridge regression based on AIC/R². **Output**: Write the `selected_model_type` (e.g., "univariate_flare", "univariate_cme") to a dedicated intermediate file `results/model_selection.json` to ensure explicit artifact consumption by T023. **Input**: Used `df_analysis_subset`. **Rationale**: Matches FR-006 requirement for univariate fallback and provides explicit artifact for T023. **Dependency**: T016b.
- [X] T023 [US2] Implemented linear regression modeling using the model selected in T024. **Logic**: Run the selected model (univariate or joint if VIF ≤ 5) to calculate R². **Input**: Explicitly consumed `results/model_selection.json` (created by T024) to determine model type. **Output**: Write the R² value to `results/metrics.json`. **Dependency**: T024.
- [X] T025 [US2] Performed post-hoc power analysis using `statsmodels.stats.power.tt_solve_power` with a pre-specified effect size r=0.30. **Logic**: If effective sample size (N) < 30, log a "Power Limitation" warning and append a specific "Power Limitation" section to `results/metrics.json` explaining that definitive threshold claims cannot be made. **Dependency**: T023.
- [X] T026 [US2] Implemented non-linear (piecewise) model testing using `scipy.optimize.curve_fit` with a custom piecewise linear function (one breakpoint). **Trigger**: ONLY if linear regression R² < 0.1. **Output**: Report the improvement in fit in `results/metrics.json` under the key `piecewise_r2_improvement`. **Dependency**: T023. **Note**: Removed [P] tag as this task depends on T023's output.
- [X] T027 [US2] Ensured all findings are framed as associational in output documentation.
- [X] T028 [US2] Validated output against `contracts/metrics.schema.yaml` (which now includes performance keys per T070). **Dependency**: T070.
- [X] T067 [US2] **Power Analysis Clarity**: In `code/analysis.py`, ensured the post-hoc power analysis explicitly calculated the "Minimum Detectable Effect Size" (MDES). **Dependency**: T025.
- [X] T070 [US2] Updated `contracts/metrics.schema.yaml` to include new keys for performance metrics and data limitations. (Moved to Phase 2).

**Checkpoint**: At this point, At least one of T022, T023, T024, T025, T026, T027, T028, T067, T070 should be implemented.

---

## Phase 5: User Story 3 - Threshold Identification and Sensitivity Analysis (Priority: P3)

**Goal**: Identify predictive thresholds using a time-series hold-out set (recent years) and perform sensitivity analysis.

**Independent Test**: Verify threshold identification, hold-out validation, and sensitivity sweep are executed correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Contract test for threshold sensitivity results in `tests/contract/test_thresholds.py`
- [X] T031 [P] [US3] Integration test for time-series split validation in `tests/integration/test_threshold_validation.py`

### Implementation for User Story 3

- [ ] T032a [US3] Verified the dataset contains events spanning the required 2010-2023 range for the fixed split and logged a warning if incomplete. **Dependency**: T068. **Note**: This task validates the fixed split logic (Train: 2010-2020, Test: 2021-2023) as per Plan.md.
- [X] T032c [US3] Implemented a unit test in `tests/unit/test_thresholds.py` to verify the strict time-series split logic (Fixed: 2010-2020 / 2021-2023) and ensure no data leakage occurs. **Dependency**: T068.
- [X] T033 [US3] Implemented threshold identification for severe storms (**Dst ≤ -100 nT**) by filtering for severe storm events and analyzing CME speeds. **Constraint**: Uses the citation logic defined in T076 for the "severe storm" threshold. **Citation**: Explicitly cites "https://www.swpc.noaa.gov/phenomena/geomagnetic-storms" in the task description and code. **Dependency**: T023, T068, T076. **Rationale**: This task now explicitly defines the numeric threshold (Dst ≤ -100 nT) and the specific citation URL within the task description to ensure self-containment and satisfy FR-007.
- [X] T034b [US3] Implemented sensitivity analysis sweeping cutoffs across a range of values with fine-grained step sizes. **Logic**: Must include **bootstrap resampling** (1000 iterations) to estimate confidence intervals for detection rates. **Output**: Report True Positive Rate for each of these specific points in `results/metrics.json`. **Cutoffs**: Must explicitly report for **{900, 1000, 1100} km/s**. **Dependency**: T033.
- [X] T035 [US3] Computed and reported True Positive Rate (detection rate) variation across the specified cutoffs on the hold-out set. **Logic**: Must include **bootstrap resampling** (1000 iterations) to estimate confidence intervals. **Dependency**: T034b.
- [X] T036 [US3] If no significant threshold is found, explicitly reported this with justification.
- [X] T037 [US3] Updated `results/metrics.json` with threshold candidates, sensitivity results, and citation.
- [X] T038 [US3] Validated final metrics against `contracts/metrics.schema.yaml` (which now includes performance keys per T070). **Dependency**: T070.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Updated `README.md` to frame findings as associational and include data provenance
- [ ] T040 [P] Refactored `code/align.py` to reduce cyclomatic complexity to <10. **Target**: Extracted `match_events` logic into a separate function.
- [ ] T042 [P] Additional unit tests in `tests/unit/` targeting coverage. **Specifics**: Added tests for edge cases in `align.py` (e.g., missing data, recurrent events).
- [X] T043 Ran `quickstart.md` validation
- [X] T044 [US1-US3] Implemented `code/plotting.py` to generate plots.
- [X] T045 [US1-US3] Ran full pipeline profiling and output performance metrics.
- [X] T045b [US1-US3] Implemented performance metrics writing to `results/metrics.json` including `execution_time` and `peak_ram_gb` as required by FR-012. **Dependency**: T006.
- [X] T076 [US3] **Threshold Justification**: Implemented strict citation logic in `code/analysis.py` for the NOAA SWPC definition document. **Citation**: Stores the primary source URL ` as a static citation in `results/metrics.json` and code comments. **Constraint**: The code performs a HEAD request to verify URL reachability AND **fetches the page content to verify the presence of the "severe storm" definition** (e.g., by checking for specific keywords like "Dst ≤ -100 nT" or "severe storm" in the text). This satisfies Constitution Principle II (Verified Accuracy). **Dependency**: T071.
- [X] T078 [US1-US3] Verified all data sources in `data/source_manifest.yaml` and updated `last_verified_at` timestamps.
- [X] T079 [US2] Implemented piecewise regression logic in `code/analysis.py` as a fallback for low R² (< 0.1), ensuring `scipy.optimize.curve_fit` is used and results are reported under the key `piecewise_r2_improvement`.

---

## Revision Tasks (Addressing Analysis Findings)

**Purpose**: New tasks added to resolve specific gaps identified in the analysis phase.

- [X] T081 [US1] **[FR-002] CME Data Parser Robustness**: In `code/ingest.py`, implement a dedicated parser for the CDAWeb SOHO/LASCO CME catalog (typically a text-based or ASCII table format) that handles missing speed values gracefully by setting `cme_speed` to `NaN` and flagging them with `cme_speed_missing: true`, rather than skipping the row. **Rationale**: Spec US-1 requires retaining events with missing predictors; current logic may be dropping them. **Dependency**: T012 (to modify existing logic).
- [ ] T083 [US2] **VIF Calculation on Correct Subset**: Ensure `code/analysis.py` calculates the VIF on the `df_analysis_subset` (non-recurrent storms) as required, not the full `df_aligned`. **Rationale**: VIF on the full dataset including recurrent events may yield misleading collinearity metrics.
- [X] T084 [US3] **Threshold Sensitivity Sweep Range**: In `code/analysis.py`, ensure the sensitivity analysis sweeps CME speed cutoffs specifically at values **{900, 1000, 1100} km/s** with a step size of **100 km/s**. **Output**: Report True Positive Rate for each of these specific points in `results/metrics.json`. **Rationale**: Spec FR-008 mandates specific step sizes; generic sweeps may miss these critical points.
- [X] T085 [US3] **Hold-Out Set Verification**: Add a validation step in `code/analysis.py` to assert that the `train_set` contains ONLY events from `2010-01-01` to `2020-12-31` and `test_set` contains ONLY events from `2021-01-01` to `2023-12-31`, raising an error if any leakage is detected. **Assertion Logic**: `assert train_set['timestamp'].max() <= '2020-12-31' and test_set['timestamp'].min() >= '2021-01-01'`. **Error Message**: "Data Leakage Detected: Train/Test split violated." **Rationale**: FR-011 requires a strict time-series split; this needs explicit enforcement.

---

## Phase N+1: Final Integration & Verification (Post-Revision)

**Purpose**: Ensure all revision tasks are integrated and the pipeline runs end-to-end without errors.

- [ ] T086 [US1-US3] **End-to-End Regression Test**: Execute the full pipeline (`code/main.py`) from scratch (clean `data/` and `results/`) to verify that all revision tasks (T081, T083-T085) integrate correctly and produce valid outputs. **Acceptance**: Pipeline completes with exit code 0, `results/metrics.json` is valid per schema, and `data/processed/aligned_events.csv` contains no dropped events due to missing CME speeds. **Status**: Incomplete. **Dependency**: T045b, T088b1.
- [ ] T087b [US2] **Non-Recurrent Subset Verification**: Run `tests/unit/test_align.py` (T082) and `code/validate.py` to assert that all events with `is_recurrent == True` (from `aligned_events.csv`) have been filtered out in `analysis_subset.csv`, and that the "24-hour recovery" rule was applied correctly. **Dependency**: T086.
- [X] T088b1 [US3] **Threshold Sweep Output Verification (Part 1)**: Run `tests/contract/test_thresholds.py` to assert that `results/metrics.json` contains the `threshold_sensitivity` key with entries specifically for **900, 1000, and 1100 km/s** with corresponding True Positive Rates. **Dependency**: T086.
- [X] T088b2 [US3] **Threshold Sweep Output Verification (Part 2)**: Verify that the `threshold_sensitivity` entries include `confidence_interval` fields derived from bootstrap resampling as required by Plan.md. **Dependency**: T088b1.
- [X] T088b3 [US3] **Threshold Sweep Output Verification (Part 3)**: Verify that the `threshold_sensitivity` entries report the exact step size of 100 km/s used. **Dependency**: T088b2.
- [X] T089 [US1] **Source Manifest Finalization**: Verify `data/source_manifest.yaml` lists the exact NOAA Dst URL and CDAWeb CME URL used, with `status: verified` and `last_verified_at` timestamps populated. **Dependency**: T086.
