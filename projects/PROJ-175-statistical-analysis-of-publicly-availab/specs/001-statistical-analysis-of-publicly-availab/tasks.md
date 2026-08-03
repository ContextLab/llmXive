# Tasks: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

**Input**: Design documents from `/specs/001-statistical-analysis-of-recipe-data/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

> **⚠️ CRITICAL GOVERNANCE NOTE**: This `tasks.md` implements the **Plan's Critical Reframe** (Recipe1M embeddings/ratings, Partial Correlation) ONLY **IF AND ONLY IF** the original Spec requirements (FlavorDB, Counterfactual datasets) are unavailable. The pipeline MUST first attempt to fulfill the original Spec requirements. If they fail, a formal `RatifiedAmendment` log MUST be generated before proceeding with proxies. The project transitions to correlating factors within Recipe1M corpus instead of causal independence.

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

## Phase 1: Setup (Shared Infrastructure & Ratification)

**Purpose**: Project initialization, governance, and spec alignment.

- [ ] T001a Create project directory structure: `projects/PROJ-175-statistical-analysis-of-publicly-availab/code/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/data/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/tests/`. **Verification**: Verify existence of directories via `os.path.isdir` and log to `data/setup_log.json`. **Schema**: `{"status": "SUCCESS"|"FAILED", "timestamp": "ISO8601", "paths_verified": ["path1", "path2"]}`. **Implementation**: Use `json.dump` with `indent=2` to write the log.
- [X] T001c Create empty `code/__init__.py`, `tests/__init__.py`, and `code/data/__init__.py`
- [X] T001d Create `code/requirements.txt` placeholder and `tests/conftest.py` placeholder
- [ ] T012a Dataset Availability Check: Attempt to download Recipe1M, FlavorDB, and Counterfactual datasets from verified URLs. **Action**: Use `datasets.load_dataset` for HuggingFace sources and `requests` for direct URLs. Log success/failure for EACH dataset in `data/download_status.json`. **Output**: `data/download_status.json` with keys `recipe1m`, `flavordb`, `counterfactual` and status "SUCCESS" or "FAILED". **Constraint**: If `flavordb` or `counterfactual` fails, set `use_proxy` flag to true. **DEPENDS ON**: T001a.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python project with `code/requirements.txt` (pandas, numpy, scikit-learn, pyarrow, statsmodels, pymc>=5.0.0, scipy, matplotlib, seaborn, pyyaml, pytest, python-Levenshtein)
- [X] T033a Configure linting: Create `ruff.toml` at repository root with specific rules (select = ["E", "F"]) to enforce a subset of error and warning categories as outlined in the project's coding standards. (Constitution I, FR‑001)
- [X] T033b Configure formatting: Create `pyproject.toml` at repository root with black configuration (line‑length=88, target-version=py) to ensure consistent code style. (Constitution I, FR‑001)
- [X] T004 [P] Setup `data/` directory structure (`raw/`, `processed/`, `final/`) and `code/` module structure
- [X] T005 [P] Implement global random seed pinning. **Deliverable**: Create `code/__init__.py` with `seed = 42` and `tests/conftest.py` with `@pytest.fixture(autouse=True) def set_seed()`.
- [X] T006 [P] Setup memory profiling utility in `code/utils/memory_monitor.py` to enforce a predefined RAM limit. **Deliverable**: Create `check_limit(limit_mb=7168)` function that raises `MemoryError` if exceeded, and log to `data/memory_profile.json`. **Schema**: `{"peak_ram_mb": float, "timestamp": "ISO8601", "limit_mb": 7168, "downsampled": bool, "downsample_ratio": float}`. **Constraint**: If RAM > 80% limit, trigger dynamic downsampling logic and log the calculated `downsample_ratio`. (US-1 Edge Cases)
- [X] T007 [P] Create base data schema definitions in `specs/001-statistical-analysis-of-recipe-data/contracts/`: specifically `dataset.schema.yaml` and `model_output.schema.yaml`. **Deliverable**: Schemas defining fields `ingredient_id`, `log_co_occurrence`, `flavor_similarity` (defined as Recipe1M embedding cosine similarity per Plan's Critical Reframe if proxy used), `functional_role`, `compatibility_label`, etc., plus a validator script `code/utils/validate_schema.py`. (Constitution II) **NOTE**: Schema reflects Plan's Critical Reframe; **Constitution Exception**: Explicitly flag that `flavor_similarity` uses Recipe1M embeddings instead of FlavorDB chemical vectors (FR-004) if proxy is active.
- [X] T038 [P] Implement `code/data/verify.py` robust error handling: Replace any generic `try/except` blocks with specific HTTP error handling that **raises** on failure (no synthetic fallback) and logs the exact URL and error code to `data/download_errors.log`. (Constitution II)
- [X] T042 [P] Extend `code/data/verify.py` with schema validation for the Recipe1M Ratings dataset: enforce presence and type of the `rating` column; fail the pipeline on mismatch.
- [ ] T013a Stream & Validate Recipe1M: Stream the full Recipe1M dataset (or downsampled subset if T012a failed and proxy is active). **DEPENDS ON**: T012a. **Action**: Use `datasets.load_dataset(..., streaming=True)`. **Output**: `data/raw/recipe1m_raw.parquet`. **Verification**: Ensure file exists and schema matches T007. **Constraint**: If T012a failed for Recipe1M, fail the pipeline (no proxy for Recipe1M itself).
- [ ] T013b Pilot Download & Power Analysis: Download a small pilot sample (e.g., a subset of recipes) to estimate dataset size and variance. **DEPENDS ON**: T013a. **Action**: Calculate required sample size for power analysis (effect size ≥ 0.1, power ≥ 0.8). **Output**: `data/pilot_stats.json` with `sample_size_required`.
- [ ] T014 Normalization: Normalize ingredient names and derive functional roles. **DEPENDS ON**: T013a, T012a. **Action**:
 1. If `flavordb` status in T012a is SUCCESS: Use FlavorDB canonical list with Levenshtein distance ≤ 2.
 2. If `flavordb` status is FAILED: Use Recipe1M ingredient list. Normalize using Levenshtein distance ≤ 2. For ties, select the canonical form with the highest marginal frequency (count(ingredient) / total_recipes). If still tied, use alphabetical order.
 3. Derive functional role using 'positional rank' and 'marginal frequency' (count(ingredient) / total_recipes), excluding co-occurrence frequency to prevent multicollinearity.
 **Output**: `data/processed/normalized_ingredients.csv`.
- [ ] T015 Co-occurrence Matrix: Construct global co-occurrence matrix $C$. **DEPENDS ON**: T014. **Action**: Count pairs $(i, j)$ in recipes. Apply log-transform with epsilon smoothing for zero counts. **Output**: `data/processed/co_occurrence_matrix.parquet`.
- [ ] T016 Semantic Similarity: Compute cosine similarity between ingredient embeddings. **DEPENDS ON**: T014, T012a. **Action**:
 1. If `flavordb` status is SUCCESS: Use FlavorDB chemical vectors.
 2. If `flavordb` status is FAILED: Use Recipe1M visual/text embeddings.
 **Output**: `data/processed/similarity_scores.parquet`.
- [ ] T017 Functional Role Derivation & Validation: Derive functional role (primary, secondary, garnish) and validate against multicollinearity with semantic similarity. **DEPENDS ON**: T014, T015. **Action**: Ensure functional role is not correlated with co-occurrence frequency. **Output**: `data/processed/functional_roles.parquet`.
- [ ] T018 Imputation & Bias Check: Handle missing values in embeddings, similarity scores, and functional roles. **DEPENDS ON**: T016, T017. **Action**: Impute missing similarity scores with 0. Log exclusion counts. **Output**: `data/processed/ingredient_pairs.csv` (final dataset for modeling).
- [ ] T019 Compatibility Labels: Create binary compatibility labels. **DEPENDS ON**: T018, T012a. **Action**:
 1. If `counterfactual` status is SUCCESS: Use Counterfactual Recipe Generation dataset labels.
 2. If `counterfactual` status is FAILED: Use Recipe1M ratings (median threshold) as proxy.
 **Output**: `data/processed/ingredient_pairs_with_labels.csv`.

**Checkpoint**: User Story 1 pipeline ready.

---

## Phase 3: User Story 2 – Statistical Model Fitting and Validation (Priority: P2)

**Goal**: Fit regularized logistic regression and hierarchical Bayesian models, controlling for co‑occurrence while isolating semantic similarity and functional role effects.

- [ ] T023 VIF Calculation: Compute Variance Inflation Factors (VIF) for all predictors. **DEPENDS ON**: T019. **Action**: Calculate VIF for `log_co_occurrence`, `flavor_similarity`, `functional_role`. **Output**: `data/logs/vif_scores.json`.
- [ ] T024a Data Leakage Audit: Quantify mutual information between predictors and outcome. **DEPENDS ON**: T019. **Action**: Calculate MI. Raise error if MI > 0.5 indicating significant data leakage (if using proxy). **Output**: `data/logs/leakage_audit.json`.
- [ ] T024b_likelihood Attempt Likelihood-Ratio Test: Perform the Likelihood Ratio test. **DEPENDS ON**: T023, T024a. **Action**: Compare full model vs. null model (co-occurrence only). **Output**: `data/logs/lrt_results.json`. **Condition**: Only valid if `counterfactual` status is SUCCESS.
- [ ] T024b_partial Partial Correlation Analysis: Compute partial correlation. **DEPENDS ON**: T023, T024a. **Action**: Compute partial correlation between `flavor_similarity` and `functional_role` controlling for `log_co_occurrence`. **Output**: `data/logs/partial_corr.json`. **Condition**: Only valid if `counterfactual` status is FAILED (proxy path).
- [ ] T024c_ratify_amendment Document Amendment Ratification (FR-008): **DEPENDS ON**: T024b_likelihood (if failed) OR T024b_partial (if used). **Action**: If proxy path used, document ratification of partial correlation as substitute for LRT. **Output**: `data/amendment_log.json`.
- [ ] T024d_metric Model Comparison Metric: **DEPENDS ON**: T024b_likelihood (if success) OR T024b_partial (if success). **Action**: Extract the key metric (LRT p-value or partial correlation coefficient) for the report. **Output**: `data/logs/model_metric.json`.
- [ ] T025 Hierarchical Bayesian Model Fit: Fit a hierarchical Bayesian model on downsampled data. **DEPENDS ON**: T024d_metric. **Action**: Use PyMC with NUTS on stratified subset. **Output**: `data/logs/bayesian_results.json`.

**Checkpoint**: User Story 1 & 2 functional.

---

## Phase 4: User Story 3 – Evaluation and Reporting (Priority: P3)

- [ ] T029 Evaluation Metrics: Calculate AUC, precision, recall. **DEPENDS ON**: T025. **Action**: Evaluate on held-out test set. **Output**: `data/logs/evaluation_metrics.csv`.
- [ ] T030 Calibration Plot: Generate calibration plot. **DEPENDS ON**: T029. **Action**: Plot predicted vs. actual probabilities. **Output**: `docs/calibration_plot.png`.
- [ ] T031 Final Report Generation: Generate final report. **DEPENDS ON**: T024d_metric, T029, T030. **Action**: Compare full model vs. baseline. Test hypothesis. **Output**: `docs/final_report.md`.
- [ ] T032 Sensitivity Analysis: Evaluate robustness of results. **DEPENDS ON**: T031. **Action**: Vary thresholds and re-run. **Output**: `docs/sensitivity_analysis.md`.

---

## Phase 5: Orchestration & Governance

- [ ] T099a_graph Orchestration Graph Definition: **DEPENDS ON**: T001a. **Action**: Define the logical execution graph for the pipeline (dependencies between tasks). **Output**: `docs/pipeline_graph.yaml`. **Constraint**: Does NOT depend on task *execution* results.
- [ ] T099a_impl Orchestration Implementation: **DEPENDS ON**: T099a_graph. **Action**: Implement `run_full_pipeline.py` to execute tasks in order. **Output**: `code/run_full_pipeline.py`.
- [ ] T099b Execute Pipeline: **DEPENDS ON**: T099a_impl. **Action**: Run the full pipeline. **Output**: All artifacts in `data/` and `docs/`.

---

## Phase 6: Concrete Code Implementation (Specific Functions)

- [ ] T201 Implement Data Loader: **Action**: Create `code/data/download.py` with function `download_dataset(url, output_path, checksum)`. **Logic**: Validate URL, download, verify checksum, raise on failure (no synthetic fallback). **Output**: `code/data/download.py`.
- [ ] T202 Implement Schema Validator: **Action**: Create `code/utils/validate_schema.py` with function `validate_schema(dataframe, schema_path)`. **Logic**: Check columns, types, and required fields against `schema.yaml`. **Output**: `code/utils/validate_schema.py`.
- [ ] T203 Implement Normalization: **Action**: Create `code/data/preprocess.py` with function `normalize_ingredients(ingredients, canonical_list, threshold=2)`. **Logic**: Levenshtein distance ≤ 2, frequency-weighted tie-breaking. **Output**: `code/data/preprocess.py`.
- [ ] T204 Implement Co-occurrence: **Action**: Create `code/data/preprocess.py` with function `compute_co_occurrence(recipes)`. **Logic**: Count pairs, log-transform. **Output**: `code/data/preprocess.py`.
- [ ] T205 Implement Model Fitting: **Action**: Create `code/models/logistic.py` with function `fit_logistic_regression(X, y)`. **Logic**: L2 regularization, VIF check. **Output**: `code/models/logistic.py`.
- [ ] T206 Implement Evaluation: **Action**: Create `code/evaluation/report.py` with function `generate_report(metrics, plot_path)`. **Logic**: AUC, precision, recall, calibration plot. **Output**: `code/evaluation/report.py`.