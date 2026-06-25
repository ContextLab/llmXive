# Feature Specification: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

**Feature Branch**: `feature-001-geomagnetic-correlation`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: “How do variations in solar wind composition (proton density, temperature, helium abundance) relate to the intensity of geomagnetic disturbances as measured by Kp and Dst indices? The project will download 20 years of ACE composition data and NOAA geomagnetic indices, align them to 1‑hour resolution, compute lagged Pearson and Spearman correlations (0–6 h), apply Bonferroni correction, and validate on a held‑out 3‑year period.”

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Data Acquisition & Synchronisation (Priority: P1)

A researcher needs a reproducible, end‑to‑end pipeline that downloads the ACE solar‑wind composition data and NOAA Kp/Dst indices, resamples both to a common 1‑hour UTC grid, and handles missing values.

**Why this priority**: Without clean, time‑aligned data the entire scientific inquiry collapses; this is the foundation for every downstream analysis.

**Independent Test**: Run the pipeline for a month‑long window (e.g., using a representative start and end date). Verify that the output CSV contains exactly five columns (timestamp, proton_density, temperature, helium_abundance, Kp, Dst) with no NaNs after the built‑in imputation step.

**Acceptance Scenarios**:

1. **Given** a valid time window, **When** the pipeline executes, **Then** it produces a synchronised CSV file with 1‑hour rows covering the entire window and no missing entries.
2. **Given** a time window that includes a known data‑gap in ACE (e.g., instrument outage), **When** the pipeline runs, **Then** it fills the gap by linear interpolation and logs a warning indicating the interpolated interval.

---

### User Story 2 – Lagged Correlation & Significance Testing (Priority: P2)

A researcher wants to compute Pearson and Spearman correlation coefficients between each composition parameter and each geomagnetic index at lags 0, 1, 2, 3, 6 hours, and determine statistical significance with a Bonferroni‑adjusted α = 0.05.

**Why this priority**: The core scientific claim hinges on whether composition variables exhibit statistically robust relationships with geomagnetic activity.

**Independent Test**: Execute the correlation module on the full 20‑year dataset. Verify that a results table (30 rows = 3 params × 2 indices × 5 lags) is produced, each row containing Pearson r, Spearman ρ, raw p‑value, and Bonferroni‑corrected p‑value.

**Acceptance Scenarios**:

1. **Given** the synchronised CSV from US‑1, **When** the correlation module runs for lag = 3 h, **Then** it outputs Pearson r = 0.62, Spearman ρ = 0.58, raw p = 1.2e‑07, Bonferroni p = 3.6e‑06 for helium vs Dst (example values).
2. **Given** the same input, **When** the module evaluates all lagged pairs, **Then** any pair with Bonferroni‑corrected p < 0.05 is flagged as “significant”.

---

### User Story 3 – Visualisation, Reporting & Validation (Priority: P3)

A researcher needs automatically generated visualisations (time‑series overlay, correlation heatmaps) and a validation report on a held‑out 3‑year test period (2018‑2020) that summarises whether any composition‑index pair exceeds a pre‑specified effect‑size threshold (|r| > 0.5).

**Why this priority**: Clear visual communication and out‑of‑sample validation are essential for scientific credibility and for informing downstream forecasting work.

**Independent Test**: After running US‑2 on the training period (1998‑2017), execute the validation module on 2018‑2020. Confirm that PNG files are created, each ≤ 5 MB, and that a short Markdown report states whether the helium‑Dst correlation surpasses |r| = 0.5 in the test set.

**Acceptance Scenarios**:

1. **Given** the correlation results from US‑2, **When** the validation module processes the 2018‑2020 window, **Then** it produces a heatmap PNG showing all lagged correlations and a report that reads “Helium abundance vs. Dst at 3 h lag: r = 0.54 (significant)”.
2. **Given** a scenario where no composition variable reaches |r| > 0.5, **When** the report is generated, **Then** it explicitly states “No composition parameter achieved the pre‑registered effect‑size threshold; composition does not add predictive value beyond dynamic pressure.”

---

### Edge Cases

- **Missing Variable**: What happens if the ACE dataset does not contain helium abundance for a given day?  
  *The pipeline aborts with a clear error message and logs the missing timestamps (see SC‑002).*

- **Non‑stationary Sampling**: How does the system handle periods where the ACE cadence drops below 1 hour (e.g., spacecraft anomalies)?  
  *The resampling step interpolates to 1‑hour resolution; extreme gaps (>6 h) trigger a warning and are excluded from correlation calculations.*

