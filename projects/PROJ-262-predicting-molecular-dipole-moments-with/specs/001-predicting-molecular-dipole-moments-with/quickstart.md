# Quickstart: Predicting Molecular Dipole Moments with Graph Neural Networks

## Prerequisites
*   Python 3.11+
*   Git
*   Sufficient free disk space (for data and cache)
*   GB RAM (minimum)

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-262-predicting-molecular-dipole-moments-with
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Execution Workflow

### Step 1: Data Download & Preprocessing
Download the QM9 dataset from the verified Hugging Face source and preprocess it.
```bash
python code/data/download_qm9.py
python code/data/preprocess.py
```
*Output*: `data/processed/train.parquet`, `data/reports/excluded_molecules.csv`.

### Step 2: Model Training
Train the GNN and Random Forest models across multiple seeds.
```bash
# Train GNN
python code/train/train_gnn.py --seeds 42,123,456,789,1011

# Train RF Baseline
python code/train/train_rf.py --seeds 42,123,456,789,1011
```
*Output*: `models/schnet_seed_*.pt`, `models/rf_seed_*.pkl`.

### Step 3: Evaluation & Attribution
Compute metrics and generate feature attribution.
```bash
python code/eval/metrics.py
python code/eval/attribution.py
python code/eval/stats.py  # Paired t-tests
```
*Output*: `results/metrics.json`, `results/attribution.json`.

### Step 4: Visualization
Generate plots of feature importance.
```bash
python code/viz/plot_feature_importance.py
```
*Output*: `figures/feature_importance.png`.

## Verification

Run the test suite to ensure data integrity and model outputs:
```bash
pytest tests/
```

## Troubleshooting

*   **OOM Error**: If you encounter memory errors, reduce the `--subset_size` in `preprocess.py` (default: a sufficiently large sample size to ensure statistical power and representativeness).
*   **CUDA Error**: If running on a GPU, ensure `CUDA_VISIBLE_DEVICES` is set. The default is CPU.
*   **Missing Data**: Check `data/reports/excluded_molecules.csv` for molecules with missing coordinates.
