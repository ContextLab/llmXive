# Tasks: Ambient Temperature Influence on Moral Decision Speed

**Input**: Design documents from `/specs/001-ambient-temp-moral-speed/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Data Availability & Validation (CRITICAL BLOCKER)

**Purpose**: Verify data sources, download, and validate resolution standards before any ingestion or modeling can proceed.

**⚠️ CRITICAL**: No other tasks can begin until Phase 0 is complete and the data gap is resolved.

- [X] T001 [P] Verify the canonical URL for the Copernicus Climate Data Store (CDS) API for ERA hourly data (2016-2019) and confirm accessibility (HTTP 200) using the `cdsapi` library configuration. Log the verification result (including API endpoint and status) to `results/logs/data_validation_log.txt`.
- [ ] T002 [P] Write a Python script `code/fetch_era5_sample.py` to fetch a **specific sample subset** for validation: **Jan 1, 2016 to Jan 7, 2016** in **London (51.5N, -0.1W)**. Execute this script to fetch the sample to `data/raw/era5_sample.h5`. Log success/fail to `results/logs/data_validation_log.txt`.
- [X] T002b [P] Write a Python script `code/fetch_era5_full.py` to fetch the **full 2016-2019 ERA5 2m temperature dataset** required for the primary analysis. The script MUST implement chunking by year to avoid single-call timeout. **Parameters**: Variable `2t`, Time range `2016-01-01` to `2019-12-31`, Area `Global` (-90 to 90, -180 to 180).
- [ ] T002c [P] Execute the script from T002b to fetch the full dataset. **Execution Logic**: Run `fetch_era5_full.py` which must fetch by year, merge results, and save to `data/raw/era5_full.h5`. Log success/fail to `results/logs/data_validation_log.txt`.
- [ ] T002d [P] Compute and record the SHA-256 checksum of the downloaded full ERA5 file (`data/raw/era5_full.h5`) in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml` under the key `artifact_hashes.era5_full`. **Crucially, this task MUST also update the `updated_at` timestamp in the same YAML file** to comply with Constitution Principle V.
- [ ] T003 [P] Compute and record the SHA-256 checksum of the downloaded ERA5 sample file (`data/raw/era5_sample.h5`) in `state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml` under the key `artifact_hashes.era5_sample`. **Crucially, this task MUST also update the `updated_at` timestamp in the same YAML file** to comply with Constitution Principle V.
- [X] T004 [P] Programmatically validate that the downloaded ERA5 sample meets the hourly temporal resolution and geographic grid size standards defined in FR-014. Log validation status (Pass/Fail) to `results/logs/data_validation_log.txt`.
- [X] T005 [P] Verify the Moral Machine dataset source against the "Verified Accuracy" principle and log the validation status to `results/logs/data_validation_log.txt` using a standardized format: "Source: <name>, Status: <Pass/Fail>".
- [X] T006 Aggregate all validation results from T001-T005 into a final summary in `results/logs/data_validation_log.txt`. **Note**: This task depends on T001-T005 completing.

**Checkpoint**: Data validation complete. If Pass, proceed to Phase 1. If Fail, project is blocked.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T007 Create project structure per implementation plan, specifically creating directories: `code/`, `data/raw/`, `data/processed/`, `results/figures/`, `results/logs/`, `results/stats/`, `tests/`
- [X] T008 Initialize a Python project with dependencies (pandas, numpy, statsmodels>=0.13, scikit-learn, requests, pyyaml, seaborn, matplotlib, geopandas, cdsapi, huggingface_hub) in requirements.txt
- [ ] T009 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T010 Create base configuration module `code/config.py` defining paths, random seeds, and **configurable** distance thresholds (default 100km, with parameters for 25km and 50km sensitivity analysis).
- [ ] T011 [P] Setup logging infrastructure to write data quality logs and model diagnostics to `results/logs/`
- [X] T012 [P] Implement checksum generation and verification for `data/raw/` and `data/processed/` files in `code/utils.py`
- [X] T013 Create data loading utilities in `code/loaders.py` using `pandas.read_parquet` with `chunksize` parameter for memory mapping. Implement function `load_chunked_parquet(path, chunk_size)` to handle large Parquet ingestion without memory overflow.
- [ ] T014 [P] Setup unit test framework (pytest) with configuration for CPU-only execution and stratified sampling

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Temperature Matching (Priority: P1) 🎯 MVP

