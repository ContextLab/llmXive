# Quickstart: Predicting Molecular Surface Area from Graph Convolutional Networks

## Prerequisites

- Python 3.10+
- `pip`
- 8 GB RAM (recommended for processing)
- Access to Hugging Face (for dataset download)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-412-predicting-molecular-surface-area-from-g
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` includes `rdkit`, `torch`, `pandas`, `pyarrow`, `scikit-learn`, `deepchem`.*

## Data Setup

The pipeline automatically downloads the verified dataset from Hugging Face on the first run.

1. **Run the data ingestion script**:
   ```bash
   python code/data/ingest.py
   ```
   This will:
   - Download `zinc_processed.parquet` to `data/raw/`.
   - Validate SMILES.
   - Generate 2D graphs and 3D conformers.
   - Compute SASA labels.
   - Save processed data to `data/processed/graphs_with_features.parquet`.

2. **Verify data generation**:
   Check that `data/processed/graphs_with_features.parquet` exists and contains columns: `smiles`, `sasa_label`, `graph_features`.

## Training & Evaluation

1. **Run the full pipeline**:
   ```bash
   python code/main.py
   ```
   This executes:
   - Data splitting (stratified by MW).
   - GCN Training (CPU, max 50 epochs).
   - Baseline Training (Linear Regression).
   - Evaluation (MAE, RMSE, R², t-test).
   - Sensitivity Analysis (threshold sweep).

2. **View results**:
   - **Metrics**: `results/reports/final_metrics.json`
   - **Sensitivity**: `results/reports/sensitivity_analysis.csv`
   - **Runtime**: `results/reports/runtime_verification.md`

## Testing

Run the test suite to verify contract compliance:

```bash
pytest tests/ -v
```

Specific contract tests:
- `tests/contract/test_schema.py`: Validates output against `contracts/`.
- `tests/integration/test_pipeline.py`: End-to-end run on a small subset.

## Troubleshooting

- **Conformer Generation Failure**: If >10% of molecules fail 3D generation, the pipeline halts. Check `data/processed/failure_report.csv` for reasons.
- **OOM (Out of Memory)**: Reduce `BATCH_SIZE` in `code/config.py` or enable streaming in `code/data/ingest.py`.
- **GPU Offload**: If CPU training fails, the script will attempt to re-run on a Kaggle GPU (requires `KAGGLE_USERNAME` and `KAGGLE_KEY` environment variables).
