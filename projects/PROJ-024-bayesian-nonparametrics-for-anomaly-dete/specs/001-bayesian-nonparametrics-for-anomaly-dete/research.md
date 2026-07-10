# Research: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Overview

This research investigates whether the temporal derivative of the concentration parameter ($\dot{\alpha}$) in a Dirichlet Process Gaussian Mixture Model (DP-GMM) serves as a robust early-warning signal for regime shifts in univariate time series. The core hypothesis is that as a system approaches a critical transition, the posterior uncertainty and the rate of change in the number of active components (reflected in $\alpha$) will exhibit distinct signatures compared to benign non-stationarity.

**Critical Methodological Note**: This research employs a "Local DP-GMM" approach where the model is re-initialized at each sliding window step, treating $\alpha$ as a local parameter. The derivative is the difference between independent local estimates. This design choice is explicitly validated against ground truth in Phase 0 to ensure the signal is not an artifact of the variational approximation.

## Theoretical Background

### Dirichlet Process Gaussian Mixture Models (DP-GMM)
A DP-GMM is a nonparametric Bayesian model that allows the number of mixture components to grow with the data. The concentration parameter $\alpha$ controls the expected number of clusters. In a stick-breaking construction, $\alpha$ influences the weights $\pi_k$ of the components.
* **Hypothesis**: In a stationary regime, $\alpha$ is relatively stable. Approaching a regime shift, the model attempts to accommodate new data distributions, causing $\alpha$ to fluctuate or drift. The derivative $\dot{\alpha}$ is hypothesized to spike before the shift is fully realized.
* **Caution**: In small windows (n=30), $\alpha$ is heavily influenced by the prior. The plan includes a simulation study (FR-020) to verify the signal-to-noise ratio of $\dot{\alpha}$ against the null hypothesis to ensure it is not an artifact of the variational approximation.
* **Local DP-GMM**: The sliding window approach treats $\alpha$ as a local parameter by re-initializing the model at each step. The derivative is the difference between independent local estimates, with high variance acknowledged.

### Variational Inference (ADVI)
Automatic Differentiation Variational Inference (ADVI) approximates the posterior distribution by optimizing a variational lower bound (ELBO).
* **Feasibility**: ADVI is significantly faster than MCMC (NUTS) and is the only viable option for running inference on hundreds of sliding windows within the standard GitHub Actions runtime limit on a multi-core CPU.
* **Convergence**: The system must monitor the ELBO delta. If convergence criteria (delta < 0.01 for 10 iterations) are not met within 500 iterations, the window is excluded (FR-009).

## Dataset Strategy

### Verified Datasets
The plan strictly adheres to the "Verified datasets" block. No fabricated URLs will be used.

| Dataset Name | Source/URL | Usage | Verification Status |
|:--- |:--- |:--- |:--- |
| **Synthetic Data** | N/A (Generated) | Primary testing ground for injected anomalies (US-1, US-2). Must include pre-anomaly dynamics (FR-021). | **Verified** (Logic check FR-022). |
| **UCI HAR** | ` | Potential real-world validation (if regime shifts exist). | **Verified** (URL exists). |
| **UCI Shopper** | ` | Potential real-world validation. | **Verified** (URL exists). |
| **DP-GMM Specific** | NO verified source found. | N/A | **Deferred** (FR-017). |
| **PhysioNet** | NO verified source found. | N/A | **Deferred** (FR-017). |

**Strategy**:
1. **Primary**: Use the `synthetic_generator.py` to create datasets with known ground-truth injection timestamps (abrupt shifts, gradual drift, pre-anomaly dynamics). This allows for precise calculation of "time-to-detection" (FR-013).
2. **Secondary**: Attempt to load `UCI HAR` or `UCI Shopper` via `ucimlrepo` or direct HuggingFace loading. If these datasets do not contain clear, labeled regime shifts, the project will proceed with the "Deferred by Design" status for real-world validation (FR-017), focusing on the synthetic validation of the hypothesis.
3. **Negative Control**: Generate a dataset with only benign non-stationarity (e.g., slowly drifting mean) to serve as the baseline for the KS test (FR-014).

### Pre-anomaly Dynamics (FR-021)
The synthetic data generator implements a "critical slowing down" phase before the injection timestamp. This phase is characterized by:
* **Increasing Autocorrelation**: The lag-1 autocorrelation of the time series increases.
* **Increasing Variance**: The variance of the time series increases.
* **Duration**: A defined duration (e.g., -30 time steps) before the injection point.
This ensures the "early-warning" hypothesis is testable, as the model should detect these pre-shift dynamics.

### Data Preprocessing
* **Normalization**: All datasets will be normalized to zero mean and unit variance (FR-001).
* **Windowing**: Sliding window of a defined length, stride 1.
* **Missing Data**: If timestamps are missing, synthetic integer timestamps (0, 1, 2...) will be generated (Edge Case).

## Methodology

### 1. Ground Truth Simulation (FR-020)
* **Purpose**: Validate the ADVI estimator's fidelity before deployment.
* **Mechanism**: Generate synthetic data with known, controlled $\alpha$ dynamics (ground truth).
* **Validation**: Compare ADVI-estimated $\dot{\alpha}$ against the ground truth. Calculate Signal-to-Noise Ratio (SNR).
* **Decision**: If SNR is insufficient, the system flags the metric as invalid and switches to the Fallback Strategy (component weight variance or reconstruction error).

