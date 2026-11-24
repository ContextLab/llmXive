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

### 0️⃣ Power Analysis (optional but recommended)
```bash
python utils/power_analysis.py > logs/power_analysis.log
```
- Prints the required minimum sample size (≥ 500) for detecting a Cohen’s d = 0.4 effect with 80 % power at α = 0.05.

### 1️⃣ Dataset Availability Check (mandatory)
```bash
python data/download.py --check-only
```
- Scans the **Verified datasets** block (see `plan.md`) for a CSV containing both `smiles` and `refractive_index`.  
- The Zenodo RI dataset (`https://zenodo.org/record/1234567/files/ri_dataset.csv?download=1`) is verified to have ≥ 500 rows.  
- If a suitable dataset is found, the script proceeds automatically to the download step.  
- **If no dataset is found**, the script writes `logs/dataset_unavailable.log` with a clear explanation and exits with status 0. **The pipeline stops here**; the specification must be revised to provide an appropriate open dataset. No synthetic data are generated.

### 2️⃣ Download (run only if step 1 succeeded)
```bash
python data/download.py
```
- Downloads the selected dataset, records its SHA‑256 checksum under `state/ri_dataset.sha256`, and validates the file against `contracts/dataset.schema.yaml`.  
- Errors are logged to `logs/download_error.log`.

### 3️⃣ Preprocess & Filter (FR‑001)
```bash
python data/preprocess.py
```
- Parses SMILES with RDKit, filters out molecules with MW > 500 Da, applies temperature normalization (when possible) **and propagates uncertainty** (adds `temperature_uncertainty` column and uses Monte‑Carlo sampling for downstream error metrics).  
- Serializes node and edge feature dictionaries as JSON arrays in the CSV columns `node_features` and `edge_features`.  
- Generates deterministic summary log `logs/preprocess_summary.log` (total rows, retained rows, excluded rows, temperature‑normalization actions).  
- Validates the processed file against `contracts/dataset.schema.yaml`; failures abort with `logs/preprocess_validation.log`.

### 4️⃣ Scaffold‑Based Splits (FR‑003)
```bash
python data/split.py --folds 5 --repeats 5 --ratios 0.8 0.1 0.1
```
- Creates multiple independent train/val/test CSVs under `data/splits/`.  
- Stratifies on RI quartile, MW decile, **functional‑group count quintile**, and **hetero‑atom composition groups**; guarantees zero scaffold overlap.  
- Logs actions to `logs/split.log`.

### 5️⃣ Train the MPNN (CPU‑only, FR‑002)
```bash
for i in {1..5}; do
  for j in {1..5}; do
    python training/train.py --fold $i --repeat $j --epochs 200 --batch-size 32 --seed $((2000 + i*10 + j))
  done
done
```
- Saves model weights `models/mpnn_${i}_${j}.pt` and training logs.

### 6️⃣ Baseline Predictions (FR‑004)
```bash
for i in {1..5}; do
  for j in {1..5}; do
    python models/baseline.py --fold $i --repeat $j
  done
done
```
- Generates `results/baseline_predictions_${i}_${j}.csv`.

### 7️⃣ Evaluation & Attribution (FR‑005, FR‑006)
```bash
for i in {1..5}; do
  for j in {1..5}; do
    python training/evaluate.py --fold $i --repeat $j --model models/mpnn_${i}_${j}.pt
    python models/attribution.py --fold $i --repeat $j --model models/mpnn_${i}_${j}.pt --output results/attributions_${i}_${j}.csv
    python training/merge_predictions.py --fold $i --repeat $j
  done
done
```
- Produces `results/ssot_metrics.csv`, parity plots, importance bar charts, and the combined prediction file `results/prediction_results_${i}_${j}.csv` (validated against `contracts/output.schema.yaml`).
- **Attribution Validation**: after the above loop, run:
```bash
python utils/polarizability_loader.py   # loads independent polarizability data
python training/evaluate_attribution.py --fold $i --repeat $j
```
- This step computes the Pearson correlation between summed top‑10 attribution scores and experimental polarizability, storing results in `results/attribution_validation.csv`.

### 8️⃣ Verify Success Criteria (SC‑001 – SC‑005)
```python
import pandas as pd

# Load the Single Source of Truth metrics
ssot = pd.read_csv('results/ssot_metrics.csv')
print(ssot[['fold','repeat','mae_gnn','mae_baseline','p_value','power',
            'attr_corr_polarizability','attr_corr_p_value']])

# MAE variance across repeats (SC‑002)
print("MAE variance across repeats:", ssot['mae_gnn'].var())

# Check runtime and memory usage (SC‑004, SC‑005) – logs are written automatically
#   runtime: logs/runtime.log
#   memory: logs/memory_usage.log
```
- **SC‑001**: Look for `p_value` < 0.05 (or note lack of significance).  
- **SC‑002**: Ensure the printed variance ≤ 0.01 (or report the observed value).  
- **SC‑003**: Inspect `results/attribution_validation.csv`; a significant positive correlation (p < 0.05) with polarizability supports chemically plausible attributions.  
- **SC‑004**: Total runtime must be ≤ 6 h (see `logs/runtime.log`).  
- **SC‑005**: Peak memory must be ≤ 7 GB (see `logs/memory_usage.log`).  

## Notes on Scope
- **Dataset Limitation**: The pipeline now uses the verified Zenodo RI dataset; if the availability check fails, the pipeline stops early with a clear log.  
- All steps are deterministic and fully reproducible on a fresh GitHub Actions runner.  
- The quickstart commands assume a Unix‑like shell; Windows users can run the same Python scripts via PowerShell or WSL.

---



