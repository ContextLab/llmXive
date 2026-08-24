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
- [X] T003 [P] Configure linting (flake8/pylint) and formatting (black/isort) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `contracts/aligned_event.schema.yaml` defining SolarFlareEvent, CMEEvent, GeomagneticStorm, and AlignedEvent entities
- [X] T005 [P] Create `contracts/metrics.schema.yaml` defining correlation coefficients, p-values, R², VIF, and threshold metrics
- [X] T006 [P] Implement `code/versioning.py` for SHA-256 hashing and state file updates (`state/projects/PROJ-031-...yaml`)
- [X] T006b [P] [Setup Only] Define the `code/profiler.py` interface and configuration for end-to-end timing and peak RAM measurement. **This task MUST NOT execute the final profiling run; it only sets up the module. The actual execution to measure total pipeline time MUST occur in Phase N (T045) after all metric writers complete.**
- [X] T006c [P] [Foundational] Implement `code/profiler.py` logic for an **early profiling run** on a limited subset (first 1000 rows) of the data to verify FR-010 feasibility (RAM ≤7GB, Time ≤6h) before full implementation. **This task MUST run after T006b and before T011. If this check fails, the pipeline halts and alerts the user.**
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
- [X] T010 [P] [US1] Integration test for full download-and-align flow in `tests/integration/test_ingest_align.py` (Function: `test_full_ingest_align_flow`, Assert: `os.path.exists(aligned_csv) and len(df) > 0` using a mocked FTP response with 100 rows of synthetic but schema-valid data)

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/ingest.py` to download GOES X-ray flare lists from `ftp://ftp.swpc.noaa.gov/pub/lists/` (≥10 years) [UNRESOLVED-CLAIM: c_bc4f91db — status=not_enough_info]
- [X] T012 [US1] Implement `code/ingest.py` to retrieve CME catalog data (speed, width, direction) from CDAWeb SOHO/LASCO
- [X] T012b [US1] Implement `code/ingest.py` utility to verify the CDAWeb SOHO/LASCO URL is reachable and returns valid data; update `data/source_manifest.yaml` with **exact keys**: if successful, write `cme_status: Verified`, `cme_url: <actual_url>`, `retrieved_at: <timestamp>`; if failed, write `cme_status: Unverified`. **This task MUST record the successful URL and timestamp upon verification success to satisfy Constitution Principle VI.**
- [X] T013 [US1] Implement `code/ingest.py` to download Dst indices from NOAA SWPC and write to `data/raw/dst_indices.csv`
- [X] T013b [US1] Implement `code/ingest.py` to download Kp indices from NOAA SWPC and write to `data/raw/kp_indices.csv`; validate against schema.
- [X] T014 [US1] Implement `code/align.py` to identify Dst minima (storms) independently, then match preceding solar events within ≤3-day window
- [X] T015 [US1] Implement `code/align.py` logic to flag missing solar predictors as null (do NOT exclude events) and handle "no match found" cases
- [X] T016 [US1] Implement logic to flag recurrent activity periods (distinct minima separated by <24 hours of recovery) in the primary `data/processed/aligned_events.csv` with a `is_recurrent` flag. **This task MUST NOT exclude events from the primary dataset; exclusion for analysis MUST happen in a derived subset (T016b).** The `is_recurrent` flag MUST be used to exclude these events from the correlation analysis (US2) via T016b.
- [X] T016b [US1] Implement logic to filter non-recurrent storms from the primary dataset to create a derived `data/processed/analysis_subset.csv` for use in correlation analysis (US2). **Filter logic: `is_recurrent == False`.** **Verification: Assert file exists and row count < primary dataset row count.** **This task explicitly creates the filtered subset to satisfy the 'no exclusion' rule for the primary dataset while enabling the analysis requirement.**
- [X] T018 [US1] Implement blocking validation gate in `code/validate.py` to check `aligned_events.csv` against `contracts/aligned_event.schema.yaml`. **This validation MUST block the writing of `aligned_events.csv` and the update of `data/source_manifest.yaml` if validation fails.**
- [X] T017 [US1] Write `data/processed/aligned_events.csv` and update `data/source_manifest.yaml` with checksums (only if T018 passes)
- [X] T019 [US1] Add logging for data quality metrics (counts of missing CME speeds, flares, etc.) and explicitly log exclusion counts as data-quality metrics.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Compute Spearman correlations, perform linear regression with VIF checks, and execute post-hoc power analysis.

