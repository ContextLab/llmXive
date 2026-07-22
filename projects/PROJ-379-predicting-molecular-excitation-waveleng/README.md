# Predicting Molecular Excitation Wavelengths with GNNs

This project implements a machine learning pipeline to predict the maximum excitation wavelength (λmax) of molecules from their SMILES strings using Graph Neural Networks (GNNs).

## Prerequisites

- Python 3.9+
- pip
- 7GB+ RAM (CPU-only execution)

## Quickstart

### 1. Environment Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Directory Structure

Ensure the project directory structure exists:

```bash
python code/create_project_dirs.py
```

This creates:
- `data/raw/`
- `data/processed/`
- `code/`
- `tests/`
- `docs/`

### 3. Data Fetching

The pipeline fetches UV-Vis spectral data from the `zjunlp/UV-Vis-ML` Hugging Face dataset. This is handled automatically by the ingestion script.

### 4. Running the Pipeline End-to-End

Execute the full pipeline in sequence:

```bash
# Step 1: Ingest and validate raw data
python code/ingest.py

# Step 2: Split data into train/val/test sets
python code/split.py

# Step 3: Train the GNN model
python code/train.py

# Step 4: Evaluate model performance
python code/evaluate.py
```

### 5. Results

After completion, check the following outputs:
- `data/processed/metrics.json`: Contains MAE, R², and SC-001 status
- `data/processed/model.pt`: Trained GNN model weights
- `data/processed/splits.json`: Train/val/test split information

## Project Structure

```
.
├── code/ # Source code
│ ├── ingest.py # Data ingestion
│ ├── split.py # Data splitting
│ ├── train.py # Model training
│ ├── evaluate.py # Model evaluation
│ ├── models.py # Pydantic data models
│ ├── utils.py # Utility functions
│ └── validate_data.py # Data validation
├── data/
│ ├── raw/ # Raw downloaded data
│ └── processed/ # Processed data and models
├── tests/ # Test suite
├── docs/ # Documentation
├── requirements.txt # Dependencies
└── README.md # This file
```

## Development

### Running Tests

```bash
pytest tests/
```

### Linting

```bash
flake8 code/
```

### Formatting

```bash
black code/
```

## License

MIT License