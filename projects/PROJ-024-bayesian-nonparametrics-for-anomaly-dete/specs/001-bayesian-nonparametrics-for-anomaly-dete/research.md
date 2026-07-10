# Research: Bayesian Nonparametrics for Anomaly Detection in Time Series

## 1. Literature Review & Theoretical Basis

### 1.1 Dirichlet Process Gaussian Mixture Models (DP-GMM)
DP-GMMs allow the number of mixture components to grow with the data, making them ideal for detecting unknown regime shifts in time series. The stick-breaking construction (Sethuraman,) provides a tractable representation for inference.

**Critical Theoretical Correction**: In standard DP-GMM, the concentration parameter $\alpha$ is a global hyperparameter. To make $\alpha$ a valid local signal for sliding windows, this project implements a **hierarchical time-varying prior**: $\alpha_t \sim \text{Normal}(\alpha_{t-1}, \sigma)$. This re-parameterization allows $\alpha$ to evolve locally, making its derivative $\dot{\alpha}$ a meaningful signal for local regime shifts.

**Key Insight**: Under normal conditions, $\alpha_t$ is stable. During a regime shift, the model adapts by increasing the number of components locally, causing $\alpha_t$ to fluctuate. The rate of change $\dot{\alpha}_t$ is hypothesized to be an early-warning signal (FR-020, US-1).

### 1.2 Variational Inference (ADVI) & MCMC Validation
Automatic Differentiation Variational Inference (ADVI) (Kucukelbir et al.,) is used for scalable inference in PyMC 4. Unlike MCMC, ADVI is deterministic and faster, making it feasible for sliding window inference on CPU. However, ADVI assumes a unimodal posterior approximation, which may fail in the small-n (n=50) regime.

**Robustness Strategy**: We perform a **MCMC subset validation** (Phase 4) on 50 representative windows to verify that the ADVI approximation is accurate for this specific model and data regime.

### 1.3 Baseline Methods
- **Fixed GMMs**: k=3, 5, 10 components. These serve as static baselines to isolate the nonparametric advantage.
- **ARIMA**: Autoregressive Integrated Moving Average models capture linear temporal dependencies. Reconstruction error (MSE) is the anomaly score.

## 2. Dataset Strategy

### 2.1 Verified Datasets
Per the project constraints, we use ONLY the following verified datasets (URLs from `# Verified datasets` block):

