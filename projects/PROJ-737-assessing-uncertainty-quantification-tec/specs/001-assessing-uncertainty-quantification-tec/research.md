# Research: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

## Problem Statement
How do Gaussian‑process regression, Monte‑Carlo dropout, deep ensembles, and conformal prediction differ in calibration error and prediction‑interval sharpness when applied to machine‑learning models that predict materials properties such as **Band Gap**, **Thermal Conductivity**, and **Formation Energy** (proxy for Elastic Modulus)?

## Dataset Strategy

The plan relies on three specific materials property datasets. Per the `# Verified datasets` block, the following sources are used.

| Property | Target Dataset (Verified Source) | URL / Loader | Notes on Variable Fit |
|:--- |:--- |:--- |:--- |
| **Band Gap** | **OQMD** | ` | Contains `band_gap` target. Features likely include composition. **Fit**: Good. |
| **Thermal Conductivity** | **AFLOW** | ` | Contains thermal conductivity target. **Fit**: Good. |
| **Elastic Modulus (Proxy)** | **OQMD (Formation Energy)** | ` | **Critical Gap**: No verified URL explicitly provides "Elastic Modulus". The verified OQMD dataset contains `formation_energy_per_atom`. **Decision**: Substitute "Elastic Modulus" with "Formation Energy" to maintain N=3 datasets. This changes the research scope slightly but preserves the comparative methodology. |

**Dataset Variable Fit Assessment**:
- **OQMD (Band Gap)**: Verified to have `band_gap` target. Features are composition-based. **Fit**: Good.
- **AFLOW (Thermal Conductivity)**: Verified to have thermal conductivity target. **Fit**: Good.
- **OQMD (Formation Energy)**: Verified to have `formation_energy_per_atom`. **Fit**: Good for a fundamental property comparison.
- **Elastic Modulus**: No verified source. **Mitigation**: Use Formation Energy as the third property. The research question is interpreted as comparing UQ robustness across *fundamental material properties* rather than specifically Elastic Modulus.

## UQ Methodology

### 1. Gaussian Process Regression (GPR)
- **Approach**: Standalone model.
- **Implementation**: `sklearn.gaussian_process.GaussianProcessRegressor` with RBF kernel.
- **Feasibility**: O(N^3) complexity. **Constraint**: Must limit dataset to ≤ 2,000 samples. If N > 2000, downsample or use `SparseGaussianProcess` (if available in sklearn).
- **Output**: Mean and Variance (σ²). Prediction Interval = Mean ± 1.96 * σ.

### 2. Monte Carlo (MC) Dropout
- **Approach**: Apply dropout at inference time to a baseline neural network.
- **Baseline**: A small Multi-Layer Perceptron (MLP).
- **Feasibility**: Requires multiple forward passes (e.g., 50 passes). CPU-only is fine for small MLPs.
- **Constraint**: Model must be small (< 2M params) to fit in memory alongside the ensemble.
- **Output**: Mean and Variance of 50 predictions.

### 3. Deep Ensembles
- **Approach**: Train K independent models (K=3) with different seeds.
- **Baseline**: Same small MLP as MC Dropout.
- **Feasibility**: Training 3 models sequentially. Inference is K forward passes.
- **Constraint**: Must reduce ensemble size to 3 to stay within 2GB RAM during training.
- **Output**: Mean and Variance of K predictions.

### 4. Split-Conformal Prediction
- **Approach**: Train a baseline model (e.g., XGBoost), calculate non-conformity scores on a calibration set, and determine quantile for the prediction interval.
- **Feasibility**: Very low compute cost.
- **Constraint**: Requires a hold-out calibration set (10-20% of data).
- **Output**: Prediction Interval [L, U] such that P(Y ∈ [L, U]) ≥ 1-α.

## Statistical Analysis Plan

### Significance Testing (FR-004, SC-001) - **CORRECTED**
- **Test**: **Paired Wilcoxon Signed-Rank Test** (non-parametric) or Paired t-test.
- **Unit of Analysis**: **Per-sample prediction errors** (or interval widths) across the test set.
- **Rationale**: All methods are evaluated on the **same test set**. Therefore, the errors are **paired** (dependent), not independent. The previous "independent-sample" logic was a category error.
- **Procedure**:
 1. For each method, calculate the per-sample error (or interval width) for every sample in the test set.
 2. Compare the distribution of these per-sample values between Method A and Method B using the Wilcoxon Signed-Rank test.
 3. This provides N > 1 observations (one per test sample) for the test, satisfying statistical requirements.
- **Correction**: No multiple-comparison correction is applied *within* the test (as per FR-004), but the plan will report the number of tests run.

### Sensitivity Analysis (FR-005, SC-004)
- **Method**: Sweep Conformal Prediction nominal coverage (α) from 0.80 to 0.99 in steps of 0.01.
- **Metric**: Plot/Report Average Interval Width vs. Coverage Error.

## Compute Feasibility & Constraints

- **RAM Limit**: 2 GB.
 - **Strategy**: Limit dataset to [deferred] samples per property.
 - **Deep Ensembles**: Train 3 models sequentially.
 - **GPR**: Use `sklearn` with `alpha` regularization; if N > 2000, downsample.
- **Time Limit**: 1 hour.
 - **Strategy**: Parallelize dataset loading (if possible) but serialize training to manage memory.
 - **Fallback**: If a method fails (e.g., GPR convergence), log error and skip to next method.

## Assumptions & Risks

- **Assumption**: `matminer` can be installed and run on CPU without GPU dependencies.
- **Risk**: If `matminer` fails or requires heavy dependencies, fallback to simple composition features (e.g., atomic number counts) using `pandas`.
- **Risk**: Elastic Modulus data not found in verified sources.
 - **Mitigation**: Use Formation Energy (OQMD) as the third property. This is documented as a scope adjustment.
- **Risk**: GPR underfitting due to N=2000 cap.
 - **Mitigation**: Use kernel approximation or strict N cap; acknowledge potential bias in results.
