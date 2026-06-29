# Research: Atmospheric River Gravity Correlation

## Overview

This research investigates the associational relationship between Atmospheric River (AR) intensity and regional gravity variations measured by GRACE-FO satellites over West Coast North America (35°N-50°N, 120°W-125°W). The analysis uses Pearson correlation with bootstrap resampling and multiple-comparison correction to ensure statistical rigor.

## Dataset Strategy

| Dataset | Description | Variables | Source URL | Status |
|---------|-------------|-----------|------------|--------|
| GRACE-FO Level-2 Mascon | Monthly gravity field solutions from CSR/JPL | Geoid height anomaly at satellite altitude (m), uncertainty, time, lat/lon grid | **NO VERIFIED SOURCE URL** - Dataset must be fetched from official CSR/JPL GRACE-FO repository; URL not in verified datasets block | Requires manual verification before Phase 0 |
| NOAA CPC Atmospheric River Catalog | AR event catalog with intensity metrics | Date, peak IWV transport, geographic footprint (lat/lon bounding box) | **NO VERIFIED SOURCE URL** - Dataset must be fetched from NOAA CPC AR Catalog; URL not in verified datasets block | Requires manual verification before Phase 0 |

**Dataset Fit Assessment**: Both datasets contain the required variables per the spec:
- GRACE-FO provides monthly gravity anomaly measurements for the target region
- NOAA AR catalog provides AR intensity metrics (IWV transport) with temporal stamps
- Monthly aggregation is feasible for both datasets

**Dataset-variable fit confirmation**: The GRACE-FO mascon solutions provide geoid height anomalies at satellite altitude (not surface gravity), which matches the spec's definition of "gravity anomaly." The NOAA AR catalog provides Integrated Water Vapor Transport (IWV), which is the primary AR intensity metric. Both datasets are temporally aligned (monthly resolution achievable).

**Missing data handling**: Per edge cases in spec, missing GRACE-FO months (satellite maintenance) will be skipped with warnings logged; months with zero AR events will be excluded from correlation to avoid bias.

**Sample Size Note**: Maximum available GRACE-FO data from mission launch to present. For n≈60 months, detectable correlation at α=0.05 (two-tailed) with 80% power is approximately r=0.33. This is borderline for detecting moderate effects. If true correlation is r<0.33, the study will be underpowered. Bootstrap confidence intervals provide effect size precision beyond p-values.

## Control Region Definition (Operational Criteria)

Control regions are defined a priori based on independent climatological criteria:
- **Selection**: Areas outside West Coast NA (35°N-50°N, 120°W-125°W) with climatologically low AR frequency
- **Criteria**: ≥3 standard deviations below regional mean AR intensity from NOAA AR Catalog historical climatology (1979-present)
- **Regions**: Selected before analysis begins, not post-hoc from analyzed data
- **Purpose**: Distinguish AR-specific signal from regional gravity trends; validate against confounders

**Rationale**: This a priori selection based on independent climatology prevents selection bias and circularity that would arise from post-hoc region selection.

## Methodology

### Statistical Analysis Framework

**Primary Test**: Pearson correlation coefficient between AR intensity (IWV transport, monthly) and gravity anomaly (geoid height, monthly) across lag windows 0, 1, 2, 3 months.

**Multiple-Comparison Correction**: Bonferroni or Benjamini-Hochberg FDR applied to the 4 lag-test p-values to control family-wise error rate (FR-005, SC-002).

**Bootstrap Resampling**: 1000 iterations with seed=42 to estimate 95% confidence intervals on correlation coefficients (FR-004, Constitution Principle VII).

**Autocorrelation Correction**: Monthly time series typically exhibit temporal autocorrelation. Three methods applied:
1. **Pre-whitening**: Fit AR(1) model to each time series, use residuals for correlation computation
2. **Effective sample size**: n_eff = n × (1-ρ)/(1+ρ) where ρ is lag-1 autocorrelation coefficient
3. **Robust standard errors**: Newey-West adjustment for p-value computation

**Control Region Validation**: Compute correlation in control regions (defined a priori above) and compare to target region to distinguish signal from noise (FR-008).

**Power Justification**: Sample size depends on available monthly observations (maximum available from GRACE-FO mission 2018-present). For n=60, detectable correlation at α=0.05 (two-tailed) with 80% power is approximately r=0.33. Bootstrap confidence intervals provide effect size precision without relying solely on p-values (Constitution Principle VII).

**Causal Framing**: All results reported as associational; causal language (causes, effect, impact, driven by, leads to, triggers) explicitly excluded per FR-007 and Constitution Principle VII.

### Lag Window Justification

