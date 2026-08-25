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

- [X] T001 Create project structure per `plan.md` "Project Structure" code block: `projects/PROJ-031-exploring-the-correlation-between-solar-/` containing `code/`, `data/`, `results/`, `contracts/`, `tests/`, `requirements.txt`, `README.md`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, statsmodels, requests, pyyaml, pytest)
- [X] T003 [P] Configure linting (flake8/pylint) and formatting (black/isort)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `contracts/aligned_event.schema.yaml` defining SolarFlareEvent, CMEEvent, GeomagneticStorm, and AlignedEvent entities
- [X] T005 [P] Create `contracts/metrics.schema.yaml` defining correlation coefficients, p-values, R², VIF, and threshold metrics
- [X] T006 [P] [Foundational] Create `code/versioning.py` for SHA-256 hashing and state file updates (`state/projects/PROJ-031-...yaml`)
- [X] T006b [P] [Foundational] Define the `code/profiler.py` interface (function signatures) for end-to-end timing and peak RAM measurement. **This task MUST NOT execute the profiling; it only sets up the module.**
- [X] T006c [P] [Foundational] Create `config/profiler_config.yaml` defining timing thresholds (6h) and RAM thresholds (7GB) for validation.

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

- [X] T011 [US1] Implement `code/ingest.py` to download GOES X-ray flare lists, SOHO/LASCO CME data, and Dst indices from NOAA SWPC/CDAWeb. **Constraint**: Explicitly enforce a download window spanning **2010-01-01 to 2023-12-31**. If the current date is after 2023, truncate the download at 2023-12-31. **Pre-flight validation**: Explicitly check for and reject any imports of `datasets` (HuggingFace) or `huggingface_hub`. If found, raise an `ImportError` with a message citing the Assumptions section.
- [X] T011b [US1] **Date Range Validation**: Add a validation step in `code/ingest.py` to verify the downloaded data covers **2010-01-01 to 2023-12-31**. Verification logic: `min(date) == 2010-01-01 AND max(date) >= 2023-12-31`. If incomplete, raise a `DataWindowError`. **Log Format**: "Window: {start} to {end}, Duration: {years} years. Missing: {missing_years}".
- [X] T012 [US1] Implement `code/ingest.py` to retrieve CME catalog data (speed, width, direction) from CDAWeb SOHO/LASCO
- [X] T012b [US1] Implement `code/ingest.py` utility to verify the CDAWeb SOHO/LASCO URL is reachable and returns valid data; update `data/source_manifest.yaml` with **exact keys**: if successful, write `cme_status: Verified`, `cme_url: <actual_url>`, `retrieved_at: <timestamp>`; if failed, write `cme_status: Unverified`.
- [X] T013 [US1] Implement `code/ingest.py` to download Dst indices from NOAA SWPC and write to `data/raw/dst_indices.csv`. **Note**: Do NOT validate against `aligned_event.schema.yaml` here; defer validation to alignment step.
- [X] T013b [US1] Implement `code/ingest.py` to download Kp indices from NOAA SWPC and write to `data/raw/kp_indices.csv`; defer validation to alignment step.
- [X] T014 [US1] Implement `code/align.py` to identify Dst minima (storms) independently, then match preceding solar events within ≤3-day window
- [X] T015 [US1] Implement `code/align.py` logic to flag missing solar predictors as null (do NOT exclude events) and handle "no match found" cases
- [X] T016 [US1] Implement logic to flag recurrent activity periods in the primary dataset with a `is_recurrent` flag.
- [X] T016b [US1] Implement logic to filter non-recurrent storms from the primary dataset to create a derived `data/processed/analysis_subset.csv`. **Filtering Rule**: Only include distinct minima separated by ≥24 hours of recovery. **Depends on T016.**
- [X] T017 [US1] Implement blocking validation gate in `code/validate.py` to check `aligned_events.csv` against `contracts/aligned_event.schema.yaml`. **Failure Behavior**: If validation fails, raise a `ValidationError` exception and exit immediately; do not write the file.
- [X] T018 [US1] Write `data/processed/aligned_events.csv` and update `data/source_manifest.yaml` with checksums (only if T017 passes)
- [X] T018b [US1] **Atomic Write**: Implement atomic write logic for `aligned_events.csv` to prevent partial file corruption. Write to a temporary file first, then rename to the final path only after successful write and checksum verification.
- [X] T019 [US1] Add logging for data quality metrics (counts of missing CME speeds, flares, etc.)
- [X] T006d [P] [Foundational] Depends on T011/T012/T018. Implement `code/profiler.py` logic for an **early profiling run** on a **limited subset (first 1000 rows)** of the data to verify FR-010 feasibility (RAM ≤7 GB, Time ≤6 h) before full implementation. **This task MUST run after T018.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Compute Spearman correlations, perform linear regression with VIF checks, and execute post-hoc power analysis.

