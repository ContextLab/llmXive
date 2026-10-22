# Tasks: Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance

**Inputs**: Feature specification (`spec.md`), implementation plan (`plan.md`), research‑question validation, data model (`data-model.md`), and output contracts (`model_output.schema.yaml`, `processed_data.schema.yaml`).

The study acquires paired metabolomics–herbivory data from public repositories, preprocesses and normalizes it, explores correlations, fits baseline OLS and phylogenetically‑adjusted models, trains a Random Forest regressor, applies rigorous multiple‑comparison correction, performs power and sensitivity analyses, and generates reproducible reports and hand‑off documentation. All steps are designed to run on the GitHub Actions free‑tier CPU runner (2 cores, ~7 GB RAM, ≤ 6 h).

---

## Phase 1: Setup and first end‑to‑end analysis

**Goal**: Establish project structure, configure dependencies, acquire a real dataset, and run a minimal executable analysis to confirm data flow and output contracts early.

- [X] T001 [US‑1] **Project initialization and data‑acquisition framework**
  - Create `code/` with `src/`, `tests/`, `scripts/` sub‑directories; create `data/raw/`, `data/processed/`, `outputs/`, `contracts/`.  
  - Add `requirements.txt` (Python 3.11, pandas, numpy, scikit‑learn, statsmodels, seaborn, matplotlib, dendropy, requests, tqdm, scipy, fuzzywuzzy, python‑Levenshtein, pytest).  
  - Implement `code/src/config.py` fixing random seeds (`np.random.seed(42)`, `random.seed(42)`, `random_state=42`).  
  - Implement `code/src/fetch_data.py` with three fetch functions (`fetch_metabolights()`, `fetch_pmn()`, `fetch_hpid()`) that each (a) query the documented REST endpoint, (b) return a `pd.DataFrame` with required columns, and (c) retry up‑to‑3 times with exponential back‑off (30 s base) before raising.  
  - Write `code/tests/test_fetch_data.py` checking: (i) column presence, (ii) no missing values in required columns, (iii) ≥ 1 species per successful fetch.  
  - Verification: run `pytest code/tests/test_fetch_data.py -v`; ensure `outputs/fetch_log.txt` records a sample of fetched species IDs and that total paired species ≥ 50 (FR‑001).  
  - **Paths**: `code/src/config.py`, `code/src/fetch_data.py`, `code/tests/test_fetch_data.py`, `requirements.txt`, `outputs/fetch_log.txt`.

- [ ] T002 [US‑1] **Data ingestion and preprocessing pipeline**  
  - Implement `code/src/preprocess.py` with function `load_and_preprocess(raw_dfs: List[pd.DataFrame]) -> pd.DataFrame` that:  
    1. Concatenates the raw DataFrames and harmonises column names.  
    2. Filters out rows missing any required predictor or outcome column.  
    3. For metabolite‑class columns documented as biologically absent, inserts a zero **after** standardisation and records the absence in an `absence_indicator` JSON column; true missing values are excluded.  
    4. Detects extreme herbivory outliers via the IQR method (1.5 × IQR) and caps them, logging any caps.  
    5. Z‑scores the four metabolite columns using `sklearn.preprocessing.StandardScaler`.  
    6. Validates the resulting DataFrame against `contracts/processed_data.schema.yaml` with `jsonschema`.  
    7. Writes the cleaned DataFrame to `data/processed/clean.parquet` and records its SHA‑256 checksum in `outputs/preprocessing_log.json`.  
  - Write `code/tests/test_preprocess.py` verifying: (i) no missing values in required columns, (ii) each metabolite column has mean ≈ 0 and std ≈ 1, (iii) `absence_indicator` correctly populated, (iv) schema validation passes, (v) checksum file exists and contains a valid entry.  
  - Verification: run `pytest code/tests/test_preprocess.py -v`; inspect `data/processed/clean.parquet` for correct schema, column names, and data types.  
  - **Paths**: `code/src/preprocess.py`, `code/tests/test_preprocess.py`, `data/processed/clean.parquet`, `outputs/preprocessing_log.json`.

