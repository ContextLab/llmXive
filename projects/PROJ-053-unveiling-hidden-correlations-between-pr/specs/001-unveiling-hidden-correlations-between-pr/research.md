# Research: Unveiling Hidden Correlations Between Processing Parameters and Mechanical Properties in Additively Manufactured Alloys

## 1. Dataset Strategy

The original specification required a public AM‑alloy dataset containing **laser power, scan speed, layer thickness, yield strength, and ductility**. A systematic search of the verified dataset list reveals **no open dataset that provides this exact variable set**. Consequently, the pipeline is designed to **abort** if the downloaded dataset does not contain the required columns. When a suitable dataset becomes available, the same workflow will be applied without modification.

| Dataset | Verified URL | Variables Present | Fit for Study |
|---------|--------------|-------------------|---------------|
| **Open AM‑Alloy Dataset (to be supplied)** | *pending* | `laser_power`, `scan_speed`, `layer_thickness`, `alloy_composition`, `yield_strength`, `ductility` (and possibly additional covariates) | **Exact Fit** – will satisfy FR‑001 and all downstream FR/SC requirements. |

> **Critical Finding:** No open, directly downloadable AM‑alloy dataset currently satisfies the required columns. The pipeline therefore **cannot be executed** until such a dataset is provided. All FR/SC references are retained but will be evaluated against the forthcoming data.

## 2. Statistical Rigor & Methodology

### Gaussian Process Regression (GPR)
- **Model**: `GaussianProcessRegressor` with an RBF kernel (scikit‑learn).  
- **Hyper‑parameter Optimization**: Grid search over `length_scale` ∈ {0.1, 1, 10} and noise `sigma` ∈ {1e‑10, 1e‑5, 1e‑2}, evaluated via 5‑fold cross‑validation maximizing log‑marginal‑likelihood.  
- **Observational Nature**: All claims are **associational**; no causal inference is attempted.  
- **Power Consideration**: A **bootstrap‑based power analysis** (Task T011) uses the **effective post‑preprocessing sample size** (after any row removal) and the observed variance to estimate the 80 % confidence interval lower bound for the minimum detectable R². This accounts for the higher variance inherent to GPR and avoids the oversimplified fixed‑N estimate.  
- **Collinearity Check**: Variance Inflation Factor (VIF) computed for `laser_power`, `scan_speed`, `layer_thickness`, and any one‑hot encoded alloy flags; any VIF > 5 triggers a warning and, if needed, dimensionality reduction is logged.  
- **Heteroscedasticity**: Residuals are examined with the Breusch‑Pagan test; results are stored in `results/metrics.json` under `residual_analysis`.  

### Baseline Comparison
- **Linear Regression** (`LinearRegression`) trained on the same split.  
- **Metric**: Difference in R² between GPR and baseline; significance assessed via a permutation test (10 000 permutations) on the two R² scores (p < 0.05 considered significant) (addresses SC‑001).  

### Uncertainty Quantification
- Predictive variance (σ²) extracted from GPR.  
- **High‑Uncertainty Flag**: σ > 2 × median(σ) (FR‑007). The fraction of test points meeting this criterion is stored as `high_uncertainty_ratio` (SC‑003).  

### Importance Analysis
- **Permutation Importance** (30 repeats, `random_state=42`).  
- **External Reference Ranking**: Currently **unavailable** for the required variables; therefore SC‑004 cannot be satisfied. The plan records this gap and requests a literature source that ranks processing‑parameter importance for the targeted alloy system. Until such a reference is provided, the raw permutation‑importance scores will be reported without correlation validation.

### Power Analysis (Improved)
- Implements a **bootstrap simulation** (1 000 resamples) on the training data to generate a distribution of achievable R² values under the null hypothesis.  
- Reports the **lower bound of the 80 % confidence interval** as the **minimum detectable R²** and stores this in `results/metrics.json` under `power_analysis`.  
- The analysis explicitly notes the **effective sample size** after preprocessing (rows removed due to missingness or zero‑variance features) and the **observed residual variance**, providing a realistic power estimate for the GPR model.

### Confounder Assessment
- Computes a Pearson correlation matrix among all numeric predictors and the response.  
- Flags any absolute correlation > 0.8 as a potential confounder in `results/confounders.json`.  
- Calculates VIF for each predictor; VIF > 5 is logged as a warning.  
- **Alloy Composition**: If `alloy_composition` is present, per‑alloy R² and subgroup analyses will be performed; otherwise, the assessment is limited to available covariates and the limitation is documented (addresses FR‑009).  

## 3. Compute Feasibility

- **Platform**: GitHub Actions free tier (2 CPU, ~7 GB RAM).  
- **Method**: CPU‑first; all steps (including bootstrap power analysis) are sized to run within the 6 h limit on ≤ 500 samples.  
- **GPU Escape Hatch**: Not required.  

## 4. Decision / Rationale

| Decision | Rationale |
|----------|-----------|
| **Dataset** | No open dataset satisfies the specified functional requirement; the pipeline will abort with a clear error until an appropriate dataset is supplied. |
| **Model** | GPR with RBF kernel satisfies Principle VI (non‑linear mapping) and FR‑003. |
| **Compute** | CPU‑only fits within free‑tier limits; no GPU needed. |
| **Uncertainty** | Predictive variance from GPR provides epistemic uncertainty; the 2 × median rule meets FR‑007. |
| **Power Analysis** | Bootstrap‑based approach yields a realistic detectable R² estimate that accounts for effective sample size and model variance. |
| **Importance Validation** | SC‑004 cannot be satisfied without an external ranking; the requirement is flagged for amendment. |
| **Confounder Handling** | Limited to available numeric covariates; full alloy‑composition control awaits appropriate data. |
| **Scope** | The project is currently on hold pending acquisition of a dataset meeting FR‑001. All downstream analyses are defined and will be executed once the data is available. |

---