**Goal**: Ingest Moral Machine data, merge with ERA5 Reanalysis data, and ensure data quality.

**Independent Test**: Can be fully tested by running the ingestion script on a small, known subset of the Moral Machine data and verifying that every output record contains a valid temperature value within a reasonable geographic range and that no records are dropped due to missing location data.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tests are optional for the MVP. However, if the 'Independent Test' scenario is to be automated, these specific test files must be implemented and verified.
> The 'Independent Test' scenario (running the script on a subset) is MANDATORY for verification of the data pipeline.

- [X] T015 [P] [US1] Unit test for location validation and exclusion logic in `tests/test_ingestion.py`
- [X] T016 [P] [US1] Integration test for ERA5 data fetching and merging with sample Moral Machine data in `tests/test_ingestion.py`. **Specifics**: Use the Jan 2016 London sample from T002 and verify the exact schema of the merged output.

### Implementation for User Story 1

- [X] T017 [P] [US1] Implement `code/ingestion.py` to load Moral Machine dataset and filter records with missing location data or impossible response times (<100ms or >10,000ms) [UNRESOLVED-CLAIM: c_080180e2 — status=not_enough_info], logging excluded records to `results/logs/exclusion_log.csv` in CSV format (FR-002, FR-010)
- [X] T018 [P] [US1] Implement ERA5 Reanalysis data fetching logic in `code/ingestion.py` using the CDS API (`cdsapi`) for 2016-2019 (FR-001). **Note**: This task is for writing the logic only; execution is T018b.
- [ ] T018b [US1] Execute the fetching logic from T018 to fetch the full dataset (using the script from T002c) and merge it with Moral Machine data [UNRESOLVED-CLAIM: c_b1b996b9 — status=not_enough_info]. **Dependencies**: T018, T002d.
- [X] T019 [US1] Implement geospatial matching logic in `code/ingestion.py` to link Moral Machine records to nearest ERA5 grid within 100km threshold [UNRESOLVED-CLAIM: c_25db86ba — status=not_enough_info]. Explicitly flag records >100km by setting `match_quality` to 'low' and logging the exact reason "distance > 100km" to `results/logs/exclusion_log.csv` before exclusion (FR-009). **Note**: This task depends on T018b and T002d (Data Ready).
- [X] T020 [US1] Implement time-based interpolation for missing ERA5 hourly values in `code/ingestion.py`: apply linear interpolation ONLY if the gap is ≤2 hours [UNRESOLVED-CLAIM: c_2c57cba5 — status=not_enough_info]; EXCLUDE the record if the gap >2 hours. Log all excluded records with reasons (e.g., "ERA5 coverage gap", "Low confidence match", "temporal_gap > 2h") to `results/logs/exclusion_log.csv` in CSV format (Edge Case: Missing Temp, FR-002). **Note**: This task depends on T019 and T002d.
- [ ] T022 [US1] Implement output generation to save merged dataset to `data/processed/merged_dataset.parquet` and log success rate (SC-001)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Mixed-Effects Regression Modeling (Priority: P2)

**Goal**: Fit statistical models to quantify the temperature effect on response time, controlling for confounds.

**Independent Test**: Can be fully tested by running the modeling script on the pre-processed dataset and verifying that the model converges, produces a coefficient for `temperature_celsius`, and reports a p-value for the fixed effect.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for log-transformation and outlier handling in `tests/test_modeling.py`
- [X] T024 [P] [US2] Integration test for model convergence and coefficient extraction in `tests/test_modeling.py`

### Implementation for User Story 2

