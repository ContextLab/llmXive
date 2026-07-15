# Predicting Plant Root Architecture from Soil Nutrient Availability

## Project Overview

This project implements an automated scientific pipeline to predict plant root architecture based on soil nutrient availability. It ingests root phenotype data from RootReader/PlantPheno and soil nutrient data from ISRIC, processes and merges these datasets, fits statistical models (Linear Mixed-Effects Models and Random Forest), and generates comprehensive reports with visualizations.

## User Stories

### US1: Data Ingestion and Preprocessing Pipeline (MVP)
- Ingest root phenotype data from RootReader/PlantPheno
- Fetch soil nutrient data from ISRIC
- Filter for valid observations (n≥20 per species)
- Merge with spatial interpolation
- Produce cleaned, merged dataset

### US2: Statistical Modeling and Association Analysis
- Fit Linear Mixed-Effects Models (LMM)
- Fit baseline Random Forest models
- Perform species-level cross-validation
- Report statistical significance

### US3: Visualization and Reporting
- Generate partial dependence plots
- Compile final report with statistical findings
- Ensure output size constraints

## Project Structure

```
.
├── code/
│ ├── config.py # Configuration and logging setup
│ ├── config.yaml.template # Environment configuration template
│ ├── data_ingestion.py # Data loading and merging
│ ├── preprocessing.py # Data transformation and imputation
│ ├── modeling.py # Model training and evaluation
│ ├── visualization.py # Plot generation
│ ├── reporting.py # Report compilation
│ ├── sensitivity_analysis.py # Sensitivity analysis
│ ├── models.py # Data models
│ └── requirements.txt # Python dependencies
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed datasets
├── artifacts/
│ ├── models/ # Trained model artifacts
│ ├── plots/ # Generated visualizations
│ └── reports/ # Final reports and metrics
├── tests/
│ ├── contract/ # Schema contract tests
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── docs/
│ └── README.md # This file
├──.flake8 # Linting configuration
└── pyproject.toml # Project configuration
```

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
3. Configure environment:
 ```bash
 cp code/config.yaml.template code/config.yaml
 # Edit config.yaml with your settings
 ```

### Running the Pipeline

1. **Data Ingestion and Preprocessing**:
 ```bash
 python code/data_ingestion.py
 python code/preprocessing.py
 ```

2. **Model Training**:
 ```bash
 python code/modeling.py
 ```

3. **Visualization and Reporting**:
 ```bash
 python code/visualization.py
 python code/reporting.py
 ```

### Running Tests

```bash
python -m pytest tests/
```

### Code Quality

```bash
black code/
flake8 code/
```

## Data Sources

- **Root Phenotype Data**: RootReader and PlantPheno datasets
- **Soil Nutrient Data**: ISRIC SoilGrids
- **Note**: All data is fetched from real sources. The pipeline will fail loudly if data cannot be retrieved.

## Model Details

### Linear Mixed-Effects Models (LMM)
- Random intercept for species
- REML estimation
- Satterthwaite p-values

### Random Forest Baseline
- max_depth=5
- CPU-only execution
- Limited n_estimators for runtime constraints

## Output Artifacts

- **Processed Data**: `data/processed/merged_dataset.csv`
- **Model Results**: `artifacts/models/`
- **Visualizations**: `artifacts/plots/`
- **Reports**: `artifacts/reports/`

## Success Criteria

- **SC-001**: Merge success rate documented
- **SC-002**: LMM vs RF R² difference ≤ 5%
- **SC-004**: Total output size ≤ 100MB
- **SC-005**: Excluded species documented
- **SC-006**: Biological plausibility verified

## Contributing

1. Follow PEP8 style guidelines
2. Write tests for new functionality
3. Update documentation as needed

## License

[License information]
