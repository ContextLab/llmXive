# API Reference

This document provides a reference for the public APIs exposed by the project modules.

## `benchmarks.config`

### `ConfigManager`
- **`create_default_manager()`**: Creates a default configuration manager with standard flags and dimensions.
- **`validate_flags(flags: List[str])`**: Validates a list of compiler flags.
- **`get_configs()`**: Iterator yielding `BenchmarkConfig` objects.

### `BenchmarkConfig`
- **`config_id`**: Unique identifier string.
- **`flags`**: List of compiler flags.
- **`dimensions`**: Tuple of (height, width).

## `benchmarks.executor`

### `Executor`
- **`execute(config: BenchmarkConfig, binary_path: str)`**: Runs the binary and measures latency.
- **`handle_memory_pressure(config)`**: Downsamples dimensions if allocation fails.

## `analysis.stability_check`

### `StabilityResult`
- **`config_id`**: Configuration ID.
- **`l2_error`**: L2 relative error.
- **`max_diff`**: Maximum absolute difference.
- **`status`**: "STABLE" or "UNSTABLE".

### `calculate_l2_relative_error(output, reference)`
- Calculates L2 relative error between two numpy arrays.

### `calculate_max_absolute_difference(output, reference)`
- Calculates maximum absolute difference.

## `analysis.stats`

### `welch_ttest(sample_a, sample_b)`
- Performs Welch's t-test on two independent samples.
- Returns: `(t_statistic, p_value)`.

### `compute_block_averages(latencies, block_size)`
- Computes block averages from a list of latencies.

## `analysis.viz`

### `plot_pareto_frontier(data, exploration=True)`
- Generates a Pareto frontier plot.
- **`exploration`**: If True, includes downsampled runs with distinct markers.

## `utils.logger`

### `setup_logging()`
- Configures the logging infrastructure.

### `log_compiler_version(version)`
- Logs the compiler version.

### `log_nan_detection(config_id)`
- Logs NaN detection for a specific configuration.

## `utils.manifest_generator`

### `generate_manifest(output_path)`
- Scans `data/` and generates a manifest with SHA-256 hashes.
