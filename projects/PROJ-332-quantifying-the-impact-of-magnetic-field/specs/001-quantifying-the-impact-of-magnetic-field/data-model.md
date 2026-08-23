# Data Model: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

## Entities

### Discharge
A single tokamak shot containing time-series data for magnetic equilibrium and plasma profiles.
*   `discharge_id`: int (Unique identifier)
*   `island_width`: float (Pre-calculated magnetic island width in meters)
*   `chirikov_parameter`: float (Chirikov stochasticity parameter, normalized)
*   `q_profile_range`: float (Range of q-profile, max - min)
*   `q_separation_min`: float (Minimum separation between rational q-values)
*   `tau_e`: float (Energy confinement time in seconds)
*   `confinement_mode`: str ("L-mode" or "H-mode")
*   `minor_radius`: float (Plasma minor radius in meters)

### CorrelationResult
Structured object containing the results of the statistical analysis.
*   `metric_name`: str (e.g., "chirikov_parameter")
*   `mode`: str (e.g., "all", "L-mode", "H-mode")
*   `spearman_r`: float (Spearman correlation coefficient)
*   `spearman_p`: float (Spearman p-value)
*   `posterior_median_r`: float (Posterior median of the correlation coefficient)
*   `ci_lower`: float (95% Credible Interval lower bound)
*   `ci_upper`: float (95% Credible Interval upper bound)
*   `power`: float (Statistical power to detect |r| = 0.5)
*   `hypothesis_status`: str ("supported", "inconclusive", "not supported")

## Data Flow

1.  **Raw Data**: Retrieved from DIII-D MDSplus archive (EFIT, islands, taue trees).
2.  **Processed Data**: `analysis_ready.csv` containing validated discharge records.
3.  **Analysis Output**: `correlation_results.json` and `topology_vs_confinement.png`.

## Validation Rules

*   `discharge_id` must be unique.
*   `island_width` and `tau_e` must be present for inclusion.
*   `island_width` must be <= `minor_radius`.
*   `chirikov_parameter` >= 0.
*   `q_separation_min` > 0.
*   `confinement_mode` must be one of ["L-mode", "H-mode", "unknown"].
*   `posterior_median_r` must be in [-1, 1].
*   `ci_lower` and `ci_upper` must be in [-1, 1].
*   `power` must be in [0, 1].