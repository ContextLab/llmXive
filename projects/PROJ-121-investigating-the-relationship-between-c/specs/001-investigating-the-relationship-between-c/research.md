# Research: Cosmic Ray Anisotropy Solar‑Cycle Modulation

## Summary

This research phase validates the feasibility of the proposed pipeline, identifies verified data sources, confirms dataset-variable fit, and outlines the statistical methodology under CPU constraints. It explicitly addresses the fundamental limitation of the 10-year window for 11-year cycle detection and defines fallback strategies for unverified data sources.

## Dataset Strategy

| Dataset | Purpose | Verified URL | Notes |
|---------|---------|--------------|-------|
| IceCube Muon Tracks | Event data for anisotropy analysis | ` | Parquet format; contains event timestamps, directions. Verified. |
| Pierre Auger Surface Detector | Event data for anisotropy analysis | *No verified source in input block* | **Fallback Strategy**: If no verified URL is found, the pipeline proceeds with IceCube-only analysis and logs a warning. Combined analysis is skipped if Auger is unavailable. |
| NOAA Solar Indices (Sunspot, Wind, IMF) | Solar activity proxies | *No verified URL in input block* | Plan will use NOAA NGDC standard API/FTP. If no verified URL, the system fetches via standard endpoints and logs the source name only. |

**Dataset-Variable Fit Assessment**:

- **IceCube**: Verified HuggingFace dataset contains event data (timestamps, directions) suitable for HEALPix mapping and dipole fitting. Matches spec requirements for 2010-2020 interval.
- **Pierre Auger**: **MISMATCH ALERT** – No verified URL provided. The spec requires Auger data, but the input block only lists IceCube. **Action**: The plan explicitly states that Auger analysis is conditional on data availability. If unavailable, the system proceeds with IceCube-only.
- **Solar Proxies**: NOAA NGDC provides sunspot number, solar wind speed, and IMF magnitude. No verified URL in input block; plan will reference NOAA by name and rely on standard API/FTP access.

**Interval Count Calculation**:
- Time Window: -01-01 to 2020-12-31 = [deferred].
- Bin Size: Default configuration.
- Expected Intervals: A large number of days divided by a divisor yields approximately 135.
- **Correction**: The spec mentioned ~115 rows; the correct calculation yields ~135. The success criteria (SC-002) will be updated to expect ≥135 rows (or [deferred] of 135).

## Statistical Methodology

### Lomb-Scargle Periodogram
- **Purpose**: Search for periodic signals in the dipole amplitude time series.
- **Limitation**: The 10-year window (T=10) gives a frequency resolution Δf ≈ 0.1 cycles/year. The multi-year cycle is indistinguishable from the zero-frequency (DC) component or a linear trend.
- **Implementation**: `scipy.signal.lombscargle` or `astropy.timeseries.LombScargle`.
- **Frequency Grid**: Cover 0.05–1.0 cycles/year.
- **Noise Level**: Median power in low-frequency band (0.01–0.05 cycles/year).
- **Significance**: Report peak power relative to noise level and Monte-Carlo FAP. **Crucially**, the report will include a "Resolution Warning" stating that the 11-year peak cannot be statistically distinguished from DC/trend given the window.

### Block Bootstrap (Data-Driven)
- **Purpose**: Estimate confidence intervals for Pearson/Spearman correlation coefficients.
- **Block Length**: Instead of a fixed "2x bin size", use a data-driven approach (Stationary Bootstrap) to estimate the autocorrelation time of the residuals.
 - **Minimum**: 27 days (Constitution Principle VII).
 - **Maximum**: Available series length.
 - **Fallback**: If the estimated autocorrelation time is shorter than 27 days, use 27 days.
- **Resamples**: 10,000 permutations.
- **Fallback**: If the number of resulting blocks is < 10, switch to Fourier-based surrogate generation (10,000 permutations) as per FR-005.

### Monte-Carlo Shuffle (Corrected)
- **Purpose**: Estimate False Alarm Probability (FAP) under null hypothesis (independence).
- **Method**: **Phase randomization of BOTH series** (or block-shuffling both) to preserve the temporal autocorrelation structure of both the anisotropy and the solar proxy. Shuffling only the proxy is incorrect as it destroys the null hypothesis validity for time-series.
- **Metric**: Proportion of shuffled correlations ≥ observed |r|.

### Phase-Sensitive Analysis
- **Purpose**: Account for the vector nature of anisotropy (dipole phase).
- **Method**: Calculate circular-linear correlation (e.g., Mardia's test) between the dipole phase and solar activity. Perform lagged cross-correlation with phase wrapping.

### Multiple Testing Correction
- **Method**: Bonferroni correction for 6 tests (2 detectors × 3 proxies).
- **Adjusted α**: 0.0017 (0.01 / 6).
- **Positive Result**: |r| ≥ 0.4 AND p ≤ 0.0017. **Note**: The |r| ≥ 0.4 threshold is a spec requirement but is physically unlikely for cosmic ray anisotropy (typically <0.1%). The report will include a "Physical Plausibility Note" explaining this.

## Compute Feasibility

- **CPU Constraints**: All methods (Lomb-Scargle, bootstrap, shuffle) are CPU-tractable. No GPU required.
- **Memory**: Data subset to ~7 GB RAM via sampling (e.g., events >10 TeV or [deferred] random sample) if the full dataset exceeds limits. HEALPix Nside maps at a moderate resolution are small.
- **Runtime**: 10-year data, ~135 intervals, 10k bootstrap/shuffle iterations estimated at <4 hours on 2 CPU.
- **Libraries**: `scipy`, `astropy`, `healpy`, `numpy`, `statsmodels` all have CPU wheels; no CUDA dependencies.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Auger data unavailable | Loss of multi-detector consistency | Fallback to IceCube-only; log warning; report partial results. Combined analysis skipped. |
| Solar proxy gaps >5 days | Biased correlation estimates | Interpolate gaps (linear) or exclude intervals; document in report. |
| Bootstrap blocks <10 | Invalid confidence intervals | Switch to Fourier phase randomization (FR-005). |
| -hour runtime exceeded | Pipeline failure | Optimize by sampling events; reduce resamples to a manageable threshold if needed; log warning. |
| 11-year cycle resolution | Cannot distinguish from DC/trend | Report "Resolution Warning" in all plots and the report. Do not claim detection. |

## Decision Rationale

- **Method Selection**: Lomb-Scargle is standard for unevenly spaced time series; data-driven block bootstrap preserves temporal autocorrelation; Monte-Carlo shuffle (both series) provides robust FAP.
- **CPU-Only**: All chosen methods run efficiently on CPU; no deep learning or large-LLM inference required.
- **Dataset Strategy**: Prioritize verified IceCube source; handle Auger gap transparently; rely on NOAA for solar proxies.
- **Sampling**: Essential to fit the 10-year dataset into 7GB RAM.
