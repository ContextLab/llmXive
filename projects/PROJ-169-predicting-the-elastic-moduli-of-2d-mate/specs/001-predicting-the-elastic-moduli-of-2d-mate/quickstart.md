# Quickstart: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Prerequisites
- Python 3.11+ (≥ 7 GB RAM, ≥ 14 GB disk, internet access).  
- GitHub Actions free‑tier runner or equivalent local environment.

## 2. Installation
```bash
# Clone the repository (assumed already done)
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

## 3. Run the Full Pipeline
```bash
python src/main_pipeline.py
```
The orchestrator executes the stages in order, halting on any non‑zero exit code.

| # | Script | Output | Hard Gate |
|---|--------|--------|-----------|
| 0 | `src/utils/verify_constitution_title.py` | `data/results/constitution_title_audit.json` | Exit 1 on any forbidden term. |
| 1 | `src/data/loader.py` | `data/raw/raw_dataset.parquet`, `data/raw/metadata.json` | Abort if < 1 000 valid 2D entries or missing columns (scope‑revision). |
| 2 | `src/data/graph_builder.py` | `data/processed/graphs_v1.parquet` | — |
| 3 | `src/data/split_generator.py` | `data/processed/split_indices.json` (atomic write) | — |
| 4 | `src/model/splitter.py` | `data/results/split_validation.json` | Exit 1 if any family appears in multiple splits. |
| 5 | `src/model/train.py` (+ `cross_validation.py`) | `data/processed/model_v1.pt`, `data/results/training_logs.json` | Exit 1 if peak memory > 16 GB. |
| 6 | `src/model/eval_runner.py` | `data/results/predictions.json`, `data/results/generalization_metrics.json` | Exit 1 if any SC gate fails (accuracy, reduction, etc.). |
| 7 | `src/model/inference_benchmark.py` | Updates `generalization_metrics.json` with timing | Exit 1 if median inference > 200 ms. |
| 8 | `src/analysis/feature_importance.py` | `data/results/feature_importance_report.md` | Exit 1 if < 3 qualifying descriptors. |
| 9 | `src/utils/compute_hashes.py` | Updates project state hashes | — |

## 4. Verification
```bash
# Verify constitution audit
python src/utils/verify_constitution_title.py   # should exit 0

# Run contract tests
pytest tests/contract/ tests/integration/ -q
```

## 5. Troubleshooting
- **MemoryError**: Reduce `batch_size` in `src/model/train.py` (default 16).  
- **Loader aborts**: Indicates none of the verified sources contain the required columns; edit `src/data/loader.py` to point to a new open dataset and/or adjust the research question.  
- **Title audit fails**: Rename offending titles to remove “First‑Principles” (see Section 4b of the spec).  
- **Slow inference**: Ensure `torch.set_num_threads(2)` and that no code forces GPU usage.  

---

