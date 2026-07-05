# Quickstart: Predicting Molecular Reactivity Using Graph Neural Networks

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace (for dataset download)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-536-predicting-molecular-reactivity-using-gr
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: This installs CPU-only versions of PyTorch and PyTorch Geometric.*

## Data Setup

1. **Download Dataset**:
   The script `code/data/download.py` will fetch the USPTO dataset from the verified HuggingFace source.
   ```bash
   python code/data/download.py --dataset uspto
   ```
   *Output*: `data/raw/uspto_*.parquet`

2. **Process Data**:
   Convert SMILES to molecular graphs.
   ```bash
   python code/data/preprocess.py --input data/raw/uspto_*.parquet --output data/processed/graphs.pt
   ```
   *Output*: `data/processed/graphs.pt` (PyTorch Geometric DataList)

## Running the Pipeline

Execute the full pipeline (Training, Evaluation, Analysis) in one command:

```bash
python code/cli/run_pipeline.py
```

**What this does**:
1. Loads processed graphs.
2. Trains Random Forest Baseline (5-fold CV).
3. Trains MPNN GNN (5-fold CV, Early Stopping).
4. Evaluates on held-out test set.
5. Runs Sensitivity Analysis and GNNExplainer Attribution.
6. Generates `results/metrics.json`, `results/predictions.json`, and `results/sensitivity.csv`.

## Expected Output

- **Console**: Progress bars, training loss logs, final metrics summary.
- **Files**:
  - `results/metrics.json`: R², MAE, RMSE for both models.
  - `results/predictions.json`: Individual predictions with confidence intervals.
  - `results/sensitivity.csv`: MAE vs. Noise Tolerance.
  - `results/attribution.json`: Top 5 subgraphs.

## Troubleshooting

- **OOM (Out of Memory)**: Reduce `batch_size` in `code/config.py` or sample a smaller dataset in `preprocess.py`.
- **SMILES Parsing Errors**: Check `logs/parsing_errors.log` for specific SMILES strings that failed.
- **Slow Training**: Ensure `num_workers=0` in DataLoader. Reduce epochs if necessary (Early Stopping should help).
