# Tasks: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning  

**Input**: Design documents from `/specs/001-the-influence-of-algorithmic-recommendations/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data‑model.md`, `contracts/`  

## Phase 1 – Project scaffolding (shared infrastructure)

- [ ] **T001** Create required project directories:  
  `projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/`, `tests/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/processed/`, `docs/`, `docs/reports/`.  
  **Verification**: Run `ls -R projects/PROJ-367-the-influence-of-algorithmic-recommendat/` and confirm all listed folders appear.

- [ ] **T002** Add `__init__.py` files to make the `code/` and `tests/` packages importable (`code/__init__.py`, `tests/__init__.py`, `tests/unit/__init__.py`).  
  **Verification**: `python -c "import code"` should exit without ImportError.

- [ ] **T003** Create `projects/PROJ-367-the-influence-of-algorithmic-recommendat/code/requirements.txt` with pinned versions for the eight core packages:  

  ```text
  pandas==2.2.2
  numpy==1.26.4
  scikit-learn==1.5.0
  statsmodels==0.14.2
  scipy==1.13.0
  datasets==2.20.0
  pyyaml==6.0.2
  sentence-transformers==3.0.1
  ```  

  **Verification**: `pip install -r requirements.txt` completes without errors.

- [ ] **T004** Create `code/config.py` containing path constants, random‑seed settings, and a whitelist of verified dataset identifiers.  
  **Verification**: `python -c "from code.config import *; print(EDUCATIONAL_DATASET_IDS)"` prints a non‑empty list.

- [ ] **T005a** Define `DataSchemaError` exception class in `code/ingestion.py`.  
- [ ] **T005b** Implement schema‑validation logic in `code/ingestion.py` that raises `DataSchemaError` with the exact message:  

  ```
  Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design.
  ```  

- [ ] **T005c** Create unit test `tests/unit/test_ingestion.py::test_schema_error` that supplies a CSV missing the required columns and asserts the exception and message.  

- [ ] **T015** Implement `code/data_fetcher.py` to **download a real, publicly available educational dataset** (e.g., OULAD from Zenodo) that contains the required columns. The script must:  

  1. Verify the dataset identifier is in `config.EDUCATIONAL_DATASET_IDS`.  
  2. Download the file (streaming if > 7 GB) to `data/raw/verified_dataset.csv`.  
  3. Raise `DataAvailabilityError` with message  

     ```
     Verified educational dataset not found or inaccessible. Project blocked per Data Availability Gate.
     ```  

     if the download fails.  

  **Verification**: After running the script, `data/raw/verified_dataset.csv` exists and `head -n 1` shows the required column names.

- [ ] **T047** Create `code/validate_real_data.py` that loads `data/raw/verified_dataset.csv`, checks for the presence of `recommended_categories` and `enrolled_categories`, and raises `DataSchemaError` (FR‑007) if they are missing.  
  **Verification**: Run on a deliberately malformed CSV (`data/raw/mock_missing_columns.csv`) and confirm the exact exception message.

- [ ] **T045** Implement `code/metrics.py::calculate_shannon_entropy(categories: List[str]) -> float` using log‑base‑2.  
  **Verification**: `python -c "from code.metrics import calculate_shannon_entropy; print(calculate_shannon_entropy(['A','B','C']))"` matches manual calculation (≈1.585).

- [ ] **T046** Write unit test `tests/unit/test_metrics.py::test_entropy_single_category_returns_zero` asserting that a single‑category list returns 0.0 within 1e‑6 tolerance.

- [ ] **T007** Create `code/modeling.py` skeleton (imports, docstrings) so that `import code.modeling` succeeds.

- [ ] **T008** Create `code/robustness.py` skeleton so that `import code.robustness` succeeds.

- [ ] **T010** Add `code/main.py` helper `log_runtime(start: datetime, end: datetime)` that writes `{ "start": ..., "end": ..., "duration_seconds": ... }` to `data/processed/runtime_log.json`.  
  **Verification**: A short script calling the helper creates the JSON file with the three keys.

- [ ] **T011** Create `pytest.ini` with `testpaths = tests/` and a custom marker `us1, us2, us3`.  
  **Verification**: `pytest --collect-only` lists the marker definitions without error.

