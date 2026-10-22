# Tasks: Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance

**Inputs**: Feature specification (`spec.md`), implementation plan (`plan.md`), research question validation, data model (`data-model.md`), and output contracts (`model_output.schema.yaml`, `processed_data.schema.yaml`).

This is a research implementation plan for a cross-species metabolomics–herbivory analysis. The study acquires paired data from public repositories, preprocesses and normalizes it, explores correlations, fits baseline OLS with family covariate, phylogenetic‑adjusted models (PGLS, mixed‑effects), trains a Random Forest regressor, applies rigorous multiple‑comparison correction, performs power analysis and sensitivity checks, and generates reproducible reports and visualizations. All steps are designed to run on the GitHub Actions free‑tier CPU runner (2 cores, ~7 GB RAM, ~14 GB disk, ≤6 h).

---

## Phase 1: Setup and first end‑to‑end analysis

**Goal**: Establish project structure, configure dependencies with pinned random seeds, acquire and validate a real dataset from public repositories, and run a minimal executable analysis to confirm data flow and output contracts early.

- [X] T001 [P1] [US-1] **Project initialization and data acquisition framework** <!-- ATOMIZE: requested -->
  - Create `code/` directory structure with `src/`, `tests/`, and `scripts/` subdirectories.  
  - Create `data/raw/`, `data/processed/`, `outputs/`, `contracts/` directories.  
  - Pin Python 3.11 with `requirements.txt` including `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `dendropy`, `requests`, `tqdm`, `scipy`, `fuzzywuzzy`, `python-Levenshtein`, `pytest`.  
  - Implement `code/src/config.py` with global random seeds (`np.random.seed(42)`, `random.seed(42)`, `random_state=42` for sklearn).  
  - Implement `code/src/fetch_data.py` with three fetch functions: `fetch_metabolights()`, `fetch_pmn()`, `fetch_hpid()`, each returning a pandas DataFrame with required columns (`species_id`, `species_name`, `family`, `alkaloids`, `terpenes`, `phenolics`, `benzoxazinoids`, `herbivory_score`).  
  - Each fetch function must implement 3‑attempt exponential back‑off (30‑second base) on connection failure; raise an exception (do NOT fall back to synthetic data) if all three attempts fail.  
  - Document the exact URLs and API endpoints being queried in `code/src/fetch_data.py` as comments.  
  - Write `code/tests/test_fetch_data.py` with unit tests verifying that (a) each fetch function returns a DataFrame with the required columns, (b) no missing values exist in required columns, (c) species count is ≥ 1 for a successful fetch.  
  - **Verification**:  
    - Run `pytest code/tests/test_fetch_data.py -v` and confirm all tests pass.  
    - Assert that the required directory structure, `code/src/config.py`, `requirements.txt`, and `outputs/fetch_log.txt` exist.  
    - Assert that `outputs/fetch_log.txt` is non‑empty and contains a sample of fetched species IDs.  
    - **Enforcement**: Fail if total paired species after fetching is **< 50** (FR‑001).  
  - **Paths**: `code/src/config.py`, `code/src/fetch_data.py`, `code/tests/test_fetch_data.py`, `requirements.txt`, `outputs/fetch_log.txt`.

- [ ] T002 [P1] [US-1] **Data ingestion and preprocessing pipeline**
  - Implement `code/src/preprocess.py` with function `load_and_preprocess(raw_dataframes: List[pd.DataFrame]) -> pd.DataFrame` that:  
    - Concatenates input DataFrames and harmonizes column names (e.g., `'Alkaloid_conc' → 'alkaloids'`).  
    - Filters rows with any missing required predictor or outcome columns (`species_id`, `family`, `alkaloids`, `terpenes`, `phenolics`, `benzoxazinoids`, `herbivory_score`).  
    - For metabolite‑class columns documented as biologically absent in the source metadata, imputes zeros and records the absence in an `absence_indicator` JSON column (e.g., `{"alkaloids": "documented_absent"}`); for truly missing data, excludes the row.  
    - Detects extreme herbivory outliers via IQR method (1.5 × IQR); caps values at the upper whisker or flags them in a log.  
    - Z‑score standardizes all four metabolite columns using `sklearn.preprocessing.StandardScaler` (fit on training data only in later phases).  
    - Validates output against `processed_data.schema.yaml` using `jsonschema`.  
    - Writes cleaned DataFrame to `data/processed/clean.parquet` and computes SHA‑256 checksum, recording it in `outputs/preprocessing_log.json`.  
  - Write `code/tests/test_preprocess.py` verifying that (a) output has no missing values in required columns, (b) metabolite columns are z‑scored (mean ≈ 0, std ≈ 1), (c) `absence_indicator` is correctly populated, (d) output validates against the schema, (e) `outputs/preprocessing_log.json` exists and contains a valid checksum entry.  
  - **Verification**: Run `pytest code/tests/test_preprocess.py -v` and confirm all tests pass. Inspect `data/processed/clean.parquet` and verify row count, column names, and data types match the contract.  
  - **Paths**: `code/src/preprocess.py`, `code/tests/test_preprocess.py`, `data/processed/clean.parquet`, `outputs/preprocessing_log.json`.

- [ ] T003 [P2] [US-2] **Exploratory correlation analysis and early visualization** <!-- FAILED-IN-EXECUTION: code/src/correlation_analysis.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/correlation_analysis.py exit=1 -->
  - Implement `code/src/correlation_analysis.py` with function `compute_correlations(df: pd.DataFrame) -> dict` that:  
    - Computes Pearson correlation coefficients between each of the four metabolite classes (averaged across species) and `herbivory_score`.  
    - Computes two‑tailed p‑values for each correlation using `scipy.stats.pearsonr`.  
    - Applies Benjamini‑Hochberg FDR correction to the four class‑level p‑values (q‑value threshold 0.05).  
    - Identifies metabolite classes with **significant negative correlation** (q < 0.05, coefficient < 0) **and enforces that the total number of such classes is exactly 3‑5** (FR‑003).  
    - Returns a dict conforming to `AnalysisResult` with `result_type="correlation"` and payload containing `matrix`, `p_values`, `q_values`, `significant_negative_classes`, and `method="Pearson"`.  
  - Implement `code/src/visualization.py` with function `plot_correlation_heatmap(corr_dict: dict, output_path: str)` that generates a seaborn heatmap PNG with (a) correlation values in cells, (b) asterisks or color intensity indicating significance (q < 0.05), (c) axis labels for metabolite classes and `herbivory_score`.  
  - Write `code/tests/test_correlation.py` verifying that (a) correlation coefficients are in [‑1, 1], (b) p‑values and q‑values are in [0, 1], (c) `significant_negative_classes` length is between 3 and 5 inclusive, (d) failure is raised if outside this range.  
  - **Verification**: Run the correlation analysis on `data/processed/clean.parquet`, generate the heatmap PNG, and save the AnalysisResult JSON to `outputs/correlation_results.json`. Confirm that exactly 3‑5 classes are reported; otherwise fail. Visually inspect the heatmap for readability and correct significance annotation.  
  - **Paths**: `code/src/correlation_analysis.py`, `code/src/visualization.py`, `code/tests/test_correlation.py`, `outputs/correlation_results.json`, `outputs/heatmap.png`.

---

## Phase 2: Complete the study and validate its evidence

**Goal**: Run the complete specified analyses (baseline OLS with family covariate, phylogenetic‑adjusted PGLS, mixed‑effects, Random Forest regressor, sensitivity & power analyses), apply rigorous multiple‑comparison correction, and validate all outputs against contracts.

- [ ] T004 [P2] [US-3] **Baseline OLS regression with family covariate and multicollinearity diagnostics**
  - Implement `code/src/ols_regression.py` with function `fit_ols_cv(df: pd.DataFrame, n_splits: int = 5) -> dict` that:  
    - Performs **5‑fold cross‑validation** (Stratified by `family`) using `sklearn.model_selection.StratifiedKFold`.  
    - In each fold, fits an OLS model (`statsmodels.api.OLS`) with `herbivory_score` as the dependent variable, four metabolite predictors, and one‑hot encoded `family` as a fixed‑effect covariate.  
    - Computes VIF for each metabolite predictor; **fails** if any VIF ≥ 5 (SC‑004).  
    - Aggregates CV metrics (mean R², adjusted R², RMSE) across folds.  
    - Applies Benjamini‑Hochberg FDR correction to metabolite coefficient p‑values.  
    - **Enforces** that the mean CV R² > 0.3 (SC‑002); otherwise the task fails.  
    - Returns an `AnalysisResult` dict with `result_type="ols"` containing coefficients, p‑values, q‑values, CV R²/adj_R²/RMSE, VIF, family effect, and FDR method.  
  - Write `code/tests/test_ols.py` verifying that (a) 5‑fold CV is performed, (b) VIF values are < 5, (c) mean CV R² > 0.3, (d) output validates against `model_output.schema.yaml`.  
  - **Verification**: Run OLS on `data/processed/clean.parquet`, save the AnalysisResult JSON to `outputs/ols_results.json`. If any VIF ≥ 5 or mean CV R² ≤ 0.3, the task fails. Log any VIF warnings to `outputs/ols_warnings.txt`.  
  - **Paths**: `code/src/ols_regression.py`, `code/tests/test_ols.py`, `outputs/ols_results.json`, `outputs/ols_warnings.txt`.

- [ ] T005 [P2] **Phylogenetic adjustment via PGLS and mixed‑effects models**
  - Implement `code/src/phylogenetic_analysis.py` with functions:  
    - `fetch_phylogeny(species_names: List[str]) -> dendropy.Tree` that retrieves plant phylogeny from Open Tree of Life (OTL) via the OTL API.  
    - `match_species_to_otl(species_names: List[str]) -> Tuple[List[str], List[str]]` that uses fuzzy matching (`fuzzywuzzy`, threshold 0.8) to match species names to OTL taxa; returns matched and unmatched lists.  
    - `fit_pgls_cv(df: pd.DataFrame, phylogeny: dendropy.Tree, n_splits: int = 5) -> dict` that:  
      - Constructs a phylogenetic variance‑covariance matrix.  
      - Performs **5‑fold CV** (stratified by `family`) fitting a GLS model with the phylogenetic covariance and family covariate.  
      - Computes a likelihood‑ratio test (LRT) comparing each CV fold’s PGLS fit to the corresponding OLS fold; records mean LRT statistic and p‑value.  
      - Applies FDR correction to coefficient p‑values.  
      - Returns an `AnalysisResult` with `result_type="pgls"` including CV metrics, phylogeny source, matched/unmatched counts, and LRT summary.  
    - `fit_mixed_effects_cv(df: pd.DataFrame, n_splits: int = 5) -> dict` that fits a linear mixed‑effects model (`statsmodels.MixedLM`) with `family` as fixed, metabolites as fixed, and a species‑level random intercept, using **5‑fold CV**. Returns an `AnalysisResult` with `result_type="mixed_effects"` and CV performance metrics.  
  - Write `code/tests/test_phylogenetic.py` verifying that (a) phylogeny retrieval succeeds, (b) fuzzy matching yields reasonable match rate, (c) both models run with CV and produce valid JSON, (d) LRT p‑value in [0,1], (e) outputs validate against the schema.  
  - **Verification**: Run phylogenetic analysis on `data/processed/clean.parquet`, save PGLS results to `outputs/pgls_results.json` and mixed‑effects results to `outputs/mixed_effects_results.json`. Ensure `outputs/phylogeny_matching_log.txt` is generated and contains matched/unmatched counts.  
  - **Paths**: `code/src/phylogenetic_analysis.py`, `code/tests/test_phylogenetic.py`, `outputs/pgls_results.json`, `outputs/mixed_effects_results.json`, `outputs/phylogeny_matching_log.txt`, `outputs/model_comparison.txt`.

- [ ] T006 [P2] **Random Forest regressor with permutation feature importance and FDR correction**
  - Implement `code/src/random_forest_model.py` with function `fit_rf_cv(df: pd.DataFrame, n_splits: int = 5) -> dict` that:  
    - Uses the same **5‑fold CV** (stratified by `family`) as OLS.  
    - Fits a `RandomForestRegressor(max_depth=5, n_estimators=200, random_state=42, n_jobs=2)` within each CV fold.  
    - Computes permutation feature importance on the held‑out fold using `sklearn.inspection.permutation_importance(..., n_repeats=100, random_state=42)`.  
    - Derives p‑values from the permutation distribution and applies Benjamini‑Hochberg FDR correction (q < 0.05).  
    - Aggregates CV R², adjusted R², RMSE across folds and also reports test‑set metrics from a final 80/20 hold‑out (consistent with earlier splits).  
    - **Enforces** that the mean CV R² > 0.3; otherwise the task fails.  
    - Returns an `AnalysisResult` with `result_type="rf"` containing ranked `feature_importance` (metabolite, importance, p_value, q_value), CV metrics, test metrics, and FDR method.  
  - Write `code/tests/test_rf.py` verifying that (a) feature importance scores are non‑negative, (b) p‑values/q‑values in [0,1], (c) CV R² > 0.3, (d) output validates against the schema.  
  - Log a warning to `outputs/rf_warnings.txt` **only if** the test‑set R² < 0.3 (instead of 0.1).  
  - **Verification**: Run Random Forest on `data/processed/clean.parquet`, save the AnalysisResult JSON to `outputs/rf_results.json`. Ensure `outputs/rf_warnings.txt` exists when the condition triggers.  
  - **Paths**: `code/src/random_forest_model.py`, `code/tests/test_rf.py`, `outputs/rf_results.json`, `outputs/rf_warnings.txt`.

- [ ] T007 [P2] **Sensitivity analysis: p‑value thresholds, outlier caps, and robustness checks**
  - Implement `code/src/sensitivity_analysis.py` with function `run_sensitivity_analysis(df: pd.DataFrame) -> dict` that:  
    - **P‑value threshold sweep**: Re‑run correlation analysis (from T003) with thresholds from 0.01 to 0.10 (step 0.01); record the number of significant metabolite classes at each threshold.  
    - **Outlier cap variation**: Re‑run OLS CV and Random Forest CV (from T004 & T006) with herbivory outlier caps at ±10 % of the baseline IQR whisker; record mean CV R² for each cap level (`minus_10%`, `baseline`, `plus_10%`).  
    - **Standardization robustness**: Instead of raw‑data re‑runs, perform a robustness check by adding Gaussian noise (±5 % of each metabolite’s std) to the standardized data and re‑running OLS CV and RF CV; compare top‑3 biomarker rankings to the original run and report agreement level.  
    - Returns an `AnalysisResult` dict with `result_type="sensitivity"` containing `p_threshold_sweep`, `outlier_cap_variation`, and `standardization_robustness` comparison.  
  - Write `code/tests/test_sensitivity.py` verifying that (a) the sweep yields entries for all thresholds, (b) outlier cap results have three entries, (c) robustness comparison documents ranking agreement.  
  - **Verification**: Run sensitivity analysis on `data/processed/clean.parquet`, save the AnalysisResult JSON to `outputs/sensitivity_results.json`. Ensure the results demonstrate robustness or clearly flag substantial sensitivity.  
  - **Paths**: `code/src/sensitivity_analysis.py`, `code/tests/test_sensitivity.py`, `outputs/sensitivity_results.json`.

- [ ] T008 [P2] **Power analysis and study adequacy assessment**
  - Implement `code/src/power_analysis.py` with function `compute_power_analysis(df: pd.DataFrame, pgls_result: dict) -> dict` that:  
    - Computes effective sample size after phylogenetic adjustment using the phylogenetic λ parameter (if available) or a default estimate; formula: `effective_n = n_observed / (1 + (lambda - 1) * phylogenetic_signal)`.  
    - Estimates statistical power to detect small‑to‑medium effect sizes (r ≈ 0.3, corresponding to R² ≈ 0.09) at α = 0.05 with Benjamini‑Hochberg FDR correction (adjusted α ≈ 0.0125 for four tests) using `statsmodels.stats.power.TTestIndPower`.  
    - **Flags** the study as exploratory (`under_power_flag=True`) if the **observed** paired species count is **< 50** (SC‑001) **or** effective_n < 30; otherwise marks as adequate.  
    - Returns an `AnalysisResult` dict with `result_type="power_analysis"` containing observed N, effective N, power estimates for OLS/PGLS/RF, under‑power flag, and interpretation.  
  - Write `code/tests/test_power.py` verifying that (a) `effective_n ≤ observed_n`, (b) power estimates in [0,1], (c) `under_power_flag` set correctly based on N thresholds.  
  - **Verification**: Run power analysis on `data/processed/clean.parquet` and the PGLS results, save the AnalysisResult JSON to `outputs/power_analysis_results.json`. The task must fail if the study is under‑powered and the report does not contain the required disclaimer.  
  - **Paths**: `code/src/power_analysis.py`, `code/tests/test_power.py`, `outputs/power_analysis_results.json`.

---

## Phase 3: Reproducible results and paper handoff

**Goal**: Validate all artifacts against contracts, assemble a concise methods‑and‑results report, re‑run the complete workflow from declared inputs to confirm reproducibility, and prepare for paper‑stage handoff.

- [ ] T009 [P3] **Contract validation and artifact verification**
  - Implement `code/src/validation.py` with functions:  
    - `validate_processed_data(df: pd.DataFrame, schema_path: str) -> bool` that validates `data/processed/clean.parquet` against `contracts/processed_data.schema.yaml` using `jsonschema.validate()`.  
    - `validate_analysis_results(result_dict: dict, schema_path: str) -> bool` that validates each AnalysisResult JSON (correlation, OLS, PGLS, mixed‑effects, RF, sensitivity, power_analysis) against `contracts/model_output.schema.yaml`.  
    - `compute_checksums(artifact_paths: List[str]) -> dict` that computes SHA‑256 checksums for all data and result artifacts and returns a dict mapping path → checksum.  
    - **Additional verification**:  
      - Ensure species count ≥ 50 (FR‑001 & SC‑001).  
      - Ensure OLS and RF mean CV R² > 0.3 (SC‑002).  
      - Ensure VIF < 5 for all metabolites (SC‑004).  
      - Ensure T003 reported exactly 3‑5 significant negative classes (FR‑003).  
    - Any violation causes task failure.  
  - Write `code/tests/test_validation.py` verifying that (a) schema files exist and are valid JSON Schema, (b) all artifacts pass schema validation, (c) checksums are reproducible, (d) acceptance‑criteria checks work as intended.  
  - **Verification**: Run validation on all artifacts generated in T001–T008; save checksum report to `outputs/artifact_checksums.json`. Confirm that all artifacts pass schema validation **and** all acceptance criteria are met; otherwise the task fails.  
  - **Paths**: `code/src/validation.py`, `code/tests/test_validation.py`, `outputs/artifact_checksums.json`.

- [ ] T010 [P3] **Comprehensive methods‑and‑results report**
  - Assemble a Markdown report in `outputs/report.md` that:  
    - Documents the research question, data sources (explicit URLs), and sample size (N species, number of metabolites, number of herbivory measurements).  
    - Describes preprocessing steps: z‑score standardization, handling of missing data and documented biological absence, outlier detection and capping.  
    - Summarizes exploratory correlation analysis: metabolite classes with significant negative correlation (exact count 3‑5, q < 0.05), heatmap visualization, and interpretation.  
    - Reports baseline OLS results: coefficients, FDR‑corrected p‑values, mean CV R² > 0.3, adjusted R², RMSE, VIF diagnostics, and family‑covariate effect.  
    - Reports phylogenetic‑adjusted results: PGLS coefficients, LRT comparison to OLS, mixed‑effects random intercept and marginal/conditional R², and interpretation of phylogenetic signal.  
    - Reports Random Forest results: ranked feature importance (with FDR‑corrected p‑values), CV and test metrics (CV R² > 0.3), and comparison to OLS.  
    - Documents sensitivity analysis outcomes (threshold sweep, outlier cap robustness, standardization robustness).  
    - Reports power analysis: effective sample size, power estimates, and study adequacy flag.  
    - **Explicitly states** any unmet acceptance criteria (e.g., if N < 50, R² ≤ 0.3, VIF ≥ 5, or correlation class count outside 3‑5).  
    - Includes links to all JSON result files and PNG figures (e.g., `[Correlation heatmap](heatmap.png)`, `[OLS results](ols_results.json)`).  
    - **If a placeholder dataset was used** (due to repository unavailability), includes a prominent disclaimer: “Results are based on synthetic/placeholder data and do not address the biological research question.”  
    - Discusses limitations (phylogenetic non‑independence, observational nature, power constraints).  
    - Concludes with recommendations for future work.  
  - **Verification**:  
    - Run a script that parses `outputs/report.md` and checks that every Markdown link points to an existing file in the repository.  
    - Fail if any link is broken or if required disclaimer sections are missing when criteria are unmet.  
  - **Paths**: `outputs/report.md`.

- [ ] T011 [P3] **End‑to‑end reproducibility run and documentation**
  - Create a shell script `scripts/run_pipeline.sh` that:  
    - Activates the Python virtual environment (or specifies `python3.11`).  
    - Runs all data acquisition, preprocessing, analysis, and validation steps in order:  
      `python code/src/fetch_data.py && python code/src/preprocess.py && python code/src/correlation_analysis.py && python code/src/ols_regression.py && python code/src/phylogenetic_analysis.py && python code/src/random_forest_model.py && python code/src/sensitivity_analysis.py && python code/src/power_analysis.py && python code/src/validation.py`.  
    - Records start and end timestamps and total wall‑clock elapsed time in `outputs/pipeline_log.txt`.  
    - Exits with status 0 on success, non‑zero on any failure.  
  - Create a `README.md` in the project root documenting:  
    - **Quick start**: “Run `bash scripts/run_pipeline.sh` to execute the complete analysis from scratch.”  
    - **Input data sources**: Lists the three repository URLs (MetaboLights, PMN, HPID) and the fallback placeholder dataset (if applicable).  
    - **Output artifacts**: Lists all generated files (`clean.parquet`, JSON results, PNG figures, `report.md`) and their locations.  
    - **Dependencies**: References `requirements.txt` and specifies Python 3.11.  
    - **Reproducibility**: Notes that all random seeds are fixed (`random_state=42`) and all computations are deterministic.  
    - **Runtime**: States the expected total wall‑clock time (e.g., “Approximately 2–3 hours on a 2‑core CPU runner”).  
  - Write `code/tests/test_pipeline.py` (integration test) that:  
    - Executes the pipeline on a minimal subset (or full if within CI limits).  
    - Verifies that all expected output files are created.  
    - Confirms that the pipeline completes within the 6‑hour time limit (measured in CI).  
  - **Verification**: Execute `bash scripts/run_pipeline.sh` on a fresh checkout; confirm that all outputs are generated, all tests pass, and the total runtime is logged in `outputs/pipeline_log.txt` and does not exceed 6 hours. Verify that the README instructions are accurate and the project is reproducible.  
  - **Paths**: `scripts/run_pipeline.sh`, `README.md`, `code/tests/test_pipeline.py`, `outputs/pipeline_log.txt`.

- [ ] T012 [P3] **Paper‑stage handoff documentation**
  - Create `outputs/handoff.md` that:  
    - Lists all scientific findings (significant metabolite classes, biomarker rankings, model performance metrics, power limitations).  
    - Specifies the exact data artifacts available for the paper stage: `data/processed/clean.parquet` (processed dataset), `outputs/heatmap.png` (correlation visualization), `outputs/ols_results.json`, `outputs/pgls_results.json`, `outputs/mixed_effects_results.json`, `outputs/rf_results.json` (model outputs), `outputs/report.md` (summary).  
    - Documents the schema contracts (`processed_data.schema.yaml`, `model_output.schema.yaml`) that define the structure of all results.  
    - Notes any data source fallbacks or placeholder usage (if applicable) and their implications for interpretation.  
    - **Mandates** that the paper‑stage team verify that all acceptance criteria (≥ 50 species, R² > 0.3, VIF < 5, 3‑5 significant classes) are satisfied before inclusion in the manuscript.  
    - Provides checksums (`outputs/artifact_checksums.json`) for verification of result integrity.  
    - States that the research stage is complete; the paper stage will handle figure layout, PDF compilation, and submission workflows (not replicated here).  
  - **Verification**: Confirm that the handoff document accurately reflects all completed work, all artifact paths are correct, and the paper‑stage team has clear guidance on required criteria.  
  - **Paths**: `outputs/handoff.md`.
