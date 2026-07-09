# Research: Reconstructing Solar Irradiance from Historical Sunspot Records

## Overview

This research document outlines the dataset strategy, methodological choices, and statistical rigor for reconstructing Total Solar Irradiance (TSI) from historical Group Sunspot Number (GSN) records. The core hypothesis is that a cycle‑specific non‑linear regression model (Random Forest or Gaussian Process) will outperform the 2007 baseline by capturing cycle‑to‑cycle variability in the sunspot‑TSI relationship. Crucially, the reconstruction is anchored to physical reality via a **Two-Stage Calibration** process that uses cosmogenic isotopes to adjust for distributional shifts between the satellite and pre-satellite eras.

## Dataset Strategy

| Dataset | Purpose | Verified Source | Loading Method | Notes |
|---------|---------|-----------------|----------------|-------|
| GSN (Group Sunspot Number) | Primary predictor (early modern period–present) | SILSO Royal Observatory of Belgium: <https://www.sidc.be/silso/datafiles> (Direct link to `gsn_monthly.csv`) | `pandas.read_csv()` after manual placement in `data/raw/` | Contains daily/monthly GSN values; missing values will be interpolated linearly. |
| SORCE/TIM TSI | Ground truth for training (early 2000s–2015) and validation (2016–present) | NASA SORCE/TIM: <https://lasp.colorado.edu/home/sorce/data/> (Direct link to `TIM_v5.csv`) | `pandas.read_csv()` after manual placement in `data/raw/` | Satellite‑era TSI measurements; used as target variable. |
| CMIP6 v3.2 | External comparison for overlapping period | ESGF CMIP6: <> (Filter: `variable: rsdt`, `experiment: historical`) | `pandas.read_parquet()` after manual placement in `data/raw/` | Used to compute correlation coefficient vs. new reconstruction. Requires full forcing dataset, not test shards. |
| 14C Cosmogenic Isotope | Independent proxy for solar activity (pre‑satellite) | NOAA Paleoclimate: <https://www.ncei.noaa.gov/access/paleo-search/> (Search for "IntCal20" or "Δ14C") | `pandas.read_csv()` after manual placement in `data/raw/` | Provides an external anchor for variance validation. |
| 10Be Cosmogenic Isotope | Independent proxy for solar activity (pre‑satellite) | NOAA Paleoclimate: <https://www.ncei.noaa.gov/access/paleo-search/> (Search for "10Be") | `pandas.read_csv()` after manual placement in `data/raw/` | Same purpose as 14C. |
| Mg II Index (facular proxy) | Optional facular proxy for the satellite era | NOAA: <> | `pandas.read_csv()` | Used if available; otherwise model relies on GSN + cycle_phase. |

> **Critical Note**: All URLs point to primary, canonical sources. The pipeline requires manual download of specific CSV/Parquet files from these portals to ensure data integrity. Each file must be checksum‑verified before processing to satisfy the Constitution’s Data Hygiene and Verified Accuracy principles.

## Methodological Choices

### Model Selection: Random Forest vs. Gaussian Process

- **Random Forest**: Preferred for robustness on the limited satellite‑era dataset; hyper‑parameters (`n_estimators≤100`, `max_depth≤10`) tuned via 5‑fold CV.
- **Gaussian Process**: Optional for richer uncertainty quantification; a sparse approximation (`SparseGaussianProcessRegressor`) will be used if computationally feasible on CPU.
- **Decision**: Default to Random Forest; switch to GP only if uncertainty bands are deemed insufficient.

### Cycle‑Specific Calibration

- **Feature Engineering**: Solar cycle boundaries are identified using the Hilbert‑Huang Transform (HHT) via the `pyhht` library. From the HHT output we compute a continuous **cycle_phase** (fraction of the way through the current cycle, 0-1) and one‑hot encode it into a set of bins. This replaces the raw `cycle_id` to reduce collinearity while preserving cycle‑specific information.
- **Rationale**: `cycle_phase` is a **time-based** feature derived from the temporal structure of the GSN series, independent of the GSN magnitude. This prevents the model from memorizing "Cycle 23 = high TSI" and forces it to learn the physics of cycle progression.

### Two-Stage Calibration (Addressing Distributional Shift)

1. **Stage 1 (Satellite Training)**: Train the model on 2003-2015 data using GSN, `cycle_phase`, and facular proxies.
2. **Stage 2 (Isotope Anchoring)**: Apply the trained model to the pre-satellite GSN data. Then, adjust the model's uncertainty bands and bias by minimizing the difference between the *reconstructed variance* and the *empirical variance* of the 14C/10Be proxies for the same periods (Maunder, Dalton, Modern). This ensures the reconstruction is not just an extrapolation but is anchored to physical reality.

### Validation Strategy

