# The Impact of Simulated Social Validation on Self-Perception in Adolescents

## Project Overview

This research project investigates the relationship between simulated social validation (e.g., likes, comments, engagement metrics) and self-perception in adolescents. The study utilizes a rigorous statistical pipeline to analyze longitudinal data, ensuring methodological robustness through Structural Equation Modeling (SEM), multiple linear regression with confounder control, and extensive sensitivity analyses.

**Key Objectives:**
- Quantify the association between perceived social validation and self-esteem scores.
- Control for critical confounders (age, gender, offline relationships, intrinsic traits).
- Validate findings against stability thresholds and non-linearity checks.
- Ensure all reported findings are strictly "associational" to avoid causal overreach.

## Project Structure

```text
PROJ-447-the-impact-of-simulated-social-validation/
├── code/
│ ├── data/
│ │ ├── __init__.py
│ │ ├── generator.py # Synthetic data generation via SEM
│ │ ├── loader.py # Real data fetching logic
│ │ ├── processor.py # Feature engineering (PSV calculation)
│ │ └── validator.py # Data quality and structure checks
│ ├── analysis/
│ │ ├── __init__.py
│ │ ├── regression.py # Multiple linear regression & VIF
│ │ ├── sensitivity.py # Robustness checks (outliers, confounders)
│ │ └── nonlinearity.py # Quadratic term analysis
│ ├── viz/
│ │ ├── __init__.py
│ │ ├── plots.py # Diagnostic visualizations
│ │ └── validator.py # Visualization count validation
│ ├── utils/
│ │ ├── __init__.py
│ │ ├── constants.py # Configuration, thresholds, seeds
│ │ ├── exceptions.py # Custom exception classes
│ │ ├── logger.py # Logging infrastructure
│ │ └── config.py # Environment/config management
│ ├── main.py # Pipeline orchestration
│ └── setup_structure.py # Directory initialization
├── data/
│ ├── raw/ # Raw data storage
│ └── processed/ # Processed data, model results, plots
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── requirements.txt # Python dependencies
├── quickstart.md # Execution guide
└── README.md # This file
```

## Dependencies

Install all required dependencies using pip:

```bash
pip install -r requirements.txt
```

**Core Libraries:**
- `pandas`, `numpy`: Data manipulation
- `scipy`, `statsmodels`, `scikit-learn`: Statistical modeling
- `semopy`: Structural Equation Modeling
- `matplotlib`, `seaborn`: Visualization
- `pytest`: Testing
- `ruff`, `black`: Code quality

## Quick Start

1. **Initialize Structure** (if not already done):
 ```bash
 python code/setup_structure.py
 ```

2. **Run the Full Pipeline**:
 The main script handles data loading (real or synthetic), validation, modeling, sensitivity analysis, and visualization.
 ```bash
 python code/main.py
 ```

3. **View Results**:
 - **Model Results**: `data/processed/model_results.json`
 - **Pipeline Log**: `data/processed/pipeline_run_log.json`
 - **Visualizations**: `data/processed/scatter_plot.png`, `data/processed/residuals.png`

## Methodology

### Data Generation & Validation
- **Real Data**: The pipeline attempts to fetch real datasets. If unavailable, it falls back to synthetic data generated via SEM (`semopy`) to simulate measurement error and reverse causality.
- **Validation**: Checks for sample size (N ≥ 100), longitudinal ordering, and required column presence.

### Statistical Analysis
- **Primary Model**: Multiple linear regression with confounders (Age, Gender, Offline Relationships, Intrinsic Traits).
- **Multicollinearity**: Variance Inflation Factor (VIF) calculated for all predictors.
- **Sensitivity**: 3x2 matrix analysis (3 outlier strategies × 2 confounder states) to verify coefficient stability.
- **Non-linearity**: Quadratic term fitting to detect non-linear relationships.

### Quality Assurance
- **Causal Language Check**: Automated scanner rejects reports containing causal trigger words (e.g., "causes", "leads to").
- **Stability Threshold**: Pipeline halts if coefficient variation exceeds defined thresholds.

## Testing

Run the full test suite:
```bash
pytest tests/
```

Specific test categories:
- `tests/unit/`: Unit tests for generators, validators, and regression models.
- `tests/integration/`: End-to-end sensitivity and visualization tests.

## Contributing

1. Ensure code passes `ruff check` and `black --check`.
2. Add tests for new functionality.
3. Update documentation if new configuration options are added.

## License

[Insert License Information Here]
