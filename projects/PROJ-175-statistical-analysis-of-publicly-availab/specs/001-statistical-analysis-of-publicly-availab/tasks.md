---
description: "Task list template for feature implementation"
---

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

- [X] T001a Create project directory structure: `projects/PROJ-175-statistical-analysis-of-publicly-availab/code/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/data/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/tests/`. **Verification**: Verify existence of directories via `os.path.isdir` and log to `data/setup_log.json`.
- [X] T001b Create empty `code/__init__.py`, `tests/__init__.py`, and `code/data/__init__.py`
- [X] T001c Create `code/requirements.txt` placeholder and `tests/conftest.py` placeholder

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python project with `code/requirements.txt` (pandas, numpy, scikit-learn, pyarrow, statsmodels, pymc, scipy, requests, tqdm, huggingface_hub)
- [X] T033a [P] Configure linting: Create `ruff.toml` at repository root with specific rules (select = ["E", "E7", "E9", "F"]) to ensure code quality and reproducibility (Constitution Principle I, FR-001).
- [X] T033b [P] Configure formatting: Create `pyproject.toml` at repository root with black configuration (line-length=88, target-version=py311) to ensure consistent code style (Constitution Principle I, FR-001).
- [X] T004 [P] Setup `data/` directory structure (`raw/`, `processed/`, `final/`) and `code/` module structure
- [X] T005 [P] Implement global random seed pinning. **Deliverable**: Create `code/__init__.py` with `seed = 42` and `tests/conftest.py` with `@pytest.fixture(autouse=True) def set_seed()`.
- [X] T006 [P] Setup memory profiling utility in `code/utils/memory_monitor.py` to enforce a predefined RAM limit. **Deliverable**: Create `check_limit(limit_mb=6144)` function that raises `MemoryError` if exceeded, and log to `data/memory_profile.json`.
- [X] T007 Create base data schema definitions in `specs/001-statistical-analysis-of-recipe-data/contracts/`: specifically `dataset.schema.yaml` and `model_output.schema.yaml` (YAML format). **Deliverable**: Create schemas using Pydantic or JSON Schema, and add script `code/utils/validate_schema.py` that loads these and validates a sample row.
- [X] T038 [P] [US1] Implement `code/data/verify.py` robust error handling: Replace any generic `try/except` blocks with specific HTTP error handling that **raises** on failure (no synthetic fallback) and logs the exact URL and error code to `data/download_errors.log` (Constitution II: Verified Accuracy). **DEPENDS ON**: T002.
- [X] T042 [P] [US1] Implement `code/data/verify.py` schema validation for Counterfactual dataset: Add a strict schema check for the `compatibility_label` column to ensure it contains only binary values (0/1) or valid float scores, failing the pipeline if the schema deviates (FR-001b). **DEPENDS ON**: T002.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest Recipe1M, FlavorDB, and Counterfactual datasets; normalize ingredients; construct co-occurrence matrix and chemical similarity vectors within GitHub Actions constraints.

