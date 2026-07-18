# Exploring the Correlation Between Molecular Complexity and Degradation Rates in Pharmaceuticals

This project investigates the relationship between molecular complexity metrics (e.g., TPSA, Wiener Index, Zagreb Index) and the degradation half-lives of FDA-approved pharmaceuticals. By analyzing real-world data, we aim to identify if more complex molecules exhibit different stability profiles compared to simpler ones.

## Project Overview

The pipeline consists of three main phases:
1. **Data Ingestion & Descriptor Calculation**: Fetches drug structures from the HuggingFace `Synthyra/FDA-Approved-Drugs` dataset, validates degradation data, and computes molecular descriptors using RDKit.
2. **Standardization & Analysis**: Standardizes degradation rates to half-lives (hours), applies Arrhenius normalization where possible, and performs correlation analysis and regression modeling (MLR, LASSO).
3. **Visualization & Reporting**: Generates diagnostic plots (residuals, QQ-plots) and a comprehensive reproducibility report.

## Key Features

- **Real Data Processing**: Uses the `Synthyra/FDA-Approved-Drugs` dataset via the HuggingFace `datasets` library. No synthetic data is used.
- **Robust Error Handling**: Implements a "Data Availability Gate" to ensure statistical validity (N ≥ 30) and flags molecules with valence errors.
- **Advanced Modeling**: Includes Multiple Linear Regression (MLR), LASSO with cross-validation, and sensitivity analysis.
- **Reproducibility**: Automatically logs package versions, dataset hashes, and retrieval dates in the final report.

## Quick Start

See [`quickstart.md`](quickstart.md) for a step-by-step guide to installation and execution.

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
git clone <repository-url>
cd PROJ-071-exploring-the-correlation-between-molecu
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the Pipeline

1. **Setup Data Directories**:
 ```bash
 python code/setup_data.py
 ```
2. **Run Ingestion & Descriptors**:
 ```bash
 python code/ingest.py
 ```
3. **Run Standardization & Analysis**:
 ```bash
 python code/standardize.py
 python code/analysis.py
 ```
4. **Run Visualization & Reporting**:
 ```bash
 python code/viz.py
 python code/report.py
 ```

## Project Structure

```
PROJ-071-exploring-the-correlation-between-molecu/
├── code/
│ ├── __init__.py
│ ├── ingest.py # Data fetching and merging
│ ├── descriptors.py # RDKit descriptor calculation
│ ├── standardize.py # Unit conversion and normalization
│ ├── analysis.py # Correlation and regression
│ ├── viz.py # Plot generation
│ ├── report.py # Report generation
│ ├── models.py # Pydantic data models
│ ├── error_handlers.py # Error handling utilities
│ ├── logging_config.py # Logging setup
│ ├── setup_data.py # Directory initialization
│ └── verify_outputs.py # Output validation
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Cleaned/merged data
│ ├── outputs/ # Generated plots
│ └── output_schema.yaml # Output schema definition
├── tests/
│ ├── conftest.py
│ ├── test_pipeline.py
│ ├── test_descriptors.py
│ ├── test_standardize.py
│ └── test_analysis.py
├── results_report.md # Final generated report
├── requirements.txt
├── quickstart.md
└── README.md
```

## Methodology

1. **Data Source**: `Synthyra/FDA-Approved-Drugs` from HuggingFace.
2. **Descriptors**: TPSA, Rotatable Bond Count, Molecular Weight, Aromatic Ring Count, Wiener Index, Zagreb Index.
3. **Degradation Metric**: Half-life (t1/2) converted from rate constants (k) and normalized to standard conditions (25°C, pH 7.4) using the Arrhenius equation where Activation Energy (Ea) is available.
4. **Statistical Analysis**:
 - Pearson and Spearman correlation matrices.
 - Multiple Linear Regression (MLR) and LASSO with k-fold cross-validation.
 - Residual diagnostics (Shapiro-Wilk, Breusch-Pagan).

## Results

Upon successful completion, the project generates:
- `results_report.md`: A detailed summary of findings, coefficients, and model performance.
- `data/outputs/*.png`: Visualizations of correlations and residuals.
- `data/processed/analysis_results.json`: Raw statistical data for further inspection.

## Contributing

Contributions are welcome! Please refer to the `tasks.md` file for the current implementation roadmap and `CONTRIBUTING.md` for guidelines.

## License

[Insert License Here]