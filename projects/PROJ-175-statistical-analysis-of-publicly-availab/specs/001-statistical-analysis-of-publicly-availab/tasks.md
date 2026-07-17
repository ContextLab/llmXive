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

- [X] T001a Create project directory structure: `projects/PROJ-175-statistical-analysis-of-publicly-availab/code/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/data/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/tests/`
- [X] T001b Create empty `code/__init__.py`, `tests/__init__.py`, and `code/data/__init__.py`
- [X] T001c Create `code/requirements.txt` placeholder and `tests/conftest.py` placeholder

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python project with `code/requirements.txt` (pandas, numpy, scikit-learn, pyarrow, statsmodels, pymc, scipy, requests, tqdm, huggingface_hub)
- [X] T033a [P] Configure linting: Create `ruff.toml` at repository root with specific rules (select = ["E4", "E7", "E9", "F"]) to ensure code quality and reproducibility (Constitution Principle I, FR-001).
- [X] T033b [P] Configure formatting: Create `pyproject.toml` at repository root with black configuration (line-length=88, target-version=py311) to ensure consistent code style (Constitution Principle I, FR-001).
- [X] T004 [P] Setup `data/` directory structure (`raw/`, `processed/`, `final/`) and `code/` module structure
- [X] T005 [P] Implement global random seed pinning to ensure reproducibility. in `code/__init__.py` and `tests/conftest.py`
- [X] T006 [P] Setup memory profiling utility in `code/utils/memory_monitor.py` to enforce a predefined RAM limit.
- [X] T007 Create base data schema definitions in `specs/001-statistical-analysis-of-recipe-data/contracts/`: specifically `dataset.schema.yaml` and `model_output.schema.yaml` (YAML format)
- [X] T038 [P] [US1] Implement `code/data/verify.py` robust error handling: Replace any generic `try/except` blocks with specific HTTP error handling that **raises** on failure (no synthetic fallback) and logs the exact URL and error code to `data/download_errors.log` (Constitution II: Verified Accuracy). **DEPENDS ON**: T002.
- [X] T042 [P] [US1] Implement `code/data/verify.py` schema validation for Counterfactual dataset: Add a strict schema check for the `compatibility_label` column to ensure it contains only binary values (0/1) or valid float scores, failing the pipeline if the schema deviates (FR-001b). **DEPENDS ON**: T002.

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

- [X] T012 [P] [US1] Implement `code/data/verify.py` to check URL availability and schema of Recipe1M embeddings, FlavorDB chemical matrix, and Counterfactual dataset (FR-001b). **Must implement hard fail logic**: if any URL is unreachable or schema (specifically `compatibility_label` column) is missing, raise an error and generate `data/verification_report.json` with status "FAILED".
- [X] T013 [US1] Implement `code/data/download.py` to fetch Recipe1M (streaming), FlavorDB chemical matrix, and Counterfactual datasets from verified URLs (FR-001). **DEPENDS ON**: T012.
- [X] T008a [US1] Implement `code/models/diagnostics.py` step 0a: Perform Power Analysis for Logistic Regression using `statsmodels.stats.power` to calculate required sample size N_logistic for effect size ≥ 0.1 and power 0.8, outputting N_logistic to `data/power_analysis_logistic.json` to determine the downsampled subset size for T019. **Note**: This task must complete AFTER data download to estimate distribution. **DEPENDS ON**: T013.
- [X] T008b [US1] Implement `code/models/diagnostics.py` step 0b: Perform Convergence/Power Analysis for Hierarchical Bayesian Model to determine required sample size N_bayesian for MCMC chain convergence and posterior stability, outputting N_bayesian to `data/power_analysis_bayesian.json` to determine the downsampled subset size for T019. **Note**: This task must complete AFTER data download. **DEPENDS ON**: T013.
- [X] T014 [US1] Implement `code/data/preprocess.py` step 1-2: Normalize ingredient names using **Levenshtein distance threshold = 2 (hard constraint)** mapped explicitly to the **FlavorDB canonical list** (FR-002). **Log the fixed threshold to `data/normalization_config.json`**. **DEPENDS ON**: T013.
- [X] T015 [US1] Implement `code/data/preprocess.py` step 3: Construct global co-occurrence matrix $C$ with log-transform ($\log(C_{ij} + 1)$) (FR-003)
- [X] T016 [US1] Implement `code/data/preprocess.py` step 4: Calculate cosine similarity between **FlavorDB chemical vectors** (fetched in T013) for ingredient pairs to derive the **flavor-profile similarity** feature (FR-004). **Note**: This explicitly overrides the Plan summary's mention of "text embeddings" to ensure the Spec's chemical mechanism is used. **DEPENDS ON**: T014 (Requires normalized IDs to join vectors).
- [X] T017 [US1] Implement `code/data/preprocess.py` step 5: Derive functional role by **stratified binning** of ingredient rank within frequency buckets (excluding co-occurrence frequency) to ensure statistical independence (FR-005). **Rationale**: This method satisfies FR-005's requirement to exclude co-occurrence frequency without over-constraining to a specific statistical technique like OLS residuals.
- [X] T017b [US1] Implement `code/data/preprocess.py` step 5b: Discretize the functional role into categorical labels: **Primary**, **Secondary**, **Garnish** using **stratified binning by tertiles** (fixed method). **Log the method and cutpoints used to `data/role_cutpoints.json`** (FR-005).
- [X] T018 [US1] Implement `code/data/preprocess.py` step 6-7: Handle missing data by imputing missing **categorical role** (from T017b) with 'Unknown' and creating a `role_missing_flag` column; impute missing similarity with **median similarity value** and create a `similarity_missing_flag` column. **Include a verification step**: Calculate correlation between imputed similarity and orthogonalized role to ensure no bias is introduced, logging the result. Join with Counterfactual labels (FR-005, FR-004).
- [X] T019 [US1] Implement `code/data/split.py` to create the **unified** train/test split. **Explicitly downsample the dataset** to a single size N_unified (determined by T008a/T008b, taking the minimum or a unified N) using `pandas.sample` with the specified seed. **Rationale**: This ensures a "Single Source of Truth" (Constitution IV) for all models, aligning with the Plan's single decision point. **DEPENDS ON**: T008a, T008b, T018.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Model Fitting and Validation (Priority: P2)

