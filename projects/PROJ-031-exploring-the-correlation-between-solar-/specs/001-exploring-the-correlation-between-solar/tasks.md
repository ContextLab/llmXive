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
- [X] T006 [P] Create `code/versioning.py` for SHA-256 hashing and state file updates (`state/projects/PROJ-031-...yaml`)
- [X] T006b [P] [Setup Only] Define the `code/profiler.py` interface and configuration for end-to-end timing and peak RAM measurement. **This task MUST NOT execute the final profiling run; it only sets up the module.**
- [X] T006c [P] [Foundational] Depends on T006b. Implement `code/profiler.py` logic for an **early profiling run** on a limited subset (first rows) of the data to verify FR-010 feasibility (RAM ≤7 GB, Time ≤6 h) before full implementation. **This task MUST run after T006b and before T011.**
- [X] T007 [P] Setup `data/source_manifest.yaml` structure for tracking FTP/HTTP URLs and retrieval timestamps
- [X] T008 Create base `code/__init__.py` and directory structure (`data/raw`, `data/processed`, `results`, `code`, `tests`)

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

- [X] T011 [US1] Implement `code/ingest.py` to download GOES X-ray flare lists from NOAA SWPC FTP (`ftp://ftp.swpc.noaa.gov/pub/lists/`) covering ≥10 years of historical data (See US-1). **Pre-flight validation**: Explicitly check for and reject any imports of `datasets` (HuggingFace) or `huggingface_hub`. If found, raise an `ImportError` with a message citing the Assumptions section.
- [X] T012 [US1] Implement `code/ingest.py` to retrieve CME catalog data (speed, width, direction) from CDAWeb SOHO/LASCO
- [X] T012b [US1] Implement `code/ingest.py` utility to verify the CDAWeb SOHO/LASCO URL is reachable and returns valid data; update `data/source_manifest.yaml` with **exact keys**: if successful, write `cme_status: Verified`, `cme_url: <actual_url>`, `retrieved_at: <timestamp>`; if failed, write `cme_status: Unverified`.
- [X] T013 [US1] Implement `code/ingest.py` to download Dst indices from NOAA SWPC and write to `data/raw/dst_indices.csv`
- [X] T013b [US1] Implement `code/ingest.py` to download Kp indices from NOAA SWPC and write to `data/raw/kp_indices.csv`; validate against schema.
- [X] T014 [US1] Implement `code/align.py` to identify Dst minima (storms) independently, then match preceding solar events within ≤3-day window
- [X] T015 [US1] Implement `code/align.py` logic to flag missing solar predictors as null (do NOT exclude events) and handle "no match found" cases
- [X] T016 [US1] Implement logic to flag recurrent activity periods in the primary dataset with a `is_recurrent` flag.
- [X] T016b [US1] Implement logic to filter non-recurrent storms from the primary dataset to create a derived `data/processed/analysis_subset.csv`. **Depends on US1.**
- [X] T017 [US1] Implement blocking validation gate in `code/validate.py` to check `aligned_events.csv` against `contracts/aligned_event.schema.yaml`.
- [X] T018 [US1] Write `data/processed/aligned_events.csv` and update `data/source_manifest.yaml` with checksums (only if T017 passes)
- [X] T019 [US1] Add logging for data quality metrics (counts of missing CME speeds, flares, etc.)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Compute Spearman correlations, perform linear regression with VIF checks, and execute post-hoc power analysis.

**Independent Test**: Verify correlation coefficients, p-values, R², VIF, and power analysis warnings are computed and output correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for `metrics.json` schema validation in `tests/contract/test_metrics.py`
- [X] T021 [P] [US2] Unit test for Spearman correlation and VIF calculation logic in `tests/unit/test_analysis.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/analysis.py` to compute Spearman rank correlation (log10(flare flux)→Dst and CME speed→Dst) with p-values. **Input: MUST consume `data/processed/analysis_subset.csv`. Depends on US1.**
- [X] T023 [US2] Implement linear regression modeling (flare vs. CME as separate predictors or Ridge) and calculate R². **Input**: Use the model selected in T024. Output the R² value of the selected model to `results/metrics.json` under the key `model_r2`.
- [X] T023b [US2] Implement multiple-comparison correction using Bonferroni (as per Plan.md decision). **Configurable**: Allow switching between Bonferroni and Benjamini-Hochberg via a configuration variable in analysis.py.
- [X] T024 [US2] Implement Variance Inflation Factor (VIF) calculation. **If VIF > 5:** Compute both separate univariate linear models *and* a Ridge regression model (alpha=1.0). Calculate the AIC for both models and select the one with the lowest AIC. Record the selected model type in `results/metrics.json`.
- [X] T025 [US2] Implement post-hoc power analysis using pre-specified effect size r=0.30; log warning if N < 30.
- [X] T026 [US2] If R² from the selected model in T024 is < 0.1, test a piecewise linear regression and report the improvement in fit compared to the selected model. **Depends on T023 & T024.**
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

