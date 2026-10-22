# Research: Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance

**Feature**: `001-investigating-plant-metabolite-herbivore-resistance`  
**Date**: 2026-10-22  

## Objective
Quantify how the four plant secondary‑metabolite classes (alkaloids, terpenes, phenolics, benzoxazinoids) associate with herbivore damage, identify the strongest predictive biomarkers, and assess robustness to analytical choices (standardization, outlier handling, phylogenetic non‑independence).

## Decision / Rationale
- **Method choice**: Classical statistical models (OLS, PGLS, mixed‑effects) and a shallow Random Forest are fully CPU‑tractable; no GPU is required.  
- **Dataset selection**: **No open, verified paired metabolomics‑herbivory dataset exists** in MetaboLights, PMN, or HPID. Consequently, the pipeline will run on the **verified GHZ placeholder dataset** (`). This dataset does **not** contain real plant metabolite or herbivory measurements; it is used **solely to validate the workflow**. A clear disclaimer will be added to the final report.  
- **Statistical rigor**: Benjamini‑Hochberg FDR correction applied to all correlation, regression, and permutation‑importance p‑values. 5‑fold cross‑validation for model performance (R², adjusted R², RMSE) satisfies Constitution Principle VII. A formal power analysis estimates effective sample size after phylogenetic adjustment and flags under‑power.  
- **Phylogenetic control**: A variance‑covariance matrix derived from the Open Tree of Life will be incorporated via GLS (PGLS) and via a mixed‑effects model with species‑level random intercepts (FR‑008). A likelihood‑ratio test will assess whether phylogenetic adjustment significantly improves fit.  
- **Construct validity**: Z‑score standardization (Constitution VI) is applied; robustness to raw concentrations is examined in Phase 7. Zero‑imputation is performed **only after** standardization for truly missing values; documented absences are stored in a separate binary indicator (`absence_indicator`).  
- **Confounder acknowledgement**: If additional ecological covariates (e.g., plant size, geographic region) are present in the source data they will be included in the OLS model; otherwise, the limitation will be explicitly noted in the report.  

## Dataset Strategy
| Source | Verified URL (provided) | Loader | Notes |
|--------|------------------------|--------|-------|
| MetaboLights (primary) | *no verified URL* | REST API | Attempted first; retry logic with 3 attempts + 30 s back‑off. |
| Plant Metabolic Network (PMN) (primary) | *no verified URL* | REST API | Attempted second; same retry logic. |
| Herbivore‑Plant Interaction Database (HPID) (primary) | *no verified URL* | REST API | Attempted third; same retry logic. |
| GHZ placeholder (fallback) | ` | `datasets.load_dataset` | **Used ONLY for methodological proof‑of‑concept**. Disclaimer: results are not biologically meaningful. |

> No fabricated URLs are introduced. The plan explicitly states which required datasets lack a verified source and why the placeholder is required.

## Power Analysis & Sample Size
1. **Effective N**: After phylogenetic adjustment (λ estimated from OTL tree) the effective sample size is reduced relative to observed N.  
2. **Multiple‑comparison impact**: Benjamini‑Hochberg lowers the per‑test α; The power to detect a moderate correlation at α ≈ 0.0125 is modest.  
3. **Estimated power** (assuming observed N ≥ 50): Effective sample sizes in the order of a few dozen provide moderate statistical power for OLS and somewhat lower power for PGLS.  
4. **Under‑power flag**: If the final cleaned dataset contains **< 50 species**, the study is flagged as exploratory; results are framed as hypothesis‑generating.

## Statistical Methods
| Analysis | Method | Software | Multiple‑Comparison | Power / Sample‑Size |
|----------|--------|----------|----------------------|---------------------|
| Correlation (class ↔ herbivory) | Pearson r (class‑level) + Pearson r (compound‑level) | `scipy.stats.pearsonr` | Benjamini‑Hochberg (q < 0.05) | Power estimated in Phase 8 |
| Baseline OLS | OLS + family covariate + any extra covariates if present | `statsmodels.api.OLS` | BH on coefficients | Effective N from Phase 8 |
| Phylogenetic GLS | GLS with phylogenetic covariance | `statsmodels.api.GLS` | BH on coefficients; LRT vs OLS | Same N |
| Mixed‑Effects | `MixedLM` (family fixed, species random) | `statsmodels` | BH on fixed effects | Same N |
| Random Forest | `RandomForestRegressor(max_depth=5)` + 5‑fold CV | `sklearn` | BH on permutation p‑values | CV‑based R² reported |
| Sensitivity | Threshold sweep, outlier‑cap variation, raw vs. standardized | Custom loops | BH per sweep | Exploratory |

## Expected Outputs
- `data/processed/clean.parquet` – normalized dataset (no missing values); includes optional `absence_indicator`.  
- `outputs/heatmap.png` – correlation heatmap with significance annotations.  
- `outputs/correlation_summary.json` – list of metabolite classes with significant negative correlation (q < 0.05).  
- `outputs/ols_results.json`, `outputs/pgls_results.json`, `outputs/mixed_effects_results.json` – regression diagnostics and performance metrics.  
- `outputs/rf_results.json` – permutation importance ranking + CV / test performance.  
- `outputs/sensitivity.json` – robustness checks.  
- `outputs/power_analysis.json` – effective N, power estimates, under‑power flag.  
- `outputs/report.md` – human‑readable summary, links to all artifacts, and **disclaimer** if placeholder data were used.  
- YAML contracts under `contracts/` for the processed dataset and all model outputs.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open paired metabolomics‑herbivory dataset | Biological conclusions impossible | Use GHZ placeholder for workflow validation; clearly label results as methodological only. |
| Memory overflow on large CSVs | Job failure | Stream data (`datasets.load_dataset(..., streaming=True)`) and batch‑process. |
| API rate‑limits or downtime | Incomplete acquisition | 3‑attempt exponential back‑off; graceful degradation to placeholder. |
| Multicollinearity among metabolites | Inflated variance in OLS | Compute VIF; if any VIF ≥ 5, report and rely on Random Forest for ranking. |
| Species unmatched to OTL phylogeny | Reduced phylogenetic sample | Fuzzy matching + documentation; exclude unmatched with note. |
| Under‑power (N < 50) | Weak inference | Formal power analysis; flag as exploratory; frame results accordingly. |
| Standardization artifacts | Threat to construct validity | Sensitivity analysis comparing raw vs. standardized results (Phase 7). |
| Missing ecological covariates | Potential bias | Include any available covariates; otherwise acknowledge limitation in report. |

---

