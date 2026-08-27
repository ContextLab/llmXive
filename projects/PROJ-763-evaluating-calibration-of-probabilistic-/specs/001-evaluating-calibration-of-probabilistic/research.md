# Research: Evaluating Calibration of Probabilistic Weather Forecasts

## Summary of Research

This research investigates the calibration of probabilistic weather forecasts, specifically targeting the SubseasonalRodeo dataset or verified equivalents. The core problem is that raw ensemble forecasts (e.g., from NOAA GFS) are often systematically biased or over/under-confident. The proposed solution involves a two-tiered recalibration strategy: a robust non-parametric method (Isotonic Regression) and a more complex, physics-aware method (Bayesian Hierarchical Logistic Regression). The research validates these methods against proper scoring rules (Brier, CRPS) and statistical significance tests (Diebold-Mariano).

**Data Feasibility Warning**: No verified public URL was found for the SubseasonalRodeo dataset containing `probability_value` fields. The pipeline will halt with a "Data Unavailability Report" if no suitable data source is found. If `ensemble_members` are available, probabilities may be derived, but this is not guaranteed to match the required distribution.

## Dataset Strategy

The project relies on probabilistic forecast data. The primary target is the **SubseasonalRodeo** dataset. However, as per the verified search results, **no direct public URL** for the full SubseasonalRodeo dataset containing `probability_value` fields was found.

**Strategy**:
1. **Primary Attempt**: Use `datasets.load_dataset("subseasonal_rodeo")` if available on Hugging Face Hub.
2. **Fallback (Verified Sources)**: If the specific Rodeo dataset is unavailable, the pipeline will attempt to construct the required data from the **verified NOAA/GFS sources** listed below.
 * **NOAA Buoy Data**: ` (Used for verification of observation alignment).
 * **GFS Ensemble Data**: ` (Contains GFS ensemble members).
 * *Note*: The implementation strictly enforces the presence of `probability_value` OR `ensemble_members` fields. If neither exists, the "Data Availability Gate" triggers a halt.

| Dataset Name | Source Type | Verified URL | Usage |
|:--- |:--- |:--- |:--- |
| SubseasonalRodeo | HF Dataset | (None found) | Primary target. If missing, check for `probability_value` in fallbacks. |
| NOAA Buoy | Parquet | ` | Ground truth observations (if Rodeo missing). |
| GFS Ensemble | ZIP/Parquet | ` | Forecast ensembles (if Rodeo missing). |

**Data Availability Gate**:
The pipeline includes a mandatory check: `if 'probability_value' not in dataset.columns and 'ensemble_members' not in dataset.columns: raise DataAvailabilityGateError("NO_PROB_DATA")`. This prevents the project from proceeding with binary data only, which would invalidate the Brier/CRPS calculations required by the spec.

## Statistical Methodology

### 1. Calibration Metrics
* **Brier Score**: $BS = \frac{1}{N} \sum (f_i - o_i)^2$. Used for binary events (e.g., precipitation > 1mm). Computed per lead time.
* **CRPS**: Continuous Ranked Probability Score. Used for continuous variables (e.g., temperature). Measures the integrated difference between the forecast CDF and the observation CDF.
* **Reliability Diagrams**: Visualizes the relationship between forecast probability bins and observed relative frequencies. A perfectly calibrated forecast lies on the 45-degree line.
* **PIT Histograms**: Probability Integral Transform. For a well-calibrated forecast, the PIT values should be uniformly distributed.

### 2. Recalibration Methods
* **Isotonic Regression**: A non-parametric, monotonic mapping $f(x) \to \hat{p}$. It preserves the rank order of forecasts but corrects the probability scale.
 * *Validation*: Blocked/Expanding window split to prevent look-ahead bias.
 * *Sensitivity*: Tested with 60/40, 70/30, 80/20 splits.
* **Bayesian Hierarchical Logistic Regression**:
 * *Model*: $\text{logit}(p_{i,t,s}) = \alpha_s + \beta_t \cdot \text{raw\_prob}_{i,t,s} + \epsilon$.
 * *Hierarchical Priors*: $\alpha_s \sim \mathcal{N}(\mu_\alpha, \sigma_\alpha)$, $\beta_t \sim \mathcal{N}(\mu_\beta, \sigma_\beta)$ with $\mu_\beta < 0$ (decay).
 * *Physics Constraint*: Priors on $\beta_t$ are structured to decay with lead time $t$, reflecting the degradation of forecast skill.
 * *Inference*: MCMC (NUTS) via PyMC.
 * *Control*: 'Flat Prior' model (no decay) to test for prior dominance.

### 3. Statistical Testing
* **Diebold-Mariano (DM) Test**: Compares the predictive accuracy of two competing forecasts.
 * *HAC Estimators*: Used to account for autocorrelation in forecast errors.
 * *Decision*: If Shapiro-Wilk test on error differences fails ($p < 0.05$), switch to Wilcoxon Signed-Rank test.
 * *Rank-Preserving Control*: Compare Isotonic against a 'Rank-Preserving Calibration' baseline.
* **Convergence Diagnostics**: R-hat $\le 1.05$ for all parameters.
* **Bootstrap**: Stratified bootstrap (1000 iterations) for sparse events.

## Decision Rationale

* **Why Isotonic First?** It is computationally cheap, non-parametric, and robust. It serves as a strong baseline.
* **Why Bayesian Hierarchical?** It allows "borrowing strength" across lead times and seasons.
* **Why CPU-First?** The GitHub Actions free tier has no GPU. The Bayesian model is scaled down.
* **Why Streaming?** The full subseasonal dataset may exceed available RAM capacity.

## Limitations & Assumptions

* **Data Availability**: The project assumes `probability_value` or `ensemble_members` fields exist. If not, the project halts.
* **Causal Claims**: The study is observational.
* **Computational Limits**: The Bayesian model is constrained by a timeout.
* **Sparse Events**: For lead times with very few events, pooling or global fit is used.
* **Prior Dominance**: The 'Flat Prior' control ensures improvements are not artifacts of the prior.