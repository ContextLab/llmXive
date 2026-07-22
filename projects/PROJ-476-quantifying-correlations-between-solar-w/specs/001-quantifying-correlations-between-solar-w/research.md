# Research: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

## Summary of Scientific Question

The study investigates the associational relationship between solar wind composition parameters (proton density, temperature, helium abundance) and geomagnetic indices (Kp, Dst) over a multi-year period. Specifically, it tests whether variations in composition predict geomagnetic disturbances at lags of 0 to 6 hours, using rigorous statistical controls for multiple comparisons (Holm-Bonferroni) and autocorrelation (Thomson's Multitaper Method).

## Dataset Strategy

### Verified Datasets

The plan relies on the following verified, canonical public sources. **Note**: The "Verified datasets" block in the initial prompt contained unrelated speech/text data. This plan uses the **standard public sources** for solar wind physics, which are the only sources containing the required variables.

1. **ACE Solar Wind Composition**:
 * **Source**: NASA CDAWeb (Coordinated Data Analysis Web).
 * **Dataset**: ACE SWEPAM Level 2 (Proton Density, Temperature) and ACE SWICS Level 2 (Helium Abundance).
 * **URL**: `
 * **Access Method**: Programmatic download via CDAWeb API or direct FTP/HTTP to `.
 * **Variables**: `N_p` (cm⁻³), `T_p` (K), `He2+_ratio` (%).

2. **NOAA Geomagnetic Indices**:
 * **Source**: NOAA Space Weather Prediction Center (SWPC).
 * **Dataset**: Kp Planetary Indices and Dst Index.
 * **URL**: ` and `.
 * **Access Method**: Direct CSV/ASCII download from the SWPC website.
 * **Variables**: `kp` (0–9), `dst` (nT).

**Data Acquisition Strategy**:
* **Fetch**: Download Level 2 data for 1998–2020.
* **Sync**: Resample to 1-hour UTC grid.
* **Interpolation**: Linear interpolation for gaps ≤ 6 hours.
* **Validation**: Ensure all required columns exist; abort if missing.

## Statistical Methodology

### Correlation Analysis

* **Metrics**: Pearson $r$ and Spearman $\rho$.
* **Lags**: 0, 1, 2, 3, 6 hours.
* **Scope**: Full continuous time series (not filtered for storms) to avoid selection bias.
* **Hypothesis Tests**: 30 tests (3 vars × 2 indices × 5 lags).

### Autocorrelation Adjustment (FR-010 Replacement)

* **Problem**: Solar wind and geomagnetic time series exhibit long-range dependence (/f noise) and 27-day solar rotation cycles. Simple lag-1 autocorrelation (Pyper & Peterman) is insufficient and leads to under-corrected p-values (false positives).
* **Solution**: Use **Thomson's Multitaper Method (MTM)** to estimate the spectral density and calculate **Effective Degrees of Freedom (EDF)**.
 * **Method**: MTM provides a robust estimate of the spectral density $S(f)$ by averaging multiple orthogonal tapers (Slepian sequences).
 * **EDF Calculation**: $EDF = \frac{(\int S(f) df)^2}{\int S^2(f) df} \times \frac{N}{B}$, where $B$ is the bandwidth. This accounts for the true correlation structure.
 * **Implementation**: Use `nitime` or `scipy.signal` multitaper implementation.
* **Application**: Calculate the t-statistic for correlation: $t = r \sqrt{\frac{EDF - 2}{1 - r^2}}$. Compute raw p-value from the t-distribution with $df = EDF - 2$.

### Multiple Comparison Correction (FR-004 Replacement)

* **Method**: **Holm-Bonferroni Step-Down Procedure**.
* **Reason**: The 5 lags for a single variable pair are not independent (overlapping time windows). Bonferroni is overly conservative. Holm-Bonferroni controls the Family-Wise Error Rate (FWER) while maintaining higher power for dependent tests.
* **Procedure**:
 1. Calculate raw p-values for all 30 tests.
 2. Sort p-values: $p_{(1)} \le p_{(2)} \le... \le p_{(30)}$.
 3. For $i = 1$ to 30: if $p_{(i)} < \frac{0.05}{30 - i + 1}$, reject $H_{(i)}$; else stop.
* **Reporting**: Raw p-value and Holm-Bonferroni-corrected p-value for each test.

### Effect Size Threshold (SC-003 Compliance)

* **Threshold**: $|r| > 0.5$ (pre-registered).
* **Validation**: Check if any pair in the held-out set (2018–2020) exceeds this threshold with **Holm-Bonferroni-corrected** significance.
* **Validation Procedure**:
 1. Compute correlations on 2018–2020 data ONLY.
 2. Compute **EDF** using MTM on 2018–2020 data ONLY.
 3. Apply **Holm-Bonferroni** correction to the 30 p-values from 2018–2020.
 4. Flag pairs where $|r| > 0.5$ AND Holm-Bonferroni $p < 0.05$.

## Statistical Rigor & Limitations

* **Observational Nature**: All findings are **associational**. No causal claims.
* **Collinearity**: Proton density and helium abundance may be correlated. Variance Inflation Factor (VIF) will be calculated; results reported descriptively without claiming independent effects.
* **Power**: The large sample size (multi-year × 8760 hours) provides high power, but the effective sample size is reduced by autocorrelation (accounted for by MTM).
* **Missing Data**: Gaps > 6 hours are excluded, potentially reducing power slightly.

## Decision Rationale

* **CPU-First**: The analysis involves classical statistics (correlation, p-values) on a large-scale dataset. This is trivial for a CPU. No GPU is required.
* **Data Source**: The plan uses the standard public sources (CDAWeb/NOAA) to ensure **real results**. The provided "Verified datasets" block in the prompt was invalid for this domain.
* **Validation**: The 2018–2020 hold-out period ensures the model is not overfitting to the training data (1998–2017). The EDF and correction are recalculated independently for the test set to ensure validity.
* **Methodology**: Thomson's MTM is superior to lag-1 methods for geophysical time series with long-range dependence. Holm-Bonferroni is superior to Bonferroni for dependent lagged tests.