- [X] T032 [US3] Implement a time-series split: **Enforce the fixed split window defined in Plan.md (Train: 2010-01-01 to 2020-12-31; Test: subsequent period following the training window)**. **Pre-check**: Verify the dataset `data/processed/analysis_subset.csv` contains events spanning this exact window. If the dataset does not cover 2010-2023, raise a `DataWindowError` and log the discrepancy. Do NOT dynamically calculate the split; use the fixed dates from Plan.md as the authoritative strategy per FR-011 and Plan.md override.
- [X] T033 [US3] Implement threshold identification for severe storms (Dst ≤ significant negative threshold) by filtering for severe storm events and analyzing CME speeds.
- [X] T034b [US3] Implement sensitivity analysis sweeping cutoffs over a range of **900 km/s to 1200 km/s** with a step size of **100 km/s** (i.e., 900, 1000, 1100, 1200).
- [X] T035 [US3] Compute and report True Positive Rate (detection rate) variation across the specified cutoffs on the hold-out set.
- [X] T036 [US3] If no significant threshold is found, explicitly report this with justification.
- [X] T037 [US3] Update `results/metrics.json` with threshold candidates, sensitivity results, and citation.
- [X] T038 [US3] Validate final metrics against `contracts/metrics.schema.yaml`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Update `README.md` to frame findings as associational and include data provenance
- [X] T040 Refactor `code/align.py` to reduce cyclomatic complexity to <10 and remove unused imports.
- [X] T041 Performance optimization (ensure execution ≤6h, RAM ≤7GB)
- [X] T042 [P] Additional unit tests in `tests/unit/`
- [X] T043 Run `quickstart.md` validation
- [X] T044 Generate final `results/figures/` (scatter plots, threshold distributions)
- [X] T045 [US1-US3] Execute the final pipeline profiling and report results in `results/metrics.json`.

---

## Dependencies & Execution Order

(unchanged from prior version)

---

## Revision Tasks (Addressing Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data provenance, streaming, and fail-safe mechanisms.

- [X] T046 [US1] Implement robust error handling in `code/ingest.py` with retry mechanism for NOAA FTP and CDAWeb endpoints.
- [X] T047 [US1] Update `code/ingest.py` to implement streaming for large dataset ingestion.
- [X] T048 [US1] Add a pre-flight verification task in `code/ingest.py` to validate the exact URLs in `data/source_manifest.yaml`.
- [X] T049 [US1] Implement logic to count missing CME speed, flare flux, and Dst data and record the counts in `results/metrics.json`.
- [X] T050 [US3] Update `code/analysis.py` to enforce the fixed time-series split (-2020 / 2021-2023).
- [X] T051 [US1] Implement logic to flag recurrent activity periods in the primary dataset with a `is_recurrent` flag.
- [X] T052 [US1] Update `code/ingest.py` to implement strict fail-loud behavior: remove any `try/except` blocks that fall back to `generate_synthetic_*()` or `mock_*()` functions. If a real data fetch fails, the script MUST raise a clear `DataFetchError` exception and exit, ensuring no synthetic data is ever substituted.
- [X] T053 [US1] Add a docstring to `code/ingest.py` function `download_data` specifying the streaming/sampling rule: "all available data", chunking strategy "process rows in batches of a suitable size", and no random sampling (seed=42 not used).
- [X] T054 [US1] Add a validation step in `code/validate.py` to check for imports of HuggingFace libraries, raising an error if found.
- [X] T055 [US3] Implement logic to filter non-recurrent storms from the primary dataset and create derived file (`data/processed/analysis_subset.csv`).
- [X] T056 [US2] Ensure `code/analysis.py` explicitly cites the Zhang et al., n.d.

The specific value to remove/generalize: 'n.d.'

Rewritten passage:
Zhang et al.

The specific value to remove/generalize: 'n.d.'

Rewritten passage:
Zhang et al. paper when performing the post-hoc power analysis with r=0.30.
- [X] T057 [US3] Update `code/analysis.py` to include the NOAA SWPC definition document URL for the "severe storm" threshold justification.
- [X] T058 [US2] Verify that `code/analysis.py` correctly handles the VIF > 5 condition by switching to univariate models or Ridge regression.
- [X] T059 [US3] Implement a sensitivity sweep over specified cutoffs on the hold-out set and report detection rate variation.
- [X] T060 [US1] Add checksum verification step in `code/validate.py` for downloaded raw data files.
- [X] T061 [US2] Programmatically inject "Findings are associational, not causal" into results/metrics.json.