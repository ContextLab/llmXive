# Tasks: Adoption of Sustainable Agricultural Practices in Low‑Income Areas through Community Engagement

**Input**: Design documents from `/specs/018-adoption-sustainable-agriculture/`
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

- [X] T001 Create project structure: Create root directory `projects/PROJ-018-adoption-of-sustainable-agricultural-pra/` and subdirectories `code/`, `data/raw/`, `data/processed/`, `results/`, `tests/`, and `docs/`.
- [X] T002 Initialize Python 3.11 project with requirements (`pandas`, `statsmodels`, `scikit-learn`, `matplotlib`, `pyyaml`, `factor_analyzer`, `evalues`) in `code/requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create data schema contracts in `specs/018-adoption-sustainable-agriculture/contracts/dataset.schema.yaml` and `contracts/results.schema.yaml`
- [ ] T005 [P] Implement synthetic data generator in `code/00_generate_synthetic_data.py` to conform to schema (fallback for missing API URLs) <!-- FAILED: unspecified -->
- [X] T006 [P] Setup logging infrastructure and `modeling_log.yaml` initialization in `code/`
- [ ] T007 Create base configuration management for data paths and random seeds in `code/config.py` <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Acquire & Pre‑process Survey Data (Priority: P1) 🎯 MVP

**Goal**: Obtain relevant agricultural survey dataset (or synthetic equivalent), filter to low-income countries, and prepare a cleaned CSV with no missing values for required variables.

**Independent Test**: The pipeline can be executed end-to-end to produce a cleaned CSV file containing all required variables, and the test passes if the file is generated without errors and contains ≥ 95% of all available records matching the low-income country filter in the source API (or synthetic equivalent).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**
> **NOTE**: T010 and T011 can be *written* in parallel, but T011 *execution* depends on artifacts from T012/T014.
> **NOTE**: T011 execution is blocked until T014 completes.

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/test_schemas.py`
- [X] T011 [P] [US1] Integration test for end-to-end data download and cleaning in `tests/test_pipeline.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/01_download_data.py` to attempt World Bank LSMS/FAO FIES fetch; if URLs unavailable, fallback to synthetic generator; explicitly log source metadata and the inability to fetch real data as a "documented limitation" in `data/metadata.yaml` (FR-001, FR-002, F001) <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T013 [US1] Implement variable validation in `code/01_download_data.py` to check for required fields (age, education, farm_size, credit, adoption, engagement items) and log gaps (FR-002) <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T014 [US1] Implement `code/02_clean_data.py` to handle missing values (impute or drop rows with >30% missing), normalize categorical codes, and export `data/processed/cleaned_data.csv` (FR-003) <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T015 [US1] Implement power analysis check in `code/02_clean_data.py`: Calculate `effective_N_events / num_predictors` (where `effective_N_events` = count of positive outcomes in `adoption_binary` if available, or estimated a non-negligible proportion of N if not); if ratio < 10, log `{'shortfall': true, 'ratio': <value>}` to `modeling_log.yaml` under key `power_analysis`. **Do not halt execution**; document shortfall as a study limitation per SC-006 (SC-006, Plan Phase 3) <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T016 [US1] Add validation and error handling for data ingestion and cleaning steps: raise `CustomDataError` and log to `modeling_log.yaml` on failure (FR-003)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Construct Community‑Engagement Score & Adoption Indicator (Priority: P2)

**Goal**: Create a composite index for community-engagement intensity (`engagement_score`) and a binary indicator for sustainable-practice adoption (`adoption_binary`), including reliability and validity checks.

**Independent Test**: Running the "feature engineering" script on the cleaned dataset must produce two new columns (`engagement_score`, `adoption_binary`) and report reliability statistics; the test passes if the columns are generated and reliability statistics are reported (regardless of threshold achievement).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for feature engineering output schema in `tests/test_schemas.py`
- [X] T019 [P] [US2] Integration test for engagement score calculation and adoption flagging in `tests/test_pipeline.py`

### Implementation for User Story 2

- [~] T020 [US2] Implement `code/03_engineer_features.py` to create `adoption_binary` (1 if any sustainable practice reported) based on FR-005 <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [~] T021 [US2] Implement `code/03_engineer_features.py` to construct `engagement_score` using proxy variables (membership, extension, collective action, knowledge exchange) per FR-011 (weighted sum or equal-weight average) with explicit fallback mechanism if top-priority proxies are absent (FR-011) <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [~] T022 [US2] Implement `code/03_engineer_features.py` to: (1) Calculate Cronbach's α; (2) Conduct Exploratory Factor Analysis (EFA) using **Principal Axis Factoring** extraction, **Varimax** rotation, and **Kaiser's rule** (eigenvalues > 1) for factor retention; (3) Perform convergent validity check (correlation with theoretically related constructs); (4) Serialize all metrics (α, factor loadings, correlations) to `results/validity_metrics.yaml` and update `modeling_log.yaml` with `convergent_validity_status` (FR-004, SC-002, FR-011, Plan Phase 2) <!-- SKIPPED: YAML+regex parse failed (while scanning a simple key <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
 in "<unicode string>", line 2, column 1:
 1. **Cronbach's Alpha** calcula...
 ^
could not find expected ':'
 in "<unicode string>", line 3, column 1:
 2. **Exploratory Factor Analysi...
 ^) -->
