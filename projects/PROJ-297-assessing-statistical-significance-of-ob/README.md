# Assessing Statistical Significance of Observed Correlations in Public Databases

A research pipeline to assess the statistical significance of observed correlations in multivariate datasets from the UCI Machine Learning Repository using permutation testing and multiple testing correction.

## Overview

This project implements a rigorous statistical framework to:
1. Ingest multivariate datasets from the UCI repository
2. Compute observed network statistics from correlation matrices
3. Generate empirical null distributions via permutation testing
4. Apply Benjamini-Yekutieli correction for multiple testing
5. Perform threshold sensitivity analysis

## Project Structure

```
PROJ-297-assessing-statistical-significance-of-ob/
├── code/ # Core implementation
│ ├── config.py # Configuration and path management
│ ├── loaders.py # Data loading and hygiene pipelines
│ ├── stats_engine.py # Statistical analysis and permutation testing
│ ├── correction.py # Multiple testing correction (BY procedure)
│ ├── viz.py # Visualization generation
│ └── main.py # Pipeline orchestration
├── data/
│ ├── raw/ # Downloaded UCI datasets
│ └── processed/ # Cleaned and processed datasets
├── output/
│ ├── results/ # Statistical analysis results
│ ├── plots/ # Generated visualizations
│ ├── reports/ # Summary reports
│ └── exploratory/ # Exploratory analyses (Spearman matrices)
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── docs/ # Documentation
├── requirements.txt # Python dependencies
├── README.md # This file
└── tasks.md # Task tracking
```

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-297-assessing-statistical-significance-of-ob

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Requirements

- Python 3.11+
- pandas
- numpy
- scipy
- networkx
- matplotlib
- seaborn
- requests

## Usage

### Running the Full Pipeline

```bash
# Run the complete analysis pipeline
python code/main.py
```

### Running Specific Analyses

```bash
# Run threshold sensitivity sweep
python code/main.py --task threshold_sweep

# Run synthetic validation (100 iterations)
python code/main.py --task synthetic_validation

# Generate primary threshold visualizations
python code/main.py --task viz_primary
```

### Command Line Arguments

- `--task`: Specify which task to run (default: full pipeline)
 - `full`: Run complete pipeline
 - `synthetic_validation`: Run validation on synthetic data
 - `threshold_sweep`: Run sensitivity analysis
 - `viz_primary`: Generate primary visualizations
- `--threshold`: Correlation threshold for analysis (default: 0.3)
- `--n_permutations`: Number of permutations (default: 1000)
- `--output-dir`: Custom output directory

## Statistical Methods

### Permutation Testing

- N=1,000 permutations per dataset (optimized for feasibility)
- Reduced to N=500 for clustering coefficient on datasets with >50 variables
- Marginal distributions preserved during permutation

### Network Statistics

1. **Mean Absolute Correlation**: Average of absolute correlation values
2. **Edge Density**: Proportion of edges above threshold
3. **Max Absolute Correlation**: Maximum absolute correlation value
4. **Average Clustering Coefficient**: Network clustering measure

### Multiple Testing Correction

- Benjamini-Yekutieli (BY) procedure for FDR control under dependence
- Empirical p-values calculated as (r+1)/(N+1) to avoid 0/1 extremes

### Threshold Sensitivity

Analysis performed across thresholds: {0.1, 0.2, 0.3, 0.4, 0.5}

## Data Sources

- Primary: UCI Machine Learning Repository
- Dynamic discovery mechanism ensures >=3 valid datasets with >=20 continuous variables
- Strict data hygiene: missing values dropped, constant variables excluded

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run unit tests only
python -m pytest tests/unit/ -v

# Run integration tests only
python -m pytest tests/integration/ -v

# Run specific test
python -m pytest tests/unit/test_stats_engine.py::test_permutation_preserves_marginals -v
```

## Validation

The pipeline includes built-in validation:
- Synthetic data validation (identity covariance) should yield p > 0.05 in >=95% of runs
- Threshold sweep validates sensitivity across correlation thresholds
- Primary visualizations generated for threshold |r| > 0.3

## Output Files

### Results
- `output/results/summary.csv`: Dataset statistics, p-values, q-values
- `output/results/sensitivity_report.csv`: Significant counts per threshold
- `output/results/validation_report.json`: Synthetic validation results

### Plots
- `output/plots/primary/heatmap.png`: Correlation matrix heatmap
- `output/plots/primary/histogram.png`: Null distribution with observed value
- `output/plots/sensitivity/*.png`: Sensitivity analysis visualizations

### Reports
- `output/reports/associational_report.txt`: Final associational analysis report
- `output/reports/sensitivity_summary.txt`: Threshold sensitivity summary

## Configuration

Edit `code/config.py` to customize:
- Default correlation threshold
- Number of permutations
- Output directories
- Random seed for reproducibility

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- UCI Machine Learning Repository for dataset availability
- scipy.stats for correlation and statistical functions
- networkx for graph analysis
- matplotlib and seaborn for visualization

## Contact

For questions or issues, please open an issue in the repository.
