# Tasks: Exploring the Correlation Between Crystal Structure and Thermal Conductivity in Perovskites

**Input**: Design documents from `/specs/001-correlation-perovskites/`
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

- [ ] T001 Create project structure with exact directory tree: src/, tests/, data/raw/, data/cleaned/, data/results/, figures/, contracts/
- [ ] T002 Initialize Python 3.9 project with requirements.txt at repository root (pymatgen==2023.9.1, pandas==2.2.2, numpy==1.26.4, scikit-learn==1.5.0, statsmodels==0.14.2, matplotlib==3.9.0, seaborn==0.13.2, requests==2.32.3, tqdm==4.66.5, pytest)
- [ ] T003 [P] Configure linting and formatting: create .flake8 (max-line-length=88, extend-ignore=E203) and pyproject.toml (black settings)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup environment configuration management for API keys (Materials Project API) at src/config/env.py with environment variable loading and error handling
- [ ] T005 [P] Create contracts/merged_perovskite.schema.yaml for CSV schema validation
- [ ] T006 Implement deterministic seed handling (--seed argument) in exact modules: src/ingest/, src/cleaning/, src/descriptors/, src/analysis/, src/utils/
- [ ] T007 Setup SHA-256 checksum tracking for raw data files to state/projects/PROJ-035-exploring-the-correlation-between-crysta.yaml artifact_hashes (Constitution III)
- [ ] T008 Create base validation utilities at src/utils/validation.py with function signatures: calculate_vif(df, predictors), handle_error(message, level), setup_logger(name, level)
- [ ] T039 [P] Execute Reference-Validator Agent as blocking gate for all citations (Slack 1979, Smith et al. 2021) per Constitution II; output verification report to data/results/reference_validation.json

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion & Cleaning Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download perovskite crystal structures from Materials Project API and merge with thermal conductivity values from peer-reviewed literature/NIST (NOT Materials Project thermal endpoint), filtering for valid ABX₃ stoichiometry and removing entries with missing data

**Independent Test**: Execute data ingestion script and verify output CSV contains ≥ 50 rows with no null values in thermal_conductivity or structure_id columns

**Acceptance Scenarios**:

1. **Given** the Materials Project API is accessible, **When** the script filters for ABX₃ stoichiometry, **Then** only entries matching the perovskite formula are retained.
2. **Given** a merged dataset of structures and thermal properties, **When** entries with missing thermal conductivity are identified, **Then** the resulting dataframe has ≥50 rows after filtering (SC-001).

**TDD Execution Note**: All test tasks below are written to FAIL first, then implementation follows.

### Tests for User Story 1

- [ ] T009 [US1] Contract test for merged_perovskite.schema.yaml in tests/contract/test_schema.py
- [ ] T010 [US1] Integration test for full data ingestion pipeline in tests/integration/test_full_pipeline.py

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement src/ingest/fetch_structures.py for Materials Project API download with ABX₃ filtering, exponential backoff (max 3 retries), and error handling (FR-001)
- [ ] T012 [P] [US1] Implement src/ingest/fetch_thermal.py for loading literature/NIST thermal conductivity CSVs ONLY (explicitly exclude Materials Project thermal properties endpoint per FR-010) (FR-010)
- [ ] T013 [US1] Implement src/cleaning/clean_merge.py to merge structures with thermal data, remove nulls, validate geometry, enforce minimum 50 compositions, and add error handling for insufficient samples with message 'Insufficient samples: N < 50' (FR-002, FR-010, SC-001)
- [ ] T014 [US1] Implement src/cleaning/provenance_validator.py to verify peer-reviewed/NIST source_reference for each entry (FR-010)
- [ ] T015 [US1] Implement src/cleaning/temperature_normalize.py using Slack (1979) formula for 300K ± 10K window with error handling for unknown temperature (FR-013)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Structural Descriptor Calculation & Correlation Analysis (Priority: P2)

**Goal**: Compute crystallographic distortion metrics (octahedral tilting angles, bond-length variance, tolerance factor) using pymatgen and perform statistical correlation analysis stratified by perovskite chemistry class

**Independent Test**: Run correlation module on cleaned, stratified dataset and verify output includes correlation matrix with p-values for all defined descriptors within each chemistry class

**TDD Execution Note**: All test tasks below are written to FAIL first, then implementation follows.

