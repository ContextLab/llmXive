# Research: Predicting the Diffusion Coefficient of Hydrogen in Metals from Compositional and Microstructural Descriptors

## Decision / Rationale
*Compute Feasibility*: All heavy algorithms have mature CPU‑only implementations. The 2‑hour Bayesian budget and a bootstrap with a large number of iterations (now using fixed hyperparameters) are bounded. If the full dataset exceeds memory, the pipeline automatically falls back to a reduced‑sample subset (Phase 6). No GPU is required.

*Dataset Availability*: No verified open‑source hydrogen diffusion dataset containing the required descriptors is available. To ensure the project is executable and the methodology is verified, we will **generate a synthetic benchmark dataset**. The project's goal is shifted to **methodological validation**: demonstrating that the proposed non‑linear pipeline can recover known interactions and provide stable estimates.

*Methodological Rigor*:
- **Nested Cross‑Validation** (5‑fold outer, inner Bayesian) provides unbiased performance estimates.
- **Multiple‑Comparison Control**: Holm‑adjusted p‑values for pairwise RMSE differences.
- **Power Analysis** *(new)*: After model training, we will compute the effect size (Cohen’s f²) for the interaction terms by comparing variance explained by the best non‑linear model to that of the linear baseline. Using `statsmodels.stats.power.FTestPower`, we will conduct a post‑hoc power analysis with α = 0.05 and the observed sample size (≈200). The achieved power will be reported; if it falls below 0.8, we will note the limitation and the wider confidence intervals.
- **Observational Framing**: All findings are stated as associations per the “Methodological Framing” assumption.
- **Confounding Analysis**: To ensure interaction importance is not an artifact of linear correlation, we will compute the correlation matrix between all microstructural proxies and the target $\log_{10}(D)$ before training. High correlations will be reported to contextualize the $\Delta R^{2}$ gain of non‑linear models.
- **Collinearity Awareness**: Variance inflation factors (VIF) will be reported for compositional descriptors.

## Synthetic Benchmark Design
To avoid trivial predictability, the synthetic diffusion coefficient $D$ will be generated as:
$$\log_{10}(D) = \beta_0 + \sum \beta_i X_i + \sum \gamma_{jk} (X_j \times X_k) + \epsilon$$
where:
- $X_i$ are the descriptors (electronegativity, radius variance, proxies, temperature).
- $\gamma_{jk}$ are pre‑defined interaction coefficients (e.g., `radius_variance` × `grain_boundary_density`).
- $\epsilon$ is additive Gaussian noise ($\sigma \approx 0.2$) to ensure the model must actually learn the signal.
- All predictor variables are sampled from distributions mimicking typical metal properties.

An **independent external synthetic test set** (80 samples, seed = 999) is generated with the same generative model but independent random draws. This set is held out for out‑of‑sample validation, addressing the constitutional claim that non‑linear interactions explain >70 % of variance.

## Dataset Strategy
| Role | Source | Access Method | Variable Coverage |
|------|--------|---------------|-------------------|
| **Primary diffusion data** | Synthetic Benchmark (seeded `42`). | `numpy.random` generation; saved as Parquet. | All required columns (`diffusion_coefficient`, `mean_electronegativity`, `atomic_radius_variance`, `free_volume_proxy`, `grain_boundary_density`, `temperature`). |
| **External validation set** | Synthetic Benchmark (seeded `999`). | Same generation pipeline, separate file. | Same schema as primary, never used in training or CV. |
| **Compositional properties** | Materials Project API (public). | `mp_api` Python client (cached locally). | Provides electronegativity & atomic radius per element. |
| **Microstructural proxies** | Literature‑derived linear formulas. | Pure Python functions. | Independent of diffusion measurements (Principle VII). |

## Statistical Methods
- **Target Transformation**: $\log_{10}(D)$ for variance stabilization.  
- **Model Families**: `xgboost.XGBRegressor`, `sklearn.ensemble.RandomForestRegressor`, `sklearn.linear_model.LinearRegression`.  
- **Hyper‑parameter Search**: Optuna `TPESampler`; objective = mean outer‑fold RMSE on $\log_{10}(D)$; time budget = 2 h.  
- **Performance Metrics**: RMSE, $R^{2}$ on $\log_{10}(D)$; Holm‑adjusted p‑values.  
- **SHAP Interaction**: `shap.TreeExplainer(...).shap_interaction_values`. Ranked by absolute mean interaction magnitude.  
- **Bootstrap**: For $b = 1,\dots,1000$: resample rows with replacement, refit full nested pipeline (using best hyper‑parameters), re‑calculate SHAP interactions, and perform ablation on a held‑out slice. Compute 95 % CI quantiles for top‑5 importances.  
- **External Validation**: After hyper‑parameter selection, the best non‑linear model is evaluated on the external synthetic test set. RMSE, $R^{2}$, and variance explained are reported. We explicitly test whether the variance explained exceeds the constitutional >70 % threshold and record the outcome.  
- **Power Analysis**:  
  1. Compute effect size $f^{2} = \frac{R^{2}_{\text{non‑linear}} - R^{2}_{\text{linear}}}{1 - R^{2}_{\text{non‑linear}}}$.  
  2. Use `statsmodels.stats.power.FTestPower().solve_power(effect_size=f2, df_num=..., df_denom=..., alpha=0.05)` (df derived from model degrees of freedom) to obtain achieved power.  
  3. Log the power value; if `< 0.8`, flag limited sensitivity and note wider bootstrap CIs.  
- **Resource Monitoring**: `psutil.virtual_memory().used` polled every 30 s; threshold = 6 GB. Wall‑clock via `time.perf_counter()`; abort hooks at 5 h 55 m. Fallback to 150‑sample subset if limits approached.

## Resource Monitoring
- **RAM**: `psutil.virtual_memory().used` polled every 30 s; threshold = 6 GB.  
- **Wall‑clock**: `time.perf_counter()`; abort hooks at 5 h 55 m.  
- **Fallback**: Random seed‑controlled 150‑sample subset.  

## Expected Deliverables
- CSV/Parquet tables: `model_performance.parquet`, `interaction_terms.parquet`, `bootstrap_ci.parquet`, `external_validation.parquet`, `power_analysis.parquet`.  
- Figures: `rmse_comparison.png`, `shap_interaction_heatmap.png`, `bootstrap_feature_importance_violin.png`, `external_validation_plot.png`, `power_analysis_plot.png`.  
- Markdown summary linking each SC to a concrete measurement, including a post‑hoc power analysis result and external validation outcome (specifically testing the >70 % variance claim).  

