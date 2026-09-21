# Predicting Yield Strength of BCC Alloys

This project implements an automated science pipeline to predict the yield strength of Body-Centered Cubic (BCC) alloys using machine learning.

## Project Structure

```
.
├── code/ # Source code for the pipeline
│ ├── config.py # Configuration management (local vs CI)
│ ├── data_ingestion.py # Data download and filtering
│ ├── feature_engineering.py # Feature generation
│ ├── modeling.py # Model training and validation
│ ├── utils.py # Utility functions
│ └──...
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed and filtered data
│ └── logs/ # Execution logs
├── reports/ # Model comparison reports
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
├── pyproject.toml # Project configuration (black, ruff, pytest)
└── README.md
```

## Setup

1. **Create Virtual Environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. **Install Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

3. **Configure Environment**:
 The `code/config.py` module automatically detects if running in a CI environment or locally.
 - **Local**: Uses standard paths relative to the project root.
 - **CI**: Adjusts resource limits and paths based on environment variables.

## Usage

Run the pipeline steps sequentially:

```bash
# 1. Ingest and Filter Data
python code/01_download.py

# 2. Engineer Features
python code/02_engineer.py

# 3. Train Models
python code/modeling.py
```

## Linting and Formatting

```bash
python code/lint_format.py
```

Or manually:
```bash
ruff check code/
black --check code/
```

## Testing

```bash
pytest
```
