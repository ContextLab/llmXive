# Methodology: Cross-Validation and Reproducibility

## Overview
This document defines the statistical validation procedure for the regression models
used to predict the impact of impurity clustering on grain boundary segregation.
The methodology prioritizes reproducibility, statistical robustness, and adherence
to the project's constraint of using real data without synthetic fallbacks.

## 1. Cross-Validation Procedure

### 1.1 Primary Strategy: K-Fold Cross-Validation
The primary validation method is **5-Fold Cross-Validation** (`k=5`).
This approach splits the dataset into 5 equal-sized groups (folds). The model is
trained on 4 folds and validated on the remaining fold. This process is repeated
5 times, ensuring every data point is used exactly once for validation.

**Algorithm:**
1. Shuffle the dataset using the fixed random seed (see Section 2).
2. Partition the data into $k=5$ disjoint sets $F_1, F_2,..., F_5$.
3. For each fold $i$ from 1 to 5:
 - **Training Set**: $\bigcup_{j \neq i} F_j$
 - **Validation Set**: $F_i$
 - Train the Linear Regression model on the Training Set.
 - Compute metrics ($R^2$, RMSE, p-values) on the Validation Set.
4. Aggregate metrics across all 5 folds (mean and standard deviation).

### 1.2 Fallback Strategy: Leave-One-Out Cross-Validation (LOOCV)
If the total number of samples $N$ is less than 5, 5-Fold CV is statistically
unstable or impossible. In this case, the system automatically switches to
**Leave-One-Out Cross-Validation (LOOCV)**.

**Algorithm:**
1. For each sample $x_i$ in the dataset (where $i = 1$ to $N$):
 - **Training Set**: All samples except $x_i$.
 - **Validation Set**: $\{x_i\}$.
 - Train the model on the Training Set.
 - Compute metrics on the single validation sample.
2. Aggregate metrics across all $N$ iterations.

**Decision Logic:**
```python
if N >= 5:
 strategy = "5-Fold CV"
 k = 5
else:
 strategy = "LOOCV"
 k = N
```

## 2. Reproducibility and Random Seeds

To ensure that results are exactly reproducible across different runs and environments,
a single, fixed random seed is used for all stochastic operations.

- **Seed Value**: Defined in `code/config.py` (e.g., `RANDOM_SEED = 42`).
- **Scope of Application**:
 - Dataset shuffling prior to CV splitting.
 - Random perturbations in structural simulations (if applicable).
 - Initialization of any random number generators in modeling libraries.
- **Implementation**:
 All code paths utilizing randomness must explicitly instantiate their generator
 using the configured seed:
 ```python
 import numpy as np
 from config import RANDOM_SEED

 rng = np.random.default_rng(RANDOM_SEED)
 ```

## 3. Metric Definitions

The following metrics are computed for each fold and aggregated:

- **$R^2$ (Coefficient of Determination)**: Measures the proportion of variance
 in the dependent variable (segregation energy) predictable from the independent
 variables (clustering descriptors).
- **RMSE (Root Mean Squared Error)**: Measures the square root of the average
 squared differences between predicted and actual values.
- **P-Values**: Extracted from the t-statistics of the regression coefficients
 (Linear Regression only) to assess the statistical significance of each descriptor.
- **Confidence Intervals**: 95% confidence intervals for predictions, calculated
 using the standard error of the prediction.

## 4. Handling Collinearity

As per project requirements (FR-007), features are **not** removed even if
collinearity is detected.
- **Detection**: Variance Inflation Factor (VIF) is calculated prior to training.
- **Reporting**: If VIF $\ge$ 10, a warning is logged, and the collinearity report
 is generated (`data/processed/collinearity_report.md`).
- **Modeling**: The model proceeds with raw descriptors. P-values are interpreted
 with caution, noting that high collinearity may inflate standard errors.

## 5. Execution Flow

1. **Data Loading**: Load real data from `data/processed/descriptors.csv` and
 `data/processed/segregation_energies.csv`.
2. **Preprocessing**: Verify data integrity and handle missing values (if any).
3. **Split Selection**: Determine if $N \ge 5$ to select CV strategy.
4. **Model Training Loop**: Execute the chosen CV strategy.
5. **Aggregation**: Compute mean and standard deviation of metrics.
6. **Output**: Save results to `results/metrics.json` and `results/metrics_per_fold.json`.