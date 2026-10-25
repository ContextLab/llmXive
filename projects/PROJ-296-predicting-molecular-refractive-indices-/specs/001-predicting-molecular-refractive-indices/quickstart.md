# Quickstart: Predicting Molecular Refractive Indices

## Prerequisites
- Python 3.11+  
- `pip` (or `conda`)  
- Linux environment (GitHub Actions runner or local Linux VM)  
- At least 2 GB RAM (full pipeline uses < 1 GB)  

## Installation

```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd projects/PROJ-296-predict-molecular-refractive-indices-/code

# Install dependencies
pip install -r requirements.txt

# Install CPU‑only PyTorch Geometric wheels
pip install torch-geometric torch-scatter torch-sparse torch-cluster torch-spline-conv -f https://data.pyg.org/whl/torch-2.0.0+cpu.html
```

## Step‑by‑Step Execution

### 1️⃣ Dataset Availability Check (always runs first)
```bash
python data/download.py --check-only
```
- The script scans the verified SMILES datasets for a column `refractive_index`.  
- If a suitable dataset is found, it proceeds automatically to the download step.  
- If not, it writes `logs/dataset_unavailable.log` and exits with status 0 (pipeline stops cleanly).

### 2️⃣ Download (run only if step 1 succeeded)
```bash
python data/download.py
```
- Downloads the selected dataset, records SHA‑256 under `state/ri_dataset.sha256`, and validates against `contracts/dataset.schema.yaml`.

### 3️⃣ Preprocess & Filter
```bash
python data/preprocess.py
```
- Parses SMILES, filters MW > 500 Da, applies temperature normalization, writes `data/processed/filtered.csv`.  
- Generates deterministic summary log `logs/preprocess_summary.log`.

### 4️⃣ Scaffold‑Based Splits
```bash
python data/split.py --folds 5 --repeats 5 --ratios 0.8 0.1 0.1
```
- Creates a set of train/val/test CSVs under `data/splits/`.  
- Logs actions to `logs/split.log`.

### 5️⃣ Train the MPNN (CPU‑only)
```bash
for i in {1..5}; do
  for j in {1..5}; do
    python training/train.py --fold $i --repeat $j --epochs 200 --batch-size 32 --seed $((2000 + i*10 + j))
  done
done
```
- Saves model weights `models/mpnn_${i}_${j}.pt` and training logs.

### 6️⃣ Baseline Predictions
```bash
for i in {1..5}; do
  for j in {1..5}; do
    python models/baseline.py --fold $i --repeat $j
  done
done
```
- Generates `results/baseline_predictions_${i}_${j}.csv`.

### 7️⃣ Evaluation & Attribution
```bash
for i in {1..5}; do
  for j in {1..5}; do
    python training/evaluate.py --fold $i --repeat $j --model models/mpnn_${i}_${j}.pt
    python models/attribution.py --fold $i --repeat $j --model models/mpnn_${i}_${j}.pt --output results/attributions_${i}_${j}.csv
  done
done
```
- Produces `results/metrics_summary.csv`, parity plots, importance bar charts, and attribution CSVs.

### 8️⃣ Verify Success Criteria
```python
import pandas as pd
metrics = pd.read_csv('results/metrics_summary.csv')
print(metrics[['fold','repeat','mae_gnn','mae_baseline','p_value']])

# Check variance of MAE across repeats
print("MAE variance:", metrics['mae_gnn'].var())
```
- Expected outputs:
  - **SC‑001**: Paired test p‑value (or Wilcoxon) reported; significance noted only if p < 0.05.
  - **SC‑002**: MAE variance across repeats ≤ 0.01 (or reported value with disclaimer).
  - **SC‑003**: Top‑5 graph features listed in `results/attributions_*` files.
  - **SC‑004**: Total runtime logged in `logs/runtime.log` (must be ≤ 6 h).  
  - **SC‑005**: Peak memory logged in `logs/memory_usage.log` (must be ≤ 7 GB).

## Notes on Scope
- **Dataset Limitation**: If the availability check fails (no open RI dataset), the pipeline stops early with a clear log. In that case, the project requires a specification revision to either (a) provide a suitable open dataset or (b) change the target property. No synthetic data are generated, preserving scientific integrity.  
- All steps are deterministic and fully reproducible on a fresh GitHub Actions runner.  
- The quickstart commands assume a Unix‑like shell; Windows users can run the same Python scripts via PowerShell or WSL.

---