- [ ] T003 [US‑2] **Exploratory correlation analysis and heat‑map visualisation**   <!-- FAILED-IN-EXECUTION: code/src/correlation_analysis.py exit=1 -->
  - Implement `code/src/correlation_analysis.py` with function `compute_correlations(df: pd.DataFrame) -> dict` that:  
    1. Computes Pearson r between each metabolite class (averaged across compounds) and `herbivory_score`.  
    2. Calculates two‑tailed p‑values via `scipy.stats.pearsonr`.  
    3. Applies Benjamini‑Hochberg FDR correction to the four class‑level p‑values (q < 0.05).  
    4. Selects metabolite classes with **significant negative** correlation (q < 0.05, r < 0) and enforces that the total number of such classes is **between 3 and 5 inclusive** (FR‑003).  
    5. Returns an `AnalysisResult` dict (`result_type="correlation"`) containing `matrix`, `p_values`, `q_values`, `significant_negative_classes`, and `method="Pearson"`.  
  - Implement `code/src/visualization.py` with function `plot_correlation_heatmap(corr_dict: dict, out_path: str)` that creates a seaborn heat‑map PNG: cells show correlation coefficients, asterisks or colour intensity denote significance (q < 0.05), axes labelled with metabolite classes and `herbivory_score`.  
  - Write `code/tests/test_correlation.py` verifying: (i) coefficients lie in [‑1, 1], (ii) p‑values/q‑values in [0, 1], (iii) length of `significant_negative_classes` is 3‑5, (iv) task raises an informative error if the length falls outside this range.  
  - Verification: run the analysis on `data/processed/clean.parquet`, save the `AnalysisResult` JSON to `outputs/correlation_results.json` and the heat‑map PNG to `outputs/heatmap.png`. Ensure exactly 3‑5 classes are reported; otherwise the task fails.  
  - **Paths**: `code/src/correlation_analysis.py`, `code/src/visualization.py`, `code/tests/test_correlation.py`, `outputs/correlation_results.json`, `outputs/heatmap.png`.

---

## Phase 2: Complete the study and validate its evidence

**Goal**: Run the full suite of analyses (OLS, phylogenetic models, Random Forest, sensitivity & power analyses), apply multiple‑comparison correction, and validate all outputs against contracts.

- [ ] T004 [US‑3] **Baseline OLS regression with family covariate and multicollinearity diagnostics**  
  - Implement `code/src/ols_regression.py` with `fit_ols_cv(df: pd.DataFrame, n_splits: int = 5) -> dict` that:  
    * Performs 5‑fold CV stratified by `family`.  
    * Fits an OLS model (`statsmodels.api.OLS`) with `herbivory_score` as outcome, four metabolites as predictors, and one‑hot encoded `family` as fixed effects.  
    * Computes VIF for each metabolite; fails if any VIF ≥ 5 (SC‑004).  
    * Aggregates mean CV R², adjusted R², and RMSE; enforces mean CV R² > 0.3 (SC‑002).  
    * Applies Benjamini‑Hochberg correction to coefficient p‑values.  
    * Returns an `AnalysisResult` (`result_type="ols"`).  
  - Write `code/tests/test_ols.py` checking CV execution, VIF < 5, mean CV R² > 0.3, and schema compliance.  
  - Verification: run on `data/processed/clean.parquet`; save JSON to `outputs/ols_results.json`; log any VIF warnings to `outputs/ols_warnings.txt`.  
  - **Paths**: `code/src/ols_regression.py`, `code/tests/test_ols.py`, `outputs/ols_results.json`, `outputs/ols_warnings.txt`.

