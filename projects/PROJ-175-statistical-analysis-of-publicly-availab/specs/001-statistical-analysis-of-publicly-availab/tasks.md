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

- [X] T001a Create project directory structure: `projects/PROJ-175-statistical-analysis-of-publicly-availab/code/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/data/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/tests/`. **Verification**: Verify existence of directories via `os.path.isdir` and log to `data/setup_log.json`. **Schema**: `{"status": "SUCCESS"|"FAILED", "timestamp": "ISO8601", "paths_verified": ["path1", "path2"]}`.
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
- [X] T006 [P] Setup memory profiling utility in `code/utils/memory_monitor.py` to enforce a predefined RAM limit. **Deliverable**: Create `check_limit(limit_mb=6144)` function that raises `MemoryError` if exceeded, and log to `data/memory_profile.json`. **Schema**: `{"peak_ram_mb": float, "timestamp": "ISO8601", "limit_mb": 6144}`.
- [X] T007 Create base data schema definitions in `specs/001-statistical-analysis-of-recipe-data/contracts/`: specifically `dataset.schema.yaml` and `model_output.schema.yaml` (YAML format). **Deliverable**: Create schemas using Pydantic or JSON Schema, and add script `code/utils/validate_schema.py` that loads these and validates a sample row. **Content**: `dataset.schema.yaml` must define fields: `ingredient_id` (str), `log_co_occurrence` (float), `flavor_similarity` (float), `functional_role` (str), `compatibility_label` (int). `model_output.schema.yaml` must define: `coefficients` (dict), `p_values` (dict), `vif_scores` (dict).
- [X] T008 [P] [US1] **Power Analysis**: Perform a **unified** power analysis for Logistic Regression and Hierarchical Bayesian Model using `statsmodels.stats.power` to calculate a single required sample size N_unified for effect size ≥ 0.1 and power 0.8. **Output**: Write `N_unified` directly to **BOTH** `data/power_analysis.json` and `data/split_config.json` (along with `seed`) to serve as the single source of truth for sampling. **Note**: This task MUST complete BEFORE data download (T013) to define the sampling strategy. **Implementation**: Use theoretical effect sizes from literature to estimate N_unified a priori. **Rationale**: Consolidates T008a/T008b to ensure a "Single Source of Truth" for sample size and satisfies Phase 0.5 of the plan. **DEPENDS ON**: T002.
- [X] T008b [P] **Bridging Task**: Copy `N_unified` from `data/power_analysis.json` to `data/split_config.json` to ensure T019 can access the sample size. **Deliverable**: Update `data/split_config.json` with `N_unified` and `seed`. **DEPENDS ON**: T008.
- [X] T038 [P] [US1] Implement `code/data/verify.py` robust error handling: Replace any generic `try/except` blocks with specific HTTP error handling that **raises** on failure (no synthetic fallback) and logs the exact URL and error code to `data/download_errors.log` (Constitution II: Verified Accuracy). **DEPENDS ON**: T002.
- [X] T042 [P] [US1] Implement `code/data/verify.py` schema validation for Counterfactual dataset: Add a strict schema check for the `compatibility_label` column to ensure it contains only binary values (0/1) or valid float scores, failing the pipeline if the schema deviates (FR-001b). **DEPENDS ON**: T002.
- [X] T099 [P] **Create Pipeline Entrypoint**: Implement `code/run_full_pipeline.py` that orchestrates T051, T013-T019, T022, T025, T029-T032. **Deliverable**: The script must write three log files with the following schemas:
  1. `data/pipeline_execution_log.json`: `{"status": "SUCCESS"|"FAILED", "runtime_seconds": float, "peak_ram_mb": float, "artifacts_created": [...]}`
  2. `data/model_fitting_log.json`: `{"status": "SUCCESS"|"FAILED", "convergence_status": "OK"|"FAILED", "models_fitted": [...]}`
  3. `data/evaluation_log.json`: `{"status": "SUCCESS"|"FAILED", "metrics_calculated": true, "report_generated": true}`.
  **DEPENDS ON**: T002.
