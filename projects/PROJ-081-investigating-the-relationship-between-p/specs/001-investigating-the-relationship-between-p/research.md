# Research: Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance

**Feature**: `001-investigating-plant-metabolite-herbivore-resistance`  
**Date**: 2026-10-19  

## Objective
Quantify how plant secondary‑metabolite class abundances (alkaloids, terpenes, phenolics, benzoxazinoids) associate with measured herbivory damage, and identify which metabolites are the strongest predictive biomarkers. All findings are framed as associational (observational data) and robustness to analytical choices (standardization, outlier handling, phylogenetic adjustment) is documented.

## Decision / Rationale
- **Method choice**: Classical statistical models (OLS with family covariate, PGLS, mixed-effects) and a shallow Random Forest are fully CPU‑tractable; no GPU is required.  
- **Dataset selection**: The intended repositories (MetaboLights, PMN, HPID) are the PRIMARY targets. If all three fail to provide ≥50 species with paired metabolite–herbivory data, the study scope is reduced: if an alternative open metabolomics-herbivory dataset is available, use it; otherwise, fall back to the placeholder dataset (GHZ parquet) with an explicit disclaimer that results do not address the biological research question (placeholder is language-model training data, not plant data). This fallback validates the pipeline methodology but not the biological conclusions.  
- **Statistical rigor**: Multiple‑comparison correction (Benjamini‑Hochberg) will be applied to all correlation, regression, and permutation-importance p‑values. A 5‑fold cross‑validation scheme will be used for model performance estimation, satisfying Constitution Principle VII. A formal power analysis will estimate the effective sample size after phylogenetic adjustment and flag under-power if N < 50.  
- **Phylogenetic control**: A phylogenetic covariance matrix from the Open Tree of Life will be incorporated via GLS (PGLS) and via mixed-effects random intercepts to address non-independence (FR‑008). A likelihood-ratio test will assess whether phylogenetic adjustment significantly improves model fit.  
- **Construct validity**: Z‑score standardization is applied for cross-species comparison (Constitution VI), but robustness to raw-concentration representation is tested in Phase 7 sensitivity analysis. Zero-imputation for missing metabolite classes is restricted to documented biological absence; missing data are excluded.  

## Dataset Strategy
| Source | Verified URL (provided) | Loader | Notes |
|--------|------------------------|--------|-------|
| MetaboLights (intended PRIMARY) | *no verified URL* | REST API | Attempted first; retry logic with 3 attempts + 30 s backoff. |
| Plant Metabolic Network (PMN) (intended PRIMARY) | *no verified URL* | REST API | Attempted second; same retry logic. |
| Herbivore-Plant Interaction Database (HPID) (intended PRIMARY) | *no verified URL* | REST API | Attempted third; same retry logic. |
| Alternative open metabolomics-herbivory source (if available) | *to be identified* | – | If all three primaries fail, search for alternative open source. |
| Placeholder (GHZ language-model dataset) | ` | `datasets.load_dataset(...)` | **Used ONLY if all primaries and alternatives are unavailable.** Disclaimer: not plant data; results are methodology proof-of-concept only. |

> **Important**: No fabricated URLs are introduced. The plan clearly states which required datasets lack a verified source and what fallback logic applies.

## Power Analysis & Sample Size

Before modeling, the effective sample size is calculated as follows:

1. **Phylogenetic adjustment reduces effective N**: A phylogenetic PGLS or mixed-effects model accounts for species non-independence. The effective sample size is typically reduced by a factor reflecting phylogenetic signal (Pagel's λ or Brownian-motion scaling). If λ is substantially less than 1, effective N is correspondingly reduced relative to observed N.  
2. **Multiple-comparison correction reduces power**: With Benjamini-Hochberg FDR control at q < 0.05 across 4 metabolite classes (and additional tests for sensitivity analysis), the per-test α threshold is lowered; power to detect a given effect size is reduced.  
3. **Estimated power**: Assuming observed N ≥ 50, effective N ≈ 35–40 after phylogenetic adjustment. Power to detect a small-to-medium effect (r ≈ 0.3) at α = 0.05 (per-test, post-FDR) is ~60–[deferred] for OLS and ~50–[deferred] for PGLS. This is modest but acceptable for hypothesis-generating research.
4. **Flag if N < 50**: If the acquired data yields < 50 species with complete paired data after filtering, the study is flagged as exploratory and under-powered for confirmatory claims; results are framed as hypothesis-generating.  

## Statistical Methods
| Analysis | Method | Software | Multiple‑Comparison | Power / Sample‑Size |
|----------|--------|----------|----------------------|---------------------|
| Correlation (class vs herbivory) | Pearson r | `scipy.stats.pearsonr` | Benjamini‑Hochberg (FDR q < 0.05) | Effective N reported; power estimated post-adjustment. |
| Baseline OLS | OLS with family as fixed covariate | `statsmodels.api.OLS` | BH on coefficient p‑values | Effective N from power analysis. |
| Phylogenetic GLS | GLS with phylogenetic covariance matrix (OTL-derived) | `statsmodels.api.GLS` | BH on coefficients; LRT (p < 0.05) for PGLS vs OLS fit | Same N; LRT assesses adjustment significance. |
| Mixed‑Effects | `MixedLM` with family fixed, species random intercept | `statsmodels` | BH on fixed-effect coefficients | Same N; LRT compares to OLS. |
| Random Forest | `RandomForestRegressor(max_depth=5)` with permutation importance | `sklearn.ensemble` + `sklearn.inspection.permutation_importance` | BH on permutation p-values (n_repeats=100) | CV-based R² reported; power not formally estimated. |
| Sensitivity | Threshold sweep (p ∈ [0.01, 0.10]), outlier-cap variation ±10%, raw-concentration robustness | Custom loops | BH applied per sweep | Exploratory; no formal power. |

## Expected Outputs
- Normalized clean dataset (`data/processed/clean.parquet`) with optional absence_indicator column.  
- Correlation heatmap PNG (`outputs/heatmap.png`).  
- JSON summaries for correlation, OLS, PGLS, mixed-effects, Random Forest, sensitivity, and power analyses (`outputs/*.json`), all in AnalysisResult format.  
- Markdown report linking all artifacts (`outputs/report.md`), with explicit disclaimer if placeholder data was used.  
- YAML contracts for dataset and model outputs (`contracts/*.schema.yaml`).  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open metabolomics‑herbivory dataset available | Limits biological relevance | Attempt MetaboLights/PMN/HPID first; if all fail, search for alternatives; only use placeholder with explicit disclaimer that results do not address the research question. |
| Memory overflow on large CSVs | Job failure | Stream data in Phase 1 using `datasets.load_dataset(..., streaming=True)`; batch processing fallback. |
| API rate‑limits or downtime | Incomplete acquisition | Retry logic (3 attempts, 30 s back‑off) and graceful degradation to next data source. |
| Multicollinearity among metabolites | Inflated OLS variance | Compute VIF; if any VIF ≥ 5, report and rely on Random Forest for ranking (less sensitive to collinearity). |
| Species unmatched to OTL phylogeny | Reduced phylogenetic model sample | Fuzzy matching + fallback to common-name lookup; document unmatched species and exclude with note. |
| Under-power (N < 50 after filtering) | Weak statistical inference | Conduct formal power analysis; flag study as exploratory if N < 50; frame results as hypothesis-generating. |
| Standardization artifacts | Construct validity threat | Test robustness by repeating OLS/RF on raw (non-standardized) concentrations in Phase 7. |

---