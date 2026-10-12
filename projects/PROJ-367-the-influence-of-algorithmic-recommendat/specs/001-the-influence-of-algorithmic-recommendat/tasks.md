# Tasks: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/` from `specs/001-the-influence-of-algorithmic-recommendations/`  
**Prerequisites**: All Phase‑0/1 design artifacts complete.

## Phase 0: Data Fetching & Validation

- [ ] T001 [US1] Fetch the real OULAD dataset and validate its schema in `code/data_fetcher.py` (FR-007).   <!-- FAILED-IN-EXECUTION: code/data_fetcher.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_fetcher.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_fetcher.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_fetcher.py exit=1 -->
  Download the Open University Learning Analytics Dataset (OULAD) from its official source (`https://analyse.kmi.open.ac.uk/open_dataset`) – files `studentInfo.csv`, `studentVle.csv`, `vle.csv`, `studentRegistration.csv`; if the primary host is unreachable, fetch the mirrored ZIP `https://prod-dcd-datasets-cache-zipfiles.s3.eu-west-1.amazonaws.com/9b3hc-8t26.zip` (Figshare/Data‑in‑Cache artifact). Save raw CSVs under `data/raw/oulad/`. The fetcher must raise on failure — NO synthetic/mock fallback. Then map OULAD fields to the session schema (`user_id`, `session_id`, `recommended_categories` from top‑K VLE resource categories accessed in the observation window, `enrolled_categories` from actual module enrollments), per the plan's proxy design, and validate the derived table contains both category columns; if missing, raise `DataSchemaError("Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design.")`.  
  **Verification**: `python -m code.data_fetcher` exits 0; `data/raw/oulad/*.csv` exist with real row counts > 0; the derived session table in `data/processed/cleaned_data.parquet` has the four required columns; running against a deliberately malformed CSV raises the exact error message (unit test `tests/unit/test_data_fetcher.py::test_schema_error`).

## Phase 1: Preprocessing & Metric Calculation

- [ ] T002 [US1] Implement diversity metrics with category merging, handle missing recommendation logs, and their unit tests in `code/preprocessing.py` (FR-001, FR-009).  
  Implement `calculate_shannon_entropy(categories) -> float` using log base 2 (single‑category list returns exactly 0.0), and `merge_categories(categories, threshold)` that merges categories whose semantic similarity distance is below the threshold (character/TF‑IDF cosine distance via scikit‑learn). **Rows where `recommended_categories` is missing or empty must be excluded from the analysis dataframe**; the pipeline must log the count of such excluded sessions. Rows with empty `enrolled_categories` must yield `learner_diversity_score = null` and be excluded from the analysis dataframe with a logged warning count (Edge Case 1). Write per‑session scores to `data/processed/diversity_scores.json` matching `contracts/dataset.schema.yaml`.  
  **Verification**: `pytest tests/unit/test_preprocessing.py` passes, including: entropy of `['A','B','C']` ≈ 1.585 within 0.001; single category returns 0.0 within 1e-6; empty enrollment yields null plus logged warning; missing recommendation rows are excluded and the exclusion count appears in logs; merging at threshold 0.05 collapses near‑duplicate labels.

- [ ] T003 [US1] Connect the pipeline entry point and run a small real end‑to‑end case in `code/main.py` (SC-005).  
  Orchestrate fetch → validate → preprocess, producing `data/processed/cleaned_data.parquet` and `data/processed/diversity_scores.json` from a first real subset (e.g., first 200 OULAD students), with start/end timestamps and duration written to `data/processed/runtime_log.json`. Do NOT write to `state/` — the platform owns canonical state.  
  **Verification**: `python -m code.main` completes without error on the real subset; both artifacts exist; `tests/unit/test_main_output.py` recomputes entropy for a hard‑coded mini‑dataset embedded in the test and asserts each score matches within 0.001.

## Phase 2: Modeling

- [ ] T004 [US2] Implement baseline vectors, propensity‑score weighting, primary model, and correct fallback logic in `code/modeling.py` (FR-002, FR-003, FR-008, SC-001, SC-004).  
  Implement `compute_baseline_vectors(df)` deriving a normalized pre‑study enrollment‑history distribution per user (uniform imputation for users with no history, flagged in the data dictionary). Implement `fit_psw(df, baseline_vectors)` producing stabilized weights; report effective sample size and flag extreme weights (> 10× median). **Fallback logic**:  
    1. If the propensity‑score model fails to converge **or** produces unstable weights, fall back to a **standard linear regression with robust (HC3) standard errors**.  
    2. If the total number of unique users is **< 30**, fall back to a **Generalized Least Squares (GLS) model with robust standard errors**.  
  Fit the chosen regression (weighted or fallback) of `learner_diversity_score` on `recommendation_diversity_score` with baseline controls (principal components of the baseline vector). Compute VIF for each covariate and flag if any exceeds 5.0. Write results to `data/processed/model_results.json` conforming to `contracts/output.schema.yaml` (single JSON object with nested `weights_distribution`, `sensitivity_analysis`, and `permutation_test` fields).  
  **Verification**: `pytest tests/unit/test_modeling.py` passes, covering baseline‑vector shape, extreme‑weight flagging, convergence‑failure fallback to robust OLS, and N < 30 GLS fallback; running on the full real dataset produces `model_results.json` with all required fields populated from real data.

## Phase 3: Robustness

