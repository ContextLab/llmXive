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
- [X] T001b [P] Create `__init__.py` files in all `code/` sub-packages (`data/`, `analysis/`, `viz/`, `utils/`)
- [X] T002 Initialize Python 3.14.6 project with pinned dependencies in `code/requirements.txt` (pandas>=2.0.0, numpy>=1.24.0, scikit-learn>=1.3.0, statsmodels>=0.14.0, geopandas>=0.13.0, matplotlib>=3.7.0, seaborn>=0.12.0, requests>=2.31.0, pyyaml>=6.0.0). **Note: The Plan's Technical Context mandates a specific major version of Python as a verified fact.**
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup directory structure for `data/raw/`, `data/processed/`, and `state/` for checksums
- [X] T005 [P] Implement `code/utils/logging.py` for provenance logging (mapping derived variables to raw IDs)
- [X] T006 [P] Create `code/utils/config.py` to manage environment variables (target countries, years, RAM limits)
- [X] T007 Create base data schema definitions in `specs/001-csa-food-security/contracts/dataset.schema.yaml`
- [X] T007b [P] **Define CSA Index Formula** in `specs/001-csa-food-security/data-model.md`:
 - **CSA Index Definition**: Define the CSA Index formula as a weighted composite: `CSA_Index = w1*(Conservation Tillage) + w2*(Crop Diversification) + w3*(Irrigation Efficiency) + w4*(Digital Access) + w5*(Finance Access)`. Weights (w-w) are defined as equal (0.2 each) or practice-specific intensity scores, normalized to [0, 1]. **This is the Primary Index.**
 - **Strict Adherence**: This artifact MUST be completed before T022. T022 MUST strictly follow this definition.
 - **Note**: If `data-model.md` does not exist, create it with the explicit formula text above.
- [X] T007c [P] **Define CSA Index Weighting Strategy** in `specs/001-csa-food-security/data-model.md`:
 - **Index Weighting**: Define the weighting strategy as simple intensity-based weights. **DO NOT use Inverse Probability Weighting (IPW) for the index itself.**
 - **Sampling Weight Strategy**: Define sampling weights separately: Use Inverse Probability Weighting (IPW) based on country/year sampling fractions for the statistical model (T023). This is distinct from the CSA Index weighting.
 - **Dual Role Documentation**: Document the dual role of digital/finance variables: (1) Included in the Primary CSA Index (per FR-003), (2) Tested as external moderators/mediators in the model.
- [X] T007d [P] **Define CSA Index Provenance** in `specs/001-csa-food-security/data-model.md`:
 - **Provenance Mapping**: Mandate that the weights themselves (e.g., 0.2) are linked to the 'equal weighting strategy' defined in T007c. This ensures provenance records map back to the raw survey responses and the logic used to derive the weights, satisfying Constitution Principle VI.
- [X] T008 [P] Implement `code/data/download.py` with function stubs: `download_lsms(country, year)`, `download_nasa_power(lat, lon, start, end)`, `download_faostat(indicator)`
- [X] T009 Setup pytest environment in `tests/` with configuration for CPU-only execution

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download, clean, merge, and sample LSMS, FAOSTAT, and NASA POWER data into a single analysis-ready dataset.

