# Quickstart: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

## Prerequisites

* Python 3.11+ (installed on the runner)  
* `git` (to clone the repository)  
* Internet access (to download the verified NetFlow dataset)

## Setup Steps

```bash
# 1️⃣ Clone the repository
git clone <REPO_URL>
cd <repo-directory>

# 2️⃣ Create a clean virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3️⃣ Install exact dependencies (pinned)
pip install -r code/requirements.txt
```

## Data Preparation

```bash
# Stream the verified NetFlow dataset directly via HuggingFace Datasets
python - <<'PY'
from datasets import load_dataset

# Streaming load avoids full download into memory
ds = load_dataset("keys-i/netFlow", split="train", streaming=True)
# The dataset object can be iterated downstream; no separate file is persisted here.
print("NetFlow dataset stream ready.")
PY
# No separate download script is needed; the pipeline will stream the data as needed.
```

## Running the Full Analysis

```bash
# Execute the end‑to‑end pipeline:
python code/main.py \
  --seeds 42 123 456 789 101112 \
  --train_ratio 0.7 \
  --max_nodes 5000
```

The command performs:

1. Streaming ingestion → deterministic graph construction with memory guard and unbiased stratified subsampling.  
2. Feature extraction → Parquet feature tables.  
3. Training of GCN, Random Forest, and XGBoost (CPU‑only).  
4. Evaluation on the temporal hold‑out test set (unseen IPs added as isolated nodes).  
5. Wilcoxon signed‑rank tests + Benjamini‑Hochberg correction (5 seeds).  
6. Integrated‑Gradients attribution for the GCN.  

### Expected Outputs

| Directory | Contents |
|-----------|----------|
| `data/processed/` | `graph_{scenario}_subsampled.graphml.gz`, `features_{scenario}.parquet` |
| `data/results/` | `metrics_{scenario}.csv`, `final_aggregate.csv` |
| `logs/` | Memory‑usage logs (`memory_{scenario}.log`), training progress (`train_{scenario}.log`) |
| `figures/` | ROC curves, feature‑importance bar plots, attribution heatmaps |

## Verification

```bash
# Unit tests (do not require the full dataset)
pytest code/tests/test_graph_construction.py -q

# Memory‑limit test (simulates a large graph)
pytest code/tests/test_memory_limits.py -q
```

All tests must pass before committing results.

## Troubleshooting

* **Out‑of‑Memory** – Ensure the memory‑monitor logs show peak < 7 GB. If the script aborts, verify that the subsampling step triggered (check `graph_{scenario}_subsampled.graphml.gz` header).  
* **Dataset Access Issues** – The streaming load will raise a clear error if the HuggingFace URL is unreachable. No fallback to another dataset is attempted.  
* **CUDA Errors** – The code forces `torch.device('cpu')`. If you see CUDA warnings, reinstall the CPU‑only wheel (`pip uninstall torch && pip install torch==2.3.0+cpu`).  

---
