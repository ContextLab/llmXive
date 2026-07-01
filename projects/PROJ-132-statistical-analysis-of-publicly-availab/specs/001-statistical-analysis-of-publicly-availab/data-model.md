# Data Model: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Entity Relationship Overview

The data model flows from raw observations to aggregated grid cells, then to statistical models and trajectory outputs.

1.  **Raw Ingestion**: `MigrationRecord` (eBird) and `ClimateRaw` (NOAA/PRISM).
2.  **Aggregation**: `GridCell` (0.5° × 0.5°) containing `PhenologyMetric` and `ClimateVariable`.
3.  **Model Input**: `ModelDataset` (joined grid data).
4.  **Output**: `ModelResult` (coefficients, p-values) and `Trajectory` (route shifts).

## Sampling Strategy

**Critical Constraint**: The analysis is performed on a **sampled subset** of the full population to meet CI constraints. The following rules apply to all entities:

1.  **Species Selection**: Only the **Top 5** migratory species by observation count are included.
2.  **Spatial Sampling**: **Tail-preserving stratified sampling** is used for grid cells.
    -   **Stratification**: Grid cells are stratified by observation density.
    -   **Oversampling**: Cells with the **earliest arrival dates** (lower tail of the phenology distribution) are explicitly oversampled to ensure the 'first_arrival_date' metric is not biased toward later dates.
    -   **Target**: ~100 grid cells per species.
3.  **Data Representation**: All entities defined below represent this **sampled subset**, not the full population. Statistical inference must account for this sampling design.

## Core Entities

### MigrationRecord
Represents a single bird observation (sampled subset).
*   **Attributes**:
    *   `species_id` (str): Unique species code.
    *   `latitude` (float): Decimal degrees.
    *   `longitude` (float): Decimal degrees.
    *   `date` (date): Observation date (YYYY-MM-DD).
    *   `count` (int): Number of individuals observed.
    *   `checklist_id` (str): Unique eBird checklist ID.
    *   `grid_cell` (str): Calculated as `f"{int(lat*2)/2:.1f}_{int(lon*2)/2:.1f}"`.
    *   `checklist_duration` (float): Duration of the checklist in minutes (effort covariate).
    *   `distance_traveled` (float): Distance traveled during checklist in km (effort covariate).
    *   `num_observers` (int): Number of observers on the checklist (effort covariate).

### PhenologyMetric
Computed metric for a species-grid cell-week combination (sampled subset).
*   **Attributes**:
    *   `species_id` (str)
    *   `grid_cell` (str)
    *   `year` (int)
    *   `week` (int): ISO week number.
    *   `first_arrival_date` (date): Earliest observation date in the season.
    *   `median_arrival_date` (date): Median observation date.
    *   `stopover_duration` (float): Days between first and last observation in the week.
    *   `data_quality` (str): "sufficient" or "insufficient".
    *   `centroid_uncertainty` (float): Standard error of the centroid estimate, derived from observation density (1/N) per cell. Used in Riemannian analysis.

### ClimateVariable
Climate measurement for a grid cell-week.
*   **Attributes**:
    *   `grid_cell` (str)
    *   `year` (int)
    *   `week` (int)
    *   `mean_temperature` (float): °C.
    *   `total_precipitation` (float): mm.
    *   `extreme_weather_index` (float): Derived index.
    *   `imputed` (bool): True if value was interpolated.
    *   `imputation_source` (str): Source of imputation (e.g., "spatial_interpolation", "synthetic").

### Trajectory
Sequence of weekly centroids for a species-year (sampled subset).
*   **Attributes**:
    *   `species_id` (str)
    *   `year` (int)
    *   `weekly_centroids` (list): List of `(lat, lon)` tuples.
    *   `centroid_uncertainty` (list): List of standard errors corresponding to each centroid.
    *   `shift_vector` (dict): `{magnitude: float, direction: float}`.
    *   `p_value` (float): From permutation test (1,000 shuffles, early stopping).
    *   `ci_lower` (float): 95% CI lower bound.
    *   `ci_upper` (float): 95% CI upper bound.

## Centroid Uncertainty Propagation (Algorithm)

To address the concern that centroid noise invalidates Riemannian p-values (scientific_soundness-a012dabc), the following algorithm is used:

1.  **Calculate Centroid Variance**: For each weekly centroid in a trajectory, calculate the variance $\sigma^2$ based on the inverse of the observation count $N$ in that cell: $\sigma^2 \propto 1/N$.
2.  **Manifold Metric**: Use `geomstats` to compute the Fréchet mean and variance on the Riemannian manifold (sphere), incorporating the calculated $\sigma^2$ as a weight in the distance metric.
3.  **Permutation Test**: During the permutation test, the uncertainty $\sigma^2$ is propagated to each shuffled trajectory. The p-value is derived from the distribution of distances that accounts for this uncertainty, ensuring the result is not a tautology of noise.

## Data Flow & Transformations

1.  **Ingest**: Raw CSV/Parquet → `MigrationRecord` / `ClimateRaw`.
2.  **Filter**: Keep –2024, migratory species only. Apply **Top 5 species** filter.
3.  **Grid**: Assign `grid_cell` to each record.
4.  **Sample**: Apply **tail-preserving stratified sampling** to select ~100 grid cells per species.
5.  **Aggregate**:
    *   Group by `species_id`, `grid_cell`, `year`, `week`.
    *   Compute `first_arrival_date`, `median_arrival_date`, `stopover_duration`.
    *   Calculate `centroid_uncertainty` from observation counts.
    *   Join with `ClimateVariable` (interpolated if missing).
    *   Flag "insufficient data" if count < threshold.
6.  **Model**: Fit GAMM (Unified Spatial Model) → `ModelResult`.
7.  **Trajectory**: Compute centroids → Apply Centroid Uncertainty Propagation → Riemannian analysis → `Trajectory`.