**Independent Test**: Verify correlation coefficients, p-values, R², VIF, and power analysis warnings are computed and output correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for `metrics.json` schema validation in `tests/contract/test_metrics.py` (Function: `test_metrics_schema_valid`, Assert: `schema.validate(metrics)` using a mock fixture with valid schema-compliant JSON)
- [X] T021 [P] [US2] Unit test for Spearman correlation and VIF calculation logic in `tests/unit/test_analysis.py` (Function: `test_spearman_correlation`, Assert: `abs(result - expected) < tolerance` using a small, deterministic mock dataset)

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/analysis.py` to compute Spearman rank correlation (log10(flare flux)→Dst and CME speed→Dst) with p-values. **Input: MUST consume `data/processed/analysis_subset.csv` (from T016b), NOT the primary dataset.** **Depends on T016b.**
- [X] T023 [US2] Implement linear regression modeling (flare vs. CME as separate predictors) and calculate R². [UNRESOLVED-CLAIM: c_2be0ce4a — status=not_enough_info]
- [X] T024 [US2] Implement Variance Inflation Factor (VIF) calculation. **Selection Logic**: If VIF > 5, switch to separate univariate models. **Specific Logic**: The Plan mandates selecting the **univariate model with the higher absolute correlation coefficient** if VIF > 5. **Output**: Record the chosen fallback strategy (e.g., "univariate_flare") and the **selected univariate R²** to `results/metrics.json` under the key `selected_model_r2`. The joint R² is NOT reported if the joint model is discarded.
- [X] T023b [US2] Implement multiple-comparison correction using the **Bonferroni** method (as per Plan). **Output**: Write corrected p-values to `results/metrics.json` under `corrected_p_values` and explicitly record the method used under `correction_method` (value: "bonferroni"). **Documentation**: Explicitly document in the code comments and output rationale that "Bonferroni selected per Plan.md, overriding FR-005 flexibility" and write the **rationale** (e.g., "family-wise error rate control for small test family") to `results/metrics.json` under `correction_rationale`.
- [X] T025 [US2] Implement post-hoc power analysis using pre-specified effect size r=0.30 (Zhang et al., 2020); log warning if N < 30. **Output**: Write the calculated `min_detectable_effect_size` and a boolean `power_warning_flag` to `results/metrics.json`.
- [X] T026 [US2] {{claim:c_7838aa47}} **Output**: Report the improvement in `results/metrics.json` under the key `piecewise_r2_improvement`.
- [X] T027 [US2] Ensure all findings are framed as ASSOCIATIONAL (not causal) in output documentation.
- [X] T028 [US2] Validate output against `contracts/metrics.schema.yaml` and write `results/metrics.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Identification and Sensitivity Analysis (Priority: P3)

**Goal**: Identify predictive thresholds using a time-series hold-out set (recent years) and perform sensitivity analysis.

**Independent Test**: Verify threshold identification, hold-out validation, and sensitivity sweep (a range of velocities) are executed correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Contract test for threshold sensitivity results in `tests/contract/test_thresholds.py` (Function: `test_threshold_sensitivity_schema`, Assert: `schema.validate(thresholds)` using a mock fixture)
- [X] T031 [P] [US3] Integration test for time-series split validation in `tests/integration/test_threshold_validation.py` (Function: `test_timeseries_split_validation`, Assert: `train_years == "2010-2020" and test_years == "2021-2023"` using a mock dataset with timestamps)

### Implementation for User Story 3

