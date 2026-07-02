# Research: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

## Scientific Background

The relationship between solar wind composition and geomagnetic activity is a core heliophysics question. While dynamic pressure and IMF are established drivers, the contribution of proton density, temperature, and helium abundance remains under‑explored. This project quantifies lagged correlations between ACE composition parameters and NOAA Kp/Dst indices over a multi‑decadal span.

### Key Variables
- **Proton Density (`N_p`)**: cm⁻³ (SWEPAM Level 2)
- **Proton Temperature (`T_p`)**: K (SWEPAM Level 2)
- **Helium Abundance (`He2+_ratio`)**: dimensionless (SWICS Level 2)
- **Kp Index**: 0‑9 (hourly, resampled)
- **Dst Index**: nT (hourly)

## Verified Datasets

| Dataset | Source URL | Format | Notes |
|:--- |:--- |:--- |:--- |
| **ACE Solar Wind Composition** | ` | ZIP (CSV/NetCDF) | Contains `N_p`, `T_p`, `He2+_ratio`. |
| **ACE Test Data** | ` | TSV | Used for unit‑test validation of variable names. |
| **ACE Challenge Set** | ` | JSONL | Structural validation. |
| **UTC Info** | ` | JSON | Leap‑second handling. |
| **NOAA Geomagnetic Indices** | *Verified source not present in the # Verified datasets block* | *N/A* | **Critical Gap** – without a verified URL the pipeline cannot fetch Kp/Dst data. The implementation will abort until a verified source is added. |

> **Dataset Fit**: ACE files provide all required composition variables. NOAA Kp/Dst data are required but currently lack a verified download URL; this violates Principle II of the Constitution and must be resolved before execution.

## Dataset Strategy

1. **Download ACE** from the verified HuggingFace URL.
2. **Attempt NOAA download** – if a verified URL is supplied later, the fetch script will retrieve hourly Kp/Dst; otherwise the pipeline aborts with a clear error.
3. **Validate** that ACE files contain `N_p`, `T_p`, `He2+_ratio`. Missing any triggers abort with message “Missing required variable: `<name>`”.
4. **Align** to 1‑hour UTC grid, linearly interpolate gaps ≤ 6 h, and *exclude* longer gaps from correlation (they remain in visualisations).
5. **Split** into training (1998‑2017) and validation (2018‑2020) periods for reporting only; statistical thresholds are **global**.

## Statistical Methodology

### Effective Sample Size (Neff)

Solar wind and geomagnetic series exhibit strong autocorrelation. For each composition‑index pair we compute lag‑1 autocorrelations (ρ₁, ρ₂) on the **full 1998‑2020 series**. To accommodate non‑stationarity we calculate a rolling‑window (30‑day) lag‑1 autocorrelation, take the median value for each series, and then apply the Pyper & Peterman (1998) formula:

```
Neff = N * (1 - ρ₁·ρ₂) / (1 + ρ₁·ρ₂)
```

For lagged pairs (e.g., Xₜ vs Yₜ₊ₖ) we use the same product ρ₁·ρ₂, which is a standard extension for lagged correlations.

### Correlation Coefficients

- Pearson *r* (linear) and Spearman *ρ* (rank) computed at lags 0, 1, 2, 3, 6 h.
- Raw p‑values are derived from the *t*‑distribution using the corresponding Neff.

### Multiple‑Comparison Control

- Total tests = 3 params × 2 indices × 5 lags = **30**.
- Global Bonferroni factor = 30 → adjusted α = 0.05 / 30 ≈ 0.00167.
- The same α_adj is applied to **both** training and validation results (fulfilling FR‑010 and SC‑003).

### Effect‑Size Threshold

A pair is flagged “practically significant” when |r| > 0.5 **and** Bonferroni‑corrected p < 0.05.

### Interpolation Bias Mitigation

Linear interpolation ≤ 6 h is used solely for creating a complete time grid. Interpolated points are **excluded** from the correlation calculations to avoid biasing r and p‑values; they remain for visualisation only.

### Dependency of Tests

Although lagged tests share data points, the Bonferroni correction is retained per community convention for exploratory heliophysics studies. This conservative approach is documented (see Scientific Soundness concerns).

## Compute Feasibility

- Data ≈ 175 k rows → fits comfortably in memory.
- All calculations use `scipy`/`statsmodels`, CPU‑only.
- Estimated total runtime < 1 h, RAM < 2 GB.

## Risks & Mitigations

| Risk | Mitigation |
|:--- |:--- |
| Missing NOAA source | Abort with explicit error; Constitution Principle II marked FAIL. |
| Large gaps (>6 h) | Exclude from correlation; log warning. |
| Autocorrelation non‑stationarity | Use median of rolling‑window ρ₁, ρ₂ for Neff. |
| Interpolation bias | Exclude interpolated points from statistical tests. |
| Dependent tests | Justify Bonferroni conservatism; note possible future FDR use. |
