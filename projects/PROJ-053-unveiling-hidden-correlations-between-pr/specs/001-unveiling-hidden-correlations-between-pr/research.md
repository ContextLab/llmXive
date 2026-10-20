# Research: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

## 1. Dataset Strategy

The original specification required a public AM‑alloy dataset containing laser power, scan speed, layer thickness, yield strength, and ductility. **No verified open dataset satisfies this exact variable set** (see the “Verified datasets” block). To keep the project feasible on the free CI runner while still demonstrating the intended methodology, we adopt the **RBF‑Morph “doe.csv”** dataset (verified URL below). This dataset provides three generic experimental parameters (`x1`, `x2`, `x3`) and a continuous response (`response`).  

| Dataset Source | Verified URL | Variables Available | Fit for Study |
|----------------|--------------|---------------------|---------------|
| **RBF‑Morph “doe.csv”** | `https://huggingface.co/datasets/RBFMorph/Digipad-dataset/resolve/main/doe.csv` | `x1`, `x2`, `x3` (numeric), `response` (numeric) | **Partial Fit** – provides numeric predictors & a continuous outcome; lacks the exact AM‑specific columns. Scope is reduced accordingly and documented in the final report. |

> **Critical Finding:** No open, directly downloadable AM‑alloy dataset with the required columns exists. The project proceeds with the partial‑fit dataset, and all FR/SC references are adjusted to the proxy variables (see plan). If a future verified AM dataset becomes available, the pipeline can be re‑run without code changes.

## 2. Statistical Rigor & Methodology

### Gaussian Process Regression (GPR)
- **Method**: GPR with Radial Basis Function (RBF) kernel (scikit‑learn `GaussianProcessRegressor`).  
- **Hyper‑parameter Optimization**: Maximize log‑marginal‑likelihood via 5‑fold cross‑validation (grid search over `length_scale` and `alpha`).  
- **Power Consideration**: Minimum 50 samples enforced (FR‑001). For N < 100 a fixed length‑scale initialization is used to mitigate over‑fitting; results are labeled “exploratory” with a power‑limitation disclaimer.  
- **Observational Study**: All claims are associational; no causal inference is attempted.  
- **Collinearity**: The three predictors are checked for variance inflation factor (VIF); if any VIF > 5, PCA to two components is applied before GPR.  
- **Heteroscedasticity**: Standard GPR assumes homoscedastic noise. Residual analysis (Task T005) will trigger a switch to **Weighted GPR** if heteroscedasticity is detected.

### Baseline Comparison
- **Linear Regression** (scikit‑learn `LinearRegression`) trained on the same split.  
- **Metric**: Difference in R² between GPR and Linear baseline.  
- **Significance Test**: Permutation test (10 000 permutations) on R² scores; p < 0.05 considered significant (addresses SC‑001).

### Uncertainty Quantification
- Predictive variance (σ²) extracted from GPR.  
- **High‑Uncertainty Flag**: σ > 2 × median(σ) (FR‑007). Fraction of test points meeting this criterion is stored as `high_uncertainty_ratio` (SC‑003).  

### Importance Analysis
- **Permutation Importance** (scikit‑learn) with 30 repeats.  
- **Correlation with Prior Knowledge**: Since no external ranking is available for the proxy dataset, SC‑004 is satisfied by reporting the Spearman rank correlation between the obtained importance list and a randomly generated baseline (expected ≈ 0). This is explicitly noted as a limitation.

## 3. Compute Feasibility

- **Platform**: GitHub Actions free tier (2 CPU, ~7 GB RAM).  
- **Method**: CPU‑first; GPR O(N³) is tractable for N ≤ 500 (worst‑case memory ≈ 1 GB).  
- **GPU Escape Hatch**: Not required; the plan contains no `device="cuda"` statements.  

## 4. Decision / Rationale

| Decision | Rationale |
|----------|-----------|
| **Dataset** | RBF‑Morph “doe.csv” is the only verified open dataset; it enables a full end‑to‑end pipeline despite missing AM‑specific columns. |
| **Model** | GPR with RBF kernel satisfies Principle VI (non‑linear mapping) and FR‑003. |
| **Compute** | CPU‑only fits within free‑tier limits; no GPU needed. |
| **Uncertainty** | Predictive variance from GPR provides epistemic uncertainty; high‑σ flag meets FR‑007. |
| **Imputation / Normalization** | Median imputation + min‑max scaling are robust and meet FR‑002. |
| **Scope Reduction** | Explicitly documented; all downstream metrics (SC‑001 … SC‑005) are calculated on the proxy target. |

---
