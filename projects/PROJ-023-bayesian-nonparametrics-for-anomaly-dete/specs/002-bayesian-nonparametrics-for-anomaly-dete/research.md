# Research: Bayesian Nonparametrics for Anomaly Detection in Time Series

## 1. Research Question & Hypothesis

**Research Question**: Does a Gaussian Process regression model with Sparse Variational Inference provide superior sensitivity to abrupt variance shifts and mean changes in univariate time series compared to traditional Statistical Process Control (SPC) charts and a lightweight Variational Auto-Encoder (VAE), particularly in the presence of non-stationary noise?

**Hypothesis**: The Bayesian nonparametric approach will outperform Shewhart and CUSUM charts in detecting subtle, short-duration variance spikes (near-threshold values) due to its ability to model complex temporal correlations without assuming a fixed parametric form for the noise distribution. However, it may not significantly outperform the VAE on long-duration mean shifts where the VAE's reconstruction error is highly sensitive.

**Associational Framing**: All claims regarding "detectability" are framed as associational correlations between shift characteristics (magnitude, duration) and F1-scores. No causal claims are made about the underlying physical process generating the time series, as the data is either synthetic or observational.

**Clarification on Nonparametric Claim**: While the GP is nonparametric in the limit, the specific implementation uses a stationary RBF kernel. The hypothesis does *not* claim the model handles non-stationarity via the kernel itself; rather, it tests whether the flexible mean function of the GP (learned via VI) provides better robustness against non-stationary *shifts* (anomalies) compared to fixed-window baselines, even with a stationary prior.

## 2. Dataset Strategy

The study utilizes public univariate time series datasets. Per the project constitution and verified dataset constraints, only sources with verified URLs are cited.

| Dataset Source | Verified URL | Usage |
|----------------|--------------|-------|
| **UCR Time Series Archive** (via HuggingFace) | ` | Primary source for real-world univariate time series windows. |
| **UCI Machine Learning Repository** (via HuggingFace) | ` | Secondary source for validation on human activity data (aggregated to univariate if needed). |

**Note on VAE**: No verified external dataset URL exists specifically for a "VAE anomaly detection benchmark." The VAE will be trained and evaluated on the same data windows derived from the UCR/UCI sources listed above, using the synthetic anomalies injected by the pipeline.

**Data Fit Verification**:
- **Requirement**: The dataset must contain continuous univariate time series suitable for windowing.
- **Verification**: The UCR/UCI datasets listed contain raw sensor readings (e.g., accelerometer, temperature) which are univariate or can be reduced to a single channel for this study.
- **Constraint Check**: The datasets do *not* contain pre-labeled "anomalies" for the specific synthetic shifts (mean shift 2.5σ, variance spike 3x) required by FR-009. Therefore, the pipeline **must** inject these anomalies synthetically (FR-004) to create the ground truth. This is a planned and necessary step, not a data gap.

## 3. Methodology

### 3.1 Data Preprocessing & Anomaly Injection
1. **Windowing**: Extract non-overlapping or sliding windows of moderate length from raw UCR/UCI data.
2. **Clean Data Selection (CRITICAL)**:
 - For VAE training and Baseline statistics, identify a "clean" segment within the window (e.g., the first [deferred] or a segment identified by a robust MAD filter) that contains no anomalies.
 - **Normalization**: Calculate Z-score parameters (mean $\mu$, std $\sigma$) **only** from this clean segment.
 - **Apply**: Apply these fixed parameters to normalize the **entire** window (including the anomaly region). This preserves the absolute scale of the injected anomaly relative to the true baseline, avoiding the "contaminated normalization" flaw.
3. **Injection (FR-009, FR-011)**:
 - **Mean Shift**: Add a constant offset of $2.5 \times \sigma_{baseline}$ to a segment of length $L \in [5, 15]$.
 - **Variance Spike**: Scale the noise in a segment by a substantial factor.
 - **Gradual Drift**: Linear ramp over $L$ points.
 - **Near-Threshold**: Include shifts at $1.5\sigma$ to test floor effects (FR-011).
4. **Ground Truth**: Generate a binary mask vector matching the window length.

### 3.2 Bayesian Nonparametric Model (FR-002)
- **Model**: Gaussian Process Regression with a Radial Basis Function (RBF) kernel.
- **Training Strategy (Circular Validation Fix)**: The model is trained **ONLY** on the "clean" portion of the window (excluding the injected anomaly segment). This ensures the posterior mean/variance reflects the *normal* behavior.
- **Inference**: Sparse Variational Inference (SVI) using inducing points (e.g., 20-30 points) to reduce complexity from $O(N^3)$ to $O(NM^2)$.
- **Library**: `pymc` (CPU-optimized build). `numpyro` is noted as a fallback but `pymc` is the primary target.
- **Anomaly Scoring (Rolling Window Fix)**:
 - For each time point $t$ in the test segment (anomaly region), calculate the posterior predictive probability $P(y_t | y_{t-k} \dots y_{t-1})$ using a **fixed history window** of size $k$ (e.g., $k=10$) drawn from the *clean* training distribution, or by predicting $y_t$ conditioned on the model fit to the clean segment.
 - This prevents the model from "chasing" the anomaly. If an anomaly occurs at $t-1$, it does not corrupt the prediction for $t$ because the model is not re-fit on the anomaly data.
 - Score: $S_t = -\log P(y_t | \text{clean model})$.
