# Predicting the Yield Strength of Steel Alloys

An automated research pipeline to predict the yield strength of steel alloys based on chemical composition and heat treatment parameters. This project implements a rigorous scientific workflow including data ingestion, feature engineering (with orthogonalization), multi-model training, and sensitivity analysis.

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── data/
│ │ │ ├── ingest.py
│ │ │ ├── features.py
│ │ │ └── loader.py
│ │ ├── models/
│ │ │ ├── train.py
│ │ │ ├── evaluate.py
│ │ │ └── sensitivity.py
│ │ ├── utils/
│ │ │ ├── config.py
│ │ │ └── validators.py
│ │ └── main.py
│ └── tests/
├── data/
│ ├── raw/
│ ├── processed/
│ └── results/
├── docs/
├── requirements.txt
└── README.md
```

## Installation

1. Create a virtual environment (Python 3.11 recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

Run the pipeline stages via the CLI:

```bash
# 1. Ingest and clean data
python code/src/main.py ingest --sources nist materials_project --output data/processed/ingested.csv

# 2. Engineer features
python code/src/main.py features --input data/processed/ingested.csv --output data/processed/features.csv

# 3. Train models
python code/src/main.py train --data data/processed/features.csv --output data/results/models/

# 4. Evaluate (SHAP, PDP, Permutation tests)
python code/src/main.py evaluate --data data/processed/features.csv --models data/results/models/ --output data/results/evaluation/

# 5. Sensitivity Analysis
python code/src/main.py sensitivity --results data/results/evaluation/ --output data/results/sensitivity_report.md
```

## Data Sources

- **NIST Materials Data Repository**: Primary source for steel composition and yield strength data.
- **Materials Project**: Secondary source for crystallographic and thermodynamic properties.
- **Literature Mining**: Fallback mechanism using web scraping for open-access metallurgy journals.

## Methodology

- **Feature Engineering**: Includes elemental ratios (C/Mn, Cr/Ni), pairwise interactions (cooling rate × holding time), and non-linear orthogonalization against main effects using natural splines.
- **Models**: Generalized Additive Models (GAM), Regularized Linear Regression, Random Forest, and XGBoost.
- **Validation**: Nested permutation tests, SHAP interaction values, and Partial Dependence Plots (PDPs).
- **Sensitivity**: Threshold sweeps (0.01, 0.05, 0.10) with Jaccard index and Kuncheva index for stability assessment.

## License

MIT License

## Contributing

See `docs/CONTRIBUTING.md` for guidelines on adding new tasks and extending the pipeline.
