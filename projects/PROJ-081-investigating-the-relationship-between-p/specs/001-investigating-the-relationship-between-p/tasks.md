# Tasks: Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance

**Inputs**: Feature specification (`spec.md`), implementation plan (`plan.md`), research question validation, data model (`data-model.md`), and output contracts (`model_output.schema.yaml`, `processed_data.schema.yaml`).

This is a research implementation plan for a cross-species metabolomics–herbivory analysis. The study acquires paired data from public repositories, preprocesses and normalizes it, explores correlations, fits baseline OLS with family covariate and phylogenetic-adjusted models (PGLS, mixed-effects), trains a Random Forest regressor, applies rigorous multiple-comparison correction and permutation testing, conducts power analysis and sensitivity checks, and generates reproducible reports and visualizations. All steps are designed to run on the GitHub Actions free-tier CPU runner (2 cores, ~7 GB RAM, ~14 GB disk, ≤6 h).

---

## Phase 1: Setup and first end-to-end analysis

**Goal**: Establish project structure, configure dependencies with pinned random seeds, acquire and validate a small real dataset from public repositories, and run a minimal executable analysis to confirm data flow and output contracts early.

- [ ] T001 [P1] [US-1] **Project initialization and data acquisition framework**
  - Create `code/` directory structure with `src/`, `tests/`, and `scripts/` subdirectories.
  - Create `data/raw/`, `data/processed/`, `outputs/`, `contracts/` directories.
  - Pin Python 3.11 with `requirements.txt` including `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `dendropy`, `requests`, `tqdm`, `scipy`, `fuzzywuzzy`, `python-Levenshtein`, `pytest`.
  - Create `code/src/config.py` with global random seeds (`np.random.seed(42)`, `random.seed(42)`, `random_state=42` for sklearn).
  - Implement `code/src/fetch_data.py` with three fetch functions: `fetch_metabolights()`, `fetch_pmn()`, `fetch_hpid()`, each returning a pandas DataFrame with required columns (`species_id`, `species_name`, `family`, `alkaloids`, `terpenes`, `phenolics`, `benzoxazinoids`, `herbivory_score`).
  - Each fetch function must implement 3-attempt exponential backoff (30-second base) on connection failure; raise an exception (do NOT fall back to synthetic data) if all three attempts fail.
  - Document the exact URLs and API endpoints being queried in `code/src/fetch_data.py` as comments.
  - Write `code/tests/test_fetch_data.py` with unit tests verifying that (a) each fetch function returns a DataFrame with the required columns, (b) no missing values exist in required columns, (c) species count is ≥ 1 for a successful fetch.
  - **Verification**: Run `pytest code/tests/test_fetch_data.py -v` and confirm all tests pass. Document a sample of fetched species IDs and counts in `outputs/fetch_log.txt`.
  - **Paths**: `code/src/config.py`, `code/src/fetch_data.py`, `code/tests/test_fetch_data.py`, `requirements.txt`, `outputs/fetch_log.txt`.

- [ ] T002 [P1] [US-1] **Data ingestion and preprocessing pipeline**
  - Implement `code/src/preprocess.py` with function `load_and_preprocess(raw_dataframes: List[pd.DataFrame]) -> pd.DataFrame` that:
    - Concatenates input DataFrames and harmonizes column names (e.g., 'Alkaloid_conc' → 'alkaloids').
    - Filters rows with any missing required predictor or outcome columns (species_id, family, alkaloids, terpenes, phenolics, benzoxazinoids, herbivory_score).
    - For metabolite-class columns documented as biologically absent in the source metadata, imputes zeros and records the absence in an `absence_indicator` JSON column (e.g., `{"alkaloids": "documented_absent"}`); for truly missing data, excludes the row.
    - Detects extreme herbivory outliers via IQR method (1.5 × IQR); caps values at the upper whisker or flags them in a log.
    - Z-score standardizes all four metabolite columns using `sklearn.preprocessing.StandardScaler` (fit on training data only in later phases).
    - Validates output against `processed_data.schema.yaml` using `jsonschema`.
    - Writes cleaned DataFrame to `data/processed/clean.parquet` and computes SHA-256 checksum, recording it in `outputs/preprocessing_log.json`.
  - Write `code/tests/test_preprocess.py` verifying that (a) output has no missing values in required columns, (b) metabolite columns are z-scored (mean ≈ 0, std ≈ 1), (c) absence_indicator is correctly populated, (d) output validates against the schema.
  - **Verification**: Run `pytest code/tests/test_preprocess.py -v` and confirm all tests pass. Inspect `data/processed/clean.parquet` and verify row count, column names, and data types match the contract.
  - **Paths**: `code/src/preprocess.py`, `code/tests/test_preprocess.py`, `data/processed/clean.parquet`, `outputs/preprocessing_log.json`.

- [ ] T003 [P1] [US-2] **Exploratory correlation analysis and early visualization**
  - Implement `code/src/correlation_analysis.py` with function `compute_correlations(df: pd.DataFrame) -> dict` that:
    - Computes Pearson correlation coefficients between each of the four metabolite classes (averaged across species) and herbivory_score.
    - Computes two-tailed p-values for each correlation using `scipy.stats.pearsonr`.
    - Applies Benjamini-Hochberg FDR correction to the four class-level p-values (q-value threshold 0.05).
    - Identifies metabolite classes with significant negative correlation (q < 0.05, coefficient < 0) and stores them in a list.
    - Returns a dict conforming to `AnalysisResult` with `result_type="correlation"` and payload containing `matrix`, `p_values`, `q_values`, `significant_negative_classes`, and `method="Pearson"`.
  - Implement `code/src/visualization.py` with function `plot_correlation_heatmap(corr_dict: dict, output_path: str)` that generates a seaborn heatmap PNG with (a) correlation values in cells, (b) asterisks or color intensity indicating significance (q < 0.05), (c) axis labels for metabolite classes and herbivory_score.
  - Write `code/tests/test_correlation.py` verifying that (a) correlation coefficients are in [-1, 1], (b) p-values and q-values are in [0, 1], (c) significant_negative_classes contains only classes with q < 0.05 and coefficient < 0.
  - **Verification**: Run the correlation analysis on `data/processed/clean.parquet`, generate the heatmap PNG, and save the AnalysisResult JSON to `outputs/correlation_results.json`. Confirm that at least one metabolite class is identified as significant (or document if none are, as a null result). Visually inspect the heatmap for readability and correct significance annotation.
  - **Paths**: `code/src/correlation_analysis.py`, `code/src/visualization.py`, `code/tests/test_correlation.py`, `outputs/correlation_results.json`, `outputs/heatmap.png`.

---

## Phase 2: Complete the study and validate its evidence

**Goal**: Run the complete specified analyses (baseline OLS with family covariate, phylogenetic-adjusted PGLS and mixed-effects, Random Forest with permutation importance), apply rigorous multiple-comparison correction, conduct sensitivity and power analyses, and validate all outputs against contracts.

- [ ] T004 [P2] [US-3] **Baseline OLS regression with family covariate and multicollinearity diagnostics**
  - Implement `code/src/ols_regression.py` with function `fit_ols_model(df: pd.DataFrame, test_size: float = 0.2) -> dict` that:
    - Splits data 80/20 stratified by family using `sklearn.model_selection.train_test_split(stratify=df['family'], random_state=42)`.
    - Fits an OLS model using `statsmodels.api.OLS` with herbivory_score as the dependent variable, four metabolite concentrations as predictors, and family (one-hot encoded) as a fixed-effect categorical covariate.
    - Computes variance inflation factors (VIF) for each metabolite predictor using `statsmodels.stats.outliers_influence.variance_inflation_factor`; flags any VIF ≥ 5.
    - Evaluates on the test set: computes R², adjusted R², and RMSE.
    - Computes p-values for each metabolite coefficient and applies Benjamini-Hochberg FDR correction (q-value threshold 0.05).
    - Returns an AnalysisResult dict with `result_type="ols"`, containing coefficients, p-values, q-values, R², adj_R², RMSE, VIF, family effect, train/test sample sizes, and FDR method.
  - Write `code/tests/test_ols.py` verifying that (a) train/test split respects the 80/20 ratio, (b) VIF values are non-negative, (c) R² is in [0, 1], (d) output validates against `model_output.schema.yaml`.
  - **Verification**: Run OLS on `data/processed/clean.parquet`, save the AnalysisResult JSON to `outputs/ols_results.json`, and confirm that the model achieves R² > 0.1 (or document if lower, as a null result). Log any VIF ≥ 5 warnings to `outputs/ols_warnings.txt`.
  - **Paths**: `code/src/ols_regression.py`, `code/tests/test_ols.py`, `outputs/ols_results.json`, `outputs/ols_warnings.txt`.

- [ ] T005 [P2] [US-3] **Phylogenetic adjustment via PGLS and mixed-effects models**
  - Implement `code/src/phylogenetic_analysis.py` with functions:
    - `fetch_phylogeny(species_names: List[str]) -> dendropy.Tree` that retrieves plant phylogeny from Open Tree of Life (OTL) via the OTL API (https://api.opentreeoflife.org/v3/tree_of_life/mrca) or `dendropy.datamodel.tree.Tree.get()`.
    - `match_species_to_otl(species_names: List[str]) -> Tuple[List[str], List[str]]` that uses fuzzy matching (fuzzywuzzy, threshold 0.8) to match species names to OTL taxa; returns matched and unmatched lists.
    - `fit_pgls_model(df: pd.DataFrame, phylogeny: dendropy.Tree, test_size: float = 0.2) -> dict` that:
      - Constructs a variance-covariance matrix from the phylogeny using `dendropy` methods.
      - Fits a generalized least squares (GLS) model using `statsmodels.api.GLS` with the phylogenetic covariance as the covariance matrix, herbivory_score as dependent variable, metabolites and family as predictors.
      - Performs a likelihood-ratio test (LRT) comparing PGLS to OLS fit: computes LRT statistic and p-value; if LRT p < 0.05, phylogenetic adjustment is significant.
      - Returns an AnalysisResult dict with `result_type="pgls"`, containing coefficients, p-values, q-values (FDR-corrected), R², adj_R², RMSE, phylogeny_source, species_matched, species_unmatched, LRT statistic, LRT p-value, and interpretation.
    - `fit_mixed_effects_model(df: pd.DataFrame, test_size: float = 0.2) -> dict` that:
      - Fits a linear mixed-effects model using `statsmodels.regression.mixed_linear_model.MixedLM` with family as fixed covariate, metabolites as fixed predictors, and species-level random intercept.
      - Computes p-values for fixed effects and applies Benjamini-Hochberg FDR correction.
      - Returns an AnalysisResult dict with `result_type="mixed_effects"`, containing fixed_effects, fixed_p_values, fixed_q_values, random_intercept_std, R² marginal, R² conditional, and RMSE.
  - Write `code/tests/test_phylogenetic.py` verifying that (a) phylogeny retrieval returns a valid tree, (b) fuzzy matching produces a reasonable match rate, (c) PGLS and mixed-effects models fit without errors, (d) LRT p-value is in [0, 1], (e) outputs validate against the schema.
  - **Verification**: Run phylogenetic analysis on `data/processed/clean.parquet`, save PGLS results to `outputs/pgls_results.json` and mixed-effects results to `outputs/mixed_effects_results.json`. Document the number of species matched and unmatched in `outputs/phylogeny_matching_log.txt`. Compare coefficients across OLS, PGLS, and mixed-effects models; record any changes in coefficient direction or significance (e.g., 95% CI overlap) in `outputs/model_comparison.txt`.
  - **Paths**: `code/src/phylogenetic_analysis.py`, `code/tests/test_phylogenetic.py`, `outputs/pgls_results.json`, `outputs/mixed_effects_results.json`, `outputs/phylogeny_matching_log.txt`, `outputs/model_comparison.txt`.

- [ ] T006 [P2] [US-3] **Random Forest regressor with permutation feature importance and FDR correction**
  - Implement `code/src/random_forest_model.py` with function `fit_rf_model(df: pd.DataFrame, test_size: float = 0.2) -> dict` that:
    - Uses the same 80/20 train-test split (stratified by family, `random_state=42`) as OLS.
    - Fits a `RandomForestRegressor(max_depth=5, n_estimators=200, random_state=42, n_jobs=2)` with 5-fold cross-validation using `sklearn.model_selection.cross_validate`.
    - Computes permutation feature importance on the test set using `sklearn.inspection.permutation_importance(estimator, X_test, y_test, n_repeats=100, random_state=42)`, which returns importance scores and standard errors.
    - Derives p-values from permutation importance by comparing observed importance to a null distribution (importance ≈ 0); applies Benjamini-Hochberg FDR correction to the four metabolite p-values (q-value threshold 0.05).
    - Evaluates cross-validated R², adjusted R², RMSE and test-set R², adjusted R², RMSE.
    - Returns an AnalysisResult dict with `result_type="rf"`, containing ranked feature_importance list (with metabolite, importance, p_value, q_value for each), CV metrics, test metrics, and FDR method.
  - Write `code/tests/test_rf.py` verifying that (a) feature importance scores are non-negative, (b) p-values and q-values are in [0, 1], (c) feature ranking is consistent across runs (due to fixed random_state), (d) output validates against the schema.
  - Log a warning if test-set R² < 0.1 to `outputs/rf_warnings.txt` (per US-3 acceptance scenario).
  - **Verification**: Run Random Forest on `data/processed/clean.parquet`, save the AnalysisResult JSON to `outputs/rf_results.json`, and confirm that the ranked feature list contains all four metabolites with FDR-corrected p-values. Inspect the CV and test metrics for consistency.
  - **Paths**: `code/src/random_forest_model.py`, `code/tests/test_rf.py`, `outputs/rf_results.json`, `outputs/rf_warnings.txt`.

- [ ] T007 [P2] **Sensitivity analysis: p-value thresholds, outlier caps, and standardization robustness**
  - Implement `code/src/sensitivity_analysis.py` with function `run_sensitivity_analysis(df: pd.DataFrame) -> dict` that:
    - **P-value threshold sweep**: Re-run correlation analysis (from T003) with p-value thresholds from 0.01 to 0.10 (step 0.01); record the number of significant metabolite classes at each threshold. Store results in a dict keyed by threshold string (e.g., "0.01": {"n_significant_classes": 2}).
    - **Outlier cap variation**: Re-run OLS and Random Forest (from T004 and T006) with herbivory outlier caps at ±10% of the baseline IQR whisker; record R² for each model at each cap level (minus_10%, baseline, plus_10%).
    - **Raw vs. standardized robustness**: Re-run OLS and Random Forest on the raw (non-z-scored) metabolite concentrations; compare the identified biomarker rankings (top 3 metabolites by coefficient magnitude or importance) to the z-scored results; document the ranking agreement (e.g., "high (top 2 consistent)", "moderate", "low").
    - Returns an AnalysisResult dict with `result_type="sensitivity"`, containing p_threshold_sweep, outlier_cap_variation, and raw_vs_standardized comparison.
  - Write `code/tests/test_sensitivity.py` verifying that (a) p-value sweep produces results for all thresholds, (b) outlier cap results have three entries (minus, baseline, plus), (c) raw vs. standardized comparison documents ranking agreement.
  - **Verification**: Run sensitivity analysis on `data/processed/clean.parquet`, save the AnalysisResult JSON to `outputs/sensitivity_results.json`, and confirm that results demonstrate robustness (e.g., top biomarkers remain consistent across thresholds and standardization approaches) or document substantial sensitivity if found.
  - **Paths**: `code/src/sensitivity_analysis.py`, `code/tests/test_sensitivity.py`, `outputs/sensitivity_results.json`.

- [ ] T008 [P2] **Power analysis and study adequacy assessment**
  - Implement `code/src/power_analysis.py` with function `compute_power_analysis(df: pd.DataFrame, pgls_result: dict) -> dict` that:
    - Computes effective sample size after phylogenetic adjustment using the phylogenetic lambda parameter (if available from PGLS) or a default estimate; formula: `effective_n = n_observed / (1 + (lambda - 1) * phylogenetic_signal)`.
    - Estimates statistical power to detect small-to-medium effect sizes (r ≈ 0.3, corresponding to R² ≈ 0.09) at α = 0.05 with Benjamini-Hochberg FDR correction (adjusted α ≈ 0.0125 for four tests) using `scipy.stats.power_divergence` or `statsmodels.stats.power.tt_ind_solve_power`.
    - Flags the study as exploratory (under_power_flag=True) if N < 50 after filtering; otherwise, marks as adequate (under_power_flag=False).
    - Returns an AnalysisResult dict with `result_type="power_analysis"`, containing observed_n, phylogenetic_lambda, effective_n, effect_size_target, alpha_per_test, power_ols, power_pgls, power_rf, under_power_flag, and interpretation.
  - Write `code/tests/test_power.py` verifying that (a) effective_n ≤ observed_n, (b) power estimates are in [0, 1], (c) under_power_flag is correctly set based on N.
  - **Verification**: Run power analysis on `data/processed/clean.parquet` and PGLS results, save the AnalysisResult JSON to `outputs/power_analysis_results.json`, and confirm that the study's power is documented (e.g., "adequate for hypothesis-generating research" or "exploratory due to sample size < 50").
  - **Paths**: `code/src/power_analysis.py`, `code/tests/test_power.py`, `outputs/power_analysis_results.json`.

---

## Phase 3: Reproducible results and paper handoff

**Goal**: Validate all artifacts against contracts, assemble a concise methods-and-results report, re-run the complete workflow from declared inputs to confirm reproducibility, and prepare for paper-stage handoff.

- [ ] T009 [P3] **Contract validation and artifact verification**
  - Implement `code/src/validation.py` with functions:
    - `validate_processed_data(df: pd.DataFrame, schema_path: str) -> bool` that validates `data/processed/clean.parquet` against `contracts/processed_data.schema.yaml` using `jsonschema.validate()`.
    - `validate_analysis_results(result_dict: dict, schema_path: str) -> bool` that validates each AnalysisResult JSON (correlation, OLS, PGLS, mixed-effects, RF, sensitivity, power_analysis) against `contracts/model_output.schema.yaml`.
    - `compute_checksums(artifact_paths: List[str]) -> dict` that computes SHA-256 checksums for all data and result artifacts and returns a dict mapping path → checksum.
  - Write `code/tests/test_validation.py` verifying that (a) schema files exist and are valid JSON Schema, (b) all artifacts pass validation, (c) checksums are reproducible (same input → same checksum).
  - **Verification**: Run validation on all artifacts generated in T001–T008; save checksum report to `outputs/artifact_checksums.json`. Confirm that all artifacts pass schema validation; any failures must be corrected in the upstream tasks before proceeding.
  - **Paths**: `code/src/validation.py`, `code/tests/test_validation.py`, `outputs/artifact_checksums.json`.

- [ ] T010 [P3] **Comprehensive methods-and-results report**
  - Assemble a Markdown report in `outputs/report.md` that:
    - Documents the research question, data sources (URLs), and sample size (N species, number of metabolites, number of herbivory measurements).
    - Describes preprocessing steps: z-score standardization, handling of missing data and documented biological absence, outlier detection and capping.
    - Summarizes exploratory correlation analysis: metabolite classes with significant negative correlation (q < 0.05), heatmap visualization, and interpretation.
    - Reports baseline OLS results: coefficients, p-values (FDR-corrected), R², adjusted R², RMSE, VIF diagnostics, and family-covariate effect.
    - Reports phylogenetic-adjusted results: PGLS coefficients and LRT comparison to OLS, mixed-effects random intercept and marginal/conditional R², and interpretation of phylogenetic signal.
    - Reports Random Forest results: ranked feature importance (with FDR-corrected p-values), CV and test metrics, and comparison to OLS.
    - Documents sensitivity analysis: p-value threshold sweep, outlier cap robustness, and raw vs. standardized comparison.
    - Reports power analysis: effective sample size, power estimates, and study adequacy flag.
    - Includes links to all JSON result files and PNG figures (e.g., `[Correlation heatmap](heatmap.png)`, `[OLS results](ols_results.json)`).
    - **If a placeholder dataset was used** (due to repository unavailability), includes a prominent disclaimer: "Results are based on synthetic/placeholder data and do not address the biological research question."
    - Discusses limitations: phylogenetic non-independence, observational nature of data (no causal claims), potential confounders (e.g., plant family effects), and power constraints if N < 50.
    - Concludes with recommendations for future work (e.g., larger sample size, experimental validation, functional genomics).
  - **Verification**: Proofread the report for clarity, confirm all file links are correct, and ensure that negative findings (if any) are documented honestly. Save the report to `outputs/report.md`.
  - **Paths**: `outputs/report.md`.

- [ ] T011 [P3] **End-to-end reproducibility run and documentation**
  - Create a shell script `scripts/run_pipeline.sh` that:
    - Activates the Python virtual environment (or specifies `python3.11`).
    - Runs all data acquisition, preprocessing, analysis, and validation steps in order: `python code/src/fetch_data.py`, `python code/src/preprocess.py`, `python code/src/correlation_analysis.py`, `python code/src/ols_regression.py`, `python code/src/phylogenetic_analysis.py`, `python code/src/random_forest_model.py`, `python code/src/sensitivity_analysis.py`, `python code/src/power_analysis.py`, `python code/src/validation.py`.
    - Records start and end timestamps and total wall-clock elapsed time in `outputs/pipeline_log.txt`.
    - Exits with status 0 on success, non-zero on any failure.
  - Create a `README.md` in the project root documenting:
    - **Quick start**: "Run `bash scripts/run_pipeline.sh` to execute the complete analysis from scratch."
    - **Input data sources**: Lists the three repository URLs (MetaboLights, PMN, HPID) and the fallback placeholder dataset (if applicable).
    - **Output artifacts**: Lists all generated files (clean.parquet, JSON results, PNG figures, report.md) and their locations.
    - **Dependencies**: References `requirements.txt` and specifies Python 3.11.
    - **Reproducibility**: Notes that all random seeds are fixed (`random_state=42`) and all computations are deterministic.
    - **Runtime**: States the expected total wall-clock time (e.g., "Approximately 2–3 hours on a 2-core CPU runner").
  - Write `code/tests/test_pipeline.py` (integration test) that:
    - Runs the entire pipeline end-to-end (or a minimal subset for speed).
    - Verifies that all expected output files are created.
    - Confirms that the pipeline completes within the 6-hour time limit (measured in CI).
  - **Verification**: Execute `bash scripts/run_pipeline.sh` on a fresh checkout; confirm that all outputs are generated, all tests pass, and the total runtime is logged in `outputs/pipeline_log.txt` and does not exceed 6 hours. Verify that the README instructions are accurate and the project is reproducible.
  - **Paths**: `scripts/run_pipeline.sh`, `README.md`, `code/tests/test_pipeline.py`, `outputs/pipeline_log.txt`.

- [ ] T012 [P3] **Paper-stage handoff documentation**
  - Create `outputs/handoff.md` that:
    - Lists all scientific findings (significant metabolite classes, biomarker rankings, model performance metrics, power limitations).
    - Specifies the exact data artifacts available for the paper stage: `data/processed/clean.parquet` (processed dataset), `outputs/heatmap.png` (correlation visualization), `outputs/ols_results.json`, `outputs/pgls_results.json`, `outputs/rf_results.json` (model outputs), `outputs/report.md` (summary).
    - Documents the schema contracts (`processed_data.schema.yaml`, `model_output.schema.yaml`) that define the structure of all results.
    - Notes any data source fallbacks or placeholder usage (if applicable) and their implications for interpretation.
    - Specifies which results are suitable for inclusion in the paper (e.g., "OLS and PGLS coefficients with FDR-corrected p-values are publication-ready; RF feature importance is exploratory").
    - Provides checksums (`outputs/artifact_checksums.json`) for verification of result integrity.
    - Clarifies that the research stage is complete; the paper stage will handle figure layout, PDF compilation, and submission workflows (not replicated here).
  - **Verification**: Confirm that the handoff document accurately reflects all completed work, all artifact paths are correct, and the paper stage team has clear guidance on what is available and how to use it.
  - **Paths**: `outputs/handoff.md`.

---

## Dependencies and requirement coverage

| Requirement | Tasks | Verification command |
|-------------|-------|----------------------|
| **FR-001**: Download and parse metabolomics–herbivory data from public repositories (≥50 species) | T001 | `python code/src/fetch_data.py && wc -l data/raw/*.csv` |
| **FR-002**: Normalize metabolite concentrations (z-score), handle missing values, impute zeros for documented absence | T002 | `pytest code/tests/test_preprocess.py -v && python -c "import pandas as pd; df=pd.read_parquet('data/processed/clean.parquet'); print(f'Rows: {len(df)}, Missing: {df.isnull().sum().sum()}')"` |
| **FR-003**: Compute correlations, identify 3–5 classes with significant negative correlation (q < 0.05), generate heatmap | T003 | `pytest code/tests/test_correlation.py -v && ls -lh outputs/heatmap.png outputs/correlation_results.json` |
| **FR-004**: Fit baseline OLS with family covariate, compute VIF, assess multicollinearity | T004 | `pytest code/tests/test_ols.py -v && python -c "import json; r=json.load(open('outputs/ols_results.json')); print(f\"R²: {r['payload']['r2']}, VIF: {r['payload']['vif']}\")"` |
| **FR-005**: Train Random Forest (max_depth=5, 5-fold CV), rank metabolites by feature importance | T006 | `pytest code/tests/test_rf.py -v && python -c "import json; r=json.load(open('outputs/rf_results.json')); print(f\"Top metabolite: {r['payload']['feature_importance'][0]['metabolite']}\")"` |
| **FR-006**: Apply Benjamini–Hochberg FDR correction to all p-values | T003, T004, T006 | `python -c "import json; r=json.load(open('outputs/correlation_results.json')); print('q_values' in r['payload'])"` (confirm for all result types) |
| **FR-007**: Validate dataset–variable fit before analysis | T002 | `pytest code/tests/test_preprocess.py -v` (verifies required columns present) |
| **FR-008**: Fit PGLS and mixed-effects models, account for phylogenetic non-independence, report LRT | T005 | `pytest code/tests/test_phylogenetic.py -v && python -c "import json; r=json.load(open('outputs/pgls_results.json')); print(f\"LRT p-value: {r['payload']['lrt_p_value']}\")"` |
| **SC-001**: Measure sample size against target (≥50 species) | T001, T008 | `python -c "import pandas as pd; df=pd.read_parquet('data/processed/clean.parquet'); print(f'N species: {len(df)}')"` |
| **SC-002**: Measure R² against threshold (> 0.3) | T004, T006 | `python -c "import json; r=json.load(open('outputs/ols_results.json')); print(f\"OLS R²: {r['payload']['r2']}\")"` |
| **SC-003**: Measure FDR and identify significant classes (q < 0.05) | T003 | `python -c "import json; r=json.load(open('outputs/correlation_results.json')); print(f\"Significant classes: {r['payload']['significant_negative_classes']}\")"` |
| **SC-004**: Measure multicollinearity (VIF < 5) | T004 | `python -c "import json; r=json.load(open('outputs/ols_results.json')); print(f\"Max VIF: {max(r['payload']['vif'].values())}\")"` |
| **SC-005**: Measure runtime (≤6 hours) | T011 | `grep "Total elapsed" outputs/pipeline_log.txt` |

---

## Revision behavior

Preserve working artifacts and already verified requirements. Carry forward their identities and status; do not erase completed work to make the list look shorter. Use the precise failing command or verifier diagnosis to repair affected tasks. Consolidate redundant pending tasks without dropping their acceptance criteria. A narrow implementation failure is not a reason to rebuild the project skeleton, rewrite unrelated modules, or expand the study into an application framework.

When the `/speckit.analyze` stage identifies issues, the tasker agent (Mode B) will propose targeted patches to `spec.md`, `plan.md`, or this `tasks.md` file. Such patches will:
- Address the specific reviewer concern or failing verification command.
- Preserve all completed task checkboxes and their identities.
- Reopen only the affected task(s) for correction (e.g., if T004 has a wrong path, uncheck T004 and update its paths; do not regenerate the entire task list).
- Never substitute a different analysis or remove a scientific requirement to satisfy a constraint.