### 2. Core Model: Local DP-GMM with ADVI
* **Implementation**: PyMC 4 with ADVI.
* **Parameters**: Track posterior mean of $\alpha$ and component weights $\pi_k$ for each window.
* **Signal Extraction**: Compute the first derivative $\dot{\alpha}$ (rate of change) and the variance of $\pi$.
* **Validation**: Run a simulation study (FR-020) to confirm $\dot{\alpha}$ is not an ADVI artifact under the null hypothesis.

### 3. Baseline Models
* **Fixed GMMs**: Fit GMMs with $k=3, 5, 10$ on each window. Compute reconstruction error (MSE).
* **ARIMA**: Fit ARIMA on each window. Compute prediction error.
* **Comparison**: Compare the "time-to-detection" of the DP-GMM $\dot{\alpha}$ signal against the reconstruction error thresholds of baselines (US-2).

### 4. Statistical Testing
* **Time-to-Detection**: Calculate steps from injection to threshold crossing.
* **Primary Test**: Wilcoxon signed-rank test (non-parametric) to compare detection times between DP-GMM and baselines (FR-006). Paired t-test is secondary and only if normality is confirmed.
* **Distributional Differences**: Two-sample Kolmogorov-Smirnov (KS) test comparing:
 * Anomaly vs. Negative Control $\dot{\alpha}$ rates (FR-014).
 * Baseline reconstruction errors vs. DP-GMM signature distributions (FR-015).
* **Low Power Handling**: If anomaly count < 10, switch to non-parametric bootstrap resampling for p-values and confidence intervals (FR-011, FR-012).
* **Nested Validation**: The final statistical comparison is performed on a held-out test set that was NOT used for threshold selection or tuning. This prevents Type I error inflation.
* **Degenerate Distribution Check**: Before performing statistical tests, verify that the "time-to-detection" distribution is not degenerate (e.g., all values undefined). If degenerate, flag the result as inconclusive.

### 5. Threshold Sensitivity
* **Sweep**: Test thresholds at {0.01, 0.05, 0.1} on normalized MSE (FR-007).
* **Correction**: Apply Bonferroni correction for multiple comparisons in statistical tests involving threshold sweeps (FR-007b).
* **Validation**: Select threshold on validation set, apply to test set (FR-019).

### 6. Window and Derivative Sensitivity (FR-016)
* **Sweep**: Test window sizes (e.g., small, medium, large ranges) and derivative calculation methods (e.g., finite difference, Savitzky-Golay smoothing).
* **Validation**: Ensure the "rate of change" signal remains robust across these variations.

### 7. MCMC Robustness Check (FR-018)
* **Subset Selection**: Select a small subset of windows (both normal and anomaly) from the dataset.
* **Validation**: Run MCMC (NUTS) on this subset to validate the ADVI-derived $\dot{\alpha}$ signal. Acknowledge small-sample limitations but proceed as a qualitative validation.

### 8. Computational Feasibility
* **Constraints**: 2 CPU cores, 7 GB RAM, 6 hours.
* **Mitigation**:
 * Use CPU-only PyMC (no CUDA).
 * Limit ADVI iterations to a sufficient number to ensure convergence.
 * Sample data if necessary (though a substantial number of points are required, the window size is small).
 * Monitor RAM via `psutil` and fail gracefully if limits are exceeded (FR-008).

## Decision Rationale

* **Why ADVI over MCMC?** MCMC is too slow for the sliding window approach on CPU-only hardware. ADVI provides a tractable approximation that fits the 6-hour runtime constraint.
* **Why Synthetic Data?** Real-world datasets with verified, labeled regime shifts are scarce (FR-017). Synthetic data with injected dynamics (FR-021) allows for controlled testing of the "early-warning" hypothesis and precise ground-truth comparison.
* **Why Bootstrap?** Parametric tests assume normality and sufficient sample size. With potentially <10 anomalies, bootstrap resampling ensures robust inferential testing (FR-011).
* **Why $\dot{\alpha}$?** While $\alpha$ is a global parameter, its *rate of change* in a sliding window is hypothesized to capture the instability preceding a shift. This is a novel contribution requiring rigorous validation (FR-020) to rule out artifacts.
* **Why Local DP-GMM?** Treating $\alpha$ as a local parameter allows for the extraction of temporal derivatives in a sliding window context, which is necessary for the "early-warning" hypothesis.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| ADVI fails to converge | Loss of data points in trajectory | Exclude non-convergent windows (FR-009); log warnings. |
| $\dot{\alpha}$ is noisy/artifact | False positives | **Ground Truth Simulation** (FR-020) to verify SNR; **Fallback Strategy**. |
| Real-world data unavailable | Inability to validate on real regime shifts | Proceed with "Deferred by Design" status (FR-017); focus on synthetic validation. |
| Runtime exceeds 6 hours | CI failure | Optimize window size; reduce ADVI iterations; profile memory usage. |
| Low anomaly count (<10) | Low statistical power | Switch to bootstrap resampling (FR-011). |
| Degenerate detection times | Invalid statistical tests | **Degenerate Distribution Check** before performing tests. |
| Threshold tuning bias | Type I error inflation | **Nested Validation**: Final tests on held-out test set distinct from tuning set. |

## Fallback Strategy

If the Ground Truth Simulation (Phase 0) fails to validate $\dot{\alpha}$ (SNR < threshold):
1. Log a warning: "Primary metric $\dot{\alpha}$ validation failed."
2. Switch to using **Component Weight Variance** or **Reconstruction Error** as the primary metric.
3. Document the fallback in the final report.