### Tests for User Story 2

- [ ] T016 [US2] Unit test for descriptor calculation in tests/unit/test_descriptors.py
- [ ] T017 [US2] Unit test for correlation analysis in tests/unit/test_analysis.py
- [ ] T024 [US2] Unit test for sensitivity analysis in tests/unit/test_sensitivity.py verifying p-value sweep output includes results for {0.01, 0.05, 0.1} (FR-009)

### Implementation for User Story 2

- [ ] T018 [US2] Implement src/descriptors/compute_descriptors.py for octahedral tilting angles, bond-length variance, tolerance factor, unit cell volume (FR-003)
- [ ] T019 [US2] Implement src/analysis/stratify.py for stratification by perovskite chemistry class (oxide, halide, nitride) (FR-014)
- [ ] T020 [US2] Implement src/analysis/correlation.py for Pearson and Spearman correlation with multiple-comparison correction (FR-004)
- [ ] T021 [US2] Extend src/utils/validation.py (T008) with VIF > 5 exclusion logic and causal-language scanner functions (FR-008, FR-007)
- [ ] T022 [US2] Implement src/analysis/sensitivity.py for p-value threshold sensitivity analysis (0.01, 0.05, 0.1) (FR-009)
- [ ] T023 [US2] Add error handling for insufficient sample size after cleaning in src/cleaning/clean_merge.py with message 'Insufficient samples: N < 50'

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regression Modeling & Validation (Priority: P3)

**Goal**: Fit a multiple linear regression model using scikit-learn with 5-fold cross-validation, evaluate performance on a held-out test set, report R² and RMSE, and generate scatter plots with 95% confidence intervals

**Independent Test**: Execute modeling script on pre-processed dataset and verify output includes (i) cross-validated performance metrics, (ii) R² > 0.5 on the held-out test set (SC-003), (iii) RMSE value, (iv) a feature-importance report, and (v) the required scatter plots

**TDD Execution Note**: All test tasks below are written to FAIL first, then implementation follows.

### Tests for User Story 3

- [ ] T025 [US3] Contract test for regression output schema in tests/contract/test_regression_schema.py
- [ ] T026 [US3] Integration test for full modeling pipeline in tests/integration/test_regression.py

### Implementation for User Story 3

- [ ] T027 [US3] Implement src/analysis/regression.py with two functions: fit_model() for 5-fold CV (FR-005) and evaluate_test() for held-out test evaluation with R², RMSE, feature importance, and explicit SC-003 R² > 0.5 pass/fail verification (FR-006, SC-003)
- [ ] T028 [US3] Extend src/utils/validation.py (T008, T021) with scan_causal_language(text) function that fails pipeline on prohibited keywords {cause, leads to, driven by, effect of, result of} (FR-007)
- [ ] T029 [US3] Implement src/analysis/visualize.py for scatter plot generation for top-3 correlated descriptors with 95% CI bands (FR-012)
- [ ] T030 [US3] Generate R² > 0.5 performance target justification citing Smith et al. 2021 to data/results/final_report.md section (FR-015, SC-003)
- [ ] T031 [US3] Generate feature importance report (coefficients magnitude or permutation importance) to data/results/feature_importance.csv (FR-011)
- [ ] T032 [US3] Save all figures as high-resolution PNG files (minimum 300 DPI) to figures/ directory (FR-012)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Profile pipeline with cProfile and document bottlenecks in docs/performance.md
- [ ] T034 [P] Documentation updates: docs/quickstart.md (setup instructions) and docs/api.md (function documentation) with content requirements
- [ ] T035 [P] Additional unit tests for edge cases in tests/unit/test_edge_cases.py covering: API rate limits, invalid geometry, insufficient samples, collinearity detection
- [ ] T036 Run constitution check and document any remaining conflicts in research.md
- [ ] T037 [US3] Document Constitution VII vs FR-010 conflict in research.md and flag for spec amendment (FR-010, Constitution VII)
- [ ] T038 [US3] Generate final results package with all metrics, plots, justifications, and artifact hashes to data/results/final_report.md (FR-015)
- [ ] T039 [P] Execute Reference-Validator Agent on final_report.md citations before publication (Constitution II)
- [ ] T040 [P] Generate content hashes for ALL artifacts (raw data, cleaned data, descriptors, figures, reports) and update state/projects/PROJ-035-exploring-the-correlation-between-crysta.yaml artifact_hashes (Constitution V)

