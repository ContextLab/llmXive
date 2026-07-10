# Predicting Molecular Excitation Wavelengths from SMILES with Graph Neural Networks

This project implements a pipeline to predict molecular excitation wavelengths ($\lambda_{max}$) from SMILES strings using Graph Neural Networks (GNNs). It follows a rigorous scientific protocol including data ingestion, scaffold-based splitting, model training, and statistical validation.

## Prerequisites

- Python 3.9+
- 7GB+ RAM (CPU-only execution)
- pip and virtual environment tools

## Quickstart

### 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Dependencies**:
- `rdkit==2023.9.5`
- `torch==2.1.0+cpu`
- `torch-geometric==2.4.0`
- `pandas==2.1.0`
- `scikit-learn==1.3.0`
- `numpy==1.24.0`
- `pyyaml==6.0.1`
- `pytest==7.4.0`
- `datasets` (for HuggingFace dataset loading)

### 2. Data Fetching

The pipeline automatically fetches real UV-Vis spectral data from the HuggingFace dataset `zjunlp/UV-Vis-ML` during the ingestion step. No manual download is required.

To verify the data directory structure:

```bash
python code/create_dirs.py
```

This ensures `data/raw/`, `data/processed/`, `code/`, `tests/`, and `docs/` exist.

### 3. Running the Pipeline End-to-End

Execute the full pipeline in sequence:

```bash
# Step 1: Ingest and validate data
python code/ingest.py

# Step 2: Split data by scaffold
python code/split.py

# Step 3: Train GNN and Baseline models
python code/train.py

# Step 4: Evaluate and compute metrics
python code/evaluate.py

# Step 5: Generate feature attribution and sensitivity analysis
python code/explain.py
python code/sensitivity.py
```

### 4. Outputs

After successful execution, check the following artifacts:

- `data/raw/processed.csv`: Cleaned molecular data with SMILES, $\lambda_{max}$, and scaffold IDs.
- `data/processed/metrics.json`: Performance metrics (MAE, R², Wilcoxon p-value, SC-001 status).
- `data/processed/redundancy_masks.json`: Collinearity flags and redundancy masks.
- `data/processed/attribution_results.json`: Feature attribution results.
- `model.pt`: Trained GNN model weights.

### 5. Testing

Run the test suite to verify implementation:

```bash
pytest tests/ -v
```

## Project Structure

```
.
├── code/ # Implementation scripts
│ ├── ingest.py # Data ingestion from HuggingFace
│ ├── split.py # Scaffold-based splitting
│ ├── model.py # GNN and Baseline definitions
│ ├── train.py # Training loop
│ ├── evaluate.py # Evaluation and statistical tests
│ ├── explain.py # Feature attribution
│ ├── sensitivity.py # Sensitivity analysis
│ ├── utils.py # RDKit helpers and logging
│ └──...
├── data/
│ ├── raw/ # Raw and processed datasets
│ └── processed/ # Intermediate and final artifacts
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── requirements.txt # Dependencies
└── README.md # This file
```

## Notes

- All computations are CPU-only to ensure compatibility with constrained environments.
- The pipeline enforces a minimum test set size of 50 molecules for statistical power. [UNRESOLVED-CLAIM: c_838e26cd — status=not_enough_info]
- Scaffold splitting ensures no data leakage between train, validation, and test sets.