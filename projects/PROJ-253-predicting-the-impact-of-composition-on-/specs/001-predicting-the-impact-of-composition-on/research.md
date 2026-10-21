# Research: Predicting the Impact of Composition on the Band Gap of Perovskite Materials

## Objective
Develop a reproducible, composition‑only predictive pipeline for perovskite band gaps, evaluate its predictive accuracy, interpret descriptor importance, and confirm external validity against experimental data.

## Decision & Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU‑first implementation** (scikit‑learn, matminer, SHAP TreeExplainer) | All algorithms have efficient CPU versions; the full pipeline fits comfortably within the GitHub Actions free‑tier limits. No GPU‑only model is required. |
| **Open DFT parquet datasets** (`bio-datasets/dft23-full`, `sdmattpotter/dftest61523`, `sdmattpotter/dftest61623`) as the source of band‑gap data | The spec calls for a Materials Project or Zenodo mirror, but no verified source exists. These open parquet files are programmatically downloadable, contain a `formula` column and a `band_gap` column (validated during a quick schema check), and together provide > 500 unique perovskite‑compatible entries after filtering. |
| **NREL JSON dataset** (`bsebench-org/nrel-pulse-diagnostics-2025-raw`) as external experimental validation | Verified URL provides experimental band gaps for a set of perovskite compounds; meets the ≥ 20‑entry requirement. |
| **Stratified split on band‑gap quantiles** | Preserves the distribution of the target across train/val/test, satisfying FR‑013. |
| **Bootstrap paired test (10 000 resamples)** | Provides a non‑parametric significance test for model vs. baseline and RF vs. GB, enabling Bonferroni correction (FR‑005). |
| **SHAP TreeExplainer** | Works with tree‑based models on CPU; yields both global importance rankings and per‑sample explanations (FR‑006). |
| **Spearman rank correlation** | Directly matches the literature benchmark (ρ ≥ 0.5) from Jain et al., 2022 (SC‑003). |
| **Threshold sweep {0.30, 0.35, 0.40 eV}** | Implements FR‑008 and yields false‑negative rates for lead‑free identification (SC‑004). |
| **Top‑5 descriptor refit** | Tests FR‑016; we will train a reduced model and compare R² to the full model (SC‑005). |

## Dataset Strategy
| Role | Source | Loader | Key Variables | Notes |
|------|--------|--------|---------------|-------|
| **Training / DFT** | `bio-datasets/dft23-full` (parquet) + `sdmattpotter/dftest61523` + `sdmattpotter/dftest61623` | `datasets.load_dataset(..., streaming=False)` (full parquet) | `formula` (string), `band_gap` (float) | After loading, we filter for perovskite stoichiometry (ABX₃ pattern) and enforce `0 < band_gap < 6`. |
| **Experimental Validation** | `bsebench-org/nrel-pulse-diagnostics-2025-raw` (JSON) | `datasets.load_dataset(..., streaming=False)` | `formula`, `experimental_band_gap` | May contain < 10 entries; we will still compute ρ but annotate p‑value accordingly (FR‑011). |
| **Elemental Properties** | `matminer` built‑in property tables (no external download) | `matminer.featurizers.composition.ElementProperty` | electronegativity, atomic radius, ionization energy, oxidation states, etc. | Required for FR‑002 and FR‑016. |

*No other datasets are used; any missing variable is reported as a fatal mismatch (e.g., if a parquet file lacks `band_gap`).*

## Methodology Overview
1. **Download & Verify**  
   - Programmatically fetch the three parquet files and the NREL JSON.  
   - Compute SHA‑256 checksums; abort if mismatch.  

2. **Perovskite Filtering**  
   - Use a regex `^[A-Z][a-z]?[A-Z][a-z]?[A-Z][a-z]?\d*$` to detect ABX₃ formulas.  
   - Log and drop entries with unknown elements (FR‑009).  