**Goal**: Fit regularized logistic regression and hierarchical Bayesian models to predict compatibility, controlling for co-occurrence while isolating flavor/role effects.

**Independent Test**: The model fitting process can be run on a downsampled subset to verify coefficients are significant (p < 0.05), VIF confirms no multicollinearity, and sample size supports power analysis.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T021 [P] [US2] Unit test for VIF calculation and Likelihood-Ratio test logic in `tests/unit/test_diagnostics.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement `code/models/diagnostics.py` step 1: Calculate Variance Inflation Factors (VIF) for all predictors; drop predictors if VIF > 5 (FR-007). **DEPENDS ON**: T019 (Data ready).
- [X] T022 [P] [US2] Implement `code/models/fit_logistic.py`: Fit Null Model (frequency only) and Full Model (frequency + similarity + **categorical role** from T017b) with L regularization using the downsampled subset determined by T019 (FR-006). **DEPENDS ON**: T023 (VIF check must pass first).
- [X] T024 [US2] Implement `code/models/diagnostics.py` step 2: Perform Likelihood-Ratio Test (Null vs Full) and record p-value (FR-008)
- [X] T025 [US2] Implement `code/models/fit_bayesian.py`: Implement the full Hierarchical Bayesian model logic (CPU-only NUTS) on the downsampled subset determined by T019. **Include early stopping and convergence checks**: Monitor R-hat and effective sample size (ESS); if convergence is not reached within a reasonable time limit, the task must fail loudly and report the specific diagnostic failure rather than proceeding with unreliable posterior estimates (FR-002 context: Hierarchical Bayesian model fitting). **DEPENDS ON**: T019.
- [X] T026 [US2] Implement `code/models/diagnostics.py` step 3: Run **Post-Hoc Power Validation** to verify the achieved power for effect size ≥ 0.1 given the actual sample size used and model convergence metrics (FR-002 context: Hierarchical Bayesian model fitting)
- [X] T040 [US2] Implement `code/models/diagnostics.py` step 3b: **Multicollinearity Resolution**: If VIF > 5 is detected for the 'Functional Role' predictor (from T023), automatically drop the 'Functional Role' variable from the Full Model and re-run the Likelihood-Ratio Test, documenting the exclusion in the final report (FR-007). **Deliverable**: Update `data/model_comparison.json` with a `dropped_predictors` field and save results to `data/lrt_result_vif_corrected.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User User Story 3 - Evaluation and Reporting of Generalization (Priority: P3)

**Goal**: Evaluate models on held-out test set, calculate metrics, and generate report comparing full model vs baseline.

**Independent Test**: The evaluation script runs on the test split and produces a summary table and calibration plot, demonstrating whether the full model achieves a statistically significant improvement.

**⚠️ GATE**: Phase 5 tasks depend on the completion of Phase 4 (T023, T024, T025, T026, T040) and Phase 2 (T038, T042).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for evaluation metrics schema in `tests/contract/test_metrics.py`
- [X] T028 [P] [US3] Integration test for report generation in `tests/integration/test_report.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/evaluation/metrics.py`: Calculate AUC, Precision, Recall, and generate Calibration Plot for both models (FR-009)
- [X] T030 [US3] Implement `code/evaluation/report.py` step 1: Perform **DeLong's test (mandatory method)** to test hypothesis $\Delta AUC \ge \text{a clinically meaningful threshold}$. **Explicitly calculate the confidence interval for the delta** and compare against frequency-only baseline, generating p-value and 95% CI. **Save results to `data/auc_delta_metrics.json`** (FR-010).
- [X] T031 [US3] Implement `code/evaluation/report.py` step 2: Map LRT p-value to SC-001 and VIF scores to SC-003 in final summary. **DEPENDS ON**: T023 (VIF), T024 (LRT), T025 (Bayesian Results) (FR-010)
- [X] T032 [US3] Implement `code/evaluation/report.py` step 3: Generate final report stating whether "flavor and role predict compatibility beyond frequency" is supported with specific evidence (p-values, AUC delta, CI). **DEPENDS ON**: T042 (Verified Accuracy Gate), T025 (Convergence Gate).
- [X] T042 [US3] **Gate**: Verify Constitution II Compliance: Ensure tasks T038, T042 are completed and `data/verification_report.json` indicates success before allowing final report generation (T032). This task explicitly links the 'Verified Accuracy' gate to the completion of gap-resolution tasks. **DEPENDS ON**: T038, T042.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

