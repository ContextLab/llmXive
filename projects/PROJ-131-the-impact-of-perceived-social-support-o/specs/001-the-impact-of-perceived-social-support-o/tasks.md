# Tasks: The Impact of Perceived Social Support on Resilience to Online Harassment

**Input**: Design documents from `/specs/001-social-support-resilience/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**⚠️ CRITICAL METHODOLOGICAL DEVIATION**: 
This implementation follows the **single-dataset approach** (Cyberbullying Survey 2021 only) as defined in `plan.md`. 
The **Synthetic Cohort** methodology (FR-001, FR-002, US-1) from `spec.md` is **NOT implemented** in this phase due to methodological invalidity identified in the plan. 
**Kickback Required**: The spec owner must either accept the single-dataset approach or provide a valid method for multi-dataset interaction analysis. 
FR-001, FR-002, US-1, and SC-001 are **Deferred/Kickback** until the spec is amended.

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

- [ ] T001 Create project structure per implementation plan (`code/data`, `code/analysis`, `code/config`, `code/tests`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies (`requirements.txt`: pandas, numpy, scikit-learn, statsmodels, scipy, pyyaml)
- [ ] T003 [P] Configure linting (flake8/ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `config/scales.yaml` defining standard scoring weights for CES-D, GAD-7, and PCL-5. 
      **Sources**: CES-D Manual (1977, CDC), GAD-7 Scoring Guide (2006, APA), PCL-5 User Guide (2013, NCBI). 
      **Conditional**: PCL-5 scoring is conditional on data availability; log E-MISSING-001 if items are absent.
- [ ] T005 [P] Implement `tests/test_scales.py` with unit tests verifying scoring logic matches validated scale definitions
- [ ] T006 [P] Setup `code/data/ingestion.py` skeleton with read-only raw data validation logic
- [ ] T007 Create `code/data/cohort.py` skeleton for constructing the single-dataset analysis cohort
- [ ] T008 [P] Configure `main_pipeline.py` entry point to orchestrate modular steps
- [ ] T009 [P] Setup environment configuration management for data paths and random seeds
- [ ] T009a [P] Create `config/seeds.yaml` to define random seeds for reproducibility (e.g., `random_seed: 42`, `bootstrap_seed: 123`). This file is referenced by T013a and T022.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Cohort Construction (Priority: P1) 🎯 MVP

**⚠️ METHODOLOGICAL DEVIATION**: This phase implements the **single-dataset approach** (Cyberbullying Survey 2021 only). 
The **Synthetic Cohort** approach (FR-001, FR-002, US-1) from `spec.md` is **NOT implemented**. 
**Kickback Required**: FR-001, FR-002, US-1, and SC-001 are deferred until the spec is amended.

**Goal**: Ingest the Cyberbullying Survey 2021 dataset, validate variables, calculate standardized scores, and produce a clean analysis cohort.

**Independent Test**: The system can be tested by running the ingestion script alone and verifying the output CSV contains no `NaN` values in critical columns and that score calculations match the `config/scales.yaml` definitions.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data schema in `tests/contract/test_analysis_cohort_schema.py`
- [ ] T011 [P] [US1] Unit test for CES-D/GAD-7 scoring logic in `tests/unit/test_scale_scoring.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/data/ingestion.py` to fetch and load the **Cyberbullying Survey 2021 dataset ONLY**. 
      **Source URL**: `https://osf.io/...` (Replace with actual URL from plan.md or data repository). 
      **Note**: GSS 2022 is NOT fetched (see Methodological Deviation note).
- [ ] T013 [US1] Implement `code/data/preprocessing.py` to handle missing values and apply scale scoring.
      **Rule**: Use listwise deletion if >5% missing in a variable; otherwise, use MICE (m=5, max_iter=10, random_state=42) from `config/seeds.yaml`.
- [ ] T013a [US1] Implement `code/data/preprocessing.py` to apply scale scoring from `config/scales.yaml`.
      **Conditional**: If PCL-5 items are missing, skip PCL-5 scoring and log E-MISSING-001.
- [ ] T014 [US1] Implement `code/data/cohort.py` to filter for valid cases and construct the final **analysis_cohort** DataFrame (single-dataset).
- [ ] T015 [US1] Add validation checks in `code/data/cohort.py` to ensure sufficient variance in Harassment Exposure.
      **Metric**: Check if Standard Deviation (SD) > 0.5 and N > 30. Also check for multicollinearity (VIF < 5). Warn if checks fail.
