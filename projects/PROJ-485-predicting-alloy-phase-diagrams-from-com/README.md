# PROJ-485: Predicting Alloy Phase Diagrams from Compositional Data

## Project Structure

```
.
├── code/
│ ├── __init__.py
│ ├── ingest/
│ │ ├── __init__.py
│ │ └── load_data.py
│ ├── features/
│ │ ├── __init__.py
│ │ └── generate_descriptors.py
│ ├── models/
│ │ ├── __init__.py
│ │ └── train.py
│ ├── viz/
│ │ ├── __init__.py
│ │ └── plot_phase_diagrams.py
│ ├── utils/
│ │ ├── __init__.py
│ │ ├── logging.py
│ │ ├── checksum.py
│ │ ├── error_codes.py
│ │ └── config.py
│ ├── main.py
│ └── setup_directories.py
├── data/
│ ├── raw/
│ ├── processed/
│ └── artifacts/
├── tests/
│ ├── __init__.py
│ └── test_*.py
├── state/
│ └── PROJ-485/
├──.gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Setup

1. Create virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Create project directories:
 ```bash
 python code/setup_directories.py
 ```

## Configuration

- Linting: Ruff (configured in `pyproject.toml`)
- Formatting: Black (configured in `pyproject.toml`)
- Testing: pytest (configured in `pyproject.toml`)

## Data Sources

- Primary: NIST-JANAF/SGTE (configurable via environment variables)
- Fallback: Local CSV files in `data/raw/`

## Constitution Principles

- **Principle II**: Data integrity and verification
- **Principle III**: Data checksumming and verification
- **Principle V**: State management and artifact tracking

## License

MIT License