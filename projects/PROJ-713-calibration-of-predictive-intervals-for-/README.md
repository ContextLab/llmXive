# Calibration of Predictive Intervals for Time-Series Forecasts

## Project Structure

```
.
├── code/ # Source code
│ ├── config.py # Configuration
│ ├── data_loader.py # Data loading utilities
│ ├── models/ # Forecasting models
│ ├── metrics/ # Evaluation metrics
│ ├── evaluation/ # Evaluation pipeline
│ └── utils/ # Utilities
├── data/
│ ├── raw/ # Raw data downloads
│ └── processed/ # Processed data
├── results/ # Output results
├── tests/ # Test suite
├── requirements.txt # Python dependencies
└── README.md
```

## Setup

1. Create virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # Linux/Mac
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Initialize directory structure:
 ```bash
 python code/setup_data_dirs.py
 ```

## Usage

Run the evaluation pipeline:
```bash
python code/evaluation/runner.py
```

## Data

This project uses M4 and UCI Electricity datasets. Data is downloaded automatically by `data_loader.py`.

## Testing

Run tests:
```bash
pytest tests/
```

## Linting

Run linter:
```bash
flake8 code/
black --check code/
```