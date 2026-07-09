# Data Model: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

## 1. Entities

### 1.1 PlanetRecord
Represents a single exoplanet observation from the cleaned Kepler catalog.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `planet_id` | string | Unique identifier (e.g., "Kepler-10b") | Primary Key, Not Null |
| `radius` | float | Planet radius in Earth radii (R_earth) | > 0, Not Null |
| `radius_uncertainty` | float | Uncertainty in radius | > 0, Not Null |
| `period` | float | Orbital period in days | > 0, Not Null |
| `period_uncertainty` | float | Uncertainty in period | > 0, Not Null |
| `stellar_radius` | float | Host star radius in Solar radii | > 0, Not Null |
| `stellar_mass` | float | Host star mass in Solar masses | > 0, Not Null |
| `stellar_temp` | float | Host star effective temperature in Kelvin | > 0, Not Null |
| `completeness_weight` | float | Weight from Kepler completeness map | [0, 1] |
| `log_period` | float | Log10 of the period | Not Null |

### 1.2 PeriodBin
Represents a specific orbital period interval and the derived gap metrics.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `bin_id` | integer | Sequential bin index | Primary Key |
| `bin_center_log_period` | float | Center of the log-period bin | Not Null |
| `weighted_mean_log_period` | float | Weighted mean log period of planets in bin | Not Null |
| `planet_count` | integer | Number of planets in the bin | ≥ 30 (after merge) |
| `gap_location` | float | Estimated gap radius (R_earth) | Not Null |
| `gap_uncertainty` | float | 95% CI half-width from bootstrap | > 0 |
| `validation_status` | string | "PASS", "FAIL", "UNRESOLVED" | Enum |
| `kde_gap_location` | float | Gap location from KDE validation | Not Null |
| `kde_gap_uncertainty` | float | Uncertainty of KDE gap | > 0 |

### 1.3 GapAnalysisResult
The final aggregated result of the analysis.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `measured_slope` | float | Slope of Gap vs Log(Period) | Not Null |
| `slope_uncertainty` | float | 95% CI of the slope | > 0 |
| `p_value_photoevaporation` | float | Permutation test p-value vs Photoevap theory | [0, 1] |
| `p_value_core_powered` | float | Permutation test p-value vs Core-Powered theory | [0, 1] |
| `theoretical_dist_photoevaporation` | list[float] | Sampled theoretical slope distribution (Photoevap) | Not Null |
| `theoretical_dist_core_powered` | list[float] | Sampled theoretical slope distribution (Core-Powered) | Not Null |
| `validation_status` | string | Overall validation (Synthetic Ground Truth) | "PASS", "FAIL" |
| `sensitivity_status` | string | Sensitivity analysis result | "PASS", "FAIL" |
| `vif_max` | float | Maximum Variance Inflation Factor | Not Null |

## 2. Data Flow

1.  **Raw Input**: `data/raw/kepler_dr25.csv`, `data/raw/kic.csv`, `data/raw/completeness_map.csv`
2.  **Cleaned Input**: `data/processed/cleaned_planets.csv` (Filtered, deduped, merged, weighted).
3.  **Intermediate**: `data/processed/binned_results.csv` (Gap locations per bin, including KDE validation).
4.  **Final Output**: `data/processed/final_analysis_results.json` (Aggregated stats, theoretical distributions).

## 3. Transformation Rules

-   **Filtering**: Remove rows where `radius_uncertainty` > 20% of `radius` OR `period_uncertainty` > 1% of `period`.
-   **Deduplication**: If multiple entries exist for `planet_id`, keep the one with the lowest `radius_uncertainty`.
-   **Completeness Weighting**: Join with Kepler Completeness Map; assign `completeness_weight` to each planet.
-   **Binning**: Log-spaced bins from log(5) to log(100). If count < 30, merge with adjacent bin (closest period).
-   **GMM Fitting**: Fit 2-component GMM. If BIC(2) - BIC(1) < 10 or convergence fails, mark as "UNRESOLVED".
-   **Bootstrap**: 1000 iterations. 95% CI = [2.5th percentile, 97.5th percentile].
-   **Regression**: Use 'PASS' bins only. Apply errors-in-variables regression.
-   **Theory Comparison**: Generate theoretical distributions via Monte Carlo (stellar + model params). Use Permutation Test.
