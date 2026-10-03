# Quickstart Guide

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

1. Ensure UK Biobank data is placed in `data/raw/` with names: `microbiome.csv`, `cognitive.csv`, `dietary.csv`.
2. Run the main pipeline:
 ```bash
 python code/main.py
 ```
3. This will execute:
 - Data Ingestion (T011-T015)
 - Diversity Analysis (T020)
 - Transformation (T021)
 - Correlation, Regression, and VIF Diagnostics (T022-T024)

## Expected Outputs

The pipeline will generate the following files in `data/processed/`:
- `cleaned_data.csv`: Preprocessed dataset.
- `correlation_results.csv`: Spearman correlation results.
- `regression_results.csv`: Multivariate regression coefficients.
- `lasso_results.csv`: Lasso regression results.
- `vif_results.json`: VIF diagnostics for multicollinearity.
- `clr_taxa.csv`: CLR-transformed taxa abundances.
- `plots/`: Visualization files (scatter plots, histograms).