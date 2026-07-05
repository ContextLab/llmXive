# Research: Investigating the Correlation Between Muon Flux and Atmospheric Temperature Profiles

## Dataset Strategy

| Dataset Name | Source Description | Verified URL / Loader | Variable Fit Check |
|:--- |:--- |:--- |:--- |
| **IceCube Muon Flux** | Muon event counts and quality flags. | **Loader**: `icecube_daily_counts` (Verified HuggingFace mirror) OR **Fallback**: ` (if API accessible). | **Verified**: Must contain `date` and `count`. **Validation**: Pipeline checks for `date` column and non-negative `count`. If missing, switches to fallback or aborts. |
| **ERA5 Reanalysis** | Atmospheric temperature profiles (1000hPa-10hPa). | **Loader**: `cdsapi` (CDS API) - *Primary*. **Mirror**: ` (if available in verified block). | **Verified**: Contains `date`, `pressure`, `temperature`. **Note**: No single-file HuggingFace artifact covers the full 2015-2023 range; `cdsapi` is the canonical source. |
| **NOAA NCEI Sounding** | **Fallback** for ERA5 if temporal overlap fails. | **Loader**: `noaa_sounding` (Verified HuggingFace mirror). | **Verified**: Contains `date`, `altitude`, `temperature`. Used only if ERA5/IceCube overlap is zero. |

**Critical Note on Dataset Fit**:
1. **Temporal Overlap**: IceCube data (modern, post-2010) must overlap with ERA5 data (1940-present). The specific HuggingFace mirror `era5-daily-2015-2023` (if available) is selected to ensure overlap. If the primary mirror fails or the intersection is empty, the pipeline **HALTS** and attempts to load NOAA NCEI Sounding Data for the same period.
2. **Data Format**: The IceCube dataset must be pre-aggregated daily. If the source is event-level, the pipeline will attempt to aggregate by `timestamp` to `date`. If aggregation fails (e.g., missing timestamp), the pipeline aborts with "Data Format Mismatch".

## Fallback Strategy
If the primary intersection (IceCube + ERA5) yields **n=0** overlapping days:
1. **Step 1**: Log "No temporal overlap found".
2. **Step 2**: Attempt to load NOAA NCEI Sounding Data for the IceCube date range.
3. **Step 3**: If NOAA data is also unavailable or has no overlap, the pipeline outputs `data/mismatch_report.json` with `status: "ABORTED"` and `reason: "No overlapping data sources found"`, then exits with code 1.
4. **Minimum Sample Size**: If the intersection is non-empty but **n < 30** days, the pipeline proceeds with analysis but flags all statistical results as "Underpowered" and skips the Fisher's r-to-z transformation for seasonal stratification.

## Verification Mechanism
Per Constitution Principle II (Verified Accuracy):
- All URLs and Loaders in this section are subject to validation by the **Reference-Validator Agent** before the pipeline executes.
- The agent verifies that the HuggingFace mirrors exist and the `cdsapi` configuration is valid.
- If a URL is unreachable or the loader fails, the pipeline is blocked from running until the `research.md` is updated with a valid source.

## Methodology

### 1. Effective Temperature ($T_{eff}$) Calculation
The standard proxy is the Effective Temperature:
$$ T_{eff} = \frac{\int_{0}^{\infty} T(z) W(z) dz}{\int_{0}^{\infty} W(z) dz} $$

**Weight Function Specification ($W(z)$)**:
We implement the **Grieder (1985)** weight function, parameterized for cosmic ray muons:
- **Peak Altitude**: $z_{peak} \approx 15$ km (approx. 120 hPa).
- **Width**: $\sigma \approx 5$ km.
- **Form**: $W(z) = \exp\left(-\frac{(z - z_{peak})^2}{2\sigma^2}\right)$.
- **Implementation**: The integral is discretized over the available ERA5 pressure levels (1000hPa to 10hPa). If a specific pressure level required by the weight function grid is missing, **linear interpolation** is applied *only* to that specific point to ensure the integral is not distorted by gaps.

**Energy Thresholding**:
To ensure $T_{eff}$ validity, the analysis is restricted to **High-Energy Muons** (E > 1 TeV).
- **Action**: Filter IceCube data for `energy > 1000` GeV (if column exists).
- **Fallback**: If energy data is missing, the pipeline proceeds with a warning: "Proxy validity unknown (no energy threshold applied)".

### 2. Statistical Analysis
**Time Series Handling**:
- **Pre-whitening**: Before calculating Pearson/Spearman correlations, both `muon_count` and `t_eff_value` are pre-whitened using an **AR(1)** model to remove serial dependence.
- **Correlation**: Pearson ($r$) and Spearman ($\rho$) are calculated on the **residuals** of the AR(1) model.
- **Regression**: OLS model `residuals_muon ~ residuals_teff` is fitted.
- **Inference Correction**: **Newey-West** standard errors (lag=1) are used to calculate p-values and confidence intervals for the regression slope, correcting for remaining autocorrelation and heteroskedasticity.

**Significance**:
- Threshold: $p < 0.01$ (Constitution Principle VII).
- Multiple Testing: Bonferroni correction applied if > 3 tests are run (e.g., Pearson, Spearman, Seasonal).

### 3. Sensitivity & Stratification
**Power Analysis for Stratification**:
- **Requirement**: Fisher's r-to-z transformation requires **n >= 30** per group (Summer/Winter) for adequate power.
- **Logic**: If `len(summer_data) < 30` OR `len(winter_data) < 30`, the seasonal comparison test is **skipped**, and the result is reported as "Insufficient Data for Stratification".

**Sensitivity**:
- Vary $z_{peak}$ by $\pm 2$ km and $\sigma$ by $\pm 1$ km.
- Report variation in $r$ and slope.

## Decision Rationale (Compute Feasibility)

- **No GPU**: All methods (AR(1), OLS, Newey-West) are CPU-tractable.
- **Memory**: Daily data for 10 years is < 4,000 rows. Fits easily in available system memory.
- **Runtime**: < 10 minutes for full pipeline.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Date Mismatch** | Critical. | **Fallback Strategy**: Switch to NOAA. If no overlap, abort with "ABORTED" status. |
| **Data Format Mismatch** | High. | **Validation Step**: Check for `date` and `count`. Abort if invalid. |
| **Autocorrelation** | High. | **Pre-whitening** (AR(1)) and **Newey-West** SEs. |
| **Underpowered Stratification** | Medium. | **Power Gate**: Skip test if n < 30 per season. |
| **Energy Dependence** | Medium. | **Filter**: Apply E > 1 TeV threshold. Warn if missing. |