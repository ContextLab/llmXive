# Research: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

## Executive Summary

This research aims to predict the `critical_cooling_rate` (CCR) of ternary alloys using thermodynamic descriptors derived from the **MatsSci-Glass** experimental dataset. The core hypothesis is that mixing enthalpy, atomic size mismatch, and electronegativity variance are predictive of glass-forming ability. The study will employ a Random Forest regressor, validated via 5-fold cross-validation, to establish associational links between these descriptors and CCR.

## Dataset Strategy

### Verified Datasets
The following datasets are verified and used for this project. **No other URLs are used.**

| Dataset Name | Verified URL | Usage | Notes |
|--------------|--------------|-------|-------|
| MatsSci-Glass | `https://huggingface.co/datasets/matsci/glass-forming-ability` | Primary Data Source | Contains ternary alloy entries with experimental `critical_cooling_rate` (K/s). Verified to contain >1000 records with non-null CCR. |

### Data Availability & Feasibility
- **Source**: The MatsSci-Glass dataset is a public Hugging Face repository. The verified URL is a direct programmatic access point suitable for CI runners.
- **Feasibility**: The dataset is lightweight (<50 MB). It fits comfortably within the RAM limit of the GitHub Actions runner.
- **Gap Handling**: The dataset is verified to contain `critical_cooling_rate`. If the column is missing (contradicting verification), the pipeline will raise a `DataAvailabilityError` (FR-001) and halt. No synthetic data will be generated.
- **Streaming**: Not required for this dataset size; full load into RAM is feasible.

## Methodological Rigor

### Statistical Approach
- **Model**: Random Forest Regressor (scikit-learn).
- **Validation**: 5-fold cross-validation on an 80/20 train-test split.
- **Metric**: Root Mean Squared Error (RMSE).
- **Baseline Significance**: **Permutation Test**. The null hypothesis (no relationship between features and CCR) is tested by shuffling the `critical_cooling_rate` labels [deferred] times and re-computing the RMSE for each permutation. The observed model RMSE is compared against this null distribution to derive a p-value. This avoids the invalidity of t-tests on CV folds vs a scalar null.
- **Multiple Comparisons**: Not applicable for the primary regression metric, but permutation importance (n=1000) will use a permutation test to establish p < 0.05 significance for feature rankings.
- **Causal Claims**: **None**. The study is observational. All results will be framed as "associational" (FR-006).
- **Collinearity**: A correlation matrix will be computed. Pairs with |r| > 0.8 will be flagged. The model will be re-run excluding one of the collinear features to verify stability (US-3).

### Power & Sample Size
- **Target**: N ≥ 1000 (minimum N ≥ 500).
- **Justification**: Based on standard power analysis for Random Forests in materials science (e.g., detecting an R² effect size of ~0.3 with 80% power at alpha=0.05), a sample size of 500 is the minimum threshold for stable performance. The verified dataset contains >1000 records, satisfying this requirement.
- **Limitation**: If the verified dataset yields < 500 valid entries after filtering (unlikely), the study will report a power limitation and fail the SC-001 gate. No synthetic data will be generated.

### Measurement Validity
- **Descriptors**: Mixing enthalpy, atomic size mismatch, and electronegativity variance are standard thermodynamic descriptors in materials science.
- **Source**: Elemental properties (atomic radius, electronegativity, etc.) will be sourced from the `mendeleev` library, a validated periodic table database, ensuring measurement validity.
- **Target Variable**: `critical_cooling_rate` is an experimentally measured kinetic property. The dataset source (MatsSci-Glass) is verified to contain these experimental values.

## Compute Feasibility

### CPU-First Strategy
- **Hardware**: GitHub Actions Free Tier (multi-core CPU, moderate RAM).
- **Method**: Random Forest on a dataset of moderate size and dimensionality is computationally trivial for CPU. No GPU is required.
- **Scaling**: If the dataset is larger (e.g., with a substantial number of rows), the plan will sample a random subset (fixed seed) to ensure execution within 6 hours, noting the power limitation.
- **GPU Escape Hatch**: Not required for this specific model (Random Forest) and dataset size.

## Decision Rationale

- **Why Random Forest?**: Handles non-linear relationships between thermodynamic descriptors and CCR, robust to outliers, and provides feature importance rankings (US-2, US-3).
- **Why MatsSci-Glass?**: It is the only verified dataset in the input block that contains `critical_cooling_rate` for ternary alloys. OQMD was rejected because it only contains equilibrium thermodynamic data (formation energies), not kinetic CCR.
- **Why CPU?**: The model complexity and dataset size fit comfortably within CPU constraints. Using a GPU would be an unnecessary overhead and complexity.