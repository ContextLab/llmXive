# Quickstart: The Influence of Visual Salience on Attentional Bias in Moral Judgements

## Prerequisites
- Python 3.11+ and `pip`.
- **Data (manual)**: Download the OpenNeuro ds003123 “Moral Foundations Eye‑Tracking” dataset yourself and place the extracted directory at `data/raw/ds003123/`. It must contain a `stimuli/` folder **and** at least one `sub‑*` participant folder with eye‑tracking logs. No verified automated download exists; the pipeline will abort with `DATA_MISSING_001` if the structure is incomplete.

## Installation
```bash
git clone <repo-url>
cd projects/PROJ-471-the-influence-of-visual-salience-on-atte
python code/bootstrap.py --root .
pip install -r requirements.txt
```

## Verify data presence
```bash
python -m code.ingestion.verify_data
# OK:    "✅ Dataset structure valid; N files checksummed to data/raw/checksums.json"
# FAIL:  "❌ DATA_MISSING_001 – expected data/raw/ds003123/stimuli/ and sub-* directories"
```
The script exits non‑zero on missing structure or on an empty checksum file.

## Run the full pipeline
```bash
python -m code.main --stage full
```
Execution order: verify data → DeepGaze II salience maps (CPU) → ROI masks (YOLOv8 for faces, Detectron2 for weapons, with YOLOv8 fallback) → fixation extraction → alignment + covariates → VIF/PCA → mixed models A/B + FDR + power → contract validation.

## Expected outputs
- `data/raw/checksums.json` – SHA‑256 of every raw file (non‑empty).  
- `data/interim/salience_maps/<stimulus_id>.npy` + `salience_metadata.json` (schema‑conformant; `generation_method` will be `"deepgaze_ii"` for primary runs).  
- `data/interim/masks/` + `mask_metadata.csv` (YOLOv8 masks for faces; Detectron2 masks for weapons when available).  
- `data/interim/fixations.csv` (fixation metrics).  
- `data/processed/aligned_data.csv` (validates against `dataset.schema.yaml`).  
- `data/processed/results.json` (validates against `output.schema.yaml`; includes FDR‑corrected p‑values, sensitivity metric, VIF report, `power_status`, and the mandatory `"correlational only"` disclaimer).  
- `logs/pipeline.log`, `logs/diagnostics.log`, `logs/resource.log`.

## Run tests
```bash
pytest tests/ -q
```
Unit tests cover bootstrap (with `--root tmp_path`), data verification, salience generation (DeepGaze II with fallback), ROI segmentation (including graceful degradation when Detectron2 is unavailable), fixation parsing, and contract validation.

## Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| `DATA_MISSING_001` | ds003123 not placed / incomplete structure | Place the full extracted dataset (stimuli + sub‑* dirs) under `data/raw/ds003123/`. |
| Empty `checksums.json` | Verification ran on an empty directory | Ensure raw files exist; re‑run `verify_data.py`. |
| All masks `undetected` | Detectron2 weights unavailable offline | Allow network on first run to cache Detectron2 weights, or accept YOLOv8‑only weapon detection (graceful fallback). |
| High VIF | Collinear low‑level covariates | PCA orthogonalization is applied automatically when VIF > 5; see `logs/diagnostics.log`. |
| `power_status: "invalid"` | Simulated power < 0.8 | Result is reported as invalid for inference per SC‑003; limitation documented. |
| DeepGaze II OOM or timeout | Image too large for CPU memory | The script automatically falls back to the deterministic spectral‑residual method for that image. |

---

