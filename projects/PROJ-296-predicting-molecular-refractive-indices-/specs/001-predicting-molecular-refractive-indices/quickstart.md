# Quickstart: Predicting Molecular Refractive Indices

## Prerequisites

- Python 3.11+  
- `pip` or `conda`  
- Access to a Linux environment (GitHub Actions or local Linux VM).  
- A few gigabytes of RAM (on the order of several GB for the pipeline).

## Installation

1. **Clone Repository**  
   ```bash
   git clone <repo-url>
   cd projects/PROJ-296-predicting-molecular-refractive-indices-/code
   ```

2. **Install Dependencies**  
   ```bash
   pip install -r requirements.txt
   # Ensure CPU‑only PyTorch Geometric is installed
   pip install torch-geometric torch-scatter torch-sparse torch-cluster torch-spline-conv -f https://data.pyg.org/whl/torch-2.0.0+cpu.html
   ```

3. **Verify RDKit**  
   ```bash
   python -c "import rdkit; print(rdkit.__version__)"
   ```

## Data Download

Run the download script to fetch the verified dataset:  
```bash
python data/download.py
```
This will:
1. Fetch the **`chemistry/ri_dataset`** from Hugging Face.  
2. Verify that the columns `smiles` and `refractive_index` are present; aborts with a clear error if missing (addresses data‑resource concern).  
3. Compute and store a SHA‑256 checksum under `state/` for reproducibility.  
4. Save the raw parquet file to `data/raw/`.

## Preprocessing

Process the data and create splits:  
```bash
python data/preprocess.py --filter-mw 500 --split-ratio 0.8,0.1,0.1
```
This will:
1. Parse SMILES with RDKit (invalid entries logged to `failed_parsing.log`).  
2. Exclude molecules with MW > 500 Da.  
3. Add **normalized molecular weight** as a global feature.  
4. Perform a scaffold‑based split with **zero scaffold overlap** and the 80/10/10 ratio.  
5. Save `train.csv`, `val.csv`, `test.csv` to `data/processed/`.

## Training

Train the MPNN model (CPU‑only):  
```bash
python training/train.py --epochs 200 --batch-size 32 --seed 42
```
- **Output**: `models/mpnn.pt`, `logs/training.log`.  
- **Runtime**: ~1‑3 h on the GitHub Actions free tier.

## Evaluation & Interpretation

Run evaluation and attribution:  
```bash
python training/evaluate.py --model models/mpnn.pt
python models/attribution.py --model models/mpnn.pt --output results/attributions.csv
```
- **Outputs**: `results/metrics.csv`, `results/plots/parity.png`, `results/plots/importance.png`.

## Verification

Check that the pipeline completed successfully and met success criteria:  
```python
import pandas as pd
metrics = pd.read_csv('results/metrics.csv')
assert metrics['mae_gnn'].iloc[0] < 1.0, "MAE too high"
assert metrics['p_value'].iloc[0] < 0.05, "Not statistically significant"
print("All checks passed.")
```
