# Data Model: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

## Entity Definitions

### 1. PlanetRecord
Represents a single exoplanet observation after ingestion and filtering.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `planet_id` | `str` | Unique identifier (e.g., Kepler Object ID). |
| `radius` | `float` | Planet radius in Earth radii ($R_{\oplus}$). |
| `radius_uncertainty` | `float` | Uncertainty in radius ($R_{\oplus}$). |
| `period` | `float` | Orbital period in days. |
| `period_uncertainty` | `float` | Uncertainty in period (days). |
| `stellar_radius` | `float` | Stellar radius in solar radii ($R_{\odot}$). |
| `stellar_mass` | `float` | Stellar mass in solar masses ($M_{\odot}$). |
| `stellar_temp` | `float` | Stellar effective temperature (K). |
| `completeness_value` | `float` | Detection completeness at (period, radius) from Kepler map. |

### 2. PeriodBin
Represents a log-spaced orbital period bin containing a subset of planets.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `bin_center_log_period` | `float` | Center of the bin in log-space. |
| `weighted_mean_log_period` | `float` | Weighted mean period of planets in the bin. |
| `planet_count` | `int` | Number of planets in the bin (≥ 30). |
| `gap_location` | `float` | Estimated gap radius (valley between GMM peaks). |
| `gap_uncertainty` | `float` | Standard deviation from bootstrap resampling. |
| `gap_ci_lower` | `float` | Lower bound of 95% CI. |
| `gap_ci_upper` | `float` | Upper bound of 95% CI. |
| `is_bimodal` | `bool` | True if BIC diff ≥ 10 and peak separation ≥ 0.1. |
| `status` | `str` | "valid", "unresolved", or "merged". |
| `kde_gap_location` | `float` | Gap location from KDE validation. |
| `validation_status` | `str` | "PASS" if KDE gap within GMM CI, else "FAIL". |
| `regression_weight` | `float` | Inverse variance of the gap location estimate (1/sigma^2). |

### 3. GapAnalysisResult
The final aggregated output of the analysis.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `measured_slope` | `float` | Slope from weighted linear regression. |
| `slope_uncertainty` | `float` | 95% CI width of the slope. |
| `p_value_photoevaporation` | `float` | P-value comparing measured slope to Owen & Wu model. |
| `p_value_core_powered` | `float` | P-value comparing measured slope to Ginzburg et al. model. |
| `validation_status` | `str` | Overall status (PASS/FAIL based on KDE and synthetic tests). |
| `sensitivity_status` | `str` | Result of synthetic data recovery test. |
| `run_duration_seconds` | `float` | Total runtime in seconds (for SC-005). |

## Data Flow

1.  **Raw CSV** (Kepler DR25 + KIC) → **Ingest** → **PlanetRecord** DataFrame.
2.  **PlanetRecord** → **Filter** (uncertainty thresholds) → **Filtered PlanetRecord**.
3.  **Filtered PlanetRecord** → **Bin** → **PeriodBin** list.
4.  **PeriodBin** → **GMM + Bootstrap** (with completeness weighting) → **PeriodBin** (updated with gap stats).
5.  **PeriodBin** → **Regression** (using resolved bins only) → **GapAnalysisResult**.
6.  **GapAnalysisResult** → **Validation** (KDE, Synthetic) → Final Report.