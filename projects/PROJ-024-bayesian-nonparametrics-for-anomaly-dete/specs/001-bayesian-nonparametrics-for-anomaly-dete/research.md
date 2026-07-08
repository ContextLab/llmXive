# Research: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Problem Definition

The project investigates whether the temporal dynamics of the concentration parameter ($\alpha$) in a non-parametric Bayesian model (DP-GMM) can serve as an "early-warning" signal for anomalies in time series data. Unlike fixed-component models (GMM, ARIMA) that detect anomalies based on reconstruction error after the fact, the hypothesis posits that the *rate of change* (derivative) of $\alpha$ and the variance of component weights ($\pi$) will exhibit distinct **distributional instability** (abrupt shifts or increased variance) prior to or immediately at the onset of a regime shift, providing a statistical advantage in "time-to-detection."

**Reframed Hypothesis**: We do not assume $\alpha$ will exhibit "high-frequency oscillations" as a pre-defined waveform. Instead, we test for **distributional instability** (abrupt shifts or increased variance) relative to the baseline drift, acknowledging that $\alpha$ is a global parameter and its local derivative is a high-variance proxy subject to empirical validation. The "high-frequency oscillation" criterion mentioned in the spec (User Story 1, Scenario 2) is treated as a specific sub-case to be tested, not the definition of success.

## Dataset Strategy

### Verified Sources Analysis
The "Verified datasets" block provided for this project contains the following entries:
- **MSE (parquet)**: `mserras/alpaca-es-hackaton-backup` (Text/LLM data, not time series).
- **GMMs (parquet)**: `LuJa111/GMM-Sefai-Dataset` (Likely synthetic GMM samples, not temporal).
- **ARIMA (json/csv)**: `CyberHarem/arima_kana_oshinoko`, `dunzing/ARIMA-Date-Prediction`, `ArimaKn/ArabicSemanticSimilairtyDataset` (Mixed; some are date prediction, others text similarity).
- **DP-GMM**: **NO verified source found**.
- **UCI (csv)**: `udayl/UCI_HAR` (Human Activity Recognition, multivariate, not ideal for univariate regime shift), `jlh/uci-shopper` (Shopping behavior), `ucinlp/drop` (Reading comprehension).

**Critical Gap**: None of the verified sources are explicitly labeled as "Univariate Time Series with Regime Shifts" (e.g., Electricity Load, Air Quality, or Sensor Fault datasets) required by the spec's assumptions. The spec assumes availability of datasets like "Electricity Load Diagrams," but these are **not** in the verified list.

### Resolution Strategy
To satisfy **FR-001** (n ≥ 1,000) and **FR-017** (validation against real-world regime shifts) while adhering to the "Verified datasets" constraint:
1.  **Primary Source**: A **Synthetic Data Generator** will be implemented (`code/src/data/synthetic_generator.py`). This generator will create univariate time series with:
    -   Known ground-truth injection points (point anomalies, abrupt shifts, gradual drift).
    -   **Pre-anomaly dynamics**: Explicit modeling of increasing variance or changing autocorrelation *before* the injection point to simulate the "early-warning" precursor. This is critical; without simulating the precursor dynamics, the experiment only tests detection of the anomaly itself, not the warning signal.
    -   Adjustable noise levels and regime parameters.
    -   Compliance with the n ≥ 1,000 requirement.
    -   This ensures the "independent ground-truth" required for **FR-013** and **FR-014**.
    -   **Verification**: The generator's logic is verified via unit tests against known statistical properties (Constitution Principle II).
2.  **Secondary Source (Fallback)**: The `dunzing/ARIMA-Date-Prediction` dataset (CSV) will be inspected. If it contains a univariate numeric column with sufficient length and temporal structure, it will be used for a "real-world" sanity check. If not, the synthetic generator remains the sole source.
3.  **FR-017 Waiver**: If no verified real-world dataset with regime shifts is found, the plan will document the search, the specific gap, and mark FR-017 as "Waived" in the final report, with a recommendation for future work. This satisfies the requirement to *address* the FR.
4.  **No Fabrication**: No URLs for "Electricity Load" or "Air Quality" will be cited, as they are not in the verified list.

