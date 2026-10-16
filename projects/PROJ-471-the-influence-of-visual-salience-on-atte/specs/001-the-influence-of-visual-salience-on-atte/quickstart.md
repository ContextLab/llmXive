# Quickstart: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## Prerequisites
- **Python** 3.11+ (Ubuntu 22.04 recommended)
- **Git**  
- **GitHub Actions runner** (CPU‑only, ≤7 GB RAM) – the CI environment used for reproducibility.
- **Data**: The OpenNeuro *Moral Foundations Eye‑Tracking* dataset (ds003123) must be placed manually in `data/raw/ds003123/`. No automated download is attempted because the dataset is not in the verified list.

## Installation
```bash
git clone <repo-url>
cd projects/PROJ-471-the-influence-of-visual-salience-on-atte
pip install -r code/requirements.txt
```

## Verify Data Presence
```bash
python code/ingestion/verify_data.py
# Expected output: "Dataset found. Proceeding..."
# If missing: "ERROR: DATA_MISSING_001 – place ds003123 in data/raw/"
```

## Run the Full Pipeline
```bash
python code/main.py
```
The orchestrator executes the steps defined in `plan.md` in order:
1. Verify dataset presence.  
2. Generate salience maps (GBVS on CPU; DeepGaze II GPU fallback).  
3. Create ROI masks (YOLOv8 + Detectron2).  
4. Parse eye‑tracking metrics (including fixation latency).  
5. Align data.  
6. Compute low‑level visual features (luminance, contrast, edge density).  
7. Fit the mixed‑effects model with covariates, apply FDR correction, run sensitivity analysis, and **always** add the `"disclaimer": "correlational only"` field to the JSON results.  
8. Validate outputs against contracts.

## Expected Outputs
- `data/processed/aligned_data.csv` – merged predictor & outcome table (includes `fixation_latency_ms` and `edge_density`).  
- `data/processed/results.json` – statistical summary adhering to `output.schema.yaml`.  
- `logs/pipeline.log` – detailed runtime log, including resource usage (SC‑002) and any excluded trials (SC‑005).

## Troubleshooting
| Symptom | Likely Cause | Fix |
|---|---|---|
| `DATA_MISSING_001` | Dataset not in `data/raw/` | Download ds003123 from OpenNeuro and extract there. |
| `CUDA error` | Accidental GPU usage on CPU runner | Ensure `code/config.py` sets `device = "cpu"`; re‑run. |
| MemoryError during salience generation | Batch size too large | Reduce `BATCH_SIZE` in `code/config.py` (e.g., from 8 to 4). |
| `POWER_INSUFFICIENT` | Simulated power < 0.8 | Collect more participants or accept that inference is not valid. |
| Missing columns in `aligned_data.csv` | Alignment step omitted latency or edge density | Verify `code/analysis/align_data.py` produces those columns; run `code/utils/independence_validator.py` for diagnostics. |

---

