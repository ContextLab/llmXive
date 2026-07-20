# Data Model Specification

## Entities

### StrainEvent

Represents a gravitational wave event.

| Field | Type | Description |
|-------|------|-------------|
| event_id | str | Unique identifier (e.g., GW150914) |
| source | str | Data source (GWOSC, Injection) |
| sampling_rate | float | Original sampling rate (Hz) |
| duration | float | Duration (seconds) |
| snr | float | Signal-to-noise ratio |

### ResolutionConfig

Represents a specific resolution configuration.

| Field | Type | Description |
|-------|------|-------------|
| sampling_rate | float | Target sampling rate (Hz) |
| bit_depth | int | Bit depth (16, 32) |
| description | str | Human-readable description |

### PosteriorDistribution

Represents results from Bayesian inference.

| Field | Type | Description |
|-------|------|-------------|
| event_id | str | Associated event ID |
| resolution_config | ResolutionConfig | Configuration used |
| parameters | Dict[str, np.ndarray] | Parameter samples |
| status | str | 'valid' or 'inconclusive' |
| width_to_prior_ratio | float | Posterior width / Prior width |

### BiasMetric

Represents calculated bias metrics.

| Field | Type | Description |
|-------|------|-------------|
| event_id | str | Associated event ID |
| resolution_config | ResolutionConfig | Configuration used |
| parameter_name | str | Parameter being measured |
| bias_value | float | Calculated bias |
| hellinger_distance | float | Hellinger distance |
| exceeds_threshold | bool | Bias > catalog CI |
| catalog_ci | float | Catalog confidence interval |

## Relationships

- A `StrainEvent` can have multiple `PosteriorDistribution`s (one per `ResolutionConfig`).
- A `PosteriorDistribution` generates one or more `BiasMetric`s.

## File Formats

- **Posteriors**: JSON files containing parameter samples and metadata.
- **Metrics**: JSON files containing bias calculations and flags.
- **Aggregation**: JSON file containing summary statistics and thresholds.
