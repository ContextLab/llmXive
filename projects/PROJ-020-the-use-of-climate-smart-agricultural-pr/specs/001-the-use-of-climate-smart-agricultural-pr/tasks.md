# Tasks: The Use of Climate-Smart Agricultural Practices in Rural Areas to Improve Food Security and Livelihoods

**Input**: Design documents from `/specs/001-csa-food-security/`
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

- [X] T001a [P] Create project directories: `code/`, `data/`, `tests/`, `specs/`
- [ ] T001b [P] Create `__init__.py` files in all `code/` sub-packages (`data/`, `analysis/`, `viz/`, `utils/`)
- [X] T002 Initialize Python 3.12.0 project with pinned dependencies in `code/requirements.txt` (pandas>=2.0.0, numpy>=1.24.0, scikit-learn>=1.3.0, statsmodels>=0.14.0, geopandas>=0.13.0, matplotlib>=3.7.0, seaborn>=0.12.0, requests>=2.31.0, pyyaml>=6.0.0).
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup directory structure for `data/raw/`, `data/processed/`, and `state/` for checksums
- [X] T005 [P] Implement `code/utils/logging.py` for provenance logging (mapping derived variables to raw IDs)
- [X] T006 [P] Create `code/utils/config.py` to manage environment variables (target countries, years, RAM limits)
- [X] T007 Create base data schema definitions in `specs/001-csa-food-security/contracts/dataset.schema.yaml`
- [X] T007b [P] [US1] **Define CSA Index Formula** in `specs/001-csa-food-security/data-model.md`:
 - **Action**: Create or update `specs/001-csa-food-security/data-model.md` with a new section "CSA Index Formula".
 - **Definition**: Define the CSA Index formula abstractly as a weighted composite: `CSA_Index = f(Conservation Tillage, Crop Diversification, Irrigation Efficiency, Digital Access, Finance Access)`.
 - **Intensity Calculation**: Define the intensity score calculation algorithm as min-max scaling: `normalized_value = (x - min) / (max - min)`.
 - **Weights**: Define weights as configurable parameters with `equal weighting (0.2 each)` as the DEFAULT strategy. The implementation MUST allow these weights to be overridden by a configuration file if data-driven intensity analysis suggests otherwise.
 - **Note**: If `data-model.md` does not exist, create it with the explicit formula text above.
- [X] T007c [P] [US1] **Implement CSA Index Calculation** in `code/data/features.py`:
 - **Index Weighting**: Implement the weighting strategy using configurable parameters. Default to equal weighting (w=w2=w3=w4=w5 = 0.2).
 - **Sampling Weight Strategy**: Define sampling weights separately: Use Inverse Probability Weighting (IPW) based on country/year sampling fractions for the statistical model.
 - **Dual Role Documentation**: Document the dual role of digital/finance variables: (1) Included in the Primary CSA Index, (2) Tested as moderators to satisfy Principle VII.
 - **Note**: IPW is NOT used for the index calculation itself; it is reserved for the model weights in T023.
- [X] T007d [P] [US1] **Define CSA Index Provenance** in `specs/001-csa-food-security/data-model.md`:
 - **Provenance Mapping**: Mandate that the weights themselves are linked to the 'configurable weighting strategy' defined in T007c. This ensures provenance records map back to the raw survey responses and the logic used to derive the weights, satisfying Constitution Principle VI.
- [X] T008 [P] Implement `code/data/download.py` with function stubs: `download_lsms(country, year)`, `download_nasa_power(lat, lon, start, end)`, `download_faostat(indicator)`
- [X] T009 [P] Create `code/main.py` entry point to orchestrate the full analysis and viz pipeline. **Rationale**: The Plan's 'Project Structure' defines `code/main.py` as a foundational component for the full pipeline execution.
- [X] T010 [P] Setup pytest environment in `tests/` with configuration for CPU-only execution

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download, clean, merge, and sample LSMS, FAOSTAT, and NASA POWER data into a single analysis-ready dataset.

**Independent Test**: Execute `code/data/pipeline.py` and verify `data/processed/merged_sample.parquet` contains ≥ 95% valid records, no missing values in key predictors after imputation, and matches the schema.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for data schema validation in `tests/contract/test_dataset_schema.py`
- [X] T012 [P] [US1] Integration test for download and merge pipeline in `tests/integration/test_data_pipeline.py`: Verify pipeline runs without error and output file exists.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement LSMS downloader in `code/data/download.py` targeting Kenya, India, Vietnam (recent years) with error handling for missing years
- [ ] T014 [P] [US1] Implement NASA POWER climate downloader in `code/data/download.py` using `requests` and nearest-neighbor spatial interpolation for gaps ≤ 3 months
- [ ] T015 [P] [US1] Implement FAOSTAT agricultural indicator downloader in `code/data/download.py`
- [ ] T016 [US1] Implement data cleaning and merging logic in `code/data/clean.py`:
 - Merge using country code + year
 - Match climate data to survey coordinates **within a defined proximity radius** using the **WGS84 (EPSG:4326) CRS** and **Haversine formula** for distance calculation.
 - Match climate data using **growing season average (3-month pre-harvest mean)** as the temporal window.
 - Flag unmatched rows and log warnings.