**⚠️ GATE**: Phase N tasks depend on the completion of all User Story implementations (Phases 3, 4, 5).

- [X] T033a [P] Documentation updates: Update `docs/research.md` with 'Methodology' section (include power analysis N values).
- [X] T033b [P] Documentation updates: Update `docs/research.md` with 'Results' section (include model coefficients, VIF, AUC delta).
- [X] T033c [P] Documentation updates: Update `docs/research.md` with 'Limitations' section (include sampling constraints).
- [X] T033d [P] Documentation updates: Update `docs/quickstart.md` with 'Environment Setup' section (include requirements.txt install).
- [X] T033e [P] Documentation updates: Update `docs/quickstart.md` with 'Data Pipeline' and 'Model Execution' sections (include streaming instructions and runtime estimate methodology).
- [X] T034 [P] Code cleanup: Implement streaming for Recipe1M and chunked processing for FlavorDB in `code/data/download.py` and `code/data/preprocess.py` to ensure Peak RAM < 6GB. **Deliverable**: Reference `data/memory_profile.json` produced by T037. **Linked to**: FR-001, US-1. **Note**: T037 is the primary implementation of this logic.
- [X] T035a [P] Additional unit tests: Add `tests/unit/test_preprocess.py::test_levenshtein_normalization` and `tests/unit/test_diagnostics.py::test_vif_calculation` to verify FR-002 and FR-007 logic.
- [X] T036 [P] Run `quickstart.md` validation to ensure full pipeline execution ≤ 6 hours. **Execute**: `python code/validate_runtime.py` which runs the pipeline and measures time. **Deliverable**: Generate `data/ci_validation_report.json` containing the measured runtime and a boolean `passed` field.

---

## Phase N+1: Revision & Gap Resolution (Addressing Review Concerns)

**Purpose**: Address specific gaps identified in the analysis phase regarding data robustness, error handling, and reproducability.

- [X] T037 [US1] Implement `code/data/preprocess.py` explicit streaming logic: Refactor T013 to use `datasets.load_dataset(..., streaming=True)` for Recipe1M and `itertools.islice` for controlled downsampling, ensuring the full dataset is never loaded into RAM, and log the exact sampling ratio and seed used (Constitution II: Verified Accuracy). **Deliverable**: `data/memory_profile.json`. **Status**: Active.
- [X] T045 [US2] Implement `code/models/fit_bayesian.py` early stopping and convergence checks: (Note: Logic integrated into T025; this task serves as a reminder to verify convergence in T025). **DEPENDS ON**: T025.
- [X] T041 [US3] **Gate**: Verify Constitution II Compliance: Ensure tasks T038, T042 are completed and `data/verification_report.json` indicates success before allowing final report generation (T032). This task explicitly links the 'Verified Accuracy' gate to the completion of gap-resolution tasks.

---

## Phase N+2: Final Execution Validation

**Purpose**: Ensure the entire pipeline runs successfully on the CI runner and produces the final report.

- [ ] T043 [P] Execute the full pipeline on the GitHub Actions runner using the `quickstart.md` script to verify end-to-end execution. **Deliverable**: `data/final_execution_log.json` containing runtime, peak memory, and success status. **DEPENDS ON**: All Phase N and N+1 tasks.
- [ ] T044 [P] Generate the final `docs/final_report.md` by aggregating results from `data/auc_delta_metrics.json`, `data/lrt_result_vif_corrected.json`, and `data/final_execution_log.json`. **DEPENDS ON**: T043. <!-- FAILED: unspecified -->

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase N+1)**: Must be completed before final deployment to ensure all analysis gaps are closed
- **Final Execution (Phase N+2)**: Depends on all previous phases being complete

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
- Revision tasks (T037-T041) can be implemented in parallel with Polish tasks if they target different files

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
- **Critical**: Tasks T038, T042 are mandatory to address the "Fabrication Gate" and "Verified Accuracy" requirements. They must be completed before T032.
- **Critical**: T019 creates a single unified sample size for both models.
- **Critical**: T014 uses text for normalization with fixed threshold=2; T016 uses chemical vectors for similarity (overrides Plan summary).
- **Critical**: T022 and T025 use categorical role (Primary/Secondary/Garnish) as per Spec FR-005.
- **Critical**: T023 (VIF) must precede T022 (Fit Logistic).
- **Critical**: T025 includes convergence checks (R-hat, ESS).
- **Critical**: T030 uses DeLong's test for AUC comparison.
- **Critical**: T037 is active and produces `data/memory_profile.json`.