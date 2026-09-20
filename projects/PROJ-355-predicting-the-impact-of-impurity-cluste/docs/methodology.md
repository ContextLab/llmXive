# Methodology: Cross-Validation and Model Evaluation

This document outlines the statistical methodology employed for training and evaluating the regression models in the "Predicting the Impact of Impurity Clustering on Grain Boundary Segregation" project.

## 1. Overview

The primary objective is to predict segregation energies based on clustering descriptors (RDF peaks, pair correlation, Voronoi neighbor counts). Given the likely limited size of the simulated dataset (due to computational cost of energy calculations), a robust cross-validation strategy is essential to assess model generalizability and avoid overfitting.

We employ **k-Fold Cross-Validation** as the primary evaluation protocol, with a fallback to **Leave-One-Out Cross-Validation (LOOCV)** for very small datasets.

## 2. Random Seed and Reproducibility

To ensure strict reproducibility of all random operations (data shuffling, fold splitting, perturbation initialization), a fixed random seed is mandated.

- **Source**: The seed is defined in `code/config.py` under the key `RANDOM_SEED`.
- **Default Value**: `42` (unless overridden in the configuration file).
- **Application**:
 - Used to initialize `numpy.random` and `pandas` shuffling operations.
 - Passed to `sklearn.model_selection.KFold` and `LeaveOneOut` splitters.
 - Used in `code/data/simulate_energy.py` for structural perturbations.

## 3. Cross-Validation Procedure

### 3.1. Primary Strategy: k-Fold Cross-Validation

For datasets with sufficient sample size ($N \ge 5$), we utilize **5-Fold Cross-Validation**.

**Procedure**:
1. **Data Preparation**: The dataset (descriptors $X$, segregation energies $y$) is loaded from `data/processed/`.
2. **Shuffling**: The data is shuffled once using the fixed `RANDOM_SEED` to ensure folds are not biased by the order of insertion.
3. **Splitting**: The data is partitioned into $k=5$ mutually exclusive folds of approximately equal size.
4. **Iteration**: The model (Linear Regression via `statsmodels.api.OLS` with `cov_type='HC3'` for robust standard errors) is trained and evaluated 5 times:
 - In iteration $i$, fold $i$ is held out as the **validation set**.
 - The remaining $k-1$ folds are combined to form the **training set**.
 - The model is trained on the training set.
 - Predictions are made on the validation set.
 - Metrics ($R^2$, RMSE) are computed and stored.
5. **Aggregation**: Final performance metrics are reported as the mean and standard deviation across the 5 folds.

**Rationale**: 5-fold CV offers a good balance between computational efficiency and variance in the performance estimate, reducing the bias inherent in a single train/test split while being less computationally expensive than LOOCV for moderate $N$.

### 3.2. Fallback Strategy: Leave-One-Out Cross-Validation (LOOCV)

For very small datasets ($N < 5$), k-Fold CV (with $k=5$) is not feasible or would result in extremely small training sets. In this case, we switch to **LOOCV**.

**Procedure**:
1. **Iteration**: The process iterates $N$ times (where $N$ is the total number of samples).
2. **Splitting**: In iteration $i$, the $i$-th sample is held out as the validation set, and the remaining $N-1$ samples form the training set.
3. **Training & Evaluation**: The model is trained on $N-1$ samples and evaluated on the single held-out sample.
4. **Aggregation**: Metrics are aggregated across all $N$ iterations.

**Rationale**: LOOCV provides an almost unbiased estimate of the model error (as the training set size is maximized) but has higher variance and computational cost. It is strictly reserved for cases where $N$ is too small for k-Fold.

## 4. Model Training Details

- **Algorithm**: Ordinary Least Squares (OLS) Linear Regression.
- **Library**: `statsmodels.api.OLS`.
- **Covariance Type**: `HC3` (White's heteroskedasticity-consistent standard errors) to ensure valid p-values and confidence intervals even if the assumption of homoscedasticity is violated.
- **Features**: Raw clustering descriptors (RDF, Pair Correlation, Voronoi Count) as per `contracts/dataset.schema.yaml`. PCA is explicitly **not** applied (per FR-007).
- **Collinearity Check**: Before training, Variance Inflation Factor (VIF) is calculated (see `code/data/descriptor_filter.py`). If VIF $\ge 10$, a warning is logged, but training proceeds with raw features to satisfy the "report, don't remove" requirement.

## 5. Metrics and Reporting

The following metrics are computed for each fold and aggregated:

1. **$R^2$ (Coefficient of Determination)**: Measures the proportion of variance in the target variable explained by the model.
2. **RMSE (Root Mean Squared Error)**: Measures the average magnitude of the error in the same units as the target (eV).
3. **P-values**: Extracted from the OLS summary for each coefficient to assess statistical significance of individual descriptors.
4. **Confidence Intervals**: 95% confidence intervals for predictions are calculated using `statsmodels` `get_prediction()` method.

All results are saved to `results/metrics.json` and `results/confidence_intervals.json`.

## 6. Implementation Location

The logic for this methodology is implemented in:
- `code/modeling/train.py`: Contains the `run_kfold_cv` function which handles the splitting logic, seed initialization, and the training loop.
- `code/config.py`: Contains the `RANDOM_SEED` constant.