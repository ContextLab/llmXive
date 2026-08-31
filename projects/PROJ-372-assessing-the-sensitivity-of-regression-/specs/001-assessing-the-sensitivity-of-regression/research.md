# Research: Sample Size Tier Rationale

## Objective
This document defines and justifies the fixed sample size tier percentages used in the sensitivity analysis of regression coefficients. These tiers determine the subset sizes generated during the resampling phase (User Story 2) to evaluate how regression coefficient stability varies with data volume.

## Selected Tiers
The following percentage tiers are selected for the study:
`[10, 25, 50, 75, 90]`

## Rationale

### 1. Coverage of the Data Spectrum
The selected tiers provide a non-linear but comprehensive coverage of the dataset size spectrum:
- **10%**: Represents a "small" subset. This is the critical lower bound where statistical power is lowest, and variance due to sampling is highest. It tests the robustness of the model when data is scarce.
- **25%**: Represents a "moderate-small" subset. This tier often marks the transition point where the Central Limit Theorem begins to stabilize estimates for many distributions, but outliers can still exert significant leverage.
- **50%**: Represents a "median" split. This is a standard benchmark for stability testing, offering a balance between computational cost and statistical reliability. It serves as the midpoint for observing convergence trends.
- **75%**: Represents a "large" subset. At this level, the influence of individual outliers should diminish significantly, and the coefficient estimates should approach the asymptotic values of the full dataset.
- **90%**: Represents a "near-full" subset. This tier tests the upper bound of sensitivity. If significant instability remains at 90%, it indicates that the dataset (or the model specification) is inherently unstable regardless of sample size, likely due to multicollinearity or structural violations of OLS assumptions.

### 2. Asymmetry and Edge Case Focus
The tiers are asymmetric (skewed towards higher percentages) rather than evenly spaced (e.g., 20, 40, 60, 80). This design choice is intentional:
- Sensitivity to subset selection is typically non-linear. The most dramatic changes in coefficient stability occur between very small samples (10-25%) and moderate samples (25-50%).
- The "tail" of the distribution (75% to 90%) is critical for detecting subtle instabilities that only emerge when the dataset is nearly complete. A 90% tier allows us to distinguish between "converged" and "asymptotically unstable" models.

### 3. Computational Feasibility vs. Statistical Power
- **Lower Bound (10%)**: Ensures that the resampling loop can run quickly even on large datasets (e.g., >100k rows), allowing for a high number of bootstrap iterations (N=200+) within the 6-hour wall-clock budget.
- **Upper Bound (90%)**: Avoids the computational redundancy of running on 95% or 99% of the data, which yields diminishing returns in terms of new information about stability while increasing compute time linearly.

### 4. Alignment with Statistical Literature
These tiers align with standard practices in bootstrap sensitivity analysis and subsampling literature, where the goal is to observe the "learning curve" of the estimator. The specific intervals allow for the detection of "kinks" or non-monotonic behavior in the variance curve, which would suggest complex interactions between sample size and specific data violations (e.g., heteroscedasticity patterns that only manifest at certain N).

## Implementation
These values are hardcoded as constants in `src/utils/config.py` under `SAMPLE_SIZE_TIERS` to ensure consistency across the ingestion, resampling, and analysis modules.
