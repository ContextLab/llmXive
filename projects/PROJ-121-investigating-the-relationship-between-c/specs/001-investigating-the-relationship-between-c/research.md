# Research: Cosmic Ray Anisotropy Solar‑Cycle Modulation

## Domain Context

Cosmic ray anisotropy at TeV–PeV energies is a key probe of local interstellar magnetic fields and solar modulation. The solar cycle modulates the heliospheric magnetic field, potentially imprinting periodicity on anisotropy measurements. This project tests the hypothesis that dipole amplitude and phase correlate with solar activity indices (sunspot number, solar wind speed, IMF magnitude).

## Dataset Strategy

| Dataset | Source URL | Load Method | Variables Used | Notes |
|---------|------------|-------------|----------------|-------|
| IceCube Muon Tracks | ` (Official Open Data Portal) | `pandas.read_parquet()` / `requests` | `timestamp`, `ra`, `dec`, `energy` | **Verified**: Official source for the past decade. Pipeline checks temporal coverage. |
| Pierre Auger Events | ` (Official Open Data Portal) | `pandas.read_parquet()` / `requests` | `timestamp`, `ra`, `dec`, `energy` | **Verified**: Official source for the past decade. Pipeline checks temporal coverage. |
| Solar Proxies | NOAA NGDC (via `requests`) | `pandas.read_csv()` (FTP/HTTP) | `date`, `sunspot_number`, `solar_wind_speed`, `imf_magnitude` | Daily resolution; gaps handled via interpolation (within a reasonable temporal window). |

**Dataset Fit Verification**:
- IceCube/Auger datasets contain `timestamp`, `ra`, `dec` → sufficient for HEALPix mapping and dipole fitting.
- Solar proxies from NOAA NGDC provide daily indices → sufficient for correlation with binned anisotropy series.
- **Critical Note**: The pipeline will verify that downloaded files span 2010–2020. If coverage is <90%, it will flag the result as 'partial_coverage' and proceed with available data.

## Statistical Methodology

### 1. Relative Anisotropy Correction (Crucial)
- **Problem**: Raw event maps are dominated by detector acceptance (geometric effects).
- **Solution**: Compute an 'acceptance map' (exposure) using the full dataset or a large reference sample. Calculate relative anisotropy: `δ(θ,φ) = (N_obs(θ,φ) - N_exp(θ,φ)) / N_exp(θ,φ)`.
- **Implementation**: Use `healpy` to create exposure maps. Fit spherical harmonics to the *relative* map to extract dipole/quadrupole.

### 2. Periodicity Detection
- **Method**: Lomb-Scargle periodogram (`scipy.signal.lombscargle`).
- **Noise Level**: Median power in low-frequency band (low-frequency range).
- **Significance**: Peak power relative to noise (σ) + Monte-Carlo FAP (a sufficient number of shuffles).

### 3. Cross-Correlation & Autocorrelation Handling
- **Primary Method**: Pearson/Spearman correlation (`scipy.stats.pearsonr`, `spearmanr`).
- **Autocorrelation Mitigation**:
 - **Block Bootstrap**: Block length = 2 × bin_size (10k resamples) for confidence intervals.
 - **Monte-Carlo Shuffle (FAP)**: As per **Spec US-2 and SC-005**, the **solar proxy time-series** is shuffled relative to the anisotropy series. This tests the null hypothesis that 'solar proxy values are independent of anisotropy'.
 - *Note*: While phase-randomization is statistically superior for autocorrelated data, the plan adheres to the spec's defined method. The limitation is acknowledged in the report.
- **Lagged Analysis**: Compute Cross-Correlation Function (CCF) with lags ±365 days to detect hysteresis.
- **Non-Linearity**: Supplement with Distance Correlation (dCor) for exploratory analysis.

### 4. Multi-Detector Consistency
- **Method**: Fisher's Method for combining p-values from IceCube and Auger.
- **Rationale**: Avoids the 'winner's curse' of conditional gates. Combines evidence regardless of individual significance.
- **Threshold**: Combined p-value ≤ 0.0017 (Bonferroni-corrected) or individual p-values ≤ 0.0017.

### 5. Power Analysis
- **Sample Size**: ~135 bins (10 years / 27 days).
- **Power**: At α=0.0017, power to detect r=0.4 is ~0.45. Power to detect r=0.6 is ~0.85.
- **Implication**: A non-significant result is a valid scientific outcome (upper limit). The blind validation (FR-011) will verify FPR ≤ 0.05 and Power ≥ 0.8 for injected signals of r≥0.6.

## Computational Feasibility

- **Data Volume**: ~1 GB total (parquet files). Fits in available RAM.
- **Runtime**: HEALPix mapping (Nside=64) is fast (<1 min per bin). Lomb-Scargle (10k points) <1 min. Bootstrap (resampling) ~minutes per test. Total <6 hours.
- **CPU-Only**: All libraries (`scipy`, `healpy`, `numpy`) have CPU wheels. No CUDA required.

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Official data lacks 2010–2020 coverage | Pipeline checks timestamp range; if <90% coverage, logs warning and proceeds with available data (partial success). |
| Solar proxy gaps >5 days | Interpolate gaps; if gap >5 days, flag interval as "low_confidence" in CSV. |
| Bootstrap resamples <30 | Reduce block length to 1×bin_size (as per FR-005). |
| LaTeX compilation failure | Use minimal `report.tex` template; pre-verify `pdflatex` on runner. |
| Autocorrelation invalidating p-values | Acknowledge limitation in report; use block-bootstrap to mitigate. |

## Decision Rationale

- **HEALPix Nside=64**: Balances resolution (≈1.8°) and computational cost.
- **27-day bin**: Matches Carrington rotation; aligns with solar rotation sub-structures.
- **Block Bootstrap (2×bin)**: Captures autocorrelation; reduces to 1×bin if insufficient blocks.
- **Monte-Carlo Shuffle (10k)**: Spec-mandated method (shuffle solar proxy).
- **Bonferroni α=0.0017**: Spec requirement; ensures strict control of family-wise error rate.
- **Relative Anisotropy**: Essential to remove detector geometry bias.
