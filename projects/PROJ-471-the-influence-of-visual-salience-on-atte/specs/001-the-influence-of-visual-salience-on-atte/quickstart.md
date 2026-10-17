# Quickstart: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## Prerequisites
- **Python** 3.11+ (Ubuntu 22.04 recommended)
- **Git**  
- **GitHub Actions runner** (CPU‑only, ≤7 GB RAM) – the CI environment used for reproducibility.
- **Data**: The OpenNeuro *Moral Foundations Eye‑Tracking* dataset (ds003123) must be **manually placed** in `data/raw/ds003123/`. 
  - **Why manual placement?** The dataset is not in the verified‑datasets list, and the pipeline does not attempt automated download (per the verified-datasets rule).
  - **How?** Download ds003123 from OpenNeuro, extract it, and place the directory under `data/raw/ds003123/`.

## Installation
```bash
git clone <repo-url>
cd projects/PROJ-471-the-influence-of-visual-salience-on-atte
pip install -r code/requirements.txt
```

## Verify Data Presence
```bash
python -m code.ingestion.verify_data
# Expected output:
#   "✅ Dataset ds003123 found. Checksum recorded."
# If missing:
#   "❌ ERROR: DATA_MISSING_001 – please place the extracted OpenNeuro dataset under data/raw/ds003123/."
```

## Run the Full Pipeline
```bash
python -m code.main --stage full
```
The orchestrator executes the steps defined in `plan.md` in the required order:
1. **Dataset verification** (checks presence; no download).  
2. **Salience map generation** (GBVS on CPU with error handling; DeepGaze II GPU fallback only if CUDA available AND needed).  
3. **ROI mask creation** (YOLOv8 + Detectron2).  
4. **Eye‑tracking metric extraction** (including fixation latency).  
5. **Alignment & low‑level + semantic feature augmentation**.  
6. **Collinearity reduction** (PCA orthogonalization if VIF > 5).  
7. **Statistical modeling** (mixed‑effects, FDR, sensitivity, power check).  
8. **Contract validation** (schema checks, disclaimer enforcement).  

## Expected Outputs
- `data/processed/aligned_data.csv` – merged table containing salience scores, fixation metrics, low‑level covariates (luminance, contrast, edge_density), and semantic covariates (moral_valence, scene_complexity); includes `fixation_latency_ms` and `excluded` columns.  
- `data/processed/results.json` – statistical summary adhering to `output.schema.yaml`, including post-orthogonalization VIF if collinearity reduction was applied.  
- `data/interim/salience_metadata.json` – metadata for all generated salience maps, adhering to `salience.schema.yaml`.  
- `logs/pipeline.log` – detailed runtime log, including resource usage (SC‑002), any excluded trials (SC‑005), and collinearity diagnostics.  
- `logs/diagnostics.log` – detailed VIF report (pre/post-orthogonalization), power analysis summary, and edge-case handling notes.

## Troubleshooting
| Symptom | Likely Cause | Fix |
|---|---|---|
| `DATA_MISSING_001` | OpenNeuro dataset not placed | Download ds003123 from OpenNeuro, extract, and place under `data/raw/ds003123/`. |
| `CUDA error` | Accidental GPU usage on CPU runner | Ensure `code/config.py` sets `device = "cpu"`; re‑run. |
| MemoryError during salience generation | Batch size too large | Reduce `BATCH_SIZE` in `code/config.py` (e.g., from 8 to 4). |
| `POWER_INSUFFICIENT` | Simulated power < 0.8 | Collect more participants or accept that inference is not valid. |
| Missing columns in `aligned_data.csv` | Alignment step omitted covariates | Verify `code/analysis/align_data.py` produces `moral_valence`, `scene_complexity`, and other required columns; run `code/utils/independence_validator.py` for diagnostics. |
| High VIF values in results | Collinearity among visual features | Check `logs/diagnostics.log` for VIF summary; PCA orthogonalization should have been applied. If not, verify `code/analysis/orthogonalize.py` ran successfully. |
