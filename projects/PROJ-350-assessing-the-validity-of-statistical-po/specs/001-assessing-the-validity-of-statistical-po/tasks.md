# Tasks: Assessing the Validity of Statistical Power in Publicly Available Pre-Registered Studies

**Input**: Design documents from `/specs/001-assessing-the-validity-of-statistical-power-validity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Unit and integration tests included for extraction, power calculation, and regression logic.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Note on Spec Contradiction (FR-005 vs Plan)**: The `spec.md` (FR-005) mentions binning `sample_size` into categories (Small/Medium/Large) as a predictor. However, the `plan.md` (Complexity Tracking) explicitly mandates the **exclusion** of `sample_size_category` to avoid mathematical coupling with `power_gap`. These tasks follow the `plan.md` constraint (exclusion) as the primary directive. **FR-005 is Narrowed** in implementation to exclude this specific predictor; the regression will be performed on `field` and `effect_size_domain` only.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
- Paths shown below assume single project - adjusted based on `plan.md` structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create directory structure: `code/`, `data/raw/`, `data/derived/`, `tests/`, `specs/`, `results/`, `docs/`
- [ ] T001b [P] Create placeholder files: `.gitkeep` in all data directories
- [ ] T002 Initialize `code/__init__.py` as an empty file
- [ ] T003 [P] Create configuration files: `.pre-commit-config.yaml`, `requirements.txt`, `pyproject.toml`
- [ ] T004 [P] Setup GitHub Actions workflow for CI (CPU-only, limited core count, constrained memory limits) and data checksum validation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Populate `code/__init__.py` with global constants (ALPHA=0.05, VIF_THRESHOLD=5.0, MIN_SAMPLE_SIZE=30)
- [X] T006 Implement `code/utils/data_hygiene.py` for checksumming raw/derived data and validating file existence
- [X] T007 Implement `code/utils/osf_client.py` with exponential backoff for API rate limiting and resume capability
- [X] T008 Setup `pytest` configuration in `tests/conftest.py` with fixtures for sample OSF IDs and mock data

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Metadata Extraction (Priority: P1) 🎯 MVP

**Goal**: Connect to OSF, extract planned power, target_n, and effect_size_assumption from pre-registrations.
**Extended Goal**: Retrieve actual results (sample size, observed effect) from linked data for auditing.

**Independent Test**: Run extraction against a set of known OSF IDs.; verify JSON output matches manual inspection of source documents.

### Tests for User Story 1

- [X] T009 [P] [US1] Unit test for `code/extraction.py` parsing logic with mock OSF JSON in `tests/unit/test_extraction.py`
- [~] T010 [P] [US1] Integration test for OSF API connection and backoff logic in `tests/integration/test_osf_client.py`
- [ ] T011 [US1] Contract test: Verify output schema of `data/derived/study_records_raw.json` against `specs/contracts/study_record.schema.yaml`

### Implementation for User Story 1 (Extraction)

- [X] T012 [US1] Implement `code/extraction.py`: OSF API fetcher with retry logic (FR-001)
- [X] T013 [US1] Implement NLP/Regex hybrid parser in `code/extraction.py` to extract `planned_power`, `target_n`, `effect_size_assumption` (FR-001)
- [~] T014 [US1] Implement logic to handle missing data (flag `missing_planned_data`) and prioritize "Primary Pre-registration" (FR-001)
- [ ] T015 [US1] Implement data validation: ensure `target_n > 0` and flag invalid records (Edge Case)
- [ ] T016 [US1] Write extracted planned records to `data/derived/study_records_raw.json` with source citations (`page_number:paragraph_id`)

### Implementation for User Story 1 (Result Retrieval)

- [ ] T017 [US1] Implement `code/retrieval.py`: Fetch `observed_effect_size` from linked data repositories or published results. **Logic MUST**: (1) Parse OSF files nodes to find data links; (2) Resolve DOIs to data URLs if direct links are missing; (3) Flag records where no data file is found. Explicitly NOT used for sensitivity power calculation (FR-002).
- [ ] T018 [US1] Implement `code/retrieval.py`: Fetch `actual_sample_size` from linked data repositories or published results. **Logic MUST**: (1) Parse OSF files nodes; (2) Resolve DOIs; (3) Flag records where data is missing. **This task is a blocking prerequisite for Phase 4** (FR-002).
- [ ] T019 [US1] Implement validation for retrieved results: handle CI midpoints, flag missing `actual_sample_size` (Edge Case)

**Checkpoint**: At this point, User Story 1 (Extraction + Result Retrieval) should be fully functional and testable independently

---

## Phase 4: User Story 2 - Sensitivity Power Calculation and Power Gap Analysis (Priority: P2)

**Goal**: Calculate Sensitivity Power using actual sample size and assumed effect size; compute Power Gap.
**Constraint**: Use `effect_size_assumption` (not `observed_effect_size`) for the calculation to avoid "Winner's Curse".

**Independent Test**: Feed known `n`, `assumed_effect_size`, `alpha` to module; verify `sensitivity_power` matches manual `statsmodels` calculation.

### Tests for User Story 2

- [ ] T020 [P] [US2] Unit test for `code/power_calc.py` with known statistical inputs in `tests/unit/test_power_calc.py`. **Must verify** that `alpha` is hardcoded to 0.05 (FR-003).
- [ ] T021 [P] [US2] Unit test for edge cases (power > 1.0, power < 0.0) and clamping logic in `tests/unit/test_power_calc.py`
- [ ] T021a [P] [US2] Regression test: Compare `code/power_calc.py` output against a hard-coded `statsmodels` baseline result for a known input to satisfy SC-005.
- [ ] T022 [US2] Contract test: Verify `data/derived/power_analysis.csv` schema and data types

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/power_calc.py`: Sensitivity power calculation using `statsmodels.stats.power` with `effect_size_assumption` and `actual_sample_size` (from T018). **Verify** `alpha=0.05` is hardcoded (FR-003).
- [ ] T024 [US2] Implement `power_gap` calculation: `planned_power - sensitivity_power` (FR-004)
- [ ] T025 [US2] Implement validation: clamp sensitivity power to the valid probability range and log warnings for anomalies (Edge Case)
- [ ] T026 [US2] Write final analysis dataset to `data/derived/power_analysis.csv` including all calculated metrics (FR-004, FR-006)
- [ ] T026a [US2] **CRITICAL GUARDRAIL**: Filter `power_analysis.csv` to include only studies with valid power calculations. If the count is < 30 (SC-004), **halt execution** and write an error artifact to `results/error/sample_size_insufficient.json`.
- [ ] T027 [US2] Implement one-sample t-test (or Wilcoxon) on `data/derived/power_analysis.csv` column `power_gap` against null hypothesis of zero (SC-001). **Output**: Write test statistic, p-value, and conclusion to `data/derived/regression_diagnostics.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regression Modeling and Predictor Identification (Priority: P3)

**Goal**: Perform multiple linear regression to identify predictors of Power Gap; include VIF diagnostics.
**Constraint**: Exclude `sample_size_category` to avoid mathematical coupling with `power_gap`. **FR-005 is Narrowed**.

**Independent Test**: Run regression on synthetic data with known relationships; verify model recovers correct coefficients and flags collinearity.

### Tests for User Story 3

- [ ] T028 [P] [US3] Unit test for `code/regression.py` with synthetic dataset in `tests/unit/test_regression.py`
- [ ] T029 [P] [US3] Unit test for VIF calculation and threshold flagging (VIF > 5) in `tests/unit/test_regression.py`
- [ ] T030 [US3] Contract test: Verify `data/derived/regression_results.json` schema

### Implementation for User Story 3

- [ ] T031 [US3] Implement `code/regression.py`: Preprocess data (encode `field` as dummies). **EXCLUDE** `sample_size_category` from regression model to avoid mathematical coupling (Plan Constraint). **If** dataset size < 30 (from T026a), **halt execution**.
- [ ] T032 [US3] Implement multiple linear regression model using `statsmodels.OLS` with `power_gap` as target and predictors: `field`, `effect_size_domain` (excluding `sample_size_category`) (FR-005). **Verification**: Assert that `sample_size_category` is NOT in the model's feature list.
- [ ] T033 [US3] Implement Variance Inflation Factor (VIF) calculation for all predictors; flag if > 5.0 (FR-006, SC-003)
- [ ] T034 [US3] Implement logic to suppress independent effect claims if VIF > 5.0 and report joint relationship (FR-006)
- [ ] T035 [US3] Generate diagnostic plots (residuals, predictor vs. Power Gap) and save to `results/plots/`
- [ ] T036 [US3] Write regression results (coefficients, p-values, R-squared, VIF) to `data/derived/regression_results.json` (FR-005)
- [ ] T037 [US3] Add explicit associational framing to output (no causal claims) (FR-007)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Implement `code/report_generator.py` to fetch metrics from `data/derived/` and render `docs/report.md` template
- [ ] T039 [P] Execute `code/report_generator.py` to generate `docs/report.md` from `data/derived/` metrics. **Verify** file existence and non-empty content.
- [ ] T040 [P] Code cleanup and refactoring of `code/main.py` pipeline orchestration
- [ ] T041 [P] Run `pytest` suite with coverage report (target > 90%)
- [ ] T042 [P] Validate all data checksums and update `state/projects/PROJ-350-assessing-the-validity-of-statistical-po.yaml` with content hashes (Constitution Principle V)
- [ ] T043 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T044 Review and update `README.md` with execution instructions and data provenance

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed) **EXCEPT** US2 and US3.
 - **US2 (Power Calc) must complete before US3 (Regression)** because US3 consumes the `power_analysis.csv` artifact.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (requires `study_records_raw.json` from T016/T018). **T018 is a blocking prerequisite**.
- **User Story 3 (P3)**: Depends on US2 (requires `power_analysis.csv` from T026/T026a). **Strictly Sequential**: US3 cannot run in parallel with US2.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before Services/Calculators
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately.
- US2 can start once T018 (blocking) is done.
- US3 can start **only after** US2 is fully complete (T026a/T027).
- All tests for a user story marked [P] can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Extraction + Retrieval)
4. **STOP and VALIDATE**: Test User Story 1 independently (Extraction pipeline works)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Power Gap calculated)
4. Add User Story 3 → Test independently → Deploy/Demo (Regression complete)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Extraction)
 - Developer B: User Story 2 (Power Calc) - *Note: Can start once T018 is done*
 - Developer C: User Story 3 (Regression) - *Note: Can start ONLY after T026a is done*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All statistical methods must be CPU-tractable (no GPU, no 8-bit quantization, no large LLMs).
- **Data Integrity**: Never fabricate data; all inputs must come from real OSF API responses or real linked repositories.
- **Methodological Constraint**: `sample_size_category` is explicitly excluded from the regression model (T031, T032) to avoid mathematical coupling, per `plan.md` Complexity Tracking. **FR-005 is Narrowed**.
- **Sample Size Guardrail**: T026a enforces the ≥30 study threshold (SC-004). If unmet, the pipeline halts.