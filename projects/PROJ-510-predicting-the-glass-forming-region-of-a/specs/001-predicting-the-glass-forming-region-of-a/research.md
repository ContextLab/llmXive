# Research: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

## Domain Overview

Glass-forming alloys (amorphous metals) exhibit unique mechanical properties. The ability to form a glass depends on the critical cooling rate (CCR). Predicting CCR from composition is a key inverse design problem. Thermodynamic parameters—mixing enthalpy ($\Delta H_{mix}$), atomic size mismatch ($\delta$), and electronegativity variance ($\sigma_{\chi}$)—are hypothesized to be strong predictors. **Note:** This study is observational. All findings are framed as associational.

## Dataset Strategy

### Verified Datasets
The project relies on **experimental** datasets containing `critical_cooling_rate`.
1. **Primary Source**: `bulk-metallic-glasses/CCR-experimental` (Zenodo).
 - URL: `
 - **Verification**: This URL is listed in the "Verified datasets" block. It contains experimental CCR values for ternary alloys.
 - **Target Variable Check**: The dataset contains `critical_cooling_rate` (K/s).
2. **Fallback Source**: `bmgliterature/CCR-curated` (Figshare).
 - URL: `
 - **Verification**: Curated from literature, contains experimental CCR.

### Data Feability Plan
- **Streaming**: Datasets are CSVs (< 100MB). Full load is safe on sufficient RAM.
- **Filtering**: The script filters for ternary alloys (3 elements) and non-zero CCR.
- **Size**: Target N ≥ 500. If the filtered count < 500 after both sources, the pipeline halts with `DataInsufficiencyError`.
- **Bias Mitigation**: If the dataset is biased towards specific alloy systems (e.g., Zr-based), the `Learning Curve` and `OOB Score` will be used to detect overfitting.

### Data Scarcity & Bias Mitigation
- **Scenario**: If N < 500 after primary and fallback sources.
- **Action**: Halt pipeline. Report "Data Insufficiency". Do not proceed with synthetic data.
- **Rationale**: Statistical power (SC-001) cannot be guaranteed with N < 500.

## Methodology

### Feature Engineering
Descriptors are calculated using `mendeleev` (Periodic Table) for:
1. **Mixing Enthalpy** ($\Delta H_{mix}$): Weighted average of binary enthalpies.
2. **Atomic Size Mismatch** ($\delta$): Standard deviation of **Covalent** radii weighted by composition.
3. **Electronegativity Variance** ($\sigma_{\chi}$): Variance of **Pauling** electronegativity.

*Constraint*: All calculations use standard elemental properties (Pauling, Covalent). No fallbacks.

### Modeling
- **Algorithm**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
- **Validation**: 5-fold Cross-Validation.
- **Split**: 80/20 Train-Test Split (`random_state=42`).
- **Metric**: RMSE (Root Mean Squared Error).
- **Baseline**: Dummy Regressor (mean prediction).
- **Hypothesis Test**: Two-sided paired t-test (`scipy.stats.ttest_rel`) comparing RF RMSE vs. Dummy RMSE (SC-002).

### Causal Inference & Confounding
- **Observational Nature**: The dataset is observational. No randomization exists.
- **Claim Limitation**: All claims are framed as "associational". We cannot claim thermodynamic descriptors *cause* glass formation.
- **Negative Control**: To ensure the signal is not due to dataset artifacts (e.g., element selection bias), the pipeline will:
 1. Shuffle the `critical_cooling_rate` column 10 times.
 2. Retrain the model for each shuffle.
 3. Compare the mean RMSE of the shuffled models to the real model.
 4. **Rejection Criteria**: If the real model's RMSE is not significantly lower (p < 0.05) than the shuffled baseline, the hypothesis is rejected (signal is spurious).

### Sensitivity & Robustness
- **Threshold Sweep**: Binarize CCR at **50 (Low)**, **100 (Medium)**, **150 (High)** K/s. These values are physically grounded in typical cooling rates for bulk metallic glasses vs. crystalline alloys.
- **Stability**: "Negligible margin" is defined as variance < 5% of mean RMSE (SC-003).
- **Collinearity**: Check correlation matrix. If $r > 0.8$, flag and re-run model excluding one feature (US-3).
- **Permutation Importance**: $n=1000$ permutations. P-value < 0.05 for **top-2** features (SC-004).
- **Overfitting Check**: Report `oob_score` and `learning_curve_slope` to verify small sample size (N~500) does not lead to overfitting.

## Compute Feasibility

- **CPU-First**: Random Forest on N=500, K=3 features is trivial for CPU.
- **No GPU Needed**: No deep learning or large transformers.
- **Time**: < 1 hour total runtime.

## Decision/Rationale

- **Why Random Forest**: Handles non-linear relationships between thermodynamics and CCR; robust to outliers; provides feature importance.
- **Why No GPU**: Method is classical ML on tabular data.
- **Data Risk**: If both verified experimental sources lack the target, the project halts. This is a **fatal feasibility flaw** if true, but the plan handles it by failing gracefully rather than fabricating data.
- **Associational Framing**: The report generator will prepend a disclaimer to all "prediction" claims to ensure compliance with FR-006.