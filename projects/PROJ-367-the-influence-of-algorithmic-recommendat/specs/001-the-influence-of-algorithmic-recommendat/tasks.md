# Tasks: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts from `specs/001-the-influence-of-algorithmic-recommendat/`, and any reviewer feedback.

The following tasks implement the smallest complete, reproducible study that satisfies every functional requirement, success criterion, and reviewer comment. Tasks are ordered to respect data flow and scientific dependencies. All paths are relative to the project root.

---

## Phase 0 – Dataset discovery & validation  

| Goal | Obtain a real dataset that contains the required `recommended_categories` and `enrolled_categories` columns, or, if none exists, create a deterministic synthetic dataset while documenting the limitation. |

- [ ] T001 [US1] **Locate a verified open‑source dataset** containing distinct `recommended_categories` and `enrolled_categories` columns.   <!-- FAILED-IN-EXECUTION: code/data_fetcher.py exit=1 -->
  *Implementation*: Add a script `code/data_fetcher.py` that (a) searches known repositories (OpenML, Zenodo, Kaggle) for datasets whose schema matches `specs/.../contracts/dataset.schema.yaml`; (b) downloads the first matching dataset; (c) validates the schema using `jsonschema`.  
  *Verification*: `pytest tests/unit/test_data_fetcher.py::test_find_real_dataset` passes – it asserts that the downloaded parquet contains the required columns and that the script exits with status 0. If no dataset is found, the script **raises a `DataSchemaError` with the message** `"Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design."` **but does not abort the pipeline; the orchestrator catches this exception and proceeds to the synthetic fallback (T002).**

- [ ] T002 [US1] **Generate a deterministic synthetic dataset** when no real dataset is available.  
  *Implementation*: Extend `code/data_fetcher.py` with a fallback function `generate_synthetic_dataset(seed=42, n_users=200, n_sessions=500)` that writes `data/raw/synthetic_dataset.parquet`. The synthetic data includes `user_id`, `session_id`, `recommended_categories`, `enrolled_categories`, and optional covariates, all generated from the fixed seed. The script records the used seed in `data/raw/synthetic_seed.txt` and computes a SHA‑256 checksum of the parquet file, storing it in `data/raw/synthetic_checksum.txt`. It also adds a clear “Synthetic‑Data‑Limitation” note to `docs/limitations.md`.  
  *Verification*: `pytest tests/unit/test_data_fetcher.py::test_synthetic_generation` checks that the file exists, contains the required columns, and that the checksum file matches the checksum computed at runtime (no hard‑coded value).

- [ ] T021 [US1] **Record the random seed used for synthetic data generation**.  
  *Implementation*: After synthetic generation, write the seed value (e.g., `42`) to `data/raw/synthetic_seed.txt` and include this file in the artifact checksum log.  
  *Verification*: `pytest tests/unit/test_data_fetcher.py::test_seed_recorded` asserts that `synthetic_seed.txt` exists and contains the integer seed used.

---

## Phase 1 – Preprocessing & metric construction  

| Goal | Produce cleaned data, diversity scores, and baseline interest vectors. |

- [ ] T003 [US1] **Semantic merging & Shannon‑entropy calculation** (`code/preprocessing.py`).  
  *Features*:  
  • Load category embeddings via `sentence‑transformers/all‑MiniLM‑L6‑v2`.  
  • `merge_categories(categories, threshold)` merges any pair whose cosine distance ≤ threshold (default 0.05).  
  • `calculate_shannon_entropy(categories)` uses log base 2; returns `0.0` for a single‑category list and `null` for an empty list.  
  • Handle missing `recommended_categories` by excluding the session (logged).  
  • Handle empty `enrolled_categories` by setting `learner_diversity_score = null` and logging a warning.  
  *Outputs*: `data/processed/cleaned_data.parquet`, `data/processed/diversity_scores.json`.  
  *Verification*: `pytest tests/unit/test_preprocessing.py` validates entropy values (e.g., `['A','B','C']` ≈ 1.585 ± 0.001), correct handling of edge cases, and that merging at 0.05 reduces near‑duplicate labels.

