# Research: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

## 1. Dataset Strategy

The project requires **verified** diffusion-MRI (dMRI) data to generate structural connectomes. Since no verified public dataset contains matched dMRI and resting-state EEG for the same participants, the study adopts a **simulation-based approach**. Structural connectomes from verified dMRI data will be used to generate synthetic EEG time-series, from which avalanche statistics are computed.

**Verified Datasets**:

| Modality | Dataset Source | URL (Verified Only) | Format | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **dMRI** | OpenNeuro ds003813 | `https://openneuro.org/datasets/ds003813/versions/1.0.0` | BIDS | Contains diffusion MRI data with HCP parcellation. Verified source for structural connectomes. |
| **Simulation** | N/A (Generated) | N/A | N/A | Synthetic EEG time-series generated from dMRI structural connectomes using a linear neural mass model. |

**Dataset Fit Assessment**:
- **Variable Coverage**: The OpenNeuro structural connectivity dataset provides structural connectivity metrics. The simulation module generates the required EEG time-series.
- **No Mismatch Risk**: By using a simulation-based approach, the need for matched empirical EEG data is eliminated. The analysis is now between structural metrics and *simulated* avalanche exponents.
- **Plan Adjustment**: The implementation will download dMRI data from OpenNeuro ds003813, process it to generate structural connectomes, and then simulate EEG avalanches. No empirical EEG data is required.

**Decision**: The plan proceeds with the **simulation pipeline** using verified dMRI data. The statistical association (FR-006) is between structural metrics and simulated avalanche exponents, which is executable without matched empirical data.

## 2. Methodological Rigor

### 2.1 Statistical Approach
- **Correlation**: Spearman rank correlation (FR-006) is chosen over Pearson due to the likely non-normal distribution of power-law exponents and network metrics.
- **Multiple Comparisons**: Family-wise error rate (FWER) control via 1000-shuffle permutation test (FR-007).
- **Collinearity**: Variance Inflation Factor (VIF) calculated for degree and clustering (FR-009). If VIF ≥ 5, results are flagged as "high collinearity" and independent effects are not claimed.
- **Causal Framing**: All findings framed as **associational** (FR-010). No causal claims.

### 2.2 Power-Law Fitting
- **Model Comparison**: Likelihood ratio test (FR-011) between Power-Law, Exponential, and Log-Normal.
- **Fallback**: If Power-Law is not preferred, the exponent is not reported for that subject.
- **Convergence**: If `powerlaw` fails to converge, the subject is excluded from correlation analysis.

### 2.3 Sensitivity Analysis
- **Threshold Sweep**: {70%, 75%, 80%} of the 75th percentile amplitude (FR-008).
- **Robustness**: Correlation stability across thresholds will be reported.

## 3. Compute Feasibility (CPU-Only)

- **Hardware**: GitHub Actions Free Tier (2 vCPU, 7 GB RAM).
- **Strategy**:
  - **Data Loading**: Stream data from BIDS/Parquet; do not load entire dataset into RAM if > 4GB.
  - **Preprocessing**: MRtrix3 and NetworkX are CPU-efficient. Simulation will be limited to a subset of subjects to save time.
  - **Parallelization**: Use `joblib` for parallel processing of subjects (max 2 workers).
  - **Runtime**: Target < 6 hours. If a subject's processing exceeds a predefined time threshold, it is flagged and potentially skipped.

## 4. Limitations & Assumptions

- **Sample Size**: Power analysis is [deferred]. The study acknowledges power limitations if N < 30.
- **Data Quality**: Participants with >30% channels removed or disconnected graphs are excluded.
- **Simulation Validity**: The study assumes the linear neural mass model is a valid proxy for empirical avalanche dynamics. This is a known limitation of simulation-based approaches.
- **Data Availability**: The primary limitation is the availability of verified dMRI data. The plan is robust to this by validating the pipeline even if the correlation cannot be computed (Null Result Protocol).