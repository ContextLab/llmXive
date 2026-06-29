# Research: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Sensorimotor Performance

## Dataset Strategy

The study relies on the Human Connectome Project (HCP) release. To ensure reproducibility and computational feasibility on GitHub Actions, the data strategy prioritizes **verified preprocessed data** (HCP S1200 ICA-FIX) which is part of the official HCP release.

| Requirement | Dataset Source | Verified URL | Access Method | Notes |
|-------------|----------------|--------------|---------------|-------|
| Resting-state fMRI (Preprocessed) & Behavioral Metrics | HCP S1200 ICA-FIX (Derived) | ` | `pandas.read_parquet` | Primary source. Contains preprocessed time-series (or derived metrics) and behavioral scores. Verified as part of HCP S1200 release. |
| Supplemental HCP Data (Metadata) | HCP S1200 (Metadata) | ` | `json.load` | Contains subject demographics and metadata. |
| **Gap Note** | Direct Raw fMRI NIfTI | **NO VERIFIED SOURCE** | N/A | The provided "Verified datasets" block does not contain a verified URL for raw NIfTI files. **Action**: The pipeline will use the verified ICA-FIX data as the primary source. Raw preprocessing is only attempted as a fallback for a small subset if API credentials are available, acknowledging the computational risk. |

**Dataset Variable Fit**:
- **Required**: Resting-state fMRI time series (or preprocessed connectivity), Motor Task Performance composite score, Framewise Displacement (FD), Age, Sex.
- **Verified Fit**: The HCP-derived parquet file contains the behavioral proxy and derived connectivity metrics. The raw fMRI time series required for *de novo* preprocessing (as per FR-002) are not guaranteed to be in the verified parquet. The plan explicitly handles this by prioritizing the verified preprocessed data (ICA-FIX) which meets the "preprocessed" requirement without needing raw NIfTI reprocessing.

## Methodological Rationale

### Preprocessing Strategy
- **Tool**: `nilearn` (CPU-optimized) and `fsl` (if available in CI, otherwise `nilearn` only).
- **Steps**: Motion correction, slice-time correction, normalization, smoothing (only if raw data fallback is triggered).
- **Motion Control**:
 1. **Time-Series Level**: Motion parameters (6 rigid-body + FD) are regressed out from the time-series *before* connectivity matrix calculation.
 2. **Statistical Level**: Mean Framewise Displacement (FD) is included as a covariate in the final correlation analysis.
- **Quality Control**: Calculate tSNR (mean signal / std dev, excluding initial volumes) and ensure motion parameters < 0.5mm. Subjects failing QC are excluded.
- **CPU Feasibility**: Processing will be done in batches. If memory usage exceeds a predefined threshold, batch size is reduced dynamically.

### Network Metric Extraction
- **Atlas**: Schaefer high-resolution atlas (9 networks).
- **Connectivity**: Pearson correlation of region time series to generate 400x400 symmetric matrices.
- **Metrics**:
 - **Modularity**: Global scalar (Louvain algorithm).
 - **Global Efficiency**: Global scalar.
 - **Participation Coefficient**: Mean across all nodes.
 - **Within-Module Degree**: Mean across all nodes.
- **Multivariate Approach**: Since Modularity, Participation Coefficient, and Within-Module Degree are derived from the same community detection (mathematically coupled), the plan will perform **Principal Component Analysis (PCA)** on these metrics (plus Global Efficiency) to derive a single "Network Architecture" factor. Alternatively, a MANOVA will be used if multivariate testing is preferred. This avoids pseudo-replication and handles collinearity.

### Statistical Analysis
- **Test**: Correlation (Spearman/Pearson) between the Network Metrics (or PCA factor) and Motor Task Performance.
- **Covariate**: Framewise Displacement (FD) is controlled for in the correlation.
- **Correction**: Benjamini-Hochberg FDR (q < 0.05).
- **Threshold Logging**: The analysis script will **log the correlation coefficient threshold (r > 0.3)** as required by Constitution Principle VII, even if it is not a gating condition for significance.
- **Effect Size Precision**: Instead of post-hoc power (which is redundant with p-values), the plan will report **95% Confidence Intervals (CIs)** for the correlation coefficients to indicate precision and effect size magnitude.
- **Causal Framing**: All results will be framed as **associational relationships** (Observational study).

## Construct Validity & Limitations

1. **Proxy Measure**: The study uses the **Motor Task Performance composite score** (finger tapping + grip force) as a proxy for **proprioceptive acuity**. While Motor Task Performance is a validated measure of sensorimotor function, it primarily measures motor execution speed/force, not joint position sense. The final report will explicitly state this limitation and frame findings as "associations with sensorimotor performance" rather than "proprioceptive accuracy."
2. **Data Availability**: If raw fMRI data cannot be retrieved via HCP API, the analysis relies on verified preprocessed (ICA-FIX) data, which is the standard for such analyses and avoids the computational bottleneck of raw preprocessing.
3. **Observational Nature**: No causal claims can be made.
4. **Sample Size**: N is limited to a small sample of subjects, which may limit power to detect small effect sizes.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Use Motor Task Performance as proxy | HCP S1200 lacks direct proprioceptive tests. This is the best available validated proxy for sensorimotor function. |
| Derived-First Strategy (ICA-FIX) | Raw NIfTI preprocessing for a cohort of subjects on a limited-core CPU exceeds 6 hours. Verified ICA-FIX data is part of the HCP release and meets the "preprocessed" requirement. |
| Dynamic batch sizing | Required to meet SC-004 (7GB RAM limit) on GitHub Actions free tier. |
| FDR over Bonferroni | FDR provides higher power for the set of tests while controlling false discovery rate. |
| PCA/MANOVA for metrics | Network metrics are mathematically coupled; independent testing leads to pseudo-replication. |
| CI over Post-hoc Power | Post-hoc power is mathematically redundant with p-values; CIs provide better precision information. |
| Two-step Motion Control | Motion regression at time-series level + FD covariate at statistical level ensures robust motion control. |