### Dataset Variable Fit
-   **Required**: Univariate numeric sequence, timestamps (or index), ground-truth anomaly labels.
-   **Synthetic Fit**: Perfect fit for variable requirements.
-   **Real-world Fit**: Dependent on the content of `dunzing/ARIMA-Date-Prediction`. If it lacks regime shifts, it serves only as a "normal" baseline.

## Methodological Rigor

### Statistical Model: Stick-Breaking DP-GMM
The core model uses a Dirichlet Process with a stick-breaking construction, truncated at $K_{max}$ components (e.g., 20) for computational tractability.
-   **Inference**: ADVI (Automatic Differentiation Variational Inference) in PyMC 4.
-   **Convergence**: ELBO delta < 0.01 over 10 iterations (FR-009).
-   **Dynamic Signatures**:
    -   $\alpha_t$: Posterior mean of concentration parameter at window $t$.
    -   $\dot{\alpha}_t$: First derivative (finite difference) of $\alpha_t$.
    -   $\sigma^2_{\pi, t}$: Variance of component weights at window $t$.

### Theoretical Justification for $\alpha$ Dynamics
In standard DP-GMM theory, $\alpha$ controls the expected number of clusters. In a sliding window of a fixed size, the posterior for $\alpha$ is often dominated by the prior or the data's inherent noise, leading to high variance. The hypothesis is that a regime shift (change in local distributional complexity) induces a *change* in the posterior mean of $\alpha$ or its variance. We do **not** assume $\alpha$ will exhibit "high-frequency oscillations" as a pre-defined waveform. Instead, we test for **distributional instability** (abrupt shifts or increased variance) relative to the baseline drift. This avoids circular validation where the metric is defined by the very shape it is supposed to detect.

**Empirical Validation**: The plan explicitly acknowledges the lack of direct literature supporting $\dot{\alpha}$ as a local anomaly detector. The experiment is framed as an **empirical test** of this proxy's validity, rather than assuming it as a known fact.

### Robustness Check: ADVI Bias Detection
ADVI is known to underestimate posterior variance. To address this, the plan includes a **Small-Scale MCMC Validation**:
1.  Select 100 random windows.
2.  Run full MCMC (NUTS) for these windows.
3.  Compare ADVI posterior mean and variance against MCMC.
4.  **Bias Criteria**: If ADVI variance underestimates MCMC variance by >50% OR the mean difference exceeds 2 standard deviations of the MCMC posterior, the $\dot{\alpha}$ metric is flagged as unreliable for that window and excluded from the primary analysis. **The system then defaults to using the component weight variance ($\sigma^2_{\pi, t}$) as the primary signature for that window**, ensuring the detection pipeline continues.

### Statistical Testing & Power
-   **Time-to-Detection**: Defined as steps from injection ($t_{inj}$) to threshold crossing ($t_{det}$).
-   **Hypothesis Tests**:
    -   **Wilcoxon Signed-Rank Test (Primary)**: Comparing detection times of DP-GMM vs. Baselines (ARIMA, Fixed GMM) across datasets (FR-006). This non-parametric test is chosen because the distribution of detection time differences (discrete steps) is likely skewed and non-normal.
    -   **Paired t-test (Secondary)**: Used only as a sensitivity check.
    -   **Kolmogorov-Smirnov (KS) Test**: Comparing distributions of $\dot{\alpha}$ for anomaly vs. normal windows (FR-010, FR-014).
    -   **Baseline KS Test**: **FR-015**: Perform KS test on the *distributions* of baseline reconstruction errors (normal vs. anomaly windows) to ensure the baselines themselves show distributional differences.
