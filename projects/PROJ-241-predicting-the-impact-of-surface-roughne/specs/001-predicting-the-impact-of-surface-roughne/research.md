# Research: Predicting the Impact of Surface Roughness on Tribological Properties

**Feature**: `001-predict-tribology`  
**Research Date**: 2026-10-25  

## Objective
Build a fully reproducible end‑to‑end analysis that predicts **coefficient of friction** and **wear rate** from surface‑roughness descriptors and material properties, evaluates model performance against the success criteria, and provides interpretable SHAP‑based feature‑importance evidence.

## Decision / Rationale
| Decision | Rationale |
|----------|-----------|
| **Compute Platform** | All required algorithms (OLS, Random Forest, Gradient Boosting, SHAP) run comfortably on the CPU‑only GitHub Actions runner; no GPU is needed, satisfying the “CPU‑first” rule. |
| **Dataset Strategy** | The spec cites an OpenML dataset and a NIST Materials Data Repository DOI, but **neither URL is verified nor do they contain the required columns**. Consequently, Phase 0 will attempt to download the dataset and **abort with `DataAvailabilityError`** if the dataset is missing or lacks the needed variables. The owner must provide a verified open dataset that includes the required roughness descriptors and target variables before the pipeline can proceed. |
| **Statistical Methods** | Two targets ⇒ Bonferroni correction for the two p‑values. Power analysis uses a **data‑driven effect size** (Cohen’s d estimated from the training data) with `statsmodels.stats.power.TTestPower` (α = 0.05). If power < 0.8 **or** n < 200, we employ a **Wilcoxon signed‑rank test**; otherwise a **paired t‑test**. |
| **Model Validation** | **Strict group split** by `material_pair_id` **and** by individual material identifiers (`material_1_id`, `material_2_id`) prevents leakage across material pairs and across single materials (Methodology‑bb98e702). Nested cross‑validation (outer + inner folds) yields unbiased performance estimates and satisfies FR‑007. |
| **Interpretability** | SHAP (TreeExplainer for tree models, KernelExplainer for OLS) provides global importance and per‑feature dependence plots. The sign of each important feature is **reported** and compared to known physical trends (e.g., hardness inversely correlates with wear). Discrepancies are logged and highlighted (FR‑011) but do not cause pipeline failure. |
| **Reproducibility** | Random seeds (`RANDOM_SEED=42`) are fixed; all external data are checksummed (`sha256`) and stored read‑only under `data/raw/`. |

## Dataset Strategy
| Source | Verified URL | Loader | Notes |
|--------|--------------|--------|-------|
| **OpenML “Surface Roughness & Tribology”** (ID …) | *No verified URL* | – | Public OpenML API exists, but the specific dataset with required columns has not been verified. Phase 0 will abort if unavailable. |
| **NIST Materials Data Repository** (DOI …) | *No verified URL* | – | Intended source for material properties; if unavailable, median imputation is used. |

*Only the OpenML API is a genuine open source; the other two lack verified URLs and therefore constitute data‑gaps that must be resolved before proceeding.*

## Methodology Sketch
1. **Data Availability Assessment** – confirm downloadability and required columns.  
2. **Acquisition** – stream OpenML dataset; query Materials Project for missing material properties.  
3. **Feature Extraction** – compute Sa, Sq, Ssk, Sku, Sp, Sv with `pySurf`. If raw files missing, validate fallback roughness columns via a Kolmogorov‑Smirnov test (p > 0.05) before use.  
4. **Cleaning** – MAD outlier removal, median imputation (logging each event), `StandardScaler` standardization, exclude derived aggregate fields from predictors, assert ≥ 200 rows remain.  
5. **Strict Group‑Aware Split** – stratify by `material_pair_id` **and** enforce that each unique material identifier (`material_1_id`, `material_2_id`) appears in only one split (custom `GroupShuffleSplit` on the union of material IDs).  
6. **Modeling** – nested CV (outer 5‑fold if n ≥ 100 else 3‑fold; inner same) with `GridSearchCV`; train OLS, Random Forest, Gradient Boosting. OLS serves as baseline for significance testing.  
7. **Evaluation** – compute R², MAE, RMSE on held‑out test set for both targets; store in `results/metrics.json`.  
8. **Power & Significance** – power analysis (data‑driven effect size, fallback d = 0.5); choose paired t‑test or Wilcoxon based on power/n; Bonferroni‑corrected p‑values recorded.  
9. **SHAP Interpretation** – generate SHAP values, global importance bar plot, per‑feature dependence plots for top‑5 features; **report** whether the sign of each important feature matches the physics lookup table; log contradictions.  
10. **Reporting** – compile `results.json` (SSoT for downstream paper) with metrics, p‑values, top‑5 SHAP features, `imputed_fraction`, row‑count, any sign‑consistency flags, and a checksum manifest for all artifacts.  

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
| **Data‑gap (OpenML or NIST unavailable or missing columns)** | Blocking – cannot proceed to modeling. | Phase 0 aborts with explicit `DataAvailabilityError` and exits with a non‑zero status; request a verified open dataset or adjust the specification. |
| **Materials Project API key missing** | Missing material properties → reliance on median imputation, possible performance loss. | Log missing‑rate; if > 30 % of material rows are imputed, raise a warning in `results.json`. |
| **Insufficient sample size (< 200)** | Power < 0.8, may force non‑parametric test; R² targets harder to meet. | Issue warning; proceed with Wilcoxon; note limitation in summary. |
| **Collinearity among roughness descriptors** | Inflated variance, misleading SHAP directionality. | Compute Variance Inflation Factor (VIF); if any VIF > 5, record collinearity warning and avoid interpreting individual coefficients. |
| **Raw profilometry files missing** | Cannot compute `pySurf` descriptors. | Perform KS test on fallback columns; abort if distributions differ (p ≤ 0.05). |

---



