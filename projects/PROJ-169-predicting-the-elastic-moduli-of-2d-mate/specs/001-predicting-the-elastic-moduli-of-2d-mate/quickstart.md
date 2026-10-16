# Quickstart: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Prerequisites
- Python 3.11+, ≥ 7 GB RAM, ≥ 14 GB disk, internet access
- GitHub Actions free‑tier runner or equivalent

## 2. Installation
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r code/requirements.txt
```

## 3. Run the Full Pipeline
```bash
python code/main_pipeline.py
```

Stages (each must exit 0 to continue):

| # | Script | Output | Hard gate |
|---|--------|--------|-----------|
| 0 | `code/utils/verify_constitution_title.py` | `data/results/constitution_title_audit.json` | Exit 1 on any failed title check |
| 1 | `code/data/loader.py` | `data/raw/*.parquet` | Abort on checksum/column failure or dataset‑variable mismatch (scope‑revision) |
| 2 | `code/data/graph_builder.py` | `data/processed/graphs_v1.parquet` | — |
| 3 | `code/data/split_generator.py` | `data/processed/split_indices.json` | Atomic write verified |
| 4 | `code/model/splitter.py` | `data/results/split_validation.json` | Exit 1 on family leakage |
| 5 | `code/model/train.py` (+ `cross_validation.py`) | `data/processed/model_v1.pt`, `data/results/training_logs.json` | Exit 1 if peak memory > 7 GB |
| 6 | `code/model/eval_runner.py` | `data/results/predictions.json`, `data/results/generalization_metrics.json` | Exit 1 if any SC gate fails |
| 7 | `code/model/inference_benchmark.py` | timings merged into `generalization_metrics.json` | Exit 1 if median ≥ 100 ms |
| 8 | `code/analysis/feature_importance.py` | `data/results/feature_importance_report.md` | Exit 1 if < 3 qualifying descriptors |
| 9 | `code/utils/compute_hashes.py` | Updated project state hashes | — |

## 4. Verification
```bash
python code/utils/verify_constitution_title.py   # exits 0
pytest tests/contract/ tests/integration/ -q
```

## 5. Troubleshooting
- **MemoryError**: reduce `batch_size` in `code/model/train.py` (default 16).  
- **Loader aborts**: indicates none of the verified parquet files contain the required columns; the pipeline aborts with a clear mismatch report – a scope revision is needed.  
- **Title audit fails**: rename offending titles per Section 4b of the spec.  
- **Slow inference**: ensure `torch.set_num_threads(2)` and that no code overrides the CPU device.  