- [X] T032 [US3] Implement time-series split logic: **Dynamically compute** the hold-out set as the **last two years** of the available data range (e.g., if max date is 2024, test is 2023-2024; if max date is 2023, test is 2022-2023). **Train on events prior to the last two years.** **Input**: This task MUST consume `data/processed/analysis_subset.csv` from T016b. **Depends on T016b.** This dynamic split is mandatory per FR-011 and Spec US-3.
- [X] T033 [US3] Implement threshold identification for severe storms (Dst ≤ significant negative threshold)
- [X] T034a [US3] Implement logic to **identify candidate predictive thresholds** by filtering for severe storm events (Dst ≤ significant negative threshold) and analyzing the distribution of CME speeds for these events. **This task MUST implement the identification logic, not just the citation.**
- [X] T034b [US3] Implement sensitivity analysis sweeping cutoffs over a specific set of representative velocity thresholds (a range of values around a characteristic velocity scale). The research question remains: How do velocity threshold variations impact the stability of the model? The method is: Systematic sensitivity analysis across representative parameter ranges. References: [Author, Year] (DOI: 10.xxxx/xxxx). and report detection rates (True Positive Rate) on the hold-out set.
- [X] T034c [US3] Define the constant URL for the NOAA SWPC "Geomagnetic Storms" definition in `code/constants.py` and inject this URL into `results/metrics.json` under `threshold_citation_url` and into `README.md` with the exact string format: "Threshold defined per NOAA SWPC: <URL>". **This task separates the constant definition from the injection logic.**
- [X] T035 [US3] Compute and report True Positive Rate (detection rate) variation across cutoffs on the hold-out set
- [X] T036 [US3] If no significant threshold is found, explicitly report this with justification
- [X] T037 [US3] Update `results/metrics.json` with threshold candidates, sensitivity results, and citation (including output from T034c)
- [X] T038 [US3] Validate final metrics against `contracts/metrics.schema.yaml`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Update `README.md` to frame findings as associational and include data provenance
- [X] T040 Refactor `code/align.py` to reduce cyclomatic complexity to <10 and remove unused imports. **Update task status to [X] and ensure complexity management is documented per Plan 'Complexity Tracking' section.**
- [X] T041 Performance optimization (ensure execution ≤6h, RAM ≤7GB)
- [X] T042 [P] Additional unit tests in `tests/unit/`
- [X] T043 Run `quickstart.md` validation
- [X] T044 Generate final `results/figures/` (scatter plots, threshold distributions)
- [X] T045 [US1-US3] Execute the final pipeline profiling: Run the full pipeline (`main.py`) and measure total execution time and peak RAM usage. Write these metrics to `results/metrics.json` under the key `performance`. **This task MUST run sequentially after T037 and T028. If FR-010 constraints are violated, this task MUST fail and halt the report generation.**

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (specifically `analysis_subset.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 analysis context

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Contracts before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for aligned_events.csv schema validation in tests/contract/test_aligned_event.py"
Task: "Integration test for full download-and-align flow in tests/integration/test_ingest_align.py"

# Launch all models for User Story 1 together:
Task: "Create contracts/aligned_event.schema.yaml"
Task: "Create contracts/metrics.schema.yaml"
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **T006b Note**: This task is for setup/definition only. The actual execution to measure total pipeline time is moved to T045 in Phase N.
- **T006c Note**: This task performs an early profiling run on a limited subset to verify FR-010 feasibility before full implementation.
- **T045 Note**: This task MUST run sequentially after T037 and T028 to avoid race conditions on `results/metrics.json` and to ensure accurate measurement.
- **T016/T016b Note**: T016 flags recurrent events in the primary dataset; T016b creates the filtered analysis subset. This ensures the primary dataset retains all events as required by US-1.
- **T012b Note**: This task ensures the plan's Constitution Check strategy for CME source verification is implemented, recording success or failure.
- **T032 Note**: This task now dynamically computes the hold-out set to align with the Spec's FR-011 requirement for "last two years".

---

## Revision Tasks (Addressing Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data provenance, streaming, and fail-safe mechanisms.

- [X] T046 [US1] Implement robust error handling in `code/ingest.py` for NOAA FTP and CDAWeb endpoints: **Implement a retry mechanism with exponential backoff (e.g., 3 retries)** for transient network errors. If all retries fail, raise a clear `ConnectionError` or `TimeoutError`. Explicitly **remove** any `try/except` blocks that fall back to `generate_synthetic_*()` or `mock_*()` data. **Rationale**: Per the "Loader must fail loudly" rule, silent synthetic fallbacks are fabrication; a failed real fetch must halt execution to allow the execution stage to discover and retry verified sources, but transient errors should be retried for robustness.
- [X] T047 [US1] Update `code/ingest.py` to implement **streaming** for large dataset ingestion: Use `requests` with `stream=True` and iterate line-by-line (or chunk-by-chunk) to parse raw flare/CME/Dst files, accumulating statistics online without loading the entire multi-year history into RAM at once. [UNRESOLVED-CLAIM: c_e481c86f — status=not_enough_info] **Rationale**: To satisfy FR-010 (≤7 GB RAM) while processing ≥10 years of real data, the pipeline must stream rather than bulk-load; this prevents OOM errors on the CPU-only runner while ensuring the full real dataset contributes to the result.
- [X] T048 [US1] Add a pre-flight verification task in `code/ingest.py` to validate the exact URLs in `data/source_manifest.yaml` against the live NOAA/CDAWeb endpoints before any download begins; if a URL returns 404 or invalid content, log a `FATAL` error and abort the pipeline. **Output**: Update `data/source_manifest.yaml` with a `pre_flight_status` key (e.g., "passed" or "failed"). **Rationale**: To satisfy the "Verified Accuracy" and "Solar Event Data Provenance" constitution checks, the system must confirm source validity before proceeding, preventing the ingestion of broken or placeholder links.
- [ ] T049 [US2] Add a data-quality metric task in `code/analysis.py` to explicitly count and report the number of events with missing CME speed or flare flux data in `results/metrics.json` under the key `missing_data_counts`. **Structure**: The value MUST be a dictionary: `{cme_speed: int, flare_flux: int, dst: int}`. **Rationale**: To satisfy US-1's requirement to "include events with missing data flags" and US-2's transparency requirements, the analysis must explicitly quantify how many events were excluded from specific paired calculations due to missing values, ensuring the sample size is accurately reported.
- [X] T050 [US3] Update `code/analysis.py` to enforce the **strict time-series split** (Train: dynamic prior to last two years, Test: last two years) by adding a validation check that raises an error if any test-set event falls outside the computed window. **Rationale**: To prevent data leakage and ensure the predictive threshold is validated on truly unseen data (FR-011), the code must strictly enforce the date boundaries and reject any misaligned splits.