# Tasks: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

**Input**: Design documents from `/specs/001-statistical-analysis-of-recipe-data/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

> **⚠️ CRITICAL GOVERNANCE NOTE**: This `tasks.md` implements the **Plan's Critical Reframe** (Recipe1M embeddings/ratings, Partial Correlation) ONLY **IF AND ONLY IF** the original Spec requirements (FlavorDB, Counterfactual datasets) are unavailable AND a formal `RatifiedAmendment` is present in `docs/amendment_record.md`. The pipeline MUST first attempt to fulfill the original Spec requirements. If they fail, a formal `RatifiedAmendment` log MUST be generated **BEFORE** any downstream processing. The project transitions to correlating factors within Recipe1M corpus instead of causal independence.

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

- [X] T001a Create project directory structure: `projects/PROJ-175-statistical-analysis-of-publicly-availab/code/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/data/`, `projects/PROJ-175-statistical-analysis-of-publicly-availab/tests/`. **Verification**: Create `data/setup_log.json` with status "SUCCESS" if directories exist. **Output**: `data/setup_log.json`. **Schema**: `{"status": "SUCCESS"|"FAILED", "timestamp": "ISO8601", "paths_verified": ["path1", "path2"]}`. **Implementation**: Use `os.makedirs(..., exist_ok=True)` then `json.dump` with `indent=2`.
- [X] T001b Create empty `code/__init__.py`, `tests/__init__.py`, and `code/data/__init__.py`
- [X] T001c Create `code/requirements.txt` placeholder and `tests/conftest.py` placeholder
- [ ] T012a_recipe1m Download Recipe1M: Stream the Recipe1M dataset from verified HuggingFace URL (`recipe1m/recipe1m`). **Action**: Use `datasets.load_dataset(..., streaming=True)`. **Constraint**: If download fails, write `{"dataset": "recipe1m", "status": "FAILED", "error_code": "HTTP_XXX"}` to `data/download_status_recipe1m.json`, then raise error. **Output**: `data/raw/recipe1m_raw.parquet` (if success) or `data/download_status_recipe1m.json` (if failure). **DEPENDS ON**: T001a.
- [ ] T012a_flavordb Download FlavorDB: Download FlavorDB chemical matrix from verified URL (`flavordb/chemical_matrix`). **Action**: Use `datasets.load_dataset` or `requests`. **Constraint**: If download fails, write `{"dataset": "flavordb", "status": "FAILED", "error_code": "HTTP_XXX"}` to `data/download_status_flavordb.json`. If success, parse and write to `data/raw/flavordb_raw.csv`. **Output**: `data/raw/flavordb_raw.csv` or `data/download_status_flavordb.json`. **DEPENDS ON**: T001a.
- [ ] T012a_counterfactual Download Counterfactual: Download Counterfactual Recipe Generation dataset from verified URL (check `research.md` for canonical source). **Action**: Use `requests` or `datasets.load_dataset`. **Constraint**: If download fails, write `{"dataset": "counterfactual", "status": "FAILED", "error_code": "HTTP_XXX"}` to `data/download_status_counterfactual.json`. If success, parse and write to `data/raw/counterfactual_raw.csv`. **Output**: `data/raw/counterfactual_raw.csv` or `data/download_status_counterfactual.json`. **DEPENDS ON**: T001a.
- [ ] T012b_agg Aggregate Download Status: Read `data/download_status_recipe1m.json`, `data/download_status_flavordb.json`, `data/download_status_counterfactual.json`. **Action**: Merge into a single `data/download_status.json` with keys `recipe1m`, `flavordb`, `counterfactual`. **Output**: `data/download_status.json`. **DEPENDS ON**: T012a_recipe1m, T012a_flavordb, T012a_counterfactual.
- [ ] T012c_schema_validate Validate Counterfactual Schema: Read `data/raw/counterfactual_raw.csv` (if exists). **Action**: Verify presence of column `independent_sensory_compatibility` or `rating`. **Constraint**: If column missing, set status "INVALID_SCHEMA" in `data/download_status.json`. **Output**: `data/download_status.json` updated. **DEPENDS ON**: T012a_counterfactual.
- [X] T012b Prepare Amendment Log: Read `data/download_status.json`. **Logic**:
 1. If `recipe1m` is "FAILED", raise error (Pipeline Halt).
 2. If `flavordb` or `counterfactual` is "FAILED" or "INVALID_SCHEMA", check for `docs/amendment_record.md`.
 3. **CRITICAL**: If `docs/amendment_record.md` does NOT exist, create a draft `docs/amendment_record.md` with status "PENDING_HUMAN_REVIEW" and halt execution. If it exists and status is "RATIFIED", set `methodology` to "Correlational Analysis" and `proxy_source` to "Recipe1M".
 4. If all "SUCCESS", set `methodology` to "Causal Independence" and `proxy_source` to null.
 5. Write `data/amendment_log.json` with keys `status`="PENDING"|"RATIFIED", `methodology`, `proxy_source`, `timestamp`.
 **Constraint**: This task prepares the log but does NOT ratify. **Output Schema**: `{"status": "PENDING"|"RATIFIED", "methodology": "Causal Independence"|"Correlational Analysis", "proxy_source": "Recipe1M"|null, "timestamp": "ISO8601"}`. **DEPENDS ON**: T012a_recipe1m, T012a_flavordb, T012a_counterfactual, T012b_agg, T012c_schema_validate.
- [ ] T012d_ratification_gate Ratification Gate: Read `data/amendment_log.json`. **Action**: Verify `status` is "PENDING" or "RATIFIED". If "PENDING", halt and wait for human intervention. If "RATIFIED", proceed. **Output**: `data/amendment_log.json` with `status`="RATIFIED" (if automated) or unchanged (if manual). **Constraint**: HARD GATE. No downstream tasks (T013+) run until this file exists and `status`="RATIFIED". **DEPENDS ON**: T012b.

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
- [ ] T007a_schema_dataset Create Base Dataset Schema: **Action**: Create `dataset.schema.yaml` in `specs/001-statistical-analysis-of-recipe-data/contracts/` defining fields for `IngredientPair` (ingredient_id, log_co_occurrence, flavor_similarity, functional_role, compatibility_label). **Constraint**: Must run BEFORE T012d. **Output**: `specs/001-statistical-analysis-of-recipe-data/contracts/dataset.schema.yaml`. **DEPENDS ON**: T001a.
- [ ] T007a_schema_model Create Base Model Schema: **Action**: Create `model_output.schema.yaml` in `specs/001-statistical-analysis-of-recipe-data/contracts/` defining fields for `ModelResult` (coefficients, p_values, vif_scores, posterior_distributions). **Constraint**: Must run BEFORE T012d. **Output**: `specs/001-statistical-analysis-of-recipe-data/contracts/model_output.schema.yaml`. **DEPENDS ON**: T001a.
- [ ] T007a_validator Create Schema Validator: **Action**: Create `code/utils/validate_schema.py` to validate data against `dataset.schema.yaml` and `model_output.schema.yaml`. **Constraint**: Must run BEFORE T012d. **Output**: `code/utils/validate_schema.py`. **DEPENDS ON**: T001a.
- [ ] T007b Update Schema for Ratified Path: **Action**: Read `data/amendment_log.json`. If `methodology` is "Correlational Analysis", update `dataset.schema.yaml` to define `flavor_similarity` as "Recipe1M embedding cosine similarity". If "Causal Independence", define as "FlavorDB chemical vectors". **Output**: Updated `specs/001-statistical-analysis-of-recipe-data/contracts/dataset.schema.yaml`. **Constraint**: Do not define proxy schema until amendment ratified. **DEPENDS ON**: T012d_ratification_gate, T007a_schema_dataset, T007a_schema_model, T007a_validator.
- [X] T038 [P] Implement `code/data/verify.py` robust error handling: Replace any generic `try/except` blocks with specific HTTP error handling that **raises** on failure (no synthetic fallback) and logs the exact URL and error code to `data/download_errors.log`. (Constitution II)
- [X] T042 [P] Extend `code/data/verify.py` with schema validation for the Recipe1M Ratings dataset: enforce presence and type of the `rating` column; fail the pipeline on mismatch.
- [X] T013b Pilot Download & Power Analysis: Download a small pilot sample (e.g., a subset of recipes) to estimate dataset size and variance. **Action**: Calculate required sample size for power analysis using parameters: alpha=0.05, beta=0.2 (power=0.8), effect_size=0.1. Use Cohen's h or logistic regression power formula. **Output**: `data/pilot_stats.json` with `sample_size_required`. **Fallback**: If pilot fails, write `{"sample_size_required": "a statistically sufficient magnitude", "status": "DEFAULT_USED"}`. **DEPENDS ON**: T012d_ratification_gate.
- [ ] T013a Stream & Validate Recipe1M: Stream the full Recipe1M dataset (or downsampled subset if T012a failed and proxy is active). **DEPENDS ON**: T013b, T012d_ratification_gate. **Action**: Use `datasets.load_dataset(..., streaming=True)`. Read `sample_size_required` from T013b output; enforce via `itertools.islice` or filtering. **Validation**: Ensure `rating` column is present if `proxy_source` is "Recipe1M". **Output**: `data/raw/recipe1m_processed.parquet`. **Verification**: Ensure file exists and schema matches T007b. Write `data/logs/recipe1m_validation.json` with `rating_column_present`: bool. **Constraint**: If T012a_recipe1m failed, fail the pipeline (no proxy for Recipe1M itself).
- [ ] T014a Normalize Ingredients: Normalize ingredient names and map to canonical IDs. **DEPENDS ON**: T013a, T012d_ratification_gate, T007b. **Action**: <!-- ATOMIZE: requested -->
 1. Read `data/amendment_log.json`. Verify `status`="RATIFIED".
 2. Use FlavorDB canonical list (if Causal) or Recipe1M list (if Correlational) with Levenshtein distance ≤ 2.
 3. For ties, select the canonical form with the highest marginal frequency.
 **Output**: `data/processed/normalized_ingredients.csv`. **Schema**: `{"ingredient_id": str, "canonical_name": str, "frequency": int}`. **DEPENDS ON**: T013a, T012d_ratification_gate, T007b.
- [ ] T014b Derive Functional Roles: Derive functional role (primary, secondary, garnish) based on position and frequency. **DEPENDS ON**: T014a. **Action**: Calculate marginal frequency from raw recipe list ONLY, excluding any co-occurrence matrix $C$ being built in T015, to ensure independence per FR-005. **Output**: `data/processed/functional_roles.csv`. **DEPENDS ON**: T014a.
- [X] T014c Circularity Check: **Action**: Calculate Pearson correlation between 'marginal frequency' and 'co-occurrence' (if available). If $r > 0.1$, log warning to `data/logs/circularity_warning.json`. **Output**: `data/logs/circularity_warning.json`. **DEPENDS ON**: T014a, T014b.
- [ ] T015 Co-occurrence Matrix: Construct global co-occurrence matrix $C$. **DEPENDS ON**: T014a, T014b. **Action**: Count pairs $(i, j)$ in recipes. Apply log-transform with epsilon smoothing for zero counts. **Output**: `data/processed/co_occurrence_matrix.parquet`.
- [X] T016a Chemical Similarity: **DEPENDS ON**: T012d_ratification_gate, T007b. **Action**: Read `data/amendment_log.json`. If `methodology` is "Causal Independence", download FlavorDB chemical matrix and compute cosine similarity between chemical vectors. **Constraint**: If `methodology` is "Correlational Analysis", SKIP this task. **Output**: `data/processed/similarity_scores_chemical.parquet`. <!-- SKIPPED: YAML+regex parse failed (expected '<document start>', but found '<scalar>'
 in "<unicode string>", line 33, column 3:
 e disdisa.
 ^) -->
- [ ] T016b Embedding Similarity: **DEPENDS ON**: T012d_ratification_gate, T007b. **Action**: Read `data/amendment_log.json`. If `methodology` is "Correlational Analysis", use `sentence-transformers/all-MiniLM-L6-v2` for Recipe dataset visual/text embeddings. Input: `data/processed/normalized_ingredients.csv`. **Constraint**: If `methodology` is "Causal Independence", SKIP this task. **Output**: `data/processed/similarity_scores_embedding.parquet`.
- [ ] T017 Functional Role Validation: **DEPENDS ON**: T014b, T015. **Action**: Ensure functional role is not correlated with co-occurrence frequency. If proxy, apply circularity correction. **Output**: `data/processed/functional_roles_validated.parquet`. <!-- ATOMIZE: requested -->
- [ ] T017_validate_role_independence [P] Role Independence Audit: **DEPENDS ON**: T014b, T015. **Action**: Calculate Pearson correlation between `functional_role` (encoded) and `log_co_occurrence`. If $r > 0.1$, log warning and flag for manual review. **Output**: `data/logs/role_independence_audit.json`.
- [ ] T018 Imputation & Bias Check: Handle missing values in embeddings, similarity scores, and functional roles. **DEPENDS ON**: T016a, T016b, T017. **Action**: Impute missing similarity scores with 0. Log exclusion counts. **Constraint**: Select the correct similarity file (`similarity_scores_chemical.parquet` or `similarity_scores_embedding.parquet`) based on `data/amendment_log.json`. **Output**: `data/processed/ingredient_pairs.csv` (final dataset for modeling).
- [~] T019a Compatibility Labels (Independent): **DEPENDS ON**: T018, T013a, T012d_ratification_gate, T007b. **Action**:
 1. Read `data/amendment_log.json`. Verify `status`="RATIFIED".
 2. If `proxy_source` is null: Use Counterfactual Recipe Generation dataset labels. Verify `independent_sensory_compatibility` or `rating` column exists.
 **Output**: `data/processed/ingredient_pairs_with_labels.csv`. **Constraint**: Fails if independent data is missing and amendment is not ratified.
- [ ] T019b Compatibility Labels (Proxy): **DEPENDS ON**: T018, T013a, T012d_ratification_gate, T007b. **Action**:
 1. Read `data/amendment_log.json`. Verify `status`="RATIFIED" AND `proxy_source` is "Recipe1M".
 2. Extract `rating` column from Recipe1M. Calculate median. Binary label = 1 if rating >= median, else 0.
 3. **CRITICAL**: Write `data/logs/circularity_warning.json` flagging violation of Constitution Principle VI. Create `docs/circularity_report.md`.
 **Output**: `data/processed/ingredient_pairs_with_labels.csv`. **Output Schema for Warning**: `{"switched_to_correlational": bool, "threshold": float}`.

**Checkpoint**: User Story 1 pipeline ready.

---

## Phase 3: User Story 2 – Statistical Model Fitting and Validation (Priority: P2)

**Goal**: Fit regularized logistic regression and hierarchical Bayesian models, controlling for co‑occurrence while isolating semantic similarity and functional role effects. **DEPENDS on T012d_ratification_gate.**

- [ ] T023 VIF Calculation: Compute Variance Inflation Factors (VIF) for all predictors. **DEPENDS ON**: T014a, T014b, T015, T016a, T016b, T017, T018, T019a, T019b. **Action**: Calculate VIF for `log_co_occurrence`, `flavor_similarity`, `functional_role`. **Output**: `data/logs/vif_scores.json`.
- [ ] T024_methodology_decision Methodology Decision & Documentation: **DEPENDS ON**: T012d_ratification_gate, T023. **Action**: Read `data/amendment_log.json`. If `methodology` == "Causal Independence", set `use_lrt`=true, `use_partial_corr`=false. If "Correlational Analysis", set `use_lrt`=false, `use_partial_corr`=true. Write `docs/amendment_record.md` if not present (draft) or update if ratified. **Output**: `data/logs/methodology_flag.json`. **Schema**: `{"use_partial_corr": bool, "use_lrt": bool, "methodology": str}`.
- [ ] T024b_LRT_Execution [P] Execute Likelihood-Ratio Test: **DEPENDS ON**: T023, T024_methodology_decision. **Logic**: Read `data/logs/methodology_flag.json`. If `use_lrt` is true, perform LRT against null model (frequency only). If `use_lrt` is false, SKIP. **Output**: `data/logs/lrt_results.json`. **Constraint**: Only runs if independent data is available.
- [ ] T024b_partial [P] Partial Correlation Analysis: **DEPENDS ON**: T023, T024_methodology_decision. **Logic**: Read `data/logs/methodology_flag.json`. If `use_partial_corr` is true, use `pingouin.partial_corr`. Inputs: `data/processed/ingredient_pairs.csv`. **Output**: `data/logs/partial_corr.json`.
- [ ] T024d_metric Model Comparison Metric: **DEPENDS ON**: T024b_LRT_Execution, T024b_partial, T024_methodology_decision. **Action**: Extract the key metric (LRT p-value or partial correlation coefficient) for the report. **Output**: `data/logs/model_metric.json`.
- [ ] T304 [US2] Refine Bayesian Priors for Proxy Data: **DEPENDS ON**: T012d_ratification_gate. **Action**: Adjust PyMC model priors to be more conservative (wider) if the proxy path is active, reflecting the higher uncertainty of derived labels. **Output**: `code/models/bayesian.py` (updated) and `data/logs/prior_config.json`.
- [ ] T025 Hierarchical Bayesian Model Fit: **DEPENDS ON**: T024_methodology_decision, T304. **Action**: Use PyMC with NUTS on stratified subset. Read `data/amendment_log.json`; if `methodology` == "Correlational Analysis", load conservative priors from T304 output. **Output**: `data/logs/bayesian_results.json`.

**Checkpoint**: User Story 1 & 2 functional.

---

## Phase 4: User Story 3 – Evaluation and Reporting (Priority: P3)

- [ ] T029 Evaluation Metrics: Calculate AUC, precision, recall. **DEPENDS ON**: T025. **Action**: Evaluate on held-out test set. **Output**: `data/logs/evaluation_metrics.csv`.
- [ ] T030b_hypothesis_test [P] Hypothesis Test: **DEPENDS ON**: T029. **Action**: Perform statistical test (e.g., DeLong's test or bootstrap) for AUC delta ≥ 0.05 (or amended criterion). **Output**: `data/logs/hypothesis_test.json` with `p_value`, `delta`, `significant`: bool.
- [ ] T030 Calibration Plot: Generate calibration plot. **DEPENDS ON**: T029. **Action**: Plot predicted vs. actual probabilities. **Output**: `docs/calibration_plot.png`.
- [ ] T031 Final Report Generation: Generate final report. **DEPENDS ON**: T024d_metric, T030b_hypothesis_test, T030. **Action**: Compare full model vs. baseline. Test hypothesis. Include leakage-adjusted threshold if Correlational. **Output**: `docs/final_report.md`.
- [ ] T032 Sensitivity Analysis: Evaluate robustness of results. **DEPENDS ON**: T031. **Action**: Vary thresholds and re-run. **Output**: `docs/sensitivity_analysis.md`.
- [ ] T032b Circularity Quantification: **DEPENDS ON**: T024_methodology_decision. **Action**: Calculate and report the magnitude of circularity (shared variance) between predictors and outcomes if the "Correlational Analysis" path is active. **Output**: `docs/final_report.md` (updated).

---

## Phase 5: Orchestration & Governance

- [ ] T099a_graph Orchestration Graph Definition: **DEPENDS ON**: T001a. **Action**: Define the logical execution graph for the pipeline (dependencies between tasks). **Output**: `docs/pipeline_graph.yaml`. **Constraint**: Does NOT depend on task *execution* results.
- [ ] T099a_impl Orchestration Implementation: **DEPENDS ON**: T099a_graph. **Action**: Implement `run_full_pipeline.py` to execute tasks in order. **Output**: `code/run_full_pipeline.py`.
- [ ] T099b Execute Pipeline: **DEPENDS ON**: T099a_impl. **Action**: Run the full pipeline. **Output**: All artifacts in `data/` and `docs/`.

---

## Phase 7: Governance & Review Resolution (Post-Analysis)

**Purpose**: Address specific reviewer concerns regarding data provenance, circularity, and statistical validity raised during the analysis phase.

- [ ] T301 [US1] Explicitly Document Data Source Provenance: **DEPENDS ON**: T012d_ratification_gate. **Action**: If `flavordb` or `counterfactual` failed, create `docs/data_provenance.md` detailing the exact fallback to Recipe1M proxies, citing the specific Plan amendment (Section "Spec Amendment Proposal") and the rationale (unavailability of verified independent sources). **Output**: `docs/data_provenance.md`.
- [ ] T302 [US2] Implement Circularity Quantification: **DEPENDS ON**: T024_methodology_decision. **Action**: In `docs/final_report.md`, add a dedicated section "Limitations: Corpus Circularity" that explicitly states the correlation between predictor (Recipe1M embeddings) and outcome (Recipe1M ratings) and quantifies the shared variance using the leakage audit results. **Output**: `docs/final_report.md` (updated).
- [ ] T303 [US3] Validate Proxy Assumptions: **DEPENDS ON**: T016b, T019b. **Action**: Run a correlation check between the proxy-derived `flavor_similarity` and `compatibility_label` against a random baseline to ensure the proxy has non-zero signal. **Output**: `data/logs/proxy_validation.json`.
- [ ] T305 [US3] Update Hypothesis Statement: **DEPENDS ON**: T024_methodology_decision. **Action**: Ensure the final report's hypothesis statement explicitly reflects the "Correlational Analysis" scope (e.g., "Quantify associative strength within corpus") rather than "Causal Independence". **Output**: `docs/final_report.md` (updated).