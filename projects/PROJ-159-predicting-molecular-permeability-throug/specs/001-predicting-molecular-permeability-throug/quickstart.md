# Quickstart: Predicting Molecular Permeability Through Porous Materials Using Graph Neural Networks

## Prerequisites
- Python 3.10 or higher
- Git
- Internet access (to download the open datasets)
- ≤ 7 GB RAM, ≤ 4 h runtime on a Linux CI runner

## Installation

```bash
# 1. Clone the repository
git clone <REPO_URL>
cd projects/PROJ-159-predicting-molecular-permeability-throug

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

> **Important**: The pipeline **requires** a peer‑reviewed, publicly available experimental permeability dataset (FR‑016). No such dataset is currently listed among the verified sources. Until one is provided, the pipeline will abort with a clear error message; it will **not** fabricate targets.

### Step 1 – Download & Preprocess (includes target loading)
```bash
python code/main.py --step download_preprocess
```
- Downloads the verified MOF and IZA datasets.  
- Constructs heterogeneous graphs.  
- **Loads experimental permeability values** (log₁₀) from the required dataset.  

### Step 2 – Train & Evaluate (5‑fold CV)
```bash
python code/main.py --step train_evaluate
```
- Trains the heterogeneous GNN and three baselines under the same CV splits.  
- Generates `data/results/metrics.json` with RMSE, MAE, R², Pearson r per fold and overall statistics.  

### Step 3 – Ablation, Sensitivity, and Feature‑Importance
```bash
python code/main.py --step ablation_sensitivity
```
- Runs the model without cross‑edges (ΔRMSE).  
- Sweeps cross‑contact thresholds `{0.30, 0.50, 0.70}` nm and records variance in RMSE.  
- Computes SHAP values and writes `feature_importance.json` with the top‑5 molecular and top‑5 framework features.  

## Verification

```bash
pytest tests/
```
- Unit tests check graph construction, metric calculations, and schema compliance.  
- Integration test runs a miniature end‑to‑end pipeline on a small representative subset of pairs (requires the experimental permeability dataset) to guarantee reproducibility.

## Troubleshooting

| Symptom | Likely Cause | Remedy |
|---|---|---|
| **OOM / MemoryError** | Too many pairs loaded | Reduce `MAX_PAIRS` in `config.py` (default 500) or lower `batch_size` to 4. |
| **Runtime > 4 h** | Early stopping not triggered | Lower `max_epochs` in `config.py` or increase `patience`. |
| **Missing permeability values** | No experimental dataset supplied | Provide a verified experimental permeability dataset; the pipeline will abort with a clear error otherwise. |
| **No CUDA device found** | Accidentally added a `device="cuda"` flag | Ensure all model code uses `device = torch.device("cpu")`. |

All results are reproducible by re‑running the three steps with the same seed (`seed=42` in `config.py`).  

---


