# Quickstart: Exploring the Impact of Network Structure on Synchronization in Complex Physical Systems

## Prerequisites
*   Python 3.11+
*   `pip` or `conda`
*   Access to a UNIX-like environment (Linux/macOS/WSL)

## Installation

1.  **Clone and Setup**:
    ```bash
    cd projects/PROJ-212-exploring-the-impact-of-network-structur/code/
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `networkx`, `scipy`, `scikit-learn`, and `datasets` are installed.
    ```bash
    python -c "import networkx; import scipy; print('Dependencies OK')"
    ```

## Running the Pipeline

### Step 1: Data Loading
The pipeline will attempt to load the verified datasets. If they are not graph data, it will fallback to synthetic generation.
```bash
python main.py --mode load
```
*Output*: `data/processed/networks.json` (List of graph objects with metrics).

### Step 2: Simulation
Run Kuramoto simulations on the loaded networks.
```bash
python main.py --mode simulate
```
*Output*: `data/processed/simulation_results.json` (Thresholds for each network).

### Step 3: Analysis
Perform regression and cross-validation.
```bash
python main.py --mode analyze
```
*Output*: `results/regression_summary.json`, `results/heatmap.png`.

### Step 4: Validation (Optional)
Run the analytical check on a Ring Graph.
```bash
python main.py --mode validate
```

## Configuration
Edit `config.yaml` to adjust:
*   `random_seed`: For reproducibility.
*   `threshold_r`: The order parameter threshold (default 0.8).
*   `k_sweep`: Range and step size for coupling strength.

## Troubleshooting
*   **"Dataset Mismatch"**: The verified parquet files do not contain edge lists. The pipeline will automatically switch to synthetic graph generation. Check `logs/` for details.
*   **"Memory Error"**: Unlikely for N=200, but if using a massive graph, reduce `node_count` in `config.yaml`.
*   **"VIF > 5"**: The model will automatically flag collinear features and re-run with Ridge Regression. Check `results/regression_summary.json` for the `vif_scores` field.
