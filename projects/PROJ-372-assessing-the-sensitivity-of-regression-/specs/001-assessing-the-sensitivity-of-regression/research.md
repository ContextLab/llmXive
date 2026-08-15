# Research Rationale: Sample Size Tier Selection for Regression Sensitivity Analysis

## Overview

This document defines the rationale for the fixed sample size tier percentages used in the regression coefficient sensitivity analysis pipeline. These tiers are hardcoded in `src/utils/config.py` as `SAMPLE_SIZE_TIERS = [10, 25, 50, 75, 90]` and are utilized by the resampling engine (`src/resampling/engine.py`) to generate random observation subsets for stability estimation.

## Selected Tiers: [10%, 25%, 50%, 75%, 90%]

The selection of these five specific percentage tiers is driven by the need to balance statistical power, computational feasibility, and the resolution of the sensitivity curve across the full spectrum of dataset utilization.

### 1. Statistical Resolution and Curve Fitting

To accurately characterize the relationship between sample size and regression coefficient stability (variance), a minimum of five data points is required to fit a non-linear decay curve (typically following a power law or inverse-square relationship) with sufficient confidence.

- **10%**: Represents the **low-data regime**. This tier tests the limits of the model where high variance is expected. It is critical for identifying the "elbow" point where the model transitions from unstable to stable. If the coefficient variance at 10% is already low, the dataset is robust even with sparse data.
- **25%**: Represents the **early-stability regime**. This tier captures the initial rapid decay in variance as sample size increases. It helps distinguish between models that stabilize quickly versus those requiring larger samples.
- **50%**: Represents the **mid-point**. This is the median tier, providing a baseline for comparison. It is the standard "half-sample" cross-validation split often used in literature, serving as a reference anchor for the sensitivity curve.
- **75%**: Represents the **high-data regime**. This tier tests the asymptotic behavior of the variance. At this level, the variance should be significantly reduced, and the curve should begin to flatten. It verifies that the model is not overfitting to small subsets.
- **90%**: Represents the **near-full-data regime**. This tier is crucial for detecting subtle instabilities that only appear when the sample is very large but not complete. It ensures that the "stability" observed at 100% is not an artifact of the specific full dataset composition.

### 2. Computational Feasibility vs. Granularity

The project operates under strict computational constraints (CPU-only, ~7GB RAM limit for streaming).

- **Exponential vs. Linear**: A linear progression (e.g., 10%, 20%, 30%...) would provide uniform granularity but requires more runs to cover the same range. A logarithmic progression (e.g., 10%, 30%, 70%) might miss critical transition zones. The chosen geometric-like progression (10, 25, 50, 75, 90) offers the best trade-off, providing high resolution where the variance changes most rapidly (low N) and sufficient coverage at high N.
- **Run Count**: With 5 tiers, the total number of resampling iterations remains manageable (5 tiers × N subsets per tier). This ensures the full experiment can complete within the 6-hour wall-clock budget defined in `quickstart.md` without sacrificing the ability to plot a meaningful sensitivity curve.

### 3. Alignment with Statistical Power Analysis

In regression analysis, the standard error of the coefficient estimates scales approximately as $1/\sqrt{n}$.

- The jump from **10% to 25%** represents a 2.5x increase in $n$, theoretically reducing standard error by $\approx 37\%$.
- The jump from **50% to 90%** represents a 1.8x increase, reducing standard error by $\approx 25\%$.
- This distribution ensures that the experiment captures distinct "steps" in the error reduction curve, allowing us to empirically verify the theoretical $1/\sqrt{n}$ scaling in the presence of real-world data violations (heteroscedasticity, multicollinearity).

### 4. Replacement of Deferred Values

Prior to this task, the sample size tiers were marked as `[deferred]` in `spec.md`. This document explicitly resolves that ambiguity. The values `[10, 25, 50, 75, 90]` are now fixed for this implementation cycle to satisfy **FR-003** (Sample Size Tier Configuration).

## Implementation Details

- **Configuration**: These values are defined as a constant list in `src/utils/config.py`.
- **Usage**: The `src/resampling/engine.py` module reads this configuration to determine the target subset sizes for each iteration of the resampling loop.
- **Constraint**: The resampling engine must ensure that the absolute number of samples at the 10% tier is sufficient for the model to converge (typically $n \ge 10 \times p$, where $p$ is the number of predictors). If a dataset is too small to support a 10% tier meeting this constraint, the engine must raise a `ValueError` rather than falling back to synthetic data or skipping the tier silently.

## Conclusion

The selection of `[10, 25, 50, 75, 90]` provides a scientifically rigorous, computationally efficient, and statistically robust framework for assessing the sensitivity of regression coefficients to dataset subset selection. It allows the pipeline to generate a high-fidelity sensitivity curve that can distinguish between stable and unstable regression models across the full range of data availability.