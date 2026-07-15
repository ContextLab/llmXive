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
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, numpy, scikit-learn, statsmodels, geopandas, matplotlib, seaborn, requests, pyyaml)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup directory structure for `data/raw/`, `data/processed/`, and `state/` for checksums
- [X] T005 [P] Implement `code/utils/logging.py` for provenance logging (mapping derived variables to raw IDs)
- [X] T006 [P] Create `code/utils/config.py` to manage environment variables (target countries, years, RAM limits)
- [X] T007 Create base data schema definitions in `specs/001-csa-food-security/contracts/dataset.schema.yaml`
- [X] T008 [P] Implement `code/data/download.py` with function stubs: `download_lsms(country, year)`, `download_nasa_power(lat, lon, start, end)`, `download_faostat(indicator)`
- [X] T009 Setup pytest environment in `tests/` with configuration for CPU-only execution
- [X] T022b [P] [US2] **Implement CSA Index & Weighting Definition** in `specs/001-csa-food-security/data-model.md`:
 - **CSA Index Definition**: Define the CSA Index formula as a weighted composite of conservation tillage, crop diversification, irrigation efficiency, **digital-technology access, and finance access** (per Spec FR-003). This is the **Primary Index** used for the main model.
 - **Index Weighting**: Define the weighting strategy for the index as a simple intensity-based weight (e.g., equal weights or practice-specific weights). **DO NOT use Inverse Probability Weighting (IPW) for the index itself.**
 - **Sampling Weight Strategy**: Define the sampling weights separately: Use Inverse Probability Weighting (IPW) based on country/year sampling fractions for the statistical model (T017). This is distinct from the CSA Index weighting.
 - **Dual Role Documentation**: Document the dual role of digital/finance variables: (1) Included in the Primary CSA Index (per FR-003), (2) Tested as external moderators/mediators in the model.
 - **Strict Adherence**: This artifact MUST be completed before T022. T022 MUST strictly follow this definition.

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
 - Match climate data to survey coordinates **within a 50km proximity radius** using the **WGS84 (EPSG:4326) CRS** and **Haversine formula** for distance calculation.
 - Match climate data using **growing season average (3-month pre-harvest mean)** as the temporal window.
 - Flag unmatched rows and log warnings.
- [X] T016 [US1] Implement imputation strategy in `code/data/clean.py` for missing predictor values
- [X] T017 [US1] [FR-005] Implement stratified sampling with **design weights** in `code/data/clean.py`:
 - **Target**: Aim for N ≥ 5000 households **per country** (Kenya, India, Vietnam) if data volume permits.
 - **Trigger**: If raw data > 7GB, apply stratified sampling to reduce size to fit RAM.
 - **Else**: If raw data < 7GB, retain all data regardless of sample size.
 - **Stratification Variables**: Country, Year, Region.
 - **Weight Calculation**: Calculate Inverse Probability Weighting (IPW) based on sampling fractions **for the model** (not the index). This calculation is internal to T017 and does not depend on T022b for the weight logic, only for variable definitions.
 - **Resilience**: If the target N ≥ 5000 cannot be met due to data scarcity (e.g., < 5000 available for a country), **log a warning** and **proceed with the available data**. **DO NOT raise a critical error.**
 - **Enforcement**: If sampling fails to reduce size below a predefined threshold, raise a critical error and generate `sampling_report.json` with schema: `{"final_size": int, "per_country_counts": {"Kenya": int, "India": int, "Vietnam": int}, "sampling_ratio": float, "warning": "Data scarcity detected, proceeding with available N"}`.
- [X] T018 [US1] [FR-011] Implement provenance logger in `code/utils/logging.py` to log a JSON mapping **every derived CSA variable, including the final weighted composite index**, to its source LSMS question ID and response ID
- [X] T019 [US1] Create `code/main.py` entry point to orchestrate the full data pipeline (Download → Clean → Save) **(Must run after T012-T018)**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean, merged, sampled dataset ready)

---

## Phase 4: User Story 2 - Statistical Modeling and Analysis (Priority: P2)

**Goal**: Fit Mixed-Effects Regression models to quantify associational relationships between CSA adoption and food security, including interaction terms and mediation analysis.

