# API Reference (Detailed)

*Note: This file is a placeholder for auto-generated documentation.
Use `sphinx-apidoc` or `pdoc` to generate the full reference from docstrings.*

## Modules

### `code.config`
- `Config`: Dataclass for configuration.
- `get_config()`: Singleton accessor.

### `code.data.ingestion`
- `fetch_satellite_data(satellite_id, year)`: Fetches data.
- `parse_slr_file(content)`: Parses SLR files.
- `aggregate_satellites(ids)`: Merges data.

### `code.data.preprocessing`
- `filter_residuals(df, threshold)`: Filters data.
- `align_time_series(dfs)`: Aligns time series.

### `code.models.dynamics`
- `DynamicsModel`: Force model class.
- `compute_acceleration(state, time)`: Computes total acceleration.

### `code.models.estimator`
- `separate_fit_satellite(data, params)`: Orbit determination.
- `run_joint_fit(data_pair, params)`: Joint orbit determination.

### `code.analysis.eotvos`
- `compute_eotvos_parameter(ac, g, cov)`: Calculates eta.

### `code.analysis.validation`
- `compare_null_vs_alternative(null, alt)`: Model comparison.
- `apply_correction(p_values, method)`: Multiple comparison correction.

### `code.utils.logging`
- `init_logging()`: Setup logging.
- `get_logger(name)`: Get logger.
- `PipelineError`, `DataUnavailableError`: Custom exceptions.
