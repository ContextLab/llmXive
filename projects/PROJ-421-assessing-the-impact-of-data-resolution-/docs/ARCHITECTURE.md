# Architecture Documentation

## System Overview
This project implements a modular pipeline for analyzing the impact of data resolution on statistical power in spatial datasets. The architecture follows a clear separation of concerns with distinct modules for data ingestion, processing, analysis, and visualization.

## Module Responsibilities

### data_ingestion.py
- **Purpose**: Download and validate NLCD data
- **Key Functions**:
 - `download_with_progress()`: Downloads data with progress tracking
 - `verify_download()`: Validates checksums and metadata
 - `run_ingestion()`: Orchestrates the download process
- **Dependencies**: utils.py (for retry logic, checksumming)

### resampling.py
- **Purpose**: Generate coarser resolution rasters
- **Key Functions**:
 - `generate_resolution()`: Creates single coarser raster
 - Windowed reading for memory efficiency
 - Nearest-neighbor resampling to preserve categorical values
- **Constraints**: Must stay within 7GB RAM limit

### calibration.py
- **Purpose**: Estimate spatial lag parameter (λ)
- **Key Functions**:
 - `estimate_lambda()`: MLE estimation on random sample
- **Output**: `data/results/calibration_lambda.json`

### analysis.py
- **Purpose**: Core spatial statistical analysis
- **Key Functions**:
 - `create_binary_indicator_map()`: Forest vs. Others
 - `calculate_moran_i()`: Spatial autocorrelation
 - `generate_null_distribution()`: 1,000 permutations for H0
 - `simulate_h1_gibbs()`: Gibbs sampler for H1
 - `calculate_statistical_power()`: Rejection rate
- **Dependencies**: pysal, numpy, scipy

### visualization.py
- **Purpose**: Generate plots and identify thresholds
- **Key Functions**:
 - `find_threshold()`: Locate resolution where power < 0.80
 - Plot generation for power curves
- **Output**: `data/results/threshold_report.txt`

### utils.py
- **Purpose**: Shared utilities
- **Key Functions**:
 - Memory-mapped I/O helpers
 - Windowed raster readers
 - Logging setup
 - Retry with exponential backoff
 - Checksum validation

### config.py
- **Purpose**: Centralized configuration
- **Settings**:
 - Resolution factors: [2, 4, 8, 16]
 - Random seed: 42
 - Paths for data and results
 - HuggingFace URL

## Data Flow

1. **Ingestion**: NLCD 30m data → `data/raw/`
2. **Resampling**: 30m → 60m, 120m, 240m, 480m → `data/derived/`
3. **Calibration**: Sample → λ estimate → `data/results/calibration_lambda.json`
4. **Analysis**: Each resolution → Moran's I, p-values, power → `data/results/power_results.csv`
5. **Visualization**: Power results → curve, threshold → `data/results/threshold_report.txt`
6. **Reporting**: All results → `data/results/final_report.md`

## Memory Management
- Windowed reading for large rasters
- Memory-mapped arrays for efficient access
- Chunked processing to stay within 7GB RAM limit

## Error Handling
- Retry with exponential backoff for network operations
- Checksum validation for data integrity
- Bounds checking for valid resolutions
- Fail loudly on missing real data sources

## Testing Strategy
- Unit tests for core functions
- Integration tests for pipeline components
- Tests verify:
 - Integer preservation in resampling
 - Correct Moran's I calculation
 - Proper power estimation
 - Threshold identification accuracy

## Configuration Management
- All parameters in `config.py`
- Easy to modify resolutions, seeds, paths
- Environment variables for API keys

## Output Formats
- **CSV**: `power_results.csv` (resolution, moran_i, p_value, power)
- **JSON**: `calibration_lambda.json` (λ value)
- **TXT**: `threshold_report.txt`, `sensitivity_report.txt`
- **MD**: `final_report.md` (comprehensive analysis)
- **PNG**: Power curve visualization