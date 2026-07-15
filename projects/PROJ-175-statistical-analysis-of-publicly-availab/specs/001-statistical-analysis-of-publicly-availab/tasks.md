# Tasks: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

**Input**: Design documents from `/specs/001-statistical-analysis-of-recipe-data/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [ ] T001a Create project directory structure: `projects/PROJ-175-statistical-analysis-of-publicly-availab/code/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/data/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/tests/`
- [X] T001b Create empty `code/__init__.py`, `tests/__init__.py`, and `code/data/__init__.py`
- [X] T001c Create `code/requirements.txt` placeholder and `tests/conftest.py` placeholder

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.11 project with `code/requirements.txt` (pandas, numpy, scikit-learn, pyarrow, statsmodels, pymc, scipy, requests, tqdm, huggingface_hub)
- [ ] T003 [P] Configure linting (flake8/ruff) and formatting (black) tools
- [ ] T004 Setup `data/` directory structure (`raw/`, `processed/`, `final/`) and `code/` module structure
- [X] T005 [P] Implement global random seed pinning (42) in `code/__init__.py` and `tests/conftest.py`
- [X] T006 [P] Setup memory profiling utility in `code/utils/memory_monitor.py` to enforce 6 GB RAM limit
- [ ] T007 Create base data schema definitions in `specs/001-statistical-analysis-of-recipe-data/contracts/` (dataset.schema.yaml, model_output.schema.yaml)
- [X] T008a [P] [US1] Implement `code/models/diagnostics.py` step 0a: Perform Power Analysis for Logistic Regression using `statsmodels.stats.power` to calculate required sample size N_logistic for effect size ≥ 0.1, outputting N_logistic to `data/power_analysis_logistic.json` to determine the downsampled subset size for T022
- [X] T008b [P] [US2] Implement `code/models/diagnostics.py` step 0b: Perform Convergence/Power Analysis for Hierarchical Bayesian Model to determine required sample size N_bayesian for MCMC chain convergence and posterior stability, outputting N_bayesian to `data/power_analysis_bayesian.json` to determine the downsampled subset size for T025

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest Recipe1M, FlavorDB, and Counterfactual datasets; normalize ingredients; construct co-occurrence matrix and chemical similarity vectors within GitHub Actions constraints.

**Independent Test**: The pipeline can be executed in isolation to produce a single, validated CSV file containing pairs of ingredients with their log-transformed co-occurrence counts, cosine similarity scores, and functional role labels, without requiring the model fitting step.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [X] T011 [P] [US1] Integration test for full pre-processing pipeline in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data/verify.py` to check URL availability and schema of Recipe1M embeddings, FlavorDB chemical matrix, and Counterfactual dataset (FR-001b)
- [X] T013 [US1] Implement `code/data/download.py` to fetch Recipe1M (streaming), FlavorDB chemical matrix, and Counterfactual datasets from verified URLs (FR-001)
- [X] T014 [US1] Implement `code/data/preprocess.py` step 1-2: Normalize ingredient names using **Levenshtein distance threshold ≤ 2** only (per spec FR-002) to map to FlavorDB canonical IDs; **DO NOT** use text embeddings for this step (removed unverified dependency)
- [X] T015 [US1] Implement `code/data/preprocess.py` step 3: Construct global co-occurrence matrix $C$ with log-transform ($\log(C_{ij} + 1)$) (FR-003)
- [X] T016 [US1] Implement `code/data/preprocess.py` step 4: Calculate cosine similarity between **FlavorDB chemical vectors** (fetched in T013) for ingredient pairs to derive the **flavor-profile similarity** feature (FR-004). **Note**: This uses chemical vectors, NOT text embeddings.
- [X] T017 [US1] Implement `code/data/preprocess.py` step 5: Derive orthogonalized Functional Role by regressing **raw** rank on global log-frequency using OLS, then extracting the residuals as the continuous 'Functional Role' predictor to ensure orthogonality to Frequency (FR-005)
- [X] T017b [US1] Implement `code/data/preprocess.py` step 5b: Discretize the continuous residuals from T017 into categorical labels: **Primary** (top [deferred] of residuals), **Secondary** (middle [deferred]), **Garnish** (bottom [deferred]) to match the Key Entity definition (FR-005)
- [X] T018 [US1] Implement `code/data/preprocess.py` step 6-7: Handle missing data by imputing missing **categorical role** (from T017b) with 'Unknown' and creating a `role_missing_flag` column; impute missing similarity with median + flag; join with Counterfactual labels (FR-005, FR-004) <!-- FAILED: unspecified -->
- [X] T019 [US1] Implement `code/data/split.py` to create train/test splits ensuring stratified sampling by ingredient frequency (using subset size N determined by T008a/T008b)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Model Fitting and Validation (Priority: P2)

