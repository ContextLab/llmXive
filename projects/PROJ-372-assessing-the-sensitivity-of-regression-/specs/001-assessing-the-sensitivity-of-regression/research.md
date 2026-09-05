# Research: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

## Overview
This research validates the feasibility of the statistical methodology and identifies specific, open datasets that satisfy the project's constraints: purely numerical, sufficient sample size for subset resampling, and publicly downloadable without authentication.

## Dataset Strategy

The project requires datasets that:
1. Are purely numerical (or easily castable) to run OLS without complex encoding.
2. Have $N \ge 1000$ to allow meaningful subset resampling (Tier 1 = 10% still yields N>=100).
3. Are available via a programmatic loader (HuggingFace `datasets` or `ucimlrepo`) to ensure CI reproducibility.
4. Contain multiple predictors to allow for multicollinearity checks.
5. Have a **continuous numerical target variable** suitable for OLS regression.

### Verified Datasets
The following datasets have been verified for availability, format, and target variable type. Only these sources will be used.

| Dataset Name | Source URL | Loader | Suitability |
|:--- |:--- |:--- |:--- |
| **California Housing** | `https://huggingface.co/datasets/huggingface-datasets/california_housing` | `datasets.load_dataset` | **High**. Continuous target (`MedHouseVal`), numerical predictors, N=20k. Ideal for OLS. |
| **Delaney Solubility** | `https://huggingface.co/datasets/moleculenet/delaney` | `datasets.load_dataset` | **High**. Continuous target (`pIC50`), molecular descriptors, N=~1k. High collinearity expected. |
| **UCI Wine Quality (Red)** | ` | `pandas.read_csv` | **High**. Continuous target (`quality`), chemical predictors, N=~1600. |

*Note: `DatasetProfile` is a project artifact, not an external dataset. No URL is cited for it.*

**Dataset Selection Rationale**:
- **California Housing**: Chosen for its large size and clear continuous target, ensuring stable OLS fits even at the [deferred] tier.
- **Delaney Solubility**: Chosen for its high dimensionality and expected multicollinearity, providing a stress test for coefficient stability.
- **Wine Quality**: Chosen as a standard regression benchmark with moderate size and known chemical predictors.
- **Excluded**: UCI HAR (categorical target), UCI Census Income (categorical target), and UCI DROP (ambiguous target/URL) were excluded as they do not support OLS regression without violating assumptions or requiring synthetic target generation.

## Methodology Validation

### 1. OLS Assumption Profiling (Per Subset)
To address measurement error and circularity concerns, violation metrics are calculated **on each subset**, not the full dataset.
- **Multicollinearity**: Measured via **Condition Number** of the design matrix $X$ for the subset.
- **Heteroscedasticity**: Measured via **Breusch-Pagan** test on the subset residuals.
- **Outliers**: Measured via **Cook's Distance** on the subset.
- **Profile Generation**: These metrics are calculated for every subset (a fixed number per tier) and stored alongside the coefficient SD. This ensures the predictors and target are derived from the same data realization.

### 2. Resampling Strategy
- **Tiers**: [deferred], [deferred], [deferred], [deferred], [deferred] of $N$.
- **Iterations**: 200 random subsets per tier.
- **Convergence**: The Standard Error (SE) of the Standard Deviation (SD) of coefficients across the 200 subsets must be **< 7%** of the SD.
 - $SE_{SD} = \frac{SD}{\sqrt{2 \times (200 - 1)}} \approx \frac{SD}{20} = 0.05 \times SD$.
 - **Revised Requirement**: $SE_{SD} / SD < 0.07$.
 - **Rationale**: The theoretical limit for N=200 is [deferred]. Requiring < 5% is mathematically impossible for a normal distribution. A threshold of 7% provides a realistic buffer for non-normality while still ensuring the SD estimate is stable.
 - **Verification Logic (Hard Gate)**: If the ratio exceeds 7%, the results for that tier are marked "Unverified" and **excluded** from the final stratified analysis and stability curves. This satisfies the spec's requirement to "verify" as a condition for inclusion.

### 3. Stratified Stability Analysis (Replaces Meta-Analysis)
Due to insufficient degrees of freedom for a regression with interaction terms on N=3 datasets, the methodology has been updated:
- **Unit of Analysis**: Individual subsets (N=200 per dataset per tier), not datasets.
- **Binning**: For each dataset and tier, subsets are binned by their calculated violation severity (Low/Medium/High) based on the subset-level metrics (BP p-value, CondNum, Cook's D).
- **Comparison**: The mean coefficient stability (SD) is compared across these bins using the **Kruskal-Wallis H-test** (non-parametric) to detect if violation severity significantly impacts stability.
- **Visualization**: Stability curves will plot the mean SD (with confidence intervals) for each severity bin.
- **Goal**: Estimate the magnitude of the relationship between violation severity and stability without relying on impossible interaction regressions. Findings are strictly **associational** and descriptive of the specific datasets analyzed.

## Compute Feasibility

- **CPU-First**: All operations (OLS, BP test, resampling) are linear algebra operations in `numpy`/`scipy` or `statsmodels`. No GPU required.
- **Memory**: The largest dataset (California Housing) is ~20k rows. Even with 200 subsets, we process them sequentially or in small batches. Memory usage will be < 2 GB.
- **Time**: 3 datasets * 5 tiers * 200 subsets = 3,000 OLS fits. On a 2-core CPU, a single OLS fit on 2k rows takes < 1 second. Total time is well within the project's time limit..

## Risks & Mitigations

- **Risk**: Datasets lack a continuous numerical target variable.
 - **Mitigation**: Selected datasets (California Housing, Delaney, Wine Quality) are confirmed to have continuous targets.
- **Risk**: [deferred] tier is too small for stable OLS (N < 30).
 - **Mitigation**: California N=20k -> 10% = 2,000. Delaney N=1k -> 10% = 100. Wine N=1.6k -> 10% = 160. All are sufficient.
- **Risk**: Convergence check fails (SE > 7%).
 - **Mitigation**: The pipeline will exclude the tier from the final analysis and log the failure. This ensures only verified results contribute to the scientific claims.
- **Risk**: Stratified analysis lacks power.
 - **Mitigation**: With N=200 subsets per tier, we have sufficient power to detect differences in stability across severity bins using non-parametric tests. The unit of analysis is now the subset, not the dataset.