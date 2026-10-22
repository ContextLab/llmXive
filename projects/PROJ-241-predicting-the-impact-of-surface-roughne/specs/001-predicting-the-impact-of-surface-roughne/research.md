# Research: Predicting the Impact of Surface Roughness on Tribological Properties

**Feature**: `001-predict-tribology`  
**Research Date**: 2026-10-22  

## Objective
Build a fully reproducible end‑to‑end analysis that predicts **coefficient of friction** and **wear rate** from surface‑roughness descriptors and material properties, evaluates model performance against the success criteria, and provides interpretable SHAP‑based feature‑importance evidence.

## Decision / Rationale
| Decision | Rationale |
|----------|-----------|
| **Compute Platform** | All required algorithms (OLS, Random Forest, Gradient Boosting, SHAP) run comfortably on the CPU‑only GitHub Actions runner; no GPU is needed, satisfying the “CPU‑first” rule. |
| **Dataset Strategy** | The spec cites OpenML dataset **ID 42123** and the NIST Materials Data Repository. Neither appears in the verified datasets block, so Phase 0 will attempt to download them. If either download fails or required columns are missing, the pipeline aborts with `DataAvailabilityError` and the owner must provide an open, verified alternative. |
| **Statistical Methods** | Two targets ⇒ Bonferroni correction for the two p‑values. Power analysis uses a **data‑driven effect size** (Cohen’s d estimated from the training data) with `statsmodels.stats.power.TTestPower` (α = 0.05). If power < 0.8 **or** n < 200, we employ a **Wilcoxon signed‑rank test**; otherwise a **paired t‑test**. |
| **Model Validation** | **Group split** by `pairing_id` prevents leakage across material pairs (Constitution VI, FR‑014). **Nested cross‑validation** (outer + inner folds) yields unbiased performance estimates and satisfies FR‑015. |
| **Interpretability** | SHAP (TreeExplainer for tree models, KernelExplainer for OLS) provides global importance and per‑feature dependence plots. The sign of each important feature is **reported** and compared to known physical trends (e.g., hardness inversely correlates with wear). Discrepancies are logged and highlighted (FR‑011) but do not cause pipeline failure. |
| **Reproducibility** | Random seeds (`RANDOM_SEED=42`) are fixed; all external data are checksummed (`sha256`) and stored read‑only under `data/raw/`. |

## Dataset Strategy
| Source | Verified URL | Loader | Notes |
|--------|--------------|--------|-------|
| **OpenML “Surface Roughness & Tribology”** (ID 42123) | *None in verified list* | `openml.datasets.get_dataset(42123, download_all_files=True, streaming=True)` | Public OpenML API; Phase 0 will verify column presence. |
| **NIST Materials Data Repository** (DOI …) | *None in verified list* | – | Material properties fetched via Materials Project API; fallback to median imputation if unavailable. |
| **Materials Project API** | Requires API key (not publicly available) | `pymatgen.ext.matproj.MPRester` | Attempted; if key missing or request fails, median imputation is used. |

*Only the OpenML API is a genuine open source; the other two lack verified URLs and therefore constitute data‑gaps that must be resolved before proceeding.*

## Methodology Sketch
1. **Data Availability Assessment** – confirm downloadability and required columns.  
2. **Acquisition** – stream OpenML dataset; query Materials Project for missing material properties.  
3. **Feature Extraction** – compute Sa, Sq, Ssk, Sku, Sp, Sv with `pySurf`. If raw files missing, validate fallback roughness columns via a Kolmogorov‑Smirnov test (p > 0.05) before use.  
4. **Cleaning** – MAD outlier removal, median imputation (logging each event), `StandardScaler` standardization, exclude derived aggregate fields from predictors, assert ≥ 200 rows remain.  
5. **Group‑Aware Split** – stratify by `pairing_id` using `GroupShuffleSplit` (80/20).  
6. **Modeling** – nested CV (outer 5‑fold if n ≥ 100 else 3‑fold; inner same) with `GridSearchCV`; train OLS, Random Forest, Gradient Boosting. OLS serves as baseline for significance testing.  
7. **Evaluation** – compute R², MAE, RMSE on held‑out test set for both targets; store in `results/metrics.json`.  
8. **Power & Significance** – power analysis (data‑driven effect size, fallback d = 0.5); choose paired t‑test or Wilcoxon based on power/n; Bonferroni‑corrected p‑values recorded.  
9. **SHAP Interpretation** – generate SHAP values, global importance bar plot, per‑feature dependence plots for top‑5 features; **report** sign consistency with physics, flag contradictions.  
10. **Reporting** – compile `results.json` (SSoT) with metrics, p‑values, top‑5 SHAP features, `imputed_fraction`, row‑count, any sign‑consistency flags, and a checksum manifest for all artifacts.  

## Success Criteria Mapping
| SC | Metric | Target | Implementation Check |
|----|--------|--------|-----------------------|
| SC‑001 | R² (friction) | ≥ 0.7 | `results/metrics.json['r2_friction']` |
| SC‑002 | R² (wear) | ≥ 0.7 | `results/metrics.json['r2_wear']` |
| SC‑003 | p‑value (model vs baseline) | α = 0.05 (Bonferroni‑adjusted) | `results/metrics.json['p_value_friction']`, `p_value_wear` |
| SC‑004 | # features with mean |SHAP| > 0.01 | Count of features in SHAP summary where mean \|SHAP\| > 0.01 |
| SC‑005 | Total runtime | ≤ 6 h | CI logs; pipeline aborts if runtime exceeds limit |
| SC‑006 | Final rows after cleaning | ≥ 200 | `results.json['n_rows']` (asserted in Phase 3) |
| SC‑007 | Imputed rows ≤ 5 % of total | ≤ 5 % | `results.json['imputed_fraction']` (asserted in Phase 3) |

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Data‑gap (OpenML or NIST unavailable)** | Blocking – cannot proceed to modeling. | Phase 0 aborts with explicit error; request alternative open dataset or provide verified URL. |
| **Materials Project API key missing** | Missing material properties → reliance on median imputation, possible performance loss. | Log missing‑rate; if > 30 % of material rows are imputed, raise a warning in `results.json`. |
| **Insufficient sample size (< 200)** | Power < 0.8, may force non‑parametric test; R² targets harder to meet. | Issue warning; proceed with Wilcoxon; note limitation in summary. |
| **Collinearity among roughness descriptors** | Inflated variance, misleading SHAP directionality. | Compute Variance Inflation Factor (VIF); if any VIF > 5, record collinearity warning and avoid interpreting individual coefficients. |
| **Raw profilometry files missing** | Cannot compute `pySurf` descriptors. | Perform KS test on fallback columns; abort if distributions differ (p ≤ 0.05). |

---