- [ ] T016 [US1] Save the final **analysis_cohort** to `data/results/analysis_cohort.csv`.
      **Note**: Artifact renamed from 'synthetic_cohort.csv' to reflect single-dataset methodology.
- [ ] T017 [US1] Add logging for data ingestion steps and missing value handling.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. 
**SC-001 Status**: Deferred/Kickback. The original SC-001 (covariate balance ≤ 0.1) is untestable in this phase. 
A new check (T015) for internal data variance is implemented as a proxy for data quality.

---

## Phase 4: User Story 2 - Interaction Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Fit robust linear regression models (OLS with HCSE) for Depression, Anxiety, and PTSD (if available) testing the interaction between Social Support and Harassment Exposure, with bootstrapped CIs.

**Independent Test**: The system can be tested by running the regression module on the clean cohort and verifying the output table contains interaction coefficients, p-values, and 95% bootstrap CIs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for regression results schema in `tests/contract/test_regression_results_schema.py`
- [ ] T019 [P] [US2] Unit test for bootstrapping logic in `tests/unit/test_bootstrap_ci.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/analysis/models.py` to fit OLS models with heteroskedasticity-consistent standard errors.
- [ ] T021 [US2] Implement `code/analysis/models.py` logic to include the interaction term `SocialSupport:HarassmentExposure`.
- [ ] T022 [US2] Implement `code/analysis/models.py` to compute 95% bias-corrected bootstrapped CIs (1,000 resamples) using **BCa** method from `statsmodels.stats.bootstrap`.
      **Seed**: Use `bootstrap_seed` from `config/seeds.yaml`.
- [ ] T023 [US2] Implement fallback logic in `code/analysis/models.py` to skip PCL-5 model if items are missing (log E-MISSING-001).
- [ ] T024 [US2] Implement Benjamini-Hochberg correction in `code/analysis/results.py` for the family of outcome tests.
- [ ] T025 [US2] Save regression results to `data/results/regression_results.csv`.
- [ ] T026 [US2] Add error handling for non-convergence (fallback to standard OLS without robust SEs).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Robustness Checks (Priority: P3)

**Goal**: Execute sensitivity analyses by varying harassment exposure definition (binary vs. continuous) and stratifying by platform type (if available).

**Independent Test**: The system can be tested by running the sensitivity script and verifying the output table shows coefficient shifts across scenarios.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for sensitivity results schema in `tests/contract/test_sensitivity_results_schema.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `code/analysis/sensitivity.py` to re-run models with continuous harassment severity.
- [ ] T029 [US3] Implement `code/analysis/sensitivity.py` logic to stratify by platform type if `Platform` column exists.
      **Fallback**: Skip stratification and log E-SKIP-001 if unique platform count < 2.
- [ ] T030 [US3] Implement `code/analysis/sensitivity.py` to compare interaction coefficients against the baseline model.
- [ ] T031 [US3] Generate a summary report table in `data/results/sensitivity_analysis.csv`.
- [ ] T032 [US3] Add logging for sensitivity scenario variations and data availability checks.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Update `main_pipeline.py` to chain all phases: Ingestion → Modeling → Sensitivity → Reporting
- [ ] T034 Code cleanup and refactoring in `code/analysis/` to ensure modularity
- [ ] T035 Performance optimization: Verify bootstrapping completes within 6 hours on 2-core CPU
- [ ] T036 [P] Additional unit tests for edge cases (empty datasets, missing columns) in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation to ensure pipeline executes end-to-end
- [ ] T038 Update `research.md` with placeholder for results interpretation (associational only)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
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
Task: "Contract test for data schema in tests/contract/test_analysis_cohort_schema.py"
Task: "Unit test for CES-D/GAD-7 scoring logic in tests/unit/test_scale_scoring.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/ingestion.py to fetch and load the Cyberbullying Survey 2021 dataset"
Task: "Implement code/data/preprocessing.py to handle missing values and apply scale scoring"
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
- **Critical Methodological Note**: This implementation follows the single-dataset (Cyberbullying Survey) approach. The "Synthetic Cohort" approach from the original spec (FR-001, FR-002, US-1) is **NOT implemented** and is flagged for **Kickback**. 
- **Kickback Required**: The spec owner must review the "METHODOLOGICAL DEVIATION" note in Phase 3 and either accept the single-dataset approach or provide a valid method for multi-dataset interaction analysis. FR-001, FR-002, US-1, and SC-001 are deferred until the spec is amended.