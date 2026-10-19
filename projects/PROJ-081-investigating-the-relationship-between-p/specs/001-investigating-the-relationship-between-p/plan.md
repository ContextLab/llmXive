# Implementation Plan: Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance

**Branch**: `001-investigating-plant-metabolite-herbivore-resistance` | **Date**: 2026-10-19 | **Spec**: [spec.md](../specs/001-investigating-the-relationship-between-p/spec.md)  
**Input**: Feature specification from `/specs/001-investigating-the-relationship-between-p/spec.md`

## Summary
The project must (1) acquire paired metabolomics–herbivory data from open repositories, (2) preprocess and normalize it while preserving construct validity, (3) explore correlations between metabolite classes and herbivory scores, (4) fit baseline OLS with family covariate, phylogenetic-adjusted PGLS, and mixed-effects models, plus a Random Forest regressor, (5) apply rigorous multiple‑comparison correction and permutation testing, (6) conduct power analysis and sensitivity checks, and (7) generate reproducible reports and visualizations. All steps are designed to run on the GitHub Actions free‑tier CPU runner; no GPU‑only methods are required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `dendropy` (for phylogeny), `datasets` (HuggingFace), `requests`, `tqdm`, `scipy`  
- **Storage**: File‑based CSV/Parquet in `data/` and `outputs/` directories  
- **Testing**: `pytest` + contract validation via generated YAML schemas  
- **Target Platform**: Linux (Ubuntu‑latest) GitHub Actions runner  
- **Project Type**: Research library/CLI (no web service)  
- **Performance Goals**: End‑to‑end wall‑clock ≤ 6 h, peak RAM ≤ 7 GB  
- **Constraints**: Must honor the Constitution (reproducibility, data hygiene, etc.)  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | All scripts are deterministic (fixed random seeds) and fetch data from canonical URLs each run. |
| II. Verified Accuracy | No external citations are introduced beyond the verified dataset URLs listed in the "Verified datasets" block. |
| III. Data Hygiene | Raw files are stored read‑only; every transformation writes a new file with a checksum recorded in `state/projects/PROJ-081...yaml`. |
| IV. Single Source of Truth | Every figure/table is generated directly from the processed data artifact; no manual transcription. |
| V. Versioning Discipline | All artifacts are content‑hashed; updates trigger timestamp bump in the project state file. |
| VI. Cross‑Species Metabolite Normalization | Z‑score standardization is applied to all metabolite columns before any modeling; robustness to raw-concentration representation is tested in Phase 7. |
| VII. Statistical Model Validation Rigor | 5‑fold CV, R²/adjusted R², RMSE, FDR‑controlled p‑values, and formal power analysis are reported for all models. |

## Phase/Task Mapping (covers every FR‑ and SC‑ item)

