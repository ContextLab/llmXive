# Quickstart: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

## Prerequisites

* Python 3.11+ (installed on the runner)  
* `git` (to clone the repository)  
* Internet access (to download the NetFlow dataset)

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

The pipeline attempts to use the **CTU‑13** NetFlow dataset first (a verified mirror at a fixed revision). If that download fails—for example due to network restrictions—the pipeline **deterministically falls back** to the verified `keys-i/netFlow` dataset (revision `c9f7a1b2e5d4`). The fallback logic is built into `code/data/ingest.py`.

```python
from datasets import load_dataset

def load_netflow():
    try:
        # Attempt CTU‑13 mirror (pinned revision)
        ds = load_dataset('ctu13/ctu13', revision='v1.0.0', split='train', streaming=True)
        print("Using CTU‑13 dataset.")
    except Exception as e:
        print(f"CTU‑13 unavailable ({e}); falling back to keys‑i/netFlow.")
        ds = load_dataset('keys-i/netFlow', revision='c9f7a1b2e5d4', split='train', streaming=True)
    # Preview first record
    print('Dataset streaming initialized – first record preview:')
    print(next(iter(ds)))
    return ds

load_netflow()
```

> **Note**: No conditional fallback to other datasets is performed beyond the CTU‑13 → keys‑i/netFlow logic; the source is deterministic given the network outcome.

## Running the Full Analysis (once data is available)

```bash
# Execute the end‑to‑end pipeline with 20 seeds
python code/main.py \
  --seeds 42 123 456 789 101112 131415 161718 192021 222324 252627 \
          272829 303132 333435 363738 394041 424344 454647 484950 515253 545556 \
  --train_ratio 0.7 \
  --max_nodes 5000
```

The command performs:

1. **Streaming ingestion** → deterministic graph construction with memory guard, deterministic subsampling, and validation against `contracts/dataset.schema.yaml`.  
2. **Feature extraction** → Parquet feature tables.  
3. **Temporal hold‑out split** → training on earliest timestamps, testing on later timestamps.  
4. **Training** of GCN, Random Forest, and XGBoost (CPU‑only) across the 20 seeds.  
5. **Evaluation** (Precision, Recall, F1, AUC‑ROC).  
6. **Paired t‑tests** + Benjamini‑Hochberg correction (20 seeds).  
7. **Integrated‑Gradients attribution** → ranked predictive patterns.  
8. **Pattern‑based classifier** evaluation (target AUC ≥ 0.80).  

### Expected Outputs

| Directory | Contents |
|-----------|----------|
| `data/processed/` | `graph_{scenario}_subsampled.graphml.gz`, `features_{scenario}.parquet` |
| `data/results/` | `metrics_{model}_{scenario}.csv`, `final_aggregate.csv`, `gcn_attribution_{scenario}.csv`, `pattern_classifier_{scenario}.csv` |
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

* **Out‑of‑Memory** – Check `logs/memory_*.log`; if peak > 7 GB, the script aborts and logs a warning that subsampling was applied.  
* **Dataset Access Issues** – The script logs any download failures; because the fallback dataset is verified, the pipeline will continue with `keys-i/netFlow`.  
* **CUDA Errors** – The code forces `torch.device('cpu')`. If you see CUDA warnings, reinstall the CPU‑only wheel (`pip uninstall torch && pip install torch==2.3.0+cpu`).  

---


