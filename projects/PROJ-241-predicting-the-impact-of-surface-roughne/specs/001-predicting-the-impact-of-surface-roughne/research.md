# Research: Predicting the Impact of Surface Roughness on Tribological Properties

**Feature**: `001-predict-tribology`  
**Research Date**: 2026‑10‑11  

## Objective
Create a reproducible end‑to‑end analysis that predicts coefficient of friction and wear rate from surface‑roughness descriptors and material properties, evaluates model performance against predefined success criteria, and supplies interpretable feature‑importance evidence.

## Decision / Rationale
| Decision | Rationale |
|----------|-----------|
| **Compute Platform** | All algorithms (OLS, Random Forest, Gradient Boosting, SHAP) run comfortably on the CPU‑only GitHub Actions runner. No GPU is required; we therefore stay on the CPU path for full reproducibility. |
| **Dataset Strategy** | The spec demands the OpenML dataset ID 42123 and material properties from the NIST Materials Data Repository. No verified download URL for either source is present in the “Verified datasets” block, and The OpenML dataset referenced does not contain the required columns. Consequently, the pipeline **first performs a Data‑Availability Assessment (Phase 0)**. If the dataset cannot be fetched, the pipeline aborts with a clear “data‑gap” error and the project owner must provide an alternative open, verified dataset. |
| **Statistical Methods** | Since we evaluate two targets, we apply Bonferroni correction to the two p‑values (model vs baseline for each target). Power analysis uses `statsmodels.stats.power.TTestPower` with effect size ΔR² = 0.10, α = 0.05 (two‑tailed). If power < 0.8 or n < 200, we use the Wilcoxon signed‑rank test per FR‑010. |
| **Model Validation** | Group‑split by material identifiers ensures no material appears in both train and test sets (Constitution VI). Nested CV (outer + inner folds) provides unbiased performance estimates and prevents optimistic bias. |
| **Interpretability** | SHAP (TreeExplainer for RF/GB, KernelExplainer for OLS) will produce global importance plots and per‑feature dependence plots. We will compare the sign of each SHAP mean effect with known physical expectations (e.g., hardness ↘ wear rate). Discrepancies will be logged and highlighted. |
| **Reproducibility** | Random seeds (`numpy`, `sklearn`) are set to a fixed value for reproducibility. All external data are checksummed (`sha256`) and stored under `data/raw/`. |

## Dataset Strategy
| Source | Verified URL | Loader | Notes |
|--------|--------------|--------|-------|
| **OpenML “Surface Roughness & Tribology”** (ID 42123) | *None provided in verified list* | `openml.datasets.get_dataset(42123, download_all_files=True, streaming=True)` | Public OpenML API; will be attempted. If unavailable, pipeline aborts with “data‑gap”. |
| **NIST Materials Data Repository** | *None provided in verified list* | – | No verified source; material properties will be fetched via the Materials Project API when possible; otherwise median‑imputed. |
| **Materials Project API** | Requires API key (not publicly available) | `pymatgen.ext.matproj.MPRester` | Attempted; if key missing or request fails, fallback to median imputation. |

*Only the OpenML API is considered a genuine open source; the other two are noted as unavailable.*

## Methodology Sketch
1. **Data Acquisition** – Phase 0 verifies downloadability; Phase 1 streams the OpenML dataset.  
2. **Feature Extraction** – Requires raw profilometry files; `pySurf` computes Sa, Sq, Ssk, Sku, Sp, Sv. If raw files are missing, the pipeline aborts with an informative error (no silent fallback).  
3. **Material Property Retrieval** – For each `material_id`, query Materials Project; if no response, log and impute median.  
4. **Cleaning** – Robust outlier removal using the IQR method (1.5 × IQR) for each numeric feature (addresses non‑Gaussian roughness distributions). <br>• Median imputation for any remaining missing values. <br>• `StandardScaler` on all numeric columns.  
5. **Splitting** – **Group split** by material identifiers (`material_1_id` + `material_2_id`) using `GroupKFold` (ensuring no leakage). Random seed = 42.  
6. **Modeling** – Nested cross‑validation: outer CV (3‑fold if n < 100 else 5‑fold) for unbiased performance; inner CV (same fold count) for hyper‑parameter tuning via `GridSearchCV`. Train OLS, Random Forest, Gradient Boosting on the full training set with best hyper‑parameters. Exclude derived fields (`avg_hardness`, `avg_modulus`, `hardness_modulus_ratio_avg`) from predictor set.  
7. **Evaluation** – Compute R², MAE, RMSE on held‑out test set for each target. Record metrics in `results/metrics.json`.  
8. **Power & Significance** – Power analysis (effect size = 0.10, α = 0.05) → choose paired t‑test if power ≥ 0.8 and n ≥ 200, otherwise Wilcoxon signed‑rank test. Apply Bonferroni correction for the two targets; store p‑values.  
9. **SHAP Interpretation** – Generate SHAP values, produce global importance bar plot (`figures/shap_importance.png`) and per‑feature dependence plots for the top‑5 features. Validate directionality against physical expectations; flag any contradictions.  
10. **Reporting** – Assemble a JSON summary (`results/summary.json`) containing metrics, p‑values, top‑5 features, and any flagged discrepancies. This file serves as the **SSoT** for downstream paper generation.

## Success Criteria Mapping
| SC | Metric | Target | Implementation Check |
|----|--------|--------|-----------------------|
| SC‑001 | R² (friction) | ≥ 0.7 | `results/metrics.json['r2_friction']` |
| SC‑002 | R² (wear) | ≥ 0.7 | `results/metrics.json['r2_wear']` |
| SC‑003 | p‑value (model vs baseline) | α = 0.05 (Bonferroni‑adjusted) | `results/metrics.json['p_value']` |
| SC‑004 | # of features with mean |SHAP| > 0.01 | Count in SHAP summary |
| SC‑005 | Total runtime | ≤ 6 h | Measured via CI logs; abort if exceeded |

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Data‑gap (OpenML unavailable)** | Blocking – cannot proceed to modeling. | Early gate (Phase 0) aborts with clear error; request alternative open dataset or provide verified URL. |
| **Materials Project API key missing** | Missing material properties → imputation may degrade performance. | Median imputation fallback, log missing‑rate; if > 30 % missing, flag for dataset revision. |
| **Insufficient sample size (< 200)** | Power < 0.8, may force non‑parametric test; R² targets harder to meet. | Issue warning; proceed with Wilcoxon; note limitation in `results/summary.json`. |
| **Collinearity among roughness descriptors** | Inflated variance, misleading SHAP directionality. | Compute VIF; if VIF > 5, report collinearity in `results/summary.json` and avoid interpreting individual coefficients. |

---