| Dataset | Source URL | Usage |
|---------|------------|-------|
| **NAB (Numenta Anomaly Benchmark)** | ` | Real-world time series with labeled anomalies (verified). |
| **PhysioNet Sleep** | ` | Multivariate physiological signals. **Projection**: Select ECG lead II or compute heart rate variability to obtain univariate series. |
| **PhysioNet Digiscope** | ` | High-frequency time series. **Projection**: Select single representative channel (e.g., SpO2). |

> **Note**: UCI HAR is **excluded** as it is a static classification dataset, not a continuous time series with regime shifts. Real-world datasets with labeled regime shifts are scarce; synthetic data is the primary source for pre-anomaly dynamics.

### 2.2 Dataset Search Procedure (FR-017, FR-017b)
1. Search for "time series regime shift labeled" in UCI, NAB, PhysioNet.
2. If no verified source found with labeled regime shifts, generate a "Validation Deferred" report.
3. Log the search query and result count in the final report.
4. Mark requirement as "Deferred by Design" if no source is found.

### 2.3 Synthetic Data Generation
Since real-world datasets may lack labeled regime shifts, we implement a synthetic generator (FR-021) that:
- Injects point anomalies, abrupt shifts, and gradual drift.
- Includes **pre-anomaly dynamics** (increasing variance, changing autocorrelation) to test the early-warning hypothesis.
- Verifies generator logic (FR-022) before use.
- **Null Hypothesis Simulation**: Generates stationary data with known properties to verify that $\dot{\alpha}$ remains near zero under the null (FR-020).

### 2.4 Data Preprocessing
- **Normalization**: Zero mean, unit variance (FR-001).
- **Missing Timestamps**: Synthetic integer timestamps generated (Edge Case).
- **Sample Size**: Datasets with <1,000 obs are rejected (Edge Case).
- **Splitting**: Data is split into Training/Validation/Test sets. Thresholds selected on Validation, applied to Test (FR-019).

## 3. Methodology & Statistical Rigor

### 3.1 Sliding Window Inference
- **Window Length**: 50 observations (increased from 30 for stability in nonparametric estimation).
- **Stride**: 1 observation.
- **Model**: Hierarchical DP-GMM with time-varying $\alpha_t$ (PyMC 4, ADVI).
- **Output**: Posterior mean $\alpha_t$, component weights $\pi_t$, and their derivatives $\dot{\alpha}_t$, $\dot{\pi}_t$.

### 3.2 Anomaly Scoring
- **DP-GMM**: $|\dot{\alpha}_t|$ (rate of change of local concentration parameter).
- **Baselines**: Reconstruction error (MSE) from fixed GMMs and ARIMA.

### 3.3 Statistical Testing
- **Time-to-Detection**: Steps from injection to threshold crossing.
- **Blind Validation**: Detect anomalies in held-out test set without prior knowledge of injection points.
- **Bootstrap Resampling**: If anomaly count <10, switch to non-parametric bootstrap for p-values (FR-011, FR-012). This is the **primary** test for distributional differences.
- **Kolmogorov-Smirnov (KS) Test**: Supplementary descriptive metric for distributional differences (FR-010, FR-014, FR-015).

### 3.4 Sensitivity Analysis
- **Threshold**: Sweep {0.01, 0.05, 0.1} on normalized MSE (FR-007).
- **Window Size & Smoothing**: Robustness check for $\dot{\alpha}$ signal (FR-016).
- **Prior Sensitivity**: Vary $\alpha$ hyperparameters (Constitution Principle VII).

### 3.5 Simulation Study (FR-020)
- **Goal**: Verify signal-to-noise ratio of $\dot{\alpha}$ under null hypothesis (stationary data).
- **Null Hypothesis**: Data is stationary; $\dot{\alpha}$ should be near zero.
- **Outcome**: If SNR < 1, flag metric as invalid and halt pipeline (US-1, Scenario 2).

## 4. Computational Feasibility

### 4.1 Resource Constraints
- **Hardware**: GitHub Actions free-tier (multi-core CPU, ~7 GB RAM, 14 GB disk).
- **Runtime Limit**: ≤6 hours per job.
- **Memory Limit**: Peak RAM < 7 GB (measured via `psutil`).

### 4.2 Feasibility Strategy
- **No GPU**: PyMC 4 configured for CPU-only; no CUDA imports.
- **Sampled Data**: Real-world datasets sampled to fit RAM (e.g., a manageable number of observations).
- **ADVI Limit**: Max 500 iterations per window; non-convergent models excluded.
- **Parallelization**: Sliding windows processed sequentially to avoid memory spikes.
- **MCMC Subset**: A subset of windows runs with NUTS to keep runtime feasible.

### 4.3 Validation
- **Peak RAM Monitoring**: `psutil.Process().memory_info().rss` tracked throughout pipeline.
- **Runtime Tracking**: `time` module logs total execution time.
- **Failure Mode**: If limits exceeded, pipeline fails with validation report (FR-008).

## 5. Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **Hierarchical Time-Varying Alpha** | Standard global $\alpha$ is invalid for local signals. The hierarchical prior makes $\alpha_t$ a local state variable, enabling $\dot{\alpha}$ as a valid signal. |
| **ADVI over MCMC (Full)** | MCMC (NUTS) is too slow for full sliding window inference on CPU. ADVI provides a CPU-tractable approximation. |
| **MCMC Subset Validation** | ADVI may fail in small-n regimes. Running NUTS on 50 windows validates the approximation without violating CPU constraints. |
| **Window Size = 50** | Increased from 30 to ensure sufficient data for nonparametric estimation and reduce prior dominance. |
| **Bootstrap for n<10** | Parametric tests require sufficient sample size. Bootstrap ensures robustness for rare anomalies. |
| **Synthetic Injection** | Real-world datasets often lack labeled regime shifts. Synthetic injection allows controlled validation of the early-warning hypothesis. |
| **Blind Validation** | Required to prove the metric has predictive power on unseen data, not just fitting injection artifacts. |