- [X] T025 [P] [US2] Implement `code/modeling.py` to perform log-transformation of response times and handle non-convergence by switching to GLMM (FR-003)
- [X] T028 [US2] Implement **Derivation of Age/Gender Covariates**. **Logic**: First, check if individual-level `age` and `gender` columns exist. If present, include them. **If absent, fetch aggregate country-level data from the World Bank API [UNRESOLVED-CLAIM: c_c682e737 — status=not_enough_info]** (Endpoint: `https://api.worldbank.org/v2/country/{id}/indicator/SP.DYN.LE00.IN` for life expectancy as age proxy; `SP.POP.TOTL` for population). **Years**: 2016-2019. **Merge** these country-level covariates to the **participant-aggregated** rows (per Plan's Two-Stage Aggregation). If derivation fails, log the specific reduction in statistical power and document the absence of these covariates in `results/logs/demographic_gap_log.txt`. Conditionally include these in the model if data is available (FR-004). **Note**: This task must run BEFORE T026.
- [ ] T026 [US2] Implement **Primary Model: OLS with Clustered Robust Standard Errors** in `code/modeling.py` with fixed effects: temperature, dilemma complexity, time-of-day, dilemma choice. **Note**: This OLS approach is a fallback per Plan Scalable Strategy due to 7GB RAM limit, deviating from Spec FR-003 LMM requirement. **Secondary Validation**: If memory permits on a small random subset (≤ 10k participants), fit a Linear Mixed-Effects Model (LMM) for comparison to validate against FR-003. Perform a Likelihood Ratio Test (LRT) or AIC/BIC comparison between OLS and LMM (alpha=0.05) [UNRESOLVED-CLAIM: c_93e3bdfe — status=not_enough_info]. Save the combined comparison result to `results/robustness/nonlinearity_comparison.json` (FR-003, FR-004, FR-011, FR-013). **Dependencies**: T025, T028, T022.
- [ ] T029 [US2] Implement likelihood-ratio test in `code/modeling.py` comparing full model vs. null model (without temperature) and record p-value (FR-005, SC-002)
- [ ] T030 [US2] Implement diagnostic plot generation (QQ-plot, residual vs. fitted) AND the Anderson-Darling statistical test on a random sample to verify residual normality. Record the Anderson-Darling p-value in `results/stats/model_results.json` (FR-007, SC-005).
- [ ] T032 [US2] Export model coefficients, standard errors, p-values, and cluster-robust variances to `results/stats/model_results.json` in a format compliant with `model_output.schema.yaml` (FR-008)
- [ ] T041 [US2] Extract the **cluster-robust variance** for the cultural region from the primary model output (output of T032) to quantify the baseline "individual difference" noise floor observed in the data. **Method**: Use `statsmodels>=0.13` and access `results.get_robustcov_results('cluster').cov_params().diagonal` (or fallback to `results.bse**2` if version mismatch). Record this value in `results/stats/model_results.json` under the field `cluster_robust_variance`. **Note**: This task depends on T032 completing. (Note: This aligns with the Plan's OLS strategy which produces cluster variance, not random intercept variance).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Validate findings through alternative metrics, sensitivity checks, and confound analysis.

**Independent Test**: Can be fully tested by running the robustness script and verifying that it produces a summary table comparing the primary model results with alternative specifications.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test for sensitivity analysis threshold sweeping in `tests/test_robustness.py`
- [ ] T034 [P] [US3] Integration test for robustness summary table generation in `tests/test_robustness.py`

### Implementation for User Story 3

- [ ] T035 [P] [US3] Implement `code/robustness.py` to calculate alternative temperature metrics (e.g., 3-hour moving average) and re-run modeling (FR-006)
- [ ] T035b [P] [US3] Implement **Distance Sensitivity Analysis** in `code/robustness.py`. Re-run the primary model excluding records >25km and >50km (using config from T010) and report the variation in the temperature coefficient. This explicitly covers the distance threshold sensitivity required by the Plan but missing from T035.
- [ ] T036 [US3] Implement sensitivity analysis in `code/robustness.py` sweeping temperature outlier thresholds (e.g., varying standard deviation multipliers) and reporting coefficient variation (FR-006, SC-003)
- [ ] T037 [US3] Implement indoor/outdoor confound analysis in `code/robustness.py` by FIRST attempting to stratify data or apply proxy adjustment using urban/rural classification. **Data Source**: Fetch urban/rural data from `datasets.load_dataset('jrc/ghsl', '2023_v1')` and use the `GHSL_POP_GLO_2020V1.0.zip` file. If metadata is unavailable, THEN report the limitation and quantify noise impact (FR-012).
- [ ] T038 [US3] Generate comparison table in `code/robustness.py` showing temperature coefficient and p-value for primary vs. alternative models (US-3)
- [ ] T039 [US3] Save all robustness figures (scatter plots, conditional effect plots) to `results/figures/` (FR-008)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Limitations & Review Resolution (Priority: P3 - Revision)

**Goal**: Address the absence of baseline data and arousal proxies by documenting them as limitations, as required by the spec's assumptions, and quantifying the noise floor via observed cluster-robust variances.

**Independent Test**: Verify that the results log explicitly states the inability to control for baseline speed and arousal due to data absence, and includes the quantified variance of individual differences from the model.

### Implementation for Limitations

- [ ] T040 [P3] Generate a final limitations report in `results/logs/limitations.md` explicitly stating: (1) No individual baseline reaction time data exists in the dataset; (2) Arousal/micro-climate effects are unmeasured noise; (3) These factors are not controlled for, only reported (FR-012, Spec Assumptions). **Note**: Spec does not mandate a specific "daniel-kahneman-simulated" review resolution; this task documents the limitations as allowed by FR-012.
- [ ] T042 [P3] Update `results/logs/limitations.md` to include the findings from T041, emphasizing that the observed temperature effect is an upper bound on the true causal effect and may be inflated by unmeasured individual differences.

**Checkpoint**: Limitations documented; analysis complete within data constraints.

---

## Phase 7: Research-Stage Review Resolution (Priority: P3 - Revision)

**Goal**: Address the specific concern from the "daniel-kahneman-simulated" review regarding the confounding of temperature effects with individual baseline reaction speed and physiological arousal, by explicitly documenting the data gap and quantifying the theoretical impact via observed variance.

**Independent Test**: Verify that the `results/logs/limitations.md` contains a specific entry for the Kahneman review, acknowledging the lack of baseline/arousal data, and that the `results/logs/limitations.md` includes the quantified noise floor.

### Implementation for Review Resolution

- [ ] T043 [P3] Update `results/logs/limitations.md` to add a specific section for the "daniel-kahneman-simulated" review (dated -06-21), explicitly stating that the dataset lacks pre-test baseline reaction times and physiological arousal proxies (skin conductance), making the "temperature-adjusted RT" calculation impossible. This documents the known constraint per the Spec's Assumptions.
- [ ] T044 [P3] Update `docs/research.md` to include a "Future Work" section proposing a follow-up study design that includes a neutral reaction-time task and physiological sensors to directly measure the baseline and arousal confounds identified in the review.

**Checkpoint**: Review concerns acknowledged, theoretical impact quantified, and future work proposed.

---

## Phase 8: Review-Driven Confound Quantification (Priority: P3 - Revision)

**Goal**: Directly address the Kahneman review's specific suggestion to quantify the "noise" of individual differences by implementing a stratified analysis that isolates the temperature effect within homogeneous response-time groups, and to report the theoretical impact of the missing baseline.

**Independent Test**: Verify that `results/stats/model_results.json` includes a new metric `kahneman_review_noise_floor` derived from the stratified analysis, and that `results/logs/limitations.md` contains a dedicated section "Review: daniel-kahneman-simulated" with the specific quantification of the baseline confound.

### Implementation for Review Resolution

- [ ] T045 [P3] Implement a stratified analysis in `code/robustness.py` that bins participants into quartiles based on their **country-level median response time** (serving as an external proxy for baseline speed, avoiding circularity). **Fallback**: If a country has <30 responses, exclude that country from the analysis [UNRESOLVED-CLAIM: c_1e8a512e — status=not_enough_info]. **Re-run the primary temperature model** (T026 logic) within each quartile to observe if the temperature coefficient varies by baseline speed. Save the coefficients per quartile to `results/robustness/baseline_stratification.json`. **CRITICAL DISCLAIMER**: This task DOES NOT resolve the individual baseline confound (per Spec Assumptions). The goal is strictly to **quantify the upper bound of noise** introduced by unmeasured individual differences. The output must be framed as a "Noise Floor Estimate" and explicitly state that without true baseline data, the main effect is an upper bound. This analysis quantifies the variance in coefficients as a proxy for the unmeasured confound's impact (FR-012). **Dependencies**: T022, T026.
- [ ] T046 [P3] Calculate the **variance of the temperature coefficients** across the baseline quartiles (from T045). This variance serves as a proxy for the unmeasured "individual difference" noise floor identified by the review. Record this value as `kahneman_review_noise_floor` in `results/stats/model_results.json`.
- [ ] T047 [P3] Update `results/logs/limitations.md` to include a new subsection "Quantification of Reviewer Concern (Kahneman)" that: (1) Reports the `kahneman_review_noise_floor` value from T046; (2) Explains that this value represents the estimated variance in the temperature effect due to unmeasured baseline speed differences; (3) States that without a true baseline, the main effect is an upper bound.

**Checkpoint**: Reviewer's specific concern about baseline confounding is now quantified and documented, allowing the project to proceed with a clear understanding of the noise floor.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Documentation updates in `docs/` and `quickstart.md` including instructions for running with sampled data
- [ ] T049 Code cleanup and refactoring to ensure modularity
- [ ] T050 Performance optimization: Ensure dataset sampling logic in `code/ingestion.py` prevents memory overflow on runners with constrained RAM resources
- [ ] T051 [P] Additional unit tests for edge cases (e.g., all records excluded due to distance)
- [ ] T052 Run quickstart.md validation to ensure full pipeline completes within 4 hours

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data Validation)**: No dependencies - must run FIRST. BLOCKS all other phases.
- **Phase 1 (Setup)**: Depends on Phase 0 completion - can start immediately after validation passes.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - BLOCKS all user stories.
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Limitations (Phase 6)**: Depends on US3 completion (to summarize findings)
- **Review Resolution (Phase 7)**: Depends on US3 and Limitations (Phase 6) completion to fully contextualize the data gaps.
- **Review-Driven Confound Quantification (Phase 8)**: Depends on US2 (model output T026) and US3 (robustness framework) to perform the stratified analysis.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires merged data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires model output from US2
- **Limitations (Phase 6)**: Requires US3 implementation to summarize findings
- **Review Resolution (Phase 7)**: Requires US3 and Limitations (Phase 6) to fully address the review.
- **Review-Driven Confound Quantification (Phase 8)**: Requires US2 (for baseline proxy T026) and US3 (for robustness framework).
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion (US1) before Modeling (US2)
- Modeling (US2) before Robustness (US3)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, US3 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase 6, 7, and 8 can be executed in parallel once their dependencies (US2/US3) are met.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for location validation and exclusion logic in tests/test_ingestion.py"
Task: "Integration test for ERA5 data fetching and merging with sample Moral Machine data in tests/test_ingestion.py"

# Launch all implementation tasks for User Story 1 together:
Task: "Implement code/ingestion.py to load Moral Machine dataset..."
Task: "Implement ERA5 Reanalysis data fetching logic in code/ingestion.py..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Data Validation (CRITICAL - must pass)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 → Data validated
2. Complete Setup + Foundational → Foundation ready
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Add Limitations (Phase 6) → Test independently → Deploy/Demo
7. Add Review Resolution (Phase 7) → Test independently → Deploy/Demo
8. Add Review-Driven Confound Quantification (Phase 8) → Test independently → Deploy/Demo
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 (Data Validation) together
2. Once Phase 0 passes:
 - Team completes Setup + Foundational together
3. Once Foundational is done:
 - Developer A: User Story 1 (Ingestion)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Robustness)
4. Stories complete and integrate independently
5. Developer D (or A/B/C rotation): Limitations (Phase 6), Review Resolution (Phase 7), and Review-Driven Confound Quantification (Phase 8) to document constraints, quantify noise, and address the specific Kahneman review concerns.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must be designed to run on a limited number of CPU cores and moderate memory resources. Use stratified sampling if dataset size exceeds memory.
- **NO GPU**: No -bit/4-bit quantization, no CUDA dependencies. Use standard precision models.
- **Data Constraints**: Do NOT attempt to simulate missing data (baseline, arousal) as real data. Document limitations and perform theoretical reporting instead.
- **Critical Blocker**: Phase 0 MUST pass before any ingestion tasks (T017+) are attempted.
- **Review Resolution**: Phases 6, 7, and 8 are mandatory to address the "daniel-kahneman-simulated" review regarding baseline reaction time confounds and to quantify the theoretical impact of the missing data.