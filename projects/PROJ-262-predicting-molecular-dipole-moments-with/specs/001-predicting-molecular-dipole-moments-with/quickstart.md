# Quickstart: Predicting Molecular Dipole Moments with Graph Neural Networks

## Prerequisites

- Python 3.11+
- 8GB RAM available
- 14GB disk space
- Internet access (for dataset download)

## Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-262-predicting-molecular-dipole-moments-with
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Download and Preprocess Data

```bash
python code/main.py --step download
python code/main.py --step preprocess
```

- This downloads the QM9 dataset from Hugging Face, filters missing 3D coordinates, and generates feature matrices.
- Excluded molecules are reported in `data/reports/excluded_molecules.csv`.
- **Note**: The `code/data/preprocess.py` script handles all data cleaning and exclusion logic. The deprecated `handle_missing_coords.py` has been removed.

### Step 2: Train Models

```bash
python code/main.py --step train
```

- Train SchNet GNN, Random Forest baseline, and Combined Random Forest across multiple random seeds.
- Uses 50 epochs with early stopping (patience=10).
- Results saved to `data/processed/predictions.parquet`.

### Step 3: Evaluate and Analyze

```bash
python code/main.py --step evaluate
python code/main.py --step attribute
```

- Computes MAE, RMSE, and 95% CIs.
- Performs paired t-tests (RF 2D vs Combined, SchNet vs Randomized) and generates feature attribution plots.
- Reports saved to `data/reports/`.

### Step 4: Visualize Results

```bash
python code/main.py --step visualize
```

- Generates plots comparing GNN vs. RF performance and feature importance maps (RDKit heatmaps).
- Output saved to `docs/figures/`.

## Expected Output

- `data/processed/feature_matrix.parquet`: Processed feature data.
- `data/reports/excluded_molecules.csv`: Report of excluded molecules.
- `data/reports/metrics.json`: MAE, RMSE, and confidence intervals.
- `data/reports/attribution.parquet`: Feature importance scores.
- `docs/figures/`: Comparison plots and attribution visualizations.

## Troubleshooting

- **OOM Errors**: If memory exceeds 8GB, reduce the dataset subset size in `code/data/preprocess.py`.
- **Download Failures**: Verify internet connection; retry with `--step download`.
- **Missing 3D Coords**: Check `data/reports/excluded_molecules.csv` for details.

## Constraints

- Execution time ≤ 6h on 2 CPU cores.
- Memory footprint ≤ 8GB.
- CPU-only mode for GNN training.