- [ ] T005 **Phylogenetic adjustment via PGLS and mixed‑effects models**  
  - Implement `code/src/phylogenetic_analysis.py` with:  
    * `fetch_phylogeny(species: List[str]) -> dendropy.Tree` – retrieves a plant phylogeny from the Open Tree of Life API.  
    * `match_species_to_otl(species: List[str]) -> Tuple[List[str], List[str]]` – performs deterministic fuzzy‑matching by (1) sorting candidate taxa alphabetically, (2) computing similarity scores with `fuzzywuzzy`, (3) fixing `np.random.seed(42)` before any random tie‑breaking, and (4) returning matched/unmatched lists.  
    * `fit_pgls_cv(df: pd.DataFrame, tree: dendropy.Tree, n_splits: int = 5) -> dict` – builds a phylogenetic covariance matrix, runs 5‑fold CV GLS with that covariance and family covariate, computes a likelihood‑ratio test (LRT) vs. OLS for each fold, applies FDR correction, and returns an `AnalysisResult` (`result_type="pgls"`).  
    * `fit_mixed_effects_cv(df: pd.DataFrame, n_splits: int = 5) -> dict` – fits a linear mixed‑effects model (`statsmodels.MixedLM`) with species‑level random intercepts, runs 5‑fold CV, and returns an `AnalysisResult` (`result_type="mixed_effects"`).  
  - Write `code/tests/test_phylogenetic.py` verifying successful phylogeny fetch, reasonable match rate, CV execution, LRT p‑value ∈ [0,1], and schema compliance.  
  - Verification: run on `data/processed/clean.parquet`; save PGLS JSON to `outputs/pgls_results.json`, mixed‑effects JSON to `outputs/mixed_effects_results.json`, and matching log to `outputs/phylogeny_matching_log.txt`.  
  - **Paths**: `code/src/phylogenetic_analysis.py`, `code/tests/test_phylogenetic.py`, `outputs/pgls_results.json`, `outputs/mixed_effects_results.json`, `outputs/phylogeny_matching_log.txt`.

- [ ] T006 **Random Forest regressor with permutation feature importance and FDR correction**  
  - Implement `code/src/random_forest_model.py` with `fit_rf_cv(df: pd.DataFrame, n_splits: int = 5) -> dict` that:  
    * Uses the same 5‑fold CV stratified by `family`.  
    * Fits `RandomForestRegressor(max_depth=5, n_estimators=200, random_state=42, n_jobs=2)` in each fold.  
    * Computes permutation importance on held‑out folds (`sklearn.inspection.permutation_importance`, n_repeats=100, random_state=42).  
    * Derives p‑values from the permutation distribution and applies Benjamini‑Hochberg correction.  
    * Aggregates mean CV R², adjusted R², RMSE; enforces mean CV R² > 0.3.  
    * Returns an `AnalysisResult` (`result_type="rf"`).  
  - Write `code/tests/test_rf.py` ensuring non‑negative importance scores, p/q‑values ∈ [0,1], mean CV R² > 0.3, and schema compliance.  
  - Log a warning to `outputs/rf_warnings.txt` if the final test‑set R² < 0.3.  
  - Verification: run on `data/processed/clean.parquet`; save JSON to `outputs/rf_results.json`.  
  - **Paths**: `code/src/random_forest_model.py`, `code/tests/test_rf.py`, `outputs/rf_results.json`, `outputs/rf_warnings.txt`.

- [ ] T007 **Sensitivity analysis: p‑value thresholds, outlier caps, and robustness checks**  
  - Implement `code/src/sensitivity_analysis.py` with `run_sensitivity_analysis(df: pd.DataFrame) -> dict` that:  
    1. Sweeps FDR q‑thresholds from 0.01 to 0.10 (step 0.01) re‑running the correlation analysis and recording the number of significant negative classes at each threshold.  
    2. Varies herbivory outlier caps by ±10 % of the baseline IQR whisker, re‑runs OLS CV and RF CV, and records mean CV R² for each cap level.  
    3. Sets `np.random.seed(42)` and adds Gaussian noise (±5 % of each metabolite’s std) to the standardized data, re‑runs OLS CV and RF CV, and compares the top‑3 biomarker rankings to the original run, reporting agreement.  
    - Returns an `AnalysisResult` (`result_type="sensitivity"`).  
  - Write `code/tests/test_sensitivity.py` confirming presence of entries for all thresholds, three outlier‑cap results, and a ranking‑agreement metric.  
  - Verification: run on `data/processed/clean.parquet`; save JSON to `outputs/sensitivity_results.json`.  
  - **Paths**: `code/src/sensitivity_analysis.py`, `code/tests/test_sensitivity.py`, `outputs/sensitivity_results.json`.

