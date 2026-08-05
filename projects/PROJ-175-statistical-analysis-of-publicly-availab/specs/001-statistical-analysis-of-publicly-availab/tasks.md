# Tasks: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

**Input**: Design documents from `/specs/001-statistical-analysis-of-recipe-data/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

> **⚠️ CRITICAL GOVERNANCE NOTE**: This `tasks.md` implements the **Plan's Critical Reframe** (Recipe1M embeddings/ratings, Partial Correlation) ONLY **IF AND ONLY IF** the original Spec requirements (FlavorDB, Counterfactual datasets) are unavailable. The pipeline MUST first attempt to fulfill the original Spec requirements. If they fail, a formal `RatifiedAmendment` log MUST be generated **BEFORE** any downstream processing. The project transitions to correlating factors within Recipe1M corpus instead of causal independence.

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

## Phase 1: Setup & Ratification (Shared Infrastructure & Governance)

**Purpose**: Project initialization, governance, and spec alignment. **MUST complete before any data processing.**

- [ ] T001a Create project directory structure: `projects/PROJ-175-statistical-analysis-of-publicly-availab/code/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/data/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/tests/`. **Verification**: Create `data/setup_log.json` with status "SUCCESS" if directories exist. **Output**: `data/setup_log.json`. **Schema**: `{"status": "SUCCESS"|"FAILED", "timestamp": "ISO8601", "paths_verified": ["path1", "path2"]}`. **Implementation**: Use `os.makedirs(..., exist_ok=True)` then `json.dump` with `indent=2`.
- [X] T001b Create empty `code/__init__.py`, `tests/__init__.py`, and `code/data/__init__.py`
- [X] T001c Create `code/requirements.txt` placeholder and `tests/conftest.py` placeholder
- [ ] T012a_recipe1m [P] Download Recipe1M: Stream the Recipe1M dataset from verified HuggingFace URL. **Action**: Use `datasets.load_dataset(..., streaming=True)`. **Constraint**: If download fails, raise error (no proxy for Recipe1M). **Output**: `data/raw/recipe1m_raw.parquet`. **DEPENDS ON**: T001a.
- [ ] T012a_flavordb [P] Download FlavorDB: Download FlavorDB chemical matrix from verified URL. **Action**: Use `requests` or `datasets.load_dataset`. **Constraint**: If download fails, set status "FAILED" in `data/download_status.json`. **Output**: `data/raw/flavordb_raw.csv` (or status log). **DEPENDS ON**: T001a.
- [ ] T012a_counterfactual [P] Download Counterfactual: Download Counterfactual Recipe Generation dataset from verified URL. **Action**: Use `requests` or `datasets.load_dataset`. **Constraint**: If download fails, set status "FAILED" in `data/download_status.json`. **Note**: Per Plan, this dataset is expected to be unavailable; failure is the expected path to trigger proxy logic. **Output**: `data/raw/counterfactual_raw.csv` (or status log). **DEPENDS ON**: T001a.
- [ ] T012c_schema_validate [P] Validate Counterfactual Schema: Read `data/raw/counterfactual_raw.csv` (if exists). **Action**: Verify presence of column `independent_sensory_compatibility` or `rating`. **Constraint**: If column missing, set status "INVALID_SCHEMA" in `data/download_status.json`. **Output**: `data/download_status.json` updated. **DEPENDS ON**: T012a_counterfactual.
- [ ] T012b Prepare Amendment Log: Read `data/download_status.json`. **Logic**:
 1. If `recipe1m` is "FAILED", raise error (Pipeline Halt).
 2. If `flavordb` or `counterfactual` is "FAILED" or "INVALID_SCHEMA", set `methodology` to "Correlational Analysis" and `proxy_source` to "Recipe1M".
 3. If all "SUCCESS", set `methodology` to "Causal Independence" and `proxy_source` to null.
 4. **CRITICAL**: Write `data/amendment_log.json` with keys `status`="PENDING", `methodology`, `proxy_source`, `timestamp`.
 **Constraint**: This task prepares the log but does NOT ratify. **Output Schema**: `{"status": "PENDING"|"RATIFIED", "methodology": "Causal Independence"|"Correlational Analysis", "proxy_source": "Recipe1M"|null, "timestamp": "ISO8601"}`. **DEPENDS ON**: T012a_recipe1m, T012a_flavordb, T012c_schema_validate.
- [ ] T012d_ratification_gate [P] Ratification Gate: Read `data/amendment_log.json`. **Action**: Verify `status` is "PENDING". If manual approval is required, halt and wait. If automated, set `status` to "RATIFIED". **Output**: `data/amendment_log.json` with `status`="RATIFIED". **Constraint**: HARD GATE. No downstream tasks (T013+) run until this file exists and `status`="RATIFIED". **DEPENDS ON**: T012b.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **DEPENDS on T012d_ratification_gate.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python project with `code/requirements.txt` (pandas, numpy, scikit-learn, pyarrow, statsmodels, pymc>=5.0.0, scipy, matplotlib, seaborn, pyyaml, pytest, python-Levenshtein, pingouin)
- [X] T033a Configure linting: Create `ruff.toml` at repository root with specific rules (select = ["E", "F"]) to enforce a subset of error and warning categories as outlined in the project's coding standards. (Constitution I, FR‑001)
- [X] T033b Configure formatting: Create `pyproject.toml` at repository root with black configuration (line‑length=88, target-version=py) to ensure consistent code style. (Constitution I, FR‑001)
- [X] T004 [P] Setup `data/` directory structure (`raw/`, `processed/`, `final/`) and `code/` module structure
- [X] T005 [P] Implement global random seed pinning. **Deliverable**: Create `code/__init__.py` with `seed = 42` and `tests/conftest.py` with `@pytest.fixture(autouse=True) def set_seed()`.
- [X] T006 [P] Setup memory profiling utility in `code/utils/memory_monitor.py` to enforce a predefined RAM limit. **Deliverable**: Create `check_limit(limit_mb=7168)` function that raises `MemoryError` if exceeded, and log to `data/memory_profile.json`. **Schema**: `{"peak_ram_mb": float, "timestamp": "ISO8601", "limit_mb": 7168, "downsampled": bool, "downsample_ratio": float}`. **Constraint**: If RAM > 80% limit, trigger dynamic downsampling logic and log the calculated `downsample_ratio`. (US-1 Edge Cases)
- [ ] T007a Create base data schema definitions in `specs/001-statistical-analysis-of-recipe-data/contracts/`: specifically `dataset.schema.yaml` and `model_output.schema.yaml`. **Deliverable**: Schemas defining fields `ingredient_id`, `log_co_occurrence`, `flavor_similarity`, `functional_role`, `compatibility_label`, etc., plus a validator script `code/utils/validate_schema.py`. (Constitution II) **NOTE**: Initial schema assumes original Spec.
- [ ] T007b Update Schema for Ratified Path: Read `data/amendment_log.json`. **Logic**: If `methodology` is "Correlational Analysis", update `dataset.schema.yaml` to define `flavor_similarity` as "Recipe1M embedding cosine similarity". If "Causal Independence", define as "FlavorDB chemical vectors". **Output**: Updated `specs/001-statistical-analysis-of-recipe-data/contracts/dataset.schema.yaml`. **Constraint**: Do not define proxy schema until amendment ratified. **DEPENDS ON**: T012d_ratification_gate.
- [X] T038 [P] Implement `code/data/verify.py` robust error handling: Replace any generic `try/except` blocks with specific HTTP error handling that **raises** on failure (no synthetic fallback) and logs the exact URL and error code to `data/download_errors.log`. (Constitution II)
- [X] T042 [P] Extend `code/data/verify.py` with schema validation for the Recipe1M Ratings dataset: enforce presence and type of the `rating` column; fail the pipeline on mismatch.
- [ ] T013b Pilot Download & Power Analysis: Download a small pilot sample (e.g., a subset of recipes) to estimate dataset size and variance. **Action**: Calculate required sample size for power analysis using parameters: alpha=0.05, beta=0.2 (power=0.8), effect_size=0.1. Use Cohen's h or logistic regression power formula. **Output**: `data/pilot_stats.json` with `sample_size_required`. **DEPENDS ON**: T012d_ratification_gate.
- [ ] T013a Stream & Validate Recipe1M: Stream the full Recipe1M dataset (or downsampled subset if T012a failed and proxy is active). **DEPENDS ON**: T013b, T012d_ratification_gate. **Action**: Use `datasets.load_dataset(..., streaming=True)`. Read `sample_size_required` from T013b output; enforce via `itertools.islice` or filtering. **Output**: `data/raw/recipe1m_processed.parquet`. **Verification**: Ensure file exists and schema matches T007b. **Constraint**: If T012a_recipe1m failed, fail the pipeline (no proxy for Recipe1M itself).
- [ ] T014 Normalization: Normalize ingredient names and derive functional roles. **DEPENDS ON**: T013a, T012d_ratification_gate, T007b. **Action**:
 1. Read `data/amendment_log.json`. Verify `status`="RATIFIED". If not, raise Error.
 2. If `proxy_source` is "Recipe1M": Use Recipe1M ingredient list. Normalize using Levenshtein distance ≤ 2. For ties, select the canonical form with the highest marginal frequency.
 3. **CRITICAL**: Calculate marginal frequency from raw recipe list ONLY, excluding any co-occurrence matrix $C$ being built in T015, to ensure independence per FR-005.
 4. Derive functional role using 'positional rank' and 'marginal frequency'.
 5. If `proxy_source` is null: Use FlavorDB canonical list with Levenshtein distance ≤ 2.
 **Output**: `data/processed/normalized_ingredients.csv`. **Schema**: `{"ingredient_id": str, "canonical_name": str, "functional_role": str (primary|secondary|garnish), "frequency": int}`.
- [ ] T015 Co-occurrence Matrix: Construct global co-occurrence matrix $C$. **DEPENDS ON**: T014. **Action**: Count pairs $(i, j)$ in recipes. Apply log-transform with epsilon smoothing for zero counts. **Output**: `data/processed/co_occurrence_matrix.parquet`.
- [ ] T016 Semantic Similarity: Compute cosine similarity between ingredient embeddings. **DEPENDS ON**: T014, T012d_ratification_gate, T007b. **Action**:
 1. Read `data/amendment_log.json`. Verify `status`="RATIFIED". If not, raise Error.
 2. If `proxy_source` is "Recipe1M": Use a pre-trained sentence transformer model for Recipe dataset visual/text embeddings (Reimers & Gurevych, 2019).. Input: `data/processed/normalized_ingredients.csv`.
 3. If `proxy_source` is null: Use FlavorDB chemical vectors.
 **Output**: `data/processed/similarity_scores.parquet`.
- [X] T017 Functional Role Derivation & Validation: Derive functional role (primary, secondary, garnish) and validate against multicollinearity with semantic similarity. **DEPENDS ON**: T014, T015, T012d_ratification_gate. **Action**: Ensure functional role is not correlated with co-occurrence frequency. If proxy, apply circularity correction. **Output**: `data/processed/functional_roles.parquet`.
- [ ] T017_validate_role_independence [P] Role Independence Audit: **DEPENDS ON**: T014, T015. **Action**: Calculate Pearson correlation between `functional_role` (encoded) and `log_co_occurrence`. If $r > 0.1$, log warning and flag for manual review. **Output**: `data/logs/role_independence_audit.json`.
- [ ] T018 Imputation & Bias Check: Handle missing values in embeddings, similarity scores, and functional roles. **DEPENDS ON**: T016, T017. **Action**: Impute missing similarity scores with 0. Log exclusion counts. **Output**: `data/processed/ingredient_pairs.csv` (final dataset for modeling).
- [ ] T019 Compatibility Labels: Create binary compatibility labels. **DEPENDS ON**: T018, T012d_ratification_gate, T007b. **Action**:
 1. Read `data/amendment_log.json`. Verify `status`="RATIFIED". If not, raise Error.
 2. If `proxy_source` is "Recipe1M": Extract `rating` column from Recipe1M. Calculate median. Binary label = 1 if rating >= median, else 0. **Output**: `data/logs/methodology_warning.json` with `switched_to_correlational`: true, `threshold`: median.
 3. If `proxy_source` is null: Use Counterfactual Recipe Generation dataset labels.
 **Output**: `data/processed/ingredient_pairs_with_labels.csv`. **Output Schema for Warning**: `{"switched_to_correlational": bool, "threshold": float}`.

**Checkpoint**: User Story 1 pipeline ready.

---

## Phase 3: User Story 2 – Statistical Model Fitting and Validation (Priority: P2)

**Goal**: Fit regularized logistic regression and hierarchical Bayesian models, controlling for co‑occurrence while isolating semantic similarity and functional role effects. **DEPENDS on T012d_ratification_gate.**

- [ ] T023 VIF Calculation: Compute Variance Inflation Factors (VIF) for all predictors. **DEPENDS ON**: T014, T015, T016, T017, T018, T019. **Action**: Calculate VIF for `log_co_occurrence`, `flavor_similarity`, `functional_role`. **Output**: `data/logs/vif_scores.json`.
- [ ] T024a_assumption_check [P] Validate Independent Assumption: **DEPENDS ON**: T012d_ratification_gate, T023. **Action**: Read `data/amendment_log.json`. If `methodology` == "Causal Independence", verify `data/raw/counterfactual_raw.csv` exists and has labels. If "Correlational Analysis", set flag `use_partial_corr`=true, `use_lrt`=false. **Output**: `data/logs/assumption_validation.json`.
- [ ] T024c_decision [P] Ratification Decision: Read `data/amendment_log.json` and `data/logs/assumption_validation.json`. **Logic**: Set `use_partial_corr` and `use_lrt` flags. **Output**: `data/logs/methodology_flag.json`. **Schema**: `{"use_partial_corr": bool, "use_lrt": bool, "methodology": str}`. **DEPENDS ON**: T024a_assumption_check.
- [ ] T024c_create_amendment_doc [P] Ratification Documentation: Read `data/amendment_log.json`. Write formal record to `docs/amendment_record.md` detailing the switch from Causal to Correlational (if applicable). **DEPENDS ON**: T012d_ratification_gate.
- [ ] T024c_update_state [P] Update State: Read `docs/amendment_record.md`. Update `state/...yaml` with new content hash for the amendment record. **DEPENDS ON**: T024c_create_amendment_doc.
- [ ] T024b_likelihood [P] Attempt Likelihood-Ratio Test: **DEPENDS ON**: T023, T024a_assumption_check, T024c_decision. **Logic**: Read `data/logs/methodology_flag.json`. If `use_lrt` is false, SKIP this task and log warning. If true, perform LRT. **Output**: `data/logs/lrt_results.json`.
- [ ] T024b_partial [P] Partial Correlation Analysis: **DEPENDS ON**: T023, T024a_assumption_check, T024c_decision. **Logic**: Read `data/logs/methodology_flag.json`. If `use_partial_corr` is false, SKIP. If true, use `pingouin.partial_corr`. Inputs: `data/processed/ingredient_pairs.csv`. **Output**: `data/logs/partial_corr.json`.
- [ ] T024d_metric Model Comparison Metric: **DEPENDS ON**: T024b_likelihood (if success), T024b_partial (if success), T024c_update_state. **Action**: Extract the key metric (LRT p-value or partial correlation coefficient) for the report. **Output**: `data/logs/model_metric.json`.
- [ ] T025 Hierarchical Bayesian Model Fit: **DEPENDS ON**: T024c_create_amendment_doc, T304. **Action**: Use PyMC with NUTS on stratified subset. Read `data/amendment_log.json`; if `methodology` == "Correlational Analysis", load conservative priors from T304 output. **Output**: `data/logs/bayesian_results.json`.

**Checkpoint**: User Story 1 & 2 functional.

---

## Phase 4: User Story 3 – Evaluation and Reporting (Priority: P3)

- [ ] T029 Evaluation Metrics: Calculate AUC, precision, recall. **DEPENDS ON**: T025. **Action**: Evaluate on held-out test set. **Output**: `data/logs/evaluation_metrics.csv`.
- [ ] T030b_hypothesis_test [P] Hypothesis Test: **DEPENDS ON**: T029. **Action**: Perform statistical test (e.g., DeLong's test or bootstrap) for AUC delta ≥ 0.05. **Output**: `data/logs/hypothesis_test.json` with `p_value`, `delta`, `significant`: bool.
- [ ] T030 Calibration Plot: Generate calibration plot. **DEPENDS ON**: T029. **Action**: Plot predicted vs. actual probabilities. **Output**: `docs/calibration_plot.png`.
- [ ] T031 Final Report Generation: Generate final report. **DEPENDS ON**: T024d_metric, T030b_hypothesis_test, T030. **Action**: Compare full model vs. baseline. Test hypothesis. Include leakage-adjusted threshold if Correlational. **Output**: `docs/final_report.md`.
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
- [ ] T205 Implement Model Fitting: **Action**: Create `code/models/logistic.py` with function `fit_logistic_regression(X, y)`. **Logic**: L regularization, VIF check. **Output**: `code/models/logistic.py`.
- [ ] T206 Implement Evaluation: **Action**: Create `code/evaluation/report.py` with function `generate_report(metrics, plot_path)`. **Logic**: AUC, precision, recall, calibration plot. **Output**: `code/evaluation/report.py`.

---

## Phase 7: Governance & Review Resolution (Post-Analysis)

**Purpose**: Address specific reviewer concerns regarding data provenance, circularity, and statistical validity raised during the analysis phase.

- [ ] T301 [US1] Explicitly Document Data Source Provenance: **DEPENDS ON**: T012d_ratification_gate. **Action**: If `flavordb` or `counterfactual` failed, create `docs/data_provenance.md` detailing the exact fallback to Recipe1M proxies, citing the specific Plan amendment (Section "Spec Amendment Proposal") and the rationale (unavailability of verified independent sources). **Output**: `docs/data_provenance.md`.
- [ ] T302 [US2] Implement Circularity Quantification: **DEPENDS ON**: T024a_assumption_check. **Action**: In `docs/final_report.md`, add a dedicated section "Limitations: Corpus Circularity" that explicitly states the correlation between predictor (Recipe1M embeddings) and outcome (Recipe1M ratings) and quantifies the shared variance using the leakage audit results. **Output**: `docs/final_report.md` (updated).
- [ ] T303 [US3] Validate Proxy Assumptions: **DEPENDS ON**: T016, T019. **Action**: Run a correlation check between the proxy-derived `flavor_similarity` and `compatibility_label` against a random baseline to ensure the proxy has non-zero signal. **Output**: `data/logs/proxy_validation.json`.
- [ ] T304 [US2] Refine Bayesian Priors for Proxy Data: **DEPENDS ON**: T012d_ratification_gate. **Action**: Adjust PyMC model priors to be more conservative (wider) if the proxy path is active, reflecting the higher uncertainty of derived labels. **Output**: `code/models/bayesian.py` (updated) and `data/logs/prior_config.json`.
- [ ] T305 [US3] Update Hypothesis Statement: **DEPENDS ON**: T024c_update_state. **Action**: Ensure the final report's hypothesis statement explicitly reflects the "Correlational Analysis" scope (e.g., "Quantify associative strength within corpus") rather than "Causal Independence". **Output**: `docs/final_report.md` (updated).