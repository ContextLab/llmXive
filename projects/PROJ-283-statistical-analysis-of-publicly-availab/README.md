# Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction

This project implements a statistical analysis pipeline to predict Elo rating outcomes based on publicly available chess game data from Lichess. The system ingests PGN files, extracts features (ECO codes, move times, material imbalance), and fits regression models to analyze the relationship between game features and outcome deviations.

## Features

- **Data Ingestion**: Downloads and parses Lichess PGN game records
- **Feature Extraction**: Calculates ECO codes, average move times, material imbalance at move 5
- **Elo Modeling**: Computes expected probabilities and outcome deviations
- **Statistical Analysis**: Fits Gaussian GLM and Ridge regression models with FDR correction
- **Validation**: Performs k-fold cross-validation and generates diagnostic reports
- **Visualization**: Creates residual plots, predicted vs. actual scatterplots, and feature importance rankings

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── config.py # Configuration and constants
│ │ ├── data/
│ │ │ ├── parse.py # PGN parsing and feature extraction
│ │ │ └── process.py # Data processing and calculations
│ │ ├── models/
│ │ │ ├── fit.py # Model fitting (GLM, Ridge)
│ │ │ ├── metrics.py # Statistical metrics and FDR correction
│ │ │ └── validate.py # Cross-validation and validation pipeline
│ │ ├── reports/
│ │ │ ├── generate_plots.py # Diagnostic plot generation
│ │ │ └── sensitivity.py # Sensitivity analysis
│ │ └── validation/
│ │ └── validate_contracts.py # Schema validation
│ └── tests/
│ ├── unit/ # Unit tests
│ ├── contract/ # Contract tests
│ └── integration/ # Integration tests
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed datasets
│ └── results/ # Model outputs and reports
├── specs/
│ ├── contracts/ # Data schemas
│ └── 001-statistical-chess-elo-analysis/
├── requirements.txt
├── README.md
└── quickstart.md
```

## Prerequisites

- Python 3.11+
- pip package manager

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Verify installation:
 ```bash
 python -c "import pandas, numpy, sklearn, statsmodels, chess; print('All dependencies installed successfully')"
 ```

## Usage

### Quick Start

See `quickstart.md` for a step-by-step guide to running the pipeline.

### Running the Pipeline

The pipeline consists of several stages that can be run independently:

1. **Data Download and Parsing**:
 ```bash
 python code/src/data/parse.py
 ```

2. **Data Processing**:
 ```bash
 python code/src/data/process.py
 ```

3. **Model Fitting**:
 ```bash
 python code/src/models/fit.py
 ```

4. **Model Validation**:
 ```bash
 python code/src/models/validate.py
 ```

5. **Generate Reports and Plots**:
 ```bash
 python code/src/reports/generate_plots.py
 ```

### Running Tests

```bash
pytest code/tests/ -v
```

## Configuration

Edit `code/src/config.py` to modify:
- Random seeds for reproducibility
- File paths
- Lichess dataset URLs
- Analysis parameters

## Output Files

The pipeline generates the following outputs:

- `data/processed/games.parquet`: Cleaned and processed game records
- `data/results/model_metrics.json`: Model coefficients, p-values, R², AIC
- `data/results/diagnostics.json`: Cross-validation results and diagnostic summary
- `data/results/*.png`: Diagnostic plots (residuals, predicted vs. actual, feature importance)

## Contract Validation

The system uses YAML schemas defined in `specs/contracts/` to validate data integrity:
- `game_record.schema.yaml`: Validates game record structure
- `model_output.schema.yaml`: Validates model output structure

Run validation:
```bash
python code/src/validation/validate_contracts.py
```

## License

This project is for research purposes.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