**Independent Test**: Verify correlation coefficients, p-values, R², VIF, and power analysis warnings are computed and output correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for `metrics.json` schema validation in `tests/contract/test_metrics.py`
- [X] T021 [P] [US2] Unit test for Spearman correlation and VIF calculation logic in `tests/unit/test_analysis.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/analysis.py` to compute Spearman rank correlation (log-transformed flare flux→Dst and CME speed→Dst) with p-values. **Input: MUST consume `data/processed/analysis_subset.csv` (created by T016b).** **Depends on T016b.**
- [X] T024 [US2] **VIF & Model Selection**: Implement Variance Inflation Factor (VIF) calculation. **If VIF > 5:** Compute separate univariate linear models. Select the univariate model with the **higher absolute correlation coefficient** as the primary report. Record the **selected model type** (e.g., "univariate_flare") in `results/metrics.json` under the key `selected_model_type`. **Do NOT use AIC for selection.** **Output**: Write `selected_model_type` to `results/metrics.json`.
- [X] T023 [US2] **Linear Regression Output**: Implement linear regression modeling using the model selected in T024. Calculate R² for the **selected model** (not the discarded joint model). Output the R² value to `results/metrics.json` under the key `selected_model_r2`. **Input**: Use the `selected_model_type` from T024. **MUST write 'selected_model_r2' before T026 runs.**
- [X] T023b [US2] **Multiple Comparison Correction**: Implement multiple-comparison correction using **Bonferroni** (as per Plan.md decision). **Constraint**: This method is FIXED; do NOT allow runtime switching to Benjamini-Hochberg. Record the method name in `results/metrics.json`. **Execute after T024 to ensure model selection is final.**
- [X] T025 [US2] Implement post-hoc power analysis using pre-specified effect size r=0.30; log warning if N < 30.
- [X] T025b [US2] **Citation Verification**: Verify the "Zhang et al., 2020" citation against the primary source (DOI check). Record the verification status (`citation_verified`: true/false) in `results/metrics.json`. **Dependency**: Must complete before T025 finalizes.
- [X] T026 [US2] If R² from the **selected model** (read `selected_model_r2` from `results/metrics.json` written by T023) is < 0.1, test a non-linear (piecewise) model using **statsmodels Patsy formula with breakpoints** or **scikit-learn PiecewiseRegression**. Report the improvement in fit (**delta R²**) compared to the selected model. **Skip Condition**: If T023/T024 fail or R² >= 0.1, skip this task. **Depends on T023 & T024.**
- [X] T026b [US2] **Validation**: Ensure `results/metrics.json` contains the key `piecewise_r2_improvement` if T026 was executed. If T026 was skipped, ensure the key is absent or null.
- [X] T027 [US2] Ensure all findings are framed as associational in output documentation.
- [X] T028 [US2] Validate output against `contracts/metrics.schema.yaml`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Identification and Sensitivity Analysis (Priority: P3)

**Goal**: Identify predictive thresholds using a time-series hold-out set (recent years) and perform sensitivity analysis.

**Independent Test**: Verify threshold identification, hold-out validation, and sensitivity sweep (a range of velocities) are executed correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Contract test for threshold sensitivity results in `tests/contract/test_thresholds.py`
- [X] T031 [P] [US3] Integration test for time-series split validation in `tests/integration/test_threshold_validation.py`

### Implementation for User Story 3

