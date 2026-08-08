# Predicting Molecular Excitation Wavelengths from SMILES with Graph Neural Networks

This project implements a pipeline to predict the maximum excitation wavelength (λmax) of molecules from their SMILES strings using Graph Neural Networks (GNNs). It includes data ingestion, preprocessing, model training, evaluation, and feature attribution analysis.

## Prerequisites

- Python 3.9+
- pip
- 2 vCPU, 7GB RAM (CPU-only execution required)

## Quickstart

### 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Project Structure

The project uses the following directory structure:

```
projects/PROJ-379-predicting-molecular-excitation-waveleng/
├── code/ # Source code
├── data/
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Processed data and model outputs
│ └── checksums.txt # Artifact integrity hashes
├── tests/ # Test suite
├── docs/ # Documentation
├── state/ # Project state tracking
├── requirements.txt # Dependencies
└── README.md # This file
```

### 3. Data Fetching

The pipeline automatically fetches UV-Vis spectral data from the `zjunlp/UV-Vis-ML` dataset via Hugging Face. If the dataset is unavailable, it falls back to PubChem/SDBS sources as defined in `plan.md`.

To manually trigger data ingestion:

```bash
python code/ingest.py
```

This will create `data/raw/processed.csv` containing valid SMILES, λmax values, and scaffold IDs.

### 4. Running the Pipeline End-to-End

Execute the full pipeline on CPU:

```bash
# 1. Validate raw data
python code/validate_data.py

# 2. Split data by Bemis-Murcko scaffolds
python code/split.py

# 3. Train GNN and baseline models
python code/train.py

# 4. Evaluate models and compute SC-001 status
python code/evaluate.py

# 5. (Optional) Feature attribution and sensitivity analysis
python code/explain.py
python code/sensitivity.py
```

### 5. Output Artifacts

After successful execution, the following artifacts will be generated:

- `data/processed/train.csv`, `val.csv`, `test.csv`: Scaffold-split datasets
- `data/processed/model.pt`: Trained GNN model weights
- `data/processed/metrics.json`: Evaluation metrics (MAE, R², Wilcoxon p-value, SC-001 status)
- `data/processed/redundancy_masks.json`: Collinearity-based redundancy masks
- `data/processed/attribution_results.json`: Feature attribution scores
- `state/projects/PROJ-379-predicting-molecular-excitation-waveleng.yaml`: Project state and artifact hashes

### 6. Verification

Ensure all tests pass:

```bash
pytest tests/ -v
```

Verify SC-001 compliance:
- Check `data/processed/metrics.json` for `sc001_status: "PASS"`
- Confirm test set size ≥ 50 (enforced in `code/evaluate.py`)
- Validate MAE < 30 nm and p-value < 0.05 for Wilcoxon test

## Configuration

- **Random Seed**: Fixed at 42 for reproducibility (set in `code/train.py`)
- **Device**: CPU-only (enforced in `code/utils.py`)
- **Memory Limit**: <7GB RAM (chunked loading in `code/ingest.py`)

## License

This project is part of the llmXive automated science pipeline.