- [X] T102 [P] **Create Atomic Download Scripts**: Implement `download_recipe1m.py`, `download_flavor_db.py`, `download_counterfactual.py` and define `data/download_atomic_log.json` schema. **Deliverable**: Scripts and schema file. **DEPENDS ON**: T012, T046.
- [X] T103 [P] **Create Atomic Preprocessing Scripts**: Implement `normalize_step.py`, `co_occurrence_step.py`, `similarity_step.py`, `role_step.py`, `imputation_step.py`, `split_step.py` and define `data/preprocess_atomic_log.json` schema. **Deliverable**: Scripts and schema file. **DEPENDS ON**: T061 (logic), T007.
- [X] T104 [P] **Create Atomic Model Scripts**: Implement `fit_null.py`, `fit_full.py`, `fit_bayesian.py` and define `data/model_fitting_atomic_log.json` schema. **Deliverable**: Scripts and schema file. **DEPENDS ON**: T022, T025.
- [X] T105 [P] **Create Atomic Evaluation Scripts**: Implement `calc_metrics.py`, `test_hypothesis.py` and define `data/evaluation_atomic_log.json` schema. **Deliverable**: Scripts and schema file. **DEPENDS ON**: T029, T030.
- [X] T106 [P] **Create Atomic Report Scripts**: Implement `gen_section_exec.py`, `gen_section_method.py`, `gen_section_results.py`, `gen_section_conc.py` and define `data/report_atomic_log.json` schema. **Deliverable**: Scripts and schema file. **DEPENDS ON**: T055.

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

