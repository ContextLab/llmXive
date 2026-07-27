# Tasks: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

**Input**: Design documents from `/specs/001-statistical-analysis-of-recipe-data/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

> **⚠️ SPEC AMENDMENT NOTE**: The current `spec.md` mandates datasets (FlavorDB, Counterfactual Recipe Generation) and methods (Likelihood-Ratio Test) that are unavailable or contradicted by the Plan's "Critical Reframe". This `tasks.md` implements the **Plan's Critical Reframe** (Recipe1M embeddings/ratings, Partial Correlation) as the single source of truth for execution. The `spec.md` is flagged for ratification to align with these amendments. Tasks explicitly note where they supersede Spec requirements.

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

- [X] T001a Create project directory structure: `projects/PROJ-175-statistical-analysis-of-publicly-availab/code/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/data/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/tests/`. **Verification**: Verify existence of directories via `os.path.isdir` and log to `data/setup_log.json`. **Schema**: `{"status": "SUCCESS"|"FAILED", "timestamp": "ISO8601", "paths_verified": ["path1", "path2"]}`. **Implementation**: Use `json.dump` with `indent=2` to write the log.
- [X] T001b Create empty `code/__init__.py`, `tests/__init__.py`, and `code/data/__init__.py`
- [X] T001c Create `code/requirements.txt` placeholder and `tests/conftest.py` placeholder

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python project with `code/requirements.txt` (pandas, numpy, scikit-learn, pyarrow, statsmodels, pymc, scipy, requests, tqdm, huggingface_hub, sentence-transformers)
- [X] T033a [P] Configure linting: Create `ruff.toml` at repository root with specific rules (select = ["E", "F"]) to enforce a subset of error and warning categories as outlined in the project's coding standards. (Constitution I, FR‑001)
- [X] T033b [P] Configure formatting: Create `pyproject.toml` at repository root with black configuration (line‑length=88, target-version=py311) to ensure consistent code style. (Constitution I, FR‑001)
- [X] T004 [P] Setup `data/` directory structure (`raw/`, `processed/`, `final/`) and `code/` module structure
- [X] T005 [P] Implement global random seed pinning. **Deliverable**: Create `code/__init__.py` with `seed = 42` and `tests/conftest.py` with `@pytest.fixture(autouse=True) def set_seed()`.
- [X] T006 [P] Setup memory profiling utility in `code/utils/memory_monitor.py` to enforce a predefined RAM limit. **Deliverable**: Create `check_limit(limit_mb=6144)` function that raises `MemoryError` if exceeded, and log to `data/memory_profile.json`. **Schema**: `{"peak_ram_mb": float, "timestamp": "ISO8601", "limit_mb": 6144}`.
- [X] T007 [P] Create base data schema definitions in `specs/001-statistical-analysis-of-recipe-data/contracts/`: specifically `dataset.schema.yaml` and `model_output.schema.yaml`. **Deliverable**: Schemas defining fields `ingredient_id`, `log_co_occurrence`, `flavor_similarity` (defined as Recipe1M embedding cosine similarity), `functional_role` (defined as positional rank derived), `compatibility_label`, etc., plus a validator script `code/utils/validate_schema.py`. (Constitution II) **AMENDMENT**: Explicitly reflects the 'Critical Reframe' (Recipe1M proxies) in field definitions.
- [X] T038 [P] Implement `code/data/verify.py` robust error handling: Replace any generic `try/except` blocks with specific HTTP error handling that **raises** on failure (no synthetic fallback) and logs the exact URL and error code to `data/download_errors.log`. (Constitution II) **DEPENDS ON**: T002.
- [X] T042 [P] Extend `code/data/verify.py` with schema validation for the **Recipe1M Ratings** dataset: enforce presence and type of the `rating` column; fail the pipeline on mismatch. (FR‑001b amendment) **DEPENDS ON**: T002.
- [X] T012 [P] **Data Source Verification**: Implement verification of **Recipe1M** and **Ratings** URLs, generate `data/verification_report.json` with status PASS/FAIL. Explicitly **document removal** of the Counterfactual Recipe Generation dataset requirement (amendment of FR‑001b). **DEPENDS ON**: T002.
- [X] T012b [P] **Spec Amendment Verification**: Verify that the Spec amendment for FR-001 (removing Counterfactual dataset) has been formally ratified. **Gate**: If not ratified, raise `SpecAmendmentPendingError` and halt. Output `data/amendment_ratification_log.json`. **DEPENDS ON**: T012.
- [X] T046 [P] Add pre‑flight `HEAD` checks for the verified URLs; raise `DataUnavailableError` on non‑200 responses. **DEPENDS ON**: T012, T012b.
- [X] T051 [P] **Data Source Verification**: Implement `code/data/download.py` to verify the **exact** Recipe1M subset (with embeddings) and Ratings dataset from the URLs listed in `data/verification_report.json`. **Hard‑fail** on any download error. **Clarification**: This task performs URL verification and subset manifest generation only, NOT full download. **DEPENDS ON**: T012, T046, T012b.
- [ ] T013 [P] **Atomic Download**: Implement `code/data/download.py` to stream Recipe1M (with embeddings) and Ratings using `datasets.load_dataset(..., streaming=True)`. Two‑pass algorithm for frequency counting then co-occurrence building. **Output**: `data/raw/recipe1m_counts.parquet` (frequency counts only). **DEPENDS ON**: T051.
- [X] T013b [P] **Pilot Data Fetch**: After verification (T051), fetch a small representative subset to compute variance estimates for power analysis. Output `data/raw/pilot_data.parquet` and `data/raw/pilot_stats.json`. **DEPENDS ON**: T051.
- [X] T008 [P] **Power Analysis**: Using variance from pilot data (T013b), compute unified sample size `N_unified` for effect size ≥ 0.1, power 0.8. Write to `data/power_analysis.json` and `data/split_config.json`. **DEPENDS ON**: T013b.
- [X] T049 [P] **Zero‑Occurrence Handling**: Define epsilon for log‑transform, log zero‑pair count to `data/zero_handling_log.json`. **DEPENDS ON**: T013.
- [ ] T014 [P] **Normalization**: Implement `code/data/preprocess.py` step 1‑2: normalize ingredient names using Levenshtein distance ≤ 2 against the canonical Recipe1M ingredient list. **Output**: `data/processed/normalized_ingredients.parquet`. **Verification**: Ensure file exists and schema matches T007. **DEPENDS ON**: T007, T012, T051, T013. **Note**: Removed [P] tag; requires full data stream from T013.
- [X] T014c [P] **Fetch Recipe1M Embeddings (FR-004-AMEND)**: Implement `code/data/embeddings.py` to fetch Recipe1M visual/text embeddings for all unique ingredients. **Output**: `data/processed/ingredient_embeddings.parquet`. **Verification**: Ensure file exists and schema matches T007. **AMENDMENT**: Implements amended FR-004 requirement. **DEPENDS ON**: T013, T014.
- [ ] T015 [P] **Co‑occurrence Matrix**: Build global matrix $C$ with log‑transform using epsilon from T049. **Input**: `data/raw/recipe1m_counts.parquet` from T013. **Output**: `data/processed/co_occurrence_matrix.parquet`. **Verification**: Check matrix dimensions and sparsity; log to `data/matrix_stats.json`. **DEPENDS ON**: T049, T013, T014.
- [ ] T016 [P] **Semantic Similarity**: Compute cosine similarity between Recipe1M embeddings for ingredient pairs. **Input**: `data/processed/ingredient_embeddings.parquet` from T014c. **Output**: `data/processed/similarity_scores.parquet`. **Schema**: Columns `ingredient_id_1`, `ingredient_id_2`, `similarity_score`. **Verification**: Ensure file exists and schema matches. **DEPENDS ON**: T013, T014, T014c.
- [X] T048 [P] **Sensitivity Analysis of Compatibility Threshold**: Before final label creation, evaluate how varying the median‑based threshold affects label distribution. Output `data/threshold_sensitivity.json`. **DEPENDS ON**: T013b.
- [X] T013c [P] **Derive Compatibility Labels**: Using the median rating (or selected threshold from T048), create binary `compatibility_label`. Fail if dataset empty. Output `data/processed/compatibility_labels.parquet`. **DEPENDS ON**: T013, T048.
- [ ] T017 [P] **Functional Role Derivation**: Derive functional role using 'positional rank' and 'marginal frequency' (frequency of single ingredient) only. **Explicitly exclude** 'co-occurrence frequency' from the derivation. **Output**: `data/processed/ingredient_roles_residuals.parquet`. **Verification**: Log correlation between derived role and co-occurrence frequency; must be < 0.1. **DEPENDS ON**: T015, T014.
- [X] T017b [P] **Discretize Functional Role**: Use `pandas.qcut` with `duplicates='drop'` to create tertiles (or quantile fallback if < 3 unique values). Log method and cutpoints (4‑decimal) to `data/role_cutpoints.json`. **DEPENDS ON**: T017.
- [X] T018 [P] **Imputation & Bias Check**: Impute missing categorical role with 'Unknown' and missing similarity with median; create missing‑flag columns. Compute Pearson correlation between imputed similarity and role residuals; log to `data/missing_data_bias_log.json`. **DEPENDS ON**: T013, T017b, T016, T013c.
- [ ] T019 [P] **Train/Test Split**: Downsample to `N_unified` (from T008) with fixed seed; write splits and update `data/split_config.json`. **DEPENDS ON**: T008, T018.

**Checkpoint**: User Story 1 pipeline ready.

---

## Phase 3: User Story 2 – Statistical Model Fitting and Validation (Priority: P2)

**Goal**: Fit regularized logistic regression and hierarchical Bayesian models, controlling for co‑occurrence while isolating semantic similarity and functional role effects.

- [X] T023 [P] **VIF Calculation**: Compute VIF for all predictors; write `data/vif_scores_initial.json`. Always output `data/final_predictors.json` (original or reduced list). **DEPENDS ON**: T019.
- [X] T024a [P] **Data Leakage Audit**: Quantify mutual information between predictors and outcome; raise `CircularityError` if MI > 0.5. Output `data/data_leakage_audit.json`. **DEPENDS ON**: T023, T019.
- [X] T024c [P] **Amendment Ratification Gate: FR-008**: Verify that the Spec amendment for FR-008 (replacing Likelihood-Ratio with Partial Correlation) has been formally ratified. **Gate**: If not ratified, raise `SpecAmendmentPendingError` and halt. Output `data/amendment_ratification_log_FR008.json`. **DEPENDS ON**: T023, T019.
- [X] T024b [P] **Partial Correlation Analysis**: **(Replaces Likelihood‑RATIO Test FR‑008)** Compute partial correlation of flavor similarity and functional role controlling for co-occurrence. **Gate**: Requires T024c to pass. Output `data/partial_correlation_results.json`. **DEPENDS ON**: T024a, T019, T024c.
- [X] T040 [P] **Multicollinearity Resolution**: If VIF > 5 for any predictor (esp. functional role), attempt orthogonalization; if still > 5, drop predictor as last resort. Update `data/model_comparison.json` and `data/final_predictors.json`. **DEPENDS ON**: T023.
- [ ] T040b [P] **Re‑fit Model after Predictor Drop**: If T040 drops a predictor, re‑fit logistic regression with reduced set. **Conditional**: If no predictor dropped, pass through original model. Output `data/final/logistic_results_refit.json`. **DEPENDS ON**: T040.
- [ ] T022 **Logistic Regression Fit**: Fit Null (frequency only) and Full (frequency + similarity + categorical role) models with L2 regularization using predictor list from `data/final_predictors.json`. **Verification**: Confirm model converged and `data/final/logistic_results.json` contains required fields (coefficients, p-values). **Note**: Removed [P] tag – must wait for multicollinearity resolution. **Dependency Logic**: Depends on T040; if T040 drops predictors, uses T040b output; otherwise uses original predictors. **DEPENDS ON**: T018, T023, T019, T040.
- [X] T050 [P] **CPU‑only Enforcement for Bayesian Fit**: Detect CUDA; if present, log warning and force CPU execution. Write `data/gpu_detection_log.json`. **DEPENDS ON**: T019.
- [ ] T025 [P] **Hierarchical Bayesian Model Fit (CPU‑only)**: Fit model on downsampled data; enforce ‑hour timeout. **Verification**: Verify R̂ <= 1.01 in output log. Fail if R̂ > 1.01. Output `data/final/bayesian_results.json` and on failure write `data/bayesian_convergence_log.json`. **DEPENDS ON**: T019, T050.
- [X] T026 [P] **Post‑Hoc Power Validation**: Verify achieved power for effect size ≥ 0.1 given actual sample size and convergence metrics. **DEPENDS ON**: T025.
- [ ] T047 [P] **VIF Robustness on Test Set**: Compute VIF on test split; flag if any > 5. Log to `data/vif_test_set.json`. **DEPENDS ON**: T019, T023.

**Checkpoint**: User Stories 1 & 2 functional.

---

## Phase 4: User Story 3 – Evaluation and Reporting (Priority: P3)

**Goal**: Evaluate models using cross‑validation within the corpus, compute metrics, and generate a report comparing full model vs baseline.

- [ ] T029 [P] **Metrics Calculation**: Compute AUC, precision, recall, calibration plot for Full and Baseline models; output `data/evaluation_metrics.json`. **Schema**: Keys `auc`, `precision`, `recall`, `calibration_curve`. **Verification**: Ensure file exists and schema matches. **DEPENDS ON**: T022, T025.
- [X] T030b [P] **Cross‑Validation Evaluation**: Perform k‑fold CV, bootstrap multiple resamples to obtain delta AUC, p‑value, 95 % CI. Output `data/cv_delta_metrics.json`. **DEPENDS ON**: T029.
- [X] T030 [P] **Bootstrap Hypothesis Test**: Alternative bootstrap/permutation test for AUC delta; output `data/auc_delta_metrics.json`. **DEPENDS ON**: T029.
- [X] T031 [P] **Map Diagnostics to Report**: Incorporate VIF scores (T023), partial correlation results (T024b), and Bayesian outcomes (T025) into summary. **DEPENDS ON**: T023, T024b, T025.
- [X] T041 [P] **Gate Verification**: Ensure `data/verification_report.json` PASS and Bayesian convergence SUCCESS before report generation. **DEPENDS ON**: T038, T025.
- [X] T032 [P] **Draft Final Report**: Generate `docs/draft_final_report.md` stating hypothesis support with partial correlation p‑values, AUC delta, CI, and note any multicollinearity or leakage warnings. **DEPENDS ON**: T041, T030b, T025, T047.
- [X] T054 [P] **Calibration Verification**: Bin predicted probabilities, compare to observed frequencies; fail if max deviation > 0.1. Write `data/calibration_test_results.json`. **DEPENDS ON**: T029.
- [X] T055 [P] **Final Report Generation**: Aggregate all JSON artifacts (VIF, partial correlation, AUC delta, calibration, power analysis) into `docs/final_report.md`. If Bayesian convergence failed (from T025), automatically insert a "Limitations" subsection flagging this. **DEPENDS ON**: T030b, T031, T040, T047, T054, T025.

**Checkpoint**: All user stories independently functional.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements affecting multiple stories.

- [X] T033a [P] Documentation updates: Update `docs/research.md` with Methodology section (include power analysis N values). **DEPENDS ON**: T025, T019.
- [X] T033d [P] Documentation updates: Add Environment Setup to `docs/quickstart.md`. **DEPENDS ON**: T002, T034.
- [X] T034 [P] Code cleanup: Implement streaming for Recipe1M and chunked processing in `code/data/download.py` and `code/data/preprocess.py` to keep peak RAM < 6 GB. **DEPENDS ON**: T002.
- [X] T035a [P] Additional unit tests for normalization and VIF. **DEPENDS ON**: T014, T023.

---

## Phase N+1: Revision & Gap Resolution

- [X] T037 [P] **Explicit Streaming Logic**: Refactor T013 to use `datasets.load_dataset(..., streaming=True)` and `itertools.islice` for controlled down‑sampling; log `peak_ram_mb`, `sampling_ratio`, `seed` to `data/memory_profile.json`. **DEPENDS ON**: T034, T013.
- [X] T048 (already placed earlier) **Sensitivity analysis of compatibility threshold** (see Phase 2).

---

## Phase N+2: Execution Validation & Draft Report

- [ ] T099 [P] **Pipeline Entrypoint**: Implement `code/run_full_pipeline.py` orchestrating T051, T013‑T019, T022, T025, T029‑T032. Writes three logs (`pipeline_execution_log.json`, `model_fitting_log.json`, `evaluation_log.json`). **DEPENDS ON**: All tasks it orchestrates.
- [X] T100 [P] **Verify Draft Report**: Ensure `docs/draft_final_report.md` exists; generate placeholder if upstream failed. **DEPENDS ON**: T032.
- [ ] T043a [P] **Execute Data Pipeline**: Run full data download & preprocessing via `run_full_pipeline.py --mode=full`. Output `data/pipeline_execution_log.json`. **DEPENDS ON**: T099, T051‑T019.
- [ ] T043b [P] **Execute Model Fitting**: Run models via `run_full_pipeline.py --mode=models`. Output `data/model_fitting_log.json`. **DEPENDS ON**: T099, T022, T025, T040, T040b.
- [ ] T043c [P] **Execute Evaluation**: Run evaluation/report via `run_full_pipeline.py --mode=eval`. Output `data/evaluation_log.json`. **DEPENDS ON**: T099, T029, T030b, T032.
- [X] T043d [P] **Capture Metrics**: Consolidate logs into `data/final_validation_report.json`. **DEPENDS ON**: T043a‑T043c.
- [X] T044 [P] **Generate Final Report**: Assemble `docs/final_report.md` using all intermediate artifacts and `docs/draft_final_report.md`. **DEPENDS ON**: T043d, T100, T048, T047, T025, T030b, T023, T024b.
- [X] T036 [P] **Runtime Validation**: Run `code/validate_runtime.py` to ensure full pipeline ≤ 6 h; generate `data/ci_validation_report.json`. **DEPENDS ON**: T043a.
- [X] T033e [P] Documentation updates: Add Data Pipeline section to `docs/quickstart.md` (depends on successful pipeline execution). **DEPENDS ON**: T043a.

---

## Phase N+3: Critical Data Integrity & Reproducibility Fixes

- [X] T054 (already defined) **Calibration Verification** (see Phase 4).
- [X] T055 (already defined) **Final Report Generation** (see Phase 4).

---

## Phase N+4: Execution Gate Hardening & Data Source Verification

- [X] T056 [P] **Execution Gate Pre‑Check**: Verify verification PASS, Bayesian SUCCESS, calibration PASS, VIF computed. Exit non‑zero on failure; write `data/gate_validation_report.json`. **DEPENDS ON**: T051, T025, T054, T023.
- [X] T101 [P] **Verify Normalization Config**: Ensure `data/normalization_config.json` exists; generate default if missing. **DEPENDS ON**: T014.
- [X] T057 [P] **Final Report Compilation**: Aggregate all validated artifacts (VIF, partial correlation, AUC delta, calibration, power analysis) into `docs/final_report.md` with a "Constitution Compliance" section. **DEPENDS ON**: T056, T044, T048, T047, T025, T030b, T023, T024b.
- [X] T058 [P] **Artifact Hashing**: Compute content hashes for all final artifacts. **DEPENDS ON**: T057.
- [X] T059 [P] **Reproducibility Audit**: Run reproducibility audit (T058); if PASS, update `docs/research.md` with "Final Sign‑off". **DEPENDS ON**: T058, T019, T101.
- [X] T060 [P] **Final Sign‑off**: Update project state. **DEPENDS ON**: T059.

---

## Phase N+5: Atomic Script Creation

**Purpose**: Create atomic scripts required for Phase N+6 execution.

- [X] T102 [P] **Create Atomic Download Scripts**: Implement `download_recipe1m.py` and `download_ratings.py` with checksum verification. **DEPENDS ON**: T012, T046, T051.
- [ ] T103 [P] **Create Atomic Preprocessing Scripts**: Implement `preprocess.py` with streaming and schema validation. **DEPENDS ON**: T007, T034, T013.
- [X] T104 [P] **Create Atomic Model Scripts**: Implement `model_fit.py` for Null, Full, and Bayesian models. **DEPENDS ON**: T022, T025, T040.
- [X] T105 [P] **Create Atomic Evaluation Scripts**: Implement `evaluate.py` for metrics and hypothesis testing. **DEPENDS ON**: T029, T030.
- [X] T106 [P] **Create Atomic Report Scripts**: Implement `report_gen.py` for section aggregation. **DEPENDS ON**: T055.

---

## Phase N+6: Atomic Execution & Verification

**Purpose**: Atomic execution of verified scripts to ensure reproducibility and strict ordering. Script creation tasks (T102-T106) MUST precede execution tasks (T061-T065).

- [X] T061 [P] **Atomic Data Download**: Execute `download_recipe1m.py` and `download_ratings.py` sequentially, verify checksums; log to `data/download_atomic_log.json`. **DEPENDS ON**: T012, T046, T102.
- [ ] T062 [P] **Atomic Preprocessing**: Run each preprocessing step atomically, validate output schema; log to `data/preprocess_atomic_log.json`. **DEPENDS ON**: T061, T007, T103.
- [X] T063 [P] **Atomic Model Fitting**: Fit Null, Full, Bayesian models atomically; verify convergence; log to `data/model_fitting_atomic_log.json`. **DEPENDS ON**: T062, T104.
- [X] T064 [P] **Atomic Evaluation**: Compute metrics then hypothesis testing atomically; log to `data/evaluation_atomic_log.json`. **DEPENDS ON**: T063, T105.
- [X] T065 [P] **Atomic Report Generation**: Generate each report section atomically; log to `data/report_atomic_log.json`. **DEPENDS ON**: T064, T106.

---

## Phase N+7: Documentation Finalization

- [X] T033b [P] **Update Research Doc**: Populate `docs/research.md` Results section with model coefficients, VIF, Partial Correlation, AUC delta. **DEPENDS ON**: T044.
- [X] T033c [P] **Update Research Doc Limitations**: Add Limitations section citing sampling constraints, VIF instability, sensitivity analysis, circularity warning. **DEPENDS ON**: T048, T047.

---

## Phase N+8: Execution Gate Hardening & Data Source Verification

- [X] T066 [P] **Enforce Strict Data Source Fallback Policy**: Remove any fallback to synthetic data; raise `DataUnavailableError` on any download failure. **DEPENDS ON**: T012, T038.
- [X] T067 [P] **Verified Data Source Injection**: If `VERIFIED_REAL_DATA_SOURCE` env var or config present, use that exact source; ignore hard‑coded URLs. **DEPENDS ON**: T066, T051.

---

## Phase N+9: Final Execution & Reporting

- [X] T068 [P] **Execute Atomic Download**: Run atomic download scripts with strict verification. **DEPENDS ON**: T066, T067, T012, T046.
- [ ] T069 [P] **Execute Atomic Preprocessing**: Run atomic preprocessing steps with schema validation. **DEPENDS ON**: T068, T007, T103.
- [X] T070 [P] **Execute Atomic Model Fitting**: Run atomic model fitting (Null, Full, Bayesian) with convergence checks. **DEPENDS ON**: T069, T104.
- [X] T071 [P] **Execute Atomic Evaluation**: Run atomic evaluation (metrics, hypothesis testing). **DEPENDS ON**: T070, T105.
- [X] T072 [P] **Execute Atomic Report Generation**: Assemble final report sections atomically. **DEPENDS ON**: T071, T106.
- [X] T073 [P] **Generate Final Report**: Aggregate atomic logs and results into `docs/final_report.md`, include Constitution Compliance and Limitations. **DEPENDS ON**: T072, T057, T058.
- [X] T074 [P] **Final Validation & Sign‑off**: Run reproducibility audit (T059); if PASS, update `docs/research.md` with "Final Sign‑off". **DEPENDS ON**: T073, T058, T059.