- [ ] T004 [US1] **Baseline interest vector derivation** (`code/preprocessing.py`).  
  *Features*: For each `user_id`, compute a normalized frequency distribution over all categories appearing in the user’s pre‑study enrollment history. Users with no history receive a uniform distribution over the full category set; this imputation is flagged in `data/processed/baseline_vectors.parquet` and noted in `docs/limitations.md`.  
  *Verification*: `pytest tests/unit/test_preprocessing.py::test_baseline_vectors` checks vector shape, sum‑to‑1 property, and correct flagging of imputed users.

- [ ] T005 [US1] **Pipeline orchestration & small‑scale end‑to‑end run** (`code/main.py`).  
  *Steps*: invoke `data_fetcher`, `preprocessing`, and write a lightweight `data/processed/runtime_log.json` (wall‑clock time, memory usage). Run on the first 200 sessions of the raw dataset to produce a quick sanity‑check run.  
  *Verification*: `pytest tests/unit/test_main.py` asserts that the three artifacts (`cleaned_data.parquet`, `diversity_scores.json`, `runtime_log.json`) exist and that the runtime is < 300 s for the subset.

---

## Phase 2 – Modeling (propensity weighting & regression)  

| Goal | Estimate the effect of recommendation diversity while controlling for baseline interests. |

- [ ] T006 [US2] **Generalized Propensity Score Weighting (GPSW) for continuous exposure** (`code/modeling.py`).  
  *Approach*:  
  1. Fit a Gaussian linear model `Recommendation_Diversity ~ Baseline_Vector + session_length + time_of_day + platform_version`.  
  2. Estimate the conditional normal density `f(D|X)` using the predicted mean and residual variance.  
  3. Compute raw GPSW weight = 1 / f(D|X) and stabilize by multiplying with the marginal density of `Recommendation_Diversity` (kernel density estimate).  
  4. Flag extreme weights (> 10 × median) and compute effective sample size.  
  *Fallbacks*:  
  • If the GPS model fails to converge or produces unstable weights, fall back to **standard OLS with HC3 robust SEs**.  
  • If the number of unique users < 30, automatically use **Generalized Least Squares (GLS) with heteroskedastic‑consistent SEs**.  
  *Verification*: `pytest tests/unit/test_modeling.py::test_gpsw_success` and `::test_fallback_logic` confirm weight statistics, flagging, and correct model selection.

- [ ] T007 [US2] **Weighted linear regression (or fallback) & diagnostics** (`code/modeling.py`).  
  *Features*:  
  • Fit the chosen regression of `learner_diversity_score` on `recommendation_diversity_score` plus baseline covariates (principal components of the baseline vector).  
  • Compute VIF for each covariate; if any VIF > 5.0, add a warning entry in `model_results.json`.  
  • Assemble results into a single JSON object conforming to `contracts/output.schema.yaml` (`data/processed/model_results.json`).  
  *Verification*: `pytest tests/unit/test_modeling.py::test_regression_output` checks JSON schema compliance, presence of `coefficient`, `std_error`, `p_value`, `vif`, `convergence_status`, and weight summary statistics.

- [ ] T017 [US2] **Correlation coefficient computation & significance test** (`code/analysis.py`).  
  *Procedure*: Compute the Pearson correlation between `recommendation_diversity_score` and `learner_diversity_score` on the cleaned dataset, perform a two‑sided hypothesis test against the null of zero correlation, and record the correlation coefficient, p‑value, and 95 % confidence interval. Output results to `data/processed/correlation_results.json` (conforms to a simple schema).  
  *Verification*: `pytest tests/unit/test_analysis.py::test_correlation` asserts that the JSON contains `correlation`, `p_value`, and that `p_value < 0.05` for the primary dataset (or logs a warning if not).

---

## Phase 3 – Robustness checks  

| Goal | Validate that the observed effect is not an artifact of unmeasured confounders or threshold choices. |