- **Convergence**: Monitor ELBO stability over 1000 steps (FR-010). Discard runs failing convergence. Report **ELBO stability**, **R-hat** (if MCMC fallback), and **Effective Sample Size**.

### 3.3 Baseline Models (FR-003)
- **Shewhart Chart**:
 - **Statistic Calculation**: Compute mean $\mu$ and std $\sigma$ **only** from the "clean" training segment.
 - **Threshold**: Flag points where $|x_t - \mu| > 3\sigma$.
- **CUSUM**:
 - **Statistic Calculation**: Compute target mean $\mu$ from the "clean" segment.
 - **Threshold**: Accumulate deviations from $\mu$; flag when cumulative sum exceeds threshold.
- **VAE**:
 - **Clean Data Selection Protocol**: Use a robust statistical filter (e.g., Median Absolute Deviation) on raw data to select "clean" segments for training. This ensures the VAE is not trained on natural anomalies.
 - **Architecture**: Lightweight auto-encoder with 1-2 hidden layers.
 - **Anomaly Score**: Reconstruction MSE on the test segment (excluding training data).

### 3.4 Evaluation & Statistical Testing (FR-005, FR-006, FR-009)
- **Metrics**: Precision, Recall, F1-score, AUC-ROC.
- **Fixed Threshold Strategy (Bias Fix)**:
 - Define a fixed thresholding strategy **before** aggregation: e.g., select a threshold that achieves **95% specificity** on a held-out validation set (or a fixed probability cutoff like 0.95).
 - Apply this **same** threshold to all datasets and models to calculate F1-scores. This prevents per-dataset optimization (p-hacking).
- **Significance Test (Power Fix)**:
 - Replace Wilcoxon signed-rank test with **Bootstrap Confidence Intervals**.
 - Resample the F-scores (with replacement) a sufficient number of times to compute the 95% CI for the difference in mean F1-scores between Bayesian and Baseline methods.
 - If the 95% CI does not include 0, the difference is considered significant. This is more robust for small sample sizes (5-10) and bounded metrics.
- **Multiple Comparison Correction**: Benjamini-Hochberg procedure (FR-009) applied to p-values if multiple tests are run.
- **Sensitivity Analysis**: Sweep decision thresholds (e.g., 0.5 to 0.95) and plot F1 vs. Threshold (FR-007, SC-004).
- **Correlation**: Pearson/Spearman correlation between shift magnitude and F1-score (SC-005).

## 4. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (multiple CPU cores, ~7GB RAM).
- **Memory Strategy**:
 - Process data in small windows (N < 200).
 - Use inducing points (M < 30) in GP to limit memory footprint.
 - VAE architecture kept minimal (input=50, hidden=20, output=50).
- **Time Limit**: 6 hours total.
 - Data download/prep: < 30 mins.
 - Inference (1000 steps): < 2 hours per window.
 - Baselines: < 30 mins.
 - Evaluation/Plotting: < 30 mins.
- **GPU**: **None**. All models run on CPU. No CUDA dependencies.

## 5. Limitations & Risk Mitigation

- **Risk**: GP VI fails to converge within 1000 steps.
 - *Mitigation*: Implement early stopping based on ELBO delta; fallback to a simpler kernel if needed.
- **Risk**: Synthetic anomalies do not reflect real-world complexity.
 - *Mitigation*: Acknowledge this in the paper; the study focuses on *controlled* detectability, not generalization to unknown real-world anomalies.
- **Risk**: Memory overflow during VAE training.
 - *Mitigation*: Batch size set to 1 or small integer; gradient accumulation if necessary.
- **Risk**: Stationary kernel assumption limits non-stationary detection.
 - *Mitigation*: Explicitly frame results as testing the robustness of the GP *mean function* rather than the kernel's ability to model non-stationarity.

## 6. Decision Log

| Decision | Rationale |
|----------|-----------|
| **Sparse VI over MCMC** | MCMC is too slow for 1000-step limits on CI. SVI provides a tractable approximation for the research question. |
| **Synthetic Injection** | Real anomaly labels are inconsistent across public datasets; synthetic injection ensures FR-009 parameters are met exactly. |
| **Bootstrap CI over Wilcoxon** | F1-scores are bounded and skewed; small sample sizes (5-10) make Wilcoxon low-power. Bootstrap provides robust confidence intervals. |
| **Fixed Threshold Strategy** | Prevents threshold optimization bias (p-hacking) in statistical comparisons. |
| **Clean Data Training** | Prevents circular validation and ensures baseline statistics are not inflated by anomalies. |
| **Benjamini-Hochberg** | Required by FR-009 to control False Discovery Rate when testing multiple shift types. |