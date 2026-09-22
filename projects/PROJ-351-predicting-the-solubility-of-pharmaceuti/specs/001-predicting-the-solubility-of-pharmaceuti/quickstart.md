# Quickstart: Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

## Prerequisites

- Python 3.10 or higher
- pip
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` includes pinned versions of `rdkit`, `torch`, `torch-geometric`, `scikit-learn`, etc.*

## Data Setup

The data is automatically downloaded and processed on the first run.

1. **Run the download script** (optional, usually handled by `main_pipeline.py`):
   ```bash
   python code/data/download_esol.py
   ```
   This downloads the ESOL dataset to `data/raw/` and validates the checksum.

2. **Verify data**:
   Ensure `data/raw/delaney-processed.csv` exists and is non-empty.

## Running the Pipeline

Execute the full pipeline (download, clean, train RF, train GNN, evaluate, report):

```bash
python code/main_pipeline.py
```

### What happens?
1. **Download**: Fetches ESOL dataset.
2. **Clean**: Validates SMILES, excludes invalid entries.
3. **Preprocess**: Converts to graphs and fingerprints.
4. **Train**:
   - Random Forest with **Nested Cross-Validation** (Outer 5-Fold, Inner 5-Fold).
   - MPNN with **Nested Cross-Validation** (Outer 5-Fold, Inner 5-Fold).
5. **Evaluate**: Calculates RMSE, R², **Nadeau's Corrected t-test**, and statistical power.
6. **Report**: Generates `docs/reports/final_report.md` and visualizations.

## Output Artifacts

- `artifacts/rf_model.pkl`: Trained Random Forest model.
- `artifacts/gnn_model.pt`: Trained MPNN model.
- `artifacts/results.json`: Detailed metrics and statistical test results.
- `docs/reports/final_report.md`: Human-readable summary.
- `docs/reports/interpretability_plots/`: Feature importance visualizations.

## Troubleshooting

- **RAM Error**: If you encounter `MemoryError`, reduce the batch size in `code/models/mpnn.py` (e.g., from 32 to 16).
- **CUDA Error**: The code is designed to run on CPU. If you see CUDA errors, ensure `torch.device('cpu')` is set in the code (it should be by default).
- **SMILES Error**: If the cleaning step logs many invalid SMILES, check the raw data source. The default source is verified, but mirrors may vary.

## Reproducibility

- **Random Seeds**: All random seeds are pinned in `code/main_pipeline.py` and `code/models/trainer.py`.
- **Data Source**: The dataset is downloaded from a fixed URL.
- **Dependencies**: `requirements.txt` pins all versions.

To reproduce exactly:
1. Use the same `requirements.txt`.
2. Run `python code/main_pipeline.py` on a fresh environment.
3. Compare `artifacts/results.json` with the original run.