- [ ] T008 [US3] **Residual permutation test** (`code/robustness.py`).  
  *Procedure*:  
  1. Using the final model from T007, extract residuals.  
  2. For each of **1,000** iterations (fixed seed = 12345), permute residuals, add them back to fitted values, recompute GPSW weights, and refit the regression.  
  3. Collect the `Recommendation_Diversity` coefficient each iteration to form a null distribution.  
  4. Compute observed effect, null‑distribution mean/std, and two‑sided p‑value (`p_value_permuted`).  
  *Output*: `data/processed/permutation_test_results.json` (matches `output.schema.yaml`).  
  *Verification*: `pytest tests/unit/test_robustness.py::test_permutation` runs on the 200‑session subset and asserts that the JSON contains all required fields and that `iterations >= 1000`.

- [ ] T018 [US3] **False‑positive rate assessment for permutation test** (`code/robustness.py`).  
  *Procedure*: Using the null distribution from T008, compute the proportion of permuted coefficients that are as extreme as or more extreme than the observed coefficient (two‑sided). Verify that this false‑positive rate ≤ 0.05; if it exceeds, log a methodological warning and fail the verification step. Output to `data/processed/permutation_fpr.json`.  
  *Verification*: `pytest tests/unit/test_robustness.py::test_fpr` asserts that the recorded false‑positive rate is ≤ 0.05.

- [ ] T009 [US3] **Semantic‑threshold sensitivity sweep** (`code/robustness.py`).  
  *Steps*: For thresholds `{0.01, 0.05, 0.1}`:  
  1. Re‑run the merging step (T003) with the given threshold.  
  2. Re‑compute diversity scores, baseline vectors (unchanged), GPSW weights, and regression (T006/T007).  
  3. Record `threshold`, `coefficient`, and `p_value` in `data/processed/sensitivity_analysis.csv`.  
  4. If the p‑value flips significance (p < 0.05 ↔ p ≥ 0.05) for any threshold, append a **"Sensitivity Warning"** line to the CSV and to the final report.  
  *Verification*: `pytest tests/unit/test_robustness.py::test_sensitivity_stability` checks that at least 2/3 of thresholds yield p < 0.05 (per SC‑002) and that the warning appears when the criterion is not met.

- [ ] T010 [US2] **Full‑scale pipeline execution on the complete dataset** (`code/main.py`).  
  *Action*: Run the orchestrator on the entire raw dataset (streaming if needed to stay < 5 GB RAM). Produce all artifacts: `cleaned_data.parquet`, `diversity_scores.json`, `baseline_vectors.parquet`, `model_results.json`, `permutation_test_results.json`, `sensitivity_analysis.csv`, `correlation_results.json`, `runtime_log.json`, and checksum/seed logs.  
  *Verification*: After execution, a sanity‑check script `code/validate_artifacts.py` confirms that each file exists, is non‑empty, and that schema validation passes (`tests/contract/test_schemas.py`). The script also records any methodological fallbacks actually triggered.

- [ ] T019 [US3] **Runtime budget verification** (`code/validation.py`).  
  *Procedure*: Read the total wall‑clock time from `runtime_log.json` and assert that it is ≤ 6 hours (21,600 seconds). If the limit is exceeded, raise a `RuntimeError` with a clear message.  
  *Verification*: `pytest tests/unit/test_validation.py::test_runtime_budget` ensures the check passes on the CI runner.

---

## Phase 4 – Results generation & handoff  

| Goal | Create reproducible figures, a fully compliant report, and documentation for downstream paper work. |

- [ ] T011 [US3] **Generate figures** (`code/figures.py`).  
  *Figures*:  
  1. Partial‑regression scatter plot of `Recommendation_Diversity` vs. `Learner_Diversity` with fitted weighted slope and 95 % CI.  
  2. Histogram of the permutation null distribution with the observed coefficient marked.  
  3. Sensitivity‑sweep heat‑map (threshold vs. coefficient/p‑value).  
  Files saved under `figures/` as `.png` and `.svg`.  
  *Verification*: `pytest tests/unit/test_figures.py` loads each image and checks that its size > 0 bytes and that the underlying data (e.g., CSV used for the heat‑map) matches the corresponding processed artifact.