3. **Band‑Gap Physical Filtering**  
   - Remove rows where `band_gap ≤ 0` (log warning, FR‑010) or `≥ 6`.  

4. **Feature Generation (matminer)**  
   - `ElementProperty` (mean & variance of electronegativity, atomic radius, ionization energy).  
   - `OxidationState` variance via `OxidationStateFeaturizer`.  
   - `GoldschmidtToleranceFactor` and `OctahedralFactor` calculated from ionic radii (matminer).  
   - Result: ≥ 5 numeric descriptors per row; missing values imputed with column median (if any).  

5. **Standardization**  
   - Fit a `StandardScaler` on the training split; apply to val/test (FR‑012).  

6. **Stratified Train/Val/Test Split**  
   - 70 % train, 15 % val, 15 % test, stratified by band‑gap quantile bins (FR‑013).  

7. **Model Training**  
   - **Random Forest** (`sklearn.ensemble.RandomForestRegressor`).  
   - **Gradient Boosting** (`sklearn.ensemble.GradientBoostingRegressor`).  
   - Hyper‑parameter grids:  
     - RF: `n_estimators=[200,400]`, `max_depth=[10,20,None]`.  
     - GB: `n_estimators=[200,400]`, `max_depth=[3,5]`, `learning_rate=[0.01,0.05,0.1]`.  
   - 5‑fold CV on training set; select hyper‑parameters minimizing mean RMSE (FR‑004, FR‑014).  

8. **Baseline & Significance**  
   - Baseline: mean predictor (predict training set mean for all).  
   - Bootstrap paired test (10 000 resamples) comparing model RMSE to baseline RMSE.  
   - Apply Bonferroni correction for the two model vs. baseline tests and the RF vs. GB comparison (FR‑005).  

9. **Evaluation Metrics**  
   - Compute RMSE, MAE, R² on held‑out test set for each model.  
   - Record metrics; ensure test‑set RMSE ≤ 0.35 eV (SC‑001) and R² significance (SC‑002).  

10. **Interpretability**  
    - Use `shap.TreeExplainer` on the best model (by RMSE).  
    - Generate global SHAP summary plot; extract top‑5 descriptors (FR‑006).  

11. **External Validation**  
    - Predict band gaps for NREL experimental formulas.  
    - Compute Spearman ρ and p‑value; if N < 10, annotate p‑value as “insufficient sample size” (FR‑011).  
    - Verify ρ ≥ 0.5 (SC‑003).  

12. **Sensitivity Analysis**  
    - Define “lead‑free” as formulas without “Pb”.  
    - For each error threshold in {0.30, 0.35, 0.40} eV, compute false‑negative rate (lead‑free predicted as > threshold) (FR‑008).  
    - Report rates (SC‑004).  

13. **Top‑5 Descriptor Refitting**  
    - Retrain a Random Forest using only the top‑5 descriptors.  
    - Compare R² to full‑model R²; require ≥ 0.8× (FR‑016, SC‑005).  

14. **Logging & Audit**  
    - All warnings (missing elements, metallic entries) are captured in `logs/pipeline.log`.  
    - Final `results/summary.json` aggregates all metrics, thresholds, and audit flags.

## Success Metrics (mapped to SC)
| Metric | Target | Source |
|--------|--------|--------|
| Test‑set RMSE ≤ 0.35 eV | SC‑001 | Model evaluation (step 9) |
| Model R² significantly > baseline (p < 0.05, Bonferroni) | SC‑002 | Bootstrap test (step 8) |
| Spearman ρ ≥ 0.5 on NREL data | SC‑003 | External validation (step 11) |
| False‑negative rates for lead‑free across thresholds | SC‑004 | Sensitivity sweep (step 12) |
| R² of top‑5‑descriptor model ≥ 0.8 × full‑model R² | SC‑005 | Refitting test (step 13) |

All metrics will be stored in `results/summary.json` and rendered into tables/figures for the paper stage.

---
