# Assessing Statistical Significance of Observed Correlations in Public Databases

## Project Overview

This project implements a rigorous statistical pipeline to assess the significance of observed correlations in multivariate public datasets (specifically from the UCI Machine Learning Repository). It moves beyond naive p-value reporting by employing **permutation testing** to generate empirical null distributions and the **Benjamini-Yekutieli (BY)** procedure to control the False Discovery Rate (FDR) under arbitrary dependence.

The pipeline is designed to answer: "Is the observed network structure (density, clustering, max correlation) significantly different from what we would expect by chance given the marginal distributions of the variables?"

## Key Features

- **Dynamic Dataset Discovery**: Automatically fetches and validates multivariate datasets from UCI with >=20 continuous variables.
- **Robust Data Hygiene**: Enforces strict cleaning (missing value removal, constant variable exclusion).
- **Empirical Null Modeling**: Generates null distributions via 1,000 permutations per dataset, preserving marginal distributions.
- **Multiple Testing Correction**: Implements the Benjamini-Yekutieli procedure to correct for multiple comparisons across datasets and statistics.
- **Threshold Sensitivity Analysis**: Sweeps correlation thresholds {0.1, 0.2, 0.3, 0.4, 0.5} to assess robustness of findings.
- **Visualization**: Generates heatmaps and histograms for primary thresholds and sensitivity sweeps.

## Installation

1. Ensure you have Python 3.9+ installed.
2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Running the Full Pipeline

Execute the main analysis script to process datasets, run permutations, apply corrections, and generate reports:

```bash
python code/main.py
```

This will:
1. Discover and load valid UCI datasets.
2. Compute observed correlation matrices and graph statistics.
3. Generate null distributions via permutation.
4. Calculate empirical p-values and apply BY correction.
5. Perform threshold sensitivity analysis.
6. Save results to `output/results/`, `output/plots/`, and `output/reports/`.

### Running Tests

Unit and integration tests can be run with pytest:

```bash
pytest tests/ -v
```

To run the quickstart validation:

```bash
python -m pytest tests/integration/test_quickstart.py -v
```

## Project Structure

```
.
├── code/
│ ├── config.py # Configuration paths and parameters
│ ├── loaders.py # Data fetching and hygiene pipeline
│ ├── stats_engine.py # Core statistical logic (correlation, permutation, graph stats)
│ ├── correction.py # Benjamini-Yekutieli correction implementation
│ ├── viz.py # Visualization generation (heatmaps, histograms)
│ └── main.py # Pipeline orchestration
├── data/
│ ├── raw/ # Downloaded raw UCI datasets
│ └── processed/ # Cleaned and validated datasets
├── output/
│ ├── results/ # Statistical summaries (CSV)
│ ├── plots/ # Generated visualizations (PNG)
│ └── reports/ # Final summary reports
├── tests/
│ ├── unit/ # Unit tests for individual components
│ └── integration/ # End-to-end pipeline tests
├── requirements.txt # Python dependencies
├── README.md # This file
└── docs/
 └── methodology.md # Detailed statistical methodology and assumptions
```

## Statistical Methodology

### Null Model Generation
For each dataset, we generate an empirical null distribution by permuting the values within each column (variable) independently. This preserves the marginal distribution of each variable while breaking any true associations between them. We compute the statistic of interest (e.g., mean absolute correlation, edge density) for each of the 1,000 permuted datasets.

### Significance Testing
The empirical p-value is calculated as:
```
p = (r + 1) / (N + 1)
```
where `r` is the number of permuted statistics greater than or equal to the observed statistic, and `N` is the number of permutations.

### Multiple Testing Correction
We apply the Benjamini-Yekutieli (BY) procedure to control the FDR under arbitrary dependence structures. This is more conservative than the standard Benjamini-Hochberg (BH) procedure and is required for our analysis where correlation tests are not independent.

### Threshold Sensitivity
To assess the robustness of our findings, we repeat the analysis across a range of correlation thresholds: {0.1, 0.2, 0.3, 0.4, 0.5}. This helps identify whether significant findings are stable or highly sensitive to the choice of threshold.

## Configuration

Key parameters can be adjusted in `code/config.py`:
- `DATA_RAW_DIR`: Directory for raw data
- `DATA_PROCESSED_DIR`: Directory for processed data
- `OUTPUT_RESULTS_DIR`: Directory for results
- `RANDOM_SEED`: Seed for reproducibility
- `PERMUTATIONS`: Number of permutations (default: 1000)
- `THRESHOLDS`: List of correlation thresholds for sensitivity analysis

## Contributing

When adding new features:
1. Ensure all new code passes existing tests.
2. Add new tests for new functionality.
3. Update documentation in `docs/` if methodology changes.
4. Run `black` and `flake8` for code style compliance.

## License

This project is licensed under the MIT License.
