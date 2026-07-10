# Quickstart: Predicting Molecular Excitation Wavelengths

## Prerequisites

- Python 3.10+
- 7GB+ RAM available (for dataset loading and model training)
- Internet access (to download datasets from HuggingFace)

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure `torch` is installed for CPU only. If using pip, add `--index-url https://download.pytorch.org/whl/cpu`.*

## Data Ingestion

Run the ingestion script to download and clean the dataset. This will fetch the UV-Vis ML dataset from HuggingFace, validate SMILES, and generate the scaffold-split files.

```bash
python code/ingest.py
python code/split.py
```

**Output**:
- `data/processed/cleaned.csv`
- `data/processed/train.csv`, `val.csv`, `test.csv`

## Model Training

Train the GNN model on the training set. The script automatically handles early stopping and saves the best model.

```bash
python code/train.py
```

**Output**:
- `artifacts/model.pt` (Best checkpoint)
- `artifacts/training_log.json`

## Evaluation

Evaluate the trained model against the test set and the baseline.

```bash
python code/evaluate.py
```

**Output**:
- `artifacts/results.csv` (Per-molecule predictions and errors)
- `artifacts/metrics_summary.json` (MAE, R², Baseline comparison)

## Feature Attribution & Sensitivity

Analyze feature importance and perform sensitivity analysis on error thresholds.

```bash
python code/explain.py
python code/sensitivity.py
```

**Output**:
- `artifacts/attribution.json` (Atom-level weights)
- `artifacts/sensitivity_report.csv` (Error rates at different thresholds)

## Verification

To ensure reproducibility, run the full pipeline with a fixed seed:

```bash
python code/train.py --seed 42
python code/evaluate.py --seed 42
```
