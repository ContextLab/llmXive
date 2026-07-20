# Ball Milling PSD Prediction

This project predicts the impact of ball milling on particle size distribution (PSD) using machine learning models trained on experimental data from public repositories.

## Requirements

- Python 3.11+
- pip

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. (Optional) Install dev dependencies:
 ```bash
 pip install -e ".[dev]"
 ```

## Project Structure

```
.
├── code/ # Setup scripts
├── src/ # Source code
│ ├── cli/ # CLI entry points
│ ├── config/ # Configuration management
│ ├── exceptions.py # Custom exceptions
│ ├── ingest/ # Data ingestion modules
│ ├── interpret/ # Model interpretation
│ ├── model/ # Model training
│ ├── preprocess/ # Data preprocessing
│ └── utils/ # Utilities
├── tests/ # Test suite
├── data/ # Data directories
│ ├── raw/
│ ├── processed/
│ └── splits/
├── results/ # Model results and reports
├── contracts/ # Data schemas
├── requirements.txt # Production dependencies
├── pyproject.toml # Project configuration
└── README.md
```

## Usage

### Data Ingestion
```bash
python -m src.cli.ingest
```

### Model Training
```bash
python -m src.cli.train
```

### Interpretation
```bash
python -m src.cli.interpret
```

## License

MIT License