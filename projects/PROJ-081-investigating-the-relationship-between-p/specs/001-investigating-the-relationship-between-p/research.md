# Research: Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance

**Feature**: `001-investigating-plant-metabolite-herbivore-resistance`  
**Date**: 2026-10-26  

## Objective
Quantify how the four plant secondary‑metabolite classes (alkaloids, terpenes, phenolics, benzoxazinoids) associate with herbivore damage, rank predictive biomarkers, and evaluate robustness to analytical choices (standardization, outlier handling, phylogenetic non‑independence). **Because no open, verified paired metabolomics‑herbivory dataset exists, the core scientific question cannot be answered with real data; the pipeline will therefore run on a verified placeholder dataset solely to validate the workflow.** All conclusions will be explicitly framed as methodological demonstrations.

## Decision / Rationale
| Decision | Reasoning |
|----------|-----------|
| **Dataset** | MetaboLights, PMN, HPID have **no verified open source** for paired metabolomics‑herbivory data. The pipeline therefore attempts to download them (with retry logic) but **falls back to the GHZ placeholder dataset** (`https://huggingface.co/datasets/khaoula-ghz/guanaco-llama2-5k/resolve/main/data/train-00000-of-00001.parquet`). This placeholder does **not** contain plant metabolite or herbivory measurements; it is used **only to prove that the end‑to‑end pipeline works**. The final report will contain a prominent disclaimer. |
| **Statistical methods** | Classical OLS, phylogenetic GLS, mixed‑effects, and a shallow Random Forest are fully CPU‑tractable and fit within the 6‑hour runner limit. No GPU is required. |
| **Multiple‑comparison correction** | Benjamini‑Hochberg FDR applied to all correlation and regression p‑values (FR‑006). |
| **Power analysis** | Uses Bonferroni‑adjusted per‑test α (α = 0.05 / total_tests) and a conservative effect size (r≈0.2). If effective N < 50, the study is flagged as exploratory (SC‑001, SC‑005). |
| **Phylogenetic control** | Open Tree of Life provides a species tree; incorporated via PGLS and a mixed‑effects model with species random intercepts (FR‑008). |
| **Feature‑count limit** | Variance‑based selection ensures ≤ 20 predictors (≤ 5 per class) before modeling (FR‑011). |
| **External literature validation** | PlantCyc defense‑metabolite list lacks a verified URL; thus FR‑009 cannot be satisfied. The limitation will be noted in the report. |

## Dataset Strategy
| Source | Verified URL | Loader | Notes |
|--------|--------------|--------|-------|
| MetaboLights (primary) | *no verified URL* | REST API (requests) | Attempted first; retry logic with 3 attempts, 30 s back‑off. |
| Plant Metabolic Network (PMN) (primary) | *no verified URL* | REST API | Attempted second; same retry logic. |
| Herbivore‑Plant Interaction Database (HPID) (primary) | *no verified URL* | REST API | Attempted third; same retry logic. |
| GHZ placeholder (fallback) | `https://huggingface.co/datasets/khaoula-ghz/guanaco-llama2-5k/resolve/main/data/train-00000-of-00001.parquet` | `datasets.load_dataset(..., streaming=False)` | **Used only for methodological validation**; does not contain real plant data. |

> No fabricated URLs are introduced. Required datasets lacking verified sources are explicitly listed as unavailable.

## Power Analysis & Sample Size
1. **Effective N**: Adjusted for phylogenetic signal (λ) after PGLS fitting.  
2. **Multiple‑comparison impact**: Total compound‑level tests from Phase 3 are used to compute an **effective α = 0.05 / total_tests**.  
3. **Target effect size**: Conservative r ≈ 0.2 (small).  
4. **Power estimation**: Conducted with `statsmodels.stats.power` for OLS, PGLS, and RF.  
5. **Under‑power flag**: If effective N < 50, `under_power_flag:true` is set and the study is labelled exploratory.  

## Statistical Methods
| Analysis | Method | Software | Multiple‑Comparison | Power / Sample‑Size |
|----------|--------|----------|----------------------|---------------------|
| Correlation (class & compound) | Pearson r | `scipy.stats.pearsonr` | BH (q < 0.05) | Power estimated in Phase 11 |
| Baseline OLS | Ordinary Least Squares | `statsmodels.api.OLS` | BH on coefficients | Effective N from Phase 11 |
| Phylogenetic GLS | GLS with phylogenetic covariance | `statsmodels.api.GLS` | BH on coefficients; LRT vs OLS | Same N |
| Mixed‑Effects | Random intercept for species | `statsmodels.MixedLM` | BH on fixed effects | Same N |
| Random Forest | `RandomForestRegressor(max_depth=5, n_estimators=200)` | `sklearn` | **No p‑values**; importance reported | CV‑based R² used for power‑like assessment |
| Sensitivity | Threshold sweeps, outlier caps, raw vs. standardized | Custom loops | BH per sweep | Exploratory |

## Expected Outputs
- `data/processed/clean.parquet` – standardized, no‑missing dataset (includes optional `absence_indicator`).  
- `outputs/heatmap.png` – correlation heatmap with significance markings.  
- `outputs/correlation_summary.json` – list of metabolite classes with significant negative q‑values.  
- `outputs/ols_results.json`, `outputs/pgls_results.json`, `outputs/mixed_effects_results.json` – regression diagnostics and performance metrics.  
- `outputs/rf_results.json` – permutation importance rankings + CV / test R², RMSE.  
- `outputs/sensitivity.json` – robustness checks.  
- `outputs/power_analysis.json` – effective N, power estimates, under‑power flag.  
- `outputs/report.md` – human‑readable summary, includes disclaimer about placeholder data and unmet FR‑009.  
- YAML contracts under `contracts/` for the processed dataset and all model outputs.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open paired metabolomics‑herbivory dataset | Biological conclusions impossible | Use GHZ placeholder for workflow validation; clearly label results as methodological only. |
| Memory overflow on large CSVs | Job failure | Stream downloads (`datasets.load_dataset(..., streaming=True)`) and batch‑process ≤ 20 species at a time. |
| API downtime | Incomplete acquisition | 3‑attempt exponential back‑off; fallback to placeholder. |
| Multicollinearity | Inflated variance in OLS | Compute VIF; if VIF ≥ 5, flag and rely on Random Forest rankings. |
| Species missing from phylogeny | Reduced phylogenetic sample | Fuzzy matching; document excluded species; proceed with matched subset. |
| Under‑power (N < 50) | Weak inference | Formal power analysis; flag as exploratory; no causal claims. |
| Lack of verified PlantCyc list (FR‑009) | Missing external validation | State explicitly that no verified source exists; omit overlap calculation. |
| Standardization artifacts | Threat to construct validity | Sensitivity analysis comparing raw vs. standardized results (Phase 10). |

## Implementation Notes
- **Feature selection discipline**: Correlation results are **only for reporting**; all metabolites (or variance‑selected ≤ 20) are entered into every model (FR‑003 compliance).  
- **Random Forest importance**: Reported without p‑values; interpreted qualitatively.  
- **Power analysis**: Uses Bonferroni‑adjusted α and r≈0.2 to provide realistic power estimates.  
- **Contract validation**: Every output file is validated against its JSON schema; any validation error aborts the run.  

---