**Independent Test**: The pipeline can be executed in isolation to produce a single, validated CSV file containing pairs of ingredients with their log-transformed co-occurrence counts, cosine similarity scores, and functional role labels, without requiring the model fitting step.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`. **Deliverable**: Add `tests/contract/test_data_schema.py::test_recipe1m_schema_matches_yaml` which loads `dataset.schema.yaml` and asserts columns match.
- [X] T011 [P] [US1] Integration test for full pre-processing pipeline in `tests/integration/test_pipeline.py`. **Deliverable**: Add `tests/integration/test_pipeline.py::test_full_pipeline_produces_final_features` which runs `preprocess.py` on a mock 100-row dataset and asserts `data/processed/final_features.parquet` exists with >0 rows.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data/verify.py` to check URL availability and schema of Recipe1M embeddings, FlavorDB chemical matrix, and Counterfactual dataset (FR-001b). **Must implement hard fail logic**: if any URL is unreachable or schema (specifically `compatibility_label` column) is missing, raise an error and generate `data/verification_report.json` with status "FAILED". **Deliverable**: Generate `data/verification_report.json` with keys: `status` (PASS/FAIL), `timestamp`, `errors` (list of dicts with `url`, `code`, `message`).
- [X] T046 [US1] Implement `code/data/verify.py` strict URL verification: Add a pre-flight check that attempts to `HEAD` the specific Recipe1M and FlavorDB URLs defined in `data/verification_report.json`. If the URL returns 403/404 or times out, raise a `DataUnavailableError` with the specific URL and error code to prevent silent fallbacks. **Rationale**: Addresses the "Hard Fail" requirement from T038 by ensuring the download task itself validates availability before attempting a full fetch. **DEPENDS ON**: T012.
- [X] T013 [US1] Implement `code/data/download.py` to fetch Recipe1M (streaming), FlavorDB chemical matrix, and Counterfactual datasets from verified URLs (FR-001). **DEPENDS ON**: T012, T046.
- [X] T008 [US1] Implement `code/models/diagnostics.py` step 0: Perform a **unified** power analysis for Logistic Regression and Hierarchical Bayesian Model using `statsmodels.stats.power` to calculate a single required sample size N_unified for effect size ≥ 0.1 and power 0.8, outputting N_unified to `data/power_analysis.json`. **Note**: This task must complete AFTER data download to estimate distribution. **Rationale**: Consolidates T008a/T008b to ensure a "Single Source of Truth" for sample size. **DEPENDS ON**: T013.
- [X] T014 [US1] Implement `code/data/preprocess.py` step 1-2: Normalize ingredient names using **Levenshtein distance threshold = 2 (hard constraint)** mapped explicitly to the **FlavorDB canonical list** (FR-002). **Log the fixed threshold to `data/normalization_config.json`** with schema: `{"threshold": 2, "method": "levenshtein", "timestamp": "...", "mapped_count": int, "unmapped_count": int}`. **Explicitly depends on schema validation logic established in T012/T007**. **DEPENDS ON**: T007, T012, T013.
- [X] T049 [US1] Implement `code/data/preprocess.py` step 5 (Zero-occurrence handling): Define epsilon value for log-transform ($\log(C_{ij} + \epsilon)$) to handle zero counts and log the count of zero pairs. **Deliverable**: Output `{"epsilon": float, "zero_pair_count": int, "total_pairs": int}` to `data/zero_handling_log.json`. **DEPENDS ON**: T013.
- [X] T015 [US1] Implement `code/data/preprocess.py` step 3: Construct global co-occurrence matrix $C$ with log-transform ($\log(C_{ij} + \epsilon)$) using epsilon defined in T049 (FR-003). **Output**: `data/processed/co_occurrence_matrix.parquet`. **DEPENDS ON**: T049, T013.
- [X] T016 [US1] Implement `code/data/preprocess.py` step 4: Calculate cosine similarity between **FlavorDB chemical vectors** (fetched in T013) for ingredient pairs to derive the **flavor-profile similarity** feature (FR-004). **Explicitly depends on T014's FlavorDB canonical mapping and T013's chemical vectors**. **Output**: `data/processed/flavor_similarity.parquet`. **DEPENDS ON**: T013, T014.
- [X] T017 [US1] Implement `code/data/preprocess.py` step 5: Derive functional role by **orthogonalized positional rank** (regress ingredient rank on global log-frequency and use **residuals**) to ensure statistical independence from co-occurrence frequency (FR-005, Plan Phase 1 Step 4). **Output**: `data/processed/ingredient_roles_residuals.parquet` with columns `ingredient_id`, `rank`, `frequency`, `residual_role`. **DEPENDS ON**: T015.
- [X] T017b [US1] Implement `code/data/preprocess.py` step 5b: Discretize the **residual role** (from T017) into categorical labels: **Primary**, **Secondary**, **Garnish** using **tertiles of the residuals** (fixed method). **Log the method and cutpoints used to `data/role_cutpoints.json`** (FR-005). **Output**: `data/processed/ingredient_roles_binned.parquet`. **Deliverable**: Log `{"method": "tertiles", "cutpoints": [float, float], "labels": ["Primary", "Secondary", "Garnish"]}` to `data/role_cutpoints.json`. **DEPENDS ON**: T017.
- [X] T018 [US1] Implement `code/data/preprocess.py` step 6-7: Handle missing data by imputing missing **categorical role** (from T017b) with 'Unknown' and creating a `role_missing_flag` column; impute missing similarity (T016) with **median similarity value** and create a `similarity_missing_flag` column. **Include a verification step**: Calculate correlation between imputed similarity and orthogonalized role to ensure no bias is introduced, logging the result to `data/missing_data_bias_log.json` with keys `correlation_value`, `p_value`, `bias_detected` (bool). Join with Counterfactual labels (FR-005, FR-004). **Input**: `data/processed/ingredient_roles_binned.parquet`, `data/processed/flavor_similarity.parquet`. **Output**: `data/processed/final_features.parquet`. **DEPENDS ON**: T013, T017b, T016.
- [X] T019 [US1] Implement `code/data/split.py` to create the **unified** train/test split. **Explicitly downsample the dataset** to N_unified (determined by T008) using `pandas.sample` with the specified seed. **Rationale**: This ensures a "Single Source of Truth" (Constitution IV) for all models. **Deliverable**: Write `N_unified` to `data/split_config.json` with keys `n_logistic`, `n_bayesian`, `n_unified`, `seed`. **DEPENDS ON**: T008, T018.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Model Fitting and Validation (Priority: P2)

