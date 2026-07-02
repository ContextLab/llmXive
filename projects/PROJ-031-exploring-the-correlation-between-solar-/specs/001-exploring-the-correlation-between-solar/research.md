# Research: Exploring the Correlation Between Solar Flare Characteristics and Geomagnetic Storm Intensities

## Problem Statement

To what extent do solar flare X-ray peak flux and associated CME speeds **associate** with the minimum Dst index of subsequent geomagnetic storms, and can this relationship define a **temporal stability threshold** for severe space weather events?
*Note: The term "predictive" is avoided in favor of "temporal stability" because the outcome (Dst) is the same physical phenomenon used to define the threshold, preventing independent predictive validation.*

## Dataset Strategy

The spec requires data from three primary sources:
1.  **GOES X-ray Flares**: NOAA SWPC FTP (`ftp://ftp.swpc.noaa.gov/pub/lists/`).
2.  **CME Catalog**: CDAWeb SOHO/LASCO.
3.  **Geomagnetic Indices**: NOAA SWPC (Dst, Kp).

**Verified Dataset Limitation**: The "Verified datasets" block provided in the input contains NO verified sources for these specific solar physics datasets (the listed URLs are for NLP/Finance tasks). Therefore, the implementation **MUST** rely on direct programmatic ingestion from the NOAA/CDAWeb endpoints as specified in the Functional Requirements (FR-001, FR-002, FR-003).

**Ingestion Plan**:
-   **Flares**: Use `requests` to fetch GOES flare lists (text/CSV format) from the NOAA FTP mirror via HTTP.
-   **CMEs**: Use `requests` to fetch the LASCO CME catalog (CSV/ASCII) from CDAWeb.
-   **Dst**: Use `requests` to fetch Dst indices from NOAA SWPC.

**Data Availability Check**:
-   If direct ingestion fails (e.g., network restrictions on GitHub Actions), the pipeline will log a critical error and halt. A fallback mechanism to use a small synthetic dataset for *logic testing only* will be implemented, but no research conclusions will be drawn from it.
-   **Variable Fit**: The required variables (Flare Class, CME Speed, Dst Min) are standard outputs of these catalogs. However, CME speed data is often missing for slow events or fast events with poor visibility. The plan explicitly handles missing values (FR-001, US-1) by flagging rather than dropping.

## Statistical Methodology

### 1. Correlation Analysis (FR-004)
-   **Metric**: Spearman rank correlation (non-parametric, robust to outliers).
-   **Transformations**: X-ray flux (W/m²) will be log10-transformed to normalize the distribution of flare classes.
-   **Pairs**:
    -   (Log10 Flare Flux) vs. Dst Minimum
    -   CME Speed vs. Dst Minimum
-   **Significance**: P-values calculated; **Multiple-Comparison Correction** (Benjamini-Hochberg) applied to control Family-Wise Error Rate (FWER) at α ≤ 0.05 (FR-005).

### 2. Regression & Collinearity (FR-006)
-   **Model**: Separate Univariate Linear Regression (Ordinary Least Squares) to estimate $R^2$ for each predictor independently.
-   **Collinearity Check**: Variance Inflation Factor (VIF) is calculated **only on the complete-case intersection** (rows where both flare and CME data exist).
-   **Bias Acknowledgement**: The plan explicitly acknowledges that calculating VIF or joint models on the complete-case subset introduces **selection bias** because missingness is likely not random (e.g., fast CMEs might be better observed). Therefore, the primary analysis **defaults to separate univariate models** to avoid this bias. VIF is reported only as a descriptive metric on the complete subset, not as a basis for joint model selection.
-   **Fallback Logic**:
    -   If VIF > 5 (on complete cases): Confirm use of separate univariate models (already the default).
    -   If $R^2$ < 0.1: Test non-linear (piecewise) model (FR-014).
-   **Causal Framing**: All results explicitly labeled as **ASSOCIATIONAL** (FR-009). No causal claims will be made without randomization (which is impossible in this observational context).

### 3. Power Analysis (Sensitivity Approach)
-   **Reference**: Zhang et al. used as a reference, but not a fixed threshold.
-   **Parameters**: Target power ≥ 0.8, α ≤ 0.05.
-   **Sensitivity Analysis**: Instead of a binary pass/fail against a fixed $r=0.30$, the system will calculate the **Minimum Detectable Effect Size (MDES)** for the actual sample size $N$.
 - The report will state: "With N=XX, we can detect effects > r=YY at [deferred] power."
    -   This acknowledges the uncertainty in the true effect size (which varies from 0.1 to 0.6 in solar physics) and avoids the "power fallacy" (interpreting non-significance as evidence of no effect).
    -   If N < 30, a "Power Limitation Warning" is logged, and the MDES will likely be large, indicating the study is underpowered to detect moderate associations.

### 4. Threshold Identification (Internal Consistency)
-   **Definition**: Severe storm = Dst ≤ [threshold] (NOAA SWPC standard).
-   **Validation Strategy**: Time-series split (Train: 2010-2020, Test: post-2020 period).
-   **Circularity Acknowledgement**: The plan explicitly states that validating a CME speed threshold against Dst (the same physical metric used to define "severe") is a **circular validation**. It does not prove predictive power against external outcomes (e.g., satellite damage).
-   **Reframed Metric**: Instead of "True Positive Rate" (which implies prediction), the analysis calculates the **"Association Consistency Rate"**.
    -   **Denominator**: Only events where a CME **was detected** within a short-term window.
    -   **Numerator**: Events where CME speed > Threshold AND Dst ≤.
    -   **Exclusion**: Events with "No CME detected in window" are excluded from this specific calculation to avoid conflating detection failure with predictive failure (addressing methodology-468c80f6).
-   **Goal**: To determine if the association between high CME speed and severe Dst is **temporally stable** (consistent across the 2021-2023 hold-out set), not to validate a predictive model.

## Computational Feasibility

-   **Hardware**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).
-   **Data Size**: 10 years of solar data is < 100 MB. Processing is dominated by I/O and simple statistical operations, well within limits.
-   **Libraries**: `scipy`, `statsmodels`, `pandas` are CPU-optimized and do not require GPU.
-   **Runtime**: Estimated < 15 minutes for full pipeline.

## Risk Mitigation

-   **Missing Data**: Events with missing CME speed are retained with a flag. Analysis excludes them from the specific CME-Dst correlation but includes them in the Flare-Dst correlation if flare data exists.
-   **Network Failure**: Retry logic with exponential backoff for data ingestion.
-   **Power Limitation**: Explicit logging and documentation if N < 30, reporting MDES instead of a binary pass/fail.