**Checkpoint**: Project ready for research review and publication

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
  - **User Story 2 (P2)**: Depends on US1 cleaned data for descriptor computation
  - **User Story 3 (P3)**: Depends on US2 computed descriptors for regression modeling
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 cleaned data - cannot run in parallel with US1
- **User Story 3 (P3)**: Depends on US2 computed descriptors - cannot run in parallel with US2

### Within Each User Story

- Tests MUST be written to FAIL before implementation (TDD approach)
- Data ingestion before merging before cleaning
- Descriptor computation before correlation analysis
- Correlation analysis before regression modeling
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- T011 and T012 can run in parallel (independent data sources)
- Once Foundational phase completes, tests for each user story can run in parallel
- Different user stories CANNOT be worked on in parallel due to data-flow dependencies

### Resource Constraints

- **RAM**: ~7 GB (aligned with spec.md Assumptions)
- **CPU**: 2 cores (GitHub Actions free tier)
- **Disk**: ~14 GB
- **No GPU**: All tasks must run on CPU-only hardware
- **Time limit**: Entire pipeline ≤ 6 hours

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (after implementation):
Task: "Contract test for merged_perovskite.schema.yaml in tests/contract/test_schema.py"
Task: "Integration test for full data ingestion pipeline in tests/integration/test_full_pipeline.py"

# Launch all ingestion tasks for User Story 1 together (T011, T012 have [P] tag):
Task: "Implement fetch_structures.py for Materials Project API download with ABX₃ filtering (FR-001)"
Task: "Implement fetch_thermal.py for loading literature/NIST thermal conductivity CSVs (FR-010)"
```

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together (after implementation):
Task: "Unit test for descriptor calculation in tests/unit/test_descriptors.py"
Task: "Unit test for correlation analysis in tests/unit/test_analysis.py"
Task: "Unit test for sensitivity analysis in tests/unit/test_sensitivity.py"

# Launch descriptor and correlation tasks:
Task: "Implement compute_descriptors.py for octahedral tilting angles, bond-length variance, tolerance factor, unit cell volume (FR-003)"
Task: "Implement stratification by perovskite chemistry class (oxide, halide, nitride) (FR-014)"
```

---

## Parallel Example: User Story 3

```bash
# Launch all tests for User Story 3 together (after implementation):
Task: "Contract test for regression output schema in tests/contract/test_regression_schema.py"
Task: "Integration test for full modeling pipeline in tests/integration/test_regression.py"

# Launch modeling and visualization tasks:
Task: "Implement regression.py for multiple linear regression with 5-fold CV and held-out test evaluation (FR-005, FR-006)"
Task: "Implement causal-language check scanner for prohibited keywords (FR-007)"
Task: "Implement scatter plot generation for top-3 correlated descriptors with 95% CI bands (FR-012)"
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
3. Add User Story 2 → Test independently → Deploy/Demo (requires US1 data)
4. Add User Story 3 → Test independently → Deploy/Demo (requires US2 descriptors)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (data ingestion)
   - Developer B: Tests for User Story 1
3. After US1 complete:
   - Developer A: User Story 2 (descriptors + correlation)
   - Developer B: Tests for User Story 2
4. After US2 complete:
   - Developer A: User Story 3 (regression + validation)
   - Developer B: Tests for User Story 3
5. Stories complete and integrate sequentially due to data-flow dependencies

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must run on CPU-only CI (2 cores, ~7 GB RAM, ≤6 h) - no GPU, no 8-bit/4-bit quantization, no large LLMs
- **RAM Consistency**: ~7 GB RAM (aligned with spec.md Assumptions, not 5 GB)
- **Data Flow**: T011/T012 must complete before T013; T018 must complete before T020; T027 must complete before T029
- **FR Mapping**: All 15 functional requirements (FR-001 through FR-015) are explicitly addressed in task descriptions
- **Constitution Conflict**: T037 documents the Constitution VII vs FR-010 conflict requiring spec amendment; T012 explicitly excludes MP thermal endpoint in code
- **File Scope**: T008 creates base src/utils/validation.py; T021 and T028 extend same file with additional functions (scope boundaries explicit)
- **Task ID Uniqueness**: All T### IDs are unique (T039 = Reference-Validator, T040 = artifact hashes)