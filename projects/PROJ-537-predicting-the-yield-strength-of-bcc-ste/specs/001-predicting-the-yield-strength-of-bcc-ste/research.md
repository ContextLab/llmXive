# Research: Predicting the Yield Strength of BCC Steels from Compositional Data and Density Functional Theory

## 1. Problem Statement & Research Questions

**Primary Question**: Does the inclusion of DFT-derived elastic constants (Shear/Bulk Modulus) significantly improve the prediction of yield strength in BCC Fe-alloys compared to a composition-only model?

**Hypotheses**:
- $H_0$: There is no significant difference in predictive performance (MAE) between the DFT-enhanced Random Forest model and the composition-only baseline.
- $H_1$: The DFT-enhanced model has a significantly lower MAE than the baseline.

**Statistical Approach**: Due to the non-independence of k-fold cross-validation errors, we will use **Nested Cross-Validation** to generate independent test set predictions. The comparison of model performance will be performed using a **Wilcoxon signed-rank test** on the paired errors from the outer loop hold-out sets, as this non-parametric test is robust to the dependence structure and does not assume normality of the error differences.

## 2. Dataset Strategy

### 2.1 Data Sources & Verification

The project requires two distinct data types: experimental yield strength and DFT elastic constants.

| Data Type | Source Description | Verified URL / Loader | Status |
|:--- |:--- |:--- |:--- |
| **Experimental Yield Strength** | MatNavi / NIST Materials Data Repository. Contains BCC Fe-alloy compositions and yield strength values. | **Verified Source**: MatNavi (NIMS) - [] (Iron and Steel Database). The system will query the specific BCC Fe-alloy subset. | **Verified**: Accessible via web portal and API. |
| **DFT Elastic Constants** | Materials Project API. Pre-computed bulk/shear modulus. | **Verified Source**: Materials Project API via `mp_api` loader. Endpoint: `. The system will query by composition and filter for BCC structure. | **Verified**: Programmatic loader `mp-api` connects to the official, verified API. |
| **Fallback Datasets** | None. The spec explicitly forbids synthetic data. | N/A | **Not Applicable**: If the verified sources yield < 20 rows, the system halts. |

**Decision**: The implementation will proceed by fetching data from the **canonical public sources** (MatNavi and Materials Project API) as mandated by the spec. The specific URLs and loaders listed above are the verified sources. If these sources are unreachable or do not yield the required BCC Fe-alloy data (n < 20), the system will halt with `ERR_INSUFFICIENT_DATA`.

### 2.2 Data Integration Plan

1. **Fetch Experimental**: Parse data from MatNavi. Extract `composition`, `yield_strength_MPa`.
2. **Fetch DFT**: Query Materials Project API for each unique composition. Filter for `space_group_number == 229` (BCC). Extract `bulk_modulus`, `shear_modulus`.
3. **Merge**: Join on chemical formula.
4. **Filter**: Remove rows with null DFT data.
5. **Validate**: Check row count $\ge 20$. If not, raise `ERR_INSUFFICIENT_DATA`.

### 2.3 Statistical Power & Sample Size

- **Target**: $n \ge 20$ (Spec requirement).
- **Power Analysis**: The plan includes a calculation of statistical power (1 - $\beta$) for the Wilcoxon signed-rank test (FR-009).
- **Effect Size Estimation**:
 - **Primary**: Estimate Cohen's d (or rank-biserial correlation for Wilcoxon) from prior literature on BCC steel yield strength prediction.
 - **Secondary**: If literature is unavailable, perform a pilot run on a small set of valid samples (if available) to estimate the effect size.
 - **Tertiary**: Use a conservative estimate (d=0.5) if no pilot data exists.
- **Limitation**: With $n=20$, power to detect small effect sizes is low. The report will explicitly state if power < 0.8.

## 3. Methodology

### 3.1 Feature Engineering

- **Composition Features**: One-hot encoding of elemental presence; atomic fraction of each element.
- **DFT Features**: `shear_modulus_GPa`, `bulk_modulus_GPa`.
- **Target**: `yield_strength_MPa`.
- **Collinearity Check**: Calculate Variance Inflation Factors (VIF) for all predictors. If VIF > 5, the plan will report multicollinearity and use Partial Dependence Plots (PDP) to assess the unique contribution of DFT features beyond composition.

### 3.2 Modeling Approach

- **Algorithm**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
- **Rationale**: Handles non-linear relationships, robust to outliers, provides built-in feature importance.
- **Validation**: **Nested Cross-Validation** (5-outer, 5-inner) to ensure unbiased performance estimation and valid statistical comparison.
- **Baseline**: Random Forest using only composition features.
- **Comparison**: **Wilcoxon signed-rank test** on the paired MAE errors from the outer test sets. This addresses the non-independence of k-fold errors.

### 3.3 Interpretability & Stability

- **TreeSHAP**: Used to explain individual predictions and global feature importance (FR-006).
- **Permutation Importance**: To validate SHAP results.
- **Bootstrap Stability**: Resample the **FULL dataset** (n) with replacement (10 iterations) to calculate the standard deviation of feature importance (FR-007).
 - *Correction*: Downsampling to n=10 is rejected as it introduces artificial instability. Full-dataset resampling assesses the true variance of the estimator.
- **Threshold Check**: Explicitly check if `std_dev < 0.05` for key DFT descriptors and report a boolean `is_stable` (SC-005).

## 4. Compute Feasibility

- **Hardware**: 2 CPU, 7 GB RAM.
- **Memory**: Random Forest on $n \approx 20-50$ and $p \approx 30$ features is negligible (< 500 MB). Nested CV increases runtime but remains well within the 6-hour limit.
- **Time**: Nested CV (5x5) + Bootstrap (10 runs) + SHAP on small dataset < 2 hours.
- **Dependencies**: `scikit-learn`, `shap` (CPU version), `pandas`, `mp-api` are lightweight and run efficiently on CPU.

## 5. Risk Assessment

- **Risk**: Materials Project API rate limits or unreachable.
 - **Mitigation**: Exponential backoff retry (with a configurable multiplier). If total valid rows < 20, halt.
- **Risk**: Insufficient BCC Fe-alloy data in public repositories.
 - **Mitigation**: System halts with `ERR_INSUFFICIENT_DATA` as per spec. No synthetic data.
- **Risk**: Low statistical power due to small sample size.
 - **Mitigation**: Explicitly report power calculation and limitations in final output.
- **Risk**: Multicollinearity between composition and DFT features.
 - **Mitigation**: VIF analysis and PDP to isolate unique contribution; report if DFT adds no independent value.