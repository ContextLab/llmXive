# Usage Guide

## Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Pipeline

```bash
# Run complete analysis
python code/main.py
```

This will:
- Discover and load valid UCI datasets
- Compute correlation matrices
- Generate null distributions via permutation
- Apply BY correction
- Generate visualizations and reports

### 3. View Results

Results are saved to:
- `output/results/` - Statistical results
- `output/plots/` - Visualizations
- `output/reports/` - Text reports

## Command Line Interface

### Full Pipeline

```bash
python code/main.py
```

### Synthetic Validation

```bash
python code/main.py --task synthetic_validation
```

Runs 100 iterations of synthetic data validation to verify null model correctness.

### Threshold Sensitivity Analysis

```bash
python code/main.py --task threshold_sweep
```

Tests thresholds: 0.1, 0.2, 0.3, 0.4, 0.5

### Primary Visualizations

```bash
python code/main.py --task viz_primary
```

Generates visualizations for threshold |r| > 0.3

### Custom Parameters

```bash
python code/main.py --task threshold_sweep --threshold 0.25 --n_permutations 2000
```

## Configuration

Edit `code/config.py` to modify:

```python
# Default correlation threshold
DEFAULT_THRESHOLD = 0.3

# Number of permutations
N_PERMUTATIONS = 1000

# Random seed for reproducibility
RANDOM_SEED = 42

# Dataset requirements
MIN_CONTINUOUS_VARS = 20
```

## Output Files

### Results Directory (`output/results/`)

- `summary.csv`: Main results table
- `sensitivity_report.csv`: Threshold sensitivity data
- `validation_report.json`: Synthetic validation results
- `dataset_metadata.json`: Dataset information

### Plots Directory (`output/plots/`)

#### Primary (`output/plots/primary/`)
- `heatmap.png`: Correlation matrix
- `histogram.png`: Null distribution
- `observed_vs_null.png`: Comparison heatmap

#### Sensitivity (`output/plots/sensitivity/`)
- `threshold_0.1.png`
- `threshold_0.2.png`
- `threshold_0.3.png`
- `threshold_0.4.png`
- `threshold_0.5.png`

### Reports Directory (`output/reports/`)

- `associational_report.txt`: Final analysis report
- `sensitivity_summary.txt`: Sensitivity analysis summary
- `validation_summary.txt`: Validation results summary

## Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Specific test
python -m pytest tests/unit/test_stats_engine.py::test_permutation_preserves_marginals -v
```

## Data Processing

### Dataset Selection

The pipeline automatically:
1. Queries UCI for multivariate datasets
2. Filters for >=20 continuous variables
3. Drops missing values
4. Excludes constant variables

### Data Hygiene Pipeline

Applied in order:
1. Drop rows with missing values
2. Detect and exclude constant variables
3. Filter to continuous variables only
4. Validate minimum variable count

## Statistical Methods

### Permutation Testing

- **N=1,000** permutations (default)
- Reduced to **N=500** for clustering coefficient on large datasets (>50 variables)
- Marginal distributions preserved

### Network Statistics

1. **Mean Absolute Correlation**: ⟨|r|⟩
2. **Edge Density**: Proportion of edges above threshold
3. **Max Absolute Correlation**: max(|r|)
4. **Average Clustering Coefficient**: ⟨C⟩

### Multiple Testing Correction

- **Benjamini-Yekutieli (BY)** procedure
- Controls FDR under arbitrary dependence
- Empirical p-values: (r+1)/(N+1)

### Threshold Sensitivity

Tested thresholds: **{0.1, 0.2, 0.3, 0.4, 0.5}**

## Troubleshooting

### No Datasets Found

If no valid datasets are found:
1. Check network connection
2. Verify UCI repository accessibility
3. The pipeline will attempt dynamic discovery

### Memory Issues

For large datasets:
1. Reduce N_PERMUTATIONS in config
2. Process datasets sequentially
3. Increase system RAM if possible

### Visualization Errors

If plots fail to generate:
1. Check matplotlib backend
2. Verify output directory permissions
3. Ensure sufficient disk space

## Performance

### Expected Runtime

- **Small datasets** (<30 vars): ~5-10 minutes
- **Medium datasets** (30-50 vars): ~15-30 minutes
- **Large datasets** (>50 vars): ~30-60 minutes

### Optimization

The pipeline includes:
- Conditional N reduction for clustering coefficient
- Efficient permutation implementation
- Parallel processing where applicable

## Extending the Pipeline

### Adding New Statistics

1. Implement statistic function in `stats_engine.py`
2. Add to `calculate_stats()` return dictionary
3. Update visualization functions if needed

### New Thresholds

Edit the threshold list in `run_threshold_sweep()`:
```python
thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6] # Add new thresholds
```

### Custom Corrections

Add new correction functions to `correction.py`:
```python
def custom_correction(p_values):
 # Implement correction
 return corrected_values
```