**Goal**: Fit regularized logistic regression and hierarchical Bayesian models to predict compatibility, controlling for co-occurrence while isolating flavor/role effects.

**Independent Test**: The model fitting process can be run on a downsampled subset to verify coefficients are significant (p < 0.05), VIF confirms no multicollinearity, and sample size supports power analysis.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T021 [P] [US2] Unit test for VIF calculation and Likelihood-Ratio test logic in `tests/unit/test_diagnostics.py`

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement `code/models/fit_logistic.py`: Fit Null Model (frequency only) and Full Model (frequency + similarity + role) with L2 regularization using the downsampled subset of size N_logistic determined by T008a (FR-006)
- [X] T023 [US2] Implement `code/models/diagnostics.py` step 1: Calculate Variance Inflation Factors (VIF) for all predictors; drop predictors if VIF > 5 (FR-007)
- [X] T024 [US2] Implement `code/models/diagnostics.py` step 2: Perform Likelihood-Ratio Test (Null vs Full) and record p-value (FR-008)
- [ ] T025 [P] [US2] Implement `code/models/fit_bayesian.py`: Fit Hierarchical Bayesian model using PyMC (CPU-only NUTS) on the downsampled subset of size N_bayesian determined by T008b (FR-002)
- [X] T026 [US2] Implement `code/models/diagnostics.py` step 3: Run **Post-Hoc Power Validation** to verify the achieved power for effect size ≥ 0.1 given the actual sample size used and model convergence metrics (FR-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User User Story 3 - Evaluation and Reporting of Generalization (Priority: P3)

**Goal**: Evaluate models on held-out test set, calculate metrics, and generate report comparing full model vs baseline.

**Independent Test**: The evaluation script runs on the test split and produces a summary table and calibration plot, demonstrating whether the full model achieves a statistically significant improvement.

**⚠️ GATE**: Phase 5 tasks depend on the completion of Phase 4 (T023, T024, T025, T026).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for evaluation metrics schema in `tests/contract/test_metrics.py`
- [X] T028 [P] [US3] Integration test for report generation in `tests/integration/test_report.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/evaluation/metrics.py`: Calculate AUC, Precision, Recall, and generate Calibration Plot for both models (FR-009)
- [X] T030 [US3] Implement `code/evaluation/report.py` step 1: Perform DeLong's test or bootstrap to test hypothesis $\Delta AUC \ge 0.05$ and compare against frequency-only baseline, generating p-value and 95% CI (FR-010)
- [X] T031 [US3] Implement `code/evaluation/report.py` step 2: Map LRT p-value to SC-001 and VIF scores to SC-003 in final summary. **DEPENDS ON**: T023 (VIF), T024 (LRT) (FR-010)
- [X] T032 [US3] Implement `code/evaluation/report.py` step 3: Generate final report stating whether "flavor and role predict compatibility beyond frequency" is supported with specific evidence (p-values, AUC delta, CI)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

**⚠️ GATE**: Phase N tasks depend on the completion of all User Story implementations (Phases 3, 4, 5).

- [X] T033a [P] Documentation updates: Update `docs/research.md` with specific sections: 'Methodology' (include power analysis N values), 'Results' (include model coefficients, VIF, AUC delta), 'Limitations' (include sampling constraints)
- [ ] T033b [P] Documentation updates: Update `docs/quickstart.md` with specific sections: 'Environment Setup' (include requirements.txt install), 'Data Pipeline' (include streaming instructions), 'Model Execution' (include runtime estimates)
- [ ] T034 Code cleanup and refactoring for memory efficiency
- [ ] T035 Performance optimization for data streaming in `code/data/download.py`
- [ ] T036 [P] Additional unit tests in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation to ensure full pipeline execution ≤ 6 hours on CI

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (processed data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US2 (model results)

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
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Integration test for full pre-processing pipeline in tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/verify.py to check URL availability"
Task: "Implement code/data/download.py to fetch datasets"
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