- [X] T023 [US2] [DEPRECATED - Merged into T022]
- [X] T024 [US2] [DEPRECATED - Merged into T022]

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Fit Logistic Regression & Mediation Analysis & Generate Report (Priority: P3)

**Goal**: Estimate the association between community-engagement intensity and practice adoption, control for covariates, assess model performance (VIF, FDR, ROC), test mediation effects, and generate a reproducible PDF report.

**Independent Test**: Executing the analysis script must output a regression summary, mediation analysis results, AUC value, and a PDF report; the test passes if all outputs are generated and documented, regardless of whether performance thresholds are met.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T034 [P] [US3] Contract test for results schema (regression table, mediation results, AUC) in `tests/test_schemas.py`
- [X] T035 [P] [US3] Integration test for full modeling pipeline and report generation in `tests/test_pipeline.py`

### Implementation for User Story 3

- [~] T036 [US3] Implement `code/04_model_analysis.py` to fit logistic regression (`adoption_binary` ~ `engagement_score` + covariates) using statsmodels (FR-006) <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->
- [X] T037 [US3] Implement VIF calculation for all predictors; flag VIF ≥ 5 as a collinearity warning. **Do not perform PCA**; strictly adhere to FR-007 which only requires VIF diagnostics (FR-007, SC-004)
- [X] T038 [US3] Implement Benjamini-Hochberg FDR correction (q ≤ 0.10) on hypothesis tests and report adjusted p-values (FR-008, SC-005)
- [~] T039 [US3] Implement ROC curve plotting and AUC calculation in `code/04_model_analysis.py` (FR-009, SC-003) <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [~] T040 [US3] Implement mediation analysis in `code/04_model_analysis.py`: (1) Baron & Kenny approach with bootstrap CI (≥1000 resamples) for indirect effects; (2) Sensitivity analysis using E-values (via `evalues` library) and Rosenbaum bounds (calculate for gamma values in a range including 2.5); (3) Document interpretation as "exploratory" (FR-012, FR-010, Plan Phase 3) <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [X] T041 [US3] [DEPRECATED - Merged into T040] <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [~] T042 [US3] Implement `code/05_generate_report.py` to produce a PDF report containing descriptives, regression table, VIF diagnostics, ROC plot, mediation results, sensitivity analysis, and validity metrics (consuming `results/validity_metrics.yaml`) (FR-010) <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified -->
- [X] T043 [US3] Ensure all results are saved to `results/` and `modeling_log.yaml` is updated with seeds and choices (Constitution IV, VII)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T044 [P] Documentation updates: Create `docs/README.md` with data provenance section and update `docs/METHODOLOGY.md` with methodology notes
- [X] T045 [P] Define abstract base class interface for data sources in `code/interfaces.py`: Class `DataSource` with methods `fetch_data(country_codes: List[str]) -> pd.DataFrame` and `validate_schema(df: pd.DataFrame) -> bool`
- [X] T046 [P] Additional unit tests for statistical functions in `tests/unit/`
- [X] T047 Run quickstart.md validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (Phase 3)**: Can start after Foundational. Produces `cleaned_data.csv`.
 - **US2 (Phase 4)**: **Depends on US1**. Requires `cleaned_data.csv` as input. Produces `engineered_data.csv`.
 - **US3 (Phase 5)**: **Depends on US2**. Requires `engineered_data.csv` (specifically `engagement_score` and `adoption_binary` columns) as input.
 - **Strict Sequential Flow**: US1 -> US2 -> US3. US2 and US3 cannot start until their respective upstream artifacts are generated.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on cleaned data from US1**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on engineered features from US2**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **User Stories CANNOT run in parallel**: Strict sequential dependency US1 -> US2 -> US3 due to data flow.
- All tests for a user story marked [P] can run in parallel (once implementation is ready)
- Models within a story marked [P] can run in parallel
- Different user stories cannot be worked on in parallel by different team members due to data dependencies

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/test_schemas.py"
Task: "Integration test for end-to-end data download and cleaning in tests/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/01_download_data.py..."
Task: "Implement code/02_clean_data.py..."
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
 - Developer A: User Story 1 (US2 and US3 blocked until US1 complete)
 - Developer B: Prepare US2 code structure (cannot run tests until US1 data ready)
 - Developer C: Prepare US3 code structure (cannot run tests until US2 data ready)
3. Stories complete and integrate sequentially: US1 -> US2 -> US3

---

## Notes

- [P] tasks = different files, no dependencies (for task creation/scheduling only; execution may depend on upstream artifacts)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Feasibility Note**: {{claim:c_cc99e695}} (Wikidata Q117453145, https://www.wikidata.org/wiki/Q117453145) Feasibility Note: {{claim:c_cc99e695}} (Wikidata Q117453145, https://www.wikidata.org/wiki/Q117453145) No GPU or 8-bit quantization tasks are included.
- **Data Flow Constraint**: US2 requires `cleaned_data.csv` from US1. US3 requires `engineered_data.csv` from US2. Parallel execution of US2/US3 is impossible until upstream data is generated.
- **Execution Note**: T011 execution is blocked until T014 completes. T042 execution depends on T022 completing and writing `results/validity_metrics.yaml`.
