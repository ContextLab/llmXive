# Research Configuration Documentation

This document details the configurable parameter ranges and methodological choices used in the Bayesian Nonparametrics for Anomaly Detection study (Project PROJ-023). It addresses the deferred specification requirements and clarifies the Bootstrap Confidence Interval (CI) methodology mandated by `plan.md`.

**Note**: This document does not modify `spec.md` or `plan.md` but serves as the authoritative reference for the implementation parameters used in the codebase.

---

## 1. Anomaly Injection Parameters

The anomaly injection pipeline (`code/lib/anomaly_injector.py` and `code/scripts/inject_anomalies.py`) uses the following configurable ranges. These are defined in the configuration files passed to the injector and are subject to the constraints of FR-009.

### 1.1 Mean Shift Anomalies
- **Definition**: A sudden shift in the mean of the time series by a specified number of standard deviations.
- **Configurable Range**: `2.0` to `4.0` standard deviations.
- **Default**: `2.5` standard deviations (per FR-009).
- **Implementation Detail**: The shift magnitude is calculated as `shift = magnitude * series_std`. The sign (positive or negative) is randomized to simulate both spikes and drops.

### 1.2 Variance Spike Anomalies
- **Definition**: A temporary increase in the local variance of the time series.
- **Configurable Range**: `2.0x` to `5.0x` baseline variance.
- **Default**: `3.0x` baseline variance (per FR-009).
- **Implementation Detail**: The noise term is scaled by `sqrt(multiplier)` to achieve the desired variance increase.

### 1.3 Gradual Drift Anomalies
- **Definition**: A linear or polynomial drift in the mean over a specific window.
- **Configurable Range**:
 - **Slope**: `0.01` to `0.1` standard deviations per time step.
 - **Duration**: `10` to `50` time steps.
- **Implementation Detail**: The drift is applied as `drift(t) = slope * t` within the anomaly window.

### 1.4 Anomaly Duration and Frequency
- **Duration Range**: `5` to `15` consecutive time points for point anomalies; `10` to `50` for drift anomalies.
- **Frequency**: Configurable as a percentage of total time steps (default: `5%` of the series).
- **Constraint**: Anomalies are injected with no look-ahead bias; the start index is selected randomly from the valid range.

---

## 2. Bootstrap Confidence Interval Methodology

Per the `plan.md` override, this study prioritizes **Bootstrap Confidence Intervals** over asymptotic normal approximations for metric uncertainty estimation, due to the potential skewness of F1-scores in imbalanced anomaly detection scenarios.

### 2.1 Method Selection
- **Method**: Percentile Bootstrap (non-parametric).
- **Rationale**: The distribution of F1-scores across different anomaly types and magnitudes is often non-normal. The percentile method makes fewer assumptions about the underlying distribution.
- **Reference**: Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*.

### 2.2 Configuration Parameters
- **Number of Resamples (`n_bootstrap`)**: `1000`
- **Confidence Level**: `95%` (Alpha = 0.05)
- **Sampling Strategy**:
 - **Resampling Unit**: Time steps (with replacement) from the original prediction/ground-truth pairs.
 - **Stratification**: Optional stratification by anomaly type (if ground truth labels allow) to ensure representation of rare anomaly classes in resamples.
- **Implementation**:
 - The `code/lib/metrics.py` module implements `calculate_bootstrap_ci`.
 - The `code/scripts/evaluate.py` script invokes this function for all primary metrics (Precision, Recall, F1, AUC-ROC).
 - The output includes the lower bound, point estimate, and upper bound for each metric.

### 2.3 Bonferroni Correction
- **Context**: When comparing multiple methods (Bayesian vs. Baselines) across multiple metrics.
- **Implementation**:
 - The `code/lib/metrics.py` module includes `apply_bonferroni_correction`.
 - Adjusted p-values are calculated as `p_adjusted = min(p_raw * n_tests, 1.0)`.
 - The number of tests (`n_tests`) is determined by the number of pairwise comparisons performed in `evaluate.py`.

---

## 3. Inference and Optimization Parameters

### 3.1 Bayesian Gaussian Process (Sparse VI)
- **Algorithm**: Stochastic Variational Inference (SVI) with Sparse Gaussian Processes.
- **Inducing Points**: Configurable range `10` to `50`. Default: `20`.
- **Kernel**: Matern 3/2 (default) or RBF.
- **Optimization**:
 - **Optimizer**: Adam.
 - **Learning Rate**: `0.01`.
 - **Max Iterations**: `1000` (with early stopping on ELBO stability).
- **Convergence Checks**:
 - **ELBO Stability**: Convergence if the change in ELBO over the last `50` steps is `< 0.01 * |ELBO|`.
 - **Effective Sample Size (ESS)**: Monitored for MCMC fallbacks (if applicable).

### 3.2 Baseline Parameters
- **Shewhart**:
 - **Sigma Limits**: Configurable range `2.5` to `3.5`. Default: `3.0`.
- **CUSUM**:
 - **Drift Parameter (`k`)**: `0.5` (default).
 - **Threshold (`h`)**: Configurable range `4.0` to `6.0`. Default: `5.0`.
- **VAE**:
 - **Latent Dim**: `8`.
 - **Reconstruction Loss**: MSE.
 - **Epochs**: `50`.

---

## 4. Reproducibility and Random Seed

- **Random Seed**: Fixed at `42` for all random number generators (numpy, random, torch if used) to ensure reproducibility.
- **Implementation**: Enforced via `code/lib/utils.py` `set_seed()` function, called at the entry point of all scripts.

---

## 5. Data Provenance and Versioning

- **Dataset Source**: UCR/UCI Time Series Archive (via `code/scripts/download_data.py`).
- **Version Pinning**: All datasets are pinned to specific commit hashes or version tags in `data/PROVENANCE.md`.
- **Checksum Verification**: SHA-256 checksums are verified upon download to ensure data integrity.

---

## 6. Execution Constraints

- **Memory Limit**: `7GB` RAM. Enforced via `tracemalloc` in `code/lib/utils.py` `MemoryProfiler`.
- **Time Limit**: `6 hours` per script.
- **CPU Only**: All inference scripts are configured to run on CPU (no GPU acceleration).

---

## 7. References

1. Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall/CRC.
2. Hultman, G. M., et al. (2019). "Bayesian Nonparametric Anomaly Detection in Time Series." *Journal of Machine Learning Research*.
3. UCR Time Series Archive. https://www.cs.ucr.edu/~eamonn/time_series_data/
4. Plan.md (Project PROJ-023 Constitution).