- [ ] T005 [US3] Implement the residual permutation test in `code/robustness.py` (FR-004, SC-003).  
  Implement `run_residual_permutation(iterations=1000)` (minimum 1,000 iterations, fixed random seed): fit the primary model (as produced by T004), extract residuals, shuffle them 1,000 times, refit, and collect the coefficient each iteration. Compute the observed effect, null‑distribution mean/std, and permuted p‑value (proportion of permuted coefficients ≥ observed). Write the full summary to `data/processed/permutation_test_results.json` per `contracts/output.schema.yaml`.  
  **Verification**: `pytest tests/unit/test_robustness.py::test_residual_permutation` runs on a deterministic subset defined as the **first 200 rows** of `cleaned_data.parquet` and returns a p‑value in [0, 1]; the JSON artifact contains `observed_effect`, `null_distribution_mean`, `null_distribution_std`, `p_value_permuted`, and `iterations >= 1000`.

- [ ] T006 [US3] Run the full‑model sensitivity sweep over semantic similarity thresholds in `code/robustness.py` (FR-005, SC-002).  
  Implement `run_sensitivity_analysis(thresholds=[0.01, 0.05, 0.1])`: for each threshold, re‑merge categories, recompute diversity scores, refit the regression (using the logic from T004), and record the coefficient and p‑value. Write `data/processed/sensitivity_analysis.csv` with columns `threshold,coefficient,p_value`. If the p‑value flips significance across the sweep, append an explicit **"Sensitivity Warning"** to the results stating the result is threshold‑dependent — do not suppress or tune toward significance.  
  **Verification**: The CSV contains exactly three rows from the full dataset; `tests/unit/test_robustness.py::test_sensitivity_stability` checks the 2/3 stability criterion and the warning logic; the observed outcome (stable or threshold‑dependent) is reported honestly either way.  
  **Execution Order**: Must be run **after** T005 completes to avoid concurrent writes to the same module/test file.

- [ ] T007 [US2] Execute the complete pipeline on the full real OULAD dataset and record all diagnostics.  
  Run `python -m code.main` end‑to‑end on the full dataset (streaming/chunked processing if memory requires), producing all artifacts: `cleaned_data.parquet`, `diversity_scores.json`, `model_results.json`, `sensitivity_analysis.csv`, `permutation_test_results.json`, `runtime_log.json`. Log excluded‑session counts, imputation flags, and any methodological fallbacks actually triggered. All numbers must come from the real run — no placeholder or expected values.  
  **Verification**: Every artifact exists and is non‑empty; runtime recorded in `runtime_log.json`; excluded‑session and imputation counts appear in the logs; re‑running is idempotent (fixed seeds).

## Phase 4: Reporting

- [ ] T008 [US3] Generate the results tables and figures from the validated outputs.  
  Create `figures/` outputs generated directly from `data/processed/` artifacts: (a) a partial‑regression / scatter plot of recommendation vs. learner diversity with the fitted weighted slope; (b) a histogram of the permutation null distribution with the observed effect marked; (c) the sensitivity‑sweep table rendered in the report. Include uncertainty (confidence intervals) on the primary coefficient.  
  **Verification**: Each figure file exists and its underlying data traces to a specific `data/processed/` artifact; the report's statistics match the JSON/CSV values exactly.

- [ ] T009 [US2] Write the methods/results report with strict associational framing in `docs/reports/analysis_report.md` (FR-006).  
  Summarize the model coefficient, standard error, p‑value, weight distribution, VIF diagnostics, sensitivity table, and permutation results, each linked to its artifact. Include the exact statement "Findings are associational; no causal claims are made due to lack of randomization." plus a "Limitations: Observational Data" section covering the VLE‑proxy for recommendations, the baseline‑vector proxy, and the payoff‑structure caveat raised in prior review (observed behavior may reflect equilibrium strategies absent explicit utility models). Append total runtime from `runtime_log.json`; if runtime > 6 h, append the warning line. Implement `code/validate_framing.py` scanning the report for forbidden causal terms (`causes`, `leads to`, `determines`) and exiting non‑zero if found.  
  **Verification**: `python code/validate_framing.py` exits 0; the report contains no causal language; every reported number matches a `data/processed/` artifact.

- [ ] T010 Document the runnable workflow and paper‑stage handoff in the feature's `quickstart.md`.  
  Record concrete commands: dataset fetch, `python -m code.main`, and `pytest tests/`. Document the data dictionary (including the baseline‑imputation flag), the exact sampling/streaming rules if any subset was used, and the paper‑stage handoff: the report path, figure paths, and the associational‑framing requirement the paper stage must preserve.  
  **Verification**: A fresh runner executing the quickstart commands from `data/raw/` inputs reproduces the pipeline and all `pytest` tests pass; the handoff section names every result artifact.

## Phase 5: Test Suites

- [ ] T011 [US?] Run the integration test suite `tests/integration/test_pipeline.py` to validate the full pipeline on a realistic subset (e.g., first 200 sessions).  
  Execute `pytest tests/integration/test_pipeline.py` after T003; ensure the end‑to‑end flow (fetch → preprocess → model → robustness) completes without error and produces the expected intermediate artifacts.  
  **Verification**: The test exits with 0 and asserts presence and schema conformity of `cleaned_data.parquet`, `diversity_scores.json`, and `model_results.json`.

- [ ] T012 [US?] Run the contract test suite `tests/contract/test_schemas.py` to validate dataset and output schemas against `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`.  
  Execute `pytest tests/contract/test_schemas.py` after the respective artifacts are generated.  
  **Verification**: All schema validation tests pass, confirming that `data/processed/diversity_scores.json` conforms to the dataset schema and `data/processed/model_results.json` conforms to the output schema.