-   **Power Analysis**:
    -   Target: ≥10 anomalies per dataset to achieve ≥80% power at $\alpha=0.05$ (Cohen's d=0.5).
    -   **Implementation**: Calculate expected anomaly count based on dataset length and injection rate *before* inference.
    -   **Fallback**: If anomaly count < 10, switch to non-parametric bootstrap resampling (FR-012, SC-006).
-   **Multiple Comparisons**:
    -   The plan involves multiple statistical tests (t-tests per baseline, KS tests per regime type, threshold sweeps).
    -   **Correction**: A **Holm-Bonferroni correction** will be applied to the p-values reported in the final analysis to control the family-wise error rate, addressing the dependency introduced by threshold optimization.

### Causal Inference & Validity
-   **Observational Nature**: The study is observational regarding the "early warning" signal. The claim is correlational: "Anomalous regimes are associated with high $\dot{\alpha}$."
-   **Identification**: Causal claims are avoided. The "ground truth" is synthetic (injected), allowing for a controlled test of detection latency, not causal attribution.
-   **Measurement Validity**: The DP-GMM implementation follows standard Bayesian literature (e.g., Neal, 2000; Blei & Jordan, 2006). The "rate of change" metric is a derived proxy; its validity is the subject of the experiment (SC-001).

### Dataset-Variable Fit (Re-confirmed)
-   **Predictor**: Time series values (normalized).
-   **Outcome**: Anomaly label (binary).
-   **Covariates**: Window index, derivative metrics.
-   **Fit**: The synthetic generator ensures all variables exist. The fallback dataset is only used if it contains a univariate numeric column.

## Compute Feasibility (CPU-Only)

### Constraints
-   **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM, 14GB Disk).
-   **Time**: ≤ 6 hours.
-   **No GPU**: No CUDA, no 8-bit quantization.

### Mitigation Strategies
1.  **Sliding Window**: Inference is performed on small windows (n=30). This drastically reduces the computational burden of ADVI compared to full-sequence inference.
2.  **Truncation**: DP-GMM is truncated to $K_{max}=20$ components.
3.  **Parallelization**: Windows are processed sequentially to avoid memory overhead, but the small window size ensures each step is fast.
4.  **Library Selection**:
    -   `pymc`: Uses `jax` or `numpy` backend (CPU mode) for ADVI.
    -   `scikit-learn`: Standard CPU implementation for GMM/ARIMA.
    -   `psutil`: Used to monitor RAM usage (FR-008).
5. **Sampling**: If a dataset is too large, only a representative subset (or the first [deferred] points) is processed to stay within the 6h limit, ensuring the methodology is tested.

## Sensitivity Analysis Plan

1.  **Threshold Sweep**: Test cutoffs at 0.01, 0.05, 0.1 (FR-007).
2.  **Window Size**: Test lengths 20, 30, 50 (FR-016).
3.  **Derivative Method**: Test simple difference vs. smoothed difference (Savitzky-Golay) (FR-016).
4.  **Prior Sensitivity**: Vary the base measure concentration parameter (FR-007).

## Decision/Rationale

**Why Synthetic Data?**
The verified dataset list lacks a suitable univariate time series with regime shifts. Using text or multivariate datasets (like HAR) would violate the "Dataset-Variable Fit" requirement. Synthetic data provides the necessary ground truth for **FR-013** (independent injection) and **FR-014** (negative control) without fabricating URLs or misusing datasets.

**Why ADVI over MCMC?**
MCMC (NUTS) is too slow for sliding window inference on a 2-core CPU within 6 hours. ADVI is a deterministic approximation that is significantly faster and fits the "CPU-tractable" constraint, provided convergence is monitored (FR-009) and bias is checked via the MCMC subset.

**Why Truncated DP-GMM?**
A full infinite DP-GMM is computationally intractable. Truncation at $K=20$ is a standard approximation that allows for flexible clustering while remaining within memory limits.

**Why Distributional Instability over Oscillations?**
Theoretical literature suggests $\alpha$ adapts slowly. Expecting "high-frequency oscillations" in a 30-point window is not standard. The hypothesis is reframed to test for *abrupt shifts* or *increased variance* in $\alpha$, which is a more robust and theoretically grounded signal for regime shifts. The "oscillation" criteria in the spec is treated as a specific sub-case to be tested, not the definition of success.

**Why Wilcoxon over t-test?**
Detection time is a discrete, likely skewed metric. The Wilcoxon signed-rank test is robust to non-normality and provides a valid test for "earlier detection" without assuming a specific distribution of differences.