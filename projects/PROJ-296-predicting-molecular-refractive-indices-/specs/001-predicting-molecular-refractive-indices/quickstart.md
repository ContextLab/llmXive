# Quickstart: Predicting Molecular Refractive Indices

## Prerequisites
- Python 3.11+  
- `pip` (or `conda`)  
- Linux environment (GitHub Actions runner or local Linux VM)  
- At least 2 GB RAM (the full pipeline uses < 1 GB)  

## Installation

1. **Clone the repository**  
   ```bash
   git clone <repo-url>
   cd projects/PROJ-296-predict-molecular-refractive-indices-/code
   ```

2. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   # Install CPU‑only PyTorch Geometric wheels
   pip install torch-geometric torch-scatter torch-sparse torch-cluster torch-spline-conv -f https://data.pyg.org/whl/torch-2.0.0+cpu.html
   ```

3. **Verify RDKit**  
   ```bash
   python -c "import rdkit; print(rdkit.__version__)"
   ```

## Data Preparation

The pipeline expects an **open‑source CSV** with ≥ 500 organic molecules and experimental refractive indices.  
If such a dataset is available, run:

```bash
python data/download.py
```

The script will:
1. Download the dataset from a verified public URL (Zenodo, Figshare, or HuggingFace).  
2. Compute a SHA‑256 checksum and store it under `state/ri_dataset.sha256`.  
3. Validate the CSV against `contracts/dataset.schema.yaml`.  

*If no suitable dataset is found, the script aborts with a clear error and the project must be re‑specified to accommodate the data limitation.*

## Preprocessing & Splitting

```bash
python data/preprocess.py --filter-mw 500
python data/split.py --folds 5 --repeats 5 --ratios 0.8 0.1 0.1
```
- Parses SMILES, filters MW > 500 Da, adds normalized MW as a global feature.  
- Performs **5 × 5 scaffold‑based splits** (total 25 splits) with zero scaffold overlap.

## Training the MPNN (CPU‑only)

```bash
for i in {1..5}; do
  for j in {1..5}; do
    python training/train.py --fold $i --repeat $j --epochs 200 --batch-size 32 --seed $((2000 + i*10 + j))
  done
done
```
- Saves each fold’s weights to `models/mpnn_${i}_${j}.pt`.  
- Logs training progress to `logs/training_${i}_${j}.log`.  

## Evaluation & Attribution

```bash
for i in {1..5}; do
  for j in {1..5}; do
    python training/evaluate.py --fold $i --repeat $j --model models/mpnn_${i}_${j}.pt
    python models/attribution.py --fold $i --repeat $j --model models/mpnn_${i}_${j}.pt --output results/attributions_${i}_${j}.csv
  done
done
```
- Generates `results/metrics_summary.csv` (MAE/RMSE, paired test/Wilcoxon results, Cohen’s d, confidence intervals).  
- Produces PNG plots: `results/plots/parity_${i}_${j}.png` and `results/plots/importance_${i}_${j}.png`.

## Verification of Success Criteria

```python
import pandas as pd
metrics = pd.read_csv('results/metrics_summary.csv')
print(metrics[['fold','repeat','mae_gnn','mae_baseline','p_value']])
# Expect MAE variance across repeats to be reported; p‑value may be > 0.05 due to limited power.
```

## Notes on Scope
- The bundled CSV used in earlier drafts has been replaced by an **open dataset requirement**. If such a dataset cannot be obtained, the pipeline aborts and the specification must be revised.  
- The study remains a **feasibility pilot**; no formal claim of statistical significance is made unless the dataset meets the size requirement.  
- The pipeline can be re‑run with a larger dataset in the future without code changes.

---
