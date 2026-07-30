# Statistical Analysis of Publicly Available Chess Game Data for Elo Rating Prediction

This project implements a statistical analysis pipeline to predict chess game outcomes and analyze Elo ratings using publicly available Lichess game data.

## Features

- **Data Ingestion**: Downloads and parses PGN files from Lichess/HuggingFace
- **Feature Extraction**: Extracts ECO codes, move times, material imbalance at move 5
- **Elo Analysis**: Calculates expected probabilities and outcome deviations
- **Statistical Modeling**: Fits Gaussian GLM and Ridge Regression models
- **Model Validation**: Cross-validation, FDR correction, and sensitivity analysis
- **Diagnostic Reporting**: Generates plots and comprehensive reports

## Project Structure

```
.
├── README.md
├── quickstart.md
├── requirements.txt
├── pyproject.toml
├── code/
│ ├── __init__.py
│ ├── config.py
│ ├── setup_structure.py
│ └── src/
│ ├── __init__.py
│ ├── config.py
│ ├── data/
│ │ ├── __init__.py
│ │ ├── download.py
│ │ ├── parse.py
│ │ └── process.py
│ ├── main.py
│ ├── models/
│ │ ├── __init__.py
│ │ ├── fit.py
│ │ ├── metrics.py
│ │ ├── save_metrics.py
│ │ └── validate.py
│ ├── reports/
│ │ ├── __init__.py
│ │ ├── generate_plots.py
│ │ └── sensitivity.py
│ └── validation/
│ ├── __init__.py
│ └── validate_contracts.py
├── data/
│ ├── raw/
│ ├── processed/
│ └── results/
├── specs/
│ └── contracts/
│ ├── game_record.schema.yaml
│ └── model_output.schema.yaml
└── tests/
 ├── __init__.py
 ├── contract/
 ├── unit/
 └── integration/
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <project-name>
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

See [quickstart.md](quickstart.md) for detailed instructions on running the pipeline.

### Basic Usage

Run the complete pipeline:
```bash
python code/src/main.py
```

## Configuration

Edit `code/src/config.py` to customize:
- Random seeds
- File paths
- Dataset URLs

## Data Pipeline

1. **Download**: Fetches PGN files from Lichess/HuggingFace
2. **Parse**: Extracts features from PGN files
3. **Process**: Calculates Elo probabilities and deviations
4. **Model**: Fits Gaussian GLM and Ridge Regression
5. **Validate**: Performs cross-validation and generates metrics
6. **Report**: Creates diagnostic plots and summaries

## Output Files

- `data/processed/games.parquet`: Processed game records
- `data/results/model_metrics.json`: Model performance metrics
- `data/results/diagnostics.json`: Diagnostic report summary
- `data/results/*.png`: Diagnostic plots

## Validation

The pipeline includes contract validation to ensure data quality:
- Schema validation for game records
- Schema validation for model outputs
- Contract tests in `tests/contract/`

## Testing

Run all tests:
```bash
pytest tests/
```

Run specific test suites:
```bash
pytest tests/unit/
pytest tests/contract/
pytest tests/integration/
```

## Dependencies

See `requirements.txt` for the complete list of dependencies.

## License

This project is licensed under the MIT License.