**Independent Test**: Execute `code/data/pipeline.py` and verify `data/processed/merged_sample.parquet` contains ≥ 95% valid records, no missing values in key predictors after imputation, and matches the schema.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_dataset_schema.py`
- [X] T011 [P] [US1] Integration test for download and merge pipeline in `tests/integration/test_data_pipeline.py`: Verify pipeline runs without error and output file exists.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement LSMS downloader in `code/data/download.py` targeting Kenya, India, Vietnam (recent years) with error handling for missing years
- [X] T013 [P] [US1] Implement NASA POWER climate downloader in `code/data/download.py` using `requests` and nearest-neighbor spatial interpolation for gaps ≤ 3 months
- [X] T014 [P] [US1] Implement FAOSTAT agricultural indicator downloader in `code/data/download.py`
- [X] T015 [US1] Implement data cleaning and merging logic in `code/data/clean.py`:
 - Merge using country code + year
 - Match climate data to survey coordinates **within a defined proximity radius** using the **WGS84 (EPSG:4326) CRS** and **Haversine formula** for distance calculation.
 - Match climate data using **growing season average (3-month pre-harvest mean)** as the temporal window.
 - Flag unmatched rows and log warnings.
- [X] T016 [US1] Implement imputation strategy in `code/data/clean.py` for missing predictor values
- [X] T017 [US1] [FR-005] Implement **stratified sampling** in `code/data/clean.py`:
 - **Target**: Aim for N ≥ 5000 households **per country** (Kenya, India, Vietnam) if data volume permits.
 - **Trigger**: If sum of file sizes in `data/raw/` > 7GB, apply stratified sampling to reduce size to fit RAM.
 - **Hard Cap**: If raw data < 7GB but estimated processing memory > 7GB, apply sampling to ensure the working set does not exceed a predefined memory threshold.
 - **Else**: If raw data < 7GB and estimated processing memory <= 7GB, retain all data.
 - **Stratification Variables**: Country, Year, Region.
 - **Resilience**: If the target N ≥ 5000 cannot be met due to data scarcity (e.g., < 5000 available for a country), **log a warning** and **proceed with the available data**. **DO NOT raise a critical error.**
 - **Enforcement**: If sampling fails to reduce size below a predefined threshold (7GB), **log a warning** and generate `sampling_report.json` with schema: `{"final_size": int, "per_country_counts": {"Kenya": int, "India": int, "Vietnam": int}, "sampling_ratio": float, "warning": "Data scarcity detected, proceeding with available N"}`.
 - **Note**: This task implements **sampling** only. Inverse Probability Weighting (IPW) for the model is handled in T023.
- [X] T018 [US1] [FR-011] Implement provenance logger in `code/utils/logging.py` to log a JSON mapping **every derived CSA variable, including the final weighted composite index**, to its source LSMS question ID and response ID
- [ ] T019 [US1] Create `code/main.py` entry point to orchestrate the full data pipeline (Download → Clean → Save) **(Must run after T012-T018 and T007b)**. **Enforcement**: Add a file existence check for `data/processed/merged_sample.parquet` and `specs/001-csa-food-security/data-model.md`; raise FileNotFoundError if missing.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean, merged, sampled dataset ready)

---

## Phase 4: User Story 2 - Statistical Modeling and Analysis (Priority: P2)

**Goal**: Fit Fixed-Effects Regression models to quantify associational relationships between CSA adoption and food security, including interaction terms and mediation analysis.

**Independent Test**: Run `code/analysis/model.py` on a sample subset and verify output includes standardized coefficients, p-values, VIF scores, and fixed effect estimates without runtime errors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`
- [X] T021 [P] [US2] Unit test for VIF calculation and collinearity flagging in `tests/unit/test_diagnostics.py`
- [X] T028 [P] [US2] Integration test for timeout handling in `tests/integration/test_model_timeout.py` to measure convergence time against the **GitHub Actions free-tier job limit** with explicit pass/fail criteria

### Implementation for User Story 2

- [X] T022 [US2] [FR-003] Implement CSA Index construction in `code/data/features.py`:
 - **Strict Adherence**: This implementation MUST strictly follow the formula defined in T007b (`data-model.md`), which includes digital/finance variables as per FR-003.
 - **Dependency**: Strictly follow the formula and weighting strategy defined in T007b.
 - Weighted composite score (conservation tillage, crop diversification, irrigation efficiency, **digital-technology access, finance access**) as defined in `data-model.md` (T007b).
 - Normalize to a unit scale.
 - **Note**: Do NOT attempt to decouple digital/finance variables here; that is handled by the separate diagnostic task T024.

- [X] T023 [US2] [FR-002] [FR-004] [FR-010] Implement **Fixed-Effects Regression Model (OLS with Country Dummies)** in `code/analysis/model.py`:
 - **Model Type**: Fixed-Effects Regression (OLS with Country Dummies). **Rationale**: Mixed-Effects is statistically invalid for N=3 countries. This approach controls for unobserved country-level heterogeneity and satisfies the Spec's intent for a valid model while adhering to the Plan's statistical constraints.
 - **Predictors**: Include the **Primary CSA Index** (T022) and interaction terms for digital and finance access (moderation).
 - **Mediation**: Implement mediation analysis (Baron & Kenny approach) on the Fixed-Effects coefficients to test the indirect effects of digital/finance access (Constitution Principle VII).
 - **Language Constraint**: All findings MUST be framed as **associational**. Explicitly avoid causal language (e.g., "effect", "cause", "impact") in output summaries. Use "association", "correlation", "relationship".
 - **Weights**: Apply Inverse Probability Weighting (IPW) based on sampling fractions (calculated in T017 logic but applied here).
 - **Timeout Handling**: Implement internal retry logic: If model fitting takes > 6 hours, log state and attempt a reduced-batch retry.
   - **First Retry**: Reduce sample size by **%**.
   - **Second Retry**: Reduce sample size by a significant margin (from original).
   - **Floor**: Minimum sample size of ** households**.
   - **Max Retries**: Maximum 3 retries.
   - If the retry also times out, **log a warning** and stop (do not retry indefinitely).
 - **Dependency**: **Must run after T022 and T017**. **Enforcement**: Add a file existence check for `data/processed/merged_sample.parquet` and `data/processed/features.parquet`; raise FileNotFoundError if missing.

- [X] T024 [US2] Implement collinearity diagnostics in `code/analysis/diagnostics.py`:
 - Calculate VIF for all predictors using the **Primary CSA Index** (with digital/finance).
 - Flag predictors exceeding VIF > 5.0 (log warning, do not auto-exclude mediators).
 - **Dependency**: **Must run after T022**.
 - **Parallel Opportunity**: T024 can run in parallel with T023 after T022 is complete. **Note**: T022 must be fully committed to disk before T023/T024 start.

