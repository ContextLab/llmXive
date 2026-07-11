# Research: Bayesian Nonparametrics for Anomaly Detection in Time Series

## 1. Problem Statement & Hypothesis

**Hypothesis**: The rate of change of the concentration parameter ($\dot{\alpha}$) in a time-varying Dirichlet Process Gaussian Mixture Model (DP-GMM) serves as a robust early-warning signal for regime shifts in time series, detectable before the posterior distribution of component weights fully converges to the new regime.

**Research Question**: Does the DP-GMM dynamic signature ($\dot{\alpha}$, $\text{Var}(\pi)$) detect anomalies significantly earlier than static baselines (fixed GMM, ARIMA) while maintaining low false-positive rates under gradual drift?

## 2. Dataset Strategy

The system will utilize **synthetic data** for primary hypothesis testing (due to the need for precise ground-truth injection timestamps and pre-anomaly dynamics) and **verified real-world datasets** for generalizability checks.

### 2.1 Synthetic Data Generator
- **Purpose**: Generate univariate time series with controlled regime shifts (abrupt, gradual, point anomalies) and explicit pre-anomaly dynamics (increasing variance, changing autocorrelation) as required by FR-021.
- **Validation**: FR-022 requires verification of injected statistics against expected values before use.
- **Ground Truth**: Injection timestamps are independent of model inference.

### 2.2 Real-World Datasets (Verified Sources Only)
Per the `# Verified datasets` block and FR-017, the system will attempt to load:
- **NAB (Numenta Anomaly Benchmark)**:
 - URL: `
 - Search Keywords: "NAB anomaly detection ground truth", "NAB time series regime shift".
- **PhysioNet MIT-BIH Arrhythmia**:
 - URL: ` (or verified HuggingFace mirror)
 - Search Keywords: "PhysioNet MIT-BIH arrhythmia ground truth", "ECG regime shift detection".

**Note**: If no verified source contains a known regime shift suitable for the specific "early-warning" hypothesis, the system will output a **"Validation Deferred"** report citing the search query and result count (FR-017b). **NO fabricated URLs** will be used.

## 3. Methodology & Statistical Rigor

### 3.1 Model Architecture & Mathematical Definition
- **DP-GMM**: Stick-breaking construction with a **time-varying prior** on $\alpha$: $\alpha_t \sim \text{Normal}(\alpha_{t-1}, \sigma_\alpha)$.
- **Interpretation**: In this modified regime, $\alpha_t$ is a **local latent state** per window, not a global hyperparameter. $\dot{\alpha}$ represents the rate of change of this local state.
- **Null Hypothesis**: To distinguish prior-induced drift from data signal, we run a simulation on null data (known $\alpha$) to subtract the prior-induced derivative component from the observed $\dot{\alpha}$.
- **Inference**: ADVI (Automatic Differentiation Variational Inference) for speed on CPU.
- **Convergence**: ELBO delta < 0.01 over 10 iterations within 500 max iterations (FR-009). Non-convergent windows are excluded.
- **Robustness Check**: MCMC (NUTS) run on a subset of windows (e.g., 50 highest variance) to validate ADVI results (FR-018). **Bias Quantification**: We will explicitly measure the bias between ADVI and MCMC estimates for $\dot{\alpha}$ and $\text{Var}(\pi)$.

### 3.2 Baselines
- **Fixed GMMs**: k=3, 5, 10.
- **ARIMA**: Auto-selected order on sliding windows.
- **Metric**: Reconstruction error (MSE).

### 3.3 Statistical Testing
- **Time-to-Detection**: Wilcoxon signed-rank test (primary) and paired t-test (secondary) on detection steps. **Censoring**: For windows where no detection occurs, we use **Survival Analysis (Kaplan-Meier)** to handle censored data, avoiding the skewness violation of standard Wilcoxon.
- **Distributional Differences**: Two-sample Kolmogorov-Smirnov (KS) test for:
 - Anomaly vs. Normal window signatures (FR-010).
 - Transient anomalies vs. gradual drift (FR-014).
 - Baseline vs. DP-GMM signatures (FR-015).
- **Sample Size**: If anomaly count < 10, switch to **non-parametric bootstrap** for p-values and CIs (FR-011, FR-012).
- **Signal-to-Noise**: Simulation study to verify SNR > 1 for $\dot{\alpha}$ under null (FR-020). **Separation of Variance**: The study separates 'estimator variance' (inference noise) from 'data variance' by running on null data with known parameters.
- **Temporal Alignment**: To compare 'early warning' claims, we will align the $\dot{\alpha}$ spike and the MSE threshold crossing in time. The 'time-to-detection' is calculated as the difference between the injection timestamp and the first threshold crossing of each metric, ensuring a fair comparison of temporal scales.

### 3.4 Sensitivity Analysis
- **Threshold**: Sweep {0.01, 0.05, 0.1} on **$\dot{\alpha}$** (not just MSE) to validate the core hypothesis (FR-007).
- **Window Size**: Vary length (20, 30, 50) and stride (1, 5) (FR-016).
- **Prior**: Vary $\sigma_\alpha$ in the time-varying prior (FR-007, FR-016).
- **Power Analysis**: We will perform a power analysis to justify the window size of 30 or propose an adaptive windowing strategy if 30 is insufficient for stable $\alpha$ estimation (Scientific Soundness Concern).

## 4. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions free tier (2 CPU, 7 GB RAM).
- **Strategy**:
 - **No GPU**: All models run on CPU.
 - **Memory**: Data subset to fit <7 GB; use `chunked` processing if necessary.
 - **Runtime**: Target < 6 hours. ADVI is used instead of MCMC for full trajectory.
 - **Libraries**: `pymc` (CPU wheel), `scikit-learn`, `statsmodels`, `lifelines`. No `bitsandbytes` or CUDA-specific ops.

## 5. Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **ADVI over MCMC** | MCMC is too slow for sliding window inference on large-scale datasets; ADVI provides necessary speed on CPU. MCMC retained for robustness check on subset. |
| **Time-varying $\alpha$ prior** | Standard DP-GMM has global $\alpha$; derivative is meaningless. Time-varying prior enables $\dot{\alpha}$ as a local signal. |
| **Bootstrap for N<10** | Parametric tests (t-test) assume normality which fails for small $N$. Bootstrap is robust. |
| **Specific Threshold Sweep {0.01, 0.05, 0.1}** | Mandated by FR-007 to ensure sensitivity analysis is not arbitrary. |
| **Survival Analysis** | Required to handle censored detection times where no anomaly is detected. |

## 6. Risks & Mitigations

- **Risk**: $\dot{\alpha}$ is too noisy.
 - **Mitigation**: Simulation study (FR-020) validates SNR before deployment. If SNR < 1, flag metric as invalid.
- **Risk**: ADVI non-convergence.
 - **Mitigation**: Exclude non-convergent windows (FR-009); log warnings.
- **Risk**: No verified real-world dataset with regime shifts.
 - **Mitigation**: Output "Validation Deferred" report (FR-017b); rely on synthetic data for primary results.
- **Risk**: Bias between ADVI and MCMC.
 - **Mitigation**: Explicit bias quantification test in robustness check (FR-018).