1. **Standard Hold‑Out Validation**: Train on 2003‑2015, validate on 2016‑present.
2. **Leave-One-Cycle-Out (LOCO) CV**: Within the training period, iteratively hold out each complete solar cycle, train on the remaining cycles, and evaluate on the held‑out one. This provides a validation on a physically distinct cycle, mitigating over‑fit to a single regime.
3. **Proxy Validation**: Compare reconstructed TSI for 1610‑2002 against 14C and 10Be isotope records (aligned by year). Compute Pearson correlation and variance similarity; report statistical agreement.
4. **Facular Proxy Check**: If Mg II data are available, include it as an additional feature and assess its impact on validation metrics.

### Baseline Comparison

- Treat the 2007 baseline (Lean et al.) as a **fixed, external reference**. Do **not** re-tune or re-run the baseline on the 2003-2015 split.
- Compute RMSE reduction percentage and correlation with CMIP6, requiring the new model to achieve ≥ 15 % RMSE reduction and at least equal correlation. This ensures the comparison is fair and not confounded by baseline re-tuning.

### Statistical Significance Testing

- **Block‑Bootstrap Resampling**: Perform 1 000 iterations on the reconstructed TSI variance **and** on the variance of the isotope proxies for the same periods (Maunder, Dalton, Modern).
- **Multiple‑Comparison Correction**: Apply Bonferroni correction for the three pairwise comparisons (α = 0.05/3).
- **Outcome**: Table of corrected p‑values, 95 % confidence intervals, and a statement of significance (p < 0.05 after correction). The test validates whether the reconstruction's variance is consistent with the independent proxy's variance, not just internal consistency.

## Statistical Rigor

### Multiple‑Comparison Correction
- Bonferroni correction applied to variance‑difference tests across the three minima.

### Sample Size / Power Justification
- Satellite‑era training set (~12 years) is limited; we mitigate via 5‑fold CV, LOCO‑CV, and OOB error estimation. Power limitations are acknowledged in the discussion.

### Causal‑Inference Assumptions
- All analyses are strictly associational; no causal claims are made about sunspot numbers driving TSI.

### Measurement Validity
- GSN is a vetted solar activity proxy (SILSO).
- SORCE/TIM TSI values are the current gold‑standard satellite measurements.
- Cosmogenic isotopes are established proxies for long‑term solar activity.

### Predictor Collinearity
- By using **cycle_phase** (time-based) instead of raw `cycle_id`, we reduce direct collinearity with GSN. Remaining correlation is reported descriptively; feature importance is interpreted cautiously.

### Construct Validity
- The ≥15% RMSE reduction on satellite data is a *necessary but insufficient* condition. The *sufficient* condition for historical validity is the agreement with isotope proxies in the pre-satellite era. This hierarchy prevents conflating modern fit with historical truth.

## Compute Feasibility

- **Hardware Constraints**: GitHub Actions free‑tier runner (2 CPU, ~7 GB RAM, no GPU).
- **Model Training**: Random Forest with ≤ 100 trees, max depth 10, completes within 20 min on CPU.
- **HHT**: Implemented with `pyhht`, processing one year at a time to stay within memory limits.
- **Bootstrap**: 1 000 iterations parallelized over 2 cores; expected runtime < 30 min.
- **Libraries**: All CPU‑only wheels (`scikit‑learn`, `pyhht`, `numpy`, `pandas`, `scipy`).

## Risks and Mitigations (updated)

| Risk | Mitigation |
|------|------------|
| Non-Stationarity of GSN-TSI relationship | **Non-Stationarity Check**: Compare model residuals against isotope trends. If drift detected, flag reconstruction as high uncertainty. |
| Manual download complexity | Scripted checksum verification ensures data integrity; specific canonical URLs provided. |
| HHT computational cost | Use `pyhht` in minimal mode; process data in yearly chunks. No fallback to peak detection. |
| Model over‑fit to short satellite window | 5‑fold CV + LOCO‑CV + OOB error; Isotope-Calibrated Adjustment anchors to physical reality. |
| Distribution‑shift validation | External proxy validation with 14C/10Be and Mg II; bootstrap compares reconstruction variance to independent proxies. |
| Multicollinearity between Sunspot and Cycle | Use continuous `cycle_phase` (time-based); report descriptive relationships only. |
| Bootstrap circularity | Bootstrap compares reconstruction variance to **independent isotope proxy variance**. |
| Versioning gaps | Explicit SHA‑256 hashing on file content and atomic timestamp update after every major artifact. |
| Baseline comparison bias | Strictly treat 2007 baseline as fixed; no re-tuning allowed. |

## Conclusion

The revised research plan introduces robust validation across distinct physical regimes, external proxy anchoring for the pre-satellite reconstruction, and strict adherence to constitutional principles (including explicit versioning and mandatory HHT). By re-running the 2007 baseline under identical constraints (fixed reference) and correcting for multiple comparisons, the study provides a scientifically sound assessment of whether cycle-specific calibration yields a genuinely improved solar irradiance reconstruction.