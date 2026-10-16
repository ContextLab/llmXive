# Quickstart: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## Prerequisites
- **Python** 3.11+ (Ubuntu 22.04 recommended)
- **Git**
- **GitHub Actions runner** (CPU‑only, ≤7 GB RAM) – the CI environment used for reproducibility.

## Installation
```bash
git clone <repo-url>
cd projects/PROJ-471-the-influence-of-visual-salience-on-atte
pip install -r code/requirements.txt
```

## Data Acquisition
The OpenNeuro *Moral Foundations Eye‑Tracking* dataset (ds003123) will be downloaded automatically if it is not already present.

```bash
# Download the dataset and generate the checksum manifest
python code/ingestion/download_data.py
```

## Verify Data Presence
```bash
python code/ingestion/verify_data.py
# Expected output: "Dataset verification succeeded."
# If missing or corrupted you will see a clear error message.
```

## Run the Full Pipeline
```bash
python -m code.main --stage smoke
```

The orchestrator executes the steps defined in `plan.md` in order:
1. Verify dataset presence.
2. Generate salience maps (DeepGaze II CPU‑only).
3. Create ROI masks (YOLOv8 + Detectron2).
4. Parse eye‑tracking metrics (including fixation latency).
5. Align data.
6. Compute low‑level visual features (luminance, contrast, edge density).
7. Fit the mixed‑effects model with covariates, apply FDR correction, run sensitivity analysis, and **always** add the `"disclaimer": "correlational only"` field to the JSON results.
8. Validate outputs against contracts.

## Expected Outputs
- `data/processed/aligned_data.csv` – merged predictor & outcome table (includes `fixation_latency_ms` and `edge_density`).
- `data/processed/results.json` – statistical summary adhering to `output.schema.yaml`.
- `data/interim/salience_metadata.json` – metadata for each generated salience map.
- `data/interim/salience_maps/*.npy` – pixel‑wise salience maps for every stimulus image.
- `logs/pipeline.log` – detailed runtime log, including resource usage (SC‑002) and any excluded trials (SC‑005).

## Troubleshooting
| Symptom | Likely Cause | Fix |
|---|---|---|
| `DATA_MISSING_001` | Dataset not in `data/raw/` | Run `python code/ingestion/download_data.py` to fetch it. |
| `CUDA error` | Accidental GPU usage on CPU runner | Ensure `code/config.py` sets `device = "cpu"`; re‑run. |
| MemoryError during salience generation | Batch size too large | Reduce `BATCH_SIZE` in `code/config.py` (e.g., from 8 to 4). |
| `MODEL_LOADING_ERROR` | No internet or HF token missing | Verify network connectivity and that `HF_TOKEN` is set in `.env`. |
| Missing files after pipeline | Salience generation step not run | Ensure step 2 above completes successfully; the script writes the required artifacts. |