- [ ] T008 **Power analysis and study adequacy assessment**  
  - Implement `code/src/power_analysis.py` with `compute_power_analysis(df: pd.DataFrame, pgls_res: dict) -> dict` that:  
    * Calculates effective sample size after phylogenetic adjustment using the estimated λ (or a default).  
    * Estimates power to detect an effect size r ≈ 0.3 (R² ≈ 0.09) at α = 0.05, adjusting for four tests via BH (α_adj ≈ 0.0125) using `statsmodels.stats.power.TTestIndPower`.  
    * Flags the study as exploratory (`under_power_flag=True`) if observed paired species < 50 or effective_n < 30; otherwise marks it adequate.  
    * Returns an `AnalysisResult` (`result_type="power_analysis"`).  
  - Write `code/tests/test_power.py` checking that `effective_n ≤ observed_n`, power estimates ∈ [0,1], and flag logic works.  
  - Verification: run on `data/processed/clean.parquet` and the PGLS result; save JSON to `outputs/power_analysis_results.json`. Task fails if the study is under‑powered and the required disclaimer is missing from the later report.  
  - **Paths**: `code/src/power_analysis.py`, `code/tests/test_power.py`, `outputs/power_analysis_results.json`.

---

## Phase 3: Reproducible results and paper hand‑off

**Goal**: Validate all artifacts, assemble a complete methods‑and‑results report, demonstrate end‑to‑end reproducibility, and provide a clean hand‑off package for the paper stage.

- [ ] T009 **Contract validation and artifact verification**  
  - Implement `code/src/validation.py` with:  
    * `validate_processed_data(df_path: str, schema_path: str) -> bool` – validates `clean.parquet` against `contracts/processed_data.schema.yaml`.  
    * `validate_analysis_result(json_path: str, schema_path: str) -> bool` – validates each AnalysisResult JSON against `contracts/model_output.schema.yaml`.  
    * `compute_checksums(paths: List[str]) -> dict` – SHA‑256 checksums for all data and result files.  
    * Additional acceptance checks:  
      - Species count ≥ 50 (FR‑001, SC‑001).  
      - Mean CV R² > 0.3 for OLS and RF (SC‑002).  
      - All VIF < 5 (SC‑004).  
      - Exactly 3‑5 significant negative classes from T003 (FR‑003).  
      - **Wall‑clock runtime ≤ 6 h**: reads `outputs/pipeline_log.txt` timestamps and raises if exceeded (addresses SC‑005).  
    * Any violation raises an exception causing task failure.  
  - Write `code/tests/test_validation.py` verifying schema files exist, all artifacts pass validation, checksums are reproducible, and acceptance criteria are enforced.  
  - Verification: run on all artifacts produced in T001–T008; store checksums in `outputs/artifact_checksums.json`.  
  - **Paths**: `code/src/validation.py`, `code/tests/test_validation.py`, `outputs/artifact_checksums.json`.