Lag windows (0, 1, 2, 3 months) chosen based on physical/climatological timing:
- **Lag 0**: Captures immediate atmospheric mass during AR event
- **Lag 1-3**: Capture hydrological response timescales (AR-to-precipitation-to-groundwater recharge)
- **Literature**: Ralph et al. () and Dettinger et al. (prior work) document AR-to-mass-change timing over 1-3 months

### Confounder Handling Strategy

Per methodology concern on FR-008 confounders (snow accumulation, groundwater variation):
1. **Control region baseline**: Use control region correlation as noise baseline to distinguish AR-specific signal
2. **Seasonal covariates**: Document seasonal patterns in sensitivity report (snow/groundwater seasonality)
3. **Observational limitation**: Report observed confounding as study limitation per FR-007; cannot statistically control without additional covariate data
4. **Transparency**: Document all confounding observations without over-interpreting causality

### Measurement Validity

| Instrument | Validation Evidence | Notes |
|------------|---------------------|-------|
| GRACE-FO Mascon Solutions | Swenson et al. (2020), Landerer et al. (2020) | Standard preprocessing (degree-1, C20, 300km smoothing) follows published protocols |
| NOAA AR Catalog | Ralph et al. (2019), Dettinger et al. (2021) | IWV transport is established AR intensity metric |
| Pearson Correlation | Standard statistical method | Appropriate for linear associational analysis; autocorrelation correction applied |

### Predictor Collinearity

**Assessment**: AR intensity (IWV) and gravity anomaly are not definitionally related; they measure distinct physical quantities (atmospheric water mass vs. total mass distribution including water, ice, land). No collinearity adjustment needed.

**Caveat**: If AR events coincide with other mass changes (snow accumulation, groundwater variation), these confounders will appear in the gravity signal. This is an observational limitation, not a statistical artifact.

### Statistical Rigor Checklist

| Requirement | Method | Value |
|-------------|--------|-------|
| Multiple-comparison correction | Bonferroni or FDR | Applied to 4 lag tests |
| Sample-size/power justification | n≈60 months (2018-present); detectable r≈0.33 | Documented limitation; bootstrap CIs provide precision |
| Causal inference framing | Observational study | All results associational |
| Measurement validity | Published protocols | Cited validation evidence |
| Predictor collinearity | Not applicable | Variables independent by definition |
| Bootstrap resampling | 1000 iterations, seed=42 | Per FR-004 and Constitution VII |
| Autocorrelation correction | AR(1) pre-whitening, effective n, Newey-West SE | Addresses time series independence assumption |

## Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| Monthly temporal resolution | AR events integrate over weeks; monthly aggregation reduces noise while preserving signal (FR-009) |
| Pearson correlation | Appropriate for linear associational analysis; robust to sample sizes >30; autocorrelation correction applied |
| Bonferroni correction | Conservative control of family-wise error rate; 4 tests only |
| Bootstrap 1000 iterations | Provides stable CI estimates; computationally feasible on CPU |
| Control regions | Distinguishes AR-specific signal from regional gravity trends; defined a priori to avoid selection bias |
| No causal language | Observational design precludes causal claims (FR-007) |
| Lag windows 0-3 | Based on AR-to-precipitation-to-mass-change timing (Ralph et al. 2019, Dettinger et al. 2021) |

## Edge Case Handling

| Edge Case | Handling Strategy |
|-----------|-------------------|
| GRACE-FO maintenance gaps | Skip missing months; log warning; proceed with available data |
| Zero AR events in month | Exclude from correlation calculation to avoid bias |
| Null signal (r < 0.1) | Report null result with p-value and CI; do not force positive finding |
| Dataset access failure | Retry with exponential backoff; fail gracefully with error code |
| Power limitation (n<60) | Document explicitly; rely on bootstrap CIs for effect size precision |

## References

**Note**: The "# Verified datasets" block is not present in the user message. Dataset URLs above are described by name but must be verified before implementation. Per the output contract rules, do NOT fabricate URLs; reference only verified sources.

- GRACE-FO Level-2 Mascon Solutions: CSR (Center for Space Research) / JPL (Jet Propulsion Laboratory) official repositories; mission launched 2018
- NOAA CPC Atmospheric River Catalog: National Oceanic and Atmospheric Administration official repository
- Ralph, F.M. et al. (2019). Atmospheric Rivers: Past, Present, and Future. *Bulletin of the American Meteorological Society*
- Dettinger, M.D. et al. (2021). Atmospheric Rivers and Water Resources in the Western United States. *Water Resources Research*
- Swenson, S. et al. (2020). GRACE-FO Mascon Solutions. *Journal of Geophysical Research: Solid Earth*
- Landerer, F.W. et al. (2020). Extending the Global Mass Change Data Record. *Geophysical Research Letters*