| Phase | Tasks | FR / SC addressed |
|-------|-------|--------------------|
| **0. Project Setup** | - Create virtualenv from `requirements.txt` <br> - Pin random seeds (`np.random.seed(42)`, `random_state=42`) | – |
| **1. Data Acquisition** | 1.1 Attempt download from MetaboLights, PMN, HPID via REST APIs (primary targets) <br> 1.2 Verify presence of required columns (species, family, alkaloid, terpene, phenolic, benzoxazinoid, herbivory_score) <br> 1.3 If all three repositories unavailable AND no alternative open metabolomics-herbivory dataset found, fall back to placeholder (GHZ parquet) with explicit disclaimer that results do not address the biological research question <br> 1.4 Compute SHA‑256 checksums and store in `state/projects/...yaml` <br> 1.5 Log final sample size (N species) and flag if N < 50 (power limitation) | FR‑001, FR‑007 |
| **2. Pre‑processing** | 2.1 Concatenate tables, harmonize column names <br> 2.2 **Distinguish documented biological absence from missing data**: only zero-impute metabolite-class columns when the source explicitly documents that the class is absent; for truly missing data, filter the row <br> 2.3 Filter rows with any missing required predictor/outcome <br> 2.4 Detect extreme herbivory outliers via IQR method (1.5 × IQR); cap or flag <br> 2.5 Z‑score standardize all metabolite columns (Constitution VI) <br> 2.6 Write clean DataFrame to `data/processed/clean.parquet` and checksum it | FR‑002, FR‑003 (identification of significant classes), FR‑006 (multiple‑comparison prep) |
| **3. Exploratory Correlation** | 3.1 Compute Pearson correlation matrix between each metabolite class (averaged across compounds) and herbivory_score <br> 3.2 Apply Benjamini‑Hochberg FDR correction to the class‑level p‑values <br> 3.3 Select 3‑5 classes with significant negative correlation (q < 0.05) <br> 3.4 Generate heatmap PNG with significance annotation and save to `outputs/heatmap.png` <br> 3.5 Summarize selected classes in `outputs/correlation_summary.json` (AnalysisResult format) | FR‑003, FR‑006, SC‑001, SC‑003 |
| **4. Baseline OLS Regression** | 4.1 Split data 80/20 (stratified by family) <br> 4.1a **Include family as a fixed-effect categorical covariate** in the OLS model to control for taxonomic confounding <br> 4.2 Fit OLS (`statsmodels.api.OLS`) on training set with metabolite predictors and family covariate <br> 4.3 Compute VIF for each metabolite predictor; flag VIF ≥ 5 <br> 4.4 Evaluate on test set: R², adjusted R², RMSE, p‑values (FDR‑corrected) <br> 4.5 Store coefficients, diagnostics, VIF, and family-covariate effect in `outputs/ols_results.json` (AnalysisResult format) | FR‑004, FR‑006, SC‑002, SC‑004 |
| **5. Phylogenetic Adjustment (PGLS & Mixed‑Effects)** | 5.1 Retrieve plant phylogeny from Open Tree of Life (OTL) via `dendropy` <br> 5.1a **Match species IDs to OTL taxa using fuzzy matching (e.g., fuzzywuzzy); document unmatched species and exclude them with a note** <br> 5.1b Document number of species matched and any unmatched taxa <br> 5.2 Build a variance‑covariance matrix from the phylogeny <br> 5.3 Fit PGLS using `statsmodels` GLS with phylogenetic covariance and family covariate <br> 5.3a **Apply a likelihood-ratio test (LRT) comparing PGLS vs OLS fit**: if LRT p < 0.05, phylogenetic adjustment is significant; report LRT statistic and p-value <br> 5.4 Additionally, fit a linear mixed‑effects model (`statsmodels.MixedLM`) with family as fixed covariate and species-level random intercept <br> 5.5 Compare coefficients and significance across OLS (with family), PGLS, and mixed-effects models; document any changes in coefficient direction or significance and note the effect size of the change (e.g., 95% CI overlap) | FR‑008, SC‑001 |
| **6. Random Forest Modeling** | 6.1 Use the same train/test split as OLS <br> 6.2 Fit `RandomForestRegressor(max_depth=5, n_estimators=200, random_state=42)` with 5‑fold CV <br> 6.3 **Compute permutation feature importance**: use `sklearn.inspection.permutation_importance` with n_repeats=100 to generate importance scores and p-values via comparison to null distribution <br> 6.3a **Apply Benjamini‑Hochberg FDR correction to permutation p-values** (justified by multiple-metabolite testing) <br> 6.4 Rank metabolites by FDR-corrected importance and report CV‑averaged R², adjusted R², RMSE in `outputs/rf_results.json` (AnalysisResult format) <br> 6.5 Log warning if test‑set R² < 0.1 (per US‑3) | FR‑005, SC‑002 |
| **7. Sensitivity Analysis** | 7.1 Sweep correlation p‑value threshold from 0.01 to 0.10 (step 0.01) and record number of significant classes at each threshold <br> 7.2 Record effect on OLS coefficients when outlier caps are varied ±10 % <br> 7.3 **Robustness check: repeat OLS and Random Forest on raw (non-standardized) metabolite concentrations and compare identified biomarker rankings to z-scored results** (addresses construct validity of standardization) <br> 7.4 Store results in `outputs/sensitivity.json` (AnalysisResult format) | SC‑003, Constitution VI |
| **8. Power Analysis** | 8.1 Calculate effective sample size after phylogenetic adjustment (accounting for non-independence) <br> 8.2 Estimate statistical power to detect small-to-medium effect sizes (r ≈ 0.3) at α = 0.05 with multiple-comparison correction (BH-FDR) <br> 8.3 If N < 50 after filtering, flag study as exploratory/hypothesis-generating rather than confirmatory; document power limitation in final report <br> 8.4 Store power analysis results in `outputs/power_analysis.json` | SC‑001, SC‑005 |
| **9. Reporting & Artifacts** | 9.1 **Validate processed data against processed_data.schema.yaml** <br> 9.2 **Validate all JSON results (OLS, PGLS, RF, sensitivity, power_analysis) against model_output.schema.yaml** (all are AnalysisResult instances) <br> 9.3 Assemble a concise Markdown summary (`outputs/report.md`) linking to all JSON/PNG artifacts and documenting any data source fallbacks or power limitations <br> 9.4 **If placeholder dataset was used, include a disclaimer: "Results are based on synthetic/placeholder data and do not address the biological research question."** <br> 9.5 Record total wall‑clock time in the log; enforce ≤ 6 h | SC‑005 |
| **10. Contract Generation** | 10.1 Ensure `contracts/processed_data.schema.yaml` describes the cleaned DataFrame with optional absence_indicator column <br> 10.2 Ensure `contracts/model_output.schema.yaml` covers AnalysisResult structure for all result types | – |

## Edge‑Case Handling (explicitly maps to spec)
- Missing metabolite class columns with documented absence → zero imputation (Phase 2).  
- Missing metabolite class columns with unknown status → row exclusion (Phase 2).  
- Extreme herbivory outliers → IQR capping (Phase 2).  
- Repository API failure → 3‑attempt exponential back‑off; if all three repositories fail, attempt alternative open metabolomics-herbivory sources; only if none exist, use placeholder with disclaimer (Phase 1).  
- Species unmatched to OTL phylogeny → exclude with documentation (Phase 5).  

## Compute Feasibility
All steps rely on CPU‑friendly libraries (`pandas`, `scikit-learn`, `statsmodels`, `dendropy`). The largest data object is the concatenated metabolomics table; if it exceeds RAM, Phase 1 will stream CSVs row‑wise using `datasets.load_dataset(..., streaming=True)`. Random Forest with 200 trees and depth 5 is well within the 7 GB limit. Permutation importance with n_repeats=100 adds ~10–15 min. Estimated total runtime on the order of several hours on the CI runner.

---