## Phase 2 – Foundations (validation & basic utilities)

- [ ] **T012** Unit test for entropy calculation (log‑base‑2) in `tests/unit/test_metrics.py`.  
- [ ] **T013** Unit test for schema validation (FR‑007) in `tests/unit/test_ingestion.py`.  

## Phase 3 – User Story 1: Data ingestion & diversity metrics (Priority P1)

- [ ] **T017** Implement `code/ingestion.py::ingest_and_clean(input_path: str) -> pd.DataFrame` that:  

  1. Loads the CSV/Parquet from `data/raw/verified_dataset.csv`.  
  2. Validates schema via `DataSchemaError`.  
  3. Excludes rows where `enrolled_categories` is empty, logs a warning with the count of excluded sessions.  
  4. Writes the cleaned dataframe (columns `user_id, session_id, recommended_categories, enrolled_categories`) to `data/processed/cleaned_data.parquet`.  

  **Verification**: After running, the Parquet file exists; `pd.read_parquet` shows no rows with empty `enrolled_categories`.

- [ ] **T018** Implement `code/metrics.py` functions `recommendation_diversity_score(row)` and `learner_diversity_score(row)` that compute Shannon entropy (log 2) on the raw category lists **after** optional semantic merging (see T050). Write results to a JSON file `data/processed/diversity_scores.json` with schema `{user_id, session_id, recommendation_diversity_score, learner_diversity_score}`.  
  **Verification**: Sample rows match manual entropy calculations within 0.001.

- [ ] **T019** Create full orchestration script `code/main.py` that:  

  1. Calls `code/data_fetcher.py` (if raw data missing).  
  2. Runs `code/validate_real_data.py`.  
  3. Executes `code/ingestion.py` to produce `cleaned_data.parquet`.  
  4. Calls the diversity‑score functions (T018) to produce `diversity_scores.json`.  
  5. Logs start/end timestamps via the helper from T010.  

  **Verification**: Running `python -m code.main` (or `python code/main.py`) finishes without error and produces both `data/processed/cleaned_data.parquet` and `data/processed/diversity_scores.json`.

- [ ] **T020** Add unit test `tests/unit/test_main_output.py` that loads the generated `diversity_scores.json`, recomputes entropy for a hard‑coded mini‑dataset (embedded in the test), and asserts each score matches within 0.001.  
  **Verification**: `pytest tests/unit/test_main_output.py` passes.

- [ ] **T021** Enhance `code/ingestion.py` so that rows with empty `enrolled_categories` are either (a) written with `"learner_diversity_score": null` **or** (b) excluded, **and** a warning log entry `WARNING: Excluded X sessions due to empty enrolled_categories` is emitted.  
  **Verification**: Log file `data/processed/runtime_log.json` (or a separate `data/processed/ingestion.log`) contains the warning with the correct count.

- [ ] **T050** Implement category‑merging step (FR‑009) in `code/preprocessing.py::merge_categories(categories: List[str], threshold: float) -> List[str]` using a lightweight semantic similarity model (e.g., `sentence-transformers/all-MiniLM-L6-v2`). The function merges any two categories whose cosine distance is ≤ `threshold`.  
  **Verification**: Unit test `tests/unit/test_preprocessing.py::test_category_merging` confirms that with a threshold of 0.05, synonyms like “Mathematics” and “Math” are merged into a single token.

- [ ] **T051** Perform the sensitivity‑analysis sweep (FR‑005) in `code/robustness.py::run_sensitivity_analysis(thresholds: List[float]) -> pd.DataFrame`. The function:  

  1. For each threshold in `{0.01, 0.05, 0.1}` calls the merging routine (T050), recomputes diversity scores, fits the weighted regression (T025/T026), and records the coefficient and p‑value.  
  2. Writes a CSV `data/processed/sensitivity_analysis.csv` with columns `threshold, coefficient, p_value`.  

  **Verification**: The CSV contains three rows; at least two rows have `p_value < 0.05`. A unit test `tests/unit/test_robustness.py::test_sensitivity_stability` checks this condition.

## Phase 4 – User Story 2: Baseline control & Propensity‑Score Weighting (Priority P2)

