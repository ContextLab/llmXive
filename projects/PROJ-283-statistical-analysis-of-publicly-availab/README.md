# Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction

This project implements a statistical analysis pipeline to predict chess game outcomes and analyze the impact of various features (ECO codes, move times, material imbalance) on game results.

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── config.py # Configuration and constants
│ │ ├── data/
│ │ │ ├── download.py # Data download with retry logic
│ │ │ ├── parse.py # PGN parsing and feature extraction
│ │ │ └── process.py # Data processing and calculations
│ │ ├── models/
│ │ │ ├── fit.py # Model fitting (GLM, Ridge)
│ │ │ ├── metrics.py # Statistical metrics and FDR
│ │ │ ├── save_metrics.py # Model artifact saving
│ │ │ └── validate.py # Cross-validation and stability checks
│ │ ├── reports/
│ │ │ ├── generate_plots.py # Diagnostic plot generation
│ │ │ └── sensitivity.py # Sensitivity analysis
│ │ └── validation/
│ │ └── validate_contracts.py # Schema validation
│ └── tests/
│ ├── contract/
│ ├── unit/
│ └── integration/
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed datasets
│ └── results/ # Model outputs and diagnostics
├── specs/
│ ├── contracts/ # Data schemas
│ └── 001-statistical-chess-elo-analysis/
├── requirements.txt # Python dependencies
├── pyproject.toml # Project configuration
└── quickstart.md # Quick start guide
```

## Features

- **Data Ingestion**: Downloads and parses Lichess PGN game data
- **Feature Extraction**: Extracts ECO codes, move times, and material imbalance at move 5
- **Elo Calculations**: Computes expected probabilities and outcome deviations
- **Statistical Modeling**: Fits Gaussian GLM and Ridge regression models
- **Significance Testing**: Applies Benjamini-Hochberg FDR correction
- **Cross-Validation**: Performs k-fold validation with stability checks
- **Diagnostic Reporting**: Generates residual plots and feature importance rankings

## Installation

1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

See `quickstart.md` for detailed usage instructions.

## Configuration

Configuration settings are managed in `code/src/config.py`, including:
- Random seeds for reproducibility
- File path constants
- Lichess dataset URLs

## Validation

The project uses contract-based validation to ensure data integrity:
- Game records validated against `specs/contracts/game_record.schema.yaml`
- Model outputs validated against `specs/contracts/model_output.schema.yaml`

## Testing

Run tests with pytest:
```bash
pytest code/tests/
```

## License

This project is for research purposes.
