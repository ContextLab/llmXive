# Quickstart: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Prerequisites
- Python 3.11 or newer  
- ≥ 7 GB RAM, ≥ 14 GB free disk space  
- Internet access (to download the verified parquet files, if available)  
- GitHub Actions free‑tier runner (or equivalent local environment)

## 2. Installation
```bash
# Clone the project (if not already)
git clone https://github.com/your-org/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.git
cd PROJ-169-predicting-the-elastic-moduli-of-2d-mate

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## 3. Run the Full Pipeline
```bash
python code/main_pipeline.py
```
The orchestrator executes the following ordered stages (each stage must exit 0 to continue):

| Stage | Script | Key Output | Hard‑gate outcome |
|---|---|---|---|
| 0️⃣ Constitution title audit | `code/utils/verify_constitution_title.py` | `data/results/constitution_title_audit.json` | Exit 1 on forbidden terms |
| 1️⃣ Data ingestion | `code/data/loader.py` | `data/raw/*.parquet` | Abort if checksum fails, required columns missing, or no verified dataset is found |
| 2️⃣ Graph construction | `code/data/graph_builder.py` | `data/processed/graphs_v1.parquet` | – |
| 3️⃣ Split generation | `code/data/split_generator.py` | `data/processed/split_indices.json` | – |
| 4️⃣ Split validation | `code/model/splitter.py` | `data/results/split_validation.json` | Exit 1 if leakage detected |
| 5️⃣ Training | `code/model/train.py` | `data/processed/model_v1.pt`, `data/results/training_logs.json` | Exit 1 if `peak_memory_gb > 7` |
| 6️⃣ Evaluation & baseline | `code/model/eval_runner.py` | `data/results/predictions.json`, `data/results/generalization_metrics.json` | Exit 1 if relative MAPE reduction < 10 % **or** p‑value ≥ 0.05 |
| 7️⃣ Baseline GNN (composition‑only) | `code/model/train_composition_gnn.py` | `data/results/composition_gnn_metrics.json` | – |
| 8️⃣ Inference benchmark | `code/model/inference_benchmark.py` | `data/results/inference_benchmark.json` | Exit 1 if avg > 100 ms |
| 9️⃣ Feature importance | `code/analysis/feature_importance.py` | `data/results/feature_importance_report.md` | Exit 1 if fewer than 3 significant descriptors |
| 🔟 Power analysis | `code/utils/power_analysis.py` | `data/results/power_analysis.json` | Exit 1 if estimated power < 0.8 |
| 1️⃣1️⃣ Final audit & hash | `code/utils/compute_hashes.py` | Updated `state/projects/...yaml` | – |

If any stage fails, the pipeline stops and prints the offending exit code and error message.

## 4. Verification
```bash
# Verify constitution audit (should exit 0)
python code/utils/verify_constitution_title.py

# Run contract tests
pytest tests/contract/ -q

# Check success criteria explicitly
python code/utils/verify_success_criteria.py \
    --metrics data/results/generalization_metrics.json \
    --inference data/results/inference_benchmark.json \
    --power data/results/power_analysis.json
```

## 5. Troubleshooting
- **MemoryError**: Reduce `batch_size` in `code/model/train.py` (default 16).  
- **Title audit fails**: Amend the constitution title to remove “First‑Principles” or “Schrödinger”.  
- **Dataset schema mismatch**: The loader will automatically try the two alternates; if none contain the required columns, the pipeline aborts with a clear error.  
- **Inference too slow**: Check that `torch.set_num_threads(2)` is not overridden; ensure no accidental GPU usage.  

All results are reproducible by re‑running `python code/main_pipeline.py` on a fresh runner.
