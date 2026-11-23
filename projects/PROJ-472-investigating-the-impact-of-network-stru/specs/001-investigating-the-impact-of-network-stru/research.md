# Research: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

## Summary
The hypothesis—that structural brain network properties predict neural‑avalanche statistics—can be tested using **matched diffusion‑MRI and resting‑state EEG recordings** from the **OpenNeuro HCP‑Aging dataset (ds004230)**, which provides both modalities for the same participants. This enables a full end‑to‑end analysis on real human data while respecting the functional requirement for matched participants (FR‑001).

The analysis pipeline will:

1. Download and preprocess the dMRI and EEG data for each participant.  
2. Compute structural graph metrics (degree, clustering coefficient, rich‑club) and detect neural avalanches (z‑score normalization, 75th‑percentile threshold).  
3. Fit power‑law models to avalanche size and duration distributions, perform model comparison, and retain exponents only when the power‑law model is statistically preferred (FR‑011).  
4. Conduct Spearman rank correlations between structural metrics and avalanche exponents, validate significance with ≥ 1000 permutation shuffles, apply max‑stat family‑wise error correction, and assess collinearity with VIF diagnostics (FR‑006‑FR‑009).  
5. Perform a sensitivity sweep across thresholds {0.75, 0.80} (FR‑008) and report robustness.

All results are derived from the **real matched dataset**; no synthetic data are used. Sample size may be limited by the number of participants that pass quality control, and this limitation will be transparently reported (SC‑004).

## Dataset Strategy
| Dataset | Role | Verified Source URL | Notes |
|---------|------|---------------------|-------|
| **OpenNeuro ds004230 (HCP‑Aging)** | Matched diffusion‑MRI & resting‑state EEG | `https://openneuro.org/datasets/ds004230` | Provides both modalities for the same participants; used for all FR‑001–FR‑011 steps. |
| *No other datasets* | – | – | All other open datasets (e.g., Neurofusion EEG) are unmatched and therefore not used for the primary analysis. |

**Resolution of Data Gap**: The verified OpenNeuro ds004230 dataset satisfies the matched‑data requirement, eliminating the need for synthetic matching. The pipeline will process all available participants (up to 50, or fewer if QC reduces the set) and report the exact number included (SC‑004).

## Methodological Rigor

| Aspect | Implementation Details |
|--------|------------------------|
| **Correlation** | `scipy.stats.spearmanr` (Spearman rank). |
| **Significance** | Non‑parametric permutation test with **≥ 1000 shuffles** (default 5000). Family‑wise error controlled by max‑stat correction across all metric pairs. |
| **Collinearity** | VIF computed via `statsmodels.stats.outliers_influence.variance_inflation_factor`; flagged as “high” if VIF ≥ 5 (FR‑009). |
| **Model Selection** | Likelihood‑ratio test comparing power‑law, exponential, and log‑normal fits (`powerlaw.compare_distributions`). Power‑law exponent retained only if preferred (FR‑011). |
| **Threshold Sensitivity** | Sweep thresholds `{0.75, 0.80}` (percentile of z‑scored EEG amplitude). Correlation results recorded for each threshold (FR‑008). |
| **Multiple‑Comparison Correction** | Permutation‑based max‑stat FWE correction applied to the full set of correlation tests (SC‑003). |
| **Associational Framing** | All statements explicitly qualified as “associational” (FR‑010). |
| **Power‑Law Fitting** | Participants whose avalanche distribution fails to converge or where power‑law is not preferred are excluded from correlation analysis (FR‑005). |
| **EEG Filtering** | Band‑pass 1–40 Hz, down‑sample to 250 Hz, ICA artifact removal (source:). |

## Compute Feasibility
- **CPU‑first**: All steps run on the GitHub Actions CPU runner.  
- **Memory**: Streaming download (`datasets.load_dataset(..., streaming=True)`) keeps peak RAM < 6 GB.  
- **Runtime**: Expected total ≤ 5 h (download ≈ 1 h, preprocessing ≈ 2 h, metric computation ≈ 1 h, statistical analysis ≈ 1 h).  
- **Disk**: Raw and processed files occupy < 7 GB, within the 14 GB limit.

## Decision Rationale
The **Data Availability** constraint is decisive: a verified open dataset (ds004230) now provides the required matched modalities, allowing us to answer the primary scientific question without resorting to synthetic data. This satisfies FR‑001, FR‑002, and all downstream functional requirements while remaining fully reproducible and within compute limits.

---