- [ ] T010 **Comprehensive methods‑and‑results report**  
  - Assemble `outputs/report.md` containing:  
    1. Research question, data sources (explicit URLs for MetaboLights, PMN, HPID, and the fallback GHZ placeholder if used), and sample size.  
    2. Detailed preprocessing description (z‑score standardisation, handling of documented absences, outlier capping).  
    3. Correlation results: list of 3‑5 metabolite classes with significant negative correlation (q < 0.05), heat‑map figure, and interpretation.  
    4. Baseline OLS outcomes: coefficients, FDR‑corrected p‑values, mean CV R² > 0.3, adjusted R², RMSE, VIF diagnostics, family covariate effect.  
    5. Phylogenetic analyses: PGLS coefficients, LRT vs. OLS, mixed‑effects random intercept, marginal/conditional R², phylogeny source, and matched/unmatched species counts.  
    6. Random Forest results: permutation‑importance rankings with p/q‑values, CV and test metrics (CV R² > 0.3), and any warning if test R² < 0.3.  
    7. Sensitivity analysis outcomes (threshold sweep, outlier‑cap robustness, standardisation‑noise robustness).  
    8. Power analysis summary: observed N, effective N, power estimates, and under‑power flag.  
    9. Explicit disclaimer if the fallback placeholder dataset was used.  
    10. Limitations (observational design, phylogenetic non‑independence, power constraints).  
    11. Links to all JSON result files and PNG figures.  
  - Verification script parses `outputs/report.md` to ensure every Markdown link points to an existing file and that required disclaimer sections appear when criteria are unmet.  
  - **Paths**: `outputs/report.md`.

- [ ] T011 **End‑to‑end reproducibility run and documentation**  
  - Create `scripts/run_pipeline.sh` that:  
    1. Activates the virtual environment (or runs `python3.11`).  
    2. Executes the full pipeline in order:  
       ```bash
       python -m code.src.fetch_data && \
       python -m code.src.preprocess && \
       python -m code.src.correlation_analysis && \
       python -m code.src.ols_regression && \
       python -m code.src.phylogenetic_analysis && \
       python -m code.src.random_forest_model && \
       python -m code.src.sensitivity_analysis && \
       python -m code.src.power_analysis && \
       python -m code.src.validation
       ```  
    3. Records start/end timestamps and total wall‑clock time in `outputs/pipeline_log.txt`.  
    4. Exits with status 0 on success, non‑zero on any failure.  
  - Add a `README.md` at the project root documenting: quick start (`bash scripts/run_pipeline.sh`), input URLs, output artifact list, dependency note (`requirements.txt`, Python 3.11), reproducibility guarantees (fixed seeds), and expected runtime (≈ 2–3 h on the CI runner).  
  - Write `code/tests/test_pipeline.py` (integration test) that runs the pipeline on a minimal subset (or full if within limits), checks that all expected output files exist, and asserts total runtime ≤ 6 h.  
  - Verification: execute `bash scripts/run_pipeline.sh` on a clean checkout; confirm all outputs exist, `outputs/pipeline_log.txt` shows ≤ 6 h, and all tests in `code/tests/` pass.  
  - **Paths**: `scripts/run_pipeline.sh`, `README.md`, `code/tests/test_pipeline.py`, `outputs/pipeline_log.txt`.

- [ ] T012 **Paper‑stage hand‑off documentation**  
  - Create `outputs/handoff.md` that:  
    * Summarises scientific findings (significant metabolite classes, biomarker rankings, model performance, power assessment).  
    * Lists all data and result artifacts required for manuscript preparation (`data/processed/clean.parquet`, `outputs/heatmap.png`, `outputs/ols_results.json`, `outputs/pgls_results.json`, `outputs/mixed_effects_results.json`, `outputs/rf_results.json`, `outputs/report.md`).  
    * References the schema contracts (`processed_data.schema.yaml`, `model_output.schema.yaml`).  
    * Highlights any fallback placeholder usage and its implications.  
    * Mandates verification that acceptance criteria (≥ 50 species, R² > 0.3, VIF < 5, 3‑5 significant classes) are satisfied before inclusion in the manuscript.  
    * Provides the checksum manifest (`outputs/artifact_checksums.json`) for integrity verification.  
    * States that the paper stage will handle figure layout, PDF compilation, and submission workflows.  
  - Verification: ensure all listed paths exist and match the checksum file; confirm the document clearly communicates the required criteria.  
  - **Paths**: `outputs/handoff.md`.