**Goal**: Fit regularized logistic regression and hierarchical Bayesian models to predict compatibility, controlling for co-occurrence while isolating flavor/role effects.

**Independent Test**: The model fitting process can be run on a downsampled subset to verify coefficients are significant (p < 0.05), VIF confirms no multicollinearity, and sample size supports power analysis.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T021 [P] [US2] Unit test for VIF calculation and Likelihood-Ratio test logic in `tests/unit/test_diagnostics.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement `code/models/diagnostics.py` step 1: Calculate Variance Inflation Factors (VIF) for all predictors; drop predictors if VIF > 5 (FR-007). **Output**: `data/vif_scores_initial.json` (MUST save before any dropping). **Deliverable**: Output `{"predictors": {"name": float}, "dropped": [], "max_vif": float}` to `data/vif_scores_initial.json`. **DEPENDS ON**: T019 (Data ready).
- [X] T040 [US2] Implement `code/models/diagnostics.py` step 3b: **Multicollinearity Resolution**: If VIF > 5 is detected for the 'Functional Role' predictor (from T023), automatically drop the 'Functional Role' variable from the Full Model and re-run the Likelihood-Ratio Test, documenting the exclusion in the final report (FR-007). **Deliverable**: Update `data/model_comparison.json` with a `dropped_predictors` field and save results to `data/lrt_result_vif_corrected.json`. **DEPENDS ON**: T023 (VIF Check).
- [X] T022 [P] [US2] Implement `code/models/fit_logistic.py`: Fit Null Model (frequency only) and Full Model (frequency + similarity + **categorical role** from T017b) with **L2 regularization** using the downsampled subset determined by T019 (FR-006). **Explicitly set regularization parameter to 'l2'**. **Output**: `data/final/logistic_results.json`. **DEPENDS ON**: T018, T023, T040.
- [X] T024 [US2] Implement `code/models/diagnostics.py` step 2: Perform Likelihood-Ratio Test (Null vs Full) and record p-value (FR-008). **DEPENDS ON**: T022.
- [X] T050 [P] [US2] Implement `code/models/fit_bayesian.py` CPU enforcement: Add a runtime check that detects if a CUDA-enabled device is available. If available, log a warning and **force CPU execution** (Do NOT switch to GPU) to ensure the "CPU-only" constraint is strictly honored. **Rationale**: Addresses the "Compute Feasibility" rule by ensuring the execution stage knows the task is strictly CPU-bound and no GPU offload occurs. **Deliverable**: Log to `data/gpu_detection_log.json` with `gpu_available`: bool, `action`: 'CPU_FORCED', `warning_message`: str. **DEPENDS ON**: T019.
- [X] T025 [US2] Implement `code/models/fit_bayesian.py`: Implement the full Hierarchical Bayesian model logic (CPU-only NUTS) on the downsampled subset determined by T019. **Include early stopping and convergence checks**: Monitor R-hat and effective sample size (ESS); if convergence is not reached within a reasonable time limit, the task must fail loudly and report the specific diagnostic failure rather than proceeding with unreliable posterior estimates (FR-002 context: Hierarchical Bayesian model fitting). **Output**: `data/final/bayesian_results.json`. **Deliverable**: If R-hat > 1.05 or ESS < 200, raise `ConvergenceError` and log `data/bayesian_convergence_log.json` with `status`: 'FAILED', `metrics`: {R_hat, ESS}. **DEPENDS ON**: T019, T050.
- [X] T026 [US2] Implement `code/models/diagnostics.py` step 3: Run **Post-Hoc Power Validation** to verify the achieved power for effect size ≥ 0.1 given the actual sample size used and model convergence metrics (FR-002 context: Hierarchical Bayesian model fitting). **DEPENDS ON**: T025.
- [X] T047 [US2] Implement `code/models/diagnostics.py` VIF robustness check: Add a secondary check that calculates VIF on the **test set** split (T019) to ensure multicollinearity is not an artifact of the training split distribution. If VIF > 5 on the test set, flag the model as unstable in the final report. **Rationale**: Addresses the "Statistical Independence" requirement (Constitution VI) by ensuring the predictor independence holds out-of-sample. **DEPENDS ON**: T019, T023.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluation and Reporting of Generalization (Priority: P3)

**Goal**: Evaluate models on held-out test set, calculate metrics, and generate report comparing full model vs baseline.

**Independent Test**: The evaluation script runs on the test split and produces a summary table and calibration plot, demonstrating whether the full model achieves a statistically significant improvement.

**⚠️ GATE**: Phase 5 tasks depend on the completion of Phase 4 (T023, T024, T025, T026, T040, T047) and Phase 2 (T038, T042).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for evaluation metrics schema in `tests/contract/test_metrics.py`
- [X] T028 [P] [US3] Integration test for report generation in `tests/integration/test_report.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/evaluation/metrics.py`: Calculate AUC, Precision, Recall, and generate Calibration Plot for both models (FR-009). **Ensure both Full and Baseline metrics are output** (including `auc_full`, `auc_baseline`, `delta`). **Output**: `data/evaluation_metrics.json`. **DEPENDS ON**: T022, T025.
- [X] T030 [P] [US3] Implement `code/evaluation/report.py` step 1: Perform a **Bootstrap or Permutation Test** (mandatory method) to test hypothesis $\Delta AUC \ge 0.05$. **Explicitly calculate the confidence interval for the delta** and compare against frequency-only baseline, generating p-value and 95% CI. **Save results to `data/auc_delta_metrics.json`** (FR-010). **This is a mandatory critical path task**. **Deliverable**: Save `{"auc_full": float, "auc_baseline": float, "delta": float, "p_value": float, "ci_95": [float, float], "test_method": "Bootstrap"}`. **DEPENDS ON**: T029.
- [X] T031 [US3] Implement `code/evaluation/report.py` step 2: Map LRT p-value to SC-001 and VIF scores to SC-003 in final summary. **DEPENDS ON**: T023 (VIF), T024 (LRT), T025 (Bayesian Results). **DEPENDS ON**: T023, T024, T025.
- [X] T041 [US3] **Gate**: Verify Constitution II Compliance: Ensure tasks T038 (Verification) and T025 (Bayesian Convergence) are completed and `data/verification_report.json` indicates success before allowing final report generation (T032). **DEPENDS ON**: T038, T025.
- [X] T032 [US3] Implement `code/evaluation/report.py` step 3: Generate **Draft Final Report** stating whether "flavor and role predict compatibility beyond frequency" is supported with specific evidence (p-values, AUC delta, CI). **Output**: `docs/draft_final_report.md`. **DEPENDS ON**: T041, T030, T025, T047.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

**⚠️ GATE**: Phase N tasks depend on the completion of all User Story implementations (Phases 3, 4, 5).

- [X] T033a [P] Documentation updates: Update `docs/research.md` with 'Methodology' section (include power analysis N values). **DEPENDS ON**: T025, T019.
- [X] T033b [P] Documentation updates: Update `docs/research.md` with 'Results' section (include model coefficients, VIF, AUC delta). **DEPENDS ON**: T044.
- [X] T033c [P] Documentation updates: Update `docs/research.md` with 'Limitations' section (include sampling constraints, VIF stability, sensitivity analysis). **DEPENDS ON**: T048, T047.
- [X] T033d [P] Documentation updates: Update `docs/quickstart.md` with 'Environment Setup' section (include requirements.txt install, streaming instructions). **DEPENDS ON**: T002, T034.
- [X] T033e [P] Documentation updates: Update `docs/quickstart.md` with 'Data Pipeline' and 'Model Execution' sections (include streaming instructions and runtime estimate methodology). **DEPENDS ON**: T043a.
- [X] T034 [P] Code cleanup: Implement streaming for Recipe1M and chunked processing for FlavorDB in `code/data/download.py` and `code/data/preprocess.py` to ensure Peak RAM < 6GB. **Deliverable**: Reference `data/memory_profile.json` produced by T037. **Linked to**: FR-001, US-1. **DEPENDS ON**: T002.
- [X] T035a [P] Additional unit tests: Add `tests/unit/test_preprocess.py::test_levenshtein_normalization` and `tests/unit/test_diagnostics.py::test_vif_calculation` to verify FR-002 and FR-007 logic. **DEPENDS ON**: T014, T023.
- [X] T036 [P] Run `quickstart.md` validation to ensure full pipeline execution ≤ 6 hours. **Execute**: `python code/validate_runtime.py` which runs the pipeline and measures time. **Deliverable**: Generate `data/ci_validation_report.json` containing the measured runtime and a boolean `passed` field. **DEPENDS ON**: T043a.

---

## Phase N+1: Revision & Gap Resolution (Addressing Review Concerns)

**Purpose**: Address specific gaps identified in the analysis phase regarding data robustness, error handling, and reproducability.

- [X] T037 [US1] Implement `code/data/preprocess.py` explicit streaming logic: Refactor T013 to use `datasets.load_dataset(..., streaming=True)` for Recipe1M and `itertools.islice` for controlled downsampling, ensuring the full dataset is never loaded into RAM, and log the exact sampling ratio and seed used (Constitution II: Verified Accuracy). **Deliverable**: `data/memory_profile.json` with `{"peak_ram_mb": float, "sampling_ratio": float, "seed": int}`. **DEPENDS ON**: T034, T013.
- [X] T049 [US1] Implement `code/data/preprocess.py` zero-occurrence handling: Verify zero-occurrence handling logic in T015 (log(C + epsilon)). Log the epsilon value and count of zero pairs to `data/zero_handling_log.json`. **Rationale**: Addresses the "Edge Cases" in spec.md regarding zero counts and ensures the log-transform is mathematically valid without removing data. **Ensure this data is included in the final summary report**. **Deliverable**: Output `{"epsilon": float, "zero_pair_count": int, "total_pairs": int}` to `data/zero_handling_log.json`. **DEPENDS ON**: T015.
- [X] T048 [US3] Implement `code/evaluation/report.py` sensitivity analysis: Generate a sensitivity plot showing how the AUC delta and LRT p-value change if the imputation strategy (median vs. mean) or the functional role binning (tertiles vs. quartiles) is altered. **Rationale**: Addresses the "Limitations" section requirement in T033c by quantifying the robustness of the findings to preprocessing choices. **DEPENDS ON**: T018, T017b, T030.

---

## Phase N+2: Final Execution Validation

**Purpose**: Ensure the entire pipeline runs successfully on the CI runner and produces the final report.

- [ ] T043a [P] Execute the full pipeline on the GitHub Actions runner using the `quickstart.md` script to verify end-to-end execution. **Deliverable**: `data/pipeline_execution_log.json` containing runtime, peak memory, and success status. **Deliverable**: Output `{"status": 'SUCCESS'/'FAILED', "runtime_seconds": float, "peak_ram_mb": float, "artifacts_created": [list of paths]}`. **DEPENDS ON**: T025, T030, T046, T049, T050, T047, T034, T037, T013, T014, T015, T018, T019, T022, T023, T024, T029, T048.
- [ ] T043b [P] Capture Metrics: Extract final metrics from `data/pipeline_execution_log.json` and model outputs into `data/final_validation_report.json`. **DEPENDS ON**: T043a.
- [ ] T044 [P] Generate the final `docs/final_report.md` by aggregating results from `data/auc_delta_metrics.json`, `data/lrt_result_vif_corrected.json`, `data/final_validation_report.json`, `data/bayesian_convergence_log.json`, `data/vif_scores_initial.json`, and `docs/draft_final_report.md`. **Deliverable**: Generate `docs/final_report.md` containing sections: 'Executive Summary', 'Methodology', 'Results (LRT, VIF, AUC Delta)', 'Conclusion', populated from the JSON artifacts listed in dependencies. **DEPENDS ON**: T043b, T032, T048, T047, T025, T030, T023, T024.

**Note**: Task T016b (Text Similarity) has been removed from this plan to strictly adhere to FR-004, which mandates deriving flavor similarity exclusively from FlavorDB chemical vectors. The parallel text embedding path was found to conflict with the spec's "Single Source of Truth" and statistical independence requirements.