- [X] T012 [P] [US1] Implement `code/data/verify.py` to check URL availability and schema of Recipe1M, FlavorDB, and Counterfactual dataset (FR-001b). **Must implement hard fail logic**: if any URL is unreachable or schema (specifically `compatibility_label` column) is missing, raise an error and generate `data/verification_report.json` with status "FAILED". **Deliverable**: Generate `data/verification_report.json` with keys: `status` (PASS/FAIL), `timestamp`, `errors` (list of dicts with `url`, `code`, `message`), and `verified_urls` (dict of `name`: `url`). **Note**: If T012 raises an error, the pipeline halts. If it succeeds, it writes the report with status "PASS" and the verified URLs, allowing T051 to run.
- [X] T046 [P] [US1] Implement `code/data/verify.py` strict URL verification: Add a pre-flight check that attempts to `HEAD` the specific Recipe1M and FlavorDB URLs defined in `data/verification_report.json`. If the URL returns 403/404 or times out, raise a `DataUnavailableError` with the specific URL and error code to prevent silent fallbacks. **Rationale**: Addresses the "Hard Fail" requirement from T038 by ensuring the download task itself validates availability before attempting a full fetch. **DEPENDS ON**: T012.
- [X] T051 [US1] **Data Source Verification**: Implement `code/data/download.py` to explicitly fetch the **exact** Recipe1M subset and FlavorDB matrix from the **verified URLs listed in `data/verification_report.json`** (output of T012). **Constraint**: The script MUST NOT contain any fallback to synthetic data or local mocks. If the download fails, it MUST raise a `DataFetchError` with the specific URL and HTTP status code. **Rationale**: Addresses the "Hard Fail" requirement and prevents fabrication of data sources. **Note**: This task runs only if T012 (Verification) succeeded and generated the report. **DEPENDS ON**: T012, T046.
- [X] T013 [US1] Implement `code/data/download.py` to fetch Recipe1M (Two-Pass Streaming), FlavorDB chemical matrix, and Counterfactual datasets from verified URLs (FR-001). **Streaming Logic**: Use `datasets.load_dataset(..., streaming=True)`. **Two-Pass Algorithm**: Pass 1 iterates to count ingredient frequencies (no matrix); Pass 2 iterates to build co-occurrence pairs using the pre-computed frequencies. **No synthetic fallback**. **Deliverable**: Output `data/raw/recipe1m_stream_log.json` with `{"chunk_size": int, "total_chunks_processed": int, "peak_ram_mb": float}`. **DEPENDS ON**: T051.
- [X] T014 [US1] Implement `code/data/preprocess.py` step 1-2: Normalize ingredient names using **Levenshtein distance threshold = 2 (hard constraint)** mapped explicitly to the **FlavorDB canonical list** (FR-002). **Primary Source**: FlavorDB. **Constraint**: If FlavorDB entry is missing, the pair MUST be excluded from the analysis and logged, OR assigned a neutral value (e.g., 0.0 similarity) as per Spec US-1 Edge Cases. **NO FALLBACK to text embeddings** for the primary mapping, but neutral value assignment is permitted for missing pairs. **Log the exclusion/neutral count to `data/normalization_config.json`** with schema: `{"threshold": 2, "method": "levenshtein", "timestamp": "ISO8601", "mapped_count": int, "excluded_count": int, "neutral_count": int}`. **Explicitly depends on schema validation logic established in T012/T007**. **Note**: This task MUST unconditionally write `data/normalization_config.json` even if skipped, to ensure downstream tasks have a valid config file. If normalization cannot proceed (e.g., verification failure), generate a default config with `{"threshold": 2, "method": "levenshtein", "timestamp": "ISO8601", "mapped_count": 0, "excluded_count": 0, "neutral_count": 0, "status": "DEFAULT"}`. **DEPENDS ON**: T007, T012, T013.
- [X] T014b [P] [US1] **Default Config Generation**: If T014 fails or is skipped, generate a default `data/normalization_config.json` with `{"threshold": 2, "method": "levenshtein", "timestamp": "ISO8601", "mapped_count": 0, "excluded_count": 0, "neutral_count": 0, "status": "DEFAULT"}`. **Rationale**: Ensures T059 (Reproducibility Audit) always has the required input file. **DEPENDS ON**: T014.
- [X] T049 [US1] Implement `code/data/preprocess.py` step 5 (Zero-occurrence handling): Define epsilon value for log-transform ($\log(C_{ij} + \epsilon)$) to handle zero counts and log the count of zero pairs. **Deliverable**: Output `{"epsilon": float, "zero_pair_count": int, "total_pairs": int}` to `data/zero_handling_log.json`. **Note**: This file must be written so T015 can read it. **DEPENDS ON**: T013.
- [X] T015 [US1] Implement `code/data/preprocess.py` step 3: Construct global co-occurrence matrix $C$ with log-transform ($\log(C_{ij} + \epsilon)$) using epsilon defined in T049 (FR-003). **Implementation**: Read epsilon from `data/zero_handling_log.json`. **Output**: `data/processed/co_occurrence_matrix.parquet`. **DEPENDS ON**: T049, T013.
- [X] T016 [US1] Implement `code/data/preprocess.py` step 4: Calculate cosine similarity between **FlavorDB chemical vectors** (fetched in T013) for ingredient pairs to derive the **flavor-profile similarity** feature (FR-004). **Primary Source**: FlavorDB. **Constraint**: If FlavorDB vectors are missing for a pair, the pair MUST be excluded from the analysis and logged. **NO FALLBACK to text embeddings**. **Explicitly depends on T014's FlavorDB canonical mapping and T013's chemical vectors**. **Output**: `data/processed/flavor_similarity.parquet`. **DEPENDS ON**: T013, T014.
- [X] T017 [US1] Implement `code/data/preprocess.py` step 5: Derive functional role by **orthogonalized positional rank** (regress ingredient rank on global log-frequency and use **residuals**) to ensure statistical independence from co-occurrence frequency (FR-005, Plan Phase 1 Step 4). **Input**: Ingredient list position and global log-frequency. **Output**: `data/processed/ingredient_roles_residuals.parquet` with columns `ingredient_id`, `rank`, `frequency`, `residual_role`. **DEPENDS ON**: T015.
- [X] T017b [US1] Implement `code/data/preprocess.py` step 5b: Discretize the **residual role** (from T017) into categorical labels: **Primary**, **Secondary**, **Garnish** using **tertiles of the residuals (DEFAULT method)**. **Edge Case**: If unique residual values < 3, use **quantile-based binning (20/60/20)** to ensure deterministic execution. **Log the method and cutpoints used to `data/role_cutpoints.json`** (FR-005). **Input**: `data/processed/ingredient_roles_residuals.parquet`. **Output**: `data/processed/ingredient_roles_binned.parquet`. **Deliverable**: Log `{"method": "tertiles|quantiles", "cutpoints": [float (4 decimals), float], "labels": ["Primary", "Secondary", "Garnish"]}` to `data/role_cutpoints.json`. **DEPENDS ON**: T017.
- [X] T018 [US1] Implement `code/data/preprocess.py` step 6-7: Handle missing data by imputing missing **categorical role** (from T017b) with 'Unknown' and creating a `role_missing_flag` column; impute missing similarity (T016) with **median similarity value** and create a `similarity_missing_flag` column. **Include a verification step**: Calculate correlation between imputed similarity and orthogonalized role using **Pearson correlation** (threshold p < 0.05) to ensure no bias is introduced, logging the result to `data/missing_data_bias_log.json` with keys `correlation_value`, `p_value`, `bias_detected` (bool). Join with Counterfactual labels (FR-005, FR-004). **Input**: `data/processed/ingredient_roles_binned.parquet`, `data/processed/flavor_similarity.parquet`. **Output**: `data/processed/final_features.parquet`. **Note**: The median imputation strategy is explicitly accounted for in downstream statistical validity checks, referencing FR-005. **DEPENDS ON**: T013, T017b, T016.
- [X] T019 [US1] Implement `code/data/split.py` to create the **unified** train/test split. **Explicitly downsample the dataset** to N_unified (determined by T008) using `pandas.sample` with the specified seed. **Rationale**: This ensures a "Single Source of Truth" (Constitution IV) for all models. **Deliverable**: Read `N_unified` from `data/split_config.json` (output of T008b). Write split results to `data/split_config.json` with keys `n_logistic`, `n_bayesian`, `n_unified`, `seed`. **DEPENDS ON**: T008b, T018.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Model Fitting and Validation (Priority: P2)

