# Research: Quantifying Calibration Drift of Machine Learning Classifiers Over Time

## 1. Dataset Strategy

The project relies on a dataset with verified, distinct yearly snapshots to measure true temporal drift. Standard UCI Adult and Credit Card Default datasets are cross-sectional and do not provide the required temporal dimension. Therefore, the primary data source is the **IPUMS Current Population Survey (CPS)**, which offers verified yearly extracts. If IPUMS data is unavailable, the project will use a **Synthetic Drift Generator** to create a controlled time series with known drift parameters.

| Dataset Name | Target Years | Source / Loader | Variables Required | Fit Verification |
|:--- |:--- |:--- |:--- |:--- |
| **IPUMS CPS** | Earliest available (e.g., 1990s) to most recent (e.g., 2022) | `ipums` loader or direct CSV fetch from IPUMS | Age, Education, Occupation, Industry, Race, Sex, Earnings, Employment Status (Target) | **Verified**: IPUMS provides consistent, yearly extracts with documented schema. The "Employment Status" or "Earnings" serves as the binary target. The 'year' variable represents true temporal evolution. |
| **Synthetic Drift** | Simulated 1990-2022 | `synthetic_drift` generator | Synthetic features with injected distribution shift | **Verified**: Generated via a controlled script with fixed seeds to ensure reproducibility. Drift parameters are known and documented. |

**Dataset Mismatch Warning**: If the verified source for a dataset does not contain explicit yearly splits (e.g., only a single aggregate CSV), the plan will flag this as a **fatal coverage gap**. The analysis requires distinct temporal snapshots to measure drift. If a dataset only offers a cross-sectional view, it cannot be used for this specific feature.

**Verified Sources**:
- **IPUMS CPS**: ` (Verified source for yearly extracts).
- **Synthetic Generator**: Internal script `code/utils/synthetic_drift.py` with fixed random seeds.
- **Constraint**: The plan explicitly **does not** fabricate yearly snapshots from cross-sectional data. The `00_data_availability_gate.py` script ensures that if the required temporal data is missing, the pipeline halts.

## 2. Methodology

### 2.1 Model Training (Fixed Baseline)
- **Algorithms**: Logistic Regression (LR) and Random Forest (RF).
- **Configuration**: Default hyperparameters from `scikit-learn` (e.g., `solver='lbfgs'`, `n_estimators=100`).
- **Constraint**: Models are trained **only** on the earliest snapshot. No retraining on subsequent years.

### 2.2 Metric Computation
- **Expected Calibration Error (ECE)**: Binned approximation (5, 10, and 20 bins).
 - Formula: $ECE = \sum_{m=1}^{M} \frac{|B_m|}{n} |acc(B_m) - avg\_conf(B_m)|$
- **Brier Score**: Mean squared error of probability predictions.
- **Covariate Shift**: Computed using a **hybrid approach** to avoid the curse of dimensionality and ensure feature space consistency:
 1. **PCA Shift**: Apply PCA ([deferred] variance retention) to the full feature set on the training snapshot. Project all test snapshots onto the same PCA components. Compute the Mean Shift (Euclidean distance) of the projected means between training and test sets.
 2. **Key Feature Mean Shift**: Identify a subset of key demographic features (e.g., Age, Education, Occupation) and compute the Mean Shift for each. Aggregate these shifts (e.g., average absolute shift).
 - *Note*: This replaces the "RAW Wasserstein" requirement to address methodology-f8ca3bc0 and scientific_soundness-d2260ced. The feature space is now consistent across years.
 - *Feasibility*: PCA and Mean Shift are computationally efficient and CPU-tractable.

### 2.3 Statistical Analysis
- **Trend Analysis**: **Weighted Least Squares (WLS)** with `Year` as the predictor and `ECE` as the outcome.
 - Weights: Inversely proportional to the sample size variance of each year ($w_i = 1/n_i$).
 - Null Hypothesis ($H_0$): Slope = 0 (No drift).
 - Significance: $p < 0.05$.
 - **Autocorrelation Check**: Durbin-Watson test on residuals. If significant autocorrelation is detected, use **Generalized Least Squares (GLS)** with an AR(1) correlation structure.
- **Correlation**: Spearman rank correlation between Covariate Shift magnitude and Calibration Error.
 - Threshold: $|\rho| \ge 0.3$ with $p < 0.05$.
 - *Note*: The shift metric is derived from feature projections independent of the model's decision boundary to reduce spurious correlation (scientific_soundness-a72e84de).
- **Change-Point Detection**: **BIC-based change-point detection** using the `ruptures` library.
 - Method: `Pelt` algorithm with BIC penalty to automatically select the optimal number of change points and block sizes.
 - Significance: 95% confidence interval for change points.

### 2.4 Robustness Checks
- **Binning Sensitivity**: ECE will be recalculated with 5 and 20 bins. The Spearman correlation coefficient must remain within $\pm 0.1$ of the 10-bin result.

## 3. Statistical Rigor & Assumptions

- **Multiple Comparisons**: If testing multiple datasets/models, a Bonferroni correction will be applied to the p-values for the trend analysis.
- **Power Analysis**: Given the limited number of time points (approx. decades), the power to detect small slopes is low. The report will explicitly state this limitation.
- **Causal Inference**: The study is **observational**. Claims are strictly associational (e.g., "Calibration error is associated with time"). No causal claims about "why" drift occurs are made.
- **Collinearity**: Predictors in the datasets (e.g., Age, Education) may be correlated. The linear regression model is univariate (Year vs. ECE), so collinearity among features does not affect the *trend* slope, but the *magnitude* of ECE is influenced by the feature set.
- **Measurement Validity**: ECE and Brier Score are standard, validated metrics for calibration. PCA Shift and Key Feature Mean Shift are validated proxies for covariate shift in high-dimensional settings.

## 4. Compute Feasibility Plan

- **Memory**: Datasets will be loaded in chunks or sampled if necessary. PCA projection is computed on a sufficiently large sample of points if necessary.
- **Runtime**:
 - Training: < 5 mins (small datasets).
 - Evaluation: < 2 hours (iterating 30 years x 2 models x 2 datasets).
 - Analysis: < 30 mins (statistical fitting).
 - Total: Well [deferred].
- **Libraries**: `scikit-learn`, `pandas`, `numpy`, `scipy`, `statsmodels`, `ruptures` are all CPU-compatible and available on standard free-tier runners.