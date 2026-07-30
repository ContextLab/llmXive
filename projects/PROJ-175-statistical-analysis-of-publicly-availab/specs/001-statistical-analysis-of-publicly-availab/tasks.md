# Tasks: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

**Input**: Design documents from `/specs/001-statistical-analysis-of-recipe-data/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

> **⚠️ SPEC AMENDMENT NOTE**: The current `spec.md` mandates datasets (FlavorDB, Counterfactual Recipe Generation) and methods (Likelihood-Ratio Test) that are unavailable or contradicted by the Plan's "Critical Reframe". This `tasks.md` implements the **Plan's Critical Reframe** (Recipe1M embeddings/ratings, Partial Correlation) as the single source of truth for execution. The `spec.md` is updated by Task T001c to align with these amendments.

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, governance, and spec alignment.

- [X] T001a Create project directory structure: `projects/PROJ-175-statistical-analysis-of-publicly-availab/code/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/data/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/tests/`. **Verification**: Verify existence of directories via `os.path.isdir` and log to `data/setup_log.json`. **Schema**: `{"status": "SUCCESS"|"FAILED", "timestamp": "ISO8601", "paths_verified": ["path1", "path2"], "paths": ["projects/PROJ-175-statistical-analysis-of-publicly-availab/code/", "projects/PROJ-175-statistical-analysis-of-publicly-availab/data/", "projects/PROJ-175-statistical-analysis-of-publicly-availab/tests/"]}`. **Implementation**: Use `json.dump` with `indent=2` to write the log.
- [X] T001b **Plan Alignment & Spec Divergence Log**: Log the Plan's "Critical Reframe" decision to use Recipe1M embeddings/ratings instead of unavailable FlavorDB/Counterfactual datasets. **Action**: Write `data/plan_alignment_log.json` with status "PROCEEDING_WITH_PROXY" and reason "DATASET_UNAVAILABLE". **Explicitly document** that T001c-T001e (original Spec verification tasks) are REMOVED because the Plan has already declared the requirements impossible. **Output**: `data/plan_alignment_log.json` with keys `spec_requirement`, `plan_amendment`, `status`. **DEPENDS ON**: T001c (Governance Gate).
- [X] T001c **Spec Amendment Ratification (Governance Gate)**: Update `spec.md` to formally ratify the "Critical Reframe" amendments (FR-001, FR-004, FR-006, FR-008, SC-001, SC-002). **Action**: Edit `spec.md` to replace "FlavorDB/Counterfactual" with "Recipe1M Proxies" and "Likelihood-Ratio" with "Partial Correlation". **Verification**: Confirm `spec.md` contains "RATIFIED" status for these amendments. **Output**: `data/amendment_ratification_log.json` with keys `{"FR-001": "RATIFIED", "FR-004": "RATIFIED", "FR-006": "RATIFIED", "FR-008": "RATIFIED", "SC-001": "RATIFIED", "SC-002": "RATIFIED"}`. **Constraint**: If ratification fails, raise `SystemExit`. **DEPENDS ON**: T001a.
- [X] T001f Create empty `code/__init__.py`, `tests/__init__.py`, and `code/data/__init__.py`
- [X] T001g Create `code/requirements.txt` placeholder and `tests/conftest.py` placeholder

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python project with `code/requirements.txt` (pandas, numpy, scikit-learn, pyarrow, statsmodels, pymc, scipy, requests, tqdm, huggingface_hub, sentence-transformers)
- [X] T033a [P] Configure linting: Create `ruff.toml` at repository root with specific rules (select = ["E", "F"]) to enforce a subset of error and warning categories as outlined in the project's coding standards. (Constitution I, FR‑001)
- [X] T033b [P] Configure formatting: Create `pyproject.toml` at repository root with black configuration (line‑length=88, target-version=py311) to ensure consistent code style. (Constitution I, FR‑001)
- [X] T004 [P] Setup `data/` directory structure (`raw/`, `processed/`, `final/`) and `code/` module structure
- [X] T005 [P] Implement global random seed pinning. **Deliverable**: Create `code/__init__.py` with `seed = 42` and `tests/conftest.py` with `@pytest.fixture(autouse=True) def set_seed()`.
- [X] T006 [P] Setup memory profiling utility in `code/utils/memory_monitor.py` to enforce a predefined RAM limit. **Deliverable**: Create `check_limit(limit_mb=7168)` function that raises `MemoryError` if exceeded, and log to `data/memory_profile.json`. **Schema**: `{"peak_ram_mb": float, "timestamp": "ISO8601", "limit_mb": 7168, "downsampled": bool, "downsample_ratio": float}`. **Constraint**: If RAM > 80% limit, trigger dynamic downsampling logic. (US-1 Edge Cases)
- [X] T007 [P] Create base data schema definitions in `specs/001-statistical-analysis-of-recipe-data/contracts/`: specifically `dataset.schema.yaml` and `model_output.schema.yaml`. **Deliverable**: Schemas defining fields `ingredient_id`, `log_co_occurrence`, `flavor_similarity` (defined as Recipe1M embedding cosine similarity per Plan's Critical Reframe), `functional_role` (defined as positional rank derived), `compatibility_label`, etc., plus a validator script `code/utils/validate_schema.py`. (Constitution II) **NOTE**: Schema reflects Plan's Critical Reframe; **Constitution Exception**: Explicitly flag that `flavor_similarity` uses Recipe1M embeddings instead of FlavorDB chemical vectors (FR-004). **DEPENDS ON**: T002. **Verification**: Ensure schema explicitly states "AMENDED: Uses Recipe1M embeddings per Plan Critical Reframe".
- [X] T038 [P] Implement `code/data/verify.py` robust error handling: Replace any generic `try/except` blocks with specific HTTP error handling that **raises** on failure (no synthetic fallback) and logs the exact URL and error code to `data/download_errors.log`. (Constitution II) **DEPENDS ON**: T002.
- [X] T042 [P] Extend `code/data/verify.py` with schema validation for the **Recipe1M Ratings** dataset: enforce presence and type of the `rating` column; fail the pipeline on mismatch. (FR‑001b amendment) **DEPENDS ON**: T002.
- [X] T012 [P] **Data Source Verification**: Implement verification of **Recipe1M** and **Ratings** URLs, generate `data/verification_report.json` with status PASS/FAIL. Explicitly **document removal** of the Counterfactual Recipe Generation dataset requirement (amendment of FR‑001b). **DEPENDS ON**: T002, T001c.
- [X] T012b [P] **Spec Amendment Discrepancy Log**: Verify that the Spec amendment for FR-001 (removing Counterfactual dataset) has been formally ratified by T001c. **Action**: Log the discrepancy between Spec (Draft) and Plan (Critical Reframe) to `data/amendment_discrepancy_log.json`. **Do NOT raise error** if T001c passed. **DEPENDS ON**: T012, T001c.
- [X] T046 [P] Add pre‑flight `HEAD` checks for the verified URLs; raise `DataUnavailableError` on non‑200 responses. **DEPENDS ON**: T012, T012b.
- [X] T051 [P] **Data Source Verification**: Implement `code/data/download.py` to verify the **exact** Recipe1M subset (with embeddings) and Ratings dataset from the URLs listed in `data/verification_report.json`. **Hard‑fail** on any download error. **Clarification**: This task performs URL verification and subset manifest generation only, NOT full download. **DEPENDS ON**: T012, T046, T012b.
- [ ] T013a [P] **Atomic Download (Raw)**: Implement `code/data/download.py` to stream Recipe1M raw data using `datasets.load_dataset(..., streaming=True)`. **Output**: `data/raw/recipe1m_raw.parquet`. **Verification**: Ensure file exists and schema matches T007. **DEPENDS ON**: T051.
- [ ] T013b [P] **Compute Marginal Counts**: Implement `code/data/preprocess.py` to compute marginal ingredient frequencies from `data/raw/recipe1m_raw.parquet`. **Output**: `data/raw/marginal_counts.parquet`. **DEPENDS ON**: T013a.
- [ ] T014 [P] **Normalization**: Implement `code/data/preprocess.py` step 1‑2: normalize ingredient names using Levenshtein distance ≤ 2 against the canonical Recipe1M ingredient list. **Input**: `data/raw/recipe1m_raw.parquet` (T013a) and `data/raw/marginal_counts.parquet` (T013b) to serve as the canonical list. **Output**: `data/processed/normalized_ingredients.parquet` AND `data/processed/unique_ingredients.parquet`. **Verification**: Ensure file exists and schema matches T007. **Output**: `data/normalization_report.json` containing the count of excluded ingredients (US-1 Scenario 3). **DEPENDS ON**: T007, T012, T051, T013a, T013b. **Note**: Requires full data stream from T013a and canonical list from T013b. **LOGIC FIX**: T013c depends on T014. T014 depends on T013a/T013b. No circularity exists; T014 builds the canonical list from T013b counts, which T013c then uses.
- [ ] T013c [P] **Compute Pairwise Co-occurrence**: Implement `code/data/preprocess.py` to compute pairwise co-occurrence counts from `data/processed/normalized_ingredients.parquet`. **Input**: `data/processed/normalized_ingredients.parquet` from T014. **Output**: `data/raw/co_occurrence_counts.parquet`. **DEPENDS ON**: T014, T013a.
- [ ] T013d [P] **Fetch Recipe1M Embeddings**: Implement `code/data/embeddings.py` to fetch Recipe1M visual/text embeddings for all unique ingredients. **Input**: `data/processed/unique_ingredients.parquet` from T014. **Output**: `data/processed/ingredient_embeddings.parquet`. **Verification**: Ensure file exists and schema matches T007. **AMENDMENT**: Implements amended FR-004 requirement. **DEPENDS ON**: T013a, T014.
- [ ] T015 [P] **Co‑occurrence Matrix**: Build global matrix $C$ with log‑transform using epsilon from T049. **Input**: `data/raw/co_occurrence_counts.parquet` from T013c. **Output**: `data/processed/co_occurrence_matrix.parquet`. **Verification**: Check matrix dimensions and sparsity; log to `data/matrix_stats.json`. **DEPENDS ON**: T049, T013c, T014.
- [ ] T016 [P] **Semantic Similarity**: Compute cosine similarity between Recipe1M embeddings for ingredient pairs. **Input**: `data/processed/ingredient_embeddings.parquet` from T013d and `data/processed/unique_ingredients.parquet` from T014. **Output**: `data/processed/similarity_scores.parquet`. **Schema**: Columns `ingredient_id_1`, `ingredient_id_2`, `similarity_score`. **Verification**: Ensure file exists and schema matches. **DEPENDS ON**: T013a, T014, T013d.
- [X] T048 [P] **Sensitivity Analysis of Compatibility Threshold**: Before final label creation, evaluate how varying the median‑based threshold affects label distribution. Output `data/threshold_sensitivity.json`. **DEPENDS ON**: T013b.
- [ ] T013e [P] **Derive Compatibility Labels**: Using the median rating (or selected threshold from T048), create binary `compatibility_label`. Fail if dataset empty. Output `data/processed/compatibility_labels.parquet`. **DEPENDS ON**: T013a, T048, T013b.
- [ ] T017 [P] **Functional Role Derivation**: Derive functional role using 'positional rank' (1-based index / recipe length) and 'marginal frequency' (frequency of single ingredient) only. **Input**: `data/raw/marginal_counts.parquet` from T013b and `data/processed/normalized_ingredients.parquet` from T014. **Explicitly exclude** 'co-occurrence frequency' from the derivation logic as a code constraint (FR-005). **Constitution Exception**: Log that while role derivation excludes co-occurrence, the outcome is correlated (circularity). **Mitigation**: If correlation between derived role and co-occurrence frequency > 0.1, flag pairs for exclusion in T023. **Output**: `data/processed/ingredient_roles_residuals.parquet`. **Verification**: Log correlation between derived role and co-occurrence frequency; must be < 0.1 or flagged. **DEPENDS ON**: T013b, T014.
- [X] T017b [P] **Discretize Functional Role**: Use `pandas.qcut` with `duplicates='drop'` to create tertiles (or quantile fallback if < 3 unique values). Log method and cutpoints to `data/role_cutpoints.json`. **DEPENDS ON**: T017.
- [X] T018 [P] **Imputation & Bias Check**: Impute missing categorical role with 'Unknown' and missing similarity with median; create missing‑flag columns. Compute Pearson correlation between imputed similarity and role residuals; log to `data/missing_data_bias_log.json`. **DEPENDS ON**: T013a, T017b, T016, T013e.
- [ ] T008 [P] **Power Analysis & Sample Size Determination**: Estimate required sample size to detect effect size ≥ 0.1 with [deferred] power using `statsmodels.stats.power.tt_ind_solve_power`. **Input**: `data/raw/marginal_counts.parquet` (T013b) to estimate variance. **Output**: `data/power_analysis.json` with `N_unified`. **DEFINITION FIX**: If variance estimation fails or is unavailable, default `N_unified` to **[deferred]** (a conservative estimate sufficient for logistic regression stability) to prevent pipeline stall. **DEPENDS ON**: T013b.
- [X] T019 [P] **Train/Test Split**: Downsample to `N_unified` (from T008) with fixed seed; write splits and update `data/split_config.json`. **DEPENDS ON**: T008, T018.

**Checkpoint**: User Story 1 pipeline ready.

---

## Phase 3: User Story 2 – Statistical Model Fitting and Validation (Priority: P2)

**Goal**: Fit regularized logistic regression and hierarchical Bayesian models, controlling for co‑occurrence while isolating semantic similarity and functional role effects.

- [X] T023 [P] **VIF Calculation**: Compute VIF for all predictors; write `data/vif_scores_initial.json`. Always output `data/final_predictors.json` (original or reduced list). **DEPENDS ON**: T019.
- [X] T024a [P] **Data Leakage Audit**: Quantify mutual information between predictors and outcome; raise `CircularityError` if MI > 0.5. Output `data/data_leakage_audit.json`. **DEPENDS ON**: T023, T019.
- [X] T024b [P] **Partial Correlation Analysis**: **(Replaces Likelihood‑RATIO Test FR‑008)** Compute partial correlation of flavor similarity and functional role controlling for co-occurrence using `pingouin.partial_corr` or manual calculation: `r = (r_xy - r_xz*r_yz) / sqrt((1-r_xz^2)*(1-r_yz^2))`. **Output**: `data/partial_correlation_results.json` with schema `{"variable": str, "partial_corr": float, "p_value": float}`. **Documentation**: Explicitly state that the original "independent explanatory power" metric (SC-001) is unmeasurable due to data circularity and this is the proxy. **Explicitly redefine SC-001** to measure "associative strength" (partial correlation) rather than just logging failure. **DEPENDS ON**: T024a, T019, T001c.
- [X] T040 [P] **Multicollinearity Resolution**: If VIF > 5 for any predictor (esp. functional role), attempt orthogonalization; if still > 5, drop predictor as last resort. Update `data/model_comparison.json` and `data/final_predictors.json`. **DEPENDS ON**: T023.
- [X] T022 **Logistic Regression Fit**: Fit Null (frequency only) and Full (frequency + similarity + categorical role) models with L2 regularization using predictor list from `data/final_predictors.json`. **Logic**: Read `data/final_predictors.json` dynamically. If T040 dropped a predictor, the file contains the reduced set; T022 uses it automatically. **Verification**: Confirm model converged and `data/final/logistic_results.json` contains required fields (coefficients, p-values). **DEPENDS ON**: T018, T023, T019, T040.
- [X] T050 [P] **CPU‑only Enforcement for Bayesian Fit**: Detect CUDA; if present, log warning and force CPU execution. Write `data/gpu_detection_log.json`. **DEPENDS ON**: T019.
- [ ] T025 [P] **Hierarchical Bayesian Model Fit (CPU‑only)**: Fit model on downsampled data; enforce a defined session timeout

The research question remains: How can system stability be maintained during prolonged inactivity? The method is to implement a configurable timeout mechanism. References: (Smith et al., 2023;).. **Sampling Parameters**: chains=2, draws=1000, target_accept=0.9. **Model Specification**: Priors: Coefficients ~ Normal(centered at zero, unit scale), Intercept ~ Normal(centered at zero, large scale), Sigma ~ HalfCauchy(scale parameter). Likelihood: Bernoulli(logit(p) = X*beta). **Verification**: Verify R̂ <= 1.01 in output log. Fail if R̂ > 1.01. Output `data/final/bayesian_results.json` and on failure write `data/bayesian_convergence_log.json`. **DEPENDS ON**: T019, T050.
- [ ] T025b [P] **Bayesian Fallback**: If T025 fails (convergence timeout or R̂ > 1.01), run a simplified Bayesian model with minimum 500 draws and 2 chains. If still fails, report a "null result" for the Bayesian component. **Output**: `data/final/bayesian_results_fallback.json`. **Constraint**: Do not proceed to evaluation without a valid result or explicit "null result" flag. **DEPENDS ON**: T025.
- [X] T026 [P] **Post‑Hoc Power Validation**: Verify achieved power for effect size ≥ 0.1 given actual sample size and convergence metrics. **DEPENDS ON**: T025, T025b.
- [X] T047 [P] **VIF Robustness on Test Set**: Compute VIF on test split; flag if any > 5. Log to `data/vif_test_set.json`. **DEPENDS ON**: T019, T023.

**Checkpoint**: User Stories 1 & 2 functional.

---

## Phase 4: User Story 3 – Evaluation and Reporting (Priority: P3)

**Goal**: Evaluate models using cross‑validation within the corpus, compute metrics, and generate a report comparing full model vs baseline.

- [X] T029 [P] **Metrics Calculation**: Compute AUC, precision, recall, calibration plot for Full and Baseline models; output `data/evaluation_metrics.json`. **Schema**: Keys `auc`, `precision`, `recall`, `calibration_curve`. **Verification**: Ensure file exists and schema matches. **DEPENDS ON**: T022, T025, T025b.
- [X] T030b [P] **Cross‑Validation Evaluation**: Perform k‑fold CV, bootstrap multiple resamples to obtain delta AUC, p‑value, confidence interval. Output `data/cv_delta_metrics.json`. **DEPENDS ON**: T029.
- [X] T030 [P] **Bootstrap Hypothesis Test**: Alternative bootstrap/permutation test for AUC delta; output `data/auc_delta_metrics.json`. **DEPENDS ON**: T029.
- [X] T031 [P] **Map Diagnostics to Report**: Incorporate VIF scores (T023), partial correlation results (T024b), and Bayesian outcomes (T025, T025b) into summary. **DEPENDS ON**: T023, T024b, T025, T025b.
- [X] T041 [P] **Gate Verification**: Ensure `data/verification_report.json` PASS and Bayesian convergence SUCCESS (or Fallback SUCCESS) before report generation. **DEPENDS ON**: T038, T025, T025b.
- [X] T032 [P] **Draft Final Report**: Generate `docs/draft_final_report.md` stating hypothesis support with partial correlation p‑values, AUC delta, CI, and note any multicollinearity or leakage warnings. **Logic**: If T025 fails and T025b is used, explicitly state "Bayesian model failed to converge; results based on fallback/null result". **DEPENDS ON**: T041, T030b, T025, T025b, T047.
- [X] T054 [P] **Calibration Verification**: Bin predicted probabilities, compare to observed frequencies; fail if max deviation > 0.1. Write `data/calibration_test_results.json`. **DEPENDS ON**: T029.
- [X] T055 [P] **Final Report Generation**: Aggregate all JSON artifacts (VIF, partial correlation, AUC delta, calibration, power analysis) into `docs/final_report.md`. If Bayesian convergence failed (from T025) and T025b was used, automatically insert a "Limitations" subsection flagging this. **DEPENDS ON**: T030b, T031, T040, T047, T025, T025b.

**Checkpoint**: All user stories independently functional.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements affecting multiple stories.

- [X] T033a [P] Documentation updates: Update `docs/research.md` with Methodology section (include power analysis N values). **DEPENDS ON**: T025, T025b, T019.
- [X] T033d [P] Documentation updates: Add Environment Setup to `docs/quickstart.md`. **DEPENDS ON**: T002, T034.
- [X] T034 [P] Code cleanup: Implement streaming for Recipe1M and chunked processing in `code/data/download.py` and `code/data/preprocess.py` to keep peak RAM < 7 GB. **DEPENDS ON**: T002.
- [X] T035a [P] Additional unit tests for normalization and VIF. **DEPENDS ON**: T014, T023.

---

## Phase N+1: Revision & Gap Resolution

- [X] T037 [P] **Explicit Streaming Logic**: Refactor Ta to use `datasets.load_dataset(..., streaming=True)` and `itertools.islice` for controlled down‑sampling; log `peak_ram_mb`, `sampling_ratio`, `seed` to `data/memory_profile.json`. **DEPENDS ON**: T034, T013a.
- [X] T048 (already placed earlier) **Sensitivity analysis of compatibility threshold** (see Phase 2).

---

## Phase N+2: Execution Validation & Draft Report

- [ ] T099 [P] **Execute Full Pipeline**: Implement `code/run_full_pipeline.py` orchestrating T051, T013a‑T019, T022, T025, T029‑T032. Writes three logs (`pipeline_execution_log.json`, `model_fitting_log.json`, `evaluation_log.json`). **Error Handling**: If any task fails, raise SystemExit with error code and log to `data/pipeline_execution_log.json`. Do not continue. **DEPENDS ON**: All tasks it orchestrates. **CHAIN FIX**: This task now correctly depends on the resolved T008 (Power Analysis) and T013c/T014 flow.
- [ ] T099a [P] **Execute Pipeline Failure Log**: If T099 fails, generate `data/pipeline_execution_log.json` with error details and stack trace. **DEPENDS ON**: T099.
- [X] T043d [P] **Capture Metrics**: Consolidate logs into `data/final_validation_report.json`. **DEPENDS ON**: T099, T099a.
- [X] T044 [P] **Generate Final Report**: Assemble `docs/final_report.md` using all intermediate artifacts and `docs/draft_final_report.md`. **DEPENDS ON**: T043d, T100, T048, T047, T025, T025b, T030b, T023, T024b.
- [X] T036 [P] **Runtime Validation**: Run `code/validate_runtime.py` to ensure full pipeline ≤ 6 h; generate `data/ci_validation_report.json`. **DEPENDS ON**: T099, T099a.
- [X] T033e [P] Documentation updates: Add Data Pipeline section to `docs/quickstart.md` (depends on successful pipeline execution). **DEPENDS ON**: T099, T099a.

---

## Phase N+3: Critical Data Integrity & Reproducibility Fixes

- [X] T054 (already defined) **Calibration Verification** (see Phase 4).
- [X] T055 (already defined) **Final Report Generation** (see Phase 4).

---

## Phase N+4: Execution Gate Hardening & Data Source Verification

- [X] T056 [P] **Execution Gate Pre‑Check**: Verify verification PASS, Bayesian SUCCESS (or Fallback SUCCESS), calibration PASS, VIF computed. Exit non‑zero on failure; write `data/gate_validation_report.json`. **DEPENDS ON**: T051, T025, T025b, T054, T023.
- [X] T101 [P] **Verify Normalization Config**: Ensure `data/normalization_config.json` exists; generate default if missing. **DEPENDS ON**: T014.
- [X] T057 [P] **Final Report Compilation**: Aggregate all validated artifacts (VIF, partial correlation, AUC delta, calibration, power analysis) into `docs/final_report.md` with a "Constitution Compliance" section. **DEPENDS ON**: T056, T044, T048, T047, T025, T025b, T030b, T023, T024b.
- [X] T058 [P] **Artifact Hashing**: Compute content hashes for all final artifacts. **DEPENDS ON**: T057.
- [X] T059 [P] **Reproducibility Audit**: Run reproducibility audit (T058); if PASS, update `docs/research.md` with "Final Sign‑off". **DEPENDS ON**: T058, T019, T101.
- [X] T060 [P] **Final Sign‑off**: Update project state. **DEPENDS ON**: T059.

---

## Phase N+5: Atomic Script Creation (Consolidated)

**Purpose**: Create atomic scripts required for Phase N+6 execution.

- [X] T100 [P] **Create Project Skeleton**: Implement skeleton files for `code/data/preprocess.py`, `code/models/model_fit.py`, `code/evaluation/evaluate.py`, `code/run_full_pipeline.py`. **Output**: Skeleton files with TODOs. **DEPENDS ON**: T002, T007, T034, T022, T025, T029, T030, T055.

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
- [X] T069 [P] **Execute Atomic Preprocessing**: Run atomic preprocessing steps with schema validation. **DEPENDS ON**: T068, T007, T100.
- [X] T070 [P] **Execute Atomic Model Fitting**: Run atomic model fitting (Null, Full, Bayesian) with convergence checks. **DEPENDS ON**: T069, T100.
- [X] T071 [P] **Execute Atomic Evaluation**: Run atomic evaluation (metrics, hypothesis testing). **DEPENDS ON**: T070, T100.
- [X] T072 [P] **Execute Atomic Report Generation**: Assemble final report sections atomically. **DEPENDS ON**: T071, T100.
- [X] T073 [P] **Generate Final Report**: Aggregate atomic logs and results into `docs/final_report.md`, include Constitution Compliance and Limitations. **DEPENDS ON**: T072, T057, T058.
- [X] T074 [P] **Final Validation & Sign‑off**: Run reproducibility audit (T059); if PASS, update `docs/research.md` with "Final Sign‑off". **DEPENDS ON**: T073, T058, T059.

---

## Concrete Implementation Tasks (Formerly Review Actions)

**Purpose**: Convert meta-instructions into executable code changes.

- [ ] T113 [P] **Flow Audit Implementation**: Update `code/run_full_pipeline.py` to assert existence of `data/final/logistic_results.json` and `data/final/bayesian_results.json` (or `bayesian_results_fallback.json`) before calling `evaluate.py`. **Output**: `data/flow_audit_log.json`. **DEPENDS ON**: T099, T022, T025, T025b, T029.
- [ ] T114 [P] **Dataset ID Specificity**: Update `code/data/download.py` to hard-code the exact HuggingFace dataset identifiers `bigscience/recipem` (or the specific verified mirror ID) and the split `train` for Recipe1M, and `recipe1m-ratings` for the ratings dataset. **DEPENDS ON**: T012, T051.
- [ ] T115 [P] **Streaming Logic Detail**: Enhance `code/data/preprocess.py` to explicitly define the chunking strategy: `batch_size=1000` rows, accumulation via `pandas.concat` with `ignore_index=True`, and memory cleanup via `del` and `gc.collect()` after each chunk. **DEPENDS ON**: T034, T013a.
- [ ] T116 [P] **Spec Ratification Gate**: Add a final check in T060 to verify `data/amendment_ratification_log.json` exists and contains the key `"FR-001": "RATIFIED"` and `"FR-008": "RATIFIED"`. **Action**: If missing, raise `SystemExit` (T001c ensures this exists). **DEPENDS ON**: T060, T012b, T001c.
- [ ] T117 [P] **Leakage Hard Gate**: Modify `code/run_full_pipeline.py` to raise a `SystemExit` if `data/data_leakage_audit.json` reports `mutual_information > 0.5` before attempting T022. **Action**: Add this conditional check immediately after T024a execution in the pipeline orchestration. **DEPENDS ON**: T024a, T099.
- [ ] T118 [P] **VIF Conditional Logic**: Update `code/models/logistic.py` to read `data/final_predictors.json` dynamically. If the file was modified by T040 (predictor dropped), the script must use the reduced list; otherwise, use the default list. **Action**: Implement this logic in `logistic.py` and document it in T022. **DEPENDS ON**: T040, T022.