# Research: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Background
Dirichlet Process Gaussian Mixture Models (DP‑GMM) provide a flexible non‑parametric approach to model the distribution of univariate time‑series observations without fixing the number of mixture components a priori. Stochastic Variational Inference (ADVI) enables scalable posterior approximation, and ELBO monitoring supplies convergence diagnostics (Principle VI). Prior sensitivity (Principle VII) requires exploring the concentration parameters (`alpha`, `gamma`).

**Note on Temporal Structure**: Standard DPGMM assumes i.i.d. observations, but time series exhibit autocorrelation. This plan addresses this by: (1) applying lag features (lag-1, lag-7) and rolling statistics (mean, std over window) as preprocessing, and (2) using sliding-window mini-batch updates rather than true streaming.

## Related Work
- **DP‑GMM for time‑series** – standard reference: *Rasmussen, C. E. (2000). The infinite Gaussian mixture model.*  
- **ADVI convergence diagnostics** – *Kucukelbir et al., 2017, "Automatic Differentiation Variational Inference."*  
- **Threshold calibration in streaming anomaly detection** – *Liu et al., 2021, "Adaptive Thresholding for Online Anomaly Detection."*

Citations limited to peer-reviewed sources; dataset access via ucimlrepo loader provides canonical UCI repository access per Constitution Principle I (Reproducibility).

## Dataset Strategy
| Dataset | Source (Access Method) | Ground Truth | Notes |
|---------|------------------------|--------------|-------|
| Electricity (UCI) | `ucimlrepo` loader (canonical UCI) | None by default; synthetic anomalies injected for supervised eval | Sufficient observations per series (SC‑002). Lag features + rolling stats applied. |
| Traffic (UCI) | `ucimlrepo` loader (canonical UCI) | None by default; synthetic anomalies injected for supervised eval | Univariate traffic flow counts. Lag features + rolling stats applied. |
| Synthetic Control Chart (UCI) | `ucimlrepo` loader (canonical UCI) | None by default; synthetic anomalies injected for supervised eval | Classic benchmark for change‑point detection. Lag features + rolling stats applied. |

**Data Split Strategy**: A primary portion for training (unsupervised model fitting), a secondary portion for threshold calibration (unsupervised percentile-based), and a final portion for supervised evaluation (with injected anomalies). This separates US3 (unsupervised threshold adaptation) from F1 computation (supervised evaluation).

## Sample Size Justification
Per success criterion SC-002, each dataset must contain a sufficient number of observations to support both model training and evaluation. The minimum requirement of a sufficient number of observations (as specified in `dataset.schema.yaml`) ensures:
- Adequate data for DPGMM posterior estimation with reasonable ELBO convergence
- Sufficient observations for reliable threshold calibration (percentile-based methods require stable score distributions)
- Enough data points to inject anomalies at 1-5% rates while maintaining statistical power for F1/precision/recall computation

This minimum is validated at data ingestion time; datasets failing this requirement are rejected per Constitution Principle III (Data Hygiene).

## Synthetic Anomaly Injection Methodology
**Injection Timing**: Anomalies are injected INTO RAW DATA BEFORE any temporal feature engineering (lag-1, lag-7, rolling mean/std). This ensures anomalies are not smoothed/diluted by preprocessing and maintains scientific validity of detection evaluation. The injection pipeline follows this sequence:

1. Load raw time series CSV (immutable, checksummed per Principle III)
2. Inject anomalies at specified rate (1-5% point anomalies, 50-100 window contextual shifts)
3. Compute temporal features (lag, rolling statistics) on the anomaly-injected data
4. Train DPGMM and evaluate detection performance

This ordering is critical: if anomalies were injected after feature engineering, the lag/rolling operations would attenuate spike magnitudes and reduce detection sensitivity, invalidating the evaluation.

**Injection Types**:
- Point anomalies: Random spikes (±5σ from local mean) injected at 1-5% rate
- Contextual anomalies: Distribution shifts (mean shift of ±3σ) over 50-100 observation windows
- Injection parameters documented in `code/config.yaml` for reproducibility

## Prior Sensitivity Plan
- Sweep `alpha` ∈ {0.1, 1.0, 10.0} and `gamma` ∈ {0.5, 1.0, 5.0}.  
- For each configuration, record final ELBO, number of active components, and evaluation metrics.  
- Store results in `data/processed/results/prior_sensitivity.json`.

## Expected Outcomes
- Convergent DPGMM (ELBO plateau within a reasonable number of iterations).  
- Anomaly scores with calibrated uncertainties.  
- Adaptive threshold that yields target performance metrics on held‑out synthetic test set (hypothesis to be tested, not guaranteed).  
- Full contract test coverage (substantial).  
- Robustness across prior specifications (Principle VII).

**Evaluation Regimes**:
1. **Unsupervised**: ELBO, reconstruction error on original data (no labels).
2. **Supervised**: F1, precision, recall on data with injected anomalies (labels known).

All outcomes will be traceable to specific rows in `data/processed/results/` and code sections, fulfilling Principle IV.