- **Extreme Storm Events**: If a geomagnetic storm lasts longer than the maximum lag (6 h), does the analysis miss delayed effects?  
  *The methodology is limited to 0‑6 h lags (see FR‑007); any longer‑lag effects are out of scope for this version.*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** (See US‑1): The system MUST download ACE composition data (proton density, temperature, helium abundance) and NOAA Kp/Dst indices for any user‑specified date range.  
- **FR-002** (See US‑1): The system MUST align both datasets to a common 1‑hour UTC grid, handling missing timestamps by linear interpolation (max gap = 6 h) and logging any interpolated intervals.  
- **FR-003** (See US‑2): The system MUST compute Pearson and Spearman correlation coefficients for each composition‑index pair at lags 0, 1, 2, 3, 6 hours, outputting a table with raw and Bonferroni‑corrected p‑values.  
- **FR-004** (See US‑2): The system MUST apply a Bonferroni correction for the full set of 30 hypothesis tests, enforcing a family‑wise α = 0.05.  
- **FR-005** (See US‑2): The system MUST report statistical power considerations (effect size, sample size, α) for each test; if power < 0.8, the report shall flag the result as “under‑powered”.  
- **FR-006** (See US‑1): The system MUST verify that the downloaded ACE file contains **all** required variables (proton_density, temperature, helium_abundance) and that the NOAA file contains hourly Kp and Dst values.  
  - *[NEEDS CLARIFICATION: exact variable names in ACE NetCDF/CSV files (e.g., “He+_abundance” vs. “He_abundance”)]*  
- **FR-007** (See US‑2): The system MUST limit total CPU time to ≤ 6 hours on a GitHub Actions free‑tier runner (2 CPU cores, 7 GB RAM).  
- **FR-008** (See US‑3): The system MUST generate the following visual artefacts for the validation period:  
  1. Time‑series overlay plot (composition vs. index) per lag.  
  2. Correlation heatmap (parameters × lags).  
  All artefacts shall be PNG files ≤ 5 MB each.  
- **FR-009** (See US‑3): The system MUST produce a concise Markdown validation report summarising: (a) which composition‑index pairs exceed |r| > 0.5, (b) their statistical significance after correction, and (c) power flags.  
- **FR-010** (Cross‑cutting): The system MUST run entirely on CPU‑only environments; any GPU‑specific libraries (e.g., CUDA, bitsandbytes) are prohibited.

### Key Entities

- **SolarWindRecord**: timestamp, proton_density (cm⁻³), temperature (K), helium_abundance (percentage).  
- **GeomagneticRecord**: timestamp, Kp (dimensionless 0‑9), Dst (nT).  
- **CorrelationResult**: composition_parameter, geomagnetic_index, lag_hours, pearson_r, spearman_rho, p_raw, p_bonferroni, power_estimate, significance_flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** (See US‑2): The full 20‑year lagged correlation analysis completes within 6 hours on the CI runner, consuming ≤ 7 GB RAM, and produces a 30‑row results table.  
- **SC-002** (See FR‑006): If any required variable is absent from the source files, the pipeline aborts with an explicit error message and logs the missing variable name.  
- **SC-003** (See US‑3): All visual artefacts (time‑series plots, heatmaps) are generated as PNG files ≤ 5 MB each, and the validation report correctly flags any composition‑index pair with |r| > 0.5 and Bonferroni‑corrected p < 0.05.  

## Assumptions

- ACE spacecraft provides continuous, calibrated measurements of proton density, temperature, and helium abundance for the entire 1998‑2020 interval.  
- NOAA provides hourly Kp and Dst values in a format directly ingestible (CSV/ASCII) without additional preprocessing.  
- Linear interpolation over gaps ≤ 6 h does not materially bias correlation estimates (standard practice in space‑weather time‑series analysis).  
- The chosen significance threshold (α = 0.05, Bonferroni‑adjusted) and effect‑size benchmark (|r| > 0.5) are accepted community standards for exploratory correlation studies in heliophysics.  
- All statistical operations (Pearson, Spearman, power calculations) are performed with `scipy`/`statsmodels`, which are CPU‑friendly and fit within the free‑tier resource limits.  
- No external proprietary datasets are required; all data are publicly downloadable without authentication.  
- The analysis is purely observational; therefore, findings will be framed as **associational** relationships, not causal statements (Methodological soundness).  
- Predictor collinearity (e.g., proton density vs. helium abundance) will be diagnosed via variance‑inflation factors; results will be reported descriptively without claiming independent predictive effects (Methodological soundness).  

---  

*End of Specification*
