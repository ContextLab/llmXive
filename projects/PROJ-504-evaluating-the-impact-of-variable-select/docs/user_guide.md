# User Guide: Variable Selection Impact Study

## Quick Start

1. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

2. **Verify Environment**:
 ```bash
 python code/verify.py
 ```
 This runs a pilot simulation to validate resource limits and determine the optimal `simulations_per_condition` count.

3. **Run Full Pipeline**:
 ```bash
 python code/data/pipeline.py
 python code/analysis/metrics.py
 python code/analysis/comparators.py
 ```

## Configuration Guide

Edit `code/config.py` to customize:

- **Datasets**: Modify `openml_ids` to select specific OpenML datasets
- **SNR Levels**: Adjust `snr_levels` (e.g., `[0.5, 1.0, 2.0, 5.0]`)
- **Sparsity**: Change `sparsity_levels` (e.g., `[0.0, 0.2, 0.4, 0.6]`)
- **Alpha Thresholds**: Update `alpha_levels` for sensitivity analysis

## Understanding the Output

### `data/processed/simulation_results.csv`

Contains one row per simulation run with columns:
- `dataset_id`, `dataset_name`: Source of the X matrix
- `snr`, `sparsity`: Simulation conditions
- `method`: Selection method used (Forward, Backward, LASSO)
- `power_rate`: Empirical power (proportion of true non-zero coefficients selected & significant)
- `vif`, `condition_number`: Collinearity diagnostics

### `results/final_report.md`

Includes:
- **Executive Summary**: High-level findings on method performance
- **Statistical Results**: Kruskal-Wallis p-values and Dunn's post-hoc comparisons
- **Power Curves**: Visualizations of power vs. SNR across methods
- **Methodology Notes**: Details on data sources and statistical tests

## Troubleshooting

### "Runtime limit approached"
The `watchdog.py` module will trigger a graceful shutdown if the 6-hour limit is near. Partial results are saved automatically. Check `results/partial_run_<timestamp>.csv`.

### "Memory limit exceeded"
If RAM usage exceeds 6.5 GB, the process aborts. Reduce `simulations_per_condition` in `config.py` or increase system memory.

### "Dataset validation failed"
If fewer than 10 valid datasets are found, the pipeline retries from a backup list. Ensure network connectivity to OpenML.

## Advanced Usage

### Running Specific Steps

- **Only Data Generation**:
 ```bash
 python code/data/pipeline.py --skip-analysis
 ```

- **Only Statistical Analysis**:
 ```bash
 python code/analysis/comparators.py --input data/processed/simulation_results.csv
 ```

### Custom Visualization

Modify `code/viz/plots.py` to generate custom faceted plots. The default layout includes:
- X-axis: SNR
- Y-axis: Power Rate
- Facets: Sparsity levels
- Lines: Selection methods (color-coded)

## Reproducibility

All simulations use a pinned seed defined in `config.py`. To verify reproducibility:
1. Re-run the pipeline with the same seed
2. Compare checksums of `data/processed/simulation_results.csv`
3. Verify that statistical p-values match within floating-point tolerance
