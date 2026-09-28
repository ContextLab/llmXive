# PROJ-277: Predicting the Impact of Alloying on High-Temperature Oxidation Resistance

## Project Structure

```
projects/PROJ-277-predicting-oxidation-resistance/
├── code/ # Source code
│ ├── data/ # Data fetching and processing
│ ├── models/ # Model training and evaluation
│ ├── utils/ # Utilities and logging
│ ├── viz/ # Visualization
│ ├── scripts/ # Helper scripts
│ └── __init__.py
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed data
├── tests/ # Test suite
│ ├── contract/ # Contract tests
│ ├── integration/ # Integration tests
│ └── unit/ # Unit tests
├── logs/ # Log files
├──.gitignore # Git ignore patterns
├──.pre-commit-config.yaml # Pre-commit hooks
├── pyproject.toml # Project configuration
└── README.md # This file
```

## Setup

1. Create virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -e ".[dev]"
 ```

3. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Usage

Run the main pipeline:
```bash
python code/main.py --mode=ci
```

Run tests:
```bash
pytest tests/
```

## License

Internal use only.