- [ ] **T022** Unit test for baseline‑vector derivation (`tests/unit/test_modeling.py::test_baseline_vector_shape`).  
- [ ] **T023** Unit test that PSW weights are flagged when any weight exceeds 10 × median (`tests/unit/test_modeling.py::test_extreme_weights_flag`).  
- [ ] **T024** Implement baseline‑interest vector construction in `code/modeling.py::compute_baseline_vectors(df)`. Uses pre‑study enrollment history to produce a normalized probability distribution per user.  
- [ ] **T025** Implement PSW logic in `code/modeling.py::fit_psw(df, baseline_vectors)` that returns stabilized weights and logs weight‑distribution statistics.  
- [ ] **T026** Fit a weighted linear regression (`statsmodels.WLS`) with predictor `recommendation_diversity_score`, outcome `learner_diversity_score`, covariate `baseline_vector` (or its principal components). Compute VIF for each covariate; if any VIF > 5, log a warning. Output results to `data/processed/model_results.csv` matching `output.schema.yaml`.  
- [ ] **T042** Add detection of unique‑user count `< 30` and set flag `use_gls = True`.  
- [ ] **T043** If `use_gls` is true, run a Generalized Least Squares model with robust standard errors instead of the weighted regression.  
- [ ] **T044** Log methodological switches (extreme weights, GLS fallback) to `data/processed/modeling.log`.  

## Phase 5 – User Story 3: Robustness verification (Priority P3)

- [ ] **T029** Unit test `tests/unit/test_robustness.py::test_residual_permutation` that runs the permutation routine on a tiny synthetic dataset (size 10) and checks that the returned p‑value lies in `[0,1]`.  
- [ ] **T031** Implement residual permutation test in `code/robustness.py::run_residual_permutation(iterations: int = 1000)`. Steps:  

  1. Fit the primary model (weighted regression or GLS).  
  2. Extract residuals, shuffle them `iterations` times, refit, collect coefficient each iteration.  
  3. Compute observed‑effect, null‑distribution mean/std, and p‑value (proportion of permuted coefficients ≥ observed).  
  4. Write `data/processed/permutation_test_results.json` containing the full summary per `output.schema.yaml`.  

## Phase 6 – Reporting & associational framing (cross‑cutting)

- [ ] **T034a** Generate final report `docs/reports/final_analysis.md` that:  

  - Summarizes model coefficients, weight distribution, VIF diagnostics, sensitivity‑analysis table, and permutation‑test results.  
  - Explicitly states *“Findings are associational; no causal claims are made due to lack of randomization.”* (FR‑006).  
  - Includes a “Limitations: Observational Data” section.  

- [ ] **T034b** Create `code/validate_framing.py` that scans `final_analysis.md` for forbidden causal terms (`causes`, `leads to`, `determines`) and exits with non‑zero status if any are found.  
- [ ] **T035** Read `data/processed/runtime_log.json` and append total runtime (in hours) to the final report. If runtime > 6 h, append a warning line “⚠️ Runtime exceeds the 6‑hour GitHub‑Actions limit.”  

## Phase 7 – Polishing & documentation

- [ ] **T036a** Update `docs/quickstart.md` with concrete commands for data fetch, pipeline execution (`python -m code.main`), and how to run the test suite.  
- [ ] **T036b** Update `docs/data-model.md` to include newly added fields (`recommendation_diversity_score`, `learner_diversity_score`, `baseline_vector`, `weight`).  
- [ ] **T037** Add edge‑case unit tests (empty category lists, N < 30 scenario) in `tests/unit/`.  
- [ ] **T038** Run the quick‑start validation script; checksum the generated `state.yaml` (managed by the platform) to ensure reproducibility.

---

### Dependency & execution order summary

| Phase | Must‑complete before |
|-------|----------------------|
| 1  (Scaffolding) | none |
| 2  (Foundations) | Phase 1 |
| 3  (US 1) | Phase 2 |
| 4  (US 2) | Phase 2 + US 1 output (`diversity_scores.json`) |
| 5  (US 3) | Phase 2 + US 2 output (`model_results.csv`) |
| 6  (Reporting) | US 2 & US 3 |
| 7  (Polish) | All previous phases |

Parallelism is possible for any tasks marked `[P]` (different files, no data‑flow dependencies). All other tasks follow the data‑flow chain indicated above.
