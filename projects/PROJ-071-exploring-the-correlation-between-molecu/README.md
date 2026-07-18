# Exploring the Correlation Between Molecular Complexity and Degradation Rates in Pharmaceuticals

## Project Overview

This research project investigates whether molecular complexity metrics (such as TPSA, molecular weight, rotatable bond count, etc.) correlate with pharmaceutical degradation rates. The pipeline ingests FDA-approved drug structures, calculates molecular descriptors, performs statistical analysis, and generates comprehensive reports.

## Research Question

**Does molecular complexity correlate with degradation rates in pharmaceuticals?**

## Methodology

1. **Data Ingestion**: Fetch FDA-approved drug structures from HuggingFace
2. **Descriptor Calculation**: Compute molecular complexity metrics using RDKit
3. **Data Standardization**: Convert degradation rates to half-lives, stratify by conditions
4. **Correlation Analysis**: Calculate Pearson and Spearman correlations
5. **Regression Modeling**: Fit MLR and LASSO models with cross-validation
6. **Diagnostics**: Perform residual analysis (Shapiro-Wilk, Breusch-Pagan)
7. **Visualization**: Generate scatter plots, residual plots, and Q-Q plots
8. **Reporting**: Create comprehensive results and reproducibility reports

## Project Structure

```
projects/PROJ-071-exploring-the-correlation-between-molecu/
├── code/
│ ├── __init__.py
│ ├── analysis.py # Correlation and regression analysis
│ ├── config.py # Configuration management
│ ├── descriptors.py # Molecular descriptor calculations
│ ├── error_handlers.py # Custom error handling
│ ├── ingest.py # Data ingestion and validation
│ ├── logging_config.py # Logging setup
│ ├── models.py # Data models (Pydantic)
│ ├── pipeline_runner.py # Main pipeline orchestration
│ ├── report.py # Report generation
│ ├── standardize.py # Data standardization
│ ├── validate_performance.py # Performance validation (T042)
│ ├── verify_outputs.py # Output verification
│ └── viz.py # Visualization generation
├── data/
│ ├── raw/ # Raw data (downloaded)
│ ├── processed/ # Processed data and analysis results
│ └── outputs/ # Visualizations and reports
├── tests/
│ ├── conftest.py # Shared test fixtures
│ ├── test_analysis.py # Analysis module tests
│ ├── test_descriptors.py # Descriptor calculation tests
│ ├── test_performance_validation.py # Performance validation tests
│ ├── test_pipeline.py # Integration tests
│ ├── test_standardize.py # Standardization tests
│ └── test_viz.py # Visualization tests
├── requirements.txt # Python dependencies
├── quickstart.md # Quick start guide
└── README.md # This file
```

## Key Features

### Data Availability Gate
The pipeline enforces a minimum sample size (N ≥ 30) before proceeding with analysis. If this threshold is not met, a detailed insufficiency report is generated.

### Molecular Descriptors
Calculated using RDKit:
- Topological Polar Surface Area (TPSA)
- Molecular Weight (MW)
- Rotatable Bond Count
- Aromatic Ring Count
- Wiener Index
- Zagreb Index

### Statistical Analysis
- Pearson and Spearman correlation matrices
- Multiple Linear Regression (MLR)
- LASSO regression with 5-fold cross-validation
- Residual diagnostics (Shapiro-Wilk, Breusch-Pagan)

### Performance Validation
The pipeline includes operational latency validation (T042) to ensure it meets performance requirements. Execution time is measured and compared against a configurable threshold.

## Installation

```bash
# Clone repository
git clone <repository-url>
cd projects/PROJ-071-exploring-the-correlation-between-molecu

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import rdkit; print('RDKit installed')"
```

## Usage

### Run Full Pipeline
```bash
python code/pipeline_runner.py
```

### Validate Performance
```bash
python code/validate_performance.py
```

### Run Tests
```bash
pytest tests/ -v
```

## Output Files

| File | Description |
|------|-------------|
| `data/processed/merged_drugs.csv` | Combined structural and degradation data |
| `data/processed/analysis_results.json` | Correlation and regression results |
| `data/outputs/scatter_tpsa_vs_half_life.png` | Scatter plot with regression line |
| `data/outputs/residuals.png` | Residual diagnostic plots |
| `data/outputs/qq_plot.png` | Q-Q plot for residual normality |
| `results_report.md` | Comprehensive results report |
| `reproducibility_log.json` | Reproducibility metadata |
| `data/processed/performance_validation.json` | Performance validation results |

## Performance Requirements

- **Execution Time Threshold**: 300 seconds (5 minutes)
- **Memory Requirement**: 7GB+ RAM recommended
- **Minimum Sample Size**: 30 records with degradation data

## Dependencies

Core dependencies include:
- `rdkit`: Molecular descriptor calculations
- `pandas`: Data manipulation
- `scikit-learn`: Regression modeling
- `numpy`: Numerical computations
- `matplotlib`/`seaborn`: Visualization
- `datasets`: HuggingFace dataset loading
- `pyyaml`: Configuration management

See `requirements.txt` for the complete list.

## Testing

The project includes comprehensive tests:
- Unit tests for descriptor calculations (T010a-T010f)
- Unit tests for analysis functions (T018, T019, T024a)
- Integration tests for pipeline execution (T031)
- Performance validation tests (T042)

Run tests with:
```bash
pytest tests/ -v --tb=short
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

## License

This project is for research purposes only. See LICENSE for details.

## References

- FDA-approved drugs dataset: HuggingFace `Synthyra/FDA-Approved-Drugs`
- RDKit documentation: https://www.rdkit.org/docs/
- scikit-learn documentation: https://scikit-learn.org/
