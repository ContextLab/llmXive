# Methodology: Cross-Validation and Reproducibility Strategy

This document outlines the statistical validation methodology for the
"Predicting the Impact of Impurity Clustering on Grain Boundary Segregation"
project. It defines the cross-validation procedure, random seed management,
and fallback logic to ensure reproducibility and robustness.

## 1. Random Seed Management

To ensure deterministic reproducibility across all stochastic operations
(data shuffling, model initialization, perturbation application), a single
global random seed is enforced.

- **Source**: The seed is read from `code/config.py` (`RANDOM_SEED`).
- **Default Value**: `42` (unless overridden in the configuration file).
- **Application**:
 - `numpy.random.default_rng(seed)` is used for all NumPy random operations.
 - `sklearn.model_selection` splitters are initialized with the seed.
 - `statsmodels` simulations (if applicable) use the seed.

## 2. Primary Validation Procedure: K-Fold Cross-Validation

The primary method for evaluating model performance is **K-Fold Cross-Validation**.
This approach maximizes data usage while providing an unbiased estimate of
generalization error.

### Procedure
1. **Dataset Splitting**: The processed dataset (containing descriptors and
 segregation energies) is shuffled using the fixed random seed.
2. **Fold Generation**: The data is split into **K=5** non-overlapping folds
 of approximately equal size.
 - **Stratification**: If the dataset contains distinct `alloy_system_id`
 groups, `GroupKFold` is used to ensure that no single alloy system
 appears in both training and testing sets within the same fold. This
 tests the model's ability to generalize to unseen chemical systems.
3. **Iterative Training & Evaluation**:
 - For each fold `i` (from 1 to 5):
 - **Training Set**: Folds `{1,..., i-1, i+1,..., 5}`.
 - **Test Set**: Fold `i`.
 - A Linear Regression model (MVP) is trained on the training set.
 - The model is evaluated on the test set.
 - Metrics (R², RMSE, p-values) are recorded.
4. **Aggregation**: Final metrics are reported as the **mean** and **standard
 deviation** across the 5 folds.

## 3. Fallback Logic: Leave-One-Out Cross-Validation (LOOCV)

In scenarios where the dataset size is insufficient to support 5-fold
cross-validation (i.e., fewer than 5 samples), the procedure automatically
falls back to **Leave-One-Out Cross-Validation (LOOCV)**.

### Trigger Condition
- `if N_samples < 5:`

### Procedure
1. For each sample `j` in the dataset:
 - **Training Set**: All samples except `j`.
 - **Test Set**: Sample `j` only.
 - Train the model and evaluate.
2. **Aggregation**: Metrics are averaged over all `N` iterations.

### Rationale
LOOCV maximizes the training data size for every iteration, providing a
nearly unbiased estimate when data is scarce, albeit at a higher computational
cost (N models trained instead of K).

## 4. Collinearity Handling

Per **FR-007**, feature removal is prohibited during the validation phase.
Instead, collinearity is monitored:

- **Variance Inflation Factor (VIF)** is calculated for all descriptors
 prior to model training.
- If `VIF >= 10` for any feature, a warning is logged, and the collinearity
 report is generated.
- The model proceeds with **raw descriptors**. The instability of p-values
 in the presence of high collinearity is explicitly noted in the results
 but does not alter the feature set.

## 5. Output Artifacts

The execution of this methodology produces the following artifacts:
- `results/metrics_per_fold.json`: Detailed metrics for each fold.
- `results/metrics.json`: Aggregated mean/std metrics.
- `results/confidence_intervals.json`: Prediction intervals for test samples.
- `data/processed/collinearity_report.md`: VIF analysis results.