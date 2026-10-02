# API Reference

This document provides function signatures and usage details for the core modules in the `code/` directory.

## `code/analysis.py`

Core functions for spatial autocorrelation analysis, null/alternative simulation, and statistical power calculation.

### `create_binary_indicator_map(raster_values: np.ndarray, class_id: int) -> np.ndarray`
Transforms a categorical raster into a binary indicator map.

**Parameters:**
- `raster_values`: 2D numpy array of categorical land cover values.
- `class_id`: The integer class ID to encode as 1 (all others become 0).

**Returns:**
- `np.ndarray`: Binary 2D array (1 where `raster_values == class_id`, else 0).

### `calculate_moran_i(binary_map: np.ndarray, weights: libpysal.weights.W) -> Tuple[float, float]`
Calculates Moran's I statistic and its associated p-value.

**Parameters:**
- `binary_map`: 2D numpy array of binary values.
- `weights`: Spatial weights object from `libpysal`.

**Returns:**
- `Tuple[float, float]`: (Moran's I value, p-value).

### `generate_null_distribution(binary_map: np.ndarray, weights: libpysal.weights.W, permutations: int = 1000) -> np.ndarray`
Generates a null distribution of Moran's I values via random permutations.

**Parameters:**
- `binary_map`: 2D numpy array.
- `weights`: Spatial weights object.
- `permutations`: Number of random permutations (default 1000).

**Returns:**
- `np.ndarray`: Array of permuted Moran's I values.

### `simulate_h1_gibbs(binary_map: np.ndarray, lambda_val: float, seed: int) -> np.ndarray`
Generates synthetic H1 data using a Gibbs sampler for binary spatial autoregressive process.

**Parameters:**
- `binary_map`: 2D numpy array (original binary map).
- `lambda_val`: Spatial lag parameter estimated from calibration.
- `seed`: Random seed for reproducibility.

**Returns:**
- `np.ndarray`: Synthetic binary map with spatial structure.

### `calculate_statistical_power(h0_distribution: np.ndarray, h1_simulations: np.ndarray, alpha: float = 0.05) -> float`
Computes statistical power as the rejection rate of H1 simulations against the H0 critical value.

**Parameters:**
- `h0_distribution`: Array of null Moran's I values.
- `h1_simulations`: Array of alternative Moran's I values.
- `alpha`: Significance level (default 0.05).

**Returns:**
- `float`: Proportion of H1 simulations where p < alpha.

### `run_analysis_for_resolution(resolution_path: str, weights: libpysal.weights.W, lambda_val: float, class_id: int) -> Dict[str, Any]`
Runs the full analysis pipeline for a single resolution raster.

**Parameters:**
- `resolution_path`: Path to the resolution raster file.
- `weights`: Spatial weights object.
- `lambda_val`: Estimated spatial lag parameter.
- `class_id`: Target class ID for binary transformation.

**Returns:**
- `Dict`: Dictionary containing `moran_i`, `p_value`, `power`, and `is_boundary`.

### `main()`
CLI entry point for running the full analysis sweep.

---

## `code/config.py`

Project configuration constants.

### Attributes
- `RESOLUTIONS`: List[int] - Target resolutions [30, 60, 120, 240, 480].
- `FACTORS`: List[int] - Aggregation factors [1, 2, 4, 8, 16].
- `SEED`: int - Default random seed (42).
- `DATA_DIR`: Path - Base directory for data.
- `RESULTS_DIR`: Path - Base directory for results.

---

## `code/data_ingestion.py`

Functions for downloading and validating NLCD data.

### `download_with_progress(url: str, output_path: Path) -> Path`
Downloads a file with a progress bar and retry logic.

**Parameters:**
- `url`: Source URL.
- `output_path`: Destination path.

**Returns:**
- `Path`: Path to the downloaded file.

### `verify_download(file_path: Path, expected_checksum: str) -> bool`
Validates the checksum of a downloaded file.

**Parameters:**
- `file_path`: Path to the file.
- `expected_checksum`: Expected MD5/SHA checksum.

**Returns:**
- `bool`: True if checksum matches.

### `run_ingestion()`
Orchestrates the download and validation of the 30m NLCD subset.

---

## `code/models.py`

Data models for the project.

### `class ResolutionRaster`
Represents a raster at a specific resolution.
- `resolution`: int (pixel size in meters).
- `path`: Path to the raster file.
- `values`: Optional `np.ndarray` of pixel values.

### `class BinaryIndicatorMap`
Represents a binary map derived from a raster.
- `class_id`: int (the class encoded as 1).
- `binary_values`: `np.ndarray` of 0/1 values.

---

## `code/utils.py`

Utility functions for I/O, logging, and error handling.

### `setup_logging(log_level: str = "INFO") -> None`
Configures the logging infrastructure.

### `get_logger(name: str) -> logging.Logger`
Returns a configured logger instance.

### `retry_with_backoff(func, max_retries: int = 3, backoff_factor: float = 2.0)`
Decorator for retrying functions with exponential backoff.

### `create_memory_mapped_array(file_path: Path, shape: Tuple[int, int]) -> np.ndarray`
Creates a memory-mapped array for large rasters.

### `iter_windows(shape: Tuple[int, int], window_size: int = 2000)`
Generator yielding window coordinates for chunked processing.

### `read_raster_windowed(file_path: Path, window_coords: Tuple[int, int, int, int]) -> np.ndarray`
Reads a specific window from a raster file.

### `checksum_file(file_path: Path, algorithm: str = "md5") -> str`
Computes the checksum of a file.

---

## `code/visualization.py`

Functions for plotting and reporting.

### `find_threshold(power_csv_path: Path) -> Optional[str]`
Identifies the resolution where power drops below 0.80.

**Parameters:**
- `power_csv_path`: Path to `results.csv`.

**Returns:**
- `str`: Resolution string (e.g., "240m") or None.

---

## `code/sensitivity_analysis.py`

Functions for sensitivity analysis of aggregation factors.

### `resample_bilinear_then_quantize(raster_path: Path, factor: float) -> np.ndarray`
Resamples a raster using bilinear interpolation followed by nearest-neighbor quantization.

**Parameters:**
- `raster_path`: Path to the source raster.
- `factor`: Aggregation factor (can be non-integer).

**Returns:**
- `np.ndarray`: Resampled and quantized raster.

### `run_sensitivity_sweep(base_factor: int, sweep_range: float = 0.1) -> List[Dict]`
Runs analysis for factors +/- 10% around the base factor.

---

## `code/calibration.py`

Functions for estimating the spatial lag parameter.

### `estimate_lambda(raster_path: Path, sample_size: int = 10000) -> float`
Estimates the spatial lag parameter ($\lambda$) using MLE on a random sample.

**Parameters:**
- `raster_path`: Path to the 30m raster.
- `sample_size`: Number of pixels to sample.

**Returns:**
- `float`: Estimated $\lambda$.

---

## `code/resampling.py`

Functions for generating coarser resolution rasters.

### `generate_resolution(input_path: Path, factor: int, output_dir: Path) -> Path`
Generates a coarser resolution raster using nearest-neighbor resampling.

**Parameters:**
- `input_path`: Path to the 30m input raster.
- `factor`: Aggregation factor (2, 4, 8, 16).
- `output_dir`: Directory to save the output.

**Returns:**
- `Path`: Path to the generated raster.

---

## `code/maup_analysis.py`

Functions for analyzing the Modifiable Areal Unit Problem (MAUP).

### `calculate_shannon_entropy(values: np.ndarray) -> float`
Calculates the Shannon entropy of a categorical distribution.

### `analyze_resolution_impact(resolution_paths: List[Path]) -> Dict[str, float]`
Computes entropy and variance changes across resolutions.

---

## `code/type2_error_analysis.py`

Functions for Type II error analysis.

### `calculate_type2_error_delta(power_results: pd.DataFrame) -> pd.DataFrame`
Calculates the delta (1 - power) relative to the 30m baseline.

---

## `code/save_results.py`

Functions for saving analysis results.

### `save_results_to_csv(results: List[Dict], output_path: Path) -> None`
Saves a list of result dictionaries to a CSV file.

---

## `code/validate_checksums.py`

Functions for validating data integrity.

### `validate_raster_metadata(raster_path: Path, expected: Dict) -> bool`
Validates raster metadata against expected values.

---

## `code/reference_validator.py`

Functions for validating data sources.

### `validate_huggingface_url(url: str) -> bool`
Validates a HuggingFace dataset URL.

### `validate_proxy_url(url: str) -> bool`
Validates a proxy URL for data access.

---

## `code/quickstart_validator.py`

Functions for validating the quickstart process.

### `run_script(script_path: Path) -> bool`
Executes a script and returns success status.

---

## `code/generate_final_report.py`

Functions for generating the final report.

### `generate_report_content(results: pd.DataFrame, threshold: str) -> str`
Generates the markdown content for the final report.

---

## `code/generate_sensitivity_report.py`

Functions for generating sensitivity reports.

### `generate_report(sensitivity_data: List[Dict]) -> str`
Generates the markdown content for the sensitivity report.

---

## `code/cleanup_refactor.py`

Functions for code cleanup and refactoring.

### `clean_unused_imports(file_path: Path) -> None`
Removes unused imports from a Python file.

### `standardize_docstrings(file_path: Path) -> None`
Standardizes docstrings in a Python file.

---

## `code/setup_dirs.py`

Functions for setting up project directories.

### `main()`
Creates the required directory structure.

---

## `code/tests/unit/`

Unit tests for the project modules.

- `test_config.py`: Tests for configuration constants.
- `test_models.py`: Tests for data models.
- `test_utils.py`: Tests for utility functions.
- `test_analysis.py`: Tests for analysis functions.
- `test_resampling.py`: Tests for resampling functions.