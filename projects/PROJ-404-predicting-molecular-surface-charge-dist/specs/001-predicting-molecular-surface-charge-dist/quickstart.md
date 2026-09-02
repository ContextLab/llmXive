# Quickstart: Predicting Molecular Surface Charge Distribution

## Prerequisites

- Python 3.11+
- Git
- 7 GB+ RAM (or access to a Kaggle GPU for the escape hatch)
- Internet connection (to download QM9 dataset)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-404-predicting-molecular-surface-charge-dist
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: Ensure `torch` and `torch-geometric` are installed for CPU. If using CUDA, install the CUDA-enabled versions.*

## Data Setup

The data pipeline will automatically download the QM9 dataset from the verified Hugging Face URL.

1. **Run the data loader**:
   ```bash
   python code/data/loader.py --sample-size 50000 --seed 42
   ```
   This will:
   - Download the QM9 parquet file using **streaming mode** to ensure < 7 GB RAM usage.
   - Verify the presence of `charges_merkollman` columns. **Halts** if missing.
   - Filter molecules with missing charges.
   - Compute Bemis-Murcko scaffolds.
   - Save train/val/test splits to `data/processed/` and `artifacts/splits/`.

2. **Verify data integrity**:
   ```bash
   python code/data/loader.py --validate
   ```
   Check that the output confirms the expected number of molecules, the presence of required columns, and that no OOM errors occurred.

## Training

Run the training script. This will train the 3D GNN (SchNet) and the 2D baseline.

```bash
python code/train.py --epochs 100 --early-stopping-patience 10 --batch-size 32
```

- **Output**: Model weights saved to `artifacts/models/`. Early stopping state (best epoch, best MAE) is also saved.
- **Logs**: Training progress saved to `artifacts/logs/`.

## Evaluation

Evaluate the trained models on the test set.

```bash
python code/eval.py --model-path artifacts/models/schnet.pt --baseline
```

- **Output**: A JSON report in `artifacts/reports/evaluation_results.json` containing `hypothesis_validated`, `generalization_gap`, and other metrics.
- **Exit Code**: The script will exit with `EXIT_CODE_BASELINE_LOSS` if the 3D GNN MAE > 2D GNN MAE or if MAE > 0.05 e.

## Testing

Run the unit and integration tests.

```bash
pytest tests/ -v
```

- **Unit Tests**: Verify SchNet architecture initialization and data loader schema validation.
- **Integration Tests**: Verify training loop completion, early stopping, and full evaluation pipeline.

## Troubleshooting

- **OOM Error**: Reduce `--sample-size` in the data loader or `--batch-size` in training.
- **CUDA Not Found**: The script defaults to CPU. If you have a GPU, set `CUDA_VISIBLE_DEVICES=0` and ensure PyTorch CUDA is installed.
- **Missing Columns**: If the QM9 download fails to load charges, verify the column names in the parquet file or check the `research.md` for fallback datasets. The pipeline will halt with a clear error message if `charges_merkollman` is missing.