# Predicting the Impact of Composition on the Vickers Hardness of Solder Alloys

**Project ID**: PROJ-328
**Status**: Research Pipeline Implementation

## Overview

This project implements an automated scientific research pipeline to predict the Vickers hardness (HV) of solder alloys based on their elemental composition. The pipeline ingests data from open sources (Materials Project, NIST, literature), validates compositions, engineers physical descriptors, trains regression models (XGBoost, Linear Regression), and performs rigorous statistical analysis including sensitivity analysis and SHAP interpretability.

## Key Features

- **Data Ingestion**: Aggregates solder alloy data from multiple verified sources (APIs and literature PDFs).
- **Validation**: Enforces strict composition sum thresholds (>95%) and element count limits (≤5).
- **Feature Engineering**: Calculates physical descriptors (atomic mass, electronegativity, etc.) and applies CLR transforms for compositional data.
- **Modeling**: Trains and compares XGBoost and Linear Regression models with cross-validation and bootstrap confidence intervals.
- **Interpretability**: Generates SHAP value rankings and partial dependence plots.
- **Sensitivity Analysis**: Evaluates model robustness across varying R² thresholds.
- **Reproducibility**: CPU-only execution, fixed random seeds, and comprehensive logging.

## Quickstart

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Running the Pipeline

Execute the full research pipeline:

```bash
python code/run_pipeline.py
```

This will:
1. Ingest and clean data from verified sources.
2. Validate composition sums and filter records.
3. Engineer physical and compositional descriptors.
4. Train and evaluate models.
5. Generate visualizations and reports.

### Output Artifacts

All outputs are written to the `data/` and `data/outputs/` directories:

- `data/processed/solder_hardness_cleaned.csv`: Validated dataset.
- `data/processed/descriptors.csv`: Physical descriptor features.
- `data/processed/clr_features.csv`: CLR-transformed compositional features.
- `data/processed/model_metrics.yaml`: Performance metrics (R², RMSE).
- `data/outputs/sensitivity_plot.png`: Sensitivity analysis visualization.
- `data/outputs/scatter_predictions.png`: Predicted vs. measured hardness plot.
- `data/processed/final_aggregated_report.yaml`: Summary of all results.

## Project Structure

```
.
├── code/
│ ├── config.py # Configuration constants
│ ├── run_pipeline.py # Main entry point
│ ├── ingestion/ # Data fetching, scraping, cleaning
│ ├── features/ # Descriptor engineering, transforms
│ ├── models/ # Model training and evaluation
│ ├── evaluation/ # CV, bootstrap, SHAP, sensitivity
│ ├── visualization/ # Plot generation
│ └── utils/ # Logging, error handling
├── data/
│ ├── raw/ # Immutable raw data
│ ├── processed/ # Cleaned and validated data
│ └── outputs/ # Final reports and figures
├── specs/ # Research specifications and drafts
└── tests/ # Contract and integration tests
```

## Data Sources

Data is ingested from:
- **Materials Project API**: Crystallographic and material properties.
- **NIST/UCI Repositories**: Standardized alloy datasets.
- **Literature (PDFs)**: Systematic extraction from verified scientific papers.

See `data/config/sources.yaml` for the full list of verified sources.

## Validation & Compliance

- **Constitution Principle II**: Ensures citation integrity and title overlap thresholds.
- **FR-007 (Associational Framing)**: All reports explicitly state findings are associational, not causal.
- **SC-004 (Composition Sum)**: Records with composition sums <95% are excluded and logged.
- **SC-007 (Compute Feasibility)**: Pipeline verified to run within 6h, 7GB RAM, 14GB disk.

## License

This project is for research purposes. All data sources are used under their respective open licenses.