- [X] T025 [US2] [FR-006] Implement multiple hypothesis correction in `code/analysis/model.py`:
 - **MUST implement Bonferroni correction** (as per spec FR-006) for > 5 hypotheses to control family-wise error rate.
 - **Conflict Resolution**: Explicitly note that the Plan's 'Constraints' section mandates Bonferroni, while the 'Complexity Tracking' table suggests FDR. Bonferroni is chosen to satisfy the Spec (FR-006) and the Plan's 'Constraints' list.
 - **Dependency**: **Must run after T023**. **Enforcement**: Consume `model_results.json` from T023.

- [X] T026 [US2] [FR-007] Implement robustness check logic in `code/analysis/model.py`:
 - Alternative variable specifications.
 - Sensitivity analysis on CSA adoption threshold: **sweep cutoff values from a moderate threshold to a strict threshold in incremental steps**.
 - **Traceability**: Explicitly map 0.2 to "moderate" and 0.8 to "strict" per Spec FR-007 and Plan Complexity Tracking.
 - **Output**: Generate `sensitivity_analysis_report.json` containing the sweep range, step size, and for each cutoff: variance in p-values and coefficient estimates.
 - **Dependency**: **Must run after T023**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (model fitted, diagnostics run, results outputted)

**Parallel Opportunities (User Story 2)**:
- T023 (Model) and T024 (Diagnostics) can run in **parallel** once T022 is complete.
- T025 and T026 must run after T023.

---

## Phase 5: User Story 3 - Visualization and Robustness Reporting (Priority: P3)

**Goal**: Generate scatter plots, coefficient plots, regional maps, and perform robustness checks (leave-one-country-out, bootstrap resampling).

**Independent Test**: Execute `code/viz/plots.py` and verify that multiple distinct plot types are saved to `output/` and robustness logs are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for plot output files in `tests/contract/test_plot_outputs.py`
- [ ] T030 [P] [US3] Integration test for robustness check execution in `tests/integration/test_robustness.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement scatter plot generation in `code/viz/plots.py` (CSA Index vs. Food Security) **(Must run after T022 and T023)**
- [ ] T032 [US3] Implement coefficient plot generation in `code/viz/plots.py` (standardized coefficients with confidence intervals) **(Must run after T022 and T023)**
- [ ] T033 [US3] [FR-008] Implement regional map generation in `code/viz/plots.py` using `geopandas` to visualize spatial distribution of CSA adoption and outcomes **(Must run after T023)**
- [ ] T034 [US3] Implement distribution plot generation in `code/viz/plots.py` **(Must run after T022 and T023)**
- [ ] T035 [US3] [FR-009] Implement **leave-one-country-out** cross-validation in `code/analysis/robustness.py`:
 - **Region Definition**: Administrative level 0 (Country). **Rationale**: With only 3 countries, leave-one-region-out (N=2 training) is statistically invalid. 'Region' is interpreted as 'Country' to satisfy the Spec's intent while ensuring statistical validity.
 - **Metric**: Log coefficient stability (standard deviation of estimates across folds).
 - **Dependency**: **Must run after T023**.
- [ ] T036 [US3] [FR-009] Implement bootstrap resampling with a sufficient number of iterations in `code/analysis/robustness.py` to validate model stability and report variance estimates.
- [X] T037 [US3] [FR-004] Create `code/main.py` entry point extension to orchestrate the full analysis and viz pipeline (Model → Diagnostics → Robustness → Plots) and ensure all findings are framed as associational. **Enforcement**: Add file existence checks for `model_results.json` and `robustness_results.json`; raise FileNotFoundError if missing.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Generate `specs/001-csa-food-security/quickstart.md` with step-by-step instructions to reproduce the full pipeline from raw data download to final plots.
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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
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
- **Note**: Within User Story 2, tasks T022, T023, T024, T025, T026 have the following dependencies:
 - T007b, T007c, T007d must complete before T022.
 - T022 must complete before T023 and T024.
 - **T023 (Model) and T024 (Diagnostics) can run in parallel** after T022.
 - T025 and T026 must run after T023.
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_dataset_schema.py"
Task: "Integration test for download and merge pipeline in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement LSMS downloader in code/data/download.py"
Task: "Implement NASA POWER climate downloader in code/data/download.py"
Task: "Implement FAOSTAT agricultural indicator downloader in code/data/download.py"
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
- **Model Alignment**: Fixed-Effects Regression (OLS with Country Dummies) is chosen over Mixed-Effects due to N=3 countries making Mixed-Effects statistically invalid. This satisfies the Spec's requirement for a valid model while adhering to the Plan's constraints.
- **Robustness Alignment**: Leave-one-country-out is chosen over leave-one-region-out due to N=3 countries making leave-one-region-out statistically invalid. This satisfies the Spec's requirement for robustness while adhering to the Plan's constraints.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T043 Reconcile run-book vs implementation for `code/ingestion.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/ingestion.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T044 Reconcile run-book vs implementation for `code/preprocessing.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/preprocessing.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T045 Reconcile run-book vs implementation for `code/modeling.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/modeling.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T046 Reconcile run-book vs implementation for `code/viz.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/viz.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T047 Reconcile run-book vs implementation for `code/verify_reproducibility.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/verify_reproducibility.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
