# Research: Evaluating the Predictive Power of Machine Learning for Identifying Novel High-Entropy Alloy Compositions

## Problem Statement

High-Entropy Alloys (HEAs) offer vast compositional spaces, but experimental and computational characterization is expensive. Machine learning (ML) using compositional descriptors (atomic radius, electronegativity, VEC, melting point) is a promising tool for screening. However, the predictive power of these models in **extrapolation regimes** (novel compositions outside the training manifold) is poorly understood. This study evaluates whether standard descriptor-based models can reliably identify "True Novel" compositions and quantify their own uncertainty when ground truth is unavailable.

## Research Questions

1.  How does the prediction error ($R^2$, MAE) of Random Forest and Gradient Boosting models degrade when moving from interpolation (training set) to extrapolation (Hold-out Known set)?
2.  Can ensemble variance and distance-from-convex-hull metrics serve as reliable proxies for uncertainty in "True Novel" compositions where ground truth is absent?
3.  Is the error distribution on the Hold-out Known set statistically significantly different from the interpolation error distribution?

## Dataset Strategy

The study requires thermodynamic data (formation energy, mixing enthalpy) for multi-component systems.

**Source Selection**:
The study uses the **AFLOW Thermodynamics** dataset (HuggingFace mirror) as the primary source for thermodynamic properties. This dataset contains formation energy and mixing enthalpy, unlike thermal conductivity datasets.

| Dataset Role | Source Name | Verified URL | Usage |
| :--- | :--- | :--- | :--- |
| **Training & Hold-out** | AFLOW Thermodynamics | `https://huggingface.co/datasets/foundry-ml/dataset_thermodynamics_aflow` | Primary source for formation energy and mixing enthalpy. |
| **Novel Generation** | Random Sampling | N/A | Generate random 5+ element combinations. |

**Strategy Details**:
1.  **Ingestion**: Download the AFLOW Thermodynamics parquet file. Filter for entries with $\ge 5$ elements.
2.  **Splitting**:
 * **Training Set**: Random sample ([deferred]) of the filtered data.
 * **Hold-out Known**: The remaining [deferred] (or a specific subset) of the *same* dataset. These exist in the source but are excluded from training.
    *   **True Novel**: Programmatically generate random 5-element combinations. **Query the union** of the `Training Set` and `Hold-out Known` sets. Compositions returning "Not Found" (not in the union) are labeled "True Novel". *Note: "True Novel" is defined as "unindexed in the downloaded AFLOW data" for the purpose of this study's uncertainty analysis, acknowledging the limitation that global novelty cannot be proven without live API access.*
3.  **Data Hygiene**: All downloads are checksummed. No data is modified in place; derived datasets are written to new files.

## Methodology

### 1. Feature Engineering
*   **Library**: `pymatgen` (version pinned in `requirements.txt`).
*   **Descriptors**: Weighted mean and variance of:
    *   Atomic Radius
    *   Electronegativity
    *   Valence Electron Count (VEC)
    *   Melting Point
*   **Handling**: Clamp near-zero variance values to $1e-6$ to prevent division errors.

### 2. Model Training
*   **Algorithms**: `RandomForestRegressor` and `GradientBoostingRegressor` from `scikit-learn`.
*   **Validation**: 5-fold cross-validation on the **Training Set**.
    *   *Rationale*: 5-fold CV is the standard method for model validation in this domain.
*   **Hyperparameters**: Grid search over `max_depth` and `n_estimators` within the CV loop.
*   **Uncertainty Estimation**: Train an **ensemble of 10 independent Random Forest models** with different random seeds. Uncertainty is calculated as the variance of multiple predictions for a given composition.
*   **Compute**: CPU-only execution.

### 3. Evaluation
*   **Interpolation**: $R^2$ and MAE on the 5-fold CV folds.
*   **Extrapolation (Hold-out Known)**:
    *   Predict on the Hold-out set.
    *   Calculate $R^2$ and MAE.
    *   **Statistical Test**: **Permutation Test** comparing the **pooled error distribution** (all individual sample errors from the 5 CV folds) against the error distribution of the Hold-out set.
*   **Extrapolation (True Novel)**:
    *   Predict on the True Novel set.
    *   Calculate **Ensemble Variance** (from the 10-model ensemble).
    *   Calculate **Distance from Convex Hull** (using `scipy.spatial.ConvexHull` on the training descriptor space).
    *   **Fallback**: If the convex hull is degenerate or fails to construct, switch to **Mahalanobis distance** based on the training set's covariance matrix.
    *   **Statistical Test**: **Spearman rank correlation** ($\rho$) between prediction variance and distance from the convex hull. *Note: A positive correlation is expected by construction for random samples outside the hull; the study reports this as a measure of model calibration.*

### 4. Compute Feasibility
*   **CPU-First**: All methods (RF, GB, statistical tests) are CPU-tractable.
*   **Memory**: The AFOW dataset (parquet) is typically < 1 GB. Feature engineering and model training will easily fit within 7 GB RAM.
*   **Time**: k-fold CV on a few thousand samples with RF/GB will complete in minutes, well under the established time limit.

## Decision Rationale

*   **Why AFLOW Thermodynamics?** The "Verified datasets" block explicitly lists the AFLOW thermodynamics dataset on HuggingFace. This dataset contains the required formation energy and mixing enthalpy, unlike thermal conductivity datasets.
*   **Why 5-Fold CV?** Standard method for model validation in this domain.
*   **Why Permutation Test?** Standard t-tests assume normality which may not hold for error distributions. Permutation tests are non-parametric and robust. Using the **pooled** error distribution ensures the two samples being compared are of comparable structure (individual errors vs. individual errors).
*   **Why Spearman Correlation?** The relationship between uncertainty (variance) and distance (convex hull) is likely monotonic but not necessarily linear. Spearman is appropriate for rank correlation.
*   **Why Ensemble Variance?** `scikit-learn` RF does not natively support `return_std`. Training an ensemble of 10 independent models provides a robust, reproducible estimate of prediction variance.

## Limitations

*   **"True Novel" Definition**: "True Novel" is defined as "unindexed in the downloaded AFLOW data," not necessarily "unmeasured in nature" globally. This is a pragmatic limitation for CI reproducibility.
*   **Ground Truth for Novel**: Independent DFT validation for "True Novel" candidates is computationally infeasible within the 6-hour CI window. The study relies on uncertainty metrics (variance/distance) as proxies, acknowledging this as a hypothesis to be tested (SC-005).
*   **Descriptor Sufficiency**: The study assumes standard compositional descriptors are sufficient. If performance is poor, it may indicate the need for more complex descriptors (e.g., structural features), which are out of scope for this phase.
*   **Circularity**: The Spearman correlation between variance and distance is expected to be positive by construction for random samples outside the hull. The study frames this as a **calibration** check rather than a discovery of novelty.