# API Reference

## `code/config.py`

Global configuration for the project.

### Attributes
- `RESOLUTIONS`: List of target resolutions (30, 60, 120, 240, 480).
- `SEED`: Random seed for reproducibility (default: 42).
- `DATA_PATH`: Path to raw data directory.
- `DERIVED_PATH`: Path to derived data directory.
- `RESULTS_PATH`: Path to results directory.

## `code/utils.py`

Utility functions for I/O, checksumming, and retry logic.

### Functions
- `setup_logging()`: Configures logging infrastructure.
- `get_logger(name)`: Returns a configured logger.
- `retry_with_backoff(func, max_retries, base_delay)`: Retry logic with exponential backoff.
- `checksum_file(path)`: Computes SHA256 checksum of a file.
- `create_memory_mapped_array(path, shape, dtype)`: Creates a memory-mapped array.
- `read_raster_windowed(path, window)`: Reads a raster window.
- `validate_raster_bounds(path, bounds)`: Validates raster bounds.

## `code/data_ingestion.py`

Data download and validation.

### Functions
- `download_with_progress(url, dest_path)`: Downloads a file with progress tracking.
- `verify_download(path, expected_checksum)`: Verifies file checksum.
- `run_ingestion()`: Main entry point for data ingestion.

## `code/resampling.py`

Resolution aggregation.

### Functions
- `generate_resolution(input_path, factor)`: Generates a coarser resolution raster.
- `run_resampling_pipeline()`: Main entry point for resampling.

## `code/analysis.py`

Spatial autocorrelation and power analysis.

### Functions
- `create_binary_indicator_map(raster_path, class_id)`: Creates a binary map.
- `calculate_moran_i(binary_map, weights)`: Computes Moran's I.
- `generate_null_distribution(binary_map, permutations)`: Generates H0 null distribution.
- `simulate_h1_gibbs(fixed_lambda, binary_map, seed)`: Generates H1 synthetic data.
- `calculate_statistical_power(h0_p_values, h1_p_values)`: Computes power.
- `run_analysis_for_resolution(resolution_path)`: Runs full analysis for a resolution.

## `code/visualization.py`

Visualization and threshold identification.

### Functions
- `find_threshold(power_csv_path)`: Identifies the resolution where power < 0.80.
- `plot_power_curve(power_csv_path, output_path)`: Generates the power curve plot.

## `code/sensitivity_analysis.py`

Sensitivity analysis.

### Functions
- `run_sensitivity_sweep(power_csv_path)`: Runs ±10% sweep.
- `write_sensitivity_report(results, output_path)`: Writes sensitivity report.

## `code/generate_final_report.py`

Report generation.

### Functions
- `load_power_results(csv_path)`: Loads power results.
- `generate_report(power_results, threshold, output_path)`: Generates final report.