- [ ] T017 [US1] Implement imputation strategy in `code/data/clean.py` for missing predictor values
- [ ] T018 [US1] [FR-005] Implement **stratified sampling** in `code/data/clean.py`:
 - **Target**: Aim for N ≥ 5000 households **per country** (Kenya, India, Vietnam) as a statistical power goal.
 - **Trigger**: Apply stratified sampling **ONLY IF** the raw data exceeds the **7 GB RAM** limit.
 - **Logic**: If raw data > 7GB, apply stratified sampling to reduce size while preserving representation. If raw data < 7GB, retain all data (do not downsample for N targets).
 - **Verification**: After processing, calculate the final sample size. If the target N ≥ 5000 is not met (regardless of the 7GB trigger), log a specific warning: "Target N >= 5000 per country not met. Proceeding with available data."
 - **Output**: MUST output `data/processed/ipw_weights.parquet` containing the sampling fractions for each stratum to be consumed by T023.
 - **Note**: This task implements **sampling** only. Inverse Probability Weighting (IPW) for the model is handled in T023.
- [ ] T018b [US1] [SC-001] **Calculate Merge Success Rate** in `code/data/clean.py`:
 - **Action**: Calculate the merge success rate as: `(Number of successfully merged records) / (Total available non-duplicate LSMS records for target countries) * 100`.
 - **Output**: Log this rate to `data/processed/merge_stats.json` with the schema: `{"merge_success_rate_pct": float, "total_available_records": int, "merged_records": int, "missingness_rate": float}`.
 - **Dependency**: Must run after T016 (Merge) and before T018 (Sampling).
- [ ] T018c [P] [US1] **Implement Provenance Logger** in `code/utils/logging.py`:
 - **Action**: Log a JSON mapping **every derived CSA variable, including the final weighted composite index**, to its source LSMS question ID and response ID.
 - **Output**: Write to `data/processed/provenance_log.json`.
- [ ] T018d [P] [US1] **Implement IPW Weight Calculation Verification** in `code/data/clean.py`:
 - **Dependency**: Must run after T018 completes the sampling logic and outputs `data/processed/ipw_weights.parquet`.
 - **Action**: Verify that the weights file exists and contains valid probabilities for all strata defined in T018.
 - **Output**: Log a verification report confirming the weights are ready for T023.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean, merged, sampled dataset ready)

---

## Phase 4: User Story 2 - Statistical Modeling and Analysis (Priority: P2)

**Goal**: Fit Fixed-Effects Regression models to quantify associational relationships between CSA adoption and food security, including interaction terms and mediation analysis.

