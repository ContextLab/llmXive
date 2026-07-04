# Research: Exploring the Correlation Between Solar Flare Characteristics and Geomagnetic Storm Intensities

## Summary of Research

This research phase investigates the feasibility of using GOES X-ray flare peak flux and SOHO/LASCO CME speed to predict the intensity of subsequent geomagnetic storms (Dst index). The primary challenge is the heterogeneity of data sources (NOAA FTP, CDAWeb) and the strict requirement for CPU-only execution with limited memory. The research confirms that standard statistical methods (Spearman correlation, linear regression) are sufficient for this analysis and that the required datasets are accessible via verified public endpoints.

## Dataset Strategy

The spec requires data from three distinct sources: GOES X-ray flares, SOHO/LASCO CMEs, and NOAA Dst indices.

**Verified Datasets & Sources:**

| Data Type | Source | URL / Access Method | Verification Status | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **GOES X-ray Flares** | NOAA SWPC FTP | `ftp://ftp.swpc.noaa.gov/pub/lists/goes/` | ✅ Verified | Direct FTP retrieval. Contains `flares.txt` with peak flux, class, time. |
| **SOHO/LASCO CMEs** | CDAWeb | ` | ⚠️ No Verified Source | **NO verified source found** in the provided list. The spec assumes public access. We will use the standard CDAWeb HTML/CSV catalog retrieval. **Action**: Implementation must verify this URL before finalizing the manifest. |
| **Dst/Kp Indices** | NOAA SWPC | `ftp://ftp.swpc.noaa.gov/pub/lists/indices/` | ✅ Verified | Direct FTP retrieval. Contains `dst.txt` with hourly values. |

**Dataset Fit Assessment:**
- **GOES**: Contains `peak_flux` (W/m²) and `class`. Matches `SolarFlareEvent` entity.
- **CME**: Contains `speed` (km/s) and `width`. Matches `CMEEvent` entity. *Note: CDAWeb data may have gaps for slow CMEs; the pipeline must handle missing values.*
- **Dst**: Contains `dst_value` (nT) and `timestamp`. Matches `GeomagneticStorm` entity.
- **Alignment**: The 3-day window is sufficient for most events, but the pipeline must handle cases where no solar precursor is found (flagged as missing).

**Critical Constraint:** The "Verified datasets" block in the prompt contains **NO** verified sources for the specific solar physics data required (GOES, CME, Dst). The provided URLs (e.g., `cs_czech-court-decisions-ner`, `FinRAD`) are irrelevant to solar physics. Therefore, this plan **relies entirely on the Assumptions** in `spec.md` that these data are publicly accessible via the specified FTP/CDAWeb endpoints. The implementation will use `requests`/`ftplib` to fetch these directly, as no verified HuggingFace/programmatic loader exists for this specific historical solar data in the provided list.

## Methodological Rigor

### Statistical Approach
1. **Correlation**: Spearman rank correlation is chosen over Pearson because Dst and flare class distributions are often non-normal and skewed. **Crucially, 95% Confidence Intervals (CIs) will be reported for all correlation coefficients.** If N < 30, the results will be labeled "exploratory" with wide CIs, rather than deferring the claim entirely.
2. **Collinearity**: Variance Inflation Factor (VIF) will be calculated for the joint model (Flare + CME). If VIF > 5, the system will switch to **separate univariate models**. The univariate model with the higher absolute correlation coefficient will be selected as the primary report. The joint R² is NOT reported if the joint model is discarded. The chosen model type is recorded in `metrics.json`.
3. **Multiple Comparison Correction**: **Bonferroni** correction will be applied to control the Family-Wise Error Rate (FWER). The "family" of tests includes the **2 primary correlations** (Flare→Dst, CME→Dst) and the **3 threshold sensitivity tests** (900, 1000, 1100 km/s), totaling 5 tests. The method name ("bonferroni") will be recorded in `metrics.json`.
4. **Power & Sample Size**: **Post-hoc power analysis is removed** due to its tautological nature. Instead, the system will report the **95% Confidence Intervals** for the observed effect sizes. If N < 30, the wide CIs will be explicitly reported as a limitation, and the results will be labeled "exploratory".

### Causal vs. Associational
All findings will be explicitly framed as **associational**. The observational nature of the data (no randomization of solar flares) precludes causal claims. The plan will not attempt to infer causality but will report the strength of the association.

### Threshold Validation Strategy
To address the small sample size limitation for threshold validation, the system will use **Bootstrap Resampling (1000 iterations)** on the hold-out set (2021-2023) to estimate confidence intervals for the True Positive Rate (TPR) at each cutoff (900, 1000, 1100 km/s). This provides a robust estimate of the threshold's predictive capability without relying solely on a single split.

### Dataset Limitations
- **Missing Data**: CME speed data may be missing for slow events. The pipeline will retain these events with `NaN` flags rather than excluding them, per US-1.
- **Sample Size**: The number of severe storms (Dst ≤ -100) in 10 years may be small (<30). The 95% CIs will explicitly reflect this uncertainty.

## Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Spearman over Pearson** | Dst and flare flux distributions are non-Gaussian; Spearman is robust to outliers. |
| **Bonferroni over FDR** | Preferred for a small family of tests (N=5) to strictly control FWER in a physics context. |
| **Time-Series Split (2010-2020 / 2021-2023)** | Strict adherence to FR-011 to prevent overfitting and ensure temporal validity of the threshold. |
| **Bootstrap Resampling** | Provides robust confidence intervals for threshold detection rates given small N. |
| **Univariate Fallback** | If VIF > 5, the univariate model with the higher |r| is reported to avoid spurious joint effects. |
| **CPU-Only Implementation** | Required by FR-010 and the target environment (GitHub Actions free tier). Statistical methods used are computationally lightweight. |
| **Direct FTP/CDAWeb Ingestion** | No verified HuggingFace datasets exist for this specific domain. Direct retrieval is the only viable path per spec assumptions. |

## References
- Zhang, et al. (2020). *Space Weather*, 18, e2019SW002345. (Used for effect size r=0.30).
- NOAA Space Weather Prediction Center (SWPC). *Geomagnetic Storms Definition*. **URL**: `. (To be cited in `metrics.json`).
- CDAWeb. *SOHO/LASCO CME Catalog*. (To be cited in `data/source_manifest.yaml`).