- [ ] T012 [US3] **Write associational methods & results report** (`docs/reports/analysis_report.md`).  
  *Content*:  
  • Summary of data source (real or synthetic) and its limitation.  
  • Description of preprocessing, GPSW, regression, permutation test, sensitivity analysis, and correlation analysis.  
  • All numeric results (coefficient, SE, p‑value, VIF, weight stats, permutation p‑value, sensitivity table, correlation coefficient and its p‑value).  
  • Explicit statement: “Findings are associational; no causal claims are made due to lack of randomization.” (FR‑006).  
  • Limitations section covering synthetic data (if used), proxy recommendation log, baseline‑vector imputation, and any fallback models triggered.  
  • Links to each artifact (e.g., `model_results.json`, `permutation_test_results.json`, `correlation_results.json`).  
  *Verification*: Run `python code/validate_framing.py docs/reports/analysis_report.md`; it exits 0 only if the report contains none of the forbidden causal terms (`causes`, `leads to`, `determines`). Unit test `tests/unit/test_report_framing.py` enforces this.

- [ ] T013 [US?] **Quickstart & paper‑stage handoff documentation** (`quickstart.md`).  
  *Contents*:  
  • One‑line command to fetch data (`python -m code.data_fetcher`).  
  • Full pipeline command (`python -m code.main`).  
  • Test suite command (`pytest`).  
  • Description of the data dictionary (including baseline‑imputation flag).  
  • Paths to final artifacts (`docs/reports/analysis_report.md`, `figures/`, `data/processed/`).  
  • Note that the paper stage must retain the associational framing and cite the limitation sections.  
  *Verification*: Running the commands from a fresh runner reproduces the entire pipeline and all tests pass.

---

## Phase 5 – Test suites  

| Goal | Ensure correctness, reproducibility, and contract compliance. |

- [ ] T014 [US?] **Unit test suite** (`tests/unit/`).  
  Includes `test_data_fetcher.py`, `test_preprocessing.py`, `test_modeling.py`, `test_robustness.py`, `test_analysis.py`, `test_figures.py`, `test_report_framing.py`, `test_validation.py`. All tests must pass (`pytest -q` returns exit 0).  
  *Verification*: CI runs `pytest tests/unit` and fails if any test fails.

- [ ] T015 [US?] **Integration test on realistic subset** (`tests/integration/test_pipeline.py`).  
  Executes the full pipeline on the first 200 sessions of the raw dataset, checks that each intermediate artifact is created, and that the final `model_results.json` matches the schema.  
  *Verification*: Integration test passes on CI after T010 has generated the subset artifacts.

- [ ] T016 [US?] **Contract validation tests** (`tests/contract/test_schemas.py`).  
  Uses `jsonschema` to validate `data/processed/diversity_scores.json` against `contracts/dataset.schema.yaml` and `model_results.json` against `contracts/output.schema.yaml`.  
  *Verification*: All schema validations succeed; failures abort the run.

---

### Dependency Summary

| Spec / Success Criterion | Satisfied by Task |
|--------------------------|-------------------|
| FR‑001, FR‑009            | T003 |
| FR‑002                    | T004 |
| FR‑003, FR‑008            | T006, T007 |
| FR‑004                    | T008 |
| FR‑005                    | T009 |
| FR‑006                    | T012 |
| FR‑007                    | T001 (raises DataSchemaError) / T002 (synthetic fallback) |
| FR‑009                    | T003 (semantic merging) |
| SC‑001                    | T017 |
| SC‑002                    | T009 |
| SC‑003                    | T018 |
| SC‑004                    | T007 |
| SC‑005                    | T019 |
| Edge‑case handling        | T003, T004, T006, T007 |

All tasks are unchecked (`- [ ]`) and ready for implementation. The pipeline can be executed end‑to‑end once the tasks are completed, producing real (or transparently synthetic) evidence that satisfies the specification and reviewer concerns.  