**Goal**: Fit regularized logistic regression and hierarchical Bayesian models to predict compatibility, controlling for co-occurrence while isolating flavor/role effects.

**Independent Test**: The model fitting process can be run on a downsampled subset to verify coefficients are significant (p < 0.05), VIF confirms no multicollinearity, and sample size supports power analysis.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T021 [P] [US2] Unit test for VIF calculation and Likelihood-Ratio test logic in `tests/unit/test_diagnostics.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement `code/models/diagnostics.py` step 1: Calculate Variance Inflation Factors (VIF) for all predictors; **do not drop** predictors if VIF > 5. **Output**: `data/vif_scores_initial.json` (MUST save before any flagging). **Deliverable**: Output `{"predictors": {"name": float}, "dropped": [], "max_vif": float}` to `data/vif_scores_initial.json`. **Unconditionally write `data/final_predictors.json`** with the original predictor list if VIF <= 5, or the reduced list if VIF > 5. **DEPENDS ON**: T019 (Data ready).
- [X] T040 [US2] Implement `code/models/diagnostics.py` step 3b: **Multicollinearity Resolution**: If VIF > 5 is detected for the 'Functional Role' predictor (from T023), **ATTEMPT TO RE-ORTHOGONALIZE** the variable first. If VIF > 5 persists after re-orthogonalization, **DROP** the variable as a **LAST RESORT** and re-fit the model (see T040b). If VIF <= 5, proceed with the full model. **Deliverable**: Update `data/model_comparison.json` with a `multicollinearity_flag` field and save results to `data/lrt_result_vif_corrected.json`. **Output**: Also update `data/final_predictors.json` with the reduced list if applicable. **DEPENDS ON**: T023 (VIF Check).
- [X] T040b [US2] Implement `code/models/diagnostics.py` step 3c: **Re-fit Model**: If T040 dropped the 'Functional Role' predictor, re-fit the logistic regression model with the reduced predictor set. **Deliverable**: Update `data/final_predictors.json` and `data/final/logistic_results.json` with the corrected model results. **DEPENDS ON**: T040.
- [X] T022 [P] [US2] Implement `code/models/fit_logistic.py`: Fit Null Model (frequency only) and Full Model (frequency + similarity + **categorical role** from T017b) with **L2 regularization** using the downsampled subset determined by T019 (FR-006). **Explicitly set regularization parameter to 'l2'**. **Input**: Read final predictor list from `data/final_predictors.json` (output of T023, which always writes the file). **Output**: `data/final/logistic_results.json`. **DEPENDS ON**: T018, T023, T019. **Note**: T022 depends on T023 (which always writes the file), not T040/T040b.
- [X] T024 [US2] Implement `code/models/diagnostics.py` step 2: Perform Likelihood-Ratio Test (Null vs Full) and record p-value (FR-008). **DEPENDS ON**: T022.
- [X] T050 [P] [US2] Implement `code/models/fit_bayesian.py` CPU enforcement: Add a runtime check that detects if a CUDA-enabled device is available. If available, log a warning and **force CPU execution** (Do NOT switch to GPU) to ensure the "CPU-only" constraint is strictly honored. **Rationale**: Addresses the "Compute Feasibility" rule by ensuring the execution stage knows the task is strictly CPU-bound and no GPU offload occurs. **Deliverable**: Log to `data/gpu_detection_log.json` with `gpu_available`: bool, `action`: 'CPU_FORCED', `warning_message`: str. **DEPENDS ON**: T019.
- [X] T025 [US2] Implement `code/models/fit_bayesian.py`: Implement the full Hierarchical Bayesian model logic (CPU-only NUTS) on the downsampled subset determined by T019. **Include early stopping and convergence checks**: Monitor R-hat and effective sample size (ESS); if convergence is not reached within a **reasonable time limit** (as per spec's intent for flexible statistical validation), the task must fail loudly and report the specific diagnostic failure rather than proceeding with unreliable posterior estimates (FR-002 context: Hierarchical Bayesian model fitting). **Output**: `data/final/bayesian_results.json`. **Deliverable**: If convergence is not reached, raise `ConvergenceError` with message "Bayesian model failed convergence: R_hat={R_hat}, ESS={ESS}" and log `data/bayesian_convergence_log.json` with `status`: 'FAILED', `metrics`: {`R_hat`: float, `ESS`: int}. **DEPENDS ON**: T019, T050.
- [X] T026 [US2] Implement `code/models/diagnostics.py` step 3: Run **Post-Hoc Power Validation** to verify the achieved power for effect size ≥ 0.1 given the actual sample size used and model convergence metrics (FR-002 context: Hierarchical Bayesian model fitting). **DEPENDS ON**: T025.
- [X] T047 [P] [US2] Implement `code/models/diagnostics.py` VIF robustness check: Add a secondary check that calculates VIF on the **test set** split (T019) to ensure multicollinearity is not an artifact of the training split distribution. If VIF > 5 on the test set, flag the model as unstable in the final report. **Rationale**: Addresses the "Statistical Independence" requirement (Constitution VI) by ensuring the predictor independence holds out-of-sample. **This task consolidates the functionality of the removed T053**. **DEPENDS ON**: T019, T023.

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
- [X] T030 [P] [US3] Implement `code/evaluation/report.py` step: Perform a **Bootstrap or Permutation Test** (preferred method) to test the hypothesis of a meaningful positive difference in AUC.. **Explicitly calculate the confidence interval for the delta** and compare against frequency-only baseline, generating p-value and 95% CI. **Save results to `data/auc_delta_metrics.json`** (FR-010). **Any valid hypothesis test is acceptable**, with Bootstrap/Permutation preferred for non-parametric robustness. **Deliverable**: Save `{"auc_full": float, `auc_baseline`: float, `delta`: float, `p_value`: float, `ci_95`: [float (lower), float (upper)], `test_method`: "Bootstrap", `threshold`: 0.05}`. **DEPENDS ON**: T029.
- [X] T031 [US3] Implement `code/evaluation/report.py` step 2: Map LRT p-value to SC-001 and VIF scores to SC-003 in final summary. **DEPENDS ON**: T023 (VIF), T024 (LRT), T025 (Bayesian Results). **DEPENDS ON**: T023, T024, T025.
- [X] T041 [US3] **Gate**: Verify Constitution II Compliance: Ensure tasks T038 (Verification) and T025 (Bayesian Convergence) are completed and `data/verification_report.json` indicates success before allowing final report generation (T032). **DEPENDS ON**: T038, T025.
- [X] T032 [US3] Implement `code/evaluation/report.py` step 3: Generate **Draft Final Report** stating whether "flavor and role predict compatibility beyond frequency" is supported with specific evidence (p-values, AUC delta, CI). **Include Limitations**: Explicitly state if multicollinearity flags (from T040/T047) were raised. **Output**: `docs/draft_final_report.md`. **DEPENDS ON**: T041, T030, T025, T047.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

**⚠️ GATE**: Phase N tasks depend on the completion of all User Story implementations (Phases 3, 4, 5).

- [X] T033a [P] Documentation updates: Update `docs/research.md` with 'Methodology' section (include power analysis N values). **DEPENDS ON**: T025, T019.
- [X] T033d [P] Documentation updates: Update `docs/quickstart.md` with 'Environment Setup' section (include requirements.txt install, streaming instructions). **DEPENDS ON**: T002, T034.
- [X] T033e [P] Documentation updates: Update `docs/quickstart.md` with 'Data Pipeline' and 'Model Execution' sections (include streaming instructions and runtime estimate methodology). **DEPENDS ON**: T043a.
- [X] T034 [P] Code cleanup: Implement streaming for Recipe1M and chunked processing for FlavorDB in `code/data/download.py` and `code/data/preprocess.py` to ensure Peak RAM < 6GB. **Deliverable**: Reference `data/memory_profile.json` produced by T037. **Linked to**: FR-001, US-1. **DEPENDS ON**: T002.
- [X] T035a [P] Additional unit tests: Add `tests/unit/test_preprocess.py::test_levenshtein_normalization` and `tests/unit/test_diagnostics.py::test_vif_calculation` to verify FR-002 and FR-007 logic. **DEPENDS ON**: T014, T023.
- [X] T036 [P] Run `quickstart.md` validation to ensure full pipeline execution ≤ 6 hours. **Execute**: `python code/validate_runtime.py` which runs the pipeline and measures time. **Deliverable**: Generate `data/ci_validation_report.json` containing the measured runtime and a boolean `passed` field. **DEPENDS ON**: T043a.

---

## Phase N+1: Revision & Gap Resolution (Addressing Review Concerns)

**Purpose**: Address specific gaps identified in the analysis phase regarding data robustness, error handling, and reproducability.

- [X] T037 [US1] Implement `code/data/preprocess.py` explicit streaming logic: Refactor T013 to use `datasets.load_dataset(..., streaming=True)` for Recipe1M and `itertools.islice` for controlled downsampling, ensuring the full dataset is never loaded into RAM, and log the exact sampling ratio and seed used (Constitution II: Verified Accuracy). **Deliverable**: `data/memory_profile.json` with `{"peak_ram_mb": float (MB), "sampling_ratio": float (4 decimals), "seed": int}`. **DEPENDS ON**: T034, T013.
- [X] T048 [US3] Implement `code/evaluation/report.py` sensitivity analysis: Generate a sensitivity plot showing how the AUC delta and LRT p-value change if the imputation strategy (median vs. mean) or the functional role binning (tertiles vs. quartiles) is altered. **Rationale**: Addresses the "Limitations" section requirement in T033c by quantifying the robustness of the findings to preprocessing choices. **DEPENDS ON**: T018, T017b, T030.

---

## Phase N+2: Execution Validation & Draft Report

**Purpose**: Execute the pipeline and ensure the draft report exists.

- [X] T099 [P] **Create Pipeline Entrypoint**: (Already defined in Phase 2, referenced here for clarity)
- [X] T100 [P] **Verify Draft Report**: Ensure `docs/draft_final_report.md` exists. If T032 failed or was skipped, generate a placeholder report stating "Draft report not generated due to upstream failure" to satisfy T044's dependency. **Deliverable**: `docs/draft_final_report.md` (either from T032 or placeholder). **DEPENDS ON**: T032.
- [ ] T043a [P] **Execute Data Pipeline**: Run the full data download and preprocessing pipeline on the GitHub Actions runner using `code/run_full_pipeline.py` (T099). **Deliverable**: `data/pipeline_execution_log.json` with schema defined in T099. **DEPENDS ON**: T099, T051, T013, T014, T015, T016, T017, T017b, T018, T019.
- [ ] T043b [P] **Execute Model Fitting**: Run the model fitting scripts (Logistic and Bayesian) on the CI runner. **Deliverable**: `data/model_fitting_log.json` with schema defined in T099. **DEPENDS ON**: T099, T022, T025, T040, T040b.
- [ ] T043c [P] **Execute Evaluation**: Run the evaluation and reporting scripts on the CI runner. **Deliverable**: `data/evaluation_log.json` with schema defined in T099. **DEPENDS ON**: T099, T029, T030, T032.
- [ ] T043d [P] Capture Metrics: Extract final metrics from `data/pipeline_execution_log.json`, `data/model_fitting_log.json`, and `data/evaluation_log.json` into `data/final_validation_report.json`. **DEPENDS ON**: T043a, T043b, T043c.
- [ ] T044 [P] Generate the final `docs/final_report.md` by aggregating results from `data/auc_delta_metrics.json`, `data/lrt_result_vif_corrected.json`, `data/final_validation_report.json`, `data/bayesian_convergence_log.json`, `data/vif_scores_initial.json`, and `docs/draft_final_report.md` (from T100). **Deliverable**: Generate `docs/final_report.md` containing sections: 'Executive Summary', 'Methodology', 'Results (LRT, VIF, AUC Delta)', 'Conclusion', populated from the JSON artifacts listed in dependencies. **DEPENDS ON**: T043d, T100, T048, T047, T025, T030, T023, T024.

---

## Phase N+3: Critical Data Integrity & Reproducibility Fixes (Revision Round 1)

**Purpose**: Address specific reviewer concerns regarding data sourcing, memory safety, and statistical validity that were not fully atomized in previous phases.

- [X] T054 [US3] **Calibration Verification**: Implement a rigorous calibration test in `code/evaluation/metrics.py` that bins predicted probabilities and compares them to observed frequencies. The task must fail if the maximum deviation from the ideal diagonal exceeds a defined tolerance threshold. **Deliverable**: Save `data/calibration_test_results.json` with `{"max_deviation": float, "bins": int, "passed": bool}`. **Rationale**: Addresses SC-004 (Reliability of probability estimates) and ensures the model outputs are trustworthy. **DEPENDS ON**: T029.
- [X] T055 [US3] **Final Report Generation**: Update `code/evaluation/report.py` to automatically aggregate all intermediate JSON artifacts (VIF, LRT, AUC delta, calibration, power analysis) into a single `docs/final_report.md`. The report must explicitly state whether the hypothesis "flavor and role predict compatibility beyond frequency" is supported, citing the specific p-values and effect sizes. **Rationale**: Ensures the "Single Source of Truth" (Constitution IV) for the final scientific output. **DEPENDS ON**: T030, T031, T040, T047, T054.

---

## Phase N+4: Execution Gate Validation & Atomic Script Creation

**Purpose**: Final validation of the entire pipeline against the execution gate constraints and generation of the definitive report.

- [X] T056 [P] [US3] **Execution Gate Pre-Check**: Run a final automated validation script `code/validate_execution_gate.py` that verifies: (1) `data/verification_report.json` exists and status is "PASS", (2) `data/bayesian_convergence_log.json` exists and status is "SUCCESS", (3) `data/calibration_test_results.json` exists and `passed` is true, (4) `data/vif_scores_initial.json` exists. If any check fails, the script must exit with a non-zero code and print a clear error message. **Deliverable**: `data/gate_validation_report.json` with `{"status": "PASS"|"FAIL", "checks": {"verification": bool, "bayesian": bool, "calibration": bool, "vif": bool}}`. **DEPENDS ON**: T051, T025, T054, T023.
- [X] T101 [P] **Verify Normalization Config**: Ensure `data/normalization_config.json` exists. If T014 failed or was skipped, generate a default config with `{"threshold": 2, "method": "levenshtein", "timestamp": "ISO8601", "mapped_count": 0, "excluded_count": 0, "neutral_count": 0, "status": "DEFAULT"}`. **Deliverable**: `data/normalization_config.json`. **DEPENDS ON**: T014, T014b.
- [X] T057 [P] [US3] **Final Report Compilation**: Generate the definitive `docs/final_report.md` by aggregating all validated artifacts from T056. The report must include a "Constitution Compliance" section explicitly stating that all gates (II, IV, VI) were passed, and a "Limitations" section detailing any flagged issues (e.g., VIF > 5 on test set, power analysis constraints). **Deliverable**: `docs/final_report.md` with sections: 'Executive Summary', 'Methodology', 'Constitution Compliance', 'Results (LRT, VIF, AUC Delta, Calibration)', 'Conclusion', 'Limitations'. **DEPENDS ON**: T056, T044, T048, T047, T025, T030, T023, T024.
- [X] T058 [P] [US3] **Artifact Hashing & Versioning**: Compute SHA-256 hashes for all final data artifacts (`data/final/*.parquet`, `data/final/*.json`, `docs/final_report.md`) and write them to `state/final_artifacts_hashes.json`. This ensures the "Versioning Discipline" (Constitution V) is met for the final output. **Deliverable**: `state/final_artifacts_hashes.json` with `{"artifact_path": "sha256_hash"}`. **DEPENDS ON**: T057.
- [ ] T059 [P] [US3] **Reproducibility Audit**: Run a script `code/audit_reproducibility.py` that re-fetches the **canonical datasets** (or verifies cached checksums match canonical sources) and re-runs the entire pipeline from scratch using the exact random seeds and parameters logged in `data/split_config.json` and `data/normalization_config.json`. The script must verify that the output artifacts match the hashes in `state/final_artifacts_hashes.json`. **Deliverable**: `data/reproducibility_audit.json` with `{"status": "PASS"|"FAIL", "hash_match": bool, "runtime_difference_ms": int}`. **DEPENDS ON**: T058, T019, T101.
- [X] T060 [P] [US3] **Final Sign-off**: If T059 passes, update `docs/research.md` with a final "Sign-off" section confirming the project meets all success criteria (SC-001 to SC-004) and constitution principles. If T059 fails, the project transitions to `human_input_needed`. **Deliverable**: Updated `docs/research.md` with a "Final Sign-off" section. **DEPENDS ON**: T059.

---

## Phase N+5: Atomic Execution & Verification (Revision Round 2)

**Purpose**: Break down complex execution tasks into atomic, verifiable steps to ensure the pipeline can be debugged step-by-step if it fails.

- [ ] T061 [P] **Atomic Data Download**: Split `T051` into discrete sub-tasks for each dataset (Recipe1M, FlavorDB, Counterfactual). Execute `download_recipe1m.py`, `download_flavor_db.py`, and `download_counterfactual.py` sequentially, verifying checksums immediately after each download before proceeding. **Deliverable**: `data/download_atomic_log.json` with `{"dataset": "name", "status": "SUCCESS"|"FAILED", "checksum_verified": bool}`. **Rationale**: Isolates download failures to specific datasets, preventing a single failure from halting the entire pipeline without context. **DEPENDS ON**: T012, T046, T102.
- [ ] T062 [P] **Atomic Preprocessing**: Split `T013-T019` into discrete sub-tasks for each preprocessing step (Normalization, Co-occurrence, Similarity, Role, Imputation, Split). Execute each step independently and verify the output artifact exists and matches the expected schema before proceeding. **Deliverable**: `data/preprocess_atomic_log.json` with `{"step": "name", "status": "SUCCESS"|"FAILED", "output_schema_valid": bool}`. **Rationale**: Ensures data integrity at each stage and prevents cascading errors from corrupted intermediate files. **DEPENDS ON**: T061, T007, T103.
- [ ] T063 [P] **Atomic Model Fitting**: Split `T022` and `T025` into discrete sub-tasks for Null Model, Full Model, and Bayesian Model. Execute each model fitting step independently, verifying convergence and output schema before proceeding. **Deliverable**: `data/model_fitting_atomic_log.json` with `{"model": "name", "status": "SUCCESS"|"FAILED", "convergence_verified": bool}`. **Rationale**: Isolates model fitting failures and ensures each model is valid before comparison. **DEPENDS ON**: T062, T104.
- [ ] T064 [P] **Atomic Evaluation**: Split `T029` and `T030` into discrete sub-tasks for metric calculation and hypothesis testing. Execute metric calculation first, then hypothesis testing, verifying each output before proceeding. **Deliverable**: `data/evaluation_atomic_log.json` with `{"step": "name", "status": "SUCCESS"|"FAILED", "output_valid": bool}`. **Rationale**: Ensures evaluation metrics are calculated correctly before hypothesis testing, preventing invalid statistical conclusions. **DEPENDS ON**: T063, T105.
- [ ] T065 [P] **Atomic Report Generation**: Split `T057` into discrete sub-tasks for each report section (Executive Summary, Methodology, Results, Conclusion). Generate each section independently and verify it contains the required data before assembling the final report. **Deliverable**: `data/report_atomic_log.json` with `{"section": "name", "status": "SUCCESS"|"FAILED", "data_present": bool}`. **Rationale**: Ensures each section of the report is complete and accurate before final assembly, preventing missing or incorrect information in the final output. **DEPENDS ON**: T064, T106.

---

## Phase N+6: Documentation Finalization (Moved from Phase N)

**Purpose**: Update documentation based on final results.

- [X] T033b [P] Documentation updates: Update `docs/research.md` with 'Results' section (include model coefficients, VIF, AUC delta). **DEPENDS ON**: T044.
- [X] T033c [P] Documentation updates: Update `docs/research.md` with 'Limitations' section (include sampling constraints, VIF stability, sensitivity analysis). **DEPENDS ON**: T048, T047.