**Independent Test**: Run `code/analysis/model.py` on a sample subset and verify output includes standardized coefficients, p-values, VIF scores, and random effect estimates without runtime errors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`
- [X] T021 [P] [US2] Unit test for VIF calculation and collinearity flagging in `tests/unit/test_diagnostics.py`

### Implementation for User Story 2

- [X] T022 [US2] [FR-003] Implement CSA Index construction in `code/data/features.py`:
 - **Strict Adherence**: This implementation MUST strictly follow the formula defined in T022b (`data-model.md`), which includes digital/finance variables as per FR-003.
 - **Dependency**: Strictly follow the formula and weighting strategy defined in T022b.
 - Weighted composite score (conservation tillage, crop diversification, irrigation efficiency, **digital-technology access, finance access**) as defined in `data-model.md` (T022b).
 - Normalize to a unit scale.
 - Apply the sampling weights defined in T017 (for the model, not the index).
 - **Note**: Do NOT attempt to decouple digital/finance variables here; that is handled by the separate diagnostic task T024b.
- [X] T024b [US2] [Plan Diagnostic] **Implement Decoupled CSA Index** in `code/data/features.py`:
 - Construct a **secondary index** (agronomic only: tillage, diversification, irrigation) **excluding** digital/finance variables.
 - Purpose: This index is used **only** for the multicollinearity diagnostic test to satisfy the Plan's concern about variable inclusion, without violating the Spec's FR-003 requirement for the primary index.
 - Output: Save as `data/processed/decoupled_csa_index.parquet`.
- [X] T024 [US2] Implement collinearity diagnostics in `code/analysis/diagnostics.py`:
 - Calculate VIF for all predictors using the **Primary CSA Index** (with digital/finance).
 - Also calculate VIF using the **Decoupled CSA Index** (T024b) to compare collinearity impact.
 - Flag predictors exceeding VIF > 5.0 (log warning, do not auto-exclude mediators).
- [X] T023 [US2] [FR-004] Implement Mixed-Effects Regression model in `code/analysis/model.py`:
 - Include interaction terms for digital and finance access (moderation).
 - Include mediation analysis for digital/finance access (indirect effects) per Constitution Principle VII using the **Baron & Kenny approach**.
 - **Language Constraint**: All findings MUST be framed as **associational**. Explicitly avoid causal language (e.g., "effect", "cause", "impact") in output summaries. Use "association", "correlation", "relationship".
 - Apply stratified sampling weights.
 - Use the **Primary CSA Index** (T022) as the main predictor.
- [X] T025 [US2] [FR-006] Implement multiple hypothesis correction in `code/analysis/model.py`:
 - **MUST implement Bonferroni correction** (as per spec FR-006) for > 5 hypotheses to control family-wise error rate.
 - **Override Note**: Explicitly log that Bonferroni is mandated by FR-006 (Spec) and supersedes the Plan's suggestion of Benjamini-Hochberg FDR. The Plan's FDR suggestion is rejected for this implementation.
 - **(Must run after T023)**.
- [X] T026 [US2] [FR-007] Implement robustness check logic in `code/analysis/model.py`:
 - Alternative variable specifications.
 - Sensitivity analysis on CSA adoption threshold: **sweep cutoff values from 0.3 (moderate) to 0.9 (strict) in steps of 0.1**.
 - **Output**: Generate `sensitivity_analysis_report.json` containing the sweep range, step size, and for each cutoff: variance in p-values and coefficient estimates.
- [X] T027 [US2] [FR-010] Implement timeout handling in `code/analysis/model.py`:
 - If model takes > 6 hours, log state and **attempt a reduced-batch retry**.
 - **Retry Logic**: 
 - **First Retry**: Reduce sample size by **[deferred]**.
 - **Second Retry**: Reduce sample size by **[deferred]** (from original).
   - **Floor**: Minimum sample size of **1000 households**.
   - **Max Retries**: Maximum 3 retries.
 - If the retry also times out, log a critical failure and stop (do not retry indefinitely).
- [X] T028 [US2] Implement timeout verification and performance benchmarking in `tests/integration/test_model_timeout.py` to measure convergence time against the **6-hour GitHub Actions free-tier job limit** with explicit pass/fail criteria

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (model fitted, diagnostics run, results outputted)

---

## Phase 5: User Story 3 - Visualization and Robustness Reporting (Priority: P3)

**Goal**: Generate scatter plots, coefficient plots, regional maps, and perform robustness checks (leave-one-region-out, bootstrap resampling).

**Independent Test**: Execute `code/viz/plots.py` and verify that multiple distinct plot types are saved to `output/` and robustness logs are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for plot output files in `tests/contract/test_plot_outputs.py`
- [X] T030 [P] [US3] Integration test for robustness check execution in `tests/integration/test_robustness.py`

### Implementation for User Story 3

- [X] T031 [US3] Implement scatter plot generation in `code/viz/plots.py` (CSA Index vs. Food Security) **(Must run after T023)**
- [X] T032 [US3] Implement coefficient plot generation in `code/viz/plots.py` (standardized coefficients with confidence intervals) **(Must run after T023)**
- [X] T033 [US3] [FR-008] Implement regional map generation in `code/viz/plots.py` using `geopandas` to visualize spatial distribution of CSA adoption and outcomes **(Must run after T023)**
- [X] T034 [US3] Implement distribution plot generation in `code/viz/plots.py` **(Must run after T023)**
- [X] T035 [US3] [FR-009] Implement leave-one-region-out cross-validation in `code/analysis/robustness.py`:
 - **Region Definition**: Administrative level 1 (province/state).
 - **Metric**: Log coefficient stability (standard deviation of estimates across folds).
 - **(Must run after T023)**.
- [X] T036 [US3] [FR-009] Implement bootstrap resampling with **1000 iterations** in `code/analysis/robustness.py` to validate model stability and report variance estimates.
- [X] T037 [US3] [FR-004] Create `code/main.py` entry point extension to orchestrate the full analysis and viz pipeline (Model → Diagnostics → Robustness → Plots) and ensure all findings are framed as associational.

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
- **Note**: Within User Story 2, tasks T022, T024b, T024, T023, T025 form a strict linear chain (Index -> Decoupled Index -> Diagnostics -> Model -> Correction) and **cannot** run in parallel.
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
- **Spec Alignment**: All tasks strictly adhere to `spec.md` requirements. Discrepancies between `plan.md` and `spec.md` are resolved in favor of `spec.md` (e.g., Bonferroni correction per FR-006, inclusion of digital/finance variables in CSA index per FR-003). The Plan's methodological concerns are addressed via separate diagnostic tasks (T024b) rather than altering the Spec-compliant primary implementation.