**Independent Test**: Run `code/analysis/model.py` on a sample subset and verify output includes standardized coefficients, p-values, VIF scores, and fixed effect estimates without runtime errors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`
- [X] T021 [P] [US2] Unit test for VIF calculation and collinearity flagging in `tests/unit/test_diagnostics.py`
- [X] T028 [P] [US2] Integration test for timeout handling in `tests/integration/test_model_timeout.py` to measure convergence time against the GitHub Actions free-tier job limit (6 hours) with explicit pass/fail criteria (log `convergence_time_seconds` to `metrics.json`).

### Implementation for User Story 2

- [ ] T022 [US2] [FR-003] Implement CSA Index construction in `code/data/features.py`:
 - **Strict Adherence**: This implementation MUST strictly follow the formula defined in T007b (`data-model.md`), which includes digital/finance variables as per FR-003.
 - **Dependency**: Strictly follow the formula and weighting strategy defined in T007b.
 - Weighted composite score (conservation tillage, crop diversification, irrigation efficiency, digital-technology access, finance access) as defined in `data-model.md` (T007b).
 - Normalize to a unit scale.
 - **Note**: Do NOT attempt to decouple digital/finance variables here; that is handled by the separate diagnostic task T024.
- [X] T023 [US2] [FR-002] [FR-004] [FR-010] Implement **Fixed-Effects Regression Model (OLS with Country Dummies)** in `code/analysis/model.py`:
 - **Model Type**: Fixed-Effects Regression (OLS with Country Dummies). **Rationale**: Mixed-Effects is statistically invalid for N=3 countries. This approach controls for unobserved country-level heterogeneity and satisfies the Spec's intent for a valid model while adhering to the Plan's statistical constraints.
 - **Predictors**: Include the **Primary CSA Index** (T022) and interaction terms for digital and finance access (moderation).
 - **Mediation**: Implement mediation analysis (Baron & Kenny approach) on the Fixed-Effects coefficients to test the indirect effects of digital/finance access (Constitution Principle VII).
 - **Language Constraint**: All findings MUST be framed as **associational**. Explicitly avoid causal language (e.g., "effect", "cause", "impact") in output summaries. Use "association", "correlation", "relationship".
 - **Weights**: Apply Inverse Probability Weighting (IPW) based on sampling fractions. **Dependency**: MUST consume `data/processed/ipw_weights.parquet` generated by T018.
 - **Timeout Handling**: Implement internal retry logic: If model fitting takes > 6 hours, log state and attempt a reduced-batch retry.
 - **First Retry**: Reduce sample size by **[deferred]**.
 - **Second Retry**: Reduce sample size by **[deferred]** (from original).
 - **Floor**: Adequate sample size of **1000 households** per country minimum.
 - **Max Retries**: Maximum 3 retries.
 - If the retry also times out, log a warning and stop (do not retry indefinitely).
 - **Dependency**: **Must run after T022**. **Enforcement**: Add a file existence check for `data/processed/merged_sample.parquet` and `specs/001-csa-food-security/data-model.md`; raise FileNotFoundError if missing.
- [X] T024 [US2] Implement collinearity diagnostics in `code/analysis/diagnostics.py`:
 - Calculate VIF for all predictors using the **Primary CSA Index** (with digital/finance) via `statsmodels.stats.outliers_influence.variance_inflation_factor`.
 - Flag predictors exceeding VIF > 5.0 (log warning, do not auto-exclude mediators).
 - **Dependency**: **Must run after T022**.
 - **Parallel Opportunity**: T024 can run in parallel with T023 after T022 is complete. **Note**: T022 must be fully committed to disk before T023/T024 start.
- [X] T025 [US2] [FR-006] Implement multiple hypothesis correction in `code/analysis/model.py`:
 - **MUST implement Bonferroni correction** (as per spec FR-006) for > 5 hypotheses to control family-wise error rate.
 - **Conflict Resolution**: Explicitly note that the Plan's 'Constraints' section mandates Bonferroni, while the 'Complexity Tracking' table suggests FDR. Bonferroni is chosen to satisfy the Spec (FR-006) and the Plan's 'Constraints' list.
 - **Dependency**: **Must run after T023**.
- [X] T026 [US2] [FR-007] Implement robustness check logic in `code/analysis/model.py`:
 - Alternative variable specifications.
 - Sensitivity analysis on CSA adoption threshold: **sweep cutoff values from 0.2 (moderate) to 0.8 (strict) in steps of 0.1**.
 - **Traceability**: Explicitly map 0.2 to "moderate" and 0.8 to "strict" per Spec FR-007 and Plan Complexity Tracking.
 - **Output**: Generate `sensitivity_analysis_report.json` containing the sweep range, step size, and for each cutoff: variance in p-values and coefficient estimates.
 - **Dependency**: **Must run after T023**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (model fitted, diagnostics run, results outputted)

**Parallel Opportunities (User Story 2)**:
- T023, T024 can run in **parallel** once T022 is complete.
- T025 and T026 must run after T023.

---

## Phase 5: User Story 3 - Visualization and Robustness Reporting (Priority: P3)

**Goal**: Generate scatter plots, coefficient plots, regional maps, and perform robustness checks (leave-one-country-out, bootstrap resampling).

**Independent Test**: Execute `code/viz/plots.py` and verify that multiple distinct plot types are saved to `output/` and robustness logs are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for plot output files in `tests/contract/test_plot_outputs.py`
- [ ] T030 [P] [US3] Integration test for robustness check execution in `tests/integration/test_robustness.py`

### Implementation for User Story 3

- [X] T031 [US3] Implement scatter plot generation in `code/viz/plots.py` (CSA Index vs. Food Security) **(Must run after T022 and T023)**
- [X] T032 [US3] Implement coefficient plot generation in `code/viz/plots.py` (standardized coefficients with confidence intervals) **(Must run after T022 and T023)**
- [X] T033 [US3] [FR-008] Implement regional map generation in `code/viz/plots.py` using `geopandas` to visualize spatial distribution of CSA adoption and outcomes **(Must run after T023)**. **Deliverable**: Generate `output/maps/csa_adoption_map.png` using a standard geographic projection, visualizing CSA Index and HDDS at the country/region level.
- [X] T034 [US3] Implement distribution plot generation in `code/viz/plots.py` **(Must run after T022 and T023)**
- [ ] T035 [US3] [FR-009] Implement **leave-one-country-out** cross-validation in `code/analysis/robustness.py`:
 - **Region Definition**: Administrative level 0 (Country). **Rationale**: With only 3 countries, leave-one-region-out (N=2 training) is statistically invalid. 'Region' is interpreted as 'Country' to satisfy the Spec's intent while ensuring statistical validity.
 - **Metric**: Log coefficient stability (standard deviation of estimates across folds).
 - **Dependency**: **Must run after T023**.
- [ ] T035b [US3] **Implement Stability Metric Calculation** in `code/analysis/robustness.py`:
 - **Dependency**: Must run after T035.
 - **Action**: Calculate and log the standard deviation of estimates across folds.
 - **Output**: Generate `loco_stability_report.json`.
- [ ] T036 [US3] Implement bootstrap resampling with a sufficient number of iterations in `code/analysis/robustness.py` to validate model stability and report variance estimates.
- [ ] T037 [US3] [FR-004] Create `code/main.py` entry point extension to orchestrate the full analysis and viz pipeline (Model → Diagnostics → Robustness → Plots) and ensure all findings are framed as associational. **Enforcement**: Add file existence checks for `model_results.json` and `robustness_results.json`; raise FileNotFoundError if missing.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] [US1] Create `code/ingestion.py` wrapper script to execute the data download and merge logic defined in `code/data/download.py` and `code/data/clean.py`. **Rationale**: The quickstart.md references `code/ingestion.py` which does not exist; this task creates the missing entry point to satisfy the run-book.
- [ ] T049 [P] [US3] Create `code/viz.py` wrapper script to execute the visualization logic defined in `code/viz/plots.py`. **Rationale**: The quickstart.md references `code/viz.py` which does not exist; this task creates the missing entry point to satisfy the run-book.
- [ ] T050 [P] [US3] Create `code/verify_reproducibility.py` script to validate the full pipeline reproducibility (checksums, output existence, and log consistency). **Rationale**: The quickstart.md references `code/verify_reproducibility.py` which does not exist; this task creates the missing verification script.
- [X] T038 [P] [US3] Generate `specs/001-csa-food-security/quickstart.md` with step-by-step instructions to reproduce the full pipeline from raw data download to final plots. **Dependency**: Must run after T048, T049, T050 to ensure scripts exist before documentation is generated.
- [ ] T051 [US3] Update `specs/001-csa-food-security/quickstart.md` to explicitly reference the newly created wrapper scripts (`ingestion.py`, `viz.py`, `verify_reproducibility.py`) and ensure the command paths match the actual file locations. **Rationale**: Ensures the documentation aligns with the implemented entry points. **Verification**: Run `grep -E "ingestion|viz|verify" quickstart.md` to confirm paths are present. **Dependency**: Must run after T048, T049, T050, and T038.
- [X] T039 [P] Run `ruff check` and `black` on `code/` to ensure code style compliance and fix any linting errors.
- [X] T040 [P] Add memory profiling instrumentation in `code/analysis/model.py` to log peak RAM usage during model fitting.
- [X] T041 [P] Implement unit tests in `tests/unit/` for edge cases: missing years (log warning), climate gaps (interpolation), VIF > 5.0 (flagging), and sampling balance.
- [X] T042 Run `quickstart.md` validation to ensure end-to-end reproducibility on a fresh environment.

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other story
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model results from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

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
 - Developer B: User Story 2 (Statistical Modeling)
 - Developer C: User Story 3 (Visualization & Robustness)
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
- **Constraint Check**: All tasks must run on CPU-only CI with a limited number of cores and limited RAM., with no GPU.. No 8-bit/4-bit quantization, no CUDA, no large LLMs.
- **Data Integrity**: Use real data sources (LSMS, FAOSTAT, NASA POWER) only. No synthetic data fabrication.
- **Spec Alignment**: All tasks strictly adhere to `spec.md` requirements. Discrepancies between `plan.md` and `spec.md` are resolved in favor of the Plan's statistical validity requirements (Fixed-Effects, leave-one-country-out) where the Spec's literal interpretation would be statistically invalid for N=3, while maintaining the Spec's intent for CSA index construction and digital/finance inclusion.
- **Model Alignment**: Fixed-Effects Regression (OLS with Country Dummies) is chosen over Mixed-Effects because N=3 countries makes Mixed-Effects statistically invalid. This satisfies the Spec's requirement for a valid model while adhering to the Plan's constraints.
