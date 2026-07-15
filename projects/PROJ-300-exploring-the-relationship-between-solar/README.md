# Solar Wind Speed and Geomagnetic Tail Reconnection Rates Analysis

This project investigates the relationship between solar wind speed (Vsw) and the geomagnetic tail reconnection rate proxy (Ey) using NASA OMNI and THEMIS data.

## Prerequisites

- Python 3.11+
- pip (Python package manager)

## Installation

1. Navigate to the project root directory:
 ```bash
 cd projects/PROJ-300-exploring-the-relationship-between-solar
 ```

2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Full Pipeline

The main entry point is `code/main.py`. It orchestrates data ingestion, cleaning, lag adjustment, correlation analysis, and visualization.

### Basic Execution

Run the pipeline on a specific date range (e.g., 3 days in 2023):

```bash
python code/main.py --start 2023-06-01 --end 2023-06-04
```

**Arguments:**
- `--start`: Start date (YYYY-MM-DD)
- `--end`: End date (YYYY-MM-DD)
- `--lag-window-min`: Minimum lag window in minutes (default: 30)
- `--lag-window-max`: Maximum lag window in minutes (default: 90)
- `--lag-step`: Step size for lag search in minutes (default: 5)

**Output:**
The pipeline generates the following artifacts in the `results/` directory:
- `us1_correlation.json`: Correlation coefficients, p-values, optimal lag, and sensitivity table.
- `plot_scatter.png`: Scatter plot of lag-adjusted Vsw vs. Ey with regression line.
- `plot_timeseries.png`: Dual-axis time-series overlay of Vsw and Ey.
- `quality_log.json`: Data quality warnings and statistics.

### Example with Custom Parameters

```bash
python code/main.py --start 2023-06-01 --end 2023-06-04 --lag-window-min 20 --lag-window-max 100 --lag-step 10
```

## Interpreting the Results

### 1. Correlation Coefficients (`us1_correlation.json`)

- **pearson**: Pearson correlation coefficient between lag-adjusted Vsw and Ey.
- **spearman**: Spearman rank correlation coefficient.
- **p_val_permutation**: Empirical p-value from the circular block permutation test (FR-005).
- **significant_flag**: Boolean indicating if the correlation is statistically significant (p < 0.05).
- **optimal_lag**: The lag (in minutes) that maximizes the absolute correlation.
- **lag_correlation_value**: The correlation value at the optimal lag.
- **lag_difference**: Absolute difference between the optimal lag (L*) and the physics-based lag (L_phys).
- **sensitivity_table**: Correlation values for different solar wind speed thresholds (400, 500, 600 km/s).

### 2. Visualizations

- **plot_scatter.png**:
 - X-axis: Solar wind speed (Vsw) in km/s.
 - Y-axis: Tail reconnection proxy (Ey) in mV/m.
 - Red line: Linear regression fit.
 - Annotation: Optimal lag value and correlation coefficient.

- **plot_timeseries.png**:
 - Left Y-axis: Solar wind speed (Vsw) in km/s.
 - Right Y-axis: Tail reconnection proxy (Ey) in mV/m.
 - X-axis: Time.
 - Shows the temporal alignment of Vsw and Ey after applying the optimal lag.

### 3. Quality Log (`quality_log.json`)

Contains warnings about data gaps, NaN handling, and other quality metrics. Review this file if the correlation results seem unexpected.

## Running Tests

The project includes unit and integration tests to verify correctness.

### Unit Tests

```bash
pytest tests/unit/ -v
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

### Specific Test Scenarios

- **US-1 Independent Test**:
 ```bash
 pytest tests/integration/test_pipeline.py::test_us1_full_pipeline -v
 ```

- **US-2 Lag Search Test**:
 ```bash
 pytest tests/integration/test_synthetic.py::test_synthetic_lag_45min -v
 ```

- **US-3 Visualization Test**:
 ```bash
 pytest tests/integration/test_us3.py -v
 ```

## Project Structure

```
projects/PROJ-300-exploring-the-relationship-between-solar/
├── code/
│ ├── config.py # Physics constants and configuration
│ ├── data/
│ │ ├── ingest.py # Data fetching from NASA APIs
│ │ ├── clean.py # Data cleaning and resampling
│ │ └── lag.py # Lag calculation and application
│ ├── analysis/
│ │ ├── correlation.py # Correlation and permutation tests
│ │ ├── lag_search.py # Optimal lag identification
│ │ └── sensitivity.py # Sensitivity analysis
│ ├── viz/
│ │ └── plots.py # Plotting functions
│ └── main.py # Main pipeline entry point
├── data/
│ ├── raw/ # Raw downloaded data (if cached)
│ └── processed/ # Processed data and quality logs
├── results/ # Analysis outputs (JSON, PNG)
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Notes

- **Data Sources**:
 - Solar wind data (Vsw, Bz): NASA OMNIWeb API via `requests`.
 - Tail reconnection proxy (Ey): NASA CDAWeb (THEMIS) via `cdaweb`.

- **Physics-Based Lag**:
 The physics-based lag \( L_{phys} \) is calculated as:
 \[
 L_{phys} = \frac{k \times 6371}{V_{sw}} \times 60
 \]
 where \( k \) is the propagation factor, 6371 is Earth's radius in km, and 60 converts seconds to minutes.

- **Significance Testing**:
 The permutation test (FR-005) is the primary method for significance testing. Bonferroni correction is noted as conservative for autocorrelated lag searches.

## Troubleshooting

- **Data Fetching Errors**: Ensure internet connectivity and check NASA API status.
- **Missing Dependencies**: Re-run `pip install -r requirements.txt`.
- **Plot Generation Issues**: Verify `matplotlib` backend configuration.
- **NaN Gaps**: Review `quality_log.json` for data quality warnings.

## License

This project is for research purposes.