- [X] T032a [US3] **Data Window Validation**: Verify the dataset `data/processed/analysis_subset.csv` contains events spanning **2010-01-01 to 2023-12-31**. If the dataset does not cover this range, raise a `DataWindowError`. **Error Format**: "DataWindowError: Dataset missing year {year}. Required: 2010-2023". **Graceful Failure**: If 2023 is missing, log a "Data Insufficiency" warning with the missing year, set `data_limitation` flag in `results/metrics.json`, and halt with a clear message. Do not crash.
- [X] T032c [US3] **Graceful Failure Handler**: If T032a fails (missing 2023 data), log a specific "Data Insufficiency" warning with the missing year, set a `data_limitation` flag in `results/metrics.json` (e.g., `{"data_limitation": "Missing 2023 data"}`), and halt the pipeline with a clear message. Do not crash.
- [X] T032 [US3] Implement a time-series split: **Enforce the fixed split window defined in Plan.md (Train: a defined historical period; Test: the subsequent period)**. **Pre-check**: Refer to T032a. Do NOT dynamically calculate the split; use the fixed dates from Plan.md as the authoritative strategy per FR-011 and Plan.md override.
- [X] T033 [US3] Implement threshold identification for severe storms (Dst ≤ significant negative threshold) by filtering for severe storm events and analyzing CME speeds.
- [X] T034b [US3] Implement sensitivity analysis sweeping cutoffs over a range of **high-velocity thresholds** with a **step size of 100 km/s**. **Output Format**: JSON list of `{cutoff: int, tpr: float}`. Do NOT include unit strings in the JSON keys.
- [X] T035 [US3] Compute and report True Positive Rate (detection rate) variation across the specified cutoffs on the hold-out set.
- [X] T036 [US3] If no significant threshold is found, explicitly report this with justification.
- [X] T037 [US3] Update `results/metrics.json` with threshold candidates, sensitivity results, and citation.
- [X] T037b [US3] **Citation Injection**: Explicitly inject the NOAA SWPC definition document URL ("https://www.swpc.noaa.gov/phenomena/geomagnetic-storms") into `results/metrics.json` under the key `threshold_citation_url` and into `README.md`.
- [X] T038 [US3] Validate final metrics against `contracts/metrics.schema.yaml`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Update `README.md` to frame findings as associational and include data provenance
- [X] T040 [P] Refactor `code/align.py` to reduce cyclomatic complexity to <10. **Execution Steps**: 1) Ensure `radon` is installed (`pip install radon`). 2) Identify functions in `code/align.py` with complexity ≥10 using `radon cc code/align.py -a -min 10`. 3) Refactor identified functions (e.g., `align_events`, `flag_missing`) to reduce complexity. 4) Verify reduction by re-running `radon cc code/align.py -a`. 5) Generate `reports/complexity_report.md` containing the before/after complexity metrics and a list of refactored functions (function names and scores).
- [X] T041 Performance optimization (ensure execution ≤6h, RAM ≤7GB)
- [X] T042 [P] Additional unit tests in `tests/unit/` targeting [deferred] coverage.
- [X] T043 Run `quickstart.md` validation
- [X] T044 [US1-US3] **Plotting Implementation**: Implement `code/plotting.py` to generate `results/figures/`. **Specific Plots**: 1) Scatter plot of CME speed vs Dst minimum. 2) Scatter plot of log10(Flare Flux) vs Dst minimum. 3) Histogram of threshold distribution. **Output**: Save as PNG/SVG in `results/figures/`.
- [X] T045 [US1-US3] **Full Pipeline Profiling**: Execute the final pipeline profiling on the **full dataset** with profiling enabled.
- [X] T045b [US1-US3] **Performance Metrics Output**: Explicitly write the `performance` block (total execution time, peak RAM usage) to `results/metrics.json` as required by FR-012.
- [X] T067 [US2] **Power Analysis Clarity**: In `code/analysis.py`, ensure the post-hoc power analysis (T025) explicitly calculates the "Minimum Detectable Effect Size" (MDES) using `statsmodels.stats.power.tt_solve_power` (alpha=0.05, power=0.8, nobs=sample_size). If N < 30, the script must not just log a warning but also append a specific "Power Limitation" section to `results/metrics.json` explaining that definitive threshold claims cannot be made.
- [X] T068 [US3] **Threshold Validation Isolation**: Ensure the threshold sensitivity analysis (T034b) strictly uses **only** the data from the hold-out set (recent years) as defined in T032. The training set (-2020) must be completely inaccessible to the threshold sweep logic to prevent data leakage. Add a unit test to verify the data split is strictly enforced.
- [X] T069 [US1] **Atomic Write Implementation**: Ensure `code/ingest.py` and `code/align.py` use atomic writes for all output files to prevent corruption on interruption.
- [X] T070 [US2] **Schema Update**: Update `contracts/metrics.schema.yaml` to include the following new keys: `selected_model_type` (string), `selected_model_r2` (float), `power_limitation` (object/string), `data_limitation` (string), `citation_verified` (boolean).

---

## Revision Tasks (Addressing Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data provenance, streaming, and fail-safe mechanisms.

- [X] T046 [US1] Implement robust error handling in `code/ingest.py` with retry mechanism for NOAA FTP and CDAWeb endpoints.
- [X] T047 [US1] Update `code/ingest.py` to implement streaming for large dataset ingestion.
- [X] T049 [US1] Implement logic to count missing CME speed, flare flux, and Dst data and record the counts in `results/metrics.json`.
- [X] T050 [US3] Update `code/analysis.py` to enforce the fixed time-series split (-2020 / 2021-2023).
- [X] T052 [US1] Update `code/ingest.py` to implement strict fail-loud behavior: remove any `try/except` blocks that fall back to `generate_synthetic_*()` or `mock_*()` functions. If a real data fetch fails, the script MUST raise a clear `DataFetchError` exception and exit, ensuring no synthetic data is ever substituted.
- [X] T053 [US1] Add a docstring to `code/ingest.py` function `download_data` specifying the streaming/sampling rule: "all available data", chunking strategy "process rows in batches of a suitable size", and no random sampling (seed=42 not used).
- [X] T054 [US1] Add a validation step in `code/validate.py` to check for imports of HuggingFace libraries, raising an error if found. **Error Message**: "ImportError: HuggingFace libraries are forbidden per Constitution Principle VI. Use direct NOAA/CDAWeb ingestion."
- [X] T056 [US2] Ensure `code/analysis.py` explicitly cites the Zhang et al. paper when performing the post-hoc power analysis with r=0.30.
- [X] T057 [US3] Update `code/analysis.py` to include the NOAA SWPC definition document URL for the "severe storm" threshold justification.
- [X] T058 [US2] Verify that `code/analysis.py` correctly handles the VIF > 5 condition by switching to univariate models or Ridge regression.
- [X] T059 [US3] Implement a sensitivity sweep over specified cutoffs on the hold-out set and report detection rate variation.
- [X] T060 [US1] Add checksum verification step in `code/validate.py` for downloaded raw data files using **SHA-256** and store results in `state/projects/PROJ-031-...yaml`.
- [X] T061 [US2] Programmatically inject "Findings are associational, not causal" into results/metrics.json.
- [X] T062 [US1-US3] Reconcile run-book vs implementation for `code/main.py`: Create `code/main.py` as the orchestrator script to invoke the pipeline steps in the correct order as defined in the plan. **Order**: 1) Verify Sources (T064), 2) Ingest & Stream (T063), 3) Align (T014), 4) Filter Non-Recurrent (T016b), 5) Analyze (T022).

---

## New Revision Tasks (Addressing Specific Data Integrity and Execution Order)

**Purpose**: Address critical gaps identified in the analysis of data flow, streaming implementation, and strict adherence to the "Fail Loud" principle.

- [X] T063 [US1] **Streaming Implementation**: Refactor `code/ingest.py` to use `requests` with `stream=True` and chunked processing for all large file downloads. **Constraint**: The implementation must never load the entire raw file into memory at once. It must process data in chunks of manageable size and write directly to the final CSV or an intermediate chunked format, ensuring peak RAM usage remains well below a substantial threshold even for multi-year datasets.
- [X] T064 [US1] **Fail-Loud Verification**: Add a dedicated pre-execution check in `code/main.py` that attempts to fetch a single "heartbeat" record from each configured data source (NOAA SWPC, CDAWeb) before starting the full download. If any heartbeat fails, the script MUST raise `DataFetchError` and terminate immediately with a clear error message indicating the failed source. This prevents the pipeline from running with partial or silent-failure data.
- [X] T066 [US1] **Manifest Consistency**: Update `data/source_manifest.yaml` to include a `last_verified_at` timestamp and a `status` field for every source URL. The ingestion script MUST update this file atomically after a successful full download and validation